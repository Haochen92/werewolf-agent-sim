"""Per-role/phase situation-summary LLM call (the live retrieval query).

v6: the query is composed in the SAME per-cell dimension schema as the post-game extraction
(`cell_situation_schema_for` ⇒ `compose_situation_embed`), so a live query embed-matches the stored
v6 observations. Falls back to the legacy v5 SituationSummary for any (role, phase) without a v6 cell.

This is an LLM-agent concern colocated here for now — a candidate to move into a dedicated agents/llm
module later.
"""
from __future__ import annotations

from logging import getLogger

from pydantic import BaseModel, Field, create_model

from Agents.board_clocks import criticality_from_census
from Agents.llm_factory import get_llm
from Agents.prompts.prompt_inputs import (
    build_agent_prompt_input as _build_agent_prompt_input,
    compose_cell_guidance,
)
from Agents.prompts import (
    HEALER_SITUATION_SUMMARY,
    INVESTIGATOR_SITUATION_SUMMARY,
    SERIAL_KILLER_SITUATION_SUMMARY,
    VIGILANTE_SITUATION_SUMMARY,
    VILLAGER_SITUATION_SUMMARY,
    WOLF_SITUATION_SUMMARY,
)
from Agents.prompts.memory import V6_SITUATION_SUMMARY
from Agents.schemas import SituationSummary
from Agents.schemas.memory import cell_situation_schema_for
from Agents.state import (
    HealerDayState,
    InvestigatorDayState,
    VillagerDayState,
    WolfDayState,
)

logger = getLogger(__name__)

_LEGACY_PROMPT_BY_ROLE = {
    "villager": VILLAGER_SITUATION_SUMMARY,
    "healer": HEALER_SITUATION_SUMMARY,
    "investigator": INVESTIGATOR_SITUATION_SUMMARY,
    "wolf": WOLF_SITUATION_SUMMARY,
    "serial_killer": SERIAL_KILLER_SITUATION_SUMMARY,
    "vigilante": VIGILANTE_SITUATION_SUMMARY,
}

# Cache the per-cell summary containers (list[CellSituation], 1-2 items) so we build each once.
_SUMMARY_CONTAINER_CACHE: dict[type, type[BaseModel]] = {}


def _summary_container(cell_schema: type[BaseModel]) -> type[BaseModel]:
    cached = _SUMMARY_CONTAINER_CACHE.get(cell_schema)
    if cached is None:
        cached = create_model(
            f"{cell_schema.__name__}Summary",
            __base__=BaseModel,
            situations=(
                list[cell_schema],
                Field(min_length=1, max_length=2,
                      description="1-2 distinct situations you currently face, each with its "
                                  "structured dimensional fields for semantic search."),
            ),
        )
        _SUMMARY_CONTAINER_CACHE[cell_schema] = cached
    return cached


def _computed_players_alive(payload: dict) -> int | None:
    """Deterministic living-player count from the agent's OWN payload — robust to payload shape:

    - wolf payloads carry the faction rosters (surviving_wolves + surviving_villagers) and no
      role-blind list; their sum is the whole board (self is in surviving_wolves);
    - single-actor NIGHT payloads list every living player EXCEPT the actor, so the actor is added
      back via the membership check;
    - day payloads carry the full role-blind roster including self (membership check → no adjustment).

    Returns None when neither roster is reachable (legacy fallback → keep the LLM fill)."""
    wolves = payload.get("surviving_wolves")
    villagers = payload.get("surviving_villagers")
    if wolves is not None and villagers is not None:
        return len(wolves) + len(villagers)
    roster = payload.get("surviving_players")
    if roster is None:
        return None
    self_counted = payload.get("player_id") in roster
    return len(roster) + (0 if self_counted else 1)


