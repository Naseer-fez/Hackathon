"""Unit tests for multilingual processor."""
from __future__ import annotations

from backend.engine.multilingual_processor import MultilingualProcessor


def test_detect_script() -> None:
    """Test script detection for English and Indic languages."""
    processor = MultilingualProcessor()
    assert processor.detect_script("High strength TMT bars") == "en"
    assert processor.detect_script("सौर पैनल और इनवर्टर") == "hi"


def test_translate_and_expand_hindi() -> None:
    """Test translation and term expansion for Hindi queries."""
    processor = MultilingualProcessor()
    query = "सौर पैनल और इनवर्टर"
    translated, lang = processor.translate_and_expand(query)
    assert lang == "hi"
    assert "solar" in translated.lower()
    assert "inverter" in translated.lower()


def test_translate_and_expand_english() -> None:
    """Test English query preservation."""
    processor = MultilingualProcessor()
    text, lang = processor.translate_and_expand("LED street lighting luminaire")
    assert lang == "en"
    assert text == "LED street lighting luminaire"
