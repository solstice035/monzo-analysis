# Technical Requirements Document (TRD)

## Monzo Analysis - Personal Finance Analytics

**Version:** 1.0
**Date:** 2026-01-18
**PRD Reference:** [docs/PRD.md](PRD.md)

---

## 1. Overview

This document defines HOW to build the Monzo Analysis system specified in the PRD. It covers architecture, data model, API design, and implementation approach for a personal MVP running on Unraid.

### Design Principles

- **Lightweight MVP** - Personal use only, no multi-tenancy
- **Containerised** - Docker Compose for portability (Unraid → DigitalOcean)
- **Robust** - Should run unattended with minimal intervention (~quarterly re-auth)

---

## 2. Architecture

### 2.1 System Overview

Three-container Docker Compose setup:

```
┌─────────────────────────────────────────────────────┐
│                     Unraid                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │   monzo-api │  │ monzo-web   │  │  postgres   │  │
│  │  (FastAPI)  │  │   (React)   │  │   (data)    │  │
│  │  Port 8000  │  │  Port 3000  │  │  Port 5432  │  │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  │
│         │                │                │         │
│         └────────────────┴────────────────┘         │
└─────────────────────────────────────────────────────┘
         │
         ▼
   ┌─────────────┐
   │ Slack #monzo│
   └─────────────┘
```

| Container | Purpose | Port |
|-----------|---------|------|
| `monzo-api` | FastAPI backend - OAuth, sync, rules, notifications | 8000 |
| `monzo-web` | React dashboard - view data, configure rules/budgets | 3000 |
| `postgres` | Persistent storage | 5432 |

### 2.2 Tech Stack

#### Backend (Python 3.12+)

| Component | Version | Purpose |
|-----------|---------|---------|
| FastAPI | 0.128.x | Async web framework |
| SQLAlchemy | 2.1.x | Async ORM with PostgreSQL |
| Alembic | latest | Database migrations |
| APScheduler | 4.x | Scheduled sync jobs (native async, FastAPI lifespan) |
| httpx | latest | Async HTTP client for Monzo API |
| asyncpg | latest | Async PostgreSQL driver |
| pydantic | 2.x | Request/response validation |
| pydantic-settings | latest | Environment configuration |

#### Frontend (Node 20+)

| Component | Version | Purpose |
|-----------|---------|---------|
| React | 18.x+ | UI framework |
| Vite | 7.x | Build tool |
| shadcn/ui | latest | Component library |
| Tailwind CSS | 3.x | Styling |
| TanStack Query | 5.x | Data fetching and caching |
| Recharts | latest | Dashboard charts |

#### Infrastructure

| Component | Version | Purpose |
|-----------|---------|---------|
| PostgreSQL | 16+ | Primary database |
| Docker | latest | Containerisation |
| Docker Compose | latest | Multi-container orchestration |

---

## 3. Data Model

### 3.1 Database Schema

```sql
-- Monzo accounts (retail, joint)
CREATE TABLE accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    monzo_id VARCHAR(255) UNIQUE NOT NULL,
    type VARCHAR(50) NOT NULL,  -- 'uk_retail', 'uk_retail_joint'
    name VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Transaction history
CREATE TABLE transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    monzo_id VARCHAR(255) UNIQUE NOT NULL,
    account_id UUID REFERENCES accounts(id),
    amount INTEGER NOT NULL,  -- pence, negative = spend
    merchant_name VARCHAR(255),
    monzo_category VARCHAR(100),
    custom_category VARCHAR(100),
    created_at TIMESTAMP NOT NULL,
    settled_at TIMESTAMP,
    raw_payload JSONB,  -- Full Monzo response for ML training
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Savings pots
CREATE TABLE pots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    monzo_id VARCHAR(255) UNIQUE NOT NULL,
    account_id UUID REFERENCES accounts(id),
    name VARCHAR(255) NOT NULL,
    balance INTEGER NOT NULL,  -- pence
    deleted BOOLEAN DEFAULT FALSE,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Budget definitions
CREATE TABLE budgets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category VARCHAR(100) NOT NULL,
    amount INTEGER NOT NULL,  -- pence
    period VARCHAR(20) NOT NULL,  -- 'weekly', 'monthly'
    start_day INTEGER DEFAULT 1,  -- 1-28, day of month/week
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Category rules (auto-categorisation)
CREATE TABLE category_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    conditions JSONB NOT NULL,  -- {"merchant_contains": "Tesco", "amount_gt": 8000}
    target_category VARCHAR(100) NOT NULL,
    priority INTEGER DEFAULT 0,  -- Higher = checked first
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Sync history
CREATE TABLE sync_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    status VARCHAR(50) NOT NULL,  -- 'running', 'success', 'failed'
    transactions_synced INTEGER DEFAULT 0,
    error TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- OAuth tokens (single row, personal use)
CREATE TABLE auth (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    access_token TEXT NOT NULL,
    refresh_token TEXT NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- App settings
CREATE TABLE settings (
    key VARCHAR(100) PRIMARY KEY,
    value JSONB NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_transactions_account ON transactions(account_id);
CREATE INDEX idx_transactions_created ON transactions(created_at);
CREATE INDEX idx_transactions_category ON transactions(custom_category);
CREATE INDEX idx_category_rules_priority ON category_rules(priority DESC);
```

