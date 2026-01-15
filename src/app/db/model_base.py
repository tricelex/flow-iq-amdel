"""Application SQLAlchemy base models with schema and prefix isolation."""

from advanced_alchemy.base import UUIDAuditBase
from sqlalchemy.orm import declared_attr

from app.core.settings import get_settings

settings = get_settings()


class AppBase(UUIDAuditBase):
    """Purpose: Base for app-owned models with schema and prefix isolation.

    Inputs: None.
    Returns: Declarative base class for SQLAlchemy models.
    Preconditions: Settings must be initialized.
    Postconditions: Tables created from this base use configured schema/prefix.
    Side effects: None.
    """

    __abstract__ = True
    __table_args__ = {"schema": settings.DB_SCHEMA}

    @declared_attr
    def __tablename__(cls) -> str:
        """Purpose: Provide a default prefixed table name for models.

        Inputs: Model class (cls).
        Returns: Table name with configured prefix.
        Preconditions: Prefix must be non-empty.
        Postconditions: Returned name is non-empty.
        Side effects: None.
        """
        assert settings.DB_TABLE_PREFIX != "", "DB_TABLE_PREFIX must not be empty"
        assert cls.__name__ != "", "class name must not be empty"
        explicit_name = cls.__dict__.get("__tablename__")
        if isinstance(explicit_name, str) and explicit_name != "":
            return explicit_name
        return f"{settings.DB_TABLE_PREFIX}{cls.__name__.lower()}"
