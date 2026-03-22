import { useRef, useState, useMemo } from "react";
import { TopBar } from "@/components/layout";
import { Button } from "@/components/ui/button";
import { MonthSummaryBar } from "@/components/ui/month-summary-bar";
import { BudgetTableNew } from "@/components/budget-table";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Upload } from "lucide-react";
import {
  useImportBudgets,
  useBudgetGroupStatuses,
} from "@/hooks/useApi";

export function Budgets() {
  const importBudgets = useImportBudgets();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isImportDialogOpen, setIsImportDialogOpen] = useState(false);
  const [importResult, setImportResult] = useState<{
    imported: number;
    skipped: number;
    errors: string[];
  } | null>(null);

  const { data: budgetGroups } = useBudgetGroupStatuses();

  // Compute summary data
  const summary = useMemo(() => {
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
  const budgetCount = budgetGroups?.reduce((sum, g) => sum + g.budget_count, 0) ?? 0;

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

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  return (
    <div>
      <TopBar
        title="BUDGETS"
        subtitle={`${budgetCount} active budgets`}
        showSync={false}
      >
        <div className="flex items-center gap-2">
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            accept=".csv"
            className="hidden"
          />
          <Button
            variant="outline"
            size="sm"
            onClick={handleImportClick}
            disabled={importBudgets.isPending}
          >
            <Upload className="w-3.5 h-3.5" />
            {importBudgets.isPending ? "Importing..." : "Import CSV"}
          </Button>
        </div>
      </TopBar>

      {/* Month summary bar */}
      <MonthSummaryBar
        totalSpent={summary.spent}
        totalBudget={summary.budget}
        totalRemaining={summary.remaining}
        currentDay={currentDay}
        totalDays={totalDays}
        className="mb-4"
      />

      {/* Budget table — full interactive */}
      <BudgetTableNew />

      {/* Import Result Dialog */}
      <Dialog open={isImportDialogOpen} onOpenChange={setIsImportDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Import Complete</DialogTitle>
            <DialogDescription>CSV import results</DialogDescription>
          </DialogHeader>

          {importResult && (
            <div className="py-4 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-navy rounded-xl p-4 text-center">
                  <div className="text-2xl text-mint font-bold">
                    {importResult.imported}
                  </div>
                  <div className="text-sm text-stone">Imported</div>
                </div>
                <div className="bg-navy rounded-xl p-4 text-center">
                  <div className="text-2xl text-yellow font-bold">
                    {importResult.skipped}
                  </div>
                  <div className="text-sm text-stone">Skipped</div>
                </div>
              </div>

              {importResult.errors.length > 0 && (
                <div className="bg-navy rounded-xl p-4">
                  <div className="text-sm text-coral mb-2">
                    Errors ({importResult.errors.length}):
                  </div>
                  <ul className="text-xs text-stone space-y-1 max-h-32 overflow-y-auto">
                    {importResult.errors.map((err, i) => (
                      <li key={i}>{err}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          <DialogFooter>
            <Button onClick={() => setIsImportDialogOpen(false)}>Close</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
