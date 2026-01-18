import { TopBar } from "@/components/layout";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { TransactionRow } from "@/components/ui/transaction-row";

// Mock data - will be replaced with real API calls
const mockTransactions = [
  { id: "1", merchant: "Sainsbury's", category: "groceries", amount: -4782, date: new Date().toISOString() },
  { id: "2", merchant: "Pret A Manger", category: "eating_out", amount: -450, date: new Date().toISOString() },
  { id: "3", merchant: "TfL", category: "transport", amount: -280, date: new Date(Date.now() - 86400000).toISOString() },
  { id: "4", merchant: "Salary", category: "income", amount: 345000, date: new Date(Date.now() - 172800000).toISOString() },
  { id: "5", merchant: "Netflix", category: "entertainment", amount: -1599, date: new Date(Date.now() - 259200000).toISOString() },
  { id: "6", merchant: "Amazon", category: "shopping", amount: -2499, date: new Date(Date.now() - 345600000).toISOString() },
  { id: "7", merchant: "Costa", category: "eating_out", amount: -395, date: new Date(Date.now() - 432000000).toISOString() },
  { id: "8", merchant: "Tesco", category: "groceries", amount: -6734, date: new Date(Date.now() - 518400000).toISOString() },
];

const categories = [
  "All",
  "groceries",
  "eating_out",
  "transport",
  "shopping",
  "entertainment",
  "bills",
];

export function Transactions() {
  return (
    <div>
      <TopBar
        title="TRANSACTIONS"
        subtitle={`${mockTransactions.length} transactions this month`}
        showSync={false}
      />

      {/* Filters */}
      <div className="flex gap-3 mb-6 flex-wrap">
        {categories.map((cat) => (
          <button
            key={cat}
            className={`px-4 py-2 rounded-full text-sm font-semibold transition-all ${
              cat === "All"
                ? "bg-coral text-white"
                : "bg-navy-mid text-stone hover:text-white"
            }`}
          >
            {cat === "All" ? "All" : cat.replace(/_/g, " ")}
          </button>
        ))}
      </div>

      {/* Transactions List */}
      <Card>
        <CardHeader>
          <CardTitle>ALL TRANSACTIONS</CardTitle>
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
  );
}
