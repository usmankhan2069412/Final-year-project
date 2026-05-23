import { useState, useEffect } from "react";
import { useTheme } from "../contexts/ThemeContext";
import Sidebar from "../components/Sidebar";
import TopBar from "../components/TopBar";
import { toast } from "sonner";

interface AIProvider {
  id: string;
  name: string;
}

interface RoutingRule {
  id?: string;
  config_id?: string;
  intent: string;
  model_target: string;
}

interface AIModelConfig {
  id: string;
  org_id: string;
  provider_id: string;
  secret_ref: string | null;
  provider: AIProvider;
  routing_rules: RoutingRule[];
}

const PROVIDER_SUGGESTED_MODELS: Record<string, string[]> = {
  openai: ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
  anthropic: [
    "claude-3-5-sonnet-20240620",
    "claude-3-opus-20240229",
    "claude-3-haiku-20240307",
  ],
  gemini: [
    "gemini-1.5-pro-latest",
    "gemini-1.5-flash-latest",
    "gemini-1.0-pro",
  ],
  google: [
    "gemini-1.5-pro-latest",
    "gemini-1.5-flash-latest",
    "gemini-1.0-pro",
  ],
};

const POPULAR_INTENTS = [
  "General Inquiries",
  "Complex Problems",
  "Image Analysis",
  "Code Assistance",
];

