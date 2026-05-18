import { useTheme } from "../../../contexts/ThemeContext";

export default function VolumeChart() {
  const { isDark } = useTheme();
  const c = (light: string, dark: string) => (isDark ? dark : light);

  return (
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
  );
}
