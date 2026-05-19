import { useState } from "react";
import { useTheme } from "../contexts/ThemeContext";
import Sidebar from "../components/Sidebar";
import TopBar from "../components/TopBar";

export default function Models() {
  const { isDark } = useTheme();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  
  const c = (light: string, dark: string) => (isDark ? dark : light);

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
              className={`px-4 py-2 rounded-xl border transition-[color,background-color,border-color,box-shadow] duration-200 text-[13px] font-bold flex items-center gap-1.5 shadow-sm focus-visible:ring-2 outline-none ${
                isDark
                  ? "bg-[#EBDCFF]/10 border-[#EBDCFF]/20 text-[#EBDCFF] hover:bg-[#EBDCFF]/20 focus-visible:ring-[#EBDCFF]/20"
                  : "bg-[#1c1c1e] border-[#1c1c1e] text-[#F5F5F7] hover:bg-black focus-visible:ring-black/20"
              }`}
            >
              <span className="material-symbols-outlined text-[18px]" aria-hidden="true">add</span>
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
                  className={`w-1.5 h-1.5 rounded-full animate-pulse ${
                    c("bg-[#1c1c1e]", "bg-[#EBDCFF]")
                  }`}
                ></div>
                <span
                  className={`text-[10px] font-bold uppercase tracking-widest ${
                    c("text-[#1c1c1e]", "text-[#EBDCFF]")
                  }`}
                >
                  Live
                </span>
              </div>
            </div>

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
                {/* Desktop arrow */}
                <div className="hidden md:flex items-center">
                  <div className={`w-10 h-[2px] ${c("bg-black/10", "bg-white/10")}`}></div>
                  <span className={`material-symbols-outlined text-[20px] ${c("text-black/30", "text-white/30")}`} aria-hidden="true">
                    arrow_forward
                  </span>
                </div>
                {/* Mobile arrow */}
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
                  <span className="material-symbols-outlined" aria-hidden="true">hub</span>
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
                {/* Desktop arrow */}
                <div className="hidden md:flex items-center">
                  <div className={`w-10 h-[2px] ${c("bg-black/10", "bg-white/10")}`}></div>
                  <span className={`material-symbols-outlined text-[20px] ${c("text-black/30", "text-white/30")}`} aria-hidden="true">
                    arrow_forward
                  </span>
                </div>
                {/* Mobile arrow */}
                <span className={`material-symbols-outlined text-[24px] md:hidden ${c("text-black/30", "text-white/30")}`} aria-hidden="true">
                  arrow_downward
                </span>
              </div>

              {/* Destination Nodes */}
              <div className="flex flex-col gap-3 w-full md:w-auto">
                {[
                  { label: "General Inquiries", model: "GPT-4o-mini", icon: "speed" },
                  { label: "Complex Problems", model: "Claude 3.5 Sonnet", icon: "psychology_alt" },
                  { label: "Image Analysis", model: "Gemini 1.5 Pro", icon: "image_search" },
                ].map((dest) => (
                  <button
                    key={dest.label}
                    type="button"
                    className={`rounded-2xl px-5 py-4 flex items-center justify-between gap-8 border shadow-sm text-left w-full md:w-64 outline-none transition-[border-color,box-shadow,background-color] duration-200 cursor-pointer focus-visible:ring-2 ${
                      isDark
                        ? "bg-[#131317] border-white/[0.04] hover:border-white/20 focus-visible:ring-[#EBDCFF]/20"
                        : "bg-[#F5F5F7] border-black/5 hover:border-black/20 focus-visible:ring-black/20"
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
                  </button>
                ))}
              </div>
            </div>
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
                  { label: "Latency Tolerance", value: "1200ms", pct: 40, color: c("#1c1c1e", "#EBDCFF") },
                  { label: "Cost Optimization", value: "Aggressive", pct: 80, color: c("rgba(0,0,0,0.3)", "rgba(255,255,255,0.4)") },
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
                    <div
                      className={`w-full h-2 rounded-full overflow-hidden ${
                        c("bg-black/5", "bg-[#131317]")
                      }`}
                    >
                      <div
                        className="h-full rounded-full"
                        style={{ width: `${s.pct}%`, backgroundColor: s.color }}
                      ></div>
                    </div>
                  </div>
                ))}

                <div className={`pt-6 mt-6 border-t ${c("border-black/5", "border-white/[0.06]")}`}>
                  {[
                    { label: "Auto-Failover", sub: "Switch if provider fails", enabled: true },
                    { label: "Response Caching", sub: "Cache repeated questions", enabled: false },
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
                        className={`w-12 h-6 rounded-full relative cursor-pointer outline-none transition-[background-color,box-shadow] duration-200 focus-visible:ring-2 focus-visible:ring-offset-2 ${
                          isDark 
                            ? "focus-visible:ring-offset-[#1f1f23] focus-visible:ring-[#EBDCFF]" 
                            : "focus-visible:ring-offset-white focus-visible:ring-[#1c1c1e]"
                        } ${
                          toggle.enabled
                            ? (isDark ? "bg-[#EBDCFF]" : "bg-[#1c1c1e]")
                            : (isDark ? "bg-[#353439]" : "bg-black/10")
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
                  3 providers connected
                </p>
              </div>
              
              <div className="overflow-x-auto">
                <table className="w-full text-left">
                  <thead>
                    <tr className={isDark ? "bg-black/20" : "bg-[#F5F5F7]/50"}>
                      {["Provider", "Model Version", "Status", ""].map((h) => (
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
                    {[
                      {
                        provider: "OpenAI",
                        logo: "○",
                        logoBg: isDark ? "#fff" : "#1c1c1e",
                        logoColor: isDark ? "#000" : "#fff",
                        model: "gpt-4o-mini-2024-07-18",
                        active: true,
                      },
                      {
                        provider: "Anthropic",
                        logo: "A",
                        logoBg: "#D97757",
                        logoColor: "#fff",
                        model: "claude-3-5-sonnet-20240620",
                        active: true,
                      },
                      {
                        provider: "Google",
                        logo: "G",
                        logoBg: "#4285F4",
                        logoColor: "#fff",
                        model: "gemini-1.5-pro-latest",
                        active: false,
                      },
                    ].map((b) => (
                      <tr
                        key={b.provider}
                        className={`transition-colors ${
                          isDark ? "hover:bg-white/[0.02]" : "hover:bg-black/[0.02]"
                        }`}
                      >
                        <td className="px-4 sm:px-8 py-4 sm:py-6">
                          <div className="flex items-center gap-4">
                            <div
                              className="w-10 h-10 rounded-xl flex items-center justify-center text-[16px] font-bold shadow-sm"
                              style={{ backgroundColor: b.logoBg, color: b.logoColor }}
                            >
                              {b.logo}
                            </div>
                            <span
                              className={`text-[15px] font-bold ${
                                c("text-[#1c1c1e]", "text-white")
                              }`}
                            >
                              {b.provider}
                            </span>
                          </div>
                        </td>
                        <td
                          className={`px-4 sm:px-8 py-4 sm:py-6 text-[13px] font-mono font-medium ${
                            c("text-[#1c1c1e]/60", "text-[#bbcac0]")
                          }`}
                        >
                          {b.model}
                        </td>
                        <td className="px-4 sm:px-8 py-4 sm:py-6">
                          {b.active ? (
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
                          <button
                            aria-label={`Configure settings for ${b.provider}`}
                            className={`w-10 h-10 flex items-center justify-center rounded-xl transition-[color,background-color,border-color,box-shadow] duration-200 outline-none border focus-visible:ring-2 ${
                              isDark
                                ? "text-white/30 hover:text-white hover:bg-white/5 border-transparent hover:border-white/10 focus-visible:ring-[#EBDCFF]/20"
                                : "text-[#1c1c1e]/40 hover:text-[#1c1c1e] hover:bg-black/5 border-transparent hover:border-black/5 focus-visible:ring-[#1c1c1e]/20"
                            }`}
                          >
                            <span className="material-symbols-outlined text-[20px]" aria-hidden="true">settings</span>
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
