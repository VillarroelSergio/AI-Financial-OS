export interface AiToolCall {
  name: string;
  arguments?: Record<string, unknown>;
  result?: Record<string, unknown>;
  duration_ms?: number;
  status: "ok" | "error" | "not_available";
}

export interface AiSource {
  type: string;
  provider?: string;
  observed_at?: string;
  quality_score?: number;
}

export interface AiMessage {
  id: string;
  role: "user" | "assistant" | "system" | "tool";
  content: string | null;
  tool_calls?: AiToolCall[];
  sources?: AiSource[];
  quality_score?: number;
  created_at: string;
}

export interface AiConversation {
  id: string;
  title?: string;
  summary?: string;
  created_at: string;
  updated_at: string;
  messages?: AiMessage[];
}

export interface AiChatRequest {
  message: string;
  conversation_id?: string;
  provider?: string;
  model?: string;
  enable_tools?: boolean;
}

export interface AiChatResponse {
  conversation_id: string;
  message_id: string;
  content: string | null;
  tool_calls: AiToolCall[];
  sources: AiSource[];
  quality_score?: number;
  provider?: string;
  model?: string;
}

export interface AiProviderStatus {
  name: string;
  available: boolean;
  model?: string;
  error?: string;
  latency_ms?: number;
}

export interface AiStatus {
  enabled: boolean;
  default_provider: string;
  default_model: string;
  providers: AiProviderStatus[];
}

export interface AiTool {
  name: string;
  description: string;
  source_type: string;
  returns_sources: boolean;
}
