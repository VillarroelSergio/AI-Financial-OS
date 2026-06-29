import { Trash2 } from "lucide-react";
import type { RecurringTransaction } from "@/lib/api/budgets";

const FREQ_LABEL: Record<string, string> = {
  monthly: "Mensual",
  weekly: "Semanal",
  yearly: "Anual",
};

interface Props {
  item: RecurringTransaction;
  onDelete: (id: string) => void;
}

export default function RecurringItem({ item, onDelete }: Props) {
  return (
    <div className="flex items-center justify-between rounded-xl bg-surface-elevated px-4 py-3">
      <div className="flex items-center gap-3">
        <span className={["h-2 w-2 rounded-full shrink-0", item.type === "income" ? "bg-accent-teal" : "bg-accent-danger"].join(" ")} />
        <div>
          <p className="text-sm font-medium text-on-dark">{item.name}</p>
          <p className="text-[11px] text-stone">{FREQ_LABEL[item.frequency]} · próximo {new Date(item.next_date).toLocaleDateString("es-ES")}</p>
        </div>
      </div>
      <div className="flex items-center gap-3">
        <span className={["text-sm font-semibold", item.type === "income" ? "text-accent-teal" : "text-on-dark"].join(" ")}>
          {item.type === "income" ? "+" : "-"}
          {item.amount.toLocaleString("es-ES", { style: "currency", currency: "EUR" })}
        </span>
        <button onClick={() => onDelete(item.id)} className="text-stone hover:text-accent-danger transition-colors">
          <Trash2 size={15} />
        </button>
      </div>
    </div>
  );
}
