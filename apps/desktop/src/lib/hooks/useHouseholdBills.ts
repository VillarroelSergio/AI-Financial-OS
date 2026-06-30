import { useCallback, useEffect, useState } from "react";
import {
  createHouseholdBill,
  deleteHouseholdBill,
  fetchHouseholdBillSummary,
  fetchHouseholdBills,
  type HouseholdBill,
  type HouseholdBillCreate,
  type HouseholdBillSummary,
} from "@/lib/api/household-bills";

export function useHouseholdBills() {
  const [bills, setBills] = useState<HouseholdBill[]>([]);
  const [summary, setSummary] = useState<HouseholdBillSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [billData, summaryData] = await Promise.all([fetchHouseholdBills(), fetchHouseholdBillSummary()]);
      setBills(billData);
      setSummary(summaryData);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al cargar facturas");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const add = useCallback(async (body: HouseholdBillCreate) => {
    await createHouseholdBill(body);
    await load();
  }, [load]);

  const remove = useCallback(async (id: string) => {
    await deleteHouseholdBill(id);
    await load();
  }, [load]);

  return { bills, summary, loading, error, refresh: load, add, remove };
}
