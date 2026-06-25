export interface SnapshotRoute {
  path: string;
  filename: string;
  screenName: string;
  state: string;
  description: string;
  requiresInteraction: boolean;
}

export const snapshotRoutes: SnapshotRoute[] = [
  {
    path: "/",
    filename: "overview.png",
    screenName: "Overview",
    state: "mock_data",
    description: "Dashboard principal con patrimonio neto, liquidez, inversiones y métricas del mes",
    requiresInteraction: false,
  },
  {
    path: "/spending",
    filename: "spending.png",
    screenName: "Spending",
    state: "mock_data",
    description: "Análisis de gastos mensual con pie chart por categoría y desglose",
    requiresInteraction: false,
  },
  {
    path: "/investments",
    filename: "investments.png",
    screenName: "Investments",
    state: "mock_data",
    description: "Portfolio tracker con TR stocks, Finizens funds y cuenta remunerada",
    requiresInteraction: false,
  },
  {
    path: "/investments",
    filename: "investments-empty.png",
    screenName: "Investments (empty)",
    state: "empty",
    description: "Estado vacío sin posiciones registradas",
    requiresInteraction: false,
  },
  {
    path: "/goals",
    filename: "goals.png",
    screenName: "Goals",
    state: "empty",
    description: "Objetivos financieros — estado inicial sin objetivos",
    requiresInteraction: false,
  },
  {
    path: "/economy",
    filename: "economy.png",
    screenName: "Economy",
    state: "empty",
    description: "Indicadores macroeconómicos — estado inicial",
    requiresInteraction: false,
  },
  {
    path: "/insights",
    filename: "insights.png",
    screenName: "Insights",
    state: "empty",
    description: "Insights personalizados — estado inicial sin análisis",
    requiresInteraction: false,
  },
  {
    path: "/imports",
    filename: "imports-empty.png",
    screenName: "Imports (empty)",
    state: "empty",
    description: "Centro de importación — estado vacío antes de seleccionar archivo",
    requiresInteraction: false,
  },
  {
    path: "/imports?demo=preview",
    filename: "imports-preview.png",
    screenName: "Imports (preview)",
    state: "preview_demo",
    description: "Centro de importación — preview y validación con datos ficticios",
    requiresInteraction: false,
  },
  {
    path: "/settings",
    filename: "settings.png",
    screenName: "Settings",
    state: "mock_data",
    description: "Configuración de la aplicación — idioma, moneda y tema",
    requiresInteraction: false,
  },
];
