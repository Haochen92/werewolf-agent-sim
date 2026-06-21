"""Compounding-loop INVARIANTS — fail-loud guards run every generation.

The loop's seams read game data with `... or continue` / `glob -> []` / `.get(k, 0)` defaults, so a
broken input degrades into a PLAUSIBLE WRONG number (empty ledger, haloed lift, partial slope) instead of
an error — the exact failure mode that let a dead-credit bug survive to a paid run. These guards turn that
class into an immediate, located crash: a window that should carry follows but credited nothing, an
off-arm that produced no base rates, a generation that scored zero decisions — all raise HERE, with the
context to fix them, rather than flowing silently into loop_history.json.
"""

from __future__ import annotations

import json
import os
from pathlib import Path


def expand_window(run_dir: Path, gens, arm: str) -> list[str]:
    """The rolling-window file list for `gens` (arm = 'on' | 'off'), every file asserted present. Replaces
    the space-joined glob STRING whose silent `glob.glob([]) -> []` on a multi-path pattern dead-credited
    the loop — an explicit, checkable list instead of a pattern that can quietly match nothing."""
    files = []
    for g in gens:
        p = run_dir / f"gen{g}_{arm}.jsonl"
        if not p.exists():
            raise AssertionError(f"window file missing: {p} (gens={list(gens)}, arm={arm})")
        files.append(str(p))
    if not files:
        raise AssertionError(f"empty window: gens={list(gens)} arm={arm}")
    return files


def _iter_eval_cases(window_files: list[str]):
    """Yield (game_record, eval_case) over a window, STRICTLY: a game record carrying roles + an
    eval_cases_path whose file does NOT resolve is a wiring bug (relative-path/cwd/cleanup), not a row to
    skip — raise. Closes the silent eval_cases_path skip shared by credit / measure / the tagger."""
    for f in window_files:
        for line in open(f):
            if not line.strip():
                continue
            g = json.loads(line)
            roles, path = g.get("roles"), g.get("eval_cases_path")
            if not roles:
                continue  # not a game record
            if not path:
                raise AssertionError(f"game record has roles but no eval_cases_path in {f}")
            if not os.path.exists(path):
                raise AssertionError(
                    f"eval_cases_path does not resolve: {path} (cwd={os.getcwd()}) — credit/measure would "
                    "SILENTLY skip this game")
            for cl in open(path):
                if not cl.strip():
                    continue
                ec = (json.loads(cl).get("output") or {}).get("eval_case")
                if ec:
                    yield g, ec


# build_ledger's coverage: votes (all roles) + night for these roles. healer-night is deferred and
# day_discussion is tagger/floor-dependent, so neither is a "credit MUST be non-empty" guarantee.
_CREDITABLE_NIGHT = {"investigator", "vigilante", "wolf", "serial_killer"}


def _is_creditable_follow_case(ec: dict) -> bool:
    phase, role = ec.get("action_phase"), ec.get("player_role")
    return phase == "day_vote" or (phase == "night_action" and role in _CREDITABLE_NIGHT)


def count_follow_verdicts(window_files: list[str]) -> int:
    """CREDITABLE 'follow' verdicts — mirrors the credit join's own gate so the dead-credit guard compares
    like with like: a follow counts only if the case had memory ON, the follow maps to a real retrieved SP
    key (strategy_index_to_key), AND it's on a channel build_ledger actually credits. A mem-OFF / no-SP row
    can still carry a 'follow' verdict (e.g. a wolf night action with no memory) that the ledger correctly
    ignores — counting those false-positived the guard at cold start. (Also strictly resolves every
    eval_cases_path en route, so calling this validates path wiring too.)"""
    n = 0
    for _g, ec in _iter_eval_cases(window_files):
        if not ec.get("memory_enabled") or not _is_creditable_follow_case(ec):
            continue
        idx = ec.get("strategy_index_to_key") or {}
        for sv in ec.get("strategy_verdicts") or []:
            if isinstance(sv, dict) and sv.get("verdict") == "follow" and idx.get(str(sv.get("strategy_index"))):
                n += 1
    return n


def assert_credit_engaged(window_files: list[str], ledger_keys: int) -> int:
    """THE guard that would have caught the dead-credit bug instantly: follows exist in the window but the
    credit ledger is empty => the join silently produced nothing. Cold-start safe (no SPs yet => 0 follows
    => no claim). Returns the follow count (for logging)."""
    follows = count_follow_verdicts(window_files)
    if follows > 0 and ledger_keys == 0:
        raise AssertionError(
            f"credit DEAD: {follows} follow verdicts in the window but ledger_keys=0 — the join produced "
            "nothing (window / path / glob wiring). NOT a valid 'no signal yet' state.")
    return follows


def assert_base_rates(base_rates: dict, off_ran: bool) -> None:
    """An off-arm that ran must yield >= 1 per-cell base rate; an empty map silently HALOES every lift
    (lift = utility - 0), corrupting credit AND prune decisions without erroring."""
    if off_ran and not base_rates:
        raise AssertionError(
            "off baseline ran but produced 0 base-rate channels — de-luck baseline would silently halo "
            "(lift == raw utility). Check the off-window wiring.")


def assert_score(score: dict, label: str = "") -> None:
    """A generation must score > 0 decisions; an empty/zero score is a silently-empty slope point (every
    game's eval_cases_path skipped, or a batch-glob mismatch)."""
    if not any(k.startswith("n_") and v > 0 for k, v in score.items()):
        raise AssertionError(
            f"generation_score {label} scored 0 decisions — empty/wrong slope point (eval_cases_path skips "
            "or batch glob mismatch).")
