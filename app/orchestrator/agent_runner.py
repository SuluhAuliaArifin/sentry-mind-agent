# app/orchestrator/agent_runner.py

from app.orchestrator.planner import plan_task
from app.orchestrator.executor import execute_task
from app.orchestrator.verifier import verify_result


def run_agent(task: str):
    """
    Full agent pipeline:
    plan → execute → verify
    """

    plan = plan_task(task)
    execution = execute_task(plan)
    verified = verify_result(execution)

    return verified