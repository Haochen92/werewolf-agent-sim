"""The admission pipeline's offline parts: the vote scorer (evaluation/src/model_admission/vote_scoring.py),
the gate (gate.py) and the one-command runner's --plan and --from-existing modes
(evaluation/src/cli_runner/admit.py). Synthetic files only, except one test that re-scores the Haiku effort
replay's real outputs when they are on disk."""
import json
from pathlib import Path

import pytest

from Agents.schemas.roles import TOWN, WOLVES, lineup, side_of
from evaluation.src.cli_runner import admit
from evaluation.src.core.settings import REPO_ROOT
from evaluation.src.model_admission import gate, vote_scoring
from evaluation.src.model_admission.schemas import AdmissionConfig, SpeedCriteria

PLAYERS = [f"player_{i}" for i in range(1, 11)]
ROLES = dict(zip(PLAYERS, lineup("serial_killer", "speculator")))
WOLF_SEAT = next(player for player in PLAYERS if side_of(ROLES[player]) == WOLVES)
LONE_KILLER_SEAT = next(player for player in PLAYERS if ROLES[player] == "serial_killer")
TOWN_SEATS = [player for player in PLAYERS if side_of(ROLES[player]) == TOWN]


def _write_jsonl(path: Path, rows: list[dict]) -> Path:
    """Write rows as JSON lines, creating the folder; returns the path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row) + "\n" for row in rows))
    return path


def _vote_case(case_id: str, voter: str, **extra) -> dict:
    """A day-3 vote case in the bench's shape, on the synthetic ten-seat deal."""
    return {"case_id": case_id, "phase": "day_vote", "day": 3, "speaker": voter, "role": ROLES[voter],
            "game_id": "synthetic", "slice": "vote", "kind": "control", "golden": "Meets: anything.",
            "state": {"roles": ROLES, "day_channel": []}, **extra}


def _discussion_case(case_id: str) -> dict:
    """A day-2 discussion case in the bench's shape."""
    return {"case_id": case_id, "phase": "day_discussion", "day": 2, "speaker": TOWN_SEATS[0],
            "role": ROLES[TOWN_SEATS[0]], "game_id": "synthetic", "slice": "pinned", "kind": "positive",
            "golden": "Meets: anything.", "state": {"roles": ROLES, "day_channel": []}}


def _vote_sample(case_id: str, index: int, vote: str | None, valid: bool = True) -> dict:
    """One generated vote sample."""
    return {"case_id": case_id, "sample": index, "valid": valid, "vote": vote, "units": []}


# --- the vote scorer ----------------------------------------------------------------------------------


def test_votes_are_scored_by_the_true_roles_with_abstains_unscorables_and_overrides(tmp_path):
    town_voter = TOWN_SEATS[0]
    cases_path = _write_jsonl(tmp_path / "votes.jsonl", [
        _vote_case("by_roles", town_voter),
        _vote_case("by_record", town_voter, right_vote_targets=["abstain"]),
        _vote_case("by_override", town_voter, right_vote_targets=[WOLF_SEAT]),
        _discussion_case("not_a_vote"),
    ])
    cases = vote_scoring.load_vote_cases(cases_path)
    assert list(cases) == ["by_roles", "by_record", "by_override"]  # discussion cases are dropped

    samples = [
        _vote_sample("by_roles", 0, WOLF_SEAT),          # right: a wolf
        _vote_sample("by_roles", 1, LONE_KILLER_SEAT),   # right: the lone killer is evil too
        _vote_sample("by_roles", 2, TOWN_SEATS[1]),      # wrong
        _vote_sample("by_roles", 3, "abstain"),          # scored, wrong
        _vote_sample("by_roles", 4, None, valid=False),  # unscorable: generation failed
        _vote_sample("by_roles", 5, None),               # unscorable: no vote
        _vote_sample("by_roles", 6, "player_42"),        # unscorable: not a player
        _vote_sample("by_record", 0, "abstain"),         # right: the case lists abstain
        _vote_sample("by_record", 1, WOLF_SEAT),         # wrong: the case's list replaces the roles
        _vote_sample("by_override", 0, WOLF_SEAT),       # wrong: the config override wins over the record
        _vote_sample("by_override", 1, TOWN_SEATS[2]),   # right by the override
        _vote_sample("elsewhere", 0, WOLF_SEAT),         # a case outside the set is ignored
    ]
    score = vote_scoring.score_vote_arm("candidate_low", samples, cases, {"by_override": [TOWN_SEATS[2]]})

    assert (score.right, score.scored, score.abstains) == (4, 8, 2)
    reasons = sorted(sample.unscorable_reason for sample in score.unscorable)
    assert reasons == ["invalid sample (generation failed)", "target 'player_42' is not a player in this game",
                       "the reply carries no vote target"]
    rows = {row.case_id: row for row in score.per_case}
    assert rows["by_roles"].right_source == "roles"
    assert set(rows["by_roles"].right_targets) >= {WOLF_SEAT, LONE_KILLER_SEAT}
    assert not set(rows["by_roles"].right_targets) & set(TOWN_SEATS)
    assert (rows["by_roles"].right, rows["by_roles"].scored, rows["by_roles"].unscorable) == (2, 4, 3)
    assert rows["by_record"].right_source == "case_record" and rows["by_record"].right == 1
    assert rows["by_override"].right_source == "override" and rows["by_override"].right == 1


