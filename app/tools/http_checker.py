"""Basic HTTP reachability + response shape check."""
from __future__ import annotations
import time
import httpx

from app.config import settings
from app.tools._safety import normalize_url


async def check_http(target: str) -> dict:
    url = normalize_url(target)
    out: dict = {"url": url, "ok": False, "status": None, "latency_ms": None,
                 "error": None, "redirects": 0}
    t0 = time.perf_counter()
    try:
        async with httpx.AsyncClient(
            timeout=settings.http_timeout_seconds, follow_redirects=True, max_redirects=5,
            headers={"User-Agent": "AISecAgent/1.0 (+https://example.local)"}
        ) as client:
            r = await client.get(url)
            out["status"] = r.status_code
            out["redirects"] = len(r.history)
            out["final_url"] = str(r.url)
            out["ok"] = r.status_code < 500
    except httpx.TimeoutException:
        out["error"] = "timeout"
    except httpx.HTTPError as e:
        out["error"] = f"http_error: {e.__class__.__name__}"
    finally:
        out["latency_ms"] = int((time.perf_counter() - t0) * 1000)
    return out