def _computed_dims(payload: dict, available: dict) -> dict[str, int | bool]:
    """The agent-KNOWABLE situation dims computed from game state, for whichever of the cell's
    `available` fields this payload can support. The SINGLE source for both (a) the KNOWN BOARD FACTS
    injected into the query prompt (`_known_board_facts`, so the LLM writes `criticality_stakes` from
    the true numbers) and (b) `_override_deterministic_dims` (so the gating dims are exact) — deriving
    both from here means the number the model is TOLD and the number it is OVERRIDDEN to can never
    disagree. Omits a dim when it cannot be computed (→ the LLM's own value stands)."""
    dims: dict[str, int | bool] = {}
    alive = _computed_players_alive(payload)
    if alive is not None and "players_alive" in available:
        dims["players_alive"] = alive
    if "bullets_left" in available and payload.get("vigilante_bullets") is not None:
        dims["bullets_left"] = int(payload["vigilante_bullets"])
    if "ally_revealed" in available and payload.get("initial_wolf_count") is not None:
        dims["ally_revealed"] = len(payload.get("surviving_wolves", [])) < int(payload["initial_wolf_count"])
    # Criticality is PUBLIC info too (fixed cast + role-revealing deaths -> the census gives the
    # faction COUNTS the clocks need; identities never enter). None on legacy census-less payloads.
    crit = criticality_from_census(payload.get("cast_role_counts"), payload.get("dead_roster"))
    if crit is not None:
        _, dist, swing = crit
        if "distance_to_parity" in available:
            dims["distance_to_parity"] = dist
        if "is_swing" in available:
            dims["is_swing"] = swing
    return dims


def _log_dim_override(payload: dict, field: str, llm_value, computed_value) -> None:
    """Debug-log only when the deterministic override actually corrects the LLM — so future runs
    surface residual LLM fill error for free (grep the situation-summary debug logs)."""
    if llm_value != computed_value:
        logger.debug(
            "situation dim override: %s (%s) day %s %s -> LLM said %r, computed %r",
            payload.get("player_id"), payload.get("player_role"),
            payload.get("current_day"), field, llm_value, computed_value,
        )


def _override_deterministic_dims(situation: BaseModel, payload: dict) -> None:
    """Guarantee the agent-KNOWABLE dims (`players_alive` / `bullets_left` / `ally_revealed`) equal the
    values computed from game state, never the LLM's structured output. The 2026-07 dimension-accuracy
    audit (`evidence/phase_b/dimension_accuracy_audit/`) measured the LLM mis-filling `players_alive`
    ~3% for no epistemic reason and systematically UNDER-counting `bullets_left` (0.164 exact, day-2
    acc 0.0); all three are in the agent's own information set, so they are computed here for free.

    The query prompt is ALSO handed these numbers (`_known_board_facts`), so this override is normally a
    belt-and-suspenders no-op — it still fires when the model ignores the injected fact, and
    `_log_dim_override` records that residual disagreement.

    `distance_to_parity` / `is_swing` joined the computed set on 2026-07-11: the old premise ("they
    need the true role map the live agent cannot see") was falsified by the owner — the cast is fixed
    and public and every death path announces the dead player's role, so the census (cast minus
    revealed dead) yields the faction COUNTS the clocks need (Agents.board_clocks). They fall back to
    the LLM fill only on legacy payloads that carry no `cast_role_counts`.

    RESIDUAL: only the numeric/bool dims are corrected; free-text fields (`criticality_stakes` etc.)
    are composed by the LLM from the injected facts and are not themselves overridden."""
    for field, computed in _computed_dims(payload, type(situation).model_fields).items():
        _log_dim_override(payload, field, getattr(situation, field), computed)
        setattr(situation, field, computed)


