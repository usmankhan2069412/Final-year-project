const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

// Intercept window.fetch to automatically handle 401 Unauthorized status codes
const originalFetch = window.fetch;
window.fetch = async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
  const response = await originalFetch(input, init);

  if (response.status === 401) {
    const url = typeof input === "string"
      ? input
      : input instanceof URL
        ? input.toString()
        : (input as Request).url;

    const isBackendApi = url.includes("/api/");
    const isAuthRequest = url.includes("/api/v1/auth/login") ||
                          url.includes("/api/v1/auth/signup") ||
                          url.includes("/api/v1/auth/google-login") ||
                          url.includes("/api/v1/auth/reset-password");

    if (isBackendApi && !isAuthRequest) {
      window.dispatchEvent(new Event("unauthorized"));
    }
  }

  return response;
};


export type SourceType = "file" | "text" | "website" | "email" | "phone" | "app";
export type SourceStatus = "queued" | "processing" | "indexed" | "failed";
export type ChatbotStatus = "draft" | "training" | "active" | "paused" | "archived";
export type Channel = "web" | "whatsapp";

export interface PersonaResponse {
  id: string;
  org_id: string | null;
  name: string;
  language: string;
  greeting: string | null;
  fallback: string | null;
  description: string | null;
  traits: Array<{ id: string; persona_id: string; trait_name: string }>;
}

export interface ChatbotResponse {
  id: string;
  org_id: string;
  persona_id: string;
  name: string;
  description: string | null;
  status: ChatbotStatus;
  total_conversations: number;
  total_messages: number;
  persona?: PersonaResponse | null;
}

export interface KnowledgeSourceResponse {
  id: string;
  chatbot_id: string;
  source_type: SourceType;
  label: string;
  value: string;
  status: SourceStatus;
  error_message?: string | null;
  is_searchable: boolean;
  pages_crawled?: number | null;
  total_content_chars?: number | null;
  crawl_duration_secs?: number | null;
  created_at: string;
  updated_at: string;
}

export interface DeploymentResponse {
  id: string;
  chatbot_id: string;
  channel: Channel;
  is_active: boolean;
  whatsapp_phone_number_id?: string | null;
  whatsapp_business_account_id?: string | null;
  webhook_verified_at?: string | null;
  created_at?: string | null;
}

export interface ChatResponse {
  response: string;
  conversation_id: string;
  status: "ongoing" | "resolved" | "escalated";
  sources: Array<{ chunk_id: string; source_id: string; text: string; score: number }>;
}

export interface RoutingRule {
  id?: string;
  config_id?: string;
  intent: string;
  model_override?: string | null;
}

export interface AIProvider {
  id: string;
  name: string;
}

export interface AIModelConfig {
  id: string;
  org_id: string;
  provider_id: string;
  model_name: string;
  display_name?: string | null;
  secret_ref: string | null;
  provider: AIProvider;
  routing_rules: RoutingRule[];
}

export interface AvailableProviderModels {
  id: string;
  name: string;
  models: string[];
}

class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

function authHeaders(json = true): HeadersInit {
  const token = localStorage.getItem("token");
  const headers: Record<string, string> = {};
  if (json) headers["Content-Type"] = "application/json";
  if (token) headers.Authorization = `Bearer ${token}`;
  return headers;
}

async function parseResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let message = response.statusText || "Request failed";
    try {
      const data = await response.json();
      message = data.detail || message;
    } catch {
      // Keep status text.
    }
    throw new ApiError(message, response.status);
  }
  if (response.status === 204) return undefined as T;
  return response.json();
}

export async function apiRequest<T = any>(path: string, init?: RequestInit): Promise<T>;
export async function apiRequest<T = any>(method: string, path: string, body?: unknown): Promise<T>;
export async function apiRequest<T = any>(
  pathOrMethod: string,
  initOrPath: RequestInit | string = {},
  body?: unknown
): Promise<T> {
  const isLegacySignature = typeof initOrPath === "string";
  const path = isLegacySignature
    ? initOrPath.startsWith("/api/")
      ? initOrPath
      : `/api/v1${initOrPath}`
    : pathOrMethod;
  const init: RequestInit = isLegacySignature
    ? {
        method: pathOrMethod,
        body: body === undefined ? undefined : JSON.stringify(body),
      }
    : initOrPath;

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      ...authHeaders(init.body instanceof FormData ? false : true),
      ...(init.headers || {}),
    },
  });
  return parseResponse<T>(response);
}

