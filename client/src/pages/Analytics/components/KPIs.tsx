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
  escalation_rate: KPIData;
}

interface VolumeDay {
  date: string;
  conversations: number;
  escalated_count: number;
}

interface KPIsProps {
  days: number;
  chatbotId: string;
}

// Tiny 7-point sparkline SVG
function Sparkline({ values, positive }: { values: number[]; positive: boolean }) {
  const { isDark } = useTheme();
  if (values.length < 2) return null;

  const w = 80;
  const h = 24;
  const max = Math.max(...values, 1);
  const min = Math.min(...values);
  const range = max - min || 1;

  const pts = values.map((v, i) => {
    const x = (i / (values.length - 1)) * w;
    const y = h - ((v - min) / range) * h;
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  });

  const color = positive
    ? isDark ? "#EBDCFF" : "#1c1c1e"
    : isDark ? "#fb7185" : "#e11d48";

  return (
    <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none" aria-hidden="true">
      <polyline
        points={pts.join(" ")}
        fill="none"
        stroke={color}
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        opacity="0.8"
      />
    </svg>
  );
}

export default function KPIs({ days, chatbotId }: KPIsProps) {
  const { isDark } = useTheme();
  const c = (light: string, dark: string) => (isDark ? dark : light);
  const [data, setData] = useState<KPIResponseData | null>(null);
  const [volumeData, setVolumeData] = useState<VolumeDay[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchAll() {
      setLoading(true);
      try {
        const token = localStorage.getItem("token");
        const headers: Record<string, string> = { "Content-Type": "application/json" };
        if (token) headers["Authorization"] = `Bearer ${token}`;

        const params = new URLSearchParams({ days: String(days) });
        if (chatbotId) params.set("chatbot_id", chatbotId);

        const [kpiRes, volRes] = await Promise.all([
          fetch(`http://localhost:8000/api/v1/analytics/kpi?${params}`, { headers }),
          fetch(`http://localhost:8000/api/v1/analytics/volume?${params}`, { headers }),
        ]);

        if (kpiRes.ok) setData(await kpiRes.json());
        if (volRes.ok) setVolumeData(await volRes.json());
      } catch (err) {
        console.error("Error fetching KPIs:", err);
      } finally {
        setLoading(false);
      }
    }
    fetchAll();
  }, [days, chatbotId]);

  const getDelta = (pct: number) => {
    return `${pct >= 0 ? "+" : ""}${pct.toFixed(1)}%`;
  };

  // Zero change_pct = neutral gray badge (no data yet or no change)
  const isNeutral = (pct: number) => pct === 0;

  // Build 7-point sparkline values from volume data (last 7 days)
  const recent = volumeData.slice(-7);
  const convSparkline = recent.map((d) => d.conversations);
  const escalSparkline = recent.map((d) =>
    d.conversations > 0 ? (d.escalated_count / d.conversations) * 100 : 0
  );
  const deflSparkline = recent.map((d) =>
    d.conversations > 0 ? ((d.conversations - d.escalated_count) / d.conversations) * 100 : 0
  );

  const kpis = [
    {
      id: "total-conversations",
      label: "Total Conversations",
      value: data
        ? data.total_conversations.value >= 1000
          ? `${(data.total_conversations.value / 1000).toFixed(1)}k`
          : String(Math.round(data.total_conversations.value))
        : "—",
      unit: "",
      delta: data ? getDelta(data.total_conversations.change_pct) : "+0.0%",
      isNeutralDelta: isNeutral(data?.total_conversations.change_pct ?? 0),
      isPositiveDelta: (data?.total_conversations.change_pct ?? 0) > 0,
      icon: "forum",
      sparkline: convSparkline,
      sparklinePositive: true,
    },
    {
      id: "deflection-rate",
      label: "Deflection Rate",
      value: data ? data.workload_reduction.value.toFixed(1) : "—",
      unit: "%",
      delta: data ? getDelta(data.workload_reduction.change_pct) : "+0.0%",
      isNeutralDelta: isNeutral(data?.workload_reduction.change_pct ?? 0),
      isPositiveDelta: (data?.workload_reduction.change_pct ?? 0) > 0,
      icon: "bolt",
      sparkline: deflSparkline,
      sparklinePositive: true,
      tooltip: "% of resolved/escalated outcomes resolved without human escalation",
    },
    {
      id: "escalation-rate",
      label: "Escalation Rate",
      value: data ? data.escalation_rate.value.toFixed(1) : "—",
      unit: "%",
      delta: data ? getDelta(data.escalation_rate.change_pct) : "+0.0%",
      isNeutralDelta: isNeutral(data?.escalation_rate.change_pct ?? 0),
      // Lower escalation is better — positive change_pct means more escalations = bad
      isPositiveDelta: (data?.escalation_rate.change_pct ?? 0) < 0,
      icon: "support_agent",
      sparkline: escalSparkline,
      // Inverted: lower is better
      sparklinePositive: (data?.escalation_rate.change_pct ?? 0) <= 0,
      tooltip: "% of resolved/escalated outcomes handed off to a human agent",
    },
    {
      id: "bot-latency",
      label: "Bot Latency",
      value: data ? data.avg_response_time.value.toFixed(1) : "—",
      unit: "s",
      delta: data ? getDelta(data.avg_response_time.change_pct) : "+0.0%",
      isNeutralDelta: isNeutral(data?.avg_response_time.change_pct ?? 0),
      // Lower response time = better, so negative change_pct = improvement
      isPositiveDelta: (data?.avg_response_time.change_pct ?? 0) < 0,
      icon: "timer",
      sparkline: [],
      sparklinePositive: false,
      tooltip: "Average time between user message and bot reply",
    },
    {
      id: "sentiment-score",
      label: "Sentiment Score",
      value: data ? data.satisfaction_score.value.toFixed(1) : "—",
      unit: "/5",
      delta: data ? getDelta(data.satisfaction_score.change_pct) : "+0.0%",
      isNeutralDelta: isNeutral(data?.satisfaction_score.change_pct ?? 0),
      isPositiveDelta: (data?.satisfaction_score.change_pct ?? 0) > 0,
      icon: "sentiment_satisfied",
      sparkline: [],
      sparklinePositive: true,
      tooltip: "Keyword-based sentiment score from user messages (0–5)",
    },
  ];

  if (loading) {
    return (
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-3 md:gap-5 mb-10">
        {[1, 2, 3, 4, 5].map((i) => (
          <div
            key={i}
            className={`rounded-[20px] md:rounded-3xl border p-5 md:p-6 relative overflow-hidden animate-pulse min-h-[120px] ${
              i === 1 ? "col-span-2 lg:col-span-1" : "col-span-1"
            } ${isDark ? "bg-[#1f1f23] border-white/[0.06]" : "bg-white border-black/5"}`}
          >
            <div className="flex justify-between items-start mb-5">
              <div className={`w-10 h-10 md:w-12 md:h-12 rounded-xl ${isDark ? "bg-white/5" : "bg-black/5"}`} />
              <div className={`w-12 h-6 rounded-full ${isDark ? "bg-white/5" : "bg-black/5"}`} />
            </div>
            <div className={`w-2/3 h-3 rounded-full mb-3 ${isDark ? "bg-white/5" : "bg-black/5"}`} />
            <div className={`w-1/2 h-8 rounded-lg mb-4 ${isDark ? "bg-white/5" : "bg-black/5"}`} />
            <div className={`w-full h-6 rounded ${isDark ? "bg-white/5" : "bg-black/5"}`} />
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 lg:grid-cols-5 gap-3 md:gap-5 mb-10">
      {kpis.map((card, index) => {
        const isHero = index === 0;
        return (
          <div
            key={card.id}
            title={card.tooltip}
            className={`rounded-[20px] md:rounded-3xl border p-5 md:p-6 transition-[border-color,box-shadow] duration-300 group relative overflow-hidden min-h-[120px] flex flex-col justify-between ${
              isHero ? "col-span-2 lg:col-span-1" : "col-span-1"
            } ${
              isDark
                ? "bg-[#1f1f23] border-white/[0.06] hover:border-white/10"
                : "bg-white border-black/5 shadow-[0_8px_30px_rgb(0,0,0,0.02)] hover:shadow-[0_8px_40px_rgb(0,0,0,0.06)]"
            }`}
          >
            {/* Decorative blob - hidden on mobile */}
            <div className="hidden md:block absolute -right-6 -top-6 w-24 h-24 bg-[#EBDCFF] rounded-full opacity-20 group-hover:scale-150 transition-transform duration-500 pointer-events-none" />

            <div className="flex items-start justify-between mb-5 relative z-10">
              <div className="w-10 h-10 md:w-12 md:h-12 rounded-xl flex items-center justify-center bg-[#EBDCFF] text-[#1c1c1e] shadow-inner flex-shrink-0">
                <span className="material-symbols-outlined text-[20px] md:text-[24px]" aria-hidden="true">
                  {card.icon}
                </span>
              </div>
              <span
                className={`text-[11px] font-bold px-2.5 py-1 md:py-1.5 rounded-full border shadow-sm ${
                  card.isNeutralDelta
                    ? isDark
                      ? "bg-white/5 border-white/10 text-white/60"
                      : "bg-black/5 border-black/5 text-[#1c1c1e]/60"
                    : card.isPositiveDelta
                    ? isDark
                      ? "bg-[#EBDCFF]/10 border-[#EBDCFF]/20 text-[#EBDCFF]"
                      : "bg-[#EBDCFF]/20 border-[#EBDCFF]/30 text-[#1c1c1e]"
                    : isDark
                    ? "bg-rose-500/10 border-rose-500/20 text-rose-400"
                    : "bg-rose-50 border-rose-200 text-rose-700"
                }`}
              >
                {card.delta}
              </span>
            </div>

            <div className="relative z-10 flex-1 flex flex-col justify-end">
              <p
                className={`text-[10px] md:text-[11px] font-bold uppercase tracking-[0.15em] mb-1.5 ${
                  c("text-[#1c1c1e]/60", "text-white/60")
                }`}
              >
                {card.label}
              </p>
              <h3
                className={`${isHero ? "text-3xl" : "text-2xl"} md:text-[2rem] font-serif font-bold mb-3 md:mb-4 tracking-tight flex items-baseline leading-none ${
                  c("text-[#1c1c1e]", "text-white")
                }`}
                style={{ fontFamily: "'Playfair Display', serif" }}
              >
                <span>{card.value}</span>
                {card.unit && (
                  <span
                    className={`font-sans text-base font-bold ml-1 tracking-normal ${
                      c("text-[#1c1c1e]/50", "text-white/40")
                    }`}
                  >
                    {card.unit}
                  </span>
                )}
              </h3>

              {/* Sparkline (if we have data) */}
              {card.sparkline.length >= 2 ? (
                <div className="mt-auto">
                  <Sparkline values={card.sparkline} positive={card.sparklinePositive} />
                </div>
              ) : (
                <div className={`w-full h-1 rounded-full mt-auto ${c("bg-black/5", "bg-white/10")}`} />
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
