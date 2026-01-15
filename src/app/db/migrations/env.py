import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.core.settings import get_settings
from app.db.model_base import AppBase

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

target_metadata = AppBase.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    assert url is not None, "sqlalchemy.url must be set"
    assert isinstance(url, str), "sqlalchemy.url must be a string"
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_schemas=True,
        version_table_schema=settings.DB_SCHEMA,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Purpose: Configure Alembic context and run migrations.

    Inputs: SQLAlchemy Connection.
    Returns: None.
    Preconditions: connection and metadata are valid.
    Postconditions: Migrations executed in a transaction.
    Side effects: Alters database schema.
    """
    assert connection is not None, "connection must be provided"
    assert target_metadata is not None, "target_metadata must be set"
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        include_schemas=True,
        version_table_schema=settings.DB_SCHEMA,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Purpose: Run migrations using an async engine.

    Inputs: None.
    Returns: None.
    Preconditions: Alembic config is available.
    Postconditions: Migrations are applied.
    Side effects: Alters database schema.
    """
    assert config.config_ini_section != "", "config_ini_section must not be empty"
    assert isinstance(settings.DB_SCHEMA, str), "DB_SCHEMA must be a string"
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Purpose: Run migrations in online mode.

    Inputs: None.
    Returns: None.
    Preconditions: DB settings are valid.
    Postconditions: Async migrations executed.
    Side effects: Alters database schema.
    """
    assert settings.DB_SCHEMA != "", "DB_SCHEMA must not be empty"
    assert isinstance(settings.DATABASE_URL, str), "DATABASE_URL must be a string"
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
