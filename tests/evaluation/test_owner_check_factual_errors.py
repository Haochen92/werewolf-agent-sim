"""Tests for the factual-error owner check: the adapter and the packet builder.

All data is a small synthetic bench run: three cases with a written expectation and one census
case with a fact sheet, judged in one arm. No model is called.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from evaluation.experiments.owner_check_factual_errors import (
    FLAGGED_STRATUM,
    NOT_FLAGGED_STRATUM,
    build_packet,
    collect_judged_statements,
    draw_capped_sample,
    read_judged_run,
    score_packet,
)
from evaluation.src.judges import golden_expectation
from evaluation.src.labeling.adapters.factual_errors import (
    CENSUS_READER,
    EXPECTATION_JUDGE,
    FactualErrorAdapter,
    JudgedStatement,
)

JUDGE_REASON_SENTINEL = "JUDGE-REASON-SENTINEL"
"""Written into every judge reason, so a test can prove no reason reaches the export."""

CENSUS_FACTS = {
    "roles": {
        "player_1": "wolf", "player_2": "wolf", "player_3": "serial_killer",
        "player_4": "villager", "player_5": "healer", "player_6": "investigator",
    },
    "night_resolutions": [{
        "day": 1, "deaths": ["player_4"], "wolves_target": "player_4", "kill_successful": True,
    }],
    "day_resolutions": [],
    "day_summaries": [],
}


def _golden_case(case_id: str, game_id: str) -> dict:
    """Return a bench case with a written expectation."""
    return {
        "case_id": case_id, "game_id": game_id, "day": 2, "speaker": "player_3",
        "role": "investigator", "phase": "day_discussion", "facts": {"roles": {}},
        "golden": f"EXPECTATION for {case_id}: player_3 checked only player_6.",
    }


def _judged_sample(case_id: str, sample: int, verdicts: list[str]) -> dict:
    """Return one judged sample with one unit per verdict (message, note, reads, ...)."""
    unit_kinds = ["message", "updated_strategy", "reads"]
    units = []
    golden_reasons = {}
    for unit_index, verdict in enumerate(verdicts):
        units.append({
            "unit": unit_kinds[unit_index % len(unit_kinds)],
            "text": f"statement {case_id} s{sample} u{unit_index}",
        })
        golden_reasons[str(unit_index)] = f"{JUDGE_REASON_SENTINEL} {verdict}"
    return {
        "case_id": case_id, "sample": sample, "valid": True, "units": units,
        "unit_verdicts": verdicts, "golden_reasons": golden_reasons,
        "bad": "golden_violates" in verdicts or "hallucination" in verdicts,
    }


def _write_run(tmp_path: Path, run_at: str = "2026-10-13T10:00:00+00:00", **config_overrides) -> Path:
    """Write a synthetic bench run folder and its case file; return the run folder.

    Case ``aaaa`` has 4 flagged statements, ``bbbb`` 1 flagged, ``cccc`` none; the census case
    ``dddd`` has one ``hallucination`` and one ``no_anchor`` (never read) statement.
    """
    cases = [
        _golden_case("aaaa0000aaaa0000", "g1"),
        _golden_case("bbbb0000bbbb0000", "g1"),
        _golden_case("cccc0000cccc0000", "g2"),
        {
            "case_id": "dddd0000dddd0000", "game_id": "g3", "day": 3, "speaker": "player_6",
            "role": "investigator", "phase": "day_discussion", "facts": CENSUS_FACTS, "golden": "",
        },
    ]
    cases_path = tmp_path / "cases.jsonl"
    cases_path.write_text("".join(json.dumps(case) + "\n" for case in cases))

    judged_samples = [
        _judged_sample("aaaa0000aaaa0000", 0, ["golden_violates", "golden_violates", "golden_meets"]),
        _judged_sample("aaaa0000aaaa0000", 1, ["golden_violates", "golden_violates", "golden_unclear"]),
        _judged_sample("bbbb0000bbbb0000", 0, ["golden_violates", "golden_meets", "golden_meets"]),
        _judged_sample("cccc0000cccc0000", 0, ["golden_meets", "golden_meets", "golden_meets"]),
        _judged_sample("dddd0000dddd0000", 0, ["hallucination", "no_anchor"]),
    ]
    # The census statement names dead player_4, so the screen anchors it as the bench did.
    judged_samples[-1]["units"][0]["text"] = "player_4 is still my top suspect."

    run_dir = tmp_path / "bench_run"
    run_dir.mkdir()
    (run_dir / "judged_arm_a.jsonl").write_text(
        "".join(json.dumps(judged_sample) + "\n" for judged_sample in judged_samples)
    )
    run_config = {"label": "bench_run", "dataset": str(cases_path), "arms": [{"label": "arm_a"}]}
    run_config.update(config_overrides)
    (run_dir / "summary.json").write_text(json.dumps({"run_at": run_at, "config": run_config}))
    return run_dir


# --- candidates and judge labels ---------------------------------------------------------------


def test_collect_maps_verdicts_and_skips_statements_never_read(tmp_path):
    statements, judge_label_by_key, recorded_verdict_by_key = collect_judged_statements(
        [read_judged_run(_write_run(tmp_path))]
    )
    # 4 golden samples x 3 units + 1 read census unit (its no_anchor unit was never judged).
    assert len(statements) == 13
    assert len({statement.key for statement in statements}) == 13

    first_key = "bench_run:g1:aaaa0000:arm_a:s0:u0"
    assert judge_label_by_key[first_key] == "error"
    assert recorded_verdict_by_key[first_key] == "golden_violates"
    assert judge_label_by_key["bench_run:g1:aaaa0000:arm_a:s1:u2"] == "no_error"  # golden_unclear
    assert judge_label_by_key["bench_run:g3:dddd0000:arm_a:s0:u0"] == "error"  # hallucination
    assert "bench_run:g3:dddd0000:arm_a:s0:u1" not in judge_label_by_key  # no_anchor

    # Cases are numbered 1.. in (run, game, case) order; aaaa and bbbb share game g1.
    case_index_by_case_id = {statement.case_id: statement.case_index for statement in statements}
    assert case_index_by_case_id == {
        "aaaa0000aaaa0000": 1, "bbbb0000bbbb0000": 2, "cccc0000cccc0000": 3, "dddd0000dddd0000": 4,
    }


def test_judge_kind_follows_the_case_and_carries_the_judge_input(tmp_path):
    statements, _, _ = collect_judged_statements([read_judged_run(_write_run(tmp_path))])
    statement_by_key = {statement.key: statement for statement in statements}

    golden_statement = statement_by_key["bench_run:g1:aaaa0000:arm_a:s0:u1"]
    assert golden_statement.judge_kind == EXPECTATION_JUDGE
    assert golden_statement.expectation.startswith("EXPECTATION for aaaa")
    assert golden_statement.judge_unit_name == "private strategy note"
    assert golden_statement.fact_sheet is None

    census_statement = statement_by_key["bench_run:g3:dddd0000:arm_a:s0:u0"]
    assert census_statement.judge_kind == CENSUS_READER
    assert "player_4 — villager — died night 1, killed by the wolves" in census_statement.fact_sheet["deaths"]
    assert "dead_id" in census_statement.fact_sheet["anchors"]


@pytest.mark.parametrize(
    ("run_at", "config_overrides"),
    [
        ("2026-10-13T10:00:00+00:00", {"golden_model": "anthropic/claude-sonnet-5-5"}),
        ("2026-10-11T10:00:00+00:00", {}),  # the defaults were Gemini before 2026-10-12
    ],
)
def test_a_run_not_judged_by_haiku_is_refused(tmp_path, run_at, config_overrides):
    run_dir = _write_run(tmp_path, run_at=run_at, **config_overrides)
    with pytest.raises(ValueError, match="not judged by anthropic/claude-haiku-5-5"):
        read_judged_run(run_dir)


# --- the draw ------------------------------------------------------------------------------------


def _statement(key: str, case_index: int) -> JudgedStatement:
    """Return a minimal expectation-judge statement for draw tests."""
    return JudgedStatement(
        key=key, case_index=case_index, run_label="r", game_id="g", case_id=f"c{case_index}",
        arm="a", sample=0, unit_index=0, unit_kind="message", judge_unit_name="public chat message",
        judge_kind=EXPECTATION_JUDGE, statement_text="t", expectation="e",
    )


def test_draw_is_stratified_and_capped_per_case():
    # Flagged: 10 in case 1, 1 each in cases 2-4. Not flagged: 3 in each of cases 1-4.
    statements = []
    stratum_by_key = {}
    for flagged_number in range(10):
        statements.append(_statement(f"f1-{flagged_number}", 1))
        stratum_by_key[f"f1-{flagged_number}"] = FLAGGED_STRATUM
    for case_index in (2, 3, 4):
        statements.append(_statement(f"f{case_index}", case_index))
        stratum_by_key[f"f{case_index}"] = FLAGGED_STRATUM
    for case_index in (1, 2, 3, 4):
        for unflagged_number in range(3):
            key = f"n{case_index}-{unflagged_number}"
            statements.append(_statement(key, case_index))
            stratum_by_key[key] = NOT_FLAGGED_STRATUM

    sample = draw_capped_sample(statements, stratum_by_key, per_stratum=5, cap_per_case=2, seed=7)

    # Cap 2 leaves 2 + 1 + 1 + 1 = 5 flagged, all drawn; 8 unflagged kept, 5 drawn.
    assert sample.drawn_count_by_stratum == {FLAGGED_STRATUM: 5, NOT_FLAGGED_STRATUM: 5}
    case_index_by_key = {statement.key: statement.case_index for statement in statements}
    drawn_per_case_and_stratum: dict[tuple[int, str], int] = {}
    for key in sample.drawn_keys:
        group = (case_index_by_key[key], stratum_by_key[key])
        drawn_per_case_and_stratum[group] = drawn_per_case_and_stratum.get(group, 0) + 1
    assert max(drawn_per_case_and_stratum.values()) <= 2

    repeated = draw_capped_sample(statements, stratum_by_key, per_stratum=5, cap_per_case=2, seed=7)
    assert repeated.drawn_keys == sample.drawn_keys


# --- the packet ----------------------------------------------------------------------------------


def _build(tmp_path: Path) -> Path:
    """Build a packet from the synthetic run (2 per stratum, cap 1 per case); return its folder."""
    packet_dir = tmp_path / "packet"
    build_packet([_write_run(tmp_path)], packet_dir, per_stratum=2, cap_per_case=1, seed=3)
    return packet_dir


def test_build_writes_every_packet_file(tmp_path):
    packet_dir = _build(tmp_path)
    for file_name in ("candidates.jsonl", "judge_labels.json", "strata.json", "GUIDE.md", "calib.json",
                      "export/answers_template.json"):
        assert (packet_dir / file_name).exists(), file_name
    assert list((packet_dir / "export").glob("batch_*.md"))

    judge_labels = json.loads((packet_dir / "judge_labels.json").read_text())
    assert judge_labels["labeler"] == "judge"
    assert len(judge_labels["labels"]) == 13

    strata = json.loads((packet_dir / "strata.json").read_text())
    stratum_counts = {FLAGGED_STRATUM: 0, NOT_FLAGGED_STRATUM: 0}
    for stratum in strata.values():
        stratum_counts[stratum] += 1
    assert stratum_counts == {FLAGGED_STRATUM: 2, NOT_FLAGGED_STRATUM: 2}

    answers = json.loads((packet_dir / "export/answers_template.json").read_text())
    assert sorted(row["key"] for row in answers["labels"]) == sorted(strata)

    calibration_config = json.loads((packet_dir / "calib.json").read_text())
    assert calibration_config["model_sources"] == ["judge"]
    assert calibration_config["positive_label"] == "error"


def test_export_and_candidates_are_blind(tmp_path):
    packet_dir = _build(tmp_path)
    blind_files = list((packet_dir / "export").glob("*")) + [packet_dir / "candidates.jsonl"]
    for blind_file in blind_files:
        file_text = blind_file.read_text()
        assert JUDGE_REASON_SENTINEL not in file_text, blind_file
        for recorded_verdict in ("golden_violates", "golden_meets", "golden_unclear", "recorded_verdict"):
            assert recorded_verdict not in file_text, (blind_file, recorded_verdict)
    # The expectation, the judge's input, is shown.
    batch_text = "\n".join(batch.read_text() for batch in (packet_dir / "export").glob("batch_*.md"))
    assert "EXPECTATION for" in batch_text


def test_rebuild_is_refused_once_the_owner_has_labelled(tmp_path):
    packet_dir = _build(tmp_path)
    (packet_dir / "human.json").write_text("{}")
    with pytest.raises(FileExistsError):
        build_packet([tmp_path / "bench_run"], packet_dir, per_stratum=2, cap_per_case=1, seed=3)


def test_score_on_filled_in_answers(tmp_path):
    packet_dir = _build(tmp_path)
    judge_label_by_key = {}
    for label_row in json.loads((packet_dir / "judge_labels.json").read_text())["labels"]:
        judge_label_by_key[label_row["key"]] = label_row["label"]

    answers = json.loads((packet_dir / "export/answers_template.json").read_text())
    for answer_row in answers["labels"]:
        answer_row["label"] = judge_label_by_key[answer_row["key"]]
    (packet_dir / "human.json").write_text(json.dumps(answers))

    report_paths = score_packet(packet_dir)

    assert sorted(path.name for path in report_paths) == ["calibration_judge.json", "calibration_judge.md"]
    report = json.loads((packet_dir / "reports/calibration_judge.json").read_text())
    assert report["items"] == 4
    assert report["agreement_rate"] == 1.0


# --- the adapter -------------------------------------------------------------------------------


def test_adapter_prompt_is_the_judges_own_and_parses_its_verdicts(tmp_path):
    packet_dir = _build(tmp_path)
    adapter = FactualErrorAdapter()
    items = adapter.load_items(packet_dir / "candidates.jsonl")
    golden_item = next(item for item in items if item.item_type == EXPECTATION_JUDGE)

    prompt = adapter.format_prompt(golden_item)
    assert prompt.startswith(golden_expectation.SYSTEM)
    assert golden_item.raw["statement"].expectation in prompt

    assert adapter.parse_response('{"quote": "", "reason": "r", "verdict": "violates"}') == "error"
    assert adapter.parse_response('{"quote": "", "reason": "r", "verdict": "unclear"}') == "no_error"
    assert adapter.parse_response("Verdict: hallucination") == "error"
    assert adapter.parse_response("deliberate_deception") == "no_error"
    assert adapter.parse_response("no idea") is None

    verdict = golden_expectation.GoldenVerdict(quote="q", reason="r", verdict="meets")
    assert adapter.parse_structured(golden_item, verdict)[0] == "no_error"


def test_manual_rendering_of_a_census_item_shows_the_fact_sheet(tmp_path):
    statements, _, _ = collect_judged_statements([read_judged_run(_write_run(tmp_path))])
    census_statement = next(statement for statement in statements if statement.judge_kind == CENSUS_READER)
    candidates_path = tmp_path / "one.jsonl"
    candidates_path.write_text(census_statement.model_dump_json() + "\n")

    adapter = FactualErrorAdapter()
    rendered = adapter.format_for_manual(adapter.load_items(candidates_path)[0])
    assert "Deaths so far" in rendered
    assert "player_4 is still my top suspect." in rendered
    assert "hallucination" not in rendered
