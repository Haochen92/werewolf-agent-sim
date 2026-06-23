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


def _count_follows(window_files: list[str], case_ok) -> int:
    """Shared counter: memory-ON 'follow' verdicts that map to a real retrieved SP key
    (strategy_index_to_key), restricted to the cases `case_ok` accepts. A mem-OFF / no-SP row can carry a
    'follow' the ledger correctly ignores, so those never count. (Strictly resolves every eval_cases_path
    en route, so calling this validates path wiring too.)"""
    n = 0
    for _g, ec in _iter_eval_cases(window_files):
        if not ec.get("memory_enabled") or not case_ok(ec):
            continue
        idx = ec.get("strategy_index_to_key") or {}
        for sv in ec.get("strategy_verdicts") or []:
            if isinstance(sv, dict) and sv.get("verdict") == "follow" and idx.get(str(sv.get("strategy_index"))):
                n += 1
    return n


def count_follow_verdicts(window_files: list[str]) -> int:
    """CREDITABLE 'follow' verdicts — mirrors the credit join's own gate so the dead-credit guard compares
    like with like: a follow counts only if it's on a channel build_ledger actually credits (vote /
    creditable night). The cold-start false-positive (mem-OFF wolf-night follows) is excluded by
    _count_follows' memory-ON gate."""
    return _count_follows(window_files, _is_creditable_follow_case)


def count_discussion_follow_verdicts(window_files: list[str]) -> int:
    """day_discussion 'follow' verdicts mapping to a real retrieved SP key — the cases that SHOULD earn
    discussion credit (floor or tagger). build_ledger does NOT cover this channel (vote/night only), so
    count_follow_verdicts/assert_credit_engaged are blind to it: a silently-failed tagger could drop ALL
    discussion credit while the vote/night ledger still passed the dead-credit guard. This is its counter."""
    return _count_follows(window_files, lambda ec: ec.get("action_phase") == "day_discussion")


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


def assert_discussion_credit_engaged(window_files: list[str], disc_credited: int, *, enabled: bool) -> int:
    """The day_discussion analog of assert_credit_engaged, for the channel that one is blind to. When
    discussion credit is ON and the window carries day_discussion follows, the discussion ledger MUST have
    credited something — else the tagger/floor silently no-opped. The motivating failure: the paid LLM
    tagger catches all per-day errors and returns empty tags, so on a full whiff disc credit vanishes while
    the vote/night ledger (deterministic) still passes the dead-credit guard — you spent on tags and got
    nothing. Cold-start safe (no discussion follows yet => no claim). Returns the discussion follow count."""
    if not enabled:
        return 0
    follows = count_discussion_follow_verdicts(window_files)
    if follows > 0 and disc_credited == 0:
        raise AssertionError(
            f"discussion credit DEAD: {follows} day_discussion follow verdicts in the window but the "
            "discussion ledger credited 0 SPs — the tagger/floor silently no-opped (a failed flash-lite "
            "tagger returns empty tags; you spent on tags and got no credit). NOT a valid 'no signal' state.")
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


_TOWN_ROLES = frozenset({"villager", "healer", "investigator", "vigilante"})
# Symbolic intents accepted by --expect-factions (besides an explicit comma list of roles).
FACTION_INTENTS = {
    "town_only": _TOWN_ROLES,
    "town": _TOWN_ROLES,
    "all": None,    # all = "every role with a memory_config key" — resolved against the actual arm
    "all_enabled": None,
}


def arm_memory_factions(on_jsonl: str | Path) -> frozenset[str]:
    """The set of roles ACTUALLY given memory in the ON arm, read from the first ON game record's
    memory_config. The loop reads `configs` (a name) but the engine resolves it to a per-role on/off map —
    this returns what the engine actually enabled, so intent can be checked against reality, not the name."""
    for line in open(on_jsonl):
        if not line.strip():
            continue
        mc = json.loads(line).get("memory_config")
        if isinstance(mc, dict):
            return frozenset(r for r, on in mc.items() if on)
    raise AssertionError(f"no memory_config in any ON record of {on_jsonl} — cannot verify the arm")


