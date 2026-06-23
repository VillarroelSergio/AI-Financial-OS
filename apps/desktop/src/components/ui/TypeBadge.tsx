const TYPE_STYLES: Record<string, string> = {
  income: "bg-accent-teal/10 text-accent-teal",
  expense: "bg-accent-danger/10 text-accent-danger",
  transfer: "bg-primary/10 text-primary",
  investment: "bg-accent-warning/10 text-accent-warning",
};

const TYPE_LABELS: Record<string, string> = {
  income: "Ingreso",
  expense: "Gasto",
  transfer: "Transferencia",
  investment: "Inversión",
};

export default function TypeBadge({ type }: { type: string }) {
  return (
    <span
      className={`inline-block rounded-sm px-xs py-[2px] text-caption font-medium ${
        TYPE_STYLES[type] ?? "bg-surface-elevated text-stone"
      }`}
    >
      {TYPE_LABELS[type] ?? type}
    </span>
  );
}
