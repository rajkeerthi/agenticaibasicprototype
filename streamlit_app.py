"""
Streamlit UI for prototype2_demand_supply.

Layout:
- Left: chat + run logs
- Right: task flow visualization + results + approvals

Run:
  cd /Users/rajkeerthiananthan/Desktop/AgenticAI_projects
  source venv/bin/activate
  streamlit run prototype2_demand_supply/streamlit_app.py
"""

from __future__ import annotations

import asyncio
import json
import sys
import types
from pathlib import Path
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import streamlit as st

# Streamlit Cloud checks out the repo into a directory named after the repo
# (e.g., /mount/src/agenticaibasicprototype). In our local dev machine, this folder
# is named prototype2_demand_supply, so imports like `prototype2_demand_supply.*` work.
# In cloud, the folder name differs, so we create a small compatibility shim:
# - add repo root to sys.path
# - alias the repo root as the `prototype2_demand_supply` package
REPO_ROOT = Path(__file__).resolve().parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

if "prototype2_demand_supply" not in sys.modules:
    pkg = types.ModuleType("prototype2_demand_supply")
    pkg.__path__ = [str(REPO_ROOT)]  # type: ignore[attr-defined]
    sys.modules["prototype2_demand_supply"] = pkg

from prototype2_demand_supply.agents.tools import fetch_relevant_products_by_abc_xyz
from prototype2_demand_supply.graph.demand_flow import build_demand_flow_graph
from prototype2_demand_supply.DBmock.approved_consensus_demand import (
    load_approved_consensus_demands,
    save_approved_consensus_demand,
)
from prototype2_demand_supply.graph.planner_request_parser import parse_planner_request
from prototype2_demand_supply.DBmock.consensus_demand import (
    load_consensus_demands,
    set_consensus_approval_status,
)


@dataclass
class FlowRun:
    status: str  # "idle" | "running" | "done" | "error"
    last_error: Optional[str] = None
    last_output: Optional[Dict[str, Any]] = None
    active_node: Optional[str] = None
    events: List[Dict[str, Any]] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.events is None:
            self.events = []


def _init_state() -> None:
    st.session_state.setdefault("chat", [])
    st.session_state.setdefault("run", FlowRun(status="idle"))
    st.session_state.setdefault("approval_overrides", {})  # sku_id -> approve/reject
    st.session_state.setdefault("pending_run_state", None)  # Dict[str, Any] | None
    st.session_state.setdefault("pending_run_reason", None)  # str | None
    st.session_state.setdefault("shown_approval_prompts", set())  # type: ignore[arg-type]
    st.session_state.setdefault("clarify_context", None)  # holds partial parse + original query
    # Note: we run pending workflows at the top of the script (before rendering chat/results)
    # to avoid UI lag where Results updates but Chat doesn't yet show approval buttons.


def _chat_add(role: str, content: str) -> None:
    st.session_state.chat.append({"role": role, "content": content})


def _dot_flow(active: Optional[str] = None) -> str:
    """
    Simple Graphviz DOT for the right-panel flow diagram.
    """
    def color(node: str) -> str:
        return "gold" if active == node else "lightgray"

    return f"""
digraph G {{
  rankdir=TB;
  node [shape=box, style="rounded,filled", fontname="Helvetica"];

  subgraph cluster_agents {{
    label="Demand Team";
    style="rounded";
    Actor [label="Actor Agent", fillcolor="{color('actor')}"];
    Critic [label="Critic Agent", fillcolor="{color('critic')}"];
    Actor -> Critic [label="AutoGen msg"];
    Critic -> Actor [label="rerun?", style=dashed];
  }}

  subgraph cluster_drivers {{
    label="Demand Drivers (tools)";
    style="rounded";
    Social [label="Social", fillcolor="{color('social')}"];
    Marketing [label="Marketing", fillcolor="{color('marketing')}"];
    Promo [label="Trade Promo", fillcolor="{color('trade_promo')}"];
    Shelf [label="Digital Shelf", fillcolor="{color('digital_shelf')}"];
    Weather [label="Weather", fillcolor="{color('weather')}"];
    Competitor [label="Competitor", fillcolor="{color('competitor')}"];
    Social -> Actor;
    Marketing -> Actor;
    Promo -> Actor;
    Shelf -> Actor;
    Weather -> Actor;
    Competitor -> Actor;
  }}

  HITL [label="Human Approval Gate", fillcolor="{color('human_approval')}"];
  Result [label="Final Forecast + Reasoning", fillcolor="{color('finalize')}"];

  Critic -> HITL;
  HITL -> Result;
}}
"""


