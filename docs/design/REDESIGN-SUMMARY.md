# Redesign Summary — YNAB-Inspired UI

**Date:** 2026-03-22  
**Status:** Complete, type-checked, ready for testing

---

## What Changed

### Dashboard (`pages/dashboard.tsx`) — Complete Rewrite
- **Before:** Card-soup layout with tab switcher (Budget/Analytics), BudgetGroupCards in a grid, separate SinkingFundCards, StatBlocks
- **After:** Two-panel master-detail layout. Left panel (60%) is a YNAB-style budget table. Right panel (40%) is a context panel showing either monthly overview or selected category detail
- Tab switcher removed — analytics now lives in the context panel overview mode

### Transactions (`pages/transactions.tsx`) — Major Update
- **Before:** Flat paginated list in a Card wrapper, category change via Dialog modal
- **After:** Date-grouped (TODAY / YESTERDAY / date headers) full-width table with inline category editing via dropdown on each row. No modals.

### Budgets (`pages/budgets.tsx`) — Simplified
- **Before:** Full budget CRUD page with Dialog modals for add/edit
- **After:** CSV import utility only, with clear messaging that budget management has moved to the Dashboard

---

## New Components

| Component | File | Purpose |
|-----------|------|---------|
| `InlineEdit` | `components/ui/inline-edit.tsx` | Reusable click-to-edit field (text & currency variants) |
| `BudgetTable` | `components/ui/budget-table.tsx` | Full YNAB-style budget table with collapsible groups |
| `BudgetGroupHeader` | `components/ui/budget-group-header.tsx` | Collapsible group header row with roll-up totals |
| `BudgetTableRow` | `components/ui/budget-table-row.tsx` | Individual budget line item with inline editing |
| `ContextPanel` | `components/ui/context-panel.tsx` | Right-side panel (overview mode + category detail mode) |
| `TopBarBudget` | `components/ui/top-bar-budget.tsx` | Month-aware topbar with "Ready to Assign" |
| `SpendSparkline` | `components/ui/spend-sparkline.tsx` | Mini Recharts sparkline for trends |
| `TransactionRowV2` | `components/ui/transaction-row-v2.tsx` | Transaction row with inline category dropdown |
| `CategoryDropdown` | `components/ui/category-dropdown.tsx` | Inline category selector popover |

---

## What Was NOT Changed

- `hooks/useApi.ts` — untouched
- `lib/api.ts` — untouched
- `lib/utils.ts` — untouched
- `App.tsx` — untouched
- `components/layout/*` — untouched (sidebar, layout, top-bar)
- `components/ui/button.tsx`, `card.tsx`, `dialog.tsx`, `input.tsx`, `label.tsx`, `select.tsx`, `alert-dialog.tsx` — untouched
- Backend — no changes whatsoever

---

## Key UX Decisions

1. **No more modal dialogs for editing** — budget amounts, category names, group names, and transaction categories all edit inline
2. **Budget table rows, not cards** — dense, scannable, colour-coded available amounts
3. **Context panel replaces analytics tab** — click a budget row to see its transactions without navigating away
4. **Date-grouped transactions** — TODAY, YESTERDAY, and full date headers with day totals
5. **"Ready to Assign" in topbar** — always visible, creates budget intentionality
6. **Sinking funds integrated into budget table** — no longer separate cards, they're a collapsible group section

---

## How to Test

```bash
cd ~/projects/monzo-analysis
docker compose up -d
```

Or for local dev:
```bash
cd frontend
npm install
npm run dev
# Open http://localhost:5173
```

### Test Checklist

- [ ] Dashboard loads with two-panel layout
- [ ] Budget groups are collapsible (click chevron or group header)
- [ ] Click a budget row → right panel shows category detail with transactions
- [ ] Click a budget amount → inline edit activates, save on Enter/blur
- [ ] Click a group name → inline edit activates
- [ ] Sinking funds appear as a collapsible section at the bottom of the budget table
- [ ] TopBar shows month navigation (< / >) and "Ready to Assign"
- [ ] Transactions page shows date group headers
- [ ] Click category pill on a transaction → dropdown for reassignment
- [ ] Budgets page shows CSV import utility with redirect messaging

---

## Follow-Up Items for Review

1. **Mobile responsiveness** — Two-panel layout needs breakpoint work below 1024px. Currently optimised for desktop. Consider bottom sheet for context panel on mobile.
2. **Add new budget inline** — The "+" button on group headers needs a flow to create a new budget row. Currently wired but needs backend create mutation integration.
3. **Keyboard navigation** — Tab through budget rows works but could be enhanced with arrow key support.
4. **Drag-and-drop reordering** — Future: allow reordering budget rows and groups by drag.
5. **"Ready to Assign" calculation** — Currently uses `totalBudgeted - totalSpent`. Could be refined to use actual income from transaction data.
6. **Optimistic updates** — Transaction category changes work but could benefit from optimistic UI updates for snappier feel.
