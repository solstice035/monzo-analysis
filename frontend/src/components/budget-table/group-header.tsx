import { ChevronRight } from "lucide-react";
import { cn, formatCurrency } from "@/lib/utils";
import { getGroupIcon } from "@/lib/category-icons";
import type { BudgetGroupStatus } from "@/lib/api";

export interface GroupHeaderProps {
  group: BudgetGroupStatus;
  expanded: boolean;
  onToggle: () => void;
}

export function GroupHeader({ group, expanded, onToggle }: GroupHeaderProps) {
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
      className="grid items-center py-2 px-3 bg-navy-deep/50 border-b border-navy-mid cursor-pointer select-none group hover:bg-navy-deep/80 transition-colors"
      style={{ gridTemplateColumns: "1fr 120px 120px 120px 48px" }}
      onClick={onToggle}
    >
      <div className="flex items-center gap-2">
        <ChevronRight
          className={cn(
            "w-4 h-4 text-stone transition-transform duration-200",
            expanded && "rotate-90"
          )}
        />
        <GroupIcon size={16} strokeWidth={1.5} className="text-white" />
        <span className="text-sm font-semibold text-white uppercase tracking-wide">
          {group.name}
        </span>
        <span className="text-xs text-stone">({group.budget_count})</span>
      </div>

      <span
        className="text-sm text-right text-stone tabular-nums"
        style={{ fontFamily: "var(--font-mono)" }}
      >
        {formatCurrency(group.total_budget)}
      </span>

      <span
        className="text-sm text-right text-coral tabular-nums"
        style={{ fontFamily: "var(--font-mono)" }}
      >
        -{formatCurrency(group.total_spent)}
      </span>

      <span
        className={cn("text-sm font-medium text-right tabular-nums", remainingColor)}
        style={{ fontFamily: "var(--font-mono)" }}
      >
        {isOver ? `-${formatCurrency(Math.abs(group.remaining))}` : formatCurrency(group.remaining)}
      </span>

      <span />
    </div>
  );
}
