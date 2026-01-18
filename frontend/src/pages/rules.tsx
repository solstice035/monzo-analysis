import { TopBar } from "@/components/layout";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { CategoryPill } from "@/components/ui/category-pill";
import { Plus, ArrowRight, Pencil, Trash2 } from "lucide-react";

// Mock data - will be replaced with real API calls
const mockRules = [
  {
    id: "1",
    name: "Coffee shops",
    priority: 1,
    conditions: [{ field: "merchant_name", operator: "contains", value: "Costa" }],
    category: "eating_out",
  },
  {
    id: "2",
    name: "Supermarkets",
    priority: 2,
    conditions: [{ field: "merchant_category", operator: "equals", value: "groceries" }],
    category: "groceries",
  },
  {
    id: "3",
    name: "Big shop",
    priority: 3,
    conditions: [
      { field: "merchant_category", operator: "equals", value: "groceries" },
      { field: "amount", operator: "greater_than", value: "10000" },
    ],
    category: "groceries",
  },
  {
    id: "4",
    name: "TfL",
    priority: 4,
    conditions: [{ field: "merchant_name", operator: "contains", value: "TfL" }],
    category: "transport",
  },
  {
    id: "5",
    name: "Subscriptions",
    priority: 5,
    conditions: [{ field: "is_recurring", operator: "equals", value: "true" }],
    category: "bills",
  },
];

function formatCondition(condition: { field: string; operator: string; value: string }) {
  const fieldLabels: Record<string, string> = {
    merchant_name: "Merchant",
    merchant_category: "Category",
    amount: "Amount",
    is_recurring: "Recurring",
  };

  const operatorLabels: Record<string, string> = {
    contains: "contains",
    equals: "is",
    greater_than: ">",
    less_than: "<",
  };

  const field = fieldLabels[condition.field] || condition.field;
  const operator = operatorLabels[condition.operator] || condition.operator;
  let value = condition.value;

  if (condition.field === "amount") {
    value = `£${(parseInt(value) / 100).toFixed(2)}`;
  }

  return `${field} ${operator} "${value}"`;
}

export function Rules() {
  return (
    <div>
      <TopBar
        title="RULES"
        subtitle={`${mockRules.length} categorisation rules`}
        showSync={false}
      />

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>CATEGORISATION RULES</CardTitle>
          <Button size="sm">
            <Plus className="w-4 h-4" />
            ADD RULE
          </Button>
        </CardHeader>
        <CardContent>
          <div className="text-sm text-stone mb-4">
            Rules are evaluated in priority order. Higher priority rules are checked first.
          </div>

          <div className="space-y-3">
            {mockRules.map((rule) => (
              <div
                key={rule.id}
                className="flex items-center gap-4 p-4 bg-navy rounded-xl border border-transparent hover:border-coral transition-all"
              >
                <div className="w-8 h-8 bg-charcoal rounded-lg flex items-center justify-center text-stone text-sm font-bold">
                  {rule.priority}
                </div>

                <div className="flex-1">
                  <div className="font-semibold text-white mb-1">{rule.name}</div>
                  <div className="text-sm text-slate">
                    {rule.conditions.map((c, i) => (
                      <span key={i}>
                        {i > 0 && <span className="text-coral"> AND </span>}
                        {formatCondition(c)}
                      </span>
                    ))}
                  </div>
                </div>

                <ArrowRight className="w-5 h-5 text-stone" />

                <CategoryPill category={rule.category} />

                <div className="flex gap-2">
                  <button className="p-2 text-stone hover:text-white transition-colors">
                    <Pencil className="w-4 h-4" />
                  </button>
                  <button className="p-2 text-stone hover:text-coral transition-colors">
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
