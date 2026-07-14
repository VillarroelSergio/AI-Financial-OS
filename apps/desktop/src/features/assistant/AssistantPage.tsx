import { useState } from "react";
import { AlertCircle } from "lucide-react";
import { useLocation } from "react-router-dom";
import { useAiAssistant } from "./hooks/useAiAssistant";
import { useAiConversation } from "./hooks/useAiConversation";
import AiMessageList from "./components/AiMessageList";
import AiMessageInput from "./components/AiMessageInput";
import AiStatusBadge from "./components/AiStatusBadge";
import AiConversationSidebar from "./components/AiConversationSidebar";
import AnalysisCenter from "./components/AnalysisCenter";
import { PageHeader } from "@/components/ui/Dashboard";

type Tab = "analisis" | "chat";

export default function AssistantPage() {
  const location = useLocation();
  const state = location.state as { prompt?: string; context?: Record<string, unknown> } | null;
  // Un prompt entrante (botón "Preguntar a la IA") abre directamente el chat.
  const [tab, setTab] = useState<Tab>(state?.prompt ? "chat" : "analisis");
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
    cancel,
    removeConversation,
  } = useAiConversation();

  const isAvailable = !!defaultProvider?.available;
  const inputDisabled = sending || !isAvailable;
  const context = state?.context;
  const prompt = state?.prompt;

  return (
    <div className="page-shell flex h-full min-h-0 flex-col gap-5">
      <PageHeader
        title="Asistente financiero"
        description="Analiza tus datos locales y conversa sobre decisiones concretas, sin compartir información fuera de tu equipo."
        actions={<AiStatusBadge provider={defaultProvider} loading={statusLoading} />}
      />

      <div
        className="flex w-fit flex-shrink-0 items-center gap-1 rounded-[12px] bg-[var(--bg-interactive)] p-1"
        role="tablist"
        aria-label="Modo del asistente"
      >
        {([["analisis", "Análisis"], ["chat", "Chat"]] as const).map(([key, label]) => (
          <button
            key={key}
            type="button"
            role="tab"
            aria-selected={tab === key}
            onClick={() => setTab(key)}
            className={`ui-pressable rounded-[9px] px-3.5 py-2 text-sm font-medium transition-colors ${
              tab === key
                ? "bg-[var(--bg-card)] text-[var(--text-primary)] shadow-[var(--shadow-card)]"
                : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {tab === "analisis" ? (
        <AnalysisCenter onOpenChat={() => setTab("chat")} />
      ) : (
        <div className="flex min-h-0 flex-1 gap-4">
          <AiConversationSidebar
            conversations={conversations}
            activeId={activeConversationId}
            onSelect={loadConversation}
            onNew={startNewConversation}
            onDelete={removeConversation}
            onLoad={loadConversations}
          />

          <div className="premium-card flex min-w-0 flex-1 flex-col overflow-hidden rounded-[16px]">
            <div className="flex items-center justify-between px-5 py-4 border-b border-hairline-dark flex-shrink-0">
              <div>
                <h2 className="text-heading-sm text-on-dark">Conversación</h2>
                <p className="text-caption text-stone">Tus cifras se consultan localmente y se muestran con su contexto.</p>
              </div>
            </div>

            {!statusLoading && !isAvailable && (
              <div className="mx-4 mt-3 flex items-start gap-2 rounded-lg bg-white/[.04] border border-hairline-dark p-3">
                <AlertCircle size={14} className="text-accent-warning flex-shrink-0 mt-0.5" />
                <div className="text-caption">
                  <p className="text-on-dark font-medium">Proveedor no disponible</p>
                  <p className="text-stone mt-0.5">
                    {defaultProvider?.error ??
                      (status?.default_provider === "lmstudio"
                        ? "Arranca LM Studio y carga un modelo en el servidor local (puerto 1234)."
                        : `Arranca Ollama con: ollama serve && ollama pull ${status?.default_model ?? "qwen3-coder:30b"}`)}
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
                  <button onClick={() => send(prompt, context)} disabled={inputDisabled} className="ui-pressable mercury-button-primary px-3 py-2 text-xs">Preguntar</button>
                </div>
              </div>
            )}

            <AiMessageList
              messages={messages}
              sending={sending}
              onPickSuggestion={inputDisabled ? undefined : (text) => send(text, context)}
              suggestions={
                Array.isArray(context?.suggestedQuestions)
                  ? (context.suggestedQuestions as string[])
                  : undefined
              }
            />

            <AiMessageInput
              onSend={(text) => send(text, context)}
              disabled={inputDisabled}
              sending={sending}
              onCancel={cancel}
              placeholder={
                isAvailable
                  ? "Pregunta sobre tu patrimonio, gastos o mercados..."
                  : "Proveedor offline - arranca Ollama o LM Studio"
              }
            />
          </div>
        </div>
      )}
    </div>
  );
}
