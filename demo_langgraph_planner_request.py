"""
Micro-step demo:
Natural language demand planner request -> parsed params -> multi-SKU LangGraph run.

Run (network needed for Gemini parsing):
  venv/bin/python -m prototype2_demand_supply.demo_langgraph_planner_request
"""

from __future__ import annotations

import asyncio
import json

from prototype2_demand_supply.graph.demand_flow import build_demand_flow_graph


async def main() -> None:
    graph = build_demand_flow_graph()

    user_query = (
        "For Bangalore Blinkit, run the final demand forecast for all A/Y SKUs for date 2026-01-03. "
        "Explain the boost drivers and tell me if it needs human approval."
    )

    state = {
        # Let parser select
        "sku_id": "AUTO",
        "user_query": user_query,
        "max_retries": 2,
    }

    out = await graph.ainvoke(state)

    print("\n=== Parsed + Multi-SKU Results ===\n")
    print("user_query:", user_query)
    print("customer_id:", out.get("customer_id"))
    print("location_id:", out.get("location_id"))
    print("as_of_date:", out.get("as_of_date"))
    print("scope:", out.get("scope"))
    print("sku_queue:", out.get("sku_queue"))
    print("\nresults_count:", len(out.get("results", [])))

    for r in out.get("results", []):
        print("\n--- SKU:", r.get("sku_id"), "---")
        af = (r.get("actor_forecast") or {})
        cr = (r.get("critic_result") or {})
        print(
            json.dumps(
                {
                    "baseline": af.get("baseline_forecast"),
                    "total_boost_percent": af.get("total_boost_percent"),
                    "final_demand_forecast": af.get("final_demand_forecast"),
                    "critic_decision": cr.get("decision"),
                    "next_action": cr.get("next_action"),
                    "rerun_recommendations": cr.get("rerun_recommendations"),
                },
                indent=2,
            )
        )
        print("\nActor reasoning:\n", (r.get("actor_reasoning") or ""))


if __name__ == "__main__":
    asyncio.run(main())



