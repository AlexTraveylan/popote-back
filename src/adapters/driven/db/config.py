from dataclasses import dataclass


@dataclass(frozen=True)
class DbConfig:
    DATABASE_URL: str
    DB_ECHO: bool = False
