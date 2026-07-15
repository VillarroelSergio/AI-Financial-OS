interface MetricCardProps {
  label: string;
  value: string;
  delta?: string;
  deltaPositive?: boolean;
  sublabel?: string;
}

export default function MetricCard({ label, value, delta, deltaPositive, sublabel }: MetricCardProps) {
  return (
    <div className="premium-card min-w-0 rounded-lg p-xl">
      <p className="text-[11px] text-stone uppercase tracking-[.16em] mb-xs">{label}</p>
      <p className="financial-number break-words text-[clamp(1.25rem,2vw,1.75rem)] leading-tight text-on-dark">{value}</p>
      {delta && (
        <p className={`text-caption mt-xs ${deltaPositive ? "text-accent-teal" : "text-accent-danger"}`}>
          {delta}
        </p>
      )}
      {sublabel && <p className="text-caption text-stone mt-xs">{sublabel}</p>}
    </div>
  );
}
