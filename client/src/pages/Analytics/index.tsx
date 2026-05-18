import { useTheme } from "../../contexts/ThemeContext";
import Sidebar from "../../components/Sidebar";
import TopBar from "../../components/TopBar";
import KPIs from "./components/KPIs";
import VolumeChart from "./components/VolumeChart";
import LanguageMix from "./components/LanguageMix";
import ChannelPerf from "./components/ChannelPerf";
import InteractionsTable from "./components/InteractionsTable";

export default function Analytics() {
  const { isDark } = useTheme();
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
          <KPIs />

          {/* Chart Area */}
          <VolumeChart />

          {/* Bottom Row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            {/* Language Mix */}
            <LanguageMix />

            {/* Channel Performance */}
            <ChannelPerf />
          </div>

          {/* Recent Interactions Table */}
          <InteractionsTable />
        </main>
      </div>
    </div>
  );
}
