"""Deterministic case sampler for sampled human + pro-LLM review (rung ② of the modality ladder).

Picks WHICH decision cases a reviewer reads, so the review is representative and recorded instead of
convenient and ephemeral. Four steps, each reusing a part that already exists
(``evidence/evaluation/sampled_human_review/plan.md`` is the spec):

  1. SELECT — two combinable, OUTCOME-BLIND signals:
       a. score-outliers — the DEFAULT source is a deterministic per-case decision score
          (``decision_scoring.score_vote`` / ``score_night_target``: correct/wrong/abstain vs the
          true role map). The application-JUDGE score is an OPT-IN source, flagged uncalibrated in
          the output, because that judge's calibration is a later hardening phase (Phase 2) — ranking
          on an uncalibrated judge would sample its noise, so it never leads.
       b. a deterministic leverage anchor — ``is_swing`` / ``distance_to_parity`` from
          ``decision_scoring.query_criticality``, the pivotalness proxy. It is COMPUTED from the
          case's own frozen board, NEVER read from the LLM situation-dimension fills: the Phase-1
          dimension audit found the wolf-side ``is_swing`` FILL scores 0.606 — worse than the
          always-False constant (0.827) — so trusting the fill would anchor on noise.
     THE HALO RULE IS ABSOLUTE: never select on game outcome (won/lost). Outcome conditioning
     reproduces "did your side win", not "was this case pivotal" (the extraction_selection halo
     lesson). ``assert_outcome_blind`` enforces it — passing an outcome signal raises.

  2. COHORT — expand/balance to a stratified background via ``data.sampling.sample_cases`` (stratify
     by game/role/phase/action; deterministic given a seed), so the reviewed set is representative,
     not just the cherry-picked tails.

  3. REPLAY (``replay_case_stage``) — GUARDED, default OFF, wired-not-run: reconstruct a case's stage
     through the live production prompt. It SPENDS MONEY (live LLM), so it refuses unless a caller
     passes ``enabled=True`` after spend sign-off — the same discipline as ``dimension_audit --regen``.

  4. SURFACE + RECORD — ``render_packet`` produces a human-readable review packet; ``ReviewVerdict`` +
     ``append_verdict`` persist reviewer verdicts to a durable local JSONL (the missing piece today),
     mirroring the tracing eval-capture pattern (local artifact primary).
"""

from __future__ import annotations

import contextlib
import io
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from statistics import median
from typing import Any, Iterable, Optional

from pydantic import BaseModel, Field

from Agents.schemas.evaluation import EvalCase
from evaluation.src.data.sampling import classify_game_phase, sample_cases
from evaluation.src.data.sources.sidecar import LocalCaseSource
from evaluation.src.loop.decision_scoring import (
    REPLAYABLE_DECEIVER_ROLES,
    query_criticality,
    score_night_target,
    score_vote,
)

# ── The outcome-halo guard ───────────────────────────────────────────────────────────────────────
# Substrings / exact tokens that name a game OUTCOME. Selecting on any of these reproduces the
# extraction_selection halo ("did your side win") instead of pivotalness — it is the one thing the
# sampler must never do. Kept narrow so structural signals (is_swing, distance_to_parity, hit_threat,
# town_vote_accuracy — a de-lucked proxy, allowed) pass cleanly.
_OUTCOME_BANNED_SUBSTRINGS = (
    "winner",
    "faction_won",
    "game_outcome",
    "_won",
    "who_won",
    "did_win",
)
_OUTCOME_BANNED_EXACT = frozenset(
    {"won", "win", "lost", "loss", "outcome", "victory", "defeat", "result"}
)


def assert_outcome_blind(signal: str) -> None:
    """Raise if ``signal`` names a game-outcome field. The halo rule from plan.md is absolute:
    conditioning selection on won/lost reproduces faction success, not case pivotalness."""
    name = (signal or "").strip().lower()
    if name in _OUTCOME_BANNED_EXACT or any(s in name for s in _OUTCOME_BANNED_SUBSTRINGS):
        raise ValueError(
            f"Refusing to select on {signal!r}: it is a game-OUTCOME signal. The "
            "extraction_selection halo lesson (plan.md) is absolute — selecting on won/lost "
            "reproduces 'did your side win', not 'was this case pivotal'. Use the deterministic "
            "leverage anchor (is_swing / distance_to_parity) for pivotalness instead."
        )


# ── Signal 1a: deterministic decision score (the default outlier source) ─────────────────────────
TOWN_LENS_ROLES = frozenset({"villager", "healer", "investigator", "vigilante"})
DECEIVER_LENS_ROLES = REPLAYABLE_DECEIVER_ROLES  # wolf + serial_killer

