import { useEffect, useState } from "react";
import { toast } from "sonner";
import { useTheme } from "../../contexts/ThemeContext";
import { useLayoutConfig, useLayout } from "../../contexts/LayoutContext";
import StepBar from "./components/StepBar";
import Step1Persona from "./components/Step1Persona";
import Step2Knowledge from "./components/Step2Knowledge";
import Step3Test from "./components/Step3Test";
import Step4Deploy from "./components/Step4Deploy";
import { KnowledgeItem } from "./types";
import { api, KnowledgeSourceResponse, SourceType } from "../../lib/api";

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
  const [botName, setBotName] = useState("");
  const [personaId, setPersonaId] = useState<string | null>(null);
  const [chatbotId, setChatbotId] = useState<string | null>(null);
  const [saveStatus, setSaveStatus] = useState<"idle" | "saving" | "saved" | "failed">("idle");
  const [saveError, setSaveError] = useState("");

  // Custom persona state
  const [customRole, setCustomRole] = useState("");
  const [customTone, setCustomTone] = useState("friendly");
  const [customGreeting, setCustomGreeting] = useState("");
  const [customFallback, setCustomFallback] = useState("");
  const [customDescription, setCustomDescription] = useState("");

  // Knowledge base
  const [knowledgeItems, setKnowledgeItems] = useState<KnowledgeItem[]>([]);

  const toKnowledgeItem = (source: KnowledgeSourceResponse): KnowledgeItem => ({
    id: source.id,
    type: source.source_type,
    label: source.label,
    value: source.source_type === "text" && source.value.length > 80 ? `${source.value.slice(0, 80)}...` : source.value,
    status: source.status,
    error_message: source.error_message,
  });

  // Dynamic persona object construction to ensure state integrity
  const persona = {
    id: "custom",
    name: botName || "Aina Bot",
    role: customRole || "AI Assistant",
    emoji: customTone === "formal" ? "🎩" : customTone === "casual" ? "😎" : customTone === "empathetic" ? "💙" : "😊",
    color: isDark ? "#c2ffdf" : "#5c3ea3",
    bgDark: "#c2ffdf15",
    bgLight: "#5c3ea310",
    traits: [customTone],
    greeting: customGreeting || `Assalam-o-Alaikum! Main ${botName || "Aina Bot"} hoon. Aap ki kya madad kar sakti hoon? 😊`,
    fallback: customFallback,
    description: customDescription || "Custom brand persona",
    custom: true,
  };

  const canProceed = () => {
    if (step === 1) return botName.trim().length > 0;
    return true;
  };

  const saveDraft = async () => {
    if (!botName.trim()) {
      toast.error("Bot name is required before saving.");
      return null;
    }

    setSaveStatus("saving");
    setSaveError("");
    try {
      const personaPayload = {
        name: botName.trim(),
        language: "multilingual",
        greeting: customGreeting.trim() || null,
        fallback: customFallback.trim() || null,
        description: customDescription.trim() || customRole.trim() || null,
        traits: [customTone],
      };

      const savedPersona = personaId
        ? await api.updatePersona(personaId, personaPayload)
        : await api.createPersona(personaPayload);

      setPersonaId(savedPersona.id);

      const chatbotPayload = {
        persona_id: savedPersona.id,
        name: botName.trim(),
        description: customDescription.trim() || customRole.trim() || null,
        status: "draft" as const,
      };

      const savedChatbot = chatbotId
        ? await api.updateChatbot(chatbotId, chatbotPayload)
        : await api.createChatbot(chatbotPayload);

      setChatbotId(savedChatbot.id);
      setSaveStatus("saved");
      return savedChatbot.id;
    } catch (err: any) {
      const message = err?.message || "Failed to save draft";
      setSaveStatus("failed");
      setSaveError(message);
      toast.error(message);
      return null;
    }
  };

  const ensureDraft = async () => chatbotId || (await saveDraft());

  const refreshKnowledge = async (id = chatbotId) => {
    if (!id) return;
    try {
      const sources = await api.listKnowledge(id);
      setKnowledgeItems(sources.map(toKnowledgeItem));
    } catch (err: any) {
      toast.error(err?.message || "Failed to refresh knowledge sources");
    }
  };

  useEffect(() => {
    if (!chatbotId || step !== 2) return;
    refreshKnowledge(chatbotId);
    const timer = window.setInterval(() => refreshKnowledge(chatbotId), 3000);
    return () => window.clearInterval(timer);
  }, [chatbotId, step]);

  const addKnowledgeItem = async (type: Exclude<SourceType, "file">, value: string, label: string) => {
    const id = await ensureDraft();
    if (!id) return;
    try {
      await api.createKnowledge({ chatbot_id: id, source_type: type, value, label });
      await refreshKnowledge(id);
      toast.success(type === "text" || type === "website" ? "Knowledge source queued for indexing." : "Knowledge source saved.");
    } catch (err: any) {
      toast.error(err?.message || "Failed to add knowledge source");
    }
  };

  const uploadKnowledgeFiles = async (files: FileList | File[]) => {
    const id = await ensureDraft();
    if (!id) return;
    const selected = Array.from(files);
    for (const file of selected) {
      try {
        await api.uploadKnowledgeFile(id, file);
      } catch (err: any) {
        toast.error(`${file.name}: ${err?.message || "Upload failed"}`);
      }
    }
    await refreshKnowledge(id);
  };

  const removeKnowledgeItem = async (sourceId: string) => {
    try {
      await api.deleteKnowledge(sourceId);
      setKnowledgeItems((prev) => prev.filter((item) => item.id !== sourceId));
    } catch (err: any) {
      toast.error(err?.message || "Failed to remove source");
    }
  };

  const goNext = async () => {
    if (step === 1) {
      const savedId = await saveDraft();
      if (!savedId) return;
    }
    setStep((s) => Math.min(4, s + 1));
  };

  return (
    <div className="flex-1 flex flex-col min-w-0 overflow-hidden relative">
        <div
          className={`absolute top-0 right-0 w-[600px] h-[600px] rounded-full blur-3xl pointer-events-none transition-opacity duration-500 ${
            isDark
              ? "bg-[#59eeb4]/5 mix-blend-screen"
              : "bg-[#5c3ea3]/5 mix-blend-multiply"
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
              onClick={saveDraft}
              disabled={saveStatus === "saving"}
              className={`px-4 sm:px-5 py-2.5 rounded-xl border font-bold text-[13px] transition-all shadow-sm ${
                isDark
                  ? "border-white/[0.06] text-white/70 hover:text-white hover:bg-white/[0.04]"
                  : "border-black/10 text-[#1c1c1e]/70 hover:text-[#1c1c1e] hover:bg-white"
              }`}
            >
              {saveStatus === "saving" ? "Saving..." : saveStatus === "saved" ? "Saved" : "Save Draft"}
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
                    "bg-white/5 border-white/10 text-primary"
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
                  "Customize a brand persona that represents your business identity. A well-defined personality builds trust and customer connection."}
                {step === 2 &&
                  "Upload documents, add your website, contact info, guidelines — everything your bot needs to answer accurately and confidently."}
                {step === 3 &&
                  "Test your fully-trained bot in real-time. Chat with it and see how it responds before going live."}
                {step === 4 &&
                  "Deploy your bot to WhatsApp or embed it on your website. Goes live instantly with zero downtime."}
              </p>
              {saveStatus === "failed" && saveError && (
                <p className="mt-3 text-[13px] font-semibold text-red-500">{saveError}</p>
              )}
            </div>

            {/* Step components */}
            {step === 1 && (
              <Step1Persona
                customRole={customRole}
                setCustomRole={setCustomRole}
                customTone={customTone}
                setCustomTone={setCustomTone}
                customGreeting={customGreeting}
                setCustomGreeting={setCustomGreeting}
                customFallback={customFallback}
                setCustomFallback={setCustomFallback}
                customDescription={customDescription}
                setCustomDescription={setCustomDescription}
                botName={botName}
                setBotName={setBotName}
              />
            )}
            {step === 2 && (
              <Step2Knowledge
                items={knowledgeItems}
                onAddItem={addKnowledgeItem}
                onUploadFiles={uploadKnowledgeFiles}
                onRemoveItem={removeKnowledgeItem}
              />
            )}
            {step === 3 && <Step3Test persona={persona} botName={botName} chatbotId={chatbotId} onRequireDraft={ensureDraft} />}
            {step === 4 && <Step4Deploy botName={botName} chatbotId={chatbotId} onRequireDraft={ensureDraft} knowledgeItems={knowledgeItems} />}

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
                        ? "w-6 sm:w-8 bg-primary shadow-sm"
                        : s.num < step
                        ? "w-3 sm:w-4 bg-primary/40"
                        : c("w-2.5 sm:w-3 bg-black/10", "w-2.5 sm:w-3 bg-[#2a2a2e]")
                    }`}
                  ></div>
                ))}
              </div>

              {step < 4 ? (
                <button
                  onClick={goNext}
                  disabled={step === 1 && !canProceed()}
                  className="flex items-center gap-2 px-5 sm:px-8 py-3.5 rounded-xl font-bold text-[14px] transition-all shadow-md disabled:opacity-40 disabled:cursor-not-allowed bg-primary text-primary-foreground hover:opacity-90 active:scale-[0.98]"
                >
                  {step === 2 && knowledgeItems.length === 0 ? "Skip & Continue" : "Continue"}
                  <span className="material-symbols-outlined text-[18px]">arrow_forward</span>
                </button>
              ) : (
                <button
                  className="flex items-center gap-2 px-5 sm:px-8 py-3.5 rounded-xl font-bold text-[14px] transition-all shadow-md active:scale-[0.98] bg-primary text-primary-foreground hover:opacity-90"
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
