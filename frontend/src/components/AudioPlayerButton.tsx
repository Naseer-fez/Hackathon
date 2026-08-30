import React, { useRef, useState } from "react";
import { Volume2, VolumeX, Loader2 } from "lucide-react";
import { synthesizeSpeechAudio } from "../services/pipeline.service";

interface AudioPlayerButtonProps {
  text: string;
  label?: string;
}

export const AudioPlayerButton: React.FC<AudioPlayerButtonProps> = ({
  text,
  label = "Listen",
}) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [loading, setLoading] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const handlePlay = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (isPlaying && audioRef.current) {
      audioRef.current.pause();
      setIsPlaying(false);
      return;
    }

    setLoading(true);
    try {
      const audioBlob = await synthesizeSpeechAudio(text);
      const audioUrl = URL.createObjectURL(audioBlob);
      const audio = new Audio(audioUrl);
      audioRef.current = audio;

      audio.onended = () => {
        setIsPlaying(false);
        URL.revokeObjectURL(audioUrl);
      };
      audio.onerror = () => {
        setIsPlaying(false);
        URL.revokeObjectURL(audioUrl);
      };

      await audio.play();
      setIsPlaying(true);
    } catch {
      setIsPlaying(false);
    } finally {
      setLoading(false);
    }
  };

  return (
    <button
      type="button"
      onClick={handlePlay}
      disabled={loading || !text.trim()}
      title="Listen to AI Summary (Local TTS)"
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium border transition-all ${
        isPlaying
          ? "bg-blue-600/30 border-blue-500 text-blue-300 ring-2 ring-blue-500/30"
          : "bg-slate-800/80 hover:bg-slate-700/80 border-slate-700 text-slate-300 hover:text-white"
      }`}
    >
      {loading ? (
        <Loader2 className="w-3.5 h-3.5 animate-spin" />
      ) : isPlaying ? (
        <VolumeX className="w-3.5 h-3.5 text-blue-400" />
      ) : (
        <Volume2 className="w-3.5 h-3.5 text-slate-400" />
      )}
      <span>{isPlaying ? "Playing" : label}</span>
    </button>
  );
};
