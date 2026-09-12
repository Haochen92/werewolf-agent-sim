"""One row per live server setting: a key, a JSON value, and when it last changed."""

from datetime import datetime
from typing import Any

from sqlalchemy import TIMESTAMP, Column, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


class SettingRow(SQLModel, table=True):
    __tablename__ = "settings"

    key: str = Field(sa_column=Column(Text, primary_key=True))
    value: Any = Field(sa_column=Column(JSONB, nullable=False))
    updated_at: datetime | None = Field(
        default=None,
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now()),
    )
