# Plan: Budget-Centric Redesign for Monzo Analysis

## Summary

Restructure the app to make **budget vs actual comparison** the central feature, with support for **hierarchical categories** matching the user's existing spreadsheet structure.

---

## Analysis: Spreadsheet Structure

The user's budget spreadsheet (`20251016-Joint_Monthly_Expenses.xlsx`) reveals:

**Three-level hierarchy:**
- **Area** → Expense, Income
- **Category** → Kids, Fixed Bills, Car Expenses, Travel, Savings (9 groups)
- **Line Item** → 60+ individual expense items

**Key insight:** The "Monzo Pot / Category" column shows intended transaction mapping:
- Kids → Kids Clubs, Swimming Lessons, School Meals, Queen Eleanors, etc.
- Fixed Bills → Bills, Energy, Council Tax, Mortgage, Garden
- ~25 distinct Monzo categories rolling up to ~9 budget groups

---

## Problem Diagnosis

| Current State | Problem |
|---------------|---------|
| Dashboard shows balance/trends first | Budget comparison is buried |
| 8 hardcoded categories | Can't create "Kids Clubs" or user-defined categories |
| Flat budget model | No grouping, no roll-ups |
| No hierarchy | Would need 60 individual budgets with no organisation |

---

## Recommended Solution: Category Groups with Budget Line Items

### Data Model Changes

**New Entity: `BudgetGroup`**
```sql
CREATE TABLE budget_groups (
    id UUID PRIMARY KEY,
    account_id UUID REFERENCES accounts(id),
    name VARCHAR(100) NOT NULL,
    icon VARCHAR(50),
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Modified: `Budget` table**
```sql
ALTER TABLE budgets
ADD COLUMN group_id UUID REFERENCES budget_groups(id),
ADD COLUMN name VARCHAR(200),           -- Line item name (e.g., "Elodie Piano")
ADD COLUMN period_type VARCHAR(20),     -- 'weekly', 'monthly', 'quarterly', 'annual', 'bi-annual'
ADD COLUMN annual_amount INTEGER,       -- Total annual cost in pence (for sinking funds)
ADD COLUMN target_month INTEGER,        -- Month when annual expense is due (1-12)
ADD COLUMN linked_pot_id VARCHAR(100);  -- Monzo Pot ID for balance tracking

