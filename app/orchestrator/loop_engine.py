# app/orchestrator/loop_engine.py

from app.orchestrator.planner import plan_task
from app.orchestrator.executor import execute_task
from app.orchestrator.verifier import verify_result
from app.orchestrator.memory import AgentMemory

memory = AgentMemory()


def run_autonomous_loop(task: str, max_iterations: int = 3):
    """
    Core autonomous loop engine
    """

    memory.set("last_task", task)

    iteration = 0
    result = None

    while iteration < max_iterations:
        iteration += 1

        # 🧠 Planning phase
        plan = plan_task(task)

        # ⚙️ Execution phase
        execution = execute_task(plan)

        # 🔍 Verification phase
        verified = verify_result(execution)

        # 💾 store history
        memory.update("execution_history", {
            "iteration": iteration,
            "plan": plan,
            "result": verified
        })

        result = verified

        # 🧠 decision: stop or continue
        if verified["autonomy_score"] >= 0.8:
            break

        # refine task for next loop
        task = task + " improve accuracy"

    return {
        "final_result": result,
        "iterations": iteration,
        "memory": memory.store
    }