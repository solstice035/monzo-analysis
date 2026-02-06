# Consolidated Code Review

**Consolidated from:** Reviews dated 2026-01-18, 2026-01-20, 2026-02-06
**Last verified:** 2026-02-06
**Context:** Personal dashboard on Mac Mini (Docker), single user, home network

---

## Status Summary

| ID | Issue | Severity | Status |
|----|-------|----------|--------|
| C1 | Token refresh never called | CRITICAL | OPEN |
| C2 | Scheduler budget alerts missing account filter | CRITICAL | OPEN |
| C3 | No pagination in transaction sync | CRITICAL | OPEN |
| H1 | Missing error boundaries in frontend | HIGH | OPEN |
| H2 | Database engine created per request | HIGH | **DONE** |
| H3 | CORS only configured for localhost | HIGH | OPEN |
| H4 | Frontend race conditions on account switch | HIGH | **DONE** |
| H5 | Mutation hooks don't scope to account ID | HIGH | **DONE** |
| H6 | Monzo API calls have no timeout | HIGH | OPEN |
| H7 | Rules engine not wired to sync | HIGH | OPEN |
| M1 | Migration 002 missing data backfill | MEDIUM | OPEN |
| M2 | Transaction pagination missing in frontend | MEDIUM | OPEN |
| M3 | Dashboard balance from local transactions | MEDIUM | OPEN |
| M4 | Settings page only persists to localStorage | MEDIUM | OPEN |
| M5 | Hardcoded "Last Sync" in sidebar | MEDIUM | OPEN |
| M6 | Transaction raw_payload JSON mutation | MEDIUM | OPEN |
| M7 | Budget start_day not validated (1-28) | MEDIUM | OPEN |
| M8 | Daily digest never called from scheduler | MEDIUM | OPEN |
| M9 | Transaction search missing in frontend | MEDIUM | OPEN |
| M10 | No transaction date range filter | MEDIUM | OPEN |
| M11 | System health Slack notification missing | MEDIUM | OPEN |
| L1 | Sync race condition (TOCTOU) | LOW | OPEN |
| L2 | Inconsistent sinking fund calculations | LOW | OPEN |
| L3 | No frontend 404 route | LOW | OPEN |
| L4 | CSV import not transactional | LOW | OPEN |
| L5 | Recurring detection arbitrary threshold | LOW | OPEN |
| L6 | Composite database index missing | LOW | OPEN |
| L7 | Rules update can't clear conditions | LOW | OPEN |
| L8 | Pydantic schemas inline | LOW | OPEN |
| L9 | Inefficient spend calculation (Python-side) | LOW | OPEN |
| L10 | Unnecessary date string manipulation | LOW | OPEN |
| L11 | Missing CSP header in nginx | LOW | OPEN |
| L12 | Frontend duplicates budget period logic | LOW | OPEN |
| L13 | No container resource limits | LOW | OPEN |
| L14 | Missing rules engine conditions | LOW | OPEN |
| L15 | No refund correlation logic | LOW | OPEN |
| L16 | No historical comparison on dashboard | LOW | OPEN |
| D1 | No authentication middleware | DEFERRED | — |
| D2 | IDOR in update/delete endpoints | DEFERRED | — |
| D3 | OAuth state not validated | DEFERRED | — |
| D4 | No input validation on frontend | DEFERRED | — |
| D5 | No CSV upload size limits | DEFERRED | — |
| D6 | No network isolation in Docker | DEFERRED | — |
| D7 | Backend port exposed in Docker | DEFERRED | — |
| D8 | Accessibility gaps | DEFERRED | — |

**Open:** 31 | **Done:** 3 | **Deferred:** 8

---

## PRD/TRD Feature Compliance

Assessment of all 24 PRD feature requirements against the implemented codebase.

### Must Have Features

