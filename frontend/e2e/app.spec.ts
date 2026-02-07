import { test, expect, Page } from "@playwright/test";

/**
 * Mock all backend API responses so E2E tests run without a backend.
 * Intercepts requests to http://localhost:8000/api/v1/* and returns
 * realistic fixture data.
 */
async function mockApi(page: Page) {
  // Auth status — authenticated
  await page.route("**/api/v1/auth/status", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        authenticated: true,
        expires_at: "2030-01-01T00:00:00Z",
      }),
    })
  );

  // Accounts
  await page.route("**/api/v1/accounts", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify([
        {
          id: "acc_joint",
          monzo_id: "acc_monzo_joint",
          type: "uk_retail_joint",
          name: "Joint Account",
        },
        {
          id: "acc_personal",
          monzo_id: "acc_monzo_personal",
          type: "uk_retail",
          name: "Personal Account",
        },
      ]),
    })
  );

  // Sync status
  await page.route("**/api/v1/sync/status", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        status: "success",
        last_sync: new Date().toISOString(),
        transactions_synced: 42,
      }),
    })
  );

  // Dashboard summary
  await page.route("**/api/v1/dashboard/summary*", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        balance: 150000,
        spend_today: 2500,
        spend_this_month: 85000,
        transaction_count: 342,
        top_categories: [
          { category: "groceries", amount: 35000 },
          { category: "eating_out", amount: 18000 },
          { category: "transport", amount: 12000 },
        ],
      }),
    })
  );

  // Dashboard trends
  await page.route("**/api/v1/dashboard/trends*", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        daily_spend: Array.from({ length: 30 }, (_, i) => ({
          date: `2026-01-${String(i + 1).padStart(2, "0")}`,
          amount: Math.floor(Math.random() * 5000) + 1000,
        })),
        average_daily: 3200,
        total: 96000,
      }),
    })
  );

  // Dashboard recurring
  await page.route("**/api/v1/dashboard/recurring*", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        items: [
          {
            merchant_name: "Netflix",
            category: "entertainment",
            average_amount: 1599,
            frequency_days: 30,
            frequency_label: "monthly",
            transaction_count: 6,
            monthly_cost: 1599,
            last_transaction: "2026-01-15",
            next_expected: "2026-02-15",
            confidence: 0.95,
          },
        ],
        total_monthly_cost: 1599,
      }),
    })
  );

  // Transactions
  await page.route("**/api/v1/transactions*", (route) => {
    if (route.request().method() === "GET") {
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          items: [
            {
              id: "tx_1",
              monzo_id: "tx_monzo_1",
              amount: -4500,
              merchant_name: "Tesco",
              monzo_category: "groceries",
              custom_category: null,
              created_at: "2026-02-01T10:00:00Z",
              settled_at: "2026-02-01T12:00:00Z",
              notes: null,
            },
            {
              id: "tx_2",
              monzo_id: "tx_monzo_2",
              amount: -1200,
              merchant_name: "Costa Coffee",
              monzo_category: "eating_out",
              custom_category: null,
              created_at: "2026-02-01T08:30:00Z",
              settled_at: null,
              notes: null,
            },
          ],
          total: 2,
        }),
      });
    }
    return route.fulfill({ status: 200, contentType: "application/json", body: "{}" });
  });

  // Budget groups
  await page.route("**/api/v1/budget-groups/status*", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify([
        {
          group_id: "grp_1",
          name: "Fixed Bills",
          icon: "🏠",
          display_order: 0,
          total_amount: 50000,
          total_spent: 35000,
          total_remaining: 15000,
          percentage: 70,
          status: "under",
          budget_count: 3,
          budgets: [],
          period_start: "2026-02-01",
          period_end: "2026-02-28",
        },
      ]),
    })
  );

  await page.route("**/api/v1/budget-groups/dashboard*", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        groups: [],
        total_budget: 80000,
        total_spent: 50000,
        total_remaining: 30000,
        overall_percentage: 62.5,
        overall_status: "under",
        period_start: "2026-02-01",
        period_end: "2026-02-28",
        days_in_period: 28,
        days_elapsed: 7,
      }),
    })
  );

  await page.route("**/api/v1/budget-groups*", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify([]),
    })
  );

  // Budgets
  await page.route("**/api/v1/budgets/status*", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify([]),
    })
  );

  await page.route("**/api/v1/budgets*", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify([]),
    })
  );

  // Rules
  await page.route("**/api/v1/rules*", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify([]),
    })
  );
}

