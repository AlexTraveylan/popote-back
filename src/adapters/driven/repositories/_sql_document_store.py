from collections.abc import Callable
from typing import Any
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import ColumnElement, func
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlmodel import SQLModel, select


class SqlDocumentStore[E: BaseModel, R: SQLModel]:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        record_type: type[R],
        entity_type: type[E],
        to_record: Callable[[E], R],
    ) -> None:
        self._session_factory = session_factory
        self._record_type = record_type
        self._entity_type = entity_type
        self._to_record = to_record

    def _to_entity(self, record: R) -> E:
        payload: dict[str, Any] = getattr(record, "payload")  # noqa: B009
        return self._entity_type.model_validate(payload)

    async def select(self, *conditions: ColumnElement[bool]) -> list[E]:
        async with self._session_factory() as session:
            result = await session.execute(select(self._record_type).where(*conditions))
            return [self._to_entity(record) for record in result.scalars().all()]

    async def get(self, entity_id: UUID) -> E | None:
        async with self._session_factory() as session:
            record = await session.get(self._record_type, entity_id)
            return self._to_entity(record) if record is not None else None

    async def upsert(self, entities: list[E]) -> None:
        if not entities:
            return
        async with self._session_factory() as session:
            for entity in entities:
                await session.merge(self._to_record(entity))
            await session.commit()

    async def delete(self, entity_id: UUID) -> None:
        async with self._session_factory() as session:
            record = await session.get(self._record_type, entity_id)
            if record is not None:
                await session.delete(record)
                await session.commit()

    async def count(self) -> int:
        async with self._session_factory() as session:
            result = await session.execute(select(func.count()).select_from(self._record_type))
            return int(result.scalar_one())


def payload_of(entity: BaseModel) -> dict[str, Any]:
    return entity.model_dump(mode="json")
