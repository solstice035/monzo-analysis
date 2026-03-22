import { ChevronLeft, ChevronRight, RefreshCw } from "lucide-react";
import { Button } from "./button";
import { AccountSelector } from "@/components/account-selector";
import { cn, formatCurrency } from "@/lib/utils";
import {
  useTriggerSync,
  useSyncStatus,
  useBudgetGroupStatuses,
} from "@/hooks/useApi";

const MONTH_NAMES = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];

export interface TopBarBudgetProps {
  monthOffset: number;
  onPrevMonth: () => void;
  onNextMonth: () => void;
  className?: string;
}

export function TopBarBudget({
  monthOffset,
  onPrevMonth,
  onNextMonth,
  className,
}: TopBarBudgetProps) {
  const syncMutation = useTriggerSync();
  const { data: syncStatus } = useSyncStatus();
  const { data: budgetGroups } = useBudgetGroupStatuses();

  // Current month display
  const now = new Date();
  const displayDate = new Date(now.getFullYear(), now.getMonth() + monthOffset, 1);
  const monthLabel = `${MONTH_NAMES[displayDate.getMonth()]} ${displayDate.getFullYear()}`;

  const totalBudgeted = budgetGroups?.reduce((sum, g) => sum + g.total_budget, 0) ?? 0;
  const totalSpent = budgetGroups?.reduce((sum, g) => sum + g.total_spent, 0) ?? 0;
  const readyToAssign = totalBudgeted - totalSpent;

  // Sync status
  const lastSyncLabel = syncStatus?.last_sync
    ? formatRelativeTime(syncStatus.last_sync)
    : "never";

  const syncStatusColor =
    syncStatus?.status === "running"
      ? "text-yellow"
      : syncStatus?.status === "failed"
      ? "text-coral"
      : "text-mint";

  return (
    <header className={cn("flex items-center justify-between mb-6", className)}>
      {/* Month navigation */}
      <div className="flex items-center gap-3">
        <button
          onClick={onPrevMonth}
          className="p-2 rounded-lg text-stone hover:text-white hover:bg-navy-mid transition-colors"
        >
          <ChevronLeft className="w-5 h-5" />
        </button>

        <h1
          className="text-3xl text-white min-w-[220px] text-center"
          style={{ fontFamily: "var(--font-display)", letterSpacing: "0.02em" }}
        >
          {monthLabel.toUpperCase()}
        </h1>

        <button
          onClick={onNextMonth}
          disabled={monthOffset >= 0}
          className={cn(
            "p-2 rounded-lg transition-colors",
            monthOffset >= 0
              ? "text-navy-mid cursor-not-allowed"
              : "text-stone hover:text-white hover:bg-navy-mid"
          )}
        >
          <ChevronRight className="w-5 h-5" />
        </button>
      </div>

      {/* Ready to Assign */}
      <div className="flex items-center gap-8">
        <div className="text-center">
          <div className="text-xs text-stone uppercase tracking-wider mb-1">
            Ready to Assign
          </div>
          <div
            className={cn(
              "text-2xl",
              readyToAssign >= 0 ? "text-mint" : "text-coral"
            )}
            style={{ fontFamily: "var(--font-display)" }}
          >
            {formatCurrency(Math.abs(readyToAssign))}
            {readyToAssign < 0 && (
              <span className="text-xs text-coral ml-1">over</span>
            )}
          </div>
        </div>

        {/* Sync status */}
        <div className="flex items-center gap-3">
          <div className="text-right">
            <span className={cn("text-xs", syncStatusColor)}>
              {syncStatus?.status === "running" ? (
                <span className="animate-pulse">syncing…</span>
              ) : (
                <>● Synced {lastSyncLabel}</>
              )}
            </span>
          </div>
          <Button
            size="sm"
            variant="outline"
            onClick={() => syncMutation.mutate()}
            disabled={syncMutation.isPending}
            className="h-8"
          >
            <RefreshCw
              className={cn("w-3.5 h-3.5", syncMutation.isPending && "animate-spin")}
            />
          </Button>
        </div>

        <AccountSelector />
      </div>
    </header>
  );
}

function formatRelativeTime(isoDate: string): string {
  const diff = Date.now() - new Date(isoDate).getTime();
  const minutes = Math.floor(diff / 60000);
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}
