import { forwardRef, type HTMLAttributes } from "react";
import { cn } from "@/lib/utils";
import { getCategoryIcon } from "@/lib/category-icons";

const categoryStyles: Record<string, string> = {
  groceries: "bg-mint/20 text-mint",
  transport: "bg-sky/20 text-sky",
  eating_out: "bg-coral/20 text-coral-bright",
  bills: "bg-yellow/20 text-yellow",
  shopping: "bg-purple-400/20 text-purple-400",
  entertainment: "bg-orange-400/20 text-orange-400",
  general: "bg-stone/20 text-stone",
  expenses: "bg-coral/20 text-coral",
  cash: "bg-stone/20 text-stone",
  holidays: "bg-sky/20 text-sky",
};

export interface CategoryPillProps extends HTMLAttributes<HTMLSpanElement> {
  category: string;
  showIcon?: boolean;
}

const CategoryPill = forwardRef<HTMLSpanElement, CategoryPillProps>(
  ({ className, category, showIcon = true, ...props }, ref) => {
    const normalizedCategory = category.toLowerCase().replace(/\s+/g, "_");
    const style = categoryStyles[normalizedCategory] || categoryStyles.general;
    const Icon = getCategoryIcon(category);
    const displayName = category.replace(/_/g, " ");

    return (
      <span
        ref={ref}
        className={cn(
          "px-2.5 py-1 rounded-full text-xs font-medium inline-flex items-center gap-1.5 capitalize",
          style,
          className
        )}
        {...props}
      >
        {showIcon && <Icon size={12} strokeWidth={1.5} />}
        {displayName}
      </span>
    );
  }
);
CategoryPill.displayName = "CategoryPill";

export { CategoryPill, categoryStyles };
