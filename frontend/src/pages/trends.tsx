import { useState, useMemo } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { AccountSelector } from "@/components/account-selector";
import { useTrendsEnvelopes, useOverBudget, useIncome } from "@/hooks/useApi";
import { formatCurrency } from "@/lib/utils";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Line,
  ComposedChart,
} from "recharts";
import { AlertTriangle } from "lucide-react";

type TrendsTab = "envelopes" | "income";
type MonthRange = 3 | 6 | 12;

function formatMonth(dateStr: string): string {
  const d = new Date(dateStr);
  return d.toLocaleDateString("en-GB", { month: "short", year: "2-digit" });
}

export function Trends() {
  const [activeTab, setActiveTab] = useState<TrendsTab>("envelopes");
  const [months, setMonths] = useState<MonthRange>(6);
  const [selectedBudgetId, setSelectedBudgetId] = useState<string | undefined>(
    undefined
  );

  const { data: trendsData, isLoading: trendsLoading } = useTrendsEnvelopes(
    months,
    selectedBudgetId
  );
  const { data: overBudgetData } = useOverBudget(months);
  const { data: incomeData, isLoading: incomeLoading } = useIncome(months);

  // Derive unique budgets from trends data for the envelope selector
  const budgetOptions = useMemo(() => {
    if (!trendsData) return [];
    const map = new Map<string, string>();
    for (const item of trendsData) {
      const name = item.budget_name || item.group_name;
      if (!map.has(name)) {
        map.set(name, name);
      }
    }
    return Array.from(map.keys()).sort();
  }, [trendsData]);

  // Aggregate trend data by month (sum across budgets if "All Envelopes")
  const chartData = useMemo(() => {
    if (!trendsData) return [];
    const byMonth = new Map<
      string,
      { month: string; spent: number; allocated: number }
    >();

    for (const item of trendsData) {
      const key = item.period_start;
      const existing = byMonth.get(key) || {
        month: formatMonth(item.period_start),
        spent: 0,
        allocated: 0,
      };
      existing.spent += item.spent;
      existing.allocated += item.allocated;
      byMonth.set(key, existing);
    }

    return Array.from(byMonth.entries())
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([, v]) => v);
  }, [trendsData]);

  // Month-over-month deltas
  const deltas = useMemo(() => {
    return chartData.map((item, i) => {
      if (i === 0) return { ...item, delta: null };
      const prev = chartData[i - 1].spent;
      const pct = prev > 0 ? ((item.spent - prev) / prev) * 100 : 0;
      return { ...item, delta: pct };
    });
  }, [chartData]);

  // Income chart data
  const incomeChartData = useMemo(() => {
    if (!incomeData) return [];
    return incomeData.map((item) => ({
      month: formatMonth(item.period_start),
      income: item.income_total_pence,
      expenses: item.expense_total_pence,
      net: item.net_pence,
    }));
  }, [incomeData]);

  const monthOptions: MonthRange[] = [3, 6, 12];

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h1
          className="text-3xl text-white"
          style={{ fontFamily: "var(--font-display)" }}
        >
          TRENDS
        </h1>
        <AccountSelector />
      </div>

      {/* Tab Buttons */}
      <div className="flex gap-2 mb-6">
        <button
          onClick={() => setActiveTab("envelopes")}
          className={`px-6 py-2 rounded-full text-sm font-medium transition-all ${
            activeTab === "envelopes"
              ? "bg-coral text-white shadow-lg shadow-coral/25"
              : "bg-navy text-stone hover:bg-navy-mid hover:text-white"
          }`}
        >
          Envelope Trends
        </button>
        <button
          onClick={() => setActiveTab("income")}
          className={`px-6 py-2 rounded-full text-sm font-medium transition-all ${
            activeTab === "income"
              ? "bg-coral text-white shadow-lg shadow-coral/25"
              : "bg-navy text-stone hover:bg-navy-mid hover:text-white"
          }`}
        >
          Income vs Expenses
        </button>
      </div>

      {/* Controls */}
      <div className="flex items-center gap-4 mb-6">
        {/* Month range toggle */}
        <div className="flex gap-1">
          {monthOptions.map((m) => (
            <button
              key={m}
              onClick={() => setMonths(m)}
              className={`px-4 py-1.5 rounded-full text-sm font-medium transition-all ${
                months === m
                  ? "bg-coral text-white"
                  : "bg-navy-deep text-stone hover:bg-navy-mid hover:text-white"
              }`}
            >
              {m}m
            </button>
          ))}
        </div>

        {/* Envelope selector (only on envelopes tab) */}
        {activeTab === "envelopes" && (
          <Select
            value={selectedBudgetId || "__all__"}
            onValueChange={(v) =>
              setSelectedBudgetId(v === "__all__" ? undefined : v)
            }
          >
            <SelectTrigger className="w-[220px] bg-navy-deep border-navy-mid text-white">
              <SelectValue placeholder="All Envelopes" />
            </SelectTrigger>
            <SelectContent className="bg-navy-deep border-navy-mid">
              <SelectItem
                value="__all__"
                className="text-white hover:bg-navy-mid focus:bg-navy-mid"
              >
                All Envelopes
              </SelectItem>
              {budgetOptions.map((name) => (
                <SelectItem
                  key={name}
                  value={name}
                  className="text-white hover:bg-navy-mid focus:bg-navy-mid"
                >
                  {name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}
      </div>

      {activeTab === "envelopes" ? (
        <EnvelopeTrendsView
          chartData={chartData}
          deltas={deltas}
          overBudgetData={overBudgetData || []}
          isLoading={trendsLoading}
        />
      ) : (
        <IncomeView
          chartData={incomeChartData}
          isLoading={incomeLoading}
        />
      )}
    </div>
  );
}

// --------------- Envelope Trends View ---------------

interface EnvelopeTrendsViewProps {
  chartData: Array<{ month: string; spent: number; allocated: number }>;
  deltas: Array<{
    month: string;
    spent: number;
    allocated: number;
    delta: number | null;
  }>;
  overBudgetData: Array<{
    budget_id: string;
    budget_name: string | null;
    group_name: string;
    over_budget_count: number;
    total_periods: number;
    pct_over: number;
    avg_overspend_pence: number;
  }>;
  isLoading: boolean;
}

function EnvelopeTrendsView({
  chartData,
  deltas,
  overBudgetData,
  isLoading,
}: EnvelopeTrendsViewProps) {
  if (isLoading) {
    return (
      <div className="text-center py-12 text-stone">
        Loading trends data...
      </div>
    );
  }

  if (chartData.length === 0) {
    return (
      <Card>
        <CardContent className="text-center py-12">
          <p className="text-stone">
            No trend data available. Create budgets and sync transactions to see
            trends.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Main Chart */}
      <Card>
        <CardHeader>
          <CardTitle>SPENDING VS BUDGET</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={320}>
            <BarChart data={chartData} barGap={4}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2B5278" />
              <XAxis
                dataKey="month"
                stroke="#6B7280"
                fontSize={12}
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
                formatter={(value?: number, name?: string) => [
                  formatCurrency(value ?? 0),
                  name === "spent" ? "Spent" : "Allocated",
                ]}
              />
              <Bar
                dataKey="allocated"
                fill="transparent"
                stroke="#2B5278"
                strokeWidth={2}
                radius={[4, 4, 0, 0]}
                name="allocated"
              />
              <Bar
                dataKey="spent"
                fill="#FF5A5F"
                radius={[4, 4, 0, 0]}
                name="spent"
              />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Month-over-Month Deltas */}
      <div className="flex gap-3 flex-wrap">
        {deltas.map((item) => (
          <div
            key={item.month}
            className="bg-charcoal rounded-xl px-4 py-3 text-center min-w-[90px]"
          >
            <div className="text-xs text-stone mb-1">{item.month}</div>
            <div
              className="text-lg text-white"
              style={{ fontFamily: "var(--font-display)" }}
            >
              {formatCurrency(item.spent)}
            </div>
            {item.delta !== null && (
              <span
                className={`text-xs font-medium ${
                  item.delta <= 0 ? "text-mint" : "text-coral"
                }`}
              >
                {item.delta > 0 ? "+" : ""}
                {item.delta.toFixed(1)}%
              </span>
            )}
          </div>
        ))}
      </div>

      {/* Consistently Over Budget Section */}
      {overBudgetData.length > 0 && (
        <Card className="border border-coral/20">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-coral" />
              CONSISTENTLY OVER BUDGET
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {overBudgetData.map((item) => (
              <div
                key={item.budget_id}
                className="flex items-center justify-between bg-navy rounded-xl px-4 py-3"
              >
                <div>
                  <div className="text-white font-medium">
                    {item.budget_name || item.group_name}
                  </div>
                  <div className="text-sm text-stone">
                    Over {item.over_budget_count} of {item.total_periods} months
                    ({item.pct_over.toFixed(0)}%)
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-coral font-medium">
                    Avg overspend: {formatCurrency(item.avg_overspend_pence)}
                  </div>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// --------------- Income vs Expenses View ---------------

interface IncomeViewProps {
  chartData: Array<{
    month: string;
    income: number;
    expenses: number;
    net: number;
  }>;
  isLoading: boolean;
}

function IncomeView({ chartData, isLoading }: IncomeViewProps) {
  if (isLoading) {
    return (
      <div className="text-center py-12 text-stone">
        Loading income data...
      </div>
    );
  }

  if (chartData.length === 0) {
    return (
      <Card>
        <CardContent className="text-center py-12">
          <p className="text-stone">
            No income data available. Sync transactions to see income vs
            expenses.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Income vs Expenses Chart */}
      <Card>
        <CardHeader>
          <CardTitle>INCOME VS EXPENSES</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={320}>
            <ComposedChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2B5278" />
              <XAxis
                dataKey="month"
                stroke="#6B7280"
                fontSize={12}
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
                formatter={(value?: number, name?: string) => [
                  formatCurrency(value ?? 0),
                  name === "income"
                    ? "Income"
                    : name === "expenses"
                      ? "Expenses"
                      : "Net",
                ]}
              />
              <Bar
                dataKey="income"
                fill="#00D9B5"
                radius={[4, 4, 0, 0]}
                name="income"
              />
              <Bar
                dataKey="expenses"
                fill="#FF5A5F"
                radius={[4, 4, 0, 0]}
                name="expenses"
              />
              <Line
                type="monotone"
                dataKey="net"
                stroke="#FFD93D"
                strokeWidth={2}
                dot={{ fill: "#FFD93D", r: 4 }}
                name="net"
              />
            </ComposedChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Net Position Cards */}
      <div className="flex gap-3 flex-wrap">
        {chartData.map((item) => {
          const isNegative = item.net < 0;
          return (
            <div
              key={item.month}
              className={`bg-charcoal rounded-xl px-4 py-3 text-center min-w-[100px] border ${
                isNegative ? "border-coral/30" : "border-mint/20"
              }`}
            >
              <div className="text-xs text-stone mb-1">{item.month}</div>
              <div
                className={`text-lg ${isNegative ? "text-coral" : "text-mint"}`}
                style={{ fontFamily: "var(--font-display)" }}
              >
                {formatCurrency(item.net)}
              </div>
              <div className="text-xs text-stone">net</div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
