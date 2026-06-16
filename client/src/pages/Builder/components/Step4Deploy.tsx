import { useEffect, useMemo, useRef, useState } from "react";
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
  const [deployments, setDeployments] = useState<DeploymentResponse[]>([]);
  const [isLoadingDeployments, setIsLoadingDeployments] = useState(false);
  const [deploymentError, setDeploymentError] = useState("");
  const [isPublishing, setIsPublishing] = useState(false);
  const [copied, setCopied] = useState(false);
  const copyTimerRef = useRef<number | null>(null);

  const displayName = botName || "My Aina Bot";
  const hasFailedSources = knowledgeItems.some((item) => item.status === "failed");
  const hasPendingSources = knowledgeItems.some((item) => item.status === "queued" || item.status === "processing");
  const hasIndexedOrSkippedKnowledge = knowledgeItems.length === 0 || knowledgeItems.every((item) => item.status === "indexed");
  const publishBlockReason = !botName.trim()
    ? "Bot name is required before publishing."
    : hasFailedSources
    ? "Fix failed knowledge sources before publishing."
    : hasPendingSources || !hasIndexedOrSkippedKnowledge
    ? "Wait for knowledge indexing to finish before publishing."
    : "";
  const canPublish = !publishBlockReason;
  const selectedDeployments = useMemo(
    () => deployments.filter((item) => item.channel === deployTab),
    [deployments, deployTab]
  );
  const deployment = selectedDeployments.find((item) => item.is_active) || selectedDeployments[0] || null;
  const normalizedWaNumberId = waNumberId.trim();
  const normalizedWabaId = wabaId.trim() || null;
  const matchingActiveDeployment = useMemo(
    () =>
      deployments.find((item) => {
        if (item.channel !== deployTab || !item.is_active) return false;
        if (deployTab === "web") return true;
        return (
          item.whatsapp_phone_number_id === normalizedWaNumberId &&
          (item.whatsapp_business_account_id || null) === normalizedWabaId
        );
      }) || null,
    [deployments, deployTab, normalizedWaNumberId, normalizedWabaId]
  );
  const matchingDraftDeployment = useMemo(
    () =>
      deployments.find((item) => {
        if (item.channel !== deployTab || item.is_active) return false;
        if (deployTab === "web") return true;
        return (
          item.whatsapp_phone_number_id === normalizedWaNumberId &&
          (item.whatsapp_business_account_id || null) === normalizedWabaId
        );
      }) || null,
    [deployments, deployTab, normalizedWaNumberId, normalizedWabaId]
  );

  const upsertDeployment = (next: DeploymentResponse) => {
    setDeployments((prev) => [next, ...prev.filter((item) => item.id !== next.id)]);
  };

  useEffect(() => {
    if (!chatbotId) {
      setDeployments([]);
      setDeploymentError("");
      return;
    }

    let cancelled = false;
    setIsLoadingDeployments(true);
    setDeploymentError("");

    api
      .listDeployments(chatbotId)
      .then((items) => {
        if (!cancelled) setDeployments(items);
      })
      .catch((err: any) => {
        if (cancelled) return;
        const message = err?.message || "Failed to load deployments.";
        setDeploymentError(message);
        toast.error(message);
      })
      .finally(() => {
        if (!cancelled) setIsLoadingDeployments(false);
      });

    return () => {
      cancelled = true;
    };
  }, [chatbotId]);

  useEffect(() => {
    if (deployTab !== "whatsapp" || !deployment) return;
    setWaNumberId(deployment.whatsapp_phone_number_id || "");
    setWabaId(deployment.whatsapp_business_account_id || "");
  }, [deployTab, deployment?.id]);

  useEffect(() => {
    return () => {
      if (copyTimerRef.current) window.clearTimeout(copyTimerRef.current);
    };
  }, []);

  const widgetCode = useMemo(() => {
    const deploymentId = deployment?.is_active ? deployment.id : "DEPLOYMENT_ID_AFTER_PUBLISH";
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
  }, [deployment?.id, deployment?.is_active, displayName, isDark]);

  const publishButtonLabel = isPublishing
    ? "Publishing..."
    : matchingActiveDeployment
    ? "Deployment Live"
    : matchingDraftDeployment
    ? "Activate Deployment"
    : deployment?.is_active && deployTab === "whatsapp"
    ? "Publish New Deployment"
    : "Publish Bot";

  const publish = async () => {
    if (isPublishing) return;
    if (!canPublish) {
      toast.error(publishBlockReason);
      return;
    }
    if (deployTab === "whatsapp" && !normalizedWaNumberId) {
      toast.error("WhatsApp Phone Number ID is required.");
      return;
    }

    setIsPublishing(true);
    const toastId = toast.loading(matchingDraftDeployment ? "Activating deployment..." : "Publishing deployment...");

    try {
      const id = chatbotId || (await onRequireDraft());
      if (!id) throw new Error("Save the bot before publishing.");

      if (matchingActiveDeployment) {
        toast.success(`${deployTab === "web" ? "Web widget" : "WhatsApp"} deployment is already live.`, { id: toastId });
        return;
      }

      let draft = matchingDraftDeployment;
      if (!draft) {
        draft = await api.createDeployment({
          chatbot_id: id,
          channel: deployTab,
          whatsapp_phone_number_id: deployTab === "whatsapp" ? normalizedWaNumberId : null,
          whatsapp_business_account_id: deployTab === "whatsapp" ? normalizedWabaId : null,
        });
        upsertDeployment(draft);
      }

      try {
        const activated = await api.activateDeployment(draft.id);
        upsertDeployment(activated);
        toast.success(`${deployTab === "web" ? "Web widget" : "WhatsApp"} deployment is live.`, { id: toastId });
      } catch (activateErr: any) {
        upsertDeployment(draft);
        toast.error(`Deployment was saved but activation failed. ${activateErr?.message || "Please try again."}`, { id: toastId });
      }
    } catch (err: any) {
      toast.error(err?.message || "Failed to publish deployment", { id: toastId });
    } finally {
      setIsPublishing(false);
    }
  };

  const handleCopy = async () => {
    if (!deployment?.is_active) {
      toast.error("Publish the web widget before copying the embed code.");
      return;
    }
    if (!navigator.clipboard?.writeText) {
      toast.error("Clipboard access is not available in this browser.");
      return;
    }

    try {
      await navigator.clipboard.writeText(widgetCode);
      setCopied(true);
      toast.success("Embed code copied.");
      if (copyTimerRef.current) window.clearTimeout(copyTimerRef.current);
      copyTimerRef.current = window.setTimeout(() => setCopied(false), 2000);
    } catch {
      toast.error("Could not copy embed code. Please copy it manually.");
    }
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
            {deploymentError && (
              <p className="text-[12px] font-semibold text-red-500 mt-3">{deploymentError}</p>
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
            disabled={isPublishing}
            className={`flex items-center justify-center gap-3 px-6 py-4 rounded-xl font-bold text-[14px] transition-all border shadow-sm w-full sm:w-auto ${
              deployTab === item.key
                ? c("border-[#1c1c1e] bg-[#1c1c1e] text-[#F5F5F7]", "border-[#EBDCFF]/50 bg-[#EBDCFF]/10 text-[#EBDCFF]")
                : c("border-black/5 bg-[#F5F5F7] text-[#1c1c1e]/60 hover:text-[#1c1c1e]", "border-white/[0.06] bg-[#1f1f23] text-[#85948b] hover:text-white")
            } disabled:opacity-50 disabled:cursor-not-allowed`}
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
                <h3 className={`text-[16px] font-bold ${c("text-[#1c1c1e]", "text-white")}`}>Meta Account Generated Number</h3>
                <p className={`text-[12px] font-medium mt-1 ${c("text-[#1c1c1e]/50", "text-[#85948b]")}`}>
                  Use the Meta Phone Number ID, not the display phone number.
                </p>
              </div>
              <input
                type="text"
                value={waNumberId}
                onChange={(e) => setWaNumberId(e.target.value)}
                disabled={isPublishing}
                className={`w-full rounded-xl px-5 py-4 text-[14px] font-medium outline-none shadow-inner ${
                  isDark ? "bg-[#131317] border border-white/[0.06] text-white" : "bg-[#F5F5F7] border border-black/5 text-[#1c1c1e]"
                }`}
                placeholder="Meta phone number ID"
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
              <div
                className={`border rounded-xl p-5 font-mono text-[12px] leading-relaxed overflow-auto max-h-56 whitespace-pre shadow-inner ${
                  isDark ? "bg-[#0e0e12] border-white/[0.06] text-[#EBDCFF]/80" : "bg-[#F5F5F7] border-black/10 text-[#1c1c1e]"
                }`}
              >
                {widgetCode}
              </div>
              <button
                onClick={handleCopy}
                className={`text-[12px] font-bold flex items-center gap-1 ${
                  deployment?.is_active
                    ? c("text-[#1c1c1e]", "text-[#EBDCFF]")
                    : c("text-[#1c1c1e]/50", "text-[#85948b]")
                }`}
              >
                <span className="material-symbols-outlined text-[14px]">{copied ? "check" : "content_copy"}</span>
                {copied ? "Copied!" : "Copy Code"}
              </button>
            </>
          )}

          <button
            onClick={publish}
            disabled={isPublishing || isLoadingDeployments}
            className={`w-full py-4 rounded-xl font-bold text-[14px] transition-colors flex items-center justify-center gap-2 shadow-md disabled:opacity-50 disabled:cursor-not-allowed ${
              isDark ? "bg-[#EBDCFF] hover:bg-[#d8bfff] text-[#1c1c1e]" : "bg-[#1c1c1e] hover:bg-black text-[#F5F5F7]"
            }`}
          >
            <span className="material-symbols-outlined text-[18px]">rocket_launch</span>
            {isLoadingDeployments ? "Loading Deployments..." : publishButtonLabel}
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
              {isLoadingDeployments ? "Loading" : deployment?.is_active ? "Live" : "Draft"}
            </p>
            <p className={`text-[12px] font-medium mt-2 ${c("text-[#1c1c1e]/60", "text-[#85948b]")}`}>
              {deployment
                ? `${deployment.channel} deployment: ${deployment.id}`
                : isLoadingDeployments
                ? "Checking existing deployments..."
                : "No deployment has been created yet."}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
