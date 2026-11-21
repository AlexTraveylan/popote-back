from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


def _now() -> datetime:
    return datetime.now(UTC)


class HouseholdNote(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    text: str
    author: str | None = None
    created_at: datetime = Field(default_factory=_now)
