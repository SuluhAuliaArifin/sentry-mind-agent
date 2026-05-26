"""Detect exposed .git directories — classic high-severity misconfig."""
from __future__ import annotations
import httpx
from urllib.parse import urljoin

from app.config import settings
from app.tools._safety import normalize_url

GIT_PROBE_PATHS = ("/.git/HEAD", "/.git/config")
# A valid .git/HEAD typically starts with "ref: refs/" (symbolic) or contains a sha
_HEAD_SIGNATURES = ("ref: refs/", "ref:refs/")


async def check_git_exposed(target: str) -> dict:
    base = normalize_url(target)
    out: dict = {"url": base, "exposed": False, "evidence": None, "probes": []}
    async with httpx.AsyncClient(
        timeout=settings.http_timeout_seconds, follow_redirects=False,
        headers={"User-Agent": "AISecAgent/1.0"}
    ) as client:
        for path in GIT_PROBE_PATHS:
            probe = urljoin(base, path)
            entry = {"path": path, "status": None, "matched": False, "error": None}
            try:
                r = await client.get(probe)
                entry["status"] = r.status_code
                body = (r.text or "")[:512]
                if r.status_code == 200:
                    if path.endswith("HEAD") and any(s in body for s in _HEAD_SIGNATURES):
                        out["exposed"] = True
                        out["evidence"] = body.strip()
                        entry["matched"] = True
                    elif path.endswith("config") and "[core]" in body:
                        out["exposed"] = True
                        out["evidence"] = body.strip()
                        entry["matched"] = True
            except httpx.HTTPError as e:
                entry["error"] = e.__class__.__name__
            out["probes"].append(entry)
            if out["exposed"]:
                break
    return out
