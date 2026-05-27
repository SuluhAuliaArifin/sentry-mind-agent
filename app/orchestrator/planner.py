# app/orchestrator/planner.py

def plan_task(task: str):
    """
    Generate execution plan dari input user.
    Ini masih rule-based (nanti bisa upgrade LLM planner)
    """

    task_lower = task.lower()

    plan = {
        "task": task,
        "requires_ace": True,
        "requires_rpc": False,
        "requires_sentinel": False,
        "strategy": [],
        "onchain": False
    }

    # =========================
    # ✅ RPC ROUTING
    # =========================
    if "balance" in task_lower or "wallet" in task_lower:
        plan["requires_rpc"] = True
        plan["strategy"].append("rpc_balance_check")

    # =========================
    # ✅ ACE ROUTING
    # =========================
    if "risk" in task_lower or "analyze" in task_lower:
        plan["strategy"].append("ace_analysis")

    # default ace jika kosong
    if not plan["strategy"]:
        plan["strategy"].append("ace_analysis")

    # =========================
    # ✅ EXECUTION / SENTINEL
    # =========================
    if "execute" in task_lower:
        plan["requires_sentinel"] = True
        plan["strategy"].append("sentinel_execution")
        plan["strategy"].append("chain_execution")
        plan["onchain"] = True

    return plan