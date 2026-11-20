"""Apply an admission config's pass criteria to outputs already on disk, and return the verdict.

Reads, per thinking level of the candidate, its probe record (``eval-model-admission``'s JSON) and, per
case set, the bench run's per-sample files (``judged_<arm>.jsonl``, else ``generations_<arm>.jsonl``) and
``summary.json`` (its per-case sign test against the first arm, which is the reference). Each criterion
comes back passed, failed or not measured; a level is "reject" when any failed, "incomplete" when any
was not measured, else "admit". Nothing here calls a model.

Used by the admission runner (``evaluation/src/cli_runner/admit.py``); from Python:

  from evaluation.src.model_admission.gate import evaluate_admission
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy

from evaluation.src.model_admission.schemas import (
    AdmissionConfig,
    AdmissionVerdict,
    ArmSampleStats,
    ArmVerdict,
    ArmVoteScore,
    CaseSet,
    CriterionResult,
    VoteComparison,
)
from evaluation.src.model_admission.vote_scoring import compare_vote_arms, read_bench_jsonl

# A level asks for thinking unless it is unset or "minimal": the same rule probes.recommend_mode uses.
NO_THINKING_LEVELS = (None, "minimal")


def reference_arm_label(config: AdmissionConfig) -> str:
    """Return the reference's arm label in every bench run.

    Args:
        config: the admission config.

    Returns:
        "reference_<level>", e.g. "reference_low".
    """
    return f"reference_{config.reference.thinking_level}"


def candidate_arm_label(thinking_level: str) -> str:
    """Return the candidate's arm label at one thinking level.

    Args:
        thinking_level: e.g. "medium".

    Returns:
        "candidate_<level>", e.g. "candidate_medium".
    """
    return f"candidate_{thinking_level}"


# --- reading outputs -----------------------------------------------------------------------------------


def read_arm_samples(bench_dir: Path, arm_label: str) -> tuple[list[dict], bool] | None:
    """Return one arm's samples from a bench run, preferring the judged file.

    Args:
        bench_dir: the bench run's output folder.
        arm_label: the arm, e.g. "candidate_low".

    Returns:
        (samples, judged): the lines of ``judged_<arm>.jsonl`` with judged True, else of
        ``generations_<arm>.jsonl`` with judged False; None when neither file exists.
    """
    judged_path = bench_dir / f"judged_{arm_label}.jsonl"
    if judged_path.exists():
        return read_bench_jsonl(judged_path), True
    generations_path = bench_dir / f"generations_{arm_label}.jsonl"
    if generations_path.exists():
        return read_bench_jsonl(generations_path), False
    return None


def latency_percentiles(seconds: list[float]) -> tuple[float, float]:
    """Return the median and the 95th percentile of per-sample seconds.

    Args:
        seconds: one generation time per sample, e.g. [7.5, 9.1, 12.0].

    Returns:
        (p50, p95), each by numpy's linear interpolation between the closest ranks, rounded to 0.1 s.
        Raises ValueError on an empty list (a caller reports "not measured" instead).
    """
    if not seconds:
        raise ValueError("no timed samples")
    p50 = float(numpy.percentile(seconds, 50))
    p95 = float(numpy.percentile(seconds, 95))
    return round(p50, 1), round(p95, 1)


def arm_sample_stats(arm_label: str, samples: list[dict], judged: bool) -> ArmSampleStats:
    """Sum one arm's samples: validity, bad samples, latency and tokens.

    Args:
        arm_label: the arm, e.g. "reference_low".
        samples: its bench sample lines, e.g. {"case_id": "...", "valid": true, "bad": false,
            "usage": {"output": 852, "reasoning": 364, "seconds": 4.8, ...}}.
        judged: whether the lines come from the judged file (so ``bad`` is set).

    Returns:
        The arm's totals. Latency and tokens are None when no valid sample recorded its usage; they are
        never estimated.
    """
    valid_samples = [sample for sample in samples if sample.get("valid")]
    usages = [sample["usage"] for sample in valid_samples if sample.get("usage")]
    timed_seconds = [usage["seconds"] for usage in usages if usage.get("seconds") is not None]
    if timed_seconds:
        seconds_p50, seconds_p95 = latency_percentiles(timed_seconds)
    else:
        seconds_p50, seconds_p95 = None, None
    output_per_sample = None
    reasoning_per_sample = None
    if usages:
        output_per_sample = round(sum(usage.get("output", 0) for usage in usages) / len(usages), 1)
        reasoning_per_sample = round(sum(usage.get("reasoning", 0) for usage in usages) / len(usages), 1)
    bad = None
    if judged:
        bad = sum(1 for sample in valid_samples if sample.get("bad"))
    return ArmSampleStats(
        arm_label=arm_label,
        valid=len(valid_samples),
        invalid=len(samples) - len(valid_samples),
        judged=judged,
        bad=bad,
        samples_timed=len(timed_seconds),
        seconds_p50=seconds_p50,
        seconds_p95=seconds_p95,
        samples_with_usage=len(usages),
        output_tokens_per_sample=output_per_sample,
        reasoning_tokens_per_sample=reasoning_per_sample,
    )


def read_paired_sign_test(bench_dir: Path, reference_arm: str, candidate_arm: str) -> dict | None:
    """Return the bench's per-case sign test of the candidate arm against the reference arm.

    Args:
        bench_dir: the bench run's output folder, holding ``summary.json``.
        reference_arm: the arm the bench must have run first (it compares every arm with the first).
        candidate_arm: the arm to look up.

    Returns:
        The summary's ``paired_vs_first`` entry, e.g. {"cases": 14, "better": 3, "worse": 1,
        "two_sided_sign_p": 0.625}; None when the summary is missing, its first arm is not the
        reference, or it has no entry for the candidate.
    """
    summary_path = bench_dir / "summary.json"
    if not summary_path.exists():
        return None
    summary = json.loads(summary_path.read_text())
    arms_in_order = list(summary.get("arms", {}))
    if not arms_in_order or arms_in_order[0] != reference_arm:
        return None
    return summary.get("paired_vs_first", {}).get(candidate_arm)


# --- criteria ------------------------------------------------------------------------------------------


def _not_measured(name: str, area: str, limit: str, why: str, case_set: str | None = None) -> CriterionResult:
    """Return a criterion that could not be measured.

    Args:
        name: the criterion, e.g. "p95_seconds".
        area: its report section, e.g. "speed".
        limit: the criterion in words.
        why: what was missing, e.g. "no judged samples for candidate_low".
        case_set: the case set, or None for probe-run checks.

    Returns:
        A ``CriterionResult`` with status "not_measured" and ``why`` as its value.
    """
    return CriterionResult(name=name, area=area, case_set=case_set, value=f"not measured: {why}",
                           limit=limit, status="not_measured")


def integration_criteria(probe_record: dict | None, thinking_level: str, config: AdmissionConfig) -> list[CriterionResult]:
    """Apply the integration criteria to one level's probe record.

    Args:
        probe_record: the JSON record ``eval-model-admission`` wrote for the candidate at this level, e.g.
            {"recommended_mode": "json_mode", "recommended_mode_why": "...", "real_prompt_failures":
            "0/6", "structured": [{"mode": "json_mode", "passed": "170/170", "mean_per_call":
            {"reasoning": 141.5, ...}}, ...]}; None when the record is missing.
        thinking_level: the level the record was run at.
        config: the admission config (its ``criteria.integration``).

    Returns:
        One result per integration criterion switched on.
    """
    criteria = config.criteria.integration
    results = []
    if criteria.require_recommended_mode:
        limit = "a calling mode passes every probe call"
        if probe_record is None:
            results.append(_not_measured("recommended_mode", "integration", limit, "no probe record"))
        else:
            mode = probe_record.get("recommended_mode")
            results.append(CriterionResult(
                name="recommended_mode", area="integration", limit=limit,
                value=f"{mode or 'none'}: {probe_record.get('recommended_mode_why', '')}",
                status="passed" if mode else "failed"))

    limit = f"at most {criteria.max_real_turn_failures} real game turns failed"
    real_turns_failed, real_turns_sent = 0, 0
    if probe_record is not None and probe_record.get("real_prompt_failures"):
        failed_text, sent_text = probe_record["real_prompt_failures"].split("/")
        real_turns_failed, real_turns_sent = int(failed_text), int(sent_text)
    if not real_turns_sent:
        results.append(_not_measured("real_turn_failures", "integration", limit, "no real turn in the probe record"))
    else:
        results.append(CriterionResult(
            name="real_turn_failures", area="integration", limit=limit,
            value=f"{real_turns_failed} of {real_turns_sent} failed ({probe_record.get('real_prompt_mode')})",
            status="passed" if real_turns_failed <= criteria.max_real_turn_failures else "failed"))

    if criteria.require_reasoning_when_thinking:
        limit = "the recommended mode reports reasoning tokens when thinking is asked for"
        if thinking_level in NO_THINKING_LEVELS:
            results.append(CriterionResult(name="reasons_when_thinking", area="integration", limit=limit,
                                           value=f"thinking level {thinking_level!r} asks for none", status="passed"))
        elif probe_record is None or not probe_record.get("recommended_mode"):
            results.append(_not_measured("reasons_when_thinking", "integration", limit, "no recommended mode to check"))
        else:
            mode = probe_record["recommended_mode"]
            mode_rows = [row for row in probe_record.get("structured", []) if row["mode"] == mode]
            reasoning = mode_rows[0]["mean_per_call"]["reasoning"] if mode_rows else 0
            results.append(CriterionResult(
                name="reasons_when_thinking", area="integration", limit=limit,
                value=f"{reasoning} reasoning tokens a call ({mode})",
                status="passed" if reasoning > 0 else "failed"))
    return results


def quality_criteria(case_set_name: str, reference: ArmSampleStats | None, candidate: ArmSampleStats | None,
                     paired: dict | None, config: AdmissionConfig) -> list[CriterionResult]:
    """Apply the quality criteria (bad-sample rate gap and sign test) on one case set.

    Args:
        case_set_name: e.g. "discussion".
        reference: the reference arm's totals on this set, or None when its outputs are missing.
        candidate: the candidate arm's totals, or None.
        paired: the bench's sign test of the candidate against the reference (``read_paired_sign_test``).
        config: the admission config (its ``criteria.quality``).

    Returns:
        Two results: "bad_rate_gap" and "not_significantly_worse".
    """
    criteria = config.criteria.quality
    gap_limit = f"at most {criteria.max_bad_rate_gap:+.1f} points above the reference"
    sign_limit = f"not worse on more cases with sign p < {criteria.worse_p_threshold}"
    results = []
    if reference is None or candidate is None or reference.bad_rate is None or candidate.bad_rate is None:
        results.append(_not_measured("bad_rate_gap", "quality", gap_limit, "no judged samples for both arms",
                                     case_set_name))
    else:
        bad_rate_gap = (candidate.bad_rate - reference.bad_rate) * 100
        results.append(CriterionResult(
            name="bad_rate_gap", area="quality", case_set=case_set_name, limit=gap_limit,
            value=(f"{bad_rate_gap:+.1f} points ({candidate.bad}/{candidate.valid} against "
                   f"{reference.bad}/{reference.valid})"),
            status="passed" if bad_rate_gap <= criteria.max_bad_rate_gap else "failed"))
    if paired is None:
        results.append(_not_measured("not_significantly_worse", "quality", sign_limit,
                                     "no bench summary comparing the candidate with the reference", case_set_name))
    else:
        significantly_worse = (paired["worse"] > paired["better"]
                               and paired["two_sided_sign_p"] < criteria.worse_p_threshold)
        results.append(CriterionResult(
            name="not_significantly_worse", area="quality", case_set=case_set_name, limit=sign_limit,
            value=(f"better on {paired['better']}, worse on {paired['worse']} of {paired['cases']} cases, "
                   f"p {paired['two_sided_sign_p']}"),
            status="failed" if significantly_worse else "passed"))
    return results


def vote_criteria(case_set_name: str, reference: ArmVoteScore | None, candidate: ArmVoteScore | None,
                  comparison: VoteComparison | None, config: AdmissionConfig) -> list[CriterionResult]:
    """Apply the vote criteria (votes-right gap and sign test) on one vote case set.

    Args:
        case_set_name: e.g. "votes".
        reference: the reference arm's vote score, or None when missing.
        candidate: the candidate arm's vote score, or None.
        comparison: the per-case comparison of the two (``compare_vote_arms``), or None.
        config: the admission config (its ``criteria.votes``, which must be set).

    Returns:
        Two results: "vote_gap" and "votes_not_significantly_worse".
    """
    criteria = config.criteria.votes
    gap_limit = f"at most {criteria.max_vote_gap:.1f} points below the reference"
    sign_limit = f"not right less often on more cases with sign p < {criteria.worse_p_threshold}"
    results = []
    if reference is None or candidate is None or reference.right_rate is None or candidate.right_rate is None:
        results.append(_not_measured("vote_gap", "votes", gap_limit, "no scored votes for both arms", case_set_name))
        results.append(_not_measured("votes_not_significantly_worse", "votes", sign_limit,
                                     "no scored votes for both arms", case_set_name))
        return results
    vote_gap = (reference.right_rate - candidate.right_rate) * 100
    direction = "below" if vote_gap >= 0 else "above"
    results.append(CriterionResult(
        name="vote_gap", area="votes", case_set=case_set_name, limit=gap_limit,
        value=(f"{abs(vote_gap):.1f} points {direction} ({candidate.right}/{candidate.scored} right against "
               f"{reference.right}/{reference.scored})"),
        status="passed" if vote_gap <= criteria.max_vote_gap else "failed"))
    significantly_worse = (comparison.worse > comparison.better
                           and comparison.two_sided_sign_p < criteria.worse_p_threshold)
    results.append(CriterionResult(
        name="votes_not_significantly_worse", area="votes", case_set=case_set_name, limit=sign_limit,
        value=(f"better on {comparison.better}, worse on {comparison.worse} of {comparison.cases} cases, "
               f"p {comparison.two_sided_sign_p}"),
        status="failed" if significantly_worse else "passed"))
    return results


def speed_and_cost_criteria(case_set: CaseSet, candidate: ArmSampleStats | None,
                            config: AdmissionConfig) -> list[CriterionResult]:
    """Apply the speed and cost ceilings that are set, on one case set.

    Args:
        case_set: the case set; its own ``speed`` limits, when set, replace the config's shared ones.
        candidate: the candidate arm's totals on this set, or None when its outputs are missing.
        config: the admission config (its ``criteria.speed`` and ``criteria.cost``).

    Returns:
        One result per ceiling that is not None, in the order p50, p95, output tokens, reasoning tokens.
    """
    case_set_name = case_set.name
    speed = case_set.speed if case_set.speed is not None else config.criteria.speed
    cost = config.criteria.cost
    if candidate is None:
        measured_by_name = {}
        samples_by_area = {"speed": 0, "cost": 0}
    else:
        measured_by_name = {
            "p50_seconds": candidate.seconds_p50,
            "p95_seconds": candidate.seconds_p95,
            "output_tokens_per_sample": candidate.output_tokens_per_sample,
            "reasoning_tokens_per_sample": candidate.reasoning_tokens_per_sample,
        }
        samples_by_area = {"speed": candidate.samples_timed, "cost": candidate.samples_with_usage}
    # (name, area, ceiling, unit)
    checks = [
        ("p50_seconds", "speed", speed.max_p50_seconds, "s"),
        ("p95_seconds", "speed", speed.max_p95_seconds, "s"),
        ("output_tokens_per_sample", "cost", cost.max_output_tokens_per_sample, " tokens"),
        ("reasoning_tokens_per_sample", "cost", cost.max_reasoning_tokens_per_sample, " tokens"),
    ]
    results = []
    for name, area, ceiling, unit in checks:
        if ceiling is None:
            continue
        limit = f"at most {ceiling}{unit}"
        measured = measured_by_name.get(name)
        if measured is None:
            results.append(_not_measured(name, area, limit, "no sample recorded its timing or usage", case_set_name))
            continue
        results.append(CriterionResult(name=name, area=area, case_set=case_set_name, limit=limit,
                                       value=f"{measured}{unit} over {samples_by_area[area]} samples",
                                       status="passed" if measured <= ceiling else "failed"))
    return results


def mark_advisory_criteria(criteria: list[CriterionResult], quality_rejects: bool) -> None:
    """Mark the quality and vote criteria as advisory unless the config lets quality reject.

    While the project is experimental a model is dropped only for cost, latency or integration
    (owner, 2026-10-24), so its quality results are reported but do not decide the verdict.

    Args:
        criteria: every criterion applied to one level; changed in place.
        quality_rejects: the config's ``criteria.quality_rejects``.
    """
    if quality_rejects:
        return
    for criterion in criteria:
        if criterion.area in ("quality", "votes"):
            criterion.blocking = False


def overall_verdict(criteria: list[CriterionResult]) -> str:
    """Return one level's verdict from its blocking criteria.

    Args:
        criteria: every criterion applied to the level; advisory ones (``blocking`` False) are ignored.

    Returns:
        "reject" when a blocking criterion failed; else "incomplete" when a blocking one was not measured;
        else "admit".
    """
    statuses = []
    for criterion in criteria:
        if criterion.blocking:
            statuses.append(criterion.status)
    if "failed" in statuses:
        return "reject"
    if "not_measured" in statuses:
        return "incomplete"
    return "admit"


def cheapest_passing_level(arm_verdicts: list[ArmVerdict]) -> tuple[str | None, str]:
    """Return the cheapest admitted level, preferring levels that also passed the advisory checks.

    Cheapest means the fewest output tokens per replayed sample. Output tokens already include the
    reasoning tokens (the providers bill reasoning as output and report it inside the output count), so
    they are the whole generated cost of a sample. A level that failed an advisory quality check is
    still admitted, but the cheapest level is chosen among those that failed none, when any did.

    Args:
        arm_verdicts: one verdict per level tried.

    Returns:
        (level, basis): the level, or None when no level was admitted or none recorded usage, and a
        sentence saying how it was chosen.
    """
    admitted = [arm for arm in arm_verdicts if arm.verdict == "admit"]
    if not admitted:
        return None, "no level was admitted"
    clean = []
    for arm in admitted:
        failed_any = False
        for criterion in arm.criteria:
            if criterion.status == "failed":
                failed_any = True
        if not failed_any:
            clean.append(arm)
    note = ""
    if clean:
        admitted = clean
    else:
        note = "no admitted level passed every advisory quality check; "
    priced = [arm for arm in admitted if arm.output_tokens_per_sample is not None]
    if not priced:
        return None, "no admitted level recorded token usage"
    cheapest = min(priced, key=lambda arm: arm.output_tokens_per_sample)
    others = [f"{arm.thinking_level} {arm.output_tokens_per_sample}" for arm in priced if arm is not cheapest]
    basis = (f"{note}fewest output tokens (reasoning included) per replayed sample over every case set: "
             f"{cheapest.thinking_level} {cheapest.output_tokens_per_sample}")
    if others:
        basis += f", against {', '.join(others)}"
    return cheapest.thinking_level, basis


def _pooled_output_tokens(stats_by_set: list[ArmSampleStats]) -> float | None:
    """Return the mean output tokens per sample over several case sets, each weighted by its samples.

    Args:
        stats_by_set: one arm's totals on each case set it has outputs for.

    Returns:
        The weighted mean, rounded to 0.1; None when no set recorded usage.
    """
    total_tokens = 0.0
    total_samples = 0
    for stats in stats_by_set:
        if stats.output_tokens_per_sample is None:
            continue
        total_tokens += stats.output_tokens_per_sample * stats.samples_with_usage
        total_samples += stats.samples_with_usage
    return round(total_tokens / total_samples, 1) if total_samples else None


# --- the whole gate ------------------------------------------------------------------------------------


def evaluate_admission(config: AdmissionConfig, probe_record_paths: dict[str, Path],
                       bench_dirs: dict[str, Path],
                       vote_scores: dict[str, dict[str, ArmVoteScore]]) -> AdmissionVerdict:
    """Apply every criterion to every candidate level and return the admission's verdict.

    Args:
        config: the admission config.
        probe_record_paths: thinking level → where its probe record is (it may not exist), e.g.
            {"low": Path(".../integration_low/openai__gpt-6-luna.json")}.
        bench_dirs: case set name → its bench output folder (it may not exist).
        vote_scores: vote case set name → arm label → that arm's vote score (``score_bench_votes``); a
            missing arm is reported as not measured.

    Returns:
        The verdict: one ``ArmVerdict`` per level, the cheapest admitted level, every arm's sample
        totals, and the vote scores and comparisons.
    """
    reference_arm = reference_arm_label(config)
    candidate_arms = [candidate_arm_label(level) for level in config.candidate.thinking_levels]

    sample_stats: dict[str, dict[str, ArmSampleStats]] = {}
    for case_set in config.case_sets:
        sample_stats[case_set.name] = {}
        for arm_label in [reference_arm, *candidate_arms]:
            arm_samples = read_arm_samples(bench_dirs[case_set.name], arm_label)
            if arm_samples is None:
                continue
            samples, judged = arm_samples
            sample_stats[case_set.name][arm_label] = arm_sample_stats(arm_label, samples, judged)

    vote_comparisons: dict[str, dict[str, VoteComparison]] = {}
    for set_name, scores_by_arm in vote_scores.items():
        vote_comparisons[set_name] = {}
        if reference_arm not in scores_by_arm:
            continue
        for arm_label in candidate_arms:
            if arm_label in scores_by_arm:
                vote_comparisons[set_name][arm_label] = compare_vote_arms(scores_by_arm[reference_arm],
                                                                          scores_by_arm[arm_label])

    arm_verdicts = []
    probe_records_read: dict[str, str | None] = {}
    for level in config.candidate.thinking_levels:
        arm_label = candidate_arm_label(level)
        probe_path = probe_record_paths[level]
        probe_record = json.loads(probe_path.read_text()) if probe_path.exists() else None
        probe_records_read[level] = str(probe_path) if probe_record is not None else None

        criteria = integration_criteria(probe_record, level, config)
        candidate_stats_by_set = []
        for case_set in config.case_sets:
            stats_on_set = sample_stats[case_set.name]
            candidate_stats = stats_on_set.get(arm_label)
            if candidate_stats is not None:
                candidate_stats_by_set.append(candidate_stats)
            paired = read_paired_sign_test(bench_dirs[case_set.name], reference_arm, arm_label)
            criteria += quality_criteria(case_set.name, stats_on_set.get(reference_arm), candidate_stats,
                                         paired, config)
            if case_set.kind == "vote" and config.criteria.votes is not None:
                scores_by_arm = vote_scores.get(case_set.name, {})
                criteria += vote_criteria(case_set.name, scores_by_arm.get(reference_arm),
                                          scores_by_arm.get(arm_label),
                                          vote_comparisons.get(case_set.name, {}).get(arm_label), config)
            criteria += speed_and_cost_criteria(case_set, candidate_stats, config)

        mark_advisory_criteria(criteria, config.criteria.quality_rejects)
        arm_verdicts.append(ArmVerdict(
            thinking_level=level,
            arm_label=arm_label,
            verdict=overall_verdict(criteria),
            criteria=criteria,
            output_tokens_per_sample=_pooled_output_tokens(candidate_stats_by_set),
        ))

    cheapest_level, cheapest_basis = cheapest_passing_level(arm_verdicts)
    return AdmissionVerdict(
        label=config.label,
        candidate_model=config.candidate.model,
        reference_model=config.reference.model,
        reference_arm=reference_arm,
        arms=arm_verdicts,
        cheapest_passing_level=cheapest_level,
        cheapest_basis=cheapest_basis,
        sample_stats=sample_stats,
        probe_records=probe_records_read,
        vote_scores=vote_scores,
        vote_comparisons=vote_comparisons,
    )
