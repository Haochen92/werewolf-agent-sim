"""Guard tests for the compounding loop's (b) consolidation decay levers:
  - scope-aware SP eviction (§10b applicability funnel): override-dominant evicts, not_relevant spared;
  - observation decay by age x frequency (old AND rare drop; old-but-recurring + recent kept).
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from evaluation.src.loop import consolidate as con
from evaluation.src.loop.config import LoopConfig
from evaluation.src.loop.consolidate import _evict_ok, _synth_cluster, evict_observations, prune_and_evict


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

    def test_proven_sp_exemption_protects_thin_positive(self) -> None:
        # edge 1: a rare-but-proven SP (positive lift, only 4 follows) survives even an AGGRESSIVE prune
        # (tau>=0, min_follow lowered) that would otherwise catch it — positive evidence beats deletion.
        cfg = LoopConfig(prune_tau=0.5, prune_min_follow=2, protect_min_follow=2)
        ns = {"strategy_points/villager/day_vote": [
            _sp(follow=4, pos=2, neg=1, retrieved=20, action="rare_good"),   # lift +0.11 -> protected
        ]}
        stats = prune_and_evict(ns, {"villager/day_vote": [0.0, 50]}, cfg)
        self.assertEqual(stats["pruned"], 0)
        self.assertIn("rare_good", [r["value"]["action"] for r in ns["strategy_points/villager/day_vote"]])

    def test_exemption_below_min_follow_not_protected(self) -> None:
        # a single-follow positive SP is below protect_min_follow=2 -> NOT exempt (one follow is noise)
        cfg = LoopConfig(prune_tau=0.5, prune_min_follow=1, protect_min_follow=2)
        ns = {"strategy_points/villager/day_vote": [_sp(follow=1, pos=1, neg=0, action="one_follow")]}
        stats = prune_and_evict(ns, {"villager/day_vote": [0.0, 50]}, cfg)
        self.assertEqual(stats["pruned"], 1)


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


class CostGuardTests(unittest.TestCase):
    """Pro-2.5 cost guard: every paid model slot the loop pins must be the cheap tier, never gemini-2.5-pro.
    Regression guard for the $55 run (in-process synth/tagger + dedup fallback silently hitting pro)."""

    def test_env_pins_no_pro_2_5(self) -> None:
        env = LoopConfig().env()
        self.assertNotIn("gemini-2.5-pro", env.values())
        self.assertEqual(env["GOOGLE_GENAI_PRO_MODEL"], "gemini-3.1-flash-lite")
        self.assertEqual(env["GOOGLE_GENAI_PRO_BACKUP_MODEL"], "gemini-3.1-flash-lite")
        self.assertEqual(env["MEMORY_BATCH_DEDUP_MODEL"], "gemini-3.1-flash-lite")

    def test_dedup_model_default_is_cheap(self) -> None:
        self.assertNotEqual(LoopConfig().dedup_model, "gemini-2.5-pro")


class NewClustersOnlySynthTests(unittest.TestCase):
    """The new-clusters-only gate: re-synthesize a cluster only when it carries a NEW obs (or the cell is
    depleted / we can't filter). Stops the per-cell SP compounding (~6x/run) at the source."""

    LOOKBACK = 6  # synth_lookback = current_gen - synth_every_k_gens => obs first-seen at gen 7+ are NEW

    def test_cluster_with_new_obs_synthesized(self) -> None:
        gen_map = {"a": 2, "b": 7}  # b is new (>6)
        self.assertTrue(_synth_cluster(["a", "b"], False, gen_map, self.LOOKBACK, True))

    def test_cluster_all_old_skipped(self) -> None:
        gen_map = {"a": 2, "b": 5}  # both old (<=6) -> already distilled -> skip
        self.assertFalse(_synth_cluster(["a", "b"], False, gen_map, self.LOOKBACK, True))

    def test_empty_cluster_skipped(self) -> None:
        self.assertFalse(_synth_cluster([], False, {"a": 9}, self.LOOKBACK, True))

    def test_depleted_cell_replenishes_from_old(self) -> None:
        # a cell emptied by prune/evict re-synthesizes its old clusters to refill (bypasses the filter)
        gen_map = {"a": 2, "b": 5}
        self.assertTrue(_synth_cluster(["a", "b"], True, gen_map, self.LOOKBACK, True))

    def test_non_incremental_full_resynth(self) -> None:
        self.assertTrue(_synth_cluster(["a"], False, {"a": 0}, self.LOOKBACK, False))

    def test_no_gen_map_fallback_to_all(self) -> None:
        self.assertTrue(_synth_cluster(["a"], False, None, None, True))


class SpDedupGatingTests(unittest.TestCase):
    def _store(self, d: Path) -> Path:
        (d / "strategy_points.json").write_text(json.dumps({"namespaces": {}}))
        (d / "observations.json").write_text(json.dumps({"namespaces": {}}))
        return d

    def test_sp_dedup_runs_only_when_synthesis_added(self) -> None:
        # synth_every_k_gens=1 isolates the sp_dedup-on-added logic from the synth-cadence gate
        with tempfile.TemporaryDirectory() as t:
            store = self._store(Path(t))
            with patch.object(con, "prune_and_evict", return_value={}), \
                 patch.object(con, "evict_observations", return_value={}), \
                 patch.object(con, "synthesize", return_value=({"added": 2}, {})), \
                 patch.object(con, "_dedup_strategy_points", return_value={"ran": True}) as md:
                con.consolidate(store, LoopConfig(sp_dedup=True, synth_every_k_gens=1),
                                current_gen=1, obs_gen_map={})
            md.assert_called_once()

    def test_sp_dedup_skipped_when_nothing_synthesized(self) -> None:
        with tempfile.TemporaryDirectory() as t:
            store = self._store(Path(t))
            with patch.object(con, "prune_and_evict", return_value={}), \
                 patch.object(con, "evict_observations", return_value={}), \
                 patch.object(con, "synthesize", return_value=({"added": 0}, {})), \
                 patch.object(con, "_dedup_strategy_points", return_value={"ran": True}) as md:
                con.consolidate(store, LoopConfig(sp_dedup=True, synth_every_k_gens=1),
                                current_gen=1, obs_gen_map={})
            md.assert_not_called()

    def test_synthesis_skipped_on_non_k_generation(self) -> None:
        # synth_every_k_gens=2 -> gen 1 is a cull-only generation (no synthesis, no SP-dedup)
        with tempfile.TemporaryDirectory() as t:
            store = self._store(Path(t))
            with patch.object(con, "prune_and_evict", return_value={}), \
                 patch.object(con, "evict_observations", return_value={}), \
                 patch.object(con, "synthesize", return_value=({"added": 9}, {})) as ms, \
                 patch.object(con, "_dedup_strategy_points", return_value={"ran": True}) as md:
                con.consolidate(store, LoopConfig(sp_dedup=True, synth_every_k_gens=2),
                                current_gen=1, obs_gen_map={})
            ms.assert_not_called()   # synth skipped on gen 1 (1 % 2 != 0)
            md.assert_not_called()


if __name__ == "__main__":
    unittest.main()
