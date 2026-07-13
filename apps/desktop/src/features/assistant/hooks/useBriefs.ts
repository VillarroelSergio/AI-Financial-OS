import { useCallback, useState } from "react";
import { generateBrief, listBriefs } from "../api/aiAssistantApi";
import type { AiBrief } from "../types/aiAssistant.types";

/** AI-3: historial de briefs + generación bajo demanda. El más reciente (índice 0)
 *  es el brief vigente que la UI muestra como hero. El backend hace fallback
 *  determinista si el LLM no responde, así que generate() nunca cuelga. */
export function useBriefs() {
  const [briefs, setBriefs] = useState<AiBrief[]>([]);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setBriefs(await listBriefs());
    } catch {
      // Non-fatal: la lista vacía deja el estado "genera tu primer análisis".
    }
  }, []);

  const generate = useCallback(async (scope = "monthly_review") => {
    if (generating) return;
    setGenerating(true);
    setError(null);
    try {
      const brief = await generateBrief(scope);
      // Idempotente por (scope, period): sustituye el existente y lo pone el primero.
      setBriefs((prev) => [
        brief,
        ...prev.filter((b) => !(b.scope === brief.scope && b.period === brief.period)),
      ]);
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo generar el análisis");
    } finally {
      setGenerating(false);
    }
  }, [generating]);

  return { briefs, generating, error, load, generate };
}
