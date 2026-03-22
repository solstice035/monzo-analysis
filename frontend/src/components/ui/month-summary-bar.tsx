import { cn, formatCurrency } from "@/lib/utils";

export interface MonthSummaryBarProps {
  totalSpent: number;
  totalBudget: number;
  totalRemaining: number;
  /** Day of month (1-31) */
  currentDay: number;
  /** Total days in month */
  totalDays: number;
  className?: string;
}

export function MonthSummaryBar({
  totalSpent,
  totalBudget,
  totalRemaining,
  currentDay,
  totalDays,
  className,
}: MonthSummaryBarProps) {
  const spentPercentage = totalBudget > 0
    ? Math.min((totalSpent / totalBudget) * 100, 100)
    : 0;

  const expectedPercentage = totalDays > 0
    ? (currentDay / totalDays) * 100
    : 0;

  const isOver = totalRemaining < 0;
  const isWarning = !isOver && totalBudget > 0 && spentPercentage >= 80;
  const onTrack = spentPercentage <= expectedPercentage;

  const availableColor = isOver
    ? "text-coral"
    : isWarning
    ? "text-yellow"
    : "text-mint";

  return (
    <div className={cn("py-3", className)}>
      {/* Summary stats */}
      <div className="flex items-baseline gap-6 mb-2">
        <div>
          <span className="text-xs text-stone uppercase tracking-wider">Spent</span>
          <span
            className="text-xl text-white ml-2 tabular-nums"
            style={{ fontFamily: "var(--font-mono)" }}
          >
            {formatCurrency(totalSpent)}
          </span>
        </div>
        <div>
          <span className="text-xs text-stone uppercase tracking-wider">Available</span>
          <span
            className={cn("text-xl ml-2 tabular-nums", availableColor)}
            style={{ fontFamily: "var(--font-mono)" }}
          >
            {isOver ? "-" : ""}
            {formatCurrency(Math.abs(totalRemaining))}
          </span>
        </div>
        <div>
          <span className="text-xs text-stone uppercase tracking-wider">Budget</span>
          <span
            className="text-xl text-stone ml-2 tabular-nums"
            style={{ fontFamily: "var(--font-mono)" }}
          >
            {formatCurrency(totalBudget)}
          </span>
        </div>
        <div className="flex-1" />
        <div>
          <span
            className={cn("text-lg tabular-nums", onTrack ? "text-mint" : "text-coral")}
            style={{ fontFamily: "var(--font-mono)" }}
          >
            {spentPercentage.toFixed(0)}%
          </span>
          <span className="text-xs text-stone ml-1">
            {onTrack ? "on track" : "ahead of pace"}
          </span>
        </div>
      </div>

      {/* Progress bar with expected-pace marker */}
      <div className="relative h-1.5 bg-navy-mid/50 rounded-full overflow-hidden">
        <div
          className={cn(
            "h-full rounded-full transition-all duration-500",
            isOver ? "bg-coral" : isWarning ? "bg-yellow" : "bg-mint"
          )}
          style={{ width: `${spentPercentage}%` }}
        />
        {/* Expected pace marker */}
        <div
          className="absolute top-0 h-full w-0.5 bg-white/60"
          style={{ left: `${expectedPercentage}%` }}
        />
      </div>

      {/* Days info */}
      <div className="flex justify-between mt-1.5">
        <span className="text-xs text-stone">
          Day {currentDay} of {totalDays}
        </span>
        <span className="text-xs text-stone">
          {totalDays - currentDay} days remaining
        </span>
      </div>
    </div>
  );
}
