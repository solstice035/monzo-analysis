import { useState, useMemo } from "react";
import { TopBar } from "@/components/layout";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { TransactionRow } from "@/components/ui/transaction-row";
import { useTransactions, useUpdateTransaction } from "@/hooks/useApi";
import { formatCurrency } from "@/lib/utils";

const categories = [
  "All",
  "groceries",
  "eating_out",
  "transport",
  "shopping",
  "entertainment",
  "bills",
];

const allCategories = [
  "groceries",
  "eating_out",
  "transport",
  "shopping",
  "entertainment",
  "bills",
  "general",
  "cash",
  "expenses",
  "holidays",
];

interface Transaction {
  id: string;
  merchant_name?: string | null;
  monzo_category?: string | null;
  custom_category?: string | null;
  amount: number;
  created_at: string;
}

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

export function Transactions() {
  const [selectedCategory, setSelectedCategory] = useState<string>("All");
  const [searchQuery, setSearchQuery] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [monthOffset, setMonthOffset] = useState(0);
  const [pageOffset, setPageOffset] = useState(0);
  const [editingTx, setEditingTx] = useState<Transaction | null>(null);
  const [newCategory, setNewCategory] = useState<string>("");

  // Debounce search input
  const handleSearchChange = (value: string) => {
    setSearchQuery(value);
    setPageOffset(0);
    // Simple debounce using setTimeout
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
  const updateTransaction = useUpdateTransaction();

  const transactions = data?.items || [];
  const total = data?.total || 0;
  const hasMore = pageOffset + PAGE_SIZE < total;

  const handleTransactionClick = (tx: Transaction) => {
    setEditingTx(tx);
    setNewCategory(tx.custom_category || tx.monzo_category || "general");
  };

  const handleSaveCategory = async () => {
    if (!editingTx) return;

    await updateTransaction.mutateAsync({
      id: editingTx.id,
      data: { custom_category: newCategory },
    });
    setEditingTx(null);
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
          &larr; Prev
        </button>
        <span className="text-white font-display text-lg">{monthRange.label}</span>
        <button
          onClick={handleNextMonth}
          disabled={monthOffset >= 0}
          className={`px-3 py-1 rounded-lg bg-navy-mid transition-colors ${
            monthOffset >= 0 ? "text-navy-mid cursor-not-allowed" : "text-stone hover:text-white"
          }`}
        >
          Next &rarr;
        </button>
      </div>

      {/* Category filters */}
      <div className="flex gap-3 mb-6 flex-wrap">
        {categories.map((cat) => (
          <button
            key={cat}
            onClick={() => {
              setSelectedCategory(cat);
              setPageOffset(0);
            }}
            className={`px-4 py-2 rounded-full text-sm font-semibold transition-all ${
              cat === selectedCategory
                ? "bg-coral text-white"
                : "bg-navy-mid text-stone hover:text-white hover:bg-navy-deep"
            }`}
          >
            {cat === "All" ? "All" : cat.replace(/_/g, " ")}
          </button>
        ))}
      </div>

      {/* Transactions List */}
      <Card>
        <CardHeader>
          <CardTitle>
            {selectedCategory === "All" ? "ALL TRANSACTIONS" : selectedCategory.toUpperCase().replace(/_/g, " ")}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {isLoading && (
            <div className="text-center py-8 text-stone">Loading transactions...</div>
          )}
          {error && (
            <div className="text-center py-8 text-coral">
              Failed to load transactions. Please try again.
            </div>
          )}
          {!isLoading && !error && transactions.length === 0 && (
            <div className="text-center py-8 text-stone">
              No transactions found{selectedCategory !== "All" ? ` in ${selectedCategory.replace(/_/g, " ")}` : ""}.
            </div>
          )}
          {transactions.map((tx) => (
            <TransactionRow
              key={tx.id}
              merchant={tx.merchant_name || "Unknown"}
              category={tx.custom_category || tx.monzo_category || "general"}
              amount={tx.amount}
              date={tx.created_at}
              onClick={() => handleTransactionClick(tx)}
            />
          ))}

          {/* Load more */}
          {hasMore && (
            <div className="text-center pt-4">
              <Button
                variant="outline"
                onClick={() => setPageOffset((o) => o + PAGE_SIZE)}
                disabled={isLoading}
              >
                Load more ({total - pageOffset - PAGE_SIZE} remaining)
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Category Override Dialog */}
      <Dialog open={!!editingTx} onOpenChange={(open) => !open && setEditingTx(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Change Category</DialogTitle>
            <DialogDescription>
              {editingTx && (
                <>
                  <span className="font-medium text-white">{editingTx.merchant_name || "Unknown"}</span>
                  <span className="mx-2">·</span>
                  <span className="text-coral">{formatCurrency(Math.abs(editingTx.amount))}</span>
                </>
              )}
            </DialogDescription>
          </DialogHeader>
          <div className="grid grid-cols-2 gap-2 py-4">
            {allCategories.map((cat) => (
              <button
                key={cat}
                onClick={() => setNewCategory(cat)}
                className={`px-4 py-3 rounded-xl text-sm font-medium capitalize transition-all ${
                  cat === newCategory
                    ? "bg-coral text-white"
                    : "bg-navy-mid text-stone hover:text-white hover:bg-navy-deep"
                }`}
              >
                {cat.replace(/_/g, " ")}
              </button>
            ))}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditingTx(null)}>
              Cancel
            </Button>
            <Button
              onClick={handleSaveCategory}
              disabled={updateTransaction.isPending}
            >
              {updateTransaction.isPending ? "Saving..." : "Save"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
