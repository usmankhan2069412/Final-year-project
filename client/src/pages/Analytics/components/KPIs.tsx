import { useEffect, useState } from "react";
import { useTheme } from "../../../contexts/ThemeContext";

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

export default function KPIs() {
  const { isDark } = useTheme();
  const c = (light: string, dark: string) => (isDark ? dark : light);
  const [data, setData] = useState<KPIResponseData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchKPIs() {
      try {
        const token = localStorage.getItem("token");
        const headers: Record<string, string> = {
          "Content-Type": "application/json",
        };
        if (token) {
          headers["Authorization"] = `Bearer ${token}`;
        }
        const response = await fetch("http://localhost:8000/api/v1/analytics/kpi", {
          headers,
        });
        if (response.ok) {
          const json = await response.json();
          setData(json);
        }
      } catch (err) {
        console.error("Error fetching KPIs:", err);
      } finally {
        setLoading(false);
      }
    }
    fetchKPIs();
  }, []);

  const formatConversations = (val: number) => {
    if (val >= 1000) {
      return { value: (val / 1000).toFixed(1), unit: "k" };
    }
    return { value: val.toString(), unit: "" };
  };

  const getDelta = (pct: number, fallback: string) => {
    if (pct === 0) return fallback;
    return `${pct >= 0 ? "+" : ""}${pct.toFixed(0)}%`;
  };

  const kpis = [
    {
      label: "Total Conversations",
      value: data ? formatConversations(data.total_conversations.value).value : "...",
      unit: data ? formatConversations(data.total_conversations.value).unit : "",
      delta: data ? getDelta(data.total_conversations.change_pct, "+0%") : "...",
      icon: "forum",
      bar: data ? Math.min(100, Math.max(10, Math.round(50 + data.total_conversations.change_pct))) : 50,
    },
    {
      label: "Avg. Response Time",
      value: data ? data.avg_response_time.value.toFixed(1) : "...",
      unit: "s",
      delta: data ? getDelta(data.avg_response_time.change_pct, "0%") : "...",
      icon: "timer",
      bar: data ? Math.max(10, Math.min(100, Math.round(100 - (data.avg_response_time.value * 20)))) : 40,
    },
    {
      label: "User Satisfaction",
      value: data ? data.satisfaction_score.value.toFixed(1) : "...",
      unit: "/5",
      delta: data ? getDelta(data.satisfaction_score.change_pct, "Optimal") : "...",
      icon: "sentiment_satisfied",
      bar: data ? Math.round((data.satisfaction_score.value / 5) * 100) : 80,
    },
    {
      label: "Workload Reduction",
      value: data ? data.workload_reduction.value.toFixed(0) : "...",
      unit: "%",
      delta: data ? getDelta(data.workload_reduction.change_pct, "Target") : "...",
      icon: "bolt",
      bar: data ? Math.round(data.workload_reduction.value) : 70,
    },
  ];

  if (loading) {
    return (
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6 mb-10">
        {[1, 2, 3, 4].map((i) => (
          <div
            key={i}
            className={`rounded-3xl border p-4 sm:p-6 relative overflow-hidden animate-pulse ${
              isDark ? "bg-[#1f1f23] border-white/[0.06]" : "bg-white border-black/5"
            }`}
          >
            <div className="flex justify-between items-start mb-6">
              <div className={`w-12 h-12 rounded-xl ${isDark ? "bg-white/5" : "bg-black/5"}`} />
              <div className={`w-12 h-6 rounded-full ${isDark ? "bg-white/5" : "bg-black/5"}`} />
            </div>
            <div className={`w-2/3 h-3 rounded-full mb-3 ${isDark ? "bg-white/5" : "bg-black/5"}`} />
            <div className={`w-1/2 h-8 rounded-lg mb-4 ${isDark ? "bg-white/5" : "bg-black/5"}`} />
            <div className={`w-full h-1.5 rounded-full ${isDark ? "bg-white/5" : "bg-black/5"}`} />
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6 mb-10">
      {kpis.map((card) => (
        <div
          key={card.label}
          className={`rounded-3xl border p-4 sm:p-6 transition-[border-color,box-shadow] duration-300 group relative overflow-hidden ${
            isDark
              ? "bg-[#1f1f23] border-white/[0.06] hover:border-white/10 shadow-none"
              : "bg-white border-black/5 shadow-[0_8px_30px_rgb(0,0,0,0.02)] hover:shadow-[0_8px_40px_rgb(0,0,0,0.06)]"
          }`}
        >
          {/* Decorative blob */}
          <div className="absolute -right-6 -top-6 w-24 h-24 bg-[#EBDCFF] rounded-full opacity-20 group-hover:scale-150 transition-transform duration-500 pointer-events-none"></div>

          <div className="flex items-start justify-between mb-6 relative z-10">
            <div className="w-12 h-12 rounded-xl flex items-center justify-center bg-[#EBDCFF] text-[#1c1c1e] shadow-inner">
              <span className="material-symbols-outlined text-[24px]" aria-hidden="true">
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
              className={`text-[1.8rem] sm:text-[2.5rem] font-serif font-bold mb-4 tracking-tight flex items-baseline leading-none ${
                c("text-[#1c1c1e]", "text-white")
              }`}
              style={{ fontFamily: "'Playfair Display', serif" }}
            >
              <span>{card.value}</span>
              {card.unit && (
                <span className={`font-sans text-xl font-bold ml-0.5 tracking-normal ${c("text-[#1c1c1e]/50", "text-white/40")}`}>
                  {card.unit}
                </span>
              )}
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
  );
}
