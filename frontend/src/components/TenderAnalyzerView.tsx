import React, { useState } from "react";
import { Upload, FileText, ShieldCheck } from "lucide-react";
import { analyzeTenderDocument } from "../services/api.service";
import { TenderReportView } from "./TenderReportView";
import type { TenderAnalysisReport } from "../types";

export const TenderAnalyzerView: React.FC = () => {
  const [rawText, setRawText] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState<TenderAnalysisReport | null>(null);

  const handleAnalyze = async () => {
    if (!rawText.trim() && !file) return;
    setLoading(true);
    try {
      const res = await analyzeTenderDocument(file || undefined, rawText || undefined);
      setReport(res);
    } catch {
      setReport(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-slate-900/80 p-5 rounded-2xl border border-slate-800 space-y-4">
        <h3 className="font-bold text-base text-white flex items-center gap-2">
          <FileText className="w-5 h-5 text-blue-400" />
          Tender Specification Compliance Auditor
        </h3>
        <p className="text-xs text-slate-400">
          Upload PDF/DOCX tender documents or paste technical requirements to audit IS references, detect outdated standards, and map mandatory QCOs.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <textarea
              rows={4}
              value={rawText}
              onChange={(e) => setRawText(e.target.value)}
              placeholder="Paste schedule of requirements or tender specifications here..."
              className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-slate-200 focus:outline-none focus:border-blue-500"
            />
          </div>
          <div className="border-2 border-dashed border-slate-800 hover:border-blue-500/60 rounded-xl p-4 flex flex-col items-center justify-center text-center bg-slate-950/40 cursor-pointer relative">
            <Upload className="w-6 h-6 text-slate-400 mb-2" />
            <span className="text-xs text-slate-300 font-medium">
              {file ? file.name : "Upload Tender PDF / DOCX"}
            </span>
            <span className="text-[10px] text-slate-500 mt-1">Automatic parsing & specification extraction</span>
            <input
              type="file"
              accept=".pdf,.docx,.doc,.txt"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
              className="absolute inset-0 opacity-0 cursor-pointer"
            />
          </div>
        </div>

        <div className="flex justify-end">
          <button
            onClick={handleAnalyze}
            disabled={loading || (!rawText.trim() && !file)}
            className="flex items-center gap-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 text-white text-xs font-semibold px-5 py-2.5 rounded-xl shadow-lg shadow-blue-600/30 disabled:opacity-50"
          >
            <ShieldCheck className="w-4 h-4" />
            <span>{loading ? "Auditing Document..." : "Audit Tender Specifications"}</span>
          </button>
        </div>
      </div>

      {report && <TenderReportView report={report} />}
    </div>
  );
};
