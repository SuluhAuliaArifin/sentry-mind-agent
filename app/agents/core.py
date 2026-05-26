"""Autonomous agent core loop: Observe → Analyze → Decide → Act → Save Memory."""
from __future__ import annotations
import asyncio
import logging
from datetime import datetime

from sqlalchemy.orm import Session

from app.database.db import SessionLocal
from app.database.models import Target, Scan, Finding, Analysis, Action
from app.tools.http_checker import check_http
from app.tools.ssl_checker import check_ssl
from app.tools.git_checker import check_git_exposed
from app.tools.headers_checker import check_headers
from app.ai.analyzer import analyze
from app.actions.alerts import decide
from app.actions.reports import build_report, report_hash
from app.actions.telegram import send_alert
from app.blockchain.solana_proof import anchor_hash

logger = logging.getLogger(__name__)


# ---------- OBSERVE ----------
async def observe(url: str) -> dict:
    http_task = check_http(url)
    git_task = check_git_exposed(url)
    headers_task = check_headers(url)
    # ssl is sync (stdlib), run in thread to keep loop responsive
    ssl_task = asyncio.to_thread(check_ssl, url)
    http, ssl_, git, headers = await asyncio.gather(
        http_task, ssl_task, git_task, headers_task, return_exceptions=True
    )
    return {
        "http":    http    if not isinstance(http, Exception)    else {"error": str(http)},
        "ssl":     ssl_    if not isinstance(ssl_, Exception)    else {"error": str(ssl_)},
        "git":     git     if not isinstance(git, Exception)     else {"error": str(git)},
        "headers": headers if not isinstance(headers, Exception) else {"error": str(headers)},
    }


# ---------- ANALYZE ----------
def _flatten_findings(raw: dict) -> list[dict]:
    out: list[dict] = []
    http = raw.get("http") or {}
    if http.get("error"):
        out.append({"check": "http", "severity": "HIGH",
                    "title": f"HTTP error: {http['error']}", "detail": http.get("url", ""),
                    "data": http})
    elif http.get("status") and http["status"] >= 400:
        out.append({"check": "http", "severity": "MEDIUM" if http["status"] < 500 else "HIGH",
                    "title": f"HTTP {http['status']}", "detail": http.get("final_url", ""),
                    "data": http})

    ssl_ = raw.get("ssl") or {}
    if ssl_.get("expired"):
        out.append({"check": "ssl", "severity": "CRITICAL",
                    "title": "TLS certificate expired",
                    "detail": f"expired on {ssl_.get('not_after')}", "data": ssl_})
    elif ssl_.get("error") and ssl_["error"] != "not_https":
        out.append({"check": "ssl", "severity": "HIGH",
                    "title": "TLS handshake/validation failed",
                    "detail": ssl_["error"], "data": ssl_})
    elif isinstance(ssl_.get("days_left"), int) and ssl_["days_left"] < 30:
        sev = "HIGH" if ssl_["days_left"] < 14 else "MEDIUM"
        out.append({"check": "ssl", "severity": sev,
                    "title": f"TLS expires in {ssl_['days_left']} days",
                    "detail": ssl_.get("not_after", ""), "data": ssl_})

    git = raw.get("git") or {}
    if git.get("exposed"):
        out.append({"check": "git", "severity": "CRITICAL",
                    "title": "Exposed .git directory",
                    "detail": (git.get("evidence") or "")[:200], "data": git})

    headers = raw.get("headers") or {}
    for m in headers.get("missing", []):
        out.append({"check": "headers", "severity": m["severity"],
                    "title": m["message"], "detail": m["header"], "data": m})
    return out


# ---------- DECIDE + ACT ----------
def _previous_severity(db: Session, target_id: int, before_id: int) -> str | None:
    prev = (db.query(Scan)
            .filter(Scan.target_id == target_id, Scan.id < before_id, Scan.status == "done")
            .order_by(Scan.id.desc()).first())
    return prev.severity if prev else None


def _findings_signature(findings: list[dict]) -> str:
    """Stable signature for diffing: severity:check:title sorted."""
    keys = sorted(f"{f['severity']}|{f['check']}|{f['title']}" for f in findings)
    return "\n".join(keys)


def _previous_signature(db: Session, target_id: int, before_id: int) -> str | None:
    prev = (db.query(Scan)
            .filter(Scan.target_id == target_id, Scan.id < before_id, Scan.status == "done")
            .order_by(Scan.id.desc()).first())
    if not prev:
        return None
    return _findings_signature([{
        "severity": f.severity, "check": f.check, "title": f.title
    } for f in prev.findings])


# ---------- MAIN ENTRY ----------
async def run_scan_for_target(target_id: int) -> int:
    """Run full agent cycle for one target. Returns scan id."""
    db = SessionLocal()
    try:
        target = db.get(Target, target_id)
        if not target or not target.enabled:
            raise ValueError(f"target {target_id} missing or disabled")

        scan = Scan(target_id=target.id, status="running", created_at=datetime.utcnow())
        db.add(scan); db.commit(); db.refresh(scan)

        # 1. OBSERVE
        raw = await observe(target.url)
        scan.raw = raw

        # 2. flatten findings + 3. ANALYZE (rules + AI)
        findings = _flatten_findings(raw)
        for f in findings:
            db.add(Finding(scan_id=scan.id, **f))

        result = analyze(raw)
        scan.severity = result.severity
        scan.summary = result.summary
        db.add(Analysis(scan_id=scan.id, severity=result.severity,
                        reasoning=result.reasoning, risk=result.risk,
                        mitigation=result.mitigation, model=result.model))
        scan.status = "done"
        db.commit()
        db.refresh(scan)

        # 4. DECIDE
        prev_sig = _previous_signature(db, target.id, scan.id)
        curr_sig = _findings_signature(findings)
        changed = (prev_sig is not None) and (prev_sig != curr_sig)
        prev_sev = _previous_severity(db, target.id, scan.id)
        decision = decide(scan.severity, changed, prev_sev)
        logger.info("decision for %s: %s — %s", target.url, decision, decision.reason)

        # 5. ACT
        if decision.generate_report:
            report_md = build_report(scan)
            h = report_hash(report_md)
            db.add(Action(scan_id=scan.id, kind="report", status="ok",
                          detail=f"sha256={h}"))
            if decision.anchor_onchain:
                ok, msg = anchor_hash(h)
                db.add(Action(scan_id=scan.id, kind="solana_proof",
                              status="ok" if ok else "skipped", detail=msg))

        if decision.notify:
            text = (f"<b>[{scan.severity}]</b> {target.url}\n"
                    f"{scan.summary}\n— autonomous AI security agent")
            ok, msg = await send_alert(text)
            db.add(Action(scan_id=scan.id, kind="telegram",
                          status="ok" if ok else "skipped", detail=msg))

        db.commit()
        return scan.id
    except Exception as e:
        logger.exception("scan failed for target %s: %s", target_id, e)
        if 'scan' in locals():
            scan.status = "error"
            scan.summary = f"scan error: {e}"
            db.commit()
        raise
    finally:
        db.close()


async def run_all_enabled() -> list[int]:
    db = SessionLocal()
    try:
        ids = [t.id for t in db.query(Target).filter(Target.enabled.is_(True)).all()]
    finally:
        db.close()
    results = []
    for tid in ids:
        try:
            results.append(await run_scan_for_target(tid))
        except Exception:
            continue
    return results
