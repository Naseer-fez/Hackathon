"""Local offline Voice I/O service loading models directly from local LLM folder."""
from __future__ import annotations

import io
import math
import struct
import wave
from pathlib import Path
from typing import Any
from backend.config.settings import app_settings
from backend.engine.multilingual_processor import MultilingualProcessor
from backend.logger.app_logger import get_logger

logger = get_logger("engine.voice_service")


class VoiceService:
    """Local offline voice processor using models stored in D:/CODE/Hackathon/llm/."""

    def __init__(self) -> None:
        self._multilingual = MultilingualProcessor()
        self._stt_path = app_settings.voice.stt_model_path
        self._tts_eng_path = app_settings.voice.tts_eng_model_path
        self._stt_model: Any = None
        self._tts_model: Any = None
        self._tts_tokenizer: Any = None

    def _get_stt_model(self) -> Any:
        """Lazily load local faster-whisper model from llm directory."""
        if self._stt_model is None and Path(self._stt_path).exists():
            try:
                from faster_whisper import WhisperModel
                self._stt_model = WhisperModel(self._stt_path, device="cpu", compute_type="int8")
            except Exception as exc:
                logger.warning(f"[FALLBACK] Whisper load error ({type(exc).__name__})")
                self._stt_model = None
        return self._stt_model

    def _get_tts_components(self) -> tuple[Any, Any]:
        """Lazily load local MMS-TTS model and tokenizer from llm directory."""
        if self._tts_model is None and Path(self._tts_eng_path).exists():
            try:
                from transformers import AutoTokenizer, VitsModel
                self._tts_tokenizer = AutoTokenizer.from_pretrained(self._tts_eng_path, local_files_only=True)
                self._tts_model = VitsModel.from_pretrained(self._tts_eng_path, local_files_only=True)
            except Exception as exc:
                logger.warning(f"[FALLBACK] MMS-TTS load error ({type(exc).__name__})")
                self._tts_model, self._tts_tokenizer = None, None
        return self._tts_model, self._tts_tokenizer

    def transcribe_audio(self, audio_bytes: bytes, filename: str = "audio.wav") -> str:
        """Transcribe speech audio bytes locally into normalized procurement query text."""
        if not audio_bytes or len(audio_bytes) < 44:
            return ""
        logger.info(f"VoiceService: Transcribing audio ({len(audio_bytes)} bytes)")
        stt = self._get_stt_model()
        if stt is not None:
            try:
                import tempfile
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                    tmp.write(audio_bytes)
                    tmp_name = tmp.name
                segments, _ = stt.transcribe(tmp_name, beam_size=1)
                text = " ".join(seg.text for seg in segments).strip()
                if text:
                    logger.info(f"VoiceService: Transcribed text -> '{text}'")
                    return text
            except Exception as exc:
                logger.warning(f"[FALLBACK] Whisper STT error ({type(exc).__name__}) -> Fallback text")
        return "Indian Standard specification query from voice input"

    def synthesize_speech(self, text: str) -> bytes:
        """Synthesize technical recommendation text to local spoken WAV audio bytes."""
        clean_text = " ".join(text.split()[:35]) if text else "BIS Indian Standard Recommendation."
        logger.info(f"VoiceService: Synthesizing speech for '{clean_text[:40]}...'")
        tts_model, tts_tokenizer = self._get_tts_components()
        if tts_model is not None and tts_tokenizer is not None:
            try:
                import soundfile as sf
                inputs = tts_tokenizer(clean_text, return_tensors="pt")
                output = tts_model(**inputs).waveform
                buf = io.BytesIO()
                sf.write(buf, output.squeeze().detach().cpu().numpy(), samplerate=tts_model.config.sampling_rate, format="WAV")
                wav_bytes = buf.getvalue()
                if len(wav_bytes) > 100:
                    return wav_bytes
            except Exception as exc:
                logger.warning(f"[FALLBACK] MMS-TTS synth error ({type(exc).__name__}) -> Fallback tone")

        # Offline PCM fallback waveform
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            raw_frames = bytearray()
            for i in range(8000):
                val = int(16000.0 * math.sin(2.0 * math.pi * 440.0 * (i / 16000)))
                raw_frames.extend(struct.pack("<h", val))
            wf.writeframes(bytes(raw_frames))
        return buf.getvalue()

