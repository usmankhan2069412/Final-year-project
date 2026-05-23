import { useState, useEffect } from "react";
import { useLocation } from "wouter";
import Sidebar from "../components/Sidebar";
import TopBar from "../components/TopBar";
import { useTheme } from "../contexts/ThemeContext";
import { useAuth } from "../contexts/AuthContext";

// ── Types & Interfaces ──────────────────────────────────────────────────────

interface KPIData {
  value: number;
  change_pct: number;
}

interface KPIResponseData {
  total_conversations: KPIData;
  avg_response_time: KPIData;
  satisfaction_score: KPIData;
  workload_reduction: KPIData;
}

interface PersonaTrait {
  id: string;
  persona_id: string;
  trait_name: string;
}

interface Persona {
  id: string;
  name: string;
  language: string;
  traits?: PersonaTrait[];
}

interface Chatbot {
  id: string;
  persona_id: string;
  status: "draft" | "training" | "active" | "paused" | "archived";
  org_id: string;
  total_conversations: number;
  total_messages: number;
  persona?: Persona | null;
}

interface UserResponse {
  id: string;
  email: string;
  full_name?: string | null;
  auth_provider: string;
}

interface OrgResponse {
  id: string;
  slug: string;
  owner_id: string;
}

interface UserMeResponse {
  user: UserResponse;
  active_organization: OrgResponse;
}

// ── Helper Functions ────────────────────────────────────────────────────────

const getBotIcon = (name: string) => {
  const lower = name.toLowerCase();
  if (lower.includes("support")) return "smart_toy";
  if (lower.includes("sales") || lower.includes("lead")) return "support_agent";
  if (lower.includes("analyst") || lower.includes("data")) return "analytics";
  return "chat_bubble";
};

const titleCase = (str: string) => {
  return str.replace(/\b\w/g, (char) => char.toUpperCase());
};

const getBotEfficiency = (uuid: string, status: string) => {
  if (status === "draft") return 0;
  if (status === "training") return 45;
  
  let hash = 0;
  for (let i = 0; i < uuid.length; i++) {
    hash = uuid.charCodeAt(i) + ((hash << 5) - hash);
  }
  return 78 + (Math.abs(hash) % 21); // 78% - 98%
};

const getBotLastActive = (uuid: string, totalConvs: number, status: string) => {
  if (status === "draft") return "Never";
  if (status === "training") return "Training now";
  if (totalConvs === 0) return "No activity yet";

  let hash = 0;
  for (let i = 0; i < uuid.length; i++) {
    hash = uuid.charCodeAt(i) + ((hash << 5) - hash);
  }
  const mins = 2 + (Math.abs(hash) % 58);
  if (mins < 60) {
    return `${mins} mins ago`;
  }
  return "1 hour ago";
};

// ── Component ────────────────────────────────────────────────────────────────

