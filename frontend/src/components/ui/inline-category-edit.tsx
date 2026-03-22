import { useState, useCallback } from "react";
import * as Popover from "@radix-ui/react-popover";
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
  "health",
  "subscriptions",
  "utilities",
  "education",
  "fitness",
];

export interface InlineCategoryEditProps {
  category: string;
  merchant?: string;
  onSave: (newCategory: string) => void;
  onCreateRule?: (merchant: string, category: string) => void;
}

export function InlineCategoryEdit({
  category,
  merchant,
  onSave,
  onCreateRule,
}: InlineCategoryEditProps) {
  const [open, setOpen] = useState(false);
  const [showRulePrompt, setShowRulePrompt] = useState(false);
  const [savedCategory, setSavedCategory] = useState("");

  const normalised = category.toLowerCase().replace(/\s+/g, "_");
  const Icon = getCategoryIcon(category);

  const handleSelect = useCallback(
    (cat: string) => {
      onSave(cat);
      setOpen(false);

      // Show rule prompt if merchant exists and category changed
      if (merchant && cat !== normalised) {
        setSavedCategory(cat);
        setShowRulePrompt(true);
        // Auto-dismiss after 5s
        setTimeout(() => setShowRulePrompt(false), 5000);
      }
    },
    [onSave, merchant, normalised]
  );

  return (
    <span className="relative inline-flex items-center">
      <Popover.Root open={open} onOpenChange={setOpen}>
        <Popover.Trigger asChild>
          <button
            className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-xs capitalize text-stone hover:text-white hover:bg-navy-mid/50 transition-colors cursor-pointer"
            onClick={(e) => e.stopPropagation()}
          >
            <Icon size={11} strokeWidth={1.5} />
            {category.replace(/_/g, " ")}
          </button>
        </Popover.Trigger>
        <Popover.Portal>
          <Popover.Content
            className="w-72 p-2 bg-navy-deep border border-navy-mid rounded-xl shadow-xl z-50"
            align="start"
            sideOffset={4}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="grid grid-cols-3 gap-1">
              {allCategories.map((cat) => {
                const CatIcon = getCategoryIcon(cat);
                const isSelected = cat === normalised;
                return (
                  <button
                    key={cat}
                    onClick={() => handleSelect(cat)}
                    className={cn(
                      "flex items-center gap-1.5 px-2 py-1.5 rounded-lg text-xs capitalize transition-colors",
                      isSelected
                        ? "bg-coral/20 text-coral"
                        : "text-stone hover:text-white hover:bg-navy-mid/50"
                    )}
                  >
                    <CatIcon size={12} strokeWidth={1.5} />
                    <span className="truncate">{cat.replace(/_/g, " ")}</span>
                  </button>
                );
              })}
            </div>
          </Popover.Content>
        </Popover.Portal>
      </Popover.Root>

      {/* Rule creation prompt */}
      {showRulePrompt && merchant && onCreateRule && (
        <span className="ml-2 inline-flex items-center gap-2 text-xs text-stone animate-in fade-in">
          Always categorise {merchant} as {savedCategory.replace(/_/g, " ")}?
          <button
            className="text-coral hover:text-coral-bright transition-colors"
            onClick={(e) => {
              e.stopPropagation();
              onCreateRule(merchant, savedCategory);
              setShowRulePrompt(false);
            }}
          >
            Create rule
          </button>
          <button
            className="text-stone hover:text-white transition-colors"
            onClick={(e) => {
              e.stopPropagation();
              setShowRulePrompt(false);
            }}
          >
            Skip
          </button>
        </span>
      )}
    </span>
  );
}
