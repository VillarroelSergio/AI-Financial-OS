import { useCallback, useState } from "react";
import {
  deleteConversation,
  getConversation,
  listConversations,
  sendMessage,
} from "../api/aiAssistantApi";
import type { AiChatResponse, AiConversation } from "../types/aiAssistant.types";

export interface LocalMessage {
  id: string;
  role: "user" | "assistant";
  content: string | null;
  tool_calls?: AiChatResponse["tool_calls"];
  sources?: AiChatResponse["sources"];
  quality_score?: number;
  created_at: string;
}

export function useAiConversation() {
  const [conversations, setConversations] = useState<AiConversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<LocalMessage[]>([]);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadConversations = useCallback(async () => {
    try {
      const list = await listConversations();
      setConversations(list);
    } catch (e) {
      // Non-fatal
    }
  }, []);

  const loadConversation = useCallback(async (id: string) => {
    try {
      const conv = await getConversation(id);
      setActiveConversationId(id);
      setMessages(
        (conv.messages ?? [])
          .filter((m) => m.role === "user" || m.role === "assistant")
          .map((m) => ({
            id: m.id,
            role: m.role as "user" | "assistant",
            content: m.content,
            tool_calls: m.tool_calls as AiChatResponse["tool_calls"] | undefined,
            sources: m.sources as AiChatResponse["sources"] | undefined,
            quality_score: m.quality_score,
            created_at: m.created_at,
          }))
      );
    } catch (e) {
      setError("Error al cargar la conversación");
    }
  }, []);

  const startNewConversation = useCallback(() => {
    setActiveConversationId(null);
    setMessages([]);
    setError(null);
  }, []);

  const send = useCallback(
    async (
      text: string,
      context?: Record<string, unknown>,
      provider?: string,
      model?: string,
    ) => {
      if (!text.trim() || sending) return;

      const userMsg: LocalMessage = {
        id: `local-${Date.now()}`,
        role: "user",
        content: text,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, userMsg]);
      setSending(true);
      setError(null);

      // Abort controller ensures the loading state is never infinite.
      // 90 seconds is generous for a local LLM but prevents indefinite hangs.
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 90_000);

      try {
        const response = await sendMessage(
          {
            message: text,
            conversation_id: activeConversationId ?? undefined,
            context,
            provider,
            model,
            enable_tools: true,
          },
          controller.signal,
        );

        if (!activeConversationId) {
          setActiveConversationId(response.conversation_id);
          loadConversations();
        }

        const assistantMsg: LocalMessage = {
          id: response.message_id,
          role: "assistant",
          content: response.content,
          tool_calls: response.tool_calls,
          sources: response.sources,
          quality_score: response.quality_score,
          created_at: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, assistantMsg]);
      } catch (e) {
        if (e instanceof Error && e.name === "AbortError") {
          setError(
            "La respuesta tardó demasiado. Comprueba que el provider de IA está activo y el modelo está cargado.",
          );
        } else {
          setError(e instanceof Error ? e.message : "Error al enviar mensaje");
        }
        setMessages((prev) => prev.filter((m) => m.id !== userMsg.id));
      } finally {
        clearTimeout(timeoutId);
        setSending(false); // always clear loading state
      }
    },
    [activeConversationId, sending, loadConversations]
  );

  const removeConversation = useCallback(async (id: string) => {
    try {
      await deleteConversation(id);
      setConversations((prev) => prev.filter((c) => c.id !== id));
      if (activeConversationId === id) {
        startNewConversation();
      }
    } catch (e) {
      setError("Error al eliminar la conversación");
    }
  }, [activeConversationId, startNewConversation]);

  return {
    conversations,
    activeConversationId,
    messages,
    sending,
    error,
    loadConversations,
    loadConversation,
    startNewConversation,
    send,
    removeConversation,
  };
}
