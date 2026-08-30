"""Tests for unified multi-modal recommendation pipeline."""
from __future__ import annotations

import io
from PIL import Image
import pytest
from backend.engine.pipeline import PipelineResponse, RecommendationPipeline


def create_sample_image_bytes() -> bytes:
    """Generate in-memory sample image for testing."""
    img = Image.new("RGB", (400, 200), color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.mark.asyncio
async def test_pipeline_text_input() -> None:
    """Test pipeline execution with plain text query."""
    pipeline = RecommendationPipeline()
    res = await pipeline.process_input(query="Solar PV Module 500W", division="LITD")

    assert isinstance(res, PipelineResponse)
    assert res.detected_language == "en"
    assert len(res.recommendations) > 0
    assert res.llm_analysis is not None
    assert res.llm_analysis.primary_is_code == res.recommendations[0].standard.is_code


@pytest.mark.asyncio
async def test_pipeline_multimodal_image_and_voice() -> None:
    """Test pipeline execution with image input and voice synthesis output."""
    pipeline = RecommendationPipeline()
    img_bytes = create_sample_image_bytes()

    res = await pipeline.process_input(
        query="High strength steel rebar Fe 500D",
        image_bytes=img_bytes,
        division="CED",
        generate_voice_response=True,
    )

    assert isinstance(res, PipelineResponse)
    assert res.image_analysis is not None
    assert res.image_analysis.is_technical_drawing is True or res.image_analysis.aspect_ratio == 2.0
    assert res.voice_audio_base64 is not None
    assert len(res.voice_audio_base64) > 50
