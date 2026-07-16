import { animate, type Transition, type Variants } from "framer-motion";
import { useEffect, useRef } from "react";

// ─── Variants reutilizables (Fase 4 · §8) ───
export const staggerContainer: Variants = {
  hidden: {},
  show: { transition: { staggerChildren: 0.03 } },
};

export const staggerItem: Variants = {
  hidden: { opacity: 0, y: 8 },
  show: { opacity: 1, y: 0, transition: { duration: 0.25, ease: "easeOut" } },
};

// Filas de tabla: delay 20ms
export const rowStaggerContainer: Variants = {
  hidden: {},
  show: { transition: { staggerChildren: 0.02 } },
};

// Spring para superficies que entran/salen (dialogs, drawers, popover)
export const springPanel: Transition = { type: "spring", stiffness: 260, damping: 24 };

// Transición de ruta: fade + rise 6px, sin animación de salida
export const routeTransition: Transition = { duration: 0.18, ease: "easeOut" };

function prefersReducedMotion(): boolean {
  return typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

/**
 * Cifra con count-up al montar (o al cambiar de valor). Formatea cada frame.
 * Respeta prefers-reduced-motion: si está activo, muestra el valor final sin animar.
 */
export function CountUp({
  value,
  format,
  className,
  style,
}: {
  value: number;
  format: (n: number) => string;
  className?: string;
  style?: React.CSSProperties;
}) {
  const ref = useRef<HTMLSpanElement>(null);
  const prev = useRef(0);

  useEffect(() => {
    const node = ref.current;
    if (!node) return;
    if (prefersReducedMotion()) {
      node.textContent = format(value);
      prev.current = value;
      return;
    }
    const controls = animate(prev.current, value, {
      duration: 0.6,
      ease: "easeOut",
      onUpdate: (v) => {
        node.textContent = format(v);
      },
      onComplete: () => {
        prev.current = value;
      },
    });
    return () => controls.stop();
  }, [value, format]);

  return (
    <span ref={ref} className={className} style={style}>
      {format(value)}
    </span>
  );
}
