from datetime import date, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class StockItemRecord(SQLModel, table=True):
    __tablename__ = "stock_items"

    id: UUID = Field(primary_key=True)
    name: str = Field(index=True)
    payload: dict[str, Any] = Field(sa_column=Column(JSON, nullable=False))


class RecipeRecord(SQLModel, table=True):
    __tablename__ = "recipes"

    id: UUID = Field(primary_key=True)
    title: str = Field(index=True)
    payload: dict[str, Any] = Field(sa_column=Column(JSON, nullable=False))


class CookLogRecord(SQLModel, table=True):
    __tablename__ = "cook_logs"

    id: UUID = Field(primary_key=True)
    cooked_on: date = Field(index=True)
    payload: dict[str, Any] = Field(sa_column=Column(JSON, nullable=False))


class ShoppingTripRecord(SQLModel, table=True):
    __tablename__ = "shopping_trips"

    id: UUID = Field(primary_key=True)
    shopped_on: date = Field(index=True)
    payload: dict[str, Any] = Field(sa_column=Column(JSON, nullable=False))


class PlannedMealRecord(SQLModel, table=True):
    __tablename__ = "planned_meals"

    id: UUID = Field(primary_key=True)
    planned_on: date = Field(index=True)
    payload: dict[str, Any] = Field(sa_column=Column(JSON, nullable=False))


class HouseholdNoteRecord(SQLModel, table=True):
    __tablename__ = "household_notes"

    id: UUID = Field(primary_key=True)
    created_at: datetime = Field(index=True)
    payload: dict[str, Any] = Field(sa_column=Column(JSON, nullable=False))
