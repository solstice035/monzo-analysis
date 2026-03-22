import { useState, useMemo } from "react";
import { TopBar } from "@/components/layout";
import { TransactionFilterBar } from "@/components/ui/transaction-filter-bar";
import { DateGroupHeader } from "@/components/ui/date-group-header";
import { InlineCategoryEdit } from "@/components/ui/inline-category-edit";
import { getCategoryIcon } from "@/lib/category-icons";
import { cn, formatCurrency, formatRelativeDate } from "@/lib/utils";
import { useTransactions, useUpdateTransaction, useCreateRule } from "@/hooks/useApi";
import { useAccount } from "@/contexts/AccountContext";
import { Button } from "@/components/ui/button";

const PAGE_SIZE = 50;

function getMonthRange(offset: number) {
  const d = new Date();
  d.setMonth(d.getMonth() + offset);
  const year = d.getFullYear();
  const month = d.getMonth();
  const start = new Date(year, month, 1);
  const end = new Date(year, month + 1, 0, 23, 59, 59);
  return {
    since: start.toISOString(),
    until: end.toISOString(),
    label: start.toLocaleDateString("en-GB", { month: "long", year: "numeric" }),
  };
}

function getDateGroupLabel(dateStr: string): string {
  const txDate = new Date(dateStr);
  const today = new Date();
  const yesterday = new Date();
  yesterday.setDate(yesterday.getDate() - 1);

  const isSameDay = (a: Date, b: Date) =>
    a.getDate() === b.getDate() &&
    a.getMonth() === b.getMonth() &&
    a.getFullYear() === b.getFullYear();

  if (isSameDay(txDate, today)) return "Today";
  if (isSameDay(txDate, yesterday)) return "Yesterday";

  return txDate.toLocaleDateString("en-GB", {
    weekday: "short",
    day: "numeric",
    month: "long",
  });
}

interface GroupedTransactions {
  label: string;
  total: number;
  transactions: Array<{
    id: string;
    merchant_name?: string | null;
    monzo_category?: string | null;
    custom_category?: string | null;
    amount: number;
    created_at: string;
  }>;
}

