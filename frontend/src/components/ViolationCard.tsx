import React, { useState } from "react";
import { AlertTriangle, ChevronRight, FileText } from "lucide-react";
import { clsx } from "clsx";
import { motion, AnimatePresence } from "framer-motion";

interface ViolationCardProps {
  violation: { clause: string; issue: string; snippet: string; requirement: string; severity?: string };
}

export const ViolationCard: React.FC<ViolationCardProps> = ({ violation }) => {
  const [open, setOpen] = useState(false);
  const isHigh = violation.severity === "high";

  return (
    <>
      <div 
        onClick={() => setOpen(true)}
        className="apple-glass p-4 rounded-2xl cursor-pointer hover:bg-white/10 transition-all flex items-start gap-4 group"
      >
        <div className={clsx("p-2 rounded-xl mt-1", isHigh ? "bg-apple-red/20 text-apple-red" : "bg-apple-amber/20 text-apple-amber")}>
          <AlertTriangle className="w-5 h-5" />
        </div>
        <div className="flex-1">
          <h4 className="text-white/90 font-medium mb-1">Clause {violation.clause}: {violation.issue}</h4>
          <p className="text-sm text-white/50 line-clamp-1">BIS Requirement: {violation.requirement}</p>
        </div>
        <ChevronRight className="w-5 h-5 text-white/30 group-hover:text-white/80 mt-2" />
      </div>

      <AnimatePresence>
        {open && (
          <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
            <motion.div 
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              className="absolute inset-0 bg-black/60 backdrop-blur-sm" 
              onClick={() => setOpen(false)}
            />
            <motion.div 
              initial={{ scale: 0.95, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.95, opacity: 0 }}
              className="apple-glass-dark w-full max-w-2xl rounded-3xl p-6 relative z-10 overflow-hidden"
            >
              <h3 className="text-lg font-semibold text-white/90 mb-4 flex items-center gap-2">
                <FileText className="w-5 h-5 text-apple-blue" />
                Original Document Snippet
              </h3>
              <div className="bg-white/5 border border-white/10 rounded-xl p-4 mb-4">
                <p className="text-sm font-mono text-white/80 leading-relaxed whitespace-pre-wrap">
                  "... {violation.snippet} ..."
                </p>
              </div>
              <div className="flex flex-col gap-2">
                <div className="text-sm">
                  <span className="text-white/40">Buyer Specification:</span> <span className="text-apple-red/90">{violation.issue}</span>
                </div>
                <div className="text-sm">
                  <span className="text-white/40">Required BIS Clause:</span> <span className="text-apple-mint/90">{violation.requirement}</span>
                </div>
              </div>
              <button onClick={() => setOpen(false)} className="mt-6 w-full py-3 apple-glass rounded-xl text-white/90 font-medium hover:bg-white/10 transition-colors">
                Close Inspector
              </button>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </>
  );
};
