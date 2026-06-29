import { useCallback, useEffect, useState } from "react";
import {
  Budget, BudgetComparisonItem, BudgetCreate, BudgetUpdate, CalendarEvent,
  CashflowForecast, RecurringCreate, RecurringTransaction,
  createBudget, createRecurring, deleteBudget, deleteRecurring,
  fetchBudgetComparison, fetchBudgets, fetchCalendar, fetchCashflowForecast,
  fetchRecurring, updateBudget, updateRecurring,
} from "@/lib/api/budgets";

export function useBudgets() {
  const [budgets, setBudgets] = useState<Budget[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setBudgets(await fetchBudgets());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al cargar presupuestos");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const add = useCallback(async (body: BudgetCreate) => {
    await createBudget(body);
    await load();
  }, [load]);

  const update = useCallback(async (id: string, body: BudgetUpdate) => {
    await updateBudget(id, body);
    await load();
  }, [load]);

  const remove = useCallback(async (id: string) => {
    await deleteBudget(id);
    await load();
  }, [load]);

  return { budgets, loading, error, refresh: load, add, update, remove };
}

export function useBudgetComparison(month?: string) {
  const [data, setData] = useState<BudgetComparisonItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setData(await fetchBudgetComparison(month));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al cargar comparativa");
    } finally {
      setLoading(false);
    }
  }, [month]);

  useEffect(() => { load(); }, [load]);
  return { data, loading, error, refresh: load };
}

export function useRecurring() {
  const [recurring, setRecurring] = useState<RecurringTransaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setRecurring(await fetchRecurring());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al cargar recurrentes");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const add = useCallback(async (body: RecurringCreate) => {
    await createRecurring(body);
    await load();
  }, [load]);

  const update = useCallback(async (id: string, body: Partial<RecurringCreate>) => {
    await updateRecurring(id, body);
    await load();
  }, [load]);

  const remove = useCallback(async (id: string) => {
    await deleteRecurring(id);
    await load();
  }, [load]);

  return { recurring, loading, error, refresh: load, add, update, remove };
}

export function useCalendar(days = 60) {
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setEvents(await fetchCalendar(days));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al cargar calendario");
    } finally {
      setLoading(false);
    }
  }, [days]);

  useEffect(() => { load(); }, [load]);
  return { events, loading, error, refresh: load };
}

export function useCashflowForecast(months = 3) {
  const [data, setData] = useState<CashflowForecast | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setData(await fetchCashflowForecast(months));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al cargar previsión");
    } finally {
      setLoading(false);
    }
  }, [months]);

  useEffect(() => { load(); }, [load]);
  return { data, loading, error, refresh: load };
}
