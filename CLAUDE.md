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
| Deployment | Docker on Mac Mini | Always-on local server, no ongoing cost |
| Dashboard | Full CRUD UI | Configure rules, budgets, trigger syncs from browser |
| Budget reset | Configurable day (1-28) | Aligns with payday, not calendar month |
| Visual identity | Bold dark mode | Monzo hot coral on navy; premium analytics feel |
| Display font | Bebas Neue | Striking condensed headlines for big numbers |
| Body font | Outfit | Modern geometric sans, friendly yet professional |
| Mono font | Space Mono | Financial data and technical values |
| Category override | User click → modal | Allow users to reclassify transactions |
| Budget import | CSV file upload | Batch import budgets from spreadsheet |
| Recurring detection | Interval analysis | Detect subscriptions by merchant + timing |
| Dashboard charts | Recharts AreaChart | 30-day spending trend visualization |
| Multi-account | Global account selector | Separate budgets/rules per account, default to joint |
| Budget hierarchy | Groups + line items | Roll-up totals per group, matches spreadsheet structure |
| Sinking funds | Monthly contributions | Track progress toward annual targets with pot linking |

---

## Visual Identity

See mockup: [docs/visual-identity-mockup.html](docs/visual-identity-mockup.html)

**Design Direction:** Bold Financial — premium dark mode aesthetic that makes data feel powerful.

### Colour Palette

| Token | Hex | Usage |
|-------|-----|-------|
| `--hot-coral` | #FF5A5F | Primary brand, CTAs, emphasis |
| `--coral-bright` | #FF7C7E | Hover states, highlights |
| `--coral-deep` | #E54D51 | Pressed states, danger |
| `--navy-black` | #14233C | Background, primary surface |
| `--navy-deep` | #1B3A5C | Cards, elevated surfaces |
| `--navy-mid` | #2B5278 | Borders, subtle dividers |
| `--mint` | #00D9B5 | Success, positive changes, income |
| `--yellow` | #FFD93D | Warnings, budget alerts |
| `--sky` | #4FC3F7 | Info, transport category |

### Typography

| Role | Font | Weight | Usage |
|------|------|--------|-------|
| Display | Bebas Neue | 400 | Headlines, stats, big numbers |
| Body | Outfit | 300-800 | UI text, labels, descriptions |
| Mono | Space Mono | 400, 700 | Financial data, amounts, code |

### Component Patterns

- **Stat blocks:** Coral left border, navy background, display font for values
- **Budget bars:** Gradient fills (mint→safe, yellow→warning, coral→danger)
- **Transactions:** Hover reveals coral border, slides right 8px
- **Buttons:** Pill-shaped, coral glow shadow on hover
- **Category pills:** Translucent colour backgrounds matching category

---

## API Documentation

Reference docs in [docs/api-reference/](docs/api-reference/)

### Monzo API Endpoints

| Endpoint | Purpose | Notes |
|----------|---------|-------|
| `GET /accounts` | List accounts | Returns `uk_retail`, `uk_retail_joint` |
| `GET /balance?account_id=X` | Account balance | Includes spend_today |
| `GET /pots` | List savings pots | Balance per pot |
| `GET /transactions` | Fetch transactions | Paginate with `since`, `before`, `limit` |
| `PATCH /transactions/{id}` | Add metadata | Store custom category overrides |

### Internal API Endpoints

