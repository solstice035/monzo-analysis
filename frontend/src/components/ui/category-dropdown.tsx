import { useState, useRef, useEffect } from "react";
import { cn } from "@/lib/utils";
import { getCategoryIcon } from "@/lib/category-icons";

const allCategories = [
  "groceries",
  "eating_out",
  "transport",
  "shopping",
  "entertainment",
  "bills",
  "general",
  "cash",
  "expenses",
  "holidays",
];

export interface CategoryDropdownProps {
  currentCategory: string;
  onSelect: (category: string) => void;
  disabled?: boolean;
  className?: string;
}

export function CategoryDropdown({
  currentCategory,
  onSelect,
  disabled = false,
  className,
}: CategoryDropdownProps) {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    }
    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
      return () => document.removeEventListener("mousedown", handleClickOutside);
    }
  }, [isOpen]);

  const normalised = currentCategory.toLowerCase().replace(/\s+/g, "_");
  const Icon = getCategoryIcon(currentCategory);
  const displayName = currentCategory.replace(/_/g, " ");

  const categoryColors: Record<string, string> = {
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

  const pillStyle = categoryColors[normalised] || categoryColors.general;

  return (
    <div ref={dropdownRef} className={cn("relative inline-block", className)}>
      <button
        onClick={(e) => {
          e.stopPropagation();
          if (!disabled) setIsOpen(!isOpen);
        }}
        disabled={disabled}
        className={cn(
          "px-2.5 py-1 rounded-full text-xs font-medium inline-flex items-center gap-1.5 capitalize transition-all",
          pillStyle,
          !disabled && "hover:ring-1 hover:ring-coral/30 cursor-pointer",
          disabled && "opacity-60 cursor-default"
        )}
      >
        <Icon size={12} strokeWidth={1.5} />
        {displayName}
      </button>

      {isOpen && (
        <div className="absolute z-50 top-full left-0 mt-1 w-48 bg-navy-deep border border-navy-mid rounded-xl shadow-xl overflow-hidden">
          {allCategories.map((cat) => {
            const CatIcon = getCategoryIcon(cat);
            const isSelected = cat === normalised;
            return (
              <button
                key={cat}
                onClick={(e) => {
                  e.stopPropagation();
                  onSelect(cat);
                  setIsOpen(false);
                }}
                className={cn(
                  "w-full px-3 py-2 text-left text-sm flex items-center gap-2 capitalize transition-colors",
                  isSelected
                    ? "bg-coral/20 text-coral"
                    : "text-stone hover:bg-navy-mid hover:text-white"
                )}
              >
                <CatIcon size={14} strokeWidth={1.5} />
                {cat.replace(/_/g, " ")}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
