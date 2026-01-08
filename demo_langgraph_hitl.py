"""
Micro-step demo:
Human-in-the-loop (HITL) behavior in LangGraph.

We run once to reach approval_status=pending and print the approval_request.
Then we "resume" by providing human_decision=approve and run again to finalize.

Run (network needed for Gemini parsing + reasoning):
  venv/bin/python -m prototype2_demand_supply.demo_langgraph_hitl
"""

from __future__ import annotations

import asyncio
import json

from prototype2_demand_supply.graph.demand_flow import build_demand_flow_graph


async def main() -> None:
    graph = build_demand_flow_graph()

    # A request that typically triggers out-of-threshold approvals.
    user_query = (
        "For Bangalore Blinkit, compute final demand forecast for date 2026-01-03 for PONDS_SUPER_LIGHT_GEL_100G. "
        "Explain drivers and route for approval if needed."
    )

    state = {
        "sku_id": "AUTO",
        "user_query": user_query,
        "max_retries": 2,
    }

    print("\n=== Run 1 (expect pending approval) ===")
    out1 = await graph.ainvoke(state)
    print("approval_status:", out1.get("approval_status"))
    print("finalized:", out1.get("finalized"))
    print("decision:", (out1.get("critic_result") or {}).get("decision"))
    print("\napproval_request:")
    print(json.dumps(out1.get("approval_request", {}), indent=2))

    if out1.get("approval_status") != "pending":
        print("\nUnexpected: did not stop at pending. Exiting.")
        return

    print("\n=== Run 2 (resume with approve) ===")
    out2_state = dict(out1)
    out2_state["human_decision"] = "approve"
    out2 = await graph.ainvoke(out2_state)
    print("approval_status:", out2.get("approval_status"))
    print("finalized:", out2.get("finalized"))
    print("results:", json.dumps(out2.get("results", []), indent=2))


if __name__ == "__main__":
    asyncio.run(main())



