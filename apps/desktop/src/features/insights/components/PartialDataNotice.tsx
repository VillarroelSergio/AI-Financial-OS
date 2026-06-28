import { AlertTriangle } from "lucide-react";

export function PartialDataNotice() {
  return (
    <div className="flex items-start gap-3 rounded-xl border border-amber-400/20 bg-amber-400/5 px-4 py-3">
      <AlertTriangle size={16} className="mt-0.5 shrink-0 text-amber-300" />
      <p className="text-sm text-stone">
        Algunos insights pueden estar incompletos porque faltan datos de ciertos periodos o fuentes.
      </p>
    </div>
  );
}
