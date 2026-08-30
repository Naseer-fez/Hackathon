import React from "react";
import { Search, Sparkles, X } from "lucide-react";
import { VoiceInputButton } from "./VoiceInputButton";

interface SearchBarProps {
  query: string;
  setQuery: (q: string) => void;
  onSearch: (customQuery?: string) => void;
  division: string;
  setDivision: (d: string) => void;
  loading: boolean;
}

export const SearchBar: React.FC<SearchBarProps> = ({
  query,
  setQuery,
  onSearch,
  division,
  setDivision,
  loading,
}) => {
  const suggestions = [
    { label: "सौर पैनल व इनवर्टर", query: "सौर पैनल और ग्रिड इनवर्टर" },
    { label: "TMT Rebars Fe 500D", query: "High strength TMT steel rebar Fe 500D for RCC" },
    { label: "LED Street Light 120W", query: "Outdoor LED street lighting luminaire 120W IP66" },
    { label: "PVC Insulated Wire", query: "PVC insulated copper cable 1100V FRLS" },
    { label: "Fire Extinguisher ABC", query: "Portable ABC powder fire extinguisher" },
  ];

  const handleVoiceTranscription = (text: string) => {
    setQuery(text);
    onSearch(text);
  };

  return (
    <div className="w-full space-y-3">
      <div className="relative flex items-center bg-slate-900/90 border border-slate-700/80 rounded-2xl p-1.5 shadow-xl shadow-black/40 focus-within:border-blue-500 focus-within:ring-2 focus-within:ring-blue-500/20 transition-all">
        <div className="pl-3.5 text-slate-400">
          <Search className="w-5 h-5" />
        </div>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && onSearch()}
          placeholder="Describe product or speak voice query (e.g. '11kV transformer', 'सौर पैनल')..."
          className="w-full bg-transparent px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none"
        />
        {query && (
          <button onClick={() => setQuery("")} className="p-1.5 text-slate-400 hover:text-slate-200">
            <X className="w-4 h-4" />
          </button>
        )}
        <div className="mx-1">
          <VoiceInputButton onTranscription={handleVoiceTranscription} disabled={loading} />
        </div>
        <select
          value={division}
          onChange={(e) => setDivision(e.target.value)}
          aria-label="Filter by BIS Division Council"
          className="bg-slate-800 text-xs text-slate-300 rounded-xl px-3 py-2 border border-slate-700 focus:outline-none cursor-pointer"
        >
          <option value="">All Divisions</option>
          <option value="CED">Civil (CED)</option>
          <option value="ETD">Electrotechnical (ETD)</option>
          <option value="LITD">Electronics & IT (LITD)</option>
          <option value="MED">Mechanical (MED)</option>
          <option value="TXD">Textiles/Safety (TXD)</option>
        </select>
        <button
          onClick={() => onSearch()}
          disabled={loading || !query.trim()}
          className="ml-2 flex items-center gap-1.5 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 disabled:opacity-50 text-white text-xs font-semibold px-4 py-2.5 rounded-xl shadow-md shadow-blue-600/30 transition-all"
        >
          <Sparkles className="w-3.5 h-3.5" />
          <span>{loading ? "Matching..." : "Recommend"}</span>
        </button>
      </div>

      <div className="flex items-center gap-2 flex-wrap">
        <span className="text-[11px] text-slate-400 font-medium">Quick Queries:</span>
        {suggestions.map((item) => (
          <button
            key={item.label}
            onClick={() => {
              setQuery(item.query);
              onSearch(item.query);
            }}
            className="text-[11px] bg-slate-800/80 hover:bg-slate-700/80 text-slate-300 hover:text-blue-300 px-2.5 py-1 rounded-full border border-slate-700/60 transition-all"
          >
            {item.label}
          </button>
        ))}
      </div>
    </div>
  );
};
