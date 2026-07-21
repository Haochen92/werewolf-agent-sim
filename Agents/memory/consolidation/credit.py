"""Production CREDIT-APPLY: write realized de-luck credit into a store's strategy points.

The graduated form of ``evaluation/src/loop/credit.py`` under the fixed grading rule (see
``credit_rules`` — no rule switches exist in production). Each tick recomputes the ledger over the
window's game records and SETS the positive/neutral/negative/follow counters on matching SPs —
window semantics (recomputed, not accumulated), so stale credit ages out with the window.

Channel map (one SP = one instrument): deterministic vote/night channels via ``credit_rules``;
day_discussion via the vote-endpoint floor + move-grain refinement; concealment-typed deceiver SPs
via the guarded concealment floor. Discussion credit is always on — it is part of the fixed system,
not a knob. The de-luck OFF bases come from the paired OFF window through the SAME instruments
(baseline coherence); ``base_for`` selects the right base family per SP.
"""

from __future__ import annotations

import json
import os
from collections import Counter, defaultdict
from pathlib import Path

from Agents.memory.consolidation.credit_rules import (
    VERDICT_VALUE,
    SPCredit,
    _iter_game_records,
    _vote_credit,
    build_ledger,
    compute_base_rates,
)
from Agents.memory.consolidation.decision_scoring import THREAT_ROLES

DECEIVER_ROLES = frozenset({"wolf", "serial_killer"})

# Concealment-floor verdict thresholds on the observed/expected heat ratio (expected = the day's
# accusation volume spread uniformly over the living). Knobs, not findings — chosen wide so only a
# clearly-cold or clearly-hot day moves the ledger; the middle stays neutral.
CONCEAL_POS_MAX = 0.5   # drew at most half its uniform share of the day's accusations
CONCEAL_NEG_MIN = 2.0   # drew at least twice its uniform share


def base_for(base_rates: dict, cell: str, sp_type: str | None = None) -> float:
    """The de-luck base MEAN to grade an SP against, produced by the SAME grading function as its
    counts (the baseline-coherence invariant): a concealment-typed SP differences against the
    ``conceal/<cell>`` OFF base; every other SP against its plain ``<cell>`` base."""
    key = f"conceal/{cell}" if sp_type == "concealment" else cell
    br = base_rates.get(key)
    return br[0] if br else 0.0


def _iter_disc_cases(dumps_glob: str):
    """Yield (game_record, roles, day_res_by_day, eval_case) for every day_discussion eval case —
    memory-ON and OFF alike; callers filter. Rides the teach-allowed record iterator (human guard)."""
    for g in _iter_game_records(dumps_glob):
        roles, path = g.get("roles"), g.get("eval_cases_path")
        if not roles or not path or not os.path.exists(path):
            continue
        day_res = {dr.get("day"): dr for dr in g.get("day_resolutions", [])}
        for cl in open(path):
            if not cl.strip():
                continue
            ec = (json.loads(cl).get("output") or {}).get("eval_case") or {}
            if ec.get("action_phase") == "day_discussion":
                yield g, roles, day_res, ec


def _move_grain_credit(ec: dict, lynched: str | None, roles: dict) -> str | None:
    """The move-grain refinement: when THIS turn's stance-tagged accusation is where the day's
    lynch landed, the instance is scored against the target's faction value instead of the day
    smear. None => no accusation landed (fall back to the day-grain tick).

    Deceivers: any landed push advances them (bussing-aware by construction). Town: landed x threat
    credits; landed x town is the read-partition case — excluded from the SP ledger, the read
    ledger carries the miss."""
    if not lynched:
        return None
    msg = ec.get("agent_message") or {}
    targets = {t.get("target") for t in (msg.get("addressed_targets") or [])
               if t.get("stance") == "accusation"}
    if lynched not in targets:
        return None
    if ec.get("player_role") in DECEIVER_ROLES:
        return "positive"
    return "positive" if roles.get(lynched) in THREAT_ROLES else "read_excluded"


