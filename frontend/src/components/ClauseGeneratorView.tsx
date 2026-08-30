import React, { useState } from "react";
import { Copy, Check, Download, FileCode, Shield } from "lucide-react";
import type { StandardRecommendation } from "../types";

interface ClauseGeneratorViewProps {
  rec: StandardRecommendation;
}

export const ClauseGeneratorView: React.FC<ClauseGeneratorViewProps> = ({ rec }) => {
  const [copied, setCopied] = useState(false);
  const std = rec.standard;

  const handleCopy = () => {
    navigator.clipboard.writeText(rec.sample_tender_clause);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const blob = new Blob([rec.sample_tender_clause], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `GeM_Tender_Clause_${std.is_code.replace(/\s+/g, "_")}.txt`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 space-y-4">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <FileCode className="w-4 h-4 text-emerald-400" />
          <h4 className="text-sm font-bold text-white">
            GeM / CPPP Specification Clause Builder
          </h4>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleCopy}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-all"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
            <span>{copied ? "Copied!" : "Copy Clause"}</span>
          </button>
          <button
            onClick={handleDownload}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-blue-600/20 hover:bg-blue-600/30 text-blue-300 border border-blue-500/30 transition-all"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Download</span>
          </button>
        </div>
      </div>

      <div className="bg-slate-950 p-4 rounded-xl border border-slate-800/80 font-mono text-[11px] leading-relaxed text-slate-300 whitespace-pre-wrap select-all">
        {rec.sample_tender_clause}
      </div>

      <div className="flex items-start gap-2 text-xs text-amber-300 bg-amber-950/20 border border-amber-900/40 p-3 rounded-xl">
        <Shield className="w-4 h-4 text-amber-400 mt-0.5 shrink-0" />
        <div>
          <span className="font-semibold">Statutory Advisory: </span>
          <span>{rec.certification_alert}</span>
        </div>
      </div>
    </div>
  );
};
