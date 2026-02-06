"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.accounts import router as accounts_router
from app.api.auth import router as auth_router
from app.api.budget_groups import router as budget_groups_router
from app.api.budgets import router as budgets_router
from app.api.dashboard import router as dashboard_router
from app.api.pots import router as pots_router
from app.api.rules import router as rules_router
from app.api.sync import router as sync_router
from app.api.transactions import router as transactions_router
from app.config import Settings
from app.services.scheduler import create_scheduler, start_scheduler, stop_scheduler

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown."""
    # Startup - create and start the scheduler
    scheduler = create_scheduler()
    start_scheduler(scheduler)
    app.state.scheduler = scheduler
    logger.info("Application startup complete")

    yield

    # Shutdown - stop the scheduler
    stop_scheduler(scheduler)
    logger.info("Application shutdown complete")


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application."""
    if settings is None:
        settings = Settings()

    app = FastAPI(
        title="Monzo Analysis",
        description="Personal finance tracking and analytics using the Monzo API",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS middleware - origins configurable via CORS_ORIGINS env var
    origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Health check
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy"}

    # Include routers
    app.include_router(accounts_router, prefix="/api/v1")
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(transactions_router, prefix="/api/v1")
    app.include_router(budgets_router, prefix="/api/v1")
    app.include_router(budget_groups_router, prefix="/api/v1")
    app.include_router(pots_router, prefix="/api/v1")
    app.include_router(rules_router, prefix="/api/v1")
    app.include_router(sync_router, prefix="/api/v1")
    app.include_router(dashboard_router, prefix="/api/v1")

    return app


def get_application() -> FastAPI:
    """Get the FastAPI application instance."""
    return create_app()


# Create app at import - will require env vars
# For production, these should be set in the environment
# For testing, use create_app() directly with mocked settings
try:
    app = create_app()
except Exception:
    # Allow module to load even without env vars (for testing)
    app = None  # type: ignore
