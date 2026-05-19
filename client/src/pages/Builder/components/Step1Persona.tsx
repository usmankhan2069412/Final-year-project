import { useTheme } from "../../../contexts/ThemeContext";

export interface Persona {
  id: string;
  name: string;
  role: string;
  emoji: string;
  color: string;
  bgDark: string;
  bgLight: string;
  traits: string[];
  greeting: string;
  description: string;
  custom?: boolean;
}

export const BUILT_IN_PERSONAS: Persona[] = [
  {
    id: "saraa",
    name: "Sara",
    role: "Friendly Support Rep",
    emoji: "👩‍💼",
    color: "#59eeb4",
    bgDark: "#59eeb415",
    bgLight: "#59eeb420",
    traits: ["Warm", "Empathetic", "Patient", "Clear"],
    greeting: "Assalam-o-Alaikum! Main Sara hoon. Aap ki kya madad kar sakti hoon? 😊",
    description:
      "Perfect for customer care. Sara speaks naturally in Roman Urdu & English, listens carefully and resolves issues with a human touch.",
  },
  {
    id: "zain",
    name: "Zain",
    role: "Sales Expert",
    emoji: "🧑‍💻",
    color: "#b0c6ff",
    bgDark: "#b0c6ff15",
    bgLight: "#b0c6ff30",
    traits: ["Persuasive", "Confident", "Knowledgeable", "Driven"],
    greeting: "Hey! I'm Zain. Looking for the best deal today? Let me help you find exactly what you need!",
    description:
      "Built for conversions. Zain proactively engages users, highlights value, and guides them through the sales funnel with confidence.",
  },
  {
    id: "hira",
    name: "Hira",
    role: "Technical Specialist",
    emoji: "👩‍🔬",
    color: "#f5c5ff",
    bgDark: "#f5c5ff15",
    bgLight: "#f5c5ff30",
    traits: ["Precise", "Logical", "Thorough", "Reliable"],
    greeting: "Hello! I'm Hira, your technical support specialist. Please describe the issue you're facing.",
    description:
      "Ideal for SaaS & tech products. Hira provides step-by-step guidance, troubleshoots issues and escalates when needed.",
  },
  {
    id: "bilal",
    name: "Bilal",
    role: "Casual Brand Rep",
    emoji: "😎",
    color: "#ffb4ab",
    bgDark: "#ffb4ab15",
    bgLight: "#ffb4ab25",
    traits: ["Casual", "Witty", "Relatable", "Fun"],
    greeting: "Yo! Kya haal hai! Main Bilal — bata kya chahiye? 🔥",
    description:
      "Made for youth brands & lifestyle products. Bilal keeps it real, uses GenZ slang and makes every interaction feel like a chat with a friend.",
  },
  {
    id: "custom",
    name: "Build My Own",
    role: "Fully Custom",
    emoji: "✨",
    color: "#85948b",
    bgDark: "#85948b15",
    bgLight: "#85948b20",
    traits: [],
    greeting: "",
    description: "Design your own persona from scratch. Set the name, voice, tone, and personality to perfectly represent your brand.",
    custom: true,
  },
];

interface Step1PersonaProps {
  selected: string;
  onSelect: (id: string) => void;
  customName: string;
  setCustomName: (val: string) => void;
  customRole: string;
  setCustomRole: (val: string) => void;
  customTone: string;
  setCustomTone: (val: string) => void;
  customGreeting: string;
  setCustomGreeting: (val: string) => void;
  botName: string;
  setBotName: (val: string) => void;
  language: string;
  setLanguage: (val: string) => void;
}