def _disc_case_verdict(ec: dict, day_res_by_day: dict, roles: dict) -> str:
    """One discussion decision's endpoint verdict — the SAME instrument on both arms: the
    self-lynch guard first, then the move-grain refinement, then the day-grain faction tick.
    NOTE the day-grain tick here grades the day's LYNCH, not this speaker's abstain, so the fixed
    abstain rule never enters this channel — day_res=None keeps the endpoint tick identical to the
    eval-era instrument."""
    lynched = (day_res_by_day.get(ec.get("day")) or {}).get("voted_player")
    if lynched and lynched == ec.get("player_id"):
        return "negative"
    mg = _move_grain_credit(ec, lynched, roles)
    return mg if mg is not None else _vote_credit(ec.get("player_role"), lynched, roles)


def _spoke(ec: dict) -> bool:
    """Did this discussion turn produce a real utterance? A passed/empty turn demonstrably enacted
    no speech SP, so the discussion ledger credits spoken turns only (applied to the OFF base too —
    same instrument on both arms)."""
    msg = ec.get("agent_message") or {}
    return not msg.get("passed") and bool((msg.get("message") or "").strip())


def _discussion_ledger(dumps_glob: str, conceal_keys: frozenset = frozenset()) -> tuple[dict, Counter]:
    """The endpoint floor + move-grain refinement: credit day_discussion SPs the memory-ON agent
    FOLLOWED, on SPOKEN turns only. Concealment-typed SPs are excluded — they are credited by their
    own floor (one SP = one instrument). Returns ({sp_key: SPCredit}, skipped counter)."""
    ledger: dict = defaultdict(SPCredit)
    skipped: Counter = Counter()
    for _g, roles, day_res, ec in _iter_disc_cases(dumps_glob):
        if not ec.get("memory_enabled") or not ec.get("strategy_verdicts"):
            continue
        if not _spoke(ec):
            skipped[f"passed_turn/{ec.get('player_role')}/day_discussion"] += 1
            continue
        v = _disc_case_verdict(ec, day_res, roles)
        if v == "read_excluded":
            skipped[f"read_excluded/{ec.get('player_role')}/day_discussion"] += 1
            continue
        ch = f"{ec.get('player_role')}/day_discussion"
        idx = ec.get("strategy_index_to_key") or {}
        for sv in ec["strategy_verdicts"]:
            if sv.get("verdict") == "follow":
                key = idx.get(str(sv.get("strategy_index")))
                if key and key not in conceal_keys:
                    ledger[key].add(v, ch, 0.0)  # base irrelevant to the store write (counts only)
    return dict(ledger), skipped


def _discussion_off_base(off_dumps_glob: str) -> dict:
    """Floor discussion base from the TRUE OFF arm: mean endpoint verdict of memory-OFF
    day_discussion decisions per role channel — the SAME grading function as the ledger.
    Returns channel -> (mean, n)."""
    sums, ns = defaultdict(float), defaultdict(int)
    for _g, roles, day_res, ec in _iter_disc_cases(off_dumps_glob):
        if ec.get("memory_enabled") or not _spoke(ec):
            continue
        v = _disc_case_verdict(ec, day_res, roles)
        if v not in VERDICT_VALUE:
            continue
        ch = f"{ec.get('player_role')}/day_discussion"
        sums[ch] += VERDICT_VALUE[v]
        ns[ch] += 1
    return {ch: (sums[ch] / ns[ch], ns[ch]) for ch in ns}


# ── the concealment floor ─────────────────────────────────────────────────────────────────────────


