import {
  AreaChart,
  Area,
  Tooltip,
  ResponsiveContainer,
} from "recharts";


export interface SpendSparklineProps {
  data: Array<{ period: string; amount: number }>;
  height?: number;
  className?: string;
}

export function SpendSparkline({
  data,
  height = 80,
  className,
}: SpendSparklineProps) {
  if (!data.length) {
    return (
      <div
        className={className}
        style={{ height }}
      >
        <div className="h-full flex items-center justify-center text-xs text-stone">
          No data
        </div>
      </div>
    );
  }

  // Convert pence to pounds for display
  const chartData = data.map((d) => ({
    period: d.period,
    amount: d.amount / 100,
  }));

  return (
    <div className={className} style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={chartData} margin={{ top: 2, right: 2, bottom: 2, left: 2 }}>
          <defs>
            <linearGradient id="sparkGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#FF5A5F" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#FF5A5F" stopOpacity={0} />
            </linearGradient>
          </defs>
          <Tooltip
            contentStyle={{
              backgroundColor: "#1B3A5C",
              border: "1px solid #2B5278",
              borderRadius: "8px",
              fontSize: "12px",
              padding: "4px 8px",
            }}
            labelStyle={{ color: "#fff", fontSize: "11px" }}
            formatter={(value: number | undefined) => [`£${(value ?? 0).toFixed(2)}`, "Spent"]}
          />
          <Area
            type="monotone"
            dataKey="amount"
            stroke="#FF5A5F"
            strokeWidth={2}
            fill="url(#sparkGradient)"
            dot={false}
            activeDot={{ r: 3, fill: "#FF5A5F", stroke: "#fff", strokeWidth: 1 }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
