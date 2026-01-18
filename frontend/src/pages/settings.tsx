import { TopBar } from "@/components/layout";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export function Settings() {
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
              <div>
                <div className="font-semibold text-white mb-1">
                  Account Connected
                </div>
                <div className="text-sm text-stone">
                  Last sync: 2 hours ago · 1,247 transactions
                </div>
              </div>
              <div className="flex gap-3">
                <Button variant="secondary" size="sm">
                  RECONNECT
                </Button>
                <Button variant="ghost" size="sm">
                  DISCONNECT
                </Button>
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
              <select className="bg-navy border border-navy-mid rounded-lg px-4 py-2 text-white">
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
              <select className="bg-navy border border-navy-mid rounded-lg px-4 py-2 text-white">
                {Array.from({ length: 28 }, (_, i) => i + 1).map((day) => (
                  <option key={day} value={day}>
                    {day}
                  </option>
                ))}
              </select>
            </div>
          </CardContent>
        </Card>

        {/* Slack Integration */}
        <Card>
          <CardHeader>
            <CardTitle>SLACK NOTIFICATIONS</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="font-semibold text-white mb-1">
                  Webhook URL
                </div>
                <div className="text-sm text-stone">
                  Slack incoming webhook for notifications
                </div>
              </div>
              <input
                type="text"
                placeholder="https://hooks.slack.com/..."
                className="bg-navy border border-navy-mid rounded-lg px-4 py-2 text-white w-80"
              />
            </div>

            <div className="border-t border-navy-mid pt-6">
              <div className="font-semibold text-white mb-4">
                Notification Types
              </div>
              <div className="space-y-3">
                {[
                  { label: "Sync completed", description: "When transactions are synced" },
                  { label: "Budget warnings", description: "When approaching 80% of budget" },
                  { label: "Budget exceeded", description: "When budget is exceeded" },
                  { label: "Daily summary", description: "Daily spending summary" },
                ].map((item) => (
                  <label
                    key={item.label}
                    className="flex items-center gap-4 p-3 bg-navy rounded-lg cursor-pointer hover:bg-navy-deep transition-colors"
                  >
                    <input
                      type="checkbox"
                      defaultChecked
                      className="w-5 h-5 rounded border-navy-mid bg-navy text-coral focus:ring-coral"
                    />
                    <div>
                      <div className="font-medium text-white">{item.label}</div>
                      <div className="text-sm text-stone">{item.description}</div>
                    </div>
                  </label>
                ))}
              </div>
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
                className="border-coral text-coral hover:bg-coral hover:text-white"
              >
                DELETE EVERYTHING
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
