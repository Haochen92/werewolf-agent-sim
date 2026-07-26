"""Production credit rules — the FIXED grading, hard-coded (deterministic, zero spend).

This is the graduated form of ``evaluation/src/loop/credit_backfill.py`` with the rule knobs
removed: production grades town abstains with the deadlock-negative rule unconditionally (the v7
endpoint blind-spot fix, validated in ``evidence/credit/blindspot_fix/``), and there is no switch
back to the legacy neutral bucket anywhere in this package. The eval-side module keeps its knobbed
form so the frozen research runs reproduce; a parity test pins this module byte-equal to the eval
grader under the fixed settings.

Sourcing contract (the production event stream): a window is a glob of game-record JSONL dumps,
each record carrying ``roles`` / ``day_resolutions`` / ``night_resolutions`` and an
``eval_cases_path`` sidecar of per-decision eval cases (``strategy_verdicts`` +
``strategy_index_to_key`` join the followed SPs). This is exactly what the batch runner already
emits per game — the live backend must keep emitting it, and must stamp ``human_player`` on any
game with a human seat: ``_iter_game_records`` DROPS those records (the poisoning rule — only
agent-only games may teach the store).
"""

from __future__ import annotations

import glob
import json
import os
from collections import Counter, defaultdict
from dataclasses import dataclass, field

from Agents.memory.consolidation.decision_scoring import (
    THREAT_ROLES,
    score_night_target,
    score_vote,
)

NIGHT_CREDIT_ROLES = frozenset({"investigator", "vigilante", "wolf", "serial_killer", "healer"})
TOWN_VOTE_ROLES = frozenset({"villager", "healer", "investigator", "vigilante"})

VERDICT_VALUE = {"positive": 1.0, "neutral": 0.0, "negative": -1.0}
SHRINK_K = 5  # low-follow SPs pull toward 0 lift: shrunk = lift * follow/(follow+K)


def _expand_dumps(dumps_glob: str) -> list[str]:
    """Expand a dumps spec that is EITHER a single glob pattern OR a whitespace-joined list of
    paths/patterns (the rolling window passes the latter). Plain ``glob.glob`` treats the whole
    space-separated string as ONE pattern and matches nothing — silently emptying the ledger."""
    return sorted(f for pat in dumps_glob.split() for f in glob.glob(pat))


def _iter_game_records(dumps_glob: str):
    """Every game record in the window that is allowed to TEACH: the human-seat guard lives here,
    once, so every ledger and base in this package inherits it. A record with a truthy
    ``human_player`` is a human-involved game — replayable, never mined (the poisoning rule)."""
    for dump in _expand_dumps(dumps_glob):
        for line in open(dump):
            if not line.strip():
                continue
            g = json.loads(line)
            if g.get("human_player"):
                continue
            yield g


def _majority_vote(day_res: dict) -> str | None:
    """The room's plurality vote that day (incl. 'abstain') = the BLEND reference for wolf credit.
    None if no vote happened. Uses vote_counts so an abstain-majority still counts as a consensus
    to blend with (voted_player is None on no-lynch days, which would silently drop that signal)."""
    vc = day_res.get("vote_counts") or {}
    return max(vc, key=vc.get) if vc else None


def _town_abstain_credit(day_res: dict | None) -> str:
    """THE production town-abstain rule: an abstain is scored by what the room's day actually
    resolved to. No-lynch day => NEGATIVE — the abstain fed a deadlock with a threat still votable
    (a threat is alive by construction while the game runs); the v7 endpoint forensics showed 95%
    of ON-arm town abstains sat on exactly these days. Any lynch that landed => NEUTRAL: abstaining
    from a mislynch is defensible, and abstaining while the room correctly lynched carries no
    realized harm. Missing resolution row => neutral (degrade, never guess). This closes the
    opportunity-cost blind spot the legacy neutral bucket left open (an always-abstain SP pinned at
    utility 0.00 forever, invisible to prune)."""
    if day_res is None:
        return "neutral"
    if day_res.get("no_vote") or not day_res.get("voted_player"):
        return "negative"
    return "neutral"


