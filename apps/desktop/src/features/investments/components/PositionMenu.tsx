import { useEffect, useRef, useState } from "react";
import { MoreHorizontal } from "lucide-react";

export interface MenuItem {
  label: string;
  onClick: () => void;
  danger?: boolean;
}

/** Menú contextual unificado de una posición (Editar / Fusionar / Eliminar / acciones por tipo). */
export default function PositionMenu({ items }: { items: MenuItem[] }) {
  const [open, setOpen] = useState(false);
  // Posición fija anclada al botón: el menú vive dentro de contenedores con
  // overflow (la tabla usa overflow-x-auto, que recorta un dropdown absolute).
  const [coords, setCoords] = useState<{ top: number; right: number } | null>(null);
  const ref = useRef<HTMLDivElement>(null);
  const btnRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!open) return;
    const onDoc = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") setOpen(false); };
    document.addEventListener("mousedown", onDoc);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDoc);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  const toggle = () => {
    if (!open && btnRef.current) {
      const r = btnRef.current.getBoundingClientRect();
      setCoords({ top: r.bottom + 4, right: window.innerWidth - r.right });
    }
    setOpen((v) => !v);
  };

  return (
    <div ref={ref} className="relative">
      <button
        ref={btnRef}
        onClick={toggle}
        aria-label="Acciones"
        aria-haspopup="menu"
        aria-expanded={open}
        className="text-stone hover:text-on-dark p-1 rounded-sm hover:bg-[var(--bg-interactive)]"
      >
        <MoreHorizontal size={16} />
      </button>
      {open && coords && (
        <div
          role="menu"
          style={{ position: "fixed", top: coords.top, right: coords.right }}
          className="z-50 min-w-[160px] rounded-md border border-hairline-dark bg-surface-elevated py-1 shadow-lg"
        >
          {items.map((item) => (
            <button
              key={item.label}
              role="menuitem"
              onClick={() => { setOpen(false); item.onClick(); }}
              className={`block w-full px-md py-sm text-left text-caption ${
                item.danger
                  ? "text-accent-danger hover:bg-accent-danger/10"
                  : "text-stone hover:text-on-dark hover:bg-[var(--bg-interactive)]"
              }`}
            >
              {item.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
