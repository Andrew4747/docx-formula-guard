# Docx Formula Guard

[![Tests](https://github.com/Andrew4747/docx-formula-guard/actions/workflows/tests.yml/badge.svg)](https://github.com/Andrew4747/docx-formula-guard/actions/workflows/tests.yml)

A small, read-only checker for DOCX and LaTeX equation workflows. It reports
corrupted Unicode characters, configurable LaTeX conversion risks, equation
numbering anomalies, and basic DOCX package statistics before a document is
converted between Word equations and MathType.

> 中文简介：这是一个面向学术文档的只读检查工具，用于发现 DOCX、LaTeX 与
> Word/MathType 公式转换流程中的常见风险。工具只生成报告，不修改原文件。

## Why this project exists

Mixed Chinese, LaTeX, Word, and MathType workflows can introduce replacement
characters, unusual spaces, square placeholders, or formulas that render
differently after conversion. These problems are often found late and checked
manually. Docx Formula Guard makes the first inspection repeatable while
keeping the source document untouched.

## Current checks

- replacement characters such as `U+FFFD` and `U+FFFC`;
- unusual spaces, white-square placeholders, and private-use characters;
- configurable LaTeX patterns that may be unreliable in a Word native
  equation to MathType workflow;
- duplicate or missing equation numbers detectable from visible text;
- counts of DOCX XML parts, embedded objects, OLE references, and OMML objects;
- Markdown and JSON reports suitable for issue reports and regression tests.

## Installation

Python 3.10 or newer is required.

```bash
git clone https://github.com/Andrew4747/docx-formula-guard.git
cd docx-formula-guard
python -m pip install -e .
```

## Quick start

Check a DOCX file and write a Markdown report:

```bash
formula-guard check manuscript.docx --output report.md
```

Check a LaTeX or text file and also write machine-readable JSON:

```bash
formula-guard check formulas.tex --output report.md --json report.json
```

Use a custom rule file:

```bash
formula-guard check formulas.tex --rules my-rules.json
```

The command returns zero by default even when findings are present. CI users
can request a non-zero exit code:

```bash
formula-guard check formulas.tex --fail-on warning
```

## Example

See [`examples/sample_input.tex`](examples/sample_input.tex) and
[`examples/sample_report.md`](examples/sample_report.md).

## Scope and limitations

This project is an early compatibility audit, not a formula converter. It does
not modify source files, guarantee successful conversion, or fully decode every
proprietary MathType OLE record. A warning means that a pattern deserves a
conversion test in the user's own environment; it is not a universal LaTeX
error.

DOCX files are processed locally. No document content is uploaded by the core
checker.

## Roadmap

- improve equation-number and cross-reference checks;
- add sanitized DOCX regression fixtures;
- compare DOCX package structure before and after conversion;
- allow community-maintained compatibility profiles;
- document verified behavior across Word and MathType versions.

## Contributing

Bug reports and small compatibility samples are welcome. Please remove private,
copyrighted, or identifying content before attaching a document. See
[`CONTRIBUTING.md`](CONTRIBUTING.md).

## Trademark notice

MathType is a trademark of its respective owner. This project is independent
and is not affiliated with or endorsed by MathType or Microsoft.

## License

MIT