def _status_update(status_box: Any, label: str, *, state: Optional[str] = None) -> None:
    """
    Best-effort update of a Streamlit status box.
    """
    try:
        if hasattr(status_box, "update"):
            if state is None:
                status_box.update(label=label)
            else:
                status_box.update(label=label, state=state)
        else:
            status_box.write(label)
    except Exception:
        # UI update failures should not break the flow run.
        pass


async def _run_graph_with_events(state: Dict[str, Any], status_box: Any) -> Dict[str, Any]:
    """
    Run LangGraph and collect events for live UI updates.
    """
    g = build_demand_flow_graph()
    out: Optional[Dict[str, Any]] = None
    async for ev in g.astream_events(state, version="v2"):
        # store raw events; UI will cherry-pick
        st.session_state.run.events.append({"event": ev["event"], "name": ev.get("name"), "data": ev.get("data")})
        # try to infer "active node" from events
        if ev["event"] == "on_chain_start":
            st.session_state.run.active_node = ev.get("name")
            _status_update(status_box, f"Running: {ev.get('name')}", state="running")
            # High-signal progress message (avoid spamming).
            if ev.get("name") in {"parse_request", "build_sku_queue", "actor", "critic", "human_approval", "finalize"}:
                _chat_add("assistant", f"Step started: `{ev.get('name')}`")
        if ev["event"] == "on_chain_end":
            st.session_state.run.active_node = None
            _status_update(status_box, f"Completed: {ev.get('name')}", state="running")
            if ev.get("name") in {"parse_request", "build_sku_queue", "actor", "critic", "human_approval", "finalize"}:
                _chat_add("assistant", f"Step completed: `{ev.get('name')}`")
        if ev["event"] == "on_chain_stream":
            # sometimes final state is streamed here (not always)
            pass

    out = await g.ainvoke(state)
    return out


def _set_pending_run(state: Dict[str, Any], *, reason: str) -> None:
    st.session_state.pending_run_state = state
    st.session_state.pending_run_reason = reason


def _apply_human_decision_locally(sku_id: str, decision: str) -> None:
    """
    Apply approve/reject immediately without re-running the LangGraph workflow.
    This avoids a confusing Actor/Critic "loop" and removes lag for the user.
    """
    out = st.session_state.run.last_output or {}
    results = out.get("results") or []
    decision_l = (decision or "").strip().lower()

    updated = False
    for r in results:
        if r.get("sku_id") != sku_id:
            continue
        # Only act if still pending
        if (r.get("approval_status") or "") != "pending":
            continue

        if decision_l in {"approve", "approved", "y", "yes"}:
            r["approval_status"] = "approved"
            r["human_decision"] = "approve"
            r["finalized"] = True

            af = r.get("actor_forecast") or {}
            try:
                boost_frac = float(af.get("total_boost_percent", 0.0))
            except Exception:
                boost_frac = 0.0
            record = {
                "sku_id": sku_id,
                "customer_id": out.get("customer_id"),
                "location_id": out.get("location_id"),
                "as_of_date": out.get("as_of_date"),
                "baseline_forecast": af.get("baseline_forecast"),
                "total_boost_fraction": boost_frac,
                "total_boost_percent": round(boost_frac * 100.0, 2),
                "final_demand_forecast": af.get("final_demand_forecast"),
            }
            save_approved_consensus_demand(record)
            # Update "planned consensus" status too (so the table reflects approval instantly).
            set_consensus_approval_status(
                sku_id=str(sku_id),
                customer_id=str(record.get("customer_id")),
                location_id=str(record.get("location_id")),
                as_of_date=str(record.get("as_of_date")),
                approval_status="approved",
            )
            _chat_add(
                "assistant",
                f"✅ Approved **{sku_id}**. Written to Approved consensus demand table.",
            )
        else:
            r["approval_status"] = "rejected"
            r["human_decision"] = "reject"
            r["finalized"] = False
            # Update planned consensus table as rejected (no approved writeback).
            set_consensus_approval_status(
                sku_id=str(sku_id),
                customer_id=str(out.get("customer_id")),
                location_id=str(out.get("location_id")),
                as_of_date=str(out.get("as_of_date")),
                approval_status="rejected",
            )
            _chat_add("assistant", f"Rejected **{sku_id}**. No writeback performed.")

        updated = True

    if updated:
        # Persist back into session_state so UI rerenders without buttons.
        out["results"] = results
        st.session_state.run.last_output = out


