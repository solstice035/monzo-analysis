import { TopBar } from "@/components/layout";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { StatBlock } from "@/components/ui/stat-block";
import { BudgetBar } from "@/components/ui/budget-bar";
import { TransactionRow } from "@/components/ui/transaction-row";
import {
  useTriggerSync,
  useDashboardSummary,
  useDashboardTrends,
  useBudgetStatuses,
  useTransactions,
} from "@/hooks/useApi";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

const categoryEmojis: Record<string, string> = {
  groceries: "🛒",
  eating_out: "🍽️",
  shopping: "🛍️",
  transport: "🚗",
  entertainment: "🎬",
  bills: "📄",
  general: "📦",
  holidays: "✈️",
  cash: "💵",
  expenses: "💼",
};

export function Dashboard() {
  const syncMutation = useTriggerSync();
  const { data: summary, isLoading: summaryLoading } = useDashboardSummary();
  const { data: trends } = useDashboardTrends(30);
  const { data: budgets } = useBudgetStatuses();
  const { data: transactionsData } = useTransactions({ limit: 5 });

  const handleSync = () => {
    syncMutation.mutate();
  };

  // Get current month and days until reset
  const now = new Date();
  const month = now.toLocaleString("en-GB", { month: "long" }).toUpperCase();
  const year = now.getFullYear();
  const daysInMonth = new Date(year, now.getMonth() + 1, 0).getDate();
  const daysUntilReset = daysInMonth - now.getDate();

  // Transform trends data for the chart
  const chartData =
    trends?.daily_spend.map((d) => ({
      date: new Date(d.date).toLocaleDateString("en-GB", {
        day: "numeric",
        month: "short",
      }),
      amount: d.amount / 100,
    })) || [];

  // Calculate stats from real data
  const spendThisMonth = summary?.spend_this_month || 0;
  const balance = summary?.balance || 0;
  const spendToday = summary?.spend_today || 0;
  const transactionCount = summary?.transaction_count || 0;

  // Take top 4 budgets for the dashboard
  const topBudgets = (budgets || []).slice(0, 4);

  // Recent transactions
  const recentTransactions = transactionsData?.items || [];

  return (
    <div>
      <TopBar
        title={`${month} ${year}`}
        subtitle={`Budget resets in ${daysUntilReset} days`}
        onSync={handleSync}
        isSyncing={syncMutation.isPending}
      />

      {/* Stats Row */}
      <div className="grid grid-cols-4 gap-4 mb-8">
        <StatBlock
          label="SPENT THIS MONTH"
          value={formatCurrency(spendThisMonth)}
          change={summaryLoading ? "Loading..." : `${transactionCount} transactions`}
          changeType="neutral"
        />
        <StatBlock
          label="BALANCE"
          value={formatCurrency(balance)}
          change={balance >= 0 ? "POSITIVE" : "NEGATIVE"}
          changeType={balance >= 0 ? "positive" : "negative"}
        />
        <StatBlock
          label="SPENT TODAY"
          value={formatCurrency(spendToday)}
          change={spendToday === 0 ? "NOTHING YET" : ""}
          changeType="neutral"
        />
        <StatBlock
          label="DAILY AVG"
          value={formatCurrency(trends?.average_daily || 0)}
          change="LAST 30 DAYS"
          changeType="neutral"
        />
      </div>

      {/* Spending Trend Chart */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>SPENDING TREND (30 DAYS)</CardTitle>
        </CardHeader>
        <CardContent>
          {chartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="spendGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#FF5A5F" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#FF5A5F" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#2B5278" />
                <XAxis
                  dataKey="date"
                  stroke="#6B7280"
                  fontSize={11}
                  tickLine={false}
                  interval="preserveStartEnd"
                />
                <YAxis
                  stroke="#6B7280"
                  fontSize={11}
                  tickLine={false}
                  tickFormatter={(value) => `£${value}`}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#1B3A5C",
                    border: "1px solid #2B5278",
                    borderRadius: "8px",
                  }}
                  labelStyle={{ color: "#fff" }}
                  formatter={(value) => [`£${Number(value).toFixed(2)}`, "Spent"]}
                />
                <Area
                  type="monotone"
                  dataKey="amount"
                  stroke="#FF5A5F"
                  strokeWidth={2}
                  fill="url(#spendGradient)"
                />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[200px] flex items-center justify-center text-stone">
              No spending data available
            </div>
          )}
        </CardContent>
      </Card>

      <div className="grid grid-cols-2 gap-6">
        {/* Budget Progress */}
        <Card>
          <CardHeader>
            <CardTitle>BUDGET PROGRESS</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {topBudgets.length > 0 ? (
              topBudgets.map((budget) => (
                <BudgetBar
                  key={budget.budget_id}
                  name={budget.category.replace(/_/g, " ")}
                  spent={budget.spent}
                  budget={budget.amount}
                  emoji={categoryEmojis[budget.category] || "📦"}
                />
              ))
            ) : (
              <div className="text-center py-8 text-stone">
                No budgets set. Visit Budgets page to create one.
              </div>
            )}
          </CardContent>
        </Card>

        {/* Recent Transactions */}
        <Card>
          <CardHeader>
            <CardTitle>RECENT TRANSACTIONS</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {recentTransactions.length > 0 ? (
              recentTransactions.map((tx) => (
                <TransactionRow
                  key={tx.id}
                  merchant={tx.merchant_name || "Unknown"}
                  category={tx.custom_category || tx.monzo_category || "general"}
                  amount={tx.amount}
                  date={tx.created_at}
                />
              ))
            ) : (
              <div className="text-center py-8 text-stone">
                No transactions yet. Sync to fetch data.
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Top Categories */}
      {summary?.top_categories && summary.top_categories.length > 0 && (
        <Card className="mt-6">
          <CardHeader>
            <CardTitle>TOP SPENDING CATEGORIES</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-5 gap-4">
              {summary.top_categories.map((cat) => (
                <div
                  key={cat.category}
                  className="bg-navy rounded-xl p-4 text-center"
                >
                  <div className="text-2xl mb-2">
                    {categoryEmojis[cat.category] || "📦"}
                  </div>
                  <div className="text-sm text-stone capitalize mb-1">
                    {cat.category.replace(/_/g, " ")}
                  </div>
                  <div
                    className="text-lg text-white"
                    style={{ fontFamily: "var(--font-display)" }}
                  >
                    {formatCurrency(cat.amount)}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function formatCurrency(pence: number): string {
  const pounds = Math.abs(pence) / 100;
  return `£${pounds.toLocaleString("en-GB", {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  })}`;
}
