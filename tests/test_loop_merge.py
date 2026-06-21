"""Guard the parallel-games freeze-old merge key-diff (collect_new_obs / merge_new_obs append side).
The LLM dedup half (run_batch_memory_dedup) is exercised in test_batch_dedup; here we test that the
merge collects exactly each game's NEW obs (keys absent from the snapshot), de-duplicated by key across
games, and appends them without duplicating the snapshot."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from evaluation.src.loop.merge import collect_new_obs, merge_new_obs

_NS = "observations/villager/day_vote"


def _write_store(d: Path, recs: list) -> None:
    d.mkdir(parents=True, exist_ok=True)
    (d / "observations.json").write_text(json.dumps({"namespaces": {_NS: recs}}))
    (d / "strategy_points.json").write_text(json.dumps({"namespaces": {}}))


def _rec(key: str) -> dict:
    return {"key": key, "value": {"observation_count": 1}}


class CollectNewObsTests(unittest.TestCase):
    def test_collects_new_keys_deduped_across_games(self) -> None:
        with tempfile.TemporaryDirectory() as t:
            snap, g1, g2 = Path(t) / "snap", Path(t) / "g1", Path(t) / "g2"
            _write_store(snap, [_rec("o1")])                       # gen-start snapshot
            _write_store(g1, [_rec("o1"), _rec("o2")])             # g1 added o2
            _write_store(g2, [_rec("o1"), _rec("o2"), _rec("o3")])  # g2 added o2 (dup key) + o3
            new = collect_new_obs(snap, [g1, g2])
            self.assertEqual(sorted(r["key"] for r in new[_NS]), ["o2", "o3"])  # o2 taken once

    def test_no_new_obs_when_games_add_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as t:
            snap, g1 = Path(t) / "snap", Path(t) / "g1"
            _write_store(snap, [_rec("o1")])
            _write_store(g1, [_rec("o1")])
            self.assertEqual(collect_new_obs(snap, [g1]), {})


class MergeNewObsTests(unittest.TestCase):
    def test_appends_new_without_duplicating_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as t:
            snap, g1, store = Path(t) / "snap", Path(t) / "g1", Path(t) / "store"
            _write_store(snap, [_rec("o1")])
            _write_store(g1, [_rec("o1"), _rec("o2")])
            _write_store(store, [_rec("o1")])                      # store == snapshot at call time
            res = merge_new_obs(store, snap, [g1], dedup=False)    # dedup off = pure append (offline)
            self.assertEqual(res, {"new_obs": 1, "deduped": False})
            final = json.loads((store / "observations.json").read_text())["namespaces"][_NS]
            self.assertEqual(sorted(r["key"] for r in final), ["o1", "o2"])


if __name__ == "__main__":
    unittest.main()
