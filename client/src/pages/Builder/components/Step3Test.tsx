import { useState } from "react";
import { useTheme } from "../../../contexts/ThemeContext";
import { ChatMessage } from "../types";
import ChatSimulator from "./ChatSimulator";

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
      <div className="lg:col-span-7 h-[660px]">
        <ChatSimulator
          botName={botName || persona?.name || "Aina Bot"}
          role={persona?.role || "AI Assistant"}
          emoji={persona?.emoji || "🤖"}
          tone={persona?.traits?.[0] || "friendly"}
          messages={messages}
          isTyping={isTyping}
          input={input}
          onInputChange={setInput}
          onSend={sendMessage}
          isInteractive={true}
        />
      </div>
    </div>
  );
}
