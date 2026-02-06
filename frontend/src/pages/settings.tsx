import { useState } from "react";
import { TopBar } from "@/components/layout";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
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
import { useAuthStatus, useSyncStatus } from "@/hooks/useApi";
import { api } from "@/lib/api";
import { CheckCircle, XCircle, Loader2 } from "lucide-react";

export function Settings() {
  const { data: authStatus, isLoading: authLoading } = useAuthStatus();
  const { data: syncStatus } = useSyncStatus();
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);

  const handleReconnect = async () => {
    try {
      const response = await api.getLoginUrl();
      window.location.href = response.url;
    } catch (error) {
      console.error("Failed to get login URL:", error);
    }
  };

  const handleDisconnect = () => {
    localStorage.removeItem("monzo_auth");
    window.location.href = "/";
  };

  const handleDeleteEverything = () => {
    localStorage.clear();
    window.location.href = "/";
  };

  const formatLastSync = () => {
    if (!syncStatus?.last_sync) return "Never";
    const date = new Date(syncStatus.last_sync);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));

    if (diffHours < 1) return "Less than an hour ago";
    if (diffHours === 1) return "1 hour ago";
    if (diffHours < 24) return `${diffHours} hours ago`;
    const diffDays = Math.floor(diffHours / 24);
    return diffDays === 1 ? "1 day ago" : `${diffDays} days ago`;
  };

  return (
    <div>
      <TopBar title="SETTINGS" showSync={false} />

      <div className="grid gap-6">
        {/* Monzo Connection */}
        <Card>
          <CardHeader>
            <CardTitle>MONZO CONNECTION</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                {authLoading ? (
                  <Loader2 className="w-5 h-5 text-stone animate-spin" />
                ) : authStatus?.authenticated ? (
                  <CheckCircle className="w-5 h-5 text-mint" />
                ) : (
                  <XCircle className="w-5 h-5 text-coral" />
                )}
                <div>
                  <div className="font-semibold text-white mb-1">
                    {authLoading
                      ? "Checking connection..."
                      : authStatus?.authenticated
                        ? "Account Connected"
                        : "Not Connected"}
                  </div>
                  <div className="text-sm text-stone">
                    {authStatus?.authenticated ? (
                      <>
                        Last sync: {formatLastSync()}
                        {syncStatus?.transactions_synced !== undefined &&
                          ` · ${syncStatus.transactions_synced.toLocaleString()} transactions`}
                      </>
                    ) : (
                      "Connect your Monzo account to start tracking"
                    )}
                  </div>
                </div>
              </div>
              <div className="flex gap-3">
                <Button variant="secondary" size="sm" onClick={handleReconnect}>
                  {authStatus?.authenticated ? "RECONNECT" : "CONNECT"}
                </Button>
                {authStatus?.authenticated && (
                  <Button variant="ghost" size="sm" onClick={handleDisconnect}>
                    DISCONNECT
                  </Button>
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Sync Info */}
        <Card>
          <CardHeader>
            <CardTitle>SYNC CONFIGURATION</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-sm text-stone space-y-2">
              <p>
                Sync interval and schedule are configured via environment variables on the server.
              </p>
              <p>
                Budget reset days are set per-budget on the Budgets page.
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Danger Zone */}
        <Card className="border-coral/30">
          <CardHeader>
            <CardTitle className="text-coral">DANGER ZONE</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div>
                <div className="font-semibold text-white mb-1">
                  Delete All Data
                </div>
                <div className="text-sm text-stone">
                  Permanently delete all transactions, budgets, and rules
                </div>
              </div>
              <Button
                variant="secondary"
                size="sm"
                onClick={() => setDeleteDialogOpen(true)}
                className="border-coral text-coral hover:bg-coral hover:text-white"
              >
                DELETE EVERYTHING
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent className="bg-charcoal border-navy-mid">
          <AlertDialogHeader>
            <AlertDialogTitle className="text-coral">
              Delete All Data
            </AlertDialogTitle>
            <AlertDialogDescription className="text-stone">
              This action cannot be undone. This will permanently delete all your
              transactions, budgets, rules, and settings.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel className="bg-navy border-navy-mid text-white hover:bg-navy-deep">
              Cancel
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeleteEverything}
              className="bg-coral text-white hover:bg-coral-deep"
            >
              Yes, Delete Everything
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
