"""Tests for pipeline and multimodal FastAPI endpoints."""
from __future__ import annotations

import io
from fastapi.testclient import TestClient
from PIL import Image
import pytest
from backend.main import app


@pytest.fixture
def client() -> TestClient:
    """Fixture providing FastAPI test client."""
    return TestClient(app)


def test_voice_synthesize_endpoint(client: TestClient) -> None:
    """Test voice speech synthesis endpoint returns audio/wav."""
    payload = {"text": "IS 1786 High Strength Deformed Steel Bars for Concrete Reinforcement"}
    res = client.post("/api/v1/voice/synthesize", json=payload)
    assert res.status_code == 200
    assert res.headers["content-type"] == "audio/wav"
    assert len(res.content) > 100


def test_voice_transcribe_endpoint(client: TestClient) -> None:
    """Test voice transcription endpoint accepts audio upload."""
    wav_payload = b"RIFF....WAVEfmt ...." + b"\x00" * 60
    files = {"audio_file": ("test.wav", wav_payload, "audio/wav")}
    res = client.post("/api/v1/voice/transcribe", files=files)
    assert res.status_code == 200
    data = res.json()
    assert "transcribed_text" in data


def test_image_classify_endpoint(client: TestClient) -> None:
    """Test image classification endpoint returns structured analysis."""
    img = Image.new("RGB", (300, 300), color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    files = {"image_file": ("spec.png", buf.getvalue(), "image/png")}

    res = client.post("/api/v1/image/classify", files=files)
    assert res.status_code == 200
    data = res.json()
    assert "category" in data
    assert "confidence" in data
    assert data["dimensions"] == [300, 300]


def test_pipeline_process_endpoint(client: TestClient) -> None:
    """Test multimodal pipeline processing endpoint."""
    form_data = {
        "query": "Solar PV Module 450W",
        "division": "LITD",
        "generate_voice_response": "true",
    }
    res = client.post("/api/v1/pipeline/process", data=form_data)
    assert res.status_code == 200
    data = res.json()
    assert "query" in data
    assert len(data["recommendations"]) > 0
    assert data["llm_analysis"] is not None
    assert data["voice_audio_base64"] is not None
