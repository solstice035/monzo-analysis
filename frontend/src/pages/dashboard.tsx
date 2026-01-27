import { useState } from "react";
import { TopBar } from "@/components/layout";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { StatBlock } from "@/components/ui/stat-block";
import { BudgetBar } from "@/components/ui/budget-bar";
import { BudgetGroupCard } from "@/components/ui/budget-group-card";
import { SinkingFundCard } from "@/components/ui/sinking-fund-card";
import { TransactionRow } from "@/components/ui/transaction-row";
import {
  useTriggerSync,
  useDashboardSummary,
  useDashboardTrends,
  useBudgetStatuses,
  useBudgetGroupStatuses,
  useSinkingFundsStatus,
  useTransactions,
} from "@/hooks/useApi";
import { formatCurrency } from "@/lib/utils";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

type TabType = "budget" | "analytics";

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
  const [activeTab, setActiveTab] = useState<TabType>("budget");

  const syncMutation = useTriggerSync();
  const { data: summary, isLoading: summaryLoading } = useDashboardSummary();
  const { data: trends } = useDashboardTrends(30);
  const { data: budgets } = useBudgetStatuses();
  const { data: budgetGroups, isLoading: groupsLoading } = useBudgetGroupStatuses();
  const { data: sinkingFunds } = useSinkingFundsStatus();
  const { data: transactionsData } = useTransactions({ limit: 5 });

  const handleSync = () => {
    syncMutation.mutate();
  };

  // Get current month and days until reset
  const now = new Date();
  const month = now.toLocaleString("en-GB", { month: "long" }).toUpperCase();
  const year = now.getFullYear();
  const daysInMonth = new Date(year, now.getMonth() + 1, 0).getDate();
  const dayOfMonth = now.getDate();
  const daysUntilReset = daysInMonth - dayOfMonth;

  // Calculate totals from budget groups
  const totalBudget = budgetGroups?.reduce((sum, g) => sum + g.total_budget, 0) || 0;
  const totalSpent = budgetGroups?.reduce((sum, g) => sum + g.total_spent, 0) || 0;
  const totalRemaining = totalBudget - totalSpent;
  const totalPercentage = totalBudget > 0 ? (totalSpent / totalBudget) * 100 : 0;

  return (
    <div>
      <TopBar
        title={`${month} ${year}`}
        subtitle={`Day ${dayOfMonth} of ${daysInMonth} · ${daysUntilReset} days until reset`}
        onSync={handleSync}
        isSyncing={syncMutation.isPending}
      />

      {/* Tab Buttons */}
      <div className="flex gap-2 mb-6">
        <button
          onClick={() => setActiveTab("budget")}
          className={`px-6 py-2 rounded-full text-sm font-medium transition-all ${
            activeTab === "budget"
              ? "bg-coral text-white shadow-lg shadow-coral/25"
              : "bg-navy text-stone hover:bg-navy-mid hover:text-white"
          }`}
        >
          Budget
        </button>
        <button
          onClick={() => setActiveTab("analytics")}
          className={`px-6 py-2 rounded-full text-sm font-medium transition-all ${
            activeTab === "analytics"
              ? "bg-coral text-white shadow-lg shadow-coral/25"
              : "bg-navy text-stone hover:bg-navy-mid hover:text-white"
          }`}
        >
          Analytics
        </button>
      </div>

      {activeTab === "budget" ? (
        <BudgetTab
          budgetGroups={budgetGroups || []}
          sinkingFunds={sinkingFunds || []}
          totalBudget={totalBudget}
          totalSpent={totalSpent}
          totalRemaining={totalRemaining}
          totalPercentage={totalPercentage}
          dayOfMonth={dayOfMonth}
          daysInMonth={daysInMonth}
          isLoading={groupsLoading}
        />
      ) : (
        <AnalyticsTab
          summary={summary}
          summaryLoading={summaryLoading}
          trends={trends}
          budgets={budgets || []}
          transactions={transactionsData?.items || []}
        />
      )}
    </div>
  );
}

interface BudgetTabProps {
  budgetGroups: ReturnType<typeof useBudgetGroupStatuses>["data"];
  sinkingFunds: ReturnType<typeof useSinkingFundsStatus>["data"];
  totalBudget: number;
  totalSpent: number;
  totalRemaining: number;
  totalPercentage: number;
  dayOfMonth: number;
  daysInMonth: number;
  isLoading: boolean;
}

