"""Production CREDIT-APPLY: write realized de-luck credit into a store's strategy points.

Ten-seat since the port of 2026-10-13 (plan §9.6). Each tick recomputes the ledger over the window's
game records and SETS the positive/neutral/negative/follow counters on matching SPs — window
semantics (recomputed, not accumulated), so stale credit ages out with the window.

Channel map (one SP = one instrument): vote and night decisions via ``credit_rules`` (the grades are
``grading``); day discussion by the day's lynch, refined by a landed accusation, once per seat per day;
concealment-typed SPs of the evil seats by the accusation-heat floor. The memory-off bases come from
the paired OFF window through the SAME instruments (baseline coherence). Each SP's base is the
follow-weighted mean of its follows' channels (``credit_base``); a follow whose channel has no
memory-off data leaves the SP unscored, never compared with 0.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

from Agents.memory.consolidation.credit_rules import (
    VERDICT_RANK,
    VERDICT_VALUE,
    SPCredit,
    _iter_game_records,
    build_ledger,
    compute_base_rates,
    decision_scope,
    followed_keys,
    iter_eval_cases,
)
from Agents.memory.consolidation.grading import EVIL, GameView, side

# Concealment-floor verdict thresholds on the observed/expected heat ratio (expected = the day's
# accusation volume spread uniformly over the living). Knobs, not findings — chosen wide so only a
# clearly-cold or clearly-hot day moves the ledger; the middle stays neutral.
CONCEAL_POS_MAX = 0.5   # drew at most half its uniform share of the day's accusations
CONCEAL_NEG_MIN = 2.0   # drew at least twice its uniform share


def base_for(base_rates: dict, cell: str, sp_type: str | None = None) -> float | None:
    """The memory-off base MEAN of a cell (a concealment-typed SP: the ``conceal/<cell>`` base).
    None when the window has no memory-off data for it: unscored, not 0."""
    key = f"conceal/{cell}" if sp_type == "concealment" else cell
    br = base_rates.get(key)
    return br[0] if br else None


def sp_base(value: dict, base_rates: dict, cell: str) -> float | None:
    """The base an SP's lift is measured against: its own follow-weighted base when credit wrote one
    (``credit_base``, None = unscored), else its cell's (a store credited before the port)."""
    if "credit_base" in value:
        return value["credit_base"]
    return base_for(base_rates, cell, value.get("sp_type"))


def _is_evil(ec: dict) -> bool:
    return side(ec.get("player_role")) in EVIL


def _iter_disc_cases(dumps_glob: str):
    """Yield (game_record, view, eval_case) for every day_discussion eval case — memory-ON and OFF
    alike; callers filter. Rides the teach-allowed record iterator (human guard)."""
    for g in _iter_game_records(dumps_glob):
        view = GameView(g)
        for ec in iter_eval_cases(g):
            if ec.get("action_phase") == "day_discussion":
                yield g, view, ec


def _spoke(ec: dict) -> bool:
    """Did this discussion turn produce a real utterance? A passed/empty turn demonstrably enacted
    no speech SP, so the discussion ledger credits spoken turns only (applied to the OFF base too —
    same instrument on both arms)."""
    msg = ec.get("agent_message") or {}
    return not msg.get("passed") and bool((msg.get("message") or "").strip())


def _accused(ec: dict) -> set[str]:
    """The players this turn accused (stance-tagged accusations)."""
    msg = ec.get("agent_message") or {}
    return {t.get("target") for t in (msg.get("addressed_targets") or []) if t.get("stance") == "accusation"}


def _discussion_ledger(dumps_glob: str, conceal_keys: frozenset = frozenset()) -> tuple[dict, Counter]:
    """Day-discussion SPs the memory-ON seat FOLLOWED on a spoken turn, credited once per seat per
    day (``grading.discussion_grade``: its own lynch negative; an accusation of the lynched player on
    a turn that followed the SP graded on the target; else the day's lynch under the seat's lens).
    Concealment-typed SPs are left to their own floor (one SP = one instrument)."""
    per_day: dict[tuple, dict[str, set]] = defaultdict(lambda: defaultdict(set))
    meta: dict[tuple, tuple] = {}
    skipped: Counter = Counter()
    for g, view, ec in _iter_disc_cases(dumps_glob):
        if not ec.get("memory_enabled") or not ec.get("strategy_verdicts"):
            continue
        if not _spoke(ec):
            skipped[f"passed_turn/{ec.get('player_role')}/day_discussion"] += 1
            continue
        unit = (g.get("game_id"), ec.get("player_id"), ec.get("day"))
        meta[unit] = (view, ec.get("player_role"))
        for key in followed_keys(ec):
            if key not in conceal_keys:
                per_day[unit][key] |= _accused(ec)
    ledger: dict = defaultdict(SPCredit)
    for (gid, player, day), keys in per_day.items():
        view, role = meta[(gid, player, day)]
        for key, accused in keys.items():
            v = view.discussion_grade(player, role, day, accused)
            if v is None or v == "read_excluded":
                skipped[f"{v or 'unscored'}/{role}/day_discussion"] += 1
                continue
            ledger[key].add(v, f"{role}/day_discussion")
    return dict(ledger), skipped