-- 'amount' becomes monthly contribution for sinking funds
-- 'category' becomes the Monzo category to match for transactions
```

**Budget Types:**
1. **Spending budget** (period_type = monthly/weekly): Traditional "don't exceed £X this period"
2. **Sinking fund** (period_type = quarterly/annual/bi-annual): "Contribute £X/month towards £Y target"

### Dashboard Redesign

**Tab Structure:**
- **Tab 1: Budget** (default) - Budget health grid with groups and line items
- **Tab 2: Analytics** - Balance, spending trends, category breakdown, recent transactions

**Budget Tab: Health Grid**

```
┌─────────────────────────────────────────────────────────┐
│  January 2026                        Day 19 of 31       │
├─────────────────────────────────────────────────────────┤
│  [Grid of Budget Group cards with spent/budget/percent] │
│  Click group → Expand to show line items                │
├─────────────────────────────────────────────────────────┤
│  Total: £5,905 / £7,726 (76%)          £1,821 remaining │
└─────────────────────────────────────────────────────────┘
```

**Secondary views (tabs/collapsed):**
- Spending trends chart
- Recent transactions
- Category breakdown

### API Changes

| Endpoint | Purpose |
|----------|---------|
| `GET /api/v1/budget-groups` | List all groups with roll-up totals |
| `POST /api/v1/budget-groups` | Create group |
| `PUT /api/v1/budget-groups/{id}` | Update group |
| `DELETE /api/v1/budget-groups/{id}` | Delete group (cascades to budgets) |
| `GET /api/v1/budget-groups/{id}/status` | Get group with all child budget statuses |

Existing budget endpoints modified to:
- Accept `group_id` parameter
- Return `group` relationship in responses

---

## PRD Requirements to Add

### Category & Group Management
| ID | Requirement |
|----|-------------|
| **FR-CAT-01** | Users can create, edit, delete Budget Groups with name and icon |
| **FR-CAT-02** | Budgets must belong to exactly one Budget Group (enforced - no ungrouped budgets allowed) |
| **FR-CAT-03** | Budget Groups display spent/total roll-up from child Budgets |
| **FR-CAT-04** | Dashboard primary view shows Budget Groups as cards with health indicators |
| **FR-CAT-05** | Clicking a Budget Group expands to show individual Budget line items |
| **FR-CAT-06** | Support CSV import that creates Groups and Budgets from spreadsheet structure |

### Dashboard Redesign
| ID | Requirement |
|----|-------------|
| **FR-DASH-01** | Dashboard has two tabs: "Budget" (primary) and "Analytics" (secondary) |
| **FR-DASH-02** | Budget tab shows budget period progress (Day X of Y) prominently |
| **FR-DASH-03** | Colour coding: Green (<80%), Amber (80-100%), Red (>100%) |
| **FR-DASH-04** | Analytics tab contains: balance, spending trends chart, category breakdown, recent transactions |

### Sinking Funds / Pot-Backed Budgets
| ID | Requirement |
|----|-------------|
| **FR-SINK-01** | Budgets can have period types: weekly, monthly, quarterly, annual, bi-annual |
| **FR-SINK-02** | Annual/quarterly budgets show monthly contribution target (e.g., £675/year = £56.25/month) |
| **FR-SINK-03** | Budgets can be linked to a Monzo Pot for balance tracking |
| **FR-SINK-04** | Pot-backed budgets display: contribution target, actual contributions, pot balance |
| **FR-SINK-05** | Pot transfers (deposits) are tracked as contributions, NOT as spending |
| **FR-SINK-06** | Spending from a pot-backed budget only counts when money leaves the pot (actual expense) |
| **FR-SINK-07** | Show pot balance projection: "On track to have £675 by October" or "£45 short at current rate" |

### Pot Transfer Handling
| ID | Requirement |
|----|-------------|
| **FR-POT-01** | Transfers TO pots are excluded from spending totals (savings, not spending) |
| **FR-POT-02** | Transfers FROM pots to main account are not double-counted as income |
| **FR-POT-03** | Pot balance is fetched from Monzo API and displayed alongside pot-backed budgets |

---

## Implementation Phases

### Phase 1: Data Model (Backend) ✅ COMPLETE (2026-01-20)
1. ✅ Create `BudgetGroup` model and migration
2. ✅ Add `group_id`, `name`, sinking fund fields to `Budget` model
3. ✅ Implement `BudgetGroupService` with roll-up calculations
4. ✅ Add API endpoints for CRUD operations
5. ✅ Add sinking fund contribution calculation logic

**Files Created/Modified:**
- `backend/app/models/budget_group.py` - New BudgetGroup model
- `backend/app/models/budget.py` - Added sinking fund properties
- `backend/alembic/versions/003_add_budget_groups.py` - Migration
- `backend/app/services/budget_groups.py` - BudgetGroupService
- `backend/app/services/budget.py` - SinkingFundStatus, contribution tracking
- `backend/app/api/budget_groups.py` - CRUD endpoints
- `backend/tests/test_budget.py` - Sinking fund tests

**Tests:** 112 passing

### Phase 2: Pot Integration (Backend) ✅ COMPLETE (2026-01-20)
1. ✅ Create `PotService` to fetch pot balances from Monzo API
2. ✅ Add pot linking to budget creation/update endpoints
3. ✅ Implement contribution tracking (deposits to pot)
4. ✅ Calculate pot balance projections

**Files Created/Modified:**
- `backend/app/services/pot.py` - New PotService with contribution tracking
- `backend/app/api/pots.py` - Pots API endpoints including sinking fund status
- `backend/app/api/budgets.py` - Added sinking fund fields to request/response models
- `backend/tests/test_pot.py` - 12 tests for PotService

**Tests:** 124 passing

### Phase 3: Dashboard Redesign (Frontend) ✅ COMPLETE (2026-01-20)
1. ✅ Create `BudgetGroupCard` component
2. ✅ Create `SinkingFundCard` component (shows pot balance + contribution rate)
3. ✅ Replace dashboard layout with budget-first grid
4. ✅ Implement expand/collapse for line items
5. ✅ Move existing widgets to Analytics tab

**Files Created/Modified:**
- `frontend/src/components/ui/budget-group-card.tsx` - New collapsible budget group card
- `frontend/src/components/ui/sinking-fund-card.tsx` - New sinking fund status card
- `frontend/src/lib/api.ts` - Added BudgetGroup, BudgetGroupStatus, Pot, SinkingFundStatus types and API methods
- `frontend/src/hooks/useApi.ts` - Added hooks for budget groups, pots, sinking funds
- `frontend/src/pages/dashboard.tsx` - Complete redesign with Budget/Analytics tabs

**Dashboard Features:**
- Tab navigation: Budget (primary) and Analytics (secondary)
- Total budget summary card with progress bar and on-track indicator
- Budget groups grid with expand/collapse to show line items
- Sinking funds section with pot balance tracking
- Analytics tab contains all previous dashboard widgets

### Phase 4: CSV Import Enhancement
1. Update import to detect group structure from spreadsheet
2. Create groups and budgets in single import
3. Map "Monzo Pot / Category" column to budget category field
4. Auto-detect sinking funds from Timeline column (Annual, Quarterly, etc.)

### Phase 5: Polish
1. Add group reordering (drag-drop)
2. Bulk edit budgets within a group
3. Group-level alerts when any child exceeds threshold
4. Pot balance projection warnings ("£45 short at current rate")

---

## Files to Modify

**Backend:**
- `backend/app/models/` - Add `budget_group.py`
- `backend/app/models/budget.py` - Add relationships
- `backend/alembic/versions/` - Migration for new schema
- `backend/app/services/budget.py` - Add group roll-up logic
- `backend/app/api/budgets.py` - Add group endpoints
- `backend/app/schemas/` - Add group schemas

**Frontend:**
- `frontend/src/pages/dashboard.tsx` - Complete redesign
- `frontend/src/pages/budgets.tsx` - Add group management
- `frontend/src/components/` - New `BudgetGroupCard`, `BudgetLineItem` components
- `frontend/src/lib/api.ts` - Add group API calls

---

## Verification

1. **Data model:** Migration runs without errors, existing budgets preserved
2. **API:** Group CRUD works, roll-ups calculate correctly
3. **Dashboard:** Budget groups display as primary view, click-to-expand works
4. **Import:** CSV creates correct group/budget structure
5. **Sinking funds:** Monthly contribution tracking works, pot balance displays correctly
6. **Pot integration:** Pot balances fetch from Monzo API, contributions tracked separately from spending
7. **Edge cases:** Empty groups, single-item groups, zero-budget items, pots with no linked budget

---

## Design Decisions Made

1. **Ungrouped budgets:** Block creation/update until assigned to a group (enforced)
2. **Dashboard layout:** Two tabs - "Budget" (primary) and "Analytics" (secondary)
3. **Budget hierarchy:** Line-item budgets with auto-rollup to groups
4. **Primary metric:** Budget health by group (cards with spent/budget/percentage)
5. **Sinking funds:** Track monthly contribution rate, link to Monzo Pots for balance
6. **Pot transfers:** Savings (contributions to pots), not spending

## Open Questions

1. Should group icons be predefined (dropdown) or allow any emoji (picker)?
2. For pots not linked to a budget, should they appear somewhere (e.g., "Unbudgeted Pots" section)?
3. Migration: Should we auto-create a "Miscellaneous" group for existing budgets, or require manual assignment?
