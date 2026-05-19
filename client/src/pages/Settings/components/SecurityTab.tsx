import { useTheme } from "../../../contexts/ThemeContext";

export default function SecurityTab() {
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
          Security Center
        </h2>
        <p
          className={`text-[15px] font-medium ${
            c("text-[#1c1c1e]/60", "text-white/50")
          }`}
        >
          Manage authentication, devices and access controls.
        </p>
      </div>

      <div
        className={`rounded-[2rem] border p-4 sm:p-8 space-y-6 ${
          isDark
            ? "bg-[#1f1f23] border-white/[0.06]"
            : "bg-white border-black/5 shadow-[0_8px_30px_rgb(0,0,0,0.02)]"
        }`}
      >
        <div
          className={`flex flex-row items-center justify-between p-4 sm:p-6 rounded-2xl border gap-4 ${
            isDark
              ? "bg-[#131317] border-white/[0.04]"
              : "bg-[#F5F5F7] border-black/5"
          }`}
        >
          <div className="min-w-0">
            <h3
              className={`text-[15px] font-bold ${
                c("text-[#1c1c1e]", "text-white")
              }`}
            >
              Two-Factor Authentication
            </h3>
            <p
              className={`text-[13px] font-medium mt-1.5 max-w-sm ${
                c("text-[#1c1c1e]/60", "text-[#85948b]")
              }`}
            >
              Protect your account with an extra layer via Authenticator app.
            </p>
          </div>
          {/* Toggle Switch Enabled */}
          <button
            aria-label="Toggle two-factor authentication"
            className={`w-12 h-6 rounded-full relative cursor-pointer outline-none transition-all flex-shrink-0 ${
              isDark ? "bg-[#EBDCFF]" : "bg-[#1c1c1e]"
            }`}
          >
            <div
              className={`absolute top-1 right-1 w-4 h-4 rounded-full transition-all shadow-sm ${
                isDark ? "bg-[#1c1c1e]" : "bg-[#F5F5F7]"
              }`}
            ></div>
          </button>
        </div>

        <button
          className={`w-full py-4 rounded-xl font-bold text-[14px] flex items-center justify-center gap-2 transition-all border ${
            isDark
              ? "bg-[#131317] border-white/[0.06] hover:bg-[#2a2a2e] text-white"
              : "bg-[#F5F5F7] border-black/5 hover:bg-black/5 text-[#1c1c1e]"
          }`}
        >
          <span className="material-symbols-outlined text-[20px]">lock_reset</span>
          Reset Password
        </button>
      </div>

      <div
        className={`rounded-[2rem] border p-4 sm:p-8 ${
          isDark
            ? "bg-[#1f1f23] border-white/[0.06]"
            : "bg-white border-black/5 shadow-[0_8px_30px_rgb(0,0,0,0.02)]"
        }`}
      >
        <h3
          className={`text-[18px] font-serif font-bold mb-6 ${
            c("text-[#1c1c1e]", "text-white")
          }`}
        >
          Authorized Devices
        </h3>
        <div className="space-y-4">
          {[
            { device: "MacBook Pro 16″", loc: "Karachi, PK", icon: "laptop_mac", active: true },
            { device: "iPhone 15 Pro", loc: "Karachi, PK", icon: "smartphone", active: false },
          ].map((d) => (
            <div
              key={d.device}
              className={`flex items-center justify-between p-4 sm:p-5 rounded-2xl border transition-colors gap-3 ${
                isDark
                  ? "bg-[#131317] border-white/[0.04]"
                  : "bg-[#F5F5F7] border-black/5"
              }`}
            >
              <div className="flex items-center gap-3 sm:gap-4 min-w-0">
                <div className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 ${
                  isDark ? "bg-white/5" : "bg-white shadow-sm"
                }`}>
                  <span
                    className={`material-symbols-outlined text-[20px] ${
                      c("text-[#1c1c1e]/60", "text-[#85948b]")
                    }`}
                  >
                    {d.icon}
                  </span>
                </div>
                <div className="min-w-0">
                  <p
                    className={`text-[14px] font-bold truncate ${
                      c("text-[#1c1c1e]", "text-white")
                    }`}
                  >
                    {d.device}
                  </p>
                  <p
                    className={`text-[12px] font-medium mt-0.5 truncate ${
                      c("text-[#1c1c1e]/50", "text-[#85948b]")
                    }`}
                  >
                    {d.loc} •{" "}
                    <span
                      className={`font-bold ${
                        d.active ? c("text-[#1c1c1e]", "text-[#EBDCFF]") : c("text-[#1c1c1e]/40", "text-white/30")
                      }`}
                    >
                      {d.active ? "Active Now" : "14h ago"}
                    </span>
                  </p>
                </div>
              </div>
              <button
                className={`text-[12px] font-bold px-3 py-1.5 rounded-lg transition-colors flex-shrink-0 ${
                  c("text-red-600 hover:bg-red-50", "text-[#ffb4ab] hover:bg-[#ffb4ab]/10")
                }`}
              >
                Revoke
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
