"""Credit Recommendation Engine — FastAPI application entry point."""

import logging
import os
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from credit_engine import __version__
from credit_engine.api import router
from credit_engine.api.routes import member_router

logger = logging.getLogger(__name__)


def _configure_logging() -> None:
    """Set up structured logging for the entire application.

    Log level from ``CREDIT_ENGINE_LOG_LEVEL`` env var (default: ``INFO``).
    Format includes timestamp, level, module, and message for full traceability.
    """
    level_name = os.environ.get("CREDIT_ENGINE_LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
        force=True,
    )
    logger.info("Logging configured at %s level", level_name)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan: wire the database when one is configured.

    If ``CREDIT_ENGINE_DATABASE_URL`` is set (e.g. the Azure SQL Server),
    the worker's person repository and outbox are swapped from the demo
    stand-ins to the SQL implementations at startup — no other code
    changes. Unset, the app runs fully in-memory (demo personas).
    """
    logger.info("Starting Credit Recommendation Engine v%s", __version__)

    from credit_engine.config import load_env
    from credit_engine.database.connection import DATABASE_URL_ENV_VAR

    load_env()
    url = os.environ.get(DATABASE_URL_ENV_VAR)
    if url:
        from credit_engine.database import SqlBatchRepository, SqlOutbox, SqlPersonRepository, build_engine, create_session_factory
        from credit_engine.worker import service

        factory = create_session_factory(build_engine(url))
        service.configure(
            repository=SqlPersonRepository(factory),
            outbox=SqlOutbox(factory),
            batch_repository=SqlBatchRepository(factory),
        )
        logger.info("Database wired from %s (host: %s)", DATABASE_URL_ENV_VAR, url.split("@")[-1].split("/")[0])
    else:
        logger.info("No database URL configured — running with in-memory demo data")

    yield

    logger.info("Shutting down Credit Recommendation Engine v%s", __version__)


_configure_logging()

app = FastAPI(
    title="Credit Recommendation Engine",
    description="Async ML pipeline for personalized credit product recommendations",
    version=__version__,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.include_router(member_router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Return service health status and version."""
    logger.debug("Health check requested")
    return {"status": "ok", "version": __version__}
