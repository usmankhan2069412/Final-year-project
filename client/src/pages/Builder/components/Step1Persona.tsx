import { useTheme } from "../../../contexts/ThemeContext";

interface Step1PersonaProps {
  customRole: string;
  setCustomRole: (val: string) => void;
  customTone: string;
  setCustomTone: (val: string) => void;
  customGreeting: string;
  setCustomGreeting: (val: string) => void;
  customFallback: string;
  setCustomFallback: (val: string) => void;
  customDescription: string;
  setCustomDescription: (val: string) => void;
  botName: string;
  setBotName: (val: string) => void;
}

export default function Step1Persona({
  customRole,
  setCustomRole,
  customTone,
  setCustomTone,
  customGreeting,
  setCustomGreeting,
  customFallback,
  setCustomFallback,
  customDescription,
  setCustomDescription,
  botName,
  setBotName,
}: Step1PersonaProps) {
  const { isDark } = useTheme();
  const c = (light: string, dark: string) => (isDark ? dark : light);

  return (
    <div className="max-w-2xl mx-auto space-y-6 animate-in fade-in duration-300">
      
      {/* Bot Basic Identity */}
      <div
        className={`rounded-[2rem] border p-5 sm:p-8 ${
          isDark ? "bg-[#1f1f23] border-white/[0.06]" : "bg-white border-black/5 shadow-[0_8px_30px_rgb(0,0,0,0.02)]"
        }`}
      >
        <h3 className={`text-[16px] font-bold mb-6 flex items-center gap-2.5 ${c("text-[#1c1c1e]", "text-white")}`}>
          <span className={`material-symbols-outlined text-[20px] ${c("text-[#1c1c1e]/40", "text-[#59eeb4]")}`}>badge</span>
          Bot Identity
        </h3>
        
        <div className="space-y-4">
          <div>
            <label className={`block text-[11px] font-bold uppercase tracking-widest mb-2 ${c("text-[#1c1c1e]/50", "text-[#85948b]")}`}>
              Bot Name
            </label>
            <input
              type="text"
              value={botName}
              onChange={(e) => setBotName(e.target.value)}
              className={`w-full rounded-xl px-5 py-3.5 text-[14px] font-medium outline-none transition-all shadow-inner focus:border-primary/50 focus:ring-2 focus:ring-primary/20 ${
                isDark
                  ? "bg-[#131317] border border-white/[0.06] text-white"
                  : "bg-[#F5F5F7] border border-black/5 text-[#1c1c1e] focus:bg-white"
              }`}
              placeholder="e.g. Aina Concierge"
            />
          </div>

          {/* Premium Multilingual Information Alert */}
          <div
            className={`rounded-2xl border p-4 flex gap-3.5 transition-all ${
              isDark ? "bg-[#131317] border-white/[0.04]" : "bg-[#F5F5F7] border-black/5"
            }`}
          >
            <span className="material-symbols-outlined text-[20px] text-emerald-500 flex-shrink-0">translate</span>
            <div className="space-y-1">
              <h4 className={`text-[12px] font-bold ${c("text-[#1c1c1e]", "text-white")}`}>Auto-Multilingual Active</h4>
              <p className={`text-[11px] font-medium leading-relaxed ${c("text-[#1c1c1e]/60", "text-[#85948b]")}`}>
                Your bot dynamically detects the user's language (English, Urdu Script, or Roman Urdu) and automatically answers using the matching style and script.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Custom Persona Builder */}
      <div
        className={`rounded-[2rem] border p-5 sm:p-8 space-y-6 ${
          isDark ? "bg-[#1f1f23] border-white/[0.06]" : "bg-white border-black/5 shadow-[0_8px_30px_rgb(0,0,0,0.02)]"
        }`}
      >
        <h3 className={`text-[16px] font-bold flex items-center gap-2.5 ${c("text-[#1c1c1e]", "text-white")}`}>
          <span className={`material-symbols-outlined text-[20px] ${c("text-[#1c1c1e]/40", "text-[#59eeb4]")}`}>tune</span>
          Persona Details
        </h3>

        <div>
          <label className={`block text-[11px] font-bold uppercase tracking-widest mb-2 ${c("text-[#1c1c1e]/50", "text-[#85948b]")}`}>
            Role / Title
          </label>
          <input
            type="text"
            value={customRole}
            onChange={(e) => setCustomRole(e.target.value)}
            className={`w-full rounded-xl px-5 py-3.5 text-[14px] font-medium outline-none transition-all shadow-inner focus:border-primary/50 focus:ring-2 focus:ring-primary/20 ${
              isDark
                ? "bg-[#131317] border border-white/[0.06] text-white"
                : "bg-[#F5F5F7] border border-black/5 text-[#1c1c1e] focus:bg-white"
            }`}
            placeholder="e.g. Brand Ambassador"
          />
        </div>

        <div>
          <label className={`block text-[11px] font-bold uppercase tracking-widest mb-2 ${c("text-[#1c1c1e]/50", "text-[#85948b]")}`}>
            Conversation Tone
          </label>
          <select
            value={customTone}
            onChange={(e) => setCustomTone(e.target.value)}
            className={`w-full rounded-xl px-5 py-3.5 text-[14px] font-medium outline-none transition-all shadow-inner focus:border-primary/50 focus:ring-2 focus:ring-primary/20 ${
              isDark
                ? "bg-[#131317] border border-white/[0.06] text-white"
                : "bg-[#F5F5F7] border border-black/5 text-[#1c1c1e] focus:bg-white"
            }`}
          >
            <option value="formal" className={isDark ? "bg-[#131317] text-white" : "bg-white text-[#1c1c1e]"}>🎩 Formal</option>
            <option value="friendly" className={isDark ? "bg-[#131317] text-white" : "bg-white text-[#1c1c1e]"}>😊 Friendly</option>
            <option value="casual" className={isDark ? "bg-[#131317] text-white" : "bg-white text-[#1c1c1e]"}>😎 Casual</option>
            <option value="empathetic" className={isDark ? "bg-[#131317] text-white" : "bg-white text-[#1c1c1e]"}>💙 Empathetic</option>
          </select>
        </div>

        <div>
          <label className={`block text-[11px] font-bold uppercase tracking-widest mb-2 ${c("text-[#1c1c1e]/50", "text-[#85948b]")}`}>
            Persona Description
          </label>
          <textarea
            value={customDescription}
            onChange={(e) => setCustomDescription(e.target.value)}
            rows={4}
            className={`w-full rounded-xl px-5 py-4 text-[14px] font-medium outline-none transition-all shadow-inner resize-none focus:border-primary/50 focus:ring-2 focus:ring-primary/20 ${
              isDark
                ? "bg-[#131317] border border-white/[0.06] text-white"
                : "bg-[#F5F5F7] border border-black/5 text-[#1c1c1e] focus:bg-white"
            }`}
            placeholder="Describe the chatbot's background, role, rules, constraints, or identity. E.g. 'You are Ali, a friendly AI sales assistant for Zylker. You help users discover products, answer inquiries concisely, and direct them to agents when asked.'"
          />
        </div>

        <div>
          <label className={`block text-[11px] font-bold uppercase tracking-widest mb-2 ${c("text-[#1c1c1e]/50", "text-[#85948b]")}`}>
            Opening Greeting Message
          </label>
          <textarea
            value={customGreeting}
            onChange={(e) => setCustomGreeting(e.target.value)}
            rows={3}
            className={`w-full rounded-xl px-5 py-4 text-[14px] font-medium outline-none transition-all shadow-inner resize-none focus:border-primary/50 focus:ring-2 focus:ring-primary/20 ${
              isDark
                ? "bg-[#131317] border border-white/[0.06] text-white"
                : "bg-[#F5F5F7] border border-black/5 text-[#1c1c1e] focus:bg-white"
            }`}
            placeholder="Write the first message your bot will say to a user..."
          />
        </div>

        <div>
          <label className={`block text-[11px] font-bold uppercase tracking-widest mb-2 ${c("text-[#1c1c1e]/50", "text-[#85948b]")}`}>
            Fallback Response
          </label>
          <textarea
            value={customFallback}
            onChange={(e) => setCustomFallback(e.target.value)}
            rows={2}
            className={`w-full rounded-xl px-5 py-4 text-[14px] font-medium outline-none transition-all shadow-inner resize-none focus:border-primary/50 focus:ring-2 focus:ring-primary/20 ${
              isDark
                ? "bg-[#131317] border border-white/[0.06] text-white"
                : "bg-[#F5F5F7] border border-black/5 text-[#1c1c1e] focus:bg-white"
            }`}
            placeholder="What should the bot say when it doesn't know the answer?"
          />
        </div>

        {/* Human-feel tips */}
        <div
          className={`rounded-2xl p-5 border ${
            isDark ? "bg-[#131317] border-primary/10" : "bg-white border-primary/10 shadow-sm"
          }`}
        >
          <h4
            className={`text-[12px] font-bold uppercase tracking-widest mb-4 flex items-center gap-2 ${
              c("text-primary", "text-primary-foreground")
            }`}
          >
            <span className="material-symbols-outlined text-[16px]">lightbulb</span>
            Human-Feel Tips
          </h4>
          <ul className="space-y-2.5">
            {[
              "Use first-person language — 'I understand' instead of 'The system understands'",
              "Add light filler words like 'Sure!', 'Great question!', 'Let me check that for you'",
              "Use emojis sparingly but naturally — they reduce formality",
              "Acknowledge emotions — 'I know this can be frustrating, let me help'",
            ].map((tip) => (
              <li key={tip} className={`flex items-start gap-3 text-[12px] font-medium ${c("text-[#1c1c1e]/70", "text-[#85948b]")}`}>
                <span className={`mt-0.5 flex-shrink-0 text-[16px] font-bold ${c("text-primary", "text-primary-foreground")}`}>·</span>
                {tip}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
