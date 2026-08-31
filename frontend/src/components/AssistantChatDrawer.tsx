import React, { useState } from "react";
import { X, Send, Sparkles, Bot, Mic } from "lucide-react";
import { askProcurementAssistantStream } from "../services/api.service";
import { ChatMessage, ChatMessageItem } from "./ChatMessageItem";
import { clsx } from "clsx";
import { motion, AnimatePresence } from "framer-motion";

export const AssistantChatDrawer: React.FC<{ pdfText?: string }> = ({ pdfText }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([
    { role: "assistant", text: "Hello! I am your BIS AI. Ask me about Indian Standards." },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [speaking, setSpeaking] = useState(false);

  const handleSend = async () => {
    if (!input.trim() || loading) return;
    const q = input; setInput(""); setLoading(true); setSpeaking(true);
    
    // Capture current messages as history before appending new optimistic ones
    const chatHistory = messages.map(m => ({ role: m.role, content: m.text }));
    
    setMessages(p => [...p, { role: "user", text: q }, { role: "assistant", text: "" }]);
    
    try {
      await askProcurementAssistantStream(q, (chunk) => {
        setMessages(prev => {
          if (prev.length === 0) return prev;
          const lastIdx = prev.length - 1;
          const lastMsg = prev[lastIdx];
          return [
            ...prev.slice(0, lastIdx),
            { ...lastMsg, text: lastMsg.text + chunk }
          ];
        });
      }, pdfText, chatHistory);
    } catch {
      setMessages(prev => {
        if (prev.length === 0) return prev;
        const lastIdx = prev.length - 1;
        const lastMsg = prev[lastIdx];
        return [
          ...prev.slice(0, lastIdx),
          { ...lastMsg, text: "No active LLM model available." }
        ];
      });
    } finally { 
      setLoading(false); 
      setTimeout(() => setSpeaking(false), 2000); 
    }
  };

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end gap-4">
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            className={clsx(
              "w-[380px] h-[500px] apple-glass-dark rounded-3xl flex flex-col overflow-hidden relative",
              loading && "shadow-[0_0_40px_rgba(94,92,230,0.3)]"
            )}
          >
            <div className="p-4 border-b border-white/10 flex justify-between items-center bg-white/5">
              <div className="flex gap-2 items-center">
                <Bot className="w-5 h-5 text-apple-indigo" />
                <h3 className="text-sm font-medium text-white/90">Apple Intelligence</h3>
              </div>
              <button onClick={() => setIsOpen(false)}><X className="w-4 h-4 text-white/60" /></button>
            </div>
            
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.map((m, i) => <ChatMessageItem key={i} message={m} loading={loading && i === messages.length - 1 && m.role === "assistant"} />)}
            </div>

            <div className="p-3 bg-white/5 border-t border-white/10 relative">
              {speaking && (
                <motion.div 
                  className="absolute bottom-0 left-0 right-0 h-1 bg-apple-indigo origin-left"
                  animate={{ scaleX: [0, 1, 0.5, 1, 0] }}
                  transition={{ repeat: Infinity, duration: 1.5 }}
                />
              )}
              <div className="flex gap-2 relative z-10">
                <button className="p-2 text-white/60 hover:text-white"><Mic className="w-4 h-4" /></button>
                <input
                  value={input} onChange={e => setInput(e.target.value)}
                  onKeyDown={e => e.key === "Enter" && handleSend()}
                  placeholder="Ask about standards..."
                  className="flex-1 bg-transparent text-sm text-white focus:outline-none"
                />
                <button onClick={handleSend} className="p-2 bg-apple-blue rounded-full text-white">
                  <Send className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="apple-glass-dark hover:bg-white/10 text-white p-4 rounded-full shadow-2xl transition-all"
        >
          <Sparkles className="w-6 h-6 text-apple-indigo" />
        </button>
      )}
    </div>
  );
};
