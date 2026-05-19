import { useTheme } from "../../../contexts/ThemeContext";

export default function ProfileTab() {
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
          Profile Settings
        </h2>
        <p
          className={`text-[15px] font-medium ${
            c("text-[#1c1c1e]/60", "text-white/50")
          }`}
        >
          Update your personal information and workspace details.
        </p>
      </div>

      {/* Avatar + Name */}
      <div
        className={`rounded-[2rem] border p-4 sm:p-8 ${
          isDark
            ? "bg-[#1f1f23] border-white/[0.06]"
            : "bg-white border-black/5 shadow-[0_8px_30px_rgb(0,0,0,0.02)]"
        }`}
      >
        <div className="flex flex-col sm:flex-row items-center sm:items-start text-center sm:text-left gap-6 mb-8">
          <div className="relative flex-shrink-0">
            <div
              className={`w-24 h-24 rounded-3xl border-4 flex items-center justify-center overflow-hidden shadow-sm ${
                isDark ? "bg-[#2a2a2e] border-white/5" : "bg-black/5 border-white"
              }`}
            >
              <img
                src="https://ui-avatars.com/api/?name=Admin+User&background=EBDCFF&color=1c1c1e&bold=true&size=100"
                alt="Avatar"
                className="w-full h-full object-cover"
              />
            </div>
            <button
              aria-label="Edit avatar"
              className={`absolute -bottom-2 -right-2 w-9 h-9 rounded-full flex items-center justify-center transition-all shadow-md ${
                isDark
                  ? "bg-[#353439] border border-white/10 hover:bg-[#4a4950] text-[#EBDCFF]"
                  : "bg-white border border-black/5 hover:bg-black/5 text-[#1c1c1e]"
              }`}
            >
              <span className="material-symbols-outlined text-[16px]">edit</span>
            </button>
          </div>
          <div className="flex-1 min-w-0">
            <h3
              className={`text-[22px] font-bold ${
                c("text-[#1c1c1e]", "text-white")
              }`}
            >
              Admin User
            </h3>
            <p
              className={`text-[14px] font-medium mt-1 ${
                c("text-[#1c1c1e]/60", "text-[#85948b]")
              }`}
            >
              Principal Architect @ Aina AI
            </p>
            <p
              className={`text-[10px] uppercase tracking-widest font-bold mt-2 ${
                c("text-[#1c1c1e]/40", "text-white/30")
              }`}
            >
              Last login: 2 hours ago
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {[
            { label: "Full Name", value: "Admin User", type: "text" },
            {
              label: "Email Address",
              value: "admin@aina.ai",
              type: "email",
            },
          ].map((f) => (
            <div key={f.label}>
              <label
                className={`block text-[11px] font-bold uppercase tracking-widest mb-2 ${
                  c("text-[#1c1c1e]/50", "text-[#85948b]")
                }`}
              >
                {f.label}
              </label>
              <input
                type={f.type}
                defaultValue={f.value}
                className={`w-full rounded-xl px-5 py-3.5 text-[14px] font-medium outline-none transition-all shadow-inner ${
                  isDark
                    ? "bg-[#131317] border border-white/[0.06] text-white focus:border-[#EBDCFF]/50"
                    : "bg-[#F5F5F7] border border-black/5 text-[#1c1c1e] focus:border-black/20 focus:bg-white"
                }`}
              />
            </div>
          ))}
          <div className="md:col-span-2">
            <label
              className={`block text-[11px] font-bold uppercase tracking-widest mb-2 ${
                c("text-[#1c1c1e]/50", "text-[#85948b]")
              }`}
            >
              Organization
            </label>
            <input
              type="text"
              defaultValue="Aina AI Global"
              className={`w-full rounded-xl px-5 py-3.5 text-[14px] font-medium outline-none transition-all shadow-inner ${
                isDark
                  ? "bg-[#131317] border border-white/[0.06] text-white focus:border-[#EBDCFF]/50"
                  : "bg-[#F5F5F7] border border-black/5 text-[#1c1c1e] focus:border-black/20 focus:bg-white"
              }`}
            />
          </div>
        </div>
      </div>

      <div className="flex justify-end gap-4">
        <button
          className={`px-6 py-3 rounded-xl font-bold text-[14px] transition-all ${
            isDark
              ? "text-white/60 hover:text-white hover:bg-white/5"
              : "text-[#1c1c1e]/60 hover:text-[#1c1c1e] hover:bg-black/5"
          }`}
        >
          Discard
        </button>
        <button
          className={`px-6 py-3 rounded-xl font-bold text-[14px] transition-all shadow-md active:scale-95 ${
            isDark
              ? "bg-[#EBDCFF] text-[#1c1c1e] hover:bg-[#d8bfff]"
              : "bg-[#1c1c1e] text-[#F5F5F7] hover:bg-black"
          }`}
        >
          Save Changes
        </button>
      </div>
    </div>
  );
}
