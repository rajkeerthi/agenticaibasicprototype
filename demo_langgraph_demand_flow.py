"""
Micro-step demo:
- Build LangGraph demand flow (Actor -> Critic -> route)
- Run for 3 dates to show 3 scenarios

Run:
  venv/bin/python -m prototype2_demand_supply.demo_langgraph_demand_flow
"""

from __future__ import annotations

import asyncio
import json

from prototype2_demand_supply.graph.demand_flow import build_demand_flow_graph


async def main() -> None:
    graph = build_demand_flow_graph()

    for d in ["2026-01-01", "2026-01-02", "2026-01-03"]:
        state = {
            "sku_id": "PONDS_SUPER_LIGHT_GEL_100G",
            "customer_id": "BLINKIT",
            "location_id": "BANGALORE",
            "as_of_date": d,
            "upper_threshold": 0.30,
            "lower_threshold": -0.20,
            "max_retries": 2,
            "attempt": 1,
            "user_query": "Please compute final demand forecast and explain the boost drivers.",
        }
        out = await graph.ainvoke(state)
        print("\n=== Date:", d, "===")
        print(
            json.dumps(
                {
                    "selected_sku": out.get("sku_id"),
                    "final_total_boost_percent": out.get("actor_result", {}).get("total_boost_percent"),
                    "final_demand_forecast": out.get("actor_forecast", {}).get("final_demand_forecast"),
                    "critic_decision": out.get("critic_result", {}).get("decision"),
                    "next_action": out.get("critic_result", {}).get("next_action"),
                    "history": out.get("history", []),
                },
                indent=2,
            )
        )

        print("\nActor reasoning:")
        print(out.get("actor_reasoning", ""))

        print("\nCritic reasoning:")
        print(out.get("critic_reasoning", ""))


if __name__ == "__main__":
    asyncio.run(main())


