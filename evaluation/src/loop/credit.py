"""Compounding loop — (a) CREDIT-APPLY: write realized de-luck credit into a store's strategy points.

Between generations the loop credits the SPs an agent FOLLOWED by the de-luck outcome of the decisions
they drove (reusing credit_backfill's faction-relative de-luck scoring), and writes the
positive/neutral/negative tallies onto the StoredStrategyPoint counts — the signal (b) consolidation
weights by. Adoption already writes follow/override live; this fills the outcome half that was only ever
backfilled offline.

Day discussion is credited by the v1 wiring (evidence/credit/report.md §3, rulings 2026-07-11→13):
- the DAY-GRAIN endpoint tick (the validated free floor, held-out Pearson +0.51) with a self-lynch guard,
- refined at MOVE GRAIN when this turn's stance-tagged accusation is where the day's lynch landed
  (deceivers: any landed push is positive — bussing-aware by construction; town: landed × threat
  credits, landed × town is the read-partition case and is EXCLUDED, the read ledger carries the miss),
- plus the CONCEALMENT FLOOR for deceivers' concealment-typed SPs (their own channel + OFF base — one
  SP is credited by exactly one instrument, so its lift differences against the right ambient).

The omniscient-tagger credit mode was RETIRED 2026-07-13 (owner ruling): the tagger survives as a
standalone diagnostic (discussion_tagger.py, run post-hoc on stored games) and never feeds prune,
protect, or synthesis; night credit is the deterministic scorer with the read-partition.

ROLLING WINDOW = the dumps glob: pass only the recent W generations' batch records and the counts are
RECOMPUTED (set, not accumulated) over that window each tick, so stale credit ages out — the
non-stationarity guard, for free.
"""

from __future__ import annotations

import json
import os
from collections import Counter, defaultdict
from pathlib import Path

from evaluation.src.loop.credit_backfill import (
    VERDICT_VALUE, SPCredit, _expand_dumps, _vote_credit, build_ledger, compute_base_rates,
)
from evaluation.src.loop.decision_scoring import THREAT_ROLES

DECEIVER_ROLES = frozenset({"wolf", "serial_killer"})

# Concealment-floor verdict thresholds on the observed/expected heat ratio (expected = the day's
# accusation volume spread uniformly over the living). Knobs, not findings — chosen wide so only a
# clearly-cold or clearly-hot day moves the ledger; the middle stays neutral.
CONCEAL_POS_MAX = 0.5   # drew at most half its uniform share of the day's accusations
CONCEAL_NEG_MIN = 2.0   # drew at least twice its uniform share


def base_for(base_rates: dict, cell: str, sp_type: str | None = None) -> float:
    """The de-luck base MEAN to grade an SP against, produced by the SAME grading function as its counts
    (the baseline-coherence invariant): a concealment-typed SP is credited by the concealment floor, so
    it differences against the `conceal/<cell>` OFF base; every other SP differences against its plain
    `<cell>` base (deterministic vote/night, or the discussion endpoint floor). Keeps consolidate's
    sp_lift a LIFT, not a level."""
    key = f"conceal/{cell}" if sp_type == "concealment" else cell
    br = base_rates.get(key)
    return br[0] if br else 0.0