### 3.2 Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| `raw_payload` as JSONB | Preserves full Monzo response for future ML training |
| `custom_category` separate from `monzo_category` | Enables comparison and learning |
| `conditions` as JSONB | Flexible rule format without schema migrations |
| Single `auth` row | Personal use, no user management needed |
| `settings` key-value table | Flexible config without migrations |

---

## 4. API Design

### 4.1 Endpoints

#### Authentication & Sync

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/auth/login` | Redirect to Monzo OAuth |
| `GET` | `/auth/callback` | Handle OAuth callback |
| `GET` | `/auth/status` | Check auth status |
| `POST` | `/sync/trigger` | Manual sync trigger |
| `GET` | `/sync/status` | Current sync state |

#### Data (Read)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/accounts` | List connected accounts |
| `GET` | `/transactions` | Paginated transactions with filters |
| `GET` | `/transactions/{id}` | Single transaction detail |
| `GET` | `/pots` | List pots with balances |
| `GET` | `/stats/summary` | Dashboard summary |
| `GET` | `/stats/by-category` | Spending by category |
| `GET` | `/stats/trends` | Historical trends |

#### Configuration (CRUD)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET/POST` | `/budgets` | List/create budgets |
| `PUT/DELETE` | `/budgets/{id}` | Update/delete budget |
| `GET/POST` | `/rules` | List/create rules |
| `PUT/DELETE` | `/rules/{id}` | Update/delete rule |
| `PUT` | `/rules/reorder` | Update rule priorities |
| `PUT` | `/transactions/{id}/category` | Override transaction category |
| `GET/PUT` | `/settings` | App preferences |

### 4.2 Response Format

```json
{
  "data": { ... },
  "meta": {
    "page": 1,
    "per_page": 50,
    "total": 1234
  }
}
```

Error responses:
```json
{
  "error": {
    "code": "AUTH_EXPIRED",
    "message": "Monzo authentication has expired",
    "action": "Re-authenticate at /auth/login"
  }
}
```

### 4.3 Authentication

- Simple session token stored in HTTP-only cookie
- No complex auth needed (personal use, single user)
- Protected by network (Unraid local or VPN)

---

## 5. Sync Flow

### 5.1 Scheduled Sync Process

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Scheduler  │────▶│  Monzo API  │────▶│  Database   │
│ (APScheduler)│     │   Client    │     │  (Postgres) │
└─────────────┘     └──────┬──────┘     └──────┬──────┘
                           │                   │
                           ▼                   ▼
                    ┌─────────────┐     ┌─────────────┐
                    │Rules Engine │     │   Slack     │
                    │(categorise) │     │  Notifier   │
                    └─────────────┘     └─────────────┘
