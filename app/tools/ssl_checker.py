"""TLS certificate inspection. Pure stdlib ssl + socket, no external deps."""
from __future__ import annotations
import ssl
import socket
from datetime import datetime, timezone

from app.tools._safety import normalize_url, host_of


def _parse_cert_date(s: str) -> datetime:
    # e.g. "Jun 10 12:00:00 2026 GMT"
    return datetime.strptime(s, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)


def check_ssl(target: str, port: int = 443, timeout: int = 8) -> dict:
    url = normalize_url(target)
    host = host_of(url)
    out: dict = {"host": host, "ok": False, "error": None,
                 "issuer": None, "subject": None,
                 "not_before": None, "not_after": None, "days_left": None,
                 "expired": None}
    if not url.startswith("https://"):
        out["error"] = "not_https"
        return out
    ctx = ssl.create_default_context()
    try:
        with socket.create_connection((host, port), timeout=timeout) as sock:
            with ctx.wrap_socket(sock, server_hostname=host) as ssock:
                cert = ssock.getpeercert()
        not_after = _parse_cert_date(cert["notAfter"])
        not_before = _parse_cert_date(cert["notBefore"])
        days_left = (not_after - datetime.now(timezone.utc)).days
        out.update(
            ok=True,
            issuer=dict(x[0] for x in cert.get("issuer", [])),
            subject=dict(x[0] for x in cert.get("subject", [])),
            not_before=not_before.isoformat(),
            not_after=not_after.isoformat(),
            days_left=days_left,
            expired=days_left < 0,
        )
    except ssl.SSLCertVerificationError as e:
        out["error"] = f"cert_verify_failed: {e.verify_message}"
    except (socket.timeout, TimeoutError):
        out["error"] = "timeout"
    except OSError as e:
        out["error"] = f"network_error: {e.__class__.__name__}"
    except Exception as e:  # last-resort defensive
        out["error"] = f"unexpected: {e.__class__.__name__}"
    return out
