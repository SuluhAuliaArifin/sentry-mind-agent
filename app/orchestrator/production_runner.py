# app/orchestrator/production_runner.py

from app.orchestrator.loop_engine import run_autonomous_loop
from app.core.memory_store import MemoryStore
from app.utils.audit_logger import AuditLogger
from app.core.recovery import RecoveryEngine

memory = MemoryStore()
logger = AuditLogger()
recovery = RecoveryEngine()


def run_production_agent(task: str):
    logger.log("TASK_RECEIVED", task)

    def execute():
        return run_autonomous_loop(task)

    result = recovery.retry(execute)

    memory.append("executions", result)
    logger.log("TASK_COMPLETED", result)

    return {
        "status": "production_complete",
        "result": result
    }