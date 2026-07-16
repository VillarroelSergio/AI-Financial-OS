import { animate, type Transition, type Variants } from "framer-motion";
import { useEffect, useRef } from "react";

// ─── Variants reutilizables (Fase 4 · §8) ───
// Las entradas comparten el mismo gesto: opacidad 0 → 1 y desplazamiento breve
// hasta la posición final. Sin rebote ni escalado perceptible.
export const subtleEnterTransition: Transition = {
  duration: 0.28,
  ease: [0.22, 1, 0.36, 1],
};

export const contentEnter: Variants = {
  hidden: { opacity: 0, y: 6 },
  show: { opacity: 1, y: 0, transition: subtleEnterTransition },
};

export const surfaceEnter: Variants = {
  hidden: { opacity: 0, y: 4 },
  show: { opacity: 1, y: 0, transition: subtleEnterTransition },
};

export const staggerContainer: Variants = {
  hidden: {},
  show: { transition: { staggerChildren: 0.025 } },
};

export const staggerItem: Variants = {
  hidden: { opacity: 0, y: 4 },
  show: { opacity: 1, y: 0, transition: subtleEnterTransition },
};

// Filas de tabla: delay 15ms
export const rowStaggerContainer: Variants = {
  hidden: {},
  show: { transition: { staggerChildren: 0.015 } },
};

// Spring reservado para cambios de posición interactivos, como el control segmentado.
export const springPanel: Transition = { type: "spring", stiffness: 260, damping: 24 };

// Alias conservado para consumidores existentes.
export const routeTransition = subtleEnterTransition;

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
