"""Multi-format tender document text extractor (PDF, DOCX, TXT, OCR Images)."""
from __future__ import annotations

from pathlib import Path
import docx
import fitz  # PyMuPDF
from backend.parsers.ocr_service import OcrService


class DocumentParser:
    """Extracts textual content from vector PDFs, scanned non-OCR PDFs, DOCX, and images."""

    def __init__(self, ocr_service: OcrService | None = None) -> None:
        self._ocr = ocr_service or OcrService()

    def extract_text_from_pdf(self, file_path: str | Path) -> str:
        """Extract text from PDF, falling back to OCR if page has no embedded text."""
        text_parts: list[str] = []
        try:
            doc = fitz.open(str(file_path))
            for page in doc:
                page_text = page.get_text().strip()
                # If page is a scan / non-OCR image, render pixmap and run OCR
                if len(page_text) < 15:
                    pix = page.get_pixmap(dpi=150)
                    img_bytes = pix.tobytes("png")
                    page_text = self._ocr.extract_text_from_image(img_bytes)

                if page_text:
                    text_parts.append(page_text)
            doc.close()
        except (fitz.FileDataError, OSError, ValueError):
            return ""
        return "\n\n".join(text_parts)

    def extract_text_from_docx(self, file_path: str | Path) -> str:
        """Extract text from Word .docx file."""
        try:
            doc = docx.Document(str(file_path))
            return "\n".join(p.text for p in doc.paragraphs if p.text)
        except (docx.opc.exceptions.PackageNotFoundError, OSError, ValueError):
            return ""

    def extract_text_from_file(self, file_path: str | Path) -> str:
        """Extract text depending on file extension including image formats."""
        path = Path(file_path)
        if not path.exists():
            return ""
        ext = path.suffix.lower()
        if ext == ".pdf":
            return self.extract_text_from_pdf(path)
        if ext in (".docx", ".doc"):
            return self.extract_text_from_docx(path)
        if ext in (".png", ".jpg", ".jpeg", ".webp", ".tiff", ".bmp"):
            return self._ocr.extract_text_from_image(path)
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except OSError:
            return ""
