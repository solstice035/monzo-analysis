import { useState, useRef } from "react";
import { TopBar } from "@/components/layout";
import { Card, CardContent } from "@/components/ui/card";
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
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Plus,
  Pencil,
  Trash2,
  Upload,
  ChevronDown,
  ChevronRight,
  MoreHorizontal,
  RotateCcw,
  Merge,
  Eye,
  EyeOff,
} from "lucide-react";
import {
  useEnvelopeDashboard,
  useBudgets,
  useBudgetGroups,
  useCreateBudget,
  useUpdateBudget,
  useDeleteBudget,
  useImportBudgets,
  useMergeBudget,
  useRestoreBudget,
} from "@/hooks/useApi";
import { useAccount } from "@/contexts/AccountContext";
import { formatCurrency } from "@/lib/utils";
import type { EnvelopeGroup, EnvelopeItem, BudgetGroup } from "@/lib/api";

interface InlineEditState {
  budgetId: string;
  name: string;
  amount: string;
  groupId: string;
}

interface AddCategoryState {
  groupId: string;
  name: string;
  amount: string;
  periodType: string;
}

export function Budgets() {
  const { selectedAccount } = useAccount();
  const { data: envelopeData, isLoading, error } = useEnvelopeDashboard();
  const { data: allBudgets } = useBudgets();
  const { data: budgetGroups } = useBudgetGroups();
  const createBudget = useCreateBudget();
  const updateBudget = useUpdateBudget();
  const deleteBudget = useDeleteBudget();
  const importBudgets = useImportBudgets();
  const mergeBudget = useMergeBudget();
  const restoreBudget = useRestoreBudget();

  // UI State
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set());
  const [inlineEdit, setInlineEdit] = useState<InlineEditState | null>(null);
  const [addCategory, setAddCategory] = useState<AddCategoryState | null>(null);
  const [menuOpen, setMenuOpen] = useState<string | null>(null);
  const [showArchived, setShowArchived] = useState(false);
  const [mergeDialog, setMergeDialog] = useState<{ sourceId: string; sourceName: string } | null>(null);
  const [mergeTargetId, setMergeTargetId] = useState("");
  const [archiveDialog, setArchiveDialog] = useState<{ id: string; name: string } | null>(null);
  const [isImportDialogOpen, setIsImportDialogOpen] = useState(false);
  const [importResult, setImportResult] = useState<{ imported: number; skipped: number; errors: string[] } | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const groups = envelopeData?.groups || [];
  const totalAllocated = envelopeData?.total_allocated || 0;
  const totalSpent = envelopeData?.total_spent || 0;
  const totalAvailable = envelopeData?.total_available || 0;

  // Get archived budgets from allBudgets (those not in envelope data)
  const activeBudgetIds = new Set(
    groups.flatMap((g) => g.envelopes.map((e) => e.budget_id))
  );
  const archivedBudgets = (allBudgets || []).filter(
    (b) => !activeBudgetIds.has(b.id) && b.id
  );

  const toggleGroup = (groupId: string) => {
    setExpandedGroups((prev) => {
      const next = new Set(prev);
      if (next.has(groupId)) {
        next.delete(groupId);
      } else {
        next.add(groupId);
      }
      return next;
    });
  };

  // Expand all by default on first load
  if (groups.length > 0 && expandedGroups.size === 0) {
    const allIds = new Set(groups.map((g) => g.group_id));
    if (allIds.size > 0 && expandedGroups.size === 0) {
      setExpandedGroups(allIds);
    }
  }

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

  const handleInlineEditSave = async () => {
    if (!inlineEdit) return;
    const amountInPence = Math.round(parseFloat(inlineEdit.amount) * 100);
    await updateBudget.mutateAsync({
      id: inlineEdit.budgetId,
      data: {
        name: inlineEdit.name,
        amount: amountInPence,
        group_id: inlineEdit.groupId || undefined,
      },
    });
    setInlineEdit(null);
  };

  const handleAddCategorySave = async () => {
    if (!addCategory || !selectedAccount) return;
    const amountInPence = Math.round(parseFloat(addCategory.amount) * 100);
    const slug = addCategory.name.toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_|_$/g, "");
    await createBudget.mutateAsync({
      account_id: selectedAccount.id,
      category: slug,
      name: addCategory.name,
      amount: amountInPence,
      period: "monthly",
      start_day: 1,
      group_id: addCategory.groupId,
      period_type: addCategory.periodType,
    } as any);
    setAddCategory(null);
  };

  const handleArchive = async () => {
    if (!archiveDialog) return;
    await deleteBudget.mutateAsync(archiveDialog.id);
    setArchiveDialog(null);
    setMenuOpen(null);
  };

  const handleMerge = async () => {
    if (!mergeDialog || !mergeTargetId) return;
    await mergeBudget.mutateAsync({
      id: mergeDialog.sourceId,
      targetBudgetId: mergeTargetId,
    });
    setMergeDialog(null);
    setMergeTargetId("");
    setMenuOpen(null);
  };

  const handleRestore = async (budgetId: string) => {
    await restoreBudget.mutateAsync(budgetId);
  };

  // All active budgets for the merge target picker
  const activeBudgetsList = groups.flatMap((g) =>
    g.envelopes.map((e) => ({
      id: e.budget_id,
      name: e.budget_name || e.category,
      groupName: g.group_name,
    }))
  );

  return (
    <div>
      <TopBar
        title="BUDGETS"
        subtitle={`${groups.reduce((sum, g) => sum + g.envelopes.length, 0)} active categories across ${groups.length} groups`}
        showSync={false}
      />

      {/* Summary */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        <div className="bg-charcoal rounded-2xl p-6 border border-navy-mid">
          <div className="text-xs font-semibold uppercase tracking-wider text-stone mb-2">
            TOTAL BUDGET
          </div>
          <div className="text-4xl text-white" style={{ fontFamily: "var(--font-display)" }}>
            {formatCurrency(totalAllocated)}
          </div>
        </div>
        <div className="bg-charcoal rounded-2xl p-6 border border-navy-mid">
          <div className="text-xs font-semibold uppercase tracking-wider text-stone mb-2">
            TOTAL SPENT
          </div>
          <div className="text-4xl text-coral" style={{ fontFamily: "var(--font-display)" }}>
            {formatCurrency(totalSpent)}
          </div>
        </div>
        <div className="bg-charcoal rounded-2xl p-6 border border-navy-mid">
          <div className="text-xs font-semibold uppercase tracking-wider text-stone mb-2">
            REMAINING
          </div>
          <div className="text-4xl text-mint" style={{ fontFamily: "var(--font-display)" }}>
            {formatCurrency(totalAvailable)}
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

      {/* Loading / Error */}
      {isLoading && (
        <div className="text-center py-12 text-stone">Loading budgets...</div>
      )}
      {error && (
        <div className="text-center py-12 text-coral">
          Failed to load budgets. Please try again.
        </div>
      )}

      {/* Import CSV button */}
      {!isLoading && !error && (
        <div className="flex justify-end mb-4 gap-2">
          <Button size="sm" variant="outline" onClick={handleImportClick} disabled={importBudgets.isPending}>
            <Upload className="w-4 h-4" />
            {importBudgets.isPending ? "IMPORTING..." : "IMPORT CSV"}
          </Button>
        </div>
      )}

      {/* Budget Groups - Accordion View */}
      <div className="space-y-4">
        {groups.map((group) => (
          <GroupAccordion
            key={group.group_id}
            group={group}
            expanded={expandedGroups.has(group.group_id)}
            onToggle={() => toggleGroup(group.group_id)}
            inlineEdit={inlineEdit}
            onStartEdit={(envelope) => {
              const budget = (allBudgets || []).find((b) => b.id === envelope.budget_id);
              setInlineEdit({
                budgetId: envelope.budget_id,
                name: envelope.budget_name || envelope.category,
                amount: ((budget?.amount || envelope.allocated) / 100).toString(),
                groupId: group.group_id,
              });
            }}
            onCancelEdit={() => setInlineEdit(null)}
            onSaveEdit={handleInlineEditSave}
            onEditChange={(field, value) => {
              if (inlineEdit) {
                setInlineEdit({ ...inlineEdit, [field]: value });
              }
            }}
            menuOpen={menuOpen}
            onMenuToggle={(id) => setMenuOpen(menuOpen === id ? null : id)}
            onArchive={(id, name) => setArchiveDialog({ id, name })}
            onMerge={(id, name) => {
              setMergeDialog({ sourceId: id, sourceName: name });
              setMergeTargetId("");
            }}
            addCategory={addCategory}
            onStartAdd={() =>
              setAddCategory({
                groupId: group.group_id,
                name: "",
                amount: "",
                periodType: "monthly",
              })
            }
            onCancelAdd={() => setAddCategory(null)}
            onSaveAdd={handleAddCategorySave}
            onAddChange={(field, value) => {
              if (addCategory) {
                setAddCategory({ ...addCategory, [field]: value });
              }
            }}
            budgetGroups={budgetGroups || []}
          />
        ))}
      </div>

      {/* Show Archived Toggle */}
      {archivedBudgets.length > 0 && (
        <div className="mt-6">
          <button
            onClick={() => setShowArchived(!showArchived)}
            className="flex items-center gap-2 text-sm text-stone hover:text-white transition-colors"
          >
            {showArchived ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            {showArchived ? "Hide archived" : `Show archived (${archivedBudgets.length})`}
          </button>

          {showArchived && (
            <div className="mt-3 space-y-2">
              {archivedBudgets.map((budget) => (
                <div
                  key={budget.id}
                  className="flex items-center justify-between p-3 bg-navy/50 rounded-xl border border-navy-mid opacity-60"
                >
                  <div className="text-stone line-through">
                    {budget.name || budget.category.replace(/_/g, " ")}
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-stone" style={{ fontFamily: "var(--font-mono)" }}>
                      {formatCurrency(budget.amount)}
                    </span>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => handleRestore(budget.id)}
                      className="text-mint hover:text-mint"
                    >
                      <RotateCcw className="w-3 h-3 mr-1" />
                      Restore
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Archive Confirmation Dialog */}
      <AlertDialog open={!!archiveDialog} onOpenChange={() => setArchiveDialog(null)}>
        <AlertDialogContent className="bg-charcoal border-navy-mid">
          <AlertDialogHeader>
            <AlertDialogTitle className="text-white">Archive Category</AlertDialogTitle>
            <AlertDialogDescription className="text-stone">
              Archive &ldquo;{archiveDialog?.name}&rdquo;? It will be hidden from the main view but can be restored later. Transaction history is preserved.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel className="bg-navy border-navy-mid text-white hover:bg-navy-deep">
              Cancel
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={handleArchive}
              className="bg-coral text-white hover:bg-coral-deep"
            >
              Archive
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Merge Dialog */}
      <Dialog open={!!mergeDialog} onOpenChange={() => setMergeDialog(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Merge &ldquo;{mergeDialog?.sourceName}&rdquo;</DialogTitle>
            <DialogDescription>
              All transactions and rules will be moved to the target category. This cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <Label className="text-white mb-2 block">Merge into:</Label>
            <select
              value={mergeTargetId}
              onChange={(e) => setMergeTargetId(e.target.value)}
              className="bg-navy border border-navy-mid rounded-lg px-4 py-2 text-white w-full"
            >
              <option value="">Select target category...</option>
              {activeBudgetsList
                .filter((b) => b.id !== mergeDialog?.sourceId)
                .map((b) => (
                  <option key={b.id} value={b.id}>
                    {b.groupName} → {b.name}
                  </option>
                ))}
            </select>
          </div>
          <DialogFooter>
            <Button variant="ghost" onClick={() => setMergeDialog(null)}>
              Cancel
            </Button>
            <Button
              onClick={handleMerge}
              disabled={!mergeTargetId}
              className="bg-coral text-white hover:bg-coral-deep"
            >
              Merge
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

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
                  <div className="text-2xl text-mint font-bold">{importResult.imported}</div>
                  <div className="text-sm text-stone">Imported</div>
                </div>
                <div className="bg-navy rounded-xl p-4 text-center">
                  <div className="text-2xl text-yellow font-bold">{importResult.skipped}</div>
                  <div className="text-sm text-stone">Skipped</div>
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

/* ─── Group Accordion Component ─── */

interface GroupAccordionProps {
  group: EnvelopeGroup;
  expanded: boolean;
  onToggle: () => void;
  inlineEdit: InlineEditState | null;
  onStartEdit: (envelope: EnvelopeItem) => void;
  onCancelEdit: () => void;
  onSaveEdit: () => void;
  onEditChange: (field: string, value: string) => void;
  menuOpen: string | null;
  onMenuToggle: (id: string) => void;
  onArchive: (id: string, name: string) => void;
  onMerge: (id: string, name: string) => void;
  addCategory: AddCategoryState | null;
  onStartAdd: () => void;
  onCancelAdd: () => void;
  onSaveAdd: () => void;
  onAddChange: (field: string, value: string) => void;
  budgetGroups: BudgetGroup[];
}

function GroupAccordion({
  group,
  expanded,
  onToggle,
  inlineEdit,
  onStartEdit,
  onCancelEdit,
  onSaveEdit,
  onEditChange,
  menuOpen,
  onMenuToggle,
  onArchive,
  onMerge,
  addCategory,
  onStartAdd,
  onCancelAdd,
  onSaveAdd,
  onAddChange,
  budgetGroups,
}: GroupAccordionProps) {
  const percentage = group.total_allocated > 0
    ? Math.min((group.total_spent / group.total_allocated) * 100, 100)
    : 0;
  const isOver = group.total_spent > group.total_allocated;

  return (
    <Card className="overflow-hidden">
      {/* Group Header */}
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between p-4 hover:bg-navy/30 transition-colors"
      >
        <div className="flex items-center gap-3">
          {expanded ? (
            <ChevronDown className="w-5 h-5 text-stone" />
          ) : (
            <ChevronRight className="w-5 h-5 text-stone" />
          )}
          <span className="text-xl">{group.icon || "📂"}</span>
          <div className="text-left">
            <h3 className="font-semibold text-white text-lg">{group.group_name}</h3>
            <span className="text-xs text-stone">
              {group.envelopes.length} categor{group.envelopes.length !== 1 ? "ies" : "y"}
            </span>
          </div>
        </div>
        <div className="flex items-center gap-6">
          <div className="text-right">
            <div className="text-sm text-stone">Allocated</div>
            <div className="text-white font-mono" style={{ fontFamily: "var(--font-mono)" }}>
              {formatCurrency(group.total_allocated)}
            </div>
          </div>
          <div className="text-right">
            <div className="text-sm text-stone">Spent</div>
            <div
              className={isOver ? "text-coral font-mono" : "text-white font-mono"}
              style={{ fontFamily: "var(--font-mono)" }}
            >
              {formatCurrency(group.total_spent)}
            </div>
          </div>
          <div className="text-right">
            <div className="text-sm text-stone">Available</div>
            <div
              className={isOver ? "text-coral font-mono" : "text-mint font-mono"}
              style={{ fontFamily: "var(--font-mono)" }}
            >
              {formatCurrency(group.total_available)}
            </div>
          </div>
        </div>
      </button>

      {/* Progress bar */}
      <div className="px-4 pb-2">
        <div className="h-1.5 bg-navy rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-500 ${
              isOver
                ? "bg-gradient-to-r from-coral-deep to-coral"
                : percentage >= 80
                ? "bg-gradient-to-r from-yellow to-[#FFE566]"
                : "bg-gradient-to-r from-mint to-[#00FFD4]"
            }`}
            style={{ width: `${percentage}%` }}
          />
        </div>
      </div>

      {/* Expanded Content */}
      {expanded && (
        <CardContent className="pt-2 space-y-2">
          {group.envelopes.map((envelope) => (
            <EnvelopeRow
              key={envelope.budget_id}
              envelope={envelope}
              groupId={group.group_id}
              inlineEdit={
                inlineEdit?.budgetId === envelope.budget_id ? inlineEdit : null
              }
              onStartEdit={() => onStartEdit(envelope)}
              onCancelEdit={onCancelEdit}
              onSaveEdit={onSaveEdit}
              onEditChange={onEditChange}
              menuOpen={menuOpen === envelope.budget_id}
              onMenuToggle={() => onMenuToggle(envelope.budget_id)}
              onArchive={() =>
                onArchive(envelope.budget_id, envelope.budget_name || envelope.category)
              }
              onMerge={() =>
                onMerge(envelope.budget_id, envelope.budget_name || envelope.category)
              }
              budgetGroups={budgetGroups}
            />
          ))}

          {/* Add Category inline form or button */}
          {addCategory && addCategory.groupId === group.group_id ? (
            <div className="p-3 bg-navy/50 rounded-xl border border-navy-mid space-y-3">
              <div className="grid grid-cols-3 gap-3">
                <div>
                  <Label className="text-xs text-stone">Name</Label>
                  <Input
                    value={addCategory.name}
                    onChange={(e) => onAddChange("name", e.target.value)}
                    placeholder="e.g., Dog Walker"
                    className="bg-navy border-navy-mid text-white placeholder:text-stone h-8 text-sm"
                    autoFocus
                  />
                </div>
                <div>
                  <Label className="text-xs text-stone">Monthly Amount (£)</Label>
                  <Input
                    type="number"
                    step="0.01"
                    min="0"
                    value={addCategory.amount}
                    onChange={(e) => onAddChange("amount", e.target.value)}
                    placeholder="100.00"
                    className="bg-navy border-navy-mid text-white placeholder:text-stone h-8 text-sm"
                  />
                </div>
                <div>
                  <Label className="text-xs text-stone">Type</Label>
                  <select
                    value={addCategory.periodType}
                    onChange={(e) => onAddChange("periodType", e.target.value)}
                    className="bg-navy border border-navy-mid rounded-lg px-3 py-1 text-white w-full h-8 text-sm"
                  >
                    <option value="monthly">Monthly</option>
                    <option value="weekly">Weekly</option>
                    <option value="annual">Annual (sinking)</option>
                    <option value="quarterly">Quarterly (sinking)</option>
                  </select>
                </div>
              </div>
              <div className="flex gap-2 justify-end">
                <Button size="sm" variant="ghost" onClick={onCancelAdd}>
                  Cancel
                </Button>
                <Button
                  size="sm"
                  onClick={onSaveAdd}
                  disabled={!addCategory.name || !addCategory.amount || parseFloat(addCategory.amount) <= 0}
                >
                  Add
                </Button>
              </div>
            </div>
          ) : (
            <button
              onClick={onStartAdd}
              className="flex items-center gap-2 text-sm text-stone hover:text-mint transition-colors py-2 px-3"
            >
              <Plus className="w-4 h-4" />
              Add category to this group
            </button>
          )}
        </CardContent>
      )}
    </Card>
  );
}

/* ─── Envelope Row Component ─── */

interface EnvelopeRowProps {
  envelope: EnvelopeItem;
  groupId: string;
  inlineEdit: InlineEditState | null;
  onStartEdit: () => void;
  onCancelEdit: () => void;
  onSaveEdit: () => void;
  onEditChange: (field: string, value: string) => void;
  menuOpen: boolean;
  onMenuToggle: () => void;
  onArchive: () => void;
  onMerge: () => void;
  budgetGroups: BudgetGroup[];
}

function EnvelopeRow({
  envelope,
  inlineEdit,
  onStartEdit,
  onCancelEdit,
  onSaveEdit,
  onEditChange,
  menuOpen,
  onMenuToggle,
  onArchive,
  onMerge,
  budgetGroups,
}: EnvelopeRowProps) {
  const displayName = envelope.budget_name || envelope.category.replace(/_/g, " ");

  if (inlineEdit) {
    return (
      <div className="p-3 bg-navy rounded-xl border border-coral/30 space-y-3">
        <div className="grid grid-cols-3 gap-3">
          <div>
            <Label className="text-xs text-stone">Name</Label>
            <Input
              value={inlineEdit.name}
              onChange={(e) => onEditChange("name", e.target.value)}
              className="bg-navy-deep border-navy-mid text-white h-8 text-sm"
              autoFocus
            />
          </div>
          <div>
            <Label className="text-xs text-stone">Monthly Amount (£)</Label>
            <Input
              type="number"
              step="0.01"
              min="0"
              value={inlineEdit.amount}
              onChange={(e) => onEditChange("amount", e.target.value)}
              className="bg-navy-deep border-navy-mid text-white h-8 text-sm"
            />
          </div>
          <div>
            <Label className="text-xs text-stone">Group</Label>
            <select
              value={inlineEdit.groupId}
              onChange={(e) => onEditChange("groupId", e.target.value)}
              className="bg-navy-deep border border-navy-mid rounded-lg px-3 py-1 text-white w-full h-8 text-sm"
            >
              {budgetGroups.map((g) => (
                <option key={g.id} value={g.id}>
                  {g.icon || "📂"} {g.name}
                </option>
              ))}
            </select>
          </div>
        </div>
        <div className="flex gap-2 justify-end">
          <Button size="sm" variant="ghost" onClick={onCancelEdit}>
            Cancel
          </Button>
          <Button size="sm" onClick={onSaveEdit}>
            Save
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-3 bg-navy rounded-xl hover:bg-navy-deep transition-colors group relative">
      <div className="flex items-center gap-4">
        <div className="flex-1">
          <BudgetBar
            name={displayName}
            spent={envelope.spent}
            budget={envelope.allocated}
          />
        </div>

        {/* Rollover indicator */}
        {envelope.rollover > 0 && (
          <span className="text-xs text-sky px-2 py-0.5 bg-sky/10 rounded-full whitespace-nowrap">
            +{formatCurrency(envelope.rollover)} rollover
          </span>
        )}

        {/* Edit & Menu buttons */}
        <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <button
            onClick={(e) => {
              e.stopPropagation();
              onStartEdit();
            }}
            className="p-1.5 text-stone hover:text-white transition-colors"
          >
            <Pencil className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation();
              onMenuToggle();
            }}
            className="p-1.5 text-stone hover:text-white transition-colors"
          >
            <MoreHorizontal className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Status line */}
      <div className="mt-1 flex items-center gap-3 text-xs text-slate">
        {envelope.spent > envelope.allocated ? (
          <span className="text-coral">
            Over by {formatCurrency(envelope.spent - envelope.allocated)}
          </span>
        ) : (
          <span className="text-mint">
            {formatCurrency(envelope.available)} available
          </span>
        )}
        <span className="text-stone">
          {envelope.pct_used.toFixed(0)}% used
        </span>
      </div>

      {/* Context menu */}
      {menuOpen && (
        <div className="absolute right-4 top-12 z-50 bg-charcoal border border-navy-mid rounded-lg shadow-lg py-1 min-w-[160px]">
          <button
            onClick={() => onArchive()}
            className="flex items-center gap-2 w-full px-3 py-2 text-sm text-stone hover:text-white hover:bg-navy transition-colors"
          >
            <Trash2 className="w-3.5 h-3.5" />
            Archive
          </button>
          <button
            onClick={() => onMerge()}
            className="flex items-center gap-2 w-full px-3 py-2 text-sm text-stone hover:text-white hover:bg-navy transition-colors"
          >
            <Merge className="w-3.5 h-3.5" />
            Merge into...
          </button>
        </div>
      )}
    </div>
  );
}
