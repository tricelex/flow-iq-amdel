from typing import Any

from fastapi import APIRouter
from sqlalchemy import text

from app.api.deps import DatabaseSession
from app.core.settings import get_settings
from app.infra.cube.cube_client import get_cube_client
from app.core.logging import get_logger

router = APIRouter()
settings = get_settings()
logger = get_logger(__name__)


@router.get("/health")
async def health_check() -> dict[str, Any]:
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
    }


@router.get("/health/db")
async def database_health_check(session: DatabaseSession) -> dict[str, Any]:
    """Database connectivity health check."""
    try:
        result = await session.execute(text("SELECT 1"))
        result.scalar_one()
        return {
            "status": "healthy",
            "database": "connected",
        }
    except Exception as e:
        logger.exception("database_health_check_failed", error=str(e))
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
        }


@router.get("/health/cube")
async def cube_health_check() -> dict[str, Any]:
    """Cube.js semantic layer health check."""
    try:
        cube = get_cube_client()

        # Try to fetch metadata as a health check
        meta = await cube.get_meta()
        cube_count = len(meta.get("cubes", []))

        return {
            "status": "healthy",
            "cube": "connected",
            "cubes_available": cube_count,
            "api_url": settings.CUBE_API_URL,
        }

    except Exception as e:
        logger.exception("cube_health_check_failed", error=str(e))
        return {
            "status": "unhealthy",
            "cube": "disconnected",
            "error": str(e),
            "api_url": settings.CUBE_API_URL,
        }


@router.get("/health/all")
async def full_health_check(session: DatabaseSession) -> dict[str, Any]:
    """Comprehensive health check for all services."""
    # Check database
    db_status = "healthy"
    db_error = None
    try:
        result = await session.execute(text("SELECT 1"))
        result.scalar_one()
    except Exception as e:
        db_status = "unhealthy"
        db_error = str(e)
        logger.exception("database_health_check_failed", error=str(e))

    # Check Cube.js
    cube_status = "healthy"
    cube_error = None
    cube_count = 0
    try:
        cube = get_cube_client()
        meta = await cube.get_meta()
        cube_count = len(meta.get("cubes", []))
    except Exception as e:
        cube_status = "unhealthy"
        cube_error = str(e)
        logger.exception("cube_health_check_failed", error=str(e))

    # Overall status
    overall_status = "healthy" if db_status == "healthy" and cube_status == "healthy" else "degraded"

    return {
        "status": overall_status,
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "components": {
            "database": {
                "status": db_status,
                "error": db_error,
            },
            "cube": {
                "status": cube_status,
                "cubes_available": cube_count,
                "error": cube_error,
            },
        },
    }
