from __future__ import annotations

import re
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable
from xml.etree import ElementTree

from .models import Finding, ScanResult
from .rules import load_rules


TEXT_SUFFIXES = {".tex", ".txt", ".md", ".markdown"}

CHARACTER_RULES = {
    "\ufffd": (
        "UNICODE_REPLACEMENT_CHARACTER",
        "error",
        "Unicode replacement character U+FFFD usually indicates lost or undecodable content.",
    ),
    "\ufffc": (
        "OBJECT_REPLACEMENT_CHARACTER",
        "warning",
        "Object replacement character U+FFFC may indicate a detached embedded object.",
    ),
    "\u3000": (
        "IDEOGRAPHIC_SPACE",
        "warning",
        "Ideographic space U+3000 can appear as a box in some document workflows.",
    ),
    "\u00a0": (
        "NO_BREAK_SPACE",
        "warning",
        "No-break space U+00A0 can behave differently from an ordinary space.",
    ),
    "\u25a1": (
        "WHITE_SQUARE",
        "warning",
        "White-square placeholder U+25A1 may represent a missing mathematical glyph.",
    ),
}

EQUATION_NUMBER_RE = re.compile(
    r"^\s*[\(（]\s*(?P<section>\d+)\s*[-－—]\s*(?P<number>\d+)"
    r"(?P<suffix>[a-z]?)\s*[\)）]\s*$",
    flags=re.IGNORECASE | re.MULTILINE,
)

WORDPROCESSINGML_NAMESPACE = (
    "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
)


def _excerpt(text: str, index: int, width: int = 28) -> str:
    start = max(index - width, 0)
    end = min(index + width, len(text))
    return text[start:end].replace("\r", " ").replace("\n", " ").strip()


def _character_findings(text: str, source: str) -> list[Finding]:
    findings: list[Finding] = []
    for index, char in enumerate(text):
        if char in CHARACTER_RULES:
            code, severity, message = CHARACTER_RULES[char]
            findings.append(
                Finding(
                    code=code,
                    severity=severity,
                    message=message,
                    source=source,
                    location=f"character {index + 1}",
                    excerpt=_excerpt(text, index),
                )
            )
        elif 0xE000 <= ord(char) <= 0xF8FF:
            findings.append(
                Finding(
                    code="PRIVATE_USE_CHARACTER",
                    severity="warning",
                    message=(
                        "A Unicode private-use character was found. Its appearance depends "
                        "on a specific font or application."
                    ),
                    source=source,
                    location=f"character {index + 1}",
                    excerpt=_excerpt(text, index),
                )
            )
    return findings


def _latex_findings(
    text: str, source: str, rules_data: dict[str, Any]
) -> list[Finding]:
    findings: list[Finding] = []
    for rule in rules_data["rules"]:
        pattern = re.compile(rule["pattern"])
        for match in pattern.finditer(text):
            findings.append(
                Finding(
                    code=rule["code"],
                    severity=rule["severity"],
                    message=rule["message"],
                    source=source,
                    location=f"character {match.start() + 1}",
                    excerpt=_excerpt(text, match.start()),
                )
            )
    return findings


def _equation_number_findings(text: str, source: str) -> list[Finding]:
    matches = list(EQUATION_NUMBER_RE.finditer(text))
    findings: list[Finding] = []
    labels = [
        (match.group("section"), match.group("number"), match.group("suffix").lower())
        for match in matches
    ]

    for label, count in Counter(labels).items():
        if count > 1:
            section, number, suffix = label
            findings.append(
                Finding(
                    code="DUPLICATE_EQUATION_NUMBER",
                    severity="warning",
                    message=f"Equation number ({section}-{number}{suffix}) appears {count} times.",
                    source=source,
                    location="visible text",
                    excerpt=f"({section}-{number}{suffix})",
                )
            )

    by_section: dict[str, set[int]] = defaultdict(set)
    for section, number, _suffix in labels:
        by_section[section].add(int(number))

    for section, numbers in sorted(by_section.items()):
        if len(numbers) < 2:
            continue
        missing = sorted(set(range(min(numbers), max(numbers) + 1)) - numbers)
        if missing:
            shown = ", ".join(str(item) for item in missing[:12])
            if len(missing) > 12:
                shown += ", ..."
            findings.append(
                Finding(
                    code="EQUATION_NUMBER_GAP",
                    severity="info",
                    message=f"Possible equation-number gaps in section {section}: {shown}.",
                    source=source,
                    location="visible text",
                    excerpt="Review intentional deletions and subequation grouping.",
                )
            )

    return findings


def scan_text(
    text: str,
    source: str = "text",
    rules_path: str | Path | None = None,
    include_numbering: bool = True,
) -> ScanResult:
    rules_data = load_rules(rules_path)
    findings = _character_findings(text, source)
    findings.extend(_latex_findings(text, source, rules_data))
    if include_numbering:
        findings.extend(_equation_number_findings(text, source))
    return ScanResult(
        path=source,
        findings=findings,
        metadata={
            "kind": "text",
            "characters": len(text),
            "rules_profile": rules_data.get("profile", "custom"),
        },
    )


