from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[3] / ".env",
        extra="ignore",
    )

    app_name: str = Field(default="Booking service", alias="APP_NAME")
    app_host: str = Field(default="127.0.0.1", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")
    debug: bool = Field(default=False, alias="DEBUG")

    db_password: str | None = Field(default=None, alias="DB_PASSWORD")
    db_user: str | None = Field(default=None, alias="DB_USER")
    db_name: str = Field(default="db.sqlite3", alias="DB_NAME")
    db_host: str | None = Field(default=None, alias="DB_HOST")
    db_port: str | None = Field(default=None, alias="DB_PORT")
    db_engine: str = Field(default="sqlite+aiosqlite", alias="DB_ENGINE")

    @property
    def database_url(self) -> str:

        if self.db_engine == "sqlite+aiosqlite":
            db_path = BASE_DIR / "data" / self.db_name
            return f"{self.db_engine}:///{db_path.as_posix()}"

        return f"{self.db_engine}://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"


settings: Settings | None = None


def get_settings() -> Settings:
    """Возвращает глобальные настройки проекта
    """
    global settings

    if not settings:
        settings = Settings()

    return settings
