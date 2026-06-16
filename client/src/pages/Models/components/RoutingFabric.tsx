import { memo } from "react";
import { useTheme } from "../../../contexts/ThemeContext";
import { cn } from "../../../lib/utils";

interface RouteDest {
  label: string;
  model: string;
  provider: string;
  icon: string;
}

interface RoutingFabricProps {
  loading: boolean;
  activeRules: RouteDest[];
}

function SkeletonNode({ className, isDark }: { className?: string; isDark: boolean }) {
  return (
    <div className={cn("rounded-[1.5rem] p-6 w-48 h-36 border flex flex-col items-center justify-center gap-2", isDark ? "bg-[#131317] border-white/[0.06]" : "bg-[#F5F5F7] border-black/5", className)}>
      <div className={cn("w-12 h-12 rounded-xl", isDark ? "bg-[#2a2a2e]" : "bg-black/5")} />
      <div className={cn("h-4.5 w-24 rounded", isDark ? "bg-white/5" : "bg-black/5")} />
      <div className={cn("h-3 w-28 rounded", isDark ? "bg-white/5" : "bg-black/5")} />
    </div>
  );
}

function ArrowRight({ isDark, className }: { isDark: boolean; className?: string }) {
  return (
    <div className={cn("hidden md:flex items-center", className)}>
      <div className={cn("w-10 h-[2px]", isDark ? "bg-white/10" : "bg-black/10")} />
      <span className={cn("material-symbols-outlined text-[20px]", isDark ? "text-white/30" : "text-black/30")}>arrow_forward</span>
    </div>
  );
}

function ArrowDown({ isDark, className }: { isDark: boolean; className?: string }) {
  return (
    <span className={cn("material-symbols-outlined text-[24px] md:hidden", isDark ? "text-white/30" : "text-black/30", className)}>arrow_downward</span>
  );
}

