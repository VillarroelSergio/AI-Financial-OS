import { useEffect } from "react";
import { MessageSquare, Plus, Trash2 } from "lucide-react";
import type { AiConversation } from "../types/aiAssistant.types";

interface Props {
  conversations: AiConversation[];
  activeId: string | null;
  onSelect: (id: string) => void;
  onNew: () => void;
  onDelete: (id: string) => void;
  onLoad: () => void;
}

export default function AiConversationSidebar({
  conversations,
  activeId,
  onSelect,
  onNew,
  onDelete,
  onLoad,
}: Props) {
  useEffect(() => {
    onLoad();
  }, [onLoad]);

  return (
    <div className="mercury-panel w-64 flex-shrink-0 rounded-lg flex flex-col overflow-hidden">
      <div className="p-3 border-b border-hairline-dark">
        <button
          onClick={onNew}
          className="mercury-button-primary w-full flex items-center justify-center gap-2 text-body-sm transition-colors py-2 px-3 rounded-lg"
        >
          <Plus size={14} />
          Nueva conversacion
        </button>
      </div>
      <div className="flex-1 overflow-y-auto py-2">
        {conversations.length === 0 ? (
          <p className="text-caption text-mute px-3 py-4 text-center">Sin conversaciones</p>
        ) : (
          conversations.map((conv) => (
            <div
              key={conv.id}
              className={`group flex items-center gap-2 px-3 py-2 cursor-pointer rounded-lg mx-2 transition-colors ${
                activeId === conv.id
                  ? "bg-white/[.075] text-on-dark shadow-[inset_0_0_0_1px_rgba(255,255,255,.08)]"
                  : "text-stone hover:bg-white/[.04] hover:text-on-dark"
              }`}
              onClick={() => onSelect(conv.id)}
            >
              <MessageSquare size={13} className="flex-shrink-0" />
              <span className="text-caption truncate flex-1">{conv.title ?? "Conversacion"}</span>
              <button
                aria-label="Eliminar conversacion"
                onClick={(e) => {
                  e.stopPropagation();
                  onDelete(conv.id);
                }}
                className="opacity-0 group-hover:opacity-100 hover:text-accent-danger transition-all flex-shrink-0"
              >
                <Trash2 size={12} />
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
