from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager, suppress

from advanced_alchemy.extensions.fastapi import (
    AdvancedAlchemy,
    AsyncSessionConfig,
    SQLAlchemyAsyncConfig,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import get_settings

settings = get_settings()

sqlalchemy_config = SQLAlchemyAsyncConfig(
    connection_string=settings.DATABASE_URL,
    session_config=AsyncSessionConfig(expire_on_commit=False),
    create_all=False,
    commit_mode="autocommit",
)

alchemy = AdvancedAlchemy(config=sqlalchemy_config)


@asynccontextmanager
async def get_session_context() -> AsyncGenerator[AsyncSession, None]:
    """Context manager for non-FastAPI code (e.g., workers) using AdvancedAlchemy."""
    provide = alchemy.provide_session()
    gen = provide()
    session: AsyncSession | None = None
    try:
        session = await gen.__anext__()
        yield session
        await session.commit()
    except StopAsyncIteration:
        msg = "Failed to acquire session from AdvancedAlchemy provider"
        raise RuntimeError(msg)
    except Exception:
        if session is not None:
            await session.rollback()
        raise
    finally:
        with suppress(Exception):
            await gen.aclose()


def get_db_async_session() -> AsyncSession:
    """Generator function to provide async database sessions for non-FastAPI contexts.
    Use this in services, tools, and other non-endpoint code.
    """
    cfg = alchemy.get_async_config()
    AsyncSessionMaker = cfg.create_session_maker()
    return AsyncSessionMaker()
