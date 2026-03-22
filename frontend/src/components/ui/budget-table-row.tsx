import { MoreHorizontal, Trash2 } from "lucide-react";
import { useState, useRef, useEffect } from "react";
import { cn, formatCurrency } from "@/lib/utils";
import { InlineEdit } from "./inline-edit";
import { getCategoryIcon } from "@/lib/category-icons";
import type { BudgetStatus } from "@/lib/api";

export interface BudgetTableRowProps {
  budget: BudgetStatus;
  isSelected: boolean;
  onSelect: () => void;
  onEditAmount?: (newAmount: string) => void;
  onDelete?: () => void;
  isEditingAmount?: boolean;
  className?: string;
}

export function BudgetTableRow({
  budget,
  isSelected,
  onSelect,
  onEditAmount,
  onDelete,
  isEditingAmount = false,
  className,
}: BudgetTableRowProps) {
  const [showMenu, setShowMenu] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  const percentage = budget.amount > 0
    ? Math.min((budget.spent / budget.amount) * 100, 100)
    : 0;
  const isOver = budget.spent > budget.amount;
  const isWarning = percentage >= 80 && !isOver;

  const availableColor = isOver
    ? "text-coral"
    : isWarning
    ? "text-yellow"
    : "text-mint";

  const Icon = getCategoryIcon(budget.category);
  const displayName = budget.category.replace(/_/g, " ");

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setShowMenu(false);
      }
    }
    if (showMenu) {
      document.addEventListener("mousedown", handleClickOutside);
      return () => document.removeEventListener("mousedown", handleClickOutside);
    }
  }, [showMenu]);

  return (
    <div
      className={cn(
        "grid items-center py-[10px] px-3 border-b border-navy-mid/20 cursor-pointer transition-all group hover:bg-navy-deep/30",
        isSelected && "bg-navy-deep border-l-2 border-l-coral",
        !isSelected && "border-l-2 border-l-transparent",
        className
      )}
      style={{ gridTemplateColumns: "1fr 120px 120px 120px 48px" }}
      onClick={onSelect}
      role="row"
    >
      {/* Category icon + name */}
      <div className="flex items-center gap-2 pl-6">
        <Icon size={14} strokeWidth={1.5} className="text-stone" />
        <span className="text-sm text-white capitalize truncate">
          {displayName}
        </span>
      </div>

      {/* Budgeted amount (editable) */}
      <div className="text-right" onClick={(e) => e.stopPropagation()}>
        {onEditAmount ? (
          <InlineEdit
            value={budget.amount.toString()}
            onSave={onEditAmount}
            type="currency"
            isSaving={isEditingAmount}
            className="text-sm"
            displayClassName="text-sm text-stone"
          />
        ) : (
          <span
            className="text-sm text-stone tabular-nums"
            style={{ fontFamily: "var(--font-mono)" }}
          >
            {formatCurrency(budget.amount)}
          </span>
        )}
      </div>

      {/* Activity (spent) */}
      <span
        className="text-sm text-coral text-right tabular-nums"
        style={{ fontFamily: "var(--font-mono)" }}
      >
        -{formatCurrency(budget.spent)}
      </span>

      {/* Available (colour-coded) */}
      <span
        className={cn(
          "text-sm font-medium text-right tabular-nums",
          availableColor
        )}
        style={{ fontFamily: "var(--font-mono)" }}
      >
        {isOver ? "-" : ""}
        {formatCurrency(Math.abs(budget.remaining))}
      </span>

      {/* Overflow menu */}
      <div className="relative flex justify-center" ref={menuRef}>
        <button
          onClick={(e) => {
            e.stopPropagation();
            setShowMenu(!showMenu);
          }}
          className="p-1 opacity-0 group-hover:opacity-100 text-stone hover:text-white transition-all"
        >
          <MoreHorizontal className="w-4 h-4" />
        </button>

        {showMenu && (
          <div className="absolute z-50 right-0 top-full mt-1 w-36 bg-navy-deep border border-navy-mid rounded-lg shadow-xl overflow-hidden">
            {onDelete && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setShowMenu(false);
                  onDelete();
                }}
                className="w-full px-3 py-2 text-left text-sm text-coral hover:bg-navy-mid flex items-center gap-2 transition-colors"
              >
                <Trash2 className="w-3.5 h-3.5" />
                Delete
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
