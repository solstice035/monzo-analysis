import { useState, useMemo } from "react";
import { TopBar } from "@/components/layout";
import { TransactionRowV2 } from "@/components/ui/transaction-row-v2";
import { useTransactions, useUpdateTransaction } from "@/hooks/useApi";
import { Button } from "@/components/ui/button";

const categories = [
  "All",
  "groceries",
  "eating_out",
  "transport",
  "shopping",
  "entertainment",
  "bills",
];

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

  if (isSameDay(txDate, today)) return "TODAY";
  if (isSameDay(txDate, yesterday)) return "YESTERDAY";

  return txDate
    .toLocaleDateString("en-GB", {
      weekday: "short",
      day: "numeric",
      month: "long",
    })
    .toUpperCase();
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
  const [selectedCategory, setSelectedCategory] = useState<string>("All");
  const [searchQuery, setSearchQuery] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [monthOffset, setMonthOffset] = useState(0);
  const [pageOffset, setPageOffset] = useState(0);

  const updateTransaction = useUpdateTransaction();

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

      {/* Search */}
      <div className="mb-4">
        <input
          type="text"
          placeholder="Search by merchant..."
          value={searchQuery}
          onChange={(e) => handleSearchChange(e.target.value)}
          className="w-full px-4 py-2 rounded-xl bg-navy-deep border border-navy-mid text-white placeholder-stone focus:outline-none focus:border-coral transition-colors"
        />
      </div>

      {/* Month navigation */}
      <div className="flex items-center justify-between mb-4">
        <button
          onClick={handlePrevMonth}
          className="px-3 py-1 rounded-lg bg-navy-mid text-stone hover:text-white transition-colors"
        >
          ← Prev
        </button>
        <span
          className="text-white text-lg"
          style={{ fontFamily: "var(--font-display)" }}
        >
          {monthRange.label}
        </span>
        <button
          onClick={handleNextMonth}
          disabled={monthOffset >= 0}
          className={`px-3 py-1 rounded-lg bg-navy-mid transition-colors ${
            monthOffset >= 0 ? "text-navy-mid cursor-not-allowed" : "text-stone hover:text-white"
          }`}
        >
          Next →
        </button>
      </div>

      {/* Category filters */}
      <div className="flex gap-2 mb-6 flex-wrap">
        {categories.map((cat) => (
          <button
            key={cat}
            onClick={() => {
              setSelectedCategory(cat);
              setPageOffset(0);
            }}
            className={`px-4 py-1.5 rounded-full text-sm font-medium transition-all capitalize ${
              cat === selectedCategory
                ? "bg-coral text-white"
                : "bg-navy-mid text-stone hover:text-white hover:bg-navy-deep"
            }`}
          >
            {cat === "All" ? "All" : cat.replace(/_/g, " ")}
          </button>
        ))}
      </div>

      {/* Transaction list — date-grouped, full-width */}
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
            {/* Date group header */}
            <div className="flex items-center justify-between px-4 py-2 bg-charcoal/60 border-b border-navy-mid sticky top-0 z-10">
              <span className="text-xs font-bold text-stone uppercase tracking-wider">
                {group.label}
              </span>
              <span
                className="text-xs text-stone tabular-nums"
                style={{ fontFamily: "var(--font-mono)" }}
              >
                {group.total < 0 ? "-" : "+"}£
                {(Math.abs(group.total) / 100).toFixed(2)}
              </span>
            </div>

            {/* Transactions in this date group */}
            {group.transactions.map((tx) => (
              <TransactionRowV2
                key={tx.id}
                id={tx.id}
                merchant={tx.merchant_name || "Unknown"}
                category={tx.custom_category || tx.monzo_category || "general"}
                amount={tx.amount}
                date={tx.created_at}
                onCategoryChange={handleCategoryChange}
              />
            ))}
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
