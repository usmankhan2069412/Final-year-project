import { useState } from "react";
import { useTheme } from "../../../contexts/ThemeContext";
import { ChatMessage } from "../types";

interface Step3TestProps {
  persona: any;
  botName: string;
}

export default function Step3Test({ persona, botName }: Step3TestProps) {
  const { isDark } = useTheme();
  const c = (light: string, dark: string) => (isDark ? dark : light);

  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "bot",
      text: persona?.greeting ?? `Hi! I'm ${botName || "your AI Bot"}. How can I help you today?`,
    },
  ]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);

  const DEMO_RESPONSES: Record<string, string> = {
    hello: `${persona?.greeting ?? "Hello! How can I help?"}`,
    hi: `Hello there! 😊 Main ${botName || "AI Bot"} hoon. Kya madad kar sakta hoon?`,
    price:
      "Hamari Professional plan sirf PKR 8,500/month mein available hai — jisme 5 bots, 5,000 messages, aur WhatsApp integration shamil hai! Kya aap free trial start karna chahte hain?",
    pricing:
      "Hamari pricing plans: Free (0/mo), Professional (PKR 8,500/mo), aur Enterprise (custom). Kaunsa aap ke liye best hai?",
    help: "Main aap ki poori madad karne ke liye yahan hoon! Aap mujhse kuch bhi pooch sakte hain — products, pricing, ya technical support. Kya chahiye?",
    whatsapp:
      "Bilkul! Aap ka bot WhatsApp pe deploy ho sakta hai. Setup mein sirf 5 minute lagte hain. Kya main aap ko guide karoon? 🚀",
    contact:
      "Aap humse rabta kar sakte hain:\n📧 Email: support@aina.ai\n📞 Phone: +92 300 1234567\n🌐 Website: aina.ai",
    default:
      "That's a great question! Main is ke baare mein check kar raha hoon... 🔍 Meri knowledge base ke mutabiq, main chahta hoon ke aap ko best answer milein. Kya aap thoda aur detail de sakte hain?",
  };

  const sendMessage = () => {
    if (!input.trim()) return;
    const userMsg = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", text: userMsg }]);
    setIsTyping(true);
    setTimeout(() => {
      const lower = userMsg.toLowerCase();
      const key = Object.keys(DEMO_RESPONSES).find((k) => lower.includes(k)) ?? "default";
      const response = DEMO_RESPONSES[key];
      setMessages((prev) => [...prev, { role: "bot", text: response }]);
      setIsTyping(false);
    }, 1200 + Math.random() * 800);
  };

  const displayName = botName || persona?.name || "Aina Bot";

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 animate-in fade-in duration-300">
      {/* Left: Build status */}
      <div className="lg:col-span-5 space-y-6">
        <div
          className={`rounded-[2rem] border p-4 sm:p-8 shadow-sm ${
            isDark ? "bg-[#1f1f23] border-white/[0.06]" : "bg-white border-black/5"
          }`}
        >
          <div className="flex items-center gap-4 mb-8">
            <div
              className={`w-14 h-14 rounded-2xl flex items-center justify-center shadow-inner flex-shrink-0 ${
                isDark ? "bg-[#EBDCFF]/10 text-[#EBDCFF]" : "bg-black/5 text-[#1c1c1e]"
              }`}
            >
              <span className="material-symbols-outlined text-[28px]">precision_manufacturing</span>
            </div>
            <div>
              <h3
                className={`text-[20px] font-serif font-bold ${c("text-[#1c1c1e]", "text-white")}`}
                style={{ fontFamily: "'Playfair Display', serif" }}
              >
                Bot is Ready!
              </h3>
              <p className={`text-[13px] font-medium mt-1 ${c("text-[#1c1c1e]/60", "text-[#85948b]")}`}>
                All systems trained and deployed
              </p>
            </div>
          </div>

          <div className="space-y-3">
            {[
              { label: "Persona Training", detail: "Identity & voice configured" },
              { label: "Knowledge Indexing", detail: "All sources processed" },
              { label: "Language Model", detail: "Bilingual mode active" },
              { label: "Safety Filters", detail: "Guardrails enabled" },
              { label: "Response Tuning", detail: "Optimized for accuracy" },
            ].map((item) => (
              <div
                key={item.label}
                className={`flex items-center gap-4 p-4 rounded-2xl border transition-all ${
                  isDark ? "bg-[#131317] border-white/[0.04]" : "bg-[#F5F5F7] border-black/5"
                }`}
              >
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 shadow-sm ${
                    isDark ? "bg-[#EBDCFF]/15 text-[#EBDCFF]" : "bg-white text-[#1c1c1e]"
                  }`}
                >
                  <span className="material-symbols-outlined text-[16px]">check</span>
                </div>
                <div className="flex-1">
                  <p className={`text-[14px] font-bold ${c("text-[#1c1c1e]", "text-white")}`}>{item.label}</p>
                  <p className={`text-[11px] font-medium mt-0.5 ${c("text-[#1c1c1e]/50", "text-[#55635a]")}`}>
                    {item.detail}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Quick test prompts */}
        <div
          className={`rounded-[2rem] border p-4 sm:p-8 shadow-sm ${
            isDark ? "bg-[#1f1f23] border-white/[0.06]" : "bg-white border-black/5"
          }`}
        >
          <h4 className={`text-[13px] font-bold uppercase tracking-widest mb-5 ${c("text-[#1c1c1e]/60", "text-[#85948b]")}`}>
            Quick Test Prompts
          </h4>
          <div className="flex flex-wrap gap-2.5">
            {["Hi!", "What's your pricing?", "Help me with WhatsApp", "Contact info?", "Tell me about plans"].map(
              (prompt) => (
                <button
                  key={prompt}
                  onClick={() => setInput(prompt)}
                  className={`text-[13px] font-bold border px-4 py-2.5 rounded-full transition-all shadow-sm ${
                    isDark
                      ? "text-[#85948b] border-white/[0.06] hover:border-[#EBDCFF]/40 hover:text-[#EBDCFF] hover:bg-[#EBDCFF]/5"
                      : "text-[#1c1c1e]/70 border-black/10 hover:border-black/30 hover:text-[#1c1c1e] hover:bg-black/5 bg-[#F5F5F7]"
                  }`}
                >
                  {prompt}
                </button>
              )
            )}
          </div>
        </div>
      </div>

      {/* Right: Chat preview */}
      <div className="lg:col-span-7">
        <div
          className={`rounded-[2rem] border overflow-hidden flex flex-col shadow-[0_8px_40px_rgba(0,0,0,0.06)] relative ${
            isDark ? "bg-[#1f1f23] border-white/[0.06]" : "bg-white border-black/5"
          }`}
          style={{ height: "660px" }}
        >
          {/* Top gradient decoration */}
          <div
            className={`absolute top-0 w-full h-1 z-20 ${c(
              "bg-gradient-to-r from-[#1c1c1e] to-[#1c1c1e]/5",
              "bg-gradient-to-r from-[#EBDCFF] to-transparent"
            )}`}
          ></div>

          {/* Chat header */}
          <div
            className={`flex items-center gap-4 p-4 sm:p-6 border-b z-10 ${
              isDark ? "bg-[#17171a] border-white/[0.06]" : "bg-[#F5F5F7] border-black/5"
            }`}
          >
            <div
              className={`w-12 h-12 rounded-full flex items-center justify-center text-[24px] flex-shrink-0 shadow-sm border ${c(
                "bg-white border-black/5",
                "border-transparent"
              )}`}
              style={isDark ? { background: persona?.bgDark ?? "#EBDCFF15" } : {}}
            >
              {persona?.emoji ?? "🤖"}
            </div>
            <div>
              <p className={`text-[16px] font-bold ${c("text-[#1c1c1e]", "text-white")}`}>{displayName}</p>
              <div className="flex items-center gap-2 mt-1">
                <div className={`w-2 h-2 rounded-full animate-pulse ${c("bg-[#1c1c1e]", "bg-[#EBDCFF]")}`}></div>
                <p className={`text-[11px] font-bold uppercase tracking-wider ${c("text-[#1c1c1e]/60", "text-[#EBDCFF]")}`}>
                  Online
                </p>
              </div>
            </div>
            <div className={`ml-auto flex items-center gap-2 ${c("text-[#1c1c1e]/40", "text-[#55635a]")}`}>
              <button
                className={`hover:text-current transition-colors w-10 h-10 flex items-center justify-center rounded-full ${
                  isDark ? "hover:bg-white/5" : "hover:bg-black/5"
                }`}
              >
                <span className="material-symbols-outlined text-[20px]">more_horiz</span>
              </button>
            </div>
          </div>

          {/* Messages */}
          <div className={`flex-1 overflow-y-auto p-4 sm:p-6 space-y-5 no-scrollbar ${c("bg-black/[0.02]", "bg-[#131317]")}`}>
            {messages.map((msg, idx) => (
              <div key={idx} className={`flex gap-3 ${msg.role === "user" ? "flex-row-reverse" : ""}`}>
                {msg.role === "bot" ? (
                  <div
                    className={`w-8 h-8 rounded-full flex items-center justify-center text-[16px] flex-shrink-0 mt-auto shadow-sm border ${c(
                      "bg-white border-black/5",
                      "border-transparent"
                    )}`}
                    style={isDark ? { background: persona?.bgDark ?? "#EBDCFF15" } : {}}
                  >
                    {persona?.emoji ?? "🤖"}
                  </div>
                ) : (
                  <div
                    className={`w-8 h-8 rounded-full flex items-center justify-center text-[12px] font-bold text-white flex-shrink-0 mt-auto shadow-sm ${c(
                      "bg-[#1c1c1e]",
                      "bg-[#2a2a2e]"
                    )}`}
                  >
                    U
                  </div>
                )}

                <div
                  className={`max-w-[80%] px-5 py-3.5 rounded-3xl text-[14px] leading-relaxed shadow-sm border ${
                    msg.role === "user"
                      ? c(
                          "bg-[#1c1c1e] text-[#F5F5F7] font-semibold border-transparent rounded-tr-md",
                          "bg-[#EBDCFF] text-[#1c1c1e] font-semibold border-transparent rounded-tr-md"
                        )
                      : c(
                          "bg-white border-black/5 text-[#1c1c1e] font-medium rounded-tl-md",
                          "bg-[#1f1f23] border-white/[0.04] text-[#e4e1e7] font-medium rounded-tl-md"
                        )
                  }`}
                  style={{ whiteSpace: "pre-line" }}
                >
                  {msg.text}
                </div>
              </div>
            ))}
            {isTyping && (
              <div className="flex gap-3">
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center text-[16px] flex-shrink-0 mt-auto shadow-sm border ${c(
                    "bg-white border-black/5",
                    "border-transparent"
                  )}`}
                  style={isDark ? { background: persona?.bgDark ?? "#EBDCFF15" } : {}}
                >
                  {persona?.emoji ?? "🤖"}
                </div>
                <div
                  className={`px-5 py-4 rounded-3xl rounded-tl-md flex items-center gap-1.5 shadow-sm border ${c(
                    "bg-white border-black/5",
                    "bg-[#1f1f23] border-white/[0.04]"
                  )}`}
                >
                  <div
                    className={`w-2 h-2 rounded-full animate-bounce ${c("bg-[#1c1c1e]/30", "bg-[#85948b]")}`}
                    style={{ animationDelay: "0ms" }}
                  ></div>
                  <div
                    className={`w-2 h-2 rounded-full animate-bounce ${c("bg-[#1c1c1e]/30", "bg-[#85948b]")}`}
                    style={{ animationDelay: "150ms" }}
                  ></div>
                  <div
                    className={`w-2 h-2 rounded-full animate-bounce ${c("bg-[#1c1c1e]/30", "bg-[#85948b]")}`}
                    style={{ animationDelay: "300ms" }}
                  ></div>
                </div>
              </div>
            )}
          </div>

          {/* Input area */}
          <div className={`p-4 border-t z-10 ${isDark ? "bg-[#17171a] border-white/[0.06]" : "bg-white border-black/5"}`}>
            <div
              className={`flex items-center gap-3 rounded-2xl border px-4 py-3 shadow-inner ${
                isDark ? "bg-[#131317] border-white/[0.06]" : "bg-[#F5F5F7] border-black/10"
              }`}
            >
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && sendMessage()}
                placeholder="Type a test message..."
                className={`flex-1 bg-transparent text-[14px] font-medium outline-none ${
                  isDark ? "text-white placeholder:text-[#55635a]" : "text-[#1c1c1e] placeholder:text-[#1c1c1e]/40"
                }`}
              />
              <button
                onClick={sendMessage}
                disabled={!input.trim()}
                className={`w-10 h-10 rounded-xl flex items-center justify-center transition-colors shadow-sm disabled:opacity-40 disabled:cursor-not-allowed ${
                  isDark
                    ? "bg-[#EBDCFF] hover:bg-[#d8bfff] text-[#1c1c1e]"
                    : "bg-[#1c1c1e] hover:bg-black text-[#F5F5F7]"
                }`}
              >
                <span className="material-symbols-outlined text-[18px] translate-x-[2px] -translate-y-[1px]">send</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
