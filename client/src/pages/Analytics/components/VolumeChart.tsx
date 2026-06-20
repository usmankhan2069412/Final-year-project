import { useEffect, useState } from "react";
import { useTheme } from "../../../contexts/ThemeContext";
import { api } from "../../../lib/api";

interface VolumeItem {
  date: string;
  conversations: number;
  messages: number;
  resolved_count: number;
  escalated_count: number;
}

interface VolumeChartProps {
  days: number;
  chatbotId: string;
}

export default function VolumeChart({ days, chatbotId }: VolumeChartProps) {
  const { isDark } = useTheme();
  const c = (light: string, dark: string) => (isDark ? dark : light);
  const [data, setData] = useState<VolumeItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchVolume() {
      setLoading(true);
      try {
        const token = localStorage.getItem("token");
        const headers: Record<string, string> = { "Content-Type": "application/json" };
        if (token) headers["Authorization"] = `Bearer ${token}`;

        const params = new URLSearchParams({ days: String(days) });
        if (chatbotId) params.set("chatbot_id", chatbotId);

        const res = await fetch(`${api.baseUrl}/api/v1/analytics/volume?${params}`, { headers });
        if (res.ok) setData(await res.json());
      } catch (err) {
        console.error("Error fetching volume data:", err);
      } finally {
        setLoading(false);
      }
    }
    fetchVolume();
  }, [days, chatbotId]);

  const width = 1000;
  const height = 200;
  const paddingY = 20;
  const chartHeight = height - paddingY * 2;

  const maxVal = data.length > 0 ? Math.max(...data.map((d) => d.conversations), 1) : 1;

  const toY = (val: number) => height - paddingY - (val / maxVal) * chartHeight;
  const toX = (i: number) => (data.length > 1 ? (i / (data.length - 1)) * width : 0);

  // Build SVG path strings for each series
  const buildLinePath = (values: number[]) =>
    values.map((v, i) => `${i === 0 ? "M" : "L"}${toX(i).toFixed(1)},${toY(v).toFixed(1)}`).join(" ");

  const buildAreaPath = (values: number[]) => {
    if (values.length === 0) return "";
    const line = buildLinePath(values);
    return `${line} L${width},${height} L0,${height} Z`;
  };

  const totalPts = data.map((d) => d.conversations);
  const resolvedPts = data.map((d) => d.resolved_count);
  const escalatedPts = data.map((d) => d.escalated_count);

  const totalLine = buildLinePath(totalPts);
  const resolvedArea = buildAreaPath(resolvedPts);
  const escalatedArea = buildAreaPath(escalatedPts);

  const formatYLabel = (val: number) => (val >= 1000 ? `${(val / 1000).toFixed(1)}k` : String(Math.round(val)));
  const yLabels = [maxVal, maxVal * 0.75, maxVal * 0.5, maxVal * 0.25, 0].map(formatYLabel);

  // 5 evenly-spaced X-axis date labels
  const xTicks = (() => {
    if (data.length === 0) return [];
    const step = Math.max(1, Math.floor(data.length / 4));
    const ticks = [];
    for (let i = 0; i < data.length; i += step) ticks.push(data[i]);
    if (ticks[ticks.length - 1] !== data[data.length - 1]) {
      ticks[ticks.length - 1] = data[data.length - 1];
    }
    return ticks.slice(0, 5);
  })();

  const isEmpty = !loading && data.every((d) => d.conversations === 0);

  return (
    <div
      className={`rounded-[2rem] border p-4 sm:p-8 mb-6 ${
        isDark
          ? "bg-[#1f1f23] border-white/[0.06]"
          : "bg-white border-black/5 shadow-[0_8px_30px_rgb(0,0,0,0.02)]"
      }`}
    >
      <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-8 gap-4">
        <div>
          <h2
            className={`text-[20px] font-serif font-bold ${c("text-[#1c1c1e]", "text-white")}`}
            style={{ fontFamily: "'Playfair Display', serif" }}
          >
            Resolution Trend
          </h2>
          <p className={`text-[13px] font-medium mt-1 ${c("text-[#1c1c1e]/50", "text-white/40")}`}>
            Daily conversation outcomes across all agents
          </p>
        </div>

        {/* Legend */}
        <div className="flex flex-wrap items-center gap-4 sm:gap-5">
          {[
            { label: "Total", color: isDark ? "#EBDCFF" : "#1c1c1e", dashed: true },
            { label: "Resolved", color: isDark ? "#86efac" : "#16a34a" },
            { label: "Escalated", color: isDark ? "#fca5a5" : "#dc2626" },
          ].map(({ label, color, dashed }) => (
            <div key={label} className="flex items-center gap-2">
              <svg width="20" height="2" aria-hidden="true">
                <line
                  x1="0" y1="1" x2="20" y2="1"
                  stroke={color}
                  strokeWidth="2"
                  strokeDasharray={dashed ? "4,3" : undefined}
                />
              </svg>
              <span className={`text-[10px] font-bold uppercase tracking-[0.15em] ${c("text-[#1c1c1e]/50", "text-[#85948b]")}`}>
                {label}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Chart area */}
      <div className="relative w-full h-48 sm:h-64">
        {/* Y-axis grid */}
        <div className="absolute inset-0 flex flex-col justify-between pb-0">
          {yLabels.map((v, i) => (
            <div key={i} className="flex items-center gap-4">
              <span className={`text-[11px] font-medium w-8 text-right ${c("text-[#1c1c1e]/40", "text-white/30")}`}>
                {v}
              </span>
              <div className={`flex-1 h-px ${c("bg-black/[0.03]", "bg-white/[0.03]")}`} />
            </div>
          ))}
        </div>

        {/* SVG chart */}
        <div className="absolute inset-0 pl-10 sm:pl-12">
          {loading ? (
            <div className={`w-full h-full rounded-t-3xl animate-pulse ${isDark ? "bg-white/[0.03]" : "bg-black/[0.03]"}`} />
          ) : isEmpty ? (
            <div className="w-full h-full flex items-center justify-center">
              <span className={`text-[13px] font-medium ${c("text-[#1c1c1e]/40", "text-white/30")}`}>
                No conversation data for this period
              </span>
            </div>
          ) : (
            <svg className="w-full h-full" preserveAspectRatio="none" viewBox={`0 0 ${width} ${height}`}>
              <defs>
                <linearGradient id="gradResolved" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={isDark ? "#86efac" : "#16a34a"} stopOpacity="0.25" />
                  <stop offset="100%" stopColor={isDark ? "#86efac" : "#16a34a"} stopOpacity="0" />
                </linearGradient>
                <linearGradient id="gradEscalated" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={isDark ? "#fca5a5" : "#dc2626"} stopOpacity="0.25" />
                  <stop offset="100%" stopColor={isDark ? "#fca5a5" : "#dc2626"} stopOpacity="0" />
                </linearGradient>
              </defs>

              {/* Resolved area */}
              {resolvedArea && (
                <path d={resolvedArea} fill="url(#gradResolved)" />
              )}
              {/* Escalated area */}
              {escalatedArea && (
                <path d={escalatedArea} fill="url(#gradEscalated)" />
              )}
              {/* Total line (dashed) */}
              {totalLine && (
                <path
                  d={totalLine}
                  fill="none"
                  stroke={isDark ? "#EBDCFF" : "#1c1c1e"}
                  strokeWidth="2.5"
                  strokeDasharray="8,5"
                  strokeLinecap="round"
                  vectorEffect="non-scaling-stroke"
                />
              )}
              {/* Resolved line */}
              {resolvedPts.length > 0 && (
                <path
                  d={buildLinePath(resolvedPts)}
                  fill="none"
                  stroke={isDark ? "#86efac" : "#16a34a"}
                  strokeWidth="2"
                  strokeLinecap="round"
                  vectorEffect="non-scaling-stroke"
                />
              )}
              {/* Escalated line */}
              {escalatedPts.length > 0 && (
                <path
                  d={buildLinePath(escalatedPts)}
                  fill="none"
                  stroke={isDark ? "#fca5a5" : "#dc2626"}
                  strokeWidth="2"
                  strokeLinecap="round"
                  vectorEffect="non-scaling-stroke"
                />
              )}
            </svg>
          )}
        </div>
      </div>

      {/* X-axis labels */}
      <div className="flex justify-between mt-5 pl-10 sm:pl-12">
        {loading
          ? [1, 2, 3, 4, 5].map((i) => (
              <span key={i} className={`h-4 w-12 rounded animate-pulse ${isDark ? "bg-white/5" : "bg-black/5"}`} />
            ))
          : xTicks.map((d, i) => (
              <span key={i} className={`text-[11px] font-medium ${c("text-[#1c1c1e]/40", "text-white/30")}`}>
                {new Date(d.date).toLocaleDateString("en-US", { month: "short", day: "numeric" })}
              </span>
            ))}
      </div>
    </div>
  );
}
