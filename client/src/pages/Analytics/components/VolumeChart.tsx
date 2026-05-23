import { useEffect, useState } from "react";
import { useTheme } from "../../../contexts/ThemeContext";

interface VolumeItem {
  date: string;
  conversations: number;
  messages: number;
}

export default function VolumeChart() {
  const { isDark } = useTheme();
  const c = (light: string, dark: string) => (isDark ? dark : light);
  const [days, setDays] = useState(30);
  const [data, setData] = useState<VolumeItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchVolume() {
      try {
        setLoading(true);
        const token = localStorage.getItem("token");
        const headers: Record<string, string> = {
          "Content-Type": "application/json",
        };
        if (token) {
          headers["Authorization"] = `Bearer ${token}`;
        }
        const response = await fetch(`http://localhost:8000/api/v1/analytics/volume?days=${days}`, {
          headers,
        });
        if (response.ok) {
          const json = await response.json();
          setData(json);
        }
      } catch (err) {
        console.error("Error fetching volume data:", err);
      } finally {
        setLoading(false);
      }
    }
    fetchVolume();
  }, [days]);

  // Compute SVG path coordinates
  const width = 1000;
  const height = 200;
  const paddingY = 20;
  const chartHeight = height - paddingY * 2;

  const maxVal = data.length > 0 ? Math.max(...data.map((d) => d.conversations), 10) : 10;
  const points = data.map((d, i) => {
    const x = data.length > 1 ? (i / (data.length - 1)) * width : 0;
    const y = height - paddingY - (d.conversations / maxVal) * chartHeight;
    return { x, y };
  });

  const linePath = points.length > 0
    ? points.map((p, i) => `${i === 0 ? "M" : "L"}${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(" ")
    : "";
  const areaPath = points.length > 0 ? `${linePath} L${width},${height} L0,${height} Z` : "";

  // Handover proxy path (15% of conversations)
  const handoverPoints = data.map((d, i) => {
    const x = data.length > 1 ? (i / (data.length - 1)) * width : 0;
    const handoverVal = d.conversations * 0.15;
    const y = height - paddingY - (handoverVal / maxVal) * chartHeight;
    return { x, y };
  });
  const handoverLinePath = handoverPoints.length > 0
    ? handoverPoints.map((p, i) => `${i === 0 ? "M" : "L"}${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(" ")
    : "";

  // Dynamic Y-axis labels
  const formatYLabel = (val: number) => {
    if (val >= 1000) return `${(val / 1000).toFixed(1)}k`;
    return val.toString();
  };
  const yLabels = [maxVal, maxVal * 0.75, maxVal * 0.5, maxVal * 0.25, 0].map(formatYLabel);

  // Dynamic X-axis labels (5 ticks)
  const getXTicks = () => {
    if (data.length === 0) return [];
    const ticks = [];
    const step = Math.max(1, Math.floor(data.length / 4));
    for (let i = 0; i < data.length; i += step) {
      ticks.push(data[i]);
    }
    if (ticks[ticks.length - 1] !== data[data.length - 1]) {
      ticks[ticks.length - 1] = data[data.length - 1];
    }
    return ticks.slice(0, 5); // Ensure exactly 5 ticks
  };

  const xTicks = getXTicks();

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
        <div className="flex flex-wrap items-center gap-4 sm:gap-6 w-full sm:w-auto justify-between sm:justify-start">
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
            value={days}
            onChange={(e) => setDays(Number(e.target.value))}
            className={`border rounded-xl px-4 py-2.5 text-[13px] font-medium outline-none shadow-sm cursor-pointer transition-[border-color,box-shadow] duration-200 focus-visible:ring-1 w-full sm:w-auto ${
              isDark
                ? "bg-[#131317] border-white/[0.06] text-white/80 focus-visible:ring-[#EBDCFF] focus-visible:border-transparent"
                : "bg-[#F5F5F7] border-black/5 text-[#1c1c1e]/80 focus-visible:ring-black/20 focus:border-black/20"
            }`}
          >
            <option value={30}>Last 30 Days</option>
            <option value={7}>Last 7 Days</option>
            <option value={90}>Last 90 Days</option>
          </select>
        </div>
      </div>

      {/* SVG Chart */}
      <div className="relative w-full h-48 sm:h-64">
        <div className="absolute inset-0 flex flex-col justify-between pb-0">
          {yLabels.map((v, i) => (
            <div key={i} className="flex items-center gap-4">
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
        <div className="absolute inset-0 pl-10 sm:pl-12 animate-pulse">
          {loading ? (
            <div className="w-full h-full flex flex-col justify-end">
              <div className={`w-full h-3/4 bg-gradient-to-t from-transparent ${isDark ? "to-white/[0.03]" : "to-black/[0.03]"} rounded-t-3xl`} />
            </div>
          ) : data.length > 0 && (
            <svg
              className="w-full h-full"
              preserveAspectRatio="none"
              viewBox={`0 0 ${width} ${height}`}
            >
              <defs>
                <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={isDark ? "#EBDCFF" : "#1c1c1e"} stopOpacity="0.15" />
                  <stop offset="100%" stopColor={isDark ? "#EBDCFF" : "#1c1c1e"} stopOpacity="0" />
                </linearGradient>
              </defs>
              {/* Area fill */}
              {areaPath && <path d={areaPath} fill="url(#areaGrad)" />}
              {/* Line */}
              {linePath && (
                <path
                  d={linePath}
                  fill="none"
                  stroke={isDark ? "#EBDCFF" : "#1c1c1e"}
                  strokeWidth="3"
                  strokeLinecap="round"
                  vectorEffect="non-scaling-stroke"
                />
              )}
              {/* Handovers line */}
              {handoverLinePath && (
                <path
                  d={handoverLinePath}
                  fill="none"
                  stroke={isDark ? "rgba(255,255,255,0.3)" : "rgba(0,0,0,0.2)"}
                  strokeWidth="2.5"
                  strokeDasharray="8,6"
                  vectorEffect="non-scaling-stroke"
                />
              )}
            </svg>
          )}
        </div>
      </div>

      <div className="flex justify-between mt-5 pl-10 sm:pl-12">
        {loading ? (
          [1, 2, 3, 4, 5].map((i) => (
            <span key={i} className={`h-4 w-12 rounded animate-pulse ${isDark ? "bg-white/5" : "bg-black/5"}`} />
          ))
        ) : xTicks.map((d, i) => (
          <span
            key={i}
            className={`text-[11px] font-medium ${
              c("text-[#1c1c1e]/40", "text-white/30")
            }`}
          >
            {new Date(d.date).toLocaleDateString("en-US", { month: "short", day: "numeric" })}
          </span>
        ))}
      </div>
    </div>
  );
}
