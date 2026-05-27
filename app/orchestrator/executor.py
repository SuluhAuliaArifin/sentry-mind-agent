# app/orchestrator/executor.py

from app.services.ace import AceDataClient
from app.core.rpc import SynapseRPC
from app.core.sentinel import execute_sentinel

ace = AceDataClient()
rpc = SynapseRPC()


def execute_task(plan: dict):
    results = {
        "task": plan["task"],
        "executions": []
    }

    # 🔵 ACE LAYER
    if "ace_analysis" in plan["strategy"]:
        ace_result = ace.enforce_multi_api(plan["task"])
        results["executions"].append({
            "type": "ace",
            "data": ace_result
        })

    # 🔵 RPC LAYER
    if "rpc_balance_check" in plan["strategy"]:
        rpc_result = rpc.get_balance("demo-wallet")
        results["executions"].append({
            "type": "rpc",
            "data": rpc_result
        })

    # 🔵 SENTINEL LAYER
    if "sentinel_execution" in plan["strategy"]:
        sentinel_result = execute_sentinel(plan)
        results["executions"].append({
            "type": "sentinel",
            "data": sentinel_result
        })

    return results