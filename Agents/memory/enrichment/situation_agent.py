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
    """Replace the agent-KNOWABLE situation dims with values computed from game state, so they are
    never trusted from the LLM's structured output. The 2026-07 dimension-accuracy audit
    (`evidence/phase_b/dimension_accuracy_audit/`) measured the LLM mis-filling `players_alive` ~3%
    for no epistemic reason and systematically UNDER-counting `bullets_left` (0.164 exact, day-2
    acc 0.0) — all three fields below are in the agent's own information set, so they are computed
    here deterministically and for free.

    RESIDUAL INCONSISTENCY (accepted this pass, flagged in the audit log): only the NUMERIC/BOOL
    dims are corrected — NOT the prose (`criticality_stakes` etc.), which the LLM derived from its
    OWN, possibly-wrong numbers. So a corrected `players_alive`/`bullets_left` may now disagree with
    the un-corrected prose in the same object. Re-deriving the prose is out of scope (it would need a
    second LLM call). `distance_to_parity` / `is_swing` are deliberately left LLM-filled: they need
    the true role map the live agent cannot see."""
    alive = _computed_players_alive(payload)
    if alive is not None and hasattr(situation, "players_alive"):
        _log_dim_override(payload, "players_alive", situation.players_alive, alive)
        situation.players_alive = alive

    # bullets_left lives only on the vigilante cells; vigilante_bullets is the runtime remaining-shot
    # counter (night payload carries it directly; the day payload has it threaded in — see flow.py).
    if hasattr(situation, "bullets_left") and payload.get("vigilante_bullets") is not None:
        computed = int(payload["vigilante_bullets"])
        _log_dim_override(payload, "bullets_left", situation.bullets_left, computed)
        situation.bullets_left = computed

    # ally_revealed lives only on the wolf DAY cell. initial_wolf_count is threaded from the game's
    # true role map (see flow.py); a partner is "revealed/eliminated" iff fewer wolves survive than
    # were cast (the audit's validated partner-absent truth, 0.975 accurate as an LLM fill already).
    if hasattr(situation, "ally_revealed") and payload.get("initial_wolf_count") is not None:
        living_wolves = len(payload.get("surviving_wolves", []))
        computed = living_wolves < int(payload["initial_wolf_count"])
        _log_dim_override(payload, "ally_revealed", situation.ally_revealed, computed)
        situation.ally_revealed = computed


def _generate_situations_for_agent(
    payload: VillagerDayState | HealerDayState | WolfDayState | InvestigatorDayState,
    action_phase: str,
    max_retries: int = 1,
) -> tuple[list[str], list[dict]]:
    """Returns (composed embed strings, structured query-situation dims). The dims are the v6 cell
    situation objects' model_dump (exposure_class / info_landscape_class / criticality / ...), parallel
    to the strings, retained for eval-only dimension-gating screens; [] on the legacy path / fallback."""
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
