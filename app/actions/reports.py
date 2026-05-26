"""Markdown report generator. Pure function — output stored in DB or written to disk."""
from __future__ import annotations
import hashlib
from datetime import datetime

from app.database.models import Scan


def build_report(scan: Scan) -> str:
    a = scan.analysis
    lines = [
        f"# Security Report — {scan.target.url}",
        f"_Generated: {datetime.utcnow().isoformat()}Z_",
        "",
        f"**Severity:** `{scan.severity}`",
        f"**Summary:** {scan.summary}",
        "",
        "## AI Analysis",
        f"**Reasoning:** {a.reasoning if a else '-'}",
        "",
        f"**Risk:** {a.risk if a else '-'}",
        "",
        f"**Mitigation:**\n{a.mitigation if a else '-'}",
        "",
        "## Findings",
    ]
    for f in scan.findings:
        lines.append(f"- **[{f.severity}] {f.check}** — {f.title}")
        if f.detail:
            lines.append(f"  > {f.detail}")
    lines.append("")
    lines.append(f"_Model: {a.model if a else 'n/a'}_")
    return "\n".join(lines)


def report_hash(report_md: str) -> str:
    return hashlib.sha256(report_md.encode("utf-8")).hexdigest()
