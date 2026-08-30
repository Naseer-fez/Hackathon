"""Local offline image classification and technical feature extraction service."""
from __future__ import annotations

import io
from pathlib import Path
from typing import Any
from PIL import Image, ImageStat
from pydantic import BaseModel, Field
from backend.parsers.ocr_service import OcrService


class ImageClassificationResult(BaseModel):
    """Structured result of local image classification."""
    category: str
    confidence: float
    dimensions: tuple[int, int]
    aspect_ratio: float
    is_technical_drawing: bool
    extracted_text: str = ""
    technical_attributes: dict[str, Any] = Field(default_factory=dict)


class ImageClassifier:
    """Local offline classifier for engineering drawings, spec sheets, and product images."""

    def __init__(self, ocr_service: OcrService | None = None) -> None:
        self._ocr = ocr_service or OcrService()

    def _analyze_visual_features(self, img: Image.Image) -> tuple[str, float, bool, dict[str, Any]]:
        """Compute visual heuristic features locally without external network calls."""
        width, height = img.size
        aspect = round(width / max(height, 1), 2)
        gray = img.convert("L")
        stat = ImageStat.Stat(gray)
        mean_brightness = stat.mean[0]
        std_dev = stat.stddev[0]

        is_drawing = (mean_brightness > 180 and std_dev > 30) or aspect > 1.4

        if is_drawing:
            category = "Technical Drawing / Schematic"
            confidence = 0.92 if aspect > 1.3 else 0.85
        elif mean_brightness > 200:
            category = "Specification Sheet / Label"
            confidence = 0.88
        else:
            category = "Product Physical Sample"
            confidence = 0.82

        attributes = {
            "mean_brightness": round(mean_brightness, 2),
            "contrast_variance": round(std_dev, 2),
            "color_mode": img.mode,
        }
        return category, confidence, is_drawing, attributes

    def classify(self, image_input: bytes | Path | str | Image.Image) -> ImageClassificationResult:
        """Classify image content locally and extract technical text."""
        try:
            if isinstance(image_input, (bytes, bytearray)):
                img = Image.open(io.BytesIO(image_input))
            elif isinstance(image_input, (str, Path)):
                img = Image.open(str(image_input))
            elif isinstance(image_input, Image.Image):
                img = image_input
            else:
                return ImageClassificationResult(
                    category="Unknown", confidence=0.0, dimensions=(0, 0),
                    aspect_ratio=1.0, is_technical_drawing=False,
                )

            width, height = img.size
            aspect = round(width / max(height, 1), 2)
            category, conf, is_dwg, attrs = self._analyze_visual_features(img)
            extracted_txt = self._ocr.extract_text_from_image(img)

            return ImageClassificationResult(
                category=category,
                confidence=conf,
                dimensions=(width, height),
                aspect_ratio=aspect,
                is_technical_drawing=is_dwg,
                extracted_text=extracted_txt,
                technical_attributes=attrs,
            )
        except (OSError, ValueError, TypeError) as exc:
            return ImageClassificationResult(
                category=f"Unprocessable ({type(exc).__name__})",
                confidence=0.0,
                dimensions=(0, 0),
                aspect_ratio=1.0,
                is_technical_drawing=False,
                extracted_text="",
            )
