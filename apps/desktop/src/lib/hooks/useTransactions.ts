import { useCallback, useEffect, useState } from "react";
import {
  createTransaction,
  deleteTransaction,
  fetchTransactions,
  updateTransaction,
  type TransactionCreate,
  type TransactionFilters,
} from "@/lib/api/transactions";
import type { Transaction } from "@/lib/types";

export function useTransactions(filters?: TransactionFilters) {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const filtersKey = JSON.stringify(filters);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setTransactions(await fetchTransactions(filters));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al cargar movimientos");
    } finally {
      setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filtersKey]);

  useEffect(() => {
    load();
  }, [load]);

  const add = async (data: TransactionCreate) => {
    const tx = await createTransaction(data);
    setTransactions((prev) => [tx, ...prev]);
    return tx;
  };

  const remove = async (id: string) => {
    await deleteTransaction(id);
    setTransactions((prev) => prev.filter((t) => t.id !== id));
  };

  const update = async (id: string, data: Partial<TransactionCreate>) => {
    const tx = await updateTransaction(id, data);
    setTransactions((prev) => prev.map((item) => (item.id === id ? tx : item)));
    return tx;
  };

  return { transactions, loading, error, reload: load, add, update, remove };
}
