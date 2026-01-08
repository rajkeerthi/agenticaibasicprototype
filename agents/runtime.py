"""
AutoGen runtime bootstrap for local, deterministic runs.

We use SingleThreadedAgentRuntime to keep execution simple and easy to debug.
"""

from __future__ import annotations

from autogen_core import SingleThreadedAgentRuntime

from .demand_team_agents import (
    ACTOR_AGENT_ID,
    CRITIC_AGENT_ID,
    DemandActorAgent,
    DemandCriticAgent,
)


async def build_demand_team_runtime(*, enable_llm: bool = True) -> SingleThreadedAgentRuntime:
    runtime = SingleThreadedAgentRuntime()
    await runtime.register_agent_instance(DemandActorAgent(enable_llm=enable_llm), ACTOR_AGENT_ID)
    await runtime.register_agent_instance(DemandCriticAgent(enable_llm=enable_llm), CRITIC_AGENT_ID)
    return runtime


