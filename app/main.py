"""FastAPI app: dashboard + API + autonomous agent lifecycle."""

from __future__ import annotations
import logging
import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, Form, HTTPException, Depends, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config import settings
from app.database.db import init_db, get_db
from app.database.models import Target, Scan
from app.tools._safety import normalize_url, UnsafeTargetError
from app.agents.core import run_scan_for_target
from app.actions.reports import build_report
from app.scheduler.jobs import start_scheduler, shutdown_scheduler
from app.agents.autonomous import engine

# =========================
# LOGGING
# =========================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s | %(message)s"
)
logger = logging.getLogger("agent")

# =========================
# PATH & TEMPLATE
# =========================
BASE_DIR = Path(__file__).parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# =========================
# LIFESPAN (CORE FIX)
# =========================
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    start_scheduler()

    # 🚀 AUTONOMOUS ENGINE START (ONLY ONCE)
    asyncio.create_task(engine.run())

    logger.info("agent online — env=%s", settings.app_env)

    yield

    shutdown_scheduler()

# =========================
# FASTAPI APP INIT
# =========================
app = FastAPI(
    title="Autonomous AI Security Monitoring Agent",
    lifespan=lifespan
)

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")