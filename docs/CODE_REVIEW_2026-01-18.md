# Code Review - 2026-01-18

## Summary

Full codebase review of Monzo Analysis MVP. No critical issues found. Codebase is production-ready for initial deployment.

---

## High Priority (Performance)

### 1. N+1 Query in Budget Status Calculation

**File:** `backend/app/services/budget.py:275`

**Issue:** `get_all_budget_statuses` executes a separate database query for each budget to calculate its status. This causes N+1 queries and won't scale.

```python
budgets = await self.get_all_budgets()
statuses = []
for budget in budgets:
    status = await self.get_budget_status(budget, reference_date)
    statuses.append(status)
```

**Fix:** Refactor to calculate all budget statuses in a single query using `GROUP BY` and `func.sum()`.

---

### 2. Inefficient Spend Calculation

**File:** `backend/app/services/budget.py:205`

**Issue:** Fetches all transaction rows into memory, then calculates sum in Python.

```python
result = await self._session.execute(select(Transaction).where(...))
transactions = result.scalars().all()
total = sum(abs(tx.amount) for tx in transactions if tx.amount < 0)
```

**Fix:** Perform aggregation in database:

```python
stmt = select(func.sum(func.abs(Transaction.amount))).where(
    and_(
        Transaction.custom_category == budget.category,
        Transaction.created_at >= period_start,
        Transaction.created_at <= period_end,
        Transaction.amount < 0,
    )
)
total_spend = await self._session.scalar(stmt)
```

---

### 3. Silent Slack Failures

**File:** `backend/app/services/slack.py:190`

**Issue:** Bare `except Exception:` swallows all errors without logging.

```python
except Exception:
    return False
```

**Fix:** Catch specific exceptions and add logging:

```python
except httpx.RequestError as e:
    logging.error(f"Failed to send Slack message: {e}")
    return False
```

---

## Medium Priority

### 4. Database Ports Exposed to Host

**File:** `docker-compose.yml:17, 33`

**Issue:** PostgreSQL (5432) and Redis (6379) ports exposed externally.

**Fix:** Remove `ports` sections for production. Services remain accessible via Docker network.

---

### 5. Missing Content-Security-Policy Header

**File:** `frontend/nginx.conf:16`

**Issue:** Missing CSP header; `X-XSS-Protection` is deprecated.

**Fix:** Add CSP header:

```nginx
add_header Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; object-src 'none'; frame-ancestors 'none';" always;
```

---

### 6. Frontend Duplicates Budget Period Logic

**File:** `frontend/src/pages/dashboard.tsx:72`

**Issue:** Frontend calculates `daysUntilReset` assuming calendar month, but backend uses configurable `reset_day`.

**Fix:** Use `period_start` and `period_end` from `/api/v1/budgets/status` response.

---

### 7. Unconventional App Initialization

**File:** `backend/app/main.py:71-75`

**Issue:** `try/except` block to initialize `app` as `None` obscures startup errors.

**Fix:** Remove try/except; let errors propagate. Test using `create_app()` with mocked settings.

---

## Low Priority

### 8. No Container Resource Limits

**File:** `docker-compose.yml`

**Fix:** Add for production:

```yaml
deploy:
  resources:
    limits:
      cpus: '0.50'
      memory: 512M
```

---

### 9. Unnecessary Date String Manipulation

**File:** `backend/app/services/sync.py:58`

**Issue:** Python 3.12+ handles `Z` suffix natively.

**Fix:** Remove `.replace("Z", "+00:00")`:

```python
created_at=datetime.fromisoformat(tx_data["created"]),
```

---

## Positive Findings

- Multi-stage Docker builds with non-root user
- Health checks with `condition: service_healthy`
- Clean service layer architecture
- Well-documented `.env.example`
- All 105 tests passing
