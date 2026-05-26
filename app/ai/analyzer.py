"""AI reasoning layer.

Design:
- Deterministic severity rules first (hard ground truth from raw findings).
- LLM only writes human-readable reasoning + mitigation, constrained by JSON schema.
- LLM cannot escalate severity beyond what rules detected (mitigates hallucination).

Returns AnalysisResult that always validates.
"""
from __future__ import annotations
import json
import logging
from typing import Literal
from pydantic import BaseModel, Field, ValidationError

from app.config import settings

logger = logging.getLogger(__name__)

Severity = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
_SEV_RANK = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}


class AnalysisResult(BaseModel):
    severity: Severity = "LOW"
    summary: str = Field(default="", max_length=400)
    reasoning: str = Field(default="", max_length=2000)
    risk: str = Field(default="", max_length=1000)
    mitigation: str = Field(default="", max_length=1500)
    model: str = ""


# ----- deterministic rules -----

def derive_severity(raw: dict) -> tuple[Severity, list[str]]:
    """Compute severity floor from raw scan data and return supporting reasons."""
    sev: Severity = "LOW"
    reasons: list[str] = []

    def bump(level: Severity, why: str):
        nonlocal sev
        if _SEV_RANK[level] > _SEV_RANK[sev]:
            sev = level
        reasons.append(f"[{level}] {why}")

    http = raw.get("http") or {}
    ssl_ = raw.get("ssl") or {}
    git = raw.get("git") or {}
    headers = raw.get("headers") or {}

    # HTTP
    if http.get("error") or (http.get("status") and http["status"] >= 500):
        bump("HIGH", f"site unreachable or 5xx ({http.get('error') or http.get('status')})")
    elif http.get("status") and http["status"] >= 400:
        bump("MEDIUM", f"client error response {http['status']}")

    # SSL
    if ssl_.get("expired"):
        bump("CRITICAL", "TLS certificate expired")
    elif ssl_.get("error") and ssl_["error"] != "not_https":
        bump("HIGH", f"TLS issue: {ssl_['error']}")
    elif isinstance(ssl_.get("days_left"), int) and ssl_["days_left"] < 14:
        bump("HIGH", f"TLS expires in {ssl_['days_left']} days")
    elif isinstance(ssl_.get("days_left"), int) and ssl_["days_left"] < 30:
        bump("MEDIUM", f"TLS expires in {ssl_['days_left']} days")

    # Git
    if git.get("exposed"):
        bump("CRITICAL", "exposed .git directory — source code leak")

    # Headers
    for m in headers.get("missing", []):
        bump(m["severity"], f"missing header {m['header']}")

    return sev, reasons


# ----- LLM enrichment -----

_PROMPT = """You are a senior application security analyst. You will receive raw
results from automated security scans of a single website. Produce a concise,
professional analysis. NEVER invent vulnerabilities that are not evidenced in the
input. Use only the provided data.

Return STRICT JSON matching this schema:
{{
  "summary": "one sentence, <= 200 chars",
  "reasoning": "2-4 sentences explaining what was found and why it matters",
  "risk": "concrete business/security impact",
  "mitigation": "actionable steps, numbered"
}}

The deterministic severity is: {severity}
Supporting findings:
{reasons}

Raw scan JSON:
{raw}
"""


def _call_gemini(prompt: str) -> dict | None:
    if not settings.gemini_api_key:
        return None
    try:
        import google.generativeai as genai
        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel(
            settings.gemini_model,
            generation_config={"response_mime_type": "application/json"},
        )
        resp = model.generate_content(prompt)
        text = (resp.text or "").strip()
        return json.loads(text)
    except Exception as e:  # noqa: BLE001 — never let AI failure break the agent
        logger.warning("gemini call failed: %s", e)
        return None


def analyze(raw: dict) -> AnalysisResult:
    severity, reasons = derive_severity(raw)
    prompt = _PROMPT.format(
        severity=severity,
        reasons="\n".join(f"- {r}" for r in reasons) or "- none",
        raw=json.dumps(raw, default=str)[:4000],
    )
    llm = _call_gemini(prompt)
    if llm:
        try:
            partial = AnalysisResult(severity=severity, model=settings.gemini_model, **{
                k: v for k, v in llm.items()
                if k in {"summary", "reasoning", "risk", "mitigation"}
            })
            return partial
        except ValidationError as e:
            logger.warning("llm json invalid: %s", e)

    # Fallback: deterministic text only
    return AnalysisResult(
        severity=severity,
        summary=f"{severity} severity — {len(reasons)} finding(s)",
        reasoning="\n".join(reasons) or "No issues detected.",
        risk="See findings above.",
        mitigation="Address each finding listed in the reasoning section.",
        model="rules-only",
    )
