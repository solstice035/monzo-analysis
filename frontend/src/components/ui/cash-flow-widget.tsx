import { ArrowDownLeft, ArrowUpRight } from "lucide-react";
import { cn, formatCurrency } from "@/lib/utils";

export interface CashFlowWidgetProps {
  income: number;
  spent: number;
  className?: string;
}

export function CashFlowWidget({ income, spent, className }: CashFlowWidgetProps) {
  const net = income - spent;
  const isPositive = net >= 0;

  return (
    <div className={cn("bg-charcoal rounded-xl border border-navy-mid p-4", className)}>
      <h3 className="text-xs text-stone uppercase tracking-wider mb-3">
        Cash Flow
      </h3>

      <div className="grid grid-cols-2 gap-4 mb-4">
        {/* Income */}
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-mint/10 flex items-center justify-center">
            <ArrowDownLeft size={16} strokeWidth={1.5} className="text-mint" />
          </div>
          <div>
            <div className="text-xs text-stone">Income</div>
            <div
              className="text-lg text-mint tabular-nums"
              style={{ fontFamily: "var(--font-mono)" }}
            >
              {formatCurrency(income)}
            </div>
          </div>
        </div>

        {/* Spent */}
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-coral/10 flex items-center justify-center">
            <ArrowUpRight size={16} strokeWidth={1.5} className="text-coral" />
          </div>
          <div>
            <div className="text-xs text-stone">Spent</div>
            <div
              className="text-lg text-coral tabular-nums"
              style={{ fontFamily: "var(--font-mono)" }}
            >
              {formatCurrency(spent)}
            </div>
          </div>
        </div>
      </div>

      {/* Net total */}
      <div className="pt-3 border-t border-navy-mid flex items-center justify-between">
        <span className="text-xs text-stone uppercase tracking-wider">Net</span>
        <span
          className={cn(
            "text-lg font-medium tabular-nums",
            isPositive ? "text-mint" : "text-coral"
          )}
          style={{ fontFamily: "var(--font-mono)" }}
        >
          {isPositive ? "+" : "-"}
          {formatCurrency(Math.abs(net))}
        </span>
      </div>
    </div>
  );
}
