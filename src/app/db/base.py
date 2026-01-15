from contextlib import asynccontextmanager

from advanced_alchemy.extensions.fastapi import (
    AdvancedAlchemy,
    AsyncSessionConfig,
    SQLAlchemyAsyncConfig,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import get_settings

settings = get_settings()


def get_database_url() -> str:
    """Purpose: Provide the SQLAlchemy database URL from settings.

    Inputs: Settings instance (cached).
    Returns: Database URL string for AdvancedAlchemy.
    Preconditions: Settings must be initialized.
    Postconditions: URL is non-empty.
    Side effects: None.
    """
    assert settings is not None, "settings must be initialized"
    assert isinstance(settings.DATABASE_URL, str), "DATABASE_URL must be a string"
    return settings.DATABASE_URL


sqlalchemy_config = SQLAlchemyAsyncConfig(
    connection_string=get_database_url(),
    session_config=AsyncSessionConfig(expire_on_commit=False),
    create_all=False,
    commit_mode="autocommit",
)

alchemy = AdvancedAlchemy(config=sqlalchemy_config)


# 3. Define your helper context manager
@asynccontextmanager
async def async_session_context():
    """Purpose: Provide async DB sessions for non-FastAPI contexts.

    Inputs: None.
    Returns: AsyncSession context manager.
    Preconditions: AdvancedAlchemy is configured.
    Postconditions: Session is yielded and closed properly.
    Side effects: Opens and closes a DB session.
    """
    assert alchemy is not None, "alchemy must be initialized"
    assert settings is not None, "settings must be initialized"
    async with alchemy.with_async_session() as session:
        yield session


# @asynccontextmanager
# async def get_session_context() -> AsyncGenerator[AsyncSession, None]:
#     """Context manager for non-FastAPI code (e.g., workers) using AdvancedAlchemy."""
#     provide = alchemy.provide_session()
#     gen = provide()
#     session: AsyncSession | None = None
#     try:
#         session = await gen.__anext__()
#         yield session
#         await session.commit()
#     except StopAsyncIteration:
#         msg = "Failed to acquire session from AdvancedAlchemy provider"
#         raise RuntimeError(msg)
#     except Exception:
#         if session is not None:
#             await session.rollback()
#         raise
#     finally:
#         with suppress(Exception):
#             await gen.aclose()

async_session_maker = alchemy.get_async_config().create_session_maker()


def get_db_async_session() -> AsyncSession:
    """Purpose: Create an AsyncSession for non-FastAPI contexts.

    Inputs: None.
    Returns: AsyncSession instance.
    Preconditions: AdvancedAlchemy config must exist.
    Postconditions: AsyncSession is created.
    Side effects: Allocates a session object.
    """
    assert alchemy is not None, "alchemy must be initialized"
    assert settings is not None, "settings must be initialized"
    cfg = alchemy.get_async_config()
    AsyncSessionMaker = cfg.create_session_maker()
    return AsyncSessionMaker()
