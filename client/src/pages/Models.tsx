import { useState, useEffect, useCallback, useMemo } from "react";
import { useTheme } from "../contexts/ThemeContext";
import { useLayoutConfig } from "../contexts/LayoutContext";
import { toast } from "sonner";
import { api } from "../lib/api";
import { cn } from "../lib/utils";
import { RoutingFabric } from "./Models/components/RoutingFabric";
import { ActiveModelsTable } from "./Models/components/ActiveModelsTable";
import { ConfigureModal } from "./Models/components/ConfigureModal";

interface AIProvider { id: string; name: string; }
interface AIModelConfig {
  id: string; provider_id: string; model_name: string;
  provider: { id: string; name: string };
  routing_rules: Array<{ intent: string; model_override?: string | null }>;
}

export default function Models() {
  const { isDark } = useTheme();
  const [loading, setLoading] = useState(true);
  const [providers, setProviders] = useState<AIProvider[]>([]);
  const [configs, setConfigs] = useState<AIModelConfig[]>([]);

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingConfigId, setEditingConfigId] = useState<string | null>(null);
  const [selectedProviderId, setSelectedProviderId] = useState("");
  const [modalRules, setModalRules] = useState<Array<{ intent: string; model_target: string }>>([]);
  const [availableModels, setAvailableModels] = useState<Array<{ id: string; name: string; models: string[] }>>([]);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [providersData, configsData, modelsData] = await Promise.all([
        api.getProviders(),
        api.getConfigs(),
        api.getAvailableModels().catch(() => []),
      ]);
      setProviders(providersData);
      setConfigs(configsData);
      setAvailableModels(modelsData);
    } catch (err: any) {
      toast.error(err.message || "Error fetching models data");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const getOpenRouterProvider = () => {
    return providers.find((p) => p.name.toLowerCase().includes("openrouter")) || providers[0];
  };

  const handleOpenConfigureModal = () => {
    const provider = getOpenRouterProvider();
    if (!provider) {
      toast.error("No AI providers available in the system.");
      return;
    }

    setSelectedProviderId(provider.id);
    const existingConfig = configs.find((c) => c.provider_id === provider.id);

    if (existingConfig) {
      setEditingConfigId(existingConfig.id);
      setModalRules(
        existingConfig.routing_rules.map((r) => ({
          intent: r.intent,
          model_target: r.model_override || existingConfig.model_name,
        }))
      );
    } else {
      setEditingConfigId(null);
      setModalRules([{ intent: "General Inquiries", model_target: "openai/gpt-4o-mini" }]);
    }
    setIsModalOpen(true);
  };

  const activeRules = useMemo(() =>
    configs.flatMap((config) =>
      config.routing_rules.map((rule) => ({
        label: rule.intent,
        model: rule.model_override || config.model_name,
        provider: config.provider.name,
        icon: rule.intent.toLowerCase().includes("image")
          ? "image_search"
          : rule.intent.toLowerCase().includes("complex") || rule.intent.toLowerCase().includes("reason")
          ? "psychology_alt"
          : rule.intent.toLowerCase().includes("code")
          ? "code"
          : "speed",
      }))
    ),
    [configs]
  );

  const handleCloseModal = useCallback(() => setIsModalOpen(false), []);
  const handleSaved = useCallback(() => { fetchData(); }, [fetchData]);

  useLayoutConfig({
    title: "Chatbot Models",
    actions: (
      <button
        onClick={handleOpenConfigureModal}
        className={cn("px-4 py-2 rounded-xl border transition-[color,background-color,border-color,box-shadow] duration-200 text-[13px] font-bold flex items-center gap-1.5 shadow-sm focus-visible:ring-2 outline-none cursor-pointer", isDark ? "bg-[#EBDCFF]/10 border-[#EBDCFF]/20 text-[#EBDCFF] hover:bg-[#EBDCFF]/20 focus-visible:ring-[#EBDCFF]/20" : "bg-[#1c1c1e] border-[#1c1c1e] text-[#F5F5F7] hover:bg-black focus-visible:ring-black/20")}
      >
        <span className="material-symbols-outlined text-[18px]">smart_toy</span>
        <span className="hidden sm:inline">Configure Models</span>
      </button>
    ),
  });

  return (
    <>
      <main className="flex-1 overflow-y-auto p-4 sm:p-8 lg:p-12 z-10">
        <div className="mb-12">
          <span className={cn("text-[11px] font-bold tracking-[0.2em] uppercase mb-3 block", isDark ? "text-[#EBDCFF]" : "text-[#1c1c1e]/40")}>
            Configuration
          </span>
          <h1 className={cn("text-[2.5rem] lg:text-[3.5rem] font-bold tracking-tight leading-none mb-3", isDark ? "text-white" : "text-[#1c1c1e]")} style={{ fontFamily: "'Playfair Display', serif" }}>
            Chatbot Brain
          </h1>
          <p className={cn("text-lg max-w-2xl font-medium", isDark ? "text-white/50" : "text-[#1c1c1e]/60")}>
            Choose which AI models will power your chatbot. Map different user intents to specialized models for the best performance.
          </p>
        </div>

        <RoutingFabric loading={loading} activeRules={activeRules} />

        <ActiveModelsTable loading={loading} activeRules={activeRules} onEdit={handleOpenConfigureModal} />
      </main>

      <ConfigureModal
        open={isModalOpen}
        onClose={handleCloseModal}
        onSaved={handleSaved}
        editingConfigId={editingConfigId}
        initialRules={modalRules}
        initialProviderId={selectedProviderId}
        availableModels={availableModels}
      />
    </>
  );
}