function BudgetTab({
  budgetGroups,
  sinkingFunds,
  totalBudget,
  totalSpent,
  totalRemaining,
  totalPercentage,
  dayOfMonth,
  daysInMonth,
  isLoading,
}: BudgetTabProps) {
  const isOver = totalSpent > totalBudget;
  const isWarning = totalPercentage >= 80 && !isOver;
  const expectedPercentage = (dayOfMonth / daysInMonth) * 100;
  const onTrack = totalPercentage <= expectedPercentage + 10;

  return (
    <div className="space-y-6">
      {/* Total Budget Summary Card */}
      <Card className="border-2 border-coral/30 bg-gradient-to-r from-charcoal to-navy-deep">
        <CardContent className="p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-stone text-sm mb-1">TOTAL BUDGET</h2>
              <div
                className="text-4xl text-white"
                style={{ fontFamily: "var(--font-display)" }}
              >
                {formatCurrency(totalSpent)} / {formatCurrency(totalBudget)}
              </div>
            </div>
            <div className="text-right">
              <div
                className={`text-3xl ${isOver ? "text-coral" : isWarning ? "text-yellow" : "text-mint"}`}
                style={{ fontFamily: "var(--font-display)" }}
              >
                {totalPercentage.toFixed(0)}%
              </div>
              <div className="text-stone text-sm">
                {isOver
                  ? `${formatCurrency(Math.abs(totalRemaining))} over`
                  : `${formatCurrency(totalRemaining)} remaining`}
              </div>
            </div>
          </div>

          {/* Progress bar */}
          <div className="h-4 bg-navy rounded-full overflow-hidden mb-2">
            <div
              className={`h-full rounded-full transition-all duration-500 ${
                isOver
                  ? "bg-gradient-to-r from-coral-deep to-coral"
                  : isWarning
                  ? "bg-gradient-to-r from-yellow to-[#FFE566]"
                  : "bg-gradient-to-r from-mint to-[#00FFD4]"
              }`}
              style={{ width: `${Math.min(totalPercentage, 100)}%` }}
            />
          </div>

          {/* Expected progress marker */}
          <div className="flex justify-between text-xs text-stone">
            <span>{dayOfMonth} days elapsed</span>
            <span
              className={onTrack ? "text-mint" : "text-coral"}
            >
              {onTrack ? "On track" : "Ahead of budget pace"}
            </span>
          </div>
        </CardContent>
      </Card>

      {/* Budget Groups Grid */}
      {isLoading ? (
        <div className="text-center py-12 text-stone">Loading budget groups...</div>
      ) : budgetGroups && budgetGroups.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {budgetGroups.map((group) => (
            <BudgetGroupCard
              key={group.group_id}
              group={group}
              categoryEmojis={categoryEmojis}
            />
          ))}
        </div>
      ) : (
        <Card>
          <CardContent className="text-center py-12">
            <p className="text-stone mb-4">No budget groups configured yet.</p>
            <p className="text-sm text-stone/70">
              Visit the Budgets page to create budget groups and track your spending.
            </p>
          </CardContent>
        </Card>
      )}

      {/* Sinking Funds Section */}
      {sinkingFunds && sinkingFunds.length > 0 && (
        <div className="mt-8">
          <h2
            className="text-xl text-white mb-4"
            style={{ fontFamily: "var(--font-display)" }}
          >
            SINKING FUNDS
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {sinkingFunds.map((fund) => (
              <SinkingFundCard key={fund.budget_id} fund={fund} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

interface AnalyticsTabProps {
  summary: ReturnType<typeof useDashboardSummary>["data"];
  summaryLoading: boolean;
  trends: ReturnType<typeof useDashboardTrends>["data"];
  budgets: ReturnType<typeof useBudgetStatuses>["data"];
  transactions: { id: string; merchant_name?: string; custom_category?: string; monzo_category?: string; amount: number; created_at: string }[];
}

function AnalyticsTab({
  summary,
  summaryLoading,
  trends,
  budgets,
  transactions,
}: AnalyticsTabProps) {
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

  // Take top 4 budgets for display
  const topBudgets = (budgets || []).slice(0, 4);

  return (
    <div>
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
            {transactions.length > 0 ? (
              transactions.map((tx) => (
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
