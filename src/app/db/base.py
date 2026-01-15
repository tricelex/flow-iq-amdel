from contextlib import asynccontextmanager
from urllib.parse import quote_plus

from advanced_alchemy.extensions.fastapi import (
    AdvancedAlchemy,
    AsyncSessionConfig,
    SQLAlchemyAsyncConfig,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import get_settings

settings = get_settings()


def build_azure_connection_string() -> str:
    """Build Azure SQL Database connection string with ODBC driver.

    Constructs the connection string from individual database settings fields.
    Format: mssql+aioodbc://user:password@server:port/database?driver=...&Encrypt=yes&...
    """
    # URL encode user and password to handle special characters
    user = quote_plus(settings.DB_USER)
    password = quote_plus(settings.DB_PASSWORD)

    # Build the base connection URL
    base_url = f"mssql+aioodbc://{user}:{password}@{settings.DB_SERVER}:{settings.DB_PORT}/{settings.DB_DATABASE}"

    # Build query parameters
    driver_param = f"driver={quote_plus(settings.DB_DRIVER)}"

    # Add additional Azure-specific connection parameters
    azure_params = [
        ("Encrypt", "yes"),
        ("TrustServerCertificate", "no"),
        ("Connection Timeout", "30"),
    ]

    param_parts = [driver_param]
    for key, value in azure_params:
        param_parts.append(f"{quote_plus(key)}={quote_plus(value)}")

    return f"{base_url}?{'&'.join(param_parts)}"


sqlalchemy_config = SQLAlchemyAsyncConfig(
    connection_string=build_azure_connection_string(),
    session_config=AsyncSessionConfig(expire_on_commit=False),
    create_all=False,
    commit_mode="autocommit",
)

alchemy = AdvancedAlchemy(config=sqlalchemy_config)


# 3. Define your helper context manager
@asynccontextmanager
async def async_session_context():
    """Generator function to provide async database sessions for non-FastAPI contexts."""
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
    """Generator function to provide async database sessions for non-FastAPI contexts.
    Use this in services, tools, and other non-endpoint code.
    """
    cfg = alchemy.get_async_config()
    AsyncSessionMaker = cfg.create_session_maker()
    return AsyncSessionMaker()
