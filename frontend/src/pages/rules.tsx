import { useState } from "react";
import { TopBar } from "@/components/layout";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { CategoryPill } from "@/components/ui/category-pill";
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
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Plus, ArrowRight, Pencil, Trash2 } from "lucide-react";
import { useRules, useCreateRule, useUpdateRule, useDeleteRule } from "@/hooks/useApi";
import { useAccount } from "@/contexts/AccountContext";
import type { CategoryRule } from "@/lib/api";

const categories = [
  "groceries",
  "eating_out",
  "shopping",
  "transport",
  "entertainment",
  "bills",
  "general",
  "holidays",
];

const conditionFields = [
  { value: "merchant_name", label: "Merchant Name" },
  { value: "merchant_category", label: "Merchant Category" },
  { value: "amount", label: "Amount (pence)" },
];

const conditionOperators = [
  { value: "contains", label: "contains" },
  { value: "equals", label: "equals" },
  { value: "greater_than", label: "greater than" },
  { value: "less_than", label: "less than" },
];

interface RuleFormData {
  name: string;
  target_category: string;
  priority: number;
  enabled: boolean;
  condition_field: string;
  condition_operator: string;
  condition_value: string;
}

function formatCondition(conditions: Record<string, unknown>): string {
  // Handle conditions object structure
  const parts: string[] = [];

  if (conditions.merchant_name) {
    parts.push(`Merchant contains "${conditions.merchant_name}"`);
  }
  if (conditions.merchant_category) {
    parts.push(`Category is "${conditions.merchant_category}"`);
  }
  if (conditions.amount_gt) {
    parts.push(`Amount > £${(Number(conditions.amount_gt) / 100).toFixed(2)}`);
  }
  if (conditions.amount_lt) {
    parts.push(`Amount < £${(Number(conditions.amount_lt) / 100).toFixed(2)}`);
  }

  return parts.join(" AND ") || "No conditions";
}

