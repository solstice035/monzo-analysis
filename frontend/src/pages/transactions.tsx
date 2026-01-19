import { useState } from "react";
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

export function Transactions() {
  const [selectedCategory, setSelectedCategory] = useState<string>("All");
  const [editingTx, setEditingTx] = useState<Transaction | null>(null);
  const [newCategory, setNewCategory] = useState<string>("");

  const { data, isLoading, error } = useTransactions({
    category: selectedCategory === "All" ? undefined : selectedCategory,
    limit: 50,
  });
  const updateTransaction = useUpdateTransaction();

  const transactions = data?.items || [];

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

  return (
    <div>
      <TopBar
        title="TRANSACTIONS"
        subtitle={`${transactions.length} transactions${selectedCategory !== "All" ? ` in ${selectedCategory.replace(/_/g, " ")}` : ""}`}
        showSync={false}
      />

      {/* Filters */}
      <div className="flex gap-3 mb-6 flex-wrap">
        {categories.map((cat) => (
          <button
            key={cat}
            onClick={() => setSelectedCategory(cat)}
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
