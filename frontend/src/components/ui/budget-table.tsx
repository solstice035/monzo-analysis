import { useState } from "react";
import { cn, formatCurrency } from "@/lib/utils";
import { BudgetGroupHeader } from "./budget-group-header";
import { BudgetTableRow } from "./budget-table-row";
import {
  useBudgetGroupStatuses,
  useSinkingFundsStatus,
  useUpdateBudget,
  useUpdateBudgetGroup,
  useDeleteBudget,
} from "@/hooks/useApi";
import { getCategoryIcon } from "@/lib/category-icons";
import type { SinkingFundStatus } from "@/lib/api";

export interface BudgetTableProps {
  selectedCategory: string | null;
  onSelectCategory: (category: string | null, budgetId?: string) => void;
  className?: string;
}

export function BudgetTable({
  selectedCategory,
  onSelectCategory,
  className,
}: BudgetTableProps) {
  const { data: budgetGroups, isLoading: groupsLoading } = useBudgetGroupStatuses();
  const { data: sinkingFunds } = useSinkingFundsStatus();
  const updateBudget = useUpdateBudget();
  const updateBudgetGroup = useUpdateBudgetGroup();
  const deleteBudget = useDeleteBudget();

  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set());
  const [sinkingFundsExpanded, setSinkingFundsExpanded] = useState(true);

  // Initialize all groups as expanded on first render
  const initExpanded = () => {
    if (budgetGroups && expandedGroups.size === 0) {
      setExpandedGroups(new Set(budgetGroups.map((g) => g.group_id)));
    }
  };

  // Call on render if we have groups and haven't expanded yet
  if (budgetGroups && budgetGroups.length > 0 && expandedGroups.size === 0) {
    initExpanded();
  }

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

  const handleEditBudgetAmount = (budgetId: string, newAmount: string) => {
    updateBudget.mutate({
      id: budgetId,
      data: { amount: parseInt(newAmount, 10) },
    });
  };

  const handleEditGroupName = (groupId: string, newName: string) => {
    updateBudgetGroup.mutate({
      id: groupId,
      data: { name: newName },
    });
  };

  const handleDeleteBudget = (budgetId: string) => {
    if (confirm("Delete this budget? This cannot be undone.")) {
      deleteBudget.mutate(budgetId);
    }
  };

  if (groupsLoading) {
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
          Visit the Budgets page to import or create budgets.
        </p>
      </div>
    );
  }

  return (
    <div
      className={cn(
        "rounded-xl border border-navy-mid overflow-hidden bg-navy",
        className
      )}
      role="table"
    >
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

      {/* Budget groups */}
      {budgetGroups.map((group) => {
        const isExpanded = expandedGroups.has(group.group_id);

        return (
          <div key={group.group_id}>
            <BudgetGroupHeader
              group={group}
              isExpanded={isExpanded}
              onToggle={() => toggleGroup(group.group_id)}
              onEditName={(name) => handleEditGroupName(group.group_id, name)}
            />

            {isExpanded &&
              group.budgets.map((budget) => (
                <BudgetTableRow
                  key={budget.budget_id}
                  budget={budget}
                  isSelected={selectedCategory === budget.category}
                  onSelect={() =>
                    onSelectCategory(
                      selectedCategory === budget.category ? null : budget.category,
                      budget.budget_id
                    )
                  }
                  onEditAmount={(amount) =>
                    handleEditBudgetAmount(budget.budget_id, amount)
                  }
                  onDelete={() => handleDeleteBudget(budget.budget_id)}
                />
              ))}
          </div>
        );
      })}

      {/* Sinking Funds section */}
      {sinkingFunds && sinkingFunds.length > 0 && (
        <div>
          {/* Sinking funds group header */}
          <div
            className="flex items-center gap-3 px-4 py-3 bg-charcoal/80 border-b border-t border-navy-mid cursor-pointer select-none group hover:bg-charcoal transition-colors"
            onClick={() => setSinkingFundsExpanded(!sinkingFundsExpanded)}
          >
            <button className="text-stone group-hover:text-white transition-colors shrink-0">
              {sinkingFundsExpanded ? (
                <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M6 9l6 6 6-6"/></svg>
              ) : (
                <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M9 6l6 6-6 6"/></svg>
              )}
            </button>
            {(() => {
              const TargetIcon = getCategoryIcon("savings");
              return <TargetIcon size={16} strokeWidth={1.5} className="text-white shrink-0" />;
            })()}
            <span className="text-sm font-bold text-white uppercase tracking-wide flex-1">
              Sinking Funds
            </span>
            <span
              className="text-xs text-stone shrink-0"
              style={{ fontFamily: "var(--font-mono)" }}
            >
              {sinkingFunds.filter((f) => f.on_track).length}/{sinkingFunds.length} on track
            </span>
          </div>

          {sinkingFundsExpanded &&
            sinkingFunds.map((fund) => (
              <SinkingFundRow
                key={fund.budget_id}
                fund={fund}
                isSelected={selectedCategory === fund.category}
                onSelect={() =>
                  onSelectCategory(
                    selectedCategory === fund.category ? null : fund.category,
                    fund.budget_id
                  )
                }
              />
            ))}
        </div>
      )}
    </div>
  );
}