def test_two_arms_are_compared_case_by_case_with_the_sign_test():
    cases = {f"c{i}": _vote_case(f"c{i}", TOWN_SEATS[0]) for i in range(4)}
    reference_samples = []
    candidate_samples = []
    for i in range(3):  # the candidate is right where the reference was wrong on three cases
        reference_samples.append(_vote_sample(f"c{i}", 0, TOWN_SEATS[1]))
        candidate_samples.append(_vote_sample(f"c{i}", 0, WOLF_SEAT))
    reference_samples.append(_vote_sample("c3", 0, WOLF_SEAT))  # a tie drops out
    candidate_samples.append(_vote_sample("c3", 0, WOLF_SEAT))
    reference = vote_scoring.score_vote_arm("reference_low", reference_samples, cases, {})
    candidate = vote_scoring.score_vote_arm("candidate_low", candidate_samples, cases, {})
    comparison = vote_scoring.compare_vote_arms(reference, candidate)
    assert (comparison.cases, comparison.better, comparison.worse) == (4, 3, 0)
    assert comparison.two_sided_sign_p == 0.25  # 2 × (1/2)^3


HAIKU_VOTES = REPO_ROOT / "evaluation/eval_results/hallucination_bench/haiku_effort_votes"
HAIKU_VOTE_CASES = REPO_ROOT / "evidence/gameplay/deduction/data/haiku_effort_replay/vote_cases.jsonl"


@pytest.mark.skipif(not (HAIKU_VOTES / "generations_haiku_low.jsonl").exists() or not HAIKU_VOTE_CASES.exists(),
                    reason="the Haiku effort replay's outputs (gitignored eval_results) are not on this machine")
def test_the_haiku_effort_replay_reproduces_65_and_98_of_160():
    # The 16 cases "as played" (reasoning_failures/experiment_log.md §2): the closing-line rerun is left out.
    cases = vote_scoring.load_vote_cases(HAIKU_VOTE_CASES, ["vote_compare", "vote"])
    assert len(cases) == 16
    by_roles = vote_scoring.score_bench_votes(HAIKU_VOTES, ["haiku_low", "haiku_medium"], cases, {})
    # By the true roles one low sample more is right: on 403f4dbc day 4 the healer voted player_3, the
    # necromancer (evil and alive), where the one-off script counted only player_1, the chanteuse.
    assert (by_roles["haiku_low"].right, by_roles["haiku_low"].scored) == (66, 160)
    assert (by_roles["haiku_medium"].right, by_roles["haiku_medium"].scored) == (98, 160)

    old_answer = {"8cef41762cf67c2f": ["player_1"]}
    scores = vote_scoring.score_bench_votes(HAIKU_VOTES, ["haiku_low", "haiku_medium"], cases, old_answer)
    assert (scores["haiku_low"].right, scores["haiku_low"].scored) == (65, 160)
    assert (scores["haiku_medium"].right, scores["haiku_medium"].scored) == (98, 160)
    comparison = vote_scoring.compare_vote_arms(scores["haiku_low"], scores["haiku_medium"])
    assert (comparison.better, comparison.worse) == (12, 1)
    assert comparison.two_sided_sign_p == pytest.approx(0.003, abs=0.001)


# --- a synthetic admission on disk ----------------------------------------------------------------------


