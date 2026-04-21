import { useLocation } from "wouter";
import { useTheme } from "../contexts/ThemeContext";

type NavItem = {
  label: string;
  icon: string;
  href: string;
};

const NAV_ITEMS: NavItem[] = [
  { label: "Dashboard", icon: "dashboard", href: "/dashboard" },
  { label: "Analytics", icon: "insights", href: "/analytics" },
  { label: "Models", icon: "psychology", href: "/models" },
  { label: "Settings", icon: "settings", href: "/settings" },
];

interface SidebarProps {
  onNewBot?: () => void;
}

export default function Sidebar({ onNewBot }: SidebarProps) {
  const [location, setLocation] = useLocation();
  const { isDark } = useTheme();

  const isActive = (href: string) => location === href;

  return (
    <aside
      className={`w-64 flex-shrink-0 flex flex-col h-screen sticky top-0 font-sans transition-colors duration-300 ${
        isDark
          ? "bg-[#111115] border-r border-white/5"
          : "bg-[#1c1c1e] border-r border-white/5"
      }`}
    >
      {/* Brand */}
      <div
        className="h-20 flex items-center gap-3 px-6 border-b border-white/5 cursor-pointer flex-shrink-0 group"
        onClick={() => setLocation("/")}
      >
        <div className="w-10 h-10 rounded-xl bg-[#EBDCFF] flex items-center justify-center flex-shrink-0 transition-transform group-hover:scale-105">
          <svg
            width="24"
            height="24"
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
        <div>
          <p
            className="text-[#fbfbf2] font-serif font-bold text-xl leading-tight"
            style={{ fontFamily: "'Playfair Display', serif" }}
          >
            Aina
          </p>
          <p className="text-white/40 text-[10px] uppercase tracking-[0.2em] font-bold">
            Platform
          </p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-1.5 overflow-y-auto">
        <p className="text-[10px] uppercase tracking-widest text-white/30 font-bold px-3 pt-4 pb-2">
          Overview
        </p>
        {NAV_ITEMS.map((item) => {
          const active = isActive(item.href);
          return (
            <a
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-4 py-3 rounded-xl text-[14px] font-semibold transition-all duration-200 group ${
                active
                  ? "bg-[#EBDCFF] text-[#1c1c1e] shadow-sm"
                  : "text-white/60 hover:text-[#fbfbf2] hover:bg-white/5"
              }`}
            >
              <span
                className={`material-symbols-outlined text-[20px] flex-shrink-0 transition-colors ${
                  active
                    ? "text-[#1c1c1e]"
                    : "text-white/40 group-hover:text-white/80"
                }`}
              >
                {item.icon}
              </span>
              {item.label}
              {active && (
                <span className="ml-auto w-1.5 h-1.5 rounded-full bg-[#1c1c1e]"></span>
              )}
            </a>
          );
        })}
      </nav>

      {/* Bottom Section */}
      <div className="p-4 border-t border-white/5 space-y-2 flex-shrink-0">
        <button
          onClick={() => setLocation("/builder")}
          className="w-full bg-[#EBDCFF] hover:bg-[#d8bfff] text-[#1c1c1e] font-bold py-3.5 rounded-xl flex items-center justify-center gap-2 text-[14px] transition-colors mb-4 shadow-sm"
        >
          <span className="material-symbols-outlined text-[18px]">add</span>
          New Agent
        </button>

        <a
          href="mailto:support@aina.ai"
          className="flex items-center gap-3 px-4 py-3 rounded-xl text-[14px] font-semibold text-white/60 hover:text-[#fbfbf2] hover:bg-white/5 transition-all"
        >
          <span className="material-symbols-outlined text-[20px] text-white/40">
            help_outline
          </span>
          Help & Support
        </a>

        <button
          onClick={() => setLocation("/login")}
          className="flex items-center gap-3 px-4 py-3 rounded-xl text-[14px] font-semibold text-white/60 hover:text-white hover:bg-white/5 transition-all w-full"
        >
          <span className="material-symbols-outlined text-[20px] text-white/40">
            logout
          </span>
          Sign Out
        </button>
      </div>
    </aside>
  );
}
