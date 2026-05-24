import { useState, useEffect } from "react";
import { useLocation } from "wouter";
import { useTheme } from "../contexts/ThemeContext";
import { useAuth } from "../contexts/AuthContext";
import { useNotifications } from "../contexts/NotificationContext";

interface TopBarProps {
  title?: string;
  searchPlaceholder?: string;
  actions?: React.ReactNode;
  onMenuToggle?: () => void;
}

interface NotificationItem {
  id: string;
  title: string;
  details: string;
  timestamp: string;
  read: boolean;
}

export default function TopBar({ title, searchPlaceholder, actions, onMenuToggle }: TopBarProps) {
  const [, setLocation] = useLocation();
  const { isDark, toggleTheme } = useTheme();
  const [searchOpen, setSearchOpen] = useState(false);

  const { userMe, isLoadingProfile } = useAuth();

  // Dynamic user profile state derived from global auth context
  const fullName = userMe?.user.full_name || "Admin User";
  const isOwner = userMe ? (userMe.user.id === userMe.active_organization?.owner_id) : false;
  const avatarUrl = userMe?.user.full_name
    ? `https://ui-avatars.com/api/?name=${encodeURIComponent(
        userMe.user.full_name
      )}&background=EBDCFF&color=1c1c1e&bold=true&size=100`
    : "https://i.pravatar.cc/150?u=admin";

  const {
    notifications,
    markAsRead,
    markAllAsRead,
    dismissNotification,
    clearAllNotifications
  } = useNotifications();
  const [notificationsOpen, setNotificationsOpen] = useState(false);

  function formatRelativeTime(dateString: string): string {
    try {
      const date = new Date(dateString);
      if (isNaN(date.getTime())) return dateString;

      const now = new Date();
      const diffMs = now.getTime() - date.getTime();
      const diffSecs = Math.floor(diffMs / 1000);
      const diffMins = Math.floor(diffSecs / 60);
      const diffHours = Math.floor(diffMins / 60);
      const diffDays = Math.floor(diffHours / 24);

      if (diffSecs < 60) {
        return "Just now";
      } else if (diffMins < 60) {
        return `${diffMins}m ago`;
      } else if (diffHours < 24) {
        return `${diffHours}h ago`;
      } else if (diffDays === 1) {
        return "Yesterday";
      } else {
        return date.toLocaleDateString(undefined, { month: "short", day: "numeric" });
      }
    } catch (e) {
      return dateString;
    }
  }

  // Close notifications panel on outside click
  useEffect(() => {
    if (!notificationsOpen) return;

    const handleOutsideClick = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      if (!target.closest(".notification-container")) {
        setNotificationsOpen(false);
      }
    };

    document.addEventListener("click", handleOutsideClick);
    return () => {
      document.removeEventListener("click", handleOutsideClick);
    };
  }, [notificationsOpen]);

  return (
    <header
      className={`h-16 flex items-center justify-between px-4 md:px-8 flex-shrink-0 z-30 sticky top-0 transition-colors duration-300 gap-3 ${
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

        {/* Notification bell and dropdown container */}
        <div className="relative notification-container">
          <button
            onClick={() => setNotificationsOpen((prev) => !prev)}
            aria-label="Notifications"
            className={`flex w-9 h-9 md:w-10 md:h-10 rounded-full items-center justify-center transition-all outline-none focus-visible:ring-2 focus-visible:ring-[#EBDCFF] focus-visible:ring-offset-2 dark:focus-visible:ring-offset-[#131317] shadow-sm border relative cursor-pointer ${
              isDark
                ? "bg-white/5 border-white/10 text-white/50 hover:text-white hover:bg-white/10"
                : "bg-white border-black/5 text-[#1c1c1e]/50 hover:text-[#1c1c1e] hover:bg-black/5"
            }`}
          >
            <span className="material-symbols-outlined text-[18px] md:text-[20px]" aria-hidden="true">notifications</span>

            {/* Unread badge count indicator */}
            {notifications.some((n) => !n.read) && (
              <span
                className={`absolute top-1 right-1 w-2.5 h-2.5 bg-[#EBDCFF] rounded-full border ${
                  isDark ? "border-[#111115]" : "border-white"
                }`}
              />
            )}
          </button>

          {/* Notifications Popover List */}
          {notificationsOpen && (
            <div
              className={`absolute right-[-40px] sm:right-0 mt-2 w-[280px] sm:w-80 rounded-2xl shadow-2xl border overflow-hidden transition-all duration-300 z-50 ${
                isDark
                  ? "bg-[#1f1f23] border-white/[0.06] text-white"
                  : "bg-white border-black/5 text-[#1c1c1e]"
              }`}
            >
              {/* Popover Header */}
              <div
                className={`px-4 py-3 flex items-center justify-between border-b ${
                  isDark ? "border-white/5" : "border-black/5"
                }`}
              >
                <span className="font-bold text-[14px]">Notifications</span>
                <div className="flex gap-2">
                  {notifications.some((n) => !n.read) && (
                    <button
                      onClick={markAllAsRead}
                      className="text-[11px] font-bold uppercase tracking-wider text-[#d0beed] hover:text-[#EBDCFF] transition-colors cursor-pointer"
                    >
                      Mark all read
                    </button>
                  )}
                  {notifications.length > 0 && (
                    <button
                      onClick={clearAllNotifications}
                      className="text-[11px] font-bold uppercase tracking-wider text-red-400 hover:text-red-300 transition-colors cursor-pointer"
                    >
                      Clear all
                    </button>
                  )}
                </div>
              </div>

              {/* Popover List Items */}
              <div className="max-h-64 overflow-y-auto divide-y divide-white/[0.04]">
                {notifications.length === 0 ? (
                  <div className="px-4 py-8 text-center text-[12px] opacity-40">
                    No notifications
                  </div>
                ) : (
                  notifications.map((notif) => (
                    <div
                      key={notif.id}
                      onClick={() => markAsRead(notif.id)}
                      className={`px-4 py-3 text-left transition-colors cursor-pointer relative group/item ${
                        !notif.read
                          ? isDark
                            ? "bg-white/[0.02] hover:bg-white/[0.04]"
                            : "bg-black/[0.01] hover:bg-black/[0.03]"
                          : isDark
                          ? "hover:bg-white/[0.02]"
                          : "hover:bg-black/[0.01]"
                      }`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <span className={`text-[13px] font-bold ${!notif.read ? "text-[#EBDCFF]" : ""}`}>
                          {notif.title}
                        </span>
                        <div className="flex items-center gap-1.5 flex-shrink-0">
                          <span className="text-[10px] opacity-45 whitespace-nowrap">
                            {formatRelativeTime(notif.created_at)}
                          </span>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              dismissNotification(notif.id);
                            }}
                            aria-label={`Dismiss notification: ${notif.title}`}
                            className="opacity-0 group-hover/item:opacity-100 p-0.5 rounded-full hover:bg-white/10 dark:hover:bg-white/5 focus-visible:ring-2 focus-visible:ring-[#EBDCFF] text-[14px] transition-all flex items-center justify-center cursor-pointer outline-none"
                            title="Dismiss notification"
                          >
                            <span className="material-symbols-outlined text-[14px] opacity-60 hover:opacity-100" aria-hidden="true">close</span>
                          </button>
                        </div>
                      </div>
                      <p className="text-[12px] opacity-70 mt-0.5 leading-relaxed pr-4">
                        {notif.details}
                      </p>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>

        <div className={`hidden sm:block w-px h-6 ${isDark ? "bg-white/10" : "bg-black/10"}`}></div>

        {/* Avatar */}
        <button
          className="flex items-center gap-3 group text-left"
          onClick={() => setLocation("/settings")}
          aria-label="Go to settings"
          disabled={isLoadingProfile}
        >
          {isLoadingProfile ? (
            <>
              <div
                className={`w-9 h-9 md:w-10 md:h-10 rounded-full animate-pulse flex-shrink-0 ${
                  isDark ? "bg-white/10" : "bg-black/10"
                }`}
              />
              <div className="hidden lg:block space-y-1">
                <div
                  className={`h-3.5 w-24 rounded animate-pulse ${
                    isDark ? "bg-white/10" : "bg-black/10"
                  }`}
                />
                <div
                  className={`h-2.5 w-12 rounded animate-pulse ${
                    isDark ? "bg-white/5" : "bg-black/5"
                  }`}
                />
              </div>
            </>
          ) : (
            <>
              <div
                className={`w-9 h-9 md:w-10 md:h-10 rounded-full overflow-hidden border-2 shadow-sm transition-all flex-shrink-0 ${
                  isDark
                    ? "border-white/10 group-hover:border-[#EBDCFF]/60"
                    : "border-white group-hover:border-[#EBDCFF]"
                }`}
              >
                <img src={avatarUrl} alt="User avatar" className="w-full h-full object-cover" />
              </div>
              <div className="hidden lg:block">
                <p
                  className={`text-[14px] font-bold leading-tight ${
                    isDark ? "text-[#F5F5F7]" : "text-[#1c1c1e]"
                  }`}
                >
                  {fullName}
                </p>
                <p
                  className={`text-[11px] uppercase tracking-widest font-bold mt-0.5 ${
                    isDark ? "text-white/40" : "text-[#1c1c1e]/50"
                  }`}
                >
                  {isOwner ? "Owner" : "Member"}
                </p>
              </div>
            </>
          )}
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
