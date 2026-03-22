import { forwardRef, type HTMLAttributes } from "react";
import { cn, formatCurrency, formatRelativeDate } from "@/lib/utils";
import { getCategoryIcon } from "@/lib/category-icons";

export interface TransactionRowProps extends HTMLAttributes<HTMLDivElement> {
  merchant: string;
  category: string;
  amount: number;
  date: string;
}

const TransactionRow = forwardRef<HTMLDivElement, TransactionRowProps>(
  ({ className, merchant, category, amount, date, ...props }, ref) => {
    const isExpense = amount < 0;
    const Icon = getCategoryIcon(category);

    return (
      <div
        ref={ref}
        className={cn(
          "grid items-center py-2 px-3 border-b border-navy-mid/20 transition-colors cursor-pointer hover:bg-navy-deep/20",
          className
        )}
        style={{ gridTemplateColumns: "28px 1fr auto auto" }}
        {...props}
      >
        <div className="w-7 h-7 rounded-lg bg-navy-mid/30 flex items-center justify-center">
          <Icon size={14} strokeWidth={1.5} className="text-stone" />
        </div>
        <div className="pl-3 min-w-0">
          <div className="text-sm font-medium text-white truncate">{merchant}</div>
          <div className="text-xs text-stone truncate">
            {category.replace(/_/g, " ")} · {formatRelativeDate(date)}
          </div>
        </div>
        <div
          className={cn("text-sm font-medium tabular-nums pl-4", {
            "text-coral": isExpense,
            "text-mint": !isExpense,
          })}
          style={{ fontFamily: "var(--font-mono)" }}
        >
          {isExpense ? "-" : "+"}
          {formatCurrency(Math.abs(amount))}
        </div>
      </div>
    );
  }
);
TransactionRow.displayName = "TransactionRow";

export { TransactionRow };
