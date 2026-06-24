interface Props {
  lastUpdated: string | null;
  isStale?: boolean;
}

function formatCloseDate(isoStr: string | null): string {
  if (!isoStr) return "Sin datos";
  try {
    const d = new Date(isoStr);
    return d.toLocaleDateString("es-ES", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
    });
  } catch {
    return "Sin datos";
  }
}

export default function EodBadge({ lastUpdated, isStale = false }: Props) {
  const dateStr = formatCloseDate(lastUpdated);
  return (
    <div
      className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-hairline-dark bg-surface-elevated"
      role="status"
      aria-label={isStale ? "Datos desactualizados" : `Datos de cierre del ${dateStr}`}
    >
      <span
        className={`inline-block w-2 h-2 rounded-full flex-shrink-0 ${
          isStale ? "bg-accent-warning" : "bg-stone"
        }`}
        aria-hidden="true"
      />
      <span
        className={`text-caption font-medium ${
          isStale ? "text-accent-warning" : "text-stone"
        }`}
      >
        {isStale ? "Datos desactualizados" : `Cierre ${dateStr}`}
      </span>
    </div>
  );
}
