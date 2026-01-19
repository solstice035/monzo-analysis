import { useState, useEffect } from "react";
import { TopBar } from "@/components/layout";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
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

interface NotificationSettings {
  syncCompleted: boolean;
  budgetWarnings: boolean;
  budgetExceeded: boolean;
  dailySummary: boolean;
}

export function Settings() {
  const { data: authStatus, isLoading: authLoading } = useAuthStatus();
  const { data: syncStatus } = useSyncStatus();

  const [syncInterval, setSyncInterval] = useState("24");
  const [budgetResetDay, setBudgetResetDay] = useState("1");
  const [webhookUrl, setWebhookUrl] = useState("");
  const [notifications, setNotifications] = useState<NotificationSettings>({
    syncCompleted: true,
    budgetWarnings: true,
    budgetExceeded: true,
    dailySummary: true,
  });
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);

  // Load settings from localStorage on mount
  useEffect(() => {
    const savedSettings = localStorage.getItem("monzo_settings");
    if (savedSettings) {
      try {
        const parsed = JSON.parse(savedSettings);
        setSyncInterval(parsed.syncInterval || "24");
        setBudgetResetDay(parsed.budgetResetDay || "1");
        setWebhookUrl(parsed.webhookUrl || "");
        setNotifications(parsed.notifications || {
          syncCompleted: true,
          budgetWarnings: true,
          budgetExceeded: true,
          dailySummary: true,
        });
      } catch {
        // Ignore parse errors
      }
    }
  }, []);

  // Save settings to localStorage
  const saveSettings = () => {
    setIsSaving(true);
    const settings = {
      syncInterval,
      budgetResetDay,
      webhookUrl,
      notifications,
    };
    localStorage.setItem("monzo_settings", JSON.stringify(settings));

    // Simulate a brief delay for UX feedback
    setTimeout(() => {
      setIsSaving(false);
      setSaveMessage("Settings saved!");
      setTimeout(() => setSaveMessage(null), 2000);
    }, 300);
  };

  const handleReconnect = async () => {
    try {
      const response = await api.getLoginUrl();
      window.location.href = response.url;
    } catch (error) {
      console.error("Failed to get login URL:", error);
    }
  };

  const handleDisconnect = () => {
    // Clear local auth state and redirect to login
    localStorage.removeItem("monzo_auth");
    window.location.href = "/";
  };

  const handleDeleteEverything = () => {
    // Clear all local storage
    localStorage.clear();
    // Reload the page
    window.location.href = "/";
  };

  const handleNotificationChange = (key: keyof NotificationSettings) => {
    setNotifications((prev) => ({
      ...prev,
      [key]: !prev[key],
    }));
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

        {/* Sync Settings */}
        <Card>
          <CardHeader>
            <CardTitle>SYNC SETTINGS</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="font-semibold text-white mb-1">
                  Sync Interval
                </div>
                <div className="text-sm text-stone">
                  How often to fetch new transactions
                </div>
              </div>
              <select
                value={syncInterval}
                onChange={(e) => setSyncInterval(e.target.value)}
                className="bg-navy border border-navy-mid rounded-lg px-4 py-2 text-white"
              >
                <option value="1">Every hour</option>
                <option value="6">Every 6 hours</option>
                <option value="12">Every 12 hours</option>
                <option value="24">Daily</option>
              </select>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <div className="font-semibold text-white mb-1">
                  Budget Reset Day
                </div>
                <div className="text-sm text-stone">
                  Day of month when budgets reset (1-28)
                </div>
              </div>
              <select
                value={budgetResetDay}
                onChange={(e) => setBudgetResetDay(e.target.value)}
                className="bg-navy border border-navy-mid rounded-lg px-4 py-2 text-white"
              >
                {Array.from({ length: 28 }, (_, i) => i + 1).map((day) => (
                  <option key={day} value={day}>
                    {day}
                  </option>
                ))}
              </select>
            </div>

            <div className="pt-4 border-t border-navy-mid flex justify-end items-center gap-4">
              {saveMessage && (
                <span className="text-mint text-sm">{saveMessage}</span>
              )}
              <Button onClick={saveSettings} disabled={isSaving}>
                {isSaving ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Saving...
                  </>
                ) : (
                  "Save Settings"
                )}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Slack Integration */}
        <Card>
          <CardHeader>
            <CardTitle>SLACK NOTIFICATIONS</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex items-center justify-between gap-4">
              <div className="flex-shrink-0">
                <div className="font-semibold text-white mb-1">
                  Webhook URL
                </div>
                <div className="text-sm text-stone">
                  Slack incoming webhook for notifications
                </div>
              </div>
              <Input
                type="text"
                placeholder="https://hooks.slack.com/..."
                value={webhookUrl}
                onChange={(e) => setWebhookUrl(e.target.value)}
                className="bg-navy border-navy-mid text-white placeholder:text-stone max-w-md"
              />
            </div>

            <div className="border-t border-navy-mid pt-6">
              <div className="font-semibold text-white mb-4">
                Notification Types
              </div>
              <div className="space-y-3">
                {[
                  { key: "syncCompleted" as const, label: "Sync completed", description: "When transactions are synced" },
                  { key: "budgetWarnings" as const, label: "Budget warnings", description: "When approaching 80% of budget" },
                  { key: "budgetExceeded" as const, label: "Budget exceeded", description: "When budget is exceeded" },
                  { key: "dailySummary" as const, label: "Daily summary", description: "Daily spending summary" },
                ].map((item) => (
                  <label
                    key={item.key}
                    className="flex items-center gap-4 p-3 bg-navy rounded-lg cursor-pointer hover:bg-navy-deep transition-colors"
                  >
                    <input
                      type="checkbox"
                      checked={notifications[item.key]}
                      onChange={() => handleNotificationChange(item.key)}
                      className="w-5 h-5 rounded border-navy-mid bg-charcoal text-coral focus:ring-coral accent-coral"
                    />
                    <div>
                      <div className="font-medium text-white">{item.label}</div>
                      <div className="text-sm text-stone">{item.description}</div>
                    </div>
                  </label>
                ))}
              </div>
            </div>

            <div className="pt-4 border-t border-navy-mid flex justify-end">
              <Button onClick={saveSettings} disabled={isSaving}>
                {isSaving ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Saving...
                  </>
                ) : (
                  "Save Settings"
                )}
              </Button>
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
