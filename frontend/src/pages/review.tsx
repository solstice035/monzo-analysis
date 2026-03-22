import { useState, useMemo } from "react";
import { TopBar } from "@/components/layout";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  ChevronDown,
  ChevronRight,
  Check,
  XCircle,
  Banknote,
} from "lucide-react";
import {
  usePendingReview,
  useBudgets,
  useBudgetGroups,
  useReviewTransaction,
  useBulkReview,
} from "@/hooks/useApi";
import { formatCurrency } from "@/lib/utils";
import type { PendingTransaction } from "@/lib/api";

interface MerchantGroup {
  merchantName: string;
  transactions: PendingTransaction[];
  totalAmount: number;
}

export function Review() {
  const { data: reviewData, isLoading } = usePendingReview();
  const { data: budgets } = useBudgets();
  const { data: budgetGroups } = useBudgetGroups();
  const reviewTransaction = useReviewTransaction();
  const bulkReview = useBulkReview();

  const [expandedMerchants, setExpandedMerchants] = useState<Set<string>>(new Set());
  const [bulkAssignments, setBulkAssignments] = useState<Record<string, string>>({});
  const [bulkCreateRule, setBulkCreateRule] = useState<Record<string, boolean>>({});
  const [individualAssignments, setIndividualAssignments] = useState<Record<string, string>>({});

  const pendingItems = reviewData?.items || [];
  const totalPending = reviewData?.total || 0;
  const budgetList = (budgets || []).filter((b) => !b.is_sinking_fund);
  const groupList = budgetGroups || [];

  // Group transactions by merchant
  const { merchantGroups, oneOffs } = useMemo(() => {
    const groupMap = new Map<string, PendingTransaction[]>();

    for (const tx of pendingItems) {
      const key = tx.merchant_name || "Unknown";
      if (!groupMap.has(key)) {
        groupMap.set(key, []);
      }
      groupMap.get(key)!.push(tx);
    }

    const groups: MerchantGroup[] = [];
    const singles: PendingTransaction[] = [];

    for (const [merchantName, txns] of groupMap) {
      if (txns.length >= 2) {
        groups.push({
          merchantName,
          transactions: txns.sort(
            (a, b) =>
              new Date(b.created_at || "").getTime() -
              new Date(a.created_at || "").getTime()
          ),
          totalAmount: txns.reduce((sum, t) => sum + t.amount, 0),
        });
      } else {
        singles.push(...txns);
      }
    }

    // Sort groups by number of transactions desc
    groups.sort((a, b) => b.transactions.length - a.transactions.length);
    // Sort singles by date desc
    singles.sort(
      (a, b) =>
        new Date(b.created_at || "").getTime() -
        new Date(a.created_at || "").getTime()
    );

    // Auto-expand all merchant groups and default create_rule to true
    if (groups.length > 0 && expandedMerchants.size === 0) {
      const allNames = new Set(groups.map((g) => g.merchantName));
      setExpandedMerchants(allNames);
      // Default create_rule to true for merchant groups
      const defaultRules: Record<string, boolean> = {};
      for (const g of groups) {
        defaultRules[g.merchantName] = true;
      }
      setBulkCreateRule(defaultRules);
    }

    return { merchantGroups: groups, oneOffs: singles };
  }, [pendingItems]);

  // Budget options grouped by BudgetGroup
  const budgetOptions = useMemo(() => {
    const groups: Array<{ groupName: string; budgets: Array<{ id: string; name: string }> }> = [];
    const gMap = new Map<string, Array<{ id: string; name: string }>>();

    for (const budget of budgetList) {
      const group = groupList.find((g) => g.id === budget.group_id);
      const groupName = group?.name || "Ungrouped";
      if (!gMap.has(groupName)) gMap.set(groupName, []);
      gMap.get(groupName)!.push({
        id: budget.id,
        name: budget.name || budget.category.replace(/_/g, " "),
      });
    }

    for (const [groupName, bList] of gMap) {
      groups.push({ groupName, budgets: bList.sort((a, b) => a.name.localeCompare(b.name)) });
    }
    return groups.sort((a, b) => a.groupName.localeCompare(b.groupName));
  }, [budgetList, groupList]);

  const toggleMerchant = (name: string) => {
    setExpandedMerchants((prev) => {
      const next = new Set(prev);
      if (next.has(name)) next.delete(name);
      else next.add(name);
      return next;
    });
  };

  const handleBulkAssign = async (group: MerchantGroup) => {
    const budgetId = bulkAssignments[group.merchantName];
    if (!budgetId) return;

    const createRule = bulkCreateRule[group.merchantName] ?? true;

    await bulkReview.mutateAsync({
      transaction_ids: group.transactions.map((t) => t.id),
      budget_id: budgetId,
      action: "reassign",
      create_rule: createRule,
    });
  };

  const handleIndividualAssign = async (
    transactionId: string,
    budgetId: string,
    createRule = false
  ) => {
    await reviewTransaction.mutateAsync({
      transactionId,
      data: {
        budget_id: budgetId,
        action: "reassign",
        create_rule: createRule,
      },
    });
  };

  const handleExclude = async (transactionId: string) => {
    await reviewTransaction.mutateAsync({
      transactionId,
      data: {
        action: "exclude",
      },
    });
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return "";
    const d = new Date(dateStr);
    return d.toLocaleDateString("en-GB", { day: "numeric", month: "short" });
  };

  return (
    <div>
      <TopBar
        title="REVIEW QUEUE"
        subtitle={`${totalPending} pending`}
        showSync={false}
      />

      {isLoading && (
        <div className="text-center py-12 text-stone">Loading review queue...</div>
      )}

      {!isLoading && totalPending === 0 && (
        <div className="text-center py-16">
          <Check className="w-12 h-12 text-mint mx-auto mb-4" />
          <h2 className="text-xl text-white mb-2" style={{ fontFamily: "var(--font-display)" }}>
            ALL CLEAR
          </h2>
          <p className="text-stone">No transactions pending review.</p>
        </div>
      )}

      {!isLoading && totalPending > 0 && (
        <div className="space-y-4">
          {/* Merchant Groups */}
          {merchantGroups.map((group) => (
            <Card key={group.merchantName}>
              <button
                onClick={() => toggleMerchant(group.merchantName)}
                className="w-full flex items-center justify-between p-4 hover:bg-navy/30 transition-colors"
              >
                <div className="flex items-center gap-3">
                  {expandedMerchants.has(group.merchantName) ? (
                    <ChevronDown className="w-5 h-5 text-stone" />
                  ) : (
                    <ChevronRight className="w-5 h-5 text-stone" />
                  )}
                  <div>
                    <h3 className="font-semibold text-white text-left">
                      {group.merchantName}
                    </h3>
                    <span className="text-xs text-stone">
                      {group.transactions.length} transaction{group.transactions.length !== 1 ? "s" : ""}
                    </span>
                  </div>
                </div>
                <div
                  className="text-coral font-mono"
                  style={{ fontFamily: "var(--font-mono)" }}
                >
                  {formatCurrency(Math.abs(group.totalAmount))}
                </div>
              </button>

              {expandedMerchants.has(group.merchantName) && (
                <CardContent className="pt-0 space-y-3">
                  {/* Transaction list */}
                  <div className="space-y-1">
                    {group.transactions.map((tx) => (
                      <div
                        key={tx.id}
                        className="flex items-center justify-between py-2 px-3 rounded-lg hover:bg-navy/50 transition-colors"
                      >
                        <div className="flex items-center gap-4">
                          <span className="text-sm text-stone w-16">
                            {formatDate(tx.created_at)}
                          </span>
                          <span
                            className="text-white font-mono"
                            style={{ fontFamily: "var(--font-mono)" }}
                          >
                            {formatCurrency(Math.abs(tx.amount))}
                          </span>
                        </div>
                        <div className="flex items-center gap-2">
                          {/* Individual override */}
                          <select
                            value={individualAssignments[tx.id] || ""}
                            onChange={(e) => {
                              if (e.target.value) {
                                setIndividualAssignments((prev) => ({
                                  ...prev,
                                  [tx.id]: e.target.value,
                                }));
                                handleIndividualAssign(tx.id, e.target.value);
                              }
                            }}
                            className="bg-navy-deep border border-navy-mid rounded px-2 py-1 text-xs text-stone w-[140px]"
                          >
                            <option value="">Override...</option>
                            {budgetOptions.map((g) => (
                              <optgroup key={g.groupName} label={g.groupName}>
                                {g.budgets.map((b) => (
                                  <option key={b.id} value={b.id}>
                                    {b.name}
                                  </option>
                                ))}
                              </optgroup>
                            ))}
                          </select>
                          <button
                            onClick={() => handleExclude(tx.id)}
                            className="p-1 text-stone hover:text-coral transition-colors"
                            title="Mark as income/transfer (exclude)"
                          >
                            <XCircle className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Bulk assign controls */}
                  <div className="border-t border-navy-mid pt-3 space-y-2">
                    <div className="flex items-center gap-3">
                      <span className="text-sm text-stone whitespace-nowrap">
                        Assign all to:
                      </span>
                      <select
                        value={bulkAssignments[group.merchantName] || ""}
                        onChange={(e) =>
                          setBulkAssignments((prev) => ({
                            ...prev,
                            [group.merchantName]: e.target.value,
                          }))
                        }
                        className="bg-navy-deep border border-navy-mid rounded-lg px-3 py-1.5 text-white flex-1 text-sm"
                      >
                        <option value="">Select category...</option>
                        {budgetOptions.map((g) => (
                          <optgroup key={g.groupName} label={g.groupName}>
                            {g.budgets.map((b) => (
                              <option key={b.id} value={b.id}>
                                {b.name}
                              </option>
                            ))}
                          </optgroup>
                        ))}
                      </select>
                      <Button
                        size="sm"
                        onClick={() => handleBulkAssign(group)}
                        disabled={
                          !bulkAssignments[group.merchantName] ||
                          bulkReview.isPending
                        }
                      >
                        <Check className="w-4 h-4 mr-1" />
                        Assign All
                      </Button>
                    </div>

                    {/* Auto-learn checkbox */}
                    <label className="flex items-center gap-2 text-sm text-stone cursor-pointer">
                      <input
                        type="checkbox"
                        checked={bulkCreateRule[group.merchantName] ?? true}
                        onChange={(e) =>
                          setBulkCreateRule((prev) => ({
                            ...prev,
                            [group.merchantName]: e.target.checked,
                          }))
                        }
                        className="rounded border-navy-mid bg-navy"
                      />
                      Create rule for future {group.merchantName} transactions
                    </label>
                  </div>
                </CardContent>
              )}
            </Card>
          ))}

          {/* One-off transactions */}
          {oneOffs.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-sm">
                  ONE-OFF TRANSACTIONS ({oneOffs.length})
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {oneOffs.map((tx) => (
                  <div
                    key={tx.id}
                    className="flex items-center justify-between p-3 bg-navy rounded-xl hover:bg-navy-deep transition-colors"
                  >
                    <div className="flex items-center gap-4 flex-1">
                      <span className="text-sm text-stone w-16">
                        {formatDate(tx.created_at)}
                      </span>
                      <span className="text-white text-sm flex-1">
                        {tx.merchant_name || "Unknown"}
                      </span>
                      <span
                        className="text-coral font-mono text-sm"
                        style={{ fontFamily: "var(--font-mono)" }}
                      >
                        {formatCurrency(Math.abs(tx.amount))}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 ml-4">
                      <select
                        value=""
                        onChange={(e) => {
                          if (e.target.value) {
                            handleIndividualAssign(tx.id, e.target.value);
                          }
                        }}
                        className="bg-navy-deep border border-navy-mid rounded-lg px-3 py-1.5 text-white text-sm min-w-[180px]"
                      >
                        <option value="">Assign ▾</option>
                        {budgetOptions.map((g) => (
                          <optgroup key={g.groupName} label={g.groupName}>
                            {g.budgets.map((b) => (
                              <option key={b.id} value={b.id}>
                                {b.name}
                              </option>
                            ))}
                          </optgroup>
                        ))}
                      </select>
                      <button
                        onClick={() => handleExclude(tx.id)}
                        className="p-1.5 text-stone hover:text-coral transition-colors"
                        title="Mark as income/transfer"
                      >
                        <Banknote className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}
