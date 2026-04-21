import { useState, useRef } from "react";
import Sidebar from "../components/Sidebar";
import TopBar from "../components/TopBar";
import { useTheme } from "../contexts/ThemeContext";

/* ─────────────────────────────────────────────────────────────────────────────
   TYPES
───────────────────────────────────────────────────────────────────────────── */
interface Persona {
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

interface KnowledgeItem {
  id: string;
  type: "file" | "text" | "website" | "email" | "phone" | "app";
  label: string;
  value: string;
  status: "indexed" | "processing" | "queued";
}

interface ChatMessage {
  role: "user" | "bot";
  text: string;
}

/* ─────────────────────────────────────────────────────────────────────────────
   STATIC DATA
───────────────────────────────────────────────────────────────────────────── */
const BUILT_IN_PERSONAS: Persona[] = [
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

const KNOWLEDGE_TYPES = [
  { type: "file", icon: "upload_file", label: "Documents", hint: "PDF, DOCX, TXT, CSV", color: "#b0c6ff" },
  { type: "text", icon: "edit_note", label: "Text / Guidelines", hint: "Paste instructions directly", color: "#f5c5ff" },
  { type: "website", icon: "language", label: "Website URL", hint: "We'll crawl your site", color: "#59eeb4" },
  { type: "email", icon: "mail", label: "Contact Email", hint: "For escalation handover", color: "#ffb4ab" },
  { type: "phone", icon: "phone", label: "Phone Number", hint: "For WhatsApp escalation", color: "#EBDCFF" },
  { type: "app", icon: "apps", label: "App / API", hint: "Connect a data source", color: "#b0c6ff" },
] as const;

const STEPS = [
  { num: 1, label: "Persona", icon: "face" },
  { num: 2, label: "Knowledge", icon: "menu_book" },
  { num: 3, label: "Test", icon: "chat_bubble" },
  { num: 4, label: "Deploy", icon: "rocket_launch" },
];

/* ─────────────────────────────────────────────────────────────────────────────
   STEP PROGRESS BAR
───────────────────────────────────────────────────────────────────────────── */
function StepBar({ current, onStep }: { current: number; onStep: (n: number) => void }) {
  const { isDark } = useTheme();
  const c = (light: string, dark: string) => (isDark ? dark : light);

  return (
    <div className="flex items-center flex-shrink-0 lg:w-full lg:max-w-xl mx-auto overflow-x-auto no-scrollbar py-2">
      {STEPS.map((step, idx) => {
        const done = current > step.num;
        const active = current === step.num;
        return (
          <div key={step.num} className="flex items-center flex-shrink-0">
            <button
              onClick={() => done && onStep(step.num)}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-full transition-all text-[12px] font-bold ${
                active
                  ? c("bg-[#1c1c1e] text-[#fbfbf2] shadow-md", "bg-[#EBDCFF] text-[#1c1c1e] shadow-md")
                  : done
                  ? c("text-[#1c1c1e] hover:bg-black/5 cursor-pointer", "text-white hover:bg-white/5 cursor-pointer")
                  : c("text-[#1c1c1e]/40 cursor-default", "text-white/30 cursor-default")
              }`}
            >
              <div
                className={`w-6 h-6 rounded-full flex items-center justify-center text-[11px] font-bold flex-shrink-0 transition-colors ${
                  active
                    ? c("bg-[#fbfbf2] text-[#1c1c1e]", "bg-[#1c1c1e] text-[#EBDCFF]")
                    : done
                    ? c("bg-[#1c1c1e]/10 text-[#1c1c1e]", "bg-[#EBDCFF]/20 text-[#EBDCFF]")
                    : c("bg-black/5 text-[#1c1c1e]/40", "bg-[#2a2a2e] text-white/30")
                }`}
              >
                {done ? (
                  <span className="material-symbols-outlined text-[13px]">check</span>
                ) : (
                  step.num
                )}
              </div>
              <span className="hidden sm:inline">{step.label}</span>
            </button>
            {idx < STEPS.length - 1 && (
              <div
                className={`w-4 lg:w-8 h-[2px] mx-1 transition-colors rounded-full ${
                  done ? c("bg-[#1c1c1e]/30", "bg-[#EBDCFF]/40") : c("bg-black/5", "bg-white/[0.06]")
                }`}
              ></div>
            )}
          </div>
        );
      })}
    </div>
  );
}

/* ─────────────────────────────────────────────────────────────────────────────
   STEP 1 — PERSONA SELECTION
───────────────────────────────────────────────────────────────────────────── */
function Step1Persona({
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
}: any) {
  const { isDark } = useTheme();
  const c = (light: string, dark: string) => (isDark ? dark : light);
  const persona = BUILT_IN_PERSONAS.find((p) => p.id === selected);

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* Bot basic info */}
      <div
        className={`rounded-[2rem] border p-8 ${
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
                  : "bg-[#fbfbf2] border border-black/5 text-[#1c1c1e] focus:border-black/20 focus:bg-white"
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
                  : "bg-[#fbfbf2] border border-black/5 text-[#1c1c1e] focus:border-black/20 focus:bg-white"
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

        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-6">
          {BUILT_IN_PERSONAS.map((p) => {
            const isSelected = selected === p.id;
            return (
              <button
                key={p.id}
                onClick={() => onSelect(p.id)}
                className={`relative text-left p-6 rounded-3xl border transition-all duration-300 group ${
                  isSelected
                    ? c(
                        "border-[#1c1c1e] bg-white shadow-lg scale-[1.02]",
                        "border-[#EBDCFF]/60 bg-[#EBDCFF]/5 scale-[1.02] shadow-lg"
                      )
                    : c(
                        "border-black/5 bg-[#fbfbf2] hover:bg-white hover:border-black/10 hover:shadow-md",
                        "border-white/[0.06] bg-[#1f1f23] hover:border-white/15"
                      )
                } ${p.custom ? "border-dashed" : ""}`}
              >
                {isSelected && (
                  <div
                    className={`absolute top-4 right-4 w-6 h-6 rounded-full flex items-center justify-center shadow-md ${
                      c("bg-[#1c1c1e]", "bg-[#EBDCFF]")
                    }`}
                  >
                    <span className={`material-symbols-outlined text-[14px] ${c("text-white", "text-[#1c1c1e]")}`}>
                      check
                    </span>
                  </div>
                )}

                {p.custom ? (
                  <div className="flex flex-col items-center justify-center py-6 text-center h-full">
                    <div className="text-[40px] mb-4 drop-shadow-sm">{p.emoji}</div>
                    <h4 className={`text-[16px] font-bold mb-2 ${c("text-[#1c1c1e]", "text-white")}`}>
                      {p.name}
                    </h4>
                    <p className={`text-[12px] font-medium leading-relaxed ${c("text-[#1c1c1e]/50", "text-[#85948b]")}`}>
                      {p.description}
                    </p>
                  </div>
                ) : (
                  <div className="flex flex-col h-full">
                    <div className="flex items-center gap-4 mb-4">
                      <div
                        className="w-14 h-14 rounded-2xl flex items-center justify-center text-[28px] flex-shrink-0 shadow-sm"
                        style={{ background: isDark ? p.bgDark : p.bgLight }}
                      >
                        {p.emoji}
                      </div>
                      <div>
                        <h4 className={`text-[17px] font-bold ${c("text-[#1c1c1e]", "text-white")}`}>{p.name}</h4>
                        <p className="text-[11px] font-bold uppercase tracking-[0.15em]" style={{ color: isDark ? p.color : c(p.color === "#f5c5ff" ? "#d073e6" : p.color === "#59eeb4" ? "#0b9662" : p.color === "#b0c6ff" ? "#295bd9" : p.color === "#ffb4ab" ? "#d14b3d" : p.color, p.color) }}>
                          {p.role}
                        </p>
                      </div>
                    </div>

                    <p className={`text-[13px] leading-relaxed mb-4 flex-1 font-medium ${c("text-[#1c1c1e]/60", "text-white/60")}`}>
                      {p.description}
                    </p>

                    <div className="flex flex-wrap gap-2 mb-5">
                      {p.traits.map((t) => (
                        <span
                          key={t}
                          className="text-[10px] font-bold px-2.5 py-1 rounded-full border"
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
                      className={`rounded-2xl p-4 border mt-auto relative shadow-inner ${
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
          className={`rounded-[2rem] border p-8 space-y-6 animate-in slide-in-from-bottom-4 duration-300 ${
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
                    : "bg-[#fbfbf2] border border-black/5 text-[#1c1c1e] focus:border-black/20 focus:bg-white"
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
                    : "bg-[#fbfbf2] border border-black/5 text-[#1c1c1e] focus:border-black/20 focus:bg-white"
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
                        : "bg-[#fbfbf2] border-black/5 peer-checked:border-[#1c1c1e]/50 peer-checked:bg-white peer-checked:shadow-md text-[#1c1c1e]/50 peer-checked:text-[#1c1c1e]"
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
                  : "bg-[#fbfbf2] border border-black/5 text-[#1c1c1e] focus:border-black/20 focus:bg-white"
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
                  : "bg-[#fbfbf2] border border-black/5 text-[#1c1c1e] focus:border-black/20 focus:bg-white"
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
          className={`rounded-[2rem] border p-8 animate-in slide-in-from-bottom-4 duration-300 ${
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

/* ─────────────────────────────────────────────────────────────────────────────
   STEP 2 — KNOWLEDGE BASE
───────────────────────────────────────────────────────────────────────────── */
function Step2Knowledge({
  items,
  setItems,
}: {
  items: KnowledgeItem[];
  setItems: React.Dispatch<React.SetStateAction<KnowledgeItem[]>>;
}) {
  const [activeType, setActiveType] = useState<string>("file");
  const [inputValue, setInputValue] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);
  const { isDark } = useTheme();
  const c = (light: string, dark: string) => (isDark ? dark : light);

  const addItem = () => {
    if (!inputValue.trim() && activeType !== "file") return;
    const typeInfo = KNOWLEDGE_TYPES.find((k) => k.type === activeType);
    const newItem: KnowledgeItem = {
      id: Date.now().toString(),
      type: activeType as KnowledgeItem["type"],
      label: typeInfo?.label ?? activeType,
      value: inputValue.trim() || "Uploaded document",
      status: "processing",
    };
    setItems([...items, newItem]);
    setInputValue("");
    setTimeout(() => {
      setItems((prev: KnowledgeItem[]) =>
        prev.map((i) => (i.id === newItem.id ? { ...i, status: "indexed" } : i))
      );
    }, 2000);
  };

  const removeItem = (id: string) => setItems(items.filter((i: KnowledgeItem) => i.id !== id));
  const activeTypeInfo = KNOWLEDGE_TYPES.find((k) => k.type === activeType);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 animate-in fade-in duration-300">
      {/* Left: Input panel */}
      <div className="lg:col-span-7 space-y-6">
        <div
          className={`rounded-[2rem] border p-8 ${
            isDark ? "bg-[#1f1f23] border-white/[0.06]" : "bg-white border-black/5 shadow-[0_8px_30px_rgb(0,0,0,0.02)]"
          }`}
        >
          <h3
             className={`text-[20px] font-serif font-bold mb-2 ${c("text-[#1c1c1e]", "text-white")}`}
             style={{ fontFamily: "'Playfair Display', serif" }}
          >
            Add Knowledge Sources
          </h3>
          <p className={`text-[13px] font-medium mb-6 ${c("text-[#1c1c1e]/60", "text-[#85948b]")}`}>
            Everything you add here is what your bot knows. The more you add, the smarter it gets.
          </p>

          {/* Source type tabs */}
          <div className="grid grid-cols-3 sm:grid-cols-6 gap-3 mb-8">
            {KNOWLEDGE_TYPES.map((kt) => (
              <button
                key={kt.type}
                onClick={() => setActiveType(kt.type)}
                className={`flex flex-col items-center gap-2 p-4 rounded-2xl border transition-all text-center shadow-sm ${
                  activeType === kt.type
                    ? c("border-[#1c1c1e] bg-black/5 text-[#1c1c1e]", "border-[#EBDCFF]/40 bg-[#EBDCFF]/5 text-[#EBDCFF]")
                    : c("border-black/5 bg-[#fbfbf2] text-[#1c1c1e]/50 hover:text-[#1c1c1e]", "border-white/[0.06] bg-[#131317] text-[#85948b] hover:text-white hover:border-white/15")
                }`}
              >
                <span className="material-symbols-outlined text-[20px]">{kt.icon}</span>
                <span className="text-[10px] font-bold uppercase tracking-widest leading-tight">
                  {kt.label.split(" ")[0]}
                </span>
              </button>
            ))}
          </div>

          {/* Input area */}
          <div className="space-y-4">
            <div className="flex items-center gap-3 mb-4">
              <div
                className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                  isDark ? "bg-white/5" : "bg-black/5 text-[#1c1c1e]"
                }`}
                style={isDark ? { color: activeTypeInfo?.color, backgroundColor: `${activeTypeInfo?.color}15` } : {}}
              >
                <span className="material-symbols-outlined text-[20px]">
                  {activeTypeInfo?.icon}
                </span>
              </div>
              <div>
                <span className={`text-[15px] font-bold ${c("text-[#1c1c1e]", "text-white")}`}>{activeTypeInfo?.label}</span>
                <span className={`text-[12px] font-medium ml-2 ${c("text-[#1c1c1e]/50", "text-[#85948b]")}`}>{activeTypeInfo?.hint}</span>
              </div>
            </div>

            {activeType === "file" ? (
              <div
                onClick={() => fileRef.current?.click()}
                className={`border-2 border-dashed transition-all cursor-pointer rounded-2xl h-48 flex flex-col items-center justify-center gap-3 group ${
                  isDark
                    ? "border-white/[0.08] hover:border-[#EBDCFF]/40 hover:bg-[#EBDCFF]/[0.02]"
                    : "border-black/10 hover:border-[#1c1c1e]/40 hover:bg-black/[0.01]"
                }`}
              >
                <span
                  className={`material-symbols-outlined text-[40px] transition-colors ${
                    c("text-[#1c1c1e]/20 group-hover:text-[#1c1c1e]", "text-white/20 group-hover:text-[#EBDCFF]")
                  }`}
                >
                  cloud_upload
                </span>
                <p className={`text-[15px] font-bold transition-colors ${c("text-[#1c1c1e]/50 group-hover:text-[#1c1c1e]", "text-white/50 group-hover:text-white")}`}>
                  Click or drag files here
                </p>
                <p className={`text-[12px] font-medium ${c("text-[#1c1c1e]/40", "text-[#55635a]")}`}>PDF, DOCX, TXT, CSV — max 50MB per file</p>
                <input
                  ref={fileRef}
                  type="file"
                  className="hidden"
                  multiple
                  accept=".pdf,.docx,.txt,.csv"
                  onChange={() => {
                    const newItem: KnowledgeItem = {
                      id: Date.now().toString(),
                      type: "file",
                      label: "Documents",
                      value: "Uploaded document",
                      status: "processing",
                    };
                    setItems([...items, newItem]);
                    setTimeout(() => {
                      setItems((prev: KnowledgeItem[]) =>
                        prev.map((i) => (i.id === newItem.id ? { ...i, status: "indexed" } : i))
                      );
                    }, 2000);
                  }}
                />
              </div>
            ) : activeType === "text" ? (
              <textarea
                rows={6}
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                className={`w-full rounded-xl px-5 py-4 text-[14px] font-medium outline-none transition-all shadow-inner resize-none ${
                  isDark
                    ? "bg-[#131317] border border-white/[0.06] text-white focus:border-[#EBDCFF]/50"
                    : "bg-[#fbfbf2] border border-black/5 text-[#1c1c1e] focus:border-black/20 focus:bg-white"
                }`}
                placeholder="Paste your guidelines, FAQs, product descriptions, policies, or any text your bot should know..."
              />
            ) : (
              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                className={`w-full rounded-xl px-5 py-4 text-[14px] font-medium outline-none transition-all shadow-inner ${
                  isDark
                    ? "bg-[#131317] border border-white/[0.06] text-white focus:border-[#EBDCFF]/50"
                    : "bg-[#fbfbf2] border border-black/5 text-[#1c1c1e] focus:border-black/20 focus:bg-white"
                }`}
                placeholder={
                  activeType === "website"
                    ? "https://yourwebsite.com"
                    : activeType === "email"
                    ? "support@yourcompany.com"
                    : activeType === "phone"
                    ? "+92 300 1234567"
                    : "API endpoint or app name"
                }
                onKeyDown={(e) => e.key === "Enter" && addItem()}
              />
            )}

            {activeType !== "file" && (
              <button
                onClick={addItem}
                className={`w-full py-4 rounded-xl font-bold text-[14px] transition-all flex items-center justify-center gap-2 shadow-md active:scale-[0.98] mt-2 ${
                  isDark
                    ? "bg-[#EBDCFF] hover:bg-[#d8bfff] text-[#1c1c1e]"
                    : "bg-[#1c1c1e] hover:bg-black text-[#fbfbf2]"
                }`}
              >
                <span className="material-symbols-outlined text-[18px]">add_circle</span>
                Add to Knowledge Base
              </button>
            )}
          </div>
        </div>
        
        {/* Knowledge quality tips */}
        <div
          className={`rounded-2xl p-6 border ${
            isDark ? "bg-[#1f1f23] border-white/[0.06]" : "bg-white border-black/5 shadow-sm"
          }`}
        >
          <h4
            className={`text-[12px] font-bold uppercase tracking-widest mb-4 flex items-center gap-2.5 ${
              c("text-[#1c1c1e]", "text-[#EBDCFF]")
            }`}
          >
            <span className={`material-symbols-outlined text-[18px] ${c("text-black", "text-[#EBDCFF]")}`}>tips_and_updates</span>
            Knowledge Quality Tips
          </h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {[
              { icon: "check_circle", tip: "Add a full FAQ document for 80% better accuracy", color: isDark ? "#EBDCFF" : "#1c1c1e" },
              { icon: "link", tip: "Link your website for auto-updated product info", color: isDark ? "#b0c6ff" : "#295bd9" },
              { icon: "phone", tip: "Add your phone for seamless human handover", color: isDark ? "#ffb4ab" : "#d14b3d" },
              { icon: "description", tip: "Include your pricing PDF to handle sales queries", color: isDark ? "#f5c5ff" : "#d073e6" },
            ].map((t) => (
              <div key={t.tip} className="flex items-start gap-3">
                <span className="material-symbols-outlined text-[18px] mt-0.5" style={{ color: t.color }}>
                  {t.icon}
                </span>
                <p className={`text-[12px] font-medium leading-relaxed ${c("text-[#1c1c1e]/70", "text-[#85948b]")}`}>{t.tip}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Right: Knowledge items list */}
      <div className="lg:col-span-5">
        <div
          className={`rounded-[2rem] border p-8 sticky top-6 flex flex-col ${
            isDark ? "bg-[#1f1f23] border-white/[0.06]" : "bg-white border-black/5 shadow-[0_8px_30px_rgb(0,0,0,0.02)]"
          }`}
          style={{ minHeight: '600px' }}
        >
          <div className="flex items-center justify-between mb-8">
            <h3
             className={`text-[20px] font-serif font-bold ${c("text-[#1c1c1e]", "text-white")}`}
             style={{ fontFamily: "'Playfair Display', serif" }}
            >
              Knowledge Base
            </h3>
            <span
              className={`text-[11px] font-bold px-3 py-1.5 rounded-full border shadow-sm ${
                isDark ? "text-[#EBDCFF] bg-[#EBDCFF]/10 border-[#EBDCFF]/20" : "text-[#1c1c1e] bg-black/5 border-transparent"
              }`}
            >
              {items.length} source{items.length !== 1 ? "s" : ""}
            </span>
          </div>

          {items.length === 0 ? (
            <div className={`flex-1 flex flex-col items-center justify-center text-center gap-3 ${c("text-[#1c1c1e]/30", "text-white/20")}`}>
              <span className="material-symbols-outlined text-[48px] mb-2">inbox</span>
              <p className="text-[15px] font-bold">No sources yet</p>
              <p className="text-[13px] font-medium">Add documents, website, or contact info</p>
            </div>
          ) : (
            <div className="flex-1 space-y-3 overflow-y-auto pr-2 no-scrollbar mb-6">
              {items.map((item: any) => {
                const typeInfo = KNOWLEDGE_TYPES.find((k) => k.type === item.type);
                return (
                  <div
                    key={item.id}
                    className={`p-4 rounded-2xl border flex items-center gap-4 transition-all group ${
                      isDark
                        ? "bg-[#131317] border-white/[0.04] hover:border-white/10"
                        : "bg-[#fbfbf2] border-black/5 hover:border-black/10 hover:shadow-sm"
                    }`}
                  >
                    <div
                      className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 shadow-sm ${isDark ? "" : "bg-white"}`}
                      style={isDark ? { backgroundColor: `${typeInfo?.color}15`, color: typeInfo?.color } : { color: "#1c1c1e" }}
                    >
                      <span className="material-symbols-outlined text-[20px]">
                        {typeInfo?.icon}
                      </span>
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className={`text-[14px] font-bold truncate ${c("text-[#1c1c1e]", "text-white")}`}>{item.value}</p>
                      <p className={`text-[11px] font-medium mt-0.5 ${c("text-[#1c1c1e]/50", "text-[#55635a]")}`}>{item.label}</p>
                    </div>
                    <div className="flex items-center gap-3 flex-shrink-0">
                      {item.status === "processing" ? (
                        <span className={`text-[10px] font-bold px-2.5 py-1 rounded-full animate-pulse border ${
                          isDark ? "text-yellow-300 bg-yellow-300/10 border-yellow-300/20" : "text-yellow-700 bg-yellow-100 border-yellow-200"
                        }`}>
                          Processing
                        </span>
                      ) : (
                        <span className={`text-[10px] font-bold px-2.5 py-1 rounded-full border shadow-sm ${
                          isDark ? "text-[#EBDCFF] bg-[#EBDCFF]/10 border-[#EBDCFF]/20" : "text-[#1c1c1e] bg-white border-black/5"
                        }`}>
                          ✓ Indexed
                        </span>
                      )}
                      <button
                        onClick={() => removeItem(item.id)}
                        className={`opacity-0 group-hover:opacity-100 transition-all ${
                          c("text-red-400 hover:text-red-600", "text-white/30 hover:text-red-400")
                        }`}
                      >
                        <span className="material-symbols-outlined text-[20px]">close</span>
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {items.length > 0 && (
            <div className={`pt-6 mt-auto border-t ${c("border-black/5", "border-white/[0.04]")}`}>
              <div className="flex justify-between text-[13px] font-bold mb-3">
                <span className={c("text-[#1c1c1e]/60", "text-[#85948b]")}>Knowledge Coverage</span>
                <span className={c("text-[#1c1c1e]", "text-[#EBDCFF]")}>{Math.min(items.length * 20, 95)}%</span>
              </div>
              <div className={`w-full h-2 rounded-full overflow-hidden shadow-inner ${c("bg-black/5", "bg-[#131317]")}`}>
                <div
                  className={`h-full rounded-full transition-all duration-500 ${c("bg-[#1c1c1e]", "bg-[#EBDCFF]")}`}
                  style={{ width: `${Math.min(items.length * 20, 95)}%` }}
                ></div>
              </div>
              <p className={`text-[11px] font-medium mt-3 text-center ${c("text-[#1c1c1e]/50", "text-[#55635a]")}`}>
                {items.length < 5 ? "Add more sources for better accuracy" : "Great coverage! Your bot is well-trained."}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

/* ─────────────────────────────────────────────────────────────────────────────
   STEP 3 — BUILD & TEST
───────────────────────────────────────────────────────────────────────────── */
function Step3Test({ persona, botName }: any) {
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

  // Fake logic for demo
  const DEMO_RESPONSES: Record<string, string> = {
    "hello": `${persona?.greeting ?? "Hello! How can I help?"}`,
    "hi": `Hello there! 😊 Main ${botName || "AI Bot"} hoon. Kya madad kar sakta hoon?`,
    "price": "Hamari Professional plan sirf PKR 8,500/month mein available hai — jisme 5 bots, 5,000 messages, aur WhatsApp integration shamil hai! Kya aap free trial start karna chahte hain?",
    "pricing": "Hamari pricing plans: Free (0/mo), Professional (PKR 8,500/mo), aur Enterprise (custom). Kaunsa aap ke liye best hai?",
    "help": "Main aap ki poori madad karne ke liye yahan hoon! Aap mujhse kuch bhi pooch sakte hain — products, pricing, ya technical support. Kya chahiye?",
    "whatsapp": "Bilkul! Aap ka bot WhatsApp pe deploy ho sakta hai. Setup mein sirf 5 minute lagte hain. Kya main aap ko guide karoon? 🚀",
    "contact": "Aap humse rabta kar sakte hain:\n📧 Email: support@aina.ai\n📞 Phone: +92 300 1234567\n🌐 Website: aina.ai",
    "default": "That's a great question! Main is ke baare mein check kar raha hoon... 🔍 Meri knowledge base ke mutabiq, main chahta hoon ke aap ko best answer milein. Kya aap thoda aur detail de sakte hain?",
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

  const p = persona;
  const displayName = botName || p?.name || "Aina Bot";

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 animate-in fade-in duration-300">
      {/* Left: Build status */}
      <div className="lg:col-span-5 space-y-6">
        <div
          className={`rounded-[2rem] border p-8 shadow-sm ${
            isDark ? "bg-[#1f1f23] border-white/[0.06]" : "bg-white border-black/5"
          }`}
        >
          <div className="flex items-center gap-4 mb-8">
            <div className={`w-14 h-14 rounded-2xl flex items-center justify-center shadow-inner ${
              isDark ? "bg-[#EBDCFF]/10 text-[#EBDCFF]" : "bg-black/5 text-[#1c1c1e]"
            }`}>
              <span className="material-symbols-outlined text-[28px]">precision_manufacturing</span>
            </div>
            <div>
              <h3
                className={`text-[20px] font-serif font-bold ${c("text-[#1c1c1e]", "text-white")}`}
                style={{ fontFamily: "'Playfair Display', serif" }}
              >
                Bot is Ready!
              </h3>
              <p className={`text-[13px] font-medium mt-1 ${c("text-[#1c1c1e]/60", "text-[#85948b]")}`}>All systems trained and deployed</p>
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
                  isDark ? "bg-[#131317] border-white/[0.04]" : "bg-[#fbfbf2] border-black/5"
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
                  <p className={`text-[11px] font-medium mt-0.5 ${c("text-[#1c1c1e]/50", "text-[#55635a]")}`}>{item.detail}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Quick test prompts */}
        <div
          className={`rounded-[2rem] border p-8 shadow-sm ${
            isDark ? "bg-[#1f1f23] border-white/[0.06]" : "bg-white border-black/5"
          }`}
        >
          <h4
            className={`text-[13px] font-bold uppercase tracking-widest mb-5 ${c("text-[#1c1c1e]/60", "text-[#85948b]")}`}
          >
            Quick Test Prompts
          </h4>
          <div className="flex flex-wrap gap-2.5">
            {[
              "Hi!",
              "What's your pricing?",
              "Help me with WhatsApp",
              "Contact info?",
              "Tell me about plans",
            ].map((prompt) => (
              <button
                key={prompt}
                onClick={() => setInput(prompt)}
                className={`text-[13px] font-bold border px-4 py-2 rounded-full transition-all shadow-sm ${
                  isDark
                    ? "text-[#85948b] border-white/[0.06] hover:border-[#EBDCFF]/40 hover:text-[#EBDCFF] hover:bg-[#EBDCFF]/5"
                    : "text-[#1c1c1e]/70 border-black/10 hover:border-black/30 hover:text-[#1c1c1e] hover:bg-black/5 bg-[#fbfbf2]"
                }`}
              >
                {prompt}
              </button>
            ))}
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
          <div className={`absolute top-0 w-full h-1 z-20 ${c("bg-gradient-to-r from-[#1c1c1e] to-[#1c1c1e]/5", "bg-gradient-to-r from-[#EBDCFF] to-transparent")}`}></div>

          {/* Chat header */}
          <div
            className={`flex items-center gap-4 p-6 border-b z-10 ${
              isDark ? "bg-[#17171a] border-white/[0.06]" : "bg-[#fbfbf2] border-black/5"
            }`}
          >
            <div
              className={`w-12 h-12 rounded-full flex items-center justify-center text-[24px] flex-shrink-0 shadow-sm border ${c("bg-white border-black/5", "border-transparent")}`}
              style={isDark ? { background: p?.bgDark ?? "#EBDCFF15" } : {}}
            >
              {p?.emoji ?? "🤖"}
            </div>
            <div>
              <p className={`text-[16px] font-bold ${c("text-[#1c1c1e]", "text-white")}`}>{displayName}</p>
              <div className="flex items-center gap-2 mt-1">
                <div className={`w-2 h-2 rounded-full animate-pulse ${c("bg-[#1c1c1e]", "bg-[#EBDCFF]")}`}></div>
                <p className={`text-[11px] font-bold uppercase tracking-wider ${c("text-[#1c1c1e]/60", "text-[#EBDCFF]")}`}>Online</p>
              </div>
            </div>
            <div className={`ml-auto flex items-center gap-2 ${c("text-[#1c1c1e]/40", "text-[#55635a]")}`}>
              <button className={`hover:text-current transition-colors w-10 h-10 flex items-center justify-center rounded-full ${isDark ? "hover:bg-white/5" : "hover:bg-black/5"}`}>
                <span className="material-symbols-outlined text-[20px]">more_horiz</span>
              </button>
            </div>
          </div>

          {/* Messages */}
          <div className={`flex-1 overflow-y-auto p-6 space-y-5 ${c("bg-black/[0.02]", "bg-[#131317]")}`}>
            {messages.map((msg, idx) => (
              <div
                key={idx}
                className={`flex gap-3 ${msg.role === "user" ? "flex-row-reverse" : ""}`}
              >
                {msg.role === "bot" ? (
                  <div
                    className={`w-8 h-8 rounded-full flex items-center justify-center text-[16px] flex-shrink-0 mt-auto shadow-sm border ${c("bg-white border-black/5", "border-transparent")}`}
                    style={isDark ? { background: p?.bgDark ?? "#EBDCFF15" } : {}}
                  >
                    {p?.emoji ?? "🤖"}
                  </div>
                ) : (
                   <div className={`w-8 h-8 rounded-full flex items-center justify-center text-[12px] font-bold text-white flex-shrink-0 mt-auto shadow-sm ${c("bg-[#1c1c1e]", "bg-[#2a2a2e]")}`}>
                    U
                  </div>
                )}

                <div
                  className={`max-w-[80%] px-5 py-3.5 rounded-3xl text-[14px] leading-relaxed shadow-sm border ${
                    msg.role === "user"
                      ? c("bg-[#1c1c1e] text-[#fbfbf2] font-semibold border-transparent rounded-tr-md", "bg-[#EBDCFF] text-[#1c1c1e] font-semibold border-transparent rounded-tr-md")
                      : c("bg-white border-black/5 text-[#1c1c1e] font-medium rounded-tl-md", "bg-[#1f1f23] border-white/[0.04] text-[#e4e1e7] font-medium rounded-tl-md")
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
                  className={`w-8 h-8 rounded-full flex items-center justify-center text-[16px] flex-shrink-0 mt-auto shadow-sm border ${c("bg-white border-black/5", "border-transparent")}`}
                  style={isDark ? { background: p?.bgDark ?? "#EBDCFF15" } : {}}
                >
                  {p?.emoji ?? "🤖"}
                </div>
                <div className={`px-5 py-4 rounded-3xl rounded-tl-md flex items-center gap-1.5 shadow-sm border ${c("bg-white border-black/5", "bg-[#1f1f23] border-white/[0.04]")}`}>
                  <div className={`w-2 h-2 rounded-full animate-bounce ${c("bg-[#1c1c1e]/30", "bg-[#85948b]")}`} style={{ animationDelay: "0ms" }}></div>
                  <div className={`w-2 h-2 rounded-full animate-bounce ${c("bg-[#1c1c1e]/30", "bg-[#85948b]")}`} style={{ animationDelay: "150ms" }}></div>
                  <div className={`w-2 h-2 rounded-full animate-bounce ${c("bg-[#1c1c1e]/30", "bg-[#85948b]")}`} style={{ animationDelay: "300ms" }}></div>
                </div>
              </div>
            )}
          </div>

          {/* Input area */}
          <div className={`p-4 border-t z-10 ${isDark ? "bg-[#17171a] border-white/[0.06]" : "bg-white border-black/5"}`}>
            <div className={`flex items-center gap-3 rounded-2xl border px-4 py-3 shadow-inner ${
                isDark ? "bg-[#131317] border-white/[0.06]" : "bg-[#fbfbf2] border-black/10"
            }`}>
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
                     : "bg-[#1c1c1e] hover:bg-black text-[#fbfbf2]"
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

/* ─────────────────────────────────────────────────────────────────────────────
   STEP 4 — DEPLOY
───────────────────────────────────────────────────────────────────────────── */
function Step4Deploy({ botName }: { botName: string }) {
  const { isDark } = useTheme();
  const c = (light: string, dark: string) => (isDark ? dark : light);
  
  const [deployTab, setDeployTab] = useState<"whatsapp" | "web">("whatsapp");
  const [waNumber, setWaNumber] = useState("");
  const [connected, setConnected] = useState(false);

  const displayName = botName || "My Aina Bot";
  const widgetCode = `<!-- Aina AI Widget -->
<script>
  window.AinaConfig = {
    botId: "bot_${Math.random().toString(36).slice(2, 10)}",
    name: "${displayName}",
    theme: "${isDark ? "dark" : "light"}",
    primaryColor: "${isDark ? "#EBDCFF" : "#1c1c1e"}"
  };
</script>
<script src="https://cdn.aina.ai/widget.js" async></script>`;

  return (
    <div className="space-y-8 animate-in fade-in duration-300 max-w-5xl">
      {/* Deploy celebration header */}
      <div
        className={`rounded-[2rem] border p-8 relative overflow-hidden shadow-lg ${
          isDark ? "bg-[#1f1f23] border-[#EBDCFF]/30" : "bg-white border-black/10"
        }`}
      >
        <div
          className={`absolute top-0 left-0 w-full h-1 ${
            isDark ? "bg-gradient-to-r from-[#EBDCFF] via-[#EBDCFF]/50 to-transparent" : "bg-gradient-to-r from-[#1c1c1e] to-transparent"
          }`}
        ></div>
        <div className="flex items-center gap-6">
          <div className="text-[48px] drop-shadow-md">🚀</div>
          <div>
            <h2
               className={`text-[24px] font-serif font-bold ${c("text-[#1c1c1e]", "text-white")}`}
               style={{ fontFamily: "'Playfair Display', serif" }}
            >
              Ready to Go Live!
            </h2>
            <p className={`text-[15px] font-medium mt-1 ${c("text-[#1c1c1e]/60", "text-[#85948b]")}`}>
              <span className={`font-bold ${c("text-[#1c1c1e]", "text-[#EBDCFF]")}`}>{displayName}</span> is fully trained and ready to be deployed.
              Choose your channel below.
            </p>
          </div>
        </div>
      </div>

      {/* Channel selector */}
      <div className="flex gap-4">
        <button
          onClick={() => setDeployTab("whatsapp")}
          className={`flex items-center gap-3 px-6 py-4 rounded-xl font-bold text-[14px] transition-all border shadow-sm ${
            deployTab === "whatsapp"
              ? c("border-[#1c1c1e] bg-[#1c1c1e] text-[#fbfbf2]", "border-[#EBDCFF]/50 bg-[#EBDCFF]/10 text-[#EBDCFF]")
              : c("border-black/5 bg-[#fbfbf2] text-[#1c1c1e]/60 hover:text-[#1c1c1e] hover:bg-white", "border-white/[0.06] bg-[#1f1f23] text-[#85948b] hover:text-white")
          }`}
        >
          <span className="material-symbols-outlined text-[20px]">chat</span>
          WhatsApp
        </button>
        <button
          onClick={() => setDeployTab("web")}
           className={`flex items-center gap-3 px-6 py-4 rounded-xl font-bold text-[14px] transition-all border shadow-sm ${
            deployTab === "web"
              ? c("border-[#1c1c1e] bg-[#1c1c1e] text-[#fbfbf2]", "border-[#EBDCFF]/50 bg-[#EBDCFF]/10 text-[#EBDCFF]")
              : c("border-black/5 bg-[#fbfbf2] text-[#1c1c1e]/60 hover:text-[#1c1c1e] hover:bg-white", "border-white/[0.06] bg-[#1f1f23] text-[#85948b] hover:text-white")
          }`}
        >
          <span className="material-symbols-outlined text-[20px]">language</span>
          Web Widget
        </button>
      </div>

      {/* WhatsApp Panel */}
      {deployTab === "whatsapp" && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div
            className={`rounded-[2rem] border p-8 space-y-6 shadow-sm ${
              isDark ? "bg-[#1f1f23] border-white/[0.06]" : "bg-white border-black/5"
            }`}
          >
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-[#25D366]/10 flex items-center justify-center">
                <span className="material-symbols-outlined text-[#25D366] text-[24px]">chat</span>
              </div>
              <div>
                <h3 className={`text-[16px] font-bold ${c("text-[#1c1c1e]", "text-white")}`}>WhatsApp Business</h3>
                <p className={`text-[12px] font-medium mt-1 ${c("text-[#1c1c1e]/50", "text-[#85948b]")}`}>Connect your WhatsApp Business number</p>
              </div>
            </div>

            {!connected ? (
              <div className="space-y-6 pt-2">
                <div>
                  <label className={`block text-[11px] font-bold uppercase tracking-widest mb-2 ${c("text-[#1c1c1e]/50", "text-[#85948b]")}`}>
                    WhatsApp Business Number
                  </label>
                  <input
                    type="tel"
                    value={waNumber}
                    onChange={(e) => setWaNumber(e.target.value)}
                    className={`w-full rounded-xl px-5 py-4 text-[14px] font-medium outline-none transition-all shadow-inner ${
                      isDark
                        ? "bg-[#131317] border border-white/[0.06] text-white focus:border-[#EBDCFF]/50 placeholder:text-[#3c4a42]"
                        : "bg-[#fbfbf2] border border-black/5 text-[#1c1c1e] focus:border-black/20 focus:bg-white placeholder:text-[#1c1c1e]/30"
                    }`}
                    placeholder="+92 300 1234567"
                  />
                </div>

                <button
                  onClick={() => setConnected(true)}
                  className={`w-full py-4 rounded-xl font-bold text-[14px] transition-colors flex items-center justify-center gap-2 shadow-md active:scale-[0.98] ${
                    isDark ? "bg-[#EBDCFF] hover:bg-[#d8bfff] text-[#1c1c1e]" : "bg-[#1c1c1e] hover:bg-black text-[#fbfbf2]"
                  }`}
                >
                  <span className="material-symbols-outlined text-[18px]">link</span>
                  Connect WhatsApp
                </button>

                <div className={`rounded-2xl p-5 border shadow-inner ${isDark ? "bg-[#131317] border-white/[0.04]" : "bg-[#fbfbf2] border-black/5"}`}>
                  <h4 className={`text-[11px] font-bold uppercase tracking-widest mb-4 ${c("text-[#1c1c1e]/60", "text-[#85948b]")}`}>
                    Setup Steps
                  </h4>
                  <ol className="space-y-3">
                    {[
                      "Enter your WhatsApp Business phone number",
                      "We'll send a verification OTP via WhatsApp",
                      "Approve Aina AI as your messaging provider",
                      "Your bot goes live instantly!",
                    ].map((s, i) => (
                      <li key={i} className={`flex items-start gap-3 text-[12px] font-medium ${c("text-[#1c1c1e]/70", "text-[#85948b]")}`}>
                        <span
                          className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold flex-shrink-0 mt-0.5 shadow-sm border border-transparent ${
                            isDark ? "bg-[#2a2a2e] text-[#EBDCFF]" : "bg-white border-black/5 text-[#1c1c1e]"
                          }`}
                        >
                          {i + 1}
                        </span>
                        {s}
                      </li>
                    ))}
                  </ol>
                </div>
              </div>
            ) : (
              <div className="space-y-5 pt-2 animate-in fade-in zoom-in-95">
                <div className={`border rounded-2xl p-5 flex items-center gap-4 ${isDark ? "bg-[#EBDCFF]/5 border-[#EBDCFF]/20" : "bg-[#1c1c1e]/5 border-[#1c1c1e]/10"}`}>
                  <span className={`material-symbols-outlined text-[28px] ${c("text-[#1c1c1e]", "text-[#EBDCFF]")}`}>check_circle</span>
                  <div>
                    <p className={`text-[15px] font-bold ${c("text-[#1c1c1e]", "text-white")}`}>WhatsApp Connected!</p>
                    <p className={`text-[13px] font-medium mt-0.5 ${c("text-[#1c1c1e]/60", "text-[#85948b]")}`}>{waNumber || "+92 300 1234567"}</p>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className={`rounded-2xl p-5 text-center border shadow-inner ${isDark ? "bg-[#131317] border-white/[0.04]" : "bg-[#fbfbf2] border-black/5"}`}>
                    <p className={`text-[28px] font-bold ${c("text-[#1c1c1e]", "text-white")}`}>0</p>
                    <p className={`text-[10px] font-bold uppercase tracking-widest mt-1 ${c("text-[#1c1c1e]/50", "text-[#85948b]")}`}>Messages Today</p>
                  </div>
                  <div className={`rounded-2xl p-5 text-center border shadow-inner ${isDark ? "bg-[#131317] border-white/[0.04]" : "bg-[#fbfbf2] border-black/5"}`}>
                    <p className={`text-[28px] font-bold uppercase tracking-widest ${c("text-[#1c1c1e]", "text-[#EBDCFF]")}`}>Live</p>
                    <p className={`text-[10px] font-bold uppercase tracking-widest mt-1 ${c("text-[#1c1c1e]/50", "text-[#85948b]")}`}>Bot Status</p>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* WhatsApp preview phone */}
          <div
            className={`rounded-[2rem] border p-8 flex flex-col items-center shadow-sm ${
              isDark ? "bg-[#1f1f23] border-white/[0.06]" : "bg-white border-black/5"
            }`}
          >
            <h4
              className={`text-[13px] font-bold uppercase tracking-widest mb-6 self-start ${
                c("text-[#1c1c1e]/60", "text-[#85948b]")
              }`}
            >
              WhatsApp Preview
            </h4>
            <div className="w-64 bg-[#0a0a0a] rounded-[2rem] border-8 border-black overflow-hidden shadow-2xl relative">
              {/* Notch */}
              <div className="absolute top-0 left-1/2 -translate-x-1/2 w-24 h-5 bg-black rounded-b-xl z-20"></div>
              {/* Phone top bar */}
              <div className="bg-[#075E54] pt-8 pb-3 px-4 flex items-center gap-3 shadow-md relative z-10">
                <span className="material-symbols-outlined text-white/90 text-[20px]">arrow_back</span>
                <div className="w-9 h-9 rounded-full bg-white/20 flex items-center justify-center text-[16px] border border-white/10">
                  🤖
                </div>
                <div>
                  <p className="text-white text-[14px] font-bold leading-tight">{displayName}</p>
                  <p className="text-white/80 text-[11px] font-medium">online</p>
                </div>
              </div>
              {/* Chat area */}
              <div
                className="min-h-[280px] p-4 flex flex-col justify-end pb-12 relative"
                style={{
                  backgroundColor: "#E5DDD5",
                  backgroundImage: "url('https://i.pinimg.com/originals/8f/ba/cb/8fbacbd464e996966eb1f36dc168fac7.jpg')",
                  backgroundSize: "cover",
                  backgroundPosition: "center",
                  backgroundBlendMode: "overlay"
                }}
              >
                <div className="bg-white rounded-xl rounded-tl-sm px-3 py-2 inline-block max-w-[85%] shadow-[0_1px_1px_rgba(0,0,0,0.1)] self-start">
                  <p className="text-[#303030] text-[13px] leading-relaxed">
                    Salaam! Main {displayName} hoon. Aap ki kya madad kar sakta hoon? 😊
                  </p>
                  <p className="text-[#999] text-[10px] text-right mt-1 ml-4 float-right">10:30</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Web Widget Panel */}
      {deployTab === "web" && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div
            className={`rounded-[2rem] border p-8 space-y-6 shadow-sm ${
              isDark ? "bg-[#1f1f23] border-white/[0.06]" : "bg-white border-black/5"
            }`}
          >
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-black/5 flex items-center justify-center text-[#1c1c1e] dark:bg-[#b0c6ff]/10 dark:text-[#b0c6ff]">
                <span className="material-symbols-outlined text-[24px]">code</span>
              </div>
              <div>
                <h3 className={`text-[16px] font-bold ${c("text-[#1c1c1e]", "text-white")}`}>Web Widget</h3>
                <p className={`text-[12px] font-medium mt-1 ${c("text-[#1c1c1e]/50", "text-[#85948b]")}`}>Embed on any website in under 2 minutes</p>
              </div>
            </div>

            <div className="pt-2">
              <div className="flex items-center justify-between mb-3">
                <label className={`text-[11px] font-bold uppercase tracking-widest ${c("text-[#1c1c1e]/50", "text-[#85948b]")}`}>
                  Embed Code
                </label>
                <button
                  onClick={() => navigator.clipboard?.writeText(widgetCode)}
                  className={`text-[11px] font-bold flex items-center gap-1 transition-colors ${c("text-[#1c1c1e] hover:text-[#1c1c1e]/60", "text-[#EBDCFF] hover:text-white")}`}
                >
                  <span className="material-symbols-outlined text-[14px]">content_copy</span>
                  Copy Code
                </button>
              </div>
              <div className={`border rounded-xl p-5 font-mono text-[12px] leading-relaxed overflow-auto max-h-48 whitespace-pre shadow-inner selection:bg-[#EBDCFF] selection:text-[#1c1c1e] ${
                  isDark ? "bg-[#0e0e12] border-white/[0.06] text-[#EBDCFF]/80" : "bg-[#fbfbf2] border-black/10 text-[#1c1c1e]"
              }`}>
                {widgetCode}
              </div>
            </div>

            <div>
              <label className={`block text-[11px] font-bold uppercase tracking-widest mb-3 ${c("text-[#1c1c1e]/50", "text-[#85948b]")}`}>
                Your Website URL
              </label>
              <input
                type="url"
                className={`w-full rounded-xl px-5 py-4 text-[14px] font-medium outline-none transition-all shadow-inner ${
                    isDark
                      ? "bg-[#131317] border border-white/[0.06] text-white focus:border-[#EBDCFF]/50 placeholder:text-[#3c4a42]"
                      : "bg-[#fbfbf2] border border-black/5 text-[#1c1c1e] focus:border-black/20 focus:bg-white placeholder:text-[#1c1c1e]/30"
                  }`}
                placeholder="https://yourwebsite.com"
              />
            </div>

            <button
               className={`w-full py-4 rounded-xl font-bold text-[14px] transition-colors flex items-center justify-center gap-2 shadow-md active:scale-[0.98] ${
                isDark ? "bg-[#EBDCFF] hover:bg-[#d8bfff] text-[#1c1c1e]" : "bg-[#1c1c1e] hover:bg-black text-[#fbfbf2]"
              }`}
            >
              <span className="material-symbols-outlined text-[18px]">open_in_new</span>
              Preview on My Site
            </button>
          </div>

          {/* Web widget preview */}
          <div
            className={`rounded-[2rem] border p-8 flex flex-col shadow-sm ${
              isDark ? "bg-[#1f1f23] border-white/[0.06]" : "bg-white border-black/5"
            }`}
          >
            <h4
               className={`text-[13px] font-bold uppercase tracking-widest mb-6 ${
                c("text-[#1c1c1e]/60", "text-[#85948b]")
              }`}
            >
              Widget Preview
            </h4>
            <div className={`flex-1 rounded-[1.5rem] border relative overflow-hidden min-h-[320px] shadow-inner ${
                isDark ? "bg-[#131317] border-white/[0.04]" : "bg-[#fbfbf2] border-black/5"
            }`}>
              {/* Fake website bg */}
              <div className="absolute inset-0 p-6 space-y-4 opacity-70">
                <div className={`h-4 rounded-full w-2/3 ${c("bg-black/10", "bg-white/10")}`}></div>
                <div className={`h-3 rounded-full w-1/2 ${c("bg-black/5", "bg-white/5")}`}></div>
                <div className={`h-3 rounded-full w-3/4 ${c("bg-black/5", "bg-white/5")}`}></div>
                <div className={`h-24 rounded-2xl mt-6 ${c("bg-black/5", "bg-white/5")}`}></div>
                <div className={`h-3 rounded-full w-5/6 ${c("bg-black/5", "bg-white/5")}`}></div>
                <div className={`h-3 rounded-full w-1/2 ${c("bg-black/5", "bg-white/5")}`}></div>
              </div>

              {/* Chat widget floating UI */}
              <div className="absolute bottom-6 right-6 flex flex-col items-end gap-4 z-10">
                {/* Chat window */}
                <div
                    className={`rounded-[1.5rem] shadow-[0_12px_40px_rgba(0,0,0,0.15)] w-72 overflow-hidden border ${
                        isDark ? "bg-[#1f1f23] border-white/10" : "bg-white border-black/10"
                    }`}
                >
                  <div className={`px-5 py-4 flex items-center gap-3 ${isDark ? "bg-[#EBDCFF]" : "bg-[#1c1c1e]"}`}>
                    <div className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center text-[14px] border border-white/20">
                      🤖
                    </div>
                    <p className={`text-[14px] font-bold ${isDark ? "text-[#1c1c1e]" : "text-[#fbfbf2]"}`}>{displayName}</p>
                  </div>
                  <div className={`p-4 space-y-3 ${isDark ? "bg-[#131317]" : "bg-[#fbfbf2]"}`}>
                    <div className={`rounded-2xl rounded-tl-sm p-4 shadow-sm border ${
                        isDark ? "bg-[#1f1f23] border-white/[0.04]" : "bg-white border-black/5"
                    }`}>
                      <p className={`text-[12px] font-medium leading-relaxed ${isDark ? "text-white" : "text-[#1c1c1e]"}`}>
                        Hi! 👋 How can I help you today?
                      </p>
                    </div>
                    <div className={`flex gap-2 p-1.5 rounded-xl border ${
                        isDark ? "bg-[#1f1f23] border-white/[0.06]" : "bg-white border-black/10"
                    }`}>
                      <input
                        readOnly
                        className={`flex-1 bg-transparent px-3 py-2 text-[12px] font-medium outline-none ${
                            isDark ? "text-[#55635a]" : "placeholder:text-[#1c1c1e]/40"
                        }`}
                        placeholder="Type a message..."
                      />
                      <div className={`w-9 h-9 rounded-lg flex items-center justify-center shadow-sm ${
                          isDark ? "bg-[#EBDCFF]" : "bg-[#1c1c1e]"
                      }`}>
                        <span className={`material-symbols-outlined text-[16px] translate-x-[1px] ${isDark ? "text-[#1c1c1e]" : "text-[#fbfbf2]"}`}>send</span>
                      </div>
                    </div>
                  </div>
                </div>
                {/* Chat button launcher */}
                <div className={`w-14 h-14 rounded-full flex items-center justify-center shadow-[0_8px_30px_rgba(0,0,0,0.15)] cursor-pointer hover:scale-110 transition-transform ${
                     isDark ? "bg-[#EBDCFF]" : "bg-[#1c1c1e]"
                }`}>
                  <span className={`material-symbols-outlined text-[24px] ${isDark ? "text-[#1c1c1e]" : "text-[#fbfbf2]"}`}>chat</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Final publish row */}
      <div
        className={`rounded-[2rem] border p-6 lg:p-8 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6 shadow-sm mt-4 bg-gradient-to-r ${
          isDark
            ? "from-[#1f1f23] to-[#EBDCFF]/5 border-white/[0.06]"
            : "from-white to-black/5 border-black/5"
        }`}
      >
        <div>
          <h3
             className={`text-[20px] font-serif font-bold flex items-center gap-2 ${c("text-[#1c1c1e]", "text-white")}`}
             style={{ fontFamily: "'Playfair Display', serif" }}
          >
            <span className="text-2xl">🎉</span> All done! Publish your bot.
          </h3>
          <p className={`text-[14px] font-medium mt-1.5 ${c("text-[#1c1c1e]/60", "text-[#85948b]")}`}>
            Your bot will go live instantly. You can pause or edit it anytime from the dashboard.
          </p>
        </div>
        <button
           className={`flex-shrink-0 px-8 py-4 rounded-xl font-bold text-[14px] transition-all flex items-center gap-2 shadow-md active:scale-[0.98] ${
            isDark ? "bg-[#EBDCFF] hover:bg-[#d8bfff] text-[#1c1c1e]" : "bg-[#1c1c1e] hover:bg-black text-[#fbfbf2]"
          }`}
        >
          <span className="material-symbols-outlined text-[20px]">rocket_launch</span>
          Publish Bot
        </button>
      </div>
    </div>
  );
}

/* ─────────────────────────────────────────────────────────────────────────────
   MAIN COMPONENT
───────────────────────────────────────────────────────────────────────────── */
export default function BotBuilder() {
  const { isDark } = useTheme();
  const c = (light: string, dark: string) => (isDark ? dark : light);
  
  const [step, setStep] = useState(1);
  const [selectedPersona, setSelectedPersona] = useState("saraa");
  const [botName, setBotName] = useState("");
  const [language, setLanguage] = useState("urdu");

  // Custom persona state
  const [customName, setCustomName] = useState("");
  const [customRole, setCustomRole] = useState("");
  const [customTone, setCustomTone] = useState("friendly");
  const [customGreeting, setCustomGreeting] = useState("");

  // Knowledge base
  const [knowledgeItems, setKnowledgeItems] = useState<KnowledgeItem[]>([]);

  const persona = BUILT_IN_PERSONAS.find((p) => p.id === selectedPersona);

  const canProceed = () => {
    if (step === 1) return botName.trim().length > 0;
    return true;
  };

  return (
    <div
      className={`min-h-screen flex font-sans selection:bg-[#EBDCFF] selection:text-[#1c1c1e] transition-colors duration-300 ${
        isDark ? "bg-[#131317] text-[#e4e1e7]" : "bg-[#fbfbf2] text-[#1c1c1e]"
      }`}
    >
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0 overflow-hidden relative">
        <div
          className={`absolute top-0 right-0 w-[600px] h-[600px] rounded-full blur-3xl pointer-events-none transition-opacity duration-500 ${
            isDark
              ? "bg-[#EBDCFF] opacity-5 mix-blend-screen"
              : "bg-[#EBDCFF] opacity-10 mix-blend-multiply"
          }`}
        ></div>

        {/* Custom top bar with stepper */}
        <header
          className={`h-20 flex items-center justify-between px-8 border-b z-20 sticky top-0 backdrop-blur-md transition-colors ${
            isDark ? "bg-[#131317]/90 border-white/[0.06]" : "bg-[#fbfbf2]/90 border-black/5"
          }`}
        >
          <StepBar current={step} onStep={setStep} />
          <div className="flex items-center gap-4 ml-4 flex-shrink-0">
             <button
              className={`px-5 py-2.5 rounded-xl border font-bold text-[13px] transition-all shadow-sm ${
                isDark
                  ? "border-white/[0.06] text-white/70 hover:text-white hover:bg-white/[0.04]"
                  : "border-black/10 text-[#1c1c1e]/70 hover:text-[#1c1c1e] hover:bg-white"
              }`}
            >
              Save Draft
            </button>
          </div>
        </header>

        {/* Step content */}
        <main className="flex-1 overflow-y-auto z-10">
          <div className="max-w-6xl mx-auto px-8 lg:px-12 py-10">
            {/* Step header */}
            <div className="mb-10 animate-in slide-in-from-top-4 duration-500">
              <div className="flex items-center gap-2.5 mb-3">
                <span className={`text-[11px] font-bold tracking-[0.2em] uppercase px-3 py-1 rounded-full border shadow-sm ${c("border-black/5 bg-white text-[#1c1c1e]", "bg-white/5 border-white/10 text-[#EBDCFF]")}`}>
                  Step {step} of {STEPS.length}
                </span>
                <span className={`text-[11px] font-bold uppercase tracking-widest ${c("text-[#1c1c1e]/40", "text-white/40")}`}>
                  {STEPS[step - 1].label}
                </span>
              </div>
              <h1
                 className={`text-[2.5rem] lg:text-[3.5rem] font-bold tracking-tight leading-none mb-4 ${
                  c("text-[#1c1c1e]", "text-white")
                }`}
                style={{ fontFamily: "'Playfair Display', serif" }}
              >
                {step === 1 && "Give Your Bot a Personality"}
                {step === 2 && "Train Your Bot with Knowledge"}
                {step === 3 && "Test Before You Go Live"}
                {step === 4 && "Deploy Your Bot"}
              </h1>
              <p className={`text-lg max-w-2xl font-medium ${c("text-[#1c1c1e]/60", "text-white/50")}`}>
                {step === 1 &&
                  "Choose or customize a persona that represents your brand. A well-defined personality makes your bot feel human, not robotic."}
                {step === 2 &&
                  "Upload documents, add your website, contact info, guidelines — everything your bot needs to answer accurately and confidently."}
                {step === 3 &&
                  "Test your fully-trained bot in real-time. Chat with it and see how it responds before going live."}
                {step === 4 &&
                  "Deploy your bot to WhatsApp or embed it on your website. Goes live instantly with zero downtime."}
              </p>
            </div>

            {/* Step content */}
            {step === 1 && (
              <Step1Persona
                selected={selectedPersona}
                onSelect={setSelectedPersona}
                customName={customName}
                setCustomName={setCustomName}
                customRole={customRole}
                setCustomRole={setCustomRole}
                customTone={customTone}
                setCustomTone={setCustomTone}
                customGreeting={customGreeting}
                setCustomGreeting={setCustomGreeting}
                botName={botName}
                setBotName={setBotName}
                language={language}
                setLanguage={setLanguage}
              />
            )}
            {step === 2 && (
              <Step2Knowledge
                items={knowledgeItems}
                setItems={setKnowledgeItems}
              />
            )}
            {step === 3 && <Step3Test persona={persona} botName={botName} />}
            {step === 4 && <Step4Deploy botName={botName} />}

            {/* Navigation buttons */}
            <div className={`flex items-center justify-between mt-12 pt-8 border-t ${c("border-black/5", "border-white/[0.06]")}`}>
              <button
                onClick={() => setStep((s) => Math.max(1, s - 1))}
                className={`flex items-center gap-2 px-6 py-3.5 rounded-xl border font-bold text-[14px] transition-all shadow-sm ${
                  step === 1 ? "opacity-0 pointer-events-none" : ""
                } ${
                  isDark
                    ? "border-white/[0.06] text-white/70 hover:text-white hover:bg-white/[0.04]"
                    : "border-black/10 text-[#1c1c1e]/70 hover:text-[#1c1c1e] hover:bg-white"
                }`}
              >
                <span className="material-symbols-outlined text-[18px]">arrow_back</span>
                Back
              </button>

              <div className="flex items-center gap-3">
                {STEPS.map((s) => (
                  <div
                    key={s.num}
                    className={`h-2 rounded-full transition-all duration-500 ${
                      s.num === step
                        ? c("w-8 bg-[#1c1c1e] shadow-sm", "w-8 bg-[#EBDCFF] shadow-glow")
                        : s.num < step
                        ? c("w-4 bg-[#1c1c1e]/30", "w-4 bg-[#EBDCFF]/40")
                        : c("w-3 bg-black/10", "w-3 bg-[#2a2a2e]")
                    }`}
                  ></div>
                ))}
              </div>

              {step < 4 ? (
                <button
                  onClick={() => setStep((s) => Math.min(4, s + 1))}
                  disabled={step === 1 && !canProceed()}
                  className={`flex items-center gap-2 px-8 py-3.5 rounded-xl font-bold text-[14px] transition-all shadow-md disabled:opacity-40 disabled:cursor-not-allowed ${
                    isDark
                      ? "bg-[#EBDCFF] hover:bg-[#d8bfff] text-[#1c1c1e]"
                      : "bg-[#1c1c1e] hover:bg-black text-[#fbfbf2]"
                  }`}
                >
                  {step === 2 && knowledgeItems.length === 0 ? "Skip & Continue" : "Continue"}
                  <span className="material-symbols-outlined text-[18px]">arrow_forward</span>
                </button>
              ) : (
                <button
                   className={`flex items-center gap-2 px-8 py-3.5 rounded-xl font-bold text-[14px] transition-all shadow-md active:scale-[0.98] ${
                    isDark
                      ? "bg-[#EBDCFF] hover:bg-[#d8bfff] text-[#1c1c1e]"
                      : "bg-[#1c1c1e] hover:bg-black text-[#fbfbf2]"
                  }`}
                >
                  <span className="material-symbols-outlined text-[18px]">rocket_launch</span>
                  Publish Bot
                </button>
              )}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
