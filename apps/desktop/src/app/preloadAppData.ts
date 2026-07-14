import { api } from "@/lib/api/client";

/**
 * Calienta las lecturas de las vistas principales al arrancar. La app conserva
 * todas las pantallas disponibles desde el primer render: no hay carga diferida
 * por módulo ni navegación que espere al backend. Cada petición queda en la
 * caché compartida del cliente durante su TTL normal.
 */
export function preloadAppData(): Promise<PromiseSettledResult<unknown>[]> {
  const period = new Date().toISOString().slice(0, 7);
  const paths = [
    "/api/dashboard/overview", "/api/accounts", "/api/categories", "/api/transactions",
    "/api/dashboard/spending/years", "/api/dashboard/spending/monthly?months=12",
    `/api/dashboard/spending?month=${period}`,
    "/api/investments/summary", "/api/investments/holdings", "/api/investments/portfolio/evolution", "/api/investments/reconciliation",
    "/api/market-intelligence/economy/overview", "/api/market-intelligence/snapshot/market",
    "/api/market-intelligence/snapshot/forex", "/api/market-intelligence/snapshot/bonds", "/api/market-intelligence/ingest-status",
    `/api/insights?period=${period}&limit=10`, `/api/insights/monthly-review?period=${period}`, "/api/goals",
  ];

  return Promise.allSettled(paths.map((path) => api.get(path)));
}
