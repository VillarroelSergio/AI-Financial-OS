import { CheckCircle2, Info, XCircle } from "lucide-react";
import { createContext, useCallback, useContext, useMemo, useState } from "react";
import type { ReactNode } from "react";

type ToastTone = "success" | "error" | "info";
type Toast = { id: number; message: string; tone: ToastTone };
type ToastContextValue = { notify: (message: string, tone?: ToastTone) => void };

const ToastContext = createContext<ToastContextValue | null>(null);
const TONE = {
  success: { icon: CheckCircle2, className: "border-positive/35 bg-positive/10 text-positive" },
  error: { icon: XCircle, className: "border-negative/35 bg-negative/10 text-negative" },
  info: { icon: Info, className: "border-primary/35 bg-primary/10 text-primary-bright" },
} satisfies Record<ToastTone, { icon: typeof Info; className: string }>;

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const notify = useCallback((message: string, tone: ToastTone = "info") => {
    const id = Date.now();
    setToasts((current) => [...current, { id, message, tone }].slice(-3));
    window.setTimeout(() => setToasts((current) => current.filter((toast) => toast.id !== id)), 3600);
  }, []);
  const value = useMemo(() => ({ notify }), [notify]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="pointer-events-none fixed bottom-5 right-5 z-[120] grid w-[min(360px,calc(100vw-40px))] gap-2" aria-live="polite">
        {toasts.map((toast) => {
          const tone = TONE[toast.tone];
          const Icon = tone.icon;
          return <div key={toast.id} className={`motion-toast flex items-center gap-3 rounded-xl border px-4 py-3 text-sm shadow-lg ${tone.className}`}>
            <Icon size={17} /><span className="text-on-dark">{toast.message}</span>
          </div>;
        })}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const value = useContext(ToastContext);
  if (!value) throw new Error("useToast debe usarse dentro de ToastProvider");
  return value;
}
