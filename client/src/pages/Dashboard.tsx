import { useState } from "react";
import { useLocation } from "wouter";
import Sidebar from "../components/Sidebar";
import TopBar from "../components/TopBar";
import { useTheme } from "../contexts/ThemeContext";

// ── Data ────────────────────────────────────────────────────────────────────

const KPI_CARDS = [
  {
    label: "Total Conversations",
    value: "142,892",
    delta: "+12.4%",
    deltaPositive: true,
    icon: "forum",
    bar: 72,
  },
  {
    label: "Avg. Response Time",
    value: "1.2s",
    delta: "-40ms",
    deltaPositive: true,
    icon: "bolt",
    bar: 85,
  },
  {
    label: "Resolution Rate",
    value: "94.2%",
    delta: "+0.8%",
    deltaPositive: true,
    icon: "check_circle",
    bar: 94,
  },
  {
    label: "Sentiment Score",
    value: "4.8/5",
    delta: "+0.4",
    deltaPositive: true,
    icon: "sentiment_satisfied",
    bar: 96,
  },
];

const AGENTS = [
  {
    name: "Astra Support v2",
    type: "Customer Experience",
    icon: "smart_toy",
    status: "Active",
    efficiency: 92,
    last: "2 mins ago",
    isTraining: false,
  },
  {
    name: "Sales Lead Gen",
    type: "Outbound",
    icon: "support_agent",
    status: "Active",
    efficiency: 84,
    last: "15 mins ago",
    isTraining: false,
  },
  {
    name: "Data Analyst Core",
    type: "Internal Analytics",
    icon: "analytics",
    status: "Training",
    efficiency: 45,
    last: "1 hour ago",
    isTraining: true,
  },
];

// ── Component ────────────────────────────────────────────────────────────────

export default function Dashboard() {
  const [, setLocation] = useLocation();
  const { isDark } = useTheme();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const c = (light: string, dark: string) => (isDark ? dark : light);

  const statusBadge = (isTraining: boolean) =>
    `inline-flex items-center gap-2 py-1.5 px-3 rounded-full text-[11px] font-bold uppercase tracking-wider border shadow-sm ${
      isTraining
        ? isDark
          ? "bg-white/5 border-white/10 text-white/60"
          : "bg-[#F5F5F7] border-black/10 text-[#1c1c1e]"
        : "bg-[#EBDCFF] border-[#EBDCFF] text-[#1c1c1e]"
    }`;

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
            <h1
              className={`text-[2rem] sm:text-[2.5rem] lg:text-[3.2rem] font-bold tracking-tight leading-none mb-3 ${
                c("text-[#1c1c1e]", "text-white")
              }`}
              style={{ fontFamily: "'Playfair Display', serif" }}
            >
              Good morning, <span className="italic font-normal">Admin</span> 👋
            </h1>
            <p
              className={`text-base sm:text-lg max-w-2xl font-medium ${
                c("text-[#1c1c1e]/60", "text-white/50")
              }`}
            >
              Your AI agents are handling 2,400+ concurrent requests.
              System latency is optimal and all channels are active.
            </p>
          </div>

          {/* ── KPI Cards ── */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6 mb-8 md:mb-12">
            {KPI_CARDS.map((card) => (
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
                        ? "bg-white/5 border-white/10 text-white"
                        : "bg-white border-black/5 text-[#1c1c1e]"
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

            {/* ── Mobile: Card list (< md) ── */}
            <div className="divide-y md:hidden divide-white/[0.04]">
              {AGENTS.map((bot) => (
                <div
                  key={bot.name}
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
                    <span className="material-symbols-outlined text-[20px]">{bot.icon}</span>
                  </div>

                  {/* Name + type */}
                  <div className="flex-1 min-w-0">
                    <p className={`text-[14px] font-bold truncate ${c("text-[#1c1c1e]", "text-white")}`}>
                      {bot.name}
                    </p>
                    <p className={`text-[12px] font-medium ${c("text-[#1c1c1e]/50", "text-white/40")}`}>
                      {bot.type}
                    </p>
                    {/* Efficiency bar */}
                    <div className="mt-2 flex items-center gap-2">
                      <div className={`flex-1 h-1.5 rounded-full overflow-hidden ${c("bg-black/5", "bg-white/10")}`}>
                        <div
                          className={`h-full rounded-full ${c("bg-[#1c1c1e]", "bg-[#EBDCFF]")}`}
                          style={{ width: `${bot.efficiency}%` }}
                        />
                      </div>
                      <span className={`text-[11px] font-bold flex-shrink-0 ${c("text-[#1c1c1e]", "text-white")}`}>
                        {bot.efficiency}%
                      </span>
                    </div>
                  </div>

                  {/* Status + last active */}
                  <div className="flex flex-col items-end gap-2 flex-shrink-0">
                    <span className={statusBadge(bot.isTraining)}>
                      <span className="w-1.5 h-1.5 rounded-full animate-pulse bg-current" />
                      {bot.status}
                    </span>
                    <span className={`text-[11px] font-medium ${c("text-[#1c1c1e]/40", "text-white/30")}`}>
                      {bot.last}
                    </span>
                  </div>
                </div>
              ))}
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
                  {AGENTS.map((bot) => (
                    <tr
                      key={bot.name}
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
                            <span className="material-symbols-outlined text-[20px]">{bot.icon}</span>
                          </div>
                          <div>
                            <p
                              className={`text-[15px] font-bold transition-colors ${
                                isDark
                                  ? "text-white group-hover:text-[#EBDCFF]"
                                  : "text-[#1c1c1e] group-hover:text-black"
                              }`}
                            >
                              {bot.name}
                            </p>
                            <p className={`text-[13px] font-medium ${c("text-[#1c1c1e]/50", "text-white/40")}`}>
                              {bot.type}
                            </p>
                          </div>
                        </div>
                      </td>

                      {/* Status */}
                      <td className="px-8 py-5">
                        <span className={statusBadge(bot.isTraining)}>
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
                              {bot.efficiency}%
                            </span>
                          </div>
                          <div
                            className={`w-full h-2 rounded-full overflow-hidden shadow-inner ${
                              c("bg-[#F5F5F7] border border-black/5", "bg-white/10")
                            }`}
                          >
                            <div
                              className={`h-full rounded-full ${c("bg-[#1c1c1e]", "bg-[#EBDCFF]")}`}
                              style={{ width: `${bot.efficiency}%` }}
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
                        {bot.last}
                      </td>

                      {/* Actions */}
                      <td className="px-8 py-5 text-right">
                        <button
                          aria-label={`More options for ${bot.name}`}
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
                  ))}
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
                Showing {AGENTS.length} of {AGENTS.length} agents
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
          </div>

        </main>
      </div>
    </div>
  );
}