def _game_day_heat(g: dict) -> tuple[Counter, Counter, set, dict]:
    """Public accusation-heat census for one game: heat[(day, player)] = accusation-stance tags
    received that day, total[day] = all accusation tags that day (the opportunity normalizer),
    spoke = (day, player) pairs with a real utterance, alive_n[day] = living players entering that
    day (roster minus prior night deaths and lynches)."""
    heat: Counter = Counter()
    total: Counter = Counter()
    spoke: set = set()
    for m in g.get("day_channel", []):
        if m.get("passed") or m.get("player") == "game_master":
            continue
        d = m.get("day")
        spoke.add((d, m.get("player")))
        for t in m.get("addressed_targets") or []:
            if t.get("stance") == "accusation" and t.get("target"):
                heat[(d, t["target"])] += 1
                total[d] += 1
    dead_from: dict = {}
    for nr in g.get("night_resolutions", []):
        for p in nr.get("deaths") or []:
            dead_from.setdefault(p, nr.get("day", 0) + 1)
    for dr in g.get("day_resolutions", []):
        if dr.get("voted_player"):
            dead_from.setdefault(dr["voted_player"], dr.get("day", 0) + 1)
    roster = list(g.get("roles") or {})
    days = {d for d, _ in spoke} | set(total)
    alive_n = {d: sum(1 for p in roster if dead_from.get(p, 10 ** 9) > d) for d in days}
    return heat, total, spoke, alive_n


def _conceal_verdict(received: int, day_total: int, n_alive: int) -> str | None:
    """One deceiver player-day's concealment verdict from the heat ratio (observed accusations
    received over the uniform share). None = no opportunity — a day with zero accusations anywhere
    gives every deceiver zero heat for free, so it credits nobody."""
    if not day_total or not n_alive:
        return None
    ratio = received / (day_total / n_alive)
    if ratio <= CONCEAL_POS_MAX:
        return "positive"
    if ratio >= CONCEAL_NEG_MIN:
        return "negative"
    return "neutral"


def _concealment_ledger(dumps_glob: str, conceal_keys: frozenset) -> tuple[dict, Counter]:
    """The concealment floor: per deceiver player-day, the accusation-heat verdict, credited ONCE
    per day to each concealment-typed SP followed on any of that day's discussion turns. Guard 1:
    normalized by the day's accusation volume. Guard 2: the agent must have SPOKEN that day —
    silence cannot farm the credit. Channel key ``conceal/<role>/day_discussion``."""
    if not conceal_keys:
        return {}, Counter()
    per_day: dict[tuple, set] = defaultdict(set)
    stats_by_game: dict = {}
    for g, _roles, _day_res, ec in _iter_disc_cases(dumps_glob):
        if not ec.get("memory_enabled") or not ec.get("strategy_verdicts"):
            continue
        if ec.get("player_role") not in DECEIVER_ROLES:
            continue
        gid = g.get("game_id")
        if gid not in stats_by_game:
            stats_by_game[gid] = _game_day_heat(g)
        idx = ec.get("strategy_index_to_key") or {}
        keys = {idx.get(str(sv.get("strategy_index"))) for sv in ec["strategy_verdicts"]
                if sv.get("verdict") == "follow"} & conceal_keys
        if keys:
            per_day[(gid, ec.get("day"), ec.get("player_id"), ec.get("player_role"))] |= keys
    ledger: dict = defaultdict(SPCredit)
    skipped: Counter = Counter()
    for (gid, day, player, role), keys in per_day.items():
        heat, total, spoke, alive_n = stats_by_game[gid]
        if (day, player) not in spoke:
            skipped[f"conceal_silent/{role}"] += 1
            continue
        v = _conceal_verdict(heat.get((day, player), 0), total.get(day, 0), alive_n.get(day, 0))
        if v is None:
            skipped[f"conceal_no_opportunity/{role}"] += 1
            continue
        for k in keys:
            ledger[k].add(v, f"conceal/{role}/day_discussion", 0.0)
    return dict(ledger), skipped


