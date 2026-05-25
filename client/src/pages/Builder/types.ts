export interface KnowledgeItem {
  id: string;
  type: "file" | "text" | "website" | "email" | "phone" | "app";
  label: string;
  value: string;
  status: "indexed" | "processing" | "queued" | "failed";
  error_message?: string | null;
}

export interface ChatMessage {
  role: "user" | "bot";
  text: string;
}
