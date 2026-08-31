import React from "react";
import { Search, Mic } from "lucide-react";
import { clsx } from "clsx";
import { motion, AnimatePresence } from "framer-motion";

interface SpotlightSearchProps {
  query: string;
  setQuery: (val: string) => void;
  onSearch: () => void;
  loading: boolean;
}

export const SpotlightSearch: React.FC<SpotlightSearchProps> = ({ query, setQuery, onSearch, loading }) => {
  const [isRecording, setIsRecording] = React.useState(false);

  return (
    <div className="relative max-w-2xl mx-auto w-full group">
      <div className={clsx(
        "apple-glass-dark rounded-2xl flex items-center p-2 transition-all",
        "focus-within:ring-2 focus-within:ring-apple-indigo/50 focus-within:bg-black/60"
      )}>
        <button
          type="button"
          onClick={() => onSearch()}
          disabled={loading || !query.trim()}
          title="Search"
          className="p-1 text-white/40 hover:text-white/90 disabled:opacity-40 transition-colors"
        >
          <Search className="w-5 h-5 ml-2 mr-2" />
        </button>
        
        <div className="flex-1 relative h-10 flex items-center">
          <AnimatePresence>
            {isRecording ? (
              <motion.div 
                initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                className="absolute inset-0 flex items-center"
              >
                <div className="w-full h-1 bg-apple-mint/50 rounded overflow-hidden">
                  <motion.div 
                    className="h-full bg-apple-mint origin-left"
                    animate={{ scaleX: [0.1, 1, 0.4, 0.8, 0.2] }}
                    transition={{ repeat: Infinity, duration: 1.2 }}
                  />
                </div>
              </motion.div>
            ) : (
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && onSearch()}
                placeholder="Search standards, e.g. Solar PV module, TMT bars..."
                className="w-full bg-transparent text-lg text-white/90 placeholder-white/30 focus:outline-none"
              />
            )}
          </AnimatePresence>
        </div>

        <div className="flex items-center gap-1.5 pr-2">
          {query && (
            <button 
              onClick={() => setQuery("")}
              className="px-2 py-1 text-white/40 hover:text-white/90 hover:bg-white/10 rounded-xl transition-colors text-xs"
              title="Clear"
            >
              Clear
            </button>
          )}
          <button
            onClick={() => onSearch()}
            disabled={loading || !query.trim()}
            className="px-3.5 py-1.5 bg-apple-blue hover:bg-apple-blue/80 disabled:opacity-40 text-white rounded-xl text-xs font-semibold transition-all shadow-md shadow-apple-blue/20"
          >
            {loading ? "Searching..." : "Search"}
          </button>
          <button 
            onClick={() => setIsRecording(!isRecording)}
            className={clsx("p-2 rounded-xl transition-colors", isRecording ? "text-apple-mint bg-apple-mint/20" : "text-white/40 hover:text-white/90 hover:bg-white/10")}
            title="Voice input"
          >
            <Mic className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