def _discussion_off_base(off_dumps_glob: str) -> dict:
    """The discussion base from the memory-OFF arm: each seat-day's grade (the same function as the
    ledger, the day's spoken accusations pooled). Returns channel -> (mean, n)."""
    days: dict[tuple, set] = defaultdict(set)
    meta: dict[tuple, tuple] = {}
    for g, view, ec in _iter_disc_cases(off_dumps_glob):
        if ec.get("memory_enabled") or not _spoke(ec):
            continue
        unit = (g.get("game_id"), ec.get("player_id"), ec.get("day"))
        meta[unit] = (view, ec.get("player_role"))
        days[unit] |= _accused(ec)
    sums, ns = defaultdict(float), defaultdict(int)
    for (gid, player, day), accused in days.items():
        view, role = meta[(gid, player, day)]
        v = view.discussion_grade(player, role, day, accused)
        if v not in VERDICT_VALUE:
            continue
        ch = f"{role}/day_discussion"
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
    """The concealment floor: per evil player-day, the accusation-heat verdict, credited ONCE
    per day to each concealment-typed SP followed on any of that day's discussion turns. Guard 1:
    normalized by the day's accusation volume. Guard 2: the agent must have SPOKEN that day —
    silence cannot farm the credit. Channel key ``conceal/<role>/day_discussion``."""
    if not conceal_keys:
        return {}, Counter()
    per_day: dict[tuple, set] = defaultdict(set)
    stats_by_game: dict = {}
    for g, _view, ec in _iter_disc_cases(dumps_glob):
        if not ec.get("memory_enabled") or not ec.get("strategy_verdicts") or not _is_evil(ec):
            continue
        gid = g.get("game_id")
        if gid not in stats_by_game:
            stats_by_game[gid] = _game_day_heat(g)
        keys = set(followed_keys(ec)) & conceal_keys
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
            ledger[k].add(v, f"conceal/{role}/day_discussion")
    return dict(ledger), skipped


