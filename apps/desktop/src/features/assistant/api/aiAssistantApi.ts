import { api } from "@/lib/api/client";
import type {
  AiBrief,
  AiChatRequest,
  AiChatResponse,
  AiConversation,
  AiStatus,
  AiTool,
} from "../types/aiAssistant.types";

export const getAiStatus = () => api.get<AiStatus>("/api/ai/status");

export const getAiTools = () => api.get<AiTool[]>("/api/ai/tools");

export const sendMessage = (payload: AiChatRequest, signal?: AbortSignal) =>
  api.post<AiChatResponse>("/api/ai/chat", payload, signal);

export const createConversation = (title?: string) =>
  api.post<AiConversation>("/api/ai/conversations", { title });

export const listConversations = () =>
  api.get<AiConversation[]>("/api/ai/conversations");

export const getConversation = (id: string) =>
  api.get<AiConversation>(`/api/ai/conversations/${id}`);

export const deleteConversation = (id: string) =>
  api.delete<void>(`/api/ai/conversations/${id}`);

// AI-3: Centro de Análisis
export const listBriefs = () => api.get<AiBrief[]>("/api/ai/briefs");

export const generateBrief = (scope = "monthly_review", period?: string) =>
  api.post<AiBrief>("/api/ai/briefs", { scope, period });
