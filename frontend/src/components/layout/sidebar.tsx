import { NavLink } from "react-router-dom";
import { cn, formatCurrency } from "@/lib/utils";
import {
  LayoutDashboard,
  Receipt,
  PiggyBank,
  Settings,
  Workflow,
  RefreshCw,
} from "lucide-react";
import { useSyncStatus, useBudgetGroupStatuses } from "@/hooks/useApi";
import { useMemo } from "react";

const navItems = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/transactions", label: "Transactions", icon: Receipt, badge: "8" },
  { to: "/budgets", label: "Budgets", icon: PiggyBank },
  { to: "/subscriptions", label: "Subscriptions", icon: RefreshCw },
  { to: "/rules", label: "Rules", icon: Workflow },
  { to: "/settings", label: "Settings", icon: Settings },
];

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

export function Sidebar() {
  const { data: syncStatus } = useSyncStatus();
  const { data: budgetGroups } = useBudgetGroupStatuses();

  const lastSyncLabel = syncStatus?.last_sync
    ? formatRelativeTime(syncStatus.last_sync)
    : "never";

  const statusColor =
    syncStatus?.status === "running"
      ? "text-yellow"
      : syncStatus?.status === "failed"
        ? "text-coral"
        : "text-stone";

  // Budget pulse data
  const budgetPulse = useMemo(() => {
    if (!budgetGroups || budgetGroups.length === 0) return null;
    const totalBudget = budgetGroups.reduce((s, g) => s + g.total_budget, 0);
    const totalSpent = budgetGroups.reduce((s, g) => s + g.total_spent, 0);
    const remaining = totalBudget - totalSpent;
    const percentage = totalBudget > 0 ? (totalSpent / totalBudget) * 100 : 0;

    const now = new Date();
    const totalDays = new Date(now.getFullYear(), now.getMonth() + 1, 0).getDate();
    const daysLeft = totalDays - now.getDate();
    const expectedPercentage = (now.getDate() / totalDays) * 100;
    const onTrack = percentage <= expectedPercentage;

    return { remaining, daysLeft, percentage, onTrack };
  }, [budgetGroups]);

  return (
    <aside className="w-64 h-screen bg-charcoal border-r border-navy-mid flex flex-col fixed left-0 top-0">
      {/* Logo */}
      <div className="p-6 border-b border-navy-mid">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-coral rounded-lg flex items-center justify-center shadow-[0_0_30px_rgba(255,90,95,0.4)]">
            <span
              className="text-white text-xl"
              style={{ fontFamily: "var(--font-display)" }}
            >
              M
            </span>
          </div>
          <span
            className="text-white text-lg tracking-wider"
            style={{ fontFamily: "var(--font-display)" }}
          >
            MONZO ANALYSIS
          </span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4">
        <ul className="space-y-0.5 px-3">
          {navItems.map(({ to, label, icon: Icon, badge }) => (
            <li key={to}>
              <NavLink
                to={to}
                className={({ isActive }) =>
                  cn(
                    "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-all",
                    isActive
                      ? "bg-coral/10 text-coral border-l-2 border-coral -ml-px"
                      : "text-stone hover:text-white hover:bg-navy-mid/50 border-l-2 border-transparent -ml-px"
                  )
                }
              >
                <Icon className="w-5 h-5" strokeWidth={1.75} />
                <span className="flex-1">{label}</span>
                {badge && (
                  <span className="px-1.5 py-0.5 rounded-full bg-coral/20 text-coral text-[10px] font-semibold">
                    {badge}
                  </span>
                )}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>

      {/* Budget pulse widget */}
      {budgetPulse && (
        <div className="px-4 py-3 border-t border-navy-mid">
          <div className="flex justify-between items-baseline mb-1.5">
            <span className="text-xs text-stone uppercase tracking-wider">This month</span>
            <span
              className="text-xs text-stone tabular-nums"
              style={{ fontFamily: "var(--font-mono)" }}
            >
              {budgetPulse.daysLeft}d left
            </span>
          </div>
          <div className="flex justify-between items-baseline">
            <span
              className="text-sm text-white tabular-nums"
              style={{ fontFamily: "var(--font-mono)" }}
            >
              {formatCurrency(Math.abs(budgetPulse.remaining))}
              {budgetPulse.remaining < 0 && (
                <span className="text-xs text-coral ml-1">over</span>
              )}
            </span>
            <span
              className={cn(
                "text-xs font-medium",
                budgetPulse.onTrack ? "text-mint" : "text-coral"
              )}
            >
              {budgetPulse.onTrack ? "on track" : "over pace"}
            </span>
          </div>
          <div className="h-1 bg-navy rounded-full mt-2 overflow-hidden">
            <div
              className={cn(
                "h-full rounded-full transition-all",
                budgetPulse.percentage > 100 ? "bg-coral" : "bg-mint"
              )}
              style={{ width: `${Math.min(budgetPulse.percentage, 100)}%` }}
            />
          </div>
        </div>
      )}

      {/* Footer — sync status */}
      <div className="px-4 py-3 border-t border-navy-mid">
        <div className="text-xs text-slate">
          Last sync: <span className={statusColor}>{lastSyncLabel}</span>
          {syncStatus?.status === "running" && (
            <span className="ml-1 animate-pulse">syncing...</span>
          )}
        </div>
      </div>
    </aside>
  );
}
