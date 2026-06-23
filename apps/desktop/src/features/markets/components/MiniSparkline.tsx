// apps/desktop/src/features/markets/components/MiniSparkline.tsx
import { Line, LineChart, ResponsiveContainer } from "recharts";

interface Props {
  sparkline: number[];
  changePct: number | null;
}

export default function MiniSparkline({ sparkline, changePct }: Props) {
  if (!sparkline || sparkline.length < 2) {
    return (
      <LineChart width={60} height={24} data={[{ v: 0 }, { v: 0 }]}>
        <Line
          type="monotone"
          dataKey="v"
          stroke="#78716c"
          dot={false}
          strokeWidth={1.5}
          isAnimationActive={false}
        />
      </LineChart>
    );
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
