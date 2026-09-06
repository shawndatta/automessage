from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def default_data_dir() -> Path:
    return Path.home() / ".automessage"


class Settings(BaseSettings):
    """Runtime settings. Secrets live in the encrypted DB store, not env."""

    model_config = SettingsConfigDict(
        env_prefix="AUTOMESSAGE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    data_dir: Path = Field(default_factory=default_data_dir)
    db_path: Path | None = None
    host: str = "127.0.0.1"
    port: int = 8741
    log_level: str = "INFO"
    open_browser: bool = True
    # When True (CLI: `automessage start default`), allow auto-login as the seeded default user.
    default_user_mode: bool = False
    session_ttl_hours: int = 720  # 30 days

    @property
    def resolved_db_path(self) -> Path:
        if self.db_path is not None:
            return self.db_path.expanduser().resolve()
        return (self.data_dir / "automessage.db").expanduser().resolve()

    @property
    def key_path(self) -> Path:
        return (self.data_dir / "secret.key").expanduser().resolve()

    @property
    def pid_path(self) -> Path:
        return (self.data_dir / "server.pid").expanduser().resolve()

    @property
    def database_url(self) -> str:
        # aiosqlite wants a filesystem path after sqlite+aiosqlite:///
        path = self.resolved_db_path.as_posix()
        return f"sqlite+aiosqlite:///{path}"

    def ensure_dirs(self) -> None:
        self.data_dir.expanduser().mkdir(parents=True, exist_ok=True)
        self.resolved_db_path.parent.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    return Settings()
