"""Graph state schemas, grouped by phase (split from the former graphs/state.py)."""

from Agents.state.day import (
    DayGraphState,
    HealerDayState,
    InvestigatorDayState,
    VillagerDayState,
    WolfDayState,
)
from Agents.state.night.healer import HealerNightGraph
from Agents.state.night.investigator import InvestigatorNightGraph
from Agents.state.night.serial_killer import SerialKillerNightGraph
from Agents.state.night.vigilante import VigilanteNightGraph
from Agents.state.night.wolf import WolfNightGraph, WolfNightState
from Agents.state.orchestrator import OrchestratorGraph, fresh_game_state
from Agents.state.reducers import merge_strategies

__all__ = [
    "DayGraphState",
    "HealerDayState",
    "HealerNightGraph",
    "InvestigatorDayState",
    "InvestigatorNightGraph",
    "OrchestratorGraph",
    "SerialKillerNightGraph",
    "VigilanteNightGraph",
    "VillagerDayState",
    "WolfDayState",
    "WolfNightGraph",
    "WolfNightState",
    "fresh_game_state",
    "merge_strategies",
]
