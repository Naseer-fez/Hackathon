import React, { useState, useRef } from "react";
import { Sparkles, AlertCircle, RefreshCw } from "lucide-react";
import { explainStandardStream } from "../services/api.service";
import { clsx } from "clsx";

interface LlmExplanationCardProps {
  query: string;
  isCode: string;
  title: string;
}

export const LlmExplanationCard: React.FC<LlmExplanationCardProps> = ({ query, isCode, title }) => {
  const [displayedText, setDisplayedText] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);
  const textRef = useRef("");

  const fetchExplanation = async (signal?: AbortSignal) => {
    if (!isCode) return;
    setLoading(true);
    setError(false);
    setDisplayedText("");
    textRef.current = "";
    try {
      await explainStandardStream(query, isCode, (chunk) => {
        textRef.current += chunk;
        setDisplayedText(textRef.current);
      }, signal);
    } catch (err: any) {
      if (err.name === "AbortError") return;
      setError(true);
    } finally {
      if (!signal?.aborted) setLoading(false);
    }
  };

  return (
    <div className="apple-glass border-apple-indigo/40 rounded-3xl p-6 space-y-4 shadow-[0_0_40px_rgba(94,92,230,0.1)]">
      <div className="flex items-center justify-between border-b border-white/10 pb-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-full bg-apple-indigo/20 text-apple-indigo">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <h4 className="text-sm font-semibold text-white/90 tracking-tight">AI Technical Justification</h4>
            <span className="text-xs text-white/50">{isCode} - {title}</span>
          </div>
        </div>
        {displayedText && (
          <button
            onClick={() => fetchExplanation()}
            disabled={loading}
            className="p-2 rounded-full bg-white/5 hover:bg-white/10 text-white/60 hover:text-white transition-all disabled:opacity-50"
            title="Regenerate explanation"
          >
            <RefreshCw className={clsx("w-4 h-4", loading && "animate-spin text-apple-indigo")} />
          </button>
        )}
      </div>

      {!displayedText && !loading ? (
        <div className="flex flex-col items-center justify-center py-6 text-center space-y-3">
          <p className="text-xs text-white/50 max-w-md">
            Generate an AI evaluation comparing your procurement requirements against {isCode}.
          </p>
          <button
            onClick={() => fetchExplanation()}
            className="flex items-center gap-2 px-4 py-2 rounded-2xl bg-apple-indigo/20 hover:bg-apple-indigo/30 text-apple-indigo border border-apple-indigo/30 text-xs font-semibold transition-all shadow-lg shadow-apple-indigo/10"
          >
            <Sparkles className="w-4 h-4" />
            <span>Generate Technical Justification</span>
          </button>
        </div>
      ) : loading && !displayedText ? (
        <div className="space-y-3 py-2 animate-pulse">
          <div className="h-4 bg-white/10 rounded w-3/4" />
          <div className="h-4 bg-white/5 rounded w-full" />
          <div className="h-4 bg-white/5 rounded w-5/6" />
        </div>
      ) : error ? (
        <div className="flex items-center gap-2 text-sm text-apple-amber py-4 font-medium">
          <AlertCircle className="w-5 h-5 shrink-0" />
          <span>Could not load AI explanation. Click refresh to retry.</span>
        </div>
      ) : (
        <div className="text-sm text-white/80 leading-relaxed whitespace-pre-wrap">
          {displayedText}
          {loading && (
            <span className="inline-block w-1.5 h-4 ml-1 bg-apple-indigo animate-pulse align-middle" />
          )}
        </div>
      )}
    </div>
  );
};
