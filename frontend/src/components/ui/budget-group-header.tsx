import { ChevronDown, ChevronRight, Plus } from "lucide-react";
import { cn, formatCurrency } from "@/lib/utils";
import { InlineEdit } from "./inline-edit";
import { getGroupIcon } from "@/lib/category-icons";
import type { BudgetGroupStatus } from "@/lib/api";

export interface BudgetGroupHeaderProps {
  group: BudgetGroupStatus;
  isExpanded: boolean;
  onToggle: () => void;
  onEditName?: (newName: string) => void;
  onAddBudget?: () => void;
  isEditingName?: boolean;
  className?: string;
}

export function BudgetGroupHeader({
  group,
  isExpanded,
  onToggle,
  onEditName,
  onAddBudget,
  isEditingName = false,
  className,
}: BudgetGroupHeaderProps) {
  const isOver = group.total_spent > group.total_budget;
  const percentage = group.total_budget > 0
    ? (group.total_spent / group.total_budget) * 100
    : 0;
  const isWarning = percentage >= 80 && !isOver;

  const remainingColor = isOver
    ? "text-coral"
    : isWarning
    ? "text-yellow"
    : "text-mint";

  const GroupIcon = getGroupIcon(group.icon);

  return (
    <div
      className={cn(
        "grid items-center py-2 px-3 bg-navy-deep/50 border-b border-navy-mid cursor-pointer select-none group hover:bg-navy-deep/80 transition-colors",
        className
      )}
      style={{ gridTemplateColumns: "1fr 120px 120px 120px 48px" }}
      onClick={onToggle}
      role="rowgroup"
    >
      {/* Group name with chevron + icon */}
      <div className="flex items-center gap-2">
        <button className="text-stone group-hover:text-white transition-colors shrink-0">
          {isExpanded ? (
            <ChevronDown className="w-4 h-4" />
          ) : (
            <ChevronRight className="w-4 h-4" />
          )}
        </button>
        <GroupIcon size={16} strokeWidth={1.5} className="text-white shrink-0" />
        <div className="min-w-0" onClick={(e) => e.stopPropagation()}>
          {onEditName ? (
            <InlineEdit
              value={group.name}
              onSave={onEditName}
              isSaving={isEditingName}
              className="text-sm font-semibold text-white uppercase tracking-wide"
              displayClassName="text-sm font-semibold text-white uppercase tracking-wide"
            />
          ) : (
            <span className="text-sm font-semibold text-white uppercase tracking-wide">
              {group.name}
            </span>
          )}
        </div>
        <span className="text-xs text-stone">({group.budget_count})</span>

        {/* Add budget button */}
        {onAddBudget && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onAddBudget();
            }}
            className="opacity-0 group-hover:opacity-100 p-1 text-stone hover:text-coral transition-all shrink-0"
            title="Add budget to this group"
          >
            <Plus className="w-3.5 h-3.5" />
          </button>
        )}
      </div>

      {/* Budgeted total */}
      <span
        className="text-sm text-right text-stone tabular-nums"
        style={{ fontFamily: "var(--font-mono)" }}
      >
        {formatCurrency(group.total_budget)}
      </span>

      {/* Activity total */}
      <span
        className="text-sm text-right text-coral tabular-nums"
        style={{ fontFamily: "var(--font-mono)" }}
      >
        -{formatCurrency(group.total_spent)}
      </span>

      {/* Available total */}
      <span
        className={cn("text-sm font-medium text-right tabular-nums", remainingColor)}
        style={{ fontFamily: "var(--font-mono)" }}
      >
        {isOver
          ? `-${formatCurrency(Math.abs(group.remaining))}`
          : formatCurrency(group.remaining)}
      </span>

      <span />
    </div>
  );
}
