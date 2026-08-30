import React, { useEffect, useState } from "react";
import { SearchBar } from "./SearchBar";
import { RecommendationCard } from "./RecommendationCard";
import { LlmExplanationCard } from "./LlmExplanationCard";
import { AlliedStandardsView } from "./AlliedStandardsView";
import { ClauseGeneratorView } from "./ClauseGeneratorView";
import { fetchRecommendations } from "../services/api.service";
import type { RecommendationResponse } from "../types";

export const RecommendationTab: React.FC = () => {
  const [query, setQuery] = useState("Solar PV module for rooftop installation");
  const [division, setDivision] = useState("");
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<RecommendationResponse | null>(null);
  const [selectedIdx, setSelectedIdx] = useState(0);

  const handleSearch = async (customQ?: string) => {
    const q = customQ || query;
    if (!q.trim()) return;
    setLoading(true);
    try {
      const res = await fetchRecommendations(q, division || undefined);
      setData(res);
      setSelectedIdx(0);
    } catch {
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    handleSearch();
  }, []);

  const selectedRec = data?.recommendations[selectedIdx] || null;

  return (
    <div className="space-y-6">
      <SearchBar
        query={query}
        setQuery={setQuery}
        onSearch={handleSearch}
        division={division}
        setDivision={setDivision}
        loading={loading}
      />

      {data && data.detected_language !== "en" && (
        <div className="bg-blue-950/40 border border-blue-800/60 p-3 rounded-2xl text-xs text-blue-300 flex items-center justify-between">
          <span>Indic query ({data.detected_language.toUpperCase()}): <strong>{data.translated_query}</strong></span>
          <span className="text-slate-400">{data.latency_ms} ms</span>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        <div className="lg:col-span-5 space-y-3">
          <div className="text-xs font-bold text-slate-400 uppercase tracking-wider px-1">
            Recommended Standards ({data?.total_matches || 0})
          </div>
          {loading ? (
            <div className="p-8 text-center text-xs text-slate-400 bg-slate-900/60 rounded-2xl animate-pulse">
              Running semantic inference...
            </div>
          ) : (
            data?.recommendations.map((rec, i) => (
              <RecommendationCard
                key={rec.standard.is_code}
                rec={rec}
                isSelected={selectedIdx === i}
                onSelect={() => setSelectedIdx(i)}
              />
            ))
          )}
        </div>

        <div className="lg:col-span-7 space-y-6 sticky top-20">
          {selectedRec ? (
            <>
              <LlmExplanationCard
                query={query}
                isCode={selectedRec.standard.is_code}
                title={selectedRec.standard.title}
              />
              <AlliedStandardsView rec={selectedRec} />
              <ClauseGeneratorView rec={selectedRec} />
            </>
          ) : (
            <div className="p-12 text-center text-xs text-slate-500 bg-slate-900/40 rounded-2xl">
              Select a standard from the list to view allied normative links and tender clauses.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

