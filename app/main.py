"""FastAPI app: dashboard (Jinja+HTMX) + JSON API + lifecycle hooks."""
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
from app.agents.brain import AgentBrain
from app.actions.reports import build_report
from app.scheduler.jobs import start_scheduler, shutdown_scheduler
from app.orchestrator.agent_runner import run_agent
from app.orchestrator.production_runner import run_production_agent


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s | %(message)s"
)
logger = logging.getLogger("agent")

BASE_DIR = Path(__file__).parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    start_scheduler()
    logger.info("agent online — env=%s", settings.app_env)
    yield
    shutdown_scheduler()


app = FastAPI(
    title="Autonomous AI Security Monitoring Agent",
    lifespan=lifespan
)

app.mount(
    "/static",
    StaticFiles(directory=str(BASE_DIR / "static")),
    name="static"
)


# =========================
# AGENT EXECUTION ROUTES
# =========================

@app.post("/agent/run")
def run_agent_route(payload: dict):
    task = payload.get("task", "")
    return run_agent(task)


@app.post("/agent/run-production")
def run_production_route(payload: dict):
    task = payload.get("task", "")
    return run_production_agent(task)


# =========================
# PAGES (JINJA)
# =========================

@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    targets = db.query(Target).order_by(Target.id.desc()).all()

    rows = []
    for t in targets:
        last = (
            db.query(Scan)
            .filter(Scan.target_id == t.id)
            .order_by(Scan.id.desc())
            .first()
        )
        rows.append({"t": t, "last": last})

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "rows": rows,
        "interval": settings.scan_interval_minutes,
        "ai_enabled": bool(settings.gemini_api_key),
    })


@app.get("/scans/{scan_id}", response_class=HTMLResponse)
def scan_detail(scan_id: int, request: Request, db: Session = Depends(get_db)):
    scan = db.get(Scan, scan_id)
    if not scan:
        raise HTTPException(404)

    return templates.TemplateResponse(
        "scan_detail.html",
        {"request": request, "scan": scan}
    )


@app.get("/scans/{scan_id}/report", response_class=PlainTextResponse)
def scan_report(scan_id: int, db: Session = Depends(get_db)):
    scan = db.get(Scan, scan_id)
    if not scan:
        raise HTTPException(404)

    return build_report(scan)


# =========================
# ACTIONS
# =========================

@app.post("/targets", response_class=HTMLResponse)
def add_target(
    request: Request,
    url: str = Form(...),
    label: str = Form(""),
    db: Session = Depends(get_db)
):
    try:
        normalized = normalize_url(url)
    except UnsafeTargetError as e:
        raise HTTPException(400, str(e))

    existing = db.query(Target).filter(Target.url == normalized).first()

    if existing:
        target = existing
    else:
        target = Target(url=normalized, label=label[:128])
        db.add(target)
        db.commit()
        db.refresh(target)

    targets = db.query(Target).order_by(Target.id.desc()).all()

    rows = []
    for t in targets:
        last = (
            db.query(Scan)
            .filter(Scan.target_id == t.id)
            .order_by(Scan.id.desc())
            .first()
        )
        rows.append({"t": t, "last": last})

    return templates.TemplateResponse(
        "_targets_table.html",
        {"request": request, "rows": rows}
    )


@app.post("/targets/{target_id}/scan")
async def trigger_scan(
    target_id: int,
    background: BackgroundTasks,
    db: Session = Depends(get_db)
):
    target = db.get(Target, target_id)
    if not target:
        raise HTTPException(404)

    asyncio.create_task(run_scan_for_target(target_id))

    return JSONResponse({"ok": True, "queued": target_id})


@app.post("/targets/{target_id}/toggle")
def toggle_target(target_id: int, db: Session = Depends(get_db)):
    target = db.get(Target, target_id)
    if not target:
        raise HTTPException(404)

    target.enabled = not target.enabled
    db.commit()

    return {"ok": True, "enabled": target.enabled}


@app.delete("/targets/{target_id}")
def delete_target(target_id: int, db: Session = Depends(get_db)):
    target = db.get(Target, target_id)
    if not target:
        raise HTTPException(404)

    db.delete(target)
    db.commit()

    return {"ok": True}


# =========================
# JSON API
# =========================

@app.get("/api/health")
def health():
    return {"ok": True, "env": settings.app_env}


@app.get("/api/targets")
def api_targets(db: Session = Depends(get_db)):
    targets = db.query(Target).all()

    return [
        {
            "id": t.id,
            "url": t.url,
            "label": t.label,
            "enabled": t.enabled
        }
        for t in targets
    ]


@app.get("/api/scans/{scan_id}")
def api_scan(scan_id: int, db: Session = Depends(get_db)):
    s = db.get(Scan, scan_id)
    if not s:
        raise HTTPException(404)

    return {
        "id": s.id,
        "target": s.target.url,
        "status": s.status,
        "severity": s.severity,
        "summary": s.summary,
        "created_at": s.created_at.isoformat(),
        "raw": s.raw,
        "findings": [
            {
                "check": f.check,
                "severity": f.severity,
                "title": f.title,
                "detail": f.detail
            }
            for f in s.findings
        ],
        "analysis": (
            {
                "reasoning": s.analysis.reasoning,
                "risk": s.analysis.risk,
                "mitigation": s.analysis.mitigation,
                "model": s.analysis.model
            }
            if s.analysis else None
        ),
        "actions": [
            {
                "kind": a.kind,
                "status": a.status,
                "detail": a.detail
            }
            for a in s.actions
        ],
    }


# =========================
# AUTONOMOUS AGENT DEMO
# =========================

@app.post("/agent/decide/{target_id}")
async def agent_decide(target_id: int, db: Session = Depends(get_db)):
    try:
        target = db.get(Target, target_id)
        if not target:
            raise HTTPException(404, "Target not found")

        brain = AgentBrain()

        tools = [
            "sap_web_scanner",
            "sap_vuln_analyzer",
            "ace_ai_inspector"
        ]

        decision = brain.decide(
            target={
                "id": target.id,
                "url": target.url
            },
            tools=tools
        )

        logger.info(f"[BRAIN] decision: {decision}")

        return {
            "status": "ok",
            "mode": "agent-decision",
            "decision": decision
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"agent_decide failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agent/run/{target_id}")
async def run_agent_direct(target_id: int, db: Session = Depends(get_db)):
    try:
        target = db.get(Target, target_id)
        if not target:
            raise HTTPException(404, "Target not found")

        logger.info(f"[AGENT] target resolved: {target_id}")
        logger.info(f"[AGENT] execution started")

        result = await run_scan_for_target(target_id)

        return {
            "status": "ok",
            "mode": "direct-agent-run",
            "target_id": target_id,
            "result": result
        }

    except Exception as e:
        logger.error(f"agent run failed: {str(e)}")
        raise HTTPException(500, str(e))