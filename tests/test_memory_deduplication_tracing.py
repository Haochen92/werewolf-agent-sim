import unittest
from unittest.mock import Mock, patch

from Agents.memory.deduplication import (
    DedupAction,
    DedupResult,
    _emit_dedup_span,
)
from Agents.observability import EvalCaseSink


class FakeObservationContext:
    def __init__(self) -> None:
        self.span = Mock()
        self.span.trace_id = "trace-1"
        self.span.id = "obs-1"

    def __enter__(self):
        return self.span

    def __exit__(self, exc_type, exc, tb):
        return False


class DedupTracingTests(unittest.TestCase):
    def test_emit_dedup_span_updates_entered_span(self):
        context = FakeObservationContext()
        fake_langfuse = Mock()
        fake_langfuse.start_as_current_observation.return_value = context

        with patch("Agents.memory.deduplication.pipeline.langfuse", fake_langfuse):
            _emit_dedup_span(
                item_type="strategy_point",
                perspective="villager",
                action_phase="day_discussion",
                index=1,
                game_id="game-1",
                new_entry={"situation": "s", "action": "a"},
                result=DedupResult(action=DedupAction.KEEP, auto=True),
            )

        fake_langfuse.start_as_current_observation.assert_called_once()
        context.span.update.assert_called_once()

    def test_emit_dedup_span_tees_case_to_sink(self):
        context = FakeObservationContext()
        fake_langfuse = Mock()
        fake_langfuse.start_as_current_observation.return_value = context
        sink = EvalCaseSink()

        with patch("Agents.memory.deduplication.pipeline.langfuse", fake_langfuse):
            _emit_dedup_span(
                item_type="strategy_point",
                perspective="villager",
                action_phase="day_discussion",
                index=1,
                game_id="game-1",
                new_entry={"situation": "s", "action": "a"},
                result=DedupResult(action=DedupAction.KEEP, auto=True),
                sink=sink,
            )

        [record] = sink.records
        self.assertEqual(record["kind"], "dedup")
        self.assertEqual(record["trace_id"], "trace-1")
        self.assertEqual(record["id"], "obs-1")
        case_payload = record["output"]["dedup_case"]
        self.assertEqual(case_payload["decision"], DedupAction.KEEP.value)
        self.assertEqual(case_payload["game_id"], "game-1")
        # local record holds the same dump the Langfuse span got
        (_, kwargs) = context.span.update.call_args
        self.assertEqual(kwargs["output"]["dedup_case"], case_payload)


if __name__ == "__main__":
    unittest.main()
