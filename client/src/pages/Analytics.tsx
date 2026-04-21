import { useTheme } from "../contexts/ThemeContext";
import Sidebar from "../components/Sidebar";
import TopBar from "../components/TopBar";

export default function Analytics() {
  const { isDark } = useTheme();
  
  // Conditionally pick class based on theme
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

        <TopBar
          searchPlaceholder="Search analytics data..."
          actions={
            <button
              className={`px-4 py-2 rounded-xl border transition-all text-[13px] font-bold flex items-center gap-1.5 shadow-sm ${
                isDark
                  ? "border-white/10 bg-transparent hover:bg-white/[0.04] text-[#bbcac0] hover:text-white"
                  : "border-black/5 bg-white hover:bg-black/5 text-[#1c1c1e]"
              }`}
            >
              <span className="material-symbols-outlined text-[18px]">download</span>
              Export
            </button>
          }
        />

        <main className="flex-1 overflow-y-auto p-8 lg:p-12 z-10">
          <div className="mb-12">
            <span
              className={`text-[11px] font-bold tracking-[0.2em] uppercase mb-3 block ${
                c("text-[#1c1c1e]/40", "text-white/30")
              }`}
            >
              Intelligence
            </span>
            <h1
              className={`text-[2.5rem] lg:text-[3.5rem] font-bold tracking-tight leading-none mb-3 ${
                c("text-[#1c1c1e]", "text-white")
              }`}
              style={{ fontFamily: "'Playfair Display', serif" }}
            >
              Performance Analytics
            </h1>
            <p
              className={`text-lg max-w-2xl font-medium ${
                c("text-[#1c1c1e]/60", "text-white/50")
              }`}
            >
              Real-time insights across all active agents and conversation clusters.
            </p>
          </div>

          {/* KPI Row */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-10">
            {[
              {
                label: "Total Conversations",
                value: "42.8k",
                delta: "+12%",
                icon: "forum",
                bar: 60,
              },
              {
                label: "Avg. Response Time",
                value: "1.4s",
                delta: "-0.2s",
                icon: "timer",
                bar: 40,
              },
              {
                label: "User Satisfaction",
                value: "88%",
                delta: "Optimal",
                icon: "sentiment_satisfied",
                bar: 88,
              },
              {
                label: "Workload Reduction",
                value: "70%",
                delta: "Target",
                icon: "bolt",
                bar: 70,
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
                  
                  <div className={`w-full h-1.5 rounded-full overflow-hidden ${c("bg-black/5", "bg-white/10")}`}>
                    <div
                      className={`h-full rounded-full ${c("bg-[#1c1c1e]", "bg-[#EBDCFF]")}`}
                      style={{ width: `${card.bar}%` }}
                    ></div>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Chart Area */}
          <div
            className={`rounded-[2rem] border p-8 mb-6 ${
              isDark
                ? "bg-[#1f1f23] border-white/[0.06]"
                : "bg-white border-black/5 shadow-[0_8px_30px_rgb(0,0,0,0.02)]"
            }`}
          >
            <div className="flex flex-col md:flex-row items-start md:items-center justify-between mb-8 gap-4">
              <div>
                <h2
                  className={`text-[20px] font-serif font-bold ${
                    c("text-[#1c1c1e]", "text-white")
                  }`}
                  style={{ fontFamily: "'Playfair Display', serif" }}
                >
                  Conversation Volume
                </h2>
                <p
                  className={`text-[13px] font-medium mt-1 ${
                    c("text-[#1c1c1e]/50", "text-white/40")
                  }`}
                >
                  Daily interaction metrics across all clusters
                </p>
              </div>
              <div className="flex items-center gap-6">
                <div className="flex items-center gap-2">
                  <div className={`w-2 h-2 rounded-full ${c("bg-[#1c1c1e]", "bg-[#EBDCFF]")}`}></div>
                  <span
                    className={`text-[10px] font-bold uppercase tracking-[0.15em] ${
                      c("text-[#1c1c1e]/50", "text-[#85948b]")
                    }`}
                  >
                    Successful
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <div className={`w-2 h-2 rounded-full ${c("bg-black/20", "bg-white/30")}`}></div>
                  <span
                    className={`text-[10px] font-bold uppercase tracking-[0.15em] ${
                      c("text-[#1c1c1e]/50", "text-[#85948b]")
                    }`}
                  >
                    Handovers
                  </span>
                </div>
                <select
                  className={`border rounded-xl px-4 py-2.5 text-[13px] font-medium outline-none shadow-sm cursor-pointer ${
                    isDark
                      ? "bg-[#131317] border-white/[0.06] text-white/80"
                      : "bg-[#fbfbf2] border-black/5 text-[#1c1c1e]/80 focus:border-black/20"
                  }`}
                >
                  <option>Last 30 Days</option>
                  <option>Last 7 Days</option>
                  <option>Last 90 Days</option>
                </select>
              </div>
            </div>

            {/* Mock Chart */}
            <div className="relative w-full h-64">
              <div className="absolute inset-0 flex flex-col justify-between pb-0">
                {["2k", "1.5k", "1k", "0.5k", "0"].map((v) => (
                  <div key={v} className="flex items-center gap-4">
                    <span
                      className={`text-[11px] font-medium w-8 text-right ${
                        c("text-[#1c1c1e]/40", "text-white/30")
                      }`}
                    >
                      {v}
                    </span>
                    <div className={`flex-1 h-px ${c("bg-black/[0.03]", "bg-white/[0.03]")}`}></div>
                  </div>
                ))}
              </div>
              <div className="absolute inset-0 pl-12">
                <svg
                  className="w-full h-full"
                  preserveAspectRatio="none"
                  viewBox="0 0 1000 200"
                >
                  <defs>
                    <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor={isDark ? "#EBDCFF" : "#1c1c1e"} stopOpacity="0.15" />
                      <stop offset="100%" stopColor={isDark ? "#EBDCFF" : "#1c1c1e"} stopOpacity="0" />
                    </linearGradient>
                  </defs>
                  {/* Area fill */}
                  <path
                    d="M0,160 C200,130 400,80 600,80 C700,80 800,110 900,80 L1000,40 L1000,200 L0,200 Z"
                    fill="url(#areaGrad)"
                  />
                  {/* Line */}
                  <path
                    d="M0,160 C200,130 400,80 600,80 C700,80 800,110 900,80 L1000,40"
                    fill="none"
                    stroke={isDark ? "#EBDCFF" : "#1c1c1e"}
                    strokeWidth="3"
                    strokeLinecap="round"
                    vectorEffect="non-scaling-stroke"
                  />
                  {/* Handovers line */}
                  <path
                    d="M0,180 C300,160 400,190 1000,140"
                    fill="none"
                    stroke={isDark ? "rgba(255,255,255,0.3)" : "rgba(0,0,0,0.2)"}
                    strokeWidth="2.5"
                    strokeDasharray="8,6"
                    vectorEffect="non-scaling-stroke"
                  />
                  {/* Peak dot */}
                  <circle
                    cx="800"
                    cy="110"
                    r="5"
                    fill={isDark ? "#1f1f23" : "#fff"}
                    stroke={isDark ? "#EBDCFF" : "#1c1c1e"}
                    strokeWidth="3"
                    vectorEffect="non-scaling-stroke"
                  />
                </svg>
              </div>
            </div>

            <div className="flex justify-between mt-5 pl-12">
              {["Jan 1", "Jan 8", "Jan 15", "Jan 22", "Jan 29"].map((d) => (
                <span
                  key={d}
                  className={`text-[11px] font-medium ${
                    c("text-[#1c1c1e]/40", "text-white/30")
                  }`}
                >
                  {d}
                </span>
              ))}
            </div>
          </div>

          {/* Bottom Row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            {/* Language Mix */}
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
                Language Mix
              </h3>
              <div className="flex items-center gap-10">
                <div className="relative w-32 h-32 flex-shrink-0">
                  <svg viewBox="0 0 36 36" className="w-full h-full -rotate-90 drop-shadow-sm">
                    <path
                      strokeDasharray="100, 100"
                      d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                      fill="none"
                      stroke={isDark ? "rgba(255,255,255,0.05)" : "rgba(0,0,0,0.05)"}
                      strokeWidth="5"
                    />
                    <path
                      strokeDasharray="65, 100"
                      d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                      fill="none"
                      stroke={isDark ? "#EBDCFF" : "#1c1c1e"}
                      strokeWidth="5"
                      strokeLinecap="round"
                    />
                    <path
                      strokeDasharray="35, 100"
                      strokeDashoffset="-65"
                      d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                      fill="none"
                      stroke={isDark ? "rgba(255,255,255,0.3)" : "rgba(0,0,0,0.2)"}
                      strokeWidth="5"
                      strokeLinecap="round"
                    />
                  </svg>
                  <div className="absolute inset-0 flex flex-col items-center justify-center">
                    <span
                      className={`text-[24px] font-bold ${
                        c("text-[#1c1c1e]", "text-white")
                      }`}
                    >
                      2
                    </span>
                    <span
                      className={`text-[9px] uppercase tracking-[0.2em] font-bold ${
                        c("text-[#1c1c1e]/40", "text-[#85948b]")
                      }`}
                    >
                      Langs
                    </span>
                  </div>
                </div>
                <div className="flex-1 space-y-5">
                  {[
                    { lang: "Roman Urdu", pct: 65, color: isDark ? "#EBDCFF" : "#1c1c1e" },
                    { lang: "English", pct: 35, color: isDark ? "rgba(255,255,255,0.3)" : "rgba(0,0,0,0.2)" },
                  ].map((l) => (
                    <div key={l.lang}>
                      <div className="flex justify-between mb-2">
                        <div className="flex items-center gap-2.5">
                          <div
                            className="w-2.5 h-2.5 rounded-full"
                            style={{ backgroundColor: l.color }}
                          ></div>
                          <span
                            className={`text-[14px] font-semibold ${
                              c("text-[#1c1c1e]", "text-white")
                            }`}
                          >
                            {l.lang}
                          </span>
                        </div>
                        <span
                          className={`text-[14px] font-bold ${
                            c("text-[#1c1c1e]", "text-white")
                          }`}
                        >
                          {l.pct}%
                        </span>
                      </div>
                      <div
                        className={`w-full h-1.5 rounded-full overflow-hidden ${
                          c("bg-black/5", "bg-[#131317]")
                        }`}
                      >
                        <div
                          className="h-full rounded-full"
                          style={{ width: `${l.pct}%`, backgroundColor: l.color }}
                        ></div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Channel Performance */}
            <div
              className={`rounded-[2rem] border p-8 ${
                isDark
                  ? "bg-[#1f1f23] border-white/[0.06]"
                  : "bg-white border-black/5 shadow-[0_8px_30px_rgb(0,0,0,0.02)]"
              }`}
            >
              <div className="flex items-center justify-between mb-8">
                <h3
                  className={`text-[18px] font-serif font-bold ${
                    c("text-[#1c1c1e]", "text-white")
                  }`}
                  style={{ fontFamily: "'Playfair Display', serif" }}
                >
                  Channel Performance
                </h3>
                <span
                  className={`text-[10px] px-3 py-1.5 rounded-full font-bold tracking-widest uppercase border shadow-sm ${
                    isDark
                      ? "bg-white/5 border-white/10 text-[#EBDCFF]"
                      : "bg-[#EBDCFF]/30 border-[#EBDCFF]/50 text-[#1c1c1e]"
                  }`}
                >
                  Live
                </span>
              </div>
              <div className="space-y-6">
                {[
                  { name: "WhatsApp", icon: "chat", pct: 78, color: isDark ? "#EBDCFF" : "#1c1c1e" },
                  { name: "Web Portal", icon: "language", pct: 22, color: isDark ? "rgba(255,255,255,0.3)" : "rgba(0,0,0,0.2)" },
                ].map((ch) => (
                  <div key={ch.name}>
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-3">
                        <span
                          className={`material-symbols-outlined text-[18px] ${
                            c("text-[#1c1c1e]/50", "text-[#85948b]")
                          }`}
                        >
                          {ch.icon}
                        </span>
                        <span
                          className={`text-[14px] font-bold ${
                            c("text-[#1c1c1e]", "text-white")
                          }`}
                        >
                          {ch.name}
                        </span>
                      </div>
                      <span
                        className={`text-[13px] font-bold ${
                          c("text-[#1c1c1e]", "text-white")
                        }`}
                      >
                        {ch.pct}%
                      </span>
                    </div>
                    <div
                      className={`w-full h-1.5 rounded-full overflow-hidden ${
                        c("bg-black/5", "bg-[#131317]")
                      }`}
                    >
                      <div
                        className="h-full rounded-full"
                        style={{ width: `${ch.pct}%`, backgroundColor: ch.color }}
                      ></div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Recent Interactions Table */}
          <div
            className={`rounded-[2rem] border overflow-hidden ${
              isDark
                ? "bg-[#1f1f23] border-white/[0.06]"
                : "bg-white border-black/5 shadow-[0_8px_30px_rgb(0,0,0,0.02)]"
            }`}
          >
            <div
              className={`flex flex-col sm:flex-row items-center justify-between px-8 py-6 border-b gap-4 ${
                c("border-black/5", "border-white/[0.06]")
              }`}
            >
              <h3
                className={`text-[20px] font-serif font-bold ${
                  c("text-[#1c1c1e]", "text-white")
                }`}
                style={{ fontFamily: "'Playfair Display', serif" }}
              >
                Recent Interactions
              </h3>
              <button
                className={`text-[13px] font-bold transition-colors flex items-center gap-1.5 ${
                  c("text-[#1c1c1e] hover:text-[#1c1c1e]/70", "text-[#EBDCFF] hover:text-white")
                }`}
              >
                View All Directory
                <span className="material-symbols-outlined text-[16px]">arrow_forward</span>
              </button>
            </div>
            
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className={isDark ? "bg-black/20" : "bg-[#fbfbf2]/50"}>
                    {["Conversation ID", "Status", "Agent Focus", "Timestamp", ""].map((h) => (
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
                <tbody className={isDark ? "divide-y divide-white/[0.04]" : "divide-y divide-black/5"}>
                  {[
                    {
                      id: "#AIN-4921-X",
                      status: "Ongoing",
                      statusColor: isDark ? "#EBDCFF" : "#1c1c1e",
                      focus: "Technical Inquiry",
                      time: "2 mins ago",
                    },
                    {
                      id: "#AIN-4918-B",
                      status: "Resolved",
                      statusColor: isDark ? "rgba(255,255,255,0.4)" : "rgba(0,0,0,0.3)",
                      focus: "Account Recovery",
                      time: "14 mins ago",
                    },
                    {
                      id: "#AIN-4915-Z",
                      status: "Resolved",
                      statusColor: isDark ? "rgba(255,255,255,0.4)" : "rgba(0,0,0,0.3)",
                      focus: "Policy Update",
                      time: "28 mins ago",
                    },
                  ].map((row) => (
                    <tr
                      key={row.id}
                      className={`transition-colors ${
                        isDark ? "hover:bg-white/[0.02]" : "hover:bg-black/[0.02]"
                      }`}
                    >
                      <td
                        className={`px-8 py-5 font-mono text-[13px] font-bold ${
                          c("text-[#1c1c1e]", "text-[#EBDCFF]")
                        }`}
                      >
                        {row.id}
                      </td>
                      <td className="px-8 py-5">
                        <div className="flex items-center gap-3">
                          <div
                            className="w-2 h-2 rounded-full shadow-sm"
                            style={{ backgroundColor: row.statusColor }}
                          ></div>
                          <span
                            className={`text-[13px] font-semibold ${
                              c("text-[#1c1c1e]", "text-white")
                            }`}
                          >
                            {row.status}
                          </span>
                        </div>
                      </td>
                      <td
                        className={`px-8 py-5 text-[14px] font-medium ${
                          c("text-[#1c1c1e]/70", "text-[#bbcac0]")
                        }`}
                      >
                        {row.focus}
                      </td>
                      <td
                        className={`px-8 py-5 text-[13px] font-medium whitespace-nowrap ${
                          c("text-[#1c1c1e]/50", "text-white/40")
                        }`}
                      >
                        {row.time}
                      </td>
                      <td className="px-8 py-5 text-right">
                        <button
                          className={`w-9 h-9 flex items-center justify-center rounded-xl transition-all outline-none border ${
                            isDark
                              ? "text-white/30 hover:text-white hover:bg-white/5 border-transparent hover:border-white/10"
                              : "text-[#1c1c1e]/40 hover:text-[#1c1c1e] hover:bg-black/5 border-transparent hover:border-black/5"
                          }`}
                        >
                          <span className="material-symbols-outlined text-[18px]">more_horiz</span>
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
