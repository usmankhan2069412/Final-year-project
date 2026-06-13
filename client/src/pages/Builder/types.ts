export interface KnowledgeItem {
  id: string;
  type: "file" | "text" | "website" | "email" | "phone" | "app";
  label: string;
  value: string;
  status: "indexed" | "processing" | "queued" | "failed";
  error_message?: string | null;
  is_searchable?: boolean;
  pages_crawled?: number | null;
  total_content_chars?: number | null;
  crawl_duration_secs?: number | null;
}

export interface ChatMessage {
  id?: string;
  role: "user" | "bot";
  text: string;
}
