# Monzo Analysis — Next Phase Plan

**Date:** 2026-03-22  
**Context:** Monarch Money feature analysis + current repo state + YNAB redesign (in progress)  
**Prepared by:** Jeeves

---

## Current State

### What's Built (Complete)
- OAuth + Monzo API integration (polling, daily sync)
- Transaction storage + categorisation rules engine
- Budget groups hierarchy (Groups → Line items → Sinking funds)
- Budget vs actuals tracking
- Subscriptions/recurring detection
- Docker Compose deployment
- 124 passing tests

### What's In Progress (Design Swarm, ~90% complete)
- YNAB-inspired UI redesign (commits from 23:02–23:31 tonight)
  - Two-panel master-detail dashboard
  - Budget table (rows, not cards) with collapsible groups
  - Inline editing throughout
  - Date-grouped transactions with inline category editing
  - "Ready to Assign" topbar
  - New component library (12 new components)

### What's Missing vs Monarch Money Feature Set

Monarch Money is the aspirational bar. Gap analysis:

| Monarch Feature | Monzo Analysis | Gap |
|----------------|---------------|-----|
| Unified account view (all accounts) | Multi-account (Monzo only) | Bank aggregation — long-term |
| Bucket budgeting (Fixed/Flexible/Non-monthly) | Budget groups + period types | Minor — label and UX alignment needed |
| Cash flow insights (monthly/quarterly/yearly) | 30-day trend chart only | Significant |
| Subscription management + calendar view | Basic recurring detection page | Medium |
| Net worth tracking | Not present | Out of scope (Monzo-only) |
| AI-powered categorisation | Rules engine only | Medium-term |
| Goal tracking | Sinking funds only (partial) | Medium |
| Collaboration/household view | Joint account only | Low priority |
| Custom reports | No reporting | Significant |
| Rule creation prompt after recategorising | Planned in design doc | Soon |
| Transaction splitting | Not present | Medium |
| "Mark as reviewed" workflow | Not present (in design doc) | Soon |
| Month-over-month comparisons | Not present | Significant |
| Spending trend by category over time | Not present | Significant |

---

## Phase Plan

### Phase 0 — Design Redesign (IN PROGRESS, tonight)
**Goal:** Ship the YNAB-inspired UI

What's landing:
- Dashboard: two-panel layout, budget table, context panel
- Transactions: date-grouped, inline category editing
- Budgets page: simplified to CSV import
- 12 new components shipped

**ETA:** Done tonight. Test tomorrow.

---

### Phase 1 — Budget-First Workflow Hardening
**Priority:** High — core experience  
**Effort:** 1–2 weeks  
**Goal:** Make the budget table the centre of daily use

#### 1.1 Design Document Implementation (V2)
The design doc at `docs/design/DESIGN-DOCUMENT.md` goes significantly further than Phase 0. It specifies:

- **`MonthSummaryBar`** — replace the 4 stat blocks with a single dense horizontal bar (Spent | Budgeted | Available | Day X of Y progress track)
- **`CashFlowWidget`** — income vs spend with delta vs previous month (Monarch-inspired)
- **`EditableAmount`** — refined inline editing with Tab→next-cell keyboard nav
- **`InlineCategoryEdit`** — Radix Popover replacing the current CategoryDropdown
- **`DateGroupHeader`** — sticky on scroll, daily totals in right margin
- **`TransactionFilterBar`** — consolidated filter bar (month nav + search + category pills in one row)
- **Sidebar budget widget** — running available balance + days remaining, always visible
- **Sidebar badge** — unreviewed transaction count

Icon system: Replace all emoji with lucide-react SVG icons. `src/lib/category-icons.ts` is the single source of truth.

New Radix dependencies: `@radix-ui/react-popover` and `@radix-ui/react-dropdown-menu`

#### 1.2 "Mark as Reviewed" Workflow
Monarch's killer feature for daily use. Transactions arrive unreviewed (coral dot), you confirm they're correct, dot disappears. Gives closure.

- Backend: `reviewed` boolean on transactions table (migration needed)
- API: `PATCH /transactions/{id}/reviewed`
- Frontend: dot indicator per row, click to toggle, bulk "Mark all reviewed" button
- Sidebar badge shows unreviewed count

