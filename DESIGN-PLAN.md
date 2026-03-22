# DESIGN PLAN: Monzo Analysis UI Overhaul

> **Inspired by YNAB. Built for density, inline editing, and actual usability.**
>
> Generated: 2026-03-22 | Status: Ready for dev-lead

---

## Table of Contents

1. [Current State Critique](#1-current-state-critique)
2. [Icon System](#2-icon-system)
3. [Global Design Changes](#3-global-design-changes)
4. [Dashboard Redesign](#4-dashboard-redesign)
5. [Budget Page Redesign (YNAB-Inspired)](#5-budget-page-redesign-ynab-inspired)
6. [Transaction Page Redesign](#6-transaction-page-redesign)
7. [Sidebar Changes](#7-sidebar-changes)
8. [Inline Editing Technical Spec](#8-inline-editing-technical-spec)
9. [New/Modified Components](#9-newmodified-components)
10. [Implementation Order](#10-implementation-order)

---

## 1. Current State Critique

### Dashboard

**Problems:**

1. **Tab split kills context.** Budget Tab and Analytics Tab fragment a single story into two views. You see your budget groups OR your spending trend — never together. YNAB shows everything on one scrollable page because the data is related. Splitting it is information architecture malpractice.

2. **Card grid = visual noise.** The `BudgetGroupCard` grid (1–3 columns) renders every budget group as its own gradient-border card with status badges, progress bars, expand/collapse, percentage badges, and "▼ View details" text. It's a wall of boxes. Every group screams for attention equally — nothing has hierarchy.

3. **The "Total Budget Summary" card is enormous.** A `border-2 border-coral/30` gradient card with a 4xl heading, a h-4 progress bar, and a sub-bar with "expected progress" text. It's a dashboard widget that takes up 200+ px of vertical space before you see any budget data.

4. **Emoji icons everywhere.** `categoryEmojis` map duplicated across `dashboard.tsx`, `budgets.tsx`, `category-pill.tsx`, and `budget-group-card.tsx`. Four copies of the same 🛒🍽️🛍️ mapping. Inconsistent, unmaintainable, and visually cheap.

5. **Sinking Funds section is another card grid** below the budget groups. More cards. More gradients. More visual weight competing for attention.

6. **Analytics Tab stat blocks are too wide.** 4-column grid with `text-4xl` values in each. On most screens this is spacious but on laptop-width viewports the grid breaks awkwardly.

7. **Top Categories section** renders emoji in `text-2xl` inside `bg-navy rounded-xl p-4` boxes. Five little cards in a row. More cards.

### Budgets Page

**Problems:**

1. **Three summary stat cards** at the top (`grid-cols-3 gap-4`) each with `rounded-2xl p-6 border`. That's 72px of padding just for three numbers. Should be a single row with inline values.

2. **Flat list, zero hierarchy.** All budgets are listed inside a single `<Card>` with `space-y-6` gap. No grouping by budget group. No visual hierarchy. You have a `BudgetGroupStatus` API that returns grouped data — it's not being used on this page.

3. **Each budget row is its own card.** `p-4 bg-navy rounded-xl` per row. With `BudgetBar` inside (which adds `mb-2` label + `h-3` bar), each budget consumes ~80px vertically. A 10-budget list is 800px+ of scrolling.

4. **Editing requires a modal dialog.** Click edit pencil → Dialog opens → change category via `<select>` with emoji in options → type amount → Save. Four interactions for what should be one click on a number.

5. **No inline feedback on budget health.** The status text (`"Over budget by £X"` / `"£X remaining"`) is tiny `text-xs` below the bar. Colour-as-data (YNAB's approach) would be faster to scan.

6. **Import CSV button** gets equal visual weight to "Add Budget". Import is a rare action; it should be secondary or hidden in a menu.

### Transactions Page

**Problems:**

1. **Rows are too tall.** `TransactionRow` uses `p-4` (16px all sides) + an `w-11 h-11` (44px) icon box + the row itself. Each row is ~60-70px. At 50 items per page, that's 3000-3500px of scrolling. Brutal.

2. **Category change requires a full dialog.** Click transaction → modal opens → grid of category buttons → click one → click Save. To change a category. This should be a popover that appears inline on the row.

3. **No date grouping.** Transactions are a flat, undifferentiated list. 50 items with no visual breaks. YNAB and every decent banking app groups by date with sticky date headers.

4. **Category filter pills are chunky.** `px-4 py-2 rounded-full text-sm font-semibold` — fine, but there are only 7 of them and they take up significant vertical space. Could be a compact horizontal bar.

5. **Search bar is full-width and oversized.** `px-4 py-2 rounded-xl` — it's the first thing you see, but search is secondary to browsing. Should be integrated into a compact filter bar.

6. **Month navigation** uses text arrows (`← Prev` / `Next →`) in button elements. Works but feels ad-hoc. Should be integrated into the top bar or a month selector.

7. **"Load more" button** instead of virtual scrolling or infinite scroll. Acceptable for now but the button could be more compact.

8. **The hover effect** `hover:translate-x-2` on each row is a novelty that adds visual instability to a data-dense list. Kill it.

---

## 2. Icon System

### Kill all emoji. Replace with lucide-react.

Create a single source of truth at `src/lib/category-icons.ts`. Delete `categoryEmojis` from `dashboard.tsx`, `budgets.tsx`, `category-pill.tsx`, and `budget-group-card.tsx`.

### Complete Category → Lucide Icon Mapping

```typescript
// src/lib/category-icons.ts
import {
  ShoppingCart,
  UtensilsCrossed,
  ShoppingBag,
  Car,
  Clapperboard,
  FileText,
  Package,
  Plane,
  Banknote,
  Briefcase,
  Wallet,
  PiggyBank,
  Home,
  Wifi,
  Heart,
  GraduationCap,
  Dumbbell,
  Gift,
  Baby,
  Wrench,
  Coffee,
  Beer,
  Smartphone,
  CreditCard,
  TrendingUp,
  HelpCircle,
  type LucideIcon,
} from "lucide-react";

export const categoryIcons: Record<string, LucideIcon> = {
  groceries: ShoppingCart,
  eating_out: UtensilsCrossed,
  shopping: ShoppingBag,
  transport: Car,
  entertainment: Clapperboard,
  bills: FileText,
  general: Package,
  holidays: Plane,
  cash: Banknote,
  expenses: Briefcase,
  savings: PiggyBank,
  rent: Home,
  mortgage: Home,
  utilities: Wifi,
  health: Heart,
  education: GraduationCap,
  fitness: Dumbbell,
  gifts: Gift,
  childcare: Baby,
  maintenance: Wrench,
  coffee: Coffee,
  drinks: Beer,
  phone: Smartphone,
  subscriptions: CreditCard,
  investments: TrendingUp,
};

/**
 * Returns the appropriate lucide icon for a category.
 * Falls back to Package for unknown categories.
 */
export function getCategoryIcon(category: string): LucideIcon {
  const normalised = category.toLowerCase().replace(/\s+/g, "_");
  return categoryIcons[normalised] || HelpCircle;
}

/**
 * Standard icon styling for category icons throughout the app.
 *
 * Usage:
 *   const Icon = getCategoryIcon("groceries");
 *   <Icon {...categoryIconProps} />
 *   <Icon {...categoryIconProps} className="text-mint" /> // override colour
 */
export const categoryIconProps = {
  size: 16,
  strokeWidth: 1.5,
  className: "text-stone",
} as const;

/**
 * Larger icon variant for dashboard/summary contexts.
 */
export const categoryIconPropsLg = {
  size: 20,
  strokeWidth: 1.5,
  className: "text-stone",
} as const;
```

### Budget Group Icons

Budget groups currently use `group.icon` which falls back to "📂". Replace with lucide:

```typescript
// Add to category-icons.ts
import { Folder, Sparkles, TrendingDown, Landmark, Umbrella } from "lucide-react";

export const groupIcons: Record<string, LucideIcon> = {
  essential: Home,
  lifestyle: Sparkles,
  savings: PiggyBank,
  debt: TrendingDown,
  fixed: Landmark,
  emergency: Umbrella,
  default: Folder,
};

export function getGroupIcon(iconName?: string): LucideIcon {
  if (!iconName) return Folder;
  return groupIcons[iconName.toLowerCase()] || Folder;
}
```

### Icon Styling Standard

| Context | Size | strokeWidth | Colour | Container |
|---------|------|-------------|--------|-----------|
| Table row (budget/transaction) | 16px | 1.5 | `text-stone` | None — inline before text |
| Group header | 18px | 1.5 | `text-white` | None |
| Dashboard summary | 20px | 1.5 | Category colour | `w-8 h-8 rounded-lg bg-{cat}/10 flex items-center justify-center` |
| Category pill | 14px | 1.5 | Inherit from pill text colour | None — inline |
| Sidebar nav | 20px | 1.75 | Inherited (already correct) | None |

### Files to Modify

- **DELETE** `categoryEmojis` from: `dashboard.tsx`, `budgets.tsx`, `category-pill.tsx`
- **MODIFY** `category-pill.tsx`: import `getCategoryIcon, categoryIconProps` instead of emoji map
- **MODIFY** `budget-group-card.tsx` (or its replacement): use `getGroupIcon` instead of `group.icon || "📂"`
- **MODIFY** `transaction-row.tsx`: replace emoji with icon component
- **MODIFY** `budget-bar.tsx`: replace `emoji` prop with icon component

---

## 3. Global Design Changes

### Row/List Item Padding Reduction

| Component | Current | Target | Savings |
|-----------|---------|--------|---------|
| TransactionRow | `p-4` (16px all sides) | `py-2 px-3` (8px/12px) | ~50% height reduction |
| TransactionRow icon | `w-11 h-11` (44px) | `w-7 h-7` (28px) | 16px per row |
| BudgetRow (new) | `p-4` (16px) + `rounded-xl` | `py-1.5 px-3` (6px/12px) | ~75% reduction |
| BudgetBar label | `mb-2` (8px) | `mb-0` (inline) | 8px |
| BudgetBar height | `h-3` (12px) | `h-1.5` (6px) or remove entirely | 6px |
| Budget group gap | `space-y-6` (24px) | `space-y-0` (table rows, no gap) | 24px per item |
| Dashboard section gap | `space-y-6` (24px) | `space-y-4` (16px) | 8px per section |
| Card internal padding | `p-6` (24px) | `p-4` (16px) for data cards, `p-0` for table containers | Variable |
| Stat blocks | `p-6` (24px) | `py-3 px-4` (12px/16px) | ~50% |

### Typography Scale Adjustments

| Element | Current | Target |
|---------|---------|--------|
| Stat values | `text-4xl` (36px) | `text-2xl` (24px) |
| Budget group name | `text-lg` (18px) `font-semibold` | `text-sm` (14px) `font-medium` |
| Budget row category | `font-semibold text-white` | `text-sm font-normal text-white` |
| Money amounts in tables | varies | `text-sm font-mono` consistently |
| Section headings | `text-2xl` display font | `text-xs uppercase tracking-wider text-stone` (label style) |
| Transaction merchant | `font-semibold text-white` | `text-sm font-medium text-white` |
| Transaction meta | `text-sm text-slate` | `text-xs text-stone` |

### Card Usage Rules

**Use cards for:**
- Self-contained widgets with their own context (spending chart, monthly summary)
- Content that has a clear boundary (sidebar sections)

**Do NOT use cards for:**
- Individual list items / rows (budgets, transactions)
- Budget groups — use table group headers instead
- Stat blocks — use inline horizontal layout
- Wrapping a table — the table IS the content area, with its own bg

**Replace cards with:**
- `border-b border-navy-mid` dividers between rows
- Table structure for tabular data (budgets)
- Direct background: `bg-charcoal rounded-xl` on the containing section, not per-item

### Separator/Divider Pattern

```tsx
// Standard divider between list items
<div className="border-b border-navy-mid/50" />

// Group separator (thicker, more contrast)
<div className="border-b-2 border-navy-mid" />

// Section break within a page
<div className="h-px bg-navy-mid my-4" />
```

---

## 4. Dashboard Redesign

### Kill the Tabs

Remove `Budget Tab` / `Analytics Tab` entirely. The dashboard becomes a single scrollable view with these sections top-to-bottom:

### New Dashboard Layout

```
┌─────────────────────────────────────────────┐
│  MARCH 2026 ─ Day 22 of 31 ─ 9 days left  │  ← TopBar (existing)
├─────────────────────────────────────────────┤
│  £1,847 spent  │  £653 left  │  £2,500 total  │  ← Monthly Summary Bar
│  ▓▓▓▓▓▓▓▓▓▓▓▓░░░░░  73.9%                  │  ← Thin progress bar (h-1.5)
├─────────────────────────────────────────────┤
│  BUDGET OVERVIEW                             │
│  ┌ Essential ──────────────────────────────┐ │
│  │  Groceries      £180  -£245  ▊ -£65    │ │  ← Compact table rows
│  │  Bills          £350  -£320  ▊  £30    │ │
│  │  Transport      £100  -£78   ▊  £22    │ │
│  │  Group total    £630  -£643  ▊ -£13    │ │
│  ├ Lifestyle ──────────────────────────────┤ │
│  │  Eating out     £200  -£156  ▊  £44    │ │
│  │  ...                                    │ │
│  └─────────────────────────────────────────┘ │
├─────────────────────────────────────────────┤
│  SPENDING TREND (30 DAYS)                    │
│  [area chart — same as current but inline]   │
├─────────────────────────────────────────────┤
│  RECENT TRANSACTIONS                         │
│  Today ─────────────────────────────────────│
│  Tesco Express    groceries       -£23.40   │
│  TfL              transport        -£4.50   │
│  Yesterday ─────────────────────────────────│
│  Nando's          eating_out      -£18.90   │
└─────────────────────────────────────────────┘
```

### Monthly Summary Bar

Replaces the enormous "Total Budget Summary Card". One horizontal bar:

```tsx
// Component: MonthSummaryBar
<div className="flex items-baseline gap-6 py-3">
  <div>
    <span className="text-xs text-stone uppercase tracking-wider">Spent</span>
    <span className="text-xl font-mono text-white ml-2">£1,847</span>
  </div>
  <div>
    <span className="text-xs text-stone uppercase tracking-wider">Left</span>
    <span className="text-xl font-mono text-mint ml-2">£653</span>
  </div>
  <div>
    <span className="text-xs text-stone uppercase tracking-wider">Budget</span>
    <span className="text-xl font-mono text-stone ml-2">£2,500</span>
  </div>
  <div className="flex-1" />
  <div>
    <span className={cn("text-lg font-mono", onTrack ? "text-mint" : "text-coral")}>
      {percentage}%
    </span>
    <span className="text-xs text-stone ml-1">
      {onTrack ? "on track" : "ahead of pace"}
    </span>
  </div>
</div>
<div className="h-1.5 bg-navy rounded-full overflow-hidden">
  <div className="h-full rounded-full bg-gradient-to-r from-coral to-coral-bright"
       style={{ width: `${percentage}%` }} />
</div>
```

### Budget Overview Section

Use the same table structure as the Budgets page (Section 5) but read-only. No inline editing on dashboard — just the compact grouped table. Click any row → navigates to Budgets page with that group expanded.

Columns on dashboard: `Category | Budgeted | Spent | Available`
No editable cells. Available column uses colour-as-data (mint/yellow/coral).

### Spending Chart

Keep the recharts AreaChart but reduce height from 200px to 160px. Remove the wrapping Card. Use a section label instead:

```tsx
<div className="mt-6">
  <h3 className="text-xs uppercase tracking-wider text-stone mb-3">
    SPENDING TREND — LAST 30 DAYS
  </h3>
  <div className="bg-charcoal rounded-xl p-4">
    <ResponsiveContainer width="100%" height={160}>
      {/* existing chart */}
    </ResponsiveContainer>
  </div>
</div>
```

### Recent Transactions

Show last 5-8 transactions using the new compact `TransactionRow` (Section 6), grouped by date. No wrapping Card — just a section with a label.

### Components to Delete from Dashboard

- `BudgetGroupCard` grid
- `SinkingFundCard` grid (move to a dedicated Sinking Funds sub-page or section in Budgets)
- `StatBlock` 4-column grid (replaced by MonthSummaryBar)
- Tab buttons and tab state
- Top Categories emoji grid

---

## 5. Budget Page Redesign (YNAB-Inspired)

This is the centrepiece. The entire page becomes one dense, interactive table.

### Page Layout

```
┌─────────────────────────────────────────────────────────────┐
│  BUDGETS ─ 12 active budgets                                │  ← TopBar
├─────────────────────────────────────────────────────────────┤
│  Spent £1,847  │  Budgeted £2,500  │  Available £653       │  ← Inline summary (not cards)
├─────────────────────────────────────────────────────────────┤
│  Category          │  Budgeted  │  Activity  │  Available   │  ← Table header
├─────────────────────────────────────────────────────────────┤
│ ▼ ESSENTIAL (4)                    £630    -£643    -£13    │  ← Group header (collapsible)
│   ⊡ Groceries       │  £300.00  │  -£245.30 │  £54.70     │  ← Budget row (editable)
│   ⊡ Bills            │  £150.00  │  -£148.20 │  £1.80      │
│   ⊡ Transport        │  £100.00  │  -£78.50  │  £21.50     │
│   ⊡ Rent             │  £80.00   │  -£80.00  │  £0.00      │
│   + Add category                                            │  ← Quick add
├─────────────────────────────────────────────────────────────┤
│ ▼ LIFESTYLE (3)                    £500    -£390    £110    │  ← Group header
│   ⊡ Eating out       │  £200.00  │  -£156.40 │  £43.60     │
│   ⊡ Shopping         │  £150.00  │  -£134.00 │  £16.00     │
│   ⊡ Entertainment    │  £150.00  │  -£99.60  │  £50.40     │
│   + Add category                                            │
├─────────────────────────────────────────────────────────────┤
│ ► SAVINGS (2)  [collapsed]         £400    -£400    £0      │
├─────────────────────────────────────────────────────────────┤
│  TOTAL                             £2,500  -£1,847  £653    │  ← Footer row
└─────────────────────────────────────────────────────────────┘
```

### Table Structure

```
Column         | Width     | Alignment | Content
─────────────────────────────────────────────────────
Category       | flex-1    | left      | Icon + name
Budgeted       | 120px     | right     | £amount (EDITABLE — click to edit)
Activity       | 120px     | right     | £spent (read-only, from API)
Available      | 120px     | right     | £remaining (computed, colour-coded)
Actions        | 48px      | center    | Delete icon (visible on hover)
```

### Column Widths (Tailwind)

```tsx
<div className="grid grid-cols-[1fr_120px_120px_120px_48px] items-center">
```

### Table Header Row

```tsx
<div className="grid grid-cols-[1fr_120px_120px_120px_48px] items-center
                py-2 px-3 border-b border-navy-mid text-xs uppercase
                tracking-wider text-stone sticky top-0 bg-charcoal z-10">
  <span>Category</span>
  <span className="text-right">Budgeted</span>
  <span className="text-right">Activity</span>
  <span className="text-right">Available</span>
  <span />
</div>
```

### Group Header Row

```tsx
interface BudgetGroupHeaderProps {
  group: BudgetGroupStatus;
  expanded: boolean;
  onToggle: () => void;
}

// Markup pattern:
<div
  className="grid grid-cols-[1fr_120px_120px_120px_48px] items-center
             py-2 px-3 bg-navy-deep/50 border-b border-navy-mid
             cursor-pointer hover:bg-navy-deep/80 select-none"
  onClick={onToggle}
>
  <div className="flex items-center gap-2">
    <ChevronRight className={cn("w-4 h-4 text-stone transition-transform",
                                 expanded && "rotate-90")} />
    <GroupIcon className="w-4 h-4 text-white" />
    <span className="text-sm font-semibold text-white uppercase">{group.name}</span>
    <span className="text-xs text-stone">({group.budget_count})</span>
  </div>
  <span className="text-sm font-mono text-right text-stone">
    {formatCurrency(group.total_budget)}
  </span>
  <span className="text-sm font-mono text-right text-coral">
    {formatCurrency(-group.total_spent)}
  </span>
  <span className={cn("text-sm font-mono text-right font-medium",
    group.remaining < 0 ? "text-coral" :
    group.percentage >= 80 ? "text-yellow" : "text-mint"
  )}>
    {formatCurrency(group.remaining)}
  </span>
  <span />
</div>
```

**Collapse/Expand behaviour:**
- Default: all groups expanded
- Click group header → toggles that group
- State stored in `useState<Record<string, boolean>>` keyed by `group_id`
- Animation: `max-height` transition or `grid-template-rows: 0fr → 1fr`

### Budget Row (within a group)

```tsx
<div className="grid grid-cols-[1fr_120px_120px_120px_48px] items-center
                py-1.5 px-3 border-b border-navy-mid/30
                hover:bg-navy-deep/30 group">
  {/* Category */}
  <div className="flex items-center gap-2 pl-6">
    <CategoryIcon size={16} strokeWidth={1.5} className="text-stone" />
    <span className="text-sm text-white capitalize">
      {category.replace(/_/g, " ")}
    </span>
  </div>

  {/* Budgeted — EDITABLE */}
  <EditableAmount
    value={budget.amount}
    onSave={(newAmount) => updateBudget({ id: budget.budget_id, data: { amount: newAmount } })}
    className="text-right"
  />

  {/* Activity — read-only */}
  <span className="text-sm font-mono text-right text-coral">
    -{formatCurrency(budget.spent)}
  </span>

  {/* Available — colour-coded */}
  <span className={cn("text-sm font-mono text-right font-medium",
    budget.remaining < 0 ? "text-coral" :
    budget.percentage >= 80 ? "text-yellow" : "text-mint"
  )}>
    {formatCurrency(budget.remaining)}
  </span>

  {/* Delete action */}
  <div className="flex justify-center opacity-0 group-hover:opacity-100 transition-opacity">
    <button className="p-1 text-stone hover:text-coral">
      <Trash2 size={14} />
    </button>
  </div>
</div>
```

**Row height target: 36px** (`py-1.5` = 6px top + 6px bottom + ~24px content = 36px)

### Inline Edit UX for Budget Amount

See Section 8 for full spec. Summary:
- Click the amount → input field appears in-place, pre-filled, text selected
- Type new amount → Enter or blur to save (optimistic update)
- Escape to cancel
- Tab moves to next editable cell in the column

### Progress Visualization: Bar Goes Away

**Kill the `BudgetBar` component in the budget table.** The Available column with colour-as-data (coral = over, yellow = warning, mint = healthy) replaces it entirely. Colour is faster to scan than bar width.

The progress bar only survives on:
- Dashboard Monthly Summary Bar (thin, h-1.5)
- Sinking Funds (where progress-to-target makes sense)

### Quick Add at Bottom of Each Group

```tsx
<div className="py-1.5 px-3 pl-6">
  <button
    className="flex items-center gap-1.5 text-xs text-stone hover:text-white transition-colors"
    onClick={() => setAddingToGroup(group.group_id)}
  >
    <Plus size={14} />
    <span>Add category</span>
  </button>
</div>
```

**When clicked:**
- The button is replaced by an inline row with:
  - Category select (Radix Select, compact) in the Category column
  - Amount input in the Budgeted column
  - Enter to create, Escape to cancel
- No modal. No dialog. Inline.

```tsx
{addingToGroup === group.group_id && (
  <div className="grid grid-cols-[1fr_120px_120px_120px_48px] items-center
                  py-1.5 px-3 border-b border-navy-mid/30 bg-navy-deep/20">
    <div className="pl-6">
      <select className="bg-navy border border-navy-mid rounded px-2 py-1
                         text-sm text-white w-40"
              autoFocus>
        {availableCategories.map(cat => (
          <option key={cat} value={cat}>{cat.replace(/_/g, " ")}</option>
        ))}
      </select>
    </div>
    <div className="text-right">
      <input type="number" step="0.01" placeholder="0.00"
             className="bg-navy border border-coral/50 rounded px-2 py-1
                        text-sm font-mono text-white text-right w-20"
             onKeyDown={handleKeyDown} />
    </div>
    <span className="text-sm text-stone text-right">—</span>
    <span className="text-sm text-stone text-right">—</span>
    <button onClick={() => setAddingToGroup(null)}
            className="p-1 text-stone hover:text-coral">
      <X size={14} />
    </button>
  </div>
)}
```

### Monthly Totals Footer Row (Per Group)

Already shown in the group header row (total budgeted, total activity, total available). No separate footer needed per group — YNAB puts totals in the group header, which is cleaner.

### Page Footer: Grand Total Row

```tsx
<div className="grid grid-cols-[1fr_120px_120px_120px_48px] items-center
                py-2 px-3 border-t-2 border-navy-mid bg-charcoal
                sticky bottom-0">
  <span className="text-sm font-semibold text-white uppercase">Total</span>
  <span className="text-sm font-mono text-right font-semibold text-white">
    {formatCurrency(totalBudget)}
  </span>
  <span className="text-sm font-mono text-right font-semibold text-coral">
    -{formatCurrency(totalSpent)}
  </span>
  <span className={cn("text-sm font-mono text-right font-semibold",
    totalRemaining < 0 ? "text-coral" : "text-mint"
  )}>
    {formatCurrency(totalRemaining)}
  </span>
  <span />
</div>
```

### Keyboard Navigation

| Key | Action |
|-----|--------|
| Tab | Move to next editable cell (Budgeted column, next row) |
| Shift+Tab | Move to previous editable cell |
| Enter | Confirm edit, move to next row's editable cell |
| Escape | Cancel edit, restore previous value |
| Arrow Down | Move focus to same column, next row |
| Arrow Up | Move focus to same column, previous row |

Implementation: Each `EditableAmount` registers a ref. A parent context (`BudgetTableKeyboardContext`) tracks the currently-focused cell index and handles arrow key navigation.

### Import/Actions

Move "Import CSV" into a `...` menu (Radix DropdownMenu) in the top right. "Add Budget" is replaced by the inline quick-add per group. If you want a global "Add Budget" button, add it to the TopBar as a secondary action.

---

## 6. Transaction Page Redesign

### Row Density Target: 40px

```tsx
// New TransactionRow layout
<div className="grid grid-cols-[28px_1fr_100px_100px] items-center
                py-2 px-3 border-b border-navy-mid/30
                hover:bg-navy-deep/20 cursor-default group"
     style={{ minHeight: '40px' }}>
  {/* Icon */}
  <div className="w-7 h-7 rounded-lg bg-charcoal flex items-center justify-center">
    <CategoryIcon size={14} strokeWidth={1.5} className="text-stone" />
  </div>

  {/* Merchant + Category */}
  <div className="pl-3 min-w-0">
    <div className="text-sm font-medium text-white truncate">{merchant}</div>
    <div className="text-xs text-stone truncate">
      {/* Inline-editable category pill */}
      <InlineCategoryEdit
        category={category}
        onSave={handleCategoryChange}
      />
      <span className="mx-1.5 text-navy-mid">·</span>
      <span>{formatRelativeDate(date)}</span>
    </div>
  </div>

  {/* Amount */}
  <div className={cn("text-sm font-mono text-right",
    isExpense ? "text-coral" : "text-mint"
  )}>
    {isExpense ? "-" : "+"}{formatCurrency(Math.abs(amount))}
  </div>

  {/* Running balance (optional — stretch goal) */}
  <div className="text-xs font-mono text-right text-stone">
    {/* future: running balance */}
  </div>
</div>
```

**Kill:**
- `hover:translate-x-2` effect
- `rounded-xl` per row
- `p-4` padding
- `w-11 h-11` icon size

### Inline Category Editing

**Use Radix Popover, NOT Radix Select.**

Why: A Select replaces the trigger text. A Popover can display a rich grid of category options with icons and colour coding — more discoverable than a flat list, and matches the current Dialog grid pattern without the full-page modal.

```tsx
<Popover>
  <PopoverTrigger asChild>
    <button className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded
                       text-xs capitalize text-stone hover:text-white
                       hover:bg-navy-mid/50 transition-colors cursor-pointer">
      <CategoryIcon size={12} strokeWidth={1.5} />
      {category.replace(/_/g, " ")}
    </button>
  </PopoverTrigger>
  <PopoverContent className="w-64 p-2 bg-navy-deep border border-navy-mid rounded-xl"
                  align="start" sideOffset={4}>
    <div className="grid grid-cols-2 gap-1">
      {allCategories.map(cat => (
        <button key={cat}
                onClick={() => { onSave(cat); close(); }}
                className={cn(
                  "flex items-center gap-2 px-2 py-1.5 rounded-lg text-xs capitalize transition-colors",
                  cat === currentCategory
                    ? "bg-coral/20 text-coral"
                    : "text-stone hover:text-white hover:bg-navy-mid/50"
                )}>
          <CatIcon size={14} />
          {cat.replace(/_/g, " ")}
        </button>
      ))}
    </div>
  </PopoverContent>
</Popover>
```

### Group Transactions by Date

```tsx
interface DateGroup {
  label: string;    // "Today", "Yesterday", "Mon 18 Mar", etc.
  date: string;     // ISO date for key
  transactions: Transaction[];
  dayTotal: number; // Sum of amounts for the day
}
```

**Date header row:**

```tsx
<div className="flex items-center justify-between py-2 px-3
                bg-navy-deep/30 border-b border-navy-mid
                sticky top-[var(--header-height)] z-[5]">
  <span className="text-xs font-semibold text-stone uppercase tracking-wider">
    {label}
  </span>
  <span className="text-xs font-mono text-stone">
    {formatCurrency(Math.abs(dayTotal))}
  </span>
</div>
```

Date header should be sticky below the filter bar.

### Compact Filter Bar

Merge search, month navigation, and category filters into one horizontal bar:

```tsx
<div className="flex items-center gap-3 py-2 px-3 bg-charcoal rounded-xl mb-4
                sticky top-0 z-20">
  {/* Month nav */}
  <button onClick={handlePrevMonth} className="p-1 text-stone hover:text-white">
    <ChevronLeft size={16} />
  </button>
  <span className="text-sm font-medium text-white min-w-[120px] text-center">
    {monthRange.label}
  </span>
  <button onClick={handleNextMonth} disabled={monthOffset >= 0}
          className="p-1 text-stone hover:text-white disabled:text-navy-mid">
    <ChevronRight size={16} />
  </button>

  {/* Divider */}
  <div className="w-px h-5 bg-navy-mid" />

  {/* Search */}
  <div className="relative flex-1 max-w-xs">
    <Search size={14} className="absolute left-2 top-1/2 -translate-y-1/2 text-stone" />
    <input type="text" placeholder="Search..."
           className="w-full pl-7 pr-3 py-1.5 rounded-lg bg-navy border border-navy-mid
                      text-sm text-white placeholder:text-stone focus:border-coral
                      focus:outline-none transition-colors" />
  </div>

  {/* Divider */}
  <div className="w-px h-5 bg-navy-mid" />

  {/* Category pills — compact */}
  <div className="flex gap-1.5 overflow-x-auto">
    {categories.map(cat => (
      <button key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={cn(
                "px-2.5 py-1 rounded-full text-xs font-medium whitespace-nowrap transition-colors",
                cat === selectedCategory
                  ? "bg-coral text-white"
                  : "text-stone hover:text-white hover:bg-navy-mid"
              )}>
        {cat === "All" ? "All" : cat.replace(/_/g, " ")}
      </button>
    ))}
  </div>
</div>
```

### Editable Fields

| Field | Editable? | Method |
|-------|-----------|--------|
| Category | ✅ Yes | Radix Popover with category grid |
| Notes | ✅ Yes (stretch goal) | Click to reveal input, blur to save |
| Amount | ❌ No | Monzo-sourced, immutable |
| Merchant | ❌ No | Monzo-sourced |
| Date | ❌ No | Monzo-sourced |

---

## 7. Sidebar Changes

### Current State

The sidebar is actually decent. It already uses lucide-react icons (`LayoutDashboard`, `Receipt`, `PiggyBank`, etc.), has clean nav structure, and shows sync status in the footer. **Keep most of it.**

### Tweaks

1. **Reduce nav item padding** from `px-4 py-3` to `px-3 py-2`. Current rows are 44px; target 36px.

2. **Add budget summary widget** at the bottom, above the sync status:

```tsx
{/* Budget pulse widget */}
<div className="px-4 py-3 border-t border-navy-mid">
  <div className="flex justify-between items-baseline mb-1.5">
    <span className="text-xs text-stone uppercase tracking-wider">This month</span>
    <span className="text-xs font-mono text-stone">{daysLeft}d left</span>
  </div>
  <div className="flex justify-between items-baseline">
    <span className="text-sm font-mono text-white">
      {formatCurrency(totalRemaining)}
    </span>
    <span className={cn("text-xs font-medium",
      onTrack ? "text-mint" : "text-coral"
    )}>
      {onTrack ? "on track" : "over pace"}
    </span>
  </div>
  <div className="h-1 bg-navy rounded-full mt-2 overflow-hidden">
    <div className="h-full bg-coral rounded-full"
         style={{ width: `${spentPercentage}%` }} />
  </div>
</div>
```

3. **Active state** — change from `bg-coral/10 text-coral` to `bg-coral/10 text-coral border-l-2 border-coral` for a stronger active indicator (YNAB uses a left border accent).

4. **Logo area** — fine as-is. The coral `M` box with glow is good brand identity.

### Data for Sidebar Widget

The sidebar needs access to budget totals. Options:
- Lift data to layout level (recommended): the `App` layout fetches `useBudgetGroupStatuses` and passes summary data down via context
- Or: sidebar calls the hook directly (simpler but less clean)

Recommend a `BudgetSummaryContext` that provides `{ totalBudget, totalSpent, totalRemaining, daysLeft, onTrack }` app-wide.

---

## 8. Inline Editing Technical Spec

### EditableAmount Component

The core reusable component for click-to-edit number fields.

```tsx
// src/components/ui/editable-amount.tsx

interface EditableAmountProps {
  /** Current value in pence */
  value: number;
  /** Called with new value in pence on save */
  onSave: (newValue: number) => Promise<void>;
  /** Additional className for the container */
  className?: string;
  /** Tabindex for keyboard navigation */
  tabIndex?: number;
}

function EditableAmount({ value, onSave, className, tabIndex }: EditableAmountProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const displayValue = formatCurrency(value);

  const startEditing = () => {
    setEditValue((value / 100).toFixed(2));
    setIsEditing(true);
  };

  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [isEditing]);

  const handleSave = async () => {
    const newPence = Math.round(parseFloat(editValue) * 100);
    if (isNaN(newPence) || newPence <= 0) {
      setIsEditing(false);
      return;
    }
    if (newPence === value) {
      setIsEditing(false);
      return;
    }

    setIsSaving(true);
    try {
      await onSave(newPence);
    } catch {
      // Rollback: value hasn't changed in parent state
    } finally {
      setIsSaving(false);
      setIsEditing(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      e.preventDefault();
      handleSave();
    }
    if (e.key === "Escape") {
      setIsEditing(false);
    }
    if (e.key === "Tab") {
      // Let Tab propagate for keyboard nav, but save first
      handleSave();
    }
  };

  if (isEditing) {
    return (
      <input
        ref={inputRef}
        type="number"
        step="0.01"
        min="0"
        value={editValue}
        onChange={(e) => setEditValue(e.target.value)}
        onBlur={handleSave}
        onKeyDown={handleKeyDown}
        className={cn(
          "bg-navy border border-coral/50 rounded px-1.5 py-0.5",
          "text-sm font-mono text-white text-right w-20",
          "focus:outline-none focus:border-coral",
          className
        )}
      />
    );
  }

  return (
    <button
      onClick={startEditing}
      tabIndex={tabIndex}
      className={cn(
        "text-sm font-mono text-right text-white px-1.5 py-0.5 rounded",
        "hover:bg-navy-mid/50 cursor-text transition-colors",
        isSaving && "opacity-50",
        className
      )}
    >
      {isSaving ? "..." : displayValue}
    </button>
  );
}
```

### Optimistic Updates

Use `@tanstack/react-query`'s `onMutate` / `onError` / `onSettled` pattern:

```typescript
const updateBudget = useMutation({
  mutationFn: (params: { id: string; data: Partial<Budget> }) =>
    api.updateBudget(params.id, params.data),
  onMutate: async (params) => {
    // Cancel outgoing refetches
    await queryClient.cancelQueries({ queryKey: ["budget-statuses"] });

    // Snapshot previous value
    const previous = queryClient.getQueryData<BudgetStatus[]>(["budget-statuses"]);

    // Optimistically update
    queryClient.setQueryData<BudgetStatus[]>(["budget-statuses"], (old) =>
      old?.map((b) =>
        b.budget_id === params.id
          ? { ...b, amount: params.data.amount ?? b.amount }
          : b
      )
    );

    return { previous };
  },
  onError: (_err, _vars, context) => {
    // Rollback
    if (context?.previous) {
      queryClient.setQueryData(["budget-statuses"], context.previous);
    }
  },
  onSettled: () => {
    queryClient.invalidateQueries({ queryKey: ["budget-statuses"] });
    queryClient.invalidateQueries({ queryKey: ["budget-group-statuses"] });
  },
});
```

### InlineCategoryEdit Component

```tsx
// src/components/ui/inline-category-edit.tsx

interface InlineCategoryEditProps {
  category: string;
  onSave: (newCategory: string) => Promise<void>;
}

function InlineCategoryEdit({ category, onSave }: InlineCategoryEditProps) {
  const [open, setOpen] = useState(false);
  const [saving, setSaving] = useState(false);

  const Icon = getCategoryIcon(category);

  const handleSelect = async (newCategory: string) => {
    if (newCategory === category) {
      setOpen(false);
      return;
    }
    setSaving(true);
    try {
      await onSave(newCategory);
    } finally {
      setSaving(false);
      setOpen(false);
    }
  };

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <button className={cn(
          "inline-flex items-center gap-1 px-1.5 py-0.5 rounded",
          "text-xs capitalize transition-colors",
          saving ? "text-stone/50" : "text-stone hover:text-white hover:bg-navy-mid/50"
        )}>
          <Icon size={12} strokeWidth={1.5} />
          {category.replace(/_/g, " ")}
        </button>
      </PopoverTrigger>
      <PopoverContent
        className="w-56 p-1.5 bg-navy-deep border border-navy-mid rounded-xl shadow-xl"
        align="start"
        sideOffset={4}
      >
        <div className="grid grid-cols-2 gap-0.5">
          {allCategories.map(cat => {
            const CatIcon = getCategoryIcon(cat);
            return (
              <button
                key={cat}
                onClick={() => handleSelect(cat)}
                className={cn(
                  "flex items-center gap-1.5 px-2 py-1.5 rounded-lg text-xs capitalize transition-colors",
                  cat === category
                    ? "bg-coral/20 text-coral"
                    : "text-stone hover:text-white hover:bg-navy-mid/30"
                )}
              >
                <CatIcon size={13} strokeWidth={1.5} />
                {cat.replace(/_/g, " ")}
              </button>
            );
          })}
        </div>
      </PopoverContent>
    </Popover>
  );
}
```

### Why Popover Over Select

1. **Visual richness** — grid layout with icons and colour highlights. A Select is a flat list.
2. **Discovery** — user sees all options at once. YNAB uses a similar grid/panel approach.
3. **Positioning** — Radix Popover handles collision detection, so it works in dense table rows.
4. **Existing dependency** — Radix Popover is lightweight and may already be a Radix UI dep (if not, it's ~3KB).

Note: Need to add `@radix-ui/react-popover` to dependencies if not already installed.

### Loading & Error States

**Loading (saving):**
- EditableAmount: show "..." text with `opacity-50`
- InlineCategoryEdit: dim the trigger text with `opacity-50`, disable click

**Error (save failed):**
- Flash the cell with a `ring-2 ring-coral` outline for 1.5s
- Restore previous value (optimistic rollback handles this)
- Optional: toast notification via a lightweight toast system

**No global loading spinners for inline edits.** The interaction should feel instant (optimistic) with subtle visual feedback only on failure.

---

## 9. New/Modified Components

### New Components

#### 1. `EditableAmount`
- **File:** `src/components/ui/editable-amount.tsx`
- **Replaces:** Budget Dialog for amount editing
- **Props:**
  ```typescript
  interface EditableAmountProps {
    value: number;              // Amount in pence
    onSave: (value: number) => Promise<void>;
    className?: string;
    tabIndex?: number;
    disabled?: boolean;
  }
  ```
- **Behaviour:** Click → input, Enter/blur → save, Escape → cancel, Tab → save + move focus

#### 2. `InlineCategoryEdit`
- **File:** `src/components/ui/inline-category-edit.tsx`
- **Replaces:** Transaction category Dialog
- **Props:**
  ```typescript
  interface InlineCategoryEditProps {
    category: string;
    allCategories: string[];
    onSave: (category: string) => Promise<void>;
    disabled?: boolean;
  }
  ```
- **Behaviour:** Click pill → Popover grid appears → click category → save + close

#### 3. `BudgetTable`
- **File:** `src/components/budget-table/budget-table.tsx`
- **Replaces:** Budget list Card + BudgetBar rows on Budgets page
- **Props:**
  ```typescript
  interface BudgetTableProps {
    groups: BudgetGroupStatus[];
    onUpdateBudget: (id: string, amount: number) => Promise<void>;
    onDeleteBudget: (id: string) => Promise<void>;
    onCreateBudget: (groupId: string, category: string, amount: number) => Promise<void>;
  }
  ```
- **Behaviour:** Full YNAB-style grouped table with inline editing, collapse/expand, quick add

#### 4. `BudgetTableGroupHeader`
- **File:** `src/components/budget-table/group-header.tsx`
- **Replaces:** `BudgetGroupCard`
- **Props:**
  ```typescript
  interface BudgetTableGroupHeaderProps {
    group: BudgetGroupStatus;
    expanded: boolean;
    onToggle: () => void;
  }
  ```
- **Behaviour:** Click to expand/collapse. Shows group totals.

#### 5. `BudgetTableRow`
- **File:** `src/components/budget-table/budget-row.tsx`
- **Replaces:** Individual budget items inside BudgetGroupCard
- **Props:**
  ```typescript
  interface BudgetTableRowProps {
    budget: BudgetStatus;
    onUpdate: (amount: number) => Promise<void>;
    onDelete: () => Promise<void>;
  }
  ```
- **Behaviour:** Displays one budget row with inline-editable amount

#### 6. `QuickAddRow`
- **File:** `src/components/budget-table/quick-add-row.tsx`
- **Replaces:** "Add Budget" Dialog
- **Props:**
  ```typescript
  interface QuickAddRowProps {
    groupId: string;
    availableCategories: string[];
    onAdd: (category: string, amount: number) => Promise<void>;
    onCancel: () => void;
  }
  ```
- **Behaviour:** Inline category select + amount input. Enter → create, Escape → cancel.

#### 7. `MonthSummaryBar`
- **File:** `src/components/ui/month-summary-bar.tsx`
- **Replaces:** Total Budget Summary Card on Dashboard + 3 stat cards on Budgets page
- **Props:**
  ```typescript
  interface MonthSummaryBarProps {
    spent: number;
    budgeted: number;
    remaining: number;
    percentage: number;
    daysElapsed: number;
    daysTotal: number;
    onTrack: boolean;
  }
  ```
- **Behaviour:** Horizontal summary with thin progress bar

#### 8. `DateGroupHeader`
- **File:** `src/components/ui/date-group-header.tsx`
- **Replaces:** Nothing (new — transactions were previously ungrouped)
- **Props:**
  ```typescript
  interface DateGroupHeaderProps {
    label: string;      // "Today", "Yesterday", "Mon 18 Mar"
    dayTotal: number;   // Sum of transaction amounts
  }
  ```
- **Behaviour:** Sticky date separator row in transaction list

#### 9. `TransactionFilterBar`
- **File:** `src/components/ui/transaction-filter-bar.tsx`
- **Replaces:** Separate search input + month nav buttons + category pill row
- **Props:**
  ```typescript
  interface TransactionFilterBarProps {
    monthLabel: string;
    onPrevMonth: () => void;
    onNextMonth: () => void;
    canGoNext: boolean;
    searchQuery: string;
    onSearchChange: (q: string) => void;
    categories: string[];
    selectedCategory: string;
    onCategoryChange: (cat: string) => void;
  }
  ```
- **Behaviour:** All-in-one sticky filter bar

### Modified Components

#### 10. `TransactionRow` (MODIFIED)
- **File:** `src/components/ui/transaction-row.tsx`
- **Changes:**
  - Grid layout instead of flex
  - `py-2 px-3` instead of `p-4`
  - `w-7 h-7` icon instead of `w-11 h-11`
  - Lucide icon instead of emoji
  - Remove `hover:translate-x-2`
  - Remove `rounded-xl` per-row
  - Add `InlineCategoryEdit` component for category
  - Add `border-b border-navy-mid/30` instead of being a card
- **New Props:**
  ```typescript
  interface TransactionRowProps {
    transaction: Transaction;
    onCategoryChange: (newCategory: string) => Promise<void>;
  }
  ```

#### 11. `CategoryPill` (MODIFIED)
- **File:** `src/components/ui/category-pill.tsx`
- **Changes:**
  - Replace `categoryEmojis` with `getCategoryIcon` from `category-icons.ts`
  - Render `<Icon size={14} />` instead of emoji span
  - Delete local `categoryEmojis` map

#### 12. `Sidebar` (MODIFIED)
- **File:** `src/components/layout/sidebar.tsx`
- **Changes:**
  - Reduce nav padding: `px-3 py-2` instead of `px-4 py-3`
  - Add active left border: `border-l-2 border-coral` when active
  - Add budget pulse widget above sync status footer

### Components to DELETE

| Component | File | Reason |
|-----------|------|--------|
| `BudgetGroupCard` | `budget-group-card.tsx` | Replaced by `BudgetTableGroupHeader` + `BudgetTableRow` |
| `SinkingFundCard` | `sinking-fund-card.tsx` | Move to dedicated section/page (out of scope for v1) |
| `StatBlock` | `stat-block.tsx` | Replaced by `MonthSummaryBar` |
| `BudgetBar` | `budget-bar.tsx` | Removed from budget views. If kept for sinking funds, slim it down later. |

---

## 10. Implementation Order

Priority-ordered. Items marked ⚡ are quick wins (big visual impact, low effort). Items marked 🔗 have dependencies.

### Phase 1: Foundation (do first, unblocks everything)

| # | Task | Effort | Impact | Independent? |
|---|------|--------|--------|-------------|
| 1 | ⚡ Create `src/lib/category-icons.ts` — icon mapping + helpers | 30 min | High | ✅ Yes |
| 2 | ⚡ Update `CategoryPill` — replace emoji with lucide icons | 15 min | High | 🔗 Needs #1 |
| 3 | ⚡ Update `TransactionRow` — lucide icons, reduce padding to `py-2 px-3`, kill `hover:translate-x-2`, kill per-row rounding, use `border-b` | 30 min | High | 🔗 Needs #1 |
| 4 | ⚡ Global padding/typography pass in `index.css` — reduce stat-block padding, transaction row defaults | 20 min | Medium | ✅ Yes |

### Phase 2: Budget Table (the centrepiece)

| # | Task | Effort | Impact | Independent? |
|---|------|--------|--------|-------------|
| 5 | Build `EditableAmount` component | 1 hr | High | ✅ Yes |
| 6 | Build `BudgetTableGroupHeader` component | 45 min | High | ✅ Yes |
| 7 | Build `BudgetTableRow` component | 45 min | High | 🔗 Needs #5 |
| 8 | Build `QuickAddRow` component | 30 min | Medium | ✅ Yes |
| 9 | Build `BudgetTable` — assemble group headers + rows + quick add + footer | 1.5 hr | Critical | 🔗 Needs #5-8 |
| 10 | Rewrite `budgets.tsx` — replace card layout with BudgetTable, kill dialog, kill 3 stat cards | 1 hr | Critical | 🔗 Needs #9 |

### Phase 3: Transaction Improvements

| # | Task | Effort | Impact | Independent? |
|---|------|--------|--------|-------------|
| 11 | Install `@radix-ui/react-popover` (if needed) | 5 min | — | ✅ Yes |
| 12 | Build `InlineCategoryEdit` component | 1 hr | High | 🔗 Needs #1, #11 |
| 13 | Build `DateGroupHeader` component | 20 min | Medium | ✅ Yes |
| 14 | Build `TransactionFilterBar` component | 45 min | Medium | ✅ Yes |
| 15 | Add date grouping logic (utility function) | 30 min | Medium | ✅ Yes |
| 16 | Rewrite `transactions.tsx` — integrate filter bar, date groups, inline category edit, compact rows | 1.5 hr | High | 🔗 Needs #12-15 |

### Phase 4: Dashboard Overhaul

| # | Task | Effort | Impact | Independent? |
|---|------|--------|--------|-------------|
| 17 | Build `MonthSummaryBar` component | 30 min | High | ✅ Yes |
| 18 | Build read-only budget overview table (reuse BudgetTable structure) | 45 min | High | 🔗 Needs Phase 2 |
| 19 | Rewrite `dashboard.tsx` — kill tabs, single scroll, integrate summary bar + budget overview + chart + recent transactions | 2 hr | Critical | 🔗 Needs #17, #18 |

### Phase 5: Sidebar + Polish

| # | Task | Effort | Impact | Independent? |
|---|------|--------|--------|-------------|
| 20 | ⚡ Sidebar nav padding reduction + active border | 15 min | Medium | ✅ Yes |
| 21 | Create `BudgetSummaryContext` for app-wide budget data | 30 min | Low | ✅ Yes |
| 22 | Sidebar budget pulse widget | 30 min | Medium | 🔗 Needs #21 |
| 23 | Delete dead components: `BudgetGroupCard`, `StatBlock`, `SinkingFundCard` | 15 min | Cleanup | 🔗 After Phase 4 |
| 24 | Keyboard navigation context for budget table | 1 hr | Medium | 🔗 Needs Phase 2 |

### Total Estimated Effort

| Phase | Effort |
|-------|--------|
| Phase 1: Foundation | ~1.5 hr |
| Phase 2: Budget Table | ~5 hr |
| Phase 3: Transactions | ~4 hr |
| Phase 4: Dashboard | ~3.5 hr |
| Phase 5: Polish | ~2.5 hr |
| **Total** | **~16.5 hr** |

### Quick Wins Summary (do these first for immediate visual impact)

1. ⚡ **Icon system** (#1-2) — 45 min, kills all emoji instantly
2. ⚡ **Transaction row density** (#3) — 30 min, rows drop from ~65px to ~40px
3. ⚡ **Sidebar tightening** (#20) — 15 min, subtle but polish
4. ⚡ **Global padding pass** (#4) — 20 min, everything breathes better

These 4 quick wins take ~2 hours and will make the app feel 50% more professional before the big structural changes begin.

---

## Appendix: Radix UI Dependencies

Current:
- `@radix-ui/react-dialog` ✅
- `@radix-ui/react-alert-dialog` ✅
- `@radix-ui/react-label` ✅
- `@radix-ui/react-select` ✅
- `@radix-ui/react-slot` ✅

Need to add:
- `@radix-ui/react-popover` — for InlineCategoryEdit
- `@radix-ui/react-collapsible` — optional, for group expand/collapse (can also do with CSS/state)
- `@radix-ui/react-dropdown-menu` — for overflow actions menu on budget page

```bash
npm install @radix-ui/react-popover @radix-ui/react-dropdown-menu
```

---

## Appendix: Colour-as-Data Reference

Used consistently across Budget Table Available column, dashboard budget overview, and sidebar widget:

| Condition | Colour | Token |
|-----------|--------|-------|
| Available > 0, usage < 80% | Mint | `text-mint` (#00D9B5) |
| Available > 0, usage ≥ 80% | Yellow | `text-yellow` (#FFD93D) |
| Available ≤ 0 (over budget) | Coral | `text-coral` (#FF5A5F) |
| Exactly on budget (£0.00) | Stone | `text-stone` (#94A3B8) |

This replaces status badges, status text, and progress bar colour — the number itself communicates health.

---

## Appendix: Monarch Money Analysis (Added 2026-03-22)

> Nick specifically likes Monarch and wants its best ideas brought in. This section documents Monarch's key UI patterns and what to steal.

### What Makes Monarch Gorgeous

Monarch's brand refresh (late 2024) explicitly tackled the same problems Nick is describing:
- "More information, less scrolling" — they condensed transaction row heights, tightened spacing throughout
- "Reduced height of transactions in lists to improve information density" (their exact words)
- "Made the main sections of the budget page collapsible and improved information density"
- Interactive charts that filter the transaction list live when you click a bar

Their design philosophy: **numbers are the product**. Everything else is scaffolding.

### Key Monarch Patterns to Steal

#### 1. "Mark as Reviewed" on Transactions ⭐
Monarch's killer feature. Every transaction gets a "reviewed" state. Dashboard can show only unreviewed items. Badge on the nav item shows count of unreviewed transactions.

**Implementation for this app:**
- Add `reviewed: boolean` field to transaction display (API may already have it)
- Show a subtle checkmark icon on the right of each row, dims on hover until clicked
- Sidebar nav badge: `Transactions (12)` showing unreviewed count
- "Mark all reviewed" button in filter bar header

This single feature makes the app feel like a financial command centre.

#### 2. Customizable Dashboard Widgets
Monarch lets users drag/drop widget order and toggle visibility. Not essential for v1, but the **widget structure** itself is worth stealing:

Instead of the current approach (giant cards + tab switch), Monarch's dashboard is a **vertical stack of purpose-built widgets**, each with:
- A minimal header (label + icon, no border)
- One clear number or chart as the hero
- A "click to expand" affordance

Specific widgets to implement (in order, stacked):
1. **Cash Flow This Month** — Income vs Spending, two large numbers side by side with delta
2. **Budget Progress** — Compact table showing top 5 over-budget categories, "See All" link
3. **Unreviewed Transactions** — List of last 5 needing review, "Mark All" button
4. **Upcoming Recurring** — Next 3 bills due, amounts, days until due
5. **Spending Trend** — The existing area chart, but smaller (150px height)

#### 3. Flex Budget Buckets (3 types)
Monarch categorises budgets into:
- **Fixed** — Same every month (rent, mortgage, car payment). Shown separately, less emphasis on over/under.
- **Flexible** — Variable spending (groceries, eating out). These need the YNAB-style colour tracking.
- **Non-monthly** — Quarterly, annual, seasonal. Shows as sinking fund with monthly contribution target.

**Implementation:** Add a `budget_type` field (fixed/flexible/non_monthly) to the budget schema. Group header badges could show "Fixed" / "Flex" / "Savings". The table rows for Fixed budgets could have a muted style (they're not as urgent to track).

#### 4. Transaction Splitting
Monarch lets you split one transaction across multiple categories (e.g. a Tesco shop that's part food, part household).

**Implementation:** On the inline category editor, add a "+ Split" option at the bottom of the category popover. Opens a simple split form: two rows each with category + amount, totalling to match the original. Requires API support.

#### 5. Rules Auto-categorisation (already exists!)
The app already has a `rules.tsx` page. Monarch's UX here is clean:
- When you manually change a category, it immediately asks "Create a rule for future transactions from [Merchant]?"
- Simple Yes/No inline prompt, not a modal

**Implementation:** After `InlineCategoryEdit` saves successfully, show a subtle inline prompt below the row: `"Always categorise [Merchant] as [Category]? Create rule"` with Yes/Skip buttons. Auto-dismiss after 5 seconds.

#### 6. Recurring Bills Calendar View
Monarch shows a calendar-style view of recurring bills with:
- Day numbers as column headers
- Bills plotted on their due date
- Running total of fixed monthly costs at top
- "Amount due this month" vs "Amount paid" summary

The existing Subscriptions page is a list. Consider upgrading to a simple calendar strip (horizontal timeline of the month with bills plotted).

#### 7. Monarch's Budget Table Layout (detail)

Monarch's budget page has these exact columns on desktop:
```
[Icon] [Category Name]    [Budgeted]  [Actual]  [Available]
```

Where:
- **Available** = Budgeted - Actual. This is the money column. Coloured by health.
- **Budgeted** column is click-to-edit inline
- **Actual** links to filtered transaction view for that category
- Row height: ~36px

Group header row shows group totals in the same columns. Collapsible with chevron.

This maps directly to the design plan's Budget Table in Section 5, confirming the right direction.

#### 8. Monarch's Color Palette (for reference)

Monarch uses:
- White backgrounds (light mode) — we're dark, but the principle of high contrast is the same
- Teal/green for positive/available
- Red/coral for over budget
- Purple accent for goals
- Neutral grey for muted text

Our existing palette (coral, mint, yellow, navy) maps almost perfectly to Monarch's semantic usage. Keep it.

### Monarch vs YNAB vs Current App: Feature Gap Analysis

| Feature | Current App | YNAB | Monarch | Priority |
|---------|-------------|------|---------|----------|
| Inline budget editing | ❌ (modal) | ✅ | ✅ | P1 |
| Inline category editing | ❌ (modal) | ❌ | ✅ | P1 |
| Dense transaction rows | ❌ (60-70px) | ✅ | ✅ | P1 |
| Date grouping on transactions | ❌ | ✅ | ✅ | P1 |
| Lucide icons (no emoji) | ❌ | ✅ | ✅ | P1 |
| Budget groups/hierarchy | ✅ (card grid) | ✅ (table) | ✅ (table) | P1 |
| Mark as reviewed | ❌ | ❌ | ✅ | P2 |
| Collapsible budget sections | ❌ | ✅ | ✅ | P2 |
| Customizable dashboard | ❌ | ❌ | ✅ | P3 |
| Cash flow widget | ❌ | ❌ | ✅ | P2 |
| Recurring calendar view | ❌ (list) | ❌ | ✅ | P3 |
| Rule suggestion on edit | ❌ | ❌ | ✅ | P2 |
| Transaction splitting | ❌ | ✅ | ✅ | P3 |
| Budget type (fixed/flex) | ❌ | ✅ | ✅ | P2 |
| Spending trend chart | ✅ | ❌ | ✅ | ✅ keep |
| Month navigation | ✅ | ✅ | ✅ | ✅ keep |

### Monarch-Specific Additions to Implementation Order

These should be slotted in after Phase 4 (Dashboard):

| # | Task | Effort | Monarch Feature |
|---|------|--------|----------------|
| M1 | Add `reviewed` state to TransactionRow — checkmark icon, optimistic toggle | 1 hr | Mark as Reviewed |
| M2 | Unreviewed transaction count badge on sidebar nav item | 30 min | Nav badge |
| M3 | Rule suggestion prompt after inline category save | 1 hr | Auto-rule UX |
| M4 | Cash Flow widget (income vs spend summary) on dashboard | 45 min | Cash Flow |
| M5 | Budget type labels (Fixed/Flex) on group headers | 30 min | Flex Buckets |
| M6 | Upcoming bills strip on dashboard (3 upcoming recurring items) | 45 min | Bills Calendar |
