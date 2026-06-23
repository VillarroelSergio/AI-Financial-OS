interface MetricCardProps {
  label: string;
  value: string;
  delta?: string;
  deltaPositive?: boolean;
  sublabel?: string;
}

export default function MetricCard({ label, value, delta, deltaPositive, sublabel }: MetricCardProps) {
  return (
    <div className="bg-surface-card rounded-md p-xl border border-hairline-dark">
      <p className="text-caption text-stone uppercase tracking-widest mb-xs">{label}</p>
      <p className="text-heading-md text-on-dark">{value}</p>
      {delta && (
        <p className={`text-caption mt-xs ${deltaPositive ? "text-accent-teal" : "text-accent-danger"}`}>
          {delta}
        </p>
      )}
      {sublabel && <p className="text-caption text-stone mt-xs">{sublabel}</p>}
    </div>
  );
}