// --- Sinking Fund Row ---

interface SinkingFundRowProps {
  fund: SinkingFundStatus;
  isSelected: boolean;
  onSelect: () => void;
}

function SinkingFundRow({ fund, isSelected, onSelect }: SinkingFundRowProps) {
  const percentage = fund.target_amount > 0
    ? Math.min(((fund.pot_balance || 0) / fund.target_amount) * 100, 100)
    : 0;

  const barColor = fund.on_track ? "bg-sky" : "bg-coral";
  const statusColor = fund.on_track ? "text-sky" : "text-coral";

  return (
    <div
      className={cn(
        "flex items-center gap-3 px-4 py-2.5 border-b border-navy-mid/50 cursor-pointer transition-all group hover:bg-navy-deep/50",
        isSelected && "bg-navy-deep border-l-2 border-l-sky",
        !isSelected && "border-l-2 border-l-transparent"
      )}
      onClick={onSelect}
      role="row"
    >
      {(() => {
        const FundIcon = getCategoryIcon(fund.category);
        return <FundIcon size={14} strokeWidth={1.5} className="text-stone shrink-0 ml-2" />;
      })()}
      <span className="text-sm text-white flex-1 min-w-0 truncate">
        {fund.budget_name || fund.category}
        {fund.pot_name && (
          <span className="text-xs text-sky ml-2">→ {fund.pot_name}</span>
        )}
      </span>

      {/* Progress bar */}
      <div className="w-24 shrink-0">
        <div className="h-1.5 bg-navy rounded-full overflow-hidden">
          <div
            className={cn("h-full rounded-full transition-all duration-300", barColor)}
            style={{ width: `${percentage}%` }}
          />
        </div>
      </div>

      {/* Target */}
      <span
        className="text-xs text-stone w-24 text-right shrink-0 tabular-nums"
        style={{ fontFamily: "var(--font-mono)" }}
      >
        {formatCurrency(fund.target_amount)}
      </span>

      {/* In pot */}
      <span
        className="text-xs text-stone w-20 text-right shrink-0 tabular-nums"
        style={{ fontFamily: "var(--font-mono)" }}
      >
        {formatCurrency(fund.pot_balance || 0)}
      </span>

      {/* Monthly needed */}
      <span
        className={cn("text-xs font-semibold w-20 text-right shrink-0 tabular-nums", statusColor)}
        style={{ fontFamily: "var(--font-mono)" }}
      >
        {formatCurrency(fund.monthly_contribution)}/mo
      </span>

      <div className="w-8" />
    </div>
  );
}
