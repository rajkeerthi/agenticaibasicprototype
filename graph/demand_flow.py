"""
LangGraph demand-team workflow (Actor -> Critic -> route).

We keep this workflow deterministic (no LLM) but still:
- orchestration uses LangGraph v1.0+
- agent-to-agent communication uses AutoGen (autogen_core runtime)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, TypedDict

from langgraph.graph import END, StateGraph

from prototype2_demand_supply.agents.demand_team_agents import (
    ACTOR_AGENT_ID,
    CRITIC_AGENT_ID,
    ActorRunRequest,
    CriticReviewRequest,
)
from prototype2_demand_supply.agents.runtime import build_demand_team_runtime
from prototype2_demand_supply.agents.tools import fetch_relevant_products_by_abc_xyz
from prototype2_demand_supply.graph.planner_request_parser import parse_planner_request
from prototype2_demand_supply.DBmock.approved_consensus_demand import save_approved_consensus_demand
from prototype2_demand_supply.DBmock.consensus_demand import upsert_consensus_demand


class DemandFlowState(TypedDict, total=False):
    # Inputs
    sku_id: str
    customer_id: str
    location_id: str
    as_of_date: str
    upper_threshold: float
    lower_threshold: float
    max_retries: int
    user_query: str
    scope: str  # "single" | "all_relevant"
    abc_class: str
    xyz_classes: List[str]

    # Runtime
    attempt: int

    # Outputs
    actor_result: Dict[str, Any]
    actor_forecast: Dict[str, Any]
    actor_reasoning: str
    critic_result: Dict[str, Any]
    critic_reasoning: str
    route: str
    history: List[Dict[str, Any]]

    # Multi-SKU execution
    sku_queue: List[str]
    current_sku_index: int
    results: List[Dict[str, Any]]

    # Human-in-the-loop (per SKU)
    human_decision: str  # "approve" | "reject" | "" (optional)
    approval_status: str  # "pending" | "approved" | "rejected" | "not_required"
    approval_request: Dict[str, Any]
    finalized: bool
    halt_on_pending_approval: bool


async def parse_request_node(state: DemandFlowState) -> DemandFlowState:
    """
    Micro-step: parse natural language request into structured defaults.
    """
    user_query = state.get("user_query") or ""
    if not user_query:
        return dict(state)

    params = await parse_planner_request(user_query)
    new_state: DemandFlowState = dict(state)
    # Only fill if not explicitly set by caller
    new_state.setdefault("customer_id", params.customer_id)
    new_state.setdefault("location_id", params.location_id)
    new_state.setdefault("as_of_date", params.as_of_date)
    new_state.setdefault("upper_threshold", params.upper_threshold)
    new_state.setdefault("lower_threshold", params.lower_threshold)
    new_state.setdefault("scope", params.scope)
    new_state.setdefault("sku_id", params.sku_id)
    new_state.setdefault("abc_class", params.abc_class)
    new_state.setdefault("xyz_classes", list(params.xyz_classes))
    return new_state


def build_sku_queue_node(state: DemandFlowState) -> DemandFlowState:
    """
    Build SKU queue based on scope.
    """
    scope = (state.get("scope") or "single").strip().lower()
    location_id = state.get("location_id", "BANGALORE")
    abc_class = state.get("abc_class", "A")
    xyz_classes = state.get("xyz_classes") or ["Y", "Z"]

    if scope == "all_relevant":
        products = fetch_relevant_products_by_abc_xyz(
            location_id=location_id, abc_class=abc_class, xyz_classes=tuple(xyz_classes)
        )
        sku_queue = [p["sku_id"] for p in products]
        halt_on_pending_approval = False
    else:
        sku_id = (state.get("sku_id") or "AUTO").strip().upper()
        if not sku_id or sku_id == "AUTO":
            # fall back to first relevant
            products = fetch_relevant_products_by_abc_xyz(
                location_id=location_id, abc_class=abc_class, xyz_classes=tuple(xyz_classes)
            )
            sku_queue = [products[0]["sku_id"]] if products else []
        else:
            sku_queue = [sku_id]
        halt_on_pending_approval = True

    new_state: DemandFlowState = dict(state)
    new_state["sku_queue"] = sku_queue
    new_state["current_sku_index"] = 0
    new_state.setdefault("results", [])
    new_state.setdefault("halt_on_pending_approval", halt_on_pending_approval)
    return new_state


def set_current_sku_node(state: DemandFlowState) -> DemandFlowState:
    idx = int(state.get("current_sku_index", 0))
    queue = state.get("sku_queue") or []
    sku_id = queue[idx] if 0 <= idx < len(queue) else ""

    new_state: DemandFlowState = dict(state)
    new_state["sku_id"] = sku_id
    new_state["attempt"] = 1
    # clear per-sku artifacts
    new_state.pop("actor_result", None)
    new_state.pop("actor_forecast", None)
    new_state.pop("actor_reasoning", None)
    new_state.pop("critic_result", None)
    new_state.pop("critic_reasoning", None)
    new_state.pop("history", None)
    return new_state


def select_products_node(state: DemandFlowState) -> DemandFlowState:
    """
    Micro-step 1: Product selection.

    If sku_id is missing or "AUTO", select the first relevant SKU by ABC/XYZ filters.
    """
    sku_id = (state.get("sku_id") or "").strip().upper()
    if sku_id and sku_id != "AUTO":
        return dict(state)

    location_id = state.get("location_id", "BANGALORE")
    products = fetch_relevant_products_by_abc_xyz(location_id=location_id, abc_class="A", xyz_classes=("Y", "Z"))
    chosen = products[0]["sku_id"] if products else ""

    new_state: DemandFlowState = dict(state)
    new_state["sku_id"] = chosen
    return new_state


async def actor_node(state: DemandFlowState) -> DemandFlowState:
    runtime = await build_demand_team_runtime()
    runtime.start()
    try:
        attempt = int(state.get("attempt", 1))
        msg = ActorRunRequest(
            sku_id=state["sku_id"],
            customer_id=state.get("customer_id", "BLINKIT"),
            location_id=state.get("location_id", "BANGALORE"),
            as_of_date=state.get("as_of_date", "2026-01-01"),
            attempt=attempt,
            user_query=state.get("user_query"),
        )
        actor_result = await runtime.send_message(msg, recipient=ACTOR_AGENT_ID)
        new_state: DemandFlowState = dict(state)
        new_state["actor_result"] = actor_result.final_boost
        new_state["actor_forecast"] = actor_result.final_forecast
        new_state["actor_reasoning"] = actor_result.reasoning
        return new_state
    finally:
        await runtime.stop()


async def critic_node(state: DemandFlowState) -> DemandFlowState:
    runtime = await build_demand_team_runtime()
    runtime.start()
    try:
        attempt = int(state.get("attempt", 1))
        msg = CriticReviewRequest(
            sku_id=state["sku_id"],
            customer_id=state.get("customer_id", "BLINKIT"),
            location_id=state.get("location_id", "BANGALORE"),
            as_of_date=state.get("as_of_date", "2026-01-01"),
            upper_threshold=float(state.get("upper_threshold", 0.30)),
            lower_threshold=float(state.get("lower_threshold", -0.20)),
            attempt=attempt,
        )
        critic_result = await runtime.send_message(msg, recipient=CRITIC_AGENT_ID)
        new_state: DemandFlowState = dict(state)
        new_state["critic_result"] = critic_result.review
        new_state["critic_reasoning"] = critic_result.reasoning

        # Track history for debugging / UI
        history = list(state.get("history", []))
        history.append(
            {
                "attempt": attempt,
                "as_of_date": state.get("as_of_date"),
                "actor_total_boost": state.get("actor_result", {}).get("total_boost_percent"),
                "critic_decision": critic_result.review.get("decision"),
                "rerun_recommendations": critic_result.review.get("rerun_recommendations"),
            }
        )
        new_state["history"] = history
        return new_state
    finally:
        await runtime.stop()


def route_node(state: DemandFlowState) -> DemandFlowState:
    """
    Decide where to go next based on critic decision + retry count.
    """
    critic = state.get("critic_result", {})
    decision = critic.get("decision")
    max_retries = int(state.get("max_retries", 1))
    attempt = int(state.get("attempt", 1))

    if decision == "ask_actor_rerun":
        # Hard safety: never loop retries; allow at most 1 rerun AND only if we have concrete rerun recommendations.
        reruns = critic.get("rerun_recommendations") or []
        if attempt == 1 and max_retries >= 2 and len(reruns) > 0:
            route = "rerun"
        else:
            route = "finalize"
    elif decision == "route_to_human_approval":
        route = "human_approval"
    else:
        # within_thresholds OR retries exhausted
        route = "finalize"

    new_state: DemandFlowState = dict(state)
    new_state["route"] = route
    return new_state


def human_approval_node(state: DemandFlowState) -> DemandFlowState:
    """
    HITL gate:
    - If no human_decision is provided, mark approval_status=pending and return an approval_request payload.
    - If provided, mark approved/rejected.

    In a real UI, you would:
    - run the graph until pending,
    - show approval_request to the user,
    - then resume by calling graph.ainvoke() again with human_decision set.
    """
    decision = (state.get("human_decision") or "").strip().lower()

    new_state: DemandFlowState = dict(state)
    new_state["approval_request"] = {
        "sku_id": state.get("sku_id"),
        "customer_id": state.get("customer_id"),
        "location_id": state.get("location_id"),
        "as_of_date": state.get("as_of_date"),
        "actor_forecast": state.get("actor_forecast"),
        "actor_result": state.get("actor_result"),
        "actor_reasoning": state.get("actor_reasoning"),
        "critic_result": state.get("critic_result"),
        "critic_reasoning": state.get("critic_reasoning"),
        "message": "Human approval required to finalize consensus demand for this SKU.",
    }

    if decision in {"approve", "approved", "yes", "y"}:
        new_state["approval_status"] = "approved"
        new_state["human_decision"] = "approve"
    elif decision in {"reject", "rejected", "no", "n"}:
        new_state["approval_status"] = "rejected"
        new_state["human_decision"] = "reject"
    else:
        new_state["approval_status"] = "pending"

    return new_state


def finalize_node(state: DemandFlowState) -> DemandFlowState:
    """
    Finalization marker (consensus demand can be considered finalized for this SKU).
    """
    new_state: DemandFlowState = dict(state)
    new_state["finalized"] = True
    new_state.setdefault("approval_status", "not_required")

    # Writeback only when explicitly approved by human.
    if new_state.get("approval_status") == "approved":
        af = new_state.get("actor_forecast") or {}
        try:
            boost_frac = float(af.get("total_boost_percent", 0.0))
        except Exception:
            boost_frac = 0.0
        record = {
            "sku_id": new_state.get("sku_id"),
            "customer_id": new_state.get("customer_id"),
            "location_id": new_state.get("location_id"),
            "as_of_date": new_state.get("as_of_date"),
            "baseline_forecast": af.get("baseline_forecast"),
            # Store both for clarity:
            # - fraction is used in code, percent is for display/business.
            "total_boost_fraction": boost_frac,
            "total_boost_percent": round(boost_frac * 100.0, 2),
            "final_demand_forecast": af.get("final_demand_forecast"),
        }
        save_approved_consensus_demand(record)

    return new_state


def store_result_node(state: DemandFlowState) -> DemandFlowState:
    """
    Store per-SKU final artifacts into results[].
    """
    results = list(state.get("results", []))
    results.append(
        {
            "sku_id": state.get("sku_id"),
            "as_of_date": state.get("as_of_date"),
            "actor_forecast": state.get("actor_forecast"),
            "actor_result": state.get("actor_result"),
            "actor_reasoning": state.get("actor_reasoning"),
            "critic_result": state.get("critic_result"),
            "critic_reasoning": state.get("critic_reasoning"),
            "approval_status": state.get("approval_status"),
            "human_decision": state.get("human_decision"),
            "finalized": state.get("finalized", False),
            # Include approval_request so UI can later show pending SKUs and approve them.
            "approval_request": state.get("approval_request"),
        }
    )

    # Persist "planned consensus" for this SKU (regardless of approval status).
    af = state.get("actor_forecast") or {}
    cr = state.get("critic_result") or {}
    try:
        boost_frac = float(af.get("total_boost_percent", 0.0))
    except Exception:
        boost_frac = 0.0
    upsert_consensus_demand(
        {
            "sku_id": state.get("sku_id"),
            "customer_id": state.get("customer_id"),
            "location_id": state.get("location_id"),
            "as_of_date": state.get("as_of_date"),
            "baseline_forecast": af.get("baseline_forecast"),
            "total_boost_fraction": boost_frac,
            "total_boost_percent": round(boost_frac * 100.0, 2),
            "final_demand_forecast": af.get("final_demand_forecast"),
            "critic_decision": cr.get("decision"),
            "took_approval_route": cr.get("decision") == "route_to_human_approval",
            "approval_status": state.get("approval_status") or "pending",
        }
    )
    new_state: DemandFlowState = dict(state)
    new_state["results"] = results
    return new_state


def next_sku_or_end_node(state: DemandFlowState) -> DemandFlowState:
    """
    After finishing one SKU, decide whether to run the next.
    """
    idx = int(state.get("current_sku_index", 0))
    queue = state.get("sku_queue") or []
    if idx + 1 < len(queue):
        route = "next_sku"
    else:
        route = "end"
    new_state: DemandFlowState = dict(state)
    new_state["route"] = route
    return new_state


def bump_sku_index_node(state: DemandFlowState) -> DemandFlowState:
    new_state: DemandFlowState = dict(state)
    new_state["current_sku_index"] = int(state.get("current_sku_index", 0)) + 1
    return new_state


def bump_attempt_node(state: DemandFlowState) -> DemandFlowState:
    new_state: DemandFlowState = dict(state)
    new_state["attempt"] = int(state.get("attempt", 1)) + 1
    return new_state


def build_demand_flow_graph():
    """
    Returns a compiled LangGraph runnable.
    """
    g = StateGraph(DemandFlowState)
    g.add_node("parse_request", parse_request_node)
    g.add_node("build_sku_queue", build_sku_queue_node)
    g.add_node("set_current_sku", set_current_sku_node)
    g.add_node("actor", actor_node)
    g.add_node("critic", critic_node)
    g.add_node("route", route_node)
    g.add_node("bump_attempt", bump_attempt_node)
    g.add_node("human_approval", human_approval_node)
    g.add_node("finalize", finalize_node)
    g.add_node("store_result", store_result_node)
    g.add_node("next_sku_or_end", next_sku_or_end_node)
    g.add_node("bump_sku_index", bump_sku_index_node)

    g.set_entry_point("parse_request")
    g.add_edge("parse_request", "build_sku_queue")
    g.add_edge("build_sku_queue", "set_current_sku")
    g.add_edge("set_current_sku", "actor")
    g.add_edge("actor", "critic")
    g.add_edge("critic", "route")

    # Conditional route: rerun => bump attempt => actor, else end
    def _router(state: DemandFlowState) -> str:
        return state.get("route", "end")

    g.add_conditional_edges(
        "route",
        _router,
        {
            "rerun": "bump_attempt",
            "human_approval": "human_approval",
            "finalize": "finalize",
        },
    )
    g.add_edge("bump_attempt", "actor")
    # HITL routing: pending ends early, approved finalizes, rejected stores result.
    def _hitl_router(state: DemandFlowState) -> str:
        status = state.get("approval_status", "pending")
        return status

    g.add_conditional_edges(
        "human_approval",
        _hitl_router,
        {
            # Store the pending SKU so UI can show results + approval buttons.
            # In single-SKU mode this will end immediately after storing; in multi-SKU mode we continue.
            "pending": "store_result",
            "approved": "finalize",
            "rejected": "store_result",
        },
    )
    g.add_edge("finalize", "store_result")
    g.add_edge("store_result", "next_sku_or_end")

    def _post_router(state: DemandFlowState) -> str:
        return state.get("route", "end")

    g.add_conditional_edges(
        "next_sku_or_end",
        _post_router,
        {
            "next_sku": "bump_sku_index",
            "end": END,
        },
    )
    g.add_edge("bump_sku_index", "set_current_sku")

    return g.compile()


