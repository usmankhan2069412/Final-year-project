import { useState } from "react";
import { useTheme } from "../../../contexts/ThemeContext";

interface Step4DeployProps {
  botName: string;
}

export default function Step4Deploy({ botName }: Step4DeployProps) {
  const { isDark } = useTheme();
  const c = (light: string, dark: string) => (isDark ? dark : light);

  const [deployTab, setDeployTab] = useState<"whatsapp" | "web">("whatsapp");
  const [waNumber, setWaNumber] = useState("");
  const [connected, setConnected] = useState(false);
  const [copied, setCopied] = useState(false);

  const displayName = botName || "My Aina Bot";
  const widgetCode = `<!-- Aina AI Widget -->
<script>
  window.AinaConfig = {
    botId: "bot_${Math.random().toString(36).slice(2, 10)}",
    name: "${displayName}",
    theme: "${isDark ? "dark" : "light"}",
    primaryColor: "${isDark ? "#EBDCFF" : "#1c1c1e"}"
  };
</script>
<script src="https://cdn.aina.ai/widget.js" async></script>`;

  const handleCopy = () => {
    navigator.clipboard?.writeText(widgetCode);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-300 max-w-5xl">
      {/* Deploy celebration header */}
      <div
        className={`rounded-[2rem] border p-4 sm:p-8 relative overflow-hidden shadow-lg ${
          isDark ? "bg-[#1f1f23] border-[#EBDCFF]/30" : "bg-white border-black/10"
        }`}
      >
        <div
          className={`absolute top-0 left-0 w-full h-1 ${
            isDark
              ? "bg-gradient-to-r from-[#EBDCFF] via-[#EBDCFF]/50 to-transparent"
              : "bg-gradient-to-r from-[#1c1c1e] to-transparent"
          }`}
        ></div>
        <div className="flex flex-col sm:flex-row items-center sm:items-start gap-6 text-center sm:text-left">
          <div className="text-[48px] drop-shadow-md flex-shrink-0">🚀</div>
          <div>
            <h2
              className={`text-[22px] sm:text-[24px] font-serif font-bold ${c("text-[#1c1c1e]", "text-white")}`}
              style={{ fontFamily: "'Playfair Display', serif" }}
            >
              Ready to Go Live!
            </h2>
            <p className={`text-[14px] sm:text-[15px] font-medium mt-1.5 ${c("text-[#1c1c1e]/60", "text-[#85948b]")}`}>
              <span className={`font-bold ${c("text-[#1c1c1e]", "text-[#EBDCFF]")}`}>{displayName}</span> is fully trained
              and ready to be deployed. Choose your channel below.
            </p>
          </div>
        </div>
      </div>

      {/* Channel selector */}
      <div className="flex flex-col sm:flex-row gap-4">
        <button
          onClick={() => setDeployTab("whatsapp")}
          className={`flex items-center justify-center gap-3 px-6 py-4 rounded-xl font-bold text-[14px] transition-all border shadow-sm w-full sm:w-auto ${
            deployTab === "whatsapp"
              ? c("border-[#1c1c1e] bg-[#1c1c1e] text-[#F5F5F7]", "border-[#EBDCFF]/50 bg-[#EBDCFF]/10 text-[#EBDCFF]")
              : c(
                  "border-black/5 bg-[#F5F5F7] text-[#1c1c1e]/60 hover:text-[#1c1c1e] hover:bg-white",
                  "border-white/[0.06] bg-[#1f1f23] text-[#85948b] hover:text-white"
                )
          }`}
        >
          <span className="material-symbols-outlined text-[20px]">chat</span>
          WhatsApp
        </button>
        <button
          onClick={() => setDeployTab("web")}
          className={`flex items-center justify-center gap-3 px-6 py-4 rounded-xl font-bold text-[14px] transition-all border shadow-sm w-full sm:w-auto ${
            deployTab === "web"
              ? c("border-[#1c1c1e] bg-[#1c1c1e] text-[#F5F5F7]", "border-[#EBDCFF]/50 bg-[#EBDCFF]/10 text-[#EBDCFF]")
              : c(
                  "border-black/5 bg-[#F5F5F7] text-[#1c1c1e]/60 hover:text-[#1c1c1e] hover:bg-white",
                  "border-white/[0.06] bg-[#1f1f23] text-[#85948b] hover:text-white"
                )
          }`}
        >
          <span className="material-symbols-outlined text-[20px]">language</span>
          Web Widget
        </button>
      </div>

      {/* WhatsApp Panel */}
      {deployTab === "whatsapp" && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div
            className={`rounded-[2rem] border p-4 sm:p-8 space-y-6 shadow-sm ${
              isDark ? "bg-[#1f1f23] border-white/[0.06]" : "bg-white border-black/5"
            }`}
          >
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-[#25D366]/10 flex items-center justify-center flex-shrink-0">
                <span className="material-symbols-outlined text-[#25D366] text-[24px]">chat</span>
              </div>
              <div>
                <h3 className={`text-[16px] font-bold ${c("text-[#1c1c1e]", "text-white")}`}>WhatsApp Business</h3>
                <p className={`text-[12px] font-medium mt-1 ${c("text-[#1c1c1e]/50", "text-[#85948b]")}`}>
                  Connect your WhatsApp Business number
                </p>
              </div>
            </div>

            {!connected ? (
              <div className="space-y-6 pt-2">
                <div>
                  <label
                    className={`block text-[11px] font-bold uppercase tracking-widest mb-2 ${c(
                      "text-[#1c1c1e]/50",
                      "text-[#85948b]"
                    )}`}
                  >
                    WhatsApp Business Number
                  </label>
                  <input
                    type="tel"
                    value={waNumber}
                    onChange={(e) => setWaNumber(e.target.value)}
                    className={`w-full rounded-xl px-5 py-4 text-[14px] font-medium outline-none transition-all shadow-inner ${
                      isDark
                        ? "bg-[#131317] border border-white/[0.06] text-white focus:border-[#EBDCFF]/50 placeholder:text-[#3c4a42]"
                        : "bg-[#F5F5F7] border border-black/5 text-[#1c1c1e] focus:border-black/20 focus:bg-white placeholder:text-[#1c1c1e]/30"
                    }`}
                    placeholder="+92 300 1234567"
                  />
                </div>

                <button
                  onClick={() => setConnected(true)}
                  className={`w-full py-4 rounded-xl font-bold text-[14px] transition-colors flex items-center justify-center gap-2 shadow-md active:scale-[0.98] ${
                    isDark
                      ? "bg-[#EBDCFF] hover:bg-[#d8bfff] text-[#1c1c1e]"
                      : "bg-[#1c1c1e] hover:bg-black text-[#F5F5F7]"
                  }`}
                >
                  <span className="material-symbols-outlined text-[18px]">link</span>
                  Connect WhatsApp
                </button>

                <div
                  className={`rounded-2xl p-5 border shadow-inner ${
                    isDark ? "bg-[#131317] border-white/[0.04]" : "bg-[#F5F5F7] border-black/5"
                  }`}
                >
                  <h4 className={`text-[11px] font-bold uppercase tracking-widest mb-4 ${c("text-[#1c1c1e]/60", "text-[#85948b]")}`}>
                    Setup Steps
                  </h4>
                  <ol className="space-y-3">
                    {[
                      "Enter your WhatsApp Business phone number",
                      "We'll send a verification OTP via WhatsApp",
                      "Approve Aina AI as your messaging provider",
                      "Your bot goes live instantly!",
                    ].map((s, i) => (
                      <li key={i} className={`flex items-start gap-3 text-[12px] font-medium ${c("text-[#1c1c1e]/70", "text-[#85948b]")}`}>
                        <span
                          className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold flex-shrink-0 mt-0.5 shadow-sm border border-transparent ${
                            isDark ? "bg-[#2a2a2e] text-[#EBDCFF]" : "bg-white border-black/5 text-[#1c1c1e]"
                          }`}
                        >
                          {i + 1}
                        </span>
                        {s}
                      </li>
                    ))}
                  </ol>
                </div>
              </div>
            ) : (
              <div className="space-y-5 pt-2 animate-in fade-in zoom-in-95">
                <div
                  className={`border rounded-2xl p-5 flex items-center gap-4 ${
                    isDark ? "bg-[#EBDCFF]/5 border-[#EBDCFF]/20" : "bg-[#1c1c1e]/5 border-[#1c1c1e]/10"
                  }`}
                >
                  <span className={`material-symbols-outlined text-[28px] ${c("text-[#1c1c1e]", "text-[#EBDCFF]")}`}>
                    check_circle
                  </span>
                  <div>
                    <p className={`text-[15px] font-bold ${c("text-[#1c1c1e]", "text-white")}`}>WhatsApp Connected!</p>
                    <p className={`text-[13px] font-medium mt-0.5 ${c("text-[#1c1c1e]/60", "text-[#85948b]")}`}>
                      {waNumber || "+92 300 1234567"}
                    </p>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div
                    className={`rounded-2xl p-5 text-center border shadow-inner ${
                      isDark ? "bg-[#131317] border-white/[0.04]" : "bg-[#F5F5F7] border-black/5"
                    }`}
                  >
                    <p className={`text-[28px] font-bold ${c("text-[#1c1c1e]", "text-white")}`}>0</p>
                    <p className={`text-[10px] font-bold uppercase tracking-widest mt-1 ${c("text-[#1c1c1e]/50", "text-[#85948b]")}`}>
                      Messages Today
                    </p>
                  </div>
                  <div
                    className={`rounded-2xl p-5 text-center border shadow-inner ${
                      isDark ? "bg-[#131317] border-white/[0.04]" : "bg-[#F5F5F7] border-black/5"
                    }`}
                  >
                    <p className={`text-[28px] font-bold uppercase tracking-widest ${c("text-[#1c1c1e]", "text-[#EBDCFF]")}`}>
                      Live
                    </p>
                    <p className={`text-[10px] font-bold uppercase tracking-widest mt-1 ${c("text-[#1c1c1e]/50", "text-[#85948b]")}`}>
                      Bot Status
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* WhatsApp preview phone */}
          <div
            className={`rounded-[2rem] border p-4 sm:p-8 flex flex-col items-center shadow-sm ${
              isDark ? "bg-[#1f1f23] border-white/[0.06]" : "bg-white border-black/5"
            }`}
          >
            <h4 className={`text-[13px] font-bold uppercase tracking-widest mb-6 self-start ${c("text-[#1c1c1e]/60", "text-[#85948b]")}`}>
              WhatsApp Preview
            </h4>
            <div className="w-64 bg-[#0a0a0a] rounded-[2rem] border-8 border-black overflow-hidden shadow-2xl relative">
              {/* Notch */}
              <div className="absolute top-0 left-1/2 -translate-x-1/2 w-24 h-5 bg-black rounded-b-xl z-20"></div>
              {/* Phone top bar */}
              <div className="bg-[#075E54] pt-8 pb-3 px-4 flex items-center gap-3 shadow-md relative z-10">
                <span className="material-symbols-outlined text-white/90 text-[20px]">arrow_back</span>
                <div className="w-9 h-9 rounded-full bg-white/20 flex items-center justify-center text-[16px] border border-white/10 flex-shrink-0">
                  🤖
                </div>
                <div className="min-w-0">
                  <p className="text-white text-[14px] font-bold leading-tight truncate">{displayName}</p>
                  <p className="text-white/80 text-[11px] font-medium">online</p>
                </div>
              </div>
              {/* Chat area */}
              <div
                className="min-h-[280px] p-4 flex flex-col justify-end pb-12 relative"
                style={{
                  backgroundColor: "#E5DDD5",
                  backgroundImage: "url('https://i.pinimg.com/originals/8f/ba/cb/8fbacbd464e996966eb1f36dc168fac7.jpg')",
                  backgroundSize: "cover",
                  backgroundPosition: "center",
                  backgroundBlendMode: "overlay",
                }}
              >
                <div className="bg-white rounded-xl rounded-tl-sm px-3 py-2 inline-block max-w-[85%] shadow-[0_1px_1px_rgba(0,0,0,0.1)] self-start">
                  <p className="text-[#303030] text-[13px] leading-relaxed">
                    Salaam! Main {displayName} hoon. Aap ki kya madad kar sakta hoon? 😊
                  </p>
                  <p className="text-[#999] text-[10px] text-right mt-1 ml-4 float-right">10:30</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Web Widget Panel */}
      {deployTab === "web" && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div
            className={`rounded-[2rem] border p-4 sm:p-8 space-y-6 shadow-sm ${
              isDark ? "bg-[#1f1f23] border-white/[0.06]" : "bg-white border-black/5"
            }`}
          >
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-black/5 flex items-center justify-center text-[#1c1c1e] dark:bg-[#b0c6ff]/10 dark:text-[#b0c6ff] flex-shrink-0">
                <span className="material-symbols-outlined text-[24px]">code</span>
              </div>
              <div>
                <h3 className={`text-[16px] font-bold ${c("text-[#1c1c1e]", "text-white")}`}>Web Widget</h3>
                <p className={`text-[12px] font-medium mt-1 ${c("text-[#1c1c1e]/50", "text-[#85948b]")}`}>
                  Embed on any website in under 2 minutes
                </p>
              </div>
            </div>

            <div className="pt-2">
              <div className="flex items-center justify-between mb-3">
                <label className={`text-[11px] font-bold uppercase tracking-widest ${c("text-[#1c1c1e]/50", "text-[#85948b]")}`}>
                  Embed Code
                </label>
                <button
                  onClick={handleCopy}
                  className={`text-[11px] font-bold flex items-center gap-1 transition-colors ${c(
                    "text-[#1c1c1e] hover:text-[#1c1c1e]/60",
                    "text-[#EBDCFF] hover:text-white"
                  )}`}
                >
                  <span className="material-symbols-outlined text-[14px]">
                    {copied ? "check" : "content_copy"}
                  </span>
                  {copied ? "Copied!" : "Copy Code"}
                </button>
              </div>
              <div
                className={`border rounded-xl p-5 font-mono text-[12px] leading-relaxed overflow-auto max-h-48 whitespace-pre shadow-inner selection:bg-[#EBDCFF] selection:text-[#1c1c1e] ${
                  isDark
                    ? "bg-[#0e0e12] border-white/[0.06] text-[#EBDCFF]/80"
                    : "bg-[#F5F5F7] border-black/10 text-[#1c1c1e]"
                }`}
              >
                {widgetCode}
              </div>
            </div>

            <div>
              <label
                className={`block text-[11px] font-bold uppercase tracking-widest mb-3 ${c(
                  "text-[#1c1c1e]/50",
                  "text-[#85948b]"
                )}`}
              >
                Your Website URL
              </label>
              <input
                type="url"
                className={`w-full rounded-xl px-5 py-4 text-[14px] font-medium outline-none transition-all shadow-inner ${
                  isDark
                    ? "bg-[#131317] border border-white/[0.06] text-white focus:border-[#EBDCFF]/50 placeholder:text-[#3c4a42]"
                    : "bg-[#F5F5F7] border border-black/5 text-[#1c1c1e] focus:border-black/20 focus:bg-white placeholder:text-[#1c1c1e]/30"
                }`}
                placeholder="https://yourwebsite.com"
              />
            </div>

            <button
              className={`w-full py-4 rounded-xl font-bold text-[14px] transition-colors flex items-center justify-center gap-2 shadow-md active:scale-[0.98] ${
                isDark
                  ? "bg-[#EBDCFF] hover:bg-[#d8bfff] text-[#1c1c1e]"
                  : "bg-[#1c1c1e] hover:bg-black text-[#F5F5F7]"
              }`}
            >
              <span className="material-symbols-outlined text-[18px]">open_in_new</span>
              Preview on My Site
            </button>
          </div>

          {/* Web widget preview */}
          <div
            className={`rounded-[2rem] border p-4 sm:p-8 flex flex-col shadow-sm ${
              isDark ? "bg-[#1f1f23] border-white/[0.06]" : "bg-white border-black/5"
            }`}
          >
            <h4 className={`text-[13px] font-bold uppercase tracking-widest mb-6 ${c("text-[#1c1c1e]/60", "text-[#85948b]")}`}>
              Widget Preview
            </h4>
            <div
              className={`flex-1 rounded-[1.5rem] border relative overflow-hidden min-h-[320px] shadow-inner ${
                isDark ? "bg-[#131317] border-white/[0.04]" : "bg-[#F5F5F7] border-black/5"
              }`}
            >
              {/* Fake website bg */}
              <div className="absolute inset-0 p-6 space-y-4 opacity-70">
                <div className={`h-4 rounded-full w-2/3 ${c("bg-black/10", "bg-white/10")}`}></div>
                <div className={`h-3 rounded-full w-1/2 ${c("bg-black/5", "bg-white/5")}`}></div>
                <div className={`h-3 rounded-full w-3/4 ${c("bg-black/5", "bg-white/5")}`}></div>
                <div className={`h-24 rounded-2xl mt-6 ${c("bg-black/5", "bg-white/5")}`}></div>
                <div className={`h-3 rounded-full w-5/6 ${c("bg-black/5", "bg-white/5")}`}></div>
                <div className={`h-3 rounded-full w-1/2 ${c("bg-black/5", "bg-white/5")}`}></div>
              </div>

              {/* Chat widget floating UI */}
              <div className="absolute bottom-6 right-6 flex flex-col items-end gap-4 z-10 max-w-[calc(100%-3rem)]">
                {/* Chat window */}
                <div
                  className={`rounded-[1.5rem] shadow-[0_12px_40px_rgba(0,0,0,0.15)] w-64 sm:w-72 overflow-hidden border ${
                    isDark ? "bg-[#1f1f23] border-white/10" : "bg-white border-black/10"
                  }`}
                >
                  <div className={`px-5 py-4 flex items-center gap-3 ${isDark ? "bg-[#EBDCFF]" : "bg-[#1c1c1e]"}`}>
                    <div className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center text-[14px] border border-white/20 flex-shrink-0">
                      🤖
                    </div>
                    <p className={`text-[14px] font-bold truncate ${isDark ? "text-[#1c1c1e]" : "text-[#F5F5F7]"}`}>
                      {displayName}
                    </p>
                  </div>
                  <div className={`p-4 space-y-3 ${isDark ? "bg-[#131317]" : "bg-[#F5F5F7]"}`}>
                    <div
                      className={`rounded-2xl rounded-tl-sm p-4 shadow-sm border ${
                        isDark ? "bg-[#1f1f23] border-white/[0.04]" : "bg-white border-black/5"
                      }`}
                    >
                      <p className={`text-[12px] font-medium leading-relaxed ${isDark ? "text-white" : "text-[#1c1c1e]"}`}>
                        Hi! 👋 How can I help you today?
                      </p>
                    </div>
                    <div
                      className={`flex gap-2 p-1.5 rounded-xl border ${
                        isDark ? "bg-[#1f1f23] border-white/[0.06]" : "bg-white border-black/10"
                      }`}
                    >
                      <input
                        readOnly
                        className={`flex-1 bg-transparent px-3 py-2 text-[12px] font-medium outline-none ${
                          isDark ? "text-[#55635a]" : "placeholder:text-[#1c1c1e]/40"
                        }`}
                        placeholder="Type a message..."
                      />
                      <div
                        className={`w-9 h-9 rounded-lg flex items-center justify-center shadow-sm flex-shrink-0 ${
                          isDark ? "bg-[#EBDCFF]" : "bg-[#1c1c1e]"
                        }`}
                      >
                        <span
                          className={`material-symbols-outlined text-[16px] translate-x-[1px] ${
                            isDark ? "text-[#1c1c1e]" : "text-[#F5F5F7]"
                          }`}
                        >
                          send
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
                {/* Chat button launcher */}
                <div
                  className={`w-14 h-14 rounded-full flex items-center justify-center shadow-[0_8px_30px_rgba(0,0,0,0.15)] cursor-pointer hover:scale-110 transition-transform flex-shrink-0 ${
                    isDark ? "bg-[#EBDCFF]" : "bg-[#1c1c1e]"
                  }`}
                >
                  <span className={`material-symbols-outlined text-[24px] ${isDark ? "text-[#1c1c1e]" : "text-[#F5F5F7]"}`}>
                    chat
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Final publish row */}
      <div
        className={`rounded-[2rem] border p-4 sm:p-6 lg:p-8 flex flex-col sm:flex-row items-center sm:items-center justify-between gap-6 shadow-sm mt-4 bg-gradient-to-r ${
          isDark
            ? "from-[#1f1f23] to-[#EBDCFF]/5 border-white/[0.06]"
            : "from-white to-black/5 border-black/5"
        }`}
      >
        <div className="text-center sm:text-left">
          <h3
            className={`text-[18px] sm:text-[20px] font-serif font-bold flex items-center justify-center sm:justify-start gap-2 ${c(
              "text-[#1c1c1e]",
              "text-white"
            )}`}
            style={{ fontFamily: "'Playfair Display', serif" }}
          >
            <span className="text-2xl">🎉</span> All done! Publish your bot.
          </h3>
          <p className={`text-[13px] sm:text-[14px] font-medium mt-1.5 ${c("text-[#1c1c1e]/60", "text-[#85948b]")}`}>
            Your bot will go live instantly. You can pause or edit it anytime from the dashboard.
          </p>
        </div>
        <button
          className={`flex-shrink-0 px-8 py-4 rounded-xl font-bold text-[14px] transition-all flex items-center gap-2 shadow-md active:scale-[0.98] w-full sm:w-auto justify-center ${
            isDark ? "bg-[#EBDCFF] hover:bg-[#d8bfff] text-[#1c1c1e]" : "bg-[#1c1c1e] hover:bg-black text-[#F5F5F7]"
          }`}
        >
          <span className="material-symbols-outlined text-[20px]">rocket_launch</span>
          Publish Bot
        </button>
      </div>
    </div>
  );
}
