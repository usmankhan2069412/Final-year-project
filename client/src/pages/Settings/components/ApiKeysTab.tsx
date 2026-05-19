import { useTheme } from "../../../contexts/ThemeContext";

export default function ApiKeysTab() {
  const { isDark } = useTheme();
  const c = (light: string, dark: string) => (isDark ? dark : light);

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
        <div>
          <h2
            className={`text-[2rem] font-serif font-bold mb-2 ${
              c("text-[#1c1c1e]", "text-white")
            }`}
            style={{ fontFamily: "'Playfair Display', serif" }}
          >
            API Keys
          </h2>
          <p
            className={`text-[15px] font-medium ${
              c("text-[#1c1c1e]/60", "text-white/50")
            }`}
          >
            Manage credentials for your deployments.
          </p>
        </div>
        <button
          className={`px-5 py-3 rounded-xl font-bold text-[14px] flex items-center justify-center gap-2 transition-all shadow-md w-full sm:w-auto ${
            isDark
              ? "bg-[#EBDCFF] text-[#1c1c1e] hover:bg-[#d8bfff]"
              : "bg-[#1c1c1e] text-[#F5F5F7] hover:bg-black"
          }`}
        >
          <span className="material-symbols-outlined text-[18px]">add</span>
          Create New Key
        </button>
      </div>

      <div className="space-y-4">
        {[
          {
            name: "Production_Main_V2",
            key: "sk_live_••••••••••••49a2",
          },
          {
            name: "Staging_Test_Env",
            key: "sk_test_••••••••••••881c",
          },
        ].map((k) => (
          <div
            key={k.name}
            className={`rounded-[1.5rem] border p-4 sm:p-6 flex flex-col md:flex-row md:items-center gap-6 ${
              isDark
                ? "bg-[#1f1f23] border-white/[0.06]"
                : "bg-white border-black/5 shadow-[0_8px_30px_rgb(0,0,0,0.02)]"
            }`}
          >
            <div className="flex items-start md:items-center gap-4 flex-1 min-w-0">
              <div
                className={`w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0 ${
                  isDark ? "bg-[#EBDCFF]/10 text-[#EBDCFF]" : "bg-black/5 text-[#1c1c1e]"
                }`}
              >
                <span className="material-symbols-outlined text-[24px]">key</span>
              </div>
              <div className="min-w-0 flex-1">
                <h3
                  className={`text-[16px] font-bold truncate ${
                    c("text-[#1c1c1e]", "text-white")
                  }`}
                >
                  {k.name}
                </h3>
                <div className="flex items-center gap-3 mt-1.5 min-w-0">
                  <code
                    className={`text-[13px] font-mono font-medium px-2 py-0.5 rounded select-all break-all overflow-x-auto no-scrollbar max-w-full block ${
                      isDark ? "bg-[#131317] text-[#85948b]" : "bg-[#F5F5F7] text-[#1c1c1e]/60"
                    }`}
                  >
                    {k.key}
                  </code>
                </div>
              </div>
            </div>
            <div className="flex items-center gap-3 justify-end md:justify-start">
              <button
                className={`w-10 h-10 rounded-xl flex items-center justify-center transition-colors border ${
                  isDark
                    ? "border-transparent hover:bg-white/[0.04] text-white/50 hover:text-white"
                    : "border-black/5 bg-[#F5F5F7] hover:bg-black/5 text-[#1c1c1e]/60 hover:text-[#1c1c1e]"
                }`}
                title="Copy to clipboard"
              >
                <span className="material-symbols-outlined text-[18px]">content_copy</span>
              </button>
              <button
                className={`w-10 h-10 rounded-xl flex items-center justify-center transition-colors border ${
                  isDark
                    ? "border-transparent hover:bg-[#ffb4ab]/10 text-white/30 hover:text-[#ffb4ab]"
                    : "border-black/5 bg-[#F5F5F7] hover:bg-red-50 text-red-400 hover:text-red-500"
                }`}
                title="Revoke key"
              >
                <span className="material-symbols-outlined text-[18px]">delete</span>
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