# The identifier the default outlier source is guarded/reported under.
DETERMINISTIC_SIGNAL = "decision_score"


def _lens_for(role: str) -> str:
    return "deceiver" if role in DECEIVER_LENS_ROLES else "town"


def decision_score(case: EvalCase, roles: dict[str, str]) -> Optional[tuple[float, str]]:
    """A deterministic, OUTCOME-BLIND per-case scalar from the frozen board (``roles`` is the true
    role map, NEVER the game winner). Returns ``(signed_score, label)`` or ``None`` when the phase has
    no mechanical score (``day_discussion`` — message quality needs a judge).

    Lensed by faction so a deceiver run scores on its OWN win condition (a wolf/SK "good" day-vote
    INDUCES a town mislynch, the mirror of town's ``hit_threat``). ``+1`` = the faction-correct call,
    ``-1`` = the faction-wrong call, ``0`` = abstain/no-op. Outlier magnitude is ``abs(score)``.
    """
    lens = _lens_for(case.player_role)
    if case.action_phase == "day_vote":
        votee = case.agent_vote.votee if case.agent_vote else None
        ov = score_vote(votee, roles)
        if lens == "town":
            if ov.hit_threat:
                return 1.0, "hit_threat"
            if ov.is_town_mislynch:
                return -1.0, "mislynch"
            return 0.0, ("abstain" if ov.is_abstain else "neutral")
        # deceiver
        if ov.is_town_mislynch:
            return 1.0, "induced_mislynch"
        if ov.is_abstain:
            return 0.0, "abstain"
        return -1.0, "no_mislynch"  # voted a fellow threat or failed to drive a mislynch
    if case.action_phase == "night_action":
        target = case.agent_night_action.target if case.agent_night_action else None
        no = score_night_target(target, roles)
        if lens == "town":
            if no.hit_threat:
                return 1.0, "hit_threat"
            if no.hit_town:
                return -1.0, "hit_town"  # friendly fire (vigilante) / wasted heal on a townie-miss
            return 0.0, "noop"
        # deceiver — power kill is the high-value target
        if no.hit_power:
            return 1.0, "hit_power"
        if no.hit_town:
            return 0.5, "hit_town"
        return 0.0, "noop_or_threat"
    return None


# ── Signal 1b: deterministic leverage anchor ─────────────────────────────────────────────────────
def leverage_anchor(case: EvalCase, roles: dict[str, str]) -> Optional[dict[str, Any]]:
    """``{players_alive, distance_to_parity, is_swing}`` from the case's OWN survivor roster via
    ``query_criticality`` — computed, never the LLM fill (see module docstring). ``None`` when the
    roster is unavailable (e.g. wolf night-action cases persist an empty ``surviving_players``, per
    the dimension audit), so ``is_swing`` is never manufactured from a bogus empty board."""
    roster = list(case.private_context.surviving_players)
    if not roster:
        return None
    alive, dist, swing = query_criticality(roster, roles)
    return {"players_alive": alive, "distance_to_parity": dist, "is_swing": bool(swing)}


# ── Scored case ──────────────────────────────────────────────────────────────────────────────────
@dataclass
class ScoredCase:
    """One case with its selection signals attached. ``reasons`` records WHY it made the review set
    (``outlier:<source>`` / ``leverage:is_swing`` / ``cohort:stratified``); empty = not selected."""

    case: EvalCase
    game_id: str
    outlier_score: Optional[float]
    outlier_label: str
    outlier_source: str
    outlier_uncalibrated: bool
    leverage: Optional[dict[str, Any]]
    reasons: list[str] = field(default_factory=list)

    @property
    def key(self) -> str:
        return self.case.observation_id or self.case.span_name

    @property
    def is_swing(self) -> bool:
        return bool(self.leverage and self.leverage.get("is_swing"))

    @property
    def outlier_magnitude(self) -> float:
        return abs(self.outlier_score) if self.outlier_score is not None else 0.0


def _score_case(
    case: EvalCase,
    roles: dict[str, str],
    outlier_source: str,
    judge_scores: Optional[dict[str, float]],
    judge_center: float,
) -> tuple[Optional[float], str, bool]:
    """Return ``(score, label, uncalibrated)`` for the chosen outlier source."""
    if outlier_source == DETERMINISTIC_SIGNAL:
        ds = decision_score(case, roles)
        if ds is None:
            return None, "n/a", False
        return ds[0], ds[1], False
    # opt-in judge / metric channel — deviation from the batch median, flagged uncalibrated.
    if not judge_scores:
        return None, "no_judge_score", True
    val = judge_scores.get(case.observation_id)
    if val is None:
        return None, "no_judge_score", True
    return float(val) - judge_center, f"{outlier_source}={val:g}", True