def _vote_credit(role: str, votee: str | None, roles: dict, majority: str | None = None,
                 day_res: dict | None = None) -> str:
    """Faction-RELATIVE day-vote credit: 'did this vote advance the voter's own win condition?'

    WOLF is scored by BLENDING with the room's plurality (bussing-aware; the validated G2 signal),
    falling back to the target rule when no consensus reference exists. TOWN abstains are graded by
    ``_town_abstain_credit`` on that day's resolution — unconditionally; deceiver abstains keep
    their own semantics (wolf blend / SK neutral). The caution blind spot was town's."""
    if role == "wolf" and majority is not None:
        return "positive" if votee == majority else "negative"  # blend with the room (bussing-aware)
    o = score_vote(votee, roles)
    if o.is_abstain:
        if role in TOWN_VOTE_ROLES:
            return _town_abstain_credit(day_res)
        return "neutral"  # deceiver abstain stays its own bucket
    if role == "wolf":
        return "negative" if o.votee_role == "wolf" else "positive"  # no-consensus fallback
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
    """The ★healer_town_save_rate construct (validated +0.40 at N=180): a save is observable only
    when the heal target was ATTACKED that night — by ANY attacker — and survived. Town save =
    good-play half; shielding a threat = error half. Unattacked heal = a prediction miss, neutral;
    attacked-but-died-anyway = right prediction overwhelmed, neutral not negative. None (skip) when
    the caller has no night_resolutions row to join against."""
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
    """The read-partition trigger (uniform across night channels): the actor held a stated
    HIGH-confidence THREAT-read on its target and the target was actually town — the outcome then
    belongs to the read, not the followed tactic. Fires only on a stated-and-wrong belief; callers
    apply it to NEGATIVE verdicts only. Legacy records without a reads field no-op by construction."""
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


def _game_joins(g: dict) -> tuple[dict, dict, dict]:
    """(blend_by_day, night_by_day, day_res_by_day) — the per-day join tables every grading pass
    needs: the wolf blend reference, the healer attack-join, and the abstain-rule resolution row."""
    blend_by_day = {dr.get("day"): _majority_vote(dr) for dr in g.get("day_resolutions", [])}
    night_by_day = {nr.get("day"): nr for nr in g.get("night_resolutions", [])}
    day_res_by_day = {dr.get("day"): dr for dr in g.get("day_resolutions", [])}
    return blend_by_day, night_by_day, day_res_by_day


def compute_base_rates(dumps_glob: str) -> dict[str, tuple[float, int]]:
    """Per (role/phase) channel: the mean creditable outcome of MEMORY-OFF decisions = the ambient
    'how this decision goes with no notes', graded by the SAME fixed rule as the ledger (baseline
    coherence by construction — there is no other rule in this package). Returns
    channel -> (mean_value, n)."""
    totals: dict[str, list[float]] = defaultdict(list)
    for g in _iter_game_records(dumps_glob):
        roles, path = g.get("roles"), g.get("eval_cases_path")
        if not roles or not path or not os.path.exists(path):
            continue
        blend_by_day, night_by_day, day_res_by_day = _game_joins(g)
        for cl in open(path):
            if not cl.strip():
                continue
            env = json.loads(cl)
            if env.get("kind") != "agent_action_eval":
                continue
            ec = (env.get("output") or {}).get("eval_case")
            if not ec or ec.get("memory_enabled"):  # base rate = memory-OFF only
                continue
            verdict = _decision_credit(ec, roles, blend_by_day, night_by_day, day_res_by_day)
            if verdict in VERDICT_VALUE:  # read_excluded drops from the base too (same instrument)
                totals[f"{ec['player_role']}/{ec['action_phase']}"].append(VERDICT_VALUE[verdict])
    return {ch: (sum(vs) / len(vs), len(vs)) for ch, vs in totals.items() if vs}


def _iter_cases(dumps_glob: str):
    """Yield (game_roles, blend_by_day, night_by_day, day_res_by_day, eval_case) for every
    memory-on agent-action case with follow verdicts, over the teach-allowed records."""
    for g in _iter_game_records(dumps_glob):
        roles, path = g.get("roles"), g.get("eval_cases_path")
        if not roles or not path or not os.path.exists(path):
            continue
        blend_by_day, night_by_day, day_res_by_day = _game_joins(g)
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
                     night_by_day: dict | None = None,
                     day_res_by_day: dict | None = None) -> str | None:
    """The de-lucked credit verdict for this decision's channel; None = not creditable this round;
    "read_excluded" = the read-partition dropped it (counted separately, never valued). A missing
    join table degrades gracefully (wolf falls back to the target rule, healer skips, abstain
    grades neutral)."""
    phase, role = ec.get("action_phase"), ec.get("player_role")
    if phase == "day_vote" and ec.get("agent_vote"):
        majority = (blend_by_day or {}).get(ec.get("day"))
        return _vote_credit(role, ec["agent_vote"].get("votee"), roles, majority,
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


def build_ledger(dumps_glob: str,
                 base_rates: dict[str, tuple[float, int]]) -> tuple[dict[str, SPCredit], Counter]:
    ledger: dict[str, SPCredit] = defaultdict(SPCredit)
    skipped: Counter = Counter()
    for roles, blend_by_day, night_by_day, day_res_by_day, ec in _iter_cases(dumps_glob):
        verdict = _decision_credit(ec, roles, blend_by_day, night_by_day, day_res_by_day)
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
