// Skeletons con silueta real de la página (Fase 5 · §6)

export function Skeleton({ className = "" }: { className?: string }) {
  return <div className={`animate-pulse rounded-lg bg-[var(--bg-card-elevated)] ${className}`} />;
}

export function CardSkeleton({ rows = 3 }: { rows?: number }) {
  return (
    <div className="animate-pulse space-y-2 py-2">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="h-4 rounded bg-[var(--bg-card-elevated)]" />
      ))}
    </div>
  );
}

// Silueta del dashboard: hero + fila de 3 KPI
export function DashboardSkeleton() {
  return (
    <div className="p-8 max-w-[1500px] mx-auto space-y-6">
      <div className="space-y-2">
        <Skeleton className="h-7 w-40" />
        <Skeleton className="h-4 w-72" />
      </div>
      <Skeleton className="h-32 w-full rounded-[20px]" />
      <div className="dashboard-grid">
        {[0, 1, 2].map((i) => (
          <div key={i} className="col-span-4">
            <Skeleton className="h-28 w-full rounded-2xl" />
          </div>
        ))}
      </div>
    </div>
  );
}
