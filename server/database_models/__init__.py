"""Application-owned SQLModel table mappings.

Importing this package registers every application-owned table on
``SQLModel.metadata`` for Alembic autogeneration. LangGraph checkpoint tables are
owned by ``AsyncPostgresSaver`` and deliberately do not belong here.
"""

from server.database_models.game import EventRow, GameRow

__all__ = ["EventRow", "GameRow"]
