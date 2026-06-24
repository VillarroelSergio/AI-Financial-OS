import { useCallback, useEffect, useState } from "react";
import { getSnapshot, refreshEconomy, getPersonalImpact } from "@/lib/api/economy";
import type { MacroSnapshot, PersonalImpact } from "@/lib/types";

export function useEconomy() {
  const [snapshot, setSnapshot] = useState<MacroSnapshot | null>(null);
  const [impact, setImpact] = useState<PersonalImpact | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    try {
      const [snap, imp] = await Promise.all([getSnapshot(), getPersonalImpact()]);
      setSnapshot(snap);
      setImpact(imp);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al cargar datos económicos");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const refresh = useCallback(async () => {
    if (refreshing) return;
    setRefreshing(true);
    try {
      const snap = await refreshEconomy();
      setSnapshot(snap);
      const imp = await getPersonalImpact();
      setImpact(imp);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al actualizar datos económicos");
    } finally {
      setRefreshing(false);
    }
  }, [refreshing]);

  return { snapshot, impact, loading, error, refreshing, refresh };
}
