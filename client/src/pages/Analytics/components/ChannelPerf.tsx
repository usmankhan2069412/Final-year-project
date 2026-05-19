import { useTheme } from "../../../contexts/ThemeContext";

export default function ChannelPerf() {
  const { isDark } = useTheme();
  const c = (light: string, dark: string) => (isDark ? dark : light);

  return (
    <div
      className={`rounded-[2rem] border p-4 sm:p-8 ${
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
                  aria-hidden="true"
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
  );
}
