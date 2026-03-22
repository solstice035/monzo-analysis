# Monzo Analysis — Design Document v2.0

> **Status:** Draft for review  
> **Date:** March 2026  
> **Author:** Design Swarm (Jeeves)  
> **Replaces:** Visual Identity v1 (January 2026)  
> **Inspiration:** Monarch Money · YNAB · Monzo brand language  

---

## Table of Contents

1. [Design Philosophy](#1-design-philosophy)
2. [Visual Identity](#2-visual-identity)
3. [Layout System](#3-layout-system)
4. [Component Specifications](#4-component-specifications)
5. [Page Designs](#5-page-designs)
6. [Interaction Patterns](#6-interaction-patterns)
7. [Accessibility & Quality](#7-accessibility--quality)
8. [What Changed from V1](#8-what-changed-from-v1)

---

## 1. Design Philosophy

### Core Principle: Numbers Are the Product

Every design decision in this app should serve one goal: make financial numbers **instantly readable and actionable**. Everything else — colours, spacing, typography, layout — is scaffolding.

**Monarch's lesson:** Their 2024 brand refresh was explicitly about "more information, less scrolling" — condensing rows, tightening spacing, making dense data the default rather than the exception. We're applying the same logic.

**YNAB's lesson:** The budget table isn't a list of cards. It's a spreadsheet-style table where every number is editable inline, every row communicates health via colour, and no modal is needed for common actions.

### Design Tenets

1. **Density by default.** A financial app is a data tool. Generous whitespace belongs in marketing. Data tools should show as much information as possible without cognitive overload.

2. **Colour communicates state.** We don't need status badges, warning icons, or explanatory text. If a budget is over, the available number is coral. If it's tight, it's yellow. If healthy, mint. The number *is* the status.

3. **Inline over modal.** Modals break context. Editing a budget amount should not open a dialog box — it should turn the number into an input field. Category reassignment should be a popover on the row, not a full-screen dialog.

4. **No emoji.** Emoji are inconsistent across platforms, render at low fidelity on dark backgrounds, and communicate amateur. lucide-react provides 500+ clean, consistent SVG icons at any size. Use them.

5. **Mobile-first density.** The app runs on desktop but the row heights and interaction patterns should feel comfortable on a laptop screen. Target: 40–44px per transaction row. YNAB and Monarch both trend here.

---

## 2. Visual Identity

### 2.1 Colour Palette

The V1 palette is correct and stays unchanged. Only semantic application rules change.

#### Brand Colours

| Token | Hex | Usage |
|-------|-----|-------|
| `--coral` | `#FF5A5F` | Primary CTA, active states, over-budget indicator |
| `--coral-bright` | `#FF7C7E` | Hover states on coral |
| `--coral-deep` | `#E54D51` | Active/pressed coral |
| `--navy` | `#14233C` | Page background |
| `--charcoal` | `#1E293B` | Surface / panel background |
| `--navy-deep` | `#1B3A5C` | Card / popover background |
| `--navy-mid` | `#2B5278` | Borders, dividers, inactive states |
| `--ink` | `#0A1628` | Deepest background, footer |
| `--mint` | `#00D9B5` | Positive, available, income, on-track |
| `--yellow` | `#FFD93D` | Warning (80–99% budget usage) |
| `--stone` | `#94A3B8` | Secondary text, muted labels |
| `--slate` | `#475569` | Tertiary text, timestamps |

#### Semantic Usage Rules (new in V2)

| Situation | Colour | Do Not Also Add |
|-----------|--------|-----------------|
| Budget available, < 80% used | `text-mint` | Status badge |
| Budget warning, ≥ 80% | `text-yellow` | Warning icon |
| Budget over | `text-coral` | "Over budget" text label |
| Income transaction | `text-mint` | Positive prefix (or use `+` prefix only) |
| Expense transaction | `text-coral` | Negative prefix (always use `-`) |
| Unreviewed transaction | coral dot indicator | Additional text |

#### What V1 Got Wrong

- Using both status badges **and** colour-coded text (double-redundant)
- Using `text-4xl` for stat values inside cards — these were oversized for the information density we need
- Background gradients on every card added visual weight without meaning

### 2.2 Typography

Three fonts. Each has a job. Don't mix them up.

| Font | Weight | Use |
|------|--------|-----|
| **Bebas Neue** | Regular (only) | Page titles, top-level headings, month/year display |
| **Outfit** | 300–600 | All body text, labels, descriptions, navigation, UI copy |
| **Space Mono** | 400, 700 | All financial values — amounts, percentages, counts |

#### Type Scale

| Role | Font | Size | Weight | Letter Spacing |
|------|------|------|--------|----------------|
| Hero number | Space Mono | 14rem | 700 | 0 |
| Page title | Bebas Neue | 3.5rem | — | 0.04em |
| Section header (in-page) | Outfit | 0.65rem | 700 | 0.2em uppercase |
| Merchant name | Outfit | 0.88rem | 500 | 0 |
| Sub-label / date | Outfit | 0.72rem | 400 | 0 |
| Financial value (large) | Space Mono | 1.1rem | 700 | 0 |
| Financial value (table) | Space Mono | 0.8rem | 400 | 0 |
| Meta label | Outfit | 0.62–0.65rem | 600 | 0.15–0.2em + uppercase |

#### Typography Rules

- Numbers are always **right-aligned** when in columns
- No `text-4xl` on inline labels (max 2rem for values shown inline within a list)
- Bebas Neue is for **page context only** — not for section titles within a page
- Financial values use Space Mono. Always. No exceptions.
- Line height: 1.4 for lists/rows, 1.6 for prose paragraphs

### 2.3 Icon System

**Rule:** No emoji anywhere in the application. All category indicators use lucide-react SVG icons.

#### Standard Icon Sizes

| Context | Size | strokeWidth | Container |
|---------|------|-------------|-----------|
| Transaction row | 14px | 1.5 | 28×28px rounded-lg |
| Budget table row | 14px | 1.5 | 22×22px rounded-md |
| Sidebar navigation | 16px | 1.75 | none (inline) |
| Category pill | 11–13px | 2 | none (inline) |
| Button icon | 13px | 2 | none |
| Dashboard widget | 16px | 1.5 | 24×24px rounded |

#### Category → Icon Mapping

Defined in `src/lib/category-icons.ts`. Single source of truth.

| Category | Lucide Icon | Import |
|----------|-------------|--------|
| `groceries` | ShoppingCart | `import { ShoppingCart }` |
| `eating_out` | UtensilsCrossed | `import { UtensilsCrossed }` |
| `shopping` | ShoppingBag | `import { ShoppingBag }` |
| `transport` | Car | `import { Car }` |
| `entertainment` | Clapperboard | `import { Clapperboard }` |
| `bills` | FileText | `import { FileText }` |
| `general` | Package | `import { Package }` |
| `holidays` | Plane | `import { Plane }` |
| `cash` | Banknote | `import { Banknote }` |
| `expenses` | Briefcase | `import { Briefcase }` |
| `savings` | PiggyBank | `import { PiggyBank }` |
| `health` | Heart | `import { Heart }` |
| `subscriptions` | CreditCard | `import { CreditCard }` |
| `investments` | TrendingUp | `import { TrendingUp }` |
| `utilities` | Wifi | `import { Wifi }` |
| `education` | GraduationCap | `import { GraduationCap }` |
| `fitness` | Dumbbell | `import { Dumbbell }` |
| `income` | ArrowDownLeft | `import { ArrowDownLeft }` |
| *(fallback)* | HelpCircle | `import { HelpCircle }` |

---

## 3. Layout System

### 3.1 Spacing Philosophy

V1 used `p-4` (16px) uniformly for rows. V2 uses **context-specific density**.

| Component | V1 Padding | V2 Padding | Height |
|-----------|-----------|-----------|--------|
| Transaction row | `p-4` | `py-2 px-3` | ~44px → ~40px |
| Budget table row | `p-4 + BudgetBar` | `py-[10px] px-3` | ~80px → ~36px |
| Budget group card | `p-4 rounded-2xl border` | table group-header row | ~120px → ~36px |
| Stat blocks | `p-6 rounded-2xl` | inline month-bar | ~100px → ~56px |
| Sidebar nav item | `px-4 py-3` | `px-3 py-2` | ~48px → ~40px |

### 3.2 Card Usage Rules

**Use cards for:** self-contained widgets that could be moved (charts, cash flow summary, goals). A card has a purpose boundary.

**Do not use cards for:** list items, budget rows, transaction rows, anything in a repeating list. These get row separators instead (`border-b border-navy-mid/30`).

**V1 card anti-patterns eliminated:**
- `BudgetGroupCard` — each budget group was a full card. Replaced by table group-header row.
- `StatBlock` — 4 separate cards for 4 numbers. Replaced by `MonthSummaryBar`.
- `SinkingFundCard` — inline cards in the dashboard grid. Moved to dedicated page section.
- Transaction row cards with `rounded-xl` per row.

### 3.3 Grid System

| Context | Columns | Gap |
|---------|---------|-----|
| Dashboard two-pane | `1fr 1fr` | `1rem` |
| Budget table | `1fr 120px 120px 120px 48px` | 0 (table) |
| Sidebar + main | `220px 1fr` | 0 |
| Colour swatches | `repeat(3, 1fr)` | `1rem` |

---

## 4. Component Specifications

### 4.1 MonthSummaryBar

Replaces: 4-stat-block grid on Dashboard, 3-stat-card row on Budgets page.

**Layout:** Horizontal bar with 4 items separated by 1px dividers, plus a progress track.

```
[Spent: £2,847] | [Budgeted: £4,000] | [Available: £1,153] | [████░░░░░░░░ Day 19/31 · On track]
```

**Spec:**
- Height: ~56px
- Background: `--charcoal`, border-radius `--radius-md`
- Spent: `text-white`, Space Mono
- Available: `text-mint` / `text-yellow` / `text-coral` based on health
- Progress rail: 4px height. Fill: mint gradient. Marker: thin white line at "expected today" position.
- "On track" text: mint if actual spend ≤ expected pace + 10%, coral otherwise.

### 4.2 BudgetTable

Replaces: BudgetGroupCard grid, BudgetBar list.

**Column structure:** `[icon + name] [Budgeted] [Activity] [Available] [actions]`

**Width distribution:**
- Name column: `1fr` (flex)
- Budgeted, Activity, Available: `120px` each, right-aligned
- Actions: `48px`, right-aligned, hidden until hover

**Group header row:**
- Background: `--charcoal`
- Left chevron (▼/▶) toggles collapse
- Group name: Outfit 600, 0.8rem
- Group totals in all three number columns
- `border-top: 1px solid --navy-mid`

**Budget row:**
- Height: ~36px, `py-[10px] px-3`
- Icon: 22×22px container, `--navy-mid` background, `border-radius: 5px`
- Name: Outfit 500, 0.85rem
- All indented `1.25rem` from left edge (under group name)
- Hover: `background: rgba(255,255,255,0.025)`
- Actions (edit pencil, delete bin): appear on row hover, opacity 0→1

**Inline editing — Budgeted column:**
- Default: plain number text, cursor changes to `text` on hover, subtle hover background
- Click: number becomes `<input>` with `outline: 2px solid --coral`
- Enter / Tab: save (optimistic update) + move focus to next editable cell
- Escape: restore original value, exit edit mode
- Blur: save (same as Enter)
- Pattern: `EditableAmount` component

**Available column colour:**
- `> 0, < 80% used` → `text-mint`
- `> 0, ≥ 80% used` → `text-yellow`
- `≤ 0` → `text-coral`

**Quick Add row:**
- Appears as last row per group
- "+ Add category" button (ghost, Outfit, slate → coral on hover)
- Click: reveals inline `<select>` for category + `<input>` for amount
- Enter: creates budget, row disappears, new budget appears
- Escape: cancel

**Group footer row:**
- Below last budget row in group, above next group header
- Shows group column totals
- `font-weight: 700`, `color: --white` for totals, `border-top: 1px solid --navy-mid`

### 4.3 TransactionRow (V2)

Replaces: V1 TransactionRow with emoji, `p-4`, `rounded-xl`, `hover:translate-x-2`.

**Layout:** CSS Grid `28px 1fr auto auto`
- Col 1: icon container (28×28px, 7px border-radius, `--navy-mid` bg)
- Col 2: merchant name + date (stacked)
- Col 3: category pill (clickable → InlineCategoryEdit)
- Col 4: amount (right-aligned, Space Mono)

**Sizing:**
- `py-[10px] px-0` (no horizontal padding — padded by parent container)
- `border-bottom: 1px solid rgba(255,255,255,0.04)`
- No `border-radius` per row (list, not cards)
- No `hover:translate-x-2` (visual noise)
- Hover: `background: rgba(255,255,255,0.03)`

**Category pill (inline edit trigger):**
- Default: small coloured pill with icon + category name
- Click: Radix `<Popover>` opens below/above with 3×N grid of category options
- Each option: icon + label, click selects + closes
- No modal. No save button. Selection is immediate.
- After save: prompt appears below row: `"Always categorise [Merchant] as [Category]? Create rule"` with Yes/Skip (Monarch-style)

**Reviewed state (Monarch-inspired):**
- Small coral dot on the left of each unreviewed transaction
- Click dot → marks reviewed, dot disappears
- Sidebar badge shows count of unreviewed

### 4.4 DateGroupHeader

New component — transactions were previously ungrouped.

```
─── Today — Mon 22 Mar ──────────────────── -£52.32
```

- `font-size: 0.7rem`, `font-weight: 600`, `letter-spacing: 0.12em`, uppercase
- `color: --stone`
- Daily total: Space Mono, `color: --slate`, right-aligned
- `border-bottom: 1px solid rgba(255,255,255,0.07)`
- Sticky on scroll (position: sticky, top: filter-bar height)

### 4.5 TransactionFilterBar

Replaces: separate search input + month nav + category pill row.

**Layout:** Horizontal bar, single line, `background: --charcoal`, `border-radius: --radius-md`.

```
[‹] March 2026 [›] | Search… | All · Groceries · Eating Out · Transport · Bills
```

- Month nav: `‹` and `›` buttons (28×28px, `--navy-mid` bg)
- Search: flex-1 `<input>`, no border, `color: --white`, placeholder `--slate`
- Dividers: `1px × 20px`, `--navy-mid`
- Filter pills: small `px-3 py-1.5`, `font-size: 0.75rem`, `border-radius: 100px`
- Active pill: `background: --coral`, `color: white`

### 4.6 Sidebar (V2)

**Changes from V1:**
- Nav item padding: `px-3 py-2` (was `px-4 py-3`)
- Active state: coral left border + coral text + coral tinted background (was just coral text + bg)
- Unreviewed badge: coral pill on Transactions nav item
- Budget widget added above footer

**Budget Pulse Widget:**
```
Available this month
£1,153
12 days remaining
[███████░░░░░░░░░░] 
```
- Background: `--navy-deep`, border: `--navy-mid`, `border-radius: --radius-md`
- `sbw-remaining`: Space Mono, `text-mint`, 1.1rem
- Progress rail: 3px height (barely visible — informational only)
- Rail fill colour: mint if on-track, yellow if warning, coral if over

### 4.7 CashFlowWidget

New component, Monarch-inspired.

**Layout:** 2-cell grid (Income | Spent), separated by 1px border. Net total bar below.

- Income: `text-mint` in Bebas Neue 2.2rem
- Spent: `text-white` in Bebas Neue 2.2rem
- Delta vs previous month: small text, mint for improvement, coral for increase
- Net total bar: `background: --navy`, inline row with label + mono value

### 4.8 InlineCategoryEdit

Replaces: Dialog modal for transaction category change.

**Pattern:** Radix `<Popover>` (not `<Select>`, not `<Dialog>`)

**Why Popover over Select:**
- Select is a browser native element — difficult to style consistently
- Dialog requires explicit dismiss and save actions
- Popover opens near the trigger, closes on selection or click-outside, requires no confirmation

**Behaviour:**
1. User clicks category pill on a transaction row
2. Popover opens (Radix `PopoverContent`, `sideOffset={4}`, `align="start"`)
3. Content: 3-column grid of category buttons, each with icon + label
4. Optional: search input at top of popover
5. Click a category: API call fires (optimistic update), popover closes, pill updates
6. Escape: close without saving

### 4.9 EditableAmount

Used in BudgetTable for inline budget editing.

**Component:**
```tsx
// Simplified interface
interface EditableAmountProps {
  value: number;           // in pence
  onSave: (v: number) => Promise<void>;
  tabIndex?: number;
}
```

**Behaviour:**
- Renders as: `<span>£{value}</span>` with `cursor: text` hover
- Click: replaces with `<input type="number" />` pre-filled
- Enter / Tab: parse → validate → call `onSave()` → revert to span display
- Escape: cancel, restore original
- Blur: same as Enter
- Optimistic: span updates immediately, API call in background
- On API error: revert + `ring-2 ring-coral` flash

---

## 5. Page Designs

### 5.1 Dashboard

**V1 structure (broken):**
- Budget Tab / Analytics Tab (fragmented context)
- Giant "Total Budget Summary" card
- Grid of BudgetGroupCards (3-col)
- Analytics Tab: 4 stat blocks + chart + budget progress card + recent transactions card

**V2 structure (single scroll, no tabs):**

```
TopBar: "MARCH 2026" | Day 19 of 31, 12 days until reset | [Sync]
─────────────────────────────────────────────────────────────────
MonthSummaryBar: Spent £2,847 | Budgeted £4,000 | Available £1,153 | [progress]
─────────────────────────────────────────────────────────────────
[CashFlowWidget]              [Recent Transactions (last 5)]
Income £3,450 | Spent £2,847  Sainsbury's -£47.82
                               Pret A Manger -£4.50
                               British Gas -£124.00
                               ...
─────────────────────────────────────────────────────────────────
Budget Overview (read-only BudgetTable, top 2 groups)
  Essential Spending  £1,200  £842   £358
    Groceries          £400   £285   £115
    Shopping           £250   £312   -£62 ← coral
  Lifestyle           ...
  [Manage budgets →]
─────────────────────────────────────────────────────────────────
Spending Trend (recharts AreaChart, 150px height)
─────────────────────────────────────────────────────────────────
```

Key changes:
- No tabs
- MonthSummaryBar replaces both the 4-stat grid AND the giant summary card
- CashFlowWidget is new (Monarch-inspired)
- Budget overview is a read-only slice of the budget table (no inline editing here)
- Chart is smaller (150px vs 200px), same recharts component

### 5.2 Budgets Page

**V1 structure (broken):**
- 3 stat cards (Total Budget / Total Spent / Remaining)
- One big `<Card>` containing a flat list of budget bars + edit/delete buttons on hover

**V2 structure:**

```
TopBar: "BUDGETS" | 12 active budgets | [Import CSV ⬇] [+ Add Budget]
─────────────────────────────────────────────────────────────────
MonthSummaryBar: Spent £2,847 | Budgeted £4,000 | Available £1,153 | [progress]
─────────────────────────────────────────────────────────────────
BudgetTable:
  Category              | Budgeted  | Activity  | Available
  ────────────────────────────────────────────────────────────
  ▼ Essential Spending  | £1,200    | £842      | £358
    [icon] Groceries    | [£400]    | £285      | £115
    [icon] Shopping     | [£250]    | £312      | -£62
    [icon] Transport    | [£150]    | £98       | £52
    + Add category
    ── Group total      | £1,200    | £842      | £358
  ────────────────────────────────────────────────────────────
  ▼ Lifestyle           | £800      | £601      | £199
    [icon] Eating Out   | [£200]    | £165      | £35
    [icon] Entertainment| [£100]    | £87       | £13
    + Add category
    ── Group total      | £800      | £601      | £199
  ────────────────────────────────────────────────────────────
```

- `[£400]` = editable cell (click to edit)
- No progress bars in the table (Available column colour serves the same purpose)
- Groups collapsed by default after first session; state persisted in localStorage
- Import CSV is a ghost button (secondary — rare action)
- "Add Budget" is primary coral button — but it now adds to a specific group (popover to select group) rather than a modal

### 5.3 Transactions Page

**V1 structure (broken):**
- Full-width search bar
- Month nav buttons (← Prev / Next →)
- Horizontal category pill row
- One big `<Card>` with flat list of transaction rows
- Each row: 65px+ height, `hover:translate-x-2`, emoji icon, modal on click

**V2 structure:**

```
TopBar: "TRANSACTIONS" | 142 transactions · March | [Mark all reviewed]
─────────────────────────────────────────────────────────────────
TransactionFilterBar: [‹ Feb] March 2026 [›] | 🔍 Search… | All · Groceries · Bills · …
─────────────────────────────────────────────────────────────────
Transaction List (no card wrapper):

─── Today — Mon 22 Mar ─────────────────────────── -£52.32
[icon] Sainsbury's        [Groceries pill]    -£47.82
       22 Mar
[icon] Pret A Manger      [Eating Out pill]    -£4.50
       22 Mar

─── Yesterday — Sun 21 Mar ──────────────────────── -£124.00
[icon] British Gas        [Bills pill]        -£124.00
       21 Mar
[icon] Salary             [Income pill]      +£3,450.00
       21 Mar

─── Fri 19 Mar ──────────────────────────────────── -£38.40
...

[Load more / infinite scroll]
```

Key changes:
- TransactionFilterBar consolidates all controls into one compact bar
- No Card wrapper — list directly on page background with `border-b` dividers
- Date group headers (sticky)
- Row height: ~40px
- Click category pill → Radix Popover (no modal)
- Remove `hover:translate-x-2`
- Unreviewed dot on left

---

## 6. Interaction Patterns

### 6.1 Inline Budget Editing

```
User clicks "£400" in Budgeted column
→ <input type="number"> appears with value pre-selected
→ User types new amount
→ Press Enter or Tab:
   - Optimistic update (span shows new value immediately)
   - API call fires (PATCH /budgets/{id})
   - On success: no visual change (already showing new value)
   - On error: revert to old value, flash red ring for 1.5s
→ Press Escape:
   - Input removed, original value restored
→ Blur:
   - Same as Enter
→ Tab moves focus to next editable cell in the column (keyboard nav)
```

### 6.2 Inline Category Edit

```
User clicks category pill on a transaction
→ Radix Popover opens near pill
→ Shows 3-column grid of category options (icon + label each)
→ Optional: search box at top
→ User clicks a category:
   - Popover closes
   - Pill updates immediately (optimistic)
   - API call fires (PATCH /transactions/{id})
   - On error: revert pill, toast "Failed to save"
→ After successful save:
   Rule prompt appears below row (dismisses in 5s):
   "Always categorise [Merchant] as [Category]? [Create rule] [Skip]"
→ User clicks Escape or outside:
   - Popover closes, no change
```

### 6.3 Mark as Reviewed

```
Each transaction row has a small coral dot indicator (left edge) if unreviewed
→ Click dot:
   - Dot disappears (optimistic)
   - API call fires
   - Sidebar badge count decrements
→ "Mark all reviewed" in TopBar:
   - Confirmation: "Mark 8 transactions as reviewed?"
   - On confirm: all dots disappear, badge clears
```

### 6.4 Budget Group Collapse

```
Click group header (or chevron):
→ Group rows animate out (height: 0, opacity: 0)
→ Chevron rotates (▼ → ▶)
→ Group totals remain visible in header
→ Collapse state stored in localStorage (key: `budget_group_collapsed_{groupId}`)
→ Persists across page loads within same browser session
```

### 6.5 Quick Add Category

```
Click "+ Add category" at bottom of a group
→ Row expands: [category <select>] [amount <input>] [Enter to save] [Esc to cancel]
→ Category select: shows available categories not yet in this group
→ Enter with valid amount:
   - API call: POST /budgets
   - Row added to table immediately (optimistic)
   - Quick-add row closes
→ Escape: quick-add row closes, no action
```

---

## 7. Accessibility & Quality

### 7.1 Colour Contrast

All text passes WCAG AA at minimum:
- White on `--navy`: ✓ (12:1+)
- White on `--charcoal`: ✓ (8:1+)
- `--mint` on `--navy`: ✓ check — `#00D9B5` on `#14233C` = ~6.5:1 ✓
- `--yellow` on `--navy`: ✓ check — `#FFD93D` on `#14233C` = ~8:1 ✓
- `--coral` on `--navy`: ✓ check — `#FF5A5F` on `#14233C` = ~4.5:1 ✓ (AA)

### 7.2 Keyboard Navigation

- All interactive elements reachable by Tab
- Budget table: Tab moves between editable cells left-to-right, top-to-bottom
- Popovers: Escape closes, arrow keys navigate options
- Inline edit: Enter confirms, Escape cancels

### 7.3 Optimistic Updates

All mutations use react-query's `onMutate` for optimistic updates with `onError` rollback:

```typescript
// Pattern for inline budget edit
const mutation = useMutation({
  mutationFn: (data) => api.updateBudget(id, data),
  onMutate: async (newData) => {
    await queryClient.cancelQueries({ queryKey: ['budgets'] });
    const previous = queryClient.getQueryData(['budgets']);
    queryClient.setQueryData(['budgets'], (old) => /* apply optimistic change */);
    return { previous };
  },
  onError: (err, newData, context) => {
    queryClient.setQueryData(['budgets'], context.previous);
    // flash error state
  },
  onSettled: () => queryClient.invalidateQueries({ queryKey: ['budgets'] }),
});
```

### 7.4 Loading States

- **Inline edits:** No loading spinner. Optimistic update makes it feel instant. Error state handles failure.
- **Page loads:** Skeleton rows matching the expected layout (same height as final rows)
- **Sync button:** Spinner icon replaces sync icon during active sync

---

## 8. What Changed from V1

### Removed

| Element | Reason |
|---------|--------|
| All emoji category icons | Replaced with lucide-react SVG icons |
| `BudgetGroupCard` component | Replaced by `BudgetTable` group-header row |
| `StatBlock` component | Replaced by `MonthSummaryBar` |
| `SinkingFundCard` component | Out of scope for V2 |
| `BudgetBar` component | Replaced by table Available column colour |
| Dashboard Budget/Analytics tabs | Unified single-scroll view |
| Modal for budget editing | Replaced by inline `EditableAmount` |
| Modal for transaction category | Replaced by `InlineCategoryEdit` (Radix Popover) |
| `p-4` on transaction rows | Replaced by `py-2 px-3` |
| `hover:translate-x-2` on rows | Removed (visual noise) |
| `rounded-xl` per transaction row | Removed (rows are not cards) |
| 3-stat-card row on Budgets page | Replaced by `MonthSummaryBar` |

### Added

| Element | Purpose |
|---------|---------|
| `MonthSummaryBar` | Compact single-row summary for month context |
| `BudgetTable` | YNAB-style grouped table with inline editing |
| `EditableAmount` | Inline number editing with keyboard nav |
| `InlineCategoryEdit` | Radix Popover for category selection |
| `DateGroupHeader` | Date-grouped transactions with daily totals |
| `TransactionFilterBar` | Consolidated filter controls |
| `CashFlowWidget` | Income vs spend widget (Monarch-inspired) |
| `QuickAddRow` | Inline budget creation per group |
| `src/lib/category-icons.ts` | Single icon source of truth |
| Sidebar budget widget | Running available balance + days remaining |
| Sidebar badge | Unreviewed transaction count |
| "Mark as reviewed" | Per-transaction and bulk (Monarch-inspired) |
| Rule suggestion prompt | Post-category-edit inline prompt (Monarch-inspired) |

### Unchanged (Intentionally)

| Element | Reason kept |
|---------|-------------|
| Colour palette | Correct and distinctive — only application rules updated |
| Font stack | Bebas Neue + Outfit + Space Mono — working well |
| recharts AreaChart | Good spending trend visualisation |
| Month navigation | Functional and appropriate |
| Account selector | Works fine |
| Sync mechanism | Backend-driven, UI unchanged |
| Rules page | Out of scope for this redesign |
| Settings page | Out of scope |
| Subscriptions page | Out of scope (could be enhanced later with Monarch-style calendar view) |

---

## Appendix A: Files to Create

| File | Status |
|------|--------|
| `src/lib/category-icons.ts` | New |
| `src/components/ui/month-summary-bar.tsx` | New |
| `src/components/ui/editable-amount.tsx` | New |
| `src/components/ui/inline-category-edit.tsx` | New |
| `src/components/ui/date-group-header.tsx` | New |
| `src/components/ui/transaction-filter-bar.tsx` | New |
| `src/components/ui/cash-flow-widget.tsx` | New |
| `src/components/budget-table/budget-table.tsx` | New |
| `src/components/budget-table/group-header.tsx` | New |
| `src/components/budget-table/budget-row.tsx` | New |
| `src/components/budget-table/quick-add-row.tsx` | New |

## Appendix B: Files to Modify

| File | Changes |
|------|---------|
| `src/pages/dashboard.tsx` | Full rewrite — no tabs, new layout |
| `src/pages/budgets.tsx` | Full rewrite — BudgetTable, MonthSummaryBar |
| `src/pages/transactions.tsx` | Full rewrite — FilterBar, date groups, no modal |
| `src/components/ui/transaction-row.tsx` | Density, icon, category pill |
| `src/components/ui/category-pill.tsx` | Replace emoji with getCategoryIcon() |
| `src/components/layout/sidebar.tsx` | Padding, active border, budget widget, badge |

## Appendix C: Files to Delete

| File | Replaced by |
|------|-------------|
| `src/components/ui/budget-group-card.tsx` | BudgetTable |
| `src/components/ui/stat-block.tsx` | MonthSummaryBar |
| `src/components/ui/budget-bar.tsx` | Available column colour |

## Appendix D: NPM Dependencies to Add

```bash
npm install @radix-ui/react-popover @radix-ui/react-dropdown-menu
```

`@radix-ui/react-collapsible` is optional — group collapse can be done with CSS + React state.

---

*Design Document v2.0 — Monzo Analysis — March 2026*
