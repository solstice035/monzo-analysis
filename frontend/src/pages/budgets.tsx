import { TopBar } from "@/components/layout";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { BudgetBar } from "@/components/ui/budget-bar";
import { Button } from "@/components/ui/button";
import { Plus } from "lucide-react";

// Mock data - will be replaced with real API calls
const mockBudgets = [
  { id: "1", name: "Groceries", spent: 28500, budget: 40000, emoji: "🛒", period: "monthly" },
  { id: "2", name: "Eating Out", spent: 16500, budget: 20000, emoji: "🍽️", period: "monthly" },
  { id: "3", name: "Shopping", spent: 31200, budget: 25000, emoji: "🛍️", period: "monthly" },
  { id: "4", name: "Transport", spent: 9400, budget: 15000, emoji: "🚗", period: "monthly" },
  { id: "5", name: "Entertainment", spent: 4500, budget: 10000, emoji: "🎬", period: "monthly" },
  { id: "6", name: "Bills", spent: 85000, budget: 85000, emoji: "📄", period: "monthly" },
];

export function Budgets() {
  const totalBudget = mockBudgets.reduce((sum, b) => sum + b.budget, 0);
  const totalSpent = mockBudgets.reduce((sum, b) => sum + b.spent, 0);

  return (
    <div>
      <TopBar
        title="BUDGETS"
        subtitle={`${mockBudgets.length} active budgets`}
        showSync={false}
      />

      {/* Summary */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        <div className="bg-charcoal rounded-2xl p-6 border border-navy-mid">
          <div className="text-xs font-semibold uppercase tracking-wider text-stone mb-2">
            TOTAL BUDGET
          </div>
          <div
            className="text-4xl text-white"
            style={{ fontFamily: "var(--font-display)" }}
          >
            £{(totalBudget / 100).toLocaleString()}
          </div>
        </div>
        <div className="bg-charcoal rounded-2xl p-6 border border-navy-mid">
          <div className="text-xs font-semibold uppercase tracking-wider text-stone mb-2">
            TOTAL SPENT
          </div>
          <div
            className="text-4xl text-coral"
            style={{ fontFamily: "var(--font-display)" }}
          >
            £{(totalSpent / 100).toLocaleString()}
          </div>
        </div>
        <div className="bg-charcoal rounded-2xl p-6 border border-navy-mid">
          <div className="text-xs font-semibold uppercase tracking-wider text-stone mb-2">
            REMAINING
          </div>
          <div
            className="text-4xl text-mint"
            style={{ fontFamily: "var(--font-display)" }}
          >
            £{((totalBudget - totalSpent) / 100).toLocaleString()}
          </div>
        </div>
      </div>

      {/* Budget List */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>ALL BUDGETS</CardTitle>
          <Button size="sm">
            <Plus className="w-4 h-4" />
            ADD BUDGET
          </Button>
        </CardHeader>
        <CardContent className="space-y-6">
          {mockBudgets.map((budget) => (
            <div
              key={budget.id}
              className="p-4 bg-navy rounded-xl hover:bg-navy-deep transition-colors cursor-pointer"
            >
              <BudgetBar
                name={budget.name}
                spent={budget.spent}
                budget={budget.budget}
                emoji={budget.emoji}
              />
              <div className="mt-2 text-xs text-slate capitalize">
                {budget.period} budget
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
