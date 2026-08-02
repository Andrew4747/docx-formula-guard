from __future__ import annotations

import json
import re
from importlib.resources import files
from pathlib import Path
from typing import Any


def load_rules(path: str | Path | None = None) -> dict[str, Any]:
    if path is None:
        resource = files("docx_formula_guard").joinpath("default_rules.json")
        with resource.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    else:
        with Path(path).open("r", encoding="utf-8") as handle:
            data = json.load(handle)

    raw_rules = data.get("rules")
    if not isinstance(raw_rules, list):
        raise ValueError("Rule file must contain a 'rules' list.")

    for item in raw_rules:
        if not isinstance(item, dict):
            raise ValueError("Each rule must be an object.")
        for required in ("code", "pattern", "severity", "message"):
            if required not in item:
                raise ValueError(f"Rule is missing required field: {required}")
        if item["severity"] not in {"error", "warning", "info"}:
            raise ValueError(f"Unsupported severity: {item['severity']}")
        re.compile(item["pattern"])

    return data
