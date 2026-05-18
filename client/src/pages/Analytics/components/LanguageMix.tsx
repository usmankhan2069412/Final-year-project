import { useTheme } from "../../../contexts/ThemeContext";

export default function LanguageMix() {
  const { isDark } = useTheme();
  const c = (light: string, dark: string) => (isDark ? dark : light);

  return (
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
  );
}
