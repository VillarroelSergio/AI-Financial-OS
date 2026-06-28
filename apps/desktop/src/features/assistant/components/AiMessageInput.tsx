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
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
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
    <div className="flex items-end gap-2 border-t border-hairline-dark p-3 bg-surface">
      <textarea
        ref={textareaRef}
        value={text}
        onChange={handleInput}
        onKeyDown={handleKey}
        disabled={disabled}
        rows={1}
        placeholder={placeholder ?? "Escribe tu pregunta…"}
        className="flex-1 resize-none rounded-lg bg-surface-elevated border border-hairline-dark px-3 py-2 text-body-sm text-on-dark placeholder:text-mute focus:outline-none focus:border-primary-500 disabled:opacity-50 transition-colors"
      />
      <button
        onClick={submit}
        disabled={!text.trim() || disabled}
        className="w-8 h-8 rounded-lg bg-primary-600 hover:bg-primary-500 disabled:bg-surface-elevated disabled:text-mute flex items-center justify-center transition-colors flex-shrink-0"
      >
        <Send size={14} className="text-white disabled:text-mute" />
      </button>
    </div>
  );
}
