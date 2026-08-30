import React, { useEffect, useState } from "react";
import { Sparkles, AlertCircle, RefreshCw } from "lucide-react";
import { explainStandard } from "../services/api.service";

interface LlmExplanationCardProps {
  query: string;
  isCode: string;
  title: string;
}

export const LlmExplanationCard: React.FC<LlmExplanationCardProps> = ({
  query,
  isCode,
  title,
}) => {
  const [explanation, setExplanation] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);

  const fetchExplanation = async (signal?: AbortSignal) => {
    if (!isCode) return;
    setLoading(true);
    setError(false);
    try {
      const res = await explainStandard(query, isCode, signal);
      setExplanation(res.explanation);
    } catch (err: any) {
      if (err.name === 'AbortError') return;
      setError(true);
      setExplanation(null);
    } finally {
      if (!signal?.aborted) {
        setLoading(false);
      }
    }
  };

  useEffect(() => {
    const controller = new AbortController();
    fetchExplanation(controller.signal);
    return () => controller.abort();
  }, [query, isCode]);

  return (
    <div className="bg-gradient-to-br from-indigo-950/40 via-slate-900/80 to-slate-900/80 border border-indigo-500/30 rounded-2xl p-5 space-y-3 shadow-xl shadow-indigo-950/20">
      <div className="flex items-center justify-between border-b border-indigo-900/40 pb-3">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-indigo-500/20 text-indigo-400">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-indigo-300">
              AI Technical Justification & Reasoning
            </h4>
            <span className="text-[11px] text-slate-400">
              Grounding: {isCode} - {title}
            </span>
          </div>
        </div>
        <button
          onClick={() => fetchExplanation()}
          disabled={loading}
          title="Regenerate reasoning"
          className="p-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-300 transition-all disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
        </button>
      </div>

      {loading ? (
        <div className="space-y-2 py-2 animate-pulse">
          <div className="h-3.5 bg-indigo-900/40 rounded w-3/4" />
          <div className="h-3.5 bg-indigo-900/30 rounded w-full" />
          <div className="h-3.5 bg-indigo-900/20 rounded w-5/6" />
        </div>
      ) : error ? (
        <div className="flex items-center gap-2 text-xs text-amber-400/90 py-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>Could not load AI explanation. Click refresh to retry.</span>
        </div>
      ) : (
        <div className="text-xs text-slate-200 leading-relaxed font-sans whitespace-pre-wrap bg-slate-950/60 p-3.5 rounded-xl border border-indigo-900/30">
          {explanation}
        </div>
      )}
    </div>
  );
};