def _known_board_facts(payload: dict, cell_schema: type[BaseModel]) -> str:
    """The computable agent-knowable dims, rendered as authoritative facts for the query prompt so the
    LLM writes `criticality_stakes` (and the conditioner implications) FROM the true numbers rather than
    estimating them. This is the fix that matters: the estimate was 0.164-accurate for `bullets_left`,
    and that wrong number fed the EMBEDDED stakes prose, which `_override_deterministic_dims` cannot
    repair after the fact (it corrects the numeric dim, not the already-composed embed string). Empty
    string when nothing is computable (→ the LLM estimates, unchanged)."""
    facts = _computed_dims(payload, cell_schema.model_fields)
    if not facts:
        return ""
    lines: list[str] = []
    if "players_alive" in facts:
        lines.append(f"- Players alive right now: {facts['players_alive']} (set players_alive to exactly this).")
    if "bullets_left" in facts:
        b = facts["bullets_left"]
        tail = " — with none left you now play as a regular villager" if b == 0 else ""
        lines.append(f"- Vigilante shots you have left: {b}{tail} (set bullets_left to exactly this).")
    if "ally_revealed" in facts:
        yn = "yes" if facts["ally_revealed"] else "no"
        lines.append(f"- A wolf partner has been revealed or eliminated: {yn} (set ally_revealed accordingly).")
    if "distance_to_parity" in facts:
        lines.append(
            f"- Eliminations until the leading evil faction can win: {facts['distance_to_parity']} "
            "(set distance_to_parity to exactly this)."
        )
    if "is_swing" in facts:
        yn = "yes" if facts["is_swing"] else "no"
        lines.append(
            f"- The game can end within one more elimination: {yn} (set is_swing accordingly)."
        )
    return (
        "KNOWN BOARD FACTS (authoritative — computed from the game state; use these EXACT values and "
        "derive the Stakes from them, do not re-estimate):\n" + "\n".join(lines)
    )


def _generate_situations_for_agent(
    payload: VillagerDayState | HealerDayState | WolfDayState | InvestigatorDayState,
    action_phase: str,
    max_retries: int = 1,
) -> tuple[list[str], list[dict]]:
    """Returns (composed embed strings, structured query-situation dims). The dims are the v6 cell
    situation objects' model_dump (exposure_class / info_landscape_class / criticality / ...), parallel
    to the strings; they feed the live dimension-gating filter (default-off per role) and the offline
    gating screens. [] on the legacy path / fallback."""
    player_id = payload["player_id"]
    role = payload["player_role"]
    current_day = payload["current_day"]
    current_round = payload["current_round"]
    run_name = f"situation_summary_{role}_{action_phase}_day_{current_day}_round_{current_round}"

    cell_schema = cell_situation_schema_for(role, action_phase)
    extra: dict = {}
    if cell_schema is not None:
        chain = V6_SITUATION_SUMMARY | get_llm().with_structured_output(
            _summary_container(cell_schema)
        )
        compose = lambda r: (  # noqa: E731
            [s.composed_situation for s in r.situations],
            [s.model_dump(mode="json") for s in r.situations],
        )
        extra = compose_cell_guidance(role, action_phase, cell_schema)
        # Hand the LLM the agent-knowable numbers so criticality_stakes is written FROM truth (the
        # override below still guarantees the exact numeric dims for gating). Empty when uncomputable.
        extra["known_board_facts"] = _known_board_facts(payload, cell_schema)
    else:
        prompt_template = _LEGACY_PROMPT_BY_ROLE.get(role, VILLAGER_SITUATION_SUMMARY)
        chain = prompt_template | get_llm().with_structured_output(SituationSummary)
        compose = lambda r: (r.composed_situations, [])  # noqa: E731

    for attempt in range(max_retries + 1):
        try:
            result = chain.invoke(
                {**_build_agent_prompt_input(payload), **extra}, config={"run_name": run_name}
            )
            if cell_schema is not None:
                # Correct the agent-knowable dims from game state before composing the dims/embeds
                # (the legacy path emits no structured dims, so nothing to override there).
                for situation in result.situations:
                    _override_deterministic_dims(situation, payload)
            return compose(result)
        except Exception as e:
            logger.warning(f"Situation summary LLM call failed for {player_id}: {e}")
            if attempt < max_retries:
                continue
            break

    logger.error(f"{player_id} situation summary failed all retries, using fallback")
    return [f"Day {current_day} as {role}, round {current_round}"], []
