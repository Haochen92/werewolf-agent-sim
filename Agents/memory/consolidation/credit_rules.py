"""Production credit rules — the fixed grading, hard-coded (deterministic, zero spend).

Ten-seat since the port of 2026-10-13 (plan §9.6; the per-decision grades are ``grading``). The
nine-seat grader this module graduated from stays in ``evaluation/src/loop/credit_backfill.py`` with
its knobs, so the frozen research runs still reproduce; production no longer mirrors it.

Sourcing contract (the production event stream): a window is a glob of game-record JSONL dumps,
each record carrying ``roles`` / ``day_resolutions`` / ``night_resolutions`` and an
``eval_cases_path`` sidecar of per-decision eval cases (``strategy_verdicts`` +
``strategy_index_to_key`` join the followed SPs). This is exactly what the batch runner already
emits per game — the live backend must keep emitting it, and must stamp ``human_player`` on any
game with a human seat: ``_iter_game_records`` DROPS those records (the poisoning rule — only
agent-only games may teach the store).

One verdict per lesson per seat per scope (owner, 2026-10-13): a scope is a day's discussion, a
day's vote, a night's pack chat, or a night's act (the kill and the skill share one lookup). A seat
sees the same lessons on every turn of a scope, so counting per turn would weigh one decision
several times; the first scored decision of the scope that followed the lesson is the one counted.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import dataclass, field

from Agents.memory.consolidation.grading import EVIL, TOWN, GameView, night_channel, night_scope, side
from Agents.memory.consolidation.sources import games_from_files

VERDICT_VALUE = {"positive": 1.0, "neutral": 0.0, "negative": -1.0}
SHRINK_K = 5  # low-follow SPs pull toward 0 lift: shrunk = lift * follow/(follow+K)
VERDICT_RANK = {"follow": 3, "override": 2, "not_relevant": 1}
"""A lesson's verdict over a scope's turns: follow on any turn wins, then override."""


def _iter_game_records(window):
    """Every game record in the window that is allowed to TEACH: the human-seat guard lives here,
    once, so every ledger and base in this package inherits it. A record with a truthy
    ``human_player`` is a human-involved game — replayable, never mined (the poisoning rule).
    ``window``: a glob spec of batch-run dumps, or games already loaded (``sources``: files and the
    served games' database, decisions §14)."""
    games = games_from_files(window) if isinstance(window, str) else window
    for g in games:
        if not g.get("human_player"):
            yield g


def iter_eval_cases(g: dict):
    """The game's agent-action eval cases, in the order they were played: inline for a served game
    (``eval_cases``), else from the batch run's sidecar."""
    if not g.get("roles"):
        return
    if "eval_cases" in g:
        yield from g["eval_cases"]
        return
    path = g.get("eval_cases_path")
    if not path:
        return
    for cl in open(path):
        if not cl.strip():
            continue
        env = json.loads(cl)
        if env.get("kind") != "agent_action_eval":
            continue
        ec = (env.get("output") or {}).get("eval_case")
        if ec:
            yield ec


def decision_scope(ec: dict) -> tuple:
    """(player, day, phase, night scope): the unit one lesson gets one verdict in."""
    phase = ec.get("action_phase")
    sub = night_scope(ec) if phase == "night_action" else ""
    return ec.get("player_id"), ec.get("day"), phase, sub


def decision_channel(ec: dict) -> str:
    """The memory-off baseline a decision is compared with: its role and phase, and for a wolf's
    night its turn kind (chat, kill, skill)."""
    if ec.get("action_phase") == "night_action":
        return night_channel(ec)
    return f"{ec.get('player_role')}/{ec.get('action_phase')}"


def read_partition_excluded(ec: dict, roles: dict) -> bool:
    """The read-partition trigger (uniform across night channels): the actor held a stated
    HIGH-confidence THREAT-read on its target and the target was actually town — the outcome then
    belongs to the read, not the followed tactic. Fires only on a stated-and-wrong belief; callers
    apply it to NEGATIVE verdicts only. Legacy records without a reads field no-op by construction."""
    target = (ec.get("agent_night_action") or {}).get("target")
    if not target or target in ("hold_fire", "abstain"):
        return False
    if side(roles.get(target)) in EVIL:
        return False  # the belief was right at the faction grain — nothing to exclude
    return any(
        r.get("player") == target and r.get("confidence") == "high"
        and side(r.get("suspected_role")) in EVIL
        for r in ec.get("reads") or []
    )


@dataclass
class SPCredit:
    follow: int = 0
    positive: int = 0
    neutral: int = 0
    negative: int = 0
    channels: Counter = field(default_factory=Counter)
    """Follows per baseline channel: the SP's base is their follow-weighted mean."""

    def add(self, verdict: str, channel: str) -> None:
        self.follow += 1
        setattr(self, verdict, getattr(self, verdict) + 1)
        self.channels[channel] += 1

    @property
    def utility(self) -> float:
        """Raw outcome rate of followed decisions (the haloed, unbaselined number)."""
        return (self.positive - self.negative) / self.follow if self.follow else 0.0

    def base(self, base_rates: dict) -> float | None:
        """The memory-off mean this SP's follows are compared with: each follow against its own
        channel's base. None (unscored) when any channel has no memory-off data — a missing
        baseline is not a baseline of 0."""
        if not self.follow or any(ch not in base_rates for ch in self.channels):
            return None
        return sum(n * base_rates[ch][0] for ch, n in self.channels.items()) / self.follow


def decision_credit(ec: dict, view: GameView) -> str | None:
    """The verdict for one vote or night decision; None = not graded; "read_excluded" = a town
    seat's negative that belongs to its wrong high-confidence read (counted apart, never valued)."""
    verdict = view.decision_grade(ec)
    if (verdict == "negative" and ec.get("action_phase") == "night_action"
            and side(ec.get("player_role")) == TOWN and read_partition_excluded(ec, view.roles)):
        return "read_excluded"
    return verdict


def compute_base_rates(dumps_glob: str) -> dict[str, tuple[float, int]]:
    """Per channel: the mean graded outcome of MEMORY-OFF decisions, one per scope, graded by the
    same rules as the ledger (baseline coherence by construction). Returns channel -> (mean, n)."""
    totals: dict[str, list[float]] = defaultdict(list)
    for g in _iter_game_records(dumps_glob):
        view, seen = GameView(g), set()
        for ec in iter_eval_cases(g):
            if ec.get("memory_enabled"):  # base rate = memory-OFF only
                continue
            verdict = decision_credit(ec, view)
            if verdict not in VERDICT_VALUE or decision_scope(ec) in seen:
                continue
            seen.add(decision_scope(ec))
            totals[decision_channel(ec)].append(VERDICT_VALUE[verdict])
    return {ch: (sum(vs) / len(vs), len(vs)) for ch, vs in totals.items() if vs}


def followed_keys(ec: dict) -> list[str]:
    """The store keys of the lessons this decision followed."""
    index_to_key = ec.get("strategy_index_to_key") or {}
    keys = (index_to_key.get(str(sv.get("strategy_index"))) for sv in ec.get("strategy_verdicts") or []
            if sv.get("verdict") == "follow")
    return [k for k in keys if k]


def build_ledger(dumps_glob: str) -> tuple[dict[str, SPCredit], Counter]:
    """Credit the vote and night lessons memory-on seats followed, once per lesson per scope."""
    ledger: dict[str, SPCredit] = defaultdict(SPCredit)
    skipped: Counter = Counter()
    for g in _iter_game_records(dumps_glob):
        view, counted = GameView(g), set()
        for ec in iter_eval_cases(g):
            if not ec.get("memory_enabled") or not ec.get("strategy_verdicts"):
                continue
            keys = [k for k in followed_keys(ec) if (decision_scope(ec), k) not in counted]
            if not keys:
                continue
            verdict = decision_credit(ec, view)
            if verdict == "read_excluded":
                skipped[f"read_excluded/{ec.get('player_role')}/{ec.get('action_phase')}"] += 1
                continue
            if verdict is None:
                skipped[f"{ec.get('player_role')}/{ec.get('action_phase')}"] += 1
                continue
            for key in keys:
                counted.add((decision_scope(ec), key))
                ledger[key].add(verdict, decision_channel(ec))
    return ledger, skipped