#### 1.3 Rule Creation Prompt
After recategorising a transaction inline, show a dismissible prompt:
> *"Always categorise Sainsbury's as Groceries? [Create rule] [Skip]"*

- Wire into the inline category edit flow
- "Create rule" fires `POST /rules` with merchant name pre-filled
- Monarch does this — dramatically reduces ongoing manual recategorisation

#### 1.4 Inline Budget Row Add/Delete
The design has a `QuickAddRow` component — needs the backend mutation wired:
- `+ Add category` at bottom of each group → inline row → Enter to save → `POST /budgets`
- Row-level delete (hover → bin icon) → `DELETE /budgets/{id}` with confirmation toast (not Dialog)
- Group add: `+ Add group` at bottom of full table → `POST /budget-groups`

---

### Phase 2 — Cash Flow & Time Analysis
**Priority:** High — core differentiator from current state  
**Effort:** 2–3 weeks  
**Goal:** "Budget over time" — not just this month, but trends

This is the key ask from Nick's original message: *"tracking of budgets over time."*

#### 2.1 Month-over-Month Budget vs Actuals
New API endpoint: `GET /api/v1/budgets/history?account_id=X&months=6`

Returns per-category spend for each of the last N months. Enables:
- Sparklines per category (6-month mini chart in context panel — already in V1 design)
- "This month vs last month" delta on each budget row
- Running average ("you typically spend £285 on groceries")

Backend: group transactions by budget period + category, aggregate per period.

#### 2.2 Cash Flow Report Page
New page: `/cashflow`

Monarch-style monthly income vs expenditure view:
- Bar chart: income bar vs spend bar per month, last 12 months
- Group breakdown: how much went to Fixed vs Flexible vs Sinking Funds per month
- Net savings per month (income - spend)
- Category drill-down: click a bar to see category breakdown for that month

Uses existing transactions data, just needs new aggregation queries.

#### 2.3 Budget Period Rollover Tracking
Track whether budget periods are under/over at reset:
- Store `budget_period_snapshots` table: period end date, category, budgeted, spent, over/under
- Surfaced in: history sparkline, "last month you were X% over on groceries" context

#### 2.4 Spending Trend Chart Overhaul
Current: 30-day AreaChart on dashboard (basic, anonymous)

Replace with:
- Category-coloured stacked area chart (each category a different colour)
- Time range selector: 1M / 3M / 6M / 1Y
- Toggle: Total vs Per Category vs vs Budget baseline

---

### Phase 3 — Intelligent Categorisation
**Priority:** Medium  
**Effort:** 2 weeks  
**Goal:** Reduce manual recategorisation to near-zero

#### 3.1 ML-Ready Rules Engine Enhancement
Current rules engine: conditions-based (merchant contains X → category Y).

Enhance:
- **Learning from overrides:** Every manual category change is stored as training data (raw_payload + override). Already designed for in TRD.
- **Merchant fingerprinting:** Group transactions by merchant MCC code + name similarity → suggest shared rules
- **Confidence score:** When auto-categorising, attach a confidence score. Low confidence → flag for review

#### 3.2 Subscription Intelligence
Current subscriptions page: basic recurring detection.

Monarch-style enhancements:
- Calendar view: visual timeline of when subscriptions hit (good for cashflow planning)
- Missed payment detection: expected subscription didn't appear → alert
- Price change detection: subscription increased by £2 → notify
- Total monthly cost of subscriptions in a dedicated widget

#### 3.3 Merchant-Level Budget Mapping
Currently budgets map to Monzo categories (groceries, eating_out, etc.). The design doc mentioned Amazon/Target-style item-level categorisation is out of scope.

But we can improve within Monzo's data:
- Merchant-level spending summaries (Top 10 merchants this month by spend)
- Merchant search in transaction filter
- Per-merchant spend over time (click a merchant → see all their transactions + trend)

---

### Phase 4 — Goals & Sinking Funds Overhaul
**Priority:** Medium  
**Effort:** 1–2 weeks  
**Goal:** Make sinking funds feel like Monarch's goal tracking

#### 4.1 Goal Tracking Widget
Current sinking funds: linked to Monzo Pots, show monthly contribution progress.

