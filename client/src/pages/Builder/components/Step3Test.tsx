import { useState, useEffect, useRef } from "react";
import { useTheme } from "../../../contexts/ThemeContext";
import { ChatMessage } from "../types";
import ChatSimulator from "./ChatSimulator";
import { api, ChatResponse } from "../../../lib/api";

interface Step3TestProps {
  persona: any;
  botName: string;
  chatbotId: string | null;
  onRequireDraft: () => Promise<string | null>;
}

const createMessageId = (prefix: string) =>
  `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2)}`;

export default function Step3Test({ persona, botName, chatbotId, onRequireDraft }: Step3TestProps) {
  const { isDark } = useTheme();
  const c = (light: string, dark: string) => (isDark ? dark : light);

  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "bot",
      text: persona?.greeting ?? `Hi! I'm ${botName || "your AI Bot"}. How can I help you today?`,
    },
  ]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [lastSources, setLastSources] = useState<ChatResponse["sources"]>([]);
  const [testError, setTestError] = useState("");
  const streamInFlightRef = useRef(false);
  const isMountedRef = useRef(true);
  const activeStreamAbortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
      activeStreamAbortRef.current?.abort();
    };
  }, []);

  // Listen for out-of-band messages (e.g. human agent replies) via SSE
  useEffect(() => {
    if (!conversationId || !chatbotId) return;

    const abortController = new AbortController();

    api.streamConversationEvents(
      chatbotId,
      conversationId,
      (msg: any) => {
        setMessages((prev) => {
          if (msg.id && prev.some((item) => item.id === msg.id)) return prev;
          return [
            ...prev,
            { id: msg.id || createMessageId("event"), role: msg.role === "user" ? "user" : "bot", text: msg.content }
          ];
        });
      },
      () => {
        setMessages((prev) => [
          ...prev,
          { id: createMessageId("resolve"), role: "bot", text: "This conversation has been resolved by the agent." }
        ]);
      },
      abortController.signal
    );

    return () => {
      abortController.abort();
    };
  }, [conversationId, chatbotId]);

  const sendMessage = async () => {
    if (!input.trim() || streamInFlightRef.current) return;
    const userMsg = input.trim();
    const userMessageId = createMessageId("user");
    const botMessageId = createMessageId("bot");
    let currentResponse = "";
    let botMessageAdded = false;
    let rafId: number | null = null;
    let pendingFlush = false;
    const abortController = new AbortController();

    setInput("");
    setTestError("");
    setLastSources([]);
    setMessages((prev) => [...prev, { id: userMessageId, role: "user", text: userMsg }]);
    setIsTyping(true);
    setIsSending(true);
    streamInFlightRef.current = true;
    activeStreamAbortRef.current = abortController;

    try {
      const id = chatbotId || (await onRequireDraft());
      if (!id) throw new Error("Save the bot before testing.");

      // Batch token updates into animation frames for smooth rendering
      const flushTokens = () => {
        pendingFlush = false;
        rafId = null;
        const snapshot = currentResponse;
        setMessages((prev) => {
          return prev.map((message) =>
            message.id === botMessageId ? { ...message, text: snapshot } : message
          );
        });
      };

      const result = await api.streamBuilderMessage(
        id,
        {
          message: userMsg,
          conversation_id: conversationId,
        },
        (token) => {
          currentResponse += token;

          if (!botMessageAdded) {
            // First token: hide typing dots and add the bot message in one go
            botMessageAdded = true;
            setIsTyping(false);
            setMessages((prev) => [...prev, { id: botMessageId, role: "bot", text: currentResponse }]);
            return;
          }

          // Subsequent tokens: batch into animation frames
          if (!pendingFlush) {
            pendingFlush = true;
            rafId = requestAnimationFrame(flushTokens);
          }
        },
        undefined,
        abortController.signal
      );

      // Final payload is the source of truth. Fallback responses do not stream
      // tokens, so they need to be rendered from result.response.
      if (rafId) cancelAnimationFrame(rafId);
      console.log("[ESCALATION DEBUG] result received:", JSON.stringify(result));
      const finalResponse = result.response?.trim() || currentResponse || "";
      currentResponse = finalResponse;
      setIsTyping(false);

      // During live agent chat (escalated), response is null — don't add a bot bubble.
      // The agent will reply via SSE from the inbox.
      if (!finalResponse) {
        // Remove the bot placeholder if streaming added one with no content
        if (botMessageAdded) {
          setMessages((prev) => prev.filter((m) => m.id !== botMessageId));
        }
        setConversationId(result.conversation_id);
        setLastSources(result.sources || []);
        return;
      }

      setMessages((prev) => {
        if (!botMessageAdded && finalResponse) {
          return [...prev, { id: botMessageId, role: "bot", text: finalResponse }];
        }

        return prev.map((message) =>
          message.id === botMessageId ? { ...message, text: finalResponse } : message
        );
      });

      setConversationId(result.conversation_id);
      setLastSources(result.sources || []);
    } catch (err: any) {
      console.error("[ESCALATION DEBUG] sendMessage error:", err);
      if (!isMountedRef.current || err?.name === "AbortError") return;
      const message = err?.message || "Failed to test chatbot";
      setTestError(message);
      if (rafId) cancelAnimationFrame(rafId);
      setMessages((prev) => {
        if (botMessageAdded) {
          return prev.map((item) =>
            item.id === botMessageId ? { ...item, text: `Error: ${message}` } : item
          );
        }
        return [...prev, { id: botMessageId, role: "bot", text: `Error: ${message}` }];
      });
    } finally {
      if (activeStreamAbortRef.current === abortController) {
        activeStreamAbortRef.current = null;
      }
      streamInFlightRef.current = false;
      if (isMountedRef.current) {
        setIsSending(false);
        setIsTyping(false);
      }
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 animate-in fade-in duration-300">
      <div className="lg:col-span-5 space-y-6">
        <div
          className={`rounded-[2rem] border p-4 sm:p-8 shadow-sm ${
            isDark ? "bg-[#1f1f23] border-white/[0.06]" : "bg-white border-black/5"
          }`}
        >
          <div className="flex items-center gap-4 mb-8">
            <div
              className={`w-14 h-14 rounded-2xl flex items-center justify-center shadow-inner flex-shrink-0 ${
                isDark ? "bg-[#EBDCFF]/10 text-[#EBDCFF]" : "bg-black/5 text-[#1c1c1e]"
              }`}
            >
              <span className="material-symbols-outlined text-[28px]">precision_manufacturing</span>
            </div>
            <div>
              <h3
                className={`text-[20px] font-serif font-bold ${c("text-[#1c1c1e]", "text-white")}`}
                style={{ fontFamily: "'Playfair Display', serif" }}
              >
                Test Live Behavior
              </h3>
              <p className={`text-[13px] font-medium mt-1 ${c("text-[#1c1c1e]/60", "text-[#85948b]")}`}>
                Uses your saved persona and indexed knowledge sources
              </p>
            </div>
          </div>

          <div className="space-y-3">
            {[
              { label: "Persona", detail: persona?.name ? "Identity saved for testing" : "Save persona before testing" },
              { label: "Knowledge Retrieval", detail: "Queries the real RAG endpoint" },
              { label: "Language Mode", detail: "Backend detects English, Urdu, and Roman Urdu" },
              { label: "Conversation Memory", detail: conversationId ? "Current test session active" : "Starts on first message" },
              { label: "Sources", detail: lastSources.length ? `${lastSources.length} source chunks returned` : "No sources returned yet" },
            ].map((item) => (
              <div
                key={item.label}
                className={`flex items-center gap-4 p-4 rounded-2xl border transition-all ${
                  isDark ? "bg-[#131317] border-white/[0.04]" : "bg-[#F5F5F7] border-black/5"
                }`}
              >
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 shadow-sm ${
                    isDark ? "bg-[#EBDCFF]/15 text-[#EBDCFF]" : "bg-white text-[#1c1c1e]"
                  }`}
                >
                  <span className="material-symbols-outlined text-[16px]">check</span>
                </div>
                <div className="flex-1">
                  <p className={`text-[14px] font-bold ${c("text-[#1c1c1e]", "text-white")}`}>{item.label}</p>
                  <p className={`text-[11px] font-medium mt-0.5 ${c("text-[#1c1c1e]/50", "text-[#55635a]")}`}>
                    {item.detail}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {(testError || lastSources.length > 0) && (
          <div
            className={`rounded-[2rem] border p-4 sm:p-8 shadow-sm ${
              isDark ? "bg-[#1f1f23] border-white/[0.06]" : "bg-white border-black/5"
            }`}
          >
            {testError && <p className="text-[12px] font-semibold text-red-500">{testError}</p>}

            {lastSources.length > 0 && (
              <div className={`${testError ? "mt-5 border-t pt-4 " : ""}space-y-2 ${c("border-black/5", "border-white/[0.06]")}`}>
                <h5 className={`text-[11px] font-bold uppercase tracking-widest ${c("text-[#1c1c1e]/50", "text-[#85948b]")}`}>
                  Returned Sources
                </h5>
                {lastSources.slice(0, 3).map((source) => (
                  <p key={source.chunk_id} className={`text-[11px] leading-relaxed line-clamp-2 ${c("text-[#1c1c1e]/60", "text-[#85948b]")}`}>
                    {source.text || "Source text unavailable"}
                  </p>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      <div className="lg:col-span-7 h-[660px]">
        <ChatSimulator
          botName={botName || persona?.name || "Aina Bot"}
          role={persona?.role || "AI Assistant"}
          emoji={persona?.emoji || "🤖"}
          tone={persona?.traits?.[0] || "friendly"}
          messages={messages}
          isTyping={isTyping}
          input={input}
          onInputChange={setInput}
          onSend={sendMessage}
          isSending={isSending}
          isInteractive={true}
        />
      </div>
    </div>
  );
}