export function Transactions() {
  const { selectedAccount } = useAccount();
  const [selectedCategory, setSelectedCategory] = useState<string>("All");
  const [searchQuery, setSearchQuery] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [monthOffset, setMonthOffset] = useState(0);
  const [pageOffset, setPageOffset] = useState(0);

  const updateTransaction = useUpdateTransaction();
  const createRule = useCreateRule();

  const handleSearchChange = (value: string) => {
    setSearchQuery(value);
    setPageOffset(0);
    clearTimeout((window as any).__searchTimeout);
    (window as any).__searchTimeout = setTimeout(() => {
      setDebouncedSearch(value);
    }, 300);
  };

  const monthRange = useMemo(() => getMonthRange(monthOffset), [monthOffset]);

  const { data, isLoading, error } = useTransactions({
    category: selectedCategory === "All" ? undefined : selectedCategory,
    search: debouncedSearch || undefined,
    since: monthRange.since,
    until: monthRange.until,
    limit: PAGE_SIZE,
    offset: pageOffset,
  });

  const transactions = data?.items || [];
  const total = data?.total || 0;
  const hasMore = pageOffset + PAGE_SIZE < total;

  // Group transactions by date
  const groupedTransactions = useMemo((): GroupedTransactions[] => {
    const groups: Map<string, GroupedTransactions> = new Map();

    for (const tx of transactions) {
      const label = getDateGroupLabel(tx.created_at);
      if (!groups.has(label)) {
        groups.set(label, { label, total: 0, transactions: [] });
      }
      const group = groups.get(label)!;
      group.transactions.push(tx);
      group.total += tx.amount;
    }

    return Array.from(groups.values());
  }, [transactions]);

  const handleCategoryChange = (txId: string, newCategory: string) => {
    updateTransaction.mutate({
      id: txId,
      data: { custom_category: newCategory },
    });
  };

  const handleCreateRule = (merchant: string, category: string) => {
    if (!selectedAccount) return;
    createRule.mutate({
      account_id: selectedAccount.id,
      name: `Auto: ${merchant} → ${category}`,
      conditions: { merchant_name: merchant },
      target_category: category,
      priority: 0,
      enabled: true,
    });
  };

  const handlePrevMonth = () => {
    setMonthOffset((m) => m - 1);
    setPageOffset(0);
  };

  const handleNextMonth = () => {
    if (monthOffset < 0) {
      setMonthOffset((m) => m + 1);
      setPageOffset(0);
    }
  };

  return (
    <div>
      <TopBar
        title="TRANSACTIONS"
        subtitle={`${total} transactions${selectedCategory !== "All" ? ` in ${selectedCategory.replace(/_/g, " ")}` : ""}`}
        showSync={false}
      />

      {/* Compact filter bar */}
      <TransactionFilterBar
        monthLabel={monthRange.label}
        monthOffset={monthOffset}
        onPrevMonth={handlePrevMonth}
        onNextMonth={handleNextMonth}
        searchQuery={searchQuery}
        onSearchChange={handleSearchChange}
        selectedCategory={selectedCategory}
        onCategoryChange={(cat) => {
          setSelectedCategory(cat);
          setPageOffset(0);
        }}
      />

      {/* Transaction list — date-grouped, no card wrapper */}
      <div className="rounded-xl border border-navy-mid overflow-hidden bg-navy">
        {isLoading && (
          <div className="text-center py-12 text-stone">Loading transactions...</div>
        )}
        {error && (
          <div className="text-center py-12 text-coral">
            Failed to load transactions.
          </div>
        )}

        {!isLoading && !error && groupedTransactions.length === 0 && (
          <div className="text-center py-12 text-stone">
            No transactions found
            {selectedCategory !== "All"
              ? ` in ${selectedCategory.replace(/_/g, " ")}`
              : ""}
            .
          </div>
        )}

        {groupedTransactions.map((group) => (
          <div key={group.label}>
            <DateGroupHeader label={group.label} dayTotal={group.total} />

            {group.transactions.map((tx) => {
              const category = tx.custom_category || tx.monzo_category || "general";
              const Icon = getCategoryIcon(category);
              const isExpense = tx.amount < 0;

              return (
                <div
                  key={tx.id}
                  className="grid items-center py-2 px-3 border-b border-navy-mid/20 hover:bg-navy-deep/20 transition-colors group"
                  style={{ gridTemplateColumns: "28px 1fr auto" }}
                >
                  {/* Icon */}
                  <div className="w-7 h-7 rounded-lg bg-navy-mid/30 flex items-center justify-center">
                    <Icon size={14} strokeWidth={1.5} className="text-stone" />
                  </div>

                  {/* Merchant + category */}
                  <div className="pl-3 min-w-0">
                    <div className="text-sm font-medium text-white truncate">
                      {tx.merchant_name || "Unknown"}
                    </div>
                    <div className="text-xs text-stone flex items-center gap-1.5">
                      <InlineCategoryEdit
                        category={category}
                        merchant={tx.merchant_name || undefined}
                        onSave={(cat) => handleCategoryChange(tx.id, cat)}
                        onCreateRule={handleCreateRule}
                      />
                      <span className="text-navy-mid">·</span>
                      <span>{formatRelativeDate(tx.created_at)}</span>
                    </div>
                  </div>

                  {/* Amount */}
                  <div
                    className={cn(
                      "text-sm font-medium tabular-nums pl-4",
                      isExpense ? "text-coral" : "text-mint"
                    )}
                    style={{ fontFamily: "var(--font-mono)" }}
                  >
                    {isExpense ? "-" : "+"}
                    {formatCurrency(Math.abs(tx.amount))}
                  </div>
                </div>
              );
            })}
          </div>
        ))}

        {/* Load more */}
        {hasMore && (
          <div className="text-center py-4 border-t border-navy-mid">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPageOffset((o) => o + PAGE_SIZE)}
              disabled={isLoading}
            >
              Load more ({total - pageOffset - PAGE_SIZE} remaining)
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