def _iter_disc_cases(dumps_glob: str):
    """Yield (game_record, roles, day_res_by_day, eval_case) for every day_discussion eval case —
    memory-ON and OFF alike; callers filter. day_res_by_day = day -> that day's resolution row."""
    for dump in _expand_dumps(dumps_glob):
        for line in open(dump):
            if not line.strip():
                continue
            g = json.loads(line)
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
    """The v1 move-grain refinement: when THIS turn's stance-tagged accusation is where the day's lynch
    landed, the instance is scored against the target's faction value instead of the day smear. None =>
    no accusation landed (fall back to the day-grain tick).

    Deceivers: any landed push advances them — a mislynch and a lynched SK are both positive wolf value,
    and a landed packmate push IS the room's plurality by construction, so the bussing-aware form
    collapses to positive; no read gate (deception decouples belief from move). Town: the accusation
    stance IS the stated threat-read, so landed × threat credits and landed × town is the read-partition
    case — excluded from the SP ledger ("read_excluded"), the read ledger carries the miss."""
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
    """One discussion decision's endpoint verdict — the SAME instrument on both arms (ON credit and OFF
    base): the self-lynch guard first (the reused vote rule is blind to it: an SK lynched on its own day
    would otherwise read 'positive — any non-self lynch'), then the move-grain refinement, then the
    day-grain faction tick (`_vote_credit` on the day's lynch; no-lynch days are neutral)."""
    lynched = (day_res_by_day.get(ec.get("day")) or {}).get("voted_player")
    if lynched and lynched == ec.get("player_id"):
        return "negative"
    mg = _move_grain_credit(ec, lynched, roles)
    return mg if mg is not None else _vote_credit(ec.get("player_role"), lynched, roles)


def _spoke(ec: dict) -> bool:
    """Did this discussion turn produce a real utterance? A passed/empty turn demonstrably enacted no
    speech SP — the n=15 attribution spot-check's both misses were exactly follow-claims on passed
    turns (evidence/credit/attribution_spot_check.json, 2026-07-13) — so the discussion ledger credits
    spoken turns only. Applied to the OFF base too (same instrument on both arms)."""
    msg = ec.get("agent_message") or {}
    return not msg.get("passed") and bool((msg.get("message") or "").strip())


def _discussion_ledger(dumps_glob: str, conceal_keys: frozenset = frozenset()) -> tuple[dict, Counter]:
    """(d) the endpoint floor + move-grain refinement: credit day_discussion SPs the memory-ON agent
    FOLLOWED by `_disc_case_verdict`, on SPOKEN turns only (`_spoke` — the pass-while-claiming-follow
    gate). Concealment-typed SPs are excluded here — they are credited by their own floor
    (`_concealment_ledger`), one SP = one instrument. The de-luck base is NOT computed here — it comes
    from `_discussion_off_base` over the true OFF arm (fixing the §11j incidental-off defect). Returns
    ({sp_key: SPCredit}, skipped counter incl. the read-partition + passed-turn drops)."""
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
    """Floor discussion base from the TRUE OFF arm: mean endpoint verdict of memory-OFF day_discussion
    decisions per role channel — the SAME grading function as `_discussion_ledger` (self-lynch guard and
    move-grain refinement included: addressed_targets exist on both arms, so the instrument is identical).
    Read-partition drops fall out of the base too (same instrument on both sides). Returns
    channel -> (mean, n)."""
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
    """Public accusation-heat census for one game: heat[(day, player)] = accusation-stance tags received
    that day, total[day] = all accusation tags that day (the opportunity normalizer), spoke = (day,
    player) pairs with a real utterance, alive_n[day] = living players entering that day (roster minus
    prior night deaths and lynches — a lynch on day d removes the player from day d+1 on)."""
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
    """One deceiver player-day's concealment verdict from the heat ratio (observed accusations received
    over the uniform share). None = no opportunity — a day with zero accusations anywhere gives every
    deceiver zero heat for free, so it credits nobody (guard 1)."""
    if not day_total or not n_alive:
        return None
    ratio = received / (day_total / n_alive)
    if ratio <= CONCEAL_POS_MAX:
        return "positive"
    if ratio >= CONCEAL_NEG_MIN:
        return "negative"
    return "neutral"