```

**Steps:**

1. **Check token** - Refresh if expired (automatic)
2. **Fetch transactions** - From `last_sync_timestamp`, paginated
3. **Fetch balances** - Current account + pot balances
4. **Apply rules** - Run each new transaction through rules engine
5. **Store** - Upsert transactions (idempotent on `monzo_id`)
6. **Analyse** - Calculate budget usage, detect anomalies
7. **Notify** - Send digest/alerts to Slack
8. **Log** - Record sync result

### 5.2 Token Refresh

| Token Type | Lifespan | Renewal |
|------------|----------|---------|
| Access token | ~24 hours | Automatic via refresh token |
| Refresh token | ~90 days | Manual re-auth required (SCA) |

**Re-auth flow:**
1. Sync detects unrecoverable 401
2. Slack alert with re-authenticate link
3. User clicks, completes OAuth
4. Sync resumes

### 5.3 Error Handling

| Error | Action |
|-------|--------|
| Token expired (refreshable) | Auto-refresh, continue |
| Token expired (SCA) | Slack alert, mark auth expired |
| Rate limited | Back off, partial sync is fine |
| Network failure | Log error, Slack alert, retry next run |

---

## 6. Rules Engine

### 6.1 Categorisation Priority

1. **User override** - Manual category on transaction
2. **Custom rules** - Match against defined rules (by priority)
3. **Monzo category** - Fall back to Monzo's assignment

### 6.2 Rule Structure

```json
{
  "name": "Big weekly shop",
  "conditions": {
    "merchant_contains": "Tesco",
    "amount_gt": 8000
  },
  "target_category": "groceries-big-shop",
  "priority": 10
}
```

### 6.3 Supported Conditions

| Condition | Type | Example |
|-----------|------|---------|
| `merchant_contains` | string | `"Tesco"` |
| `merchant_exact` | string | `"TfL"` |
| `amount_gt` | integer (pence) | `8000` |
| `amount_lt` | integer (pence) | `500` |
| `amount_between` | [min, max] | `[5000, 10000]` |
| `day_of_week` | [days] | `[6, 7]` (weekend) |
| `category_is` | string | `"eating_out"` |

**Logic:** All conditions in a rule must match (AND). For OR, create separate rules.

---

## 7. Notifications

### 7.1 Slack Configuration

- Single channel: `#monzo`
- Webhook URL stored in settings
- Three message types with distinct formatting

### 7.2 Message Types

**Daily Digest:**
```
📊 Daily Summary - 18 Jan 2026

Spent today: £45.20
This week: £234.50 / £400 budget (59%)
This month: £1,245.80 / £2,000 budget (62%)

Top categories:
• Groceries: £89.40
• Transport: £52.00
• Eating out: £43.10

3 transactions synced ✓
```

**Threshold Alert:**
```
⚠️ Budget Alert

Eating out: £195 / £200 (98%)
You have £5 left for the month.
```

**System Health:**
```
🔐 Monzo auth expired
Re-authenticate: https://your-server:8000/auth/login
```

---

## 8. Frontend Dashboard

### 8.1 Views

| View | Purpose |
|------|---------|
| **Dashboard** | Summary cards, budget progress, recent transactions, quick stats |
| **Transactions** | Paginated list, filters, category override, bulk actions |
| **Budgets** | CRUD budgets, progress indicators, historical comparison |
| **Settings** | Rules management, sync controls, preferences, auth status |

### 8.2 Settings Preferences

- Sync frequency (hours)
- Slack webhook URL
- Notification toggles (digest, alerts, system)
- Budget reset day (1-28)

### 8.3 Component Structure

```
src/
├── components/
│   ├── ui/              # shadcn components
│   ├── TransactionList.tsx
│   ├── BudgetCard.tsx
│   ├── RuleEditor.tsx
│   └── SummaryCard.tsx
├── pages/
│   ├── Dashboard.tsx
│   ├── Transactions.tsx
│   ├── Budgets.tsx
│   └── Settings.tsx
├── hooks/
│   └── useApi.ts        # TanStack Query hooks
└── lib/
    ├── api.ts           # API client
    └── utils.ts         # Helpers
```

---

## 9. Deployment

### 9.1 Docker Compose

```yaml
version: '3.8'

services:
  api:
    build: ./backend
    container_name: monzo-api
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://monzo:${DB_PASSWORD}@postgres/monzo
      - MONZO_CLIENT_ID=${MONZO_CLIENT_ID}
      - MONZO_CLIENT_SECRET=${MONZO_CLIENT_SECRET}
      - SLACK_WEBHOOK_URL=${SLACK_WEBHOOK_URL}
      - SECRET_KEY=${SECRET_KEY}
    depends_on:
      - postgres
    restart: unless-stopped

  web:
    build: ./frontend
    container_name: monzo-web
    ports:
      - "3000:3000"
    environment:
      - VITE_API_URL=http://localhost:8000
    depends_on:
      - api
    restart: unless-stopped

  postgres:
    image: postgres:16-alpine
    container_name: monzo-postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_USER=monzo
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_DB=monzo
    restart: unless-stopped

volumes:
  postgres_data:
```

### 9.2 Environment Variables