| Endpoint | Purpose | Notes |
|----------|---------|-------|
| `GET /api/v1/auth/status` | Check auth status | Returns authenticated + expiry |
| `GET /api/v1/auth/login` | Get OAuth login URL | Redirects to Monzo |
| `GET /api/v1/auth/callback` | OAuth callback | Handles token exchange |
| `GET /api/v1/accounts` | List accounts | Returns all linked Monzo accounts |
| `GET /api/v1/transactions` | List transactions | Requires `account_id` param |
| `PATCH /api/v1/transactions/{id}` | Update transaction | Set custom_category |
| `GET /api/v1/budgets` | List budgets | Requires `account_id` param |
| `GET /api/v1/budgets/status` | Budget statuses | Requires `account_id` param |
| `POST /api/v1/budgets` | Create budget | Requires `account_id` in body |
| `POST /api/v1/budgets/import` | Import CSV | Requires `account_id` param |
| `GET /api/v1/rules` | List rules | Requires `account_id` param |
| `POST /api/v1/rules` | Create rule | Requires `account_id` in body |
| `GET /api/v1/sync/status` | Sync status | Last sync, status, errors |
| `POST /api/v1/sync/trigger` | Trigger sync | Manual sync start |
| `GET /api/v1/dashboard/summary` | Dashboard stats | Requires `account_id` param |
| `GET /api/v1/dashboard/trends` | Spending trends | Requires `account_id` param |
| `GET /api/v1/dashboard/recurring` | Recurring payments | Requires `account_id` param |
| `GET /api/v1/budget-groups` | List budget groups | Requires `account_id` param |
| `POST /api/v1/budget-groups` | Create budget group | Requires `account_id` in body |
| `GET /api/v1/budget-groups/{id}` | Get group with status | Includes roll-up totals |
| `PUT /api/v1/budget-groups/{id}` | Update budget group | Name, icon, display_order |
| `DELETE /api/v1/budget-groups/{id}` | Delete budget group | Cascades to budgets |

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

### Budget Hierarchy

Three-level budget organization matching the user's spreadsheet structure:

```
Account
└── BudgetGroup (e.g., "Kids", "Fixed Bills", "Car Expenses")
    └── Budget (line item, e.g., "Piano Lessons", "Car Tax")
```

**Budget Types:**
- **Spending budget** (`period_type` = weekly/monthly): "Don't exceed £X this period"
- **Sinking fund** (`period_type` = quarterly/annual/bi-annual): "Contribute £X/month towards £Y target"

**Sinking Fund Fields:**
- `annual_amount`: Total target in pence (e.g., £675 car tax = 67500)
- `target_month`: Month when expense is due (1-12)
- `linked_pot_id`: Monzo Pot for balance tracking

**Roll-up Calculations:**
- Group totals = sum of child budget amounts
- Group spent = sum of child spending
- Group status = worst status among children (over > warning > under)

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
| APScheduler | 3.10.x | Scheduled sync (pinned to 3.x for stability) |
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
| `CORS_ORIGINS` | Comma-separated allowed CORS origins (default: localhost) |

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
| Joint account handling | Completely separate budgets/rules per account with global selector |
| Pot transfers | Excluded from spending totals |
| Sync frequency | Daily default, configurable, with manual trigger |
| Rules priority | Higher priority number = checked first, all conditions AND |
| Default account | Joint account selected by default on first load |

---

## Project Status

| Milestone | Status | Date |
|-----------|--------|------|
| PRD Gate 1 | ✅ Pass | Jan 2025 |
| Project scaffold | ✅ Complete | 2026-01-17 |
| PRD deep dive | ✅ Complete | 2026-01-18 |
| TRD | ✅ Complete | 2026-01-18 |
| Visual identity | ✅ Complete | 2026-01-18 |
| Phase 1: Foundation | ✅ Complete | 2026-01-18 |
| Phase 2: Core Features | ✅ Complete | 2026-01-18 |
| Phase 3: Dashboard | ✅ Complete | 2026-01-18 |
| Phase 4: Docker Setup | ✅ Complete | 2026-01-18 |
| MVP implementation | ✅ Complete | 2026-01-18 |
| OAuth Flow Tested | ✅ Complete | 2026-01-18 |
| Local Deployment | ✅ Running | 2026-01-18 |
| Dashboard Trends | ✅ Complete | 2026-01-18 |
| Category Override | ✅ Complete | 2026-01-18 |
| Budget Import CSV | ✅ Complete | 2026-01-18 |
| Recurring Detection | ✅ Complete | 2026-01-18 |
| Subscriptions Page | ✅ Complete | 2026-01-18 |
| Connect Button Fix | ✅ Complete | 2026-01-19 |
| First Live Sync | ✅ Complete | 2026-01-19 |
| Multi-Account Support | ✅ Complete | 2026-01-19 |
| Budget Redesign Phase 1 | ✅ Complete | 2026-01-20 |
| Code Review Fixes | ✅ Complete | 2026-02-07 |
| Test Coverage | ✅ Complete | 2026-02-07 |

---

## Quick Start

### Development

```bash
# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -e ".[dev]"
pytest  # Run tests

# Frontend
cd frontend
npm install
npm run dev  # Start dev server at http://localhost:5173
```

### Production (Docker)

