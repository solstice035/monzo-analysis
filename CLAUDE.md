# Monzo Analysis

## Overview

Personal finance tracking and analytics using the Monzo API. Scheduled data extraction with budget comparison, trend analysis, and spending insights.

**Key approach:** Polling/scheduled extraction (not webhooks). Focus is analytics, not real-time notifications.

## Documentation

- **Original PRD:** [[PRD-monzo-webhook]] in Obsidian (`2-Areas/Ideas/`)
- **Local PRD:** [docs/PRD.md](docs/PRD.md)
- **TRD:** [docs/TRD.md](docs/TRD.md)

See PRD for full feature requirements (FR-01 to FR-24), user stories, and success metrics.
See TRD for architecture, data model, API design, and implementation approach.

---

## Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Data extraction | Scheduled polling | User has Monzo notifications; focus is analytics |
| Sync frequency | Daily (configurable) | Balance freshness vs API load |
| Categorisation | Layered rules engine | Respect existing Monzo categories + custom rules |
| ML learning | Future iteration | Architecture supports swap from rules → ML |
| Pot transfers | Exclude from spending | Pots are savings, not spending |
| Notifications | Slack (`#monzo`) | Single channel, webhook integration, rich formatting |
| Deployment | Docker on Unraid | Always-on, no ongoing cost, portable to DigitalOcean |
| Dashboard | Full CRUD UI | Configure rules, budgets, trigger syncs from browser |
| Budget reset | Configurable day (1-28) | Aligns with payday, not calendar month |

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
├── docker-compose.yml     # Container orchestration
├── .env.example           # Environment template
├── backend/
│   ├── app/               # FastAPI application
│   │   ├── api/           # Route handlers
│   │   ├── models/        # SQLAlchemy models
│   │   ├── services/      # Business logic
│   │   └── schemas/       # Pydantic schemas
│   ├── alembic/           # Database migrations
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── pages/         # Dashboard views
│   │   ├── hooks/         # TanStack Query hooks
│   │   └── lib/           # Utilities
│   └── public/
└── docs/
    ├── PRD.md             # Product requirements
    ├── TRD.md             # Technical requirements
    └── api-reference/     # Monzo API docs
```

---

## Tech Stack

### Backend (Python 3.12+)

| Component | Version | Purpose |
|-----------|---------|---------|
| FastAPI | 0.128.x | Async web framework |
| SQLAlchemy | 2.1.x | Async ORM |
| APScheduler | 4.x | Scheduled sync (native async) |
| httpx | latest | Async HTTP client |
| asyncpg | latest | PostgreSQL driver |

### Frontend

| Component | Version | Purpose |
|-----------|---------|---------|
| React | 18.x+ | UI framework |
| Vite | 7.x | Build tool |
| shadcn/ui | latest | Components |
| TanStack Query | 5.x | Data fetching |
| Recharts | latest | Charts |

### Infrastructure

| Component | Purpose |
|-----------|---------|
| PostgreSQL 16 | Primary database |
| Docker Compose | Container orchestration |
| Slack webhooks | Notifications |

### Environment Variables

Configured in `.env` (not committed):

| Variable | Purpose |
|----------|---------|
| `MONZO_CLIENT_ID` | OAuth client ID from developer portal |
| `MONZO_CLIENT_SECRET` | OAuth client secret |
| `MONZO_REDIRECT_URI` | Callback URL for OAuth flow |
| `MONZO_OWNER_ID` | Your Monzo account/user ID |
| `SLACK_WEBHOOK_URL` | Incoming webhook for notifications (optional) |
| `SLACK_CLIENT_ID` | App client ID (for future OAuth features) |
| `SLACK_CLIENT_SECRET` | App client secret |
| `SLACK_SIGNING_SECRET` | Request signature verification |

### Slack Webhook Setup

1. Go to [api.slack.com/apps](https://api.slack.com/apps)
2. **Create New App** → "From scratch" → Name it, select workspace
3. **Incoming Webhooks** → Toggle **On**
4. **Add New Webhook to Workspace** → Select `#monzo` channel → **Allow**
5. Copy the webhook URL to `.env`

Test with:
```bash
curl -X POST -H 'Content-Type: application/json' \
  -d '{"text":"Hello from Monzo Analysis!"}' \
  $SLACK_WEBHOOK_URL
```

---

## Resolved Questions (from TRD)

| Question | Resolution |
|----------|------------|
| Joint account handling | Configurable per-budget (combined or separate) |
| Pot transfers | Excluded from spending totals |
| Sync frequency | Daily default, configurable, with manual trigger |
| Rules priority | Higher priority number = checked first, all conditions AND |

---

## Project Status

| Milestone | Status | Date |
|-----------|--------|------|
| PRD Gate 1 | ✅ Pass | Jan 2025 |
| Project scaffold | ✅ Complete | 2026-01-17 |
| PRD deep dive | ✅ Complete | 2026-01-18 |
| TRD | ✅ Complete | 2026-01-18 |
| MVP implementation | ⏳ Pending | - |

---

## Next Steps

1. **Monzo Developer Account** - Register app, get API credentials
2. **Phase 1: Foundation** - Backend scaffold, database models, OAuth flow
3. **Phase 2: Core Features** - Rules engine, budgets, Slack notifications
4. **Phase 3: Dashboard** - React frontend with full CRUD
5. **Phase 4: Polish** - Testing, Docker setup, deployment

See [TRD Section 13](docs/TRD.md#13-implementation-phases) for detailed phase breakdown.
