import { useState } from "react";
import { useLocation } from "wouter";
import { useTheme } from "../contexts/ThemeContext";

interface TopBarProps {
  title?: string;
  searchPlaceholder?: string;
  actions?: React.ReactNode;
  onMenuToggle?: () => void;
}

export default function TopBar({ title, searchPlaceholder, actions, onMenuToggle }: TopBarProps) {
  const [, setLocation] = useLocation();
  const { isDark, toggleTheme } = useTheme();
  const [searchOpen, setSearchOpen] = useState(false);

  return (
    <header
      className={`h-16 flex items-center justify-between px-4 md:px-8 flex-shrink-0 z-10 sticky top-0 transition-colors duration-300 gap-3 ${
        isDark
          ? "bg-[#111115]/90 backdrop-blur-md border-b border-white/5"
          : "bg-[#F5F5F7]/80 backdrop-blur-md border-b border-black/5"
      }`}
    >
      {/* Left: Hamburger (mobile) + Search or Title */}
      <div className="flex items-center gap-3 flex-1 min-w-0">
        {/* Hamburger — mobile only */}
        <button
          onClick={onMenuToggle}
          aria-label="Open navigation menu"
          className={`md:hidden w-10 h-10 flex-shrink-0 flex items-center justify-center rounded-xl transition-all border ${
            isDark
              ? "text-white/60 hover:text-white hover:bg-white/5 border-white/10"
              : "text-[#1c1c1e]/60 hover:text-[#1c1c1e] hover:bg-black/5 border-black/10"
          }`}
        >
          <span className="material-symbols-outlined text-[22px]">menu</span>
        </button>

        {/* Search bar — hidden on mobile unless toggled */}
        {searchPlaceholder && (
          <>
            {/* Desktop search */}
            <div className="relative hidden sm:block w-64 lg:w-80 group">
              <span
                className={`material-symbols-outlined absolute left-4 top-1/2 -translate-y-1/2 text-[20px] transition-colors ${
                  isDark ? "text-white/30" : "text-[#1c1c1e]/40"
                }`}
              >
                search
              </span>
              <input
                type="text"
                placeholder={searchPlaceholder}
                className={`w-full text-[15px] rounded-2xl pl-12 pr-4 py-2.5 outline-none transition-all ${
                  isDark
                    ? "bg-white/5 border border-white/10 text-white placeholder:text-white/30 focus:border-white/20"
                    : "bg-white border border-black/5 text-[#1c1c1e] placeholder:text-[#1c1c1e]/40 focus:border-black/20 focus:shadow-sm hover:bg-black/[0.02]"
                }`}
              />
            </div>

            {/* Mobile search toggle button */}
            <button
              onClick={() => setSearchOpen((v) => !v)}
              aria-label="Toggle search"
              className={`sm:hidden w-10 h-10 flex-shrink-0 flex items-center justify-center rounded-xl transition-all border ${
                isDark
                  ? "text-white/60 hover:text-white hover:bg-white/5 border-white/10"
                  : "text-[#1c1c1e]/60 hover:text-[#1c1c1e] hover:bg-black/5 border-black/10"
              }`}
            >
              <span className="material-symbols-outlined text-[20px]">
                {searchOpen ? "close" : "search"}
              </span>
            </button>
          </>
        )}

        {title && (
          <span
            className={`text-[13px] font-bold tracking-widest uppercase truncate ${
              isDark ? "text-white/40" : "text-[#1c1c1e]/50"
            }`}
          >
            {title}
          </span>
        )}
      </div>

      {/* Right: Actions + Toggle + Notification + Avatar */}
      <div className="flex items-center gap-2 md:gap-4 flex-shrink-0">
        {actions}

        {/* ── Dark/Light Mode Toggle ── */}
        <button
          onClick={toggleTheme}
          aria-label="Toggle dark mode"
          className={`relative w-12 h-6 md:w-14 md:h-7 rounded-full transition-all duration-300 focus:outline-none flex-shrink-0 ${
            isDark ? "bg-[#EBDCFF]" : "bg-[#1c1c1e]"
          }`}
        >
          <span
            className={`absolute top-[3px] w-[18px] h-[18px] md:w-[22px] md:h-[22px] rounded-full shadow-md flex items-center justify-center transition-all duration-300 ${
              isDark
                ? "translate-x-[27px] md:translate-x-[30px] bg-[#1c1c1e]"
                : "translate-x-[3px] bg-white"
            }`}
          >
            {isDark ? (
              <svg width="10" height="10" viewBox="0 0 24 24" fill="currentColor" className="text-[#EBDCFF]">
                <path d="M21 12.79A9 9 0 1 1 11.21 3a7 7 0 1 0 9.79 9.79z" />
              </svg>
            ) : (
              <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" className="text-[#1c1c1e]">
                <circle cx="12" cy="12" r="5" />
                <line x1="12" y1="1" x2="12" y2="3" />
                <line x1="12" y1="21" x2="12" y2="23" />
                <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
                <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
                <line x1="1" y1="12" x2="3" y2="12" />
                <line x1="21" y1="12" x2="23" y2="12" />
                <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
                <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
              </svg>
            )}
          </span>
        </button>

        {/* Notification */}
        <button
          aria-label="Notifications"
          className={`hidden sm:flex w-9 h-9 md:w-10 md:h-10 rounded-full items-center justify-center transition-all outline-none shadow-sm border ${
            isDark
              ? "bg-white/5 border-white/10 text-white/50 hover:text-white hover:bg-white/10"
              : "bg-white border-black/5 text-[#1c1c1e]/50 hover:text-[#1c1c1e] hover:bg-black/5"
          }`}
        >
          <span className="material-symbols-outlined text-[18px] md:text-[20px]">notifications</span>
        </button>

        <div className={`hidden sm:block w-px h-6 ${isDark ? "bg-white/10" : "bg-black/10"}`}></div>

        {/* Avatar */}
        <button
          className="flex items-center gap-3 group text-left"
          onClick={() => setLocation("/settings")}
          aria-label="Go to settings"
        >
          <div
            className={`w-9 h-9 md:w-10 md:h-10 rounded-full overflow-hidden border-2 shadow-sm transition-all flex-shrink-0 ${
              isDark
                ? "border-white/10 group-hover:border-[#EBDCFF]/60"
                : "border-white group-hover:border-[#EBDCFF]"
            }`}
          >
            <img
              src="https://i.pravatar.cc/150?u=admin"
              alt="User avatar"
              className="w-full h-full object-cover"
            />
          </div>
          <div className="hidden lg:block">
            <p
              className={`text-[14px] font-bold leading-tight ${
                isDark ? "text-[#F5F5F7]" : "text-[#1c1c1e]"
              }`}
            >
              Admin User
            </p>
            <p
              className={`text-[11px] uppercase tracking-widest font-bold mt-0.5 ${
                isDark ? "text-white/40" : "text-[#1c1c1e]/50"
              }`}
            >
              Architect
            </p>
          </div>
        </button>
      </div>

      {/* Mobile search dropdown */}
      {searchOpen && searchPlaceholder && (
        <div
          className={`absolute top-full left-0 right-0 px-4 py-3 z-20 sm:hidden border-b ${
            isDark
              ? "bg-[#111115]/95 backdrop-blur-md border-white/5"
              : "bg-[#F5F5F7]/95 backdrop-blur-md border-black/5"
          }`}
        >
          <div className="relative">
            <span
              className={`material-symbols-outlined absolute left-4 top-1/2 -translate-y-1/2 text-[20px] ${
                isDark ? "text-white/30" : "text-[#1c1c1e]/40"
              }`}
            >
              search
            </span>
            <input
              autoFocus
              type="text"
              placeholder={searchPlaceholder}
              className={`w-full text-[15px] rounded-2xl pl-12 pr-4 py-3 outline-none transition-all ${
                isDark
                  ? "bg-white/5 border border-white/10 text-white placeholder:text-white/30 focus:border-white/20"
                  : "bg-white border border-black/10 text-[#1c1c1e] placeholder:text-[#1c1c1e]/40 focus:border-black/20"
              }`}
            />
          </div>
        </div>
      )}
    </header>
  );
}
