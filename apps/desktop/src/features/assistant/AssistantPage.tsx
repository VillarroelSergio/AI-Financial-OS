import { AlertCircle } from "lucide-react";
import { useLocation } from "react-router-dom";
import { useAiAssistant } from "./hooks/useAiAssistant";
import { useAiConversation } from "./hooks/useAiConversation";
import AiMessageList from "./components/AiMessageList";
import AiMessageInput from "./components/AiMessageInput";
import AiStatusBadge from "./components/AiStatusBadge";
import AiConversationSidebar from "./components/AiConversationSidebar";

export default function AssistantPage() {
  const location = useLocation();
  const state = location.state as { prompt?: string; context?: Record<string, unknown> } | null;
  const { status, loading: statusLoading, defaultProvider } = useAiAssistant();
  const {
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
  } = useAiConversation();

  const isAvailable = !!defaultProvider?.available;
  const inputDisabled = sending || !isAvailable;
  const context = state?.context;
  const prompt = state?.prompt;

  return (
    <div className="flex h-full gap-4 p-4">
      <AiConversationSidebar
        conversations={conversations}
        activeId={activeConversationId}
        onSelect={loadConversation}
        onNew={startNewConversation}
        onDelete={removeConversation}
        onLoad={loadConversations}
      />

      <div className="premium-card rounded-lg flex-1 flex flex-col min-w-0 overflow-hidden">
        <div className="flex items-center justify-between px-5 py-4 border-b border-hairline-dark flex-shrink-0">
          <div>
            <h1 className="text-heading-sm text-on-dark">Asistente IA</h1>
            <p className="text-caption text-stone">Copiloto financiero contextual - Sin SQL - Sin Internet</p>
          </div>
          <AiStatusBadge provider={defaultProvider} loading={statusLoading} />
        </div>

        {!statusLoading && !isAvailable && (
          <div className="mx-4 mt-3 flex items-start gap-2 rounded-lg bg-white/[.04] border border-hairline-dark p-3">
            <AlertCircle size={14} className="text-accent-warning flex-shrink-0 mt-0.5" />
            <div className="text-caption">
              <p className="text-on-dark font-medium">Proveedor no disponible</p>
              <p className="text-stone mt-0.5">
                {defaultProvider?.error ??
                  `Arranca Ollama con: ollama serve && ollama pull ${status?.default_model ?? "qwen3-coder:30b"}`}
              </p>
            </div>
          </div>
        )}

        {error && (
          <div className="mx-4 mt-3 flex items-center gap-2 rounded-lg bg-accent-danger/10 border border-accent-danger/30 px-3 py-2">
            <AlertCircle size={12} className="text-accent-danger flex-shrink-0" />
            <p className="text-caption text-accent-danger">{error}</p>
          </div>
        )}

        {context && prompt && (
          <div className="mx-4 mt-3 rounded-lg border border-primary/20 bg-primary/5 p-3">
            <p className="text-caption font-medium text-on-dark">Contexto recibido: {String(context.module ?? "Modulo")}</p>
            <div className="mt-2 flex items-center justify-between gap-3">
              <p className="text-caption text-stone">{prompt}</p>
              <button onClick={() => send(prompt, context)} disabled={inputDisabled} className="rounded-lg bg-primary px-3 py-2 text-xs font-medium text-white disabled:opacity-50">Preguntar</button>
            </div>
          </div>
        )}

        <AiMessageList messages={messages} sending={sending} />

        <AiMessageInput
          onSend={(text) => send(text, context)}
          disabled={inputDisabled}
          placeholder={
            isAvailable
              ? "Pregunta sobre tu patrimonio, gastos o mercados..."
              : "Proveedor offline - arranca Ollama o LM Studio"
          }
        />
      </div>
    </div>
  );
}
