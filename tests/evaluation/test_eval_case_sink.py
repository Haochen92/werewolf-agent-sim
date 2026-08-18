"""Local eval-case sink: freeze_case stamps real span identity, the sink record is
byte-equivalent to the Langfuse span copy, and it round-trips through every
read-side ``*_case_from_span`` converter (the local/Langfuse source equivalence
the frozen-set builders rely on)."""

from types import SimpleNamespace

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
from evaluation.src.data.converters.agent_decision import eval_case_from_span
from evaluation.src.data.converters.day_summary import day_summary_case_from_span
from evaluation.src.data.converters.dedup import dedup_case_from_span
from evaluation.src.data.converters.extraction import extraction_case_from_span

FAKE_SPAN = SimpleNamespace(trace_id="trace-abc", id="obs-123")


def _eval_case() -> EvalCase:
    return EvalCase(
        span_name=action_eval_span_name("player_1", 2, 3, "day_discussion"),
        player_id="player_1",
        player_role="wolf",
        day=2,
        round=3,
        action_phase="day_discussion",
        memory_enabled=True,
    )


def test_freeze_case_stamps_ids_and_returns_the_dump():
    case = _eval_case()
    sink = EvalCaseSink()
    payload = freeze_case(
        FAKE_SPAN, case, kind="agent_action_eval", case_key="eval_case", sink=sink
    )
    assert case.trace_id == "trace-abc"
    assert case.observation_id == "obs-123"
    assert payload == case.model_dump(mode="json")

    [record] = sink.records
    assert record == {
        "kind": "agent_action_eval",
        "id": "obs-123",
        "name": case.span_name,
        "trace_id": "trace-abc",
        "parent_observation_id": None,
        "metadata": {},
        "input": None,
        "output": {"eval_case": payload},
    }


def test_none_sink_is_a_noop_tee():
    case = _eval_case()
    payload = freeze_case(
        FAKE_SPAN, case, kind="agent_action_eval", case_key="eval_case", sink=None
    )
    assert payload["trace_id"] == "trace-abc"


def test_sink_records_round_trip_all_four_converters():
    sink = EvalCaseSink()
    cases = [
        (_eval_case(), "agent_action_eval", "eval_case", eval_case_from_span),
        (
            ExtractionCase(span_name=extraction_span_name("g1"), game_id="g1"),
            "postgame_extraction",
            "extraction_case",
            extraction_case_from_span,
        ),
        (
            DedupCase(span_name=dedup_span_name("observation", "wolf", "vote", 0)),
            "dedup",
            "dedup_case",
            dedup_case_from_span,
        ),
        (
            DaySummaryCase(span_name=day_summary_span_name("g1", 1), game_id="g1"),
            "day_summary",
            "day_summary_case",
            day_summary_case_from_span,
        ),
    ]
    for case, kind, case_key, _ in cases:
        freeze_case(FAKE_SPAN, case, kind=kind, case_key=case_key, sink=sink)

    assert len(sink.records) == 4
    for record, (case, _, _, converter) in zip(sink.records, cases):
        rebuilt = converter(record)
        assert rebuilt is not None
        assert rebuilt.trace_id == "trace-abc"
        assert rebuilt.observation_id == "obs-123"
        assert rebuilt.span_name == case.span_name
        # case_id convention used by the dataset records
        assert f"{rebuilt.trace_id}:{rebuilt.observation_id}" == "trace-abc:obs-123"
