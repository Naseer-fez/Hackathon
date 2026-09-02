"""Unit tests for PdfMarkdownParser using PyMuPDF4LLM."""
from __future__ import annotations
import os
import fitz
import pytest
from backend.parsers.pdf_markdown_parser import PdfMarkdownParser


def test_pdf_markdown_parser_empty_bytes() -> None:
    """Test extracting from empty bytes."""
    parser = PdfMarkdownParser()
    result = parser.extract_markdown_from_bytes(b"")
    assert result == ""


def test_pdf_markdown_parser_missing_path() -> None:
    """Test handling of non-existent file path."""
    parser = PdfMarkdownParser()
    result = parser.extract_markdown_from_path("non_existent_file.pdf")
    assert result == ""


def test_pdf_markdown_parser_valid_pdf(tmp_path: pytest.TempPathFactory) -> None:
    """Test extracting text as markdown from a real PDF generated via PyMuPDF."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "# Specification for Cement IS 269\nGrade 53 Ordinary Portland Cement")
    pdf_bytes = doc.tobytes()
    doc.close()

    parser = PdfMarkdownParser()
    markdown = parser.extract_markdown_from_bytes(pdf_bytes)

    assert "Specification for Cement" in markdown or "IS 269" in markdown
