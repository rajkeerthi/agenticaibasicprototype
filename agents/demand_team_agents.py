"""
Demand team AutoGen agents (Actor + Critic).

We use `autogen_core` (AutoGen v0.4+ family) so agent-to-agent communication is real,
but we keep the logic deterministic for now (no LLM calls yet).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from autogen_core import AgentId, MessageContext, RoutedAgent
from autogen_core._routed_agent import message_handler

from .llm import build_reasoning_client
from .tools import (
    build_boost_reasoning_context,
    calculate_final_demand_boost,
    calculate_final_demand_forecast,
    critic_review_consensus_demand_boost,
)


# ----------------------------
# Messages
# ----------------------------


@dataclass(frozen=True)
class ActorRunRequest:
    sku_id: str
    customer_id: str = "BLINKIT"
    location_id: str = "BANGALORE"
    as_of_date: str = "2026-01-01"
    attempt: int = 1
    # If critic asks to rerun specific tools later, we can pass that here.
    rerun_tools: Optional[List[str]] = None
    # Optional natural-language instruction from demand planner (for LLM to interpret)
    user_query: Optional[str] = None


@dataclass(frozen=True)
class ActorRunResult:
    sku_id: str
    customer_id: str
    location_id: str
    as_of_date: str
    attempt: int
    # Output from calculate_final_demand_boost
    final_boost: Dict[str, Any]
    # Output from calculate_final_demand_forecast
    final_forecast: Dict[str, Any]
    # Human-readable reasoning (LLM-generated if configured; else template)
    reasoning: str
    reasoning_source: str  # "llm" | "template"
    # Minimal "execution status" metadata for debugging
    executed_steps: List[str]


@dataclass(frozen=True)
class CriticReviewRequest:
    sku_id: str
    customer_id: str = "BLINKIT"
    location_id: str = "BANGALORE"
    as_of_date: str = "2026-01-01"
    upper_threshold: float = 0.30
    lower_threshold: float = -0.20
    attempt: int = 1


@dataclass(frozen=True)
class CriticReviewResult:
    sku_id: str
    customer_id: str
    location_id: str
    as_of_date: str
    attempt: int
    review: Dict[str, Any]
    reasoning: str


# ----------------------------
# Agents
# ----------------------------


class DemandActorAgent(RoutedAgent):
    """
    Demand Actor:
    - fetches/derives boost by category
    - aggregates total boost
    - sends results to Critic

    For now, it deterministically calls our Python tool functions.
    """

    def __init__(self, *, enable_llm: bool = True) -> None:
        super().__init__(description="Demand Actor agent (deterministic tool runner + optional LLM reasoning)")
        self._llm_client = build_reasoning_client(prefer="google") if enable_llm else None

    def _template_reasoning(self, context: Dict[str, Any], final_forecast: Dict[str, Any]) -> str:
        boost = context["boost"]
        scenario = context.get("scenario") or "UNKNOWN"
        notes: Dict[str, str] = context.get("driver_notes", {}) or {}
        baseline = final_forecast.get("baseline_forecast")
        total_frac = boost.get("total_boost_percent")
        total_pct = None
        try:
            total_pct = float(total_frac) * 100.0
        except Exception:
            total_pct = None
        final_fc = final_forecast.get("final_demand_forecast")

        lines = [
            f"Scenario: {scenario}",
            f"Baseline: {baseline} | Total boost: {total_pct:.0f}% | Final demand forecast: {final_fc}"
            if total_pct is not None
            else f"Baseline: {baseline} | Total boost: {total_frac} | Final demand forecast: {final_fc}",
            "Key driver notes:",
        ]
        for k in list(notes.keys())[:6]:
            lines.append(f"- {k}: {notes[k]}")
        return "\n".join(lines)

    @message_handler
    async def on_run_request(self, message: ActorRunRequest, ctx: MessageContext) -> ActorRunResult:
        executed_steps: List[str] = [
            "calculate_final_demand_boost",
            "calculate_final_demand_forecast",
        ]
        # If critic asked to rerun, we still recompute the full final boost for now.
        final_boost = calculate_final_demand_boost(
            sku_id=message.sku_id,
            customer_id=message.customer_id,
            location_id=message.location_id,
            as_of_date=message.as_of_date,
        )
        final_forecast = calculate_final_demand_forecast(
            sku_id=message.sku_id,
            customer_id=message.customer_id,
            location_id=message.location_id,
            as_of_date=message.as_of_date,
        )

        reasoning_context = build_boost_reasoning_context(
            sku_id=message.sku_id,
            customer_id=message.customer_id,
            location_id=message.location_id,
            as_of_date=message.as_of_date,
            final_boost=final_boost,
        )

        if self._llm_client is None:
            reasoning = self._template_reasoning(reasoning_context, final_forecast)
            reasoning_source = "template"
        else:
            system = (
                "You are a demand planning assistant. Explain demand boost drivers clearly and briefly. "
                "Use provided driver notes and the computed boost breakdown. Avoid jargon."
            )
            # Provide derived, display-ready numbers so the model doesn't have to interpret fractions.
            try:
                boost_pct = round(float(final_forecast.get("total_boost_percent", 0.0)) * 100.0, 1)
            except Exception:
                boost_pct = None
            user = (
                f"Demand planner request: {message.user_query or 'Explain the computed boost and final forecast.'}\n\n"
                f"IMPORTANT: Use as_of_date={message.as_of_date} exactly. Do not invent dates.\n"
                f"IMPORTANT: total_boost_percent is a fraction (e.g., -0.3 means -30%). Use boost_percent_display when provided.\n\n"
                f"boost_percent_display: {boost_pct}%\n\n"
                f"Reasoning context (dict):\n{reasoning_context}\n\n"
                f"Final forecast (dict):\n{final_forecast}\n\n"
                "Write 6-10 bullets max. End with one line: "
                "'Baseline=<x>, TotalBoost=<y%>, FinalForecast=<z>'."
            )
            try:
                reasoning = await self._llm_client.generate(system=system, user=user)
                reasoning_source = "llm"
            except Exception:
                reasoning = self._template_reasoning(reasoning_context, final_forecast)
                reasoning_source = "template"
        return ActorRunResult(
            sku_id=final_boost["sku_id"],
            customer_id=final_boost["customer_id"],
            location_id=final_boost["location_id"],
            as_of_date=final_boost["as_of_date"],
            attempt=message.attempt,
            final_boost=final_boost,
            final_forecast=final_forecast,
            reasoning=reasoning,
            reasoning_source=reasoning_source,
            executed_steps=executed_steps,
        )


class DemandCriticAgent(RoutedAgent):
    """
    Demand Critic:
    - evaluates if total boost exceeds thresholds
    - checks tool execution health
    - decides: rerun vs human approval vs ok
    """

    def __init__(self, *, enable_llm: bool = True) -> None:
        super().__init__(description="Demand Critic agent (deterministic reviewer + optional LLM reasoning)")
        self._llm_client = build_reasoning_client(prefer="google") if enable_llm else None

    def _template_reasoning(self, review: Dict[str, Any]) -> str:
        decision = review.get("decision")
        outside = review.get("outside_thresholds")
        rerun = review.get("rerun_recommendations") or []
        return f"Critic: outside_thresholds={outside}; decision={decision}; rerun_recommendations={rerun}."

    @message_handler
    async def on_review_request(self, message: CriticReviewRequest, ctx: MessageContext) -> CriticReviewResult:
        review = critic_review_consensus_demand_boost(
            sku_id=message.sku_id,
            customer_id=message.customer_id,
            location_id=message.location_id,
            as_of_date=message.as_of_date,
            upper_threshold=message.upper_threshold,
            lower_threshold=message.lower_threshold,
        )
        if self._llm_client is None:
            reasoning = self._template_reasoning(review)
        else:
            system = (
                "You are a demand planning QA critic. Explain threshold evaluation and tool health checks. "
                "Be concise and action-oriented."
            )
            user = (
                f"Review payload:\n{review}\n\n"
                "Explain: (1) threshold result, (2) tool health, (3) next action. 4-6 bullets."
            )
            try:
                reasoning = await self._llm_client.generate(system=system, user=user)
            except Exception:
                reasoning = self._template_reasoning(review)
        return CriticReviewResult(
            sku_id=review["sku_id"],
            customer_id=review["customer_id"],
            location_id=review["location_id"],
            as_of_date=review["as_of_date"],
            attempt=message.attempt,
            review=review,
            reasoning=reasoning,
        )


# ----------------------------
# Agent IDs (conventions)
# ----------------------------

ACTOR_AGENT_ID = AgentId("demand_actor", "v1")
CRITIC_AGENT_ID = AgentId("demand_critic", "v1")


