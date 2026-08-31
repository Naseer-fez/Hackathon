import type { ImageClassificationResult, PipelineResponse } from "../types";

const API_BASE = (import.meta.env.VITE_API_BASE_URL as string) || "/api/v1";

export async function processMultimodalPipeline(
  formData: FormData
): Promise<PipelineResponse> {
  const res = await fetch(`${API_BASE}/pipeline/process`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) throw new Error("Multimodal pipeline request failed");
  return res.json();
}

export async function transcribeVoiceAudio(audioBlob: Blob): Promise<string> {
  const formData = new FormData();
  formData.append("audio_file", audioBlob, "recording.wav");
  const res = await fetch(`${API_BASE}/voice/transcribe`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) throw new Error("Voice transcription failed");
  const data = await res.json();
  return data.transcribed_text || "";
}

export async function synthesizeSpeechAudio(text: string): Promise<Blob> {
  const res = await fetch(`${API_BASE}/voice/synthesize`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  if (!res.ok) throw new Error("Speech synthesis failed");
  return res.blob();
}

export async function classifyTechnicalImage(
  imageFile: File
): Promise<ImageClassificationResult> {
  const formData = new FormData();
  formData.append("image_file", imageFile);
  const res = await fetch(`${API_BASE}/image/classify`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) throw new Error("Image classification failed");
  return res.json();
}