def _xml_visible_text(root: ElementTree.Element) -> str:
    chunks: list[str] = []
    for element in root.iter():
        local_name = element.tag.rsplit("}", 1)[-1]
        namespace = (
            element.tag[1:].split("}", 1)[0]
            if element.tag.startswith("{") and "}" in element.tag
            else ""
        )
        if (
            namespace == WORDPROCESSINGML_NAMESPACE
            and local_name in {"t", "instrText", "delText"}
            and element.text
        ):
            chunks.append(element.text)
        elif local_name in {"p", "tr"}:
            chunks.append("\n")
    return "".join(chunks)


def _count_local_names(root: ElementTree.Element, names: Iterable[str]) -> Counter[str]:
    wanted = set(names)
    counts: Counter[str] = Counter()
    for element in root.iter():
        local_name = element.tag.rsplit("}", 1)[-1]
        if local_name in wanted:
            counts[local_name] += 1
    return counts


def _scan_docx(path: Path, rules_path: str | Path | None = None) -> ScanResult:
    rules_data = load_rules(rules_path)
    findings: list[Finding] = []
    visible_chunks: list[str] = []
    metadata: dict[str, Any] = {
        "kind": "docx",
        "rules_profile": rules_data.get("profile", "custom"),
    }
    total_counts: Counter[str] = Counter()

    try:
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
            xml_parts = [
                name
                for name in names
                if name.startswith("word/") and name.lower().endswith(".xml")
            ]
            embeddings = [name for name in names if name.startswith("word/embeddings/")]

            metadata.update(
                {
                    "package_parts": len(names),
                    "word_xml_parts": len(xml_parts),
                    "embedded_objects": len(embeddings),
                }
            )

            for part in xml_parts:
                raw_bytes = archive.read(part)
                decoded = raw_bytes.decode("utf-8", errors="replace")
                source = f"{path.name}:{part}"
                findings.extend(_character_findings(decoded, source))
                try:
                    root = ElementTree.fromstring(raw_bytes)
                except ElementTree.ParseError as exc:
                    findings.append(
                        Finding(
                            code="DOCX_XML_PARSE_ERROR",
                            severity="error",
                            message=f"The DOCX XML part could not be parsed: {exc}.",
                            source=source,
                            location="XML part",
                        )
                    )
                    continue

                part_text = _xml_visible_text(root)
                if part_text:
                    visible_chunks.append(part_text)
                    findings.extend(_latex_findings(part_text, source, rules_data))
                total_counts.update(
                    _count_local_names(root, {"OLEObject", "oMath", "oMathPara"})
                )

    except (OSError, zipfile.BadZipFile) as exc:
        return ScanResult(
            path=str(path),
            findings=[
                Finding(
                    code="DOCX_OPEN_ERROR",
                    severity="error",
                    message=f"The DOCX package could not be opened: {exc}.",
                    source=path.name,
                    location="file",
                )
            ],
            metadata={"kind": "docx"},
        )

    visible_text = "".join(visible_chunks)
    findings.extend(_equation_number_findings(visible_text, path.name))
    metadata.update(
        {
            "visible_characters": len(visible_text),
            "ole_references": total_counts["OLEObject"],
            "omml_objects": total_counts["oMath"],
            "omml_paragraphs": total_counts["oMathPara"],
        }
    )
    return ScanResult(path=str(path), findings=findings, metadata=metadata)


def scan_path(
    path: str | Path, rules_path: str | Path | None = None
) -> ScanResult:
    input_path = Path(path)
    if not input_path.exists():
        return ScanResult(
            path=str(input_path),
            findings=[
                Finding(
                    code="FILE_NOT_FOUND",
                    severity="error",
                    message="Input file does not exist.",
                    source=str(input_path),
                    location="file",
                )
            ],
            metadata={"kind": "unknown"},
        )

    suffix = input_path.suffix.lower()
    if suffix == ".docx":
        return _scan_docx(input_path, rules_path)
    if suffix in TEXT_SUFFIXES:
        try:
            text = input_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = input_path.read_text(encoding="utf-8", errors="replace")
        result = scan_text(text, source=str(input_path), rules_path=rules_path)
        result.metadata["suffix"] = suffix
        return result

    return ScanResult(
        path=str(input_path),
        findings=[
            Finding(
                code="UNSUPPORTED_FILE_TYPE",
                severity="error",
                message="Supported file types are DOCX, TEX, TXT, MD, and MARKDOWN.",
                source=str(input_path),
                location="file",
            )
        ],
        metadata={"kind": "unknown", "suffix": suffix},
    )
