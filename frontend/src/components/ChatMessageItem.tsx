import React from "react";

export interface ChatMessage {
  role: "user" | "assistant";
  text: string;
}

interface ChatMessageItemProps {
  message: ChatMessage;
}

export const ChatMessageItem: React.FC<ChatMessageItemProps> = ({ message }) => {
  const isUser = message.role === "user";
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[85%] rounded-2xl px-3.5 py-2.5 text-xs ${
          isUser
            ? "bg-blue-600 text-white rounded-br-none"
            : "bg-slate-800/90 text-slate-200 border border-slate-700/60 rounded-bl-none leading-relaxed whitespace-pre-wrap"
        }`}
      >
        {message.text}
      </div>
    </div>
  );
};
