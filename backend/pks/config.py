"""Application configuration.

Settings are loaded from environment variables (optionally via a `.env` file
in the backend directory). All paths default to a local `./data` directory so
the app runs out of the box with zero configuration.
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="PKS_", env_file=".env", extra="ignore")

    # Storage
    data_dir: Path = Path("data")

    # Server
    host: str = "127.0.0.1"
    port: int = 8000

    # Pipeline worker
    worker_poll_interval: float = 0.5

    # AI provider tiers (used from Milestone 3 onward).
    # Heavy: ingestion-time extraction. Fast: chat / navigation.
    heavy_model: str = "claude-opus-4-8"
    fast_model: str = "claude-haiku-4-5"

    @property
    def db_path(self) -> Path:
        return self.data_dir / "pks.db"

    @property
    def resources_dir(self) -> Path:
        """Store for original uploaded resources (spec: originals always remain available)."""
        return self.data_dir / "resources"


@lru_cache
def get_settings() -> Settings:
    return Settings()
