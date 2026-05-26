"""Decision engine: maps (severity, diff) -> list of actions to execute."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass
class Decision:
    notify: bool
    generate_report: bool
    anchor_onchain: bool
    reason: str


def decide(severity: str, changed: bool, prev_severity: str | None) -> Decision:
    notify = severity in {"HIGH", "CRITICAL"}
    report = changed or severity in {"HIGH", "CRITICAL"}
    anchor = severity == "CRITICAL"
    parts = [f"severity={severity}", f"changed={changed}", f"prev={prev_severity or 'n/a'}"]
    return Decision(notify=notify, generate_report=report, anchor_onchain=anchor,
                    reason=", ".join(parts))
