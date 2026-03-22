import { useState, useMemo } from "react";
import { cn, formatCurrency } from "@/lib/utils";
import { GroupHeader } from "./group-header";
import { BudgetRow } from "./budget-row";
import { QuickAddRow } from "./quick-add-row";
import {
  useBudgetGroupStatuses,
  useUpdateBudget,
  useDeleteBudget,
  useCreateBudget,
} from "@/hooks/useApi";
import { useAccount } from "@/contexts/AccountContext";


export interface BudgetTableNewProps {
  /** If true, table is read-only (no editing, no quick-add, no delete) */
  readOnly?: boolean;
  /** Limit to first N groups (for dashboard preview) */
  maxGroups?: number;
  className?: string;
}

export function BudgetTableNew({
  readOnly = false,
  maxGroups,
  className,
}: BudgetTableNewProps) {
  const { selectedAccount } = useAccount();
  const { data: budgetGroups, isLoading } = useBudgetGroupStatuses();
  const updateBudget = useUpdateBudget();
  const deleteBudget = useDeleteBudget();
  const createBudget = useCreateBudget();

  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set());
  const [initialised, setInitialised] = useState(false);

  // Initialise all groups as expanded
  if (budgetGroups && budgetGroups.length > 0 && !initialised) {
    setExpandedGroups(new Set(budgetGroups.map((g) => g.group_id)));
    setInitialised(true);
  }

  const toggleGroup = (groupId: string) => {
    setExpandedGroups((prev) => {
      const next = new Set(prev);
      if (next.has(groupId)) next.delete(groupId);
      else next.add(groupId);
      return next;
    });
  };

  const handleSaveAmount = async (budgetId: string, newAmount: number) => {
    await updateBudget.mutateAsync({
      id: budgetId,
      data: { amount: newAmount },
    });
  };

  const handleDelete = (budgetId: string) => {
    if (confirm("Delete this budget? This cannot be undone.")) {
      deleteBudget.mutate(budgetId);
    }
  };

  const handleQuickAdd = (groupId: string, category: string, amountPence: number) => {
    if (!selectedAccount) return;
    createBudget.mutate({
      account_id: selectedAccount.id,
      category,
      amount: amountPence,
      period: "monthly",
      start_day: 1,
      group_id: groupId,
    } as any);
  };

  // Compute totals
  const totals = useMemo(() => {
    if (!budgetGroups) return { budget: 0, spent: 0, remaining: 0 };
    return budgetGroups.reduce(
      (acc, g) => ({
        budget: acc.budget + g.total_budget,
        spent: acc.spent + g.total_spent,
        remaining: acc.remaining + g.remaining,
      }),
      { budget: 0, spent: 0, remaining: 0 }
    );
  }, [budgetGroups]);

  const displayGroups = maxGroups
    ? (budgetGroups || []).slice(0, maxGroups)
    : budgetGroups || [];

  if (isLoading) {
    return (
      <div className={cn("text-center py-12 text-stone", className)}>
        Loading budgets...
      </div>
    );
  }

  if (!budgetGroups || budgetGroups.length === 0) {
    return (
      <div className={cn("text-center py-12", className)}>
        <p className="text-stone mb-2">No budget groups yet.</p>
        <p className="text-sm text-stone/60">
          Import budgets via CSV on the Budgets page.
        </p>
      </div>
    );
  }

  return (
    <div className={cn("rounded-xl border border-navy-mid overflow-hidden bg-navy", className)}>
      {/* Column headers */}
      <div
        className="grid items-center py-2 px-3 bg-charcoal border-b border-navy-mid text-xs text-stone uppercase tracking-wider sticky top-0 z-10"
        style={{ gridTemplateColumns: "1fr 120px 120px 120px 48px" }}
      >
        <span>Category</span>
        <span className="text-right">Budgeted</span>
        <span className="text-right">Activity</span>
        <span className="text-right">Available</span>
        <span />
      </div>

      {/* Groups */}
      {displayGroups.map((group) => {
        const isExpanded = expandedGroups.has(group.group_id);
        return (
          <div key={group.group_id}>
            <GroupHeader
              group={group}
              expanded={isExpanded}
              onToggle={() => toggleGroup(group.group_id)}
            />

            {isExpanded && (
              <>
                {group.budgets.map((budget, idx) => (
                  <BudgetRow
                    key={budget.budget_id}
                    budget={budget}
                    onSaveAmount={(val) => handleSaveAmount(budget.budget_id, val)}
                    onDelete={() => handleDelete(budget.budget_id)}
                    tabIndex={readOnly ? undefined : idx + 1}
                  />
                ))}

                {!readOnly && (
                  <QuickAddRow
                    onAdd={(cat, amount) => handleQuickAdd(group.group_id, cat, amount)}
                    existingCategories={group.budgets.map((b) => b.category)}
                  />
                )}
              </>
            )}
          </div>
        );
      })}

      {/* Grand total footer */}
      {!maxGroups && (
        <div
          className="grid items-center py-2 px-3 border-t-2 border-navy-mid bg-charcoal sticky bottom-0"
          style={{ gridTemplateColumns: "1fr 120px 120px 120px 48px" }}
        >
          <span className="text-sm font-semibold text-white uppercase">Total</span>
          <span
            className="text-sm font-semibold text-right text-white tabular-nums"
            style={{ fontFamily: "var(--font-mono)" }}
          >
            {formatCurrency(totals.budget)}
          </span>
          <span
            className="text-sm font-semibold text-right text-coral tabular-nums"
            style={{ fontFamily: "var(--font-mono)" }}
          >
            -{formatCurrency(totals.spent)}
          </span>
          <span
            className={cn(
              "text-sm font-semibold text-right tabular-nums",
              totals.remaining < 0 ? "text-coral" : "text-mint"
            )}
            style={{ fontFamily: "var(--font-mono)" }}
          >
            {totals.remaining < 0 ? "-" : ""}
            {formatCurrency(Math.abs(totals.remaining))}
          </span>
          <span />
        </div>
      )}
    </div>
  );
}
