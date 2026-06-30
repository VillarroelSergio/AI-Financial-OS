import { useState } from "react";
import { ChevronDown } from "lucide-react";
import type { InsightSource } from "../types/insights.types";

export function InsightSourcesDisclosure({ sources }: { sources: InsightSource[] }) {
  const [open, setOpen] = useState(false);
  if (!sources.length) return null;

  return (
    <div className="mt-3 border-t border-hairline-dark pt-3">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-1.5 text-[11px] text-stone hover:text-on-dark transition-colors"
      >
        <ChevronDown size={12} className={`transition-transform ${open ? "rotate-180" : ""}`} />
        Datos utilizados
      </button>
      {open && (
        <ul className="mt-2 space-y-1.5">
          {sources.map((s, i) => (
            <li key={i} className="flex flex-wrap gap-x-3 text-[11px] text-stone">
              <span className="text-on-dark/70">{s.label}</span>
              {s.period && <span>Periodo: {s.period}</span>}
              {s.updated_at && <span>Actualizado: {new Date(s.updated_at).toLocaleDateString("es-ES")}</span>}
              <span className="capitalize">{s.source.replace("_", " ")}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
