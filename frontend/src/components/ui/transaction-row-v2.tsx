import { forwardRef, type HTMLAttributes } from "react";
import { cn, formatCurrency, formatRelativeDate } from "@/lib/utils";
import { getCategoryIcon } from "@/lib/category-icons";
import { CategoryDropdown } from "./category-dropdown";

export interface TransactionRowV2Props extends HTMLAttributes<HTMLDivElement> {
  id: string;
  merchant: string;
  category: string;
  amount: number;
  date: string;
  onCategoryChange?: (id: string, newCategory: string) => void;
  isCategoryUpdating?: boolean;
  compact?: boolean;
}

const TransactionRowV2 = forwardRef<HTMLDivElement, TransactionRowV2Props>(
  (
    {
      className,
      id,
      merchant,
      category,
      amount,
      date,
      onCategoryChange,
      isCategoryUpdating = false,
      compact = false,
      ...props
    },
    ref
  ) => {
    const isExpense = amount < 0;
    const Icon = getCategoryIcon(category);

    return (
      <div
        ref={ref}
        className={cn(
          "grid items-center transition-all group",
          compact
            ? "px-3 py-1.5 hover:bg-navy-mid/30"
            : "px-3 py-2 hover:bg-navy-deep/20",
          "border-b border-navy-mid/20",
          className
        )}
        style={{ gridTemplateColumns: "28px 1fr auto auto" }}
        {...props}
      >
        {/* Icon */}
        <div className="w-7 h-7 rounded-lg bg-navy-mid/30 flex items-center justify-center shrink-0">
          <Icon size={14} strokeWidth={1.5} className="text-stone" />
        </div>

        {/* Details */}
        <div className="pl-3 min-w-0">
          <div className={cn("font-medium text-white truncate", compact ? "text-xs" : "text-sm")}>
            {merchant}
          </div>
          <div className="text-xs text-stone mt-0.5 flex items-center gap-1.5">
            {onCategoryChange ? (
              <CategoryDropdown
                currentCategory={category}
                onSelect={(newCat) => onCategoryChange(id, newCat)}
                disabled={isCategoryUpdating}
              />
            ) : (
              <span className="capitalize">{category.replace(/_/g, " ")}</span>
            )}
            <span className="text-navy-mid">·</span>
            <span>{formatRelativeDate(date)}</span>
          </div>
        </div>

        {/* Amount */}
        <div
          className={cn(
            "font-medium shrink-0 tabular-nums pl-4",
            compact ? "text-xs" : "text-sm",
            isExpense ? "text-coral" : "text-mint"
          )}
          style={{ fontFamily: "var(--font-mono)" }}
        >
          {isExpense ? "-" : "+"}
          {formatCurrency(Math.abs(amount))}
        </div>
      </div>
    );
  }
);
TransactionRowV2.displayName = "TransactionRowV2";

export { TransactionRowV2 };
