from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .report import render_markdown, write_json, write_markdown
from .scanner import scan_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="formula-guard",
        description="Read-only checks for DOCX and LaTeX equation workflows.",
    )
    parser.add_argument("--version", action="version", version=__version__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    check = subparsers.add_parser("check", help="scan one DOCX or text-based file")
    check.add_argument("input", type=Path, help="DOCX, TEX, TXT, MD, or MARKDOWN file")
    check.add_argument("--output", type=Path, help="write a Markdown report")
    check.add_argument("--json", dest="json_output", type=Path, help="write JSON")
    check.add_argument("--rules", type=Path, help="custom JSON compatibility rules")
    check.add_argument(
        "--fail-on",
        choices=("none", "warning", "error"),
        default="none",
        help="return exit code 1 at or above this severity (default: none)",
    )
    return parser


def _should_fail(fail_on: str, severities: set[str]) -> bool:
    if fail_on == "none":
        return False
    if fail_on == "error":
        return "error" in severities
    return bool({"warning", "error"} & severities)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command != "check":
        parser.error("Unknown command")

    try:
        result = scan_path(args.input, rules_path=args.rules)
    except (OSError, ValueError) as exc:
        print(f"formula-guard: {exc}", file=sys.stderr)
        return 2

    if args.output:
        report_path = write_markdown(result, args.output)
        print(f"Markdown report: {report_path}")
    else:
        print(render_markdown(result))

    if args.json_output:
        json_path = write_json(result, args.json_output)
        print(f"JSON report: {json_path}")

    counts = result.counts()
    print(
        "Summary: "
        f"{counts.get('error', 0)} error(s), "
        f"{counts.get('warning', 0)} warning(s), "
        f"{counts.get('info', 0)} information item(s)"
    )
    severities = {finding.severity for finding in result.findings}
    return 1 if _should_fail(args.fail_on, severities) else 0
