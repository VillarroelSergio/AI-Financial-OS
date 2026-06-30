export interface CopilotContext {
  module: string;
  route: string;
  data_status: string;
  visible_metrics: string[];
  suggestedQuestions: string[];
}

const DEFAULT_CONTEXT: CopilotContext = {
  module: "Resumen",
  route: "/",
  data_status: "visible en pantalla",
  visible_metrics: ["patrimonio", "liquidez", "ingresos", "gastos", "insights"],
  suggestedQuestions: [
    "Resume mi situacion financiera visible",
    "Que datos faltan para una lectura mas fiable",
    "Que deberia revisar primero",
  ],
};

const CONTEXT_BY_ROUTE: Record<string, Omit<CopilotContext, "route">> = {
  "/spending": {
    module: "Gastos",
    data_status: "periodo seleccionado en pantalla",
    visible_metrics: ["gasto total", "ingreso total", "ahorro neto", "categorias", "drilldown"],
    suggestedQuestions: ["Explica esta distribucion de gasto", "Detecta categorias anomalas", "Que gastos parecen recurrentes"],
  },
  "/transactions": {
    module: "Movimientos",
    data_status: "ledger filtrado por busqueda y filtros activos",
    visible_metrics: ["descripcion", "cuenta", "categoria", "tipo", "importe", "fecha"],
    suggestedQuestions: ["Resume mis movimientos del mes", "Encuentra movimientos sin categoria", "Detecta posibles duplicados"],
  },
  "/investments": {
    module: "Inversiones",
    data_status: "cartera y calidad visibles",
    visible_metrics: ["valor cartera", "rentabilidad", "precio", "FX", "calidad de cartera"],
    suggestedQuestions: ["Revisa mi cartera", "Explica mi rentabilidad", "Que posiciones requieren revision"],
  },
  "/planificacion": {
    module: "Planificacion",
    data_status: "presupuestos, recurrentes, facturas y cashflow visibles",
    visible_metrics: ["presupuestos", "candidatos recurrentes", "facturas", "cashflow"],
    suggestedQuestions: ["Detecta posibles suscripciones", "Propone recurrentes candidatos", "Explica mi prevision de cashflow"],
  },
  "/goals": {
    module: "Objetivos",
    data_status: "objetivos y simulaciones visibles",
    visible_metrics: ["plazo", "aportacion mensual", "inflacion", "escenarios"],
    suggestedQuestions: ["Explicame si voy en plazo", "Cuanto deberia aportar para llegar", "Compara escenarios"],
  },
  "/economy": {
    module: "Economia",
    data_status: "indicadores macro disponibles por region",
    visible_metrics: ["inflacion", "tipos", "paro", "PIB", "EUR/USD", "impacto personal"],
    suggestedQuestions: ["Que indicadores afectan a mi situacion", "Explica el impacto del EUR/USD", "Que datos macro faltan"],
  },
  "/markets": {
    module: "Mercados",
    data_status: "snapshot de mercado cacheado o actualizado",
    visible_metrics: ["indices", "cripto", "materias primas", "divisas", "bonos", "calidad"],
    suggestedQuestions: ["Resume el pulso de mercado", "Que datos estan stale", "Que indicadores afectan a mis inversiones"],
  },
  "/insights": {
    module: "Insights",
    data_status: "insights calculados por reglas deterministas",
    visible_metrics: ["severidad", "fuentes", "datos usados", "estado parcial"],
    suggestedQuestions: ["Resume los insights prioritarios", "Explica los datos usados", "Que insights tienen datos incompletos"],
  },
};

export function getCopilotContext(pathname: string): CopilotContext {
  const matched = Object.entries(CONTEXT_BY_ROUTE).find(([route]) => pathname.startsWith(route));
  if (!matched) return { ...DEFAULT_CONTEXT, route: pathname };
  return { ...matched[1], route: pathname };
}
