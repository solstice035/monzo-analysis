import { cn, formatCurrency } from "@/lib/utils";
import { SpendSparkline } from "./spend-sparkline";
import { TransactionRowV2 } from "./transaction-row-v2";
import { getCategoryIcon } from "@/lib/category-icons";
import {
  useDashboardSummary,
  useDashboardTrends,
  useTransactions,
  useUpdateTransaction,
  useBudgetGroupStatuses,
} from "@/hooks/useApi";

export interface ContextPanelProps {
  selectedCategory: string | null;
  className?: string;
}

export function ContextPanel({ selectedCategory, className }: ContextPanelProps) {
  return (
    <div
      className={cn(
        "rounded-xl border border-navy-mid bg-charcoal overflow-hidden h-full",
        className
      )}
    >
      {selectedCategory ? (
        <CategoryDetail category={selectedCategory} />
      ) : (
        <OverviewPanel />
      )}
    </div>
  );
}

// --- Overview Panel (nothing selected) ---

function OverviewPanel() {
  const { data: summary } = useDashboardSummary();
  const { data: trends } = useDashboardTrends(30);

  const chartData =
    trends?.daily_spend.map((d) => ({
      period: new Date(d.date).toLocaleDateString("en-GB", {
        day: "numeric",
        month: "short",
      }),
      amount: d.amount,
    })) || [];

  return (
    <div className="p-5 space-y-6">
      <div>
        <h3 className="text-xs text-stone uppercase tracking-wider mb-1">
          Monthly Overview
        </h3>
        <div
          className="text-3xl text-white"
          style={{ fontFamily: "var(--font-display)" }}
        >
          {formatCurrency(summary?.spend_this_month || 0)}
        </div>
        <div className="text-xs text-stone mt-1">
          spent this month · {summary?.transaction_count || 0} transactions
        </div>
      </div>

      {/* Spending trend */}
      <div>
        <h4 className="text-xs text-stone uppercase tracking-wider mb-2">
          30-Day Trend
        </h4>
        <SpendSparkline data={chartData} height={100} />
      </div>

      {/* Top categories */}
      {summary?.top_categories && summary.top_categories.length > 0 && (
        <div>
          <h4 className="text-xs text-stone uppercase tracking-wider mb-3">
            Top Categories
          </h4>
          <div className="space-y-1">
            {summary.top_categories.slice(0, 5).map((cat) => {
              const Icon = getCategoryIcon(cat.category);
              return (
                <div
                  key={cat.category}
                  className="flex items-center gap-3 px-3 py-2 rounded-lg bg-navy/50"
                >
                  <Icon size={14} strokeWidth={1.5} className="text-stone" />
                  <span className="text-sm text-white capitalize flex-1">
                    {cat.category.replace(/_/g, " ")}
                  </span>
                  <span
                    className="text-sm text-coral tabular-nums"
                    style={{ fontFamily: "var(--font-mono)" }}
                  >
                    {formatCurrency(cat.amount)}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Daily average */}
      {trends?.average_daily !== undefined && (
        <div className="pt-4 border-t border-navy-mid">
          <div className="flex items-center justify-between">
            <span className="text-xs text-stone">Daily average</span>
            <span
              className="text-sm text-white"
              style={{ fontFamily: "var(--font-mono)" }}
            >
              {formatCurrency(trends.average_daily)}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}

// --- Category Detail Panel ---

interface CategoryDetailProps {
  category: string;
}

function CategoryDetail({ category }: CategoryDetailProps) {
  const { data: budgetGroups } = useBudgetGroupStatuses();
  const updateTransaction = useUpdateTransaction();

  // Find the budget for this category from the groups
  let budgetInfo: { amount: number; spent: number; remaining: number; status: string } | null = null;
  if (budgetGroups) {
    for (const group of budgetGroups) {
      const found = group.budgets.find((b) => b.category === category);
      if (found) {
        budgetInfo = found;
        break;
      }
    }
  }

  // Fetch transactions for this category
  const { data: transactionsData } = useTransactions({
    category,
    limit: 20,
  });

  const transactions = transactionsData?.items || [];
  const Icon = getCategoryIcon(category);
  const displayName = category.replace(/_/g, " ");

  const isOver = budgetInfo ? budgetInfo.spent > budgetInfo.amount : false;
  const isWarning = budgetInfo
    ? budgetInfo.amount > 0 && (budgetInfo.spent / budgetInfo.amount) * 100 >= 80 && !isOver
    : false;

  const statusColor = isOver ? "text-coral" : isWarning ? "text-yellow" : "text-mint";

  const handleCategoryChange = (txId: string, newCategory: string) => {
    updateTransaction.mutate({
      id: txId,
      data: { custom_category: newCategory },
    });
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-5 border-b border-navy-mid">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-8 h-8 rounded-lg bg-navy-mid/30 flex items-center justify-center">
            <Icon size={18} strokeWidth={1.5} className="text-white" />
          </div>
          <h3
            className="text-xl text-white capitalize"
            style={{ fontFamily: "var(--font-display)" }}
          >
            {displayName.toUpperCase()}
          </h3>
        </div>

        {/* Budget stats */}
        {budgetInfo && (
          <div className="grid grid-cols-3 gap-3">
            <div className="bg-navy/50 rounded-lg p-2.5 text-center">
              <div className="text-xs text-stone mb-1">Budgeted</div>
              <div
                className="text-sm text-white"
                style={{ fontFamily: "var(--font-mono)" }}
              >
                {formatCurrency(budgetInfo.amount)}
              </div>
            </div>
            <div className="bg-navy/50 rounded-lg p-2.5 text-center">
              <div className="text-xs text-stone mb-1">Spent</div>
              <div
                className="text-sm text-coral"
                style={{ fontFamily: "var(--font-mono)" }}
              >
                {formatCurrency(budgetInfo.spent)}
              </div>
            </div>
            <div className="bg-navy/50 rounded-lg p-2.5 text-center">
              <div className="text-xs text-stone mb-1">Available</div>
              <div
                className={cn("text-sm font-semibold", statusColor)}
                style={{ fontFamily: "var(--font-mono)" }}
              >
                {isOver ? "-" : ""}
                {formatCurrency(Math.abs(budgetInfo.remaining))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Transaction list */}
      <div className="flex-1 overflow-y-auto">
        <div className="px-5 py-3 border-b border-navy-mid/50">
          <h4 className="text-xs text-stone uppercase tracking-wider">
            Transactions ({transactions.length})
          </h4>
        </div>

        {transactions.length === 0 ? (
          <div className="p-5 text-center text-sm text-stone">
            No transactions in this category this period.
          </div>
        ) : (
          <div>
            {transactions.map((tx) => (
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
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
