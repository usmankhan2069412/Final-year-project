import { memo } from "react";
import { useTheme } from "../../../contexts/ThemeContext";
import { cn } from "../../../lib/utils";

interface RuleDisplay {
  label: string;
  model: string;
  provider: string;
  icon: string;
}

interface ActiveModelsTableProps {
  loading: boolean;
  activeRules: RuleDisplay[];
  onEdit: () => void;
}

export const ActiveModelsTable = memo(function ActiveModelsTable({ loading, activeRules, onEdit }: ActiveModelsTableProps) {
  const { isDark } = useTheme();

  return (
    <div className={cn("rounded-[2rem] border overflow-hidden lg:col-span-2", isDark ? "bg-[#1f1f23] border-white/[0.06]" : "bg-white border-black/5 shadow-[0_8px_30px_rgb(0,0,0,0.02)]")}>
      <div className={cn("p-8 border-b flex justify-between items-center", isDark ? "border-white/[0.06]" : "border-black/5")}>
        <div>
          <h3 className={cn("text-[20px] font-serif font-bold", isDark ? "text-white" : "text-[#1c1c1e]")} style={{ fontFamily: "'Playfair Display', serif" }}>
            Active Models
          </h3>
          <p className={cn("text-[13px] font-medium mt-1", isDark ? "text-white/40" : "text-[#1c1c1e]/50")}>
            Models currently powering your chatbot
          </p>
        </div>
        <button
          onClick={onEdit}
          className={cn("px-4 py-2 rounded-xl text-[12px] font-bold border transition-colors cursor-pointer", isDark ? "bg-white/5 border-white/10 hover:bg-white/10 text-white" : "bg-black/5 border-transparent hover:bg-black/10 text-[#1c1c1e]")}
        >
          Edit Configuration
        </button>
      </div>

      {loading ? (
        <div className="p-8 animate-pulse text-center">Loading settings...</div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className={isDark ? "bg-black/20" : "bg-[#F5F5F7]/50"}>
                {["Model", "Assigned Intents", "Status"].map((h) => (
                  <th
                    key={h}
                    className={cn("px-4 sm:px-8 py-3.5 sm:py-4 text-[11px] font-bold uppercase tracking-[0.15em] border-b whitespace-nowrap", isDark ? "text-white/30 border-white/[0.06]" : "text-[#1c1c1e]/40 border-black/5")}
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className={isDark ? "divide-y divide-white/[0.04]" : "divide-y divide-black/5"}>
              {activeRules.length === 0 ? (
                <tr className={cn("transition-colors", isDark ? "hover:bg-white/[0.02]" : "hover:bg-black/[0.02]")}>
                  <td className="px-4 sm:px-8 py-4 sm:py-6">
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 rounded-xl flex items-center justify-center shadow-sm text-[#fff]" style={{ backgroundColor: "#8a5cf5" }}>
                        <span className="material-symbols-outlined text-[20px]">speed</span>
                      </div>
                      <span className={cn("text-[15px] font-bold", isDark ? "text-white" : "text-[#1c1c1e]")}>gpt-4o-mini</span>
                    </div>
                  </td>
                  <td className={cn("px-4 sm:px-8 py-4 sm:py-6 text-[13px] font-medium", isDark ? "text-[#bbcac0]" : "text-[#1c1c1e]/80")}>
                    All Queries (System Default)
                  </td>
                  <td className="px-4 sm:px-8 py-4 sm:py-6">
                    <span className={cn("inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-[11px] font-bold uppercase tracking-wider border shadow-sm", isDark ? "bg-[#EBDCFF]/10 text-[#EBDCFF] border-[#EBDCFF]/20" : "bg-[#1c1c1e] text-[#F5F5F7] border-transparent")}>
                      <span className={cn("w-1.5 h-1.5 rounded-full animate-pulse", isDark ? "bg-[#EBDCFF]" : "bg-[#F5F5F7]")} />
                      Active
                    </span>
                  </td>
                </tr>
              ) : (
                activeRules.map((rule, i) => (
                  <tr key={i} className={cn("transition-colors", isDark ? "hover:bg-white/[0.02]" : "hover:bg-black/[0.02]")}>
                    <td className="px-4 sm:px-8 py-4 sm:py-6">
                      <div className="flex items-center gap-4">
                        <div className="w-10 h-10 rounded-xl flex items-center justify-center shadow-sm text-[#fff]" style={{ backgroundColor: "#8a5cf5" }}>
                          <span className="material-symbols-outlined text-[20px]">{rule.icon}</span>
                        </div>
                        <span className={cn("text-[15px] font-bold", isDark ? "text-white" : "text-[#1c1c1e]")}>{rule.model?.split('/').pop()}</span>
                      </div>
                    </td>
                    <td className={cn("px-4 sm:px-8 py-4 sm:py-6 text-[13px] font-medium", isDark ? "text-[#bbcac0]" : "text-[#1c1c1e]/80")}>
                      {rule.label}
                    </td>
                    <td className="px-4 sm:px-8 py-4 sm:py-6">
                      <span className={cn("inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-[11px] font-bold uppercase tracking-wider border shadow-sm", isDark ? "bg-[#EBDCFF]/10 text-[#EBDCFF] border-[#EBDCFF]/20" : "bg-[#1c1c1e] text-[#F5F5F7] border-transparent")}>
                        <span className={cn("w-1.5 h-1.5 rounded-full animate-pulse", isDark ? "bg-[#EBDCFF]" : "bg-[#F5F5F7]")} />
                        Active
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
});
