import React from "react";
import { motion } from "framer-motion";
import { LucideIcon } from "lucide-react";
import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

interface NavPillProps {
  id: string;
  label: string;
  icon: LucideIcon;
  active: boolean;
  onClick: () => void;
}

export const NavPill: React.FC<NavPillProps> = ({ id, label, icon: Icon, active, onClick }) => {
  return (
    <button
      onClick={onClick}
      className={twMerge(
        clsx(
          "relative flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-colors z-10",
          active ? "text-white" : "text-white/60 hover:text-white/90 hover:bg-white/5"
        )
      )}
    >
      {active && (
        <motion.div
          layoutId="activeTabPill"
          className="absolute inset-0 apple-glass-dark rounded-full -z-10 shadow-lg shadow-apple-blue/20"
          initial={false}
          transition={{ type: "spring", stiffness: 400, damping: 30 }}
        />
      )}
      <Icon className={clsx("w-4 h-4", active && "text-apple-blue")} />
      <span className="hidden sm:inline">{label}</span>
    </button>
  );
};
