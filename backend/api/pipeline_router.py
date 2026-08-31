"""FastAPI router for unified multi-modal pipeline, local voice I/O, and image classification."""
from __future__ import annotations

import asyncio
import io
from fastapi import APIRouter, File, Form, Response, UploadFile
from pydantic import BaseModel
from backend.engine.pipeline import PipelineResponse, RecommendationPipeline
from backend.engine.voice_service import VoiceService
from backend.parsers.image_classifier import ImageClassificationResult, ImageClassifier

router = APIRouter(prefix="/api/v1", tags=["pipeline"])

pipeline = RecommendationPipeline()
voice_service = VoiceService()
image_classifier = ImageClassifier()


class VoiceTranscriptionResponse(BaseModel):
    """Voice Speech-to-Text transcription output."""
    transcribed_text: str


class TextToSpeechRequest(BaseModel):
    """Text-to-Speech synthesis input payload."""
    text: str


@router.post("/pipeline/process", response_model=PipelineResponse)
async def process_pipeline(
    query: str | None = Form(None),
    division: str | None = Form(None),
    generate_voice_response: bool = Form(False),
    pdf_file: UploadFile | None = File(None),
    image_file: UploadFile | None = File(None),
    audio_file: UploadFile | None = File(None),
) -> PipelineResponse:
    """Process multi-modal inputs (text, PDF, image, audio) and return standardized recommendations."""
    pdf_bytes = await pdf_file.read() if pdf_file else None
    image_bytes = await image_file.read() if image_file else None
    audio_bytes = await audio_file.read() if audio_file else None

    return await pipeline.process_input(
        query=query,
        pdf_bytes=pdf_bytes,
        image_bytes=image_bytes,
        audio_bytes=audio_bytes,
        division=division,
        generate_voice_response=generate_voice_response,
    )


@router.post("/voice/transcribe", response_model=VoiceTranscriptionResponse)
async def transcribe_voice(audio_file: UploadFile = File(...)) -> VoiceTranscriptionResponse:
    """Transcribe uploaded audio file to text locally without external APIs."""
    audio_bytes = await audio_file.read()
    text = await asyncio.to_thread(voice_service.transcribe_audio, audio_bytes, audio_file.filename or "audio.wav")
    return VoiceTranscriptionResponse(transcribed_text=text)


@router.post("/voice/synthesize")
async def synthesize_voice(req: TextToSpeechRequest) -> Response:
    """Synthesize text into WAV audio bytes locally without external APIs."""
    wav_bytes = await asyncio.to_thread(voice_service.synthesize_speech, req.text)
    return Response(content=wav_bytes, media_type="audio/wav")


@router.post("/image/classify", response_model=ImageClassificationResult)
async def classify_image(image_file: UploadFile = File(...)) -> ImageClassificationResult:
    """Classify technical drawings, spec sheets, and product images locally."""
    img_bytes = await image_file.read()
    return await asyncio.to_thread(image_classifier.classify, img_bytes)