def _config(datasets: dict[str, Path], levels: list[str], **criteria_overrides) -> AdmissionConfig:
    """An admission config over the synthetic case sets."""
    criteria = {
        "quality": {"max_bad_rate_gap": 6.0, "worse_p_threshold": 0.05},
        "votes": {"max_vote_gap": 10.0},
        "speed": {"max_p50_seconds": 12.0, "max_p95_seconds": 30.0},
        **criteria_overrides,
    }
    return AdmissionConfig.model_validate({
        "label": "synthetic_admission",
        "candidate": {"model": "openai/gpt-6-luna", "thinking_levels": levels, "structured_mode": "json_mode"},
        "reference": {"model": "anthropic/claude-haiku-5-5", "thinking_level": "low"},
        "case_sets": [
            {"name": "discussion", "kind": "discussion", "dataset": str(datasets["discussion"]), "n": 4},
            {"name": "votes", "kind": "vote", "dataset": str(datasets["votes"]), "n": 4},
        ],
        "probe": {"floor_sizes": [256, 512]},
        "criteria": criteria,
    })


def _datasets(tmp_path: Path) -> dict[str, Path]:
    """Write a two-case discussion set and a two-case vote set."""
    return {
        "discussion": _write_jsonl(tmp_path / "cases" / "discussion.jsonl",
                                   [_discussion_case("d0"), _discussion_case("d1")]),
        "votes": _write_jsonl(tmp_path / "cases" / "votes.jsonl",
                              [_vote_case("v0", TOWN_SEATS[0]), _vote_case("v1", TOWN_SEATS[1])]),
    }


def _probe_record(reasoning: float, recommended: str | None = "json_mode", real_failures: str = "0/6") -> dict:
    """A probe record in eval-model-admission's shape."""
    return {"recommended_mode": recommended, "recommended_mode_why": "passed every call",
            "real_prompt_mode": recommended or "json_mode", "real_prompt_failures": real_failures,
            "structured": [{"mode": "json_mode", "passed": "51/51", "all_passed": True,
                            "mean_per_call": {"reasoning": reasoning, "seconds": 4.0}}]}