export default function Step1Persona({
  selected,
  onSelect,
  customName,
  setCustomName,
  customRole,
  setCustomRole,
  customTone,
  setCustomTone,
  customGreeting,
  setCustomGreeting,
  botName,
  setBotName,
  language,
  setLanguage,
}: Step1PersonaProps) {
  const { isDark } = useTheme();
  const c = (light: string, dark: string) => (isDark ? dark : light);
  const persona = BUILT_IN_PERSONAS.find((p) => p.id === selected);

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* Bot basic info */}
      <div
        className={`rounded-[2rem] border p-4 sm:p-8 ${
          isDark ? "bg-[#1f1f23] border-white/[0.06]" : "bg-white border-black/5 shadow-[0_8px_30px_rgb(0,0,0,0.02)]"
        }`}
      >
        <h3 className={`text-[16px] font-bold mb-6 flex items-center gap-2 ${c("text-[#1c1c1e]", "text-white")}`}>
          <span className={`material-symbols-outlined text-[20px] ${c("text-[#1c1c1e]/40", "text-[#EBDCFF]")}`}>badge</span>
          Bot Identity
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className={`block text-[11px] font-bold uppercase tracking-widest mb-2 ${c("text-[#1c1c1e]/50", "text-[#85948b]")}`}>
              Bot Name
            </label>
            <input
              type="text"
              value={botName}
              onChange={(e) => setBotName(e.target.value)}
              className={`w-full rounded-xl px-5 py-3.5 text-[14px] font-medium outline-none transition-all shadow-inner ${
                isDark
                  ? "bg-[#131317] border border-white/[0.06] text-white focus:border-[#EBDCFF]/50"
                  : "bg-[#F5F5F7] border border-black/5 text-[#1c1c1e] focus:border-black/20 focus:bg-white"
              }`}
              placeholder="e.g. Aina Concierge"
            />
          </div>
          <div>
            <label className={`block text-[11px] font-bold uppercase tracking-widest mb-2 ${c("text-[#1c1c1e]/50", "text-[#85948b]")}`}>
              Language
            </label>
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              className={`w-full rounded-xl px-5 py-3.5 text-[14px] font-medium outline-none transition-all shadow-inner cursor-pointer appearance-none ${
                isDark
                  ? "bg-[#131317] border border-white/[0.06] text-white focus:border-[#EBDCFF]/50"
                  : "bg-[#F5F5F7] border border-black/5 text-[#1c1c1e] focus:border-black/20 focus:bg-white"
              }`}
            >
              <option value="urdu">Roman Urdu (Recommended)</option>
              <option value="english">English</option>
              <option value="bilingual">Bilingual (Urdu + English)</option>
            </select>
          </div>
        </div>
      </div>

      {/* Persona cards */}
      <div>
        <div className="mb-6">
          <h3
            className={`text-[20px] font-serif font-bold ${c("text-[#1c1c1e]", "text-white")}`}
            style={{ fontFamily: "'Playfair Display', serif" }}
          >
            Choose a Persona
          </h3>
          <p className={`text-[13px] font-medium mt-1.5 ${c("text-[#1c1c1e]/50", "text-white/40")}`}>
            Pre-built personas are designed to sound human, not robotic.
          </p>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-2 xl:grid-cols-3 gap-3 sm:gap-6">
          {BUILT_IN_PERSONAS.map((p) => {
            const isSelected = selected === p.id;
            return (
              <button
                key={p.id}
                onClick={() => onSelect(p.id)}
                className={`relative text-left p-3 sm:p-6 rounded-2xl sm:rounded-3xl border transition-all duration-300 group ${
                  isSelected
                    ? c(
                        "border-[#1c1c1e] bg-white shadow-lg scale-[1.02]",
                        "border-[#EBDCFF]/60 bg-[#EBDCFF]/5 scale-[1.02] shadow-lg"
                      )
                    : c(
                        "border-black/5 bg-[#F5F5F7] hover:bg-white hover:border-black/10 hover:shadow-md",
                        "border-white/[0.06] bg-[#1f1f23] hover:border-white/15"
                      )
                } ${p.custom ? "border-dashed" : ""}`}
              >
                {isSelected && (
                  <div
                    className={`absolute top-2 right-2 sm:top-4 sm:right-4 w-4 h-4 sm:w-6 sm:h-6 rounded-full flex items-center justify-center shadow-md ${
                      c("bg-[#1c1c1e]", "bg-[#EBDCFF]")
                    }`}
                  >
                    <span className={`material-symbols-outlined text-[10px] sm:text-[14px] ${c("text-white", "text-[#1c1c1e]")}`}>
                      check
                    </span>
                  </div>
                )}

                {p.custom ? (
                  <div className="flex flex-col items-center justify-center py-4 sm:py-6 text-center h-full">
                    <div className="text-[28px] sm:text-[40px] mb-2 sm:mb-4 drop-shadow-sm">{p.emoji}</div>
                    <h4 className={`text-[14px] sm:text-[16px] font-bold mb-1 sm:mb-2 ${c("text-[#1c1c1e]", "text-white")}`}>
                      {p.name}
                    </h4>
                    <p className={`text-[10px] sm:text-[12px] font-medium leading-relaxed line-clamp-3 sm:line-clamp-none ${c("text-[#1c1c1e]/50", "text-[#85948b]")}`}>
                      {p.description}
                    </p>
                  </div>
                ) : (
                  <div className="flex flex-col h-full">
                    <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4 mb-3 sm:mb-4">
                      <div
                        className="w-10 h-10 sm:w-14 sm:h-14 rounded-xl sm:rounded-2xl flex items-center justify-center text-[20px] sm:text-[28px] flex-shrink-0 shadow-sm"
                        style={{ background: isDark ? p.bgDark : p.bgLight }}
                      >
                        {p.emoji}
                      </div>
                      <div className="min-w-0">
                        <h4 className={`text-[14px] sm:text-[17px] font-bold truncate ${c("text-[#1c1c1e]", "text-white")}`}>{p.name}</h4>
                        <p className="text-[9px] sm:text-[11px] font-bold uppercase tracking-[0.1em] sm:tracking-[0.15em] truncate" style={{ color: isDark ? p.color : c(p.color === "#f5c5ff" ? "#d073e6" : p.color === "#59eeb4" ? "#0b9662" : p.color === "#b0c6ff" ? "#295bd9" : p.color === "#ffb4ab" ? "#d14b3d" : p.color, p.color) }}>
                          {p.role}
                        </p>
                      </div>
                    </div>

                    <p className={`text-[11px] sm:text-[13px] leading-relaxed mb-3 sm:mb-4 flex-1 font-medium line-clamp-2 sm:line-clamp-none ${c("text-[#1c1c1e]/60", "text-white/60")}`}>
                      {p.description}
                    </p>

                    <div className="flex flex-wrap gap-1 sm:gap-2 mb-4 sm:mb-5">
                      {p.traits.slice(0, 3).map((t) => (
                        <span
                          key={t}
                          className="text-[8px] sm:text-[10px] font-bold px-1.5 py-0.5 sm:px-2.5 sm:py-1 rounded-full border"
                          style={{
                            color: isDark ? p.color : c(p.color === "#f5c5ff" ? "#d073e6" : p.color === "#59eeb4" ? "#0b9662" : p.color === "#b0c6ff" ? "#295bd9" : p.color === "#ffb4ab" ? "#d14b3d" : p.color, p.color),
                            backgroundColor: isDark ? p.bgDark : p.bgLight,
                            borderColor: "transparent"
                          }}
                        >
                          {t}
                        </span>
                      ))}
                    </div>

                    {/* Sample message bubble */}
                    <div
                      className={`hidden sm:block rounded-2xl p-4 border mt-auto relative shadow-inner ${
                        c("bg-white border-black/5", "bg-[#131317] border-white/[0.04]")
                      }`}
                    >
                      <div className={`absolute -top-3 left-4 px-2 text-[9px] font-bold uppercase tracking-widest ${
                        c("bg-white text-[#1c1c1e]/40", "bg-[#131317] text-[#55635a]")
                      }`}>
                        Sample Greeting
                      </div>
                      <p className={`text-[13px] leading-relaxed italic ${c("text-[#1c1c1e]/70", "text-[#bbcac0]")}`}>
                        "{p.greeting}"
                      </p>
                    </div>
                  </div>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* Custom persona form */}
      {selected === "custom" && (
        <div
          className={`rounded-[2rem] border p-4 sm:p-8 space-y-6 animate-in slide-in-from-bottom-4 duration-300 ${
            isDark ? "bg-[#1f1f23] border-white/[0.06]" : "bg-white border-black/5 shadow-[0_8px_30px_rgb(0,0,0,0.02)]"
          }`}
        >
           <h3 className={`text-[16px] font-bold flex items-center gap-2 ${c("text-[#1c1c1e]", "text-white")}`}>
            <span className={`material-symbols-outlined text-[20px] ${c("text-[#1c1c1e]/40", "text-[#EBDCFF]")}`}>tune</span>
            Custom Persona Builder
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className={`block text-[11px] font-bold uppercase tracking-widest mb-2 ${c("text-[#1c1c1e]/50", "text-[#85948b]")}`}>
                Persona Name
              </label>
              <input
                type="text"
                value={customName}
                onChange={(e) => setCustomName(e.target.value)}
                className={`w-full rounded-xl px-5 py-3.5 text-[14px] font-medium outline-none transition-all shadow-inner ${
                  isDark
                    ? "bg-[#131317] border border-white/[0.06] text-white focus:border-[#EBDCFF]/50"
                    : "bg-[#F5F5F7] border border-black/5 text-[#1c1c1e] focus:border-black/20 focus:bg-white"
                }`}
                placeholder="e.g. Zara"
              />
            </div>
            <div>
              <label className={`block text-[11px] font-bold uppercase tracking-widest mb-2 ${c("text-[#1c1c1e]/50", "text-[#85948b]")}`}>
                Role / Title
              </label>
              <input
                type="text"
                value={customRole}
                onChange={(e) => setCustomRole(e.target.value)}
                className={`w-full rounded-xl px-5 py-3.5 text-[14px] font-medium outline-none transition-all shadow-inner ${
                  isDark
                    ? "bg-[#131317] border border-white/[0.06] text-white focus:border-[#EBDCFF]/50"
                    : "bg-[#F5F5F7] border border-black/5 text-[#1c1c1e] focus:border-black/20 focus:bg-white"
                }`}
                placeholder="e.g. Brand Ambassador"
              />
            </div>
          </div>

          <div>
            <label className={`block text-[11px] font-bold uppercase tracking-widest mb-3 ${c("text-[#1c1c1e]/50", "text-[#85948b]")}`}>
              Conversation Tone
            </label>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              {[
                { id: "formal", label: "Formal", emoji: "🎩" },
                { id: "friendly", label: "Friendly", emoji: "😊" },
                { id: "casual", label: "Casual", emoji: "😎" },
                { id: "empathetic", label: "Empathetic", emoji: "💙" },
              ].map((t) => (
                <label key={t.id} className="cursor-pointer">
                  <input
                    type="radio"
                    name="customTone"
                    value={t.id}
                    checked={customTone === t.id}
                    onChange={() => setCustomTone(t.id)}
                    className="hidden peer"
                  />
                  <div
                    className={`py-4 rounded-2xl border text-center transition-all shadow-sm ${
                      isDark
                        ? "bg-[#131317] border-white/[0.06] peer-checked:border-[#EBDCFF]/50 peer-checked:bg-[#EBDCFF]/10 text-white/50 peer-checked:text-white"
                        : "bg-[#F5F5F7] border-black/5 peer-checked:border-[#1c1c1e]/50 peer-checked:bg-white peer-checked:shadow-md text-[#1c1c1e]/50 peer-checked:text-[#1c1c1e]"
                    }`}
                  >
                    <div className="text-[28px] mb-2">{t.emoji}</div>
                    <div className="text-[13px] font-bold">
                      {t.label}
                    </div>
                  </div>
                </label>
              ))}
            </div>
          </div>

          <div>
             <label className={`block text-[11px] font-bold uppercase tracking-widest mb-2 ${c("text-[#1c1c1e]/50", "text-[#85948b]")}`}>
              Opening Greeting Message
             </label>
            <textarea
              value={customGreeting}
              onChange={(e) => setCustomGreeting(e.target.value)}
              rows={3}
              className={`w-full rounded-xl px-5 py-4 text-[14px] font-medium outline-none transition-all shadow-inner resize-none ${
                isDark
                  ? "bg-[#131317] border border-white/[0.06] text-white focus:border-[#EBDCFF]/50"
                  : "bg-[#F5F5F7] border border-black/5 text-[#1c1c1e] focus:border-black/20 focus:bg-white"
              }`}
              placeholder="Write the first message your bot will say to a user..."
            />
             <p className={`text-[11px] font-medium mt-2 ${c("text-[#1c1c1e]/40", "text-[#55635a]")}`}>
              Tip: Start with a warm greeting in the user's language. Mention their name if available.
            </p>
          </div>

          <div>
            <label className={`block text-[11px] font-bold uppercase tracking-widest mb-2 ${c("text-[#1c1c1e]/50", "text-[#85948b]")}`}>
              Fallback Response
            </label>
            <textarea
              rows={2}
               className={`w-full rounded-xl px-5 py-4 text-[14px] font-medium outline-none transition-all shadow-inner resize-none ${
                isDark
                  ? "bg-[#131317] border border-white/[0.06] text-white focus:border-[#EBDCFF]/50"
                  : "bg-[#F5F5F7] border border-black/5 text-[#1c1c1e] focus:border-black/20 focus:bg-white"
              }`}
              placeholder="What should the bot say when it doesn't know the answer?"
            />
          </div>

          {/* Human-feel tips */}
          <div
            className={`rounded-2xl p-5 border ${
              isDark ? "bg-[#131317] border-[#EBDCFF]/15" : "bg-white border-[#1c1c1e]/10 shadow-sm"
            }`}
          >
            <h4
              className={`text-[12px] font-bold uppercase tracking-widest mb-4 flex items-center gap-2 ${
                c("text-[#1c1c1e]", "text-[#EBDCFF]")
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
                  <span className={`mt-0.5 flex-shrink-0 text-[16px] font-bold ${c("text-[#1c1c1e]", "text-[#EBDCFF]")}`}>·</span>
                  {tip}
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* Preview of selected non-custom persona */}
      {selected !== "custom" && persona && !persona.custom && (
        <div
          className={`rounded-[2rem] border p-4 sm:p-8 animate-in slide-in-from-bottom-4 duration-300 ${
            isDark ? "bg-[#1f1f23] border-white/[0.06]" : "bg-white border-black/5 shadow-[0_8px_30px_rgb(0,0,0,0.02)]"
          }`}
        >
          <h3 className={`text-[15px] font-bold mb-6 flex items-center gap-3 ${c("text-[#1c1c1e]", "text-white")}`}>
            <span className="text-[24px]">{persona.emoji}</span>
            Persona Preview — {persona.name}
          </h3>
          <div className="space-y-4 max-w-2xl mx-auto">
            {/* Bot message */}
            <div className="flex gap-4 items-end">
              <div
                className="w-10 h-10 rounded-2xl flex items-center justify-center text-[18px] flex-shrink-0 shadow-sm"
                style={{ background: isDark ? persona.bgDark : persona.bgLight }}
              >
                {persona.emoji}
              </div>
              <div
                className="rounded-3xl rounded-tl-sm px-5 py-4 shadow-sm"
                style={{
                  backgroundColor: isDark ? persona.bgDark : persona.bgLight,
                  borderColor: isDark ? "transparent" : "rgba(0,0,0,0.05)",
                  borderWidth: "1px"
                }}
              >
                <p className={`text-[14px] font-medium leading-relaxed ${isDark ? "text-white" : "text-[#1c1c1e]"}`}>
                  {persona.greeting}
                </p>
              </div>
            </div>

            {/* User message */}
            <div className="flex gap-4 items-end flex-row-reverse">
              <div
                className={`w-10 h-10 rounded-2xl flex items-center justify-center text-[14px] font-bold flex-shrink-0 shadow-sm ${
                  c("bg-[#1c1c1e] text-white", "bg-[#2a2a2e] text-white")
                }`}
              >
                U
              </div>
              <div
                className={`rounded-3xl rounded-tr-sm px-5 py-4 shadow-sm border ${
                  c("bg-white border-black/5", "bg-[#2a2a2e] border-white/[0.06]")
                }`}
              >
                <p className={`text-[14px] font-medium leading-relaxed ${c("text-[#1c1c1e]", "text-[#bbcac0]")}`}>
                  I need help with my order
                </p>
              </div>
            </div>

            {/* Bot reply */}
            <div className="flex gap-4 items-end">
              <div
                className="w-10 h-10 rounded-2xl flex items-center justify-center text-[18px] flex-shrink-0 shadow-sm"
                style={{ background: isDark ? persona.bgDark : persona.bgLight }}
              >
                {persona.emoji}
              </div>
              <div
                className="rounded-3xl rounded-tl-sm px-5 py-4 shadow-sm"
                style={{
                  backgroundColor: isDark ? persona.bgDark : persona.bgLight,
                  borderColor: isDark ? "transparent" : "rgba(0,0,0,0.05)",
                  borderWidth: "1px"
                }}
              >
                <p className={`text-[14px] font-medium leading-relaxed ${isDark ? "text-white" : "text-[#1c1c1e]"}`}>
                  Bilkul! Main abhi aap ka order check karta hoon. Aap ka order number kya hai? 🔍
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
