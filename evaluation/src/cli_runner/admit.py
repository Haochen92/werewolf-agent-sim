"""Admit one candidate model: probe run, replays against the reference, vote scores, gate, report.

One admission config (``evaluation/src/model_admission/schemas.py`` ``AdmissionConfig``; worked example
``evaluation/config/template/admission_example.json``) names the candidate and its thinking levels, the
reference model, the case sets to replay and the pass criteria. The steps, in order:

1. one probe config per candidate level, run through ``eval-model-admission``
   (``evaluation/src/cli_runner/model_admission.py``);
2. one bench config per case set, arms = the reference first, then the candidate at each level, run
   through ``eval-hallucination-bench`` (``evaluation/src/cli_runner/regen_replay/both/hallucination_bench.py``);
3. the votes of every vote case set scored by target (``evaluation/src/model_admission/vote_scoring.py``);
4. the criteria applied (``evaluation/src/model_admission/gate.py``);
5. ``admission_report.md`` and ``admission_verdict.json`` written.

Everything lands in ``evaluation/eval_results/model_admission/<label>/``: the generated configs in
``configs/``, each level's probe record in ``integration_<level>/``, each bench run in ``bench_<set>/``.
Real games stay a manual later step (``evaluation/experiments/phase3_capture.py``).

  poetry run python -m evaluation.src.cli_runner.admit --config <admission_config.json> --plan
  poetry run python -m evaluation.src.cli_runner.admit --config <admission_config.json> --from-existing
  poetry run python -m evaluation.src.cli_runner.admit --config <admission_config.json>

``--plan`` writes the generated configs and prints the steps with their model-call counts, calling
nothing. ``--from-existing`` skips steps 1–2 and gates the outputs already on disk (free, so a run can be
re-gated with new criteria). With neither flag the paid steps run, after the same call counts are printed.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from evaluation.src.core.settings import REPO_ROOT
from evaluation.src.model_admission.gate import candidate_arm_label, evaluate_admission, reference_arm_label
from evaluation.src.model_admission.schemas import (
    AdmissionConfig,
    AdmissionVerdict,
    ArmVoteScore,
    CaseSet,
    PlannedStep,
)
from evaluation.src.model_admission.vote_scoring import load_vote_cases, read_bench_jsonl, score_bench_votes

ADMISSION_RESULTS = REPO_ROOT / "evaluation/eval_results/model_admission"
PROBE_MODULE = "evaluation.src.cli_runner.model_admission"
BENCH_MODULE = "evaluation.src.cli_runner.regen_replay.both.hallucination_bench"

# Units a sample's judge reads, by phase (judged files to 2026-10-16: a vote reply has its note and its
# reads, a discussion reply adds its message). Used only for the plan's call count.
JUDGED_UNITS_PER_SAMPLE = {"day_vote": 2, "day_discussion": 3}


# --- where things go ---------------------------------------------------------------------------------


def load_admission_config(path: Path) -> AdmissionConfig:
    """Read and validate an admission config file.

    Args:
        path: the JSON config, e.g. evaluation/config/template/admission_example.json.

    Returns:
        The validated config. Raises pydantic.ValidationError on a malformed one.
    """
    return AdmissionConfig.model_validate_json(path.read_text())


def probe_label(config: AdmissionConfig, thinking_level: str) -> str:
    """Return the probe run's label for one candidate level.

    The probe runner writes to ``evaluation/eval_results/model_admission/<label>/``, so a label with a
    slash puts every level's record inside the admission's own folder.

    Args:
        config: the admission config.
        thinking_level: e.g. "low".

    Returns:
        "<admission label>/integration_<level>", e.g. "luna_admission/integration_low".
    """
    return f"{config.label}/integration_{thinking_level}"


def probe_record_path(config: AdmissionConfig, thinking_level: str, results_root: Path) -> Path:
    """Return where the probe runner writes the candidate's record for one level.

    Args:
        config: the admission config.
        thinking_level: e.g. "low".
        results_root: the probe runner's output root (``ADMISSION_RESULTS`` for a real run).

    Returns:
        <results_root>/<label>/integration_<level>/<model with "/" as "__">.json.
    """
    record_name = config.candidate.model.replace("/", "__") + ".json"
    return results_root / probe_label(config, thinking_level) / record_name


def bench_dir(config: AdmissionConfig, case_set: CaseSet, results_root: Path) -> Path:
    """Return a case set's bench output folder.

    Args:
        config: the admission config.
        case_set: one of its case sets.
        results_root: the admission results root.

    Returns:
        <results_root>/<label>/bench_<case set name>.
    """
    return results_root / config.label / f"bench_{case_set.name}"


def _repo_relative(path: Path) -> str:
    """Return a path relative to the repo root when it is inside it, else the absolute path.

    Args:
        path: any path.

    Returns:
        The path as a string, repo-relative where possible.
    """
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


# --- the generated configs -----------------------------------------------------------------------------


def build_probe_config(config: AdmissionConfig, thinking_level: str) -> dict:
    """Return the ``eval-model-admission`` config for the candidate at one level.

    Args:
        config: the admission config.
        thinking_level: the level to probe, e.g. "medium".

    Returns:
        The probe config as a dict (keys as ``model_admission.py`` reads them).
    """
    probe = config.probe
    real_turn_dataset = probe.real_turn_dataset
    if real_turn_dataset is None:
        discussion_sets = [case_set for case_set in config.case_sets if case_set.kind == "discussion"]
        real_turn_dataset = discussion_sets[0].dataset if discussion_sets else config.case_sets[0].dataset
    probe_config = {
        "label": probe_label(config, thinking_level),
        "models": [config.candidate.model],
        "thinking_level": thinking_level,
        "samples_per_schema": probe.samples_per_schema,
        "workers": probe.workers,
        "caching": {
            "floor_sizes": probe.floor_sizes,
            "wait_s": probe.wait_s,
            "dataset": real_turn_dataset,
            "cases": probe.real_turn_cases,
        },
        "notes": f"Generated by evaluation/src/cli_runner/admit.py for admission {config.label!r}.",
    }
    if probe.modes:
        probe_config["modes"] = probe.modes
    return probe_config


def _bench_arm(arm_label: str, model: str, thinking_level: str, structured_mode: str | None,
               case_set: CaseSet) -> dict:
    """Return one bench arm.

    Args:
        arm_label: e.g. "candidate_low".
        model: catalogue id.
        thinking_level: the arm's level; in a resummarize set it is the summary's level too.
        structured_mode: the calling mode, or None for the factory's choice.
        case_set: the case set the arm replays.

    Returns:
        The arm as the bench reads it: label, model, env, memory, and ``resummarize`` when set.
    """
    env = {"GOOGLE_GENAI_THINKING_LEVEL": thinking_level}
    if structured_mode:
        env["LLM_STRUCTURED_MODE"] = structured_mode
    arm = {"label": arm_label, "model": model, "env": env, "memory": "none"}
    if case_set.kind == "resummarize":
        env["GOOGLE_GENAI_SUMMARY_THINKING_LEVEL"] = thinking_level
        arm["resummarize"] = True
    return arm


def build_bench_config(config: AdmissionConfig, case_set: CaseSet, results_root: Path) -> dict:
    """Return the ``eval-hallucination-bench`` config for one case set.

    Args:
        config: the admission config.
        case_set: the case set to replay.
        results_root: the admission results root; the bench writes into ``bench_dir``.

    Returns:
        The bench config as a dict: the reference arm first (the bench compares every arm with the
        first), then the candidate at each level.
    """
    arms = [_bench_arm(reference_arm_label(config), config.reference.model, config.reference.thinking_level,
                       config.reference.structured_mode, case_set)]
    for level in config.candidate.thinking_levels:
        arms.append(_bench_arm(candidate_arm_label(level), config.candidate.model, level,
                               config.candidate.structured_mode, case_set))
    bench_config = {
        "label": f"bench_{case_set.name}",
        "output_dir": _repo_relative(results_root / config.label),
        "dataset": case_set.dataset,
        "n": case_set.n or config.n,
        "workers": config.workers,
        "arms": arms,
        "note": (f"Generated by evaluation/src/cli_runner/admit.py for admission {config.label!r}, "
                 f"case set {case_set.name!r} ({case_set.kind})."),
    }
    if case_set.slices:
        bench_config["slices"] = case_set.slices
    for judge_key, judge_model in config.judges.model_dump().items():
        if judge_model:
            bench_config[judge_key] = judge_model
    return bench_config


def write_generated_configs(config: AdmissionConfig, results_root: Path) -> tuple[dict[str, Path], dict[str, Path]]:
    """Write every probe and bench config under ``<results_root>/<label>/configs/``.

    Args:
        config: the admission config.
        results_root: the admission results root.

    Returns:
        (probe config paths by level, bench config paths by case set name).
    """
    configs_dir = results_root / config.label / "configs"
    configs_dir.mkdir(parents=True, exist_ok=True)
    probe_paths = {}
    for level in config.candidate.thinking_levels:
        probe_path = configs_dir / f"integration_{level}.json"
        probe_path.write_text(json.dumps(build_probe_config(config, level), indent=2) + "\n")
        probe_paths[level] = probe_path
    bench_paths = {}
    for case_set in config.case_sets:
        bench_path = configs_dir / f"bench_{case_set.name}.json"
        bench_path.write_text(json.dumps(build_bench_config(config, case_set, results_root), indent=2) + "\n")
        bench_paths[case_set.name] = bench_path
    return probe_paths, bench_paths


# --- call counts ---------------------------------------------------------------------------------------


def probe_call_count(config: AdmissionConfig, thinking_level: str) -> tuple[int, str]:
    """Return the most model calls one probe run makes, and how the count is reached.

    Args:
        config: the admission config.
        thinking_level: the level probed (the count does not depend on it; it labels the note).

    Returns:
        (calls, note): structured-output calls (modes × seat schemas × samples), cache-floor sends (up to
        three per size) and real-turn calls (three per case).
    """
    from evaluation.src.cli_runner.model_admission import _cases as real_turn_cases_for
    from evaluation.src.model_admission import probes
    from evaluation.src.model_admission.seat_schemas import SEAT_SCHEMAS

    probe_config = build_probe_config(config, thinking_level)
    allowed_modes = probes.modes_for(config.candidate.model)
    modes = [mode for mode in (config.probe.modes or allowed_modes) if mode in allowed_modes]
    structured_calls = len(modes) * len(SEAT_SCHEMAS) * config.probe.samples_per_schema
    floor_sends = 3 * len(config.probe.floor_sizes)
    real_cases = real_turn_cases_for(REPO_ROOT / probe_config["caching"]["dataset"], config.probe.real_turn_cases)
    real_calls = 3 * len(real_cases)
    note = (f"{len(modes)} modes × {len(SEAT_SCHEMAS)} seat schemas × {config.probe.samples_per_schema} = "
            f"{structured_calls} structured; ≤{floor_sends} cache-floor sends; "
            f"{len(real_cases)} real cases × 3 = {real_calls} real turns")
    return structured_calls + floor_sends + real_calls, note


def _resummary_calls(cases: list[dict]) -> int:
    """Return how many day summaries one resummarizing arm rewrites over a case set.

    The bench rewrites, once per game, every earlier day that had discussion before the game's latest
    case; this counts those days the same way.

    Args:
        cases: the case set's frozen cases.

    Returns:
        The number of summary calls one arm makes.
    """
    latest_case_by_game: dict[str, dict] = {}
    for case in cases:
        game_key = f"{case['game_id']}|{case.get('game_arm', '')}"
        if game_key not in latest_case_by_game or case["day"] > latest_case_by_game[game_key]["day"]:
            latest_case_by_game[game_key] = case
    summary_calls = 0
    for case in latest_case_by_game.values():
        discussion_days = set()
        for message in case["state"]["day_channel"]:
            if message["day"] < case["day"] and message["player"] != "game_master":
                discussion_days.add(message["day"])
        summary_calls += len(discussion_days)
    return summary_calls


def bench_call_count(config: AdmissionConfig, case_set: CaseSet) -> tuple[int, str]:
    """Return the most model calls one bench run makes, and how the count is reached.

    Generation is cases × n per arm (fewer when earlier samples are on disk: the bench tops up). Judging
    is counted as one golden-judge call per unit of each sample on a case with an expectation, and up to
    two census reads per unit on a case without one.

    Args:
        config: the admission config.
        case_set: the case set.

    Returns:
        (calls, note).
    """
    cases = []
    for case in read_bench_jsonl(REPO_ROOT / case_set.dataset):
        if not case_set.slices or case.get("slice") in case_set.slices:
            cases.append(case)
    samples_per_case = case_set.n or config.n
    arm_count = 1 + len(config.candidate.thinking_levels)
    generation_calls = len(cases) * samples_per_case * arm_count
    judge_calls = 0
    for case in cases:
        units = JUDGED_UNITS_PER_SAMPLE.get(case["phase"], 3)
        calls_per_unit = 1 if case.get("golden") else 2
        judge_calls += units * calls_per_unit * samples_per_case * arm_count
    note = (f"{len(cases)} cases × {samples_per_case} samples × {arm_count} arms = {generation_calls} "
            f"generations; ≤{judge_calls} judge calls")
    total = generation_calls + judge_calls
    if case_set.kind == "resummarize":
        summary_calls = _resummary_calls(cases) * arm_count
        note += f"; {summary_calls} day summaries rewritten"
        total += summary_calls
    return total, note


def plan_steps(config: AdmissionConfig, probe_paths: dict[str, Path],
               bench_paths: dict[str, Path]) -> list[PlannedStep]:
    """Return the admission's steps, in order, with their model-call counts.

    Args:
        config: the admission config.
        probe_paths: the generated probe config per level.
        bench_paths: the generated bench config per case set.

    Returns:
        One ``PlannedStep`` per probe run, per bench run, and for scoring, gating and reporting.
    """
    steps = []
    for level, probe_path in probe_paths.items():
        calls, note = probe_call_count(config, level)
        steps.append(PlannedStep(title=f"probe run: {config.candidate.model} at {level}",
                                 config_path=_repo_relative(probe_path), model_calls=calls, calls_note=note))
    for case_set in config.case_sets:
        calls, note = bench_call_count(config, case_set)
        arm_count = 1 + len(config.candidate.thinking_levels)
        steps.append(PlannedStep(title=f"bench: {case_set.name} ({case_set.kind}, {arm_count} arms)",
                                 config_path=_repo_relative(bench_paths[case_set.name]),
                                 model_calls=calls, calls_note=note))
    vote_set_names = [case_set.name for case_set in config.case_sets if case_set.kind == "vote"]
    steps.append(PlannedStep(title=f"score votes: {', '.join(vote_set_names) or 'no vote case set'}",
                             calls_note="by target, no model"))
    steps.append(PlannedStep(title="apply the criteria", calls_note="no model"))
    steps.append(PlannedStep(title="write admission_report.md and admission_verdict.json", calls_note="no model"))
    return steps


def print_plan(steps: list[PlannedStep]) -> None:
    """Print the steps and the cost note (model calls per step and in total).

    Args:
        steps: the planned steps (``plan_steps``).

    Returns:
        None; prints to stdout.
    """
    print("Admission steps (model calls are upper bounds; a rerun tops up what is on disk):")
    for number, step in enumerate(steps, start=1):
        print(f"  {number}. {step.title}")
        if step.config_path:
            print(f"       config: {step.config_path}")
        print(f"       model calls: {step.model_calls}  ({step.calls_note})")
    print(f"  total model calls: at most {sum(step.model_calls for step in steps)}")


# --- running -------------------------------------------------------------------------------------------


def run_probe_config(config_path: Path) -> None:
    """Run ``eval-model-admission`` on one generated probe config (paid: it calls the model).

    Args:
        config_path: the probe config.

    Returns:
        None. Raises subprocess.CalledProcessError when the runner exits non-zero.
    """
    subprocess.run([sys.executable, "-m", PROBE_MODULE, "--config", str(config_path)], cwd=REPO_ROOT, check=True)


def run_bench_config(config_path: Path) -> None:
    """Run ``eval-hallucination-bench`` on one generated bench config (paid: generation and judging).

    Args:
        config_path: the bench config.

    Returns:
        None. Raises subprocess.CalledProcessError when the bench exits non-zero.
    """
    subprocess.run([sys.executable, "-m", BENCH_MODULE, "--config", str(config_path)], cwd=REPO_ROOT, check=True)


def score_votes(config: AdmissionConfig, results_root: Path) -> dict[str, dict[str, ArmVoteScore]]:
    """Score the votes of every vote case set's arms that are on disk.

    Args:
        config: the admission config.
        results_root: the admission results root.

    Returns:
        Vote case set name → arm label → its score (arms without generations are left out).
    """
    arm_labels = [reference_arm_label(config)]
    for level in config.candidate.thinking_levels:
        arm_labels.append(candidate_arm_label(level))
    vote_scores = {}
    for case_set in config.case_sets:
        if case_set.kind != "vote":
            continue
        cases = load_vote_cases(case_set.dataset, case_set.slices)
        vote_scores[case_set.name] = score_bench_votes(bench_dir(config, case_set, results_root), arm_labels,
                                                       cases, case_set.right_target_overrides)
    return vote_scores


# --- the report ----------------------------------------------------------------------------------------


def _percent(numerator: int | None, denominator: int) -> str:
    """Return "n/d (p%)", or "—" when there is nothing to divide.

    Args:
        numerator: the count, or None when unknown.
        denominator: the total.

    Returns:
        e.g. "5/70 (7%)".
    """
    if numerator is None or not denominator:
        return "—"
    return f"{numerator}/{denominator} ({numerator / denominator:.0%})"


def _shown(value: object) -> str:
    """Return a table cell: the value, or "not measured" for None.

    Args:
        value: any value.

    Returns:
        The cell text.
    """
    return "not measured" if value is None else str(value)


def _criteria_table(verdict: AdmissionVerdict, areas: tuple[str, ...]) -> list[str]:
    """Return markdown table lines for every level's criteria in the given areas.

    Args:
        verdict: the admission verdict.
        areas: the criterion areas to include, e.g. ("quality", "votes").

    Returns:
        The table's lines, or a single line saying no criterion applies.
    """
    lines = ["| Level | Criterion | Case set | Value | Limit | Status |", "|---|---|---|---|---|---|"]
    for arm in verdict.arms:
        for criterion in arm.criteria:
            if criterion.area not in areas:
                continue
            lines.append(f"| {arm.thinking_level} | {criterion.name} | {criterion.case_set or '—'} | "
                         f"{criterion.value} | {criterion.limit} | {criterion.status} |")
    if len(lines) == 2:
        return ["No criterion in this area is set."]
    return lines


def render_report(config: AdmissionConfig, verdict: AdmissionVerdict) -> str:
    """Return the admission report as markdown, sectioned by the five admission questions.

    Args:
        config: the admission config.
        verdict: the gate's verdict (``evaluate_admission``).

    Returns:
        The report text.
    """
    lines = [f"# Admission: {config.candidate.model} against {config.reference.model}", ""]
    lines.append(f"Label `{config.label}`; gated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}. "
                 f"Reference arm `{verdict.reference_arm}` ({config.reference.model} at "
                 f"{config.reference.thinking_level}).")
    lines.append("")
    lines.append("| Level | Verdict | Output tokens a sample |")
    lines.append("|---|---|---|")
    for arm in verdict.arms:
        lines.append(f"| {arm.thinking_level} | **{arm.verdict}** | {_shown(arm.output_tokens_per_sample)} |")
    lines.append("")
    lines.append(f"Cheapest passing level: **{verdict.cheapest_passing_level or 'none'}** ({verdict.cheapest_basis}).")
    if config.note:
        lines += ["", f"Config note: {config.note}"]

    lines += ["", "## 1. Quality", ""]
    for case_set in config.case_sets:
        lines.append(f"**{case_set.name}** ({case_set.kind}, `{case_set.dataset}`"
                     f"{', slices ' + ', '.join(case_set.slices) if case_set.slices else ''}).")
        lines.append("")
        lines.append("| Arm | Bad samples | Invalid |")
        lines.append("|---|---|---|")
        stats_on_set = verdict.sample_stats.get(case_set.name, {})
        if not stats_on_set:
            lines.append("| — | no outputs on disk | — |")
        for arm_label, stats in stats_on_set.items():
            bad_cell = _percent(stats.bad, stats.valid) if stats.judged else "not judged"
            lines.append(f"| {arm_label} | {bad_cell} | {stats.invalid} |")
        lines.append("")
        vote_scores = verdict.vote_scores.get(case_set.name)
        if case_set.kind == "vote" and vote_scores:
            lines.append("Votes, scored by target against the true roles (or the case's own right targets):")
            lines.append("")
            lines.append("| Arm | Right | Abstains | Unscorable | Better / worse than reference | Sign p |")
            lines.append("|---|---|---|---|---|---|")
            comparisons = verdict.vote_comparisons.get(case_set.name, {})
            for arm_label, score in vote_scores.items():
                comparison = comparisons.get(arm_label)
                versus = f"{comparison.better} / {comparison.worse}" if comparison else "—"
                sign_p = comparison.two_sided_sign_p if comparison else "—"
                lines.append(f"| {arm_label} | {_percent(score.right, score.scored)} | {score.abstains} | "
                             f"{len(score.unscorable)} | {versus} | {sign_p} |")
            lines.append("")
            lines.append("| Case | Game, day | Voter | Right targets | " + " | ".join(vote_scores) + " |")
            lines.append("|---|---|---|---|" + "---|" * len(vote_scores))
            first_score = next(iter(vote_scores.values()))
            for row_index, case_row in enumerate(first_score.per_case):
                cells = []
                for score in vote_scores.values():
                    arm_row = score.per_case[row_index]
                    cells.append(f"{arm_row.right}/{arm_row.scored}")
                lines.append(f"| {case_row.case_id} | {case_row.game_id} d{case_row.day} | {case_row.voter} "
                             f"({case_row.voter_role}) | {', '.join(case_row.right_targets)} ({case_row.right_source}) "
                             f"| " + " | ".join(cells) + " |")
            for score in vote_scores.values():
                for unscorable in score.unscorable:
                    lines.append(f"- unscorable in {score.arm_label}: case {unscorable.case_id} sample "
                                 f"{unscorable.sample}: {unscorable.unscorable_reason}")
            lines.append("")
    lines += _criteria_table(verdict, ("quality", "votes"))

    lines += ["", "## 2. Integration", ""]
    for level in config.candidate.thinking_levels:
        record_path = verdict.probe_records.get(level)
        if record_path:
            lines.append(f"- {level}: probe record `{_repo_relative(Path(record_path))}`.")
        else:
            lines.append(f"- {level}: probe record missing.")
    lines.append(f"- The bench arms use calling mode {config.candidate.structured_mode or 'the factory default'} "
                 f"(candidate) and {config.reference.structured_mode or 'the factory default'} (reference).")
    lines.append("")
    lines += _criteria_table(verdict, ("integration",))

    lines += ["", "## 3. Cost and speed", ""]
    lines.append("Per replayed sample, from each sample's recorded usage and seconds (generation only; "
                 "judging is not included). Percentiles are computed, never estimated.")
    lines.append("")
    lines.append("| Case set | Arm | Timed samples | p50 s | p95 s | Output tokens | Reasoning tokens |")
    lines.append("|---|---|---|---|---|---|---|")
    for set_name, stats_on_set in verdict.sample_stats.items():
        for arm_label, stats in stats_on_set.items():
            lines.append(f"| {set_name} | {arm_label} | {stats.samples_timed} | {_shown(stats.seconds_p50)} | "
                         f"{_shown(stats.seconds_p95)} | {_shown(stats.output_tokens_per_sample)} | "
                         f"{_shown(stats.reasoning_tokens_per_sample)} |")
    lines.append("")
    lines += _criteria_table(verdict, ("speed", "cost"))

    lines += ["", "## 4. Reliability", "",
              "Not tested by this run: stalls under load, the rescue path and model drift are not exercised "
              "by replays. Real games are a manual later step: `evaluation/experiments/phase3_capture.py`."]

    lines += ["", "## 5. Rollout and records", "",
              "The catalogue row is changed by hand after review (`scripts/model_catalog.py`); this run "
              "changes nothing in the catalogue.", "",
              "- Verdict: `admission_verdict.json` beside this report.",
              f"- Generated configs: `{config.label}/configs/`."]
    return "\n".join(lines) + "\n"


def write_outputs(config: AdmissionConfig, verdict: AdmissionVerdict, results_root: Path) -> tuple[Path, Path]:
    """Write the report and the verdict JSON into the admission's folder.

    Args:
        config: the admission config.
        verdict: the gate's verdict.
        results_root: the admission results root.

    Returns:
        (report path, verdict path).
    """
    out_dir = results_root / config.label
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / "admission_report.md"
    verdict_path = out_dir / "admission_verdict.json"
    report_path.write_text(render_report(config, verdict))
    verdict_record = {"config": config.model_dump(), **verdict.model_dump()}
    verdict_path.write_text(json.dumps(verdict_record, indent=1) + "\n")
    return report_path, verdict_path


def run_admission(config: AdmissionConfig, results_root: Path = ADMISSION_RESULTS,
                  mode: str = "run") -> AdmissionVerdict | None:
    """Plan, run (or skip running) and gate one admission.

    Args:
        config: the admission config.
        results_root: where the probe runner writes its records. A real run must use
            ``ADMISSION_RESULTS``, the probe runner's fixed output root; tests point it elsewhere.
        mode: "plan" (write configs, print steps, call nothing), "from_existing" (gate what is on disk)
            or "run" (run the paid steps first).

    Returns:
        The verdict, or None in "plan" mode. Raises ValueError on an unknown mode, or on "run" with a
        results root the probe runner does not write to.
    """
    if mode not in ("plan", "from_existing", "run"):
        raise ValueError(f"unknown mode {mode!r}")
    if mode == "run" and results_root != ADMISSION_RESULTS:
        raise ValueError(f"a real run must use {ADMISSION_RESULTS}: the probe runner writes only there")
    probe_paths, bench_paths = write_generated_configs(config, results_root)
    print_plan(plan_steps(config, probe_paths, bench_paths))
    if mode == "plan":
        print("plan only: configs written, nothing run")
        return None

    if mode == "run":
        for level, probe_path in probe_paths.items():
            print(f"\n== probe run, {level}", flush=True)
            try:
                run_probe_config(probe_path)
            except subprocess.CalledProcessError as error:  # gate what did run; the record will be missing
                print(f"probe run at {level} failed: {error}")
        for set_name, bench_path in bench_paths.items():
            print(f"\n== bench, {set_name}", flush=True)
            try:
                run_bench_config(bench_path)
            except subprocess.CalledProcessError as error:
                print(f"bench {set_name} failed: {error}")

    vote_scores = score_votes(config, results_root)
    probe_record_paths = {}
    for level in config.candidate.thinking_levels:
        probe_record_paths[level] = probe_record_path(config, level, results_root)
    bench_dirs = {}
    for case_set in config.case_sets:
        bench_dirs[case_set.name] = bench_dir(config, case_set, results_root)
    verdict = evaluate_admission(config, probe_record_paths, bench_dirs, vote_scores)
    report_path, verdict_path = write_outputs(config, verdict, results_root)
    print("")
    for arm in verdict.arms:
        print(f"{arm.thinking_level}: {arm.verdict}")
    print(f"cheapest passing level: {verdict.cheapest_passing_level or 'none'} ({verdict.cheapest_basis})")
    print(f"report: {_repo_relative(report_path)}\nverdict: {_repo_relative(verdict_path)}")
    return verdict


def main(argv: list[str] | None = None) -> None:
    """Parse the command line and run one admission.

    Args:
        argv: the arguments (None reads sys.argv), e.g. ["--config", "admission.json", "--plan"].

    Returns:
        None.
    """
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--config", required=True, help="the admission config (JSON)")
    run_choice = parser.add_mutually_exclusive_group()
    run_choice.add_argument("--plan", action="store_true", help="write the configs and print the steps; run nothing")
    run_choice.add_argument("--from-existing", action="store_true",
                            help="gate the outputs already on disk; run nothing")
    args = parser.parse_args(argv)
    config = load_admission_config(Path(args.config))
    if args.plan:
        mode = "plan"
    elif args.from_existing:
        mode = "from_existing"
    else:
        from evaluation.src.core.settings import load_project_env

        load_project_env()
        mode = "run"
    run_admission(config, ADMISSION_RESULTS, mode)


if __name__ == "__main__":
    main()
