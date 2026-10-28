"""Production credit rules — the fixed grading, hard-coded (deterministic, zero spend).

Ten-seat since the port of 2026-10-13 (plan §9.6; the per-decision grades are ``grading``). The
nine-seat grader this module graduated from stays in ``evaluation/src/loop/credit_backfill.py`` with
its knobs, so the frozen research runs still reproduce; production no longer mirrors it.

Sourcing contract (the production event stream): a window is a glob of game-record JSONL dumps,
each record carrying ``roles`` / ``day_resolutions`` / ``night_resolutions`` and an
``eval_cases_path`` sidecar of per-decision eval cases (``strategy_verdicts`` +
``strategy_index_to_key`` join the followed SPs). This is exactly what the batch runner already
emits per game — the live backend must keep emitting it, and must name the human seats of any game
that has them (``human_players``, or the seat id in ``human_player``): credit grades only the AI
seats' decisions, and a human seat's are dropped (owner, 2026-10-26: most served games will have a
human seat, so an AI-only rule would leave credit almost no games; credit only grades the agents'
own decisions by fixed rules against the true roles, while extraction, which writes lesson text,
stays AI-only).

One verdict per lesson per seat per scope (owner, 2026-10-13): a scope is a day's discussion, a
day's vote, a night's pack chat, or a night's act (the kill and the skill share one lookup). A seat
sees the same lessons on every turn of a scope, so counting per turn would weigh one decision
several times; the first scored decision of the scope that followed the lesson is the one counted.
The pack chat decides nothing itself, so a lesson followed there is graded by the pack's move it is
about (its ``pack_move``: the kill, the illusionist's conceal or the chanteuse's block; owner,
2026-10-28), not by the chat's own grade (the night's kill, which stays the chat's memory-off base).
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import dataclass, field

from Agents.memory.consolidation.grading import (
    EVIL, TOWN, WOLVES, GameView, night_channel, night_scope, pack_move_channel, side,
)
from Agents.memory.consolidation.sources import games_from_files

VERDICT_VALUE = {"positive": 1.0, "neutral": 0.0, "negative": -1.0}
SHRINK_K = 5  # low-follow SPs pull toward 0 lift: shrunk = lift * follow/(follow+K)
VERDICT_RANK = {"follow": 3, "override": 2, "not_relevant": 1}
"""A lesson's verdict over a scope's turns: follow on any turn wins, then override."""
BASELINE_MIN_N = 20
"""Memory-off decisions a (channel, day) base needs before a follow is compared with it; a thinner
day falls back to the channel's base over all days (``TickConfig.baseline_min_n``)."""


def _human_seats(g: dict) -> set[str] | None:
    """The game's human seats, or None when it has one but the record does not say which (a record
    that stamps only a flag): its human's decisions could not be told from the agents'."""
    seats = set(g.get("human_players") or [])
    flag = g.get("human_player")
    if isinstance(flag, str):
        seats.add(flag)
    elif flag and not seats:
        return None
    return seats


def _iter_game_records(window):
    """Every game record in the window that may teach: the human-seat guard lives here and in
    ``iter_eval_cases``, once, so every ledger and base in this package inherits it. A game with a
    human seat is read, and only its AI seats' decisions are graded; one whose human seats are not
    named is dropped whole. ``window``: a glob spec of batch-run dumps, or games already loaded
    (``sources``: files and the served games' database, decisions §14)."""
    games = games_from_files(window) if isinstance(window, str) else window
    for g in games:
        if _human_seats(g) is not None:
            yield g


def iter_eval_cases(g: dict):
    """The game's agent-action eval cases, in the order they were played: inline for a served game
    (``eval_cases``), else from the batch run's sidecar. A human seat's cases are skipped."""
    if not g.get("roles"):
        return
    humans = _human_seats(g) or set()
    for ec in _all_eval_cases(g):
        if ec.get("player_id") not in humans:
            yield ec


def _all_eval_cases(g: dict):
    """Every eval case the game recorded, inline or from its sidecar."""
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
    night its turn kind (chat, kill, skill). A lesson followed in the chat is compared by the move it
    is about instead (``chat_follow_credit``)."""
    if ec.get("action_phase") == "night_action":
        return night_channel(ec)
    return f"{ec.get('player_role')}/{ec.get('action_phase')}"


def day_bucket(day) -> str:
    """The game-day part of a decision's baseline key: days 1-3 each on their own, later days pooled
    as "4+" (few games run that long). A night action carries the night's number as recorded."""
    return "4+" if isinstance(day, int) and day >= 4 else str(day)


def day_key(channel: str, bucket: str) -> str:
    """The base-rate key of a channel on one day bucket, beside the channel's own (all-days) key."""
    return f"{channel}@day{bucket}"


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
    """Follows per (baseline channel, day bucket): the SP's base is the follow-weighted mean of each
    follow's matched base."""

    def add(self, verdict: str, channel: str, day=None) -> None:
        self.follow += 1
        setattr(self, verdict, getattr(self, verdict) + 1)
        self.channels[(channel, day_bucket(day))] += 1

    @property
    def utility(self) -> float:
        """Raw outcome rate of followed decisions (the haloed, unbaselined number)."""
        return (self.positive - self.negative) / self.follow if self.follow else 0.0

    def base(self, base_rates: dict, by_day: bool = False, min_n: int = BASELINE_MIN_N) -> float | None:
        """The memory-off mean this SP's follows are compared with: each follow against its own
        channel's base — on its own game day when ``by_day`` (lessons fire at particular stages, and
        an all-days base mixes easy late days with hard early ones). None (unscored) when any channel
        has no memory-off data — a missing baseline is not a baseline of 0."""
        weights: Counter = Counter()
        for (channel, bucket), n in self.channels.items():
            weights[matched_base_key(base_rates, channel, bucket, by_day, min_n)] += n
        if not self.follow or any(k not in base_rates for k in weights):
            return None
        return sum(n * base_rates[k][0] for k, n in weights.items()) / self.follow


