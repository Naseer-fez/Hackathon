import React, { useEffect, useState } from "react";
import { RefreshCw, ZoomIn, ZoomOut, Share2, Info } from "lucide-react";
import { fetchKnowledgeGraph } from "../services/api.service";
import { motion, AnimatePresence } from "framer-motion";
import type { GraphData } from "../types";
import { clsx } from "clsx";

export const KnowledgeGraphView: React.FC = () => {
  const [data, setData] = useState<GraphData | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedNode, setSelectedNode] = useState<any | null>(null);
  const [zoom, setZoom] = useState(1);

  const loadGraph = async () => {
    setLoading(true);
    try {
      setData(await fetchKnowledgeGraph());
    } catch { setData(null); } finally { setLoading(false); }
  };
  useEffect(() => { loadGraph(); }, []);

  return (
    <div className="absolute inset-0 overflow-hidden bg-black flex items-center justify-center">
      {/* Background Mesh */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-apple-indigo/20 via-black to-black opacity-60" />

      {/* Floating Toolbar */}
      <div className="absolute top-28 left-6 z-10">
        <div className="apple-glass rounded-2xl p-2 flex flex-col gap-2 shadow-2xl">
          <button onClick={() => setZoom(z => Math.max(0.4, z - 0.2))} className="p-3 text-white/60 hover:text-white hover:bg-white/10 rounded-xl transition-all"><ZoomOut className="w-5 h-5" /></button>
          <button onClick={() => setZoom(z => Math.min(2, z + 0.2))} className="p-3 text-white/60 hover:text-white hover:bg-white/10 rounded-xl transition-all"><ZoomIn className="w-5 h-5" /></button>
          <div className="h-px bg-white/10 mx-2" />
          <button onClick={loadGraph} className="p-3 text-white/60 hover:text-white hover:bg-white/10 rounded-xl transition-all">
            <RefreshCw className={clsx("w-5 h-5", loading && "animate-spin text-apple-mint")} />
          </button>
        </div>
      </div>

      {/* Graph Area */}
      {loading ? (
        <div className="animate-pulse text-white/40 tracking-widest text-sm font-medium z-10">Initializing Spatial Graph...</div>
      ) : (
        <motion.div 
          className="relative w-full h-full flex flex-wrap content-center justify-center gap-10 p-20 z-0"
          animate={{ scale: zoom }} transition={{ type: "spring", stiffness: 300, damping: 30 }}
        >
          {data?.nodes.map((node, i) => (
            <motion.div
              key={node.id}
              initial={{ opacity: 0, scale: 0 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: i * 0.05, type: "spring" }}
              onClick={() => setSelectedNode(node)}
              className={clsx(
                "w-28 h-28 rounded-full apple-glass flex flex-col items-center justify-center cursor-pointer hover:scale-110 transition-transform relative group",
                node.is_mandatory ? "border-apple-red shadow-[0_0_30px_rgba(255,69,58,0.3)]" : "border-apple-blue/50"
              )}
            >
              <Share2 className={clsx("w-6 h-6 mb-1 opacity-50", node.is_mandatory ? "text-apple-red" : "text-apple-blue")} />
              <span className="text-xs font-semibold text-white/90 text-center px-2">{node.label}</span>
              
              {/* Dependency Lines (Mocked via pseudo elements for visual effect) */}
              <div className="absolute inset-0 rounded-full border border-white/5 scale-[1.5] -z-10 group-hover:scale-[2] transition-transform duration-500" />
            </motion.div>
          ))}
        </motion.div>
      )}

      {/* Glass Node Popover */}
      <AnimatePresence>
        {selectedNode && (
          <motion.div
            initial={{ opacity: 0, y: 50, scale: 0.9 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.9 }}
            className="absolute bottom-10 z-20 w-96 apple-glass-dark rounded-3xl p-6 shadow-[0_20px_50px_rgba(0,0,0,0.5)] border border-white/20"
          >
            <div className="flex justify-between items-start mb-3">
              <h4 className="text-xl font-semibold text-white tracking-tight flex items-center gap-2">
                <Info className="w-5 h-5 text-apple-blue" />
                {selectedNode.label}
              </h4>
              <button onClick={() => setSelectedNode(null)} className="text-white/40 hover:text-white px-3 py-1 bg-white/10 rounded-full text-xs">Dismiss</button>
            </div>
            <p className="text-sm text-white/70 leading-relaxed mb-4">{selectedNode.title}</p>
            <div className="flex gap-2 text-xs">
              <span className="px-3 py-1 rounded-full bg-white/5 border border-white/10 text-white/60">Div: {selectedNode.division}</span>
              <span className="px-3 py-1 rounded-full bg-apple-mint/20 border border-apple-mint/30 text-apple-mint">Active</span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
