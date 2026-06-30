import { useRef, useState } from "react";
import { Send } from "lucide-react";

interface Props {
  onSend: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

export default function AiMessageInput({ onSend, disabled, placeholder }: Props) {
  const [text, setText] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const submit = () => {
    const trimmed = text.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setText("");
    if (textareaRef.current) textareaRef.current.style.height = "auto";
  };

  const handleKey = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  };

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setText(e.target.value);
    const ta = e.target;
    ta.style.height = "auto";
    ta.style.height = `${Math.min(ta.scrollHeight, 140)}px`;
  };

  return (
    <div className="border-t border-hairline-dark p-3 bg-black/10">
      <div className="flex items-end gap-2 rounded-lg border border-hairline-dark bg-white/[.035] p-2">
        <textarea
          ref={textareaRef}
          value={text}
          onChange={handleInput}
          onKeyDown={handleKey}
          disabled={disabled}
          rows={1}
          placeholder={placeholder ?? "Escribe tu pregunta..."}
          className="flex-1 resize-none bg-transparent px-2 py-2 text-body-sm text-on-dark placeholder:text-mute focus:outline-none disabled:opacity-50"
        />
        <button
          aria-label="Enviar mensaje"
          onClick={submit}
          disabled={!text.trim() || disabled}
          className="grid h-9 w-9 flex-shrink-0 place-items-center rounded-lg bg-primary text-white transition-colors hover:bg-primary-bright disabled:bg-white/[.05] disabled:text-mute"
        >
          <Send size={14} />
        </button>
      </div>
    </div>
  );
}
