import { useCallback, useState } from "react";
import { dismissInsight } from "../api/insightsApi";

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

  return { dismiss, loading };
}
