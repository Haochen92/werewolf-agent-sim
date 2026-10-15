"""The model catalogue: one row per model a game can be played on, and its dated prices.

Read by ``Agents/llm_factory/catalog.py`` (plain SQL, so the engine and offline tools need no
ORM) and edited by ``scripts/model_catalog.py``; these mappings register the tables for Alembic.
"""

from datetime import date, datetime

from sqlalchemy import TIMESTAMP, Boolean, Column, Date, Float, Integer, Text, func, text
from sqlmodel import Field, SQLModel


class CatalogModelRow(SQLModel, table=True):
    __tablename__ = "models"

    model: str = Field(sa_column=Column(Text, primary_key=True))
    display_name: str = Field(sa_column=Column(Text, nullable=False))
    listed: bool = Field(default=False, sa_column=Column(
        Boolean, nullable=False, server_default=text("false")))
    menu_order: int = Field(default=0, sa_column=Column(
        Integer, nullable=False, server_default=text("0")))
    house_funded: bool = Field(default=False, sa_column=Column(
        Boolean, nullable=False, server_default=text("false")))
    rescue_model: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    turn_thinking: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    summary_thinking: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    structured_mode: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    notes: str = Field(default="", sa_column=Column(Text, nullable=False, server_default=""))
    updated_at: datetime | None = Field(
        default=None,
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now()),
    )


class ModelPriceRow(SQLModel, table=True):
    """USD per million tokens, keyed by the name the provider bills under (no factory prefix),
    in force from ``since`` until that model's next row."""

    __tablename__ = "model_prices"

    model: str = Field(sa_column=Column(Text, primary_key=True))
    since: date = Field(sa_column=Column(Date, primary_key=True))
    input: float = Field(sa_column=Column(Float, nullable=False))
    cached: float = Field(sa_column=Column(Float, nullable=False))
    output: float = Field(sa_column=Column(Float, nullable=False))
    peak: bool = Field(default=False, sa_column=Column(
        Boolean, nullable=False, server_default=text("false")))
    source: str = Field(default="", sa_column=Column(Text, nullable=False, server_default=""))
