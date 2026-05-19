import { useState } from "react";
import { useTheme } from "../contexts/ThemeContext";
import Sidebar from "../components/Sidebar";
import TopBar from "../components/TopBar";
import ProfileTab from "./Settings/components/ProfileTab";
import SecurityTab from "./Settings/components/SecurityTab";
import ApiKeysTab from "./Settings/components/ApiKeysTab";
import UsageBillingTab from "./Settings/components/UsageBillingTab";

const TABS = ["Profile", "Security", "API Keys", "Usage & Billing"];

export default function Settings() {
  const [activeTab, setActiveTab] = useState("Profile");
  const { isDark } = useTheme();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div
      className={`min-h-screen flex font-sans selection:bg-[#EBDCFF] selection:text-[#1c1c1e] transition-colors duration-300 ${
        isDark ? "bg-[#131317] text-[#e4e1e7]" : "bg-[#F5F5F7] text-[#1c1c1e]"
      }`}
    >
      <Sidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      <div className="flex-1 flex flex-col min-w-0 overflow-hidden relative">
        <div
          className={`absolute top-0 right-0 w-[500px] h-[500px] rounded-full blur-3xl pointer-events-none transition-opacity duration-500 ${
            isDark
              ? "bg-[#EBDCFF] opacity-5 mix-blend-screen"
              : "bg-[#EBDCFF] opacity-10 mix-blend-multiply"
          }`}
        ></div>

        <TopBar
          title="Account Settings"
          onMenuToggle={() => setSidebarOpen((v) => !v)}
        />

        <main className="flex-1 overflow-y-auto z-10">
          {/* Tab Bar */}
          <div
            className={`border-b px-4 sm:px-8 lg:px-12 sticky top-0 z-20 backdrop-blur-md transition-colors ${
              isDark
                ? "bg-[#131317]/90 border-white/[0.06]"
                : "bg-[#F5F5F7]/80 border-black/5"
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

          <div className="max-w-4xl mx-auto p-4 sm:p-8 lg:p-12 pb-24">
            {activeTab === "Profile" && <ProfileTab />}
            {activeTab === "Security" && <SecurityTab />}
            {activeTab === "API Keys" && <ApiKeysTab />}
            {activeTab === "Usage & Billing" && <UsageBillingTab />}
          </div>
        </main>
      </div>
    </div>
  );
}
