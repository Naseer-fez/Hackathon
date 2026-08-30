import React, { useState } from "react";
import { ShoppingCart, Send, ShieldAlert } from "lucide-react";
import { simulateGemBid } from "../services/api.service";

export const GemSimulatorView: React.FC = () => {
  const [bidId, setBidId] = useState("GEM-2026-B-882910");
  const [category, setCategory] = useState("Power Distribution");
  const [title, setTitle] = useState("Distribution Transformer 2500 kVA");
  const [spec, setSpec] = useState("Outdoor 33kV 3-phase oil immersed transformer with copper winding");
  const [result, setResult] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSimulate = async () => {
    setLoading(true);
    try {
      const res = await simulateGemBid(bidId, category, title, spec);
      setResult(res);
    } catch {
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-slate-900/80 p-5 rounded-2xl border border-slate-800 space-y-4">
        <h3 className="font-bold text-base text-white flex items-center gap-2">
          <ShoppingCart className="w-5 h-5 text-emerald-400" />
          Government e-Marketplace (GeM) Portal Webhook Simulator
        </h3>
        <p className="text-xs text-slate-400">
          Simulate how GeM e-procurement portal queries the BIS-SpecAI engine via webhook during bid creation to enforce mandatory Indian Standards.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
          <div>
            <label className="text-slate-400 font-medium block mb-1">GeM Bid ID</label>
            <input
              type="text"
              value={bidId}
              onChange={(e) => setBidId(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-slate-200 focus:outline-none focus:border-emerald-500"
            />
          </div>
          <div>
            <label className="text-slate-400 font-medium block mb-1">GeM Product Category</label>
            <input
              type="text"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-slate-200 focus:outline-none focus:border-emerald-500"
            />
          </div>
        </div>

        <div className="text-xs space-y-3">
          <div>
            <label className="text-slate-400 font-medium block mb-1">Product Title</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-slate-200 focus:outline-none focus:border-emerald-500"
            />
          </div>
          <div>
            <label className="text-slate-400 font-medium block mb-1">Buyer Technical Specifications</label>
            <textarea
              rows={2}
              value={spec}
              onChange={(e) => setSpec(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-slate-200 focus:outline-none focus:border-emerald-500"
            />
          </div>
        </div>

        <div className="flex justify-end">
          <button
            onClick={handleSimulate}
            disabled={loading}
            className="flex items-center gap-2 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 text-white text-xs font-semibold px-5 py-2.5 rounded-xl shadow-lg shadow-emerald-600/30"
          >
            <Send className="w-3.5 h-3.5" />
            <span>{loading ? "Triggering Webhook..." : "Dispatch GeM Validation Webhook"}</span>
          </button>
        </div>
      </div>

      {result && (
        <div className="bg-slate-900/90 border border-emerald-500/40 p-5 rounded-2xl space-y-3 text-xs">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2.5">
            <span className="font-bold text-sm text-white">GeM Bid #{result.bid_id} Validation Result</span>
            <span className="px-2.5 py-1 rounded-full bg-emerald-500/20 text-emerald-300 font-bold border border-emerald-500/30">
              {result.status}
            </span>
          </div>
          <div className="text-slate-300">
            <span className="font-semibold text-slate-100">Primary Standard:</span> {result.primary_standard}
          </div>
          {result.is_qco_mandatory && (
            <div className="bg-amber-950/20 border border-amber-800/40 p-2.5 rounded-xl text-amber-300 flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0" />
              <span>Mandatory QCO Enforced: {result.qco_order}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
