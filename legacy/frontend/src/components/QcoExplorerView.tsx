import React, { useEffect, useState } from "react";
import { Scale, Search, ShieldCheck } from "lucide-react";
import { fetchQcoList } from "../services/api.service";
import type { MandatoryQCO } from "../types";

export const QcoExplorerView: React.FC = () => {
  const [qcos, setQcos] = useState<Record<string, MandatoryQCO>>({});
  const [filter, setFilter] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchQcoList()
      .then((data) => setQcos(data))
      .catch(() => setQcos({}))
      .finally(() => setLoading(false));
  }, []);

  const entries = Object.entries(qcos).filter(
    ([code, q]) =>
      code.toLowerCase().includes(filter.toLowerCase()) ||
      q.issuing_ministry.toLowerCase().includes(filter.toLowerCase()) ||
      q.order_number.toLowerCase().includes(filter.toLowerCase())
  );

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between bg-slate-900/80 p-4 rounded-2xl border border-slate-800 gap-4 flex-wrap">
        <div>
          <h3 className="font-bold text-base text-white flex items-center gap-2">
            <Scale className="w-5 h-5 text-amber-400" />
            Mandatory Quality Control Orders (QCO) Registry
          </h3>
          <p className="text-xs text-slate-400">
            Official Indian standards under compulsory BIS ISI Mark & CRS certification orders.
          </p>
        </div>
        <div className="relative min-w-[240px]">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            placeholder="Filter by IS code, ministry, order..."
            className="w-full bg-slate-950 border border-slate-700/80 rounded-xl pl-9 pr-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-amber-500"
          />
        </div>
      </div>

      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-xs text-slate-400">Loading QCO records...</div>
        ) : entries.length === 0 ? (
          <div className="p-8 text-center text-xs text-slate-500">No matching QCO records found.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950 text-slate-400 font-semibold border-b border-slate-800">
                <tr>
                  <th className="p-3.5">Standard Code</th>
                  <th className="p-3.5">Certification Scheme</th>
                  <th className="p-3.5">Gazette Order</th>
                  <th className="p-3.5">Issuing Ministry</th>
                  <th className="p-3.5">Effective Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {entries.map(([code, q]) => (
                  <tr key={code} className="hover:bg-slate-800/40 transition-colors">
                    <td className="p-3.5 font-bold text-white">{code}</td>
                    <td className="p-3.5">
                      <span className="inline-flex items-center gap-1 font-semibold text-amber-300 bg-amber-500/10 border border-amber-500/30 px-2 py-0.5 rounded-lg text-[11px]">
                        <ShieldCheck className="w-3 h-3 text-amber-400" />
                        {q.scheme}
                      </span>
                    </td>
                    <td className="p-3.5 text-slate-300">{q.order_number || "Statutory QCO"}</td>
                    <td className="p-3.5 text-slate-300">{q.issuing_ministry}</td>
                    <td className="p-3.5 text-slate-400">{q.effective_date || "Active"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
