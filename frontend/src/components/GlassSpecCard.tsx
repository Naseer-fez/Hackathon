import React from "react";
import { ChevronRight } from "lucide-react";
import { clsx } from "clsx";
import type { StandardRecommendation } from "../types";

interface GlassSpecCardProps {
  rec: StandardRecommendation;
  isSelected: boolean;
  onSelect: () => void;
}

export const GlassSpecCard: React.FC<GlassSpecCardProps> = ({ rec, isSelected, onSelect }) => {
  const { standard, relevance_score } = rec;
  const matchPct = Math.round(relevance_score * 100);
  const isMandatory = standard.mandatory_qco?.is_mandatory;

  return (
    <div 
      onClick={onSelect}
      className={clsx(
        "group cursor-pointer apple-glass p-4 rounded-3xl transition-all duration-300 relative overflow-hidden",
        isSelected ? "border-apple-blue/50 bg-apple-blue/10" : "hover:border-white/20 hover:bg-white/5"
      )}
    >
      <div className="flex justify-between items-start mb-2">
        <div>
          <h3 className="text-lg font-semibold tracking-tight text-white/90">
            {standard.is_code}
          </h3>
          <div className="mt-1">
            {isMandatory ? (
              <span className="inline-flex px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-apple-red/20 text-apple-red border border-apple-red/30">
                Mandatory ISI Mark
              </span>
            ) : (
              <span className="inline-flex px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-apple-mint/20 text-apple-mint border border-apple-mint/30">
                Voluntary Scheme
              </span>
            )}
          </div>
        </div>
        
        {/* Similarity Ring Gauge */}
        <div className="relative w-10 h-10 flex items-center justify-center">
          <svg className="w-10 h-10 transform -rotate-90">
            <circle cx="20" cy="20" r="16" stroke="currentColor" strokeWidth="3" fill="transparent" className="text-white/10" />
            <circle cx="20" cy="20" r="16" stroke="currentColor" strokeWidth="3" fill="transparent" 
              strokeDasharray="100" strokeDashoffset={100 - matchPct}
              className={clsx("transition-all duration-1000", matchPct > 80 ? "text-apple-mint" : "text-apple-amber")} 
            />
          </svg>
          <span className="absolute text-[9px] font-bold text-white/80">{matchPct}%</span>
        </div>
      </div>

      <p className="text-sm text-white/60 leading-relaxed line-clamp-2 mt-2 pr-6">
        {standard.title}
      </p>

      {/* Expand Button */}
      <div className="absolute right-4 bottom-4">
        <div className={clsx(
          "w-6 h-6 rounded-full flex items-center justify-center transition-colors",
          isSelected ? "bg-apple-blue text-white" : "bg-white/10 text-white/40 group-hover:bg-white/20 group-hover:text-white"
        )}>
          <ChevronRight className="w-3.5 h-3.5" />
        </div>
      </div>
    </div>
  );
};
