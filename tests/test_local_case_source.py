"""Local case source: sidecar files written from sink records feed the frozen-set
builders without any Langfuse read (the primary fix for the heavy-trace 422)."""

import json
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from Agents.observability import (
    EvalCaseSink,
    action_eval_span_name,
    day_summary_span_name,
    dedup_span_name,
    extraction_span_name,
    freeze_case,
)
from Agents.schemas.evaluation import (
    DaySummaryCase,
    DedupCase,
    EvalCase,
    ExtractionCase,
)
from evaluation.src.core.config_schema import ExtractionDatasetBuildConfig
from evaluation.src.data.sources.sidecar import LocalCaseSource, read_local_spans
from evaluation.src.experiments.extraction_builder import build_records


def _sink_for_game(trace_id: str) -> EvalCaseSink:
    """Emit one case of each kind through the real freeze_case tee."""
    span = SimpleNamespace(trace_id=trace_id, id=f"obs-{trace_id}")
    sink = EvalCaseSink()
    freeze_case(
        span,
        EvalCase(
            span_name=action_eval_span_name("p1", 1, 1, "day_discussion"),
            player_id="p1",
            player_role="wolf",
            day=1,
            round=1,
            action_phase="day_discussion",
            memory_enabled=False,
        ),
        kind="agent_action_eval",
        case_key="eval_case",
        sink=sink,
    )
    freeze_case(
        span,
        ExtractionCase(
            span_name=extraction_span_name("g-" + trace_id),
            game_id="g-" + trace_id,
            formatted_discussions="full transcript " * 100,
        ),
        kind="postgame_extraction",
        case_key="extraction_case",
        sink=sink,
    )
    freeze_case(
        span,
        DedupCase(span_name=dedup_span_name("observation", "wolf", "vote", 1)),
        kind="dedup",
        case_key="dedup_case",
        sink=sink,
    )
    freeze_case(
        span,
        DaySummaryCase(span_name=day_summary_span_name("g-" + trace_id, 1), day=1),
        kind="day_summary",
        case_key="day_summary_case",
        sink=sink,
    )
    return sink


def _write_batch(tmp_path, games: list[str], with_orphan: bool = True):
    """Write per-game sidecars + a batch JSONL pointing at them (absolute paths)."""
    batch_path = tmp_path / "batch.jsonl"
    records = []
    for trace_id in games:
        sidecar = tmp_path / "eval_cases" / f"{trace_id}.jsonl"
        sidecar.parent.mkdir(parents=True, exist_ok=True)
        with sidecar.open("w", encoding="utf-8") as f:
            for rec in _sink_for_game(trace_id).records:
                f.write(json.dumps(rec) + "\n")
        records.append(
            {
                "status": "success",
                "trace_id": trace_id,
                "eval_cases_path": str(sidecar),
            }
        )
    if with_orphan:
        # a pre-feature game: success record with no pointer → skipped w/ warning
        records.append({"status": "success", "session_id": "legacy"})
    with batch_path.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec) + "\n")
    return batch_path


def test_read_local_spans_groups_by_trace(tmp_path):
    batch_path = _write_batch(tmp_path, ["t1", "t2"])
    by_trace = read_local_spans(batch_path)
    assert list(by_trace) == ["t1", "t2"]
    assert len(by_trace["t1"]) == 4


def test_local_case_source_filters_by_kind(tmp_path):
    source = LocalCaseSource(_write_batch(tmp_path, ["t1"]))
    assert source.trace_ids() == ["t1"]
    assert len(source.eval_cases("t1")) == 1
    assert len(source.extraction_cases("t1")) == 1
    assert len(source.dedup_cases("t1")) == 1
    assert len(source.day_summary_cases("t1")) == 1
    assert source.eval_cases("t1")[0].trace_id == "t1"


def test_extraction_builder_builds_from_local_source(tmp_path):
    batch_path = _write_batch(tmp_path, ["t1", "t2"])
    config = ExtractionDatasetBuildConfig(
        eval_set_id="local_test",
        local_results=batch_path,
        max_games=0,
        max_samples=0,
    )
    records = build_records(config)
    assert len(records) == 2
    for record in records:
        assert record.extraction_case.formatted_discussions.startswith(
            "full transcript"
        )
        assert record.case_id == f"{record.trace_id}:obs-{record.trace_id}"


def test_config_requires_exactly_one_source():
    with pytest.raises(ValidationError):
        ExtractionDatasetBuildConfig(
            eval_set_id="x",
            local_results="batch.jsonl",
            session_prefix="also-set",
        )
    with pytest.raises(ValidationError):
        ExtractionDatasetBuildConfig(eval_set_id="x")
