"""
LLM demo (micro-step):
Run the Actor agent once and print the reasoning output.

This will use Gemini if GOOGLE_API_KEY is set, with model default gemini-2.5-pro.

Run:
  venv/bin/python -m prototype2_demand_supply.demo_llm_actor_reasoning
"""

from __future__ import annotations

import asyncio

from prototype2_demand_supply.agents.demand_team_agents import ACTOR_AGENT_ID, ActorRunRequest
from prototype2_demand_supply.agents.runtime import build_demand_team_runtime


async def main() -> None:
    runtime = await build_demand_team_runtime(enable_llm=True)
    runtime.start()
    try:
        result = await runtime.send_message(
            ActorRunRequest(
                sku_id="PONDS_SUPER_LIGHT_GEL_100G",
                customer_id="BLINKIT",
                location_id="BANGALORE",
                as_of_date="2026-01-03",
                user_query=(
                    "I am a demand planner. Explain why the demand boost is negative today and give the final demand "
                    "forecast. Keep it short and actionable."
                ),
            ),
            recipient=ACTOR_AGENT_ID,
        )

        print("reasoning_source:", result.reasoning_source)
        print("\n=== Actor reasoning ===\n")
        print(result.reasoning)
        print("\n=== Numbers ===")
        print("baseline:", result.final_forecast.get("baseline_forecast"))
        print("total_boost_percent:", result.final_forecast.get("total_boost_percent"))
        print("final_demand_forecast:", result.final_forecast.get("final_demand_forecast"))
    finally:
        await runtime.stop()


if __name__ == "__main__":
    asyncio.run(main())



