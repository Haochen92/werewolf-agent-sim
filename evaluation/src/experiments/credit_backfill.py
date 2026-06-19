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
covers BOARD-OUTCOME decisions only this round: day-votes (all town roles) + night targets
(investigator / vigilante / wolf / serial_killer). Healer-night needs the attack-join (night_resolutions)
and is deferred; the reveal/confirm-only class is unscorable until the discussion tagger (build item d).

Compute is decoupled from the store-write: we emit the ledger + a validation read and STOP — no store
is mutated until the signal is shown to separate. Applying the ledger to a v6_1 copy is a later step.

  poetry run python evaluation/src/experiments/credit_backfill.py
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

from evaluation.src.components.decision_scoring import score_night_target, score_vote  # noqa: E402

DEFAULT_DUMPS = "batch_results/*v6ab*.jsonl"
DEFAULT_STORE = "memory_stores/v6_1"
DEFAULT_LEDGER = "evidence/v7_final/credit_backfill_ledger.json"

# Per-channel mapping from a deterministic outcome to a credit verdict. None = decision not creditable
# this round (skipped, counted separately). Each returns "positive" | "neutral" | "negative".
NIGHT_CREDIT_ROLES = frozenset({"investigator", "vigilante", "wolf", "serial_killer"})

VERDICT_VALUE = {"positive": 1.0, "neutral": 0.0, "negative": -1.0}
SHRINK_K = 5  # low-follow SPs pull toward 0 lift: shrunk = lift * follow/(follow+K)


TOWN_VOTE_ROLES = frozenset({"villager", "healer", "investigator", "vigilante"})


def _vote_credit(role: str, votee: str | None, roles: dict) -> str:
    """Faction-RELATIVE day-vote credit: 'did this vote advance the voter's own win condition?'
    Town wants threats lynched; a wolf wants non-wolves lynched; the last-standing SK wants anyone
    but itself gone. Scoring every vote town-side would invert the deceivers."""
    o = score_vote(votee, roles)
    if o.is_abstain:
        return "neutral"  # abstain is its own bucket
    if role == "wolf":
        return "negative" if o.votee_role == "wolf" else "positive"  # only lynching an ally hurts
    if role == "serial_killer":
        return "positive"  # SK wins by being last — any non-self lynch advances it
    return "positive" if o.hit_threat else "negative"  # town: threat = good, townie = mislynch


def _night_credit(role: str, target: str | None, roles: dict) -> str:
    o = score_night_target(target, roles)
    if target in (None, "hold_fire", "abstain"):
        return "neutral"  # banked the action (vigilante hold / no-op)
    if role in ("investigator",):
        # find-RATE is a null channel (transmission cap); credited but flagged weak in the report.
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
    return "neutral"


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


def compute_base_rates(dumps_glob: str) -> dict[str, tuple[float, int]]:
    """Per (role/phase) channel: the mean creditable outcome of MEMORY-OFF decisions = the ambient
    'how this decision goes with no notes'. This is the free, cell-level stand-in for a per-turn
    memory-on-vs-off replay (which would be paid). Returns channel -> (mean_value, n)."""
    totals: dict[str, list[float]] = defaultdict(list)
    for dump in sorted(glob.glob(dumps_glob)):
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
                env = json.loads(cl)
                if env.get("kind") != "agent_action_eval":
                    continue
                ec = (env.get("output") or {}).get("eval_case")
                if not ec or ec.get("memory_enabled"):  # base rate = memory-OFF only
                    continue
                verdict = _decision_credit(ec, roles)
                if verdict is not None:
                    totals[f"{ec['player_role']}/{ec['action_phase']}"].append(VERDICT_VALUE[verdict])
    return {ch: (sum(vs) / len(vs), len(vs)) for ch, vs in totals.items() if vs}


def _iter_cases(dumps_glob: str):
    """Yield (game_roles, eval_case) for every memory-on agent-action case with follow verdicts."""
    for dump in sorted(glob.glob(dumps_glob)):
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
                env = json.loads(cl)
                if env.get("kind") != "agent_action_eval":
                    continue
                ec = (env.get("output") or {}).get("eval_case")
                if ec and ec.get("memory_enabled") and ec.get("strategy_verdicts"):
                    yield roles, ec


def _decision_credit(ec: dict, roles: dict) -> str | None:
    """The de-lucked credit verdict for this decision's channel, or None if not creditable this round."""
    phase, role = ec.get("action_phase"), ec.get("player_role")
    if phase == "day_vote" and ec.get("agent_vote"):
        return _vote_credit(role, ec["agent_vote"].get("votee"), roles)
    if phase == "night_action" and ec.get("agent_night_action"):
        if role not in NIGHT_CREDIT_ROLES:
            return None  # healer-night deferred (needs the night_resolutions attack-join)
        return _night_credit(role, ec["agent_night_action"].get("target"), roles)
    return None


def build_ledger(dumps_glob: str, base_rates: dict[str, tuple[float, int]]) -> tuple[dict[str, SPCredit], Counter]:
    ledger: dict[str, SPCredit] = defaultdict(SPCredit)
    skipped: Counter = Counter()
    for roles, ec in _iter_cases(dumps_glob):
        verdict = _decision_credit(ec, roles)
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
