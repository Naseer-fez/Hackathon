import React from "react";
import { AlertTriangle, CheckCircle2, ShieldAlert, ChevronRight } from "lucide-react";
import { AudioPlayerButton } from "./AudioPlayerButton";
import type { StandardRecommendation } from "../types";

interface RecommendationCardProps {
  rec: StandardRecommendation;
  isSelected: boolean;
  onSelect: () => void;
}

export const RecommendationCard: React.FC<RecommendationCardProps> = ({
  rec,
  isSelected,
  onSelect,
}) => {
  const std = rec.standard;
  const isQco = std.mandatory_qco.is_mandatory;
  const isSuperseded = Boolean(rec.deprecation_warning);
  const audioText = `${std.is_code} ${std.title}. ${std.scope}. ${rec.certification_alert}`;

  return (
    <div
      onClick={onSelect}
      className={`p-4 rounded-2xl border transition-all cursor-pointer ${
        isSelected
          ? "bg-slate-800/90 border-blue-500 ring-2 ring-blue-500/20 shadow-xl shadow-blue-950/40"
          : "bg-slate-900/60 border-slate-800 hover:border-slate-700 hover:bg-slate-800/40"
      }`}
    >
      <div className="flex items-start justify-between gap-3 mb-2.5">
        <div>
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-bold text-base text-white tracking-wide">{std.is_code}</span>
            <span className="text-xs text-slate-400">:{std.year}</span>
            {std.reaffirmation_year && (
              <span className="text-[10px] font-semibold bg-blue-500/10 text-blue-400 border border-blue-500/30 px-2 py-0.5 rounded-md">
                Reaffirmed {std.reaffirmation_year}
              </span>
            )}
            <span className="text-[10px] uppercase font-bold bg-slate-800 text-slate-300 px-2 py-0.5 rounded-md">
              {std.division}
            </span>
          </div>
          <h3 className="font-medium text-sm text-slate-200 mt-1 leading-snug">{std.title}</h3>
        </div>
        <div className="text-right shrink-0">
          <div className="text-xs font-bold text-emerald-400">
            {Math.round(rec.relevance_score * 100)}% Match
          </div>
          <div className="w-16 h-1.5 bg-slate-700 rounded-full mt-1 overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-emerald-500 to-teal-400 rounded-full"
              style={{ width: `${Math.min(rec.relevance_score * 100, 100)}%` }}
            />
          </div>
        </div>
      </div>

      <p className="text-xs text-slate-400 line-clamp-2 mb-3">{std.scope}</p>

      {isSuperseded && (
        <div className="mb-2.5 flex items-center gap-2 bg-red-950/40 border border-red-800/60 p-2 rounded-xl text-xs text-red-300">
          <AlertTriangle className="w-4 h-4 text-red-400 shrink-0" />
          <span>{rec.deprecation_warning}</span>
        </div>
      )}

      <div className="flex items-center justify-between gap-2 pt-2 border-t border-slate-800/60 text-xs">
        <div className="flex items-center gap-2 flex-wrap">
          {isQco ? (
            <span className="flex items-center gap-1 text-[11px] font-semibold text-amber-300 bg-amber-500/10 border border-amber-500/30 px-2 py-0.5 rounded-lg">
              <ShieldAlert className="w-3 h-3 text-amber-400" />
              {std.mandatory_qco.scheme} Mandatory
            </span>
          ) : (
            <span className="flex items-center gap-1 text-[11px] text-slate-400 bg-slate-800/60 px-2 py-0.5 rounded-lg">
              <CheckCircle2 className="w-3 h-3 text-slate-500" />
              Voluntary
            </span>
          )}
          <AudioPlayerButton text={audioText} label="Listen" />
        </div>
        <div className="flex items-center gap-1 text-blue-400 font-medium text-[11px]">
          <span>View Spec</span>
          <ChevronRight className="w-3.5 h-3.5" />
        </div>
      </div>
    </div>
  );
};
