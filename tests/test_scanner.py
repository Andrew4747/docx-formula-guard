from __future__ import annotations

import unittest

from docx_formula_guard.scanner import scan_text


class TextScannerTests(unittest.TestCase):
    def test_detects_unicode_anomalies(self) -> None:
        result = scan_text("A\ufffdB\u00a0C", include_numbering=False)
        codes = {finding.code for finding in result.findings}
        self.assertIn("UNICODE_REPLACEMENT_CHARACTER", codes)
        self.assertIn("NO_BREAK_SPACE", codes)

    def test_detects_conversion_risk_patterns(self) -> None:
        result = scan_text(
            r"\begin{aligned}x&=1\qquad y=2\end{aligned}",
            include_numbering=False,
        )
        codes = [finding.code for finding in result.findings]
        self.assertIn("LATEX_ENVIRONMENT", codes)
        self.assertIn("LATEX_SPACING_COMMAND", codes)

    def test_detects_duplicate_and_missing_equation_numbers(self) -> None:
        result = scan_text("(3-1)\n(3-1)\n(3-3)")
        codes = {finding.code for finding in result.findings}
        self.assertIn("DUPLICATE_EQUATION_NUMBER", codes)
        self.assertIn("EQUATION_NUMBER_GAP", codes)

    def test_inline_cross_reference_is_not_treated_as_a_label(self) -> None:
        result = scan_text("As shown in equation (3-1), the constraint holds.")
        codes = {finding.code for finding in result.findings}
        self.assertNotIn("DUPLICATE_EQUATION_NUMBER", codes)
        self.assertNotIn("EQUATION_NUMBER_GAP", codes)

    def test_clean_text_has_no_findings(self) -> None:
        result = scan_text(r"x_{ij}=1,\forall i\in I,j\in J", include_numbering=False)
        self.assertEqual([], result.findings)


if __name__ == "__main__":
    unittest.main()