export const api = {
  baseUrl: API_BASE_URL,

  me: () => apiRequest("/api/v1/users/me"),

  createPersona: (payload: {
    name: string;
    language: string;
    greeting?: string | null;
    fallback?: string | null;
    description?: string | null;
    traits: string[];
  }) => apiRequest<PersonaResponse>("/api/v1/personas", { method: "POST", body: JSON.stringify(payload) }),

  updatePersona: (id: string, payload: Partial<{
    name: string;
    language: string;
    greeting: string | null;
    fallback: string | null;
    description: string | null;
    traits: string[];
  }>) => apiRequest<PersonaResponse>(`/api/v1/personas/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),

  createChatbot: (payload: { persona_id: string; name: string; description?: string | null; status?: ChatbotStatus }) =>
    apiRequest<ChatbotResponse>("/api/v1/chatbots", { method: "POST", body: JSON.stringify(payload) }),

  getChatbot: (id: string) => apiRequest<ChatbotResponse>(`/api/v1/chatbots/${id}`),

  updateChatbot: (id: string, payload: Partial<{ persona_id: string; name: string; description: string | null; status: ChatbotStatus }>) =>
    apiRequest<ChatbotResponse>(`/api/v1/chatbots/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),

  deleteChatbot: (id: string) => apiRequest<void>(`/api/v1/chatbots/${id}`, { method: "DELETE" }),

  listKnowledge: (chatbotId: string) => apiRequest<KnowledgeSourceResponse[]>(`/api/v1/knowledge/chatbots/${chatbotId}`),

  createKnowledge: (payload: { chatbot_id: string; source_type: Exclude<SourceType, "file">; label: string; value: string }) =>
    apiRequest<KnowledgeSourceResponse>("/api/v1/knowledge", { method: "POST", body: JSON.stringify(payload) }),

  validateWebsiteUrl: (payload: { url: string }) =>
    apiRequest<{ status: string; links_found: number }>("/api/v1/knowledge/validate-url", { method: "POST", body: JSON.stringify(payload) }),


  uploadKnowledgeFile: (chatbotId: string, file: File) => {
    const data = new FormData();
    data.append("file", file);
    return apiRequest<KnowledgeSourceResponse>(`/api/v1/knowledge/upload?chatbot_id=${chatbotId}`, {
      method: "POST",
      body: data,
    });
  },

  deleteKnowledge: (sourceId: string) => apiRequest<void>(`/api/v1/knowledge/${sourceId}`, { method: "DELETE" }),

  sendBuilderMessage: (chatbotId: string, payload: { message: string; conversation_id?: string | null }) =>
    apiRequest<ChatResponse>(`/api/v1/chat/${chatbotId}/message`, { method: "POST", body: JSON.stringify(payload) }),

  streamBuilderMessage: async (
    chatbotId: string,
    payload: { message: string; conversation_id?: string | null },
    onToken: (token: string) => void,
    onError?: (error: string) => void,
    signal?: AbortSignal
  ): Promise<ChatResponse> => {
    const response = await fetch(`${API_BASE_URL}/api/v1/chat/${chatbotId}/message?stream=true`, {
      method: "POST",
      headers: { ...authHeaders(true) } as HeadersInit,
      body: JSON.stringify(payload),
      signal,
    });

    if (!response.ok) {
      let message = response.statusText;
      try {
        const data = await response.json();
        message = data.detail || message;
      } catch {}
      if (onError) onError(message);
      throw new ApiError(message, response.status);
    }

    if (!response.body) throw new Error("No response body");

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let done = false;
    let finalData: ChatResponse | null = null;
    let buffer = "";
    const processLine = (line: string) => {
      const trimmed = line.trim();
      if (!trimmed.startsWith("data: ")) return;

      const dataStr = trimmed.slice(6);
      if (dataStr === "[DONE]") return;

      let parsed;
      try {
        parsed = JSON.parse(dataStr);
      } catch (e) {
        console.error("Error parsing SSE data", e, dataStr);
        return;
      }

      if (parsed.type === "token") {
        onToken(parsed.content);
      } else if (parsed.type === "final") {
        finalData = parsed.data;
      } else if (parsed.type === "error") {
        if (onError) onError(parsed.error);
        throw new Error(parsed.error);
      }
    };

    while (!done) {
      const { value, done: doneReading } = await reader.read();
      done = doneReading;
      if (value) {
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";
        lines.forEach(processLine);
      }
    }
    buffer += decoder.decode();
    if (buffer.trim()) {
      buffer.split("\n").forEach(processLine);
    }
    if (finalData) return finalData;
    throw new Error("Stream closed without final data");
  },

  listDeployments: (chatbotId: string) => apiRequest<DeploymentResponse[]>(`/api/v1/deployments/${chatbotId}`),

  createDeployment: (payload: { chatbot_id: string; channel: Channel; whatsapp_phone_number_id?: string | null; whatsapp_business_account_id?: string | null }) =>
    apiRequest<DeploymentResponse>("/api/v1/deployments", { method: "POST", body: JSON.stringify(payload) }),

  activateDeployment: (deploymentId: string) =>
    apiRequest<DeploymentResponse>(`/api/v1/deployments/${deploymentId}/activate`, { method: "PATCH" }),

  // --- Model Configuration ---
  getProviders: () => apiRequest<Array<{ id: string; name: string }>>("/api/v1/models/providers"),

  getConfigs: () =>
    apiRequest<Array<{
      id: string;
      org_id: string;
      provider_id: string;
      model_name: string;
      display_name: string | null;
      secret_ref: string | null;
      is_active: boolean;
      is_default: boolean;
      provider: { id: string; name: string };
      routing_rules: Array<{
        id: string;
        config_id: string;
        org_id: string;
        intent: string;
        model_override: string | null;
        priority: number;
        is_active: boolean;
        fallback_config_id: string | null;
        chatbot_id: string | null;
      }>;
    }>>("/api/v1/models/configs"),

  createConfig: (payload: {
    provider_id: string;
    model_name: string;
    display_name?: string | null;
    routing_rules?: Array<{ intent: string; model_override?: string | null }>;
  }) => apiRequest<any>("/api/v1/models/configs", { method: "POST", body: JSON.stringify(payload) }),

  updateConfig: (id: string, payload: {
    provider_id?: string;
    model_name?: string;
    display_name?: string | null;
    routing_rules?: Array<{ intent: string; model_override?: string | null }>;
  }) => apiRequest<any>(`/api/v1/models/configs/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),

  getAvailableModels: () => apiRequest<Array<{ id: string; name: string; models: string[] }>>("/api/v1/models/available"),

  streamConversationEvents: async (
    chatbotId: string,
    conversationId: string,
    onMessage: (message: any) => void,
    onResolve: () => void,
    signal: AbortSignal
  ) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/chat/${chatbotId}/conversations/${conversationId}/stream`, {
        headers: { ...authHeaders(false) } as HeadersInit,
        signal,
      });

      if (!response.ok) throw new Error("Stream connection failed");
      if (!response.body) return;

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let currentEvent = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        if (value) {
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";
          
          for (const line of lines) {
            const trimmed = line.trim();
            if (trimmed.startsWith("event: ")) {
              currentEvent = trimmed.slice(7);
            } else if (trimmed.startsWith("data: ")) {
              const dataStr = trimmed.slice(6);
              if (dataStr === "[DONE]") continue;
              try {
                const parsed = JSON.parse(dataStr);
                if (currentEvent === "message" && parsed.message) {
                  onMessage(parsed.message);
                } else if (currentEvent === "resolve") {
                  onResolve();
                }
              } catch (e) {
                console.error("Error parsing stream data", e, dataStr);
              }
            }
          }
        }
      }
    } catch (e: any) {
      if (e.name !== "AbortError") {
        console.error("Conversation stream error:", e);
      }
    }
  },
};
