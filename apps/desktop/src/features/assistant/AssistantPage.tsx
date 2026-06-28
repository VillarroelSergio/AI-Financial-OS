import { AlertCircle } from "lucide-react";
import { useAiAssistant } from "./hooks/useAiAssistant";
import { useAiConversation } from "./hooks/useAiConversation";
import AiMessageList from "./components/AiMessageList";
import AiMessageInput from "./components/AiMessageInput";
import AiStatusBadge from "./components/AiStatusBadge";
import AiConversationSidebar from "./components/AiConversationSidebar";

export default function AssistantPage() {
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

  return (
    <div className="flex h-full">
      <AiConversationSidebar
        conversations={conversations}
        activeId={activeConversationId}
        onSelect={loadConversation}
        onNew={startNewConversation}
        onDelete={removeConversation}
        onLoad={loadConversations}
      />

      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-3 border-b border-hairline-dark flex-shrink-0">
          <div>
            <h1 className="text-label-lg text-on-dark">Asistente IA</h1>
            <p className="text-caption text-stone">Análisis financiero local · Sin SQL · Sin Internet</p>
          </div>
          <AiStatusBadge provider={defaultProvider} loading={statusLoading} />
        </div>

        {/* Provider offline banner */}
        {!statusLoading && !isAvailable && (
          <div className="mx-4 mt-3 flex items-start gap-2 rounded-lg bg-surface-elevated border border-hairline-dark p-3">
            <AlertCircle size={14} className="text-yellow-400 flex-shrink-0 mt-0.5" />
            <div className="text-caption">
              <p className="text-on-dark font-medium">Proveedor no disponible</p>
              <p className="text-stone mt-0.5">
                {defaultProvider?.error ??
                  `Arranca Ollama con: ollama serve && ollama pull ${status?.default_model ?? "qwen3-coder:30b"}`}
              </p>
            </div>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="mx-4 mt-3 flex items-center gap-2 rounded-lg bg-red-500/10 border border-red-500/30 px-3 py-2">
            <AlertCircle size={12} className="text-red-400 flex-shrink-0" />
            <p className="text-caption text-red-400">{error}</p>
          </div>
        )}

        {/* Messages */}
        <AiMessageList messages={messages} sending={sending} />

        {/* Input */}
        <AiMessageInput
          onSend={(text) => send(text)}
          disabled={inputDisabled}
          placeholder={
            isAvailable
              ? "Pregunta sobre tu patrimonio, gastos o mercados…"
              : "Proveedor offline — arranca Ollama o LM Studio"
          }
        />
      </div>
    </div>
  );
}