def resolve_expected_factions(intent: str | None, actual: frozenset[str]) -> frozenset[str] | None:
    """Map a --expect-factions value to the role set it should equal. None intent => no check. A symbolic
    'all' resolves to every role present in the actual arm (intent = 'all factions', whatever the cast is);
    'town_only' => the four town roles; otherwise a comma list of role names."""
    if intent is None:
        return None
    key = intent.strip().lower()
    if key in FACTION_INTENTS:
        exp = FACTION_INTENTS[key]
        return actual if exp is None else exp     # 'all' = whatever roles the cast exposes
    return frozenset(r.strip() for r in intent.split(",") if r.strip())


def assert_arm_factions(on_jsonl: str | Path, intent: str | None) -> frozenset[str]:
    """⭐THE guard for the v2 config slip: the ON arm silently ran `all_enabled` (every faction had memory)
    when the experiment intended `town_only`, so a town-only conclusion was drawn from an all-memory-on
    arms-race board — a plausible WRONG number, no error. This asserts the ACTUAL enabled-faction set equals
    the declared intent and returns it (always — the caller records it in loop_history so the arm is visible
    even when no intent is declared). intent=None => no assertion, just surface the set."""
    actual = arm_memory_factions(on_jsonl)
    expected = resolve_expected_factions(intent, actual)
    if expected is not None and actual != expected:
        raise AssertionError(
            f"ARM MISMATCH: ON arm enabled memory for {sorted(actual)} but --expect-factions={intent!r} "
            f"requires {sorted(expected)}. The loop is running a DIFFERENT experiment than declared "
            f"(the v2 all_enabled-vs-town_only trap). Pass the right --configs or fix --expect-factions.")
    return actual


def assert_arm_declared(expect_factions: str | None, unchecked_arm: bool) -> None:
    """⭐FAIL-CLOSED pre-spend gate: refuse to start unless the ON arm is DECLARED (--expect-factions) or the
    check is explicitly WAIVED (--unchecked-arm). assert_arm_factions only fires when an intent is given, so
    a None intent left the v2 guard opt-IN — forgetting the flag silently re-opened the trap. This flips the
    default to declared: you must say what the arm should be, or knowingly opt out. No silent middle."""
    if expect_factions is None and not unchecked_arm:
        raise AssertionError(
            "arm UNDECLARED: pass --expect-factions (e.g. 'town_only' or 'all') so the ON arm is verified "
            "before spend, OR --unchecked-arm to knowingly run without the check. Refusing to run "
            "unverified — the v2 trap recurred precisely by FORGETTING to declare the arm.")


# runtime_fingerprint fields run_batch stamps on every game (Agents/run_fingerprint.py): backend, models,
# temperature, prompt-bundle hash, git commit/dirty, embeddings. All environment-level (no per-game field),
# so within ONE run every game's stamp is identical — any inequality is real drift.
def arm_fingerprint(jsonl: str | Path) -> dict:
    """The runtime_fingerprint stamped on the arm's first game record — the run's provenance (backend /
    model / temp / prompt / commit). Surfaced into run_meta and held constant across the run, so a flip
    can't silently splice incomparable scores (the 'Vertex vs Google differ at temp=0' rule, enforced)."""
    for line in open(jsonl):
        if not line.strip():
            continue
        fp = json.loads(line).get("runtime_fingerprint")
        if isinstance(fp, dict):
            return fp
    raise AssertionError(f"no runtime_fingerprint in any record of {jsonl} — cannot verify run provenance")


def assert_fingerprint_consistent(jsonl: str | Path, reference: dict) -> None:
    """Crash if any game record's fingerprint diverges from `reference`. A mid-run flip — a resume under a
    different backend/model/prompt, or an edit that changes the commit — otherwise silently mixes
    incomparable games into one slope. Records lacking a fingerprint are skipped (not all paths stamp)."""
    for line in open(jsonl):
        if not line.strip():
            continue
        fp = json.loads(line).get("runtime_fingerprint")
        if isinstance(fp, dict) and fp != reference:
            diff = {k: (reference.get(k), fp.get(k))
                    for k in set(reference) | set(fp) if reference.get(k) != fp.get(k)}
            raise AssertionError(
                f"runtime DRIFT within the run in {jsonl}: {diff} (reference vs record). A backend / model / "
                "prompt / commit flip mid-run makes the scores incomparable — pin the env and restart.")
