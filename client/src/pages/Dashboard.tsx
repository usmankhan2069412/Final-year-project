import { useLocation } from "wouter";
import Sidebar from "../components/Sidebar";
import TopBar from "../components/TopBar";
import { useTheme } from "../contexts/ThemeContext";

export default function Dashboard() {
  const [, setLocation] = useLocation();
  const { isDark } = useTheme();

  // ── Utility: conditional class helper ──
  const c = (light: string, dark: string) => (isDark ? dark : light);

  return (
    <div
      className={`min-h-screen flex font-sans selection:bg-[#EBDCFF] selection:text-[#1c1c1e] transition-colors duration-300 ${
        isDark ? "bg-[#131317] text-[#e4e1e7]" : "bg-[#fbfbf2] text-[#1c1c1e]"
      }`}
    >
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0 overflow-hidden relative">
        {/* Ambient glow */}
        <div
          className={`absolute top-0 right-0 w-[500px] h-[500px] rounded-full blur-3xl pointer-events-none transition-opacity duration-500 ${
            isDark
              ? "bg-[#EBDCFF] opacity-5 mix-blend-screen"
              : "bg-[#EBDCFF] opacity-20 mix-blend-multiply"
          }`}
        ></div>

        <TopBar searchPlaceholder="Search agents, workflows, knowledge..." />

        <main className="flex-1 overflow-y-auto p-8 lg:p-12 z-10">
          {/* ── Welcome Header ── */}
          <div className="mb-12">
            <span
              className={`text-[11px] font-bold tracking-[0.2em] uppercase mb-3 block ${
                c("text-[#1c1c1e]/40", "text-white/30")
              }`}
            >
              Overview
            </span>
            <h1
              className={`text-[2.5rem] lg:text-[3.5rem] font-bold tracking-tight leading-none mb-3 ${
                c("text-[#1c1c1e]", "text-white")
              }`}
              style={{ fontFamily: "'Playfair Display', serif" }}
            >
              Good morning, <span className="italic font-normal">Admin</span> 👋
            </h1>
            <p
              className={`text-lg max-w-2xl font-medium ${
                c("text-[#1c1c1e]/60", "text-white/50")
              }`}
            >
              Your AI agents are currently handling 2,400+ concurrent requests.
              System latency is optimal and all channels are active.
            </p>
          </div>

          {/* ── KPI Cards ── */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
            {[
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
            ].map((card) => (
              <div
                key={card.label}
                className={`rounded-3xl border p-6 transition-all group relative overflow-hidden ${
                  isDark
                    ? "bg-[#1f1f23] border-white/[0.06] hover:border-white/10 shadow-none"
                    : "bg-white border-black/5 shadow-[0_8px_30px_rgb(0,0,0,0.02)] hover:shadow-[0_8px_40px_rgb(0,0,0,0.06)]"
                }`}
              >
                {/* Decorative blob */}
                <div className="absolute -right-6 -top-6 w-24 h-24 bg-[#EBDCFF] rounded-full opacity-20 group-hover:scale-150 transition-transform duration-500 pointer-events-none"></div>

                <div className="flex items-start justify-between mb-6 relative z-10">
                  <div className="w-12 h-12 rounded-xl flex items-center justify-center bg-[#EBDCFF] text-[#1c1c1e] shadow-inner">
                    <span className="material-symbols-outlined text-[24px]">
                      {card.icon}
                    </span>
                  </div>
                  <span
                    className={`text-[12px] font-bold px-3 py-1.5 rounded-full border shadow-sm ${
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
                    className={`text-[11px] font-bold uppercase tracking-[0.15em] mb-1.5 ${
                      c("text-[#1c1c1e]/50", "text-white/40")
                    }`}
                  >
                    {card.label}
                  </p>
                  <h3
                    className={`text-[2rem] font-serif font-bold mb-4 tracking-tight ${
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
                      className={`h-full rounded-full ${
                        c("bg-[#1c1c1e]", "bg-[#EBDCFF]")
                      }`}
                      style={{ width: `${card.bar}%` }}
                    ></div>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* ── Active Agents Table ── */}
          <div
            className={`rounded-[2rem] border overflow-hidden transition-colors duration-300 ${
              isDark
                ? "bg-[#1f1f23] border-white/[0.06]"
                : "bg-white border-black/5 shadow-[0_8px_30px_rgb(0,0,0,0.02)]"
            }`}
          >
            {/* Table Header */}
            <div
              className={`flex flex-col sm:flex-row items-start sm:items-center justify-between px-8 py-6 gap-4 border-b ${
                c("border-black/5", "border-white/[0.06]")
              }`}
            >
              <div>
                <h2
                  className={`text-2xl font-serif font-bold ${
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
                className={`px-6 py-3 rounded-xl font-bold text-[14px] flex items-center gap-2 transition-all shadow-md hover:shadow-lg ${
                  isDark
                    ? "bg-[#EBDCFF] text-[#1c1c1e] hover:bg-[#d8bfff]"
                    : "bg-[#1c1c1e] text-[#fbfbf2] hover:bg-black"
                }`}
              >
                <span className="material-symbols-outlined text-[18px]">add</span>
                Deploy Agent
              </button>
            </div>

            {/* Table */}
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr
                    className={isDark ? "bg-black/20" : "bg-[#fbfbf2]/50"}
                  >
                    {["Agent Name", "Status", "Efficiency", "Last Active", ""].map(
                      (h) => (
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
                      )
                    )}
                  </tr>
                </thead>
                <tbody
                  className={isDark ? "divide-y divide-white/[0.04]" : "divide-y divide-black/5"}
                >
                  {[
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
                  ].map((bot) => (
                    <tr
                      key={bot.name}
                      className={`transition-colors cursor-pointer group ${
                        isDark
                          ? "hover:bg-white/[0.02]"
                          : "hover:bg-black/[0.02]"
                      }`}
                      onClick={() => setLocation("/builder")}
                    >
                      {/* Agent Name */}
                      <td className="px-8 py-6">
                        <div className="flex items-center gap-4">
                          <div
                            className={`w-12 h-12 rounded-2xl border flex items-center justify-center flex-shrink-0 transition-all ${
                              isDark
                                ? "bg-white/5 border-white/5 text-white/60 group-hover:bg-white/10"
                                : "bg-[#fbfbf2] border-black/5 text-[#1c1c1e] group-hover:bg-white group-hover:shadow-sm"
                            }`}
                          >
                            <span className="material-symbols-outlined text-[20px]">
                              {bot.icon}
                            </span>
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
                            <p
                              className={`text-[13px] font-medium ${
                                c("text-[#1c1c1e]/50", "text-white/40")
                              }`}
                            >
                              {bot.type}
                            </p>
                          </div>
                        </div>
                      </td>

                      {/* Status Badge */}
                      <td className="px-8 py-6">
                        <span
                          className={`inline-flex items-center gap-2 py-1.5 px-3 rounded-full text-[11px] font-bold uppercase tracking-wider border shadow-sm ${
                            bot.isTraining
                              ? isDark
                                ? "bg-white/5 border-white/10 text-white/60"
                                : "bg-[#fbfbf2] border-black/10 text-[#1c1c1e]"
                              : "bg-[#EBDCFF] border-[#EBDCFF] text-[#1c1c1e]"
                          }`}
                        >
                          <span className="w-1.5 h-1.5 rounded-full animate-pulse bg-current"></span>
                          {bot.status}
                        </span>
                      </td>

                      {/* Efficiency Bar */}
                      <td className="px-8 py-6">
                        <div className="w-32 lg:w-40">
                          <div className="flex justify-between text-[13px] mb-2 font-medium">
                            <span
                              className={c(
                                "text-[#1c1c1e]/50",
                                "text-white/40"
                              )}
                            >
                              Precision
                            </span>
                            <span
                              className={`font-bold ${
                                c("text-[#1c1c1e]", "text-white")
                              }`}
                            >
                              {bot.efficiency}%
                            </span>
                          </div>
                          <div
                            className={`w-full h-2 rounded-full overflow-hidden shadow-inner ${
                              c("bg-[#fbfbf2] border border-black/5", "bg-white/10")
                            }`}
                          >
                            <div
                              className={`h-full rounded-full ${
                                c("bg-[#1c1c1e]", "bg-[#EBDCFF]")
                              }`}
                              style={{ width: `${bot.efficiency}%` }}
                            ></div>
                          </div>
                        </div>
                      </td>

                      {/* Last Active */}
                      <td
                        className={`px-8 py-6 text-[13px] font-medium whitespace-nowrap ${
                          c("text-[#1c1c1e]/50", "text-white/40")
                        }`}
                      >
                        {bot.last}
                      </td>

                      {/* Actions */}
                      <td className="px-8 py-6 text-right">
                        <button
                          className={`w-10 h-10 flex items-center justify-center rounded-xl transition-all outline-none border ${
                            isDark
                              ? "text-white/30 hover:text-white hover:bg-white/5 border-transparent hover:border-white/10"
                              : "text-[#1c1c1e]/40 hover:text-[#1c1c1e] hover:bg-black/5 border-transparent hover:border-black/5"
                          }`}
                          onClick={(e) => e.stopPropagation()}
                        >
                          <span className="material-symbols-outlined text-[20px]">
                            more_horiz
                          </span>
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Table Footer */}
            <div
              className={`px-8 py-5 border-t flex justify-between items-center ${
                isDark
                  ? "bg-black/10 border-white/[0.06]"
                  : "bg-[#fbfbf2]/50 border-black/5"
              }`}
            >
              <span
                className={`text-[12px] font-medium ${
                  c("text-[#1c1c1e]/50", "text-white/30")
                }`}
              >
                Showing 3 of 3 agents
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
                <span className="material-symbols-outlined text-[16px]">
                  arrow_forward
                </span>
              </a>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