def _maybe_execute_pending_run(status_box: Any) -> None:
    """
    Execute a pending run request (if any) after UI is rendered enough to show progress.
    """
    state = st.session_state.get("pending_run_state")
    if not state:
        return

    st.session_state.pending_run_state = None
    st.session_state.pending_run_reason = None

    st.session_state.run = FlowRun(status="running")
    _status_update(status_box, "Starting demand flow…", state="running")
    try:
        out = asyncio.run(_run_graph_with_events(state, status_box))
        st.session_state.run.status = "done"
        st.session_state.run.last_output = out
        _status_update(status_box, "Demand flow completed.", state="complete")
        _chat_add("assistant", "Demand flow completed. Review results on the right.")

        # If any approvals are pending, add a clear chat prompt.
        pending = []
        for r in (out.get("results") or []):
            if (r.get("approval_status") or "") == "pending":
                pending.append(r)
        for r in pending:
            sku = r.get("sku_id")
            if not sku or sku in st.session_state.shown_approval_prompts:
                continue
            st.session_state.shown_approval_prompts.add(sku)
            af = r.get("actor_forecast") or {}
            try:
                boost_pct = round(float(af.get("total_boost_percent", 0.0)) * 100.0, 1)
            except Exception:
                boost_pct = None
            _chat_add(
                "assistant",
                (
                    f"Approval required for **{sku}**: "
                    f"Baseline={af.get('baseline_forecast')}, "
                    f"Boost={boost_pct}%, "
                    f"FinalForecast={af.get('final_demand_forecast')}.\n\n"
                    "Use the Approve/Reject buttons below."
                ),
            )
    except Exception as e:
        st.session_state.run.status = "error"
        st.session_state.run.last_error = str(e)
        _status_update(status_box, f"Flow error: {e}", state="error")
        _chat_add("assistant", f"Flow error: {e}")


def _render_controls() -> Dict[str, Any]:
    with st.container():
        c1, c2, c3, c4, c5 = st.columns([2, 2, 2, 3, 2])
        with c1:
            location = st.selectbox("Location", ["BANGALORE"], index=0)
        with c2:
            customer = st.selectbox("Customer", ["BLINKIT", "ZEPTO"], index=0)
        with c3:
            as_of_date = st.selectbox("As-of date", ["2026-01-01", "2026-01-02", "2026-01-03"], index=0)
        with c4:
            products = fetch_relevant_products_by_abc_xyz(location_id=location, abc_class="A", xyz_classes=("Y", "Z"))
            sku_options = ["AUTO", "ALL (A/Y)"] + [p["sku_id"] for p in products]
            sku = st.selectbox("Product (SKU)", sku_options, index=0)
        with c5:
            run_clicked = st.button("Run flow", type="primary", use_container_width=True)

    st.caption("Use the chat on the left for natural-language instructions (single chat box).")

    scope = "all_relevant" if sku.startswith("ALL") else "single"
    sku_id = "AUTO" if sku.startswith("AUTO") or sku.startswith("ALL") else sku
    user_query = (
        "Compute final demand forecast and explain the boost drivers. "
        "If approval is required, prepare an approval request."
    )

    state: Dict[str, Any] = {
        "sku_id": sku_id,
        "customer_id": customer,
        "location_id": location,
        "as_of_date": as_of_date,
        "scope": scope,
        "abc_class": "A",
        "xyz_classes": ["Y", "Z"],
        "user_query": user_query,
        "max_retries": 1,
    }

    if run_clicked:
        _chat_add(
            "user",
            f"Run flow for customer={customer}, location={location}, date={as_of_date}, sku={sku}.",
        )
        _set_pending_run(state, reason="dropdown_run")
        st.rerun()

    return state


def _render_chat() -> None:
    st.subheader("Chat")
    chat_box = st.container(height=520, border=True)
    with chat_box:
        for msg in st.session_state.chat:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        # Render approval buttons inside chat for any pending approvals in the last output.
        out = (st.session_state.run.last_output or {}) if st.session_state.run.status == "done" else {}
        for r in (out.get("results") or []):
            if (r.get("approval_status") or "") != "pending":
                continue
            sku = r.get("sku_id")
            if not sku:
                continue
            with st.chat_message("assistant"):
                st.markdown(f"**Approval needed for {sku}**")
                af = r.get("actor_forecast") or {}
                try:
                    boost_pct = round(float(af.get("total_boost_percent", 0.0)) * 100.0, 1)
                except Exception:
                    boost_pct = None
                st.markdown(
                    f"- Baseline: `{af.get('baseline_forecast')}`\n"
                    f"- Boost: `{boost_pct}%`\n"
                    f"- Final forecast: `{af.get('final_demand_forecast')}`"
                )
                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button(f"Approve {sku}", key=f"chat_approve_{sku}"):
                        _apply_human_decision_locally(sku, "approve")
                        st.rerun()
                with col_b:
                    if st.button(f"Reject {sku}", key=f"chat_reject_{sku}"):
                        _apply_human_decision_locally(sku, "reject")
                        st.rerun()

    prompt = st.chat_input("Ask the Demand Actor (e.g., 'Run all A/Y for Bangalore on 2026-01-03')")
    if prompt:
        _chat_add("user", prompt)
        # If we are in a clarification loop, combine prior query + new user answer.
        clarify = st.session_state.get("clarify_context")
        combined = prompt
        if clarify and isinstance(clarify, dict) and clarify.get("original_query"):
            combined = f"{clarify['original_query']}\nUser provided: {prompt}"

        params = asyncio.run(parse_planner_request(combined))
        if params.needs_clarification:
            st.session_state.clarify_context = {"original_query": combined}
            questions = params.clarification_questions or ["Please provide customer, location, and date."]
            _chat_add("assistant", "I need a bit more info before I can run the consensus demand:")
            for q in questions:
                _chat_add("assistant", f"- {q}")
            st.rerun()
        else:
            st.session_state.clarify_context = None
            chat_state = params.to_state(user_query=combined)
            chat_state["max_retries"] = 1
            _set_pending_run(chat_state, reason="chat_run")
            st.rerun()


