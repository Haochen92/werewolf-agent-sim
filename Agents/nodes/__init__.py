"""Graph node functions + routers, grouped by phase.

day/flow.py     — day discussion/vote control flow (scheduler hop, routers, fan-out, summary)
day/actors.py   — the two generic day actor nodes (discuss/vote); role rides the payload
orchestrator.py — the deal, day resolution, winner/terminal logic, night routing, postgame
night/solo.py   — one body for every solo role's night node (named per role in the parent)
night/pack.py   — the pack's night flow, a miniature of the day pattern (scheduler hub ->
                  sequential chat -> the carrier's kill -> parallel skills -> collect)
night/resolution.py — the NIGHT_RESOLUTION barrier: the night resolved once for every role

The turn system itself (speaker scheduling, run_agent, the memory-informed
actions, the proactive-novelty gate) lives in Agents.turn, not here — these
are only the graph nodes that call into it.

Everything is re-exported here so `from Agents.nodes import X` resolves unchanged.
"""

from Agents.nodes.orchestrator import (  # noqa: F401
    _max_days_winner,
    acts_tonight,
    check_game_end_day,
    check_game_end_night,
    day_resolution,
    determine_winner,
    end_game,
    initialize_game,
    is_draw,
    neutral_result,
    night_phase_name,
    night_start,
    one_more_day,
    post_game_analysis,
    remove_from_buckets,
    route_night_actors,
    side_counts,
)
from Agents.nodes.day import (  # noqa: F401
    _serialize_day_summary,
    collect_round,
    collect_votes,
    day_scheduler,
    discuss,
    fan_out_round,
    fan_out_vote,
    round_turn,
    route_after_day_summary,
    route_after_discussion,
    route_after_round,
    route_speaker,
    start_closing,
    start_opening,
    start_voting,
    summarize_day_discussion,
    vote,
)
from Agents.nodes.night.resolution import night_resolution  # noqa: F401
from Agents.nodes.night.solo import night_turn_payload, solo_night_phase  # noqa: F401
from Agents.nodes.night.pack import (  # noqa: F401
    carrier_kill,
    collect_pack,
    pack_chat,
    pack_fan_out_skills,
    pack_skill,
    prepare_pack_night,
    route_carrier,
    route_pack_speaker,
    start_carrier,
)
