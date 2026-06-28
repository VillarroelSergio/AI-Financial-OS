import { ChartCard } from "@/components/ui/Dashboard";
import { InsightCard } from "./InsightCard";
import type { Insight } from "../types/insights.types";

export function DataQualityCard({ insights }: { insights: Insight[] }) {
  if (!insights.length) return null;
  return (
    <ChartCard title="Calidad de datos" description="Señales que afectan la fiabilidad de los análisis">
      <div className="space-y-3">
        {insights.map((i) => <InsightCard key={i.id} insight={i} compact />)}
      </div>
    </ChartCard>
  );
}
