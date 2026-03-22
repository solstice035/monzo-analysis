import { useState, useRef, useEffect } from "react";
import { Plus, X } from "lucide-react";

const availableCategories = [
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

export interface QuickAddRowProps {
  onAdd: (category: string, amountPence: number) => void;
  existingCategories: string[];
}

export function QuickAddRow({ onAdd, existingCategories }: QuickAddRowProps) {
  const [isAdding, setIsAdding] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState("");
  const [amountStr, setAmountStr] = useState("");
  const amountRef = useRef<HTMLInputElement>(null);

  const filteredCategories = availableCategories.filter(
    (c) => !existingCategories.includes(c)
  );

  useEffect(() => {
    if (isAdding && filteredCategories.length > 0 && !selectedCategory) {
      setSelectedCategory(filteredCategories[0]);
    }
  }, [isAdding, filteredCategories, selectedCategory]);

  const handleSubmit = () => {
    const pence = Math.round(parseFloat(amountStr) * 100);
    if (!selectedCategory || isNaN(pence) || pence <= 0) return;
    onAdd(selectedCategory, pence);
    setIsAdding(false);
    setSelectedCategory("");
    setAmountStr("");
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      e.preventDefault();
      handleSubmit();
    }
    if (e.key === "Escape") {
      setIsAdding(false);
      setSelectedCategory("");
      setAmountStr("");
    }
  };

  if (!isAdding) {
    return (
      <div className="py-1.5 px-3 pl-9">
        <button
          className="flex items-center gap-1.5 text-xs text-stone hover:text-white transition-colors"
          onClick={() => setIsAdding(true)}
        >
          <Plus size={14} />
          <span>Add category</span>
        </button>
      </div>
    );
  }

  return (
    <div
      className="grid items-center py-1.5 px-3 border-b border-navy-mid/20 bg-navy-deep/20"
      style={{ gridTemplateColumns: "1fr 120px 120px 120px 48px" }}
    >
      <div className="pl-6">
        <select
          className="bg-navy border border-navy-mid rounded px-2 py-1 text-sm text-white w-40 capitalize"
          value={selectedCategory}
          onChange={(e) => setSelectedCategory(e.target.value)}
          autoFocus
        >
          {filteredCategories.map((cat) => (
            <option key={cat} value={cat}>
              {cat.replace(/_/g, " ")}
            </option>
          ))}
        </select>
      </div>
      <div className="text-right">
        <input
          ref={amountRef}
          type="number"
          step="0.01"
          placeholder="0.00"
          value={amountStr}
          onChange={(e) => setAmountStr(e.target.value)}
          onKeyDown={handleKeyDown}
          className="bg-navy border border-coral/50 rounded px-2 py-1 text-sm font-mono text-white text-right w-24"
          style={{ fontFamily: "var(--font-mono)" }}
        />
      </div>
      <span className="text-sm text-stone text-right">—</span>
      <span className="text-sm text-stone text-right">—</span>
      <div className="flex justify-center">
        <button
          onClick={() => {
            setIsAdding(false);
            setSelectedCategory("");
            setAmountStr("");
          }}
          className="p-1 text-stone hover:text-coral"
        >
          <X size={14} />
        </button>
      </div>
    </div>
  );
}
