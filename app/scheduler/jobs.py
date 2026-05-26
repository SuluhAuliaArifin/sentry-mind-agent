"""APScheduler glue. Runs the agent loop on a fixed interval."""
from __future__ import annotations
import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import settings
from app.agents.core import run_all_enabled

logger = logging.getLogger(__name__)
_scheduler: AsyncIOScheduler | None = None


async def _job():
    logger.info("scheduled scan tick")
    try:
        ids = await run_all_enabled()
        logger.info("scheduled scan complete: %d scans", len(ids))
    except Exception:
        logger.exception("scheduled scan crashed")


def start_scheduler() -> AsyncIOScheduler:
    global _scheduler
    if _scheduler:
        return _scheduler
    sched = AsyncIOScheduler(timezone="UTC")
    sched.add_job(
        _job, "interval", minutes=settings.scan_interval_minutes,
        id="agent_loop", coalesce=True, max_instances=1, next_run_time=None,
    )
    sched.start()
    _scheduler = sched
    logger.info("scheduler started: every %d min", settings.scan_interval_minutes)
    return sched


def shutdown_scheduler():
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None