def _concealment_ledger(dumps_glob: str, conceal_keys: frozenset) -> tuple[dict, Counter]:
    """The concealment floor (report §3): per deceiver player-day, the accusation-heat verdict, credited
    ONCE per day to each concealment-typed SP followed on any of that day's discussion turns. Guard 1:
    normalized by the day's accusation volume (`_conceal_verdict`). Guard 2: the agent must have SPOKEN
    that day — silence cannot farm the credit, or the store re-learns the passive play the credit prune
    just removed. Channel key `conceal/<role>/day_discussion` (its own baseline family). Empty when the
    store carries no concealment-typed SPs — the sp_type tag ships with synthesis from this build on, so
    legacy stores earn nothing here by construction."""
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
    opportunity-normalized) — the `conceal/<role>/day_discussion` OFF base the floor's lift differences
    against."""
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
    """Per SP key over the window's memory-ON eval cases: retrieved / override / not_relevant counts, SET
    from strategy_verdicts + strategy_index_to_key. This is the live-adoption half `Agents/turn/adoption.py`
    writes per-game but that NEVER reaches the run store (merge folds observations only —
    merge.py::merge_new_obs memory_kinds=["observations"]), so it is recomputed here, WINDOWED with the
    credit ledger (Finding 2/3). Makes the evict rule (_evict_ok needs override_count>0) live for the
    first time. retrieved counts every verdicted surfacing (follow included), matching adoption semantics."""
    counts: dict = defaultdict(lambda: {"retrieved": 0, "override": 0, "not_relevant": 0})
    for dump in _expand_dumps(dumps_glob):
        for line in open(dump):
            if not line.strip():
                continue
            g = json.loads(line)
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
    """Which grading function produced this cell's credited counts: 'conceal' (the concealment floor,
    self-keyed channel), 'floor' (the discussion endpoint), else 'deterministic'. Drives the
    baseline-coherence invariant; the same-function base selection is base_for's job."""
    if cell.startswith("conceal/"):
        return "conceal"
    if cell.endswith("/day_discussion"):
        return "floor"
    return "deterministic"


def credit_apply(store_sp_path: str | Path, dumps_glob: str,
                 base_rates: dict | None = None, discussion: bool = True,
                 off_window: str | None = None, *,
                 abstain_rule: str = "neutral") -> dict:
    """Recompute the de-luck ledger over `dumps_glob` and SET positive/neutral/negative/follow counts on
    matching SPs in `store_sp_path` (strategy_points.json). Returns stats incl. `credited_channels`
    ({channel: grading}) for the baseline-coherence invariant and `read_excluded` (the partition's drops).

    base_rates default = memory-off per-cell means computed from the same dumps (the de-luck baseline);
    pass a frozen set to reuse a calibration baseline across generations. `off_window` (the paired OFF-arm
    dumps) supplies the SAME-INSTRUMENT OFF baseline for the discussion + concealment channels — without
    it those fall back to base 0 (the level-not-lift bug the driver's baseline-coherence invariant then
    catches). `discussion` additionally credits day_discussion SPs (endpoint + move grain + the
    concealment floor for typed SPs). `abstain_rule` (LoopConfig.abstain_credit, keyword-only) threads
    ONE grading rule into both the ledger and the default base-rate computation — baseline coherence by
    construction. NOTE: a caller passing frozen `base_rates` under "deadlock_negative" must have computed
    them under the same rule."""
    store_sp_path = Path(store_sp_path)
    store = json.loads(store_sp_path.read_text())
    conceal_keys = frozenset(
        r["key"] for recs in store.get("namespaces", {}).values() for r in recs
        if r.get("value", {}).get("sp_type") == "concealment")
    base_rates = dict(base_rates if base_rates is not None
                      else compute_base_rates(dumps_glob, abstain_rule=abstain_rule))
    ledger, det_skipped = build_ledger(dumps_glob, base_rates, abstain_rule=abstain_rule)
    skipped = Counter({k: n for k, n in det_skipped.items() if k.startswith("read_excluded/")})
    disc_credited = 0
    if discussion:
        disc_ledger, disc_skipped = _discussion_ledger(dumps_glob, conceal_keys)
        conceal_ledger, conceal_skipped = _concealment_ledger(dumps_glob, conceal_keys)
        skipped.update(disc_skipped)
        skipped.update(conceal_skipped)
        # keys are disjoint: cells are (role, phase)-partitioned by retrieval, and concealment-typed SPs
        # are excluded from the endpoint ledger (one SP = one instrument).
        ledger = {**ledger, **disc_ledger, **conceal_ledger}
        if off_window:  # same-instrument OFF bases, never ON-window incidentals (§11j/Finding 1c)
            for cell, mn in _discussion_off_base(off_window).items():
                base_rates[cell] = mn
            for cell, mn in _conceal_off_base(off_window).items():
                base_rates[cell] = mn
        disc_credited = len(disc_ledger) + len(conceal_ledger)  # the engaged-guard signal:
        #   0 while there are discussion follows in the window = the floor silently produced nothing.

    adoption = _adoption_counts(dumps_glob)     # Finding 3: retrieved/override/not_relevant, windowed
    matched = credited = total = 0
    for recs in store.get("namespaces", {}).values():
        for r in recs:
            total += 1
            v = r["value"]
            # Finding 2: ZERO the window-scoped counters on EVERY SP before applying this window's ledger,
            # so an SP absent from THIS window stops carrying fossil credit into prune / protect /
            # _track_record / credit_distribution — the documented "recomputed, set not accumulated" window
            # semantics, now actually true. Safe: live per-game adoption bumps never reach the run store
            # (merge folds observations only), so zeroing can't clobber anything real.
            v["positive_count"] = v["neutral_count"] = v["negative_count"] = v["follow_count"] = 0
            v["retrieved_count"] = v["override_count"] = v["not_relevant_count"] = 0
            a = adoption.get(r["key"])           # Finding 3: SET adoption counters from the window's cases
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
    # persist the per-cell de-luck baseline next to the store: consolidation needs it to compute LIFT
    # (raw pos/neg counts carry the halo — e.g. SK non-abstain is ~always "positive"; lift = utility −
    # baseline is the real de-luck signal). base_rates: channel "role/phase" -> (mean, n); concealment
    # cells carry their own `conceal/<cell>` entry that base_for selects by sp_type.
    (store_sp_path.parent / "base_rates.json").write_text(
        json.dumps({k: list(v) for k, v in base_rates.items()}, indent=2))
    # credited_channels: which grading function actually produced each credited cell's counts, for the
    # baseline-coherence invariant (a floor/conceal cell needs a non-degenerate same-instrument OFF base).
    credited_channels = {ch: _grading_of(ch) for c in ledger.values() for ch in c.channels}
    return {"total_sps": total, "credited": credited, "ledger_keys": len(ledger), "matched": matched,
            "disc_credited": disc_credited, "credited_channels": credited_channels,
            "read_excluded": sum(n for k, n in skipped.items() if k.startswith("read_excluded/")),
            "skipped": dict(skipped)}


