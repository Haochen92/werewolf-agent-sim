"""v7 (a) — realized-outcome credit backfill over the v6ab dumps (zero spend, deterministic).

The credit-loop's job (plan §1b layer 3): give each strategy point a utility grounded in the realized
OUTCOME of the decisions where the agent FOLLOWED it — NOT the agent's follow/override choice, which
G3a showed is degenerate (~99% follow, no variance). The store already records the "use" half live
(`Agents/turn/adoption.py` bumps retrieved/follow/override during play); the missing half is the
OUTCOME tally (positive/neutral/negative_count), because nothing ever joined a followed decision back
to its result. This runner closes that join offline, on the already-generated dumps:

  followed SP (strategy_verdicts==follow → strategy_index_to_key) × the decision's de-lucked outcome
  (decision_scoring.score_vote / score_night_target — pure roles lookup, no model) → a credit LEDGER.

It is SP-only by design: observations are descriptive (you don't "follow" one), so they ride frequency
× criticality, protected by the extraction anchor — not post-hoc credit (see the §1a reframe). Reward
covers BOARD-OUTCOME decisions: day-votes (all roles) + night targets (investigator / vigilante / wolf /
serial_killer / healer — healer landed 2026-07-13 once the wolf-blend join made each game record, and
with it the night_resolutions attack-join, available to the pass; the rule mirrors the validated
★healer_town_save_rate construct in Agents/compute_metrics.py, +0.40 at N=180).

Two v1 rules ride the night path (evidence/credit/report.md §3, rulings 2026-07-13):
- READ-PARTITION: a negative outcome reached through a stated-and-wrong high-confidence threat-read on
  the target is EXCLUDED from the SP ledger ("read_excluded") — the belief failed, not the procedure;
  the wrong read is already priced by the read ledger (read_ledger.py scores every read at reveal, so
  exclusion here needs no extra penalty write). No stated read / low confidence / 'unclear' => credit
  normally: exclusion requires evidence of a wrong belief, not the absence of one. Legacy dumps
  (pre-2026-07-09) carry no reads field, so the partition no-ops there by construction.
- The reveal/confirm-only class stays unscorable by outcome; day discussion is credited by the
  vote-endpoint floor + move-grain refinement in credit.py.

Compute is decoupled from the store-write: we emit the ledger + a validation read and STOP — no store
is mutated until the signal is shown to separate. Applying the ledger to a v6_1 copy is a later step.

  poetry run python evaluation/src/loop/credit_backfill.py
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from evaluation.src.loop.decision_scoring import (  # noqa: E402
    THREAT_ROLES, score_night_target, score_vote,
)

DEFAULT_DUMPS = "batch_results/*v6ab*.jsonl"
DEFAULT_STORE = "memory_stores/v6_1"
DEFAULT_LEDGER = "evidence/v7_final/credit_backfill_ledger.json"


def _expand_dumps(dumps_glob: str) -> list[str]:
    """Expand a dumps spec that is EITHER a single glob pattern OR a whitespace-joined list of
    paths/patterns (the loop's rolling window passes the latter). Plain `glob.glob` treats the whole
    space-separated string as ONE pattern and matches nothing — silently emptying the credit ledger for
    any window spanning >1 generation (a single-generation smoke can't surface it)."""
    return sorted(f for pat in dumps_glob.split() for f in glob.glob(pat))

# Per-channel mapping from a deterministic outcome to a credit verdict. None = decision not creditable
# this round (skipped, counted separately). Each returns "positive" | "neutral" | "negative".
# healer joined 2026-07-13 (the attack-join rides the same game record the wolf blend already loads);
# its credit degrades to None when a caller has no night_resolutions to join against.
NIGHT_CREDIT_ROLES = frozenset({"investigator", "vigilante", "wolf", "serial_killer", "healer"})

VERDICT_VALUE = {"positive": 1.0, "neutral": 0.0, "negative": -1.0}
SHRINK_K = 5  # low-follow SPs pull toward 0 lift: shrunk = lift * follow/(follow+K)


TOWN_VOTE_ROLES = frozenset({"villager", "healer", "investigator", "vigilante"})


def _majority_vote(day_res: dict) -> str | None:
    """The room's plurality vote that day (incl. 'abstain') = the BLEND reference for wolf credit. None
    if no vote happened. Uses vote_counts so an abstain-majority still counts as a consensus to blend
    with (voted_player is None on no-lynch days, which would silently drop that signal)."""
    vc = day_res.get("vote_counts") or {}
    return max(vc, key=vc.get) if vc else None


def _town_abstain_credit(day_res: dict | None) -> str:
    """The "deadlock_negative" abstain rule for TOWN voters: an abstain is scored by what the room's day
    actually resolved to. No-lynch day => NEGATIVE — the abstain fed a deadlock with a threat still
    votable (a threat is alive by construction while the game runs), and the v7 endpoint forensics
    showed 95% of ON-arm town abstains sat on exactly these days. Any lynch that landed => NEUTRAL:
    abstaining from a mislynch is defensible (the 2% case), and abstaining while the room correctly
    lynched a threat carries no realized harm. Missing resolution row => neutral (degrade, never guess).
    This closes the opportunity-cost blind spot: under the legacy "neutral" rule an always-abstain SP
    pins at utility 0.00 forever and prune can never see it."""
    if day_res is None:
        return "neutral"
    if day_res.get("no_vote") or not day_res.get("voted_player"):
        return "negative"
    return "neutral"


def _vote_credit(role: str, votee: str | None, roles: dict, majority: str | None = None, *,
                 abstain_rule: str = "neutral", day_res: dict | None = None) -> str:
    """Faction-RELATIVE day-vote credit: 'did this vote advance the voter's own win condition?'
    Town wants threats lynched; the last-standing SK wants anyone but itself gone.

    WOLF is scored by BLENDING, not target — the validated signal (G2 day-blend r=+0.22; "blend with
    majority" audit r=+0.20). Voting the room's plurality choice = concealment, and it is bussing-aware
    by construction: when the majority is taking down an ally, blending means voting the ally too (the
    correct cover play that the old 'ally=negative' rule wrongly punished); off-consensus voting draws
    heat. `majority` None (no consensus, or called as a day-vote ENDPOINT) => the old target fallback.

    `abstain_rule` selects the town-abstain grading (LoopConfig.abstain_credit): "neutral" = the frozen
    legacy bucket (what measure.py and every pre-registered instrument keep using via the default);
    "deadlock_negative" = _town_abstain_credit on `day_res` (that day's resolution row). Keyword-only so
    no positional caller can drift onto the new rule. Deceiver abstains stay on their own semantics
    (wolf blend / SK neutral) under either rule — the caution blind spot is town's."""
    if role == "wolf" and majority is not None:
        return "positive" if votee == majority else "negative"  # blend with the room (bussing-aware)
    o = score_vote(votee, roles)
    if o.is_abstain:
        if abstain_rule == "deadlock_negative" and role in TOWN_VOTE_ROLES:
            return _town_abstain_credit(day_res)
        return "neutral"  # abstain is its own bucket
    if role == "wolf":
        return "negative" if o.votee_role == "wolf" else "positive"  # no-consensus fallback (old rule)
    if role == "serial_killer":
        return "positive"  # SK wins by being last — any non-self lynch advances it
    return "positive" if o.hit_threat else "negative"  # town: threat = good, townie = mislynch


def _night_credit(role: str, target: str | None, roles: dict,
                  night_res: dict | None = None) -> str | None:
    o = score_night_target(target, roles)
    if target in (None, "hold_fire", "abstain"):
        return "neutral"  # banked the action (vigilante hold / no-op)
    if role in ("investigator",):
        # find-RATE is a null channel (transmission cap); miss stays NEUTRAL (§6.2 ruling 2026-07-13).
        return "positive" if o.hit_threat else "neutral"
    if role == "vigilante":
        if o.hit_threat:
            return "positive"  # shot a wolf/SK
        return "negative" if o.hit_town else "neutral"  # friendly fire is the failure mode
    if role in ("wolf", "serial_killer"):
        # offense = removing town tools (power-targeting); the SK keeper also lands on killing a wolf.
        if o.hit_power or o.hit_threat:
            return "positive"
        return "neutral"  # killed a plain townie / no-op — not the high-value kill
    if role == "healer":
        return _healer_credit(target, o, night_res)
    return "neutral"


def _healer_credit(target: str, o, night_res: dict | None) -> str | None:
    """The ★healer_town_save_rate construct, promoted verbatim from Agents/compute_metrics.py (not the
    stricter screen-local lens in checkpoint_replay.py): a save is observable only when the heal target
    was ATTACKED that night — by ANY attacker, the vigilante's mistake included — and survived. Split by
    who was saved: town save = the validated good-play half (+0.40 at N=180); shielding a threat = the
    validated error half. Unattacked heal = a prediction miss, neutral like the held bullet; attacked
    but died anyway (double attack) = right prediction overwhelmed, neutral not negative. None (skip)
    when the caller has no night_resolutions row to join against."""
    if night_res is None:
        return None
    attackers = {night_res.get("wolves_target"), night_res.get("serial_killer_target"),
                 night_res.get("vigilante_target")}
    attackers.discard(None)
    if target not in attackers:
        return "neutral"
    if target in (night_res.get("deaths") or []):
        return "neutral"
    return "negative" if o.hit_threat else "positive"


def read_partition_excluded(ec: dict, roles: dict) -> bool:
    """The v1 read-partition trigger (uniform across night channels; evidence/credit/report.md §3): the
    actor held a stated HIGH-confidence THREAT-read on its target and the target was actually town — the
    outcome then belongs to the read, not the followed tactic. Fires only on a stated-and-wrong belief:
    no read on the target, low confidence, or 'unclear' => False (credit normally). Callers apply it to
    NEGATIVE verdicts only — it exists to rescue procedures from bad beliefs, and the other night
    channels have no negative to rescue (their partition pass-through is a near-no-op by design)."""
    target = (ec.get("agent_night_action") or {}).get("target")
    if not target or target in ("hold_fire", "abstain"):
        return False
    if roles.get(target) in THREAT_ROLES:
        return False  # the belief was right at the faction grain — nothing to exclude
    return any(
        r.get("player") == target and r.get("confidence") == "high"
        and r.get("suspected_role") in THREAT_ROLES
        for r in ec.get("reads") or []
    )


@dataclass
class SPCredit:
    follow: int = 0
    positive: int = 0
    neutral: int = 0
    negative: int = 0
    baselined_sum: float = 0.0  # sum over follows of (outcome_value - that cell's memory-off base rate)
    channels: Counter = field(default_factory=Counter)

    def add(self, verdict: str, channel: str, base_rate: float) -> None:
        self.follow += 1
        setattr(self, verdict, getattr(self, verdict) + 1)
        self.baselined_sum += VERDICT_VALUE[verdict] - base_rate
        self.channels[channel] += 1

    @property
    def utility(self) -> float:
        """Raw outcome rate of followed decisions (the haloed, unbaselined number)."""
        return (self.positive - self.negative) / self.follow if self.follow else 0.0

    @property
    def lift(self) -> float:
        """Outcome vs the memory-OFF base rate of the same cells — 'did following this BEAT no-memory?'"""
        return self.baselined_sum / self.follow if self.follow else 0.0

    @property
    def shrunk_lift(self) -> float:
        """Lift pulled toward 0 by follow count, so 1-follow flukes don't dominate."""
        return self.lift * self.follow / (self.follow + SHRINK_K) if self.follow else 0.0


def compute_base_rates(dumps_glob: str, *,
                       abstain_rule: str = "neutral") -> dict[str, tuple[float, int]]:
    """Per (role/phase) channel: the mean creditable outcome of MEMORY-OFF decisions = the ambient
    'how this decision goes with no notes'. This is the free, cell-level stand-in for a per-turn
    memory-on-vs-off replay (which would be paid). Returns channel -> (mean_value, n).
    abstain_rule must match the ledger's (baseline coherence: the base is produced by the SAME grading
    function as the counts it de-lucks) — credit_apply threads one value into both."""
    totals: dict[str, list[float]] = defaultdict(list)
    for dump in _expand_dumps(dumps_glob):
        for line in open(dump):
            if not line.strip():
                continue
            g = json.loads(line)
            roles, path = g.get("roles"), g.get("eval_cases_path")
            if not roles or not path or not os.path.exists(path):
                continue
            blend_by_day = {dr.get("day"): _majority_vote(dr) for dr in g.get("day_resolutions", [])}
            night_by_day = {nr.get("day"): nr for nr in g.get("night_resolutions", [])}
            day_res_by_day = {dr.get("day"): dr for dr in g.get("day_resolutions", [])}
            for cl in open(path):
                if not cl.strip():
                    continue
                env = json.loads(cl)
                if env.get("kind") != "agent_action_eval":
                    continue
                ec = (env.get("output") or {}).get("eval_case")
                if not ec or ec.get("memory_enabled"):  # base rate = memory-OFF only
                    continue
                verdict = _decision_credit(ec, roles, blend_by_day, night_by_day,
                                           abstain_rule=abstain_rule, day_res_by_day=day_res_by_day)
                if verdict in VERDICT_VALUE:  # read_excluded drops from the base too (same instrument)
                    totals[f"{ec['player_role']}/{ec['action_phase']}"].append(VERDICT_VALUE[verdict])
    return {ch: (sum(vs) / len(vs), len(vs)) for ch, vs in totals.items() if vs}


def _iter_cases(dumps_glob: str):
    """Yield (game_roles, blend_by_day, night_by_day, day_res_by_day, eval_case) for every memory-on
    agent-action case with follow verdicts. blend_by_day = day -> room plurality vote (the wolf blend
    reference); night_by_day = day -> that night's resolution row (the healer attack-join);
    day_res_by_day = day -> that day's full resolution row (the abstain-rule join)."""
    for dump in _expand_dumps(dumps_glob):
        for line in open(dump):
            if not line.strip():
                continue
            g = json.loads(line)
            roles, path = g.get("roles"), g.get("eval_cases_path")
            if not roles or not path or not os.path.exists(path):
                continue
            blend_by_day = {dr.get("day"): _majority_vote(dr) for dr in g.get("day_resolutions", [])}
            night_by_day = {nr.get("day"): nr for nr in g.get("night_resolutions", [])}
            day_res_by_day = {dr.get("day"): dr for dr in g.get("day_resolutions", [])}
            for cl in open(path):
                if not cl.strip():
                    continue
                env = json.loads(cl)
                if env.get("kind") != "agent_action_eval":
                    continue
                ec = (env.get("output") or {}).get("eval_case")
                if ec and ec.get("memory_enabled") and ec.get("strategy_verdicts"):
                    yield roles, blend_by_day, night_by_day, day_res_by_day, ec


def _decision_credit(ec: dict, roles: dict, blend_by_day: dict | None = None,
                     night_by_day: dict | None = None, *,
                     abstain_rule: str = "neutral",
                     day_res_by_day: dict | None = None) -> str | None:
    """The de-lucked credit verdict for this decision's channel; None = not creditable this round;
    "read_excluded" = the read-partition dropped it (a negative reached through a stated-and-wrong
    threat-read — counted separately, never valued). blend_by_day: day -> room plurality vote (the wolf
    BLEND reference); night_by_day: day -> that night's resolution row (the healer attack-join). Either
    None => the dependent channel degrades gracefully (wolf falls back to the target rule, healer skips).
    abstain_rule/day_res_by_day (keyword-only, defaults = frozen legacy): the town-abstain grading and
    the day -> day_resolutions row it needs — see _vote_credit. Callers that never pass them (measure.py,
    the pre-registered instruments) are byte-identical to the pre-knob behavior."""
    phase, role = ec.get("action_phase"), ec.get("player_role")
    if phase == "day_vote" and ec.get("agent_vote"):
        majority = (blend_by_day or {}).get(ec.get("day"))
        return _vote_credit(role, ec["agent_vote"].get("votee"), roles, majority,
                            abstain_rule=abstain_rule,
                            day_res=(day_res_by_day or {}).get(ec.get("day")))
    if phase == "night_action" and ec.get("agent_night_action"):
        if role not in NIGHT_CREDIT_ROLES:
            return None
        night_res = (night_by_day or {}).get(ec.get("day"))
        verdict = _night_credit(role, ec["agent_night_action"].get("target"), roles, night_res)
        if verdict == "negative" and read_partition_excluded(ec, roles):
            return "read_excluded"
        return verdict
    return None


def build_ledger(dumps_glob: str, base_rates: dict[str, tuple[float, int]], *,
                 abstain_rule: str = "neutral") -> tuple[dict[str, SPCredit], Counter]:
    ledger: dict[str, SPCredit] = defaultdict(SPCredit)
    skipped: Counter = Counter()
    for roles, blend_by_day, night_by_day, day_res_by_day, ec in _iter_cases(dumps_glob):
        verdict = _decision_credit(ec, roles, blend_by_day, night_by_day,
                                   abstain_rule=abstain_rule, day_res_by_day=day_res_by_day)
        if verdict == "read_excluded":
            skipped[f"read_excluded/{ec.get('player_role')}/{ec.get('action_phase')}"] += 1
            continue
        if verdict is None:
            skipped[f"{ec.get('player_role')}/{ec.get('action_phase')}"] += 1
            continue
        channel = f"{ec['player_role']}/{ec['action_phase']}"
        base = base_rates.get(channel, (0.0, 0))[0]  # no memory-off data for this cell -> baseline 0
        index_to_key = ec.get("strategy_index_to_key") or {}
        for sv in ec["strategy_verdicts"]:
            if sv.get("verdict") != "follow":
                continue
            key = index_to_key.get(str(sv.get("strategy_index")))
            if key:
                ledger[key].add(verdict, channel, base)
    return ledger, skipped


def _load_store_sp_meta(store: Path) -> dict[str, dict]:
    """key -> {observation_count, situation, action} for the store's strategy points (the frequency
    baseline; SPs carry NO outcome halo — only OBs do — so credit is compared against frequency)."""
    ns = json.load(open(store / "strategy_points.json"))["namespaces"]
    meta = {}
    for items in ns.values():
        for it in items:
            v = it["value"]
            meta[it["key"]] = {
                "observation_count": v.get("observation_count", 1),
                "situation": v.get("situation", "")[:80],
                "action": v.get("action", "")[:80],
            }
    return meta


def validate(ledger: dict[str, SPCredit], store: Path, base_rates: dict[str, tuple[float, int]]) -> None:
    meta = _load_store_sp_meta(store)
    total_sp = len(meta)
    credited = {k: c for k, c in ledger.items() if c.follow}

    print("\n=== (0) MEMORY-OFF BASE RATES (the 'no notes' ambient each note is graded against) ===")
    for ch, (rate, n) in sorted(base_rates.items()):
        print(f"    {ch:32s} mean outcome {rate:+.2f}  (n={n} off-decisions)")

    # (1) Conservation — every followed decision contributes exactly one outcome tally.
    bad = [k for k, c in credited.items() if c.positive + c.neutral + c.negative != c.follow]
    print(f"\n=== (1) CONSERVATION === pos+neu+neg == follow: "
          f"{'OK' if not bad else f'BROKEN on {len(bad)} keys'}")

    # (2) Coverage — how much of the store ever got a follow-credit.
    in_store = sum(1 for k in credited if k in meta)
    print(f"\n=== (2) COVERAGE === credited SPs: {len(credited)} "
          f"({in_store} in store, {len(credited)-in_store} orphan keys) / {total_sp} store SPs "
          f"= {in_store/total_sp:.0%} of the store ever followed")
    follows = sorted((c.follow for c in credited.values()), reverse=True)
    print(f"    follow counts: total={sum(follows)} max={follows[0]} "
          f"median={follows[len(follows)//2]} | SPs with >=5 follows: {sum(1 for f in follows if f>=5)}")

    # (3) RAW vs BASELINED — the headline. Raw utility is haloed (notes ride along with good
    #     decisions); LIFT (vs the memory-off base rate) is 'did following this BEAT no-memory?'.
    #     Per G3a we EXPECT lift to wash toward ~0 on this capped store — a null here confirms, not kills.
    deep = [c for c in credited.values() if c.follow >= 3]
    raw_mean = sum(c.utility for c in deep) / len(deep)
    lift_mean = sum(c.lift for c in deep) / len(deep)
    pos = sum(1 for c in deep if c.shrunk_lift > 0.1)
    neg = sum(1 for c in deep if c.shrunk_lift < -0.1)
    mid = len(deep) - pos - neg
    print(f"\n=== (3) RAW vs BASELINED LIFT (SPs with >=3 follows, n={len(deep)}) ===")
    print(f"    mean RAW utility  : {raw_mean:+.2f}   <- haloed (rides along with good decisions)")
    print(f"    mean LIFT vs off  : {lift_mean:+.2f}   <- the honest 'beat no-memory?' number")
    print(f"    shrunk-lift split :  >+0.1: {pos}   [-0.1,+0.1]: {mid}   <-0.1: {neg}")
    print("    lift~0 / mostly-mid => notes don't beat no-memory on this content (expected pre-loop);")
    print("    a real positive tail => some notes genuinely help even now.")

    # (4) Top / bottom notes by shrunk lift — eyeball whether the winners/losers look sensible.
    ranked = sorted(deep, key=lambda c: c.shrunk_lift, reverse=True)
    def _show(c):
        k = next(kk for kk, cc in credited.items() if cc is c)
        return (f"      lift{c.shrunk_lift:+.2f} (raw{c.utility:+.2f}, n={c.follow}) "
                f"{meta.get(k, {}).get('action','?')[:60]}")
    print("\n=== (4) TOP 5 / BOTTOM 5 notes by shrunk lift ===")
    for c in ranked[:5]:
        print(_show(c))
    print("    ---")
    for c in ranked[-5:]:
        print(_show(c))

    # (5) Per-channel — where the credit actually comes from.
    chan = Counter()
    for c in credited.values():
        chan.update(c.channels)
    print(f"\n=== (5) CHANNELS (follow-credits by role/phase) ===")
    for ch, n in chan.most_common():
        print(f"    {ch:32s} {n}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dumps", default=DEFAULT_DUMPS)
    ap.add_argument("--store", default=DEFAULT_STORE)
    ap.add_argument("--ledger", default=DEFAULT_LEDGER)
    args = ap.parse_args()

    base_rates = compute_base_rates(args.dumps)
    ledger, skipped = build_ledger(args.dumps, base_rates)
    print(f"built ledger: {len(ledger)} SP keys credited from {args.dumps}")
    if skipped:
        print("not-creditable-this-round (skipped):",
              ", ".join(f"{k}={n}" for k, n in skipped.most_common()))

    validate(ledger, Path(args.store), base_rates)

    out = Path(args.ledger)
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {k: {"follow": c.follow, "positive": c.positive, "neutral": c.neutral,
                   "negative": c.negative, "utility": round(c.utility, 4),
                   "lift": round(c.lift, 4), "shrunk_lift": round(c.shrunk_lift, 4),
                   "channels": dict(c.channels)}
               for k, c in ledger.items() if c.follow}
    json.dump(payload, open(out, "w"), indent=2)
    print(f"\nwrote ledger -> {out} ({len(payload)} credited SPs)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