export const RoutingFabric = memo(function RoutingFabric({ loading, activeRules }: RoutingFabricProps) {
  const { isDark } = useTheme();

  return (
    <div className={cn("rounded-[2rem] border overflow-hidden p-8 mb-8 relative", isDark ? "bg-[#1f1f23] border-white/[0.06]" : "bg-white border-black/5 shadow-[0_8px_30px_rgb(0,0,0,0.02)]")}>
      <div className="flex items-center justify-between mb-8">
        <h2 className={cn("text-[20px] font-serif font-bold", isDark ? "text-white" : "text-[#1c1c1e]")} style={{ fontFamily: "'Playfair Display', serif" }}>
          Active Model Routing
        </h2>
        <div className={cn("flex items-center gap-2 px-3 py-1.5 rounded-full border shadow-sm", isDark ? "bg-white/5 border-white/10" : "bg-[#F5F5F7] border-black/5")}>
          <div className={cn("w-1.5 h-1.5 rounded-full", activeRules.length > 0 ? "bg-green-500 animate-pulse" : isDark ? "bg-white/20" : "bg-black/20")} />
          <span className={cn("text-[10px] font-bold uppercase tracking-widest", isDark ? "text-[#EBDCFF]" : "text-[#1c1c1e]")}>
            {activeRules.length > 0 ? "Live" : "Inactive"}
          </span>
        </div>
      </div>

      {loading ? (
        <div className="flex flex-col md:flex-row items-center justify-center gap-6 py-6 animate-pulse">
          <SkeletonNode isDark={isDark} />
          <div className="hidden md:flex items-center">
            <div className={cn("w-10 h-[2px]", isDark ? "bg-white/5" : "bg-black/5")} />
            <span className={cn("material-symbols-outlined text-[20px]", isDark ? "text-white/10" : "text-black/10")}>arrow_forward</span>
          </div>
          <div className={cn("rounded-[1.5rem] p-6 w-48 h-36 border-2 border-dashed flex flex-col items-center justify-center gap-2", isDark ? "bg-[#131317] border-white/[0.1]" : "bg-[#F5F5F7] border-black/10")}>
            <div className={cn("w-12 h-12 rounded-xl", isDark ? "bg-[#2a2a2e]" : "bg-black/5")} />
            <div className={cn("h-4.5 w-24 rounded", isDark ? "bg-white/5" : "bg-black/5")} />
            <div className={cn("h-3 w-28 rounded", isDark ? "bg-white/5" : "bg-black/5")} />
          </div>
          <div className="hidden md:flex items-center">
            <div className={cn("w-10 h-[2px]", isDark ? "bg-white/5" : "bg-black/5")} />
            <span className={cn("material-symbols-outlined text-[20px]", isDark ? "text-white/10" : "text-black/10")}>arrow_forward</span>
          </div>
          <div className="flex flex-col gap-3 w-full md:w-auto">
            {[1, 2].map((i) => (
              <div key={i} className={cn("rounded-2xl px-5 py-4 w-full md:w-64 h-20 border flex items-center justify-between gap-4", isDark ? "bg-[#131317] border-white/[0.04]" : "bg-[#F5F5F7] border-black/5")}>
                <div className="space-y-1.5 flex-grow">
                  <div className={cn("h-3 w-16 rounded", isDark ? "bg-white/5" : "bg-black/5")} />
                  <div className={cn("h-4.5 w-28 rounded", isDark ? "bg-white/5" : "bg-black/5")} />
                  <div className={cn("h-3.5 w-24 rounded", isDark ? "bg-white/5" : "bg-black/5")} />
                </div>
                <div className={cn("w-10 h-10 rounded-full", isDark ? "bg-white/5" : "bg-black/5")} />
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="flex flex-col md:flex-row items-center justify-center gap-6 py-6">
          {/* Origin Node */}
          <div className={cn("rounded-[1.5rem] p-6 w-48 text-center border shadow-sm transition-all", isDark ? "bg-[#131317] border-white/[0.06]" : "bg-[#F5F5F7] border-black/5")}>
            <div className={cn("w-12 h-12 mx-auto rounded-xl flex items-center justify-center mb-4", isDark ? "bg-[#2a2a2e]" : "bg-black/5")}>
              <span className={cn("material-symbols-outlined", isDark ? "text-[#EBDCFF]" : "text-[#1c1c1e]")}>input</span>
            </div>
            <h3 className={cn("font-bold text-[14px]", isDark ? "text-white" : "text-[#1c1c1e]")}>User Query</h3>
            <p className={cn("text-[11px] font-medium mt-1", isDark ? "text-white/40" : "text-[#1c1c1e]/50")}>Multi-channel Gateway</p>
          </div>

          <div className="flex md:items-center justify-center py-2 md:py-0">
            <ArrowRight isDark={isDark} />
            <ArrowDown isDark={isDark} />
          </div>

          {/* Router Node */}
          <div className={cn("rounded-[1.5rem] p-6 w-48 text-center border-2 border-dashed relative", isDark ? "bg-[#131317] border-[#EBDCFF]/30" : "bg-[#F5F5F7] border-[#1c1c1e]/20")}>
            <div className={cn("w-12 h-12 mx-auto rounded-xl flex items-center justify-center mb-4", isDark ? "bg-[#EBDCFF]/10 text-[#EBDCFF]" : "bg-[#1c1c1e] text-[#F5F5F7]")}>
              <span className="material-symbols-outlined">hub</span>
            </div>
            <h3 className={cn("font-bold text-[14px]", isDark ? "text-white" : "text-[#1c1c1e]")}>Intent Matcher</h3>
            <p className={cn("text-[11px] font-bold mt-1", isDark ? "text-white/60" : "text-[#1c1c1e]/60")}>Smart Routing</p>
          </div>

          <div className="flex md:items-center justify-center py-2 md:py-0">
            <ArrowRight isDark={isDark} />
            <ArrowDown isDark={isDark} />
          </div>

          {/* Destination Nodes */}
          <div className="flex flex-col gap-3 w-full md:w-auto">
            {activeRules.length === 0 ? (
              <div className={cn("rounded-2xl px-5 py-4 flex items-center justify-between gap-8 border shadow-sm text-left w-full md:w-64", isDark ? "bg-[#131317] border-white/[0.04]" : "bg-[#F5F5F7] border-black/5")}>
                <div>
                  <p className={cn("text-[10px] font-bold uppercase tracking-widest mb-1", isDark ? "text-white/40" : "text-[#1c1c1e]/50")}>All Queries (Default)</p>
                  <p className={cn("text-[14px] font-bold", isDark ? "text-white" : "text-[#1c1c1e]")}>gpt-4o-mini</p>
                  <p className={cn("text-[9px] font-semibold opacity-65", isDark ? "text-white/30" : "text-[#1c1c1e]/40")}>via AI Engine</p>
                </div>
                <div className={cn("w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0", isDark ? "bg-[#EBDCFF]/10 text-[#EBDCFF]" : "bg-white border text-[#1c1c1e]")}>
                  <span className="material-symbols-outlined text-[18px]">speed</span>
                </div>
              </div>
            ) : (
              activeRules.map((dest, idx) => (
                <div key={idx} className={cn("rounded-2xl px-5 py-4 flex items-center justify-between gap-8 border shadow-sm text-left w-full md:w-64", isDark ? "bg-[#131317] border-white/[0.04]" : "bg-[#F5F5F7] border-black/5")}>
                  <div>
                    <p className={cn("text-[10px] font-bold uppercase tracking-widest mb-1", isDark ? "text-white/40" : "text-[#1c1c1e]/50")}>{dest.label}</p>
                    <p className={cn("text-[14px] font-bold", isDark ? "text-white" : "text-[#1c1c1e]")}>{dest.model?.split('/').pop()}</p>
                    <p className={cn("text-[9px] font-semibold opacity-65", isDark ? "text-white/30" : "text-[#1c1c1e]/40")}>via AI Engine</p>
                  </div>
                  <div className={cn("w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0", isDark ? "bg-[#EBDCFF]/10 text-[#EBDCFF]" : "bg-white border text-[#1c1c1e]")}>
                    <span className="material-symbols-outlined text-[18px]">{dest.icon}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
});
