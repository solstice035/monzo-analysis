import { forwardRef, type HTMLAttributes } from "react";
import { cn } from "@/lib/utils";

export interface StatBlockProps extends HTMLAttributes<HTMLDivElement> {
  label: string;
  value: string;
  change?: string;
  changeType?: "positive" | "negative" | "neutral";
}

const StatBlock = forwardRef<HTMLDivElement, StatBlockProps>(
  ({ className, label, value, change, changeType = "neutral", ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          "bg-charcoal rounded-2xl p-6 border border-navy-mid",
          className
        )}
        {...props}
      >
        <div className="text-xs font-semibold uppercase tracking-wider text-stone mb-2">
          {label}
        </div>
        <div
          className="text-4xl text-white"
          style={{ fontFamily: "var(--font-display)", letterSpacing: "0.02em" }}
        >
          {value}
        </div>
        {change && (
          <div
            className={cn("text-sm font-semibold mt-1", {
              "text-mint": changeType === "positive",
              "text-coral": changeType === "negative",
              "text-stone": changeType === "neutral",
            })}
          >
            {change}
          </div>
        )}
      </div>
    );
  }
);
StatBlock.displayName = "StatBlock";

export { StatBlock };
