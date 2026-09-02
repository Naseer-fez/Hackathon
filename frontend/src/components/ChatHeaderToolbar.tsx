import React from "react";
import { Zap, Brain, RefreshCw, X } from "lucide-react";
import { clsx } from "clsx";

interface Props {
  mode: "fast" | "heavy";
  setMode: (m: "fast" | "heavy") => void;
  onRefreshContext: () => void;
  refreshing: boolean;
  onClose: () => void;
}

export const ChatHeaderToolbar: React.FC<Props> = ({
  mode,
  setMode,
  onRefreshContext,
  refreshing,
  onClose,
}) => {
  return (
    <div className="p-3 border-b border-white/10 flex flex-col gap-2 bg-white/5">
      <div className="flex justify-between items-center">
        <div className="flex items-center gap-2">
          <Brain className="w-4 h-4 text-apple-indigo" />
          <span className="text-xs font-semibold text-white/90 uppercase tracking-wider">
            Distributed Reasoning
          </span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={onRefreshContext}
            disabled={refreshing}
            title="Refresh & Compress Context"
            className="p-1 rounded text-white/60 hover:text-white hover:bg-white/10 transition-colors"
          >
            <RefreshCw className={clsx("w-3.5 h-3.5", refreshing && "animate-spin text-apple-indigo")} />
          </button>
          <button onClick={onClose} className="text-white/60 hover:text-white">
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      <div className="flex gap-1 bg-black/30 p-0.5 rounded-xl text-xs">
        <button
          onClick={() => setMode("fast")}
          className={clsx(
            "flex-1 flex items-center justify-center gap-1.5 py-1 rounded-lg font-medium transition-all",
            mode === "fast" ? "bg-apple-blue text-white shadow-sm" : "text-white/60 hover:text-white"
          )}
        >
          <Zap className="w-3 h-3" /> Fast (2B)
        </button>
        <button
          onClick={() => setMode("heavy")}
          className={clsx(
            "flex-1 flex items-center justify-center gap-1.5 py-1 rounded-lg font-medium transition-all",
            mode === "heavy" ? "bg-apple-indigo text-white shadow-sm" : "text-white/60 hover:text-white"
          )}
        >
          <Brain className="w-3 h-3" /> Heavy (Mac)
        </button>
      </div>
    </div>
  );
};
