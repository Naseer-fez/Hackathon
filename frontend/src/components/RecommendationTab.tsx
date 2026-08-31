import React, { useEffect, useState } from "react";
import { SpotlightSearch } from "./SpotlightSearch";
import { GlassSpecCard } from "./GlassSpecCard";
import { LlmExplanationCard } from "./LlmExplanationCard";
import { AlliedStandardsView } from "./AlliedStandardsView";
import { ClauseGeneratorView } from "./ClauseGeneratorView";
import { fetchRecommendations } from "../services/api.service";
import type { RecommendationResponse } from "../types";
import { clsx } from "clsx";

export const RecommendationTab: React.FC = () => {
  const [query, setQuery] = useState("Solar PV module for rooftop installation");
  const [division, setDivision] = useState("");
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<RecommendationResponse | null>(null);
  const [selectedIdx, setSelectedIdx] = useState(0);

  const divisions = ["All", "Civil", "Electrical", "Electronics", "Solar"];

  const handleSearch = async (customQ?: string) => {
    const q = customQ || query;
    if (!q.trim()) return;
    setLoading(true);
    try {
      const divParam = division === "All" || !division ? undefined : division;
      const res = await fetchRecommendations(q, divParam);
      setData(res); setSelectedIdx(0);
    } catch {
      setData(null);
    } finally { setLoading(false); }
  };

  useEffect(() => { handleSearch(); }, [division]);

  const selectedRec = data?.recommendations[selectedIdx] || null;

  return (
    <div className="space-y-8 flex flex-col items-center">
      {/* Search & Filters */}
      <div className="w-full max-w-3xl space-y-4">
        <SpotlightSearch query={query} setQuery={setQuery} onSearch={() => handleSearch()} loading={loading} />
        
        <div className="flex justify-center">
          <div className="apple-glass-dark p-1 rounded-full flex gap-1">
            {divisions.map(div => (
              <button
                key={div}
                onClick={() => setDivision(div)}
                className={clsx(
                  "px-4 py-1.5 rounded-full text-xs font-medium transition-all",
                  division === div || (div === "All" && !division) ? "bg-white/20 text-white shadow-md" : "text-white/60 hover:text-white hover:bg-white/5"
                )}
              >
                {div}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="w-full grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Column: Spec Cards */}
        <div className="lg:col-span-5 space-y-4">
          <div className="text-xs font-bold text-white/40 uppercase tracking-wider pl-2">
            Recommended Standards ({data?.total_matches || 0})
          </div>
          {loading ? (
            <div className="apple-glass p-8 text-center text-sm text-white/40 rounded-3xl animate-pulse">
              Running semantic inference...
            </div>
          ) : (
            data?.recommendations.map((rec, i) => (
              <GlassSpecCard key={rec.standard.is_code} rec={rec} isSelected={selectedIdx === i} onSelect={() => setSelectedIdx(i)} />
            ))
          )}
        </div>

        {/* Right Column: Details */}
        <div className="lg:col-span-7 space-y-6 sticky top-28">
          {selectedRec ? (
            <>
              <LlmExplanationCard query={query} isCode={selectedRec.standard.is_code} title={selectedRec.standard.title} />
              <AlliedStandardsView rec={selectedRec} />
              <ClauseGeneratorView rec={selectedRec} />
            </>
          ) : (
            <div className="apple-glass p-12 text-center text-sm text-white/40 rounded-3xl">
              Select a standard to view its normative graph and tender clauses.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

