import { useEffect, useState } from "react";
import { useTheme } from "../../../contexts/ThemeContext";

interface ChannelItem {
  channel: string;
  count: number;
}

interface ChannelPerfProps {
  days: number;
  chatbotId: string;
}

export default function ChannelPerf({ days, chatbotId }: ChannelPerfProps) {
  const { isDark } = useTheme();
  const c = (light: string, dark: string) => (isDark ? dark : light);
  const [data, setData] = useState<ChannelItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchChannels() {
      setLoading(true);
      try {
        const token = localStorage.getItem("token");
        const headers: Record<string, string> = { "Content-Type": "application/json" };
        if (token) headers["Authorization"] = `Bearer ${token}`;

        const params = new URLSearchParams({ days: String(days) });
        if (chatbotId) params.set("chatbot_id", chatbotId);

        const res = await fetch(`http://localhost:8000/api/v1/analytics/channels?${params}`, { headers });
        if (res.ok) setData(await res.json());
      } catch (err) {
        console.error("Error fetching channels:", err);
      } finally {
        setLoading(false);
      }
    }
    fetchChannels();
  }, [days, chatbotId]);

  const totalCount = data.reduce((sum, item) => sum + item.count, 0);
  const hasData = totalCount > 0;

  const channels = data.map((item) => {
    const isWhatsApp = item.channel.toLowerCase().includes("whatsapp");
    const pct = totalCount > 0 ? Math.round((item.count / totalCount) * 100) : 0;
    return {
      name: isWhatsApp ? "WhatsApp" : item.channel,
      icon: isWhatsApp ? "chat" : "language",
      pct,
      count: item.count,
      color: isWhatsApp
        ? isDark ? "#EBDCFF" : "#1c1c1e"
        : isDark ? "rgba(255,255,255,0.3)" : "rgba(0,0,0,0.2)",
    };
  });

  return (
    <div
      className={`rounded-[2rem] border p-4 sm:p-8 ${
        isDark
          ? "bg-[#1f1f23] border-white/[0.06]"
          : "bg-white border-black/5 shadow-[0_8px_30px_rgb(0,0,0,0.02)]"
      }`}
    >
      {/* Header — LIVE badge removed (data is from nightly aggregation, not real-time) */}
      <h3
        className={`text-[18px] font-serif font-bold mb-8 ${c("text-[#1c1c1e]", "text-white")}`}
        style={{ fontFamily: "'Playfair Display', serif" }}
      >
        Channel Distribution
      </h3>

      <div className="space-y-6">
        {loading ? (
          <div className="space-y-6 animate-pulse">
            {[1, 2].map((i) => (
              <div key={i} className="space-y-2.5">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className={`w-[18px] h-[18px] rounded-full ${isDark ? "bg-white/5" : "bg-black/5"}`} />
                    <div className={`h-4 w-20 rounded ${isDark ? "bg-white/5" : "bg-black/5"}`} />
                  </div>
                  <div className={`h-4 w-8 rounded ${isDark ? "bg-white/5" : "bg-black/5"}`} />
                </div>
                <div className={`w-full h-1.5 rounded-full ${isDark ? "bg-white/5" : "bg-black/5"}`} />
              </div>
            ))}
          </div>
        ) : !hasData ? (
          <div className="flex flex-col items-center justify-center py-8 gap-3">
            <span
              className={`material-symbols-outlined text-[40px] ${c("text-[#1c1c1e]/20", "text-white/15")}`}
              aria-hidden="true"
            >
              device_hub
            </span>
            <p className={`text-[13px] font-medium ${c("text-[#1c1c1e]/40", "text-white/30")}`}>
              No channel data for this period
            </p>
          </div>
        ) : (
          channels.map((ch) => (
            <div key={ch.name}>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-3">
                  <span
                    className={`material-symbols-outlined text-[18px] ${c("text-[#1c1c1e]/50", "text-[#85948b]")}`}
                    aria-hidden="true"
                  >
                    {ch.icon}
                  </span>
                  <span className={`text-[14px] font-bold ${c("text-[#1c1c1e]", "text-white")}`}>
                    {ch.name}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`text-[12px] font-medium ${c("text-[#1c1c1e]/40", "text-white/30")}`}>
                    {ch.count.toLocaleString()}
                  </span>
                  <span className={`text-[13px] font-bold ${c("text-[#1c1c1e]", "text-white")}`}>
                    {ch.pct}%
                  </span>
                </div>
              </div>
              <div className={`w-full h-1.5 rounded-full overflow-hidden ${c("bg-black/5", "bg-[#131317]")}`}>
                <div
                  className="h-full rounded-full"
                  style={{ width: `${ch.pct}%`, backgroundColor: ch.color }}
                />
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
