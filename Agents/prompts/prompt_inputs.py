"""The Send payload turned into a template's variables: the policy layer between a turn's
payload and its prompt.

``build_agent_prompt_input`` reads the payload a Send builder made (Agents/nodes/day/flow.py, the
leak boundary) and returns the dict whose keys match the ``{placeholders}`` in the templates.
Each block of game state is rendered through prompt_formatters.py; this module adds what is not
formatting: which rules block this turn gets (the day's round, the abstain rule), the firing brief,
whether the memory synergy instruction fires, the read targets minus the speaker. The order the
blocks appear in the prompt is not decided here but by the ChatPromptTemplates and their factory
functions in the template modules.
"""

from __future__ import annotations

import random
import zlib
from typing import Any

from pydantic import BaseModel

from Agents.prompts.compose import preamble
from Agents.schemas.game_events import DayRound
from Agents.schemas.roles import ROLE_SPECS
from Agents.prompts.cell_prompt import cell_driver_horizon, dimension_menu
from Agents.prompts.day_discuss import (
    CLOSING_ROUND_RULES,
    DAY_ONE_NO_VOTE_RULES,
    OPENING_ROUND_RULES,
    PROACTIVE_ROUND_RULES,
)
from Agents.prompts.prompt_formatters import (
    format_alive_roles,
    format_day_channel_for_day,
    format_day_summaries,
    format_dead_roster,
    format_night_actions,
    format_retrieved_observations,
    format_strategy_points,
    format_wolf_channel,
)
# Source from the concrete submodules, not the Agents.prompts package __init__:
# this module now lives *inside* that package, so importing from its __init__
# would be a back-edge (cycle risk during package init).
from Agents.prompts.memory import (
    OBS_STRATEGY_SYNERGY_INSTRUCTION,
    OBSERVATIONS_BLOCK,
    STRATEGY_POINTS_BLOCK,
    STRATEGY_VERDICT_INSTRUCTION,
    SITUATION_ROLE_LENS,
)
from Agents.prompts.standards import (
    EPISTEMIC_STATUS_RULE,
    SITUATION_QUALITY_STANDARDS,
    SITUATION_STANDARDS,
)


def compose_cell_guidance(role: str, action_phase: str, schema: type[BaseModel]) -> dict[str, str]:
    """The aligned v6 per-cell guidance shared by the live query (situation_agent) AND the post-game
    extraction (reextract_cells): WHICH dims (menu, from the schema) + lead-with/horizon (driver) +
    the cross-cutting quality bar + the epistemic rule. Both sides compose from THIS one function, so
    the live query embed-matches the store — the alignment can't silently drift."""
    return {
        "dimension_menu": dimension_menu(schema),
        "driver_horizon": cell_driver_horizon(role, action_phase),
        "situation_quality": SITUATION_QUALITY_STANDARDS,
        "epistemic_status_rule": EPISTEMIC_STATUS_RULE,
    }


def _firing_brief(firing_reason: Any) -> str:
    """Turn the scheduler's firing_reason into a one-line turn brief for the agent.

    Reactive picks get an explicit 'you were addressed by X, respond' nudge so the agent
    aims its reply at the right player (and labels it a response → the debt discharges).
    Proactive / missing reasons add nothing (the silence rule already governs those).
    """
    if firing_reason is None:
        return ""
    if isinstance(firing_reason, dict):
        tier, owes = firing_reason.get("tier"), firing_reason.get("owes") or []
    else:
        tier, owes = getattr(firing_reason, "tier", None), getattr(firing_reason, "owes", []) or []
    if tier == "reactive" and owes:
        return (
            f"You were directly addressed by {', '.join(owes)}. Respond to them this turn — "
            "answer their question or defend against their accusation. Do not stay silent."
        )
    return ""


def _discussion_stage_rules(payload: dict[str, Any]) -> str:
    """The rules block for this turn's place in the day (Phase 2, discussion_evidence.md §7.2).

    The payload's ``day_round`` says which round the turn belongs to: ``opening`` (every living
    player at once, claims and night facts only), ``discussion`` (the scheduler's reactive
    turns), ``proactive`` (a sweep turn: the floor given to a player who has not spoken) or
    ``closing`` (the accused's last word). On day 1 there is no vote, and the opening says so.
    A missing ``day_round`` is a discussion turn, so older payloads and replays render as before.
    """
    day_round: DayRound = payload.get("day_round", "discussion")
    voting_today = payload.get("voting_available", True)

    if day_round == "opening":
        rules = OPENING_ROUND_RULES
        if not voting_today:
            rules = rules + DAY_ONE_NO_VOTE_RULES
        return rules
    if day_round == "proactive":
        return PROACTIVE_ROUND_RULES
    if day_round == "closing":
        return CLOSING_ROUND_RULES
    # A discussion turn. Until the opening round is wired in (step 4), day 1 still holds a
    # discussion, and it keeps the no-vote note.
    if not voting_today:
        return DAY_ONE_NO_VOTE_RULES
    return ""


