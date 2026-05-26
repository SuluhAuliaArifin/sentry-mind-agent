from app.ai.analyzer import derive_severity


def test_clean_scan_is_low():
    sev, _ = derive_severity({
        "http": {"status": 200, "ok": True},
        "ssl": {"ok": True, "days_left": 200, "expired": False},
        "git": {"exposed": False},
        "headers": {"missing": []},
    })
    assert sev == "LOW"


def test_expired_ssl_is_critical():
    sev, reasons = derive_severity({"ssl": {"expired": True}})
    assert sev == "CRITICAL"
    assert any("expired" in r.lower() for r in reasons)


def test_exposed_git_is_critical():
    sev, _ = derive_severity({"git": {"exposed": True}})
    assert sev == "CRITICAL"


def test_missing_hsts_bumps_to_high():
    sev, _ = derive_severity({
        "headers": {"missing": [{"header": "strict-transport-security",
                                  "severity": "HIGH", "message": "x"}]}
    })
    assert sev == "HIGH"


def test_5xx_is_high():
    sev, _ = derive_severity({"http": {"status": 503}})
    assert sev == "HIGH"
