import { useState } from "react";
import { TopBarBudget } from "@/components/ui/top-bar-budget";
import { BudgetTable } from "@/components/ui/budget-table";
import { ContextPanel } from "@/components/ui/context-panel";

export function Dashboard() {
  const [monthOffset, setMonthOffset] = useState(0);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);

  const handleSelectCategory = (category: string | null) => {
    setSelectedCategory(category);
  };

  return (
    <div className="flex flex-col h-[calc(100vh-2rem)]">
      {/* TopBar with month navigation */}
      <TopBarBudget
        monthOffset={monthOffset}
        onPrevMonth={() => setMonthOffset((m) => m - 1)}
        onNextMonth={() => {
          if (monthOffset < 0) setMonthOffset((m) => m + 1);
        }}
      />

      {/* Two-panel layout */}
      <div className="flex gap-4 flex-1 min-h-0">
        {/* Left panel — Budget Table (60%) */}
        <div className="w-[60%] overflow-y-auto">
          <BudgetTable
            selectedCategory={selectedCategory}
            onSelectCategory={handleSelectCategory}
          />
        </div>

        {/* Right panel — Context Panel (40%) */}
        <div className="w-[40%] overflow-hidden">
          <ContextPanel selectedCategory={selectedCategory} />
        </div>
      </div>
    </div>
  );
}
