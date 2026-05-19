export interface KnowledgeItem {
  id: string;
  type: "file" | "text" | "website" | "email" | "phone" | "app";
  label: string;
  value: string;
  status: "indexed" | "processing" | "queued";
}

export interface ChatMessage {
  role: "user" | "bot";
  text: string;
}
