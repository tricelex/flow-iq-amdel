import pathlib
from functools import lru_cache

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


def get_env_file() -> pathlib.Path:
    """Determine which .env file to load based on environment."""
    env_file = ".env"
    project_root = pathlib.Path(__file__).parent.parent.parent.parent
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

    # DATABASE_URL: str = "mssql+aioodbc://user:password@server.database.windows.net:1433/database"
    DB_DRIVER: str = "ODBC+Driver+18+for+SQL+Server"
    DB_PORT: int = 1433
    DB_DATABASE: str = "database"
    DB_USER: str = "user"
    DB_PASSWORD: str = "password"
    DB_SERVER: str = "server.database.windows.net"

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


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
