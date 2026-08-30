import React, { useEffect, useState } from "react";
import { Navbar } from "./components/Navbar";
import { SearchBar } from "./components/SearchBar";
import { RecommendationCard } from "./components/RecommendationCard";
import { AlliedStandardsView } from "./components/AlliedStandardsView";
import { ClauseGeneratorView } from "./components/ClauseGeneratorView";
import { KnowledgeGraphView } from "./components/KnowledgeGraphView";
import { TenderAnalyzerView } from "./components/TenderAnalyzerView";
import { QcoExplorerView } from "./components/QcoExplorerView";
import { GemSimulatorView } from "./components/GemSimulatorView";
import { fetchRecommendations } from "./services/api.service";
import type { RecommendationResponse } from "./types";

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState("recommend");
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
    <div className="min-h-screen bg-[#070c18] text-slate-100 flex flex-col font-sans selection:bg-blue-600">
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} />

      <main className="flex-1 max-w-7xl w-full mx-auto p-6 space-y-6">
        {activeTab === "recommend" && (
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
                <span>Indic query detected ({data.detected_language.toUpperCase()}). Translated: <strong>{data.translated_query}</strong></span>
                <span className="text-slate-400">{data.latency_ms} ms</span>
              </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
              <div className="lg:col-span-5 space-y-3">
                <div className="text-xs font-bold text-slate-400 uppercase tracking-wider px-1">
                  Recommended Standards ({data?.total_matches || 0})
                </div>
                {loading ? (
                  <div className="p-8 text-center text-xs text-slate-400 bg-slate-900/60 rounded-2xl animate-pulse">Running semantic inference...</div>
                ) : data?.recommendations.map((rec, i) => (
                  <RecommendationCard
                    key={rec.standard.is_code}
                    rec={rec}
                    isSelected={selectedIdx === i}
                    onSelect={() => setSelectedIdx(i)}
                  />
                ))}
              </div>

              <div className="lg:col-span-7 space-y-6 sticky top-20">
                {selectedRec ? (
                  <>
                    <AlliedStandardsView rec={selectedRec} />
                    <ClauseGeneratorView rec={selectedRec} />
                  </>
                ) : (
                  <div className="p-12 text-center text-xs text-slate-500 bg-slate-900/40 rounded-2xl">
                    Select a standard from the recommendations list to view allied normative links and tender clauses.
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {activeTab === "tender" && <TenderAnalyzerView />}
        {activeTab === "graph" && <KnowledgeGraphView />}
        {activeTab === "qco" && <QcoExplorerView />}
        {activeTab === "gem" && <GemSimulatorView />}
      </main>
    </div>
  );
};

export default App;
