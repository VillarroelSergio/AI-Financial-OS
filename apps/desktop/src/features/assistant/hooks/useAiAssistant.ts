import { useCallback, useEffect, useState } from "react";
import { getAiStatus } from "../api/aiAssistantApi";
import type { AiStatus } from "../types/aiAssistant.types";

export function useAiAssistant() {
  const [status, setStatus] = useState<AiStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const s = await getAiStatus();
      setStatus(s);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al conectar con el asistente");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const defaultProvider = status?.providers.find(
    (p) => p.name === status.default_provider
  );

  return {
    status,
    loading,
    error,
    reload: load,
    isAvailable: !!defaultProvider?.available,
    defaultProvider,
  };
}
