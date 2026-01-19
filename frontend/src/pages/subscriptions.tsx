import { TopBar } from "@/components/layout";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { useRecurringTransactions } from "@/hooks/useApi";
import { RefreshCw } from "lucide-react";

const categoryEmojis: Record<string, string> = {
  groceries: "🛒",
  eating_out: "🍽️",
  shopping: "🛍️",
  transport: "🚗",
  entertainment: "🎬",
  bills: "📄",
  general: "📦",
  holidays: "✈️",
  cash: "💵",
  expenses: "💼",
};

function formatCurrency(pence: number): string {
  return `£${(pence / 100).toFixed(2)}`;
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

function getConfidenceColor(confidence: number): string {
  if (confidence >= 0.8) return "text-mint";
  if (confidence >= 0.6) return "text-yellow";
  return "text-stone";
}

export function Subscriptions() {
  const { data, isLoading, error, refetch } = useRecurringTransactions();

  const items = data?.items || [];
  const totalMonthlyCost = data?.total_monthly_cost || 0;

  return (
    <div>
      <TopBar
        title="SUBSCRIPTIONS"
        subtitle={`${items.length} recurring payments detected`}
        showSync={false}
      />

      {/* Summary */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        <div className="bg-charcoal rounded-2xl p-6 border border-navy-mid">
          <div className="text-xs font-semibold uppercase tracking-wider text-stone mb-2">
            MONTHLY COST
          </div>
          <div
            className="text-4xl text-coral"
            style={{ fontFamily: "var(--font-display)" }}
          >
            {formatCurrency(totalMonthlyCost)}
          </div>
        </div>
        <div className="bg-charcoal rounded-2xl p-6 border border-navy-mid">
          <div className="text-xs font-semibold uppercase tracking-wider text-stone mb-2">
            YEARLY ESTIMATE
          </div>
          <div
            className="text-4xl text-white"
            style={{ fontFamily: "var(--font-display)" }}
          >
            {formatCurrency(totalMonthlyCost * 12)}
          </div>
        </div>
        <div className="bg-charcoal rounded-2xl p-6 border border-navy-mid">
          <div className="text-xs font-semibold uppercase tracking-wider text-stone mb-2">
            SUBSCRIPTIONS
          </div>
          <div
            className="text-4xl text-white"
            style={{ fontFamily: "var(--font-display)" }}
          >
            {items.length}
          </div>
        </div>
      </div>

      {/* Subscription List */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>DETECTED SUBSCRIPTIONS</CardTitle>
          <button
            onClick={() => refetch()}
            className="p-2 text-stone hover:text-white transition-colors"
            title="Refresh"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </CardHeader>
        <CardContent className="space-y-4">
          {isLoading && (
            <div className="text-center py-8 text-stone">
              Analyzing transactions for recurring patterns...
            </div>
          )}
          {error && (
            <div className="text-center py-8 text-coral">
              Failed to detect recurring transactions. Please try again.
            </div>
          )}
          {!isLoading && !error && items.length === 0 && (
            <div className="text-center py-8 text-stone">
              No recurring transactions detected yet. Sync more transactions to
              improve detection.
            </div>
          )}
          {items.map((item, index) => (
            <div
              key={index}
              className="p-4 bg-navy rounded-xl hover:bg-navy-deep transition-colors"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="text-2xl">
                    {categoryEmojis[item.category] || "📦"}
                  </div>
                  <div>
                    <div className="text-white font-medium">
                      {item.merchant_name}
                    </div>
                    <div className="text-sm text-stone capitalize">
                      {item.category.replace(/_/g, " ")} ·{" "}
                      {item.frequency_label}
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <div
                    className="text-xl text-coral"
                    style={{ fontFamily: "var(--font-display)" }}
                  >
                    {formatCurrency(item.average_amount)}
                  </div>
                  <div className="text-xs text-stone">
                    ~{formatCurrency(item.monthly_cost)}/month
                  </div>
                </div>
              </div>

              <div className="mt-3 pt-3 border-t border-navy-mid grid grid-cols-4 gap-4 text-xs">
                <div>
                  <span className="text-slate">Last payment</span>
                  <div className="text-stone mt-1">
                    {formatDate(item.last_transaction)}
                  </div>
                </div>
                <div>
                  <span className="text-slate">Next expected</span>
                  <div className="text-stone mt-1">
                    {item.next_expected
                      ? formatDate(item.next_expected)
                      : "Unknown"}
                  </div>
                </div>
                <div>
                  <span className="text-slate">Occurrences</span>
                  <div className="text-stone mt-1">{item.transaction_count}</div>
                </div>
                <div>
                  <span className="text-slate">Confidence</span>
                  <div className={`mt-1 ${getConfidenceColor(item.confidence)}`}>
                    {Math.round(item.confidence * 100)}%
                  </div>
                </div>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>

      {/* Tips */}
      <div className="mt-6 p-4 bg-charcoal rounded-xl border border-navy-mid">
        <div className="text-sm text-stone">
          <strong className="text-white">Tip:</strong> The detection algorithm
          looks for transactions from the same merchant occurring at regular
          intervals (weekly, monthly, etc). The confidence score indicates how
          consistent the pattern is. Higher scores mean more reliable detection.
        </div>
      </div>
    </div>
  );
}