def _conceal_off_base(off_dumps_glob: str) -> dict:
    """Ambient concealment verdict of memory-OFF evil player-days (same instrument: spoke-gated,
    opportunity-normalized) — the ``conceal/<role>/day_discussion`` OFF base."""
    sums, ns = defaultdict(float), defaultdict(int)
    stats_by_game: dict = {}
    seen: set = set()
    for g, _view, ec in _iter_disc_cases(off_dumps_glob):
        if ec.get("memory_enabled") or not _is_evil(ec):
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
    counts, once per scope (the strongest verdict of the scope's turns: follow, then override), so
    the evict rule is not inflated by a lesson shown on every turn of a day."""
    per_scope: dict[tuple, str] = {}
    for g in _iter_game_records(dumps_glob):
        for ec in iter_eval_cases(g):
            if not ec.get("memory_enabled"):
                continue
            idx = ec.get("strategy_index_to_key") or {}
            for sv in ec.get("strategy_verdicts") or []:
                key = idx.get(str(sv.get("strategy_index")))
                if not key:
                    continue
                unit = (g.get("game_id"), decision_scope(ec), key)
                verdict = sv.get("verdict")
                if VERDICT_RANK.get(verdict, 0) >= VERDICT_RANK.get(per_scope.get(unit), 0):
                    per_scope[unit] = verdict
    counts: dict = defaultdict(lambda: {"retrieved": 0, "override": 0, "not_relevant": 0})
    for (_gid, _scope, key), verdict in per_scope.items():
        counts[key]["retrieved"] += 1
        if verdict in ("override", "not_relevant"):
            counts[key][verdict] += 1
    return dict(counts)


def _grading_of(cell: str) -> str:
    """Which grading function produced this cell's credited counts: 'conceal' / 'floor' /
    'deterministic' — drives the baseline-coherence invariant."""
    if cell.startswith("conceal/"):
        return "conceal"
    if cell.endswith("/day_discussion"):
        return "floor"
    return "deterministic"


def _merged_into(store: dict) -> dict[str, str]:
    """Discarded duplicate key -> the key of the lesson that absorbed it (``merged_keys``)."""
    return {merged: r["key"] for recs in store.get("namespaces", {}).values() for r in recs
            for merged in r.get("value", {}).get("merged_keys") or []}


def _fold_merged(ledger: dict, adoption: dict, alias: dict[str, str]) -> tuple[dict, dict]:
    """Credit and adoption counts recorded against a merged duplicate's key, added to its survivor's."""
    folded: dict = defaultdict(SPCredit)
    for key, c in ledger.items():
        f = folded[alias.get(key, key)]
        f.follow += c.follow
        f.positive += c.positive
        f.neutral += c.neutral
        f.negative += c.negative
        f.channels.update(c.channels)
    counts: dict = defaultdict(lambda: {"retrieved": 0, "override": 0, "not_relevant": 0})
    for key, a in adoption.items():
        for k, n in a.items():
            counts[alias.get(key, key)][k] += n
    return dict(folded), dict(counts)


def credit_apply(store_sp_path: str | Path, dumps_glob,
                 base_rates: dict | None = None,
                 off_window: str | None = None) -> dict:
    """Recompute the ledger over ``dumps_glob`` and SET the credit counters on matching SPs in
    ``store_sp_path``, with each SP's base (``credit_base``); persist the per-channel bases next to
    the store. ``dumps_glob``: a glob spec of batch-run dumps, or games already loaded
    (``sources``). A lesson the point dedup merged into another keeps its credit there (decisions §14). base_rates default = memory-off means from the same dumps; production passes the paired
    OFF window's. ``off_window`` supplies the same-instrument OFF bases for the discussion and
    concealment channels — without it those SPs stay unscored."""
    store_sp_path = Path(store_sp_path)
    store = json.loads(store_sp_path.read_text())
    conceal_keys = frozenset(
        r["key"] for recs in store.get("namespaces", {}).values() for r in recs
        if r.get("value", {}).get("sp_type") == "concealment")
    base_rates = dict(base_rates if base_rates is not None else compute_base_rates(dumps_glob))
    ledger, det_skipped = build_ledger(dumps_glob)
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
    ledger, adoption = _fold_merged(ledger, adoption, _merged_into(store))
    matched = credited = unscored = total = 0
    for recs in store.get("namespaces", {}).values():
        for r in recs:
            total += 1
            v = r["value"]
            # window semantics: zero every window-scoped counter before applying this window's
            # ledger, so an SP absent from the window stops carrying fossil credit.
            v["positive_count"] = v["neutral_count"] = v["negative_count"] = v["follow_count"] = 0
            v["retrieved_count"] = v["override_count"] = v["not_relevant_count"] = 0
            v["credit_base"] = None
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
            v["credit_base"] = c.base(base_rates)
            unscored += v["credit_base"] is None
            credited += 1
    store_sp_path.write_text(json.dumps(store, indent=2))
    (store_sp_path.parent / "base_rates.json").write_text(
        json.dumps({k: list(v) for k, v in base_rates.items()}, indent=2))
    credited_channels = {ch: _grading_of(ch) for c in ledger.values() for ch in c.channels}
    return {"total_sps": total, "credited": credited, "ledger_keys": len(ledger), "matched": matched,
            "unscored": unscored, "disc_credited": disc_credited, "credited_channels": credited_channels,
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
                lf = sp_lift(v, sp_base(v, base_rates, cell))
                if lf is not None and lf < 0:
                    eligible_neg += 1
    follows.sort()
    return {"n_sps": n_sps, "n_followed": n_followed,
            "follow_p50": follows[len(follows) // 2] if follows else 0,
            "follow_max": follows[-1] if follows else 0,
            "n_prune_eligible": eligible, "n_eligible_neg_lift": eligible_neg}


def sp_lift(value: dict, base_mean: float | None = 0.0) -> float | None:
    """De-luck shrunk-lift for a stored SP from its counts + its base. None if no follows or no base
    (unscored). utility = (positive - negative)/follow; lift = utility - base_mean; shrunk =
    lift * follow/(follow+5)."""
    follow = value.get("follow_count", 0)
    if not follow or base_mean is None:
        return None
    util = (value.get("positive_count", 0) - value.get("negative_count", 0)) / follow
    lift = util - base_mean
    return lift * follow / (follow + 5)
