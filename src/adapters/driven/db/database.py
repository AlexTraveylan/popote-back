from pathlib import Path

from sqlalchemy import event
from sqlalchemy.engine.interfaces import DBAPIConnection
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlmodel import SQLModel

from src.adapters.driven.db.config import DbConfig

_SQLITE_PREFIX = "sqlite+aiosqlite:///"


def _ensure_sqlite_folder(url: str) -> None:
    if not url.startswith(_SQLITE_PREFIX):
        return
    location = url.removeprefix(_SQLITE_PREFIX)
    if location and location != ":memory:":
        Path(location).parent.mkdir(parents=True, exist_ok=True)


def _use_write_ahead_log(dbapi_connection: DBAPIConnection, _record: object) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()


def create_engine(db_config: DbConfig) -> AsyncEngine:
    _ensure_sqlite_folder(db_config.DATABASE_URL)
    engine = create_async_engine(db_config.DATABASE_URL, echo=db_config.DB_ECHO, future=True)
    if db_config.DATABASE_URL.startswith(_SQLITE_PREFIX):
        event.listen(engine.sync_engine, "connect", _use_write_ahead_log)
    return engine


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


async def init_db(engine: AsyncEngine) -> None:
    async with engine.begin() as async_conn:
        await async_conn.run_sync(SQLModel.metadata.create_all)
