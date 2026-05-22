import { useEffect, useState } from "react";
import { useTheme } from "../../../contexts/ThemeContext";

interface LanguageItem {
  language: string;
  count: number;
}

export default function LanguageMix() {
  const { isDark } = useTheme();
  const c = (light: string, dark: string) => (isDark ? dark : light);
  const [data, setData] = useState<LanguageItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchLanguages() {
      try {
        const token = localStorage.getItem("token");
        const headers: Record<string, string> = {
          "Content-Type": "application/json",
        };
        if (token) {
          headers["Authorization"] = `Bearer ${token}`;
        }
        const response = await fetch("http://localhost:8000/api/v1/analytics/languages", {
          headers,
        });
        if (response.ok) {
          const json = await response.json();
          setData(json);
        }
      } catch (err) {
        console.error("Error fetching languages:", err);
      } finally {
        setLoading(false);
      }
    }
    fetchLanguages();
  }, []);

  const totalCount = data.reduce((sum, item) => sum + item.count, 0);

  // Define dynamic color palette matching Aina styles
  const colors = [
    isDark ? "#EBDCFF" : "#1c1c1e",
    isDark ? "rgba(255,255,255,0.4)" : "rgba(0,0,0,0.3)",
    isDark ? "rgba(255,255,255,0.2)" : "rgba(0,0,0,0.15)",
    isDark ? "rgba(255,255,255,0.1)" : "rgba(0,0,0,0.08)",
  ];

  const processedData = data.map((item, idx) => {
    const pct = totalCount > 0 ? Math.round((item.count / totalCount) * 100) : 0;
    return {
      ...item,
      pct,
      color: colors[idx % colors.length],
    };
  });

  // Calculate accumulated offsets for SVG strokeDashoffset
  let accumulatedPercent = 0;
  const svgPaths = processedData.map((item) => {
    const strokeDasharray = `${item.pct}, 100`;
    const strokeDashoffset = -accumulatedPercent;
    accumulatedPercent += item.pct;
    return {
      ...item,
      strokeDasharray,
      strokeDashoffset,
    };
  });

  const activeLangsCount = data.filter((l) => l.count > 0).length;

  return (
    <div
      className={`rounded-[2rem] border p-4 sm:p-8 ${
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
      <div className="flex flex-col sm:flex-row items-center sm:items-start md:items-center gap-6 sm:gap-10">
        <div className="relative w-32 h-32 flex-shrink-0">
          <svg viewBox="0 0 36 36" className="w-full h-full -rotate-90 drop-shadow-sm" aria-hidden="true">
            <path
              strokeDasharray="100, 100"
              d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              fill="none"
              stroke={isDark ? "rgba(255,255,255,0.05)" : "rgba(0,0,0,0.05)"}
              strokeWidth="5"
            />
            {svgPaths.map((pathItem, idx) => (
              <path
                key={idx}
                strokeDasharray={pathItem.strokeDasharray}
                strokeDashoffset={pathItem.strokeDashoffset}
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                fill="none"
                stroke={pathItem.color}
                strokeWidth="5"
                strokeLinecap={pathItem.pct > 0 ? "round" : "butt"}
              />
            ))}
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span
              className={`text-[24px] font-bold ${
                c("text-[#1c1c1e]", "text-white")
              }`}
            >
              {activeLangsCount || "0"}
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
        <div className="flex-1 w-full space-y-5">
          {processedData.map((l) => (
            <div key={l.language}>
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
                    {l.language}
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
  );
}