```bash
# .env (not committed)
DB_PASSWORD=secure-password-here
MONZO_CLIENT_ID=oauth-client-id
MONZO_CLIENT_SECRET=oauth-client-secret
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
SECRET_KEY=random-secret-for-sessions
```

### 9.3 Unraid Deployment

1. Copy project to Unraid share
2. Create `.env` with secrets
3. `docker-compose up -d`
4. Access dashboard at `http://unraid-ip:3000`

### 9.4 Future: DigitalOcean Migration

Same Docker Compose, different host:
1. Create Droplet with Docker
2. Clone repo, add `.env`
3. Set up reverse proxy (Caddy/Nginx) for HTTPS
4. Point domain, deploy

---

## 10. Security

### 10.1 Secrets Management

| Secret | Storage |
|--------|---------|
| Monzo OAuth credentials | Environment variables |
| Slack webhook URL | Database (settings table) |
| OAuth tokens | Database (encrypted at rest by Postgres) |
| Session secret | Environment variable |

### 10.2 Network Security

- **Unraid:** Accessible only on local network (or via VPN)
- **DigitalOcean:** HTTPS via reverse proxy, firewall rules
- No public exposure of OAuth callback without HTTPS

### 10.3 Data Security

- No sensitive data in logs
- Tokens stored in database, not localStorage
- HTTP-only cookies for session

---

## 11. Testing

### 11.1 Backend Testing

```bash
pytest tests/ --cov=app --cov-report=term-missing
```

| Type | Coverage |
|------|----------|
| Unit | Rules engine, categorisation logic |
| Integration | API endpoints, database operations |
| Mock | Monzo API responses |

### 11.2 Frontend Testing

```bash
npm run test
```

| Type | Coverage |
|------|----------|
| Component | React Testing Library |
| Integration | Key user flows |

### 11.3 Manual Testing

- OAuth flow end-to-end
- Sync with real Monzo data
- Slack notifications

---

## 12. Project Structure

```
monzo-analysis/
├── CLAUDE.md
├── docker-compose.yml
├── .env.example
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── alembic/
│   │   └── versions/
│   ├── app/
│   │   ├── main.py           # FastAPI app + lifespan
│   │   ├── config.py         # Pydantic settings
│   │   ├── database.py       # SQLAlchemy setup
│   │   ├── api/
│   │   │   ├── auth.py
│   │   │   ├── sync.py
│   │   │   ├── transactions.py
│   │   │   ├── budgets.py
│   │   │   ├── rules.py
│   │   │   └── settings.py
│   │   ├── models/
│   │   │   └── *.py          # SQLAlchemy models
│   │   ├── services/
│   │   │   ├── monzo.py      # Monzo API client
│   │   │   ├── sync.py       # Sync orchestration
│   │   │   ├── rules.py      # Rules engine
│   │   │   ├── budget.py     # Budget calculations
│   │   │   └── slack.py      # Slack notifications
│   │   └── schemas/
│   │       └── *.py          # Pydantic schemas
│   └── tests/
│       └── *.py
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   └── lib/
│   └── public/
└── docs/
    ├── PRD.md
    ├── TRD.md
    └── api-reference/
```

---

## 13. Implementation Phases

### Phase 1: Foundation
- [ ] Backend scaffold (FastAPI, SQLAlchemy, Alembic)
- [ ] Database models and migrations
- [ ] Monzo OAuth flow
- [ ] Basic transaction sync

### Phase 2: Core Features
- [ ] Rules engine
- [ ] Budget tracking
- [ ] Slack notifications
- [ ] Scheduled sync (APScheduler)

### Phase 3: Dashboard
- [ ] Frontend scaffold (React, Vite, shadcn)
- [ ] Dashboard view
- [ ] Transactions view
- [ ] Budgets CRUD
- [ ] Settings + rules management

### Phase 4: Polish
- [ ] Error handling and edge cases
- [ ] Testing
- [ ] Docker Compose setup
- [ ] Documentation

---

## Appendix A: Monzo API Reference

See [docs/api-reference/](api-reference/) for full Monzo API documentation.

Key endpoints used:
- `GET /accounts` - List accounts
- `GET /balance` - Account balance
- `GET /pots` - Savings pots
- `GET /transactions` - Fetch transactions
- `PATCH /transactions/{id}` - Add metadata

## Appendix B: Category Mapping

Default Monzo categories:
```
general | eating_out | expenses | transport | cash
bills | entertainment | shopping | holidays | groceries
```

Custom categories can extend this list via budgets and rules.
