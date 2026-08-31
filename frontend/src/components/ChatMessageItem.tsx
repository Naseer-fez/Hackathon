import React from "react";
import { clsx } from "clsx";
import { Sparkles } from "lucide-react";

export interface ChatMessage {
  role: "user" | "assistant";
  text: string;
}

interface ChatMessageItemProps {
  message: ChatMessage;
  loading?: boolean;
}

export const ChatMessageItem: React.FC<ChatMessageItemProps> = ({ message, loading }) => {
  const isUser = message.role === "user";

  return (
    <div className={clsx("flex w-full", isUser ? "justify-end" : "justify-start")}>
      {!isUser && <Sparkles className="w-4 h-4 text-apple-indigo mr-2 mt-2 shrink-0" />}
      <div
        className={clsx(
          "max-w-[85%] rounded-2xl px-4 py-3 text-sm transition-all",
          isUser
            ? "bg-apple-blue text-white rounded-br-none shadow-lg shadow-apple-blue/20"
            : "apple-glass-dark text-white/90 rounded-bl-none leading-relaxed whitespace-pre-wrap"
        )}
      >
        {message.text}
        {!isUser && loading && (
          <span className="inline-block w-1.5 h-3.5 ml-1 bg-apple-indigo animate-pulse align-middle" />
        )}
      </div>
    </div>
  );
};
