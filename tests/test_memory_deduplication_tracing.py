import unittest
from unittest.mock import Mock, patch

from Agents.memory_deduplication import (
    DedupAction,
    DedupResult,
    _emit_dedup_span,
)


class FakeObservationContext:
    def __init__(self) -> None:
        self.span = Mock()

    def __enter__(self):
        return self.span

    def __exit__(self, exc_type, exc, tb):
        return False


class DedupTracingTests(unittest.TestCase):
    def test_emit_dedup_span_updates_entered_span(self):
        context = FakeObservationContext()
        fake_langfuse = Mock()
        fake_langfuse.start_as_current_observation.return_value = context

        with patch("Agents.memory_deduplication.langfuse", fake_langfuse):
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


if __name__ == "__main__":
    unittest.main()
