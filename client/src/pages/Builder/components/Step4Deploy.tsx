import { useMemo, useState } from "react";
import { toast } from "sonner";
import { useTheme } from "../../../contexts/ThemeContext";
import { KnowledgeItem } from "../types";
import { api, Channel, DeploymentResponse } from "../../../lib/api";

interface Step4DeployProps {
  botName: string;
  chatbotId: string | null;
  onRequireDraft: () => Promise<string | null>;
  knowledgeItems: KnowledgeItem[];
}

export default function Step4Deploy({ botName, chatbotId, onRequireDraft, knowledgeItems }: Step4DeployProps) {
  const { isDark } = useTheme();
  const c = (light: string, dark: string) => (isDark ? dark : light);

  const [deployTab, setDeployTab] = useState<Channel>("whatsapp");
  const [waNumberId, setWaNumberId] = useState("");
  const [wabaId, setWabaId] = useState("");
  const [websiteUrl, setWebsiteUrl] = useState("");
  const [deployment, setDeployment] = useState<DeploymentResponse | null>(null);
  const [isPublishing, setIsPublishing] = useState(false);
  const [copied, setCopied] = useState(false);

  const displayName = botName || "My Aina Bot";
  const hasFailedSources = knowledgeItems.some((item) => item.status === "failed");
  const hasPendingSources = knowledgeItems.some((item) => item.status === "queued" || item.status === "processing");
  const hasIndexedOrSkippedKnowledge = knowledgeItems.length === 0 || knowledgeItems.every((item) => item.status === "indexed");
  const canPublish = !!botName.trim() && !hasFailedSources && (hasIndexedOrSkippedKnowledge || knowledgeItems.length === 0);

  const widgetCode = useMemo(() => {
    const deploymentId = deployment?.id || "DEPLOYMENT_ID_AFTER_PUBLISH";
    return `<!-- Aina AI Widget -->
<script>
  window.AinaConfig = {
    deploymentId: "${deploymentId}",
    apiBaseUrl: "${api.baseUrl}",
    name: "${displayName.replace(/"/g, '\\"')}",
    theme: "${isDark ? "dark" : "light"}",
    primaryColor: "${isDark ? "#EBDCFF" : "#1c1c1e"}"
  };
</script>
<script src="${api.baseUrl}/widget.js" async></script>`;
  }, [deployment?.id, displayName, isDark]);

  const publish = async () => {
    if (!canPublish) {
      toast.error(hasFailedSources ? "Fix failed knowledge sources before publishing." : "Wait for knowledge indexing to finish before publishing.");
      return;
    }
    if (deployTab === "whatsapp" && !waNumberId.trim()) {
      toast.error("WhatsApp Phone Number ID is required.");
      return;
    }
    if (deployTab === "web" && websiteUrl.trim()) {
      try {
        new URL(websiteUrl.trim());
      } catch {
        toast.error("Enter a valid website URL or leave it blank.");
        return;
      }
    }

    setIsPublishing(true);
    try {
      const id = chatbotId || (await onRequireDraft());
      if (!id) throw new Error("Save the bot before publishing.");
      const created = await api.createDeployment({
        chatbot_id: id,
        channel: deployTab,
        whatsapp_phone_number_id: deployTab === "whatsapp" ? waNumberId.trim() : null,
        whatsapp_business_account_id: deployTab === "whatsapp" ? wabaId.trim() || null : null,
      });
      const activated = await api.activateDeployment(created.id);
      setDeployment(activated);
      toast.success(`${deployTab === "web" ? "Web widget" : "WhatsApp"} deployment is live.`);
    } catch (err: any) {
      toast.error(err?.message || "Failed to publish deployment");
    } finally {
      setIsPublishing(false);
    }
  };

  const handleCopy = () => {
    navigator.clipboard?.writeText(widgetCode);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-300 max-w-5xl">
      <div
        className={`rounded-[2rem] border p-4 sm:p-8 relative overflow-hidden shadow-lg ${
          isDark ? "bg-[#1f1f23] border-[#EBDCFF]/30" : "bg-white border-black/10"
        }`}
      >
        <div className={`absolute top-0 left-0 w-full h-1 ${isDark ? "bg-[#EBDCFF]" : "bg-[#1c1c1e]"}`} />
        <div className="flex flex-col sm:flex-row items-center sm:items-start gap-6 text-center sm:text-left">
          <div className="text-[48px] drop-shadow-md flex-shrink-0">🚀</div>
          <div>
            <h2
              className={`text-[22px] sm:text-[24px] font-serif font-bold ${c("text-[#1c1c1e]", "text-white")}`}
              style={{ fontFamily: "'Playfair Display', serif" }}
            >
              Publish Your Bot
            </h2>
            <p className={`text-[14px] sm:text-[15px] font-medium mt-1.5 ${c("text-[#1c1c1e]/60", "text-[#85948b]")}`}>
              <span className={`font-bold ${c("text-[#1c1c1e]", "text-[#EBDCFF]")}`}>{displayName}</span>{" "}
              {deployment?.is_active ? "is live." : "will go live after a backend deployment is created and activated."}
            </p>
            {hasPendingSources && (
              <p className="text-[12px] font-semibold text-yellow-600 mt-3">Some knowledge sources are still indexing.</p>
            )}
            {hasFailedSources && (
              <p className="text-[12px] font-semibold text-red-500 mt-3">Resolve failed knowledge sources before publishing.</p>
            )}
          </div>
        </div>
      </div>

      <div className="flex flex-col sm:flex-row gap-4">
        {[
          { key: "whatsapp" as Channel, label: "WhatsApp", icon: "chat" },
          { key: "web" as Channel, label: "Web Widget", icon: "language" },
        ].map((item) => (
          <button
            key={item.key}
            onClick={() => setDeployTab(item.key)}
            className={`flex items-center justify-center gap-3 px-6 py-4 rounded-xl font-bold text-[14px] transition-all border shadow-sm w-full sm:w-auto ${
              deployTab === item.key
                ? c("border-[#1c1c1e] bg-[#1c1c1e] text-[#F5F5F7]", "border-[#EBDCFF]/50 bg-[#EBDCFF]/10 text-[#EBDCFF]")
                : c("border-black/5 bg-[#F5F5F7] text-[#1c1c1e]/60 hover:text-[#1c1c1e]", "border-white/[0.06] bg-[#1f1f23] text-[#85948b] hover:text-white")
            }`}
          >
            <span className="material-symbols-outlined text-[20px]">{item.icon}</span>
            {item.label}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div
          className={`rounded-[2rem] border p-4 sm:p-8 space-y-6 shadow-sm ${
            isDark ? "bg-[#1f1f23] border-white/[0.06]" : "bg-white border-black/5"
          }`}
        >
          {deployTab === "whatsapp" ? (
            <>
              <div>
                <h3 className={`text-[16px] font-bold ${c("text-[#1c1c1e]", "text-white")}`}>WhatsApp Business</h3>
                <p className={`text-[12px] font-medium mt-1 ${c("text-[#1c1c1e]/50", "text-[#85948b]")}`}>
                  Use the Meta Phone Number ID, not the display phone number.
                </p>
              </div>
              <input
                type="text"
                value={waNumberId}
                onChange={(e) => setWaNumberId(e.target.value)}
                className={`w-full rounded-xl px-5 py-4 text-[14px] font-medium outline-none shadow-inner ${
                  isDark ? "bg-[#131317] border border-white/[0.06] text-white" : "bg-[#F5F5F7] border border-black/5 text-[#1c1c1e]"
                }`}
                placeholder="Meta phone number ID"
              />
              <input
                type="text"
                value={wabaId}
                onChange={(e) => setWabaId(e.target.value)}
                className={`w-full rounded-xl px-5 py-4 text-[14px] font-medium outline-none shadow-inner ${
                  isDark ? "bg-[#131317] border border-white/[0.06] text-white" : "bg-[#F5F5F7] border border-black/5 text-[#1c1c1e]"
                }`}
                placeholder="WhatsApp Business Account ID (optional)"
              />
            </>
          ) : (
            <>
              <div>
                <h3 className={`text-[16px] font-bold ${c("text-[#1c1c1e]", "text-white")}`}>Web Widget</h3>
                <p className={`text-[12px] font-medium mt-1 ${c("text-[#1c1c1e]/50", "text-[#85948b]")}`}>
                  The embed code uses the stable deployment ID returned by the backend.
                </p>
              </div>
              <input
                type="url"
                value={websiteUrl}
                onChange={(e) => setWebsiteUrl(e.target.value)}
                className={`w-full rounded-xl px-5 py-4 text-[14px] font-medium outline-none shadow-inner ${
                  isDark ? "bg-[#131317] border border-white/[0.06] text-white" : "bg-[#F5F5F7] border border-black/5 text-[#1c1c1e]"
                }`}
                placeholder="https://yourwebsite.com (optional)"
              />
              <div
                className={`border rounded-xl p-5 font-mono text-[12px] leading-relaxed overflow-auto max-h-56 whitespace-pre shadow-inner ${
                  isDark ? "bg-[#0e0e12] border-white/[0.06] text-[#EBDCFF]/80" : "bg-[#F5F5F7] border-black/10 text-[#1c1c1e]"
                }`}
              >
                {widgetCode}
              </div>
              <button
                onClick={handleCopy}
                className={`text-[12px] font-bold flex items-center gap-1 ${c("text-[#1c1c1e]", "text-[#EBDCFF]")}`}
              >
                <span className="material-symbols-outlined text-[14px]">{copied ? "check" : "content_copy"}</span>
                {copied ? "Copied!" : "Copy Code"}
              </button>
            </>
          )}

          <button
            onClick={publish}
            disabled={isPublishing || !canPublish}
            className={`w-full py-4 rounded-xl font-bold text-[14px] transition-colors flex items-center justify-center gap-2 shadow-md disabled:opacity-50 disabled:cursor-not-allowed ${
              isDark ? "bg-[#EBDCFF] hover:bg-[#d8bfff] text-[#1c1c1e]" : "bg-[#1c1c1e] hover:bg-black text-[#F5F5F7]"
            }`}
          >
            <span className="material-symbols-outlined text-[18px]">rocket_launch</span>
            {isPublishing ? "Publishing..." : deployment?.is_active ? "Publish Another Deployment" : "Publish Bot"}
          </button>
        </div>

        <div
          className={`rounded-[2rem] border p-4 sm:p-8 flex flex-col shadow-sm ${
            isDark ? "bg-[#1f1f23] border-white/[0.06]" : "bg-white border-black/5"
          }`}
        >
          <h4 className={`text-[13px] font-bold uppercase tracking-widest mb-6 ${c("text-[#1c1c1e]/60", "text-[#85948b]")}`}>
            Deployment Status
          </h4>
          <div className={`rounded-2xl p-5 border ${isDark ? "bg-[#131317] border-white/[0.04]" : "bg-[#F5F5F7] border-black/5"}`}>
            <p className={`text-[28px] font-bold ${deployment?.is_active ? c("text-[#1c1c1e]", "text-[#EBDCFF]") : c("text-[#1c1c1e]/50", "text-white/40")}`}>
              {deployment?.is_active ? "Live" : "Draft"}
            </p>
            <p className={`text-[12px] font-medium mt-2 ${c("text-[#1c1c1e]/60", "text-[#85948b]")}`}>
              {deployment ? `${deployment.channel} deployment: ${deployment.id}` : "No deployment has been created yet."}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
