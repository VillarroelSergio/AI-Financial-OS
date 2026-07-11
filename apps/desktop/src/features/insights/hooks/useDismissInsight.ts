import { useCallback, useState } from "react";
import { dismissInsight, restoreInsight } from "../api/insightsApi";

export function useDismissInsight(onSuccess?: (insightId: string) => void) {
  const [loading, setLoading] = useState(false);

  const dismiss = useCallback(async (insightId: string) => {
    setLoading(true);
    try {
      await dismissInsight(insightId);
      onSuccess?.(insightId);
    } catch {
      // silently fail — dismiss is non-critical
    } finally {
      setLoading(false);
    }
  }, [onSuccess]);

  // INS-7: deshacer un descarte (undo). Best-effort, igual que dismiss.
  const restore = useCallback(async (insightId: string) => {
    try {
      await restoreInsight(insightId);
    } catch {
      // silently fail — restore is non-critical
    }
  }, []);

  return { dismiss, restore, loading };
}
