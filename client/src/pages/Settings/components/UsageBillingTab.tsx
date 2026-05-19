import { useTheme } from "../../../contexts/ThemeContext";

export default function UsageBillingTab() {
  const { isDark } = useTheme();
  const c = (light: string, dark: string) => (isDark ? dark : light);

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      <div>
        <h2
          className={`text-[2rem] font-serif font-bold mb-2 ${
            c("text-[#1c1c1e]", "text-white")
          }`}
          style={{ fontFamily: "'Playfair Display', serif" }}
        >
          Usage & Billing
        </h2>
        <p
          className={`text-[15px] font-medium ${
            c("text-[#1c1c1e]/60", "text-white/50")
          }`}
        >
          Monitor your resource consumption and subscription plan.
        </p>
      </div>

      {/* Plan card */}
      <div
        className={`rounded-[2rem] border p-4 sm:p-8 relative overflow-hidden shadow-md ${
          isDark
            ? "bg-[#1f1f23] border-[#EBDCFF]/30"
            : "bg-[#1c1c1e] border-black text-[#F5F5F7]"
        }`}
      >
        <div
          className={`absolute top-0 left-0 w-full h-1 ${
            isDark ? "bg-gradient-to-r from-[#EBDCFF] to-transparent" : "bg-[#EBDCFF]"
          }`}
        ></div>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-6">
          <div>
            <p
              className={`text-[11px] font-bold uppercase tracking-[0.2em] mb-2 ${
                isDark ? "text-[#EBDCFF]" : "text-[#EBDCFF]/80"
              }`}
            >
              Current Plan
            </p>
            <h3 className="text-[1.75rem] font-serif font-bold">Professional</h3>
            <p className={`text-[14px] font-medium mt-1 ${isDark ? "text-white/70" : "text-white/60"}`}>
              PKR 8,500 / month
            </p>
          </div>
          <button
            className={`px-6 py-3 rounded-xl font-bold text-[14px] transition-all shadow-sm w-full sm:w-auto ${
              isDark
                ? "bg-[#EBDCFF] text-[#1c1c1e] hover:bg-[#d8bfff]"
                : "bg-white text-[#1c1c1e] hover:bg-black/5"
            }`}
          >
            Upgrade Plan
          </button>
        </div>
      </div>

      {/* Usage bars */}
      <div
        className={`rounded-[2rem] border p-4 sm:p-8 space-y-8 ${
          isDark
            ? "bg-[#1f1f23] border-white/[0.06]"
            : "bg-white border-black/5 shadow-[0_8px_30px_rgb(0,0,0,0.02)]"
        }`}
      >
        <h3
          className={`text-[18px] font-serif font-bold ${
            c("text-[#1c1c1e]", "text-white")
          }`}
        >
          Resource Consumption
        </h3>
        {[
          {
            label: "API Tokens",
            used: "8.2M",
            total: "10M",
            pct: 82,
          },
          {
            label: "Conversations",
            used: "4,286",
            total: "5,000",
            pct: 86,
          },
          {
            label: "Knowledge Base Storage",
            used: "1.2 GB",
            total: "5 GB",
            pct: 24,
          },
        ].map((u) => (
          <div key={u.label}>
            <div className="flex justify-between text-[14px] mb-3">
              <span
                className={`font-semibold ${
                  c("text-[#1c1c1e]/70", "text-[#bbcac0]")
                }`}
              >
                {u.label}
              </span>
              <span
                className={`font-bold ${
                  c("text-[#1c1c1e]", "text-white")
                }`}
              >
                {u.used} / {u.total}
              </span>
            </div>
            <div
              className={`w-full h-2 rounded-full overflow-hidden shadow-inner ${
                c("bg-black/5", "bg-[#131317]")
              }`}
            >
              <div
                className={`h-full rounded-full transition-all ${
                  c("bg-[#1c1c1e]", "bg-[#EBDCFF]")
                }`}
                style={{ width: `${u.pct}%` }}
              ></div>
            </div>
            <p
              className={`text-right text-[11px] font-bold mt-2 ${
                c("text-[#1c1c1e]/40", "text-white/30")
              }`}
            >
              {u.pct}% used · Resets in 12 days
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
