import { Trash2 } from "lucide-react";
import { cn, formatCurrency } from "@/lib/utils";
import { getCategoryIcon } from "@/lib/category-icons";
import { EditableAmount } from "@/components/ui/editable-amount";
import type { BudgetStatus } from "@/lib/api";

export interface BudgetRowProps {
  budget: BudgetStatus;
  onSaveAmount: (newAmountPence: number) => Promise<void>;
  onDelete: () => void;
  tabIndex?: number;
}

export function BudgetRow({ budget, onSaveAmount, onDelete, tabIndex }: BudgetRowProps) {
  const isOver = budget.spent > budget.amount;
  const percentage = budget.amount > 0
    ? (budget.spent / budget.amount) * 100
    : 0;
  const isWarning = percentage >= 80 && !isOver;

  const availableColor = isOver
    ? "text-coral"
    : isWarning
    ? "text-yellow"
    : "text-mint";

  const Icon = getCategoryIcon(budget.category);
  const displayName = budget.category.replace(/_/g, " ");

  return (
    <div
      className="grid items-center py-[10px] px-3 border-b border-navy-mid/20 hover:bg-navy-deep/30 transition-colors group"
      style={{ gridTemplateColumns: "1fr 120px 120px 120px 48px" }}
    >
      {/* Category */}
      <div className="flex items-center gap-2 pl-6">
        <Icon size={14} strokeWidth={1.5} className="text-stone" />
        <span className="text-sm text-white capitalize">{displayName}</span>
      </div>

      {/* Budgeted — editable */}
      <div className="text-right" onClick={(e) => e.stopPropagation()}>
        <EditableAmount
          value={budget.amount}
          onSave={onSaveAmount}
          tabIndex={tabIndex}
        />
      </div>

      {/* Activity */}
      <span
        className="text-sm text-right text-coral tabular-nums"
        style={{ fontFamily: "var(--font-mono)" }}
      >
        -{formatCurrency(budget.spent)}
      </span>

      {/* Available — colour-coded */}
      <span
        className={cn("text-sm font-medium text-right tabular-nums", availableColor)}
        style={{ fontFamily: "var(--font-mono)" }}
      >
        {isOver ? "-" : ""}
        {formatCurrency(Math.abs(budget.remaining))}
      </span>

      {/* Delete */}
      <div className="flex justify-center opacity-0 group-hover:opacity-100 transition-opacity">
        <button
          onClick={(e) => {
            e.stopPropagation();
            onDelete();
          }}
          className="p-1 text-stone hover:text-coral transition-colors"
        >
          <Trash2 size={14} />
        </button>
      </div>
    </div>
  );
}