def _conceal_off_base(off_dumps_glob: str) -> dict:
    """Ambient concealment verdict of memory-OFF deceiver player-days (same instrument: spoke-gated,
    opportunity-normalized) — the ``conceal/<role>/day_discussion`` OFF base."""
    sums, ns = defaultdict(float), defaultdict(int)
    stats_by_game: dict = {}
    seen: set = set()
    for g, _roles, _day_res, ec in _iter_disc_cases(off_dumps_glob):
        if ec.get("memory_enabled") or ec.get("player_role") not in DECEIVER_ROLES:
            continue
        gid = g.get("game_id")
        key = (gid, ec.get("day"), ec.get("player_id"))
        if key in seen:
            continue
        seen.add(key)
        if gid not in stats_by_game:
            stats_by_game[gid] = _game_day_heat(g)
        heat, total, spoke, alive_n = stats_by_game[gid]
        if (ec.get("day"), ec.get("player_id")) not in spoke:
            continue
        v = _conceal_verdict(heat.get((ec.get("day"), ec.get("player_id")), 0),
                             total.get(ec.get("day"), 0), alive_n.get(ec.get("day"), 0))
        if v is None:
            continue
        ch = f"conceal/{ec.get('player_role')}/day_discussion"
        sums[ch] += VERDICT_VALUE[v]
        ns[ch] += 1
    return {ch: (sums[ch] / ns[ch], ns[ch]) for ch in ns}


def _adoption_counts(dumps_glob: str) -> dict:
    """Per SP key over the window's memory-ON eval cases: retrieved / override / not_relevant
    counts, SET from strategy_verdicts + strategy_index_to_key — the live-adoption half, recomputed
    windowed so the scope-aware evict rule has signal."""
    counts: dict = defaultdict(lambda: {"retrieved": 0, "override": 0, "not_relevant": 0})
    for g in _iter_game_records(dumps_glob):
        roles, path = g.get("roles"), g.get("eval_cases_path")
        if not roles or not path or not os.path.exists(path):
            continue
        for cl in open(path):
            if not cl.strip():
                continue
            ec = (json.loads(cl).get("output") or {}).get("eval_case") or {}
            if not ec.get("memory_enabled"):
                continue
            idx = ec.get("strategy_index_to_key") or {}
            for sv in ec.get("strategy_verdicts") or []:
                key = idx.get(str(sv.get("strategy_index")))
                if not key:
                    continue
                counts[key]["retrieved"] += 1
                verd = sv.get("verdict")
                if verd == "override":
                    counts[key]["override"] += 1
                elif verd == "not_relevant":
                    counts[key]["not_relevant"] += 1
    return dict(counts)


def _grading_of(cell: str) -> str:
    """Which grading function produced this cell's credited counts: 'conceal' / 'floor' /
    'deterministic' — drives the baseline-coherence invariant."""
    if cell.startswith("conceal/"):
        return "conceal"
    if cell.endswith("/day_discussion"):
        return "floor"
    return "deterministic"