export function Rules() {
  const { selectedAccount } = useAccount();
  const { data: rules, isLoading, error } = useRules();
  const createRule = useCreateRule();
  const updateRule = useUpdateRule();
  const deleteRule = useDeleteRule();

  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [ruleToDelete, setRuleToDelete] = useState<string | null>(null);
  const [editingRule, setEditingRule] = useState<CategoryRule | null>(null);
  const [formData, setFormData] = useState<RuleFormData>({
    name: "",
    target_category: "groceries",
    priority: 1,
    enabled: true,
    condition_field: "merchant_name",
    condition_operator: "contains",
    condition_value: "",
  });

  const rulesList = rules || [];

  const handleOpenDialog = (rule?: CategoryRule) => {
    if (rule) {
      // Extract condition from the conditions object
      const conditions = rule.conditions as Record<string, unknown>;
      let field = "merchant_name";
      let operator = "contains";
      let value = "";

      if (conditions.merchant_name) {
        field = "merchant_name";
        operator = "contains";
        value = String(conditions.merchant_name);
      } else if (conditions.merchant_category) {
        field = "merchant_category";
        operator = "equals";
        value = String(conditions.merchant_category);
      } else if (conditions.amount_gt) {
        field = "amount";
        operator = "greater_than";
        value = String(conditions.amount_gt);
      } else if (conditions.amount_lt) {
        field = "amount";
        operator = "less_than";
        value = String(conditions.amount_lt);
      }

      setFormData({
        name: rule.name,
        target_category: rule.target_category,
        priority: rule.priority,
        enabled: rule.enabled,
        condition_field: field,
        condition_operator: operator,
        condition_value: value,
      });
      setEditingRule(rule);
    } else {
      setFormData({
        name: "",
        target_category: "groceries",
        priority: rulesList.length + 1,
        enabled: true,
        condition_field: "merchant_name",
        condition_operator: "contains",
        condition_value: "",
      });
      setEditingRule(null);
    }
    setIsDialogOpen(true);
  };

  const handleSubmit = async () => {
    if (!selectedAccount) return;

    // Build conditions object based on field and operator
    const conditions: Record<string, unknown> = {};

    if (formData.condition_field === "merchant_name") {
      conditions.merchant_name = formData.condition_value;
    } else if (formData.condition_field === "merchant_category") {
      conditions.merchant_category = formData.condition_value;
    } else if (formData.condition_field === "amount") {
      if (formData.condition_operator === "greater_than") {
        conditions.amount_gt = parseInt(formData.condition_value);
      } else {
        conditions.amount_lt = parseInt(formData.condition_value);
      }
    }

    const ruleData = {
      name: formData.name,
      target_category: formData.target_category,
      priority: formData.priority,
      enabled: formData.enabled,
      conditions,
    };

    if (editingRule) {
      await updateRule.mutateAsync({
        id: editingRule.id,
        data: ruleData,
      });
    } else {
      await createRule.mutateAsync({
        ...ruleData,
        account_id: selectedAccount.id,
      });
    }

    setIsDialogOpen(false);
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

  return (
    <div>
      <TopBar
        title="RULES"
        subtitle={`${rulesList.length} categorisation rules`}
        showSync={false}
      />

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>CATEGORISATION RULES</CardTitle>
          <Button size="sm" onClick={() => handleOpenDialog()}>
            <Plus className="w-4 h-4" />
            ADD RULE
          </Button>
        </CardHeader>
        <CardContent>
          <div className="text-sm text-stone mb-4">
            Rules are evaluated in priority order. Lower numbers are checked first.
          </div>

          {isLoading && (
            <div className="text-center py-8 text-stone">Loading rules...</div>
          )}
          {error && (
            <div className="text-center py-8 text-coral">
              Failed to load rules. Please try again.
            </div>
          )}
          {!isLoading && !error && rulesList.length === 0 && (
            <div className="text-center py-8 text-stone">
              No rules configured. Click "ADD RULE" to create one.
            </div>
          )}

          <div className="space-y-3">
            {rulesList.map((rule) => (
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
                    {formatCondition(rule.conditions)}
                  </div>
                </div>

                <ArrowRight className="w-5 h-5 text-stone" />

                <CategoryPill category={rule.target_category} />

                <div className="flex gap-2">
                  <button
                    onClick={() => handleOpenDialog(rule)}
                    className="p-2 text-stone hover:text-white transition-colors"
                  >
                    <Pencil className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => handleDeleteClick(rule.id)}
                    className="p-2 text-stone hover:text-coral transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Add/Edit Rule Dialog */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {editingRule ? "Edit Rule" : "Add New Rule"}
            </DialogTitle>
            <DialogDescription>
              Create a rule to automatically categorise transactions.
            </DialogDescription>
          </DialogHeader>

          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="name" className="text-white">Rule Name</Label>
              <Input
                id="name"
                placeholder="e.g., Coffee shops"
                value={formData.name}
                onChange={(e) =>
                  setFormData({ ...formData, name: e.target.value })
                }
                className="bg-navy border-navy-mid text-white placeholder:text-stone"
              />
            </div>

            <div className="grid gap-2">
              <Label className="text-white">Condition</Label>
              <div className="flex gap-2">
                <select
                  value={formData.condition_field}
                  onChange={(e) =>
                    setFormData({ ...formData, condition_field: e.target.value })
                  }
                  className="bg-navy border border-navy-mid rounded-lg px-3 py-2 text-white flex-1"
                >
                  {conditionFields.map((f) => (
                    <option key={f.value} value={f.value}>
                      {f.label}
                    </option>
                  ))}
                </select>
                <select
                  value={formData.condition_operator}
                  onChange={(e) =>
                    setFormData({ ...formData, condition_operator: e.target.value })
                  }
                  className="bg-navy border border-navy-mid rounded-lg px-3 py-2 text-white"
                >
                  {conditionOperators.map((op) => (
                    <option key={op.value} value={op.value}>
                      {op.label}
                    </option>
                  ))}
                </select>
              </div>
              <Input
                placeholder={formData.condition_field === "amount" ? "Amount in pence (e.g., 10000 = £100)" : "Value to match"}
                value={formData.condition_value}
                onChange={(e) =>
                  setFormData({ ...formData, condition_value: e.target.value })
                }
                className="bg-navy border-navy-mid text-white placeholder:text-stone"
              />
            </div>

            <div className="grid gap-2">
              <Label htmlFor="category" className="text-white">Assign to Category</Label>
              <select
                id="category"
                value={formData.target_category}
                onChange={(e) =>
                  setFormData({ ...formData, target_category: e.target.value })
                }
                className="bg-navy border border-navy-mid rounded-lg px-4 py-2 text-white w-full"
              >
                {categories.map((cat) => (
                  <option key={cat} value={cat}>
                    {cat.replace(/_/g, " ")}
                  </option>
                ))}
              </select>
            </div>

            <div className="grid gap-2">
              <Label htmlFor="priority" className="text-white">Priority (lower = checked first)</Label>
              <Input
                id="priority"
                type="number"
                min="1"
                value={formData.priority}
                onChange={(e) =>
                  setFormData({ ...formData, priority: parseInt(e.target.value) || 1 })
                }
                className="bg-navy border-navy-mid text-white"
              />
            </div>
          </div>

          <DialogFooter>
            <Button
              variant="ghost"
              onClick={() => setIsDialogOpen(false)}
            >
              Cancel
            </Button>
            <Button
              onClick={handleSubmit}
              disabled={!formData.name || !formData.condition_value}
            >
              {editingRule ? "Save Changes" : "Create Rule"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent className="bg-charcoal border-navy-mid">
          <AlertDialogHeader>
            <AlertDialogTitle className="text-white">Delete Rule</AlertDialogTitle>
            <AlertDialogDescription className="text-stone">
              Are you sure you want to delete this rule? This action cannot be undone.
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
