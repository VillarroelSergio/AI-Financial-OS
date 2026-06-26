import { useCallback, useEffect, useState } from "react";
import { createGoal, deleteGoal, fetchGoals, updateGoal, type Goal, type GoalCreate } from "@/lib/api/goals";

export function useGoals() {
  const [goals, setGoals] = useState<Goal[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const load = useCallback(async () => {
    setLoading(true); setError(null);
    try { setGoals(await fetchGoals()); }
    catch { setError("No se han podido cargar tus objetivos."); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { void load(); }, [load]);
  const add = async (data: GoalCreate) => { const goal = await createGoal(data); setGoals((items) => [goal, ...items]); return goal; };
  const change = async (id: string, data: Parameters<typeof updateGoal>[1]) => { const goal = await updateGoal(id, data); setGoals((items) => items.map((item) => item.id === id ? goal : item)); return goal; };
  const remove = async (id: string) => { await deleteGoal(id); setGoals((items) => items.filter((item) => item.id !== id)); };
  return { goals, loading, error, reload: load, add, change, remove };
}
