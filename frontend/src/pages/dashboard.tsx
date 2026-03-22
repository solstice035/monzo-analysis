import { useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { AreaChart, Area, ResponsiveContainer, Tooltip } from "recharts";
import { TopBar } from "@/components/layout";
import { MonthSummaryBar } from "@/components/ui/month-summary-bar";
import { CashFlowWidget } from "@/components/ui/cash-flow-widget";
import { BudgetTableNew } from "@/components/budget-table";
import { TransactionRowV2 } from "@/components/ui/transaction-row-v2";
import {
  useDashboardSummary,
  useDashboardTrends,
  useBudgetGroupStatuses,
  useTransactions,
  useUpdateTransaction,
} from "@/hooks/useApi";

export function Dashboard() {
  const navigate = useNavigate();
  const { data: summary } = useDashboardSummary();
  const { data: trends } = useDashboardTrends(30);
  const { data: budgetGroups } = useBudgetGroupStatuses();
  const { data: recentTx } = useTransactions({ limit: 5 });
  const updateTransaction = useUpdateTransaction();

  // Compute budget summary
  const budgetSummary = useMemo(() => {
    if (!budgetGroups) return { spent: 0, budget: 0, remaining: 0 };
    return budgetGroups.reduce(
      (acc, g) => ({
        spent: acc.spent + g.total_spent,
        budget: acc.budget + g.total_budget,
        remaining: acc.remaining + g.remaining,
      }),
      { spent: 0, budget: 0, remaining: 0 }
    );
  }, [budgetGroups]);

  const now = new Date();
  const currentDay = now.getDate();
  const totalDays = new Date(now.getFullYear(), now.getMonth() + 1, 0).getDate();

  // Chart data
  const chartData = useMemo(() => {
    if (!trends?.daily_spend) return [];
    return trends.daily_spend.map((d) => ({
      date: new Date(d.date).toLocaleDateString("en-GB", { day: "numeric", month: "short" }),
      amount: d.amount / 100,
    }));
  }, [trends]);

  const recentTransactions = recentTx?.items || [];

  // Income approximation: use balance as proxy if available
  const income = summary?.balance ?? 0;
  const spent = summary?.spend_this_month ?? budgetSummary.spent;

  const handleCategoryChange = (txId: string, newCategory: string) => {
    updateTransaction.mutate({
      id: txId,
      data: { custom_category: newCategory },
    });
  };

  return (
    <div>
      <TopBar
        title="DASHBOARD"
        subtitle={`Day ${currentDay} of ${totalDays} · ${totalDays - currentDay} days remaining`}
      />

      {/* Month Summary Bar */}
      <MonthSummaryBar
        totalSpent={budgetSummary.spent}
        totalBudget={budgetSummary.budget}
        totalRemaining={budgetSummary.remaining}
        currentDay={currentDay}
        totalDays={totalDays}
        className="mb-6"
      />

      {/* Two-column: Cash Flow + Recent Transactions */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <CashFlowWidget income={income} spent={spent} />

        {/* Recent Transactions */}
        <div className="bg-charcoal rounded-xl border border-navy-mid overflow-hidden">
          <div className="flex items-center justify-between px-4 py-3 border-b border-navy-mid">
            <h3 className="text-xs text-stone uppercase tracking-wider">
              Recent Transactions
            </h3>
            <button
              onClick={() => navigate("/transactions")}
              className="text-xs text-coral hover:text-coral-bright transition-colors"
            >
              View all →
            </button>
          </div>
          <div>
            {recentTransactions.length === 0 ? (
              <div className="text-center py-6 text-sm text-stone">
                No recent transactions
              </div>
            ) : (
              recentTransactions.map((tx) => (
                <TransactionRowV2
                  key={tx.id}
                  id={tx.id}
                  merchant={tx.merchant_name || "Unknown"}
                  category={tx.custom_category || tx.monzo_category || "general"}
                  amount={tx.amount}
                  date={tx.created_at}
                  onCategoryChange={handleCategoryChange}
                  compact
                />
              ))
            )}
          </div>
        </div>
      </div>

      {/* Budget Overview — read-only, top 2 groups */}
      <div className="mb-6">
        <h3 className="text-xs text-stone uppercase tracking-wider mb-3">
          Budget Overview
        </h3>
        <BudgetTableNew readOnly maxGroups={2} />
        {budgetGroups && budgetGroups.length > 2 && (
          <button
            onClick={() => navigate("/budgets")}
            className="mt-2 text-xs text-coral hover:text-coral-bright transition-colors"
          >
            View all {budgetGroups.length} groups →
          </button>
        )}
      </div>

      {/* Spending Trend Chart */}
      {chartData.length > 0 && (
        <div>
          <h3 className="text-xs text-stone uppercase tracking-wider mb-3">
            Spending Trend — Last 30 Days
          </h3>
          <div className="bg-charcoal rounded-xl border border-navy-mid p-4">
            <ResponsiveContainer width="100%" height={150}>
              <AreaChart data={chartData} margin={{ top: 2, right: 2, bottom: 2, left: 2 }}>
                <defs>
                  <linearGradient id="dashGradient" x1="0" y1="0" x2="0" y2="1">
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
                  formatter={(value: number | undefined) => [
                    `£${(value ?? 0).toFixed(2)}`,
                    "Spent",
                  ]}
                />
                <Area
                  type="monotone"
                  dataKey="amount"
                  stroke="#FF5A5F"
                  strokeWidth={2}
                  fill="url(#dashGradient)"
                  dot={false}
                  activeDot={{ r: 3, fill: "#FF5A5F", stroke: "#fff", strokeWidth: 1 }}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  );
}
