import React from "react";
import { ShieldCheck, BookOpen, FileCheck, Share2, Scale, ShoppingCart } from "lucide-react";
import { NavPill } from "./NavPill";

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

export const Navbar: React.FC<NavbarProps> = ({ activeTab, setActiveTab }) => {
  const navItems = [
    { id: "recommend", label: "Standards", icon: BookOpen },
    { id: "tender", label: "Auditor", icon: FileCheck },
    { id: "graph", label: "Graph", icon: Share2 },
    { id: "qco", label: "QCOs", icon: Scale },
    { id: "gem", label: "GeM", icon: ShoppingCart },
  ];

  return (
    <div className="fixed top-6 left-0 right-0 z-50 flex justify-center pointer-events-none">
      <header className="pointer-events-auto apple-glass rounded-full px-2 py-2 flex items-center gap-4">
        {/* Logo/Status Section */}
        <div className="flex items-center gap-3 pl-3 pr-2 border-r border-white/10">
          <div className="relative flex items-center justify-center">
            <ShieldCheck className="w-5 h-5 text-white" />
            <span className="absolute -top-1 -right-1 w-2 h-2 rounded-full bg-apple-mint animate-pulse shadow-[0_0_8px_rgba(48,209,88,0.8)]" title="System Online & Accelerated" />
          </div>
          <h1 className="font-semibold tracking-tight text-white/95 pr-2 hidden md:block">
            BIS-SpecAI
          </h1>
        </div>

        {/* Navigation Pills */}
        <nav className="flex items-center gap-1">
          {navItems.map((item) => (
            <NavPill
              key={item.id}
              id={item.id}
              label={item.label}
              icon={item.icon}
              active={activeTab === item.id}
              onClick={() => setActiveTab(item.id)}
            />
          ))}
        </nav>
      </header>
    </div>
  );
};