| FR | Feature | Status | Notes |
|----|---------|--------|-------|
| FR-01 | Scheduled data extraction | PARTIAL | Works but breaks on token expiry (C1), misses data >100 txns (C3) |
| FR-02 | Full transaction payload | DONE | `raw_payload` JSONB, merchant expand, all fields captured |
| FR-04 | Store transaction history | DONE | Idempotent upsert on `monzo_id`, indexed |
| FR-05 | Auto-categorise (layered rules) | PARTIAL | Rules engine exists but **never called during sync** (H7) |
| FR-06 | Manual category override | DONE | PATCH endpoint + frontend modal |
| FR-09 | Import budget from spreadsheet | DONE | CSV import with validation and error reporting |
| FR-10 | Budget categories with monthly limits | DONE | Weekly/monthly periods, sinking funds, budget groups |
| FR-11 | Map transaction→budget categories | PARTIAL | Simple string match only, no many-to-many mapping |
| FR-12 | Spend vs budget per category | DONE | Optimised single-query calculation |
| FR-13 | Overall monthly spend vs total | DONE | Dashboard summary with budget group roll-ups |
| FR-16 | Alert when budget exceeded | PARTIAL | Code exists but scheduler crash (C2) prevents it firing |
| FR-19 | Dashboard: budget vs actuals | DONE | Summary cards, budget bars, category breakdown |
| FR-20 | Category breakdown with progress | DONE | Visual budget bars with gradient fills |
| FR-21 | Transaction list with search/filter | PARTIAL | Category filter only — no search, no date range, no pagination |

### Should Have Features

| FR | Feature | Status | Notes |
|----|---------|--------|-------|
| FR-03 | Handle refunds correctly | MISSING | No correlation logic; refunds appear as separate income (L15) |
| FR-07 | Learn from overrides (ML data) | PARTIAL | Data stored (`monzo_category` + `custom_category` + `raw_payload`) but no export/pipeline |
| FR-08 | Identify recurring transactions | DONE | Statistical interval analysis with confidence scoring |
| FR-15 | Alert at 80% budget | PARTIAL | Code exists but scheduler crash (C2) prevents it firing |
| FR-17 | Daily/weekly spending summary | PARTIAL | `notify_daily_summary()` exists but never called (M8) |
| FR-18 | Configurable notification prefs | MISSING | No preference storage or UI |
| FR-22 | Monthly trend charts | DONE | Recharts AreaChart, 7-90 day range, daily breakdown |
| FR-23 | Subscription summary | DONE | Recurring detection + subscriptions page |

### Could Have Features

| FR | Feature | Status | Notes |
|----|---------|--------|-------|
| FR-14 | Budget rollover | MISSING | No rollover flag or carry-forward logic |
| FR-24 | AI cost reduction recommendations | MISSING | Future scope |

### TRD Sync Flow (Section 5.1)

| Step | Description | Status |
|------|-------------|--------|
| 1 | Check token, refresh if expired | PARTIAL — checks but never refreshes (C1) |
| 2 | Fetch transactions (paginated) | PARTIAL — no pagination (C3) |
| 3 | Fetch balances | PARTIAL — pots synced, account balance API not used (M3) |
| 4 | Apply rules engine | MISSING — rules engine never called during sync (H7) |
| 5 | Store (upsert) | DONE |
| 6 | Analyse (budget usage) | MISSING — no budget recalculation during sync |
| 7 | Notify (digest/alerts) | PARTIAL — sync complete notified, digest/alerts broken (C2, M8) |
| 8 | Log sync result | DONE |

### TRD Rules Engine Conditions (Section 6.3)

| Condition | TRD Spec | Implemented |
|-----------|----------|-------------|
| `merchant_contains` | Required | Yes (`merchant_pattern`) |
| `merchant_exact` | Required | No |
| `amount_gt` | Required | Yes (`amount_min`) |
| `amount_lt` | Required | Yes (`amount_max`) |
| `amount_between` | Required | Partial (use min+max together) |
| `day_of_week` | Required | No |
| `category_is` | Required | Yes (`monzo_category`) |

### TRD Slack Notifications (Section 7.2)

| Message Type | Implemented | Actually Fires |
|--------------|-------------|----------------|
| Daily Digest | Yes (`slack.py`) | No — never called from scheduler (M8) |
| Threshold Alert (80%/100%) | Yes (`slack.py`) | No — scheduler crash (C2) |
| System Health (auth expired) | No | — (M11) |

