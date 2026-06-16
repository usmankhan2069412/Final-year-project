import { useState, useEffect, useRef } from "react";
import { useTheme } from "../contexts/ThemeContext";
import { useLayoutConfig } from "../contexts/LayoutContext";
import { api } from "../lib/api";
import MarkdownRenderer from "../components/MarkdownRenderer";

interface Message {
  id: string;
  role: string;
  content: string;
  created_at: string;
}

interface Conversation {
  id: string;
  chatbot_id: string;
  chatbot_name: string;
  assigned_agent_id: string | null;
  status: string;
  started_at: string;
  messages: Message[];
  last_message: string;
}

const CANNED_RESPONSES = [
  { label: "Intro Handoff", text: "Hello! I am a support agent taking over this conversation. How can I help you today?" },
  { label: "Looking Into It", text: "Please give me a moment while I review your account details and investigate this request." },
  { label: "Fixed / Applied", text: "I have successfully resolved the issue on our end. Could you please double-check if it is working now?" },
  { label: "Resolution Closing", text: "Glad I could help! I will mark this conversation as resolved now. Feel free to reach out if you need anything else." },
];

export default function Inbox() {
  const { isDark } = useTheme();
  useLayoutConfig({ title: "Escalated Chats" });
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [filterAssigned, setFilterAssigned] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [replyText, setReplyText] = useState("");
  const [sending, setSending] = useState(false);
  const [loading, setLoading] = useState(true);
  const [isConnected, setIsConnected] = useState(false);
  const [isDetailsOpen, setIsDetailsOpen] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const sseAbortControllerRef = useRef<AbortController | null>(null);
  const escalationDebounceRef = useRef<NodeJS.Timeout | null>(null);

  const c = (light: string, dark: string) => (isDark ? dark : light);

  // Fetch escalated conversations list
  async function fetchConversations() {
    try {
      const token = localStorage.getItem("token");
      const headers: Record<string, string> = {
        "Content-Type": "application/json",
      };
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }
      const response = await fetch(
        `${api.baseUrl}/api/v1/agents/conversations?assigned_only=${filterAssigned}`,
        { headers }
      );
      if (response.ok) {
        const json = await response.json();
        setConversations(json);
      }
    } catch (err) {
      console.error("Error fetching escalated conversations:", err);
    } finally {
      setLoading(false);
    }
  }

  // Fetch on filter toggled or mount
  useEffect(() => {
    fetchConversations();
  }, [filterAssigned]);

  // Scroll to bottom of message viewport
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [selectedId, conversations]);

  // Reset details panel open state on selected chat change
  useEffect(() => {
    setIsDetailsOpen(false);
  }, [selectedId]);

  // Real-time SSE stream reader
  useEffect(() => {
    let active = true;
    const controller = new AbortController();
    sseAbortControllerRef.current = controller;

    async function connectSSE() {
      const token = localStorage.getItem("token");
      if (!token) return;

      try {
        const response = await fetch(`${api.baseUrl}/api/v1/agents/stream`, {
          signal: controller.signal,
          headers: {
            "Authorization": `Bearer ${token}`,
          },
        });

        if (!response.ok) {
          throw new Error("SSE connection failed");
        }

        setIsConnected(true);
        // Sync conversations on successful connection/reconnection to avoid missed events
        fetchConversations();
        
        const reader = response.body?.getReader();
        if (!reader) return;

        const decoder = new TextDecoder();
        let buffer = "";

        while (active) {
          const { value, done } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          let currentEvent = "";
          for (const line of lines) {
            const trimmed = line.trim();
            if (trimmed.startsWith("event: ")) {
              currentEvent = trimmed.slice(7).trim();
            } else if (trimmed.startsWith("data: ")) {
              const dataStr = trimmed.slice(6).trim();
              try {
                const data = JSON.parse(dataStr);
                handleSSEEvent(currentEvent, data);
              } catch (e) {
                console.error("Failed to parse SSE payload:", e);
              }
              currentEvent = "";
            }
          }
        }
      } catch (err) {
        const error = err as Error;
        if (error.name !== "AbortError") {
          console.warn("SSE disconnected. Reconnecting in 3s…", error);
          setIsConnected(false);
          if (active) {
            setTimeout(connectSSE, 3000);
          }
        }
      }
    }

    connectSSE();

    return () => {
      active = false;
      controller.abort();
    };
  }, [filterAssigned]); // Recalculate or reconnect if filters change

  interface SSEEventPayload {
    conversation_id?: string;
    chatbot_id?: string;
    status?: string;
    assigned_agent_id?: string;
    message?: {
      id: string;
      role: string;
      content: string;
      created_at: string;
    };
  }

  // SSE event router
  function handleSSEEvent(event: string, data: SSEEventPayload) {
    if (event === "escalation") {
      // Re-fetch list on new escalation with debouncing
      if (escalationDebounceRef.current) clearTimeout(escalationDebounceRef.current);
      escalationDebounceRef.current = setTimeout(() => {
        fetchConversations();
      }, 500);
    } else if (event === "resolve") {
      const resolvedId = data.conversation_id;
      if (resolvedId) {
        setConversations((prev) => prev.filter((conv) => conv.id !== resolvedId));
        setSelectedId((current) => (current === resolvedId ? null : current));
      }
    } else if (event === "message") {
      const msgData = data.message;
      const convId = data.conversation_id;
      if (!msgData || !convId) return;

      setConversations((prev) =>
        prev.map((conv) => {
          if (conv.id === convId) {
            // Append message if not duplicate
            const alreadyExists = Boolean(msgData.id) && conv.messages.some((m) => m.id === msgData.id);
            const updatedMessages = alreadyExists
              ? conv.messages
              : [...conv.messages, msgData];
            return {
              ...conv,
              messages: updatedMessages,
              last_message: msgData.content,
            };
          }
          return conv;
        })
      );
    }
  }

  // Selected conversation object
  const activeChat = conversations.find((c) => c.id === selectedId);

  // Send reply
  async function handleSendReply(e?: React.FormEvent) {
    if (e) e.preventDefault();
    if (!replyText.trim() || !selectedId || sending) return;

    setSending(true);
    try {
      const token = localStorage.getItem("token");
      const headers: Record<string, string> = {
        "Content-Type": "application/json",
      };
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }

      const response = await fetch(
        `${api.baseUrl}/api/v1/agents/conversations/${selectedId}/reply`,
        {
          method: "POST",
          headers,
          body: JSON.stringify({ message: replyText.trim() }),
        }
      );

      if (response.ok) {
        const res = await response.json();
        const newMsg = res.message;

        // Optimistically update conversation state
        setConversations((prev) =>
          prev.map((conv) => {
            if (conv.id === selectedId) {
              const alreadyExists = conv.messages.some((m) => m.id === newMsg.id);
              const updatedMessages = alreadyExists
                ? conv.messages
                : [...conv.messages, newMsg];
              return {
                ...conv,
                messages: updatedMessages,
                last_message: newMsg.content,
              };
            }
            return conv;
          })
        );
        setReplyText("");
      } else {
        const errorData = await response.json();
        console.error("Failed to send message:", errorData.detail || response.statusText);
      }
    } catch (err) {
      console.error("Error sending reply:", err);
    } finally {
      setSending(false);
    }
  }

  // Resolve chat
  async function handleResolveChat() {
    if (!selectedId) return;

    try {
      const token = localStorage.getItem("token");
      const headers: Record<string, string> = {};
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }

      const response = await fetch(
        `${api.baseUrl}/api/v1/agents/conversations/${selectedId}/resolve`,
        {
          method: "POST",
          headers,
        }
      );

      if (response.ok) {
        // Remove resolved chat from local state
        setConversations((prev) => prev.filter((conv) => conv.id !== selectedId));
        setSelectedId(null);
      } else {
        console.error("Failed to resolve chat");
      }
    } catch (err) {
      console.error("Error resolving conversation:", err);
    }
  }

  // Format timestamp helpers
  const formatTime = (isoString: string) => {
    const d = new Date(isoString);
    return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  };

  const getRelativeTime = (isoString: string) => {
    const now = new Date();
    const past = new Date(isoString);
    const diffMs = now.getTime() - past.getTime();
    const diffMins = Math.max(1, Math.floor(diffMs / 60000));
    if (diffMins < 60) return `${diffMins}m ago`;
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    return past.toLocaleDateString([], { month: "short", day: "numeric" });
  };

  // Filter conversations based on search
  const filteredConversations = conversations.filter(
    (conv) =>
      conv.chatbot_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      conv.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      conv.last_message.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Chats Skeleton Loader
  const ChatsSkeleton = () => (
    <div className="space-y-1">
      {[1, 2, 3, 4, 5].map((i) => (
        <div
          key={i}
          className={`p-4 rounded-2xl flex items-start gap-3.5 border animate-pulse ${
            isDark ? "bg-[#1f1f23]/40 border-white/[0.04]" : "bg-white border-black/5"
          }`}
        >
          {/* Avatar Icon */}
          <div className={`w-10 h-10 rounded-xl flex-shrink-0 ${isDark ? "bg-white/5" : "bg-black/5"}`} />

          {/* Snippet info */}
          <div className="flex-1 min-w-0 space-y-2">
            <div className="flex items-center justify-between">
              <div className={`h-3 w-16 rounded ${isDark ? "bg-white/5" : "bg-black/5"}`} />
              <div className={`h-2.5 w-12 rounded ${isDark ? "bg-white/5" : "bg-black/5"}`} />
            </div>
            <div className={`h-4 w-32 rounded ${isDark ? "bg-white/5" : "bg-black/5"}`} />
            <div className={`h-3 w-40 rounded ${isDark ? "bg-white/5" : "bg-black/5"}`} />
          </div>
        </div>
      ))}
    </div>
  );

  return (
    <div className="flex-1 flex overflow-hidden relative z-10">
          
          {/* Left Column: Conversations Sidebar */}
          <div
            className={`w-full md:w-80 lg:w-96 flex flex-col border-r flex-shrink-0 transition-colors ${
              c("bg-white border-black/5", "bg-[#17171a] border-white/[0.06]")
            } ${selectedId ? "hidden md:flex" : "flex"}`}
          >
            {/* Header & Connection status */}
            <div className="p-5 border-b border-white/5 flex flex-col gap-3">
              <div className="flex items-center justify-between">
                <h1
                  className={`text-2xl font-bold font-serif ${c("text-[#1c1c1e]", "text-white")}`}
                  style={{ fontFamily: "'Playfair Display', serif", textWrap: "balance" }}
                >
                  Agent Inbox
                </h1>
                <div
                  className="flex items-center gap-1.5"
                  aria-live="polite"
                  aria-label={`Connection status: ${isConnected ? "Live" : "Connecting"}`}
                >
                  <div
                    aria-hidden="true"
                    className={`w-2 h-2 rounded-full ${
                      isConnected ? "bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]" : "bg-amber-500 animate-pulse"
                    }`}
                  />
                  <span className={`text-[10px] font-bold uppercase tracking-wider ${c("text-black/40", "text-white/40")}`}>
                    {isConnected ? "Live" : "Connecting…"}
                  </span>
                </div>
              </div>

              {/* Search input */}
              <div
                className={`flex items-center gap-2 border px-3.5 py-2 rounded-xl transition-all shadow-inner focus-within:ring-2 focus-within:ring-purple-500/40 focus-within:border-purple-500 ${
                  isDark ? "bg-[#131317] border-white/[0.06]" : "bg-[#F5F5F7] border-black/10"
                }`}
              >
                <span className={`material-symbols-outlined text-[18px] ${c("text-black/30", "text-white/30")}`} aria-hidden="true">
                  search
                </span>
                <input
                  type="text"
                  name="search"
                  autoComplete="off"
                  spellCheck={false}
                  aria-label="Search chats, bots, and messages"
                  placeholder="Search chats, bots, messages…"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className={`flex-1 bg-transparent text-[13px] font-medium outline-none ${
                    isDark ? "text-white placeholder:text-white/30" : "text-[#1c1c1e] placeholder:text-black/30"
                  }`}
                />
              </div>

              {/* Filters Toggle Tabs */}
              <div className={`grid grid-cols-2 p-1 rounded-xl gap-1 ${c("bg-black/5", "bg-black/30")}`}>
                <button
                  onClick={() => setFilterAssigned(false)}
                  className={`py-1.5 text-[11px] font-bold uppercase tracking-widest rounded-lg transition-all focus-visible:ring-2 focus-visible:ring-purple-500 focus-visible:outline-none ${
                    !filterAssigned
                      ? isDark
                        ? "bg-[#1f1f23] text-white shadow-sm border border-white/5"
                        : "bg-white text-[#1c1c1e] shadow-sm border border-black/5"
                      : c("text-[#1c1c1e]/60 hover:text-[#1c1c1e]", "text-white/40 hover:text-white")
                  }`}
                >
                  All Escalated
                </button>
                <button
                  onClick={() => setFilterAssigned(true)}
                  className={`py-1.5 text-[11px] font-bold uppercase tracking-widest rounded-lg transition-all focus-visible:ring-2 focus-visible:ring-purple-500 focus-visible:outline-none ${
                    filterAssigned
                      ? isDark
                        ? "bg-[#1f1f23] text-white shadow-sm border border-white/5"
                        : "bg-white text-[#1c1c1e] shadow-sm border border-black/5"
                      : c("text-[#1c1c1e]/60 hover:text-[#1c1c1e]", "text-white/40 hover:text-white")
                  }`}
                >
                  Assigned To Me
                </button>
              </div>
            </div>

            {/* Chats List */}
            <div className="flex-1 overflow-y-auto custom-scrollbar divide-y divide-white/[0.04] p-2 space-y-1">
              {loading ? (
                <ChatsSkeleton />
              ) : filteredConversations.length === 0 ? (
                <div className={`text-center py-10 text-[13px] ${c("text-black/40", "text-white/30")}`}>
                  No active escalated chats found
                </div>
              ) : (
                filteredConversations.map((conv) => {
                  const isSelected = conv.id === selectedId;
                  const displayId = `#${conv.id.substring(0, 8).toUpperCase()}`;
                  return (
                    <button
                      key={conv.id}
                      onClick={() => setSelectedId(conv.id)}
                      className={`w-full text-left p-4 rounded-2xl transition-all flex items-start gap-3.5 group relative border focus-visible:ring-2 focus-visible:ring-purple-500 focus-visible:outline-none ${
                        isSelected
                          ? isDark
                            ? "bg-[#EBDCFF]/10 border-[#EBDCFF]/20 text-white"
                            : "bg-[#EBDCFF] border-[#EBDCFF] text-[#1c1c1e]"
                          : isDark
                          ? "bg-transparent border-transparent hover:bg-white/[0.02] text-white/70 hover:text-white"
                          : "bg-transparent border-transparent hover:bg-black/[0.02] text-[#1c1c1e]/70 hover:text-[#1c1c1e]"
                      }`}
                    >
                      {/* Avatar Icon */}
                      <div
                        className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 shadow-sm border text-[18px] ${
                          isSelected
                            ? isDark
                              ? "bg-[#EBDCFF]/20 border-transparent text-[#EBDCFF]"
                              : "bg-[#1c1c1e] border-transparent text-[#F5F5F7]"
                            : isDark
                            ? "bg-[#1f1f23] border-white/[0.04] text-white/50 group-hover:text-white"
                            : "bg-[#F5F5F7] border-black/5 text-[#1c1c1e]/50 group-hover:text-[#1c1c1e]"
                        }`}
                      >
                        <span className="material-symbols-outlined" aria-hidden="true">support_agent</span>
                      </div>

                      {/* Snippet info */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between mb-1">
                          <div className="flex items-center gap-2">
                            <span className="font-mono text-[12px] font-bold tracking-tight">{displayId}</span>
                            {conv.assigned_agent_id && !isSelected && (
                              <div className="flex items-center gap-0.5 bg-emerald-500/10 text-emerald-500 px-1.5 py-0.5 rounded">
                                <span className="material-symbols-outlined text-[10px]" aria-hidden="true">lock</span>
                                <span className="text-[8px] font-bold uppercase tracking-widest">Assigned</span>
                              </div>
                            )}
                          </div>
                          <span className={`text-[10px] font-medium flex-shrink-0 ${isSelected ? "opacity-70" : "opacity-40"}`}>
                            {getRelativeTime(conv.started_at)}
                          </span>
                        </div>
                        <p className="text-[13px] font-bold truncate">{conv.chatbot_name}</p>
                        <p className={`text-[11px] truncate mt-0.5 ${isSelected ? "opacity-80" : "opacity-50"}`}>
                          {conv.last_message || "No messages yet"}
                        </p>
                      </div>

                    </button>
                  );
                })
              )}
            </div>
          </div>

          {/* Middle/Right Columns: Chat Viewport & Details Panel */}
          {activeChat ? (
            <div className="flex-1 flex overflow-hidden relative">
              
              {/* Middle Column: Chat Workspace */}
              <div className="flex-1 flex flex-col overflow-hidden bg-transparent">
                
                {/* Chat Top Header */}
                <div
                  className={`p-4 sm:p-5 border-b flex items-center justify-between flex-shrink-0 transition-colors z-20 ${
                    c("bg-white border-black/5", "bg-[#17171a]/80 border-white/[0.06] backdrop-blur-md")
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <button
                      onClick={() => setSelectedId(null)}
                      aria-label="Go back to conversation list"
                      className={`md:hidden w-8 h-8 rounded-full flex items-center justify-center border hover:bg-black/5 focus-visible:ring-2 focus-visible:ring-purple-500 focus-visible:outline-none ${
                        c("border-black/5", "border-white/10")
                      }`}
                    >
                      <span className="material-symbols-outlined text-[18px]" aria-hidden="true">arrow_back</span>
                    </button>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-[14px] font-bold">
                          #{activeChat.id.substring(0, 8).toUpperCase()}
                        </span>
                        <span className="px-2 py-0.5 rounded-full text-[9px] font-bold bg-[#EF4444] text-white tracking-widest uppercase border border-red-500/20 shadow-sm animate-pulse">
                          Escalated
                        </span>
                      </div>
                      <p className={`text-[11px] font-medium mt-0.5 ${c("text-black/50", "text-white/40")}`}>
                        Source Bot: <span className="font-bold">{activeChat.chatbot_name}</span>
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={handleResolveChat}
                      className={`px-4 py-2 rounded-xl text-[12px] font-bold flex items-center gap-1.5 transition-all shadow-sm border focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-purple-500 focus-visible:outline-none ${
                        isDark
                          ? "bg-[#EBDCFF] hover:bg-[#d8bfff] text-[#1c1c1e] border-transparent"
                          : "bg-[#1c1c1e] hover:bg-black text-white border-transparent"
                      }`}
                    >
                      <span className="material-symbols-outlined text-[16px]" aria-hidden="true">check_circle</span>
                      Resolve &amp; Close
                    </button>
                    <button
                      onClick={() => setIsDetailsOpen((prev) => !prev)}
                      aria-label="Toggle takeover details and quick answers"
                      className={`lg:hidden w-9 h-9 rounded-xl flex items-center justify-center border hover:bg-black/5 focus-visible:ring-2 focus-visible:ring-purple-500 focus-visible:outline-none ${
                        c("border-black/5 bg-white text-[#1c1c1e]", "border-white/10 bg-[#1f1f23] text-white")
                      }`}
                    >
                      <span className="material-symbols-outlined text-[20px]" aria-hidden="true">info</span>
                    </button>
                  </div>
                </div>

                {/* Messages Log area */}
                <div
                  className={`flex-1 overflow-y-auto p-4 sm:p-6 space-y-5 custom-scrollbar ${
                    c("bg-black/[0.01]", "bg-[#111114]")
                  }`}
                >
                  {activeChat.messages.map((msg, index) => {
                    const isAgentReply = msg.role === "bot";
                    return (
                      <div
                        key={msg.id || index}
                        className={`flex gap-3 items-end max-w-[85%] sm:max-w-[75%] ${
                          isAgentReply ? "ml-auto flex-row-reverse" : "mr-auto"
                        }`}
                      >
                        {/* Avatar */}
                        {isAgentReply ? (
                          <div
                            className="w-7 h-7 rounded-full flex items-center justify-center text-[10px] font-bold text-[#1c1c1e] flex-shrink-0 shadow-sm border bg-[#EBDCFF] border-transparent"
                          >
                            ME
                          </div>
                        ) : (
                          <div
                            className={`w-7 h-7 rounded-full flex items-center justify-center text-[13px] flex-shrink-0 shadow-sm border ${
                              c("bg-white border-black/5 text-[#1c1c1e]", "bg-[#1f1f23] border-white/5 text-white")
                            }`}
                          >
                            <span className="material-symbols-outlined text-[16px]" aria-hidden="true">person</span>
                          </div>
                        )}

                        {/* Bubble */}
                        <div className="flex flex-col">
                          <div
                            className={`px-4 py-3.5 rounded-2xl text-[13px] leading-relaxed shadow-sm border ${
                              isAgentReply
                                ? c(
                                    "bg-[#1c1c1e] text-[#F5F5F7] font-semibold border-transparent rounded-br-none",
                                    "bg-[#EBDCFF] text-[#1c1c1e] font-semibold border-transparent rounded-br-none"
                                  )
                                : c(
                                    "bg-white border-black/5 text-[#1c1c1e] font-medium rounded-bl-none",
                                    "bg-[#1f1f23] border-white/[0.04] text-[#e4e1e7] font-medium rounded-bl-none"
                                  )
                            }`}
                          >
                            {isAgentReply ? (
                              <MarkdownRenderer content={msg.content} isDark={isDark} />
                            ) : (
                              <div style={{ whiteSpace: "pre-line" }}>{msg.content}</div>
                            )}
                          </div>
                          <span
                            className={`text-[9px] mt-1 font-semibold tracking-wider ${
                              isAgentReply ? "text-right" : "text-left"
                            } ${c("text-black/30", "text-white/30")}`}
                          >
                            {formatTime(msg.created_at)}
                          </span>
                        </div>
                      </div>
                    );
                  })}
                  <div ref={messagesEndRef} />
                </div>

                {/* Input Text Box area */}
                <div
                  className={`p-4 border-t flex flex-col gap-3 flex-shrink-0 transition-colors z-20 ${
                    c("bg-white border-black/5", "bg-[#17171a] border-white/[0.06]")
                  }`}
                >
                  <form onSubmit={handleSendReply} className="flex items-center gap-3">
                    <div
                      className={`flex-1 flex items-center gap-3 border px-4 py-3 rounded-2xl transition-all shadow-inner focus-within:ring-2 focus-within:ring-purple-500/40 focus-within:border-purple-500 ${
                        isDark ? "bg-[#131317] border-white/[0.06]" : "bg-[#F5F5F7] border-black/10"
                      }`}
                    >
                      <input
                        type="text"
                        name="reply"
                        autoComplete="off"
                        value={replyText}
                        onChange={(e) => setReplyText(e.target.value)}
                        placeholder="Write a message response…"
                        aria-label="Write a message response"
                        disabled={sending}
                        className={`flex-1 bg-transparent text-[13.5px] font-medium outline-none ${
                          isDark ? "text-white placeholder:text-white/20" : "text-[#1c1c1e] placeholder:text-black/30"
                        }`}
                      />
                    </div>
                    <button
                      type="submit"
                      disabled={!replyText.trim() || sending}
                      aria-label="Send message response"
                      className={`w-11 h-11 rounded-2xl flex items-center justify-center transition-colors shadow-sm disabled:opacity-40 disabled:cursor-not-allowed focus-visible:ring-2 focus-visible:ring-purple-500 focus-visible:outline-none ${
                        isDark
                          ? "bg-[#EBDCFF] hover:bg-[#d8bfff] text-[#1c1c1e]"
                          : "bg-[#1c1c1e] hover:bg-black text-[#F5F5F7]"
                      }`}
                    >
                      <span className="material-symbols-outlined text-[20px] translate-x-[2px] -translate-y-[0.5px]" aria-hidden="true">
                        send
                      </span>
                    </button>
                  </form>
                </div>
              </div>

              {/* Mobile details drawer backdrop overlay */}
              {isDetailsOpen && (
                <div
                  onClick={() => setIsDetailsOpen(false)}
                  className="lg:hidden fixed inset-0 bg-black/40 backdrop-blur-sm z-30 transition-opacity"
                />
              )}

              {/* Right Column: Chat Metadata & Quick Answers (Drawer on mobile/tablet, static sidebar on desktop) */}
              <div
                className={`fixed lg:static top-0 right-0 h-full lg:h-auto w-full sm:w-80 lg:w-80 flex flex-col flex-shrink-0 overflow-y-auto custom-scrollbar transition-all duration-300 z-40 border-l ${
                  isDetailsOpen ? "translate-x-0" : "translate-x-full lg:translate-x-0"
                } ${c("bg-white border-black/5", "bg-[#17171a] border-white/[0.06]")}`}
              >
                {/* Details Section */}
                <div className="p-6 border-b border-white/[0.04]">
                  {/* Drawer Header Close Button (Mobile Only) */}
                  <div className="flex items-center justify-between mb-4 lg:hidden">
                    <h3
                      className={`text-[16px] font-serif font-bold ${c("text-[#1c1c1e]", "text-white")}`}
                      style={{ fontFamily: "'Playfair Display', serif", textWrap: "balance" }}
                    >
                      Takeover Details
                    </h3>
                    <button
                      onClick={() => setIsDetailsOpen(false)}
                      aria-label="Close details panel"
                      className={`w-8 h-8 rounded-full flex items-center justify-center border hover:bg-black/5 focus-visible:ring-2 focus-visible:ring-purple-500 focus-visible:outline-none ${
                        c("border-black/5 text-[#1c1c1e]", "border-white/10 text-white")
                      }`}
                    >
                      <span className="material-symbols-outlined text-[18px]" aria-hidden="true">close</span>
                    </button>
                  </div>

                  <h3
                    className={`hidden lg:block text-[16px] font-serif font-bold mb-4 ${c("text-[#1c1c1e]", "text-white")}`}
                    style={{ fontFamily: "'Playfair Display', serif", textWrap: "balance" }}
                  >
                    Takeover Details
                  </h3>
                  <div className="space-y-4">
                    <div>
                      <span className={`text-[10px] font-bold uppercase tracking-widest ${c("text-black/40", "text-white/30")}`}>
                        Session ID
                      </span>
                      <p className="font-mono text-[12px] font-bold select-all break-all mt-0.5">
                        {activeChat.id}
                      </p>
                    </div>
                    <div>
                      <span className={`text-[10px] font-bold uppercase tracking-widest ${c("text-black/40", "text-white/30")}`}>
                        Started On
                      </span>
                      <p className="text-[13px] font-bold mt-0.5">
                        {new Date(activeChat.started_at).toLocaleString()}
                      </p>
                    </div>
                    <div>
                      <span className={`text-[10px] font-bold uppercase tracking-widest ${c("text-black/40", "text-white/30")}`}>
                        Assigned Agent
                      </span>
                      <p className="text-[13px] font-bold mt-0.5 text-emerald-500 flex items-center gap-1.5">
                        <span className="material-symbols-outlined text-[16px]" aria-hidden="true">lock_open</span>
                        You (Least-Busy Route)
                      </p>
                    </div>
                  </div>
                </div>

                {/* Canned responses templates list */}
                <div className="p-6">
                  <h3
                    className={`text-[16px] font-serif font-bold mb-4 ${c("text-[#1c1c1e]", "text-white")}`}
                    style={{ fontFamily: "'Playfair Display', serif", textWrap: "balance" }}
                  >
                    Canned Replies
                  </h3>
                  <div className="space-y-3">
                    {CANNED_RESPONSES.map((res) => (
                      <button
                        key={res.label}
                        onClick={() => {
                          setReplyText(res.text);
                          setIsDetailsOpen(false);
                        }}
                        className={`w-full text-left p-3.5 rounded-xl border text-[12px] font-semibold transition-all focus-visible:ring-2 focus-visible:ring-purple-500 focus-visible:outline-none ${
                          isDark
                            ? "bg-[#1f1f23] border-white/[0.04] text-white/70 hover:border-white/10 hover:text-white"
                            : "bg-[#F5F5F7] border-black/5 text-[#1c1c1e]/70 hover:border-black/20 hover:text-[#1c1c1e]"
                        }`}
                      >
                        <p className={`font-bold mb-1 ${c("text-violet-700", "text-[#EBDCFF]")}`}>{res.label}</p>
                        <p className="line-clamp-2 leading-relaxed opacity-85">{res.text}</p>
                      </button>
                    ))}
                  </div>
                </div>

              </div>
            </div>
          ) : (
            /* Empty State */
            <div className="flex-1 hidden md:flex flex-col items-center justify-center p-8 text-center relative select-none">
              <div
                className={`w-20 h-20 rounded-3xl flex items-center justify-center mb-6 shadow-md border ${
                  isDark ? "bg-[#1f1f23] border-white/[0.06] text-white/30" : "bg-white border-black/5 text-black/20"
                }`}
              >
                <span className="material-symbols-outlined text-[40px]" aria-hidden="true">forum</span>
              </div>
              <h2
                className={`text-2xl font-serif font-bold mb-2 ${c("text-[#1c1c1e]", "text-white")}`}
                style={{ fontFamily: "'Playfair Display', serif", textWrap: "balance" }}
              >
                No Selected Session
              </h2>
              <p className={`text-[14px] max-w-sm font-medium ${c("text-black/50", "text-white/40")}`}>
                Select an escalated chat session from the sidebar to take over bot communication in real time.
              </p>
            </div>
          )}

    </div>
  );
}
