import { useState, useRef } from "react";
import { useTheme } from "../../../contexts/ThemeContext";
import { KnowledgeItem } from "../types";
import { SourceType } from "../../../lib/api";

const KNOWLEDGE_TYPES = [
  { type: "file", icon: "upload_file", label: "Documents", hint: "PDF, DOCX, TXT, CSV", color: "#b0c6ff" },
  { type: "text", icon: "edit_note", label: "Text / Guidelines", hint: "Paste instructions directly", color: "#f5c5ff" },
  { type: "website", icon: "language", label: "Website URL", hint: "We'll crawl your site", color: "#59eeb4" },
  { type: "email", icon: "mail", label: "Contact Email", hint: "For escalation handover", color: "#ffb4ab" },
  { type: "phone", icon: "phone", label: "Phone Number", hint: "For WhatsApp escalation", color: "#EBDCFF" },
  { type: "app", icon: "apps", label: "App / API", hint: "Connect a data source", color: "#b0c6ff" },
] as const;

interface Step2KnowledgeProps {
  items: KnowledgeItem[];
  onAddItem: (type: Exclude<SourceType, "file">, value: string, label: string) => Promise<void>;
  onUploadFiles: (files: FileList | File[]) => Promise<void>;
  onRemoveItem: (id: string) => Promise<void>;
}

