import React, { useState } from "react";
import { ShoppingCart, Send, ShieldAlert, CheckCircle2 } from "lucide-react";
import { simulateGemBid } from "../services/api.service";
import { clsx } from "clsx";

export const GemSimulatorView: React.FC = () => {
  const [formData, setFormData] = useState({ id: "GEM-2026-B-882910", cat: "Power Distribution", title: "Distribution Transformer 2500 kVA", spec: "Outdoor 33kV 3-phase oil immersed transformer with copper winding" });
  const [result, setResult] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSimulate = async () => {
    setLoading(true);
    try { setResult(await simulateGemBid(formData.id, formData.cat, formData.title, formData.spec)); }
    catch { setResult(null); }
    finally { setLoading(false); }
  };

  return (
    <div className="w-full max-w-3xl mx-auto space-y-6">
      <div className="apple-glass rounded-3xl p-6 md:p-8 space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h3 className="text-xl font-bold text-white flex items-center gap-2 tracking-tight">
              <ShoppingCart className="w-5 h-5 text-apple-mint" /> GeM Webhook Simulator
            </h3>
            <p className="text-sm text-white/50 mt-1">Simulate how GeM portal queries BIS-SpecAI for compliance during bid creation.</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          {[
            { label: "GeM Bid ID", key: "id" }, { label: "Product Category", key: "cat" },
            { label: "Product Title", key: "title" }, { label: "Technical Specs", key: "spec", isTextArea: true }
          ].map((f) => (
            <div key={f.key} className={f.isTextArea ? "md:col-span-2" : ""}>
              <label className="text-white/60 font-medium block mb-1.5 ml-1">{f.label}</label>
              {f.isTextArea ? (
                <textarea rows={2} value={formData[f.key as keyof typeof formData]} onChange={(e) => setFormData(p => ({ ...p, [f.key]: e.target.value }))} className="w-full bg-black/40 border border-white/10 rounded-2xl p-3 text-white focus:outline-none focus:border-apple-mint" />
              ) : (
                <input value={formData[f.key as keyof typeof formData]} onChange={(e) => setFormData(p => ({ ...p, [f.key]: e.target.value }))} className="w-full bg-black/40 border border-white/10 rounded-2xl p-3 text-white focus:outline-none focus:border-apple-mint" />
              )}
            </div>
          ))}
        </div>

        <div className="flex justify-end pt-2">
          <button onClick={handleSimulate} disabled={loading} className="flex items-center gap-2 bg-apple-mint/20 hover:bg-apple-mint/30 text-apple-mint border border-apple-mint/30 text-sm font-semibold px-6 py-3 rounded-full shadow-lg shadow-apple-mint/20 transition-all">
            <Send className={clsx("w-4 h-4", loading && "animate-pulse")} />
            <span>{loading ? "Triggering..." : "Dispatch GeM Validation Webhook"}</span>
          </button>
        </div>
      </div>

      {result && (
        <div className="apple-glass-dark border border-apple-mint/40 p-6 rounded-3xl space-y-4 shadow-[0_0_40px_rgba(48,209,88,0.15)]">
          <div className="flex items-center justify-between border-b border-white/10 pb-4">
            <span className="font-semibold text-white tracking-tight flex items-center gap-2"><CheckCircle2 className="w-5 h-5 text-apple-mint"/> Bid Validation Successful</span>
            <span className="px-3 py-1 rounded-full bg-apple-mint/20 text-apple-mint text-xs font-bold uppercase tracking-wider">{result.status}</span>
          </div>
          <div className="text-white/70 text-sm">
            <span className="text-white/40">Primary Standard:</span> <span className="font-medium text-white/90">{result.primary_standard}</span>
          </div>
          {result.is_qco_mandatory && (
            <div className="bg-apple-red/20 border border-apple-red/30 p-3 rounded-xl text-apple-red text-sm flex items-center gap-2 font-medium">
              <ShieldAlert className="w-5 h-5" />
              Mandatory QCO Enforced: {result.qco_order}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
