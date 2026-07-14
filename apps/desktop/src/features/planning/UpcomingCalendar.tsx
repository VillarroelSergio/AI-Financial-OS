import type { CalendarEvent } from "@/lib/api/budgets";

interface Props {
  events: CalendarEvent[];
}

export default function UpcomingCalendar({ events }: Props) {
  if (events.length === 0) {
    return <p className="py-6 text-center text-sm text-stone">No hay eventos próximos.</p>;
  }

  return (
    <div className="space-y-2">
      {events.slice(0, 10).map((ev, i) => (
        <div key={i} className="flex items-center justify-between rounded-lg px-3 py-2.5 hover:bg-[var(--bg-interactive)] transition-colors">
          <div className="flex items-center gap-3">
            <span className="w-12 text-[11px] text-stone tabular-nums">
              {new Date(ev.date).toLocaleDateString("es-ES", { day: "numeric", month: "short" })}
            </span>
            <span className="text-sm text-on-dark">{ev.name}</span>
          </div>
          <span className={["text-sm font-medium", ev.type === "income" ? "text-accent-teal" : "text-on-dark"].join(" ")}>
            {ev.type === "income" ? "+" : "-"}
            {ev.amount.toLocaleString("es-ES", { style: "currency", currency: "EUR" })}
          </span>
        </div>
      ))}
    </div>
  );
}