def _render_results_and_approvals(out: Dict[str, Any]) -> None:
    st.subheader("Results")
    results = out.get("results") or []
    if not results:
        st.info("No results yet.")
        return

    for r in results:
        sku = r.get("sku_id")
        af = r.get("actor_forecast") or {}
        cr = r.get("critic_result") or {}
        approval_status = r.get("approval_status") or "not_required"
        try:
            boost_pct = round(float(af.get("total_boost_percent", 0.0)) * 100.0, 1)
        except Exception:
            boost_pct = None

        with st.expander(
            f"{sku} — final={af.get('final_demand_forecast')} | boost={boost_pct}% | {approval_status}",
            expanded=True,
        ):
            st.json(
                {
                    "baseline": af.get("baseline_forecast"),
                    "total_boost_percent": boost_pct,
                    "total_boost_fraction": af.get("total_boost_percent"),
                    "final_demand_forecast": af.get("final_demand_forecast"),
                    "critic_decision": cr.get("decision"),
                    "next_action": cr.get("next_action"),
                    "approval_status": approval_status,
                }
            )
            st.markdown("**Actor reasoning**")
            st.write(r.get("actor_reasoning") or "")

    st.subheader("All consensus demands planned by agent (mock DB)")
    consensus = load_consensus_demands()
    if consensus:
        # Filter to current context by default
        cur_customer = out.get("customer_id")
        cur_location = out.get("location_id")
        cur_date = out.get("as_of_date")
        cur_skus = {r.get("sku_id") for r in results if r.get("sku_id")}

        filtered = [
            r
            for r in consensus
            if (cur_customer is None or r.get("customer_id") == cur_customer)
            and (cur_location is None or r.get("location_id") == cur_location)
            and (cur_date is None or r.get("as_of_date") == cur_date)
            and (not cur_skus or r.get("sku_id") in cur_skus)
        ]

        show_all = st.checkbox("Show all planned consensus history", value=False)
        if show_all:
            st.dataframe(consensus, use_container_width=True, hide_index=True)
        else:
            st.caption("Showing planned consensus matching the current run context (SKU/customer/location/date).")
            st.dataframe(filtered if filtered else consensus, use_container_width=True, hide_index=True)
    else:
        st.caption("No planned consensus records yet. Run a flow to populate this table.")

    st.subheader("Approved consensus demand (mock DB)")
    approvals = load_approved_consensus_demands()
    if approvals:
        st.dataframe(approvals, use_container_width=True, hide_index=True)
    else:
        st.caption("No approved records yet.")


def _render_flow_panel() -> None:
    st.subheader("Task Flow")
    st.graphviz_chart(_dot_flow(active=st.session_state.run.active_node), use_container_width=True)

    run = st.session_state.run
    if run.status == "running":
        st.info("Running… (nodes will highlight as events arrive)")
    elif run.status == "error":
        st.error(run.last_error or "Unknown error")
    elif run.status == "done" and run.last_output:
        _render_results_and_approvals(run.last_output)
    else:
        st.caption("Run the flow to see outputs here.")


def main() -> None:
    st.set_page_config(page_title="Demand Team (Actor/Critic) — Prototype", layout="wide")
    _init_state()

    st.title("Demand Team — Actor/Critic Forecasting")
    _render_controls()

    # Run any pending workflow BEFORE rendering chat/results (prevents multi-minute lag)
    # Use a global status box at the top so progress is still visible.
    progress = st.status("Idle", expanded=False)
    _maybe_execute_pending_run(progress)

    left, right = st.columns([1, 2], gap="large")
    with left:
        _render_chat()
    with right:
        _render_flow_panel()


if __name__ == "__main__":
    main()