---

## CRITICAL (Blocks Daily Usage)

### C1. Token Refresh Never Called
**Location:** `backend/app/services/sync.py:82-83`
**Origin:** Jan 18 review, re-assessed Feb 6

Monzo access tokens expire frequently. When they do, sync raises `SyncError("Token expired")` instead of calling the existing `refresh_access_token()` in `monzo.py:42-66`. Sync breaks silently every time your token expires and you need to re-authenticate manually.

**Fix:** Call `refresh_access_token()` before raising error when token is expired.

---

### C2. Scheduler Budget Alerts Missing Account Filter
**Location:** `backend/app/services/scheduler.py:162`
**Origin:** Feb 6 review

`get_all_budget_statuses()` is called without `account_id`, but the method requires it. This raises `TypeError` at runtime, crashing the scheduled budget alert job. Slack budget alerts never fire.

**Fix:** Iterate over all accounts and check budgets per account.

---

### C3. No Pagination in Transaction Sync
**Location:** `backend/app/services/monzo.py:122-154`, `backend/app/services/sync.py:154-157`
**Origin:** Feb 6 review

`fetch_transactions` defaults to `limit=100`. If you have more than 100 transactions since last sync (holiday, sync downtime), extras are silently dropped. Budgets and trends show wrong numbers.

**Fix:** Implement pagination loop using Monzo's `since`/`before` parameters.

---

## HIGH (Degrades Daily Usage)

### H1. Missing Error Boundaries in Frontend
**Location:** Entire frontend — no `ErrorBoundary` components exist
**Origin:** Feb 6 review

If any component throws during render (bad API data, null reference in chart), the entire app crashes to a white screen. Requires manual refresh.

**Fix:** Add error boundary at App level wrapping `<Outlet />`.

---

### H3. CORS Only Configured for localhost
**Location:** `backend/app/main.py:55-60`
**Origin:** Feb 6 review

CORS origins only include `localhost` variants. Accessing from another device on LAN via Mac Mini's IP will block all API requests.

**Fix:** Add Mac Mini's hostname/LAN IP to CORS origins, or use wildcard for local network.

---

### H6. Monzo API Calls Have No Timeout
**Location:** `backend/app/services/monzo.py` — all `httpx.AsyncClient()` calls
**Origin:** Feb 6 review

If Monzo's API is slow or unresponsive, requests hang indefinitely, blocking the scheduler. No more syncs until process restart.

**Fix:** Add `timeout=httpx.Timeout(10.0)` to all clients.

---

### H7. Rules Engine Not Wired to Sync
**Location:** `backend/app/services/rules.py` (engine), `backend/app/services/sync.py` (sync flow)
**Origin:** Feb 6 PRD/TRD assessment
**PRD:** FR-05 (Must Have), TRD Sync Step 4

The rules engine (`categorise_transaction()` in `rules.py`) is fully implemented with pattern matching and priority ordering, but is **never called during the sync flow**. New transactions are stored with their Monzo category only. The entire categorisation subsystem — including rules created via the UI — has no effect.

This means:
- Custom rules created in the Rules page do nothing
- The TRD-specified categorisation priority (user override → custom rules → Monzo category) is not enforced
- `custom_category` is only ever set by manual override (FR-06), never automatically

**Fix:** Call `categorise_transaction()` on each new transaction during sync step 4, before upsert.

---

## MEDIUM (Quality of Life)

### M1. Migration 002 Missing Data Backfill
**Location:** `backend/alembic/versions/002_add_account_id_to_budgets_rules.py:19-51`
**Origin:** Jan 20 review

Existing budgets/rules from before multi-account have `NULL` account_id. They won't show up when filtering by account.

**Fix:** Add `UPDATE` statements to assign existing records to default account, then make columns non-nullable.

---

### M2. Transaction Pagination Missing in Frontend
**Location:** `frontend/src/pages/transactions.tsx:54-57`
**Origin:** Feb 6 review

Hardcoded `limit: 50` with no way to load more. Can't browse older transactions.

**Fix:** Add infinite scroll or "Load more" button.

---