def build_scored_cases(
    cases: list[EvalCase],
    game_index: dict[str, dict[str, Any]],
    *,
    outlier_source: str = DETERMINISTIC_SIGNAL,
    judge_scores: Optional[dict[str, float]] = None,
) -> list[ScoredCase]:
    """Attach both selection signals to every memory-enabled case. Memory-off cases are dropped: with
    no retrieval there is nothing to review about the memory pipeline (matches ``sample_cases``)."""
    assert_outcome_blind(outlier_source)
    judge_center = median(judge_scores.values()) if judge_scores else 0.0
    scored: list[ScoredCase] = []
    for case in cases:
        if not case.memory_enabled:
            continue
        game = game_index.get(case.trace_id)
        if not game:
            continue
        roles = game.get("roles", {}) or {}
        s, label, uncal = _score_case(case, roles, outlier_source, judge_scores, judge_center)
        scored.append(
            ScoredCase(
                case=case,
                game_id=str(game.get("game_id") or case.trace_id),
                outlier_score=s,
                outlier_label=label,
                outlier_source=outlier_source,
                outlier_uncalibrated=uncal,
                leverage=leverage_anchor(case, roles),
            )
        )
    return scored


# ── The select -> cohort assembly ────────────────────────────────────────────────────────────────
def select_review_cases(
    cases: list[EvalCase],
    game_index: dict[str, dict[str, Any]],
    game_lengths: dict[str, int],
    *,
    outlier_source: str = DETERMINISTIC_SIGNAL,
    judge_scores: Optional[dict[str, float]] = None,
    n_outliers: int = 12,
    n_leverage: int = 12,
    cohort_per_bucket: int = 1,
    cohort_max: Optional[int] = None,
    seed: int = 0,
    action_phases: Optional[Iterable[str]] = None,
) -> list[ScoredCase]:
    """Assemble the review set: outlier tails + the most-pivotal (leverage) cases + a stratified
    background cohort, deterministic given ``seed``. Each returned case carries its ``reasons``.
    Deterministically ordered by (game, day, role, phase, key).

    The two SELECT signals are combinable axes, not floodgates: the outlier channel ranks by decision
    magnitude, the leverage channel ranks by pivotalness (``is_swing`` then closeness to parity). A
    case flagged by both carries both reasons. ``is_swing`` alone spans most of late game, so leverage
    takes the top ``n_leverage`` (nearest-parity) rather than every swing case."""
    assert_outcome_blind(outlier_source)
    scored = build_scored_cases(
        cases, game_index, outlier_source=outlier_source, judge_scores=judge_scores
    )
    by_key: dict[str, ScoredCase] = {sc.key: sc for sc in scored}

    # Channel 1: score-outliers — the tails, ranked by magnitude, is_swing then later-day as
    # deterministic tie-breaks (later days are higher-stakes per vote).
    outlier_pool = sorted(
        (sc for sc in scored if sc.outlier_score is not None and sc.outlier_magnitude > 0),
        key=lambda sc: (sc.outlier_magnitude, sc.is_swing, sc.case.day, sc.key),
        reverse=True,
    )
    for sc in outlier_pool[:n_outliers]:
        tag = f"outlier:{sc.outlier_source}"
        if sc.outlier_uncalibrated:
            tag += "(uncalibrated)"
        sc.reasons.append(tag)

    # Channel 2: leverage anchor — the MOST pivotal boards. Rank by is_swing, then nearest parity
    # (smallest distance_to_parity), then later day; take the top n_leverage so it stays a handful.
    leverage_pool = sorted(
        (sc for sc in scored if sc.leverage is not None),
        key=lambda sc: (sc.is_swing, -sc.leverage["distance_to_parity"], sc.case.day, sc.key),
        reverse=True,
    )
    for sc in leverage_pool[:n_leverage]:
        if sc.is_swing:  # only genuinely pivotal boards earn the anchor tag
            sc.reasons.append("leverage:is_swing")

    # Channel 3: stratified background cohort (representative, not just the tails).
    cohort = sample_cases(
        cases,
        game_lengths,
        per_role_per_phase=cohort_per_bucket,
        max_samples=cohort_max,
        seed=seed,
        action_phases=action_phases,
    )
    for c in cohort:
        key = c.observation_id or c.span_name
        sc = by_key.get(key)
        if sc is not None:
            sc.reasons.append("cohort:stratified")

    selected = [sc for sc in scored if sc.reasons]
    selected.sort(
        key=lambda sc: (
            sc.game_id,
            sc.case.day,
            sc.case.player_role,
            str(sc.case.action_phase),
            sc.key,
        )
    )
    return selected


