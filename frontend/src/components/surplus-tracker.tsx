import { useMemo } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { useSurplus } from "@/hooks/useApi";
import { formatCurrency } from "@/lib/utils";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  ReferenceLine,
} from "recharts";
// Cell is used in JSX below

export function SurplusTracker() {
  const { data: surplusData, isLoading } = useSurplus(12);

  const chartData = useMemo(() => {
    if (!surplusData) return [];
    return surplusData.map((item) => {
      const d = new Date(item.period_start);
      return {
        month: d.toLocaleDateString("en-GB", {
          month: "short",
          year: "2-digit",
        }),
        surplus: item.surplus_pence,
        cumulative: item.cumulative_surplus_pence,
      };
    });
  }, [surplusData]);

  const runningTotal = surplusData?.length
    ? surplusData[surplusData.length - 1].cumulative_surplus_pence
    : 0;
  const isPositive = runningTotal >= 0;

  if (isLoading) {
    return (
      <Card>
        <CardContent className="py-8 text-center text-stone">
          Loading surplus data...
        </CardContent>
      </Card>
    );
  }

  if (!surplusData || surplusData.length === 0) {
    return (
      <Card>
        <CardContent className="py-8 text-center text-stone">
          No surplus data available yet. Budget data is needed to calculate
          surplus.
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Running Total Callout */}
      <Card className="border border-mint/20 bg-gradient-to-r from-charcoal to-navy-deep">
        <CardContent className="p-6 text-center">
          <div className="text-stone text-sm mb-2">
            CUMULATIVE SURPLUS (12 MONTHS)
          </div>
          <div
            className={`text-5xl ${isPositive ? "text-mint" : "text-coral"}`}
            style={{ fontFamily: "var(--font-display)" }}
          >
            {formatCurrency(runningTotal)}
          </div>
          <div className="text-stone text-sm mt-2">
            {isPositive
              ? "You've saved across all envelopes this year"
              : "You've overspent across all envelopes this year"}
          </div>
        </CardContent>
      </Card>

      {/* Bar Chart */}
      <Card>
        <CardHeader>
          <CardTitle>MONTHLY SURPLUS / DEFICIT</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2B5278" />
              <XAxis
                dataKey="month"
                stroke="#6B7280"
                fontSize={11}
                tickLine={false}
              />
              <YAxis
                stroke="#6B7280"
                fontSize={11}
                tickLine={false}
                tickFormatter={(v) => `£${(v / 100).toFixed(0)}`}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#1B3A5C",
                  border: "1px solid #2B5278",
                  borderRadius: "8px",
                }}
                labelStyle={{ color: "#fff" }}
                formatter={(value: number | undefined) => [
                  formatCurrency(value ?? 0),
                  "Surplus",
                ]}
              />
              <ReferenceLine y={0} stroke="#2B5278" strokeWidth={1} />
              <Bar dataKey="surplus" radius={[4, 4, 0, 0]} name="surplus">
                {chartData.map((entry, index) => (
                  <Cell
                    key={index}
                    fill={entry.surplus >= 0 ? "#00D9B5" : "#FF5A5F"}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Placeholder for group breakdown */}
      <Card>
        <CardContent className="py-6 text-center text-stone text-sm">
          📊 Group breakdown coming soon
        </CardContent>
      </Card>
    </div>
  );
}
