"""PDF to clean Markdown extraction using PyMuPDF4LLM on CPU to conserve VRAM."""
from __future__ import annotations
import os
import tempfile
import pymupdf4llm
from backend.logger.app_logger import get_logger

logger = get_logger("parsers.pdf_markdown_parser")


class PdfMarkdownParser:
    """Extracts clean Markdown text from PDF using PyMuPDF4LLM on CPU."""

    def extract_markdown_from_bytes(self, pdf_bytes: bytes) -> str:
        """Parse PDF byte stream into markdown without consuming VRAM."""
        if not pdf_bytes:
            return ""

        temp_path: str | None = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(pdf_bytes)
                temp_path = tmp_file.name

            logger.info("Extracting markdown with PyMuPDF4LLM from temporary PDF...")
            markdown_content = pymupdf4llm.to_markdown(temp_path)
            return markdown_content.strip() if isinstance(markdown_content, str) else ""
        except (OSError, RuntimeError, ValueError) as exc:
            logger.error(f"Failed to extract markdown from PDF ({type(exc).__name__}: {exc})")
            return ""
        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass

    def extract_markdown_from_path(self, file_path: str) -> str:
        """Parse PDF file directly from filesystem path into clean markdown."""
        if not os.path.isfile(file_path):
            logger.warning(f"PDF file does not exist: {file_path}")
            return ""
        try:
            markdown_content = pymupdf4llm.to_markdown(file_path)
            return markdown_content.strip() if isinstance(markdown_content, str) else ""
        except (OSError, RuntimeError, ValueError) as exc:
            logger.error(f"Failed to parse PDF file at {file_path} ({type(exc).__name__}: {exc})")
            return ""