```bash
# Copy environment template
cp .env.example .env
# Edit .env with your credentials

# Run with Docker Compose
docker compose up -d

# Run migrations
docker compose run --rm migrations
```

Access the app at http://localhost

---

## Next Steps

1. ~~**Monzo Developer Account**~~ ✅ Registered
2. ~~**Configure `.env`**~~ ✅ Configured
3. ~~**First OAuth**~~ ✅ Tested successfully (2026-01-18)
4. ~~**Token Persistence**~~ ✅ Database storage implemented
5. ~~**Sync Service**~~ ✅ APScheduler integration complete
6. ~~**Category Override**~~ ✅ Transaction reclassification working
7. ~~**Budget Import**~~ ✅ CSV import functional
8. ~~**Dashboard Trends**~~ ✅ Recharts visualization complete
9. ~~**Recurring Detection**~~ ✅ Subscription detection working
10. **Deploy to Mac Mini** - Copy `docker-compose.yml` and `.env` to server
11. **Initial Sync** - Trigger first real transaction sync from Monzo
12. **Slack Integration** - Configure webhook for daily summaries

### Implemented Features

| Feature | Description | Location |
|---------|-------------|----------|
| OAuth Flow | Monzo authentication with token storage | `backend/app/api/auth.py` |
| Scheduled Sync | APScheduler-based background sync | `backend/app/services/scheduler.py` |
| Transaction API | CRUD with filtering and category override | `backend/app/api/transactions.py` |
| Budget Management | Create, update, delete, import CSV | `backend/app/api/budgets.py` |
| Rules Engine | Category assignment rules | `backend/app/api/rules.py` |
| Dashboard Summary | Real-time stats from database | `backend/app/api/dashboard.py` |
| Spending Trends | 30-day daily spending chart | `frontend/src/pages/dashboard.tsx` |
| Recurring Detection | Subscription identification | `backend/app/services/recurring.py` |
| Subscriptions Page | View and manage recurring payments | `frontend/src/pages/subscriptions.tsx` |
| Multi-Account | Global account selector with per-account data | `frontend/src/contexts/AccountContext.tsx` |
| Budget Groups | Hierarchical budget organization with roll-ups | `backend/app/services/budget_groups.py` |
| Sinking Funds | Annual/quarterly budgets with contribution tracking | `backend/app/services/budget.py` |
| E2E Tests | Playwright browser tests with mocked API | `frontend/e2e/app.spec.ts` |

### Known Issues

See [docs/CodeReview/CODE_REVIEW_CONSOLIDATED.md](docs/CodeReview/CODE_REVIEW_CONSOLIDATED.md) for all findings:
- **34 of 38 items DONE**
- **5 LOW items remaining:** L5 (rate limiting), L6 (input validation), L8 (structured logging), L15 (API versioning), L16 (health checks)

See [TRD Section 13](docs/TRD.md#13-implementation-phases) for detailed phase breakdown.

---

## Troubleshooting

### Bugs Fixed (2026-01-19)

| Issue | Root Cause | Fix |
|-------|------------|-----|
| Connect button not working | API URL doubled (`/api/api/v1/...`) | Removed `VITE_API_URL: /api` build arg from docker-compose.yml |
| Login endpoint mismatch | Backend returned redirect, frontend expected JSON | Changed `auth.py` to return `{"url": "..."}` |
| APScheduler import error | APScheduler 4.x has different API | Pinned to `apscheduler>=3.10.0,<4.0.0` |

### Monzo Strong Customer Authentication (SCA)

After OAuth authentication, Monzo requires **in-app approval** before API calls work:

1. OAuth flow completes successfully (tokens stored)
2. First API call to `/accounts` returns **403 Forbidden**
3. User must open **Monzo mobile app** and approve the connection
4. After approval, sync works normally

**Symptom:** Sync status shows `"error": "Client error '403 Forbidden' for url 'https://api.monzo.com/accounts'"`

**Fix:** Open Monzo app → Approve "personal_analysis" connection → Sync again

### Docker Build Notes

- Frontend uses `VITE_API_URL` at build time (not runtime)
- Empty `VITE_API_URL` means endpoints in `api.ts` are used as-is (`/api/v1/...`)
- Nginx proxies `/api/` to backend at `http://backend:8000/api/`
- Port 8000 is exposed for direct backend access during development
