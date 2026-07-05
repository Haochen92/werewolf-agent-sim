"""Case/game-index loading + cohort selection over a batch's frozen eval-case
sidecars — the deterministic (no-LLM) substrate every screen runs on. Loads the
ground-truth roles a vote is scored against, iterates the replay-able decisions
in a phase, stratifies a diverse cohort by day, and locates single decisions."""

from __future__ import annotations

import json
import random
from collections import OrderedDict
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from Agents.schemas.evaluation import EvalCase
from evaluation.src.data.sources.sidecar import LocalCaseSource
from evaluation.src.loop.decision_scoring import REPLAYABLE_TOWN_ROLES


def load_game_index(batch_path: Path) -> dict[str, dict[str, Any]]:
    """Map trace_id -> the ground truth a vote is scored against (roles +
    day_resolutions for abstain recovery + night_resolutions for the healer-night
    attack-join), read straight from the batch records."""
    index: dict[str, dict[str, Any]] = {}
    with batch_path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            tid = rec.get("trace_id")
            if not tid:
                continue
            index[tid] = {
                "game_id": rec.get("game_id"),
                "roles": rec.get("roles", {}) or {},
                "day_resolutions": rec.get("day_resolutions", []) or [],
                "night_resolutions": rec.get("night_resolutions", []) or [],
                "winner": rec.get("winner"),
            }
    return index


def iter_cases(
    batch_path: Path,
    roles: frozenset[str] = REPLAYABLE_TOWN_ROLES,
    phase: str = "day_vote",
) -> Iterator[tuple[EvalCase, dict[str, Any]]]:
    """Yield (case, game_info) for every replay-able decision in the given phase
    with retrieved memory, for the given roles — the unit the screen scores.
    phase='day_vote' (default) or 'night_action'; roles default to town."""
    source = LocalCaseSource(batch_path)
    index = load_game_index(batch_path)
    for tid in source.trace_ids():
        game = index.get(tid)
        if not game:
            continue
        for case in source.eval_cases(tid):
            if case.action_phase != phase:
                continue
            if case.player_role not in roles:
                continue
            if not case.retrieved_observations:
                continue
            yield case, game


def _abstained_on_day(day: int, day_resolutions: list[dict]) -> bool:
    for res in day_resolutions:
        if res.get("day") == day:
            return any(v.get("votee") == "abstain" for v in res.get("votes", []))
    return False


def _select_diverse(
    batch_path: Path,
    n: int,
    min_day: int,
    max_day: int = 999,
    roles: frozenset[str] = REPLAYABLE_TOWN_ROLES,
    phase: str = "day_vote",
    seed: int = 0,
) -> list[tuple[EvalCase, dict[str, Any]]]:
    """Pick ~n decisions in [min_day, max_day] for the given roles+phase, STRATIFIED BY
    DAY and spread across games. The old round-robin walked each game's day-ordered pool
    from depth 0, so day-2 (always present) was drawn first and day-3+ was under-sampled —
    early-weighting every aggregate. Here we round-robin ACROSS days (one per day per
    round until a day is exhausted → each day is represented up to its availability), and
    within a day round-robin across games. Deterministic given `seed` (it only fixes the
    per-day game ordering, so the same seed → the same cohort)."""
    by_day: dict[int, OrderedDict[str, list[tuple[EvalCase, dict[str, Any]]]]] = {}
    for case, game in iter_cases(batch_path, roles, phase):
        if case.day < min_day or case.day > max_day:
            continue
        by_day.setdefault(case.day, OrderedDict()).setdefault(
            str(game["game_id"]), []
        ).append((case, game))

    rng = random.Random(seed)
    day_queues: dict[int, list[tuple[EvalCase, dict[str, Any]]]] = {}
    for day, games in by_day.items():
        game_pools = list(games.values())
        rng.shuffle(game_pools)  # reproducible cross-game spread within the day
        queue: list[tuple[EvalCase, dict[str, Any]]] = []
        depth = 0
        while any(len(pool) > depth for pool in game_pools):
            for pool in game_pools:
                if len(pool) > depth:
                    queue.append(pool[depth])
            depth += 1
        day_queues[day] = queue

    days = sorted(day_queues)
    picked: list[tuple[EvalCase, dict[str, Any]]] = []
    idx = 0
    while len(picked) < n and any(idx < len(day_queues[d]) for d in days):
        for d in days:
            if idx < len(day_queues[d]):
                picked.append(day_queues[d][idx])
                if len(picked) >= n:
                    break
        idx += 1
    return picked


def _mem_text(case: EvalCase) -> str:
    """The stable/actionable text of a decision's retrieved memory (each entry's
    approach + situation) — what the reasoning would echo if it actually engaged
    the memory. Outcome wording is excluded (it changes across framings)."""
    bag: list[str] = []
    for item in case.retrieved_observations or []:
        obs = item.observation
        bag.append(getattr(obs, "approach", "") or "")
        bag.append(getattr(obs, "situation", "") or "")
    return " ".join(bag)


def _find_case(
    batch_path: Path, game_prefix: str, role: str, day: int, mem_substr: str
) -> tuple[EvalCase | None, dict[str, Any] | None]:
    """Locate ONE frozen decision by game-id prefix + role + day, disambiguating
    same-game/same-role/same-day villagers by a substring of their retrieved memory
    (the memory is frozen on the case, so this is deterministic)."""
    for case, game in iter_cases(batch_path, frozenset({role}), "day_vote"):
        if (
            str(game["game_id"]).startswith(game_prefix)
            and case.day == day
            and mem_substr in _mem_text(case)
        ):
            return case, game
    return None, None


def _find_endgame_plant(batch_path: Path) -> Any | None:
    """Grab a real retrieved-observation object whose situation is unmistakably an
    ENDGAME (four-player / final-three), to inject as a clear mismatch into mid-game
    decisions. Reusing a real object guarantees a valid schema for the replay."""
    for case, _ in iter_cases(batch_path, REPLAYABLE_TOWN_ROLES, "day_vote"):
        for item in case.retrieved_observations or []:
            s = (getattr(item.observation, "situation", "") or "").lower()
            if "endgame" in s and any(
                k in s for k in ("four-player", "four player", "final-three", "final three", "three remaining")
            ):
                return item
    return None
