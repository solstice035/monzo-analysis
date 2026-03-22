import { type ReactNode } from "react";
import { Button } from "@/components/ui/button";
import { AccountSelector } from "@/components/account-selector";
import { RefreshCw } from "lucide-react";

interface TopBarProps {
  title: string;
  subtitle?: string;
  showSync?: boolean;
  onSync?: () => void;
  isSyncing?: boolean;
  children?: ReactNode;
}

export function TopBar({
  title,
  subtitle,
  showSync = true,
  onSync,
  isSyncing = false,
  children,
}: TopBarProps) {
  return (
    <header className="flex justify-between items-end mb-6">
      <div>
        <h1
          className="text-4xl text-white"
          style={{ fontFamily: "var(--font-display)", letterSpacing: "0.02em" }}
        >
          {title}
        </h1>
        {subtitle && <p className="text-sm text-stone mt-1">{subtitle}</p>}
      </div>
      <div className="flex items-center gap-3">
        {children}
        <AccountSelector />
        {showSync && (
          <Button size="sm" onClick={onSync} disabled={isSyncing}>
            <RefreshCw className={cn("w-3.5 h-3.5", isSyncing && "animate-spin")} />
            {isSyncing ? "SYNCING..." : "SYNC NOW"}
          </Button>
        )}
      </div>
    </header>
  );
}

function cn(...classes: (string | boolean | undefined)[]) {
  return classes.filter(Boolean).join(" ");
}