def matched_base_key(base_rates: dict, channel: str, bucket: str, by_day: bool,
                     min_n: int = BASELINE_MIN_N) -> str:
    """The base-rate key one follow is compared with: its (channel, day) base when ``by_day`` and
    that day has at least ``min_n`` memory-off decisions, else the channel's base over all days."""
    if by_day:
        day_base = base_rates.get(day_key(channel, bucket))
        if day_base and day_base[1] >= min_n:
            return day_key(channel, bucket)
    return channel


def decision_credit(ec: dict, view: GameView) -> str | None:
    """The verdict for one vote or night decision; None = not graded; "read_excluded" = a town
    seat's negative that belongs to its wrong high-confidence read (counted apart, never valued)."""
    verdict = view.decision_grade(ec)
    if (verdict == "negative" and ec.get("action_phase") == "night_action"
            and side(ec.get("player_role")) == TOWN and read_partition_excluded(ec, view.roles)):
        return "read_excluded"
    return verdict


def compute_base_rates(dumps_glob: str, by_day: bool = False) -> dict[str, tuple[float, int]]:
    """Per channel: the mean graded outcome of MEMORY-OFF decisions, one per scope, graded by the
    same rules as the ledger (baseline coherence by construction). Returns channel -> (mean, n);
    ``by_day`` adds each channel's per-day bases under ``day_key`` (``rate_table``)."""
    grades: list[tuple[str, object, float]] = []
    for g in _iter_game_records(dumps_glob):
        view, seen = GameView(g), set()
        for ec in iter_eval_cases(g):
            if ec.get("memory_enabled"):  # base rate = memory-OFF only
                continue
            verdict = decision_credit(ec, view)
            if verdict not in VERDICT_VALUE or decision_scope(ec) in seen:
                continue
            seen.add(decision_scope(ec))
            grades.append((decision_channel(ec), ec.get("day"), VERDICT_VALUE[verdict]))
    return rate_table(grades, by_day)


def rate_table(grades, by_day: bool = False) -> dict[str, tuple[float, int]]:
    """(channel, day, value) memory-off grades -> {key: (mean, n)}: each channel over all days, and
    with ``by_day`` each (channel, day bucket) too. Shared by every memory-off base (vote, night,
    discussion, concealment) so the day rule is applied the same way to all of them."""
    totals: dict[str, list[float]] = defaultdict(list)
    for channel, day, value in grades:
        totals[channel].append(value)
    if by_day:
        for channel, day, value in grades:
            totals[day_key(channel, day_bucket(day))].append(value)
    return {k: (sum(vs) / len(vs), len(vs)) for k, vs in totals.items() if vs}


def followed_keys(ec: dict) -> list[str]:
    """The store keys of the lessons this decision followed."""
    index_to_key = ec.get("strategy_index_to_key") or {}
    keys = (index_to_key.get(str(sv.get("strategy_index"))) for sv in ec.get("strategy_verdicts") or []
            if sv.get("verdict") == "follow")
    return [k for k in keys if k]


def build_ledger(dumps_glob: str, pack_moves: dict[str, str] | None = None) -> tuple[dict[str, SPCredit], Counter]:
    """Credit the vote and night lessons memory-on seats followed, once per lesson per scope.

    ``pack_moves``: lesson key -> the pack's move a wolf night lesson is about (kill / conceal /
    block). A lesson followed in the wolves' chat is graded by that move (owner, 2026-10-28); a
    lesson with no move recorded falls back to the night's kill, the rule before."""
    pack_moves = pack_moves or {}
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
            if is_pack_chat(ec):
                graded = {k: chat_follow_credit(ec, view, pack_moves.get(k, "kill")) for k in keys}
            else:
                verdict = decision_credit(ec, view)
                graded = {k: (verdict, decision_channel(ec)) for k in keys}
            reasons = set()  # a skip is counted once per decision
            for key, (verdict, channel) in graded.items():
                if verdict == "read_excluded":
                    reasons.add(f"read_excluded/{ec.get('player_role')}/{ec.get('action_phase')}")
                elif verdict is None:
                    reasons.add(f"{ec.get('player_role')}/{ec.get('action_phase')}")
                else:
                    counted.add((decision_scope(ec), key))
                    ledger[key].add(verdict, channel, ec.get("day"))
            skipped.update(reasons)
    return ledger, skipped


def is_pack_chat(ec: dict) -> bool:
    """A wolf's turn in the pack's night chat: it decides nothing itself."""
    return (ec.get("action_phase") == "night_action" and side(ec.get("player_role")) == WOLVES
            and (ec.get("agent_night_action") or {}).get("kind") == "chat")


def chat_follow_credit(ec: dict, view: GameView, move: str) -> tuple[str | None, str]:
    """The verdict and base channel of a lesson followed in the wolves' chat: the grade of the pack's
    move the lesson is about, compared with memory-off play of that move."""
    return view.pack_move_grade(ec.get("day"), move), pack_move_channel(ec, move)
