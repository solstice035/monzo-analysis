import { forwardRef, type HTMLAttributes } from "react";
import { cn, formatCurrency, formatRelativeDate } from "@/lib/utils";
import { categoryEmojis } from "./category-pill";

export interface TransactionRowProps extends HTMLAttributes<HTMLDivElement> {
  merchant: string;
  category: string;
  amount: number;
  date: string;
}

const TransactionRow = forwardRef<HTMLDivElement, TransactionRowProps>(
  ({ className, merchant, category, amount, date, ...props }, ref) => {
    const isExpense = amount < 0;
    const normalizedCategory = category.toLowerCase().replace(/\s+/g, "_");
    const emoji = categoryEmojis[normalizedCategory] || "📦";

    return (
      <div
        ref={ref}
        className={cn(
          "flex items-center p-4 bg-navy rounded-xl border border-transparent transition-all cursor-pointer hover:border-coral hover:translate-x-2",
          className
        )}
        {...props}
      >
        <div className="w-11 h-11 rounded-xl bg-charcoal flex items-center justify-center text-xl mr-4">
          {emoji}
        </div>
        <div className="flex-1">
          <div className="font-semibold text-white">{merchant}</div>
          <div className="text-sm text-slate capitalize">
            {category.replace(/_/g, " ")} · {formatRelativeDate(date)}
          </div>
        </div>
        <div
          className={cn("font-bold", {
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
