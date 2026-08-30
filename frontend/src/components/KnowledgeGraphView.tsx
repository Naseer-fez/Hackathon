import React, { useEffect, useState } from "react";
import { Share2, RefreshCw, ZoomIn, ZoomOut } from "lucide-react";
import { fetchKnowledgeGraph } from "../services/api.service";
import type { GraphData } from "../types";

export const KnowledgeGraphView: React.FC = () => {
  const [data, setData] = useState<GraphData | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedNode, setSelectedNode] = useState<any | null>(null);
  const [zoom, setZoom] = useState(1);

  const loadGraph = async () => {
    setLoading(true);
    try {
      const res = await fetchKnowledgeGraph();
      setData(res);
    } catch {
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadGraph();
  }, []);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between bg-slate-900/80 p-4 rounded-2xl border border-slate-800">
        <div>
          <h3 className="font-bold text-base text-white flex items-center gap-2">
            <Share2 className="w-5 h-5 text-blue-400" />
            BIS Indian Standards Normative & Allied Knowledge Graph
          </h3>
          <p className="text-xs text-slate-400">
            Interactive multi-relational network topology of Indian Standards, normative references, and test methods.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => setZoom((z) => Math.max(0.6, z - 0.2))} className="p-2 bg-slate-800 text-slate-300 rounded-xl hover:bg-slate-700">
            <ZoomOut className="w-4 h-4" />
          </button>
          <button onClick={() => setZoom((z) => Math.min(1.8, z + 0.2))} className="p-2 bg-slate-800 text-slate-300 rounded-xl hover:bg-slate-700">
            <ZoomIn className="w-4 h-4" />
          </button>
          <button onClick={loadGraph} className="p-2 bg-blue-600/20 text-blue-400 border border-blue-500/30 rounded-xl hover:bg-blue-600/30">
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      <div className="relative h-[480px] bg-[#070d18] border border-slate-800 rounded-2xl overflow-hidden flex items-center justify-center">
        {loading ? (
          <div className="text-center text-slate-400 text-sm animate-pulse">Loading Knowledge Graph...</div>
        ) : !data || data.nodes.length === 0 ? (
          <div className="text-slate-500 text-sm">No graph data available</div>
        ) : (
          <div className="w-full h-full p-6 overflow-auto">
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3" style={{ transform: `scale(${zoom})`, transformOrigin: "top left" }}>
              {data.nodes.map((node) => (
                <div
                  key={node.id}
                  onClick={() => setSelectedNode(node)}
                  className={`p-3 rounded-xl border transition-all cursor-pointer ${
                    node.is_mandatory
                      ? "bg-amber-950/20 border-amber-600/50 hover:border-amber-400 shadow-md shadow-amber-950/30"
                      : "bg-slate-900/80 border-slate-700/60 hover:border-blue-500"
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-bold text-xs text-white">{node.label}</span>
                    <span className="text-[9px] uppercase px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 font-semibold">
                      {node.division}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400 truncate">{node.title}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {selectedNode && (
        <div className="bg-slate-900/90 border border-blue-500/40 p-4 rounded-2xl flex items-center justify-between text-xs">
          <div>
            <span className="font-bold text-blue-300 text-sm">{selectedNode.label}</span>: {selectedNode.title}
            <div className="text-slate-400 mt-0.5">Division: {selectedNode.division} | Status: {selectedNode.status}</div>
          </div>
          <button onClick={() => setSelectedNode(null)} className="text-slate-400 hover:text-white px-2 py-1 bg-slate-800 rounded-lg">
            Dismiss
          </button>
        </div>
      )}
    </div>
  );
};
