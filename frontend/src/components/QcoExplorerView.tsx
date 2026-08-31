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
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row items-center justify-between apple-glass p-6 rounded-3xl gap-4">
        <div>
          <h3 className="text-lg font-bold text-white flex items-center gap-2">
            <Scale className="w-5 h-5 text-apple-amber" />
            Mandatory Quality Control Orders (QCO)
          </h3>
          <p className="text-sm text-white/50 mt-1">Official Indian standards under compulsory BIS ISI Mark certification.</p>
        </div>
        <div className="relative w-full sm:w-72">
          <Search className="w-4 h-4 text-white/40 absolute left-3 top-3" />
          <input
            type="text" value={filter} onChange={(e) => setFilter(e.target.value)}
            placeholder="Filter by IS code or ministry..."
            className="w-full bg-black/40 border border-white/10 rounded-full pl-9 pr-4 py-2 text-sm text-white focus:outline-none focus:border-apple-amber"
          />
        </div>
      </div>

      <div className="apple-glass rounded-3xl overflow-hidden border border-white/10">
        {loading ? (
          <div className="p-8 text-center text-sm text-white/40 animate-pulse">Loading QCO records...</div>
        ) : entries.length === 0 ? (
          <div className="p-8 text-center text-sm text-white/40">No matching QCO records found.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm whitespace-nowrap">
              <thead className="bg-white/5 text-white/40 border-b border-white/10">
                <tr>
                  <th className="p-4 font-medium">Standard Code</th>
                  <th className="p-4 font-medium">Scheme</th>
                  <th className="p-4 font-medium">Order Number</th>
                  <th className="p-4 font-medium">Issuing Ministry</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/10">
                {entries.map(([code, q]) => (
                  <tr key={code} className="hover:bg-white/5 transition-colors">
                    <td className="p-4 font-semibold text-white/90">{code}</td>
                    <td className="p-4">
                      <span className="inline-flex items-center gap-1 bg-apple-amber/20 text-apple-amber border border-apple-amber/30 px-2.5 py-1 rounded-full text-xs font-bold uppercase tracking-wider">
                        <ShieldCheck className="w-3.5 h-3.5" />
                        {q.scheme}
                      </span>
                    </td>
                    <td className="p-4 text-white/70 font-mono text-xs">{q.order_number || "Statutory QCO"}</td>
                    <td className="p-4 text-white/60">{q.issuing_ministry}</td>
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
