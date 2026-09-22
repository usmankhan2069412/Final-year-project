import { useEffect, useState, useRef } from "react";
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
import PageLoader from "../../components/PageLoader";

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
  const [hasVisitedStep3, setHasVisitedStep3] = useState(false);
  const knowledgeLoadedRef = useRef(false);
  const [isLoading, setIsLoading] = useState<boolean>(() => {
    const params = new URLSearchParams(window.location.search);
    return Boolean(params.get("id"));
  });

  useEffect(() => {
    if (step === 3 && !hasVisitedStep3) {
      setHasVisitedStep3(true);
    }
  }, [step, hasVisitedStep3]);

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

  const [savedValues, setSavedValues] = useState({
    botName: "",
    customRole: "",
    customTone: "friendly",
    customGreeting: "",
    customFallback: "",
    customDescription: "",
  });

  const hasUnsavedChanges =
    botName !== savedValues.botName ||
    customRole !== savedValues.customRole ||
    customTone !== savedValues.customTone ||
    customGreeting !== savedValues.customGreeting ||
    customFallback !== savedValues.customFallback ||
    customDescription !== savedValues.customDescription;

  // Knowledge base
  const [knowledgeItems, setKnowledgeItems] = useState<KnowledgeItem[]>([]);

  const toKnowledgeItem = (source: KnowledgeSourceResponse): KnowledgeItem => ({
    id: source.id,
    type: source.source_type,
    label: source.label,
    value: source.source_type === "text" && source.value.length > 80 ? `${source.value.slice(0, 80)}...` : source.value,
    status: source.status,
    error_message: source.error_message,
    is_searchable: source.is_searchable,
    pages_crawled: source.pages_crawled,
    total_content_chars: source.total_content_chars,
    crawl_duration_secs: source.crawl_duration_secs,
  });

  // Load existing chatbot if ID is provided in query params
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const id = params.get("id");
    if (id) {
      const loadChatbot = async () => {
        setIsLoading(true);
        try {
          const [bot, sources] = await Promise.all([
            api.getChatbot(id),
            api.listKnowledge(id),
          ]);
          setChatbotId(bot.id);
          const newBotName = bot.name || "";
          setBotName(newBotName);
          setPersonaId(bot.persona_id);

          let newCustomGreeting = "";
          let newCustomFallback = "";
          let newCustomDescription = "";
          let newCustomRole = "";
          let newCustomTone = "friendly";

          if (bot.persona) {
            newCustomGreeting = bot.persona.greeting || "";
            newCustomFallback = bot.persona.fallback || "";
            
            const fullDesc = bot.persona.description || "";
            if (fullDesc.startsWith("Role: ")) {
              const nlIndex = fullDesc.indexOf("\n\n");
              if (nlIndex !== -1) {
                newCustomRole = fullDesc.substring(6, nlIndex);
                newCustomDescription = fullDesc.substring(nlIndex + 2);
              } else {
                newCustomRole = fullDesc.substring(6);
                newCustomDescription = "";
              }
            } else {
              newCustomRole = "";
              newCustomDescription = fullDesc;
            }

            newCustomTone = bot.persona.traits?.[0]?.trait_name || "friendly";

            setCustomGreeting(newCustomGreeting);
            setCustomFallback(newCustomFallback);
            setCustomDescription(newCustomDescription);
            setCustomRole(newCustomRole);
            setCustomTone(newCustomTone);
          }
          setSaveStatus("saved");

          setSavedValues({
            botName: newBotName,
            customRole: newCustomRole,
            customTone: newCustomTone,
            customGreeting: newCustomGreeting,
            customFallback: newCustomFallback,
            customDescription: newCustomDescription,
          });

          // Set pre-loaded knowledge items
          setKnowledgeItems(sources.map(toKnowledgeItem));
          knowledgeLoadedRef.current = true;
        } catch (err: any) {
          toast.error(err?.message || "Failed to load chatbot details");
        } finally {
          setIsLoading(false);
        }
      };
      loadChatbot();
    }
  }, []);

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
    if (isLoading) return false;
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
      let combinedDescription = null;
      if (customRole.trim() && customDescription.trim()) {
        combinedDescription = `Role: ${customRole.trim()}\n\n${customDescription.trim()}`;
      } else if (customDescription.trim()) {
        combinedDescription = customDescription.trim();
      } else if (customRole.trim()) {
        combinedDescription = `Role: ${customRole.trim()}`;
      }

      const personaPayload = {
        name: botName.trim(),
        language: "multilingual",
        greeting: customGreeting.trim() || null,
        fallback: customFallback.trim() || null,
        description: combinedDescription,
        traits: [customTone],
      };

      let savedPersonaId = personaId;
      let savedChatbotId = chatbotId;

      if (personaId && chatbotId) {
        // Parallel execution for existing agent update (saves ~50% network latency)
        const chatbotPayload = {
          persona_id: personaId,
          name: botName.trim(),
          description: combinedDescription,
          status: "draft" as const,
        };

        const [savedPersona, savedChatbot] = await Promise.all([
          api.updatePersona(personaId, personaPayload),
          api.updateChatbot(chatbotId, chatbotPayload),
        ]);

        savedPersonaId = savedPersona.id;
        savedChatbotId = savedChatbot.id;
      } else {
        // Initial creation flow: create persona first, then link to new chatbot
        const savedPersona = personaId
          ? await api.updatePersona(personaId, personaPayload)
          : await api.createPersona(personaPayload);

        savedPersonaId = savedPersona.id;

        const chatbotPayload = {
          persona_id: savedPersona.id,
          name: botName.trim(),
          description: combinedDescription,
          status: "draft" as const,
        };

        const savedChatbot = chatbotId
          ? await api.updateChatbot(chatbotId, chatbotPayload)
          : await api.createChatbot(chatbotPayload);

        savedChatbotId = savedChatbot.id;
      }

      setPersonaId(savedPersonaId);
      setChatbotId(savedChatbotId);
      setSaveStatus("saved");

      const finalBotName = botName.trim();
      const finalRole = customRole.trim();
      const finalGreeting = customGreeting.trim();
      const finalFallback = customFallback.trim();
      const finalDescription = customDescription.trim();

      setBotName(finalBotName);
      setCustomRole(finalRole);
      setCustomGreeting(finalGreeting);
      setCustomFallback(finalFallback);
      setCustomDescription(finalDescription);

      setSavedValues({
        botName: finalBotName,
        customRole: finalRole,
        customTone: customTone,
        customGreeting: finalGreeting,
        customFallback: finalFallback,
        customDescription: finalDescription,
      });

      return savedChatbotId;
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
    if (!knowledgeLoadedRef.current) {
      refreshKnowledge(chatbotId);
      knowledgeLoadedRef.current = true;
    }
    
    const handleKnowledgeUpdate = (e: Event) => {
      const customEvent = e as CustomEvent<{ chatbotId: string }>;
      if (customEvent.detail.chatbotId === chatbotId) {
        refreshKnowledge(chatbotId);
      }
    };
    
    window.addEventListener("knowledge_update", handleKnowledgeUpdate);
    return () => window.removeEventListener("knowledge_update", handleKnowledgeUpdate);
  }, [chatbotId, step]);

  // Polling fallback: automatically poll while any knowledge item is queued or processing
  useEffect(() => {
    if (!chatbotId || step !== 2) return;
    const hasPending = knowledgeItems.some(
      (item) => item.status === "queued" || item.status === "processing"
    );
    if (!hasPending) return;

    const interval = setInterval(async () => {
      try {
        const sources = await api.listKnowledge(chatbotId);
        setKnowledgeItems(sources.map(toKnowledgeItem));
      } catch {
        // Silently ignore background polling errors
      }
    }, 2500);

    return () => clearInterval(interval);
  }, [chatbotId, step, knowledgeItems]);

  const addKnowledgeItem = async (type: Exclude<SourceType, "file">, value: string, label: string) => {
    const id = await ensureDraft();
    if (!id) return;
    try {
      await api.createKnowledge({ chatbot_id: id, source_type: type, value, label });
      await refreshKnowledge(id);
      toast.success(type === "text" || type === "website" ? "Knowledge source queued for indexing." : "Knowledge source saved.");
    } catch (err: any) {
      toast.error(err?.message || "Failed to add knowledge source");
      throw err;
    }
  };

  const uploadKnowledgeFiles = async (files: FileList | File[]) => {
    const id = await ensureDraft();
    if (!id) return;
    const selected = Array.from(files);
    let successCount = 0;
    for (const file of selected) {
      try {
        await api.uploadKnowledgeFile(id, file);
        successCount++;
      } catch (err: any) {
        toast.error(`${file.name}: ${err?.message || "Upload failed"}`);
      }
    }
    if (successCount > 0) {
      toast.success(`${successCount} file(s) uploaded successfully.`);
    }
    await refreshKnowledge(id);
  };

  const removeKnowledgeItem = async (sourceId: string) => {
    try {
      await api.deleteKnowledge(sourceId);
      setKnowledgeItems((prev) => prev.filter((item) => item.id !== sourceId));
      toast.success("Knowledge source removed successfully.");
    } catch (err: any) {
      toast.error(err?.message || "Failed to remove source");
    }
  };

  const goNext = async () => {
    if (step === 1) {
      if (!chatbotId || hasUnsavedChanges) {
        const savedId = await saveDraft();
        if (!savedId) return;
      }
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
            <StepBar current={step} onStep={(n) => !isLoading && setStep(n)} />
          </div>
          <div className="flex items-center gap-4 ml-4 flex-shrink-0">
            <button
              onClick={saveDraft}
              disabled={isLoading || saveStatus === "saving"}
              className={`px-4 sm:px-5 py-2.5 rounded-xl border font-bold text-[13px] transition-all shadow-sm ${
                isDark
                  ? "border-white/[0.06] text-white/70 hover:text-white hover:bg-white/[0.04]"
                  : "border-black/10 text-[#1c1c1e]/70 hover:text-[#1c1c1e] hover:bg-white"
              } ${isLoading ? "opacity-50 cursor-not-allowed" : ""}`}
            >
              {isLoading ? "Loading..." : saveStatus === "saving" ? "Saving..." : saveStatus === "saved" ? "Saved" : "Save Draft"}
            </button>
          </div>
        </header>

        {/* Step content */}
        <main className="flex-1 overflow-y-auto z-10">
          {isLoading ? (
            <PageLoader page="builder" contentOnly />
          ) : (
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
              {(hasVisitedStep3 || step === 3) && (
                <div className={step === 3 ? "block" : "hidden"}>
                  <Step3Test persona={persona} botName={botName} chatbotId={chatbotId} onRequireDraft={ensureDraft} />
                </div>
              )}
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
          )}
        </main>
    </div>
  );
}
