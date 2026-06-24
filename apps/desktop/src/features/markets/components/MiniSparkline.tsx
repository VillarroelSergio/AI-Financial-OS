// apps/desktop/src/features/markets/components/MiniSparkline.tsx
import { Line, LineChart, ResponsiveContainer } from "recharts";

interface Props {
  sparkline: number[];
  changePct: number | null;
}

const SPARKLINE_WIDTH = 80;
const SPARKLINE_HEIGHT = 32;

export default function MiniSparkline({ sparkline, changePct }: Props) {
  const positive = (changePct ?? 0) >= 0;
  const color = positive ? "#00a87e" : "#e23b4a";

  if (!sparkline || sparkline.length < 2) {
    return (
      <div
        className="flex items-center justify-center opacity-30"
        style={{ width: SPARKLINE_WIDTH, height: SPARKLINE_HEIGHT }}
        aria-hidden="true"
      >
        <LineChart
          width={SPARKLINE_WIDTH}
          height={SPARKLINE_HEIGHT}
          data={[{ v: 0 }, { v: 0 }]}
        >
          <Line
            type="monotone"
            dataKey="v"
            stroke="#505a63"
            dot={false}
            strokeWidth={1.5}
            isAnimationActive={false}
          />
        </LineChart>
      </div>
    );
  }

  const chartData = sparkline.map((v) => ({ v }));

  return (
    <div
      style={{ width: SPARKLINE_WIDTH, height: SPARKLINE_HEIGHT }}
      aria-hidden="true"
    >
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData} margin={{ top: 2, right: 2, bottom: 2, left: 2 }}>
          <Line
            type="monotone"
            dataKey="v"
            stroke={color}
            dot={false}
            strokeWidth={2}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
