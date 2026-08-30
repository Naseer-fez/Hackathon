import React, { useState } from "react";
import { GitFork, FlaskConical, Shield, Wrench, CheckCircle } from "lucide-react";
import type { StandardRecommendation } from "../types";

interface AlliedStandardsViewProps {
  rec: StandardRecommendation;
}

export const AlliedStandardsView: React.FC<AlliedStandardsViewProps> = ({ rec }) => {
  const [tab, setTab] = useState<"normative" | "test" | "safety" | "install">("normative");
  const std = rec.standard;

  const tabs = [
    { id: "normative", label: "Normative References", icon: GitFork, count: std.normative_references.length },
    { id: "test", label: "Test Methods", icon: FlaskConical, count: std.test_methods.length },
    { id: "safety", label: "Safety Standards", icon: Shield, count: std.safety_standards.length },
    { id: "install", label: "Installation Codes", icon: Wrench, count: std.installation_standards.length },
  ];

  const getListForTab = () => {
    switch (tab) {
      case "normative": return std.normative_references;
      case "test": return std.test_methods;
      case "safety": return std.safety_standards;
      case "install": return std.installation_standards;
    }
  };

  const currentList = getListForTab();

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 space-y-4">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <h4 className="text-sm font-bold text-white flex items-center gap-2">
          <GitFork className="w-4 h-4 text-blue-400" />
          Allied & Cross-Referenced Standards for {std.is_code}
        </h4>
      </div>

      <div className="flex items-center gap-2 overflow-x-auto pb-1">
        {tabs.map((t) => {
          const Icon = t.icon;
          const active = tab === t.id;
          return (
            <button
              key={t.id}
              onClick={() => setTab(t.id as any)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-all ${
                active
                  ? "bg-blue-600/20 text-blue-300 border border-blue-500/40"
                  : "bg-slate-800/60 text-slate-400 hover:text-slate-200 border border-slate-700/50"
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              <span>{t.label}</span>
              <span className="ml-1 px-1.5 py-0.2 rounded-full bg-slate-700/60 text-[10px] text-slate-300">
                {t.count}
              </span>
            </button>
          );
        })}
      </div>

      <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
        {currentList.length === 0 ? (
          <p className="text-xs text-slate-500 italic py-4 text-center">
            No specific {tab} standards recorded for this standard.
          </p>
        ) : (
          currentList.map((item, idx) => (
            <div
              key={idx}
              className="flex items-start gap-2.5 bg-slate-800/40 border border-slate-800 p-2.5 rounded-xl text-xs text-slate-300 hover:border-slate-700"
            >
              <CheckCircle className="w-4 h-4 text-blue-400 mt-0.5 shrink-0" />
              <div className="flex-1">
                <span className="font-semibold text-slate-200">{item}</span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
