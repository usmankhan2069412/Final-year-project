import { useState } from "react";
import { useTheme } from "../../contexts/ThemeContext";
import { useLayoutConfig, useLayout } from "../../contexts/LayoutContext";
import StepBar from "./components/StepBar";
import Step1Persona, { BUILT_IN_PERSONAS } from "./components/Step1Persona";
import Step2Knowledge from "./components/Step2Knowledge";
import Step3Test from "./components/Step3Test";
import Step4Deploy from "./components/Step4Deploy";
import { KnowledgeItem } from "./types";

const STEPS = [
  { num: 1, label: "Persona", icon: "face" },
  { num: 2, label: "Knowledge", icon: "menu_book" },
  { num: 3, label: "Test", icon: "chat_bubble" },
  { num: 4, label: "Deploy", icon: "rocket_launch" },
];

export default function BotBuilder() {
  const { isDark } = useTheme();
  const { setSidebarOpen } = useLayout();
  useLayoutConfig({ hideTopBar: true });
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
          className={`h-16 flex items-center justify-between px-4 sm:px-6 border-b z-20 sticky top-0 backdrop-blur-md transition-colors gap-3 ${
            isDark ? "bg-[#131317]/90 border-white/[0.06]" : "bg-[#F5F5F7]/90 border-black/5"
          }`}
        >
          <div className="flex items-center gap-3 min-w-0">
            {/* Hamburger — mobile only */}
            <button
              onClick={() => setSidebarOpen((v) => !v)}
              aria-label="Open navigation menu"
              className={`md:hidden w-10 h-10 flex-shrink-0 flex items-center justify-center rounded-xl transition-all border ${
                isDark
                  ? "text-white/60 hover:text-white hover:bg-white/5 border-white/10"
                  : "text-[#1c1c1e]/60 hover:text-[#1c1c1e] hover:bg-black/5 border-black/10"
              }`}
            >
              <span className="material-symbols-outlined text-[22px]">menu</span>
            </button>
            <StepBar current={step} onStep={setStep} />
          </div>
          <div className="flex items-center gap-4 ml-4 flex-shrink-0">
            <button
              className={`px-4 sm:px-5 py-2.5 rounded-xl border font-bold text-[13px] transition-all shadow-sm ${
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
          <div className="max-w-6xl mx-auto px-4 sm:px-8 lg:px-12 py-6 sm:py-8">
            {/* Step header */}
            <div className="mb-6 animate-in slide-in-from-top-4 duration-500">
              <div className="flex items-center gap-2.5 mb-3 flex-wrap">
                <span
                  className={`text-[11px] font-bold tracking-[0.2em] uppercase px-3 py-1 rounded-full border shadow-sm ${c(
                    "border-black/5 bg-white text-[#1c1c1e]",
                    "bg-white/5 border-white/10 text-[#EBDCFF]"
                  )}`}
                >
                  Step {step} of {STEPS.length}
                </span>
                <span className={`text-[11px] font-bold uppercase tracking-widest ${c("text-[#1c1c1e]/40", "text-white/40")}`}>
                  {STEPS[step - 1].label}
                </span>
              </div>
              <h1
                className={`text-[1.75rem] sm:text-[2.25rem] lg:text-[2.75rem] font-bold tracking-tight leading-none mb-3 ${c(
                  "text-[#1c1c1e]",
                  "text-white"
                )}`}
                style={{ fontFamily: "'Playfair Display', serif" }}
              >
                {step === 1 && "Give Your Bot a Personality"}
                {step === 2 && "Train Your Bot with Knowledge"}
                {step === 3 && "Test Before You Go Live"}
                {step === 4 && "Deploy Your Bot"}
              </h1>
              <p className={`text-[14px] sm:text-[15px] max-w-2xl font-medium ${c("text-[#1c1c1e]/60", "text-white/50")}`}>
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

            {/* Step components */}
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
            {step === 2 && <Step2Knowledge items={knowledgeItems} setItems={setKnowledgeItems} />}
            {step === 3 && <Step3Test persona={persona} botName={botName} />}
            {step === 4 && <Step4Deploy botName={botName} />}

            {/* Navigation buttons */}
            <div className={`flex items-center justify-between mt-8 pt-6 border-t ${c("border-black/5", "border-white/[0.06]")}`}>
              <button
                onClick={() => setStep((s) => Math.max(1, s - 1))}
                className={`flex items-center gap-2 px-4 sm:px-6 py-3.5 rounded-xl border font-bold text-[14px] transition-all shadow-sm ${
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

              <div className="flex items-center gap-2 sm:gap-3">
                {STEPS.map((s) => (
                  <div
                    key={s.num}
                    className={`h-2 rounded-full transition-all duration-500 ${
                      s.num === step
                        ? c("w-6 sm:w-8 bg-[#1c1c1e] shadow-sm", "w-6 sm:w-8 bg-[#EBDCFF] shadow-glow")
                        : s.num < step
                        ? c("w-3 sm:w-4 bg-[#1c1c1e]/30", "w-3 sm:w-4 bg-[#EBDCFF]/40")
                        : c("w-2.5 sm:w-3 bg-black/10", "w-2.5 sm:w-3 bg-[#2a2a2e]")
                    }`}
                  ></div>
                ))}
              </div>

              {step < 4 ? (
                <button
                  onClick={() => setStep((s) => Math.min(4, s + 1))}
                  disabled={step === 1 && !canProceed()}
                  className={`flex items-center gap-2 px-5 sm:px-8 py-3.5 rounded-xl font-bold text-[14px] transition-all shadow-md disabled:opacity-40 disabled:cursor-not-allowed ${
                    isDark
                      ? "bg-[#EBDCFF] hover:bg-[#d8bfff] text-[#1c1c1e]"
                      : "bg-[#1c1c1e] hover:bg-black text-[#F5F5F7]"
                  }`}
                >
                  {step === 2 && knowledgeItems.length === 0 ? "Skip & Continue" : "Continue"}
                  <span className="material-symbols-outlined text-[18px]">arrow_forward</span>
                </button>
              ) : (
                <button
                  className={`flex items-center gap-2 px-5 sm:px-8 py-3.5 rounded-xl font-bold text-[14px] transition-all shadow-md active:scale-[0.98] ${
                    isDark
                      ? "bg-[#EBDCFF] hover:bg-[#d8bfff] text-[#1c1c1e]"
                      : "bg-[#1c1c1e] hover:bg-black text-[#F5F5F7]"
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
  );
}
