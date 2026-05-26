"""Security headers audit. Returns missing + weak headers with per-header severity."""
from __future__ import annotations
import httpx

from app.config import settings
from app.tools._safety import normalize_url

# header -> (required, severity_if_missing, short_explanation)
SECURITY_HEADERS = {
    "strict-transport-security": (True, "HIGH", "HSTS missing — MITM/downgrade risk"),
    "content-security-policy":   (True, "HIGH", "CSP missing — XSS/data injection risk"),
    "x-content-type-options":    (True, "MEDIUM", "Missing X-Content-Type-Options: nosniff"),
    "x-frame-options":           (False, "MEDIUM", "Missing X-Frame-Options — clickjacking risk"),
    "referrer-policy":           (False, "LOW", "Referrer-Policy not set"),
    "permissions-policy":        (False, "LOW", "Permissions-Policy not set"),
}


async def check_headers(target: str) -> dict:
    url = normalize_url(target)
    out: dict = {"url": url, "missing": [], "present": {}, "error": None}
    try:
        async with httpx.AsyncClient(
            timeout=settings.http_timeout_seconds, follow_redirects=True,
            headers={"User-Agent": "AISecAgent/1.0"}
        ) as client:
            r = await client.get(url)
    except httpx.HTTPError as e:
        out["error"] = f"http_error: {e.__class__.__name__}"
        return out

    lower = {k.lower(): v for k, v in r.headers.items()}
    for h, (_req, sev, msg) in SECURITY_HEADERS.items():
        if h in lower:
            out["present"][h] = lower[h]
        else:
            out["missing"].append({"header": h, "severity": sev, "message": msg})
    return out
