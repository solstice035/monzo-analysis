# Multi-Account Support Design

**Date:** 2026-01-19
**Status:** Approved

## Problem

The app currently aggregates data from all Monzo accounts (personal + joint) into a single view. This makes budget vs actual tracking difficult when accounts should be managed separately.

## Decision

Implement account-scoped filtering with a global account selector. Each account has completely separate budgets, rules, and views.

## Design

### User Experience

- Global account dropdown in the header
- Selecting an account filters all data (dashboard, transactions, budgets, rules)
- Selection persists in localStorage
- Default: Joint account

### Database Changes

**Budgets table** - Add required `account_id` FK:
```sql
ALTER TABLE budgets ADD COLUMN account_id UUID NOT NULL REFERENCES accounts(id);
```

**Rules table** - Add required `account_id` FK:
```sql
ALTER TABLE rules ADD COLUMN account_id UUID NOT NULL REFERENCES accounts(id);
```

### API Changes

| Endpoint | Change |
|----------|--------|
| `GET /api/v1/accounts` | **New** - List all accounts |
| `GET /api/v1/transactions` | Add `account_id` query param (required) |
| `GET /api/v1/budgets` | Add `account_id` query param (required) |
| `GET /api/v1/budgets/status` | Add `account_id` query param (required) |
| `POST /api/v1/budgets` | Add `account_id` in body (required) |
| `GET /api/v1/rules` | Add `account_id` query param (required) |
| `POST /api/v1/rules` | Add `account_id` in body (required) |
| `GET /api/v1/dashboard/summary` | Add `account_id` query param (required) |
| `GET /api/v1/dashboard/trends` | Add `account_id` query param (required) |
| `GET /api/v1/dashboard/recurring` | Add `account_id` query param (required) |

### Frontend Changes

1. **AccountContext** - React context storing selected account ID
2. **AccountSelector** - Dropdown component in header
3. **localStorage** - Persist selection as `selectedAccountId`
4. **Default logic** - On first load, find joint account (`uk_retail_joint`) or fall back to first account

### Data Flow

```
User selects account in header
       ↓
AccountContext updates selectedAccountId
       ↓
All pages re-fetch with account_id param
       ↓
API returns account-scoped data
       ↓
UI renders filtered view
```

## Migration Strategy

Since this is a fresh deployment with minimal data:
1. Run migrations to add `account_id` columns
2. Existing budgets/rules without account_id will need manual cleanup or deletion
3. Re-create budgets per account after migration

## Verification

1. Switch between accounts - dashboard stats change
2. Create budget on personal account - not visible when viewing joint
3. Refresh page - selection persists
4. Clear localStorage - defaults to joint account