export default function Models() {
  const { isDark } = useTheme();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [loading, setLoading] = useState(true);

  // Data states
  const [providers, setProviders] = useState<AIProvider[]>([]);
  const [configs, setConfigs] = useState<AIModelConfig[]>([]);

  // Modal states
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingConfig, setEditingConfig] = useState<AIModelConfig | null>(null);
  const [selectedProviderId, setSelectedProviderId] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [secretRef, setSecretRef] = useState("");
  const [routingRules, setRoutingRules] = useState<RoutingRule[]>([]);
  const [submitting, setSubmitting] = useState(false);

  // Router settings mockup state (local state switches/sliders)
  const [latencyTolerance, setLatencyTolerance] = useState(1200);
  const [costOptimization, setCostOptimization] = useState(80);
  const [autoFailover, setAutoFailover] = useState(true);
  const [responseCaching, setResponseCaching] = useState(false);

  const c = (light: string, dark: string) => (isDark ? dark : light);

  const getProviderLogoInfo = (name: string) => {
    const norm = name.toLowerCase();
    if (norm.includes("openai")) {
      return { logo: "○", bg: isDark ? "#fff" : "#1c1c1e", color: isDark ? "#000" : "#fff" };
    }
    if (norm.includes("anthropic")) {
      return { logo: "A", bg: "#D97757", color: "#fff" };
    }
    if (norm.includes("gemini") || norm.includes("google")) {
      return { logo: "G", bg: "#4285F4", color: "#fff" };
    }
    return { logo: name.charAt(0).toUpperCase(), bg: "#8a5cf5", color: "#fff" };
  };

  const getSuggestedModels = (providerId: string) => {
    const provider = providers.find((p) => p.id === providerId);
    if (!provider) return [];
    const name = provider.name.toLowerCase();
    for (const key in PROVIDER_SUGGESTED_MODELS) {
      if (name.includes(key)) {
        return PROVIDER_SUGGESTED_MODELS[key];
      }
    }
    return ["gpt-4o", "claude-3-5-sonnet-20240620", "gemini-1.5-pro-latest"];
  };

  const getHeaders = () => {
    const token = localStorage.getItem("token");
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
    return headers;
  };

  const fetchData = async () => {
    setLoading(true);
    try {
      const headers = getHeaders();
      
      // Fetch providers
      const providersRes = await fetch("http://localhost:8000/api/v1/models/providers", { headers });
      if (!providersRes.ok) throw new Error("Failed to load AI providers");
      const providersData = await providersRes.json();
      setProviders(providersData);

      // Fetch configs
      const configsRes = await fetch("http://localhost:8000/api/v1/models/configs", { headers });
      if (!configsRes.ok) throw new Error("Failed to load model configurations");
      const configsData = await configsRes.json();
      setConfigs(configsData);
    } catch (err: any) {
      console.error(err);
      toast.error(err.message || "Error fetching models data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleOpenAddModal = () => {
    // Filter to show only non-configured providers
    const configuredProviderIds = configs.map((c) => c.provider_id);
    const unconfigured = providers.filter((p) => !configuredProviderIds.includes(p.id));

    if (unconfigured.length === 0) {
      toast.info("All available providers have already been configured. Edit existing configurations to adjust rules.");
      return;
    }

    setEditingConfig(null);
    setSelectedProviderId(unconfigured[0].id);
    setApiKey("");
    setSecretRef("");
    // Add one default rule
    setRoutingRules([{ intent: "General Inquiries", model_target: getSuggestedModels(unconfigured[0].id)[0] || "" }]);
    setIsModalOpen(true);
  };

  const handleOpenEditModal = (config: AIModelConfig) => {
    setEditingConfig(config);
    setSelectedProviderId(config.provider_id);
    setApiKey(""); // Keep blank to indicate no change unless typed
    setSecretRef(config.secret_ref || "");
    setRoutingRules(config.routing_rules.map((r) => ({ intent: r.intent, model_target: r.model_target })));
    setIsModalOpen(true);
  };

  const handleAddRule = () => {
    const suggested = getSuggestedModels(selectedProviderId);
    setRoutingRules([...routingRules, { intent: "General Inquiries", model_target: suggested[0] || "" }]);
  };

  const handleRemoveRule = (index: number) => {
    const newRules = [...routingRules];
    newRules.splice(index, 1);
    setRoutingRules(newRules);
  };

  const handleRuleChange = (index: number, field: keyof RoutingRule, value: string) => {
    const newRules = [...routingRules];
    newRules[index] = { ...newRules[index], [field]: value };
    setRoutingRules(newRules);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedProviderId) {
      toast.error("Please select a provider");
      return;
    }

    // API key is required when creating a configuration
    if (!editingConfig && !apiKey.trim()) {
      toast.error("API Key is required to configure a new provider");
      return;
    }

    // Validate routing rules
    for (let i = 0; i < routingRules.length; i++) {
      if (!routingRules[i].intent.trim() || !routingRules[i].model_target.trim()) {
        toast.error(`Please complete both fields for Routing Rule #${i + 1}`);
        return;
      }
    }

    setSubmitting(true);
    try {
      const headers = getHeaders();
      const payload: any = {
        provider_id: selectedProviderId,
        secret_ref: secretRef.trim() || null,
        routing_rules: routingRules.map((r) => ({ intent: r.intent.trim(), model_target: r.model_target.trim() })),
      };

      if (apiKey.trim()) {
        payload.api_key = apiKey.trim();
      }

      let res;
      if (editingConfig) {
        // Edit config
        res = await fetch(`http://localhost:8000/api/v1/models/configs/${editingConfig.id}`, {
          method: "PATCH",
          headers,
          body: JSON.stringify(payload),
        });
      } else {
        // Create config
        res = await fetch("http://localhost:8000/api/v1/models/configs", {
          method: "POST",
          headers,
          body: JSON.stringify(payload),
        });
      }

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Failed to save configuration");
      }

      toast.success(editingConfig ? "Configuration updated successfully!" : "Provider configured successfully!");
      setIsModalOpen(false);
      fetchData();
    } catch (err: any) {
      console.error(err);
      toast.error(err.message || "Error saving configuration");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteConfig = async (configId: string, providerName: string) => {
    if (!confirm(`Are you sure you want to disconnect ${providerName}? This will delete all its routing rules.`)) {
      return;
    }

    try {
      const headers = getHeaders();
      const res = await fetch(`http://localhost:8000/api/v1/models/configs/${configId}`, {
        method: "DELETE",
        headers,
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Failed to delete configuration");
      }

      toast.success(`Disconnected ${providerName} successfully.`);
      fetchData();
    } catch (err: any) {
      console.error(err);
      toast.error(err.message || "Error deleting configuration");
    }
  };

  // Compile active rules for the Routing Fabric visualizer
  const activeRules = configs.flatMap((config) =>
    config.routing_rules.map((rule) => ({
      label: rule.intent,
      model: rule.model_target,
      provider: config.provider.name,
      icon: rule.intent.toLowerCase().includes("image")
        ? "image_search"
        : rule.intent.toLowerCase().includes("complex") || rule.intent.toLowerCase().includes("reason")
        ? "psychology_alt"
        : rule.intent.toLowerCase().includes("code")
        ? "code"
        : "speed",
    }))
  );

  return (
    <div
      className={`min-h-screen flex font-sans selection:bg-[#EBDCFF] selection:text-[#1c1c1e] transition-colors duration-300 ${
        isDark ? "bg-[#131317] text-[#e4e1e7]" : "bg-[#F5F5F7] text-[#1c1c1e]"
      }`}
    >
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      <div className="flex-1 flex flex-col min-w-0 overflow-hidden relative">
        <div
          className={`absolute top-0 right-0 w-[500px] h-[500px] rounded-full blur-3xl pointer-events-none transition-opacity duration-500 ${
            isDark
              ? "bg-[#EBDCFF] opacity-5 mix-blend-screen"
              : "bg-[#EBDCFF] opacity-10 mix-blend-multiply"
          }`}
        ></div>

        <TopBar
          title="Production Environment"
          onMenuToggle={() => setSidebarOpen((v) => !v)}
          actions={
            <button
              onClick={handleOpenAddModal}
              className={`px-4 py-2 rounded-xl border transition-[color,background-color,border-color,box-shadow] duration-200 text-[13px] font-bold flex items-center gap-1.5 shadow-sm focus-visible:ring-2 outline-none cursor-pointer ${
                isDark
                  ? "bg-[#EBDCFF]/10 border-[#EBDCFF]/20 text-[#EBDCFF] hover:bg-[#EBDCFF]/20 focus-visible:ring-[#EBDCFF]/20"
                  : "bg-[#1c1c1e] border-[#1c1c1e] text-[#F5F5F7] hover:bg-black focus-visible:ring-black/20"
              }`}
            >
              <span className="material-symbols-outlined text-[18px]" aria-hidden="true">
                add
              </span>
              <span className="hidden sm:inline">Add Provider</span>
            </button>
          }
        />
        <main className="flex-1 overflow-y-auto p-4 sm:p-8 lg:p-12 z-10">
          <div className="mb-12">
            <span
              className={`text-[11px] font-bold tracking-[0.2em] uppercase mb-3 block ${
                c("text-[#1c1c1e]/40", "text-[#EBDCFF]")
              }`}
            >
              Configuration
            </span>
            <h1
              className={`text-[2.5rem] lg:text-[3.5rem] font-bold tracking-tight leading-none mb-3 ${
                c("text-[#1c1c1e]", "text-white")
              }`}
              style={{ fontFamily: "'Playfair Display', serif" }}
            >
              API Models & Routing
            </h1>
            <p
              className={`text-lg max-w-2xl font-medium ${
                c("text-[#1c1c1e]/60", "text-white/50")
              }`}
            >
              Configure intelligence pipelines and map intents to specialized model clusters.
            </p>
          </div>

          {/* Routing Fabric Visual */}
          <div
            className={`rounded-[2rem] border overflow-hidden p-8 mb-8 relative ${
              isDark
                ? "bg-[#1f1f23] border-white/[0.06]"
                : "bg-white border-black/5 shadow-[0_8px_30px_rgb(0,0,0,0.02)]"
            }`}
          >
            <div className="flex items-center justify-between mb-8">
              <h2
                className={`text-[20px] font-serif font-bold ${
                  c("text-[#1c1c1e]", "text-white")
                }`}
                style={{ fontFamily: "'Playfair Display', serif" }}
              >
                Active Routing Fabric
              </h2>
              <div
                className={`flex items-center gap-2 px-3 py-1.5 rounded-full border shadow-sm ${
                  isDark
                    ? "bg-white/5 border-white/10"
                    : "bg-[#F5F5F7] border-black/5"
                }`}
              >
                <div
                  className={`w-1.5 h-1.5 rounded-full ${
                    activeRules.length > 0 ? "bg-green-500 animate-pulse" : c("bg-black/20", "bg-white/20")
                  }`}
                ></div>
                <span
                  className={`text-[10px] font-bold uppercase tracking-widest ${
                    c("text-[#1c1c1e]", "text-[#EBDCFF]")
                  }`}
                >
                  {activeRules.length > 0 ? "Live" : "Inactive"}
                </span>
              </div>
            </div>

            {loading ? (
              <div className="flex flex-col md:flex-row items-center justify-center gap-6 py-6 animate-pulse">
                {/* Origin Node */}
                <div className={`rounded-[1.5rem] p-6 w-48 h-36 border flex flex-col items-center justify-center gap-2 ${isDark ? "bg-[#131317] border-white/[0.06]" : "bg-[#F5F5F7] border-black/5"}`}>
                  <div className={`w-12 h-12 rounded-xl ${isDark ? "bg-[#2a2a2e]" : "bg-black/5"}`} />
                  <div className={`h-4.5 w-24 rounded ${isDark ? "bg-white/5" : "bg-black/5"}`} />
                  <div className={`h-3 w-28 rounded ${isDark ? "bg-white/5" : "bg-black/5"}`} />
                </div>

                {/* Arrow */}
                <div className="hidden md:flex items-center">
                  <div className={`w-10 h-[2px] ${isDark ? "bg-white/5" : "bg-black/5"}`}></div>
                  <span className={`material-symbols-outlined text-[20px] ${isDark ? "text-white/10" : "text-black/10"}`}>arrow_forward</span>
                </div>

                {/* Router Node */}
                <div className={`rounded-[1.5rem] p-6 w-48 h-36 border-2 border-dashed flex flex-col items-center justify-center gap-2 ${isDark ? "bg-[#131317] border-white/[0.1]" : "bg-[#F5F5F7] border-black/10"}`}>
                  <div className={`w-12 h-12 rounded-xl ${isDark ? "bg-[#2a2a2e]" : "bg-black/5"}`} />
                  <div className={`h-4.5 w-24 rounded ${isDark ? "bg-white/5" : "bg-black/5"}`} />
                  <div className={`h-3 w-28 rounded ${isDark ? "bg-white/5" : "bg-black/5"}`} />
                </div>

                {/* Arrow */}
                <div className="hidden md:flex items-center">
                  <div className={`w-10 h-[2px] ${isDark ? "bg-white/5" : "bg-black/5"}`}></div>
                  <span className={`material-symbols-outlined text-[20px] ${isDark ? "text-white/10" : "text-black/10"}`}>arrow_forward</span>
                </div>

                {/* Destination Nodes */}
                <div className="flex flex-col gap-3 w-full md:w-auto">
                  {[1, 2].map((i) => (
                    <div key={i} className={`rounded-2xl px-5 py-4 w-full md:w-64 h-20 border flex items-center justify-between gap-4 ${isDark ? "bg-[#131317] border-white/[0.04]" : "bg-[#F5F5F7] border-black/5"}`}>
                      <div className="space-y-1.5 flex-grow">
                        <div className={`h-3 w-16 rounded ${isDark ? "bg-white/5" : "bg-black/5"}`} />
                        <div className={`h-4.5 w-28 rounded ${isDark ? "bg-white/5" : "bg-black/5"}`} />
                        <div className={`h-3.5 w-24 rounded ${isDark ? "bg-white/5" : "bg-black/5"}`} />
                      </div>
                      <div className={`w-10 h-10 rounded-full ${isDark ? "bg-white/5" : "bg-black/5"}`} />
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="flex flex-col md:flex-row items-center justify-center gap-6 py-6">
                {/* Origin Node */}
                <div
                  className={`rounded-[1.5rem] p-6 w-48 text-center border shadow-sm transition-all ${
                    isDark
                      ? "bg-[#131317] border-white/[0.06]"
                      : "bg-[#F5F5F7] border-black/5"
                  }`}
                >
                  <div
                    className={`w-12 h-12 mx-auto rounded-xl flex items-center justify-center mb-4 ${
                      isDark ? "bg-[#2a2a2e]" : "bg-black/5"
                    }`}
                  >
                    <span
                      className={`material-symbols-outlined ${
                        c("text-[#1c1c1e]", "text-[#EBDCFF]")
                      }`}
                      aria-hidden="true"
                    >
                      input
                    </span>
                  </div>
                  <h3
                    className={`font-bold text-[14px] ${
                      c("text-[#1c1c1e]", "text-white")
                    }`}
                  >
                    Request Origin
                  </h3>
                  <p
                    className={`text-[11px] font-medium mt-1 ${
                      c("text-[#1c1c1e]/50", "text-white/40")
                    }`}
                  >
                    Multi-channel Gateway
                  </p>
                </div>

                {/* Arrow */}
                <div className="flex md:items-center justify-center py-2 md:py-0">
                  <div className="hidden md:flex items-center">
                    <div className={`w-10 h-[2px] ${c("bg-black/10", "bg-white/10")}`}></div>
                    <span className={`material-symbols-outlined text-[20px] ${c("text-black/30", "text-white/30")}`} aria-hidden="true">
                      arrow_forward
                    </span>
                  </div>
                  <span className={`material-symbols-outlined text-[24px] md:hidden ${c("text-black/30", "text-white/30")}`} aria-hidden="true">
                    arrow_downward
                  </span>
                </div>

                {/* Router Node */}
                <div
                  className={`rounded-[1.5rem] p-6 w-48 text-center border-2 border-dashed relative ${
                    isDark
                      ? "bg-[#131317] border-[#EBDCFF]/30"
                      : "bg-[#F5F5F7] border-[#1c1c1e]/20"
                  }`}
                >
                  <div
                    className={`w-12 h-12 mx-auto rounded-xl flex items-center justify-center mb-4 ${
                      isDark ? "bg-[#EBDCFF]/10 text-[#EBDCFF]" : "bg-[#1c1c1e] text-[#F5F5F7]"
                    }`}
                  >
                    <span className="material-symbols-outlined" aria-hidden="true">
                      hub
                    </span>
                  </div>
                  <h3
                    className={`font-bold text-[14px] ${
                      c("text-[#1c1c1e]", "text-white")
                    }`}
                  >
                    Cognitive Router
                  </h3>
                  <p
                    className={`text-[11px] font-bold mt-1 ${
                      c("text-[#1c1c1e]/60", "text-white/60")
                    }`}
                  >
                    v2.4 Neural Matcher
                  </p>
                </div>

                {/* Arrow */}
                <div className="flex md:items-center justify-center py-2 md:py-0">
                  <div className="hidden md:flex items-center">
                    <div className={`w-10 h-[2px] ${c("bg-black/10", "bg-white/10")}`}></div>
                    <span className={`material-symbols-outlined text-[20px] ${c("text-black/30", "text-white/30")}`} aria-hidden="true">
                      arrow_forward
                    </span>
                  </div>
                  <span className={`material-symbols-outlined text-[24px] md:hidden ${c("text-black/30", "text-white/30")}`} aria-hidden="true">
                    arrow_downward
                  </span>
                </div>

                {/* Destination Nodes */}
                <div className="flex flex-col gap-3 w-full md:w-auto">
                  {activeRules.length === 0 ? (
                    <div
                      className={`rounded-2xl px-5 py-6 flex flex-col items-center justify-center border border-dashed text-center w-full md:w-64 ${
                        isDark ? "bg-white/[0.02] border-white/10" : "bg-black/[0.01] border-black/10"
                      }`}
                    >
                      <span className={`material-symbols-outlined text-[24px] mb-2 ${c("text-black/30", "text-white/30")}`}>
                        route_tos
                      </span>
                      <p className={`text-[12px] font-bold ${c("text-[#1c1c1e]/60", "text-white/50")}`}>
                        No Active Routing
                      </p>
                      <p className={`text-[10px] font-medium mt-1 ${c("text-[#1c1c1e]/40", "text-white/30")}`}>
                        Configure a provider to add routing rules.
                      </p>
                    </div>
                  ) : (
                    activeRules.map((dest, idx) => (
                      <div
                        key={idx}
                        className={`rounded-2xl px-5 py-4 flex items-center justify-between gap-8 border shadow-sm text-left w-full md:w-64 ${
                          isDark ? "bg-[#131317] border-white/[0.04]" : "bg-[#F5F5F7] border-black/5"
                        }`}
                      >
                        <div>
                          <p
                            className={`text-[10px] font-bold uppercase tracking-widest mb-1 ${
                              c("text-[#1c1c1e]/50", "text-white/40")
                            }`}
                          >
                            {dest.label}
                          </p>
                          <p
                            className={`text-[14px] font-bold ${
                              c("text-[#1c1c1e]", "text-white")
                            }`}
                          >
                            {dest.model}
                          </p>
                          <p className={`text-[9px] font-semibold opacity-65 ${c("text-[#1c1c1e]/40", "text-white/30")}`}>
                            via {dest.provider}
                          </p>
                        </div>
                        <div
                          className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 ${
                            isDark ? "bg-[#EBDCFF]/10 text-[#EBDCFF]" : "bg-white border text-[#1c1c1e]"
                          }`}
                        >
                          <span className="material-symbols-outlined text-[18px]" aria-hidden="true">
                            {dest.icon}
                          </span>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Bottom Row */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Router Settings */}
            <div
              className={`rounded-[2rem] border p-8 ${
                isDark
                  ? "bg-[#1f1f23] border-white/[0.06]"
                  : "bg-white border-black/5 shadow-[0_8px_30px_rgb(0,0,0,0.02)]"
              }`}
            >
              <h3
                className={`text-[18px] font-serif font-bold mb-8 ${
                  c("text-[#1c1c1e]", "text-white")
                }`}
                style={{ fontFamily: "'Playfair Display', serif" }}
              >
                Router Settings
              </h3>
              <div className="space-y-6">
                {[
                  {
                    label: "Latency Tolerance",
                    value: `${latencyTolerance}ms`,
                    pct: Math.min(100, (latencyTolerance / 3000) * 100),
                    color: c("#1c1c1e", "#EBDCFF"),
                    onChange: (v: number) => setLatencyTolerance(v),
                    min: 100,
                    max: 3000,
                  },
                  {
                    label: "Cost Optimization",
                    value: costOptimization > 70 ? "Aggressive" : costOptimization > 40 ? "Balanced" : "Conservative",
                    pct: costOptimization,
                    color: c("rgba(0,0,0,0.3)", "rgba(255,255,255,0.4)"),
                    onChange: (v: number) => setCostOptimization(v),
                    min: 0,
                    max: 100,
                  },
                ].map((s) => (
                  <div key={s.label}>
                    <div className="flex justify-between mb-2">
                      <span
                        className={`text-[13px] font-medium ${
                          c("text-[#1c1c1e]/70", "text-white/70")
                        }`}
                      >
                        {s.label}
                      </span>
                      <span className="text-[13px] font-bold" style={{ color: s.color }}>
                        {s.value}
                      </span>
                    </div>
                    <div className="relative group">
                      <input
                        type="range"
                        min={s.min}
                        max={s.max}
                        value={s.pct}
                        onChange={(e) => s.onChange(Number(e.target.value))}
                        className="w-full h-2 bg-black/5 dark:bg-[#131317] rounded-lg appearance-none cursor-pointer accent-[#8a5cf5] focus:outline-none"
                      />
                    </div>
                  </div>
                ))}

                <div className={`pt-6 mt-6 border-t ${c("border-black/5", "border-white/[0.06]")}`}>
                  {[
                    {
                      label: "Auto-Failover",
                      sub: "Switch if provider fails",
                      enabled: autoFailover,
                      onToggle: () => setAutoFailover(!autoFailover),
                    },
                    {
                      label: "Response Caching",
                      sub: "Cache repeated questions",
                      enabled: responseCaching,
                      onToggle: () => setResponseCaching(!responseCaching),
                    },
                  ].map((toggle) => (
                    <div
                      key={toggle.label}
                      className={`flex items-center justify-between py-4 border-b last:border-0 ${
                        c("border-black/5", "border-white/[0.04]")
                      }`}
                    >
                      <div>
                        <p
                          className={`text-[14px] font-bold ${
                            c("text-[#1c1c1e]", "text-white")
                          }`}
                        >
                          {toggle.label}
                        </p>
                        <p
                          className={`text-[12px] font-medium mt-1 ${
                            c("text-[#1c1c1e]/50", "text-[#85948b]")
                          }`}
                        >
                          {toggle.sub}
                        </p>
                      </div>

                      {/* Toggle Switch */}
                      <button
                        role="switch"
                        aria-checked={toggle.enabled}
                        aria-label={toggle.label}
                        onClick={toggle.onToggle}
                        className={`w-12 h-6 rounded-full relative cursor-pointer outline-none transition-[background-color,box-shadow] duration-200 focus-visible:ring-2 focus-visible:ring-offset-2 ${
                          isDark
                            ? "focus-visible:ring-offset-[#1f1f23] focus-visible:ring-[#EBDCFF]"
                            : "focus-visible:ring-offset-white focus-visible:ring-[#1c1c1e]"
                        } ${
                          toggle.enabled
                            ? isDark
                              ? "bg-[#EBDCFF]"
                              : "bg-[#1c1c1e]"
                            : isDark
                            ? "bg-[#353439]"
                            : "bg-black/10"
                        }`}
                      >
                        <div
                          className={`absolute top-1 w-4 h-4 rounded-full transition-all shadow-sm ${
                            toggle.enabled
                              ? `right-1 ${isDark ? "bg-[#1c1c1e]" : "bg-[#F5F5F7]"}`
                              : `left-1 ${isDark ? "bg-[#85948b]" : "bg-white"}`
                          }`}
                        ></div>
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Backends Table */}
            <div
              className={`rounded-[2rem] border overflow-hidden lg:col-span-2 ${
                isDark
                  ? "bg-[#1f1f23] border-white/[0.06]"
                  : "bg-white border-black/5 shadow-[0_8px_30px_rgb(0,0,0,0.02)]"
              }`}
            >
              <div
                className={`p-8 border-b ${
                  c("border-black/5", "border-white/[0.06]")
                }`}
              >
                <h3
                  className={`text-[20px] font-serif font-bold ${
                    c("text-[#1c1c1e]", "text-white")
                  }`}
                  style={{ fontFamily: "'Playfair Display', serif" }}
                >
                  Configured Backends
                </h3>
                <p
                  className={`text-[13px] font-medium mt-1 ${
                    c("text-[#1c1c1e]/50", "text-white/40")
                  }`}
                >
                  {configs.length} of {providers.length} providers connected
                </p>
              </div>

              {loading ? (
                <div className="overflow-x-auto animate-pulse">
                  <table className="w-full text-left">
                    <thead>
                      <tr className={isDark ? "bg-black/20" : "bg-[#F5F5F7]/50"}>
                        {["Provider", "Model Routing Targets", "Status", ""].map((h) => (
                          <th
                            key={h}
                            className={`px-4 sm:px-8 py-3.5 sm:py-4 text-[11px] font-bold uppercase tracking-[0.15em] border-b whitespace-nowrap ${
                              isDark
                                ? "text-white/30 border-white/[0.06]"
                                : "text-[#1c1c1e]/40 border-black/5"
                            }`}
                          >
                            {h}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className={isDark ? "divide-y divide-white/[0.04]" : "divide-y divide-black/5"}>
                      {[1, 2, 3].map((i) => (
                        <tr key={i}>
                          <td className="px-4 sm:px-8 py-4 sm:py-6">
                            <div className="flex items-center gap-4">
                              <div className={`w-10 h-10 rounded-xl ${isDark ? "bg-white/5" : "bg-black/5"}`} />
                              <div className={`h-4.5 w-24 rounded ${isDark ? "bg-white/5" : "bg-black/5"}`} />
                            </div>
                          </td>
                          <td className="px-4 sm:px-8 py-4 sm:py-6">
                            <div className="space-y-1.5">
                              <div className={`h-4 w-48 rounded ${isDark ? "bg-white/5" : "bg-black/5"}`} />
                              <div className={`h-3 w-64 rounded ${isDark ? "bg-white/5" : "bg-black/5"}`} />
                            </div>
                          </td>
                          <td className="px-4 sm:px-8 py-4 sm:py-6">
                            <div className={`w-20 h-6 rounded-full ${isDark ? "bg-white/5" : "bg-black/5"}`} />
                          </td>
                          <td className="px-4 sm:px-8 py-4 sm:py-6">
                            <div className="flex justify-end gap-2">
                              <div className={`w-8 h-8 rounded-lg ${isDark ? "bg-white/5" : "bg-black/5"}`} />
                              <div className={`w-8 h-8 rounded-lg ${isDark ? "bg-white/5" : "bg-black/5"}`} />
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left">
                    <thead>
                      <tr className={isDark ? "bg-black/20" : "bg-[#F5F5F7]/50"}>
                        {["Provider", "Model Routing Targets", "Status", ""].map((h) => (
                          <th
                            key={h}
                            className={`px-4 sm:px-8 py-3.5 sm:py-4 text-[11px] font-bold uppercase tracking-[0.15em] border-b whitespace-nowrap ${
                              isDark
                                ? "text-white/30 border-white/[0.06]"
                                : "text-[#1c1c1e]/40 border-black/5"
                            }`}
                          >
                            {h}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className={isDark ? "divide-y divide-white/[0.04]" : "divide-y divide-black/5"}>
                      {providers.map((p) => {
                        const config = configs.find((cfg) => cfg.provider_id === p.id);
                        const logoInfo = getProviderLogoInfo(p.name);
                        const active = !!config;

                        // Create text display for routing targets
                        let routingInfo = "Not Configured";
                        if (active && config) {
                          if (config.routing_rules.length === 0) {
                            routingInfo = "No active rules";
                          } else {
                            routingInfo = config.routing_rules
                              .map((rule) => `${rule.intent} → ${rule.model_target}`)
                              .join(", ");
                          }
                        }

                        return (
                          <tr
                            key={p.id}
                            className={`transition-colors ${
                              isDark ? "hover:bg-white/[0.02]" : "hover:bg-black/[0.02]"
                            }`}
                          >
                            <td className="px-4 sm:px-8 py-4 sm:py-6">
                              <div className="flex items-center gap-4">
                                <div
                                  className="w-10 h-10 rounded-xl flex items-center justify-center text-[16px] font-bold shadow-sm"
                                  style={{ backgroundColor: logoInfo.bg, color: logoInfo.color }}
                                >
                                  {logoInfo.logo}
                                </div>
                                <span
                                  className={`text-[15px] font-bold ${
                                    c("text-[#1c1c1e]", "text-white")
                                  }`}
                                >
                                  {p.name}
                                </span>
                              </div>
                            </td>
                            <td
                              className={`px-4 sm:px-8 py-4 sm:py-6 text-[13px] font-medium max-w-xs sm:max-w-sm truncate ${
                                active
                                  ? c("text-[#1c1c1e]/80", "text-[#bbcac0]")
                                  : c("text-[#1c1c1e]/40", "text-white/20")
                              }`}
                              title={routingInfo}
                            >
                              {routingInfo}
                            </td>
                            <td className="px-4 sm:px-8 py-4 sm:py-6">
                              {active ? (
                                <span
                                  className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-[11px] font-bold uppercase tracking-wider border shadow-sm ${
                                    isDark
                                      ? "bg-[#EBDCFF]/10 text-[#EBDCFF] border-[#EBDCFF]/20"
                                      : "bg-[#1c1c1e] text-[#F5F5F7] border-transparent"
                                  }`}
                                >
                                  <span
                                    className={`w-1.5 h-1.5 rounded-full animate-pulse ${
                                      isDark ? "bg-[#EBDCFF]" : "bg-[#F5F5F7]"
                                    }`}
                                  ></span>
                                  Active
                                </span>
                              ) : (
                                <span
                                  className={`inline-flex px-3 py-1.5 rounded-full text-[11px] font-bold uppercase tracking-wider border ${
                                    isDark
                                      ? "bg-[#2a2a2e] text-[#85948b] border-white/[0.06]"
                                      : "bg-black/5 text-[#1c1c1e]/50 border-transparent"
                                  }`}
                                >
                                  Standby
                                </span>
                              )}
                            </td>
                            <td className="px-4 sm:px-8 py-4 sm:py-6 text-right">
                              <div className="flex items-center justify-end gap-2">
                                {active && config ? (
                                  <>
                                    <button
                                      onClick={() => handleOpenEditModal(config)}
                                      aria-label={`Configure settings for ${p.name}`}
                                      className={`w-10 h-10 flex items-center justify-center rounded-xl transition-[color,background-color,border-color,box-shadow] duration-200 outline-none border cursor-pointer ${
                                        isDark
                                          ? "text-white/30 hover:text-white hover:bg-white/5 border-transparent hover:border-white/10 focus-visible:ring-[#EBDCFF]/20"
                                          : "text-[#1c1c1e]/40 hover:text-[#1c1c1e] hover:bg-black/5 border-transparent hover:border-black/5 focus-visible:ring-[#1c1c1e]/20"
                                      }`}
                                    >
                                      <span className="material-symbols-outlined text-[20px]" aria-hidden="true">
                                        settings
                                      </span>
                                    </button>
                                    <button
                                      onClick={() => handleDeleteConfig(config.id, p.name)}
                                      aria-label={`Disconnect ${p.name}`}
                                      className={`w-10 h-10 flex items-center justify-center rounded-xl transition-[color,background-color,border-color,box-shadow] duration-200 outline-none border cursor-pointer ${
                                        isDark
                                          ? "text-red-400/40 hover:text-red-400 hover:bg-white/5 border-transparent hover:border-red-400/20 focus-visible:ring-red-400/20"
                                          : "text-red-500/50 hover:text-red-600 hover:bg-red-50 border-transparent hover:border-red-100 focus-visible:ring-red-500/20"
                                      }`}
                                    >
                                      <span className="material-symbols-outlined text-[20px]" aria-hidden="true">
                                        delete
                                      </span>
                                    </button>
                                  </>
                                ) : (
                                  <button
                                    onClick={() => {
                                      setEditingConfig(null);
                                      setSelectedProviderId(p.id);
                                      setApiKey("");
                                      setSecretRef("");
                                      setRoutingRules([
                                        { intent: "General Inquiries", model_target: getSuggestedModels(p.id)[0] || "" },
                                      ]);
                                      setIsModalOpen(true);
                                    }}
                                    className={`px-3 py-1.5 rounded-lg border transition-all duration-200 text-[11px] font-bold flex items-center gap-1 cursor-pointer ${
                                      isDark
                                        ? "bg-white/5 border-white/10 hover:bg-white/10 text-white"
                                        : "bg-white border-black/10 hover:bg-black/5 text-[#1c1c1e]"
                                    }`}
                                  >
                                    <span className="material-symbols-outlined text-[14px]">add</span>
                                    Configure
                                  </button>
                                )}
                              </div>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        </main>
      </div>

      {/* Add / Edit Config Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="fixed inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setIsModalOpen(false)}></div>
          <div
            className={`relative w-full max-w-xl rounded-[2rem] border p-6 sm:p-8 space-y-6 shadow-2xl transition-all z-10 max-h-[90vh] overflow-y-auto no-scrollbar ${
              isDark ? "bg-[#1f1f23] border-white/[0.08] text-white" : "bg-white border-black/10 text-[#1c1c1e]"
            }`}
          >
            <div className="flex justify-between items-center">
              <h3 className="text-[22px] font-serif font-bold" style={{ fontFamily: "'Playfair Display', serif" }}>
                {editingConfig
                  ? `Configure ${providers.find((p) => p.id === selectedProviderId)?.name || "Provider"}`
                  : "Add Provider Connection"}
              </h3>
              <button
                onClick={() => setIsModalOpen(false)}
                className={`p-1.5 rounded-full transition-colors cursor-pointer ${
                  isDark ? "hover:bg-white/10 text-white/60" : "hover:bg-black/5 text-black/60"
                }`}
              >
                <span className="material-symbols-outlined text-[20px]">close</span>
              </button>
            </div>

            <form onSubmit={handleSave} className="space-y-6">
              {/* Provider Dropdown (only enabled when creating) */}
              <div>
                <label className={`block text-[11px] font-bold uppercase tracking-widest mb-2 ${c("text-[#1c1c1e]/50", "text-[#85948b]")}`}>
                  AI Provider
                </label>
                <select
                  disabled={!!editingConfig}
                  value={selectedProviderId}
                  onChange={(e) => {
                    setSelectedProviderId(e.target.value);
                    const suggested = getSuggestedModels(e.target.value);
                    setRoutingRules([{ intent: "General Inquiries", model_target: suggested[0] || "" }]);
                  }}
                  className={`w-full rounded-xl px-4 py-3 text-[14px] font-medium outline-none transition-all shadow-inner border ${
                    isDark
                      ? "bg-[#131317] border-white/[0.06] text-white focus:border-[#EBDCFF]/50"
                      : "bg-[#F5F5F7] border-black/5 text-[#1c1c1e] focus:border-black/20 focus:bg-white"
                  }`}
                >
                  {providers.map((p) => {
                    // When adding, disable already configured providers
                    const alreadyConfigured = configs.some((cfg) => cfg.provider_id === p.id && (!editingConfig || editingConfig.provider_id !== p.id));
                    return (
                      <option key={p.id} value={p.id} disabled={alreadyConfigured}>
                        {p.name} {alreadyConfigured ? "(Configured)" : ""}
                      </option>
                    );
                  })}
                </select>
              </div>

              {/* API Key */}
              <div>
                <label className={`block text-[11px] font-bold uppercase tracking-widest mb-2 ${c("text-[#1c1c1e]/50", "text-[#85948b]")}`}>
                  API Key
                </label>
                <input
                  type="password"
                  placeholder={editingConfig ? "•••••••• (Leave blank to keep current key)" : "Enter API Key"}
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  className={`w-full rounded-xl px-4 py-3 text-[14px] font-medium outline-none transition-all shadow-inner border ${
                    isDark
                      ? "bg-[#131317] border-white/[0.06] text-white focus:border-[#EBDCFF]/50"
                      : "bg-[#F5F5F7] border-black/5 text-[#1c1c1e] focus:border-black/20 focus:bg-white"
                  }`}
                />
              </div>

              {/* Secret Reference */}
              <div>
                <label className={`block text-[11px] font-bold uppercase tracking-widest mb-2 ${c("text-[#1c1c1e]/50", "text-[#85948b]")}`}>
                  Secret Reference (Optional)
                </label>
                <input
                  type="text"
                  placeholder="e.g. aws/secrets/openai-key-v1"
                  value={secretRef}
                  onChange={(e) => setSecretRef(e.target.value)}
                  className={`w-full rounded-xl px-4 py-3 text-[14px] font-medium outline-none transition-all shadow-inner border ${
                    isDark
                      ? "bg-[#131317] border-white/[0.06] text-white focus:border-[#EBDCFF]/50"
                      : "bg-[#F5F5F7] border-black/5 text-[#1c1c1e] focus:border-black/20 focus:bg-white"
                  }`}
                />
              </div>

              {/* Routing Rules Section */}
              <div className="space-y-4 pt-2">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className={`text-[14px] font-bold ${c("text-[#1c1c1e]", "text-white")}`}>
                      Routing Rules Mappings
                    </h4>
                    <p className={`text-[11px] font-medium ${c("text-[#1c1c1e]/50", "text-[#85948b]")}`}>
                      Map incoming intents to specific model variants.
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={handleAddRule}
                    className={`px-3 py-1.5 rounded-lg border transition-all text-[11px] font-bold flex items-center gap-1 cursor-pointer ${
                      isDark
                        ? "bg-[#EBDCFF]/10 border-[#EBDCFF]/20 text-[#EBDCFF] hover:bg-[#EBDCFF]/20"
                        : "bg-[#1c1c1e] border-[#1c1c1e] text-[#F5F5F7] hover:bg-black"
                    }`}
                  >
                    <span className="material-symbols-outlined text-[14px]">add</span>
                    Add Mapping
                  </button>
                </div>

                {routingRules.length === 0 ? (
                  <div
                    className={`p-6 rounded-xl border border-dashed text-center ${
                      isDark ? "bg-[#131317] border-white/10" : "bg-[#F5F5F7] border-black/10"
                    }`}
                  >
                    <p className={`text-[12px] font-medium ${c("text-[#1c1c1e]/50", "text-[#85948b]")}`}>
                      No mappings set. The provider configuration requires at least one routing rule mapping.
                    </p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {routingRules.map((rule, idx) => (
                      <div key={idx} className="flex gap-3 items-center">
                        {/* Intent select or input */}
                        <div className="flex-1">
                          <select
                            value={POPULAR_INTENTS.includes(rule.intent) ? rule.intent : "Custom"}
                            onChange={(e) => {
                              const val = e.target.value;
                              if (val === "Custom") {
                                handleRuleChange(idx, "intent", "");
                              } else {
                                handleRuleChange(idx, "intent", val);
                              }
                            }}
                            className={`w-full rounded-xl px-3 py-2.5 text-[13px] font-medium outline-none border ${
                              isDark
                                ? "bg-[#131317] border-white/[0.06] text-white focus:border-[#EBDCFF]/50"
                                : "bg-[#F5F5F7] border-black/5 text-[#1c1c1e] focus:border-black/20 focus:bg-white"
                            }`}
                          >
                            {POPULAR_INTENTS.map((intent) => (
                              <option key={intent} value={intent}>
                                {intent}
                              </option>
                            ))}
                            <option value="Custom">Custom...</option>
                          </select>
                          {!POPULAR_INTENTS.includes(rule.intent) && (
                            <input
                              type="text"
                              required
                              placeholder="Type custom intent..."
                              value={rule.intent}
                              onChange={(e) => handleRuleChange(idx, "intent", e.target.value)}
                              className={`w-full mt-1.5 rounded-xl px-3 py-2 text-[12px] font-medium outline-none border ${
                                isDark
                                  ? "bg-[#131317] border-white/[0.06] text-white focus:border-[#EBDCFF]/50"
                                  : "bg-[#F5F5F7] border-black/5 text-[#1c1c1e] focus:border-black/20 focus:bg-white"
                              }`}
                            />
                          )}
                        </div>

                        {/* Model select or input */}
                        <div className="flex-1">
                          <select
                            value={getSuggestedModels(selectedProviderId).includes(rule.model_target) ? rule.model_target : "Custom"}
                            onChange={(e) => {
                              const val = e.target.value;
                              if (val === "Custom") {
                                handleRuleChange(idx, "model_target", "");
                              } else {
                                handleRuleChange(idx, "model_target", val);
                              }
                            }}
                            className={`w-full rounded-xl px-3 py-2.5 text-[13px] font-medium outline-none border ${
                              isDark
                                ? "bg-[#131317] border-white/[0.06] text-white focus:border-[#EBDCFF]/50"
                                : "bg-[#F5F5F7] border-black/5 text-[#1c1c1e] focus:border-black/20 focus:bg-white"
                            }`}
                          >
                            {getSuggestedModels(selectedProviderId).map((model) => (
                              <option key={model} value={model}>
                                {model}
                              </option>
                            ))}
                            <option value="Custom">Custom...</option>
                          </select>
                          {!getSuggestedModels(selectedProviderId).includes(rule.model_target) && (
                            <input
                              type="text"
                              required
                              placeholder="Type model identifier (e.g. gpt-4)..."
                              value={rule.model_target}
                              onChange={(e) => handleRuleChange(idx, "model_target", e.target.value)}
                              className={`w-full mt-1.5 rounded-xl px-3 py-2 text-[12px] font-medium outline-none border ${
                                isDark
                                  ? "bg-[#131317] border-white/[0.06] text-white focus:border-[#EBDCFF]/50"
                                  : "bg-[#F5F5F7] border-black/5 text-[#1c1c1e] focus:border-black/20 focus:bg-white"
                              }`}
                            />
                          )}
                        </div>

                        {/* Action buttons */}
                        <button
                          type="button"
                          onClick={() => handleRemoveRule(idx)}
                          className={`p-2 rounded-xl transition-colors cursor-pointer ${
                            isDark ? "hover:bg-[#ffb4ab]/10 text-red-400" : "hover:bg-red-50 text-red-500"
                          }`}
                        >
                          <span className="material-symbols-outlined text-[20px]">delete</span>
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Submit Buttons */}
              <div className="flex justify-end gap-3 pt-4 border-t border-white/[0.04]">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className={`px-5 py-2.5 rounded-xl font-bold text-[14px] transition-all cursor-pointer ${
                    isDark ? "hover:bg-white/5 text-white/60" : "hover:bg-black/5 text-[#1c1c1e]/60"
                  }`}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className={`px-5 py-2.5 rounded-xl font-bold text-[14px] transition-all shadow-md active:scale-95 cursor-pointer ${
                    isDark
                      ? "bg-[#EBDCFF] text-[#1c1c1e] hover:bg-[#d8bfff]"
                      : "bg-[#1c1c1e] text-[#F5F5F7] hover:bg-black"
                  }`}
                >
                  {submitting ? "Saving..." : "Save Settings"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
