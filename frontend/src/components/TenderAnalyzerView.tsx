import React, { useState } from "react";
import { Upload, Loader2 } from "lucide-react";
import { analyzeTenderDocument } from "../services/api.service";
import { ViolationCard } from "./ViolationCard";
import { clsx } from "clsx";
import type { TenderAnalysisReport } from "../types";

export const TenderAnalyzerView: React.FC<{ setPdfText: (text: string) => void }> = ({ setPdfText }) => {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState<TenderAnalysisReport | null>(null);
  const [dragActive, setDragActive] = useState(false);

  const handleAnalyze = async (f: File) => {
    setLoading(true); setFile(f);
    try {
      const res = await analyzeTenderDocument(f, undefined);
      setReport(res);
      if (res.raw_text) setPdfText(res.raw_text);
    } catch {
      setReport(null);
    } finally { setLoading(false); }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault(); setDragActive(false);
    if (e.dataTransfer.files?.[0]) handleAnalyze(e.dataTransfer.files[0]);
  };

  return (
    <div className="w-full max-w-4xl mx-auto space-y-8 flex flex-col items-center">
      <div className="text-center space-y-2 mb-4">
        <h2 className="text-2xl font-semibold text-white/95 tracking-tight">Tender Radar</h2>
        <p className="text-sm text-white/50">Audit specifications against required BIS clauses</p>
      </div>

      <div 
        onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
        onDragLeave={() => setDragActive(false)}
        onDrop={handleDrop}
        className={clsx(
          "w-full h-48 apple-glass rounded-3xl flex flex-col items-center justify-center transition-all cursor-pointer relative overflow-hidden",
          dragActive ? "bg-apple-blue/20 border-apple-blue shadow-[0_0_40px_rgba(0,113,227,0.3)]" : "hover:bg-white/10"
        )}
      >
        <input type="file" accept=".pdf,.docx" onChange={(e) => e.target.files?.[0] && handleAnalyze(e.target.files[0])} className="absolute inset-0 opacity-0 cursor-pointer z-10" />
        {loading ? (
          <div className="flex flex-col items-center gap-3 text-apple-blue">
            <Loader2 className="w-8 h-8 animate-spin" />
            <span className="text-sm font-medium">Parsing Document Pages...</span>
          </div>
        ) : (
          <>
            <div className="p-4 bg-white/5 rounded-full mb-3"><Upload className="w-6 h-6 text-white/60" /></div>
            <span className="text-white/80 font-medium">{file ? file.name : "Drop Tender Document Here"}</span>
            <span className="text-xs text-white/40 mt-1">PDF or DOCX</span>
          </>
        )}
      </div>

      {report && (
        <div className="w-full space-y-4">
          <h3 className="text-lg font-semibold text-white/90">Specification Compliance Findings ({report.compliance_issues.length})</h3>
          <div className="grid gap-3">
            {report.compliance_issues.map((issue, i) => (
              <ViolationCard key={i} violation={{
                clause: issue.category,
                issue: issue.issue_text,
                snippet: `Item in ${report.document_name}`,
                requirement: issue.corrective_action,
                severity: issue.severity.toLowerCase()
              }} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