def cohort_strata(selected: list[ScoredCase], game_lengths: dict[str, int]) -> dict[str, int]:
    """Strata counts (role · phase · game-phase · selection-reason) for a report/summary line."""
    from collections import Counter

    by_role: Counter[str] = Counter()
    by_phase: Counter[str] = Counter()
    by_gamephase: Counter[str] = Counter()
    by_reason: Counter[str] = Counter()
    for sc in selected:
        by_role[sc.case.player_role] += 1
        by_phase[str(sc.case.action_phase)] += 1
        by_gamephase[
            classify_game_phase(sc.case.day, game_lengths.get(sc.case.trace_id, 3))
        ] += 1
        for r in sc.reasons:
            by_reason[r] += 1
    return {
        "n_selected": len(selected),
        "by_role": dict(by_role),
        "by_action_phase": dict(by_phase),
        "by_game_phase": dict(by_gamephase),
        "by_reason": dict(by_reason),
    }


# ── Step 3: guarded replay (wired, default OFF, PAID) ────────────────────────────────────────────
def replay_case_stage(
    case: EvalCase,
    *,
    enabled: bool = False,
    retrieved_observations: Optional[list[Any]] = None,
    strategy_points: Optional[list[Any]] = None,
) -> Any:
    """GUARDED / PAID. Reconstruct and re-run this case's decision stage through the live production
    prompt (``evaluation.src.replay.run_application_action``) — a LIVE LLM call that SPENDS MONEY.

    Default OFF and NOT auto-run (mirrors ``dimension_audit --regen``): wired so the review path can
    optionally regenerate a decision under review, but a caller must pass ``enabled=True`` after
    explicit spend sign-off. Building/selecting/rendering is $0; this is the only step that costs."""
    if not enabled:
        raise RuntimeError(
            "replay_case_stage is a PAID live-LLM step (it regenerates the decision) and is OFF by "
            "default. Pass enabled=True ONLY after explicit spend sign-off — the rest of the sampler "
            "is $0."
        )
    from evaluation.src.replay.turn_action import run_application_action  # heavy import, kept lazy

    return run_application_action(
        case,
        retrieved_observations=retrieved_observations,
        strategy_points=strategy_points,
    )


# ── Step 4a: surface — the human-readable review packet ──────────────────────────────────────────
def _discussion_tail(case: EvalCase, n: int = 8) -> list[str]:
    tail = [d for d in case.visible_discussion if not getattr(d, "passed", False)][-n:]
    return [f"    [{d.player}] {d.message}".rstrip() for d in tail if d.message]


def _retrieval_lines(case: EvalCase, n: int = 8) -> list[str]:
    lines: list[str] = []
    for i, item in enumerate(case.retrieved_observations[:n], 1):
        obs = item.observation
        score = f"{item.score:.3f}" if getattr(item, "score", None) is not None else "n/a"
        lines.append(
            f"    [{i}] sim={score} verdict={getattr(obs, 'net_verdict', '?') or '?'}"
            f" :: {(getattr(obs, 'approach', '') or '')[:140]}"
        )
        situ = (getattr(obs, "situation", "") or "")[:140]
        if situ:
            lines.append(f"        situation: {situ}")
    return lines or ["    (no retrieved observations)"]


def _decision_line(case: EvalCase, roles: dict[str, str]) -> str:
    if case.agent_vote is not None:
        v = case.agent_vote.votee
        return f"vote -> {v} (true role: {roles.get(v, 'unknown') if v and v != 'abstain' else '—'})"
    if case.agent_night_action is not None:
        t = case.agent_night_action.target
        return f"night target -> {t} (true role: {roles.get(t, 'unknown') if t else '—'})"
    if case.agent_message is not None:
        return f"message -> {case.agent_message.message[:280]}"
    return "(no recorded action)"


