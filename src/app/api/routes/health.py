from fastapi import APIRouter
from sqlalchemy import text

from app.api.deps import DatabaseSession
from app.core.settings import get_settings

router = APIRouter()
settings = get_settings()


@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
    }


@router.get("/health/db")
async def database_health_check(session: DatabaseSession):
    try:
        result = await session.execute(text("SELECT 1"))
        result.scalar_one()
        return {
            "status": "healthy",
            "database": "connected",
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
        }
