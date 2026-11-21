from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

from src.adapters.driven.db.config import DbConfig


def _default_members() -> list[str]:
    return ["Alex", "Sam"]


def _default_seed_files() -> list[str]:
    return ["seed/recipes.json", "seed/pantry.json", "data/private_seed.json"]


def _default_mcp_hosts() -> list[str]:
    return ["localhost:*", "127.0.0.1:*"]


def _split(value: object) -> object:
    if isinstance(value, str):
        return [part.strip() for part in value.split(",") if part.strip()]
    return value


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore")

    DATABASE_URL: str = "sqlite+aiosqlite:///./data/popote.db"
    DB_ECHO: bool = False

    HOUSEHOLD_MEMBERS: Annotated[list[str], NoDecode] = Field(default_factory=_default_members)

    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-5-mini"

    SEED_ON_STARTUP: bool = True
    SEED_FILES: Annotated[list[str], NoDecode] = Field(default_factory=_default_seed_files)

    ALLOWED_ORIGINS: Annotated[list[str], NoDecode] = Field(default_factory=lambda: ["*"])
    MCP_ALLOWED_HOSTS: Annotated[list[str], NoDecode] = Field(default_factory=_default_mcp_hosts)

    @field_validator("HOUSEHOLD_MEMBERS", "SEED_FILES", "ALLOWED_ORIGINS", "MCP_ALLOWED_HOSTS", mode="before")
    @classmethod
    def _split_comma_separated(cls, value: object) -> object:
        return _split(value)

    @property
    def db(self) -> DbConfig:
        return DbConfig(DATABASE_URL=self.DATABASE_URL, DB_ECHO=self.DB_ECHO)

    @property
    def seed_paths(self) -> list[Path]:
        return [Path(path) for path in self.SEED_FILES]


@lru_cache
def get_settings() -> Settings:
    return Settings()
