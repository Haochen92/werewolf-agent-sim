"""Score replayed votes by their target, with no judge: the canonical vote scorer.

A bench run over vote cases (``eval-hallucination-bench`` on a set of ``day_vote`` cases) writes one
``generations_<arm>.jsonl`` per arm; each valid sample carries ``vote`` (the structured
``vote_target``, limited to the legal targets). A vote is right when its target is on the wolves' or
the lone killer's side, read from the role registry by ``score_vote``
(``Agents/memory/consolidation/decision_scoring.py``), against the true roles frozen in the case. A case
can replace that with its own right targets, for a day where "right" is defined by the evidence rather
than the roles: the case record's ``right_vote_targets`` list, or the admission config's
``right_target_overrides`` mapping (case id → targets), which wins. "abstain" may be listed as right;
otherwise an abstain is scored as wrong.

Used by the admission runner (``evaluation/src/cli_runner/admit.py``). On its own, from Python:

  from evaluation.src.model_admission.vote_scoring import load_vote_cases, score_bench_votes
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from Agents.memory.consolidation.decision_scoring import score_vote
from evaluation.src.cli_runner.regen_replay.both.hallucination_bench import _read_jsonl as read_bench_jsonl
from evaluation.src.core.settings import REPO_ROOT
from evaluation.src.core.stats import mcnemar_exact
from evaluation.src.model_admission.schemas import (
    ArmVoteScore,
    VoteCaseRow,
    VoteComparison,
    VoteSampleScore,
)


def load_true_roles(case: dict) -> dict[str, str]:
    """Return the true role of every seat in the game a vote case was cut from.

    The case builders (e.g. ``evaluation/experiments/haiku_effort_cases.py``, through
    ``haiku_vote_cases.pre_vote_state``) freeze the game checkpoint's whole state into the case, and the
    state's ``roles`` is the game's deal. So the roles are read from the case record itself, never from
    the vote's own reasoning.

    Args:
        case: one frozen bench case, e.g. {"case_id": "...", "state": {"roles": {"player_1":
            "chanteuse", ...}, ...}, ...}.

    Returns:
        Player id → role, e.g. {"player_1": "chanteuse", "player_2": "vigilante"}. Raises ValueError
        when the case carries no roles.
    """
    roles = (case.get("state") or {}).get("roles")
    if not roles:
        raise ValueError(f"case {case.get('case_id')} has no state.roles to score its votes against")
    return dict(roles)


def right_targets_for_case(case: dict, overrides: dict[str, list[str]]) -> tuple[list[str], str]:
    """Return the targets that count as a right vote on one case, and where they came from.

    Order of precedence: the config's override for this case id, then the case record's own
    ``right_vote_targets``, then every seat whose true role is a threat (``score_vote``'s
    ``hit_threat``: the wolves' and the lone killer's sides, from the role registry).

    Args:
        case: one frozen bench case (see ``load_true_roles``).
        overrides: case id → right targets, from the case set's ``right_target_overrides``.

    Returns:
        (right targets, source), e.g. (["player_1", "player_3", "player_6"], "roles") or
        (["player_6", "player_10", "abstain"], "override"). Source is "override", "case_record" or "roles".
    """
    case_id = case["case_id"]
    if case_id in overrides:
        return list(overrides[case_id]), "override"
    if case.get("right_vote_targets"):
        return list(case["right_vote_targets"]), "case_record"
    roles = load_true_roles(case)
    threat_seats = []
    for player in roles:
        if score_vote(player, roles).hit_threat:
            threat_seats.append(player)
    return threat_seats, "roles"


def score_vote_sample(sample: dict, case: dict, right_targets: list[str]) -> VoteSampleScore:
    """Score one generated vote sample against its case's right targets.

    Args:
        sample: one line of a bench ``generations_<arm>.jsonl``, e.g. {"case_id": "...", "sample": 3,
            "valid": true, "vote": "player_6", "units": [...], "usage": {...}}.
        case: the frozen case the sample answers.
        right_targets: the case's right targets (``right_targets_for_case``).

    Returns:
        The sample's score: "right", "wrong", or "unscorable" with the reason (an invalid sample, no
        vote in the reply, or a target that is not a player in the game).
    """
    case_id = sample["case_id"]
    sample_index = sample.get("sample", -1)
    vote_target = sample.get("vote")
    if not sample.get("valid"):
        return VoteSampleScore(case_id=case_id, sample=sample_index, vote_target=vote_target,
                               outcome="unscorable", unscorable_reason="invalid sample (generation failed)")
    if not vote_target:
        return VoteSampleScore(case_id=case_id, sample=sample_index, vote_target=None,
                               outcome="unscorable", unscorable_reason="the reply carries no vote target")
    vote_outcome = score_vote(vote_target, load_true_roles(case))
    if not vote_outcome.is_abstain and vote_outcome.votee_role is None:
        return VoteSampleScore(case_id=case_id, sample=sample_index, vote_target=vote_target,
                               outcome="unscorable",
                               unscorable_reason=f"target {vote_target!r} is not a player in this game")
    outcome = "right" if vote_target in right_targets else "wrong"
    return VoteSampleScore(case_id=case_id, sample=sample_index, vote_target=vote_target,
                           outcome=outcome, is_abstain=vote_outcome.is_abstain)


def score_vote_arm(arm_label: str, samples: list[dict], cases: dict[str, dict],
                   overrides: dict[str, list[str]]) -> ArmVoteScore:
    """Score every vote sample of one arm, with totals and a row per case.

    Samples of cases outside ``cases`` are ignored, so an output file holding more cases than the case
    set (a set narrowed by slices) scores only the set's cases.

    Args:
        arm_label: the bench arm, e.g. "candidate_low".
        samples: the arm's generation lines (see ``score_vote_sample``).
        cases: case id → frozen case, in the case set's order (``load_vote_cases``).
        overrides: case id → right targets (the case set's ``right_target_overrides``).

    Returns:
        The arm's right / scored / abstain totals, its unscorable samples with reasons, and one
        ``VoteCaseRow`` per case.
    """
    scores_by_case: dict[str, list[VoteSampleScore]] = {case_id: [] for case_id in cases}
    right_by_case: dict[str, tuple[list[str], str]] = {}
    for case_id, case in cases.items():
        right_by_case[case_id] = right_targets_for_case(case, overrides)
    for sample in samples:
        case_id = sample["case_id"]
        if case_id not in cases:
            continue
        right_targets = right_by_case[case_id][0]
        scores_by_case[case_id].append(score_vote_sample(sample, cases[case_id], right_targets))

    per_case = []
    unscorable_samples = []
    for case_id, case in cases.items():
        sample_scores = scores_by_case[case_id]
        scored_samples = [score for score in sample_scores if score.outcome != "unscorable"]
        unscorable_samples += [score for score in sample_scores if score.outcome == "unscorable"]
        right_targets, right_source = right_by_case[case_id]
        per_case.append(VoteCaseRow(
            case_id=case_id,
            game_id=case.get("game_id", ""),
            day=case["day"],
            voter=case["speaker"],
            voter_role=case.get("role") or load_true_roles(case)[case["speaker"]],
            right_targets=right_targets,
            right_source=right_source,
            right=sum(1 for score in scored_samples if score.outcome == "right"),
            scored=len(scored_samples),
            abstains=sum(1 for score in scored_samples if score.is_abstain),
            unscorable=len(sample_scores) - len(scored_samples),
            vote_counts=dict(Counter(score.vote_target for score in scored_samples)),
        ))
    return ArmVoteScore(
        arm_label=arm_label,
        right=sum(row.right for row in per_case),
        scored=sum(row.scored for row in per_case),
        abstains=sum(row.abstains for row in per_case),
        unscorable=unscorable_samples,
        per_case=per_case,
    )


def compare_vote_arms(reference: ArmVoteScore, candidate: ArmVoteScore) -> VoteComparison:
    """Compare two arms' votes case by case, with an exact two-sided sign test.

    On each case scored in both arms, the candidate is "better" when its right rate is higher than the
    reference's and "worse" when lower; tied cases drop out. The sign test is the exact McNemar test of
    ``evaluation/src/core/stats.py`` on those per-case flags, which is the same two-sided binomial test
    at one half that the bench applies to bad-sample rates.

    Args:
        reference: the reference arm's score (``score_vote_arm``).
        candidate: the candidate arm's score, over the same case set.

    Returns:
        The number of shared cases, the better and worse counts, and the sign test's p.
    """
    reference_rows = {row.case_id: row for row in reference.per_case if row.scored}
    candidate_rows = {row.case_id: row for row in candidate.per_case if row.scored}
    reference_better_flags = []
    candidate_better_flags = []
    for case_id, reference_row in reference_rows.items():
        if case_id not in candidate_rows:
            continue
        reference_rate = reference_row.right / reference_row.scored
        candidate_rate = candidate_rows[case_id].right / candidate_rows[case_id].scored
        reference_better_flags.append(1 if reference_rate > candidate_rate else 0)
        candidate_better_flags.append(1 if candidate_rate > reference_rate else 0)
    if reference_better_flags:
        sign_test = mcnemar_exact(reference_better_flags, candidate_better_flags)
        better, worse, p_value = sign_test.c_on_only, sign_test.b_off_only, sign_test.p_value
    else:
        better, worse, p_value = 0, 0, 1.0
    return VoteComparison(
        reference_arm=reference.arm_label,
        candidate_arm=candidate.arm_label,
        cases=len(reference_better_flags),
        better=better,
        worse=worse,
        two_sided_sign_p=round(float(p_value), 4),
    )


def load_vote_cases(dataset: str | Path, slices: list[str] | None = None) -> dict[str, dict]:
    """Load a vote case set, keeping only vote cases in the given slices.

    Args:
        dataset: the frozen cases file, absolute or relative to the repo root, e.g.
            "evidence/gameplay/deduction/data/haiku_effort_replay/vote_cases.jsonl".
        slices: keep only cases whose ``slice`` is listed, e.g. ["vote_compare", "vote"]; None keeps all.

    Returns:
        Case id → case, in file order, for every ``day_vote`` case kept.
    """
    cases = {}
    for case in read_bench_jsonl(REPO_ROOT / dataset):
        if case.get("phase") != "day_vote":
            continue
        if slices and case.get("slice") not in slices:
            continue
        cases[case["case_id"]] = case
    return cases


def score_bench_votes(bench_dir: Path, arm_labels: list[str], cases: dict[str, dict],
                      overrides: dict[str, list[str]]) -> dict[str, ArmVoteScore]:
    """Score the votes of every listed arm a bench run has generated.

    Args:
        bench_dir: the bench run's output folder, holding ``generations_<arm>.jsonl`` files, e.g.
            evaluation/eval_results/hallucination_bench/haiku_effort_votes.
        arm_labels: the arms to score, e.g. ["reference_low", "candidate_low"].
        cases: the vote case set (``load_vote_cases``).
        overrides: case id → right targets.

    Returns:
        Arm label → its score, for each listed arm whose generations file exists (missing arms are left
        out, so a caller can report them as not measured).
    """
    scores = {}
    for arm_label in arm_labels:
        generations_path = bench_dir / f"generations_{arm_label}.jsonl"
        if not generations_path.exists():
            continue
        scores[arm_label] = score_vote_arm(arm_label, read_bench_jsonl(generations_path), cases, overrides)
    return scores
