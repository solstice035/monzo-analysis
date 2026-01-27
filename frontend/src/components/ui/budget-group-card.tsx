import { forwardRef, useState, type HTMLAttributes } from "react";
import { cn, formatCurrency } from "@/lib/utils";
import { BudgetBar } from "./budget-bar";
import type { BudgetGroupStatus } from "@/lib/api";

export interface BudgetGroupCardProps extends HTMLAttributes<HTMLDivElement> {
  group: BudgetGroupStatus;
  categoryEmojis?: Record<string, string>;
}

const BudgetGroupCard = forwardRef<HTMLDivElement, BudgetGroupCardProps>(
  ({ className, group, categoryEmojis = {}, ...props }, ref) => {
    const [expanded, setExpanded] = useState(false);
    const percentage = Math.min((group.total_spent / group.total_budget) * 100, 100);
    const isOver = group.total_spent > group.total_budget;
    const isWarning = percentage >= 80 && !isOver;

    let statusColor = "border-mint";
    let statusBg = "bg-mint/10";
    let statusText = "text-mint";
    if (isOver) {
      statusColor = "border-coral";
      statusBg = "bg-coral/10";
      statusText = "text-coral";
    } else if (isWarning) {
      statusColor = "border-yellow";
      statusBg = "bg-yellow/10";
      statusText = "text-yellow";
    }

    return (
      <div
        ref={ref}
        className={cn(
          "rounded-2xl p-4 bg-gradient-to-br from-charcoal to-navy-deep border transition-all duration-200 cursor-pointer hover:scale-[1.01]",
          statusColor,
          className
        )}
        onClick={() => setExpanded(!expanded)}
        {...props}
      >
        {/* Header */}
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-3">
            <span className="text-2xl">{group.icon || "📂"}</span>
            <div>
              <h3 className="font-semibold text-white text-lg">{group.name}</h3>
              <span className="text-xs text-stone">
                {group.budget_count} budget{group.budget_count !== 1 ? "s" : ""}
              </span>
            </div>
          </div>
          <div className="text-right">
            <div
              className="font-display text-2xl text-white"
              style={{ fontFamily: "var(--font-display)" }}
            >
              {formatCurrency(group.total_spent)}
            </div>
            <div className="text-xs text-stone">
              of {formatCurrency(group.total_budget)}
            </div>
          </div>
        </div>

        {/* Progress bar */}
        <div className="mb-3">
          <div className="h-2 bg-navy rounded-full overflow-hidden">
            <div
              className={cn(
                "h-full rounded-full transition-all duration-500",
                isOver
                  ? "bg-gradient-to-r from-coral-deep to-coral"
                  : isWarning
                  ? "bg-gradient-to-r from-yellow to-[#FFE566]"
                  : "bg-gradient-to-r from-mint to-[#00FFD4]"
              )}
              style={{ width: `${percentage}%` }}
            />
          </div>
        </div>

        {/* Status badge and remaining */}
        <div className="flex items-center justify-between">
          <span
            className={cn(
              "px-2 py-1 rounded-full text-xs font-medium",
              statusBg,
              statusText
            )}
          >
            {percentage.toFixed(0)}% used
          </span>
          <span
            className={cn(
              "text-sm font-mono",
              isOver ? "text-coral" : "text-stone"
            )}
            style={{ fontFamily: "var(--font-mono)" }}
          >
            {isOver
              ? `-${formatCurrency(Math.abs(group.remaining))} over`
              : `${formatCurrency(group.remaining)} left`}
          </span>
        </div>

        {/* Expanded: Show individual budgets */}
        {expanded && group.budgets.length > 0 && (
          <div
            className="mt-4 pt-4 border-t border-navy-mid space-y-4"
            onClick={(e) => e.stopPropagation()}
          >
            {group.budgets.map((budget) => (
              <BudgetBar
                key={budget.budget_id}
                name={budget.category.replace(/_/g, " ")}
                spent={budget.spent}
                budget={budget.amount}
                emoji={categoryEmojis[budget.category] || ""}
              />
            ))}
          </div>
        )}

        {/* Expand/Collapse indicator */}
        <div className="flex justify-center mt-2">
          <span className="text-stone text-xs">
            {expanded ? "▲ Collapse" : "▼ View details"}
          </span>
        </div>
      </div>
    );
  }
);
BudgetGroupCard.displayName = "BudgetGroupCard";

export { BudgetGroupCard };
