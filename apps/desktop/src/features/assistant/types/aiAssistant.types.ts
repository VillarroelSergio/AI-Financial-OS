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
  structured?: AiStructured | null;
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
  context?: Record<string, unknown>;
  provider?: string;
  model?: string;
  enable_tools?: boolean;
}

// AI-1: cifras/acciones deterministas extraídas de las tools (no del texto del LLM).
export interface AiStructuredFigure {
  label: string;
  value: number;
  unit: string; // "EUR" | "%" | ...
  precision?: number;
}

export interface AiStructured {
  key_figures: AiStructuredFigure[];
  actions: AiBriefAction[];
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
  structured?: AiStructured | null;
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

// AI-3: Centro de Análisis (briefs proactivos)
export interface AiKeyFigure {
  label: string;
  value: number;
  unit: string; // "EUR" | "%" | ...
}

export interface AiBriefSignal {
  title: string;
  summary: string;
  severity: string; // positive | info | warning | critical
  type: string;
}

export interface AiBriefAction {
  label: string;
  target: string;
  params: Record<string, unknown>;
}

export interface AiBriefBundle {
  scope: string;
  period: string;
  headline: string;
  summary: string;
  data_state: string;
  key_figures: AiKeyFigure[];
  signals: AiBriefSignal[];
  actions: AiBriefAction[];
  sources: unknown[];
}

export interface AiBrief {
  id: string;
  scope: string;
  period: string;
  bundle: AiBriefBundle;
  narrative: string | null; // null si el LLM falló → renderizar el bundle
  data_state: string;
  provider?: string;
  model?: string;
  created_at?: string;
}
