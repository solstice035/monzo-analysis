import { Button } from "@/components/ui/button";
import { RefreshCw } from "lucide-react";

interface TopBarProps {
  title: string;
  subtitle?: string;
  showSync?: boolean;
  onSync?: () => void;
  isSyncing?: boolean;
}

export function TopBar({
  title,
  subtitle,
  showSync = true,
  onSync,
  isSyncing = false,
}: TopBarProps) {
  return (
    <header className="flex justify-between items-end mb-8">
      <div>
        <h1
          className="text-5xl text-white"
          style={{ fontFamily: "var(--font-display)", letterSpacing: "0.02em" }}
        >
          {title}
        </h1>
        {subtitle && <p className="text-stone mt-1">{subtitle}</p>}
      </div>
      {showSync && (
        <Button onClick={onSync} disabled={isSyncing}>
          <RefreshCw className={cn("w-4 h-4", isSyncing && "animate-spin")} />
          {isSyncing ? "SYNCING..." : "SYNC NOW"}
        </Button>
      )}
    </header>
  );
}

function cn(...classes: (string | boolean | undefined)[]) {
  return classes.filter(Boolean).join(" ");
}
