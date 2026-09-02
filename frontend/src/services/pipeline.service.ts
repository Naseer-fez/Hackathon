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

export async function fetchFastAnswer(
  query: string,
  pdfFile?: File,
  pdfText?: string
): Promise<{ query: string; answer: string; source_tier: string }> {
  const formData = new FormData();
  formData.append("query", query);
  if (pdfText) formData.append("pdf_text", pdfText);
  if (pdfFile) formData.append("pdf_file", pdfFile);

  const res = await fetch(`${API_BASE}/fast-answer`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) throw new Error("Fast answer request failed");
  return res.json();
}

export async function fetchHeavyReasoning(
  query: string,
  pdfFile?: File,
  pdfText?: string,
  chatHistory?: { role: string; content: string }[],
  refreshContext: boolean = false
): Promise<{ query: string; answer: string; source_tier: string; synthesized_context?: string; summarized_history?: string }> {
  const formData = new FormData();
  formData.append("query", query);
  if (pdfText) formData.append("pdf_text", pdfText);
  if (pdfFile) formData.append("pdf_file", pdfFile);
  if (chatHistory) formData.append("chat_history", JSON.stringify(chatHistory));
  formData.append("refresh_context", refreshContext ? "true" : "false");

  const res = await fetch(`${API_BASE}/heavy-reasoning`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) throw new Error("Heavy reasoning request failed");
  return res.json();
}

export async function refreshChatContext(
  chatHistory: { role: string; content: string }[]
): Promise<string> {
  const res = await fetch(`${API_BASE}/summarize-context`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ chat_history: chatHistory }),
  });
  if (!res.ok) throw new Error("Context refresh failed");
  const data = await res.json();
  return data.summarized_context || "";
}

