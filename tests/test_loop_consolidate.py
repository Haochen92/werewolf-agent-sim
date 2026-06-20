"""Guard tests for the compounding loop's (b) consolidation decay levers:
  - scope-aware SP eviction (§10b applicability funnel): override-dominant evicts, not_relevant spared;
  - observation decay by age x frequency (old AND rare drop; old-but-recurring + recent kept).
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from evaluation.src.loop.config import LoopConfig
from evaluation.src.loop.consolidate import _evict_ok, evict_observations, prune_and_evict


def _sp(follow=0, retrieved=0, pos=0, neg=0, override=0, not_relevant=0, action="x"):
    return {"value": {"follow_count": follow, "retrieved_count": retrieved, "positive_count": pos,
                      "negative_count": neg, "override_count": override,
                      "not_relevant_count": not_relevant, "action": action}}


class ScopeAwareEvictTests(unittest.TestCase):
    def test_override_dominant_is_evictable(self) -> None:
        self.assertTrue(_evict_ok({"override_count": 9, "not_relevant_count": 1}, LoopConfig()))

    def test_not_relevant_dominant_is_spared(self) -> None:
        # the situation didn't hold = a retrieval/scoping miss, NOT bad content
        self.assertFalse(_evict_ok({"override_count": 1, "not_relevant_count": 9}, LoopConfig()))

    def test_no_verdict_signal_is_spared(self) -> None:
        # retrieved a lot but no override/not_relevant = coverage gap, not evidence of badness
        self.assertFalse(_evict_ok({"override_count": 0, "not_relevant_count": 0}, LoopConfig()))

    def test_legacy_blunt_evict_ignores_scope(self) -> None:
        cfg = LoopConfig(evict_require_override=False)
        self.assertTrue(_evict_ok({"override_count": 0, "not_relevant_count": 9}, cfg))

    def test_prune_and_evict_partition(self) -> None:
        ns = {"strategy_points/serial_killer/day_vote": [
            _sp(follow=40, pos=2, neg=30, retrieved=50, action="harmful->prune"),          # lift<<tau
            _sp(follow=0, retrieved=12, override=9, not_relevant=1, action="rejected->evict"),
            _sp(follow=0, retrieved=12, override=0, not_relevant=11, action="mismatch->spare"),
            _sp(follow=25, pos=20, neg=1, retrieved=30, action="winner->keep"),
        ]}
        base = {"serial_killer/day_vote": [-0.1, 100]}
        stats = prune_and_evict(ns, base, LoopConfig())
        self.assertEqual(stats["pruned"], 1)
        self.assertEqual(stats["evicted"], 1)
        self.assertEqual(stats["spared"], 1)
        survivors = [r["value"]["action"] for r in ns["strategy_points/serial_killer/day_vote"]]
        self.assertIn("winner->keep", survivors)
        self.assertIn("mismatch->spare", survivors)        # spared SP stays in the store
        self.assertNotIn("harmful->prune", survivors)
        self.assertNotIn("rejected->evict", survivors)

    def test_positive_lift_never_pruned(self) -> None:
        ns = {"strategy_points/villager/day_vote": [_sp(follow=20, pos=18, neg=1, action="good")]}
        stats = prune_and_evict(ns, {"villager/day_vote": [0.0, 50]}, LoopConfig())
        self.assertEqual(stats["pruned"], 0)
        self.assertEqual(stats["kept"], 1)


class ObservationDecayTests(unittest.TestCase):
    def _run(self, recs, gen_map, current_gen, cfg=None):
        cfg = cfg or LoopConfig()
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "observations.json"
            p.write_text(json.dumps({"namespaces": {"observations/villager/day_vote": recs}}))
            stats = evict_observations(p, gen_map, current_gen, cfg)
            survived = json.loads(p.read_text())["namespaces"]["observations/villager/day_vote"]
            return stats, [r["key"] for r in survived]

    def test_old_and_rare_dropped_others_kept(self) -> None:
        recs = [
            {"key": "old_rare", "value": {"observation_count": 1}},      # drop: old + rare
            {"key": "old_frequent", "value": {"observation_count": 7}},  # keep: recurring lesson
            {"key": "recent_rare", "value": {"observation_count": 1}},   # keep: recent
        ]
        gen_map = {"old_rare": 0, "old_frequent": 0, "recent_rare": 5}
        stats, survived = self._run(recs, gen_map, current_gen=5)  # min_age=2 -> gen<=3 is old
        self.assertEqual(stats["obs_dropped"], 1)
        self.assertEqual(sorted(survived), ["old_frequent", "recent_rare"])

    def test_unmapped_key_treated_as_oldest(self) -> None:
        # a key missing from the sidecar defaults to generation 0 (oldest) -> evictable if rare
        recs = [{"key": "ghost", "value": {"observation_count": 1}}]
        stats, survived = self._run(recs, {}, current_gen=5)
        self.assertEqual(stats["obs_dropped"], 1)
        self.assertEqual(survived, [])

    def test_disabled_when_count_threshold_high(self) -> None:
        recs = [{"key": "old_rare", "value": {"observation_count": 1}}]
        cfg = LoopConfig(obs_evict_max_count=0)  # nothing is "rare" -> keep everything
        stats, survived = self._run(recs, {"old_rare": 0}, current_gen=9, cfg=cfg)
        self.assertEqual(stats["obs_dropped"], 0)
        self.assertEqual(survived, ["old_rare"])


if __name__ == "__main__":
    unittest.main()
