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
| Visual identity | Bold dark mode | Monzo hot coral on navy; premium analytics feel |
| Display font | Bebas Neue | Striking condensed headlines for big numbers |
| Body font | Outfit | Modern geometric sans, friendly yet professional |
| Mono font | Space Mono | Financial data and technical values |

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
| Visual identity | ✅ Complete | 2026-01-18 |
| Phase 1: Foundation | ✅ Complete | 2026-01-18 |
| Phase 2: Core Features | ✅ Complete | 2026-01-18 |
| Phase 3: Dashboard | ✅ Complete | 2026-01-18 |
| Phase 4: Docker Setup | ✅ Complete | 2026-01-18 |
| MVP implementation | ✅ Complete | 2026-01-18 |

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

1. **Monzo Developer Account** - Register app at https://developers.monzo.com
2. **Configure `.env`** - Add Monzo OAuth credentials, Slack webhook URL
3. **Deploy to Unraid** - Copy `docker-compose.yml` and `.env` to server
4. **First OAuth** - Visit http://localhost:8000/api/v1/auth/login to authenticate
5. **Monitor** - Check Slack channel for daily summaries

See [TRD Section 13](docs/TRD.md#13-implementation-phases) for detailed phase breakdown.
