"""The find→claim→lynch CONVERSION endpoint (deterministic, zero spend) — production form.

Why this channel exists (evidence/credit/blindspot_fix/): the follow-joined ledger is structurally
blind to concealment advice — a concealment SP is never "followed" as a discrete creditable act
("maintain silence" was retrieved 179x with follow=0 in the v7 endpoint store), so prune could
never touch it while the harm was real one hop downstream (ON converted investigator finds to
lynches at 26.7% vs OFF's 47.5%). This module scores that hop directly and is ALWAYS applied in
production — there is no off switch; ``TickConfig`` only bounds when the term may prune
(conversion_min_n) and how long a find stays open (conversion_window_days).

The construct: FIND = a night_resolutions row whose investigator_target's TRUE role is a threat;
WINDOW = days d+1..d+window after a night-d find; CONVERTED (positive) = the target is lynched
inside the window; VOIDED (excluded) = the target dies to a night kill first, or the game ended
before ANY window day was played; otherwise negative — including a window cut short by game end
after >=1 played day (deadlocked games end early; voiding those would hide exactly the failure
mode this channel exists to see). Attribution is RETRIEVAL-based on purpose: every SP the finder
retrieved during the open window inherits the find's outcome, once per find — diffuse, so it is
baselined against the OFF arm through the SAME construct and shrunk before it can prune.
"""

from __future__ import annotations

import json
import os
from collections import defaultdict
from pathlib import Path

from Agents.memory.consolidation.credit_rules import SHRINK_K, _iter_game_records
from Agents.memory.consolidation.decision_scoring import THREAT_ROLES

CONVERSION_CHANNEL = "conversion/investigator"
FINDER_PHASES = frozenset({"day_discussion", "day_vote"})


def find_outcomes(game: dict, window_days: int) -> list[tuple[str, str, int, int, str]]:
    """The game's finds as (finder, target, open_day, resolution_day, outcome) with outcome in
    {"positive", "negative"}; voided finds are dropped here. resolution_day = the conversion day
    for a positive, else the last day the window actually covered."""
    roles = game.get("roles") or {}
    finder = next((p for p, r in roles.items() if r == "investigator"), None)
    if finder is None:
        return []
    day_lynch = {dr.get("day"): dr.get("voted_player") for dr in game.get("day_resolutions", [])}
    night_deaths = {nr.get("day"): set(nr.get("deaths") or []) for nr in game.get("night_resolutions", [])}
    played_days = set(day_lynch)
    out = []
    for nr in game.get("night_resolutions", []):
        target, d = nr.get("investigator_target"), nr.get("day")
        if not target or d is None or roles.get(target) not in THREAT_ROLES:
            continue
        open_day, close_day = d + 1, d + window_days
        resolution: tuple[int, str] | None = None
        last_played = None
        for day in range(open_day, close_day + 1):
            if target in night_deaths.get(day - 1, set()):
                resolution = None                       # night-killed before day `day` => voided
                break
            if day not in played_days:
                # game over mid-window: negative on the played days (the early-end deadlock case);
                # voided only when the window never opened at all
                resolution = (last_played, "negative") if last_played is not None else None
                break
            last_played = day
            if day_lynch.get(day) == target:
                resolution = (day, "positive")
                break
        else:
            resolution = (close_day, "negative")        # full window played, never converted
        if resolution:
            out.append((finder, target, open_day, resolution[0], resolution[1]))
    return out


def conversion_base(off_glob: str, window_days: int) -> tuple[float, int]:
    """The OFF arm's find-conversion mean through the SAME construct (+1 converted / -1 not) — the
    same-grading-function base the lift differences against. (0.0, 0) if the OFF window holds no
    resolvable finds."""
    vals = [1.0 if outcome == "positive" else -1.0
            for g in _iter_game_records(off_glob)
            for (_f, _t, _o, _r, outcome) in find_outcomes(g, window_days)]
    return (sum(vals) / len(vals), len(vals)) if vals else (0.0, 0)


def conversion_ledger(dumps_glob: str, window_days: int) -> dict[str, dict[str, int]]:
    """SP key -> {"pos": n, "neg": n}: each resolvable find tallies its outcome ONCE onto every SP
    the finder retrieved (any verdict) in a FINDER_PHASES case on a day inside
    [open_day, resolution_day]. Memory-ON games only."""
    ledger: dict[str, dict[str, int]] = defaultdict(lambda: {"pos": 0, "neg": 0})
    for g in _iter_game_records(dumps_glob):
        path = g.get("eval_cases_path")
        finds = find_outcomes(g, window_days)
        if not finds or not path or not os.path.exists(path):
            continue
        retrieved_by_day: dict[int, set[str]] = defaultdict(set)
        finder_ids = {f for (f, *_rest) in finds}
        for cl in open(path):
            if not cl.strip():
                continue
            ec = (json.loads(cl).get("output") or {}).get("eval_case") or {}
            if (ec.get("memory_enabled") and ec.get("player_id") in finder_ids
                    and ec.get("action_phase") in FINDER_PHASES):
                keys = (ec.get("strategy_index_to_key") or {}).values()
                retrieved_by_day[ec.get("day")].update(k for k in keys if k)
        for (_finder, _target, open_day, resolution_day, outcome) in finds:
            window_keys: set[str] = set()
            for day in range(open_day, resolution_day + 1):
                window_keys |= retrieved_by_day.get(day, set())
            for key in window_keys:
                ledger[key]["pos" if outcome == "positive" else "neg"] += 1
    return dict(ledger)


def conversion_lift(value: dict, base_mean: float = 0.0) -> float | None:
    """Shrunk conversion lift from a stored SP's conversion counters — sp_lift's exact shape on
    the conversion channel, so prune_tau means the same thing on both terms. None if no tallies."""
    pos, neg = value.get("conversion_pos_count", 0), value.get("conversion_neg_count", 0)
    n = pos + neg
    if not n:
        return None
    lift = (pos - neg) / n - base_mean
    return lift * n / (n + SHRINK_K)


def conversion_apply(store_sp_path: str | Path, dumps_glob: str, off_window: str | None,
                     window_days: int) -> dict:
    """Recompute the conversion ledger over this window's ON dumps and SET conversion_pos/neg
    counts on the store's SPs (zeroed first — window semantics), then upsert the OFF-arm
    conversion base into the sidecar base_rates.json (read-modify-write; credit_apply writes that
    file earlier in the same tick and must not be clobbered)."""
    store_sp_path = Path(store_sp_path)
    store = json.loads(store_sp_path.read_text())
    ledger = conversion_ledger(dumps_glob, window_days)
    base = conversion_base(off_window, window_days) if off_window else (0.0, 0)
    matched = total = 0
    for recs in store.get("namespaces", {}).values():
        for r in recs:
            total += 1
            v = r["value"]
            v["conversion_pos_count"] = v["conversion_neg_count"] = 0
            c = ledger.get(r["key"])
            if c:
                v["conversion_pos_count"], v["conversion_neg_count"] = c["pos"], c["neg"]
                matched += 1
    store_sp_path.write_text(json.dumps(store, indent=2))
    br_path = store_sp_path.parent / "base_rates.json"
    base_rates = json.loads(br_path.read_text()) if br_path.exists() else {}
    base_rates[CONVERSION_CHANNEL] = list(base)
    br_path.write_text(json.dumps(base_rates, indent=2))
    return {"total_sps": total, "conversion_credited": matched, "ledger_keys": len(ledger),
            "base": {CONVERSION_CHANNEL: base}}