test.describe("Dashboard", () => {
  test("loads and displays summary stats", async ({ page }) => {
    await mockApi(page);
    await page.goto("/");

    // Should see the Monzo Analysis branding
    await expect(page.locator("text=MONZO ANALYSIS")).toBeVisible();

    // Default view is "Budget" tab — check budget data renders
    await expect(page.locator("text=TOTAL BUDGET")).toBeVisible({ timeout: 10_000 });
  });

  test("shows navigation sidebar with all links", async ({ page }) => {
    await mockApi(page);
    await page.goto("/");

    const nav = page.locator("nav");
    await expect(nav.locator("text=Dashboard")).toBeVisible();
    await expect(nav.locator("text=Transactions")).toBeVisible();
    await expect(nav.locator("text=Budgets")).toBeVisible();
    await expect(nav.locator("text=Subscriptions")).toBeVisible();
    await expect(nav.locator("text=Rules")).toBeVisible();
    await expect(nav.locator("text=Settings")).toBeVisible();
  });

  test("shows last sync status", async ({ page }) => {
    await mockApi(page);
    await page.goto("/");

    await expect(page.locator("text=Last sync")).toBeVisible();
  });
});

test.describe("Navigation", () => {
  test("navigates to transactions page", async ({ page }) => {
    await mockApi(page);
    await page.goto("/");

    await page.click("nav >> text=Transactions");
    await expect(page).toHaveURL(/\/transactions/);
    // Should show transaction data
    await expect(page.locator("text=Tesco")).toBeVisible({ timeout: 10_000 });
  });

  test("navigates to budgets page", async ({ page }) => {
    await mockApi(page);
    await page.goto("/");

    await page.click("nav >> text=Budgets");
    await expect(page).toHaveURL(/\/budgets/);
  });

  test("navigates to settings page", async ({ page }) => {
    await mockApi(page);
    await page.goto("/");

    await page.click("nav >> text=Settings");
    await expect(page).toHaveURL(/\/settings/);
  });

  test("navigates to subscriptions page", async ({ page }) => {
    await mockApi(page);
    await page.goto("/");

    await page.click("nav >> text=Subscriptions");
    await expect(page).toHaveURL(/\/subscriptions/);
  });
});

test.describe("Transactions page", () => {
  test("displays transaction list", async ({ page }) => {
    await mockApi(page);
    await page.goto("/transactions");

    await expect(page.locator("text=Tesco")).toBeVisible({ timeout: 10_000 });
    await expect(page.locator("text=Costa Coffee")).toBeVisible();
  });
});

test.describe("Budgets page", () => {
  test("loads budgets page", async ({ page }) => {
    await mockApi(page);
    await page.goto("/budgets");

    // Page should load without errors
    await expect(page.locator("nav >> text=Budgets")).toBeVisible();
  });
});

test.describe("Settings page", () => {
  test("loads settings page", async ({ page }) => {
    await mockApi(page);
    await page.goto("/settings");

    await expect(page.locator("nav >> text=Settings")).toBeVisible();
  });
});

test.describe("404 page", () => {
  test("shows 404 for unknown routes", async ({ page }) => {
    await mockApi(page);
    await page.goto("/nonexistent-page");

    await expect(page.locator("text=404")).toBeVisible();
    await expect(page.locator("text=PAGE NOT FOUND")).toBeVisible();
  });

  test("has link back to dashboard", async ({ page }) => {
    await mockApi(page);
    await page.goto("/nonexistent-page");

    await page.click("text=Back to Dashboard");
    await expect(page).toHaveURL("/");
  });
});
