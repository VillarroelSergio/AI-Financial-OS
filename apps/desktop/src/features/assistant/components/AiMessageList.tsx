import { useEffect, useRef } from "react";
import { Bot, User } from "lucide-react";
import type { LocalMessage } from "../hooks/useAiConversation";
import AiToolTrace from "./AiToolTrace";
import AiSourceBadge from "./AiSourceBadge";

interface Props {
  messages: LocalMessage[];
  sending: boolean;
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

export default function AiMessageList({ messages, sending }: Props) {
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
            {[
              "¿Cómo voy este mes?",
              "¿Qué señales macro hay?",
              "¿Cómo está mi cartera?",
            ].map((s) => (
              <span
                key={s}
                className="text-caption px-3 py-1 rounded-full border border-hairline-dark text-stone"
              >
                {s}
              </span>
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
                ? "bg-primary-600"
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
              className={`rounded-xl px-4 py-3 text-body-sm whitespace-pre-wrap ${
                msg.role === "user"
                  ? "bg-primary-600 text-white"
                  : "bg-surface-elevated border border-hairline-dark text-on-dark"
              }`}
            >
              {msg.content ?? (
                <span className="text-stone italic">
                  {(msg.tool_calls?.length ?? 0) > 0 ? "Analizando datos…" : "Sin respuesta"}
                </span>
              )}
            </div>
            {msg.role === "assistant" && (
              <>
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
