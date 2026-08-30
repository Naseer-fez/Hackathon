"""Unit tests for document parser."""
from __future__ import annotations

from pathlib import Path
from backend.parsers.document_parser import DocumentParser


def test_extract_text_from_txt_and_missing() -> None:
    """Test document parser with txt file and handling non-existent files."""
    parser = DocumentParser()

    # Non-existent file test
    missing = parser.extract_text_from_file("non_existent_file.pdf")
    assert missing == ""

    # Temporary text file test
    tmp_path = Path("d:/CODE/Hackathon/backend/data/test_sample.txt")
    tmp_path.write_text("Supply of 500 MT of TMT Rebars as per IS 1786 Fe 500D.", encoding="utf-8")

    extracted = parser.extract_text_from_file(tmp_path)
    assert "IS 1786" in extracted
    assert "Fe 500D" in extracted

    if tmp_path.exists():
        tmp_path.unlink()
