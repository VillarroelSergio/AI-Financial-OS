// apps/desktop/src/features/markets/components/MiniSparkline.tsx
import { Line, LineChart, ResponsiveContainer } from "recharts";

interface Props {
  sparkline: number[];
  changePct: number | null;
}

export default function MiniSparkline({ sparkline, changePct }: Props) {
  if (!sparkline.length) {
    return <div className="w-[60px] h-6 bg-surface-elevated rounded" />;
  }

  const positive = (changePct ?? 0) >= 0;
  const color = positive ? "#00a87e" : "#e23b4a";
  const chartData = sparkline.map((v) => ({ v }));

  return (
    <ResponsiveContainer width={60} height={24}>
      <LineChart data={chartData}>
        <Line
          type="monotone"
          dataKey="v"
          stroke={color}
          dot={false}
          strokeWidth={1.5}
          isAnimationActive={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
