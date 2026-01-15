import pathlib
from functools import lru_cache
from urllib.parse import quote_plus

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


def get_env_file() -> pathlib.Path:
    """Purpose: Resolve the .env path used by Settings.

    Inputs: none.
    Returns: Absolute Path to the .env file.
    Preconditions: Project root must be resolvable.
    Postconditions: Returned path is absolute and non-empty.
    Side effects: None.
    """
    assert pathlib.Path(__file__).exists(), "settings.py path must exist"
    assert pathlib.Path(__file__).is_file(), "settings.py must be a file"
    env_file = ".env"
    project_root = pathlib.Path(__file__).parent.parent.parent.parent
    assert project_root.is_dir(), "project root must be a directory"
    assert env_file != "", "env filename must not be empty"
    return project_root / env_file


DOTENV = get_env_file()


class PrometheusSettings(BaseModel):
    enabled: bool = True


class LogfireSettings(BaseModel):
    enabled: bool = False
    write_token: str | None = None


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(DOTENV),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_nested_delimiter="__",
    )

    PROJECT_NAME: str = "FastAPI Application"
    VERSION: str = "0.1.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"

    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ALLOWED_HOSTS: list[str] = ["http://localhost:8000", "http://localhost:3000"]

    DB_DRIVER: str = "ODBC Driver 18 for SQL Server"
    DB_PORT: int = 1433
    DB_DATABASE: str = "database"
    DB_USER: str = "user"
    DB_PASSWORD: str = ""
    DB_SERVER: str = "server.database.windows.net"
    DB_SCHEMA: str = "app"
    DB_TABLE_PREFIX: str = "app_"

    LOG_LEVEL: str = "INFO"

    # Observability
    prometheus: PrometheusSettings = PrometheusSettings()
    logfire: LogfireSettings = LogfireSettings()

    OPENAI_API_KEY: str = "sk-proj-1234567890"

    @property
    def host(self) -> str:
        return self.HOST

    @property
    def port(self) -> int:
        return self.PORT

    @property
    def log_level(self) -> str:
        return self.LOG_LEVEL.lower()

    @property
    def reload(self) -> bool:
        return self.DEBUG

    @property
    def env(self) -> str:
        return self.ENVIRONMENT

    @property
    def debug(self) -> bool:
        return self.DEBUG

    @property
    def DATABASE_URL(self) -> str:
        """Purpose: Build a SQL Server connection URL for async usage.

        Inputs: Settings DB fields.
        Returns: A SQLAlchemy-compatible database URL.
        Preconditions: DB fields are non-empty and port is valid.
        Postconditions: Returned URL is non-empty and contains driver param.
        Side effects: None.
        """
        assert isinstance(self.DB_PORT, int), "DB_PORT must be an int"
        assert self.DB_PORT > 0, "DB_PORT must be positive"
        return self._build_database_url()

    def _build_database_url(self) -> str:
        """Purpose: Build the Azure SQL ODBC connection string.

        Inputs: DB settings fields on this instance.
        Returns: SQLAlchemy async connection string.
        Preconditions: DB fields are non-empty.
        Postconditions: URL includes driver and encryption settings.
        Side effects: None.
        """
        assert self.DB_USER != "", "DB_USER must not be empty"
        assert self.DB_PASSWORD != "", "DB_PASSWORD must not be empty"
        if self.DB_SERVER == "" or self.DB_DATABASE == "":
            raise ValueError("DB_SERVER and DB_DATABASE must be set")
        user = quote_plus(self.DB_USER)
        password = quote_plus(self.DB_PASSWORD)
        base_url = f"mssql+aioodbc://{user}:{password}@{self.DB_SERVER}:{self.DB_PORT}/{self.DB_DATABASE}"
        driver_param = f"driver={quote_plus(self.DB_DRIVER)}"
        azure_params = [
            ("Encrypt", "yes"),
            ("TrustServerCertificate", "no"),
            ("Connection Timeout", "30"),
        ]
        assert len(azure_params) == 3, "azure_params must have 3 entries"
        assert azure_params[0][0] != "", "azure_params must be non-empty"
        param_parts = [
            driver_param,
            f"{quote_plus(azure_params[0][0])}={quote_plus(azure_params[0][1])}",
            f"{quote_plus(azure_params[1][0])}={quote_plus(azure_params[1][1])}",
            f"{quote_plus(azure_params[2][0])}={quote_plus(azure_params[2][1])}",
        ]
        return f"{base_url}?{'&'.join(param_parts)}"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
