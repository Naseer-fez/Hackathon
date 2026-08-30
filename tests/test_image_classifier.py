"""Tests for local offline image classification skill."""
from __future__ import annotations

import io
from PIL import Image, ImageDraw
import pytest
from backend.parsers.image_classifier import ImageClassifier, ImageClassificationResult


def create_mock_technical_drawing_image() -> bytes:
    """Create synthetic technical schematic drawing image in memory."""
    img = Image.new("RGB", (600, 300), color="white")
    draw = ImageDraw.Draw(img)
    draw.rectangle([20, 20, 580, 280], outline="black", width=2)
    draw.line([50, 150, 550, 150], fill="black", width=2)
    draw.text((60, 60), "BIS SPECIFICATION IS 14286", fill="black")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_image_classifier_drawing() -> None:
    """Test classification of synthetic engineering schematic drawing."""
    classifier = ImageClassifier()
    img_bytes = create_mock_technical_drawing_image()

    result = classifier.classify(img_bytes)

    assert isinstance(result, ImageClassificationResult)
    assert result.dimensions == (600, 300)
    assert result.aspect_ratio == 2.0
    assert result.is_technical_drawing is True
    assert "Drawing" in result.category or "Specification" in result.category
    assert result.confidence > 0.7


def test_image_classifier_invalid_input() -> None:
    """Test graceful handling of invalid binary payload."""
    classifier = ImageClassifier()
    result = classifier.classify(b"not-an-image-data-payload")

    assert isinstance(result, ImageClassificationResult)
    assert result.confidence == 0.0
    assert result.dimensions == (0, 0)
