import { useEffect, useRef, useState } from "react";
import { useTheme } from "../../../contexts/ThemeContext";

interface Bot {
  id: string;
  name: string;
}

interface GlobalFiltersProps {
  days: number;
  chatbotId: string;
  onDaysChange: (days: number) => void;
  onChatbotChange: (id: string) => void;
}

const PRESET_OPTIONS = [
  { label: "Last 7 Days", value: 7 },
  { label: "Last 30 Days", value: 30 },
  { label: "Last 90 Days", value: 90 },
];

// Returns today's date as "YYYY-MM-DD" for max attr on date inputs
function todayStr() {
  return new Date().toISOString().split("T")[0];
}

// Returns "YYYY-MM-DD" for a date that is `days` days ago
function daysAgoStr(days: number) {
  const d = new Date();
  d.setDate(d.getDate() - days);
  return d.toISOString().split("T")[0];
}

export default function GlobalFilters({
  days,
  chatbotId,
  onDaysChange,
  onChatbotChange,
}: GlobalFiltersProps) {
  const { isDark } = useTheme();
  const [bots, setBots] = useState<Bot[]>([]);
  const [isCustom, setIsCustom] = useState(false);
  const [customFrom, setCustomFrom] = useState(daysAgoStr(30));
  const [customTo, setCustomTo] = useState(todayStr());
  const didMountRef = useRef(false);

  useEffect(() => {
    async function fetchBots() {
      try {
        const token = localStorage.getItem("token");
        const headers: Record<string, string> = { "Content-Type": "application/json" };
        if (token) headers["Authorization"] = `Bearer ${token}`;
        const res = await fetch("http://localhost:8000/api/v1/bots/chatbots", { headers });
        if (res.ok) setBots(await res.json());
      } catch {
        // silently fail
      }
    }
    fetchBots();
  }, []);

  // When custom dates change, compute days and propagate up
  useEffect(() => {
    if (!isCustom) return;
    if (!didMountRef.current) { didMountRef.current = true; return; }
    const from = new Date(customFrom);
    const to = new Date(customTo);
    const diffDays = Math.max(1, Math.round((to.getTime() - from.getTime()) / 86400000));
    onDaysChange(diffDays);
  }, [customFrom, customTo]);

  const handlePresetChange = (val: string) => {
    if (val === "custom") {
      setIsCustom(true);
      // Initialize custom dates from current days value
      setCustomFrom(daysAgoStr(days));
      setCustomTo(todayStr());
      didMountRef.current = false;
    } else {
      setIsCustom(false);
      onDaysChange(Number(val));
    }
  };

  // Determine the select value — if none of the presets match the current days, show "custom"
  const selectValue = isCustom
    ? "custom"
    : PRESET_OPTIONS.find((o) => o.value === days)
    ? String(days)
    : "custom";

  const selectClass = `border rounded-xl px-4 py-2.5 text-[13px] font-medium outline-none shadow-sm cursor-pointer transition-[border-color,box-shadow] duration-200 focus-visible:ring-1 ${
    isDark
      ? "bg-[#131317] border-white/[0.06] text-white/80 focus-visible:ring-[#EBDCFF] focus-visible:border-transparent"
      : "bg-[#F5F5F7] border-black/5 text-[#1c1c1e]/80 focus-visible:ring-black/20 focus:border-black/20"
  }`;

  const dateInputClass = `border rounded-xl px-3 py-2.5 text-[13px] font-medium outline-none shadow-sm cursor-pointer transition-[border-color] duration-200 focus-visible:ring-1 ${
    isDark
      ? "bg-[#131317] border-white/[0.06] text-white/80 focus-visible:ring-[#EBDCFF] [color-scheme:dark]"
      : "bg-[#F5F5F7] border-black/5 text-[#1c1c1e]/80 focus-visible:ring-black/20"
  }`;

  return (
    <div className="flex flex-wrap items-center gap-3 mb-8">
      <span
        className={`text-[11px] font-bold uppercase tracking-[0.15em] mr-1 ${
          isDark ? "text-white/30" : "text-[#1c1c1e]/40"
        }`}
      >
        Filter by
      </span>

      {/* Date range preset */}
      <select
        id="global-date-range"
        value={selectValue}
        onChange={(e) => handlePresetChange(e.target.value)}
        className={selectClass}
        aria-label="Date range filter"
      >
        {PRESET_OPTIONS.map((opt) => (
          <option key={opt.value} value={String(opt.value)}>
            {opt.label}
          </option>
        ))}
        <option value="custom">Custom Range</option>
      </select>

      {/* Custom date pickers — shown only when Custom is selected */}
      {isCustom && (
        <>
          <span className={`text-[12px] font-medium ${isDark ? "text-white/30" : "text-[#1c1c1e]/40"}`}>
            From
          </span>
          <input
            id="custom-date-from"
            type="date"
            value={customFrom}
            max={customTo}
            onChange={(e) => setCustomFrom(e.target.value)}
            className={dateInputClass}
            aria-label="Custom start date"
          />
          <span className={`text-[12px] font-medium ${isDark ? "text-white/30" : "text-[#1c1c1e]/40"}`}>
            to
          </span>
          <input
            id="custom-date-to"
            type="date"
            value={customTo}
            min={customFrom}
            max={todayStr()}
            onChange={(e) => setCustomTo(e.target.value)}
            className={dateInputClass}
            aria-label="Custom end date"
          />
        </>
      )}

      {/* Bot selector — only shown when user has multiple bots */}
      {bots.length > 1 && (
        <select
          id="global-bot-filter"
          value={chatbotId}
          onChange={(e) => onChatbotChange(e.target.value)}
          className={selectClass}
          aria-label="Agent filter"
        >
          <option value="">All Agents</option>
          {bots.map((bot) => (
            <option key={bot.id} value={bot.id}>
              {bot.name}
            </option>
          ))}
        </select>
      )}
    </div>
  );
}
