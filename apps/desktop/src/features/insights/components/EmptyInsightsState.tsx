import { Lightbulb, Upload } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { EmptyState } from "@/components/ui/Dashboard";

export function EmptyInsightsState() {
  const navigate = useNavigate();
  return (
    <EmptyState
      icon={Lightbulb}
      title="Aún no hay suficientes datos para generar insights fiables"
      description="Importa movimientos y actualiza tus cuentas para que Financial OS pueda detectar patrones, alertas y oportunidades."
      action={
        <button
          onClick={() => navigate("/imports")}
          className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2.5 text-sm font-semibold text-white"
        >
          <Upload size={16} /> Importar movimientos
        </button>
      }
    />
  );
}
