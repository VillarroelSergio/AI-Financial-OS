import { useCallback, useEffect, useState } from "react";
import {
  createAccount,
  deleteAccount,
  fetchAccounts,
  updateAccount,
  type AccountCreate,
  type AccountUpdate,
} from "@/lib/api/accounts";
import type { Account } from "@/lib/types";

export function useAccounts() {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setAccounts(await fetchAccounts());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al cargar cuentas");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const add = async (data: AccountCreate) => {
    const account = await createAccount(data);
    setAccounts((prev) => [...prev, account]);
    return account;
  };

  const update = async (id: string, data: AccountUpdate) => {
    const account = await updateAccount(id, data);
    setAccounts((prev) => prev.map((a) => (a.id === id ? account : a)));
    return account;
  };

  const remove = async (id: string) => {
    await deleteAccount(id);
    setAccounts((prev) => prev.filter((a) => a.id !== id));
  };

  return { accounts, loading, error, reload: load, add, update, remove };
}
