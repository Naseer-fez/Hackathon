import React from "react";
import { ShieldCheck, BookOpen, FileCheck, Share2, Scale, ShoppingCart } from "lucide-react";

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

export const Navbar: React.FC<NavbarProps> = ({ activeTab, setActiveTab }) => {
  const navItems = [
    { id: "recommend", label: "Standards Recommender", icon: BookOpen },
    { id: "tender", label: "Tender Spec Auditor", icon: FileCheck },
    { id: "graph", label: "Knowledge Graph", icon: Share2 },
    { id: "qco", label: "Mandatory QCOs", icon: Scale },
    { id: "gem", label: "GeM Simulator", icon: ShoppingCart },
  ];

  return (
    <header className="sticky top-0 z-50 bg-[#0c1322]/90 backdrop-blur-md border-b border-slate-800 px-6 py-3.5 flex flex-wrap items-center justify-between gap-4">
      <div className="flex items-center gap-3">
        <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-blue-600 via-indigo-500 to-amber-500 flex items-center justify-center shadow-lg shadow-blue-500/20">
          <ShieldCheck className="w-6 h-6 text-white" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="font-bold text-lg tracking-tight bg-gradient-to-r from-white via-slate-100 to-blue-300 bg-clip-text text-transparent">
              BIS-SpecAI
            </h1>
            <span className="text-[10px] uppercase font-bold tracking-widest px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
              LIVE BIS v2.0
            </span>
          </div>
          <p className="text-xs text-slate-400">e-Procurement Indian Standards AI Engine</p>
        </div>
      </div>

      <nav className="flex items-center gap-1 bg-slate-900/80 p-1 rounded-xl border border-slate-800">
        {navItems.map((item) => {
          const Icon = item.icon;
          const active = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
                active
                  ? "bg-blue-600 text-white shadow-md shadow-blue-600/30"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>
    </header>
  );
};