def _retrieved_present(x: Any) -> bool:
    """True when a retrieved-memory input actually has items: a non-empty list, or a pre-formatted
    string that isn't the empty-sentinel ("No past observations available." / "No dynamic strategy
    points available."). Drives the combined-arm synergy instruction (fires only when BOTH present)."""
    if isinstance(x, str):
        return bool(x.strip()) and not x.lstrip().startswith("No ")
    return bool(x)


# The solo night roles that draw a lot on night 1, as their cards say (NightWords.lot). The
# vigilante does not: a shot with no evidence is bad play, and holding fire is its night 1
# answer. The wolves draw one lot as a pack (the chat and the carrier's turn), so the two do not
# argue over two draws.
_LOT_ROLES = ("investigator", "healer", "serial_killer", "sentinel", "trailseer", "sigilist", "chanteuse")


def night_one_lot(payload: dict[str, Any]) -> str:
    """The line a night 1 prompt adds for a role that must choose with nothing to go on.

    Left to itself, a model with no reason to prefer anyone takes the smallest player number:
    over 32 boards, 95 of 96 night 1 choices were the lowest-numbered other seat, whatever order
    the list came in (discussion_evidence.md §7.5). So on night 1 the engine draws the default
    by lot, seeded by the game, the night and the player (the pack as one), and offers it: the
    agent may still prefer someone for a reason. "" on every later night, and for every role
    that draws no lot.
    """
    if payload.get("current_day", 1) != 1:
        return ""
    role = payload.get("player_role", "")
    player_id = payload.get("player_id", "")
    spec = ROLE_SPECS.get(role)
    if spec is not None and spec.pack and payload.get("pack_turn"):
        # The chat and the carrier's turn: one lot for the pack's kill.
        candidates = list(payload.get("surviving_villagers", []))
        who = "pack"
        wording = "a lot has been drawn for the pack"
    elif role in _LOT_ROLES:
        # A wolf's own skill turn draws its own lot, among the non-wolves.
        pool = payload.get("surviving_villagers") if spec is not None and spec.pack else payload.get("surviving_players", [])
        candidates = []
        for player in pool or []:
            if player != player_id:
                candidates.append(player)
        who = player_id
        wording = "a lot has been drawn for you"
    else:
        return ""
    if not candidates:
        return ""
    seed_text = "{}:{}:{}:lot".format(payload.get("game_id", ""), payload.get("current_day", 1), who)
    rng = random.Random(zlib.crc32(seed_text.encode("utf-8")))
    drawn = candidates[rng.randrange(len(candidates))]
    return (
        "Night 1: nothing in the record points anywhere yet, so {}: {}. "
        "Take it unless you have a reason to prefer someone else.\n\n".format(wording, drawn)
    )


