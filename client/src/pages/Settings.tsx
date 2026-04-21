import { useState } from "react";
import { useTheme } from "../contexts/ThemeContext";
import Sidebar from "../components/Sidebar";
import TopBar from "../components/TopBar";

const TABS = ["Profile", "Security", "API Keys", "Usage & Billing"];

export default function Settings() {
  const [activeTab, setActiveTab] = useState("Profile");
  const { isDark } = useTheme();

  const c = (light: string, dark: string) => (isDark ? dark : light);

  return (
    <div
      className={`min-h-screen flex font-sans selection:bg-[#EBDCFF] selection:text-[#1c1c1e] transition-colors duration-300 ${
        isDark ? "bg-[#131317] text-[#e4e1e7]" : "bg-[#fbfbf2] text-[#1c1c1e]"
      }`}
    >
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0 overflow-hidden relative">
        <div
          className={`absolute top-0 right-0 w-[500px] h-[500px] rounded-full blur-3xl pointer-events-none transition-opacity duration-500 ${
            isDark
              ? "bg-[#EBDCFF] opacity-5 mix-blend-screen"
              : "bg-[#EBDCFF] opacity-10 mix-blend-multiply"
          }`}
        ></div>

        <TopBar title="Account Settings" />

        <main className="flex-1 overflow-y-auto z-10">
          {/* Tab Bar */}
          <div
            className={`border-b px-8 lg:px-12 sticky top-0 z-20 backdrop-blur-md transition-colors ${
              isDark
                ? "bg-[#131317]/90 border-white/[0.06]"
                : "bg-[#fbfbf2]/80 border-black/5"
            }`}
          >
            <div className="flex gap-6 overflow-x-auto no-scrollbar">
              {TABS.map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`py-5 text-[14px] font-bold transition-all border-b-2 whitespace-nowrap ${
                    activeTab === tab
                      ? (isDark ? "text-[#EBDCFF] border-[#EBDCFF]" : "text-[#1c1c1e] border-[#1c1c1e]")
                      : (isDark ? "text-white/40 border-transparent hover:text-white" : "text-[#1c1c1e]/40 border-transparent hover:text-[#1c1c1e]")
                  }`}
                >
                  {tab}
                </button>
              ))}
            </div>
          </div>

          <div className="max-w-4xl mx-auto p-8 lg:p-12 pb-24">
            {/* PROFILE TAB */}
            {activeTab === "Profile" && (
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
                  className={`rounded-[2rem] border p-8 ${
                    isDark
                      ? "bg-[#1f1f23] border-white/[0.06]"
                      : "bg-white border-black/5 shadow-[0_8px_30px_rgb(0,0,0,0.02)]"
                  }`}
                >
                  <div className="flex items-center gap-6 mb-8">
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
                        className={`absolute -bottom-2 -right-2 w-9 h-9 rounded-full flex items-center justify-center transition-all shadow-md ${
                          isDark
                            ? "bg-[#353439] border border-white/10 hover:bg-[#4a4950] text-[#EBDCFF]"
                            : "bg-white border border-black/5 hover:bg-black/5 text-[#1c1c1e]"
                        }`}
                      >
                        <span className="material-symbols-outlined text-[16px]">edit</span>
                      </button>
                    </div>
                    <div>
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
                              : "bg-[#fbfbf2] border border-black/5 text-[#1c1c1e] focus:border-black/20 focus:bg-white"
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
                            : "bg-[#fbfbf2] border border-black/5 text-[#1c1c1e] focus:border-black/20 focus:bg-white"
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
                        : "bg-[#1c1c1e] text-[#fbfbf2] hover:bg-black"
                    }`}
                  >
                    Save Changes
                  </button>
                </div>
              </div>
            )}

            {/* SECURITY TAB */}
            {activeTab === "Security" && (
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
                  className={`rounded-[2rem] border p-8 space-y-6 ${
                    isDark
                      ? "bg-[#1f1f23] border-white/[0.06]"
                      : "bg-white border-black/5 shadow-[0_8px_30px_rgb(0,0,0,0.02)]"
                  }`}
                >
                  <div
                    className={`flex items-start justify-between p-6 rounded-2xl border ${
                      isDark
                        ? "bg-[#131317] border-white/[0.04]"
                        : "bg-[#fbfbf2] border-black/5"
                    }`}
                  >
                    <div>
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
                      className={`w-12 h-6 rounded-full relative cursor-pointer outline-none transition-all ${
                        isDark ? "bg-[#EBDCFF]" : "bg-[#1c1c1e]"
                      }`}
                    >
                      <div
                        className={`absolute top-1 right-1 w-4 h-4 rounded-full transition-all shadow-sm ${
                          isDark ? "bg-[#1c1c1e]" : "bg-[#fbfbf2]"
                        }`}
                      ></div>
                    </button>
                  </div>

                  <button
                    className={`w-full py-4 rounded-xl font-bold text-[14px] flex items-center justify-center gap-2 transition-all border ${
                      isDark
                        ? "bg-[#131317] border-white/[0.06] hover:bg-[#2a2a2e] text-white"
                        : "bg-[#fbfbf2] border-black/5 hover:bg-black/5 text-[#1c1c1e]"
                    }`}
                  >
                    <span className="material-symbols-outlined text-[20px]">lock_reset</span>
                    Reset Password
                  </button>
                </div>

                <div
                  className={`rounded-[2rem] border p-8 ${
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
                        className={`flex items-center justify-between p-5 rounded-2xl border transition-colors ${
                          isDark
                            ? "bg-[#131317] border-white/[0.04]"
                            : "bg-[#fbfbf2] border-black/5"
                        }`}
                      >
                        <div className="flex items-center gap-4">
                          <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
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
                          <div>
                            <p
                              className={`text-[14px] font-bold ${
                                c("text-[#1c1c1e]", "text-white")
                              }`}
                            >
                              {d.device}
                            </p>
                            <p
                              className={`text-[12px] font-medium mt-0.5 ${
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
                          className={`text-[12px] font-bold px-3 py-1.5 rounded-lg transition-colors ${
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
            )}

            {/* API KEYS TAB */}
            {activeTab === "API Keys" && (
              <div className="space-y-8 animate-in fade-in duration-300">
                <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-6">
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
                    className={`px-5 py-3 rounded-xl font-bold text-[14px] flex items-center gap-2 transition-all shadow-md ${
                      isDark
                        ? "bg-[#EBDCFF] text-[#1c1c1e] hover:bg-[#d8bfff]"
                        : "bg-[#1c1c1e] text-[#fbfbf2] hover:bg-black"
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
                      className={`rounded-[1.5rem] border p-6 flex flex-col md:flex-row md:items-center gap-6 ${
                        isDark
                          ? "bg-[#1f1f23] border-white/[0.06]"
                          : "bg-white border-black/5 shadow-[0_8px_30px_rgb(0,0,0,0.02)]"
                      }`}
                    >
                      <div
                        className={`w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0 ${
                          isDark ? "bg-[#EBDCFF]/10 text-[#EBDCFF]" : "bg-black/5 text-[#1c1c1e]"
                        }`}
                      >
                        <span className="material-symbols-outlined text-[24px]">key</span>
                      </div>
                      <div className="flex-1">
                        <h3
                          className={`text-[16px] font-bold ${
                            c("text-[#1c1c1e]", "text-white")
                          }`}
                        >
                          {k.name}
                        </h3>
                        <div className="flex items-center gap-3 mt-1.5">
                          <code
                            className={`text-[13px] font-mono font-medium px-2 py-0.5 rounded ${
                              isDark ? "bg-[#131317] text-[#85948b]" : "bg-[#fbfbf2] text-[#1c1c1e]/60"
                            }`}
                          >
                            {k.key}
                          </code>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <button
                          className={`w-10 h-10 rounded-xl flex items-center justify-center transition-colors border ${
                            isDark
                              ? "border-transparent hover:bg-white/[0.04] text-white/50 hover:text-white"
                              : "border-black/5 bg-[#fbfbf2] hover:bg-black/5 text-[#1c1c1e]/60 hover:text-[#1c1c1e]"
                          }`}
                          title="Copy to clipboard"
                        >
                          <span className="material-symbols-outlined text-[18px]">content_copy</span>
                        </button>
                        <button
                          className={`w-10 h-10 rounded-xl flex items-center justify-center transition-colors border ${
                            isDark
                              ? "border-transparent hover:bg-[#ffb4ab]/10 text-white/30 hover:text-[#ffb4ab]"
                              : "border-black/5 bg-[#fbfbf2] hover:bg-red-50 text-red-400 hover:text-red-500"
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
            )}

            {/* USAGE & BILLING TAB */}
            {activeTab === "Usage & Billing" && (
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
                  className={`rounded-[2rem] border p-8 relative overflow-hidden shadow-md ${
                    isDark
                      ? "bg-[#1f1f23] border-[#EBDCFF]/30"
                      : "bg-[#1c1c1e] border-black text-[#fbfbf2]"
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
                      className={`px-6 py-3 rounded-xl font-bold text-[14px] transition-all shadow-sm ${
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
                  className={`rounded-[2rem] border p-8 space-y-8 ${
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
            )}
          </div>
        </main>
      </div>
    </div>
  );
}