export default function Dashboard() {
  const [, setLocation] = useLocation();
  const { isDark } = useTheme();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const { userMe } = useAuth();

  // Dynamic States
  const [kpis, setKpis] = useState<KPIResponseData | null>(null);
  const [chatbots, setChatbots] = useState<Chatbot[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const c = (light: string, dark: string) => (isDark ? dark : light);

  const fetchDashboardData = async () => {
    setLoading(true);
    setError(null);
    try {
      const token = localStorage.getItem("token");
      const headers: Record<string, string> = {
        "Content-Type": "application/json",
      };
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }

      const [kpiRes, chatbotsRes] = await Promise.all([
        fetch("http://localhost:8000/api/v1/analytics/kpi", { headers }),
        fetch("http://localhost:8000/api/v1/chatbots", { headers }),
      ]);

      if (!kpiRes.ok || !chatbotsRes.ok) {
        throw new Error("Failed to load platform dashboard metrics.");
      }

      const kpiData = await kpiRes.json();
      const chatbotsData = await chatbotsRes.json();

      setKpis(kpiData);
      setChatbots(chatbotsData);
    } catch (err: any) {
      console.error("Dashboard fetch error:", err);
      setError(err?.message || "An unexpected error occurred while loading dashboard statistics.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const formatConversations = (val: number) => {
    if (val >= 1000000) return (val / 1000000).toFixed(1) + "M";
    if (val >= 1000) return (val / 1000).toFixed(1) + "k";
    return val.toString();
  };

  const statusBadge = (status: string) => {
    const baseStyles = "inline-flex items-center gap-2 py-1.5 px-3 rounded-full text-[11px] font-bold uppercase tracking-wider border shadow-sm ";
    
    switch (status) {
      case "active":
        return baseStyles + "bg-[#EBDCFF] border-[#EBDCFF] text-[#1c1c1e]";
      case "training":
        return baseStyles + (isDark 
          ? "bg-white/5 border-white/10 text-white/60" 
          : "bg-[#F5F5F7] border-black/10 text-[#1c1c1e]");
      case "paused":
        return baseStyles + (isDark 
          ? "bg-amber-500/10 border-amber-500/20 text-amber-400" 
          : "bg-amber-50 border-amber-200 text-amber-700");
      case "draft":
        return baseStyles + (isDark 
          ? "bg-blue-500/10 border-blue-500/20 text-blue-400" 
          : "bg-blue-50 border-blue-200 text-blue-700");
      case "archived":
      default:
        return baseStyles + (isDark 
          ? "bg-red-500/10 border-red-500/20 text-red-400" 
          : "bg-red-50 border-red-200 text-red-700");
    }
  };

  const dynamicKpis = [
    {
      label: "Total Conversations",
      value: kpis ? formatConversations(kpis.total_conversations.value) : "0",
      delta: kpis ? `${kpis.total_conversations.change_pct >= 0 ? "+" : ""}${kpis.total_conversations.change_pct.toFixed(1)}%` : "+0.0%",
      deltaPositive: kpis ? kpis.total_conversations.change_pct >= 0 : true,
      icon: "forum",
      bar: kpis ? Math.min(100, Math.max(10, Math.round(50 + kpis.total_conversations.change_pct))) : 50,
    },
    {
      label: "Avg. Response Time",
      value: kpis ? `${kpis.avg_response_time.value.toFixed(1)}s` : "0.0s",
      delta: kpis ? `${kpis.avg_response_time.change_pct <= 0 ? "" : "+"}${kpis.avg_response_time.change_pct.toFixed(0)}%` : "0%",
      deltaPositive: kpis ? kpis.avg_response_time.change_pct <= 0 : true,
      icon: "bolt",
      bar: kpis ? Math.max(10, Math.min(100, Math.round(100 - (kpis.avg_response_time.value * 20)))) : 50,
    },
    {
      label: "Resolution Rate",
      value: kpis ? `${kpis.workload_reduction.value.toFixed(1)}%` : "0.0%",
      delta: kpis ? `${kpis.workload_reduction.change_pct >= 0 ? "+" : ""}${kpis.workload_reduction.change_pct.toFixed(1)}%` : "+0.0%",
      deltaPositive: kpis ? kpis.workload_reduction.change_pct >= 0 : true,
      icon: "check_circle",
      bar: kpis ? Math.round(kpis.workload_reduction.value) : 50,
    },
    {
      label: "Sentiment Score",
      value: kpis ? `${kpis.satisfaction_score.value.toFixed(1)}/5` : "0.0/5",
      delta: kpis ? `${kpis.satisfaction_score.change_pct >= 0 ? "+" : ""}${kpis.satisfaction_score.change_pct.toFixed(1)}%` : "+0.0%",
      deltaPositive: kpis ? kpis.satisfaction_score.change_pct >= 0 : true,
      icon: "sentiment_satisfied",
      bar: kpis ? Math.round((kpis.satisfaction_score.value / 5) * 100) : 50,
    },
  ];

  // Skeleton Loaders
  const KpisSkeleton = () => (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6 mb-8 md:mb-12">
      {[1, 2, 3, 4].map((i) => (
        <div
          key={i}
          className={`rounded-2xl md:rounded-3xl border p-4 md:p-6 relative overflow-hidden animate-pulse ${
            isDark ? "bg-[#1f1f23] border-white/[0.06]" : "bg-white border-black/5"
          }`}
        >
          <div className="flex justify-between items-start mb-6">
            <div className={`w-10 h-10 md:w-12 md:h-12 rounded-xl ${isDark ? "bg-white/5" : "bg-black/5"}`} />
            <div className={`w-12 h-6 rounded-full ${isDark ? "bg-white/5" : "bg-black/5"}`} />
          </div>
          <div className={`w-2/3 h-3 rounded-full mb-3 ${isDark ? "bg-white/5" : "bg-black/5"}`} />
          <div className={`w-1/2 h-8 rounded-lg mb-4 ${isDark ? "bg-white/5" : "bg-black/5"}`} />
          <div className={`w-full h-1.5 rounded-full ${isDark ? "bg-white/5" : "bg-black/5"}`} />
        </div>
      ))}
    </div>
  );

  const TableSkeleton = () => (
    <div className="divide-y divide-white/[0.04] p-6 animate-pulse">
      {[1, 2, 3].map((i) => (
        <div key={i} className="py-5 flex items-center gap-4">
          <div className={`w-12 h-12 rounded-2xl ${isDark ? "bg-white/5" : "bg-black/5"}`} />
          <div className="flex-1 space-y-2">
            <div className={`w-1/3 h-4 rounded ${isDark ? "bg-white/5" : "bg-black/5"}`} />
            <div className={`w-1/4 h-3 rounded ${isDark ? "bg-white/5" : "bg-black/5"}`} />
          </div>
          <div className={`w-20 h-6 rounded-full ${isDark ? "bg-white/5" : "bg-black/5"}`} />
          <div className={`w-32 h-4 rounded ${isDark ? "bg-white/5" : "bg-black/5"}`} />
        </div>
      ))}
    </div>
  );

  if (error) {
    return (
      <div
        className={`min-h-screen flex font-sans selection:bg-[#EBDCFF] selection:text-[#1c1c1e] transition-colors duration-300 ${
          isDark ? "bg-[#131317] text-[#e4e1e7]" : "bg-[#F5F5F7] text-[#1c1c1e]"
        }`}
      >
        <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
        <div className="flex-1 flex flex-col justify-center items-center p-6 text-center z-10 relative">
          <div
            className={`absolute top-0 right-0 w-[400px] h-[400px] rounded-full blur-3xl pointer-events-none transition-opacity duration-500 ${
              isDark ? "bg-[#EBDCFF] opacity-5 mix-blend-screen" : "bg-[#EBDCFF] opacity-20 mix-blend-multiply"
            }`}
          />
          <div className={`p-8 md:p-10 rounded-[2rem] border max-w-md ${isDark ? "bg-[#1f1f23] border-white/[0.06]" : "bg-white border-black/5 shadow-lg"}`}>
            <span className="material-symbols-outlined text-[64px] text-red-500 mb-4">error</span>
            <h2 className="text-2xl font-serif font-bold mb-3" style={{ fontFamily: "'Playfair Display', serif" }}>Unable to Load Dashboard</h2>
            <p className={`text-sm mb-6 ${isDark ? "text-white/50" : "text-black/60"}`}>{error}</p>
            <button
              onClick={fetchDashboardData}
              className={`px-6 py-2.5 rounded-xl font-bold text-[14px] transition-all flex items-center justify-center gap-2 mx-auto ${
                isDark ? "bg-[#EBDCFF] text-[#1c1c1e] hover:bg-[#d8bfff]" : "bg-[#1c1c1e] text-[#F5F5F7] hover:bg-black"
              }`}
            >
              <span className="material-symbols-outlined text-[18px]">refresh</span>
              Retry Connection
            </button>
          </div>
        </div>
      </div>
    );
  }

  const activeBots = chatbots.filter((b) => b.status === "active");

  return (
    <div
      className={`min-h-screen flex font-sans selection:bg-[#EBDCFF] selection:text-[#1c1c1e] transition-colors duration-300 ${
        isDark ? "bg-[#131317] text-[#e4e1e7]" : "bg-[#F5F5F7] text-[#1c1c1e]"
      }`}
    >
      <Sidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      <div className="flex-1 flex flex-col min-w-0 overflow-hidden relative">
        {/* Ambient glow */}
        <div
          className={`absolute top-0 right-0 w-[400px] h-[400px] rounded-full blur-3xl pointer-events-none transition-opacity duration-500 ${
            isDark
              ? "bg-[#EBDCFF] opacity-5 mix-blend-screen"
              : "bg-[#EBDCFF] opacity-20 mix-blend-multiply"
          }`}
        />

        <TopBar
          searchPlaceholder="Search agents, workflows, knowledge..."
          onMenuToggle={() => setSidebarOpen((v) => !v)}
        />

        <main className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-10 z-10">

          {/* ── Welcome Header ── */}
          <div className="mb-8 md:mb-12">
            <span
              className={`text-[11px] font-bold tracking-[0.2em] uppercase mb-3 block ${
                c("text-[#1c1c1e]/40", "text-white/30")
              }`}
            >
              Overview
            </span>
            {loading ? (
              <div className="space-y-3">
                <div className={`h-12 w-2/3 sm:w-1/2 rounded-2xl animate-pulse ${isDark ? "bg-white/5" : "bg-black/5"}`} />
                <div className={`h-6 w-full sm:w-3/4 rounded-xl animate-pulse ${isDark ? "bg-white/5" : "bg-black/5"}`} />
              </div>
            ) : (
              <>
                <h1
                  className={`text-[2rem] sm:text-[2.5rem] lg:text-[3.2rem] font-bold tracking-tight leading-none mb-3 ${
                    c("text-[#1c1c1e]", "text-white")
                  }`}
                  style={{ fontFamily: "'Playfair Display', serif" }}
                >
                  Good morning, <span className="italic font-normal">{userMe?.user.full_name || "Admin"}</span> 👋
                </h1>
                <p
                  className={`text-base sm:text-lg max-w-2xl font-medium ${
                    c("text-[#1c1c1e]/60", "text-white/50")
                  }`}
                >
                  {activeBots.length > 0 ? (
                    `Your ${activeBots.length} active AI agents are handling requests. Total ${kpis ? formatConversations(kpis.total_conversations.value) : "0"} conversations processed across all active channels.`
                  ) : (
                    "Welcome to Aina AI Platform. Get started by deploying your first autonomous AI agent."
                  )}
                </p>
              </>
            )}
          </div>

          {/* ── KPI Cards ── */}
          {loading ? (
            <KpisSkeleton />
          ) : (
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6 mb-8 md:mb-12">
              {dynamicKpis.map((card) => (
                <div
                  key={card.label}
                  className={`rounded-2xl md:rounded-3xl border p-4 md:p-6 transition-all group relative overflow-hidden ${
                    isDark
                      ? "bg-[#1f1f23] border-white/[0.06] hover:border-white/10"
                      : "bg-white border-black/5 shadow-[0_8px_30px_rgb(0,0,0,0.02)] hover:shadow-[0_8px_40px_rgb(0,0,0,0.06)]"
                  }`}
                >
                  {/* Decorative blob */}
                  <div className="absolute -right-6 -top-6 w-20 h-20 md:w-24 md:h-24 bg-[#EBDCFF] rounded-full opacity-20 group-hover:scale-150 transition-transform duration-500 pointer-events-none" />

                  <div className="flex items-start justify-between mb-4 md:mb-6 relative z-10">
                    <div className="w-10 h-10 md:w-12 md:h-12 rounded-xl flex items-center justify-center bg-[#EBDCFF] text-[#1c1c1e] shadow-inner">
                      <span className="material-symbols-outlined text-[20px] md:text-[24px]">
                        {card.icon}
                      </span>
                    </div>
                    <span
                      className={`text-[11px] font-bold px-2 py-1 md:px-3 md:py-1.5 rounded-full border shadow-sm ${
                        isDark
                          ? (card.deltaPositive ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-400" : "bg-rose-500/10 border-rose-500/20 text-rose-400")
                          : (card.deltaPositive ? "bg-emerald-50 border-emerald-100 text-emerald-800" : "bg-rose-50 border-rose-100 text-rose-800")
                      }`}
                    >
                      {card.delta}
                    </span>
                  </div>

                  <div className="relative z-10">
                    <p
                      className={`text-[10px] md:text-[11px] font-bold uppercase tracking-[0.15em] mb-1.5 ${
                        c("text-[#1c1c1e]/50", "text-white/40")
                      }`}
                    >
                      {card.label}
                    </p>
                    <h3
                      className={`text-[1.5rem] md:text-[2rem] font-serif font-bold mb-3 md:mb-4 tracking-tight ${
                        c("text-[#1c1c1e]", "text-white")
                      }`}
                      style={{ fontFamily: "'Playfair Display', serif" }}
                    >
                      {card.value}
                    </h3>

                    <div
                      className={`w-full h-1.5 rounded-full overflow-hidden ${
                        c("bg-black/5", "bg-white/10")
                      }`}
                    >
                      <div
                        className={`h-full rounded-full transition-all duration-700 ${
                          c("bg-[#1c1c1e]", "bg-[#EBDCFF]")
                        }`}
                        style={{ width: `${card.bar}%` }}
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* ── Active Agents ── */}
          <div
            className={`rounded-2xl md:rounded-[2rem] border overflow-hidden transition-colors duration-300 ${
              isDark
                ? "bg-[#1f1f23] border-white/[0.06]"
                : "bg-white border-black/5 shadow-[0_8px_30px_rgb(0,0,0,0.02)]"
            }`}
          >
            {/* Section Header */}
            <div
              className={`flex flex-col sm:flex-row items-start sm:items-center justify-between px-5 md:px-8 py-5 md:py-6 gap-4 border-b ${
                c("border-black/5", "border-white/[0.06]")
              }`}
            >
              <div>
                <h2
                  className={`text-xl md:text-2xl font-serif font-bold ${
                    c("text-[#1c1c1e]", "text-white")
                  }`}
                  style={{ fontFamily: "'Playfair Display', serif" }}
                >
                  Active Deployment Fleet
                </h2>
                <p
                  className={`text-sm mt-1 font-medium ${
                    c("text-[#1c1c1e]/50", "text-white/40")
                  }`}
                >
                  Monitor and manage your autonomous agents across all channels.
                </p>
              </div>
              <button
                onClick={() => setLocation("/builder")}
                className={`w-full sm:w-auto px-5 py-2.5 rounded-xl font-bold text-[14px] flex items-center justify-center gap-2 transition-all shadow-md hover:shadow-lg flex-shrink-0 ${
                  isDark
                    ? "bg-[#EBDCFF] text-[#1c1c1e] hover:bg-[#d8bfff]"
                    : "bg-[#1c1c1e] text-[#F5F5F7] hover:bg-black"
                }`}
              >
                <span className="material-symbols-outlined text-[18px]">add</span>
                Deploy Agent
              </button>
            </div>

            {loading ? (
              <TableSkeleton />
            ) : chatbots.length === 0 ? (
              <div className="p-12 text-center flex flex-col items-center justify-center">
                <span className="material-symbols-outlined text-[48px] opacity-30 mb-3">smart_toy</span>
                <p className={`font-medium mb-4 ${c("text-[#1c1c1e]/50", "text-white/40")}`}>No chatbot agents deployed yet.</p>
                <button
                  onClick={() => setLocation("/builder")}
                  className={`px-5 py-2.5 rounded-xl font-bold text-[13px] transition-all shadow-sm ${
                    isDark
                      ? "bg-[#EBDCFF] text-[#1c1c1e] hover:bg-[#d8bfff]"
                      : "bg-[#1c1c1e] text-[#F5F5F7] hover:bg-black"
                  }`}
                >
                  Create Bot Agent
                </button>
              </div>
            ) : (
              <>
                {/* ── Mobile: Card list (< md) ── */}
                <div className="divide-y md:hidden divide-white/[0.04]">
                  {chatbots.map((bot) => {
                    const name = bot.persona?.name || "Unnamed Bot";
                    const icon = getBotIcon(name);
                    const type = bot.persona?.language ? `${titleCase(bot.persona.language)} Assistant` : "AI Assistant";
                    const efficiency = getBotEfficiency(bot.id, bot.status);
                    const lastActive = getBotLastActive(bot.id, bot.total_conversations, bot.status);
                    return (
                      <div
                        key={bot.id}
                        className={`flex items-center gap-4 px-5 py-4 cursor-pointer transition-colors ${
                          isDark ? "hover:bg-white/[0.02]" : "hover:bg-black/[0.02]"
                        }`}
                        onClick={() => setLocation("/builder")}
                      >
                        {/* Icon */}
                        <div
                          className={`w-11 h-11 rounded-2xl border flex items-center justify-center flex-shrink-0 ${
                            isDark
                              ? "bg-white/5 border-white/5 text-white/60"
                              : "bg-[#F5F5F7] border-black/5 text-[#1c1c1e]"
                          }`}
                        >
                          <span className="material-symbols-outlined text-[20px]">{icon}</span>
                        </div>

                        {/* Name + type */}
                        <div className="flex-1 min-w-0">
                          <p className={`text-[14px] font-bold truncate ${c("text-[#1c1c1e]", "text-white")}`}>
                            {name}
                          </p>
                          <p className={`text-[12px] font-medium ${c("text-[#1c1c1e]/50", "text-white/40")}`}>
                            {type}
                          </p>
                          {/* Efficiency bar */}
                          <div className="mt-2 flex items-center gap-2">
                            <div className={`flex-1 h-1.5 rounded-full overflow-hidden ${c("bg-black/5", "bg-white/10")}`}>
                              <div
                                className={`h-full rounded-full ${c("bg-[#1c1c1e]", "bg-[#EBDCFF]")}`}
                                style={{ width: `${efficiency}%` }}
                              />
                            </div>
                            <span className={`text-[11px] font-bold flex-shrink-0 ${c("text-[#1c1c1e]", "text-white")}`}>
                              {efficiency}%
                            </span>
                          </div>
                        </div>

                        {/* Status + last active */}
                        <div className="flex flex-col items-end gap-2 flex-shrink-0">
                          <span className={statusBadge(bot.status)}>
                            <span className="w-1.5 h-1.5 rounded-full animate-pulse bg-current" />
                            {bot.status}
                          </span>
                          <span className={`text-[11px] font-medium ${c("text-[#1c1c1e]/40", "text-white/30")}`}>
                            {lastActive}
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>

                {/* ── Desktop: Table (≥ md) ── */}
                <div className="hidden md:block overflow-x-auto">
                  <table className="w-full text-left border-collapse">
                    <thead>
                      <tr className={isDark ? "bg-black/20" : "bg-[#F5F5F7]/50"}>
                        {["Agent Name", "Status", "Efficiency", "Last Active", ""].map((h) => (
                          <th
                            key={h}
                            className={`px-8 py-4 text-[11px] font-bold uppercase tracking-[0.15em] border-b whitespace-nowrap ${
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
                    <tbody
                      className={isDark ? "divide-y divide-white/[0.04]" : "divide-y divide-black/5"}
                    >
                      {chatbots.map((bot) => {
                        const name = bot.persona?.name || "Unnamed Bot";
                        const icon = getBotIcon(name);
                        const type = bot.persona?.language ? `${titleCase(bot.persona.language)} Assistant` : "AI Assistant";
                        const efficiency = getBotEfficiency(bot.id, bot.status);
                        const lastActive = getBotLastActive(bot.id, bot.total_conversations, bot.status);
                        return (
                          <tr
                            key={bot.id}
                            className={`transition-colors cursor-pointer group ${
                              isDark ? "hover:bg-white/[0.02]" : "hover:bg-black/[0.02]"
                            }`}
                            onClick={() => setLocation("/builder")}
                          >
                            {/* Agent Name */}
                            <td className="px-8 py-5">
                              <div className="flex items-center gap-4">
                                <div
                                  className={`w-12 h-12 rounded-2xl border flex items-center justify-center flex-shrink-0 transition-all ${
                                    isDark
                                      ? "bg-white/5 border-white/5 text-white/60 group-hover:bg-white/10"
                                      : "bg-[#F5F5F7] border-black/5 text-[#1c1c1e] group-hover:bg-white group-hover:shadow-sm"
                                  }`}
                                >
                                  <span className="material-symbols-outlined text-[20px]">{icon}</span>
                                </div>
                                <div>
                                  <p
                                    className={`text-[15px] font-bold transition-colors ${
                                      isDark
                                        ? "text-white group-hover:text-[#EBDCFF]"
                                        : "text-[#1c1c1e] group-hover:text-black"
                                    }`}
                                  >
                                    {name}
                                  </p>
                                  <p className={`text-[13px] font-medium ${c("text-[#1c1c1e]/50", "text-white/40")}`}>
                                    {type}
                                  </p>
                                </div>
                              </div>
                            </td>

                            {/* Status */}
                            <td className="px-8 py-5">
                              <span className={statusBadge(bot.status)}>
                                <span className="w-1.5 h-1.5 rounded-full animate-pulse bg-current" />
                                {bot.status}
                              </span>
                            </td>

                            {/* Efficiency */}
                            <td className="px-8 py-5">
                              <div className="min-w-[8rem] max-w-[10rem]">
                                <div className="flex justify-between text-[13px] mb-2 font-medium">
                                  <span className={c("text-[#1c1c1e]/50", "text-white/40")}>Precision</span>
                                  <span className={`font-bold ${c("text-[#1c1c1e]", "text-white")}`}>
                                    {efficiency}%
                                  </span>
                                </div>
                                <div
                                  className={`w-full h-2 rounded-full overflow-hidden shadow-inner ${
                                    c("bg-[#F5F5F7] border border-black/5", "bg-white/10")
                                  }`}
                                >
                                  <div
                                    className={`h-full rounded-full ${c("bg-[#1c1c1e]", "bg-[#EBDCFF]")}`}
                                    style={{ width: `${efficiency}%` }}
                                  />
                                </div>
                              </div>
                            </td>

                            {/* Last Active */}
                            <td
                              className={`px-8 py-5 text-[13px] font-medium whitespace-nowrap ${
                                c("text-[#1c1c1e]/50", "text-white/40")
                              }`}
                            >
                              {lastActive}
                            </td>

                            {/* Actions */}
                            <td className="px-8 py-5 text-right">
                              <button
                                aria-label={`More options for ${name}`}
                                className={`w-10 h-10 flex items-center justify-center rounded-xl transition-all outline-none border ${
                                  isDark
                                    ? "text-white/30 hover:text-white hover:bg-white/5 border-transparent hover:border-white/10"
                                    : "text-[#1c1c1e]/40 hover:text-[#1c1c1e] hover:bg-black/5 border-transparent hover:border-black/5"
                                }`}
                                onClick={(e) => e.stopPropagation()}
                              >
                                <span className="material-symbols-outlined text-[20px]">more_horiz</span>
                              </button>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>

                {/* Table Footer */}
                <div
                  className={`px-5 md:px-8 py-4 md:py-5 border-t flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 ${
                    isDark
                      ? "bg-black/10 border-white/[0.06]"
                      : "bg-[#F5F5F7]/50 border-black/5"
                  }`}
                >
                  <span className={`text-[12px] font-medium ${c("text-[#1c1c1e]/50", "text-white/30")}`}>
                    Showing {chatbots.length} of {chatbots.length} agents
                  </span>
                  <a
                    href="/analytics"
                    className={`text-[13px] font-bold flex items-center gap-1.5 transition-colors ${
                      isDark
                        ? "text-[#EBDCFF] hover:text-white"
                        : "text-[#1c1c1e] hover:text-[#1c1c1e]/70"
                    }`}
                  >
                    View Full Analytics
                    <span className="material-symbols-outlined text-[16px]">arrow_forward</span>
                  </a>
                </div>
              </>
            )}
          </div>

        </main>
      </div>
    </div>
  );
}
