import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from prometheus_fastapi_instrumentator import Instrumentator

from app.core.settings import get_settings


def _add_cors_middleware(app: FastAPI) -> None:
    """Add CORS Middleware."""
    app.add_middleware(CORSMiddleware, allow_origins=["*"])


def _add_prometheus_middleware(app: FastAPI) -> None:
    """Add Prometheus Middleware."""
    settings = get_settings()
    if not settings.prometheus.enabled:
        return
    instrumenter = Instrumentator().instrument(app)
    instrumenter.expose(app)


def _add_logfire_middleware(app: FastAPI) -> None:
    """Add Logfire Middleware."""
    import logfire

    settings = get_settings()
    if not settings.logfire.enabled:
        return
    if not settings.logfire.write_token:
        logger.warning("Logfire is enabled but no write token is provided. Skipping Logfire middleware.")
        return
    logfire.configure(
        token=settings.logfire.write_token,
        environment=settings.env,
        send_to_logfire="if-token-present",
        service_name=settings.PROJECT_NAME.lower().replace(" ", "-"),
    )
    logfire.instrument_fastapi(app, capture_headers=True)
    logfire.instrument_asyncpg()
    logfire.instrument_system_metrics()
    # Configure loguru with both console and Logfire handlers
    logger.configure(
        handlers=[
            {
                "sink": sys.stdout,
                "level": "INFO",
            },
            logfire.loguru_handler(),
        ]
    )


def add_middleware(app: FastAPI) -> None:
    """Add all middlewares."""
    _add_cors_middleware(app)
    _add_prometheus_middleware(app)
    _add_logfire_middleware(app)
