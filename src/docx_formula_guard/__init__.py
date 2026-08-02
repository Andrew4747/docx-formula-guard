"""Read-only checks for DOCX and LaTeX equation workflows."""

__version__ = "0.1.0"

from .scanner import scan_path, scan_text

__all__ = ["__version__", "scan_path", "scan_text"]
