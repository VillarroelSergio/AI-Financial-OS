import { useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { Bot, User } from "lucide-react";
import { formatCurrency, formatNumber } from "@/lib/formatters/currency";
import type { LocalMessage } from "../hooks/useAiConversation";
import type { AiStructured, AiStructuredFigure } from "../types/aiAssistant.types";
import AiToolTrace from "./AiToolTrace";
import AiSourceBadge from "./AiSourceBadge";
import Markdown from "./Markdown";

// AI-5: sugerencias del empty-state. Si el usuario llega desde el copiloto de un
// módulo, se pasan las de ese módulo (contextualCopilot); si no, estas genéricas.
const FALLBACK_SUGGESTIONS = [
  "¿Cómo voy este mes?",
  "¿Qué señales macro hay?",
  "¿Cómo está mi cartera?",
];

interface Props {
  messages: LocalMessage[];
  sending: boolean;
  onPickSuggestion?: (text: string) => void;
  suggestions?: string[];
}

function formatFigure(fig: AiStructuredFigure): string {
  if (fig.unit === "EUR") return formatCurrency(fig.value);
  if (fig.unit === "%") return `${fig.value.toFixed(fig.precision ?? 1)} %`;
  return formatNumber(fig.value);
}

// AI-1: cifras y acciones deterministas (de las tools) bajo la respuesta del chat.
function StructuredPanel({ data }: { data: AiStructured }) {
  const navigate = useNavigate();
  return (
    <div className="mt-2 space-y-2">
      {data.key_figures.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {data.key_figures.map((fig) => (
            <div key={fig.label} className="rounded-lg bg-surface-elevated border border-hairline-dark px-3 py-1.5">
              <p className="text-caption text-stone">{fig.label}</p>
              <p className="text-body-sm text-on-dark font-medium">{formatFigure(fig)}</p>
            </div>
          ))}
        </div>
      )}
      {data.actions.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {data.actions.map((act, i) => (
            <button
              key={i}
              onClick={() => navigate(act.target)}
              className="rounded-lg border border-hairline-dark bg-surface-elevated px-3 py-1.5 text-caption text-on-dark hover:border-primary/40"
            >
              {act.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function TypingIndicator() {
  return (
    <div className="flex items-start gap-3">
      <div className="w-7 h-7 rounded-full bg-surface-elevated border border-hairline-dark flex items-center justify-center flex-shrink-0">
        <Bot size={14} className="text-stone" />
      </div>
      <div className="flex gap-1 pt-2">
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            className="w-1.5 h-1.5 rounded-full bg-stone animate-bounce"
            style={{ animationDelay: `${i * 0.15}s` }}
          />
        ))}
      </div>
    </div>
  );
}

export default function AiMessageList({ messages, sending, onPickSuggestion, suggestions }: Props) {
  const starterSuggestions = suggestions?.length ? suggestions : FALLBACK_SUGGESTIONS;
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, sending]);

  if (!messages.length && !sending) {
    return (
      <div className="flex-1 flex items-center justify-center text-center px-8">
        <div className="space-y-2">
          <Bot size={32} className="text-stone mx-auto" />
          <p className="text-body-md text-on-dark">Asistente Financiero Local</p>
          <p className="text-body-sm text-stone max-w-xs">
            Pregunta sobre tu patrimonio, gastos, inversiones o señales de mercado.
          </p>
          <div className="flex flex-wrap gap-2 justify-center mt-4">
            {starterSuggestions.map((s) => (
              <button
                key={s}
                onClick={() => onPickSuggestion?.(s)}
                disabled={!onPickSuggestion}
                className="text-caption px-3 py-1 rounded-full border border-hairline-dark text-stone transition-colors hover:border-primary/40 hover:text-on-dark disabled:cursor-default disabled:hover:border-hairline-dark disabled:hover:text-stone"
              >
                {s}
              </button>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto px-4 py-4 space-y-6">
      {messages.map((msg) => (
        <div key={msg.id} className={`flex items-start gap-3 ${msg.role === "user" ? "flex-row-reverse" : ""}`}>
          <div
            className={`w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 ${
              msg.role === "user"
                ? "bg-primary"
                : "bg-surface-elevated border border-hairline-dark"
            }`}
          >
            {msg.role === "user" ? (
              <User size={14} className="text-white" />
            ) : (
              <Bot size={14} className="text-stone" />
            )}
          </div>
          <div className={`max-w-[80%] ${msg.role === "user" ? "items-end" : "items-start"} flex flex-col`}>
            <div
              className={`rounded-xl px-4 py-3 text-body-sm ${
                msg.role === "user"
                  ? "bg-primary text-on-primary whitespace-pre-wrap"
                  : "bg-surface-elevated border border-hairline-dark text-on-dark"
              }`}
            >
              {msg.content ? (
                msg.role === "assistant" ? (
                  <Markdown content={msg.content} />
                ) : (
                  msg.content
                )
              ) : (
                <span className="text-stone italic">
                  {(msg.tool_calls?.length ?? 0) > 0 ? "Analizando datos…" : "Sin respuesta"}
                </span>
              )}
            </div>
            {msg.role === "assistant" && (
              <>
                {msg.structured && (msg.structured.key_figures.length > 0 || msg.structured.actions.length > 0) && (
                  <StructuredPanel data={msg.structured} />
                )}
                {msg.tool_calls && msg.tool_calls.length > 0 && (
                  <AiToolTrace toolCalls={msg.tool_calls} />
                )}
                {msg.sources && msg.sources.length > 0 && (
                  <AiSourceBadge sources={msg.sources} quality_score={msg.quality_score} />
                )}
              </>
            )}
          </div>
        </div>
      ))}
      {sending && <TypingIndicator />}
      <div ref={bottomRef} />
    </div>
  );
}
