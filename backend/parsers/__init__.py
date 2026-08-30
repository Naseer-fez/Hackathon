"""Document parsing, OCR, and local image classification package."""
from backend.parsers.document_parser import DocumentParser
from backend.parsers.image_classifier import ImageClassificationResult, ImageClassifier
from backend.parsers.ocr_service import OcrService
from backend.parsers.spec_extractor import SpecExtractor

__all__ = [
    "DocumentParser",
    "OcrService",
    "SpecExtractor",
    "ImageClassifier",
    "ImageClassificationResult",
]
