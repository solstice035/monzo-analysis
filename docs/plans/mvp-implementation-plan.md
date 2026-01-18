# MVP Implementation Plan

Using TDD to build Monzo Analysis MVP.

## Phase 1: Foundation
- [x] Backend scaffold - FastAPI project structure, pyproject.toml, dependencies
- [ ] Database models - SQLAlchemy models for all tables
- [ ] Alembic migrations setup and initial migration
- [ ] Config module with Pydantic settings
- [ ] Monzo OAuth flow (login, callback, token refresh)
- [ ] Basic transaction sync service

## Phase 2: Core Features
- [ ] Rules engine for categorisation
- [ ] Budget tracking service
- [ ] Slack notifications service
- [ ] APScheduler integration for scheduled sync

## Phase 3: Dashboard
- [ ] Frontend scaffold - React, Vite, shadcn setup
- [ ] Dashboard view with summary cards
- [ ] Transactions view with filters
- [ ] Budgets CRUD UI
- [ ] Settings and rules management UI

## Phase 4: Polish
- [ ] Docker Compose setup
- [ ] End-to-end testing

## Commit Checkpoints

1. **Backend scaffold complete** - project structure, dependencies, config tests
2. **Database models complete** - all models with tests
3. **OAuth flow complete** - login, callback, token refresh working
4. **Sync service complete** - fetches and stores transactions
5. **Rules engine complete** - categorisation working
6. **Notifications complete** - Slack integration working
7. **Frontend scaffold complete** - basic React app
8. **Dashboard complete** - summary and transactions views
9. **Full CRUD complete** - budgets and rules management
10. **Docker ready** - docker-compose working
