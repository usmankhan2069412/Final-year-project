import { useTheme } from "../../../contexts/ThemeContext";

const STEPS = [
  { num: 1, label: "Persona", icon: "face" },
  { num: 2, label: "Knowledge", icon: "menu_book" },
  { num: 3, label: "Test", icon: "chat_bubble" },
  { num: 4, label: "Deploy", icon: "rocket_launch" },
];

export default function StepBar({ current, onStep }: { current: number; onStep: (n: number) => void }) {
  const { isDark } = useTheme();
  const c = (light: string, dark: string) => (isDark ? dark : light);

  return (
    <div className="flex items-center flex-shrink-0 lg:w-full lg:max-w-xl mx-auto overflow-x-auto no-scrollbar py-2">
      {STEPS.map((step, idx) => {
        const done = current > step.num;
        const active = current === step.num;
        return (
          <div key={step.num} className="flex items-center flex-shrink-0">
            <button
              onClick={() => done && onStep(step.num)}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-full transition-all text-[12px] font-bold ${
                active
                  ? c("bg-[#1c1c1e] text-[#F5F5F7] shadow-md", "bg-[#EBDCFF] text-[#1c1c1e] shadow-md")
                  : done
                  ? c("text-[#1c1c1e] hover:bg-black/5 cursor-pointer", "text-white hover:bg-white/5 cursor-pointer")
                  : c("text-[#1c1c1e]/40 cursor-default", "text-white/30 cursor-default")
              }`}
            >
              <div
                className={`w-6 h-6 rounded-full flex items-center justify-center text-[11px] font-bold flex-shrink-0 transition-colors ${
                  active
                    ? c("bg-[#F5F5F7] text-[#1c1c1e]", "bg-[#1c1c1e] text-[#EBDCFF]")
                    : done
                    ? c("bg-[#1c1c1e]/10 text-[#1c1c1e]", "bg-[#EBDCFF]/20 text-[#EBDCFF]")
                    : c("bg-black/5 text-[#1c1c1e]/40", "bg-[#2a2a2e] text-white/30")
                }`}
              >
                {done ? (
                  <span className="material-symbols-outlined text-[13px]">check</span>
                ) : (
                  step.num
                )}
              </div>
              <span className="hidden sm:inline">{step.label}</span>
            </button>
            {idx < STEPS.length - 1 && (
              <div
                className={`w-4 lg:w-8 h-[2px] mx-1 transition-colors rounded-full ${
                  done ? c("bg-[#1c1c1e]/30", "bg-[#EBDCFF]/40") : c("bg-black/5", "bg-white/[0.06]")
                }`}
              ></div>
            )}
          </div>
        );
      })}
    </div>
  );
}
