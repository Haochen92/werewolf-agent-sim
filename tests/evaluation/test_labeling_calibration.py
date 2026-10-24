"""Tests for the labelling pipeline's calibration half: kappa, the anchor draw, the person's label
file, the acceptance test, the generalised exporter and the `calibrate` CLI stage.

All data is synthetic and every number asserted is worked out by hand in a comment.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from evaluation.src.core.stats import cohens_kappa
from evaluation.src.labeling.adapters.reranker import RerankerAdapter
from evaluation.src.labeling.anchor import (
    draw_stratified_sample,
    read_stratum_file,
    sample_size_for_ci,
    write_stratum_file,
)
from evaluation.src.labeling.calibration import (
    calibrate,
    load_model_labels,
    read_human_labels,
    write_calibration_report,
)
from evaluation.src.labeling.config import CalibrationConfig, ExportConfig
from evaluation.src.labeling.exporter import export_for_manual
from evaluation.src.labeling.pipeline import stage_calibrate
from evaluation.src.labeling.schemas import CalibrationReport

BINARY_LABELS = ["accuse", "none"]


def _calibration_config(tmp_path: Path, **overrides) -> CalibrationConfig:
    """Return a calibration config for binary accuse/none labels, with any field overridden."""
    config_fields = {
        "human_labels_path": tmp_path / "human.json",
        "model_label_paths": [tmp_path / "model.json"],
        "model_sources": ["speaker_tag"],
        "allowed_labels": BINARY_LABELS,
        "positive_label": "accuse",
        "output_dir": tmp_path / "reports",
    }
    config_fields.update(overrides)
    return CalibrationConfig(**config_fields)


def _write_simple_golden(path: Path, labeler: str, labels_by_key: dict[str, str | None]) -> Path:
    """Write a simple-golden label file, one row per key, all in case 0."""
    label_rows = []
    for key, label in labels_by_key.items():
        label_rows.append({"case_index": 0, "key": key, "label": label, "note": ""})
    path.write_text(json.dumps({"labeler": labeler, "labels": label_rows}))
    return path


# --- Cohen's kappa ---------------------------------------------------------------------------


def test_cohens_kappa_textbook_example():
    # 50 items: both "yes" 20, A yes / B no 5, A no / B yes 10, both "no" 15.
    # Observed agreement = (20 + 15) / 50 = 0.7.
    # A says yes 25/50 = 0.5, B says yes 30/50 = 0.6.
    # Chance agreement = 0.5 * 0.6 + 0.5 * 0.4 = 0.5.
    # Kappa = (0.7 - 0.5) / (1 - 0.5) = 0.4.
    rater_a = ["yes"] * 20 + ["yes"] * 5 + ["no"] * 10 + ["no"] * 15
    rater_b = ["yes"] * 20 + ["no"] * 5 + ["yes"] * 10 + ["no"] * 15
    assert cohens_kappa(rater_a, rater_b) == pytest.approx(0.4)


def test_cohens_kappa_edge_cases():
    # Both raters use one single label throughout: chance agreement is 1, the formula would
    # divide by zero, and full agreement is reported as 1.0.
    assert cohens_kappa(["no"] * 4, ["no"] * 4) == 1.0
    # Each rater uses one label but different ones: chance agreement 0, observed 0 -> kappa 0.
    assert cohens_kappa(["yes"] * 3, ["no"] * 3) == 0.0
    with pytest.raises(ValueError):
        cohens_kappa(["yes"], ["yes", "no"])
    with pytest.raises(ValueError):
        cohens_kappa([], [])


# --- anchor.py -------------------------------------------------------------------------------


def test_sample_size_for_ci_reproduces_the_table():
    # n = 1.96^2 * 0.8 * 0.2 / h^2:  h=0.10 -> 61.5 -> 62;  h=0.05 -> 245.9 -> 246.
    assert sample_size_for_ci(0.10) == 62
    assert sample_size_for_ci(0.05) == 246
    # h=0.08 -> 96.04, which rounds UP to 97; plan.md's "~96" rounds it to the nearest.
    assert sample_size_for_ci(0.08) == 97
    with pytest.raises(ValueError):
        sample_size_for_ci(0.0)


def test_stratified_draw_is_deterministic_and_reports_short_strata():
    flagged_keys = [f"f{index:02d}" for index in range(5)]
    unflagged_keys = [f"u{index:02d}" for index in range(30)]
    stratum_by_key = {key: "flagged" for key in flagged_keys}
    stratum_by_key.update({key: "unflagged" for key in unflagged_keys})
    candidate_keys = flagged_keys + unflagged_keys

    first_draw = draw_stratified_sample(candidate_keys, stratum_by_key, per_stratum=8, seed=7)
    repeat_draw = draw_stratified_sample(
        list(reversed(candidate_keys)), stratum_by_key, per_stratum=8, seed=7
    )
    other_seed_draw = draw_stratified_sample(candidate_keys, stratum_by_key, per_stratum=8, seed=8)

    # Same seed and candidate set -> same keys, whatever the input order.
    assert first_draw == repeat_draw
    assert first_draw.drawn_keys != other_seed_draw.drawn_keys
    # The short stratum gives all 5 of its keys and a note; the full one gives 8.
    assert first_draw.drawn_count_by_stratum == {"flagged": 5, "unflagged": 8}
    assert set(flagged_keys) <= set(first_draw.drawn_keys)
    assert first_draw.short_stratum_notes == ["flagged: asked for 8, only 5 candidates"]
    assert first_draw.drawn_keys == sorted(first_draw.drawn_keys)


def test_stratified_draw_rejects_a_candidate_with_no_stratum():
    with pytest.raises(ValueError, match="no stratum"):
        draw_stratified_sample(["a", "b"], {"a": "flagged"}, per_stratum=1, seed=0)


def test_stratum_file_round_trip(tmp_path):
    stratum_by_key = {"a": "flagged", "b": "unflagged", "c": "flagged"}
    path = write_stratum_file(["a", "b"], stratum_by_key, tmp_path / "strata.json")
    assert read_stratum_file(path) == {"a": "flagged", "b": "unflagged"}


# --- read_human_labels -----------------------------------------------------------------------


def test_read_human_labels_returns_labels_by_key(tmp_path):
    path = _write_simple_golden(tmp_path / "human.json", "owner", {"a": "accuse", "b": " none "})
    human_labels = read_human_labels(path, expected_keys=["a", "b"], allowed_labels=BINARY_LABELS)
    assert human_labels == {"a": "accuse", "b": "none"}


def test_read_human_labels_reports_every_problem_at_once(tmp_path):
    label_rows = [
        {"case_index": 0, "key": "a", "label": "accuse", "note": ""},
        {"case_index": 0, "key": "a", "label": "none", "note": ""},  # labelled twice
        {"case_index": 0, "key": "b", "label": "", "note": ""},  # empty label
        {"case_index": 0, "key": "c", "label": "maybe", "note": ""},  # not an allowed label
        {"case_index": 0, "key": "zzz", "label": "none", "note": ""},  # not an expected key
        {"key": "e", "label": "none", "note": ""},  # no case_index
        {"case_index": 0, "label": "none", "note": ""},  # no key
    ]
    path = tmp_path / "human.json"
    path.write_text(json.dumps({"labeler": "owner", "labels": label_rows}))

    with pytest.raises(ValueError) as raised:
        read_human_labels(path, expected_keys=["a", "b", "c", "d", "e"], allowed_labels=BINARY_LABELS)

    message = str(raised.value)
    assert "7 problem(s)" in message
    assert "key 'a': labelled 2 times" in message
    assert "key 'b': empty label" in message
    assert "key 'c': label 'maybe' is not one of" in message
    assert "key 'd': not labelled" in message
    assert "key 'zzz': not one of the expected keys" in message
    assert "(key 'e'): no case_index" in message
    assert "row 7: no key" in message


# --- calibrate -------------------------------------------------------------------------------


def _passing_data() -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    """50 items: person says accuse on k00-k24, none on k25-k49.

    The model misses k00-k02 (says none) and false-alarms on k25-k26 (says accuse):
    45/50 agree. Strata: k00-k24 "flagged", k25-k49 "unflagged".
    """
    human_labels: dict[str, str] = {}
    model_labels: dict[str, str] = {}
    stratum_by_key: dict[str, str] = {}
    for index in range(50):
        key = f"k{index:02d}"
        human_labels[key] = "accuse" if index < 25 else "none"
        model_labels[key] = human_labels[key]
        stratum_by_key[key] = "flagged" if index < 25 else "unflagged"
    for missed_key in ["k00", "k01", "k02"]:
        model_labels[missed_key] = "none"
    for false_alarm_key in ["k25", "k26"]:
        model_labels[false_alarm_key] = "accuse"
    return human_labels, model_labels, stratum_by_key


def test_calibrate_passing_source(tmp_path):
    human_labels, model_labels, stratum_by_key = _passing_data()
    config = _calibration_config(tmp_path)

    report = calibrate(human_labels, model_labels, stratum_by_key, "speaker_tag", config)

    assert report.items == 50 and report.agreeing_items == 45
    assert report.agreement_rate == pytest.approx(0.9)
    # Clopper-Pearson 95% for 45/50 is about [0.782, 0.967].
    assert report.agreement_ci[0] == pytest.approx(0.782, abs=0.001)
    # Observed 0.9; person accuse 0.5, model accuse 24/50 = 0.48;
    # chance = 0.5*0.48 + 0.5*0.52 = 0.5; kappa = (0.9 - 0.5) / 0.5 = 0.8.
    assert report.cohens_kappa == pytest.approx(0.8)
    assert report.confusion == {
        "accuse": {"accuse": 22, "none": 3},
        "none": {"accuse": 2, "none": 23},
    }

    accuse_row, none_row = report.label_rows
    assert (accuse_row.label, accuse_row.human_count, accuse_row.model_count, accuse_row.both_count) == (
        "accuse", 25, 24, 22,
    )
    assert accuse_row.precision == pytest.approx(22 / 24)
    assert accuse_row.recall == pytest.approx(22 / 25)
    assert (none_row.human_count, none_row.model_count, none_row.both_count) == (25, 26, 23)

    rate_by_stratum = {row.stratum: row.agreement_rate for row in report.stratum_rows}
    assert rate_by_stratum == {"flagged": pytest.approx(22 / 25), "unflagged": pytest.approx(23 / 25)}

    assert [disagreement.key for disagreement in report.disagreements] == [
        "k00", "k01", "k02", "k25", "k26",
    ]
    assert report.disagreements[0].human_label == "accuse"
    assert report.disagreements[0].model_label == "none"

    # 3 misses vs 2 false alarms: exact McNemar p = 1.0.
    assert report.bias_test.human_only_positive == 3
    assert report.bias_test.model_only_positive == 2
    assert report.bias_test.p_value == pytest.approx(1.0)

    assert [condition.status for condition in report.gate] == ["passed", "passed", "passed"]
    assert report.accepted is True


def test_calibrate_failing_source(tmp_path):
    # 20 items: person accuse on k00-k09, none on k10-k19. The model says accuse on k00-k15:
    # 6 false alarms (k10-k15), 0 misses -> 14/20 = 0.70 agreement.
    human_labels: dict[str, str] = {}
    model_labels: dict[str, str] = {}
    for index in range(20):
        key = f"k{index:02d}"
        human_labels[key] = "accuse" if index < 10 else "none"
        model_labels[key] = "accuse" if index < 16 else "none"
    config = _calibration_config(tmp_path)

    report = calibrate(human_labels, model_labels, None, "echo_gate", config)

    assert report.agreement_rate == pytest.approx(0.7)
    assert [row.stratum for row in report.stratum_rows] == ["all"]
    # 6 false alarms, 0 misses: exact two-sided p = 2 * 0.5^6 = 0.03125.
    assert report.bias_test.model_only_positive == 6
    assert report.bias_test.p_value == pytest.approx(0.03125)
    status_by_condition = {condition.name: condition.status for condition in report.gate}
    assert status_by_condition == {
        "agreement": "failed",
        "ci_lower_bound": "failed",
        "no_directional_bias": "failed",
    }
    assert "more often than the person" in report.gate[2].explanation
    assert report.accepted is False


def test_calibrate_skips_bias_test_for_three_labels_and_lists_missing_model_labels(tmp_path):
    human_labels = {"a": "0", "b": "1", "c": "2", "d": "2"}
    model_labels = {"a": "0", "b": "1", "c": "2"}  # no label for "d"
    config = _calibration_config(tmp_path, allowed_labels=None, positive_label=None)

    report = calibrate(human_labels, model_labels, None, "panel", config)

    assert report.items == 3 and report.agreeing_items == 3
    assert report.keys_without_model_label == ["d"]
    assert report.bias_test is None
    assert report.bias_test_skipped_reason == "no positive label configured"
    assert report.gate[2].status == "not_applicable"
    # 3/3 agree, but the interval is wide: Clopper-Pearson lower bound for 3/3 is about 0.29.
    assert report.gate[1].status == "failed"
    assert report.accepted is False


def test_write_calibration_report(tmp_path):
    human_labels, model_labels, stratum_by_key = _passing_data()
    config = _calibration_config(tmp_path)
    report = calibrate(human_labels, model_labels, stratum_by_key, "gemini/flash lite", config)

    markdown_path, json_path = write_calibration_report(report, tmp_path / "reports")

    assert markdown_path.name == "calibration_gemini_flash_lite.md"
    markdown_lines = markdown_path.read_text().splitlines()
    assert markdown_lines[2] == "**Verdict: ACCEPT**"
    markdown_text = markdown_path.read_text()
    assert "| accuse | 25 | 24 | 22 | 91.7% | 88.0% |" in markdown_text
    assert "| flagged | 25 | 22 | 88.0% |" in markdown_text
    assert "| k25 | unflagged | none | accuse |" in markdown_text
    assert CalibrationReport.model_validate_json(json_path.read_text()) == report


def test_load_model_labels_finds_the_source_or_names_the_ones_found(tmp_path):
    engine_path = tmp_path / "model.json"
    engine_path.write_text(json.dumps({"results": [
        {"case_index": 0, "key": "a", "model_scores": {"speaker_tag": "accuse", "echo_gate": None}},
        {"case_index": 1, "key": "b", "model_scores": {"speaker_tag": "none", "echo_gate": "none"}},
    ]}))
    assert load_model_labels([engine_path], "speaker_tag") == {"a": "accuse", "b": "none"}
    # A null label means the source did not label that item.
    assert load_model_labels([engine_path], "echo_gate") == {"b": "none"}
    with pytest.raises(ValueError, match="sources found"):
        load_model_labels([engine_path], "judge")


# --- the calibrate CLI stage -----------------------------------------------------------------


def test_stage_calibrate_end_to_end(tmp_path):
    human_labels, model_labels, stratum_by_key = _passing_data()
    _write_simple_golden(tmp_path / "human.json", "owner", human_labels)
    _write_simple_golden(tmp_path / "model.json", "speaker_tag", model_labels)
    write_stratum_file(sorted(stratum_by_key), stratum_by_key, tmp_path / "strata.json")
    config = _calibration_config(tmp_path, stratum_path=tmp_path / "strata.json")

    report_paths = stage_calibrate(config)

    assert [path.name for path in report_paths] == [
        "calibration_speaker_tag.md", "calibration_speaker_tag.json",
    ]
    report = CalibrationReport.model_validate_json(report_paths[1].read_text())
    assert report.accepted is True and report.items == 50


# --- exporter --------------------------------------------------------------------------------

EXPORT_CANDIDATES = {"cases": [
    {"case_index": 0, "golden_situations": ["Day 2, seer claim"],
     "retrieved_observations": [{"key": "obs-aaaaaaaaaaaa-1", "situation": "A seer claimed",
                                 "approach": "Voted", "outcome": "Won", "score": 0.91}],
     "retrieved_strategy_points": [{"key": "sp-bbbbbbbbbbbb-2", "situation": "Late game",
                                    "action": "Push", "score": 0.5}]},
    {"case_index": 1, "golden_situations": ["Night 1"],
     "retrieved_observations": [{"key": "obs-cccccccccccc-3", "situation": "Quiet night",
                                 "score": 0.2}],
     "retrieved_strategy_points": []},
]}

# The reranker export as the exporter wrote it before `manual_response_field` existed.
EXPECTED_DEFAULT_BATCHES = [
    'INSTRUCTIONS\n\n---\n\n# Case 0\n\n### Memory [obs-aaaaaaaa] (observation) (score: 0.9100)\n'
    '**Situation:** A seer claimed\n**Approach:** Voted\n**Outcome:** Won\n\n'
    '### Memory [sp-bbbbbbbbb] (strategy_point) (score: 0.5000)\n**Situation:** Late game\n'
    '**Action:** Push\n\n## Response for Case 0\n\nRate each of the 2 items above. JSON format:\n'
    '```json\n[\n  {"idx": 1, "key": "obs-aaaaaaaa", "type": "observation", "relevance": _},\n'
    '  {"idx": 2, "key": "sp-bbbbbbbbb", "type": "strategy_point", "relevance": _}\n]\n```',
    'INSTRUCTIONS\n\n---\n\n# Case 1\n\n### Memory [obs-cccccccc] (observation) (score: 0.2000)\n'
    '**Situation:** Quiet night\n\n## Response for Case 1\n\nRate each of the 1 items above. '
    'JSON format:\n```json\n[\n  {"idx": 1, "key": "obs-cccccccc", "type": "observation", '
    '"relevance": _}\n]\n```',
]


class _AccusationAdapter(RerankerAdapter):
    """A reranker adapter whose manual export asks for an "accusation" field."""

    @property
    def manual_response_field(self) -> str:
        return "accusation"


def _export_config(tmp_path: Path, **overrides) -> ExportConfig:
    """Return an export config over EXPORT_CANDIDATES, one case per batch."""
    candidates_path = tmp_path / "candidates.json"
    candidates_path.write_text(json.dumps(EXPORT_CANDIDATES))
    config_fields = {
        "candidates_path": candidates_path,
        "output_dir": tmp_path / "export",
        "batch_size": 1,
    }
    config_fields.update(overrides)
    return ExportConfig(**config_fields)


def test_exporter_default_output_is_unchanged(tmp_path):
    config = _export_config(tmp_path)
    batch_paths = export_for_manual(config, RerankerAdapter(), "INSTRUCTIONS")
    assert [path.read_text() for path in batch_paths] == EXPECTED_DEFAULT_BATCHES
    assert not (config.output_dir / "answers_template.json").exists()


def test_exporter_uses_the_adapter_response_field(tmp_path):
    batch_paths = export_for_manual(_export_config(tmp_path), _AccusationAdapter(), "INSTRUCTIONS")
    first_batch = batch_paths[0].read_text()
    assert '"accusation": _' in first_batch
    assert '"relevance"' not in first_batch


def test_exporter_key_filter_and_answers_template(tmp_path):
    config = _export_config(
        tmp_path,
        keys=["sp-bbbbbbbbbbbb-2", "obs-cccccccccccc-3"],
        write_answers_template=True,
    )
    batch_paths = export_for_manual(config, RerankerAdapter(), "INSTRUCTIONS")

    assert "obs-aaaaaaaa" not in batch_paths[0].read_text()
    template = json.loads((config.output_dir / "answers_template.json").read_text())
    assert template == {"labeler": "owner", "labels": [
        {"case_index": 0, "key": "sp-bbbbbbbbbbbb-2", "label": None, "note": ""},
        {"case_index": 1, "key": "obs-cccccccccccc-3", "label": None, "note": ""},
    ]}

    # Unfilled, the template fails validation on every row; filled, it reads back.
    template_path = config.output_dir / "answers_template.json"
    with pytest.raises(ValueError, match="2 problem"):
        read_human_labels(template_path, config.keys, allowed_labels=["0", "1", "2"])
    for label_row in template["labels"]:
        label_row["label"] = 2
    template_path.write_text(json.dumps(template))
    assert read_human_labels(template_path, config.keys, allowed_labels=["0", "1", "2"]) == {
        "sp-bbbbbbbbbbbb-2": "2",
        "obs-cccccccccccc-3": "2",
    }


def test_exporter_rejects_unknown_keys(tmp_path):
    config = _export_config(tmp_path, keys=["no-such-key"])
    with pytest.raises(ValueError, match="no-such-key"):
        export_for_manual(config, RerankerAdapter(), "INSTRUCTIONS")