def build_agent_prompt_input(payload: dict[str, Any]) -> dict[str, Any]:
    """Format a graph/eval payload into the keys consumed by agent prompts."""
    role = payload.get("player_role", "")
    retrieved_observations = payload.get("retrieved_observations", [])
    strategy_points = payload.get("strategy_points", [])
    # Synergy instruction fires ONLY when BOTH memory types are actually present (the combined "both"
    # arm) — data-driven, so obs-only / sp-only arms get "" and need no config flag.
    synergy_instruction = (
        OBS_STRATEGY_SYNERGY_INSTRUCTION
        if _retrieved_present(retrieved_observations) and _retrieved_present(strategy_points)
        else ""
    )
    strategy_points_text = (
        strategy_points if isinstance(strategy_points, str) else format_strategy_points(strategy_points)
    )
    observations_text = (
        retrieved_observations
        if isinstance(retrieved_observations, str)
        else format_retrieved_observations(retrieved_observations)
    )
    current_round = payload.get("current_round", 0)  # only the night templates render it
    if payload.get("allow_abstain"):
        abstain_instruction = (
            'You may vote "abstain" if you have no one you can justify eliminating yet — '
            "an abstain plurality means no one is eliminated today. Only abstain when "
            "holding off genuinely beats a guess; a wrong elimination is costly, but so is "
            "letting the killers act another night unchecked."
        )
    else:
        abstain_instruction = (
            "Abstaining is not available today — you must vote for a surviving player."
        )
    uses_left = payload.get("uses_left")
    return {
        "player_id": payload.get("player_id", ""),
        "player_role": role,
        "current_day": payload.get("current_day", 1),
        "current_round": current_round,
        "abstain_instruction": abstain_instruction,
        # The rules block, composed from the dealt lineup (public).
        "preamble": preamble(list(payload.get("lineup", []))) if payload.get("lineup") else "",
        # What a limited ability has left, under the name its card uses.
        "vigilante_bullets": uses_left if role == "vigilante" and uses_left is not None else payload.get("vigilante_bullets", 0),
        "sigils_left": uses_left if role == "sigilist" else 0,
        "checks_left": uses_left if role == "investigator" else 0,
        "watches_left": uses_left if role == "sentinel" else 0,
        "conceal_uses": uses_left if role == "illusionist" else 0,
        "fortune_self_bets": uses_left if role == "fortune_teller" else 0,
        "fortune_points": payload.get("fortune_points", 0),
        "speculator_pick": payload.get("speculator_pick", "not yet"),
        "bodies": ", ".join(payload.get("bodies", [])) or "none tonight",
        "carrier": payload.get("carrier", ""),
        "wolves_target": payload.get("wolves_target") or "not named yet",
        "firing_brief": _firing_brief(payload.get("firing_reason")),
        "discussion_stage_rules": _discussion_stage_rules(payload),
        "surviving_players": ", ".join(payload.get("surviving_players", [])),
        "surviving_wolves": ", ".join(payload.get("surviving_wolves", [])),
        "surviving_villagers": ", ".join(payload.get("surviving_villagers", [])),
        # Night 1 only, the solo roles and the pack: the default drawn by lot (night_one_lot).
        "night_lot": night_one_lot(payload),
        "dead_roster": format_dead_roster(payload.get("dead_roster", [])),
        # Roles still in play = the fixed public cast census minus every revealed-dead role (public,
        # deterministic — see format_alive_roles). "" when no census rode the payload (legacy replay).
        "alive_roles": format_alive_roles(
            payload.get("cast_role_counts", {}),
            payload.get("dead_roster", []),
        ),
        # The exact living players (minus self) the reads instruction enumerates — derived here, never
        # hard-coded, so it stays complete as players die (the T4 completeness mechanism). The fallback
        # covers the wolf day payload, which splits survivors into wolves + villagers.
        "read_targets": ", ".join(
            p
            for p in (
                payload.get("surviving_players")
                or (payload.get("surviving_wolves", []) + payload.get("surviving_villagers", []))
            )
            if p != payload.get("player_id")
        ),
        # The speaker also sees its own held-back drafts, marked as unseen by anyone else.
        "day_channel": format_day_channel_for_day(
            payload.get("day_channel", []),
            payload.get("current_day", 1),
            viewer=payload.get("player_id") or None,
        ),
        "day_summaries": format_day_summaries(
            payload.get("day_summaries", []),
            before_day=payload.get("current_day", 1),
            dead_roster=payload.get("dead_roster", []),
            cast_role_counts=payload.get("cast_role_counts", {}),
            messages=payload.get("day_channel", []),
        ),
        "wolf_channel": format_wolf_channel(payload.get("wolf_channel", [])),
        # The actor's own engine-written night record (only night actors' payloads carry it).
        "night_actions": format_night_actions(payload.get("night_actions", []), payload.get("current_day")),
        "previous_strategy": payload.get("previous_strategy", ""),
        "strategy_points": strategy_points_text,
        "retrieved_observations": observations_text,
        # The memory blocks and their instructions appear only when they hold something.
        "observations_block": (
            OBSERVATIONS_BLOCK.format(where="the current situation", retrieved_observations=observations_text)
            if _retrieved_present(retrieved_observations) else ""
        ),
        "night_observations_block": (
            OBSERVATIONS_BLOCK.format(where="your night decision", retrieved_observations=observations_text)
            if _retrieved_present(retrieved_observations) else ""
        ),
        "strategy_points_block": (
            STRATEGY_POINTS_BLOCK.format(strategy_points=strategy_points_text,
                                         adoption_instruction=STRATEGY_VERDICT_INSTRUCTION,
                                         synergy_instruction=synergy_instruction)
            if _retrieved_present(strategy_points) else ""
        ),
        "situation_standards": SITUATION_STANDARDS,
        "epistemic_status_rule": EPISTEMIC_STATUS_RULE,
        "role_lens": SITUATION_ROLE_LENS.get(role, ""),
        "adoption_instruction": STRATEGY_VERDICT_INSTRUCTION,
        "synergy_instruction": synergy_instruction,
        # The v1 tell book (2026-07-13): "" unless the arm sets WW_TELL_BOOK — see
        # Agents/memory/tell_book.py for the env gating + the per-turn roles-alive filter.
        # (imported lazily: Agents.memory's package init imports retrieval, which imports this module)
        "tell_book": _tell_book_block()(
            payload.get("dead_roster", []), payload.get("cast_role_counts", {})
        ),
    }

def _tell_book_block():
    from Agents.memory.tell_book import tell_book_block
    return tell_book_block
