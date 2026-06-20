import { useState } from "react";
import { ChevronDown, Download, FileText, Loader2, Table2 } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "../../components/ui/dropdown-menu";
import { useTheme } from "../../contexts/ThemeContext";
import { useLayoutConfig } from "../../contexts/LayoutContext";
import { api } from "../../lib/api";
import { toast } from "sonner";
import GlobalFilters from "./components/GlobalFilters";
import KPIs from "./components/KPIs";
import VolumeChart from "./components/VolumeChart";
import LanguageMix from "./components/LanguageMix";
import ChannelPerf from "./components/ChannelPerf";
import InteractionsTable from "./components/InteractionsTable";

export default function Analytics() {
  const { isDark } = useTheme();
  const c = (light: string, dark: string) => (isDark ? dark : light);

  const [days, setDays] = useState(30);
  const [chatbotId, setChatbotId] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [exporting, setExporting] = useState(false);

  const triggerDownload = (blob: Blob, filename: string) => {
    const url = window.URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = filename;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    window.setTimeout(() => window.URL.revokeObjectURL(url), 1000);
  };

  const handleExport = async (reportType: "analytics" | "conversations", format: "csv" | "pdf") => {
    if (exporting) return;

    setExporting(true);
    try {
      const token = localStorage.getItem("token");
      const headers: Record<string, string> = {};
      if (token) headers.Authorization = `Bearer ${token}`;

      const params = new URLSearchParams({
        report_type: reportType,
        format,
        days: String(days),
      });
      if (chatbotId) params.set("chatbot_id", chatbotId);
      if (reportType === "conversations" && statusFilter) params.set("status", statusFilter);

      const response = await fetch(`${api.baseUrl}/api/v1/analytics/export?${params}`, { headers });
      if (!response.ok) {
        let message = "Failed to export report.";
        try {
          const data = await response.json();
          message = data.detail || message;
        } catch {
          message = response.statusText || message;
        }
        throw new Error(message);
      }

      const blob = await response.blob();
      const statusSuffix = reportType === "conversations" && statusFilter ? `-${statusFilter}` : "";
      const filename = `${reportType}-report-${days}d${statusSuffix}.${format}`;
      triggerDownload(blob, filename);
      toast.success("Export downloaded.");
    } catch (error: any) {
      console.error("Export failed:", error);
      toast.error(error?.message || "Could not export report.");
    } finally {
      setExporting(false);
    }
  };

  const exportActions = (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button
          className={`px-4 py-2 rounded-xl border transition-[color,background-color,border-color,box-shadow] duration-200 text-[13px] font-bold flex items-center gap-2 shadow-sm focus-visible:ring-2 outline-none ${
            isDark
              ? "border-white/10 bg-transparent hover:bg-white/[0.04] text-[#bbcac0] hover:text-white focus-visible:ring-[#EBDCFF]/20"
              : "border-black/5 bg-white hover:bg-black/5 text-[#1c1c1e] focus-visible:ring-black/20"
          }`}
          disabled={exporting}
          aria-busy={exporting}
        >
          {exporting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Download className="h-4 w-4" />}
          <span className="hidden sm:inline">Export</span>
          <ChevronDown className="h-3.5 w-3.5 opacity-70" />
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-56">
        <DropdownMenuLabel>Analytics Report</DropdownMenuLabel>
        <DropdownMenuItem onSelect={() => void handleExport("analytics", "csv")}>
          <Table2 className="h-4 w-4" />
          CSV
        </DropdownMenuItem>
        <DropdownMenuItem onSelect={() => void handleExport("analytics", "pdf")}>
          <FileText className="h-4 w-4" />
          PDF
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuLabel>Conversation Report</DropdownMenuLabel>
        <DropdownMenuItem onSelect={() => void handleExport("conversations", "csv")}>
          <Table2 className="h-4 w-4" />
          CSV
        </DropdownMenuItem>
        <DropdownMenuItem onSelect={() => void handleExport("conversations", "pdf")}>
          <FileText className="h-4 w-4" />
          PDF
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );

  useLayoutConfig({
    title: "Intelligence Analytics",
    actions: exportActions,
  });

  return (
    <main className="flex-1 overflow-y-auto p-4 sm:p-8 lg:p-12 z-10">
      <div className="mb-10">
        <span
          className={`text-[11px] font-bold tracking-[0.2em] uppercase mb-3 block ${
            c("text-[#1c1c1e]/40", "text-white/30")
          }`}
        >
          Intelligence
        </span>
        <h1
          className={`text-[2.5rem] lg:text-[3.5rem] font-bold tracking-tight leading-none mb-3 ${
            c("text-[#1c1c1e]", "text-white")
          }`}
          style={{ fontFamily: "'Playfair Display', serif" }}
        >
          Performance Analytics
        </h1>
        <p
          className={`text-lg max-w-2xl font-medium ${
            c("text-[#1c1c1e]/60", "text-white/50")
          }`}
        >
          Real-time insights across all active agents and conversation clusters.
        </p>
      </div>

      <GlobalFilters
        days={days}
        chatbotId={chatbotId}
        onDaysChange={setDays}
        onChatbotChange={setChatbotId}
      />

      <KPIs days={days} chatbotId={chatbotId} />

      <VolumeChart days={days} chatbotId={chatbotId} />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <LanguageMix days={days} chatbotId={chatbotId} />
        <ChannelPerf days={days} chatbotId={chatbotId} />
      </div>

      <InteractionsTable
        days={days}
        chatbotId={chatbotId}
        statusFilter={statusFilter}
        onStatusFilterChange={setStatusFilter}
      />
    </main>
  );
}
