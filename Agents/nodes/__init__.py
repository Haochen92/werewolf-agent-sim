"""Graph node functions + routers, grouped by phase.

day/flow.py     — day discussion/vote control flow (scheduler hop, routers, fan-out, summary)
day/actors.py   — per-role day discuss/vote nodes, built from two factories
orchestrator.py — game setup, day resolution, winner/terminal logic, postgame
scheduler.py    — sequential-discussion speaker ranking
night/<role>.py — each role's night action node (single-actor roles are one-line
                  bindings over night/factory.py:make_night_act_node)
night/wolf.py   — the multi-node wolf night discussion flow
night/resolution.py — cross-role night kill resolution + routing

The shared actor execution engine itself (_run_agent, the memory-informed
actions, the proactive-novelty gate) lives in Agents.engine, not here — these
are only the graph nodes that call into it.

Everything is re-exported here so `from Agents.nodes import X` resolves unchanged.
"""

from Agents.nodes.scheduler import (  # noqa: F401
    cycle_seed,
    select_next_speaker,
)
from Agents.nodes.orchestrator import (  # noqa: F401
    _faction_counts,
    _max_days_winner,
    _nullify_special_roles,
    check_game_end_day,
    check_game_end_night,
    day_resolution,
    determine_winner,
    end_game,
    initialize_game,
    one_more_day,
    post_game_analysis,
)
from Agents.nodes.day import (  # noqa: F401
    _serialize_day_summary,
    collect_votes,
    day_scheduler,
    fan_out_vote,
    healer_discuss,
    healer_vote,
    investigator_discuss,
    investigator_vote,
    route_after_day_summary,
    route_speaker,
    serial_killer_discuss,
    serial_killer_vote,
    start_voting,
    summarize_day_discussion,
    vigilante_discuss,
    vigilante_vote,
    villager_discuss,
    villager_vote,
    wolf_discuss,
    wolf_vote,
)
from Agents.nodes.night.resolution import (  # noqa: F401
    night_finalize,
    night_kill_resolution,
    route_after_healer_night,
    route_after_kill_resolution,
    route_after_serial_killer_night,
    route_after_wolf_night,
)
from Agents.nodes.night.wolf import (  # noqa: F401
    check_night_end,
    collect_wolf_night_discussion,
    prepare_wolf_night,
    wolf_fan_out,
    wolf_night_discuss,
)
from Agents.nodes.night.healer import healer_act  # noqa: F401
from Agents.nodes.night.investigator import investigator_act  # noqa: F401
from Agents.nodes.night.serial_killer import serial_killer_act  # noqa: F401
from Agents.nodes.night.vigilante import vigilante_act  # noqa: F401
