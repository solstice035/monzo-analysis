# Code Review: Multi-Account Support - 2026-01-20

## Summary

Review of the multi-account support implementation (commit `3d63a51`) with PAL precommit and code review validation.

**Overall Status:** ⚠️ Security issues identified - fixes required before production deployment

## Test Results

- **Backend Tests:** 108/108 PASSING
- **Playwright Tests:** Not configured (no test files exist)

## Critical Security Issues (IDOR Vulnerabilities)

### 1. Budget Update/Delete - Missing Account Ownership Validation

**File:** `backend/app/api/budgets.py` (lines 104-135)

**Issue:** The `update_budget` and `delete_budget` endpoints identify budgets solely by `budget_id`. No validation ensures the budget belongs to the user's selected account.

**Risk:** An attacker could modify or delete budgets belonging to other accounts by guessing `budget_id` values.

**Fix Required:**
```python
@router.delete("/{budget_id}", status_code=204)
async def delete_budget(
    budget_id: str,
    account_id: str = Query(..., description="The account ID that owns the budget"),
) -> None:
    async with get_session() as session:
        service = BudgetService(session)
        deleted = await service.delete_budget(budget_id, account_id)
        if not deleted:
            raise HTTPException(
                status_code=404, detail="Budget not found or does not belong to this account"
            )
```

### 2. Rule Update/Delete - Missing Account Ownership Validation

**File:** `backend/app/api/rules.py` (lines 98-135)

**Issue:** Same as budgets - `update_rule` and `delete_rule` operate solely on `rule_id` without `account_id` verification.

**Risk:** User could modify or delete rules belonging to another account.

**Fix Required:** Same pattern as budgets - add `account_id` query parameter and compound lookup.

### 3. Transaction Update - Missing Account Validation

**File:** `backend/app/api/transactions.py` (lines 110-138)

**Issue:** The `PATCH /transactions/{id}` endpoint fetches a transaction using only its `transaction_id`:
```python
result = await session.execute(
    select(TransactionModel).where(TransactionModel.id == transaction_id)
)
```

**Risk:** Any user could modify any transaction in the system if they guess the ID.

**Fix Required:**
```python
result = await session.execute(
    select(TransactionModel).where(
        TransactionModel.id == transaction_id,
        TransactionModel.account_id == account_id  # ADD THIS
    )
)
```

## High Priority Issues

### 4. Migration Does Not Handle Existing Data

**File:** `backend/alembic/versions/002_add_account_id_to_budgets_rules.py` (lines 24, 49-51)

**Issue:** The migration adds nullable `account_id` columns but leaves existing records with `NULL` values. No automated backfill.

**Risk:** Existing installations will have orphaned data that becomes inaccessible or causes errors.

**Fix Required:** Add data migration step:
```python
def upgrade() -> None:
    # ... (add nullable columns as before)

    # Backfill existing records to primary account
    op.execute("""
        WITH primary_account AS (SELECT id FROM accounts LIMIT 1)
        UPDATE budgets
        SET account_id = (SELECT id FROM primary_account)
        WHERE account_id IS NULL;
    """)
    op.execute("""
        WITH primary_account AS (SELECT id FROM accounts LIMIT 1)
        UPDATE category_rules
        SET account_id = (SELECT id FROM primary_account)
        WHERE account_id IS NULL;
    """)

    # Make columns non-nullable
    op.alter_column('budgets', 'account_id', nullable=False)
    op.alter_column('category_rules', 'account_id', nullable=False)
```

## Suggestions (Nice to Have)

### 5. Account Selector Visual Enhancement
**File:** `frontend/src/components/account-selector.tsx` (lines 24-29)

Consider adding icons or badges to distinguish account types more clearly.

### 6. Account Context Loading State
**File:** `frontend/src/contexts/AccountContext.tsx` (lines 38-59)

Consider adding `isInitializing` state or using `useMemo` for initial selection to avoid brief flash.

### 7. Batch Query Invalidation
**File:** `frontend/src/contexts/AccountContext.tsx` (lines 66-72)

Multiple individual invalidation calls could be consolidated with a predicate.

## What's Working Well

1. **Clean Architecture:** `AccountContext` properly encapsulates account state management
2. **Query Optimization:** `BudgetService.get_all_budget_statuses()` avoids N+1 queries
3. **Proper React Patterns:** All hooks use `enabled: !!accountId` correctly
4. **Database Indexes:** Performance indexes created (`idx_budgets_account`, `idx_category_rules_account`)
5. **localStorage Persistence:** Selected account survives page refresh
6. **GET/CREATE Operations:** All properly scope by `account_id`

## Frontend Files (All Good)

| File | Status | Notes |
|------|--------|-------|
| `frontend/src/contexts/AccountContext.tsx` | ✅ | Clean implementation |
| `frontend/src/components/account-selector.tsx` | ✅ | Well-structured UI |
| `frontend/src/hooks/useApi.ts` | ✅ | Proper account scoping |
| `frontend/src/lib/api.ts` | ✅ | Correct API signatures |
| `frontend/src/pages/budgets.tsx` | ✅ | Passes account_id on create |
| `frontend/src/pages/rules.tsx` | ✅ | Passes account_id on create |

## Action Items

- [ ] Fix IDOR in `backend/app/api/budgets.py` (update_budget, delete_budget)
- [ ] Fix IDOR in `backend/app/api/rules.py` (update_rule, delete_rule)
- [ ] Fix IDOR in `backend/app/api/transactions.py` (update_transaction)
- [ ] Update migration `002_add_account_id_to_budgets_rules.py` with backfill
- [ ] Update frontend to pass `account_id` on update/delete calls
- [ ] Add integration tests for account isolation

## Related Files

- Previous review: [docs/CODE_REVIEW_2026-01-18.md](CODE_REVIEW_2026-01-18.md)
- Multi-account design: [docs/plans/2026-01-19-multi-account-support-design.md](plans/2026-01-19-multi-account-support-design.md)
