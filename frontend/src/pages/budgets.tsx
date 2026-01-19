import { useState, useRef } from "react";
import { TopBar } from "@/components/layout";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { BudgetBar } from "@/components/ui/budget-bar";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Plus, Pencil, Trash2, Upload } from "lucide-react";
import { useBudgetStatuses, useCreateBudget, useUpdateBudget, useDeleteBudget, useImportBudgets } from "@/hooks/useApi";

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

const categories = [
  "groceries",
  "eating_out",
  "shopping",
  "transport",
  "entertainment",
  "bills",
  "general",
  "holidays",
];

interface BudgetFormData {
  category: string;
  amount: string;
  period: "monthly" | "weekly";
  start_day: number;
}

export function Budgets() {
  const { data: budgetStatuses, isLoading, error } = useBudgetStatuses();
  const createBudget = useCreateBudget();
  const updateBudget = useUpdateBudget();
  const deleteBudget = useDeleteBudget();
  const importBudgets = useImportBudgets();

  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [isImportDialogOpen, setIsImportDialogOpen] = useState(false);
  const [importResult, setImportResult] = useState<{ imported: number; skipped: number; errors: string[] } | null>(null);
  const [editingBudget, setEditingBudget] = useState<string | null>(null);
  const [formData, setFormData] = useState<BudgetFormData>({
    category: "groceries",
    amount: "",
    period: "monthly",
    start_day: 1,
  });
  const fileInputRef = useRef<HTMLInputElement>(null);

  const budgets = budgetStatuses || [];
  const totalBudget = budgets.reduce((sum, b) => sum + b.amount, 0);
  const totalSpent = budgets.reduce((sum, b) => sum + b.spent, 0);

  const handleImportClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      const result = await importBudgets.mutateAsync(file);
      setImportResult(result);
      setIsImportDialogOpen(true);
    } catch (err) {
      setImportResult({
        imported: 0,
        skipped: 0,
        errors: [err instanceof Error ? err.message : "Import failed"],
      });
      setIsImportDialogOpen(true);
    }

    // Reset file input
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handleOpenDialog = (budgetId?: string) => {
    if (budgetId) {
      const budget = budgets.find((b) => b.budget_id === budgetId);
      if (budget) {
        setFormData({
          category: budget.category,
          amount: (budget.amount / 100).toString(),
          period: "monthly",
          start_day: 1,
        });
        setEditingBudget(budgetId);
      }
    } else {
      setFormData({
        category: "groceries",
        amount: "",
        period: "monthly",
        start_day: 1,
      });
      setEditingBudget(null);
    }
    setIsDialogOpen(true);
  };

  const handleSubmit = async () => {
    const amountInPence = Math.round(parseFloat(formData.amount) * 100);

    if (editingBudget) {
      await updateBudget.mutateAsync({
        id: editingBudget,
        data: {
          category: formData.category,
          amount: amountInPence,
          period: formData.period,
          start_day: formData.start_day,
        },
      });
    } else {
      await createBudget.mutateAsync({
        category: formData.category,
        amount: amountInPence,
        period: formData.period,
        start_day: formData.start_day,
      });
    }

    setIsDialogOpen(false);
  };

  const handleDelete = async (budgetId: string) => {
    if (confirm("Are you sure you want to delete this budget?")) {
      await deleteBudget.mutateAsync(budgetId);
    }
  };

  return (
    <div>
      <TopBar
        title="BUDGETS"
        subtitle={`${budgets.length} active budgets`}
        showSync={false}
      />

      {/* Summary */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        <div className="bg-charcoal rounded-2xl p-6 border border-navy-mid">
          <div className="text-xs font-semibold uppercase tracking-wider text-stone mb-2">
            TOTAL BUDGET
          </div>
          <div
            className="text-4xl text-white"
            style={{ fontFamily: "var(--font-display)" }}
          >
            £{(totalBudget / 100).toLocaleString()}
          </div>
        </div>
        <div className="bg-charcoal rounded-2xl p-6 border border-navy-mid">
          <div className="text-xs font-semibold uppercase tracking-wider text-stone mb-2">
            TOTAL SPENT
          </div>
          <div
            className="text-4xl text-coral"
            style={{ fontFamily: "var(--font-display)" }}
          >
            £{(totalSpent / 100).toLocaleString()}
          </div>
        </div>
        <div className="bg-charcoal rounded-2xl p-6 border border-navy-mid">
          <div className="text-xs font-semibold uppercase tracking-wider text-stone mb-2">
            REMAINING
          </div>
          <div
            className="text-4xl text-mint"
            style={{ fontFamily: "var(--font-display)" }}
          >
            £{((totalBudget - totalSpent) / 100).toLocaleString()}
          </div>
        </div>
      </div>

      {/* Hidden file input for CSV import */}
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileChange}
        accept=".csv"
        className="hidden"
      />

      {/* Budget List */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>ALL BUDGETS</CardTitle>
          <div className="flex gap-2">
            <Button size="sm" variant="outline" onClick={handleImportClick} disabled={importBudgets.isPending}>
              <Upload className="w-4 h-4" />
              {importBudgets.isPending ? "IMPORTING..." : "IMPORT CSV"}
            </Button>
            <Button size="sm" onClick={() => handleOpenDialog()}>
              <Plus className="w-4 h-4" />
              ADD BUDGET
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          {isLoading && (
            <div className="text-center py-8 text-stone">Loading budgets...</div>
          )}
          {error && (
            <div className="text-center py-8 text-coral">
              Failed to load budgets. Please try again.
            </div>
          )}
          {!isLoading && !error && budgets.length === 0 && (
            <div className="text-center py-8 text-stone">
              No budgets set. Click "ADD BUDGET" to create one.
            </div>
          )}
          {budgets.map((budget) => (
            <div
              key={budget.budget_id}
              className="p-4 bg-navy rounded-xl hover:bg-navy-deep transition-colors group"
            >
              <div className="flex items-center gap-4">
                <div className="flex-1">
                  <BudgetBar
                    name={budget.category.replace(/_/g, " ")}
                    spent={budget.spent}
                    budget={budget.amount}
                    emoji={categoryEmojis[budget.category] || "📦"}
                  />
                </div>
                <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button
                    onClick={() => handleOpenDialog(budget.budget_id)}
                    className="p-2 text-stone hover:text-white transition-colors"
                  >
                    <Pencil className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => handleDelete(budget.budget_id)}
                    className="p-2 text-stone hover:text-coral transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
              <div className="mt-2 text-xs text-slate capitalize">
                {budget.status === "over" ? (
                  <span className="text-coral">Over budget by £{((budget.spent - budget.amount) / 100).toFixed(2)}</span>
                ) : budget.status === "warning" ? (
                  <span className="text-yellow">£{(budget.remaining / 100).toFixed(2)} remaining (warning)</span>
                ) : (
                  <span className="text-mint">£{(budget.remaining / 100).toFixed(2)} remaining</span>
                )}
              </div>
            </div>
          ))}
        </CardContent>
      </Card>

      {/* Add/Edit Budget Dialog */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {editingBudget ? "Edit Budget" : "Add New Budget"}
            </DialogTitle>
            <DialogDescription>
              Set a spending limit for a category.
            </DialogDescription>
          </DialogHeader>

          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="category" className="text-white">Category</Label>
              <select
                id="category"
                value={formData.category}
                onChange={(e) =>
                  setFormData({ ...formData, category: e.target.value })
                }
                className="bg-navy border border-navy-mid rounded-lg px-4 py-2 text-white w-full"
              >
                {categories.map((cat) => (
                  <option key={cat} value={cat}>
                    {categoryEmojis[cat]} {cat.replace(/_/g, " ")}
                  </option>
                ))}
              </select>
            </div>

            <div className="grid gap-2">
              <Label htmlFor="amount" className="text-white">Monthly Budget (£)</Label>
              <Input
                id="amount"
                type="number"
                step="0.01"
                min="0"
                placeholder="100.00"
                value={formData.amount}
                onChange={(e) =>
                  setFormData({ ...formData, amount: e.target.value })
                }
                className="bg-navy border-navy-mid text-white placeholder:text-stone"
              />
            </div>

            <div className="grid gap-2">
              <Label htmlFor="period" className="text-white">Period</Label>
              <select
                id="period"
                value={formData.period}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    period: e.target.value as "monthly" | "weekly",
                  })
                }
                className="bg-navy border border-navy-mid rounded-lg px-4 py-2 text-white w-full"
              >
                <option value="monthly">Monthly</option>
                <option value="weekly">Weekly</option>
              </select>
            </div>
          </div>

          <DialogFooter>
            <Button
              variant="ghost"
              onClick={() => setIsDialogOpen(false)}
            >
              Cancel
            </Button>
            <Button
              onClick={handleSubmit}
              disabled={!formData.amount || parseFloat(formData.amount) <= 0}
            >
              {editingBudget ? "Save Changes" : "Create Budget"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Import Result Dialog */}
      <Dialog open={isImportDialogOpen} onOpenChange={setIsImportDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Import Complete</DialogTitle>
            <DialogDescription>
              CSV import results
            </DialogDescription>
          </DialogHeader>

          {importResult && (
            <div className="py-4 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-navy rounded-xl p-4 text-center">
                  <div className="text-2xl text-mint font-bold">{importResult.imported}</div>
                  <div className="text-sm text-stone">Imported</div>
                </div>
                <div className="bg-navy rounded-xl p-4 text-center">
                  <div className="text-2xl text-yellow font-bold">{importResult.skipped}</div>
                  <div className="text-sm text-stone">Skipped (duplicate)</div>
                </div>
              </div>

              {importResult.errors.length > 0 && (
                <div className="bg-navy rounded-xl p-4">
                  <div className="text-sm text-coral mb-2">Errors ({importResult.errors.length}):</div>
                  <ul className="text-xs text-stone space-y-1 max-h-32 overflow-y-auto">
                    {importResult.errors.map((err, i) => (
                      <li key={i}>{err}</li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="text-xs text-stone">
                <p className="font-medium mb-1">Expected CSV format:</p>
                <code className="block bg-navy p-2 rounded text-mint">
                  category,amount,period,start_day<br />
                  groceries,30000,monthly,1<br />
                  transport,15000,monthly,1
                </code>
                <p className="mt-2 text-stone">Amount in pence (30000 = £300.00)</p>
              </div>
            </div>
          )}

          <DialogFooter>
            <Button onClick={() => setIsImportDialogOpen(false)}>
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
