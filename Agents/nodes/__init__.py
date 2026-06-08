"""Graph node functions, grouped by phase (split from graphs/nodes.py + agents.py).

day.py        — day-discussion/vote flow nodes + per-role day actor nodes
orchestrator.py — game setup, day resolution, winner/terminal logic, postgame
runtime.py    — the shared actor execution engine (_run_agent, memory-informed
                actions, the proactive-novelty gate) + prompt_log
scheduler.py  — sequential-discussion speaker ranking
night/<role>.py — each role's night action node
night/resolution.py — cross-role night kill resolution + routing

Everything is re-exported here so the historical `from Agents.nodes import X`
(and the former Agents.nodes / Agents.nodes call sites) resolve unchanged.
"""

from Agents.nodes.runtime import (  # noqa: F401
    NOVELTY_JUDGE_PROMPT,
    judge_proactive_novelty,
    prompt_log,
    _run_agent,
    _run_memory_informed_action,
    _run_memory_informed_night_action,
)
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
