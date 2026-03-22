import { useRef, useState } from "react";
import { Link } from "react-router-dom";
import { TopBar } from "@/components/layout";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Upload, ArrowLeft } from "lucide-react";
import { useImportBudgets } from "@/hooks/useApi";

export function Budgets() {
  const importBudgets = useImportBudgets();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isImportDialogOpen, setIsImportDialogOpen] = useState(false);
  const [importResult, setImportResult] = useState<{
    imported: number;
    skipped: number;
    errors: string[];
  } | null>(null);

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
        subtitle="Import and manage budget data"
        showSync={false}
      />

      {/* Navigation back to dashboard */}
      <div className="mb-8 p-6 bg-charcoal rounded-xl border border-navy-mid">
        <div className="flex items-center gap-3 mb-4">
          <ArrowLeft className="w-5 h-5 text-coral" />
          <h2
            className="text-lg text-white"
            style={{ fontFamily: "var(--font-display)" }}
          >
            BUDGET MANAGEMENT HAS MOVED
          </h2>
        </div>
        <p className="text-stone text-sm mb-4">
          Budget groups, line items, and inline editing are now on the{" "}
          <Link to="/" className="text-coral hover:text-coral-bright underline">
            Dashboard
          </Link>
          . Click any budget amount or category name to edit inline.
        </p>
        <Link to="/">
          <Button>Go to Dashboard</Button>
        </Link>
      </div>

      {/* CSV Import — kept here as a utility */}
      <div className="p-6 bg-charcoal rounded-xl border border-navy-mid">
        <h3
          className="text-lg text-white mb-3"
          style={{ fontFamily: "var(--font-display)" }}
        >
          CSV IMPORT
        </h3>
        <p className="text-stone text-sm mb-4">
          Batch import budgets from a CSV file. Existing budgets with the same
          category won't be duplicated.
        </p>

        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileChange}
          accept=".csv"
          className="hidden"
        />

        <Button
          variant="outline"
          onClick={handleImportClick}
          disabled={importBudgets.isPending}
        >
          <Upload className="w-4 h-4" />
          {importBudgets.isPending ? "IMPORTING..." : "IMPORT CSV"}
        </Button>

        <div className="mt-4 text-xs text-stone">
          <p className="font-medium mb-1">Expected CSV format:</p>
          <code className="block bg-navy p-3 rounded text-mint">
            category,amount,period,start_day
            <br />
            groceries,30000,monthly,1
            <br />
            transport,15000,monthly,1
          </code>
          <p className="mt-2">Amount in pence (30000 = £300.00)</p>
        </div>
      </div>

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
