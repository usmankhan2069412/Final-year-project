import { useState, useEffect } from "react";
import { useLocation } from "wouter";
import { useTheme } from "../contexts/ThemeContext";
import { useAuth } from "../contexts/AuthContext";

type NavItem = {
  label: string;
  icon: string;
  href: string;
};

const NAV_ITEMS: NavItem[] = [
  { label: "Dashboard", icon: "dashboard", href: "/dashboard" },
  { label: "Inbox", icon: "inbox", href: "/inbox" },
  { label: "Analytics", icon: "insights", href: "/analytics" },
  { label: "Models", icon: "psychology", href: "/models" },
  { label: "Settings", icon: "settings", href: "/settings" },
];

interface SidebarProps {
  onNewBot?: () => void;
  isOpen?: boolean;
  onClose?: () => void;
}

export default function Sidebar({ onNewBot, isOpen = false, onClose }: SidebarProps) {
  const [location, setLocation] = useLocation();
  const { isDark } = useTheme();
  const { logout } = useAuth();

  // Desktop collapse state with persistence
  const [isCollapsed, setIsCollapsed] = useState(() => {
    if (typeof window !== "undefined") {
      return localStorage.getItem("sidebar-collapsed") === "true";
    }
    return false;
  });

  useEffect(() => {
    localStorage.setItem("sidebar-collapsed", String(isCollapsed));
  }, [isCollapsed]);

  const isActive = (href: string) => location === href;

  // Close sidebar on route change (mobile)
  useEffect(() => {
    if (onClose) onClose();
  }, [location]); // eslint-disable-line react-hooks/exhaustive-deps

  // Close on Escape key
  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === "Escape" && onClose) onClose();
    };
    document.addEventListener("keydown", handleKey);
    return () => document.removeEventListener("keydown", handleKey);
  }, [onClose]);

  const sidebarContent = (
    <aside
      className={`relative h-full flex flex-col font-sans transition-all duration-200 ease-in-out ${
        isCollapsed ? "w-[76px]" : "w-64"
      } ${
        isDark
          ? "bg-[#111115] border-r border-white/5"
          : "bg-[#1c1c1e] border-r border-white/5"
      }`}
    >
      {/* Brand */}
      <div
        className={`h-16 flex items-center border-b border-white/5 cursor-pointer flex-shrink-0 group transition-all duration-200 ${
          isCollapsed ? "justify-center px-0" : "px-5"
        }`}
        onClick={() => setLocation("/")}
      >
        <div className="w-9 h-9 rounded-xl bg-[#EBDCFF] flex items-center justify-center flex-shrink-0 transition-transform group-hover:scale-105">
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="#1c1c1e"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M12 2L2 22h20L12 2z"></path>
          </svg>
        </div>
        
        <div
          className={`flex flex-col transition-all duration-200 overflow-hidden ${
            isCollapsed ? "opacity-0 w-0 scale-95 pointer-events-none ml-0" : "opacity-100 w-auto ml-2.5"
          }`}
        >
          <p
            className="text-[#F5F5F7] font-serif font-bold text-lg leading-tight"
            style={{ fontFamily: "'Playfair Display', serif" }}
          >
            Aina
          </p>
          <p className="text-white/40 text-[9px] uppercase tracking-[0.2em] font-bold">
            Platform
          </p>
        </div>

        {/* Close button — mobile only */}
        {onClose && (
          <button
            onClick={(e) => { e.stopPropagation(); onClose(); }}
            aria-label="Close menu"
            className="ml-auto w-8 h-8 flex items-center justify-center rounded-lg text-white/40 hover:text-white hover:bg-white/5 transition-all md:hidden"
          >
            <span className="material-symbols-outlined text-[20px]">close</span>
          </button>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-3.5 space-y-1 overflow-y-auto overflow-x-hidden no-scrollbar">
        <p
          className={`text-[9px] uppercase tracking-widest text-white/30 font-bold px-3 pt-2.5 pb-1.5 transition-all duration-200 overflow-hidden ${
            isCollapsed ? "opacity-0 h-0 py-0" : "opacity-100"
          }`}
        >
          Overview
        </p>
        {NAV_ITEMS.map((item) => {
          const active = isActive(item.href);
          return (
            <a
              key={item.href}
              href={item.href}
              className={`flex items-center rounded-xl text-[13px] font-semibold transition-all duration-200 group relative ${
                isCollapsed ? "justify-center p-2.5" : "px-3.5 py-2.5"
              } ${
                active
                  ? "bg-[#EBDCFF] text-[#1c1c1e] shadow-sm"
                  : "text-white/60 hover:text-[#F5F5F7] hover:bg-white/5"
              }`}
            >
              <span
                className={`material-symbols-outlined text-[18px] flex-shrink-0 transition-colors ${
                  active
                    ? "text-[#1c1c1e]"
                    : "text-white/40 group-hover:text-white/80"
                }`}
              >
                {item.icon}
              </span>
              
              <span
                className={`inline-block transition-all duration-200 overflow-hidden whitespace-nowrap ${
                  isCollapsed ? "opacity-0 w-0 scale-95 pointer-events-none" : "opacity-100 w-auto ml-3"
                }`}
              >
                {item.label}
              </span>

              {active && !isCollapsed && (
                <span className="ml-auto w-1.5 h-1.5 rounded-full bg-[#1c1c1e]"></span>
              )}

              {/* Tooltip on Hover (Collapsed only) */}
              {isCollapsed && (
                <span className="absolute left-16 bg-[#1c1c1e] text-white text-[11px] font-bold px-3 py-1.5 rounded-lg opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity duration-200 whitespace-nowrap z-50 shadow-md border border-white/10">
                  {item.label}
                </span>
              )}
            </a>
          );
        })}
      </nav>

      {/* Bottom Section */}
      <div className={`p-3.5 border-t border-white/5 space-y-1 flex-shrink-0 transition-all duration-200 overflow-x-hidden ${isCollapsed ? "items-center" : ""}`}>
        <button
          onClick={() => setLocation("/builder")}
          className={`bg-[#EBDCFF] hover:bg-[#d8bfff] text-[#1c1c1e] font-bold rounded-xl flex items-center justify-center text-[13px] transition-all mb-2.5 shadow-sm overflow-hidden ${
            isCollapsed ? "w-10 h-10 p-0 rounded-full" : "w-full py-2.5 px-3.5 gap-2"
          }`}
          title={isCollapsed ? "New Agent" : undefined}
        >
          <span className="material-symbols-outlined text-[16px] flex-shrink-0">add</span>
          <span
            className={`inline-block transition-all duration-200 overflow-hidden whitespace-nowrap ${
              isCollapsed ? "opacity-0 w-0 scale-95 pointer-events-none" : "opacity-100 w-auto"
            }`}
          >
            New Agent
          </span>
        </button>

        <a
          href="mailto:support@aina.ai"
          className={`flex items-center rounded-xl text-[13px] font-semibold text-white/60 hover:text-[#F5F5F7] hover:bg-white/5 transition-all group relative ${
            isCollapsed ? "justify-center p-2.5" : "px-3.5 py-2"
          }`}
        >
          <span className="material-symbols-outlined text-[18px] text-white/40 flex-shrink-0">
            help_outline
          </span>
          <span
            className={`inline-block transition-all duration-200 overflow-hidden whitespace-nowrap ${
              isCollapsed ? "opacity-0 w-0 scale-95 pointer-events-none" : "opacity-100 w-auto ml-3"
            }`}
          >
            Help &amp; Support
          </span>

          {/* Tooltip */}
          {isCollapsed && (
            <span className="absolute left-16 bg-[#1c1c1e] text-white text-[11px] font-bold px-3 py-1.5 rounded-lg opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity duration-200 whitespace-nowrap z-50 shadow-md border border-white/10">
              Help &amp; Support
            </span>
          )}
        </a>

        <button
          onClick={() => { logout(); setLocation("/login"); }}
          className={`flex items-center rounded-xl text-[13px] font-semibold text-white/60 hover:text-white hover:bg-white/5 transition-all w-full group relative ${
            isCollapsed ? "justify-center p-2.5" : "px-3.5 py-2"
          }`}
        >
          <span className="material-symbols-outlined text-[18px] text-white/40 flex-shrink-0">
            logout
          </span>
          <span
            className={`inline-block transition-all duration-200 overflow-hidden whitespace-nowrap ${
              isCollapsed ? "opacity-0 w-0 scale-95 pointer-events-none" : "opacity-100 w-auto ml-3"
            }`}
          >
            Sign Out
          </span>

          {/* Tooltip */}
          {isCollapsed && (
            <span className="absolute left-16 bg-[#1c1c1e] text-white text-[11px] font-bold px-3 py-1.5 rounded-lg opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity duration-200 whitespace-nowrap z-50 shadow-md border border-white/10">
              Sign Out
            </span>
          )}
        </button>
      </div>

      {/* Collapse Toggle Button (Desktop only) */}
      <button
        onClick={(e) => {
          e.stopPropagation();
          setIsCollapsed(!isCollapsed);
        }}
        aria-label={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
        className={`hidden md:flex absolute -right-3 top-20 w-6 h-6 rounded-full items-center justify-center cursor-pointer shadow-md z-30 transition-all duration-200 hover:scale-110 active:scale-95 border ${
          isDark
            ? "bg-[#1c1c1e] border-white/10 text-white/60 hover:text-white"
            : "bg-white border-black/10 text-black/60 hover:text-black"
        }`}
      >
        <span className="material-symbols-outlined text-[14px] transition-transform duration-200">
          {isCollapsed ? "chevron_right" : "chevron_left"}
        </span>
      </button>
    </aside>
  );

  return (
    <>
      {/* ── Desktop: always-visible sticky sidebar ── */}
      <div
        className={`hidden md:flex h-screen sticky top-0 flex-shrink-0 transition-all duration-200 ease-in-out z-20 ${
          isCollapsed ? "w-[76px]" : "w-64"
        }`}
      >
        {sidebarContent}
      </div>

      {/* ── Mobile: overlay drawer ── */}
      {/* Backdrop */}
      <div
        className={`fixed inset-0 z-40 bg-black/60 backdrop-blur-sm transition-opacity duration-300 md:hidden ${
          isOpen ? "opacity-100 pointer-events-auto" : "opacity-0 pointer-events-none"
        }`}
        onClick={onClose}
        aria-hidden="true"
      />
      {/* Drawer */}
      <div
        className={`fixed inset-y-0 left-0 z-50 h-full transition-transform duration-300 ease-in-out md:hidden ${
          isOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        {/* On mobile, sidebar is never collapsed */}
        <aside className="relative h-full w-64 flex flex-col font-sans bg-[#1c1c1e] border-r border-white/5">
          {/* We instantiate mobile version of sidebarContent without collapsible states */}
          <div className="h-16 flex items-center border-b border-white/5 cursor-pointer flex-shrink-0 px-5" onClick={() => setLocation("/")}>
            <div className="w-9 h-9 rounded-xl bg-[#EBDCFF] flex items-center justify-center flex-shrink-0">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#1c1c1e" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 2L2 22h20L12 2z"></path>
              </svg>
            </div>
            <div className="flex flex-col ml-2.5">
              <p className="text-[#F5F5F7] font-serif font-bold text-lg leading-tight" style={{ fontFamily: "'Playfair Display', serif" }}>
                Aina
              </p>
              <p className="text-white/40 text-[9px] uppercase tracking-[0.2em] font-bold">
                Platform
              </p>
            </div>
            {onClose && (
              <button
                onClick={(e) => { e.stopPropagation(); onClose(); }}
                aria-label="Close menu"
                className="ml-auto w-8 h-8 flex items-center justify-center rounded-lg text-white/40 hover:text-white hover:bg-white/5 transition-all md:hidden"
              >
                <span className="material-symbols-outlined text-[20px]">close</span>
              </button>
            )}
          </div>
          
          <nav className="flex-1 p-3.5 space-y-1 overflow-y-auto no-scrollbar">
            <p className="text-[9px] uppercase tracking-widest text-white/30 font-bold px-3 pt-2.5 pb-1.5">
              Overview
            </p>
            {NAV_ITEMS.map((item) => {
              const active = isActive(item.href);
              return (
                <a
                  key={item.href}
                  href={item.href}
                  className={`flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-[13px] font-semibold transition-all duration-200 group ${
                    active ? "bg-[#EBDCFF] text-[#1c1c1e] shadow-sm" : "text-white/60 hover:text-[#F5F5F7] hover:bg-white/5"
                  }`}
                >
                  <span className={`material-symbols-outlined text-[18px] flex-shrink-0 transition-colors ${active ? "text-[#1c1c1e]" : "text-white/40 group-hover:text-white/80"}`}>
                    {item.icon}
                  </span>
                  {item.label}
                  {active && <span className="ml-auto w-1.5 h-1.5 rounded-full bg-[#1c1c1e]"></span>}
                </a>
              );
            })}
          </nav>

          <div className="p-3.5 border-t border-white/5 space-y-1 flex-shrink-0">
            <button
              onClick={() => setLocation("/builder")}
              className="w-full bg-[#EBDCFF] hover:bg-[#d8bfff] text-[#1c1c1e] font-bold py-2.5 px-3.5 rounded-xl flex items-center justify-center gap-2 text-[13px] transition-colors mb-2.5 shadow-sm"
            >
              <span className="material-symbols-outlined text-[16px]">add</span>
              New Agent
            </button>
            <a
              href="mailto:support@aina.ai"
              className="flex items-center gap-3 px-3.5 py-2 rounded-xl text-[13px] font-semibold text-white/60 hover:text-[#F5F5F7] hover:bg-white/5 transition-all"
            >
              <span className="material-symbols-outlined text-[18px] text-white/40">help_outline</span>
              Help &amp; Support
            </a>
            <button
              onClick={() => { logout(); setLocation("/login"); }}
              className="flex items-center gap-3 px-3.5 py-2 rounded-xl text-[13px] font-semibold text-white/60 hover:text-white hover:bg-white/5 transition-all w-full"
            >
              <span className="material-symbols-outlined text-[18px] text-white/40">logout</span>
              Sign Out
            </button>
          </div>
        </aside>
      </div>
    </>
  );
}
