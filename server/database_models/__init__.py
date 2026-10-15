"""Application-owned SQLModel table mappings.

Importing this package registers every application-owned table on
``SQLModel.metadata`` for Alembic autogeneration. LangGraph checkpoint tables are
owned by ``AsyncPostgresSaver`` and deliberately do not belong here.
"""

from server.database_models.capture import PromptCaptureRow
from server.database_models.cast import CharacterRow, GameCastRow
from server.database_models.game import EventRow, GameRow
from server.database_models.model_catalog import CatalogModelRow, ModelPriceRow
from server.database_models.settings import SettingRow

__all__ = ["CatalogModelRow", "CharacterRow", "EventRow", "GameCastRow", "GameRow", "ModelPriceRow",
           "PromptCaptureRow", "SettingRow"]