### M3. Dashboard Balance from Local Transactions
**Location:** `backend/app/api/dashboard.py:123-128`
**Origin:** Feb 6 review

Balance is calculated by summing local transactions instead of using Monzo's `/balance` endpoint. If sync missed transactions (see C3), balance will be wrong.

**Fix:** Call Monzo's `/balance` endpoint for the real number.

---

### M4. Settings Page Only Persists to localStorage
**Location:** `frontend/src/pages/settings.tsx:66-82`
**Origin:** Feb 6 review

Settings like sync interval are saved in localStorage but never sent to the backend. They have no actual effect on backend behavior.

**Fix:** Wire settings to the backend, or remove settings that can't be persisted.

---

### M5. Hardcoded "Last Sync" in Sidebar
**Location:** `frontend/src/components/layout/sidebar.tsx:70-72`
**Origin:** Feb 6 review

Shows "2 hours ago" regardless of actual sync status. You can't tell if sync is working.

**Fix:** Query actual sync status from the API.

---

### M6. Transaction `raw_payload` JSON Mutation
**Location:** `backend/app/api/transactions.py:130-133`
**Origin:** Feb 6 review

In-place mutation of JSON field may not trigger SQLAlchemy's change detection. Category overrides could silently fail to persist.

**Fix:** Use `flag_modified(tx, 'raw_payload')` or reassign the dict.

---

### M7. Budget `start_day` Not Validated (1-28)
**Location:** `backend/app/api/budgets.py` — create/update endpoints
**Origin:** Feb 6 review

Direct API calls allow `start_day=31`, which will crash when calculating periods for February. CSV import already clamps this — the API endpoints don't.

**Fix:** Add the same 1-28 validation to the API create/update endpoints.

---

### M8. Daily Digest Never Called from Scheduler
**Location:** `backend/app/services/slack.py` (method), `backend/app/services/scheduler.py` (scheduler)
**Origin:** Feb 6 PRD/TRD assessment
**PRD:** FR-17 (Should Have), TRD Section 7.2

`notify_daily_summary()` is fully implemented in `slack.py` with formatting for total spend, transaction count, and top categories. However, it is never invoked from the scheduler or any other code path. The daily spending summary Slack message never fires.

**Fix:** Add a scheduled job in `scheduler.py` that calls `notify_daily_summary()` at end of day.

---

### M9. Transaction Search Missing in Frontend
**Location:** `frontend/src/pages/transactions.tsx`
**Origin:** Feb 6 PRD/TRD assessment
**PRD:** FR-21 (Must Have)

No search input for finding transactions by merchant name or amount. The backend API supports filtering but the frontend only offers category pills. Users can't search for "Tesco" or find a specific transaction.

**Fix:** Add a search input with debounced query to the transactions page.

---

### M10. No Transaction Date Range Filter
**Location:** `frontend/src/pages/transactions.tsx`
**Origin:** Feb 6 PRD/TRD assessment
**PRD:** FR-21 (Must Have)

Only category filter is implemented. The backend supports `since` and `until` parameters but the frontend doesn't expose date range selection. Users can't view transactions for a specific week or month.

**Fix:** Add date range picker (or month selector) to the transactions page filter bar.

---

### M11. System Health Slack Notification Missing
**Location:** `backend/app/services/slack.py`
**Origin:** Feb 6 PRD/TRD assessment
**TRD:** Section 7.2

The TRD specifies three Slack message types: daily digest, threshold alert, and system health (auth expired alert with re-auth link). The system health notification is not implemented. When auth expires, the user has no way to know unless they check the dashboard.

**Fix:** Add `notify_auth_expired()` to `slack.py` and call it from sync error handling when token refresh fails.

---

## LOW (Polish)

### L1. Sync Race Condition (TOCTOU)
**Location:** `backend/app/services/sync.py:25-64`

SELECT-then-INSERT pattern could cause duplicate inserts if manual sync overlaps with scheduled sync.

**Fix:** Use `INSERT ... ON CONFLICT DO UPDATE`.

---

### L2. Inconsistent Sinking Fund Calculations
**Location:** `backend/app/services/budget.py:483-486` vs `backend/app/services/pot.py:250-253`

