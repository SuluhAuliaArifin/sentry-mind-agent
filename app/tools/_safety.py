"""SSRF / input sanitization helpers shared by all checkers."""
from urllib.parse import urlparse, urlunparse
import ipaddress
import socket

from app.config import settings


class UnsafeTargetError(ValueError):
    pass


def normalize_url(raw: str) -> str:
    """Return a normalized https/http URL or raise UnsafeTargetError.

    - Allow only schemes in settings.allowed_schemes.
    - Reject empty host, userinfo, non-default suspicious ports left to caller.
    - We intentionally allow private IPs to be PRESENT in the URL but resolution is
      checked separately via assert_public_host() before HTTP calls if needed.
    """
    if not raw or not isinstance(raw, str):
        raise UnsafeTargetError("empty target")
    raw = raw.strip()
    if "://" not in raw:
        raw = "https://" + raw
    p = urlparse(raw)
    if p.scheme.lower() not in settings.allowed_schemes_list:
        raise UnsafeTargetError(f"scheme not allowed: {p.scheme}")
    if not p.hostname:
        raise UnsafeTargetError("missing host")
    if p.username or p.password:
        raise UnsafeTargetError("userinfo not allowed")
    # Strip fragment, keep path/query
    return urlunparse((p.scheme.lower(), p.netloc, p.path or "/", "", p.query, ""))


def host_of(url: str) -> str:
    return urlparse(url).hostname or ""


def assert_public_host(url: str) -> None:
    """Resolve host and reject loopback/private/link-local. Call before scanning
    untrusted user-supplied URLs in production. For an MVP we keep it best-effort."""
    host = host_of(url)
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror as e:
        raise UnsafeTargetError(f"dns resolution failed: {e}") from e
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
            raise UnsafeTargetError(f"host resolves to non-public IP: {ip}")
