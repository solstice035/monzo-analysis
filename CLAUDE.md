# Monzo Analysis

## Overview

Personal finance tracking and analytics using the Monzo API. Scheduled data extraction with budget comparison, trend analysis, and spending insights.

**Key approach:** Polling/scheduled extraction (not webhooks). Focus is analytics, not real-time notifications.

## PRD Reference

- **Original PRD:** [[PRD-monzo-webhook]] in Obsidian (`2-Areas/Ideas/`)
- **Local copy:** [docs/PRD.md](docs/PRD.md)
- **Current version:** 0.4 (PRD deep dive complete)

See PRD for full feature requirements (FR-01 to FR-24), user stories, and success metrics.

---

## Key Decisions (from Brainstorm)

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Data extraction | Scheduled polling | User has Monzo notifications; focus is analytics |
| Sync frequency | Daily (configurable) | Balance freshness vs API load |
| Categorisation | Layered rules engine | Respect existing Monzo categories + custom rules |
| ML learning | Future iteration | Architecture supports swap from rules → ML |
| Pot transfers | Exclude from spending | Pots are savings, not spending |

---

## API Documentation

Reference docs in [docs/api-reference/](docs/api-reference/)

### Key Endpoints

| Endpoint | Purpose | Notes |
|----------|---------|-------|
| `GET /accounts` | List accounts | Returns `uk_retail`, `uk_retail_joint` |
| `GET /balance?account_id=X` | Account balance | Includes spend_today |
| `GET /pots` | List savings pots | Balance per pot |
| `GET /transactions` | Fetch transactions | Paginate with `since`, `before`, `limit` |
| `PATCH /transactions/{id}` | Add metadata | Store custom category overrides |

### Transaction Payload (FR-02)

Capture full payload for rich analysis:
- `amount` (pence, negative=spend)
- `merchant` (name, category, logo, address, MCC)
- `category` (Monzo's assignment)
- `metadata` (custom fields via PATCH)
- `created`, `settled` (timestamps)
- `local_amount`, `local_currency` (foreign transactions)
- `counterparty` (for transfers)
- `notes`, `attachments` (user-added)

### Monzo Categories

```
general | eating_out | expenses | transport | cash
bills | entertainment | shopping | holidays | groceries
```

---

## Architecture Considerations

### Categorisation Layer (FR-05)

Priority order for category assignment:
1. User's existing Monzo custom categories (via `metadata`)
2. Monzo's default merchant categories
3. Budget category mapping rules

### Rules Engine

Beyond simple merchant→category mapping:
- **Value-based:** `groceries > £100` → "Big Shop"
- **Merchant+amount:** Specific rules per merchant
- **Time-based:** Weekend patterns, recurring dates

### ML Readiness (FR-07)

Store training data for future ML layer:
- Original Monzo category
- User override category
- Transaction features (merchant, amount, time, etc.)

Architecture should support swappable classification backend.

---

## User Journeys (Summary)

See PRD Appendix B for full flows.

### First-Time Setup
OAuth → Account selection → Initial sync → Budget import → Category mapping → Preferences

### Regular Usage
- **Daily:** Quick health check (2-3 min)
- **Weekly:** Review + reclassify (10-15 min)
- **Monthly:** Trend analysis, budget reset, subscription audit

### Edge Cases
- **Refunds:** Correlate with original purchase
- **Pot transfers:** Exclude from spending totals
- **Joint account:** Configurable split/combined view
- **Foreign currency:** Display both currencies

---

## Project Structure

```
monzo-analysis/
├── CLAUDE.md              # This file
├── docs/
│   ├── PRD.md             # Product requirements
│   └── api-reference/     # Monzo API docs (12 files)
├── src/                   # Source code (TBD)
└── .gitignore
```

---

## Tech Stack

*To be determined in TRD*

Considerations:
- Python (FastAPI/Django) or Node (Next.js) backend
- PostgreSQL for transaction storage
- Redis for caching/job queue
- React/Next.js frontend
- OAuth 2.0 for Monzo auth

---

## Open Questions (for TRD)

From PRD Section 11:
- [ ] Joint account handling: separate budgets or combined?
- [ ] Pot transfers: exclude entirely or track separately?
- [ ] Sync frequency: hourly, daily, or manual trigger?
- [ ] Rules priority order for categorisation conflicts

---

## Project Status

| Milestone | Status | Date |
|-----------|--------|------|
| PRD Gate 1 | ✅ Pass | Jan 2025 |
| Project scaffold | ✅ Complete | 2026-01-17 |
| PRD deep dive | ✅ Complete | 2026-01-18 |
| TRD | ⏳ Pending | - |
| MVP implementation | ⏳ Pending | - |

---

## Next Steps

1. **Create TRD** - Tech stack, data model, API design
2. **Monzo Developer Account** - Register app, get API credentials
3. **Begin MVP** - OAuth flow, transaction sync, basic dashboard