def credit_distribution(store_sp_path: str | Path, min_follow: int = 8) -> dict:
    """How much the credit signal ENGAGED this tick — so a flat slope stays INTERPRETABLE (did prune get
    a fair shot, or did nothing reach the follow threshold?). Reads the just-credited SP store + the
    persisted base_rates. Reports: total SPs, # ever followed, follow p50/max, # prune-ELIGIBLE
    (follow>=min_follow), and how many of those have NEGATIVE lift (= real prune candidates). A flat trend
    with n_prune_eligible≈0 means the loop never had signal to cull (raise W), not that memory failed."""
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
    """De-luck shrunk-lift for a stored SP from its counts + the per-cell baseline. None if no follows.

    utility = (positive − negative)/follow; lift = utility − base_mean; shrunk = lift·follow/(follow+5).
    The baseline strip is what separates the SK −0.30 blend loser (raw utility +0.39) from a real winner.
    Caller supplies base_mean = base_for(base_rates, cell, sp_type) for this SP's namespace and type."""
    follow = value.get("follow_count", 0)
    if not follow:
        return None
    util = (value.get("positive_count", 0) - value.get("negative_count", 0)) / follow
    lift = util - base_mean
    return lift * follow / (follow + 5)


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--store-sp", required=True, help="strategy_points.json to credit (in place)")
    ap.add_argument("--dumps", required=True, help="glob of this window's batch records (eval-case-bearing)")
    args = ap.parse_args()
    print(credit_apply(args.store_sp, args.dumps))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
