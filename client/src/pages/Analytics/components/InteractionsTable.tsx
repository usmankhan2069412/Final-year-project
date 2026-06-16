import { useEffect, useState } from "react";
import { useTheme } from "../../../contexts/ThemeContext";

interface Interaction {
  id: string;
  chatbot_id: string;
  chatbot_name: string;
  status: string;
  total_messages: number;
  started_at: string;
  duration_seconds: number | null;
}

interface InteractionsTableProps {
  days: number;
  chatbotId: string;
}

const STATUS_OPTIONS = [
  { label: "All", value: "" },
  { label: "Ongoing", value: "ongoing" },
  { label: "Resolved", value: "resolved" },
  { label: "Escalated", value: "escalated" },
];

function formatDuration(seconds: number | null): string {
  if (seconds === null || seconds < 0) return "—";
  if (seconds < 60) return `${seconds}s`;
  const mins = Math.floor(seconds / 60);
  if (mins < 60) return `${mins}m`;
  const hrs = Math.floor(mins / 60);
  const remMins = mins % 60;
  return remMins > 0 ? `${hrs}h ${remMins}m` : `${hrs}h`;
}

function formatRelativeTime(dateString: string): string {
  const now = new Date();
  const past = new Date(dateString);
  const diffMs = now.getTime() - past.getTime();
  const diffMins = Math.max(1, Math.floor(diffMs / 60000));
  if (diffMins < 60) return `${diffMins}m ago`;
  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours}h ago`;
  const diffDays = Math.floor(diffHours / 24);
  return `${diffDays}d ago`;
}

export default function InteractionsTable({ days, chatbotId }: InteractionsTableProps) {
  const { isDark } = useTheme();
  const c = (light: string, dark: string) => (isDark ? dark : light);
  const [data, setData] = useState<Interaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState("");

  useEffect(() => {
    async function fetchInteractions() {
      setLoading(true);
      try {
        const token = localStorage.getItem("token");
        const headers: Record<string, string> = { "Content-Type": "application/json" };
        if (token) headers["Authorization"] = `Bearer ${token}`;

        const params = new URLSearchParams({ limit: "20", days: String(days) });
        if (statusFilter) params.set("status", statusFilter);
        if (chatbotId) params.set("chatbot_id", chatbotId);

        const res = await fetch(`http://localhost:8000/api/v1/analytics/interactions?${params}`, { headers });
        if (res.ok) setData(await res.json());
      } catch (err) {
        console.error("Error fetching interactions:", err);
      } finally {
        setLoading(false);
      }
    }
    fetchInteractions();
  }, [statusFilter, chatbotId, days]);

  const getStatusStyle = (status: string) => {
    const s = status.toLowerCase();
    if (s === "escalated")
      return {
        dot: isDark ? "#fca5a5" : "#dc2626",
        label: isDark ? "text-red-400" : "text-red-600",
      };
    if (s === "ongoing")
      return {
        dot: isDark ? "#EBDCFF" : "#7c3aed",
        label: isDark ? "text-[#EBDCFF]" : "text-purple-700",
      };
    return {
      dot: isDark ? "rgba(255,255,255,0.4)" : "rgba(0,0,0,0.3)",
      label: isDark ? "text-white/50" : "text-[#1c1c1e]/50",
    };
  };

  const selectClass = `border rounded-xl px-3 py-2 text-[12px] font-bold outline-none cursor-pointer transition-[border-color] duration-200 focus-visible:ring-1 ${
    isDark
      ? "bg-[#131317] border-white/[0.06] text-white/70 focus-visible:ring-[#EBDCFF]"
      : "bg-[#F5F5F7] border-black/5 text-[#1c1c1e]/70 focus-visible:ring-black/20"
  }`;

  const COLS = ["Conversation ID", "Status", "Agent / Bot", "Messages", "Duration", "Started"];

  return (
    <div
      className={`rounded-[2rem] border overflow-hidden ${
        isDark
          ? "bg-[#1f1f23] border-white/[0.06]"
          : "bg-white border-black/5 shadow-[0_8px_30px_rgb(0,0,0,0.02)]"
      }`}
    >
      {/* Header */}
      <div
        className={`flex flex-col sm:flex-row items-start sm:items-center justify-between px-6 sm:px-8 py-5 sm:py-6 border-b gap-4 ${
          c("border-black/5", "border-white/[0.06]")
        }`}
      >
        <h3
          className={`text-[20px] font-serif font-bold ${c("text-[#1c1c1e]", "text-white")}`}
          style={{ fontFamily: "'Playfair Display', serif" }}
        >
          Recent Conversations
        </h3>

        {/* Status filter */}
        <div className="flex items-center gap-3">
          <label
            htmlFor="status-filter"
            className={`text-[11px] font-bold uppercase tracking-[0.12em] ${c("text-[#1c1c1e]/40", "text-white/30")}`}
          >
            Status
          </label>
          <select
            id="status-filter"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className={selectClass}
          >
            {STATUS_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className={isDark ? "bg-black/20" : "bg-[#F5F5F7]/50"}>
              {COLS.map((h) => (
                <th
                  key={h}
                  className={`px-4 sm:px-8 py-3.5 text-[11px] font-bold uppercase tracking-[0.15em] border-b whitespace-nowrap ${
                    isDark
                      ? "text-white/30 border-white/[0.06]"
                      : "text-[#1c1c1e]/40 border-black/5"
                  }`}
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className={isDark ? "divide-y divide-white/[0.04]" : "divide-y divide-black/5"}>
            {loading ? (
              [1, 2, 3, 4, 5].map((i) => (
                <tr key={i} className="animate-pulse">
                  {[1, 2, 3, 4, 5, 6].map((j) => (
                    <td key={j} className="px-4 sm:px-8 py-4">
                      <div className={`h-4 rounded w-16 ${isDark ? "bg-white/5" : "bg-black/5"}`} />
                    </td>
                  ))}
                </tr>
              ))
            ) : data.length === 0 ? (
              <tr>
                <td
                  colSpan={6}
                  className={`px-8 py-10 text-center text-[14px] ${c("text-[#1c1c1e]/50", "text-white/40")}`}
                >
                  {statusFilter
                    ? `No ${statusFilter} conversations found`
                    : "No recent conversations"}
                </td>
              </tr>
            ) : (
              data.map((row) => {
                const displayId = `#${row.id.substring(0, 8).toUpperCase()}`;
                const displayStatus = row.status.charAt(0).toUpperCase() + row.status.slice(1);
                const statusStyle = getStatusStyle(row.status);

                return (
                  <tr
                    key={row.id}
                    className={`transition-colors ${isDark ? "hover:bg-white/[0.02]" : "hover:bg-black/[0.02]"}`}
                  >
                    {/* Conversation ID */}
                    <td
                      className={`px-4 sm:px-8 py-4 font-mono text-[13px] font-bold ${
                        c("text-[#1c1c1e]", "text-[#EBDCFF]")
                      }`}
                    >
                      {displayId}
                    </td>

                    {/* Status */}
                    <td className="px-4 sm:px-8 py-4">
                      <div className="flex items-center gap-2.5">
                        <div
                          className="w-2 h-2 rounded-full flex-shrink-0"
                          style={{ backgroundColor: statusStyle.dot }}
                        />
                        <span className={`text-[13px] font-semibold ${statusStyle.label}`}>
                          {displayStatus}
                        </span>
                      </div>
                    </td>

                    {/* Bot name */}
                    <td
                      className={`px-4 sm:px-8 py-4 text-[14px] font-medium ${
                        c("text-[#1c1c1e]/70", "text-[#bbcac0]")
                      }`}
                    >
                      {row.chatbot_name}
                    </td>

                    {/* Messages */}
                    <td
                      className={`px-4 sm:px-8 py-4 text-[13px] font-bold tabular-nums ${
                        c("text-[#1c1c1e]/70", "text-white/60")
                      }`}
                    >
                      {row.total_messages}
                    </td>

                    {/* Duration — new column */}
                    <td
                      className={`px-4 sm:px-8 py-4 text-[13px] font-medium tabular-nums ${
                        c("text-[#1c1c1e]/50", "text-white/40")
                      }`}
                    >
                      {formatDuration(row.duration_seconds)}
                    </td>

                    {/* Timestamp */}
                    <td
                      className={`px-4 sm:px-8 py-4 text-[13px] font-medium whitespace-nowrap tabular-nums ${
                        c("text-[#1c1c1e]/50", "text-white/40")
                      }`}
                    >
                      {formatRelativeTime(row.started_at)}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
