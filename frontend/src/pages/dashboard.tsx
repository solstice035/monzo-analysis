import { TopBar } from "@/components/layout";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { StatBlock } from "@/components/ui/stat-block";
import { BudgetBar } from "@/components/ui/budget-bar";
import { TransactionRow } from "@/components/ui/transaction-row";
import { useTriggerSync } from "@/hooks/useApi";

// Mock data - will be replaced with real API calls
const mockStats = {
  spent: 284700,
  remaining: 115300,
  savings: 45000,
  savingsRate: 24,
};

const mockBudgets = [
  { name: "Groceries", spent: 28500, budget: 40000, emoji: "🛒" },
  { name: "Eating Out", spent: 16500, budget: 20000, emoji: "🍽️" },
  { name: "Shopping", spent: 31200, budget: 25000, emoji: "🛍️" },
  { name: "Transport", spent: 9400, budget: 15000, emoji: "🚗" },
];

const mockTransactions = [
  {
    id: "1",
    merchant: "Sainsbury's",
    category: "groceries",
    amount: -4782,
    date: new Date().toISOString(),
  },
  {
    id: "2",
    merchant: "Pret A Manger",
    category: "eating_out",
    amount: -450,
    date: new Date().toISOString(),
  },
  {
    id: "3",
    merchant: "TfL",
    category: "transport",
    amount: -280,
    date: new Date(Date.now() - 86400000).toISOString(),
  },
  {
    id: "4",
    merchant: "Salary",
    category: "income",
    amount: 345000,
    date: new Date(Date.now() - 172800000).toISOString(),
  },
  {
    id: "5",
    merchant: "Netflix",
    category: "entertainment",
    amount: -1599,
    date: new Date(Date.now() - 259200000).toISOString(),
  },
];

export function Dashboard() {
  const syncMutation = useTriggerSync();

  const handleSync = () => {
    syncMutation.mutate();
  };

  // Get current month and days until reset
  const now = new Date();
  const month = now.toLocaleString("en-GB", { month: "long" }).toUpperCase();
  const year = now.getFullYear();
  const daysInMonth = new Date(year, now.getMonth() + 1, 0).getDate();
  const daysUntilReset = daysInMonth - now.getDate();

  return (
    <div>
      <TopBar
        title={`${month} ${year}`}
        subtitle={`Budget resets in ${daysUntilReset} days`}
        onSync={handleSync}
        isSyncing={syncMutation.isPending}
      />

      {/* Stats Row */}
      <div className="grid grid-cols-4 gap-4 mb-8">
        <StatBlock
          label="SPENT"
          value={formatCurrency(mockStats.spent)}
          change="↓ 12% VS DEC"
          changeType="positive"
        />
        <StatBlock
          label="REMAINING"
          value={formatCurrency(mockStats.remaining)}
          change="ON TRACK"
          changeType="positive"
        />
        <StatBlock
          label="SAVINGS"
          value={formatCurrency(mockStats.savings)}
          change="↑ 15%"
          changeType="positive"
        />
        <StatBlock
          label="RATE"
          value={`${mockStats.savingsRate}%`}
          change="TARGET: 20%"
          changeType="positive"
        />
      </div>

      <div className="grid grid-cols-2 gap-6">
        {/* Budget Progress */}
        <Card>
          <CardHeader>
            <CardTitle>BUDGET PROGRESS</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {mockBudgets.map((budget) => (
              <BudgetBar
                key={budget.name}
                name={budget.name}
                spent={budget.spent}
                budget={budget.budget}
                emoji={budget.emoji}
              />
            ))}
          </CardContent>
        </Card>

        {/* Recent Transactions */}
        <Card>
          <CardHeader>
            <CardTitle>RECENT TRANSACTIONS</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {mockTransactions.map((tx) => (
              <TransactionRow
                key={tx.id}
                merchant={tx.merchant}
                category={tx.category}
                amount={tx.amount}
                date={tx.date}
              />
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function formatCurrency(pence: number): string {
  const pounds = Math.abs(pence) / 100;
  return `£${pounds.toLocaleString("en-GB", {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  })}`;
}
