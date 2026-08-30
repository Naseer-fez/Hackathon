"""Unit tests for OCR service and scanned image handling."""
from __future__ import annotations

import io
from pathlib import Path
from PIL import Image, ImageDraw
from backend.parsers.document_parser import DocumentParser
from backend.parsers.ocr_service import OcrService


def test_ocr_service_image_creation_and_extraction() -> None:
    """Test OCR service processing synthesized test image."""
    ocr = OcrService()
    # Create simple RGB test image in memory
    img = Image.new("RGB", (300, 100), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((10, 40), "IS 1786 TMT Steel", fill=(0, 0, 0))

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    img_bytes = buf.getvalue()

    category, text = ocr.classify_and_extract(img_bytes)
    assert category in ("Technical Document / Drawing", "Specification Sheet")


def test_document_parser_image_support() -> None:
    """Test document parser extracting text from image file."""
    parser = DocumentParser()
    tmp_img_path = Path("d:/CODE/Hackathon/backend/data/temp_test_ocr.png")

    img = Image.new("RGB", (200, 80), color=(255, 255, 255))
    img.save(tmp_img_path)

    try:
        res = parser.extract_text_from_file(tmp_img_path)
        assert isinstance(res, str)
    finally:
        if tmp_img_path.exists():
            tmp_img_path.unlink()