def credit_apply(store_sp_path: str | Path, dumps_glob: str,
                 base_rates: dict | None = None,
                 off_window: str | None = None) -> dict:
    """Recompute the fixed-rule ledger over ``dumps_glob`` and SET the credit counters on matching
    SPs in ``store_sp_path``; persist the per-cell de-luck baseline next to the store. base_rates
    default = memory-off per-cell means from the same dumps; production passes the paired OFF
    window's rates. ``off_window`` supplies the SAME-INSTRUMENT OFF baseline for the discussion +
    concealment channels — without it those grade against 0 (level, not lift)."""
    store_sp_path = Path(store_sp_path)
    store = json.loads(store_sp_path.read_text())
    conceal_keys = frozenset(
        r["key"] for recs in store.get("namespaces", {}).values() for r in recs
        if r.get("value", {}).get("sp_type") == "concealment")
    base_rates = dict(base_rates if base_rates is not None else compute_base_rates(dumps_glob))
    ledger, det_skipped = build_ledger(dumps_glob, base_rates)
    skipped = Counter({k: n for k, n in det_skipped.items() if k.startswith("read_excluded/")})
    disc_ledger, disc_skipped = _discussion_ledger(dumps_glob, conceal_keys)
    conceal_ledger, conceal_skipped = _concealment_ledger(dumps_glob, conceal_keys)
    skipped.update(disc_skipped)
    skipped.update(conceal_skipped)
    # keys are disjoint: cells are (role, phase)-partitioned by retrieval, and concealment-typed
    # SPs are excluded from the endpoint ledger (one SP = one instrument).
    ledger = {**ledger, **disc_ledger, **conceal_ledger}
    if off_window:  # same-instrument OFF bases, never ON-window incidentals
        for cell, mn in _discussion_off_base(off_window).items():
            base_rates[cell] = mn
        for cell, mn in _conceal_off_base(off_window).items():
            base_rates[cell] = mn
    disc_credited = len(disc_ledger) + len(conceal_ledger)  # the engaged-guard signal

    adoption = _adoption_counts(dumps_glob)
    matched = credited = total = 0
    for recs in store.get("namespaces", {}).values():
        for r in recs:
            total += 1
            v = r["value"]
            # window semantics: zero every window-scoped counter before applying this window's
            # ledger, so an SP absent from the window stops carrying fossil credit.
            v["positive_count"] = v["neutral_count"] = v["negative_count"] = v["follow_count"] = 0
            v["retrieved_count"] = v["override_count"] = v["not_relevant_count"] = 0
            a = adoption.get(r["key"])
            if a:
                v["retrieved_count"] = a["retrieved"]
                v["override_count"] = a["override"]
                v["not_relevant_count"] = a["not_relevant"]
            c = ledger.get(r["key"])
            if c is None:
                continue
            matched += 1
            v["positive_count"] = c.positive
            v["neutral_count"] = c.neutral
            v["negative_count"] = c.negative
            v["follow_count"] = c.follow
            credited += 1
    store_sp_path.write_text(json.dumps(store, indent=2))
    (store_sp_path.parent / "base_rates.json").write_text(
        json.dumps({k: list(v) for k, v in base_rates.items()}, indent=2))
    credited_channels = {ch: _grading_of(ch) for c in ledger.values() for ch in c.channels}
    return {"total_sps": total, "credited": credited, "ledger_keys": len(ledger), "matched": matched,
            "disc_credited": disc_credited, "credited_channels": credited_channels,
            "read_excluded": sum(n for k, n in skipped.items() if k.startswith("read_excluded/")),
            "skipped": dict(skipped)}


def credit_distribution(store_sp_path: str | Path, min_follow: int = 8) -> dict:
    """How much the credit signal ENGAGED this tick — total SPs, # followed, follow p50/max,
    # prune-eligible and how many of those carry negative lift. Reads the just-credited store +
    the persisted base_rates."""
    store_sp_path = Path(store_sp_path)
    store = json.loads(store_sp_path.read_text())
    br_path = store_sp_path.parent / "base_rates.json"
    base_rates = json.loads(br_path.read_text()) if br_path.exists() else {}
    follows: list[int] = []
    n_sps = n_followed = eligible = eligible_neg = 0
    for ns, recs in store.get("namespaces", {}).items():
        cell = "/".join(ns.split("/")[1:])              # strategy_points/role/phase -> role/phase
        for r in recs:
            v = r["value"]
            f = v.get("follow_count", 0)
            n_sps += 1
            follows.append(f)
            if f > 0:
                n_followed += 1
            if f >= min_follow:
                eligible += 1
                lf = sp_lift(v, base_for(base_rates, cell, v.get("sp_type")))
                if lf is not None and lf < 0:
                    eligible_neg += 1
    follows.sort()
    return {"n_sps": n_sps, "n_followed": n_followed,
            "follow_p50": follows[len(follows) // 2] if follows else 0,
            "follow_max": follows[-1] if follows else 0,
            "n_prune_eligible": eligible, "n_eligible_neg_lift": eligible_neg}


def sp_lift(value: dict, base_mean: float = 0.0) -> float | None:
    """De-luck shrunk-lift for a stored SP from its counts + the per-cell baseline. None if no
    follows. utility = (positive - negative)/follow; lift = utility - base_mean; shrunk =
    lift * follow/(follow+5)."""
    follow = value.get("follow_count", 0)
    if not follow:
        return None
    util = (value.get("positive_count", 0) - value.get("negative_count", 0)) / follow
    lift = util - base_mean
    return lift * follow / (follow + 5)
