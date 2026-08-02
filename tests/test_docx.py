from __future__ import annotations

import unittest
import zipfile
from pathlib import Path
from uuid import uuid4

from docx_formula_guard.scanner import scan_path


DOCUMENT_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
 xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math"
 xmlns:o="urn:schemas-microsoft-com:office:office">
 <w:body>
  <w:p><w:r><w:t>Equation (3-1)</w:t></w:r></w:p>
  <w:p><w:r><w:t>Bad replacement: \ufffd</w:t></w:r></w:p>
  <w:p><m:oMath><m:r><m:t>x</m:t></m:r></m:oMath></w:p>
  <w:p><w:object><o:OLEObject/></w:object></w:p>
 </w:body>
</w:document>
"""


class DocxScannerTests(unittest.TestCase):
    def test_scans_minimal_docx_package(self) -> None:
        path = Path(__file__).parent / f"_runtime-{uuid4().hex}.docx"
        self.addCleanup(path.unlink, missing_ok=True)
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("word/document.xml", DOCUMENT_XML)
            archive.writestr("word/embeddings/oleObject1.bin", b"synthetic")

        result = scan_path(path)
        codes = {finding.code for finding in result.findings}
        self.assertIn("UNICODE_REPLACEMENT_CHARACTER", codes)
        self.assertEqual(1, result.metadata["embedded_objects"])
        self.assertEqual(1, result.metadata["ole_references"])
        self.assertEqual(1, result.metadata["omml_objects"])

    def test_missing_file_is_reported(self) -> None:
        result = scan_path("definitely-missing.docx")
        self.assertEqual("FILE_NOT_FOUND", result.findings[0].code)


if __name__ == "__main__":
    unittest.main()
