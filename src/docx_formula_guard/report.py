from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import ScanResult


def _escape(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ").strip()


def render_markdown(result: ScanResult) -> str:
    counts = result.counts()
    lines = [
        "# Docx Formula Guard report",
        "",
        f"- Input: `{result.path}`",
        f"- Errors: {counts.get('error', 0)}",
        f"- Warnings: {counts.get('warning', 0)}",
        f"- Information: {counts.get('info', 0)}",
        "",
        "## Document metadata",
        "",
    ]

    if result.metadata:
        for key, value in sorted(result.metadata.items()):
            lines.append(f"- `{key}`: {_escape(value)}")
    else:
        lines.append("No metadata was collected.")

    lines.extend(["", "## Findings", ""])
    if not result.findings:
        lines.append("No configured issue was detected.")
    else:
        lines.extend(
            [
                "| Severity | Code | Source | Location | Excerpt | Message |",
                "|---|---|---|---|---|---|",
            ]
        )
        for finding in result.findings:
            lines.append(
                "| "
                + " | ".join(
                    [
                        _escape(finding.severity),
                        _escape(finding.code),
                        _escape(finding.source),
                        _escape(finding.location),
                        _escape(finding.excerpt),
                        _escape(finding.message),
                    ]
                )
                + " |"
            )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "This is a read-only heuristic audit. A finding identifies a pattern to review; "
            "it does not prove that a formula is mathematically wrong or that conversion will fail.",
            "",
        ]
    )
    return "\n".join(lines)


def write_markdown(result: ScanResult, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_markdown(result), encoding="utf-8")
    return output


def write_json(result: ScanResult, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return output
