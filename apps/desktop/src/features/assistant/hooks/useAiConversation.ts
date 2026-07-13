import { useCallback, useRef, useState } from "react";
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
  structured?: AiChatResponse["structured"];
  quality_score?: number;
  created_at: string;
}

export function useAiConversation() {
  const [conversations, setConversations] = useState<AiConversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<LocalMessage[]>([]);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // Controlador de la petición en vuelo, para poder cancelarla desde el botón Detener.
  const controllerRef = useRef<AbortController | null>(null);
  const userCancelledRef = useRef(false);

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
            structured: m.structured,
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
      // Must exceed the backend provider timeout (120s) so we don't cancel a
      // request the server is still legitimately working on.
      const controller = new AbortController();
      controllerRef.current = controller;
      userCancelledRef.current = false;
      const timeoutId = setTimeout(() => controller.abort(), 130_000);

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
          structured: response.structured,
          quality_score: response.quality_score,
          created_at: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, assistantMsg]);
      } catch (e) {
        if (e instanceof Error && e.name === "AbortError") {
          // Cancelación del usuario: sin error; timeout: aviso de provider lento.
          if (!userCancelledRef.current) {
            setError(
              "La respuesta tardó demasiado. Comprueba que el provider de IA está activo y el modelo está cargado.",
            );
          }
        } else {
          setError(e instanceof Error ? e.message : "Error al enviar mensaje");
        }
        setMessages((prev) => prev.filter((m) => m.id !== userMsg.id));
      } finally {
        clearTimeout(timeoutId);
        controllerRef.current = null;
        setSending(false); // always clear loading state
      }
    },
    [activeConversationId, sending, loadConversations]
  );

  const cancel = useCallback(() => {
    userCancelledRef.current = true;
    controllerRef.current?.abort();
  }, []);

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
    cancel,
    removeConversation,
  };
}
