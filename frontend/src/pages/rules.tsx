import { useState, useMemo } from "react";
import { TopBar } from "@/components/layout";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import {
  Search,
  ChevronDown,
  ChevronRight,
  Plus,
  Pencil,
  Trash2,
  ArrowRight,
  Settings2,
} from "lucide-react";
import {
  useMerchants,
  useBudgets,
  useBudgetGroups,
  useRules,
  useCreateRule,
  useUpdateRule,
  useDeleteRule,
} from "@/hooks/useApi";
import { useAccount } from "@/contexts/AccountContext";
import type { Merchant, CategoryRule } from "@/lib/api";

interface MerchantGroup {
  groupName: string;
  groupId: string | null;
  merchants: Merchant[];
}

export function Rules() {
  const { selectedAccount } = useAccount();
  const { data: merchants, isLoading: merchantsLoading } = useMerchants();
  const { data: budgets } = useBudgets();
  const { data: budgetGroups } = useBudgetGroups();
  const { data: rules } = useRules();
  const createRule = useCreateRule();
  const updateRule = useUpdateRule();
  const deleteRule = useDeleteRule();

  const [searchQuery, setSearchQuery] = useState("");
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(["uncategorised"]));
  const [showAdvanced, setShowAdvanced] = useState(false);

  // Advanced rule editor state
  const [advancedDialogOpen, setAdvancedDialogOpen] = useState(false);
  const [editingRule, setEditingRule] = useState<CategoryRule | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [ruleToDelete, setRuleToDelete] = useState<string | null>(null);
  const [ruleForm, setRuleForm] = useState({
    name: "",
    target_category: "",
    target_budget_id: "",
    priority: 100,
    enabled: true,
    condition_field: "merchant_name",
    condition_operator: "contains",
    condition_value: "",
  });

  const merchantList = merchants || [];
  const budgetList = (budgets || []).filter((b) => !b.is_sinking_fund);
  const groupList = budgetGroups || [];
  const rulesList = rules || [];

  // Filter merchants by search
  const filteredMerchants = useMemo(() => {
    if (!searchQuery.trim()) return merchantList;
    const q = searchQuery.toLowerCase();
    return merchantList.filter((m) => m.name.toLowerCase().includes(q));
  }, [merchantList, searchQuery]);

  // Split merchants into uncategorised and categorised groups
  const uncategorised = filteredMerchants.filter((m) => !m.assigned_budget_id);
  const categorised = filteredMerchants.filter((m) => !!m.assigned_budget_id);

  // Group categorised merchants by their assigned group
  const merchantGroups = useMemo(() => {
    const groupMap = new Map<string, MerchantGroup>();

    for (const m of categorised) {
      const key = m.assigned_group_name || "Ungrouped";
      if (!groupMap.has(key)) {
        groupMap.set(key, {
          groupName: key,
          groupId: null,
          merchants: [],
        });
      }
      groupMap.get(key)!.merchants.push(m);
    }

    return Array.from(groupMap.values()).sort((a, b) =>
      a.groupName.localeCompare(b.groupName)
    );
  }, [categorised]);

  // Identify advanced rules (not simple merchant_exact)
  const advancedRules = useMemo(() => {
    return rulesList.filter((r) => {
      const conds = r.conditions || {};
      // An "advanced" rule has something other than just merchant_exact
      const hasMerchantExact = !!conds.merchant_exact;
      const hasOtherConditions =
        !!conds.merchant_pattern ||
        conds.amount_min !== undefined ||
        conds.amount_max !== undefined ||
        !!conds.monzo_category ||
        conds.day_of_week !== undefined;

      return !hasMerchantExact || hasOtherConditions;
    });
  }, [rulesList]);

  const toggleSection = (key: string) => {
    setExpandedSections((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  // Build grouped budget options for dropdowns
  const budgetOptions = useMemo(() => {
    const groups: Array<{ groupName: string; budgets: Array<{ id: string; name: string }> }> = [];
    const groupMap = new Map<string, Array<{ id: string; name: string }>>();

    for (const budget of budgetList) {
      const group = groupList.find((g) => g.id === budget.group_id);
      const groupName = group?.name || "Ungrouped";
      if (!groupMap.has(groupName)) {
        groupMap.set(groupName, []);
      }
      groupMap.get(groupName)!.push({
        id: budget.id,
        name: budget.name || budget.category.replace(/_/g, " "),
      });
    }

    for (const [groupName, budgets] of groupMap) {
      groups.push({ groupName, budgets: budgets.sort((a, b) => a.name.localeCompare(b.name)) });
    }

    return groups.sort((a, b) => a.groupName.localeCompare(b.groupName));
  }, [budgetList, groupList]);

  const handleAssignMerchant = async (merchant: Merchant, budgetId: string) => {
    if (!selectedAccount) return;

    const targetBudget = budgetList.find((b) => b.id === budgetId);
    if (!targetBudget) return;

    if (merchant.rule_id) {
      // Update existing rule
      await updateRule.mutateAsync({
        id: merchant.rule_id,
        data: {
          target_budget_id: budgetId,
          target_category: targetBudget.category,
        },
      });
    } else {
      // Create new rule
      await createRule.mutateAsync({
        account_id: selectedAccount.id,
        name: `Auto: ${merchant.name}`,
        conditions: { merchant_exact: merchant.name },
        target_category: targetBudget.category,
        target_budget_id: budgetId,
        priority: 50,
        enabled: true,
      });
    }
  };

  // Advanced rule CRUD
  const handleOpenAdvancedDialog = (rule?: CategoryRule) => {
    if (rule) {
      const conds = rule.conditions || {};
      setRuleForm({
        name: rule.name,
        target_category: rule.target_category,
        target_budget_id: rule.target_budget_id || "",
        priority: rule.priority,
        enabled: rule.enabled,
        condition_field: conds.merchant_pattern
          ? "merchant_name"
          : conds.monzo_category
          ? "merchant_category"
          : conds.amount_gt || conds.amount_lt || conds.amount_min || conds.amount_max
          ? "amount"
          : "merchant_name",
        condition_operator: conds.merchant_pattern ? "contains" : "equals",
        condition_value:
          (conds.merchant_pattern as string) ||
          (conds.monzo_category as string) ||
          String(conds.amount_min || conds.amount_max || conds.amount_gt || conds.amount_lt || ""),
      });
      setEditingRule(rule);
    } else {
      setRuleForm({
        name: "",
        target_category: "",
        target_budget_id: "",
        priority: rulesList.length + 1,
        enabled: true,
        condition_field: "merchant_name",
        condition_operator: "contains",
        condition_value: "",
      });
      setEditingRule(null);
    }
    setAdvancedDialogOpen(true);
  };

  const handleAdvancedSubmit = async () => {
    if (!selectedAccount) return;

    const conditions: Record<string, unknown> = {};
    if (ruleForm.condition_field === "merchant_name") {
      conditions.merchant_pattern = ruleForm.condition_value;
    } else if (ruleForm.condition_field === "merchant_category") {
      conditions.monzo_category = ruleForm.condition_value;
    } else if (ruleForm.condition_field === "amount") {
      if (ruleForm.condition_operator === "greater_than") {
        conditions.amount_min = parseInt(ruleForm.condition_value);
      } else {
        conditions.amount_max = parseInt(ruleForm.condition_value);
      }
    }

    const ruleData = {
      name: ruleForm.name,
      target_category: ruleForm.target_category,
      target_budget_id: ruleForm.target_budget_id || undefined,
      priority: ruleForm.priority,
      enabled: ruleForm.enabled,
      conditions,
    };

    if (editingRule) {
      await updateRule.mutateAsync({ id: editingRule.id, data: ruleData });
    } else {
      await createRule.mutateAsync({
        ...ruleData,
        account_id: selectedAccount.id,
      });
    }
    setAdvancedDialogOpen(false);
  };

  const handleDeleteClick = (ruleId: string) => {
    setRuleToDelete(ruleId);
    setDeleteDialogOpen(true);
  };

  const handleConfirmDelete = async () => {
    if (ruleToDelete) {
      await deleteRule.mutateAsync(ruleToDelete);
      setRuleToDelete(null);
    }
    setDeleteDialogOpen(false);
  };

  const categorisedCount = categorised.length;
  const uncategorisedCount = uncategorised.length;

  return (
    <div>
      <TopBar
        title="MERCHANTS"
        subtitle={`${categorisedCount} categorised · ${uncategorisedCount} uncategorised`}
        showSync={false}
      />

      {/* Search */}
      <div className="mb-6">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-stone" />
          <Input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search merchants..."
            className="pl-10 bg-charcoal border-navy-mid text-white placeholder:text-stone"
          />
        </div>
      </div>

      {merchantsLoading && (
        <div className="text-center py-12 text-stone">Loading merchants...</div>
      )}

      {!merchantsLoading && (
        <div className="space-y-4">
          {/* Uncategorised Section — always shown first */}
          {uncategorised.length > 0 && (
            <Card>
              <button
                onClick={() => toggleSection("uncategorised")}
                className="w-full flex items-center justify-between p-4 hover:bg-navy/30 transition-colors"
              >
                <div className="flex items-center gap-3">
                  {expandedSections.has("uncategorised") ? (
                    <ChevronDown className="w-5 h-5 text-coral" />
                  ) : (
                    <ChevronRight className="w-5 h-5 text-coral" />
                  )}
                  <h3 className="font-semibold text-coral text-lg">
                    UNCATEGORISED ({uncategorised.length})
                  </h3>
                </div>
              </button>
              {expandedSections.has("uncategorised") && (
                <CardContent className="pt-0 space-y-2">
                  {uncategorised.map((merchant) => (
                    <MerchantRow
                      key={merchant.name}
                      merchant={merchant}
                      budgetOptions={budgetOptions}
                      onAssign={(budgetId) => handleAssignMerchant(merchant, budgetId)}
                    />
                  ))}
                </CardContent>
              )}
            </Card>
          )}

          {/* Categorised Merchant Groups */}
          {merchantGroups.map((group) => (
            <Card key={group.groupName}>
              <button
                onClick={() => toggleSection(group.groupName)}
                className="w-full flex items-center justify-between p-4 hover:bg-navy/30 transition-colors"
              >
                <div className="flex items-center gap-3">
                  {expandedSections.has(group.groupName) ? (
                    <ChevronDown className="w-5 h-5 text-stone" />
                  ) : (
                    <ChevronRight className="w-5 h-5 text-stone" />
                  )}
                  <h3 className="font-semibold text-white">
                    {group.groupName}{" "}
                    <span className="text-stone font-normal">
                      ({group.merchants.length} merchant{group.merchants.length !== 1 ? "s" : ""})
                    </span>
                  </h3>
                </div>
              </button>
              {expandedSections.has(group.groupName) && (
                <CardContent className="pt-0 space-y-2">
                  {group.merchants.map((merchant) => (
                    <MerchantRow
                      key={merchant.name}
                      merchant={merchant}
                      budgetOptions={budgetOptions}
                      onAssign={(budgetId) => handleAssignMerchant(merchant, budgetId)}
                    />
                  ))}
                </CardContent>
              )}
            </Card>
          ))}

          {/* Advanced Rules Section */}
          <div className="border-t border-navy-mid pt-4 mt-6">
            <button
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="flex items-center gap-2 text-sm text-stone hover:text-white transition-colors"
            >
              <Settings2 className="w-4 h-4" />
              Advanced Rules ({advancedRules.length})
              {showAdvanced ? (
                <ChevronDown className="w-4 h-4" />
              ) : (
                <ChevronRight className="w-4 h-4" />
              )}
            </button>

            {showAdvanced && (
              <Card className="mt-3">
                <CardHeader className="flex flex-row items-center justify-between">
                  <CardTitle className="text-sm">ADVANCED RULES</CardTitle>
                  <Button size="sm" onClick={() => handleOpenAdvancedDialog()}>
                    <Plus className="w-4 h-4" />
                    ADD RULE
                  </Button>
                </CardHeader>
                <CardContent>
                  {advancedRules.length === 0 && (
                    <div className="text-center py-4 text-stone text-sm">
                      No advanced rules configured.
                    </div>
                  )}
                  <div className="space-y-2">
                    {advancedRules.map((rule) => (
                      <div
                        key={rule.id}
                        className="flex items-center gap-4 p-3 bg-navy rounded-xl border border-transparent hover:border-coral transition-all"
                      >
                        <div className="w-7 h-7 bg-charcoal rounded-lg flex items-center justify-center text-stone text-xs font-bold">
                          {rule.priority}
                        </div>
                        <div className="flex-1">
                          <div className="font-semibold text-white text-sm">{rule.name}</div>
                          <div className="text-xs text-slate">
                            {formatCondition(rule.conditions)}
                          </div>
                        </div>
                        <ArrowRight className="w-4 h-4 text-stone" />
                        <span className="text-sm text-mint">
                          {rule.target_category.replace(/_/g, " ")}
                        </span>
                        <div className="flex gap-1">
                          <button
                            onClick={() => handleOpenAdvancedDialog(rule)}
                            className="p-1.5 text-stone hover:text-white transition-colors"
                          >
                            <Pencil className="w-3.5 h-3.5" />
                          </button>
                          <button
                            onClick={() => handleDeleteClick(rule.id)}
                            className="p-1.5 text-stone hover:text-coral transition-colors"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </div>

          {/* Empty state */}
          {filteredMerchants.length === 0 && !merchantsLoading && (
            <div className="text-center py-12 text-stone">
              {searchQuery ? "No merchants matching your search." : "No merchants found."}
            </div>
          )}
        </div>
      )}

      {/* Advanced Rule Dialog */}
      <Dialog open={advancedDialogOpen} onOpenChange={setAdvancedDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editingRule ? "Edit Rule" : "Add Advanced Rule"}</DialogTitle>
            <DialogDescription>
              Create a rule with custom conditions for auto-categorisation.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label className="text-white">Rule Name</Label>
              <Input
                placeholder="e.g., Large supermarket shops"
                value={ruleForm.name}
                onChange={(e) => setRuleForm({ ...ruleForm, name: e.target.value })}
                className="bg-navy border-navy-mid text-white placeholder:text-stone"
              />
            </div>
            <div className="grid gap-2">
              <Label className="text-white">Condition</Label>
              <div className="flex gap-2">
                <select
                  value={ruleForm.condition_field}
                  onChange={(e) => setRuleForm({ ...ruleForm, condition_field: e.target.value })}
                  className="bg-navy border border-navy-mid rounded-lg px-3 py-2 text-white flex-1"
                >
                  <option value="merchant_name">Merchant Name</option>
                  <option value="merchant_category">Monzo Category</option>
                  <option value="amount">Amount (pence)</option>
                </select>
                <select
                  value={ruleForm.condition_operator}
                  onChange={(e) => setRuleForm({ ...ruleForm, condition_operator: e.target.value })}
                  className="bg-navy border border-navy-mid rounded-lg px-3 py-2 text-white"
                >
                  <option value="contains">contains</option>
                  <option value="equals">equals</option>
                  <option value="greater_than">greater than</option>
                  <option value="less_than">less than</option>
                </select>
              </div>
              <Input
                placeholder={ruleForm.condition_field === "amount" ? "Amount in pence" : "Value to match"}
                value={ruleForm.condition_value}
                onChange={(e) => setRuleForm({ ...ruleForm, condition_value: e.target.value })}
                className="bg-navy border-navy-mid text-white placeholder:text-stone"
              />
            </div>
            <div className="grid gap-2">
              <Label className="text-white">Assign to Category</Label>
              <select
                value={ruleForm.target_budget_id}
                onChange={(e) => {
                  const budget = budgetList.find((b) => b.id === e.target.value);
                  setRuleForm({
                    ...ruleForm,
                    target_budget_id: e.target.value,
                    target_category: budget?.category || "",
                  });
                }}
                className="bg-navy border border-navy-mid rounded-lg px-4 py-2 text-white w-full"
              >
                <option value="">Select category...</option>
                {budgetOptions.map((group) => (
                  <optgroup key={group.groupName} label={group.groupName}>
                    {group.budgets.map((b) => (
                      <option key={b.id} value={b.id}>
                        {b.name}
                      </option>
                    ))}
                  </optgroup>
                ))}
              </select>
            </div>
            <div className="grid gap-2">
              <Label className="text-white">Priority</Label>
              <Input
                type="number"
                min="1"
                value={ruleForm.priority}
                onChange={(e) => setRuleForm({ ...ruleForm, priority: parseInt(e.target.value) || 1 })}
                className="bg-navy border-navy-mid text-white"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="ghost" onClick={() => setAdvancedDialogOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleAdvancedSubmit}
              disabled={!ruleForm.name || !ruleForm.condition_value}
            >
              {editingRule ? "Save Changes" : "Create Rule"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent className="bg-charcoal border-navy-mid">
          <AlertDialogHeader>
            <AlertDialogTitle className="text-white">Delete Rule</AlertDialogTitle>
            <AlertDialogDescription className="text-stone">
              Are you sure? This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel className="bg-navy border-navy-mid text-white hover:bg-navy-deep">
              Cancel
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={handleConfirmDelete}
              className="bg-coral text-white hover:bg-coral-deep"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

/* ─── Merchant Row ─── */

interface MerchantRowProps {
  merchant: Merchant;
  budgetOptions: Array<{ groupName: string; budgets: Array<{ id: string; name: string }> }>;
  onAssign: (budgetId: string) => void;
}

function MerchantRow({ merchant, budgetOptions, onAssign }: MerchantRowProps) {
  return (
    <div className="flex items-center justify-between p-3 bg-navy rounded-xl hover:bg-navy-deep transition-colors">
      <div className="flex-1">
        <div className="text-white font-medium">{merchant.name}</div>
        <div className="text-xs text-stone">
          {merchant.transaction_count} transaction{merchant.transaction_count !== 1 ? "s" : ""}
        </div>
      </div>
      <div className="min-w-[200px]">
        <select
          value={merchant.assigned_budget_id || ""}
          onChange={(e) => {
            if (e.target.value) {
              onAssign(e.target.value);
            }
          }}
          className="bg-navy-deep border border-navy-mid rounded-lg px-3 py-1.5 text-white w-full text-sm"
        >
          <option value="">{merchant.assigned_budget_id ? "Change category..." : "Pick category ▾"}</option>
          {budgetOptions.map((group) => (
            <optgroup key={group.groupName} label={group.groupName}>
              {group.budgets.map((b) => (
                <option key={b.id} value={b.id}>
                  {b.name}
                </option>
              ))}
            </optgroup>
          ))}
        </select>
        {merchant.assigned_budget_name && (
          <div className="text-xs text-mint mt-1 pl-1">{merchant.assigned_budget_name}</div>
        )}
      </div>
    </div>
  );
}

/* ─── Helpers ─── */

function formatCondition(conditions: Record<string, unknown>): string {
  const parts: string[] = [];
  if (conditions.merchant_pattern) parts.push(`Merchant contains "${conditions.merchant_pattern}"`);
  if (conditions.merchant_exact) parts.push(`Merchant = "${conditions.merchant_exact}"`);
  if (conditions.monzo_category) parts.push(`Category is "${conditions.monzo_category}"`);
  if (conditions.amount_min) parts.push(`Amount ≥ ${conditions.amount_min}p`);
  if (conditions.amount_max) parts.push(`Amount ≤ ${conditions.amount_max}p`);
  if (conditions.day_of_week !== undefined) parts.push(`Day = ${conditions.day_of_week}`);
  return parts.join(" AND ") || "No conditions";
}