Monarch-inspired enhancements:
- Named goals with target amount + target date (not just annual budget)
- Progress bar: £450 saved of £3,000 goal (15%)
- Monthly contribution required to hit target by date
- "You're on track" / "You need £X more per month" status
- Visual: mini timeline showing projected goal completion date

#### 4.2 Pot Sync Integration
Currently pots are synced but balance tracking could be stronger:
- Auto-detect pot top-ups and link to goal contributions
- Show pot balance history (Monzo API → store snapshots on each sync)
- Alert when pot balance drops (withdrawal happened)

#### 4.3 Non-Monthly Expense Planning (Monarch "Non-Monthly" Bucket)
Monarch has a specific "non-monthly" category bucket — quarterly bills, annual costs. Our sinking funds cover this but UX isn't there.

New sub-view in budget table: "Non-Monthly" group with:
- Next due date prominently displayed
- Months until due → implied monthly save rate
- Pot balance as progress tracker

---

### Phase 5 — Reporting & Export
**Priority:** Lower  
**Effort:** 1 week  
**Goal:** "Show me the numbers" without going to the dashboard

#### 5.1 Custom Date Range Reports
- Filter any view by custom date range (not just calendar months)
- "July - September 2025" → shows budget performance for that period
- Useful for: annual reviews, quarterly spending analysis

#### 5.2 Export
- CSV export of transactions with full metadata
- PDF spending report (monthly snapshot)
- Useful for: tax preparation, shared household review

#### 5.3 Insights Widget
Monarch's AI assistant is table stakes eventually. Short-term, rule-based insights are achievable:
- "You've spent £124 more on groceries this month vs your 3-month average"
- "3 subscriptions haven't been charged this month — check if cancelled"
- "Your spending pace suggests you'll overspend on Eating Out by £47 this month"

All derivable from existing data, no ML needed.

---

## Recommended Next Phase Sequence

Given the redesign landing tonight:

1. **Immediately** (this week): Test the Phase 0 redesign. Deploy to Mac Mini. Get it actually running with live Monzo data.

2. **Phase 1** (next 1-2 weeks): Design doc V2 implementation + Mark as Reviewed + Rule creation prompt + Inline add/delete. This makes the app genuinely pleasant for daily use.

3. **Phase 2** (2-4 weeks): Cash flow and time analysis. This is the core gap vs Monarch and the thing Nick asked for originally — budget tracking over time, not just this month.

4. **Phase 3** (4-6 weeks): Smarter categorisation. Subscription intelligence first (high value, contained scope), then ML prep.

5. **Phases 4-5** (6-10 weeks): Goals + reporting. Lower urgency, higher polish.

---

## What Needs a Backend Change vs Frontend Only

| Feature | Backend? | Migration? |
|---------|---------|-----------|
| Design doc V2 components | No | No |
| Mark as reviewed | Yes | Yes (`reviewed` column) |
| Rule creation prompt | No (uses existing POST /rules) | No |
| Inline budget add/delete | No (uses existing endpoints) | No |
| Month-over-month history API | Yes | Yes (budget_period_snapshots) |
| Cash flow report page | Yes (new endpoint) | No (uses existing data) |
| Rollover tracking | Yes | Yes (new table) |
| Subscription calendar | No | No |
| Price change detection | Yes (background job) | No |
| Goal tracking widget | Yes | Yes (goals table or extend budgets) |
| Custom date range reports | No (filter param) | No |
| CSV export | Yes (new endpoint) | No |
| Insights widget | No (frontend compute) | No |

---

## Open Questions for Nick

1. **Phase 1 vs Phase 2 priority:** Do you want the UI polished first (Phase 1 Design Doc V2) or get month-over-month data working (Phase 2) while the Phase 0 UI beds in?

2. **"Mark as reviewed":** Is this workflow something you'd actually use daily, or is it noise? Drives a backend migration.

3. **Webhook vs polling:** The CLAUDE.md notes polling is current design. Webhooks would enable real-time updates. Worth switching now while we're rebuilding the frontend, or keep polling?

4. **Deployment:** Is the app actually running on the Mac Mini? If so, what port/URL are you hitting? The Docker Compose is configured but "Local Deployment" was the last milestone in Jan.
