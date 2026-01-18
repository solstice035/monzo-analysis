import { forwardRef, type HTMLAttributes } from "react";
import { cn, formatCurrency } from "@/lib/utils";

export interface BudgetBarProps extends HTMLAttributes<HTMLDivElement> {
  name: string;
  spent: number;
  budget: number;
  emoji?: string;
}

const BudgetBar = forwardRef<HTMLDivElement, BudgetBarProps>(
  ({ className, name, spent, budget, emoji, ...props }, ref) => {
    const percentage = Math.min((spent / budget) * 100, 100);
    const isOver = spent > budget;
    const isWarning = percentage >= 80 && !isOver;

    let fillClass = "bg-gradient-to-r from-mint to-[#00FFD4]";
    if (isOver) {
      fillClass = "bg-gradient-to-r from-coral-deep to-coral";
    } else if (isWarning) {
      fillClass = "bg-gradient-to-r from-yellow to-[#FFE566]";
    }

    return (
      <div ref={ref} className={cn("", className)} {...props}>
        <div className="flex justify-between items-center mb-2">
          <span className="font-semibold text-white">
            {emoji && <span className="mr-2">{emoji}</span>}
            {name}
          </span>
          <span
            className="text-sm text-stone"
            style={{ fontFamily: "var(--font-mono)" }}
          >
            {formatCurrency(spent)} / {formatCurrency(budget)}
          </span>
        </div>
        <div className="h-3 bg-navy rounded-full overflow-hidden">
          <div
            className={cn("h-full rounded-full transition-all duration-500", fillClass)}
            style={{ width: `${percentage}%` }}
          />
        </div>
      </div>
    );
  }
);
BudgetBar.displayName = "BudgetBar";

export { BudgetBar };
