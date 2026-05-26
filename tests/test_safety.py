import pytest
from app.tools._safety import normalize_url, UnsafeTargetError


def test_adds_https():
    assert normalize_url("example.com").startswith("https://")


def test_rejects_userinfo():
    with pytest.raises(UnsafeTargetError):
        normalize_url("https://user:pass@example.com")


def test_rejects_unknown_scheme():
    with pytest.raises(UnsafeTargetError):
        normalize_url("ftp://example.com")


def test_rejects_empty():
    with pytest.raises(UnsafeTargetError):
        normalize_url("")
