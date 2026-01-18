import { forwardRef, type HTMLAttributes } from "react";
import { cn } from "@/lib/utils";

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

const categoryEmojis: Record<string, string> = {
  groceries: "🛒",
  transport: "🚗",
  eating_out: "🍽️",
  bills: "📄",
  shopping: "🛍️",
  entertainment: "🎬",
  general: "📦",
  expenses: "💼",
  cash: "💵",
  holidays: "✈️",
};

export interface CategoryPillProps extends HTMLAttributes<HTMLSpanElement> {
  category: string;
  showEmoji?: boolean;
}

const CategoryPill = forwardRef<HTMLSpanElement, CategoryPillProps>(
  ({ className, category, showEmoji = true, ...props }, ref) => {
    const normalizedCategory = category.toLowerCase().replace(/\s+/g, "_");
    const style = categoryStyles[normalizedCategory] || categoryStyles.general;
    const emoji = categoryEmojis[normalizedCategory] || "📦";
    const displayName = category.replace(/_/g, " ");

    return (
      <span
        ref={ref}
        className={cn(
          "px-4 py-2 rounded-full text-sm font-semibold inline-flex items-center gap-2 capitalize",
          style,
          className
        )}
        {...props}
      >
        {showEmoji && <span>{emoji}</span>}
        {displayName}
      </span>
    );
  }
);
CategoryPill.displayName = "CategoryPill";

export { CategoryPill, categoryStyles, categoryEmojis };
