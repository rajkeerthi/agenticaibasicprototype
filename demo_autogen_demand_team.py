"""
Micro-step demo:
- Spin up AutoGen runtime
- Send ActorRunRequest
- Send CriticReviewRequest

Run:
  venv/bin/python -m prototype2_demand_supply.demo_autogen_demand_team
"""

from __future__ import annotations

import asyncio
import json

from autogen_core import AgentId

from prototype2_demand_supply.agents.demand_team_agents import (
    ACTOR_AGENT_ID,
    CRITIC_AGENT_ID,
    ActorRunRequest,
    CriticReviewRequest,
)
from prototype2_demand_supply.agents.runtime import build_demand_team_runtime


async def main() -> None:
    runtime = await build_demand_team_runtime()
    runtime.start()
    try:
        # 1) Actor computes boosts
        actor_result = await runtime.send_message(
            ActorRunRequest(
                sku_id="PONDS_SUPER_LIGHT_GEL_100G",
                customer_id="BLINKIT",
                location_id="BANGALORE",
                as_of_date="2026-01-03",
                attempt=1,
            ),
            recipient=ACTOR_AGENT_ID,
        )

        # 2) Critic reviews thresholds + tool health
        critic_result = await runtime.send_message(
            CriticReviewRequest(
                sku_id="PONDS_SUPER_LIGHT_GEL_100G",
                customer_id="BLINKIT",
                location_id="BANGALORE",
                as_of_date="2026-01-03",
                upper_threshold=0.30,
                lower_threshold=-0.20,
                attempt=1,
            ),
            recipient=CRITIC_AGENT_ID,
        )

        print("=== Actor total boost ===")
        print(
            json.dumps(
                {
                    "as_of_date": actor_result.as_of_date,
                    "total_boost_percent": actor_result.final_boost["total_boost_percent"],
                    "raw_total_boost_percent": actor_result.final_boost["raw_total_boost_percent"],
                },
                indent=2,
            )
        )
        print("\n=== Critic decision ===")
        print(
            json.dumps(
                {
                    "outside_thresholds": critic_result.review["outside_thresholds"],
                    "decision": critic_result.review["decision"],
                    "next_action": critic_result.review["next_action"],
                    "rerun_recommendations": critic_result.review["rerun_recommendations"],
                },
                indent=2,
            )
        )

        print("\n=== Actor reasoning (template unless OPENAI_API_KEY configured) ===")
        print("source:", actor_result.reasoning_source)
        print(actor_result.reasoning)

        print("\n=== Critic reasoning (template unless OPENAI_API_KEY configured) ===")
        print(critic_result.reasoning)
    finally:
        await runtime.stop()


if __name__ == "__main__":
    asyncio.run(main())


