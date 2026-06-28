import { useEffect } from "react";
import { Plus, Trash2, MessageSquare } from "lucide-react";
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
  useEffect(() => { onLoad(); }, [onLoad]);

  return (
    <div className="w-56 flex-shrink-0 border-r border-hairline-dark flex flex-col bg-surface">
      <div className="p-3 border-b border-hairline-dark">
        <button
          onClick={onNew}
          className="w-full flex items-center gap-2 text-body-sm text-on-dark hover:text-primary-400 transition-colors py-1.5 px-2 rounded-lg hover:bg-surface-elevated"
        >
          <Plus size={14} />
          Nueva conversación
        </button>
      </div>
      <div className="flex-1 overflow-y-auto py-2">
        {conversations.length === 0 ? (
          <p className="text-caption text-mute px-3 py-4 text-center">Sin conversaciones</p>
        ) : (
          conversations.map((conv) => (
            <div
              key={conv.id}
              className={`group flex items-center gap-2 px-3 py-2 cursor-pointer rounded-lg mx-1 transition-colors ${
                activeId === conv.id
                  ? "bg-surface-elevated text-on-dark"
                  : "text-stone hover:bg-surface-elevated hover:text-on-dark"
              }`}
              onClick={() => onSelect(conv.id)}
            >
              <MessageSquare size={12} className="flex-shrink-0" />
              <span className="text-caption truncate flex-1">
                {conv.title ?? "Conversación"}
              </span>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onDelete(conv.id);
                }}
                className="opacity-0 group-hover:opacity-100 hover:text-red-400 transition-all flex-shrink-0"
              >
                <Trash2 size={11} />
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
