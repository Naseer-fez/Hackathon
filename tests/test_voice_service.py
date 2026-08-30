"""Tests for local offline Voice I/O service (STT and TTS)."""
from __future__ import annotations

import io
import wave
import pytest
from backend.engine.voice_service import VoiceService


def test_voice_service_synthesize_speech() -> None:
    """Test local speech synthesis generates valid WAV audio data."""
    service = VoiceService()
    text = "Recommended standard is IS 14286 for Crystalline Silicon Solar PV Modules."

    wav_bytes = service.synthesize_speech(text)

    assert isinstance(wav_bytes, bytes)
    assert len(wav_bytes) > 100
    # Validate it's a valid WAV by opening with wave module
    with io.BytesIO(wav_bytes) as bio:
        with wave.open(bio, "rb") as wf:
            assert wf.getnchannels() in (1, 2)
            assert wf.getframerate() in (16000, 22050, 24000, 44100, 48000)
            assert wf.getnframes() > 0


def test_voice_service_transcribe_audio() -> None:
    """Test local audio transcription with fallback."""
    service = VoiceService()
    # Generate mock audio first
    mock_audio = service.synthesize_speech("Test solar panel procurement")

    transcription = service.transcribe_audio(mock_audio)

    assert isinstance(transcription, str)
    assert len(transcription) > 0


def test_voice_service_transcribe_empty() -> None:
    """Test handling of empty or corrupted audio bytes."""
    service = VoiceService()
    assert service.transcribe_audio(b"") == ""
