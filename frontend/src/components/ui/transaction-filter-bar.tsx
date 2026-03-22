import { ChevronLeft, ChevronRight, Search } from "lucide-react";
import { cn } from "@/lib/utils";

const categories = [
  "All",
  "groceries",
  "eating_out",
  "transport",
  "shopping",
  "entertainment",
  "bills",
  "general",
];

export interface TransactionFilterBarProps {
  monthLabel: string;
  monthOffset: number;
  onPrevMonth: () => void;
  onNextMonth: () => void;
  searchQuery: string;
  onSearchChange: (value: string) => void;
  selectedCategory: string;
  onCategoryChange: (category: string) => void;
}

export function TransactionFilterBar({
  monthLabel,
  monthOffset,
  onPrevMonth,
  onNextMonth,
  searchQuery,
  onSearchChange,
  selectedCategory,
  onCategoryChange,
}: TransactionFilterBarProps) {
  return (
    <div className="flex items-center gap-3 py-2 px-3 bg-charcoal rounded-xl mb-4 sticky top-0 z-20">
      {/* Month navigation */}
      <button
        onClick={onPrevMonth}
        className="p-1 text-stone hover:text-white transition-colors"
      >
        <ChevronLeft size={16} />
      </button>
      <span className="text-sm font-medium text-white min-w-[120px] text-center">
        {monthLabel}
      </span>
      <button
        onClick={onNextMonth}
        disabled={monthOffset >= 0}
        className={cn(
          "p-1 transition-colors",
          monthOffset >= 0
            ? "text-navy-mid cursor-not-allowed"
            : "text-stone hover:text-white"
        )}
      >
        <ChevronRight size={16} />
      </button>

      {/* Divider */}
      <div className="w-px h-5 bg-navy-mid" />

      {/* Search */}
      <div className="relative flex-1 max-w-xs">
        <Search
          size={14}
          className="absolute left-2 top-1/2 -translate-y-1/2 text-stone"
        />
        <input
          type="text"
          placeholder="Search..."
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          className="w-full pl-7 pr-3 py-1.5 rounded-lg bg-navy border border-navy-mid text-sm text-white placeholder:text-stone focus:border-coral focus:outline-none transition-colors"
        />
      </div>

      {/* Divider */}
      <div className="w-px h-5 bg-navy-mid" />

      {/* Category pills */}
      <div className="flex gap-1.5 overflow-x-auto">
        {categories.map((cat) => (
          <button
            key={cat}
            onClick={() => onCategoryChange(cat)}
            className={cn(
              "px-2.5 py-1 rounded-full text-xs font-medium whitespace-nowrap transition-colors capitalize",
              cat === selectedCategory
                ? "bg-coral text-white"
                : "text-stone hover:text-white hover:bg-navy-mid"
            )}
          >
            {cat === "All" ? "All" : cat.replace(/_/g, " ")}
          </button>
        ))}
      </div>
    </div>
  );
}
