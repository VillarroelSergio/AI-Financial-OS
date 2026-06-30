import { AlertTriangle } from "lucide-react";
import type { ConcentrationAlert } from "@/lib/api/investments";

const TYPE_LABEL: Record<string, string> = {
  asset:    "activo",
  currency: "divisa",
};

export default function ConcentrationAlertCard({ alert }: { alert: ConcentrationAlert }) {
  return (
    <div className="flex items-start gap-3 rounded-lg border-l-[3px] border-accent-warning bg-accent-warning/5 px-4 py-3">
      <AlertTriangle size={16} className="mt-0.5 shrink-0 text-accent-warning" />
      <p className="text-sm text-on-dark">
        <span className="font-medium">{alert.key}</span>
        {" "}representa el{" "}
        <span className="font-semibold text-accent-warning">{alert.weight_pct.toFixed(1)}%</span>
        {" "}de tu cartera por {TYPE_LABEL[alert.type] ?? alert.type}
        {" "}(limite recomendado: {alert.threshold_pct}%).
      </p>
    </div>
  );
}
