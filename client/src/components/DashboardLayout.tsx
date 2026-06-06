import { useState, ReactNode } from "react";
import { useTheme } from "../contexts/ThemeContext";
import { useLayout } from "../contexts/LayoutContext";
import Sidebar from "./Sidebar";
import TopBar from "./TopBar";

export default function DashboardLayout({ children }: { children: ReactNode }) {
  const { isDark } = useTheme();
  const { title, searchPlaceholder, actions, hideTopBar, sidebarOpen, setSidebarOpen } = useLayout();

  return (
    <div
      className={`h-screen flex font-sans overflow-hidden selection:bg-[#EBDCFF] selection:text-[#1c1c1e] transition-colors duration-300 ${
        isDark ? "bg-[#131317] text-[#e4e1e7]" : "bg-[#F5F5F7] text-[#1c1c1e]"
      }`}
    >
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      <div className="flex-1 flex flex-col min-w-0 overflow-hidden relative">
        {/* Ambient background glow */}
        <div
          className={`absolute top-0 right-0 w-[500px] h-[500px] rounded-full blur-3xl pointer-events-none transition-opacity duration-500 ${
            isDark
              ? "bg-[#EBDCFF] opacity-5 mix-blend-screen"
              : "bg-[#EBDCFF] opacity-10 mix-blend-multiply"
          }`}
        />

        {!hideTopBar && (
          <TopBar
            title={title}
            searchPlaceholder={searchPlaceholder}
            actions={actions}
            onMenuToggle={() => setSidebarOpen((v) => !v)}
          />
        )}

        {children}
      </div>
    </div>
  );
}
