import React, { useRef, useState } from "react";
import { Mic, MicOff } from "lucide-react";
import { transcribeVoiceAudio } from "../services/pipeline.service";

interface VoiceInputButtonProps {
  onTranscription: (text: string) => void;
  disabled?: boolean;
}

export const VoiceInputButton: React.FC<VoiceInputButtonProps> = ({
  onTranscription,
  disabled = false,
}) => {
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) audioChunksRef.current.push(event.data);
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: "audio/wav" });
        setIsTranscribing(true);
        try {
          const text = await transcribeVoiceAudio(audioBlob);
          if (text) onTranscription(text);
        } catch {
          // Silent fallback
        } finally {
          setIsTranscribing(false);
          stream.getTracks().forEach((t) => t.stop());
        }
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch {
      setIsRecording(false);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  return (
    <button
      type="button"
      onClick={isRecording ? stopRecording : startRecording}
      disabled={disabled || isTranscribing}
      title={isRecording ? "Stop Recording Voice" : "Record Voice Query (Local STT)"}
      className={`p-2 rounded-xl border transition-all flex items-center justify-center ${
        isRecording
          ? "bg-red-600/30 border-red-500 text-red-300 animate-pulse ring-2 ring-red-500/40"
          : isTranscribing
          ? "bg-amber-600/30 border-amber-500 text-amber-300 animate-spin"
          : "bg-slate-800/80 border-slate-700 text-slate-300 hover:text-blue-300 hover:border-blue-500"
      }`}
    >
      {isRecording ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
    </button>
  );
};