Two different methods for calculating `months_elapsed`. Could cause subtle discrepancies.

---

### L3. No Frontend 404 Route
**Location:** `frontend/src/App.tsx`

Unknown URLs show a blank page.

---

### L4. CSV Import Not Transactional
**Location:** `backend/app/api/budgets.py:260-311`

Partial imports leave orphaned records if it fails mid-way.

---

### L5. Recurring Detection Arbitrary Threshold
**Location:** `backend/app/services/recurring.py:125`

`avg_interval < 5` days threshold may miss or misclassify some subscriptions.

---

### L6. Composite Database Index Missing
**Location:** `backend/alembic/versions/001_initial_tables.py:46-48`

Separate indexes instead of composite. Won't matter at single-user data volume.

---

### L7. Rules Update Can't Clear Conditions
**Location:** `backend/app/services/rules.py:234-243`

Passing `None` means "don't update", not "clear". Workaround: delete and recreate.

---

### L8. Pydantic Schemas Inline
**Location:** Multiple API files

Schemas scattered across API files instead of centralized in `schemas/`.

---

### L9. Inefficient Spend Calculation
**Location:** `backend/app/services/budget.py:282-296`
**Origin:** Jan 18 review (#2)

`calculate_spend()` fetches all transactions into memory and sums in Python. Should use SQL `func.sum()`.

---

### L10. Unnecessary Date String Manipulation
**Location:** `backend/app/services/sync.py:55,57`
**Origin:** Jan 18 review (#9)

`.replace("Z", "+00:00")` still present. Python 3.12+ handles `Z` suffix natively in `fromisoformat()`.

---

### L11. Missing Content-Security-Policy Header
**Location:** `frontend/nginx.conf:16`
**Origin:** Jan 18 review (#5)

Has `X-XSS-Protection` (deprecated) but no CSP header.

---

### L12. Frontend Duplicates Budget Period Logic
**Location:** `frontend/src/pages/dashboard.tsx:59-65`
**Origin:** Jan 18 review (#6)

Frontend calculates `daysUntilReset` assuming calendar month, but backend uses configurable `reset_day`. Should use `period_start`/`period_end` from API response.

---

### L13. No Container Resource Limits
**Location:** `docker-compose.yml`
**Origin:** Jan 18 review (#8)

No `deploy.resources` sections. Containers can consume unlimited resources.

---

### L14. Missing Rules Engine Conditions
**Location:** `backend/app/services/rules.py`
**Origin:** Feb 6 PRD/TRD assessment
**TRD:** Section 6.3

Rules engine implements 4 of 7 TRD-specified condition types. Missing: `merchant_exact`, `amount_between` (as single condition), `day_of_week`. These limit rule expressiveness but aren't blocking since `merchant_contains` and `amount_min`+`amount_max` cover most cases.

---

### L15. No Refund Correlation Logic
**Location:** N/A — not implemented
**Origin:** Feb 6 PRD/TRD assessment
**PRD:** FR-03 (Should Have)

Refunds appear as separate positive-amount transactions. No logic to correlate them with original purchases by merchant + amount + timing. This can skew spending totals (a purchase + refund should net to zero in a category). Categorised as LOW because refunds are infrequent and the user can manually spot them.

---

### L16. No Historical Comparison on Dashboard
**Location:** `frontend/src/pages/dashboard.tsx`
**Origin:** Feb 6 PRD/TRD assessment
**PRD:** FR-06 (User Story US-09)

Dashboard shows current month spending but no "vs last month" comparison. The 30-day trend chart provides some context but there's no explicit month-over-month delta shown in summary cards (e.g., "Groceries: £450 — 12% more than last month").

---

## DEFERRED (Only If Scope Changes to Multi-User / Cloud)

| ID | Issue | Why Deferred |
|----|-------|--------------|
| D1 | No authentication middleware | Single user on LAN |
| D2 | IDOR in update/delete endpoints | All data is yours |
| D3 | OAuth state not validated | CSRF irrelevant — authenticating yourself |
| D4 | No input validation on frontend | You're the only one entering data |
| D5 | No CSV upload size limits | You control what you upload |
| D6 | No network isolation in Docker | All containers are yours |
| D7 | Backend port exposed in Docker | Useful for debugging, no external threat |
| D8 | Accessibility gaps | Personal tool |

---

## DONE (Verified Fixed)

### ~~H2. Database Engine Created Per Request~~ ✅
**Location:** `backend/app/database.py:33-46`
**Fixed:** Engine is now a module-level singleton via `get_engine()`.

### ~~H4. Frontend Race Conditions on Account Switch~~ ✅
**Location:** `frontend/src/contexts/AccountContext.tsx:66-72`
**Fixed:** Properly invalidates all account-scoped queries on switch.

### ~~H5. Mutation Hooks Don't Scope to Account ID~~ ✅
**Location:** `frontend/src/hooks/useApi.ts`
**Fixed:** Query keys now include `accountId` for proper cache isolation.

### ~~N+1 Query in Budget Status~~ ✅
**Origin:** Jan 18 review (#1)
**Fixed:** `get_all_budget_statuses()` now fetches all transactions in a single query.

### ~~Silent Slack Failures~~ ✅
**Origin:** Jan 18 review (#3)
**Fixed:** `logger.error()` with `exc_info=True` and specific `httpx.RequestError` catch.

### ~~Database Ports Exposed~~ ✅
**Origin:** Jan 18 review (#4)
**Fixed:** PostgreSQL and Redis ports removed from `docker-compose.yml`.

### ~~Unconventional App Initialization~~ ✅
**Origin:** Jan 18 review (#7)
**Fixed:** Clean initialization, no try/except wrapping.

---

## Test Coverage

### What's Tested (10 test files)

| File | Coverage | Quality |
|------|----------|---------|
| `test_auth.py` | OAuth flow, token storage | Good |
| `test_budget.py` | Period calculation, create/update | Good |
| `test_config.py` | Settings loading | Basic |
| `test_main.py` | App creation, health check | Basic |
| `test_models.py` | Model instantiation | Basic |
| `test_pot.py` | Pot operations | Moderate |
| `test_rules.py` | Rule CRUD, matching | Good |
| `test_scheduler.py` | Scheduler lifecycle | Basic |
| `test_slack.py` | Notification sending | Good |
| `test_sync.py` | Transaction sync | Moderate |

### Worth Adding

| Missing Test | Why | Location |
|-------------|-----|----------|
| Sinking fund calculations | Complex math, wrong numbers on budget page | `services/budget.py:443-529` |
| Budget group roll-ups | Totals could be wrong silently | `services/budget_group.py` |
| Token refresh flow | Core to keeping sync alive | `services/monzo.py:42-66` |
| Transaction sync pagination | Ensures you don't miss data | `services/sync.py` |
| Rules applied during sync | Verify categorisation actually runs | `services/sync.py` + `services/rules.py` |

---

## Priority Recommendations

### Fix First (Sync Reliability)
1. **C1 — Token refresh** — sync breaks every time tokens expire
2. **C3 — Sync pagination** — silently miss transactions
3. **H6 — API timeouts** — slow Monzo API kills scheduler
4. **C2 — Scheduler account_id** — runtime TypeError crashes alert job
5. **H7 — Wire rules to sync** — auto-categorisation has no effect (Must Have FR-05)

### Fix Next (Data Accuracy + Notifications)
6. **M3 — Balance from Monzo API** — show real balance
7. **M8 — Daily digest** — wire the existing function to the scheduler
8. **M11 — Auth expired notification** — know when re-auth is needed
9. **M5 — Sidebar last sync** — know when sync is working
10. **M6 — JSON mutation** — category overrides may not persist

### Fix When Motivated (UX Polish)
11. **H1 — Error boundaries** — prevent white screen crashes
12. **H3 — CORS for LAN** — access from other devices
13. **M9 — Transaction search** — find transactions by merchant/amount
14. **M10 — Date range filter** — view transactions for a specific period
15. **M2 — Transaction pagination** — browse older transactions
16. **M4 — Settings wiring** — stop the confusion
17. **M1 — Migration backfill** — one-time fix for pre-migration data
