"""The <2-item retrieval-judge short-circuit returns efficiency=5 without an LLM judging it.
These rows were silently pooled into judged averages (arm-asymmetrically), so they must be
TAGGED (is_fallback) and EXCLUDED from the aggregates, with a fallback count reported instead.
"""

from __future__ import annotations

import io
import unittest
from contextlib import redirect_stdout

from evaluation.src.experiments.retrieval import summarize_records
from evaluation.src.judges.retrieval import minimal_retrieval_scores, run_retrieval_judge


class MinimalScoresTests(unittest.TestCase):
    def test_short_circuit_rows_are_tagged_fallback(self) -> None:
        for count in (0, 1):
            scores = run_retrieval_judge(
                item_type="observations",
                situations=["s"],
                items_formatted="",
                item_count=count,
                model="unused",  # never reached: item_count < 2 short-circuits before any LLM
            )
            self.assertIsNotNone(scores)
            self.assertTrue(scores.is_fallback)
            self.assertEqual(scores.efficiency, 5)  # the placeholder that used to inflate averages

    def test_real_scores_default_not_fallback(self) -> None:
        self.assertFalse(
            minimal_retrieval_scores(1).model_copy(update={"is_fallback": False}).is_fallback
        )


class SummarizeExclusionTests(unittest.TestCase):
    def _row(self, *, efficiency: int, is_fallback: bool, redundancy: float | None) -> dict:
        return {
            "snapshot": "snap",
            "pipeline": "pipe",
            "item_type": "observations",
            "retrieved_count": 1 if is_fallback else 5,
            "redundancy_ratio": redundancy,
            "retrieval_quality": {
                "relevance": 1 if is_fallback else 4,
                "efficiency": efficiency,
                "unique_lessons": 1 if is_fallback else 4,
                "is_fallback": is_fallback,
            },
        }

    def test_fallback_rows_excluded_from_averages_and_counted(self) -> None:
        rows = [
            self._row(efficiency=5, is_fallback=True, redundancy=None),   # excluded
            self._row(efficiency=5, is_fallback=True, redundancy=None),   # excluded
            self._row(efficiency=2, is_fallback=False, redundancy=0.5),   # counted
        ]
        buf = io.StringIO()
        with redirect_stdout(buf):
            summarize_records(rows)
        out = buf.getvalue()
        # Two fallback rows reported, and the efficiency average is the single real row's 2.00,
        # NOT (5+5+2)/3=4.00 that the old pooled logic produced.
        self.assertIn("fallback_rows=2", out)
        self.assertIn("judged=1", out)
        self.assertIn("avg_efficiency=2.00", out)


if __name__ == "__main__":
    unittest.main()
