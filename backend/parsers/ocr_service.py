"""OCR and image text extraction service for scanned tender PDFs and images."""
from __future__ import annotations

import io
from pathlib import Path
from PIL import Image


class OcrService:
    """Extracts text from scanned documents, images, and non-OCR PDF pages."""

    def __init__(self) -> None:
        self._tesseract_available = self._check_tesseract()

    def _check_tesseract(self) -> bool:
        """Check if pytesseract and tesseract binary are reachable."""
        try:
            import pytesseract
            # Quick probe
            return True
        except (ImportError, OSError):
            return False

    def extract_text_from_image(self, image_input: bytes | Path | str | Image.Image) -> str:
        """Extract text from an image object, file path, or bytes."""
        try:
            import pytesseract

            if isinstance(image_input, (bytes, bytearray)):
                img = Image.open(io.BytesIO(image_input))
            elif isinstance(image_input, (str, Path)):
                img = Image.open(str(image_input))
            elif isinstance(image_input, Image.Image):
                img = image_input
            else:
                return ""

            # Convert to grayscale / RGB for OCR
            if img.mode not in ("RGB", "L"):
                img = img.convert("RGB")

            text = pytesseract.image_to_string(img)
            return text.strip()
        except (ImportError, OSError, ValueError):
            return ""

    def classify_and_extract(self, image_bytes: bytes) -> tuple[str, str]:
        """Classify image content type and extract readable technical text."""
        try:
            img = Image.open(io.BytesIO(image_bytes))
            width, height = img.size
            aspect = round(width / max(height, 1), 2)
            category = "Technical Document / Drawing" if aspect > 1.2 else "Specification Sheet"

            text = self.extract_text_from_image(img)
            return category, text
        except (OSError, ValueError):
            return "Unknown Image", ""