def _judged_samples(case_ids: list[str], bad_per_case: int, samples_per_case: int, seconds: float,
                    output_tokens: int, votes: list[str] | None = None) -> list[dict]:
    """Judged bench samples: the first ``bad_per_case`` of each case are bad; votes cycle when given."""
    rows = []
    for case_id in case_ids:
        for index in range(samples_per_case):
            row = {"case_id": case_id, "sample": index, "valid": True, "units": [], "bad": index < bad_per_case,
                   "usage": {"output": output_tokens, "reasoning": output_tokens // 2, "seconds": seconds}}
            if votes is not None:
                row["vote"] = votes[index % len(votes)]
            rows.append(row)
    return rows


def _write_bench(bench: Path, arms: dict[str, list[dict]], paired: dict[str, dict]) -> None:
    """Write judged files and a summary.json whose first arm is the first in ``arms``."""
    for arm_label, samples in arms.items():
        _write_jsonl(bench / f"judged_{arm_label}.jsonl", samples)
    summary = {"arms": {arm_label: {} for arm_label in arms}, "paired_vs_first": paired}
    (bench / "summary.json").write_text(json.dumps(summary))


def _write_synthetic_outputs(results_root: Path, config: AdmissionConfig) -> None:
    """Outputs for levels low (passes, cheap), medium (passes, dear), high (too many bad samples);
    the "minimal" level, when configured, has no probe record."""
    for level, reasoning in (("low", 300.0), ("medium", 900.0), ("high", 1500.0)):
        record_path = admit.probe_record_path(config, level, results_root)
        record_path.parent.mkdir(parents=True)
        record_path.write_text(json.dumps(_probe_record(reasoning)))
    even = {"cases": 2, "better": 0, "worse": 0, "two_sided_sign_p": 1.0}
    worse = {"cases": 2, "better": 0, "worse": 2, "two_sided_sign_p": 0.5}

    discussion_ids = ["d0", "d1"]
    _write_bench(results_root / config.label / "bench_discussion", {
        "reference_low": _judged_samples(discussion_ids, 1, 4, 9.0, 1200),
        "candidate_low": _judged_samples(discussion_ids, 1, 4, 8.0, 800),
        "candidate_medium": _judged_samples(discussion_ids, 1, 4, 11.0, 1700),
        "candidate_high": _judged_samples(discussion_ids, 3, 4, 11.0, 2500),
    }, {"candidate_low": even, "candidate_medium": even, "candidate_high": worse})

    vote_ids = ["v0", "v1"]
    right_votes = [WOLF_SEAT, WOLF_SEAT, WOLF_SEAT, TOWN_SEATS[3]]  # 3 of 4 right
    vote_bench = results_root / config.label / "bench_votes"
    vote_arms = {
        "reference_low": _judged_samples(vote_ids, 0, 4, 5.0, 900, right_votes),
        "candidate_low": _judged_samples(vote_ids, 0, 4, 5.0, 600, right_votes),
        "candidate_medium": _judged_samples(vote_ids, 0, 4, 9.0, 1500, right_votes),
        "candidate_high": _judged_samples(vote_ids, 0, 4, 9.0, 2000, right_votes),
    }
    _write_bench(vote_bench, vote_arms, {"candidate_low": even, "candidate_medium": even, "candidate_high": even})
    for arm_label, samples in vote_arms.items():  # the vote scorer reads the generations
        _write_jsonl(vote_bench / f"generations_{arm_label}.jsonl", samples)


def _gate(config: AdmissionConfig, results_root: Path):
    """Run the gate the way the runner does, on outputs under ``results_root``."""
    probe_paths = {level: admit.probe_record_path(config, level, results_root)
                   for level in config.candidate.thinking_levels}
    bench_dirs = {case_set.name: admit.bench_dir(config, case_set, results_root) for case_set in config.case_sets}
    return gate.evaluate_admission(config, probe_paths, bench_dirs, admit.score_votes(config, results_root))


def test_the_gate_admits_rejects_and_marks_incomplete_and_names_the_cheapest_level(tmp_path):
    config = _config(_datasets(tmp_path), ["low", "medium", "high", "minimal"])
    config.criteria.quality_rejects = True  # the commercial setting: a quality failure rejects
    results_root = tmp_path / "results"
    _write_synthetic_outputs(results_root, config)

    verdict = _gate(config, results_root)
    by_level = {arm.thinking_level: arm for arm in verdict.arms}
    assert by_level["low"].verdict == "admit"
    assert by_level["medium"].verdict == "admit"
    assert by_level["high"].verdict == "reject"
    failed = {criterion.name for criterion in by_level["high"].criteria if criterion.status == "failed"}
    assert failed == {"bad_rate_gap"}  # +50 points; worse on 2 of 2 is p 0.5, not significant
    assert by_level["minimal"].verdict == "incomplete"  # no probe record, no bench arm
    assert verdict.cheapest_passing_level == "low"
    assert "reasoning included" in verdict.cheapest_basis

    low_votes = verdict.vote_scores["votes"]["candidate_low"]
    assert (low_votes.right, low_votes.scored) == (6, 8)
    discussion_low = verdict.sample_stats["discussion"]["candidate_low"]
    assert (discussion_low.seconds_p50, discussion_low.seconds_p95) == (8.0, 8.0)


def test_quality_failures_are_advisory_by_default_and_the_cheapest_level_avoids_them(tmp_path):
    config = _config(_datasets(tmp_path), ["low", "medium", "high"])
    assert config.criteria.quality_rejects is False  # experimental: drop only for cost, latency, integration
    results_root = tmp_path / "results"
    _write_synthetic_outputs(results_root, config)

    verdict = _gate(config, results_root)
    by_level = {arm.thinking_level: arm for arm in verdict.arms}
    assert by_level["high"].verdict == "admit"  # its +50-point bad-rate gap is reported, not a rejection
    advisory_failures = []
    for criterion in by_level["high"].criteria:
        if criterion.status == "failed":
            advisory_failures.append((criterion.name, criterion.blocking))
    assert advisory_failures == [("bad_rate_gap", False)]
    assert verdict.cheapest_passing_level == "low"  # chosen among levels with no failed check
    bad_rate_gap = None
    for criterion in by_level["high"].criteria:
        if criterion.name == "bad_rate_gap" and criterion.status == "failed":
            bad_rate_gap = criterion  # one per case set; the discussion set's is the one that failed
    assert admit.criterion_status_text(bad_rate_gap) == "failed (advisory)"


def test_integration_fails_a_mode_that_does_not_reason_and_a_failed_real_turn(tmp_path):
    config = _config(_datasets(tmp_path), ["medium"])
    results = gate.integration_criteria(_probe_record(0.0, real_failures="3/6"), "medium", config)
    statuses = {criterion.name: criterion.status for criterion in results}
    assert statuses == {"recommended_mode": "passed", "real_turn_failures": "failed",
                        "reasons_when_thinking": "failed"}
    no_mode = gate.integration_criteria(_probe_record(0.0, recommended=None), "medium", config)
    assert {criterion.name: criterion.status for criterion in no_mode}["recommended_mode"] == "failed"


def test_latency_is_not_measured_when_samples_have_no_timings(tmp_path):
    samples = [{"case_id": "d0", "sample": 0, "valid": True, "bad": False, "units": []}]
    stats = gate.arm_sample_stats("candidate_low", samples, judged=True)
    assert stats.seconds_p50 is None and stats.seconds_p95 is None
    config = _config(_datasets(tmp_path), ["low"])
    discussion_set = config.case_sets[0]
    speed = gate.speed_and_cost_criteria(discussion_set, stats, config)
    assert [criterion.status for criterion in speed] == ["not_measured", "not_measured"]


def test_a_case_set_s_own_speed_limits_replace_the_shared_ones(tmp_path):
    samples = []
    for sample_index in range(4):
        samples.append({"case_id": "d0", "sample": sample_index, "valid": True, "bad": False, "units": [],
                        "usage": {"seconds": 8.0}})
    stats = gate.arm_sample_stats("candidate_low", samples, judged=True)
    config = _config(_datasets(tmp_path), ["low"])
    config.criteria.speed = SpeedCriteria(max_p50_seconds=12.0)
    discussion_set = config.case_sets[0]
    shared = gate.speed_and_cost_criteria(discussion_set, stats, config)
    assert [criterion.status for criterion in shared] == ["passed"]  # 8 s against the shared 12 s
    discussion_set.speed = SpeedCriteria(max_p50_seconds=5.5)
    own = gate.speed_and_cost_criteria(discussion_set, stats, config)
    assert [(criterion.limit, criterion.status) for criterion in own] == [("at most 5.5s", "failed")]


# --- the runner ----------------------------------------------------------------------------------------


def _write_config(tmp_path: Path, levels: list[str]) -> Path:
    """Write a synthetic admission config file; returns its path."""
    config_path = tmp_path / "admission.json"
    config_path.write_text(_config(_datasets(tmp_path), levels).model_dump_json())
    return config_path


def test_plan_writes_the_configs_and_calls_nothing(tmp_path, monkeypatch, capsys):
    calls = []
    monkeypatch.setattr(admit, "run_probe_config", lambda path: calls.append(("probe", path)))
    monkeypatch.setattr(admit, "run_bench_config", lambda path: calls.append(("bench", path)))
    monkeypatch.setattr(admit, "ADMISSION_RESULTS", tmp_path / "results")

    admit.main(["--config", str(_write_config(tmp_path, ["low", "medium"])), "--plan"])

    assert calls == []
    configs_dir = tmp_path / "results" / "synthetic_admission" / "configs"
    assert sorted(path.name for path in configs_dir.iterdir()) == [
        "bench_discussion.json", "bench_votes.json", "integration_low.json", "integration_medium.json"]
    bench_config = json.loads((configs_dir / "bench_votes.json").read_text())
    assert [arm["label"] for arm in bench_config["arms"]] == ["reference_low", "candidate_low", "candidate_medium"]
    assert bench_config["arms"][2]["env"] == {"GOOGLE_GENAI_THINKING_LEVEL": "medium", "LLM_STRUCTURED_MODE": "json_mode"}
    probe_config = json.loads((configs_dir / "integration_low.json").read_text())
    assert probe_config["label"] == "synthetic_admission/integration_low"
    assert probe_config["thinking_level"] == "low"
    printed = capsys.readouterr().out
    assert "2 cases × 4 samples × 3 arms = 24 generations" in printed
    assert "total model calls: at most" in printed
    assert not (tmp_path / "results" / "synthetic_admission" / "admission_report.md").exists()


def test_from_existing_builds_the_report_and_verdict_without_running(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(admit, "run_probe_config", lambda path: calls.append(("probe", path)))
    monkeypatch.setattr(admit, "run_bench_config", lambda path: calls.append(("bench", path)))
    results_root = tmp_path / "results"
    monkeypatch.setattr(admit, "ADMISSION_RESULTS", results_root)
    config_path = _write_config(tmp_path, ["low", "medium"])
    _write_synthetic_outputs(results_root, admit.load_admission_config(config_path))

    admit.main(["--config", str(config_path), "--from-existing"])

    assert calls == []
    out_dir = results_root / "synthetic_admission"
    verdict = json.loads((out_dir / "admission_verdict.json").read_text())
    assert [arm["verdict"] for arm in verdict["arms"]] == ["admit", "admit"]
    assert verdict["cheapest_passing_level"] == "low"
    report = (out_dir / "admission_report.md").read_text()
    for heading in ("## 1. Quality", "## 2. Integration", "## 3. Cost and speed", "## 4. Reliability",
                    "## 5. Rollout and records"):
        assert heading in report
    assert "Not tested by this run" in report
    assert "evaluation/experiments/phase3_capture.py" in report
    assert "The catalogue row is changed by hand after review" in report
