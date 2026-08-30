import React, { useState } from "react";
import { X, Send, Bot, Sparkles, RefreshCw } from "lucide-react";
import { askProcurementAssistant } from "../services/api.service";
import { ChatMessage, ChatMessageItem } from "./ChatMessageItem";

export const AssistantChatDrawer: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
      text: "Hello! I am your BIS Procurement AI Advisor. Ask me anything about Indian Standards, mandatory QCOs, test methods, or GeM compliance.",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSend = async (customQ?: string) => {
    const q = customQ || input;
    if (!q.trim() || loading) return;
    setMessages((prev) => [...prev, { role: "user", text: q }]);
    setInput("");
    setLoading(true);
    try {
      const res = await askProcurementAssistant(q);
      setMessages((prev) => [...prev, { role: "assistant", text: res.answer }]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text: "No active LLM model is currently available to process this query. Please verify system model status.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 z-50 flex items-center gap-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white text-xs font-semibold px-4 py-3 rounded-full shadow-2xl shadow-blue-500/50 border border-blue-400/30 transition-all hover:scale-105"
      >
        <Sparkles className="w-4 h-4" />
        <span>Ask BIS AI</span>
      </button>

      {isOpen && (
        <div className="fixed inset-y-0 right-0 z-50 w-full sm:w-[420px] bg-slate-900 border-l border-slate-800 shadow-2xl flex flex-col">
          <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-950/80">
            <div className="flex items-center gap-2">
              <div className="p-1.5 rounded-lg bg-blue-600/20 text-blue-400">
                <Bot className="w-4 h-4" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-white">BIS Procurement Assistant</h3>
                <p className="text-[10px] text-slate-400">Grounded in ChromaDB Indian Standards</p>
              </div>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="p-1.5 text-slate-400 hover:text-white rounded-lg transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {messages.map((m, i) => (
              <ChatMessageItem key={i} message={m} />
            ))}
            {loading && (
              <div className="flex justify-start">
                <div className="bg-slate-800 text-slate-400 rounded-2xl px-3.5 py-2 text-xs flex items-center gap-2 animate-pulse">
                  <RefreshCw className="w-3 h-3 animate-spin text-blue-400" />
                  <span>Searching Vector DB & reasoning...</span>
                </div>
              </div>
            )}
          </div>

          <div className="p-3 border-t border-slate-800 bg-slate-950/80 flex items-center gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSend()}
              placeholder="Ask about standards, QCOs, tests..."
              className="flex-1 bg-slate-900 border border-slate-700/80 rounded-xl px-3 py-2 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500"
            />
            <button
              onClick={() => handleSend()}
              disabled={loading || !input.trim()}
              className="p-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white rounded-xl transition-colors"
            >
              <Send className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      )}
    </>
  );
};
