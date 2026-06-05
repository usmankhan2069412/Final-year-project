import { useEffect, useRef } from "react";
import { useTheme } from "../../../contexts/ThemeContext";
import MarkdownRenderer from "../../../components/MarkdownRenderer";

interface ChatMessage {
  role: "bot" | "user";
  text: string;
}

interface ChatSimulatorProps {
  botName: string;
  role: string;
  emoji: string;
  tone: string;
  greeting?: string;
  messages?: ChatMessage[];
  isTyping?: boolean;
  input?: string;
  onInputChange?: (val: string) => void;
  onSend?: () => void;
  isInteractive?: boolean;
}

export default function ChatSimulator({
  botName,
  role,
  emoji,
  tone,
  greeting,
  messages,
  isTyping = false,
  input = "",
  onInputChange,
  onSend,
  isInteractive = false,
}: ChatSimulatorProps) {
  const { isDark } = useTheme();
  const c = (light: string, dark: string) => (isDark ? dark : light);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Derive tone styles dynamically matching design tokens
  const toneBg = isDark ? "bg-primary/10" : "bg-primary/5";
  const toneBorder = isDark ? "border-primary/20" : "border-primary/10";

  // Static conversation sequence fallback (for Step 1 Preview)
  const staticMessages: ChatMessage[] = [
    {
      role: "bot",
      text: greeting || `Assalam-o-Alaikum! Main ${botName || "your AI Bot"} hoon. Aap ki kya madad kar sakti hoon? 😊`,
    },
    {
      role: "user",
      text: "I need help with my order",
    },
    {
      role: "bot",
      text: tone === "formal" 
        ? "Tashreef rakhye. Main abhi aap ke order ki tafseelat check karta hoon. Baraye meharbani apna order number faraham karein. 📋"
        : tone === "casual"
        ? "Yo! Fikr not. Main abhi check karta hoon. Apna order number send kar do! ⚡"
        : tone === "empathetic"
        ? "I understand how important this is to you. Let me check your order details right away. Could you please share your order number? 💙"
        : "Bilkul! Main abhi aap ka order check karta hoon. Aap ka order number kya hai? 🔍",
    },
  ];

  const activeMessages = messages || staticMessages;
  const displayName = botName || "Aina Bot";
  const displayRole = role || "AI Assistant";

  // Scroll to bottom when message list updates or typing status changes
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [activeMessages, isTyping]);

  return (
    <div
      className={`rounded-[2rem] border overflow-hidden flex flex-col shadow-[0_8px_40px_rgba(0,0,0,0.06)] relative h-full w-full ${
        isDark ? "bg-[#1f1f23] border-white/[0.06]" : "bg-white border-black/5"
      }`}
    >
      {/* Top indicator bar */}
      <div className={`absolute top-0 w-full h-1 z-20 bg-primary/40`}></div>

      {/* Header */}
      <div
        className={`flex items-center gap-4 p-4 sm:p-5 border-b z-10 ${
          isDark ? "bg-[#17171a] border-white/[0.06]" : "bg-[#F5F5F7] border-black/5"
        }`}
      >
        <div
          className={`w-11 h-11 rounded-full flex items-center justify-center text-[22px] flex-shrink-0 shadow-sm border ${toneBg} ${toneBorder}`}
        >
          {emoji || "🤖"}
        </div>
        <div className="min-w-0">
          <p className={`text-[15px] font-bold truncate ${c("text-[#1c1c1e]", "text-white")}`}>
            {displayName}
          </p>
          <div className="flex items-center gap-2 mt-0.5">
            <span className={`w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse`}></span>
            <p className={`text-[10px] font-bold uppercase tracking-wider ${c("text-[#1c1c1e]/50", "text-[#85948b]")} truncate`}>
              {displayRole} • Online
            </p>
          </div>
        </div>
        <div className={`ml-auto flex items-center gap-2 ${c("text-[#1c1c1e]/40", "text-[#55635a]")}`}>
          <button
            className={`w-8 h-8 flex items-center justify-center rounded-full transition-colors ${
              isDark ? "hover:bg-white/5" : "hover:bg-black/5"
            }`}
          >
            <span className="material-symbols-outlined text-[18px]">more_horiz</span>
          </button>
        </div>
      </div>

      {/* Message Feed */}
      <div className={`flex-1 overflow-y-auto p-4 sm:p-5 space-y-4 no-scrollbar ${c("bg-black/[0.01]", "bg-[#131317]")}`}>
        {activeMessages.map((msg, idx) => (
          <div key={idx} className={`flex gap-3 ${msg.role === "user" ? "flex-row-reverse" : ""}`}>
            {msg.role === "bot" ? (
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center text-[15px] flex-shrink-0 mt-auto shadow-sm border ${toneBg} ${toneBorder}`}
              >
                {emoji || "🤖"}
              </div>
            ) : (
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center text-[11px] font-bold text-white flex-shrink-0 mt-auto shadow-sm ${c(
                  "bg-[#1c1c1e]",
                  "bg-[#2a2a2e]"
                )}`}
              >
                U
              </div>
            )}

            <div
              className={`max-w-[80%] px-4 py-3 rounded-2xl text-[13px] leading-relaxed shadow-sm border ${
                msg.role === "user"
                  ? "bg-primary text-primary-foreground font-semibold border-transparent rounded-tr-md"
                  : c(
                      "bg-white border-black/5 text-[#1c1c1e] font-medium rounded-tl-md",
                      "bg-[#1f1f23] border-white/[0.04] text-[#e4e1e7] font-medium rounded-tl-md"
                    )
              }`}
            >
              {msg.role === "user" ? (
                <div style={{ whiteSpace: "pre-line" }}>{msg.text}</div>
              ) : (
                <MarkdownRenderer content={msg.text} isDark={isDark} />
              )}
            </div>
          </div>
        ))}
        {isTyping && (
          <div className="flex gap-3">
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center text-[15px] flex-shrink-0 mt-auto shadow-sm border ${toneBg} ${toneBorder}`}
            >
              {emoji || "🤖"}
            </div>
            <div
              className={`px-4 py-3.5 rounded-2xl rounded-tl-md flex items-center gap-1 shadow-sm border ${c(
                "bg-white border-black/5",
                "bg-[#1f1f23] border-white/[0.04]"
              )}`}
            >
              <div
                className={`w-1.5 h-1.5 rounded-full animate-bounce bg-primary/40`}
                style={{ animationDelay: "0ms" }}
              ></div>
              <div
                className={`w-1.5 h-1.5 rounded-full animate-bounce bg-primary/40`}
                style={{ animationDelay: "150ms" }}
              ></div>
              <div
                className={`w-1.5 h-1.5 rounded-full animate-bounce bg-primary/40`}
                style={{ animationDelay: "300ms" }}
              ></div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input area */}
      <div className={`p-3 border-t z-10 ${isDark ? "bg-[#17171a] border-white/[0.06]" : "bg-white border-black/5"}`}>
        <div
          className={`flex items-center gap-2 rounded-xl border px-3 py-2 ${
            isInteractive ? "shadow-inner" : "opacity-50 cursor-not-allowed"
          } ${isDark ? "bg-[#131317] border-white/[0.06]" : "bg-[#F5F5F7] border-black/10"}`}
        >
          <input
            type="text"
            value={input}
            onChange={(e) => onInputChange?.(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && onSend?.()}
            placeholder={isInteractive ? "Type a test message..." : "Chat simulation active"}
            disabled={!isInteractive}
            className={`flex-1 bg-transparent text-[13px] font-medium outline-none ${
              isDark ? "text-white placeholder:text-[#55635a]" : "text-[#1c1c1e] placeholder:text-[#1c1c1e]/40"
            }`}
          />
          <button
            onClick={onSend}
            disabled={!isInteractive || !input.trim()}
            className={`w-8 h-8 rounded-lg flex items-center justify-center transition-colors shadow-sm disabled:opacity-40 disabled:cursor-not-allowed bg-primary text-primary-foreground hover:opacity-90`}
          >
            <span className="material-symbols-outlined text-[16px] translate-x-[1px]">send</span>
          </button>
        </div>
      </div>
    </div>
  );
}
