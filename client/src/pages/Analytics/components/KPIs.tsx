import { useTheme } from "../../../contexts/ThemeContext";

export default function KPIs() {
  const { isDark } = useTheme();
  const c = (light: string, dark: string) => (isDark ? dark : light);

  const kpis = [
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
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-10">
      {kpis.map((card) => (
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
  );
}
