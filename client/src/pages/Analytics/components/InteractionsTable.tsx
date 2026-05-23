import { useEffect, useState } from "react";
import { useTheme } from "../../../contexts/ThemeContext";

interface Interaction {
  id: string;
  chatbot_id: string;
  chatbot_name: string;
  status: string;
  total_messages: number;
  started_at: string;
}

export default function InteractionsTable() {
  const { isDark } = useTheme();
  const c = (light: string, dark: string) => (isDark ? dark : light);
  const [data, setData] = useState<Interaction[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchInteractions() {
      try {
        const token = localStorage.getItem("token");
        const headers: Record<string, string> = {
          "Content-Type": "application/json",
        };
        if (token) {
          headers["Authorization"] = `Bearer ${token}`;
        }
        const response = await fetch("http://localhost:8000/api/v1/analytics/interactions?limit=15", {
          headers,
        });
        if (response.ok) {
          const json = await response.json();
          setData(json);
        }
      } catch (err) {
        console.error("Error fetching interactions:", err);
      } finally {
        setLoading(false);
      }
    }
    fetchInteractions();
  }, []);

  const formatRelativeTime = (dateString: string) => {
    const now = new Date();
    const past = new Date(dateString);
    const diffMs = now.getTime() - past.getTime();
    const diffMins = Math.max(1, Math.floor(diffMs / 60000));
    if (diffMins < 60) {
      return `${diffMins} min${diffMins > 1 ? "s" : ""} ago`;
    }
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) {
      return `${diffHours} hour${diffHours > 1 ? "s" : ""} ago`;
    }
    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays} day${diffDays > 1 ? "s" : ""} ago`;
  };

  const getStatusColor = (status: string) => {
    const s = status.toLowerCase();
    if (s === "escalated") return "#EF4444"; // Red for escalated
    if (s === "ongoing") return isDark ? "#EBDCFF" : "#1c1c1e"; // Purple/Dark
    return isDark ? "rgba(255,255,255,0.4)" : "rgba(0,0,0,0.3)"; // Gray for resolved
  };

  return (
    <div
      className={`rounded-[2rem] border overflow-hidden ${
        isDark
          ? "bg-[#1f1f23] border-white/[0.06]"
          : "bg-white border-black/5 shadow-[0_8px_30px_rgb(0,0,0,0.02)]"
      }`}
    >
      <div
        className={`flex flex-col sm:flex-row items-center justify-between px-6 sm:px-8 py-5 sm:py-6 border-b gap-4 ${
          c("border-black/5", "border-white/[0.06]")
        }`}
      >
        <h3
          className={`text-[20px] font-serif font-bold ${
            c("text-[#1c1c1e]", "text-white")
          }`}
          style={{ fontFamily: "'Playfair Display', serif" }}
        >
          Recent Interactions
        </h3>
        <button
          className={`text-[13px] font-bold transition-all flex items-center gap-1.5 focus-visible:ring-2 rounded-lg px-2 py-1 outline-none ${
            c(
              "text-[#1c1c1e] hover:text-[#1c1c1e]/70 focus-visible:ring-[#1c1c1e]/20",
              "text-[#EBDCFF] hover:text-white focus-visible:ring-[#EBDCFF]/20"
            )
          }`}
        >
          View All Directory
          <span className="material-symbols-outlined text-[16px]" aria-hidden="true">arrow_forward</span>
        </button>
      </div>
      
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className={isDark ? "bg-black/20" : "bg-[#F5F5F7]/50"}>
              {["Conversation ID", "Status", "Agent Focus / Bot", "Messages", "Timestamp", ""].map((h) => (
                <th
                  key={h}
                  className={`px-4 sm:px-8 py-3.5 sm:py-4 text-[11px] font-bold uppercase tracking-[0.15em] border-b whitespace-nowrap ${
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
              [1, 2, 3, 4].map((i) => (
                <tr key={i} className="animate-pulse">
                  <td className="px-4 sm:px-8 py-4 sm:py-5">
                    <div className={`h-4.5 w-16 rounded ${isDark ? "bg-white/5" : "bg-black/5"}`} />
                  </td>
                  <td className="px-4 sm:px-8 py-4 sm:py-5">
                    <div className="flex items-center gap-3">
                      <div className={`w-2.5 h-2.5 rounded-full ${isDark ? "bg-white/5" : "bg-black/5"}`} />
                      <div className={`h-4.5 w-16 rounded ${isDark ? "bg-white/5" : "bg-black/5"}`} />
                    </div>
                  </td>
                  <td className="px-4 sm:px-8 py-4 sm:py-5">
                    <div className={`h-4.5 w-28 rounded ${isDark ? "bg-white/5" : "bg-black/5"}`} />
                  </td>
                  <td className="px-4 sm:px-8 py-4 sm:py-5">
                    <div className={`h-4 w-6 rounded ${isDark ? "bg-white/5" : "bg-black/5"}`} />
                  </td>
                  <td className="px-4 sm:px-8 py-4 sm:py-5">
                    <div className={`h-4.5 w-20 rounded ${isDark ? "bg-white/5" : "bg-black/5"}`} />
                  </td>
                  <td className="px-4 sm:px-8 py-4 sm:py-5 text-right">
                    <div className={`h-8 w-8 rounded-lg ml-auto ${isDark ? "bg-white/5" : "bg-black/5"}`} />
                  </td>
                </tr>
              ))
            ) : data.length === 0 ? (
              <tr>
                <td colSpan={6} className={`px-8 py-8 text-center text-[14px] ${c("text-[#1c1c1e]/50", "text-white/40")}`}>
                  No recent interactions
                </td>
              </tr>
            ) : (
              data.map((row) => {
                const displayId = `#${row.id.substring(0, 8).toUpperCase()}`;
                const displayStatus = row.status.charAt(0).toUpperCase() + row.status.slice(1);
                return (
                  <tr
                    key={row.id}
                    className={`transition-colors ${
                      isDark ? "hover:bg-white/[0.02]" : "hover:bg-black/[0.02]"
                    }`}
                  >
                    <td
                      className={`px-4 sm:px-8 py-4 sm:py-5 font-mono text-[13px] font-bold ${
                        c("text-[#1c1c1e]", "text-[#EBDCFF]")
                      }`}
                    >
                      {displayId}
                    </td>
                    <td className="px-4 sm:px-8 py-4 sm:py-5">
                      <div className="flex items-center gap-3">
                        <div
                          className="w-2.5 h-2.5 rounded-full shadow-sm"
                          style={{ backgroundColor: getStatusColor(row.status) }}
                        ></div>
                        <span
                          className={`text-[13px] font-semibold ${
                            c("text-[#1c1c1e]", "text-white")
                          }`}
                        >
                          {displayStatus}
                        </span>
                      </div>
                    </td>
                    <td
                      className={`px-4 sm:px-8 py-4 sm:py-5 text-[14px] font-medium ${
                        c("text-[#1c1c1e]/70", "text-[#bbcac0]")
                      }`}
                    >
                      {row.chatbot_name}
                    </td>
                    <td
                      className={`px-4 sm:px-8 py-4 sm:py-5 text-[13px] font-bold ${
                        c("text-[#1c1c1e]/70", "text-white/60")
                      }`}
                    >
                      {row.total_messages}
                    </td>
                    <td
                      className={`px-4 sm:px-8 py-4 sm:py-5 text-[13px] font-medium whitespace-nowrap tabular-nums ${
                        c("text-[#1c1c1e]/50", "text-white/40")
                      }`}
                    >
                      {formatRelativeTime(row.started_at)}
                    </td>
                    <td className="px-4 sm:px-8 py-4 sm:py-5 text-right">
                      <button
                        aria-label={`Options for conversation ${displayId}`}
                        className={`w-9 h-9 flex items-center justify-center rounded-xl transition-[color,background-color,border-color,box-shadow] duration-200 outline-none border focus-visible:ring-2 ${
                          isDark
                            ? "text-white/30 hover:text-white hover:bg-white/5 border-transparent hover:border-white/10 focus-visible:ring-[#EBDCFF]/20"
                            : "text-[#1c1c1e]/40 hover:text-[#1c1c1e] hover:bg-black/5 border-transparent hover:border-black/5 focus-visible:ring-[#1c1c1e]/20"
                        }`}
                      >
                        <span className="material-symbols-outlined text-[18px]" aria-hidden="true">more_horiz</span>
                      </button>
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