export default function Step2Knowledge({ items, onAddItem, onUploadFiles, onRemoveItem }: Step2KnowledgeProps) {
  const [activeType, setActiveType] = useState<string>("file");
  const [inputValue, setInputValue] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);
  const { isDark } = useTheme();
  const c = (light: string, dark: string) => (isDark ? dark : light);

  const addItem = async () => {
    if (!inputValue.trim() && activeType !== "file") return;
    const typeInfo = KNOWLEDGE_TYPES.find((k) => k.type === activeType);
    if (activeType === "file") return;
    setIsSubmitting(true);
    try {
      await onAddItem(activeType as Exclude<SourceType, "file">, inputValue.trim(), typeInfo?.label ?? activeType);
      setInputValue("");
    } finally {
      setIsSubmitting(false);
    }
  };

  const activeTypeInfo = KNOWLEDGE_TYPES.find((k) => k.type === activeType);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 animate-in fade-in duration-300">
      {/* Left: Input panel */}
      <div className="lg:col-span-7 space-y-6">
        <div
          className={`rounded-[2rem] border p-4 sm:p-8 ${
            isDark ? "bg-[#1f1f23] border-white/[0.06]" : "bg-white border-black/5 shadow-[0_8px_30px_rgb(0,0,0,0.02)]"
          }`}
        >
          <h3
            className={`text-[20px] font-serif font-bold mb-2 ${c("text-[#1c1c1e]", "text-white")}`}
            style={{ fontFamily: "'Playfair Display', serif" }}
          >
            Add Knowledge Sources
          </h3>
          <p className={`text-[13px] font-medium mb-6 ${c("text-[#1c1c1e]/60", "text-[#85948b]")}`}>
            Everything you add here is what your bot knows. The more you add, the smarter it gets.
          </p>

          {/* Source type tabs */}
          <div className="grid grid-cols-3 sm:grid-cols-6 gap-2.5 mb-8">
            {KNOWLEDGE_TYPES.map((kt) => (
              <button
                key={kt.type}
                onClick={() => setActiveType(kt.type)}
                className={`flex flex-col items-center gap-2 p-2.5 sm:p-4 rounded-2xl border transition-all text-center shadow-sm ${
                  activeType === kt.type
                    ? c("border-[#1c1c1e] bg-black/5 text-[#1c1c1e]", "border-[#EBDCFF]/40 bg-[#EBDCFF]/5 text-[#EBDCFF]")
                    : c("border-black/5 bg-[#F5F5F7] text-[#1c1c1e]/50 hover:text-[#1c1c1e]", "border-white/[0.06] bg-[#131317] text-[#85948b] hover:text-white hover:border-white/15")
                }`}
              >
                <span className="material-symbols-outlined text-[20px]">{kt.icon}</span>
                <span className="text-[10px] font-bold uppercase tracking-widest leading-tight">
                  {kt.label.split(" ")[0]}
                </span>
              </button>
            ))}
          </div>

          {/* Input area */}
          <div className="space-y-4">
            <div className="flex items-center gap-3 mb-4">
              <div
                className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                  isDark ? "bg-white/5" : "bg-black/5 text-[#1c1c1e]"
                }`}
                style={isDark ? { color: activeTypeInfo?.color, backgroundColor: `${activeTypeInfo?.color}15` } : {}}
              >
                <span className="material-symbols-outlined text-[20px]">
                  {activeTypeInfo?.icon}
                </span>
              </div>
              <div className="min-w-0">
                <span className={`text-[15px] font-bold block sm:inline ${c("text-[#1c1c1e]", "text-white")}`}>{activeTypeInfo?.label}</span>
                <span className={`text-[12px] font-medium block sm:inline sm:ml-2 truncate ${c("text-[#1c1c1e]/50", "text-[#85948b]")}`}>{activeTypeInfo?.hint}</span>
              </div>
            </div>

            {activeType === "file" ? (
              <div
                onClick={() => fileRef.current?.click()}
                className={`border-2 border-dashed transition-all cursor-pointer rounded-2xl h-48 flex flex-col items-center justify-center gap-3 p-4 group ${
                  isDark
                    ? "border-white/[0.08] hover:border-[#EBDCFF]/40 hover:bg-[#EBDCFF]/[0.02]"
                    : "border-black/10 hover:border-[#1c1c1e]/40 hover:bg-black/[0.01]"
                }`}
              >
                <span
                  className={`material-symbols-outlined text-[40px] transition-colors ${
                    c("text-[#1c1c1e]/20 group-hover:text-[#1c1c1e]", "text-white/20 group-hover:text-[#EBDCFF]")
                  }`}
                >
                  cloud_upload
                </span>
                <p className={`text-[15px] font-bold text-center transition-colors ${c("text-[#1c1c1e]/50 group-hover:text-[#1c1c1e]", "text-white/50 group-hover:text-white")}`}>
                  Click or drag files here
                </p>
                <p className={`text-[12px] font-medium text-center ${c("text-[#1c1c1e]/40", "text-[#55635a]")}`}>PDF, DOCX, TXT, CSV — max 50MB per file</p>
                <input
                  ref={fileRef}
                  type="file"
                  className="hidden"
                  multiple
                  accept=".pdf,.docx,.txt,.csv"
                  onChange={async (event) => {
                    const files = event.target.files;
                    if (!files?.length) return;
                    setIsSubmitting(true);
                    try {
                      await onUploadFiles(files);
                    } finally {
                      setIsSubmitting(false);
                      event.target.value = "";
                    }
                  }}
                />
              </div>
            ) : activeType === "text" ? (
              <textarea
                rows={6}
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                className={`w-full rounded-xl px-5 py-4 text-[14px] font-medium outline-none transition-all shadow-inner resize-none ${
                  isDark
                    ? "bg-[#131317] border border-white/[0.06] text-white focus:border-[#EBDCFF]/50"
                    : "bg-[#F5F5F7] border border-black/5 text-[#1c1c1e] focus:border-black/20 focus:bg-white"
                }`}
                placeholder="Paste your guidelines, FAQs, product descriptions, policies, or any text your bot should know..."
              />
            ) : (
              <>
                <input
                  type="text"
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  className={`w-full rounded-xl px-5 py-4 text-[14px] font-medium outline-none transition-all shadow-inner ${
                    isDark
                      ? "bg-[#131317] border border-white/[0.06] text-white focus:border-[#EBDCFF]/50"
                      : "bg-[#F5F5F7] border border-black/5 text-[#1c1c1e] focus:border-black/20 focus:bg-white"
                  }`}
                  placeholder={
                    activeType === "website"
                      ? "https://yourwebsite.com"
                      : activeType === "email"
                      ? "support@yourcompany.com"
                      : activeType === "phone"
                      ? "+92 300 1234567"
                      : "API endpoint or app name"
                  }
                  onKeyDown={(e) => e.key === "Enter" && addItem()}
                />

                {/* Website capability guide — shown only on website tab */}
                {activeType === "website" && (
                  <div
                    className={`rounded-xl border p-4 text-[12px] ${
                      isDark
                        ? "bg-[#131317] border-white/[0.06]"
                        : "bg-[#F5F5F7] border-black/5"
                    }`}
                  >
                    <p className={`font-bold uppercase tracking-widest mb-3 ${c("text-[#1c1c1e]/60", "text-[#85948b]")}`}>
                      Crawling Compatibility
                    </p>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      {/* Supported */}
                      <div className="space-y-1.5">
                        <p className={`font-bold mb-1.5 flex items-center gap-1.5 ${c("text-green-700", "text-green-400")}`}>
                          <span className="material-symbols-outlined text-[14px]">check_circle</span>
                          Works
                        </p>
                        {[
                          "Static blogs & articles",
                          "University / info portals",
                          "Public documentation",
                          "Server-rendered HTML sites",
                        ].map((t) => (
                          <p key={t} className={`leading-snug ${c("text-[#1c1c1e]/60", "text-[#85948b]")}`}>
                            · {t}
                          </p>
                        ))}
                      </div>
                      {/* Unsupported */}
                      <div className="space-y-1.5">
                        <p className={`font-bold mb-1.5 flex items-center gap-1.5 ${c("text-red-600", "text-red-400")}`}>
                          <span className="material-symbols-outlined text-[14px]">cancel</span>
                          Won't work
                        </p>
                        {[
                          "Cloudflare / firewall-protected",
                          "React / Vue / Angular SPAs",
                          "Login-required pages",
                          "PDF / ZIP / media links",
                        ].map((t) => (
                          <p key={t} className={`leading-snug ${c("text-[#1c1c1e]/60", "text-[#85948b]")}`}>
                            · {t}
                          </p>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </>
            )}

            {activeType !== "file" && (
              <button
                onClick={addItem}
                disabled={isSubmitting}
                className={`w-full py-4 rounded-xl font-bold text-[14px] transition-all flex items-center justify-center gap-2 shadow-md active:scale-[0.98] mt-2 ${
                  isDark
                    ? "bg-[#EBDCFF] hover:bg-[#d8bfff] text-[#1c1c1e]"
                    : "bg-[#1c1c1e] hover:bg-black text-[#F5F5F7]"
                }`}
              >
                <span className="material-symbols-outlined text-[18px]">add_circle</span>
                {isSubmitting ? "Saving..." : "Add to Knowledge Base"}
              </button>
            )}
          </div>
        </div>

        {/* Knowledge quality tips */}
        <div
          className={`rounded-2xl p-4 sm:p-6 border ${
            isDark ? "bg-[#1f1f23] border-white/[0.06]" : "bg-white border-black/5 shadow-sm"
          }`}
        >
          <h4
            className={`text-[12px] font-bold uppercase tracking-widest mb-4 flex items-center gap-2.5 ${
              c("text-[#1c1c1e]", "text-[#EBDCFF]")
            }`}
          >
            <span className={`material-symbols-outlined text-[18px] ${c("text-black", "text-[#EBDCFF]")}`}>tips_and_updates</span>
            Knowledge Quality Tips
          </h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {[
              { icon: "check_circle", tip: "Add a full FAQ document for 80% better accuracy", color: isDark ? "#EBDCFF" : "#1c1c1e" },
              { icon: "link", tip: "Link your website for auto-updated product info", color: isDark ? "#b0c6ff" : "#295bd9" },
              { icon: "phone", tip: "Add your phone for seamless human handover", color: isDark ? "#ffb4ab" : "#d14b3d" },
              { icon: "description", tip: "Include your pricing PDF to handle sales queries", color: isDark ? "#f5c5ff" : "#d073e6" },
            ].map((t) => (
              <div key={t.tip} className="flex items-start gap-3">
                <span className="material-symbols-outlined text-[18px] mt-0.5 flex-shrink-0" style={{ color: t.color }}>
                  {t.icon}
                </span>
                <p className={`text-[12px] font-medium leading-relaxed ${c("text-[#1c1c1e]/70", "text-[#85948b]")}`}>{t.tip}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Right: Knowledge items list */}
      <div className="lg:col-span-5">
        <div
          className={`rounded-[2rem] border p-4 sm:p-8 lg:sticky lg:top-24 flex flex-col ${
            isDark ? "bg-[#1f1f23] border-white/[0.06]" : "bg-white border-black/5 shadow-[0_8px_30px_rgb(0,0,0,0.02)]"
          }`}
          style={{ minHeight: "350px" }}
        >
          <div className="flex items-center justify-between gap-4 mb-8">
            <h3
              className={`text-[20px] font-serif font-bold ${c("text-[#1c1c1e]", "text-white")}`}
              style={{ fontFamily: "'Playfair Display', serif" }}
            >
              Knowledge Base
            </h3>
            <span
              className={`text-[11px] font-bold px-3 py-1.5 rounded-full border shadow-sm flex-shrink-0 ${
                isDark ? "text-[#EBDCFF] bg-[#EBDCFF]/10 border-[#EBDCFF]/20" : "text-[#1c1c1e] bg-black/5 border-transparent"
              }`}
            >
              {items.length} source{items.length !== 1 ? "s" : ""}
            </span>
          </div>

          {items.length === 0 ? (
            <div className={`flex-1 flex flex-col items-center justify-center text-center gap-3 py-12 ${c("text-[#1c1c1e]/30", "text-white/20")}`}>
              <span className="material-symbols-outlined text-[48px] mb-2">inbox</span>
              <p className="text-[15px] font-bold">No sources yet</p>
              <p className="text-[13px] font-medium">Add documents, website, or contact info</p>
            </div>
          ) : (
            <div className="flex-1 space-y-3 overflow-y-auto pr-2 no-scrollbar mb-6 max-h-[350px] lg:max-h-[450px]">
              {items.map((item) => {
                const typeInfo = KNOWLEDGE_TYPES.find((k) => k.type === item.type);
                return (
                  <div
                    key={item.id}
                    className={`p-4 rounded-2xl border flex items-center gap-4 transition-all group ${
                      isDark
                        ? "bg-[#131317] border-white/[0.04] hover:border-white/10"
                        : "bg-[#F5F5F7] border-black/5 hover:border-black/10 hover:shadow-sm"
                    }`}
                  >
                    <div
                      className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 shadow-sm ${isDark ? "" : "bg-white"}`}
                      style={isDark ? { backgroundColor: `${typeInfo?.color}15`, color: typeInfo?.color } : { color: "#1c1c1e" }}
                    >
                      <span className="material-symbols-outlined text-[20px]">
                        {typeInfo?.icon}
                      </span>
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className={`text-[14px] font-bold truncate ${c("text-[#1c1c1e]", "text-white")}`}>{item.value}</p>
                      <p className={`text-[11px] font-medium mt-0.5 ${c("text-[#1c1c1e]/50", "text-[#55635a]")}`}>{item.label}</p>
                    </div>
                    <div className="flex items-center gap-3 flex-shrink-0">
                      {item.status === "failed" ? (
                        <span className={`text-[10px] font-bold px-2.5 py-1 rounded-full border ${
                          isDark ? "text-red-300 bg-red-300/10 border-red-300/20" : "text-red-700 bg-red-100 border-red-200"
                        }`} title={item.error_message || "Indexing failed"}>
                          Failed
                        </span>
                      ) : item.status === "processing" || item.status === "queued" ? (
                        <span className={`text-[10px] font-bold px-2.5 py-1 rounded-full animate-pulse border ${
                          isDark ? "text-yellow-300 bg-yellow-300/10 border-yellow-300/20" : "text-yellow-700 bg-yellow-100 border-yellow-200"
                        }`}>
                          {item.status === "queued" ? "Queued" : "Processing"}
                        </span>
                      ) : (
                        <span className={`text-[10px] font-bold px-2.5 py-1 rounded-full border shadow-sm ${
                          isDark ? "text-[#EBDCFF] bg-[#EBDCFF]/10 border-[#EBDCFF]/20" : "text-[#1c1c1e] bg-white border-black/5"
                        }`}>
                          ✓ Indexed
                        </span>
                      )}
                      <button
                        onClick={() => onRemoveItem(item.id)}
                        aria-label="Remove source"
                        className={`opacity-0 group-hover:opacity-100 transition-all ${
                          c("text-red-400 hover:text-red-600", "text-white/30 hover:text-red-400")
                        }`}
                      >
                        <span className="material-symbols-outlined text-[20px]">close</span>
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {items.length > 0 && (
            <div className={`pt-6 mt-auto border-t ${c("border-black/5", "border-white/[0.04]")}`}>
              <div className="flex justify-between text-[13px] font-bold mb-3">
                <span className={c("text-[#1c1c1e]/60", "text-[#85948b]")}>Knowledge Coverage</span>
                <span className={c("text-[#1c1c1e]", "text-[#EBDCFF]")}>{Math.min(items.length * 20, 95)}%</span>
              </div>
              <div className={`w-full h-2 rounded-full overflow-hidden shadow-inner ${c("bg-black/5", "bg-[#131317]")}`}>
                <div
                  className={`h-full rounded-full transition-all duration-500 ${c("bg-[#1c1c1e]", "bg-[#EBDCFF]")}`}
                  style={{ width: `${Math.min(items.length * 20, 95)}%` }}
                ></div>
              </div>
              <p className={`text-[11px] font-medium mt-3 text-center ${c("text-[#1c1c1e]/50", "text-[#55635a]")}`}>
                {items.length < 5 ? "Add more sources for better accuracy" : "Great coverage! Your bot is well-trained."}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