def render_packet(sc: ScoredCase, roles: dict[str, str], *, question: str = "") -> str:
    """Render one case to a plain-markdown review packet: WHY it was flagged (the scores), the
    situation, the visible discussion tail, the retrieval, and the decision. Outcome-blind — it
    shows the board and the decision, never who won the game."""
    c = sc.case
    lines: list[str] = []
    lines.append(f"### {sc.game_id[:8]} · {c.player_role} · day {c.day} · {c.action_phase}")
    lines.append(f"- case: trace={c.trace_id[:8]} obs={c.observation_id or c.span_name}")
    lines.append(f"- selected because: {', '.join(sc.reasons) or '(none)'}")
    if sc.outlier_score is not None:
        cal = " [UNCALIBRATED judge score]" if sc.outlier_uncalibrated else ""
        lines.append(
            f"- outlier[{sc.outlier_source}] = {sc.outlier_score:+g} ({sc.outlier_label}){cal}"
        )
    lines.append(f"- leverage: {sc.leverage if sc.leverage is not None else '(no roster)'}")
    if question:
        lines.append(f"- review question: {question}")
    lines.append("")
    lines.append("**situation summary (query side):**")
    for s in case_situations(c):
        lines.append(f"    {s}")
    lines.append("")
    lines.append("**visible discussion tail:**")
    lines.extend(_discussion_tail(c) or ["    (none)"])
    lines.append("")
    lines.append("**retrieval:**")
    lines.extend(_retrieval_lines(c))
    lines.append("")
    lines.append("**decision:**")
    lines.append(f"    {_decision_line(c, roles)}")
    if c.updated_strategy:
        lines.append(f"    reasoning: {c.updated_strategy[:400]}")
    lines.append("")
    return "\n".join(lines)


def case_situations(case: EvalCase) -> list[str]:
    return [s for s in case.situations if s] or ["(no situation summary captured)"]


# ── Step 4b: record — durable verdict JSONL (local artifact primary) ─────────────────────────────
class ReviewVerdict(BaseModel):
    """One recorded review of one case — the durable artifact rung ② lacked. Local JSONL is the
    primary store (mirrors the tracing eval-capture pattern), so a review is reproducible and citable
    as evidence, not just judgment."""

    trace_id: str = ""
    observation_id: str = ""
    span_name: str = ""
    game_id: str = ""
    player_role: str = ""
    day: int = 0
    action_phase: str = ""
    reviewer: str
    """Who reviewed: ``human`` or a model id (e.g. ``model:gemini-2.5-pro``)."""
    question: str
    """The question this verdict answers (e.g. 'does the situation read like the right query?')."""
    verdict: str
    """The reviewer's call (free-form or a small enum the caller defines, e.g. good/bad/needs_fix)."""
    notes: str = ""
    selection_reasons: list[str] = Field(default_factory=list)
    """Why the case was sampled — carried onto the verdict so the record is self-describing."""
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


def verdict_for(
    sc: ScoredCase, *, reviewer: str, question: str, verdict: str, notes: str = ""
) -> ReviewVerdict:
    """Build a ``ReviewVerdict`` pre-filled from a selected case's identity + selection reasons."""
    c = sc.case
    return ReviewVerdict(
        trace_id=c.trace_id,
        observation_id=c.observation_id,
        span_name=c.span_name,
        game_id=sc.game_id,
        player_role=c.player_role,
        day=c.day,
        action_phase=str(c.action_phase),
        reviewer=reviewer,
        question=question,
        verdict=verdict,
        notes=notes,
        selection_reasons=list(sc.reasons),
    )


def append_verdict(path: Path, verdict: ReviewVerdict) -> None:
    """Append one verdict as a JSONL line (durable, local-primary). Creates the file/parents."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(verdict.model_dump_json() + "\n")


def load_verdicts(path: Path) -> list[ReviewVerdict]:
    if not path.exists():
        return []
    out: list[ReviewVerdict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            out.append(ReviewVerdict.model_validate_json(line))
    return out


# ── Loading real local cases (sidecar + batch record) ────────────────────────────────────────────
def load_cases_and_index(
    batch_path: Path,
) -> tuple[list[EvalCase], dict[str, dict[str, Any]], dict[str, int]]:
    """Load every eval case from a batch's local sidecars plus the per-game index (roles + game_id)
    and game_lengths, joined by ``trace_id`` — the read side the sampler runs on ($0, offline)."""
    with contextlib.redirect_stdout(io.StringIO()):  # silence the "skipped N games" chatter
        source = LocalCaseSource(batch_path)
    index: dict[str, dict[str, Any]] = {}
    game_lengths: dict[str, int] = {}
    for line in batch_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rec = json.loads(line)
        tid = rec.get("trace_id")
        if not tid:
            continue
        index[tid] = {"roles": rec.get("roles", {}) or {}, "game_id": rec.get("game_id") or tid}
        cm = rec.get("computed_metrics") or {}
        length = cm.get("game_length")
        if not length:
            drs = rec.get("day_resolutions") or []
            length = max((r.get("day", 0) for r in drs), default=3)
        game_lengths[tid] = int(length) or 3

    cases: list[EvalCase] = []
    for tid in source.trace_ids():
        cases.extend(source.eval_cases(tid))
    return cases, index, game_lengths
