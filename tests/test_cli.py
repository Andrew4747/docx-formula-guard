from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path
from uuid import uuid4


class CliTests(unittest.TestCase):
    def test_cli_writes_markdown_and_json(self) -> None:
        stem = Path(__file__).parent / f"_runtime-{uuid4().hex}"
        source = stem.with_suffix(".tex")
        markdown = stem.with_suffix(".md")
        json_report = stem.with_suffix(".json")
        for path in (source, markdown, json_report):
            self.addCleanup(path.unlink, missing_ok=True)
        source.write_text(r"x=1\qquad y=2", encoding="utf-8")

        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "docx_formula_guard",
                "check",
                str(source),
                "--output",
                str(markdown),
                "--json",
                str(json_report),
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertTrue(markdown.exists())
        self.assertTrue(json_report.exists())
        self.assertIn("LATEX_SPACING_COMMAND", markdown.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
