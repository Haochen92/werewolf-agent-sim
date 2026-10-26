"""The learning tick's dedup judges only what is new.

The tick builds its working folder from the database each time, so the folder carries no last-dedup
marker; without the keys named explicitly, an incremental dedup judged the whole store, old against
old, which the freeze-old guard exists to prevent. Both callers now name their new keys."""

import json
from pathlib import Path

from Agents.memory.batch_deduplication.config import BatchDedupRunConfig
from Agents.memory.batch_deduplication.incremental import _write_last_dedup_at
from Agents.memory.batch_deduplication.orchestration import incremental_new_keys
from Agents.memory.consolidation import store_ops
from Agents.memory.consolidation.config import TickConfig


def _obs_store(folder: Path, keys: list[str]) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    recs = [{"key": k, "created_at": "2026-01-01T00:00:00+00:00", "value": {}} for k in keys]
    (folder / "observations.json").write_text(json.dumps({"namespaces": {"observations/villager/day_vote": recs}}))
    return folder


def test_named_keys_win_over_a_missing_marker(tmp_path):
    cfg = BatchDedupRunConfig(seed_store_dir=tmp_path, dump_store_dir=tmp_path, incremental=True,
                              new_keys={"n1", "n2"})
    assert incremental_new_keys(cfg) == {"n1", "n2"}


def test_named_keys_win_over_a_marker_too(tmp_path):
    _obs_store(tmp_path, ["old1"])
    _write_last_dedup_at(tmp_path)
    cfg = BatchDedupRunConfig(seed_store_dir=tmp_path, dump_store_dir=tmp_path, incremental=True,
                              new_keys=set())
    assert incremental_new_keys(cfg) == set()


def test_without_named_keys_a_folder_without_a_marker_is_judged_whole(tmp_path):
    cfg = BatchDedupRunConfig(seed_store_dir=tmp_path, dump_store_dir=tmp_path, incremental=True)
    assert incremental_new_keys(cfg) is None


def test_a_system_wide_run_judges_everything(tmp_path):
    cfg = BatchDedupRunConfig(seed_store_dir=tmp_path, dump_store_dir=tmp_path, new_keys={"n1"})
    assert incremental_new_keys(cfg) is None


def test_the_fold_names_the_observations_it_appended(tmp_path, monkeypatch):
    from Agents.memory.batch_deduplication import orchestration
    from Agents.memory.consolidation.obs_fold import merge_new_obs

    seen = {}
    monkeypatch.setattr(orchestration, "run_batch_memory_dedup", lambda cfg: seen.setdefault("cfg", cfg))
    store = _obs_store(tmp_path / "store", ["old1", "old2"])
    snapshot = _obs_store(tmp_path / "snap", ["old1", "old2"])
    game = _obs_store(tmp_path / "game", ["old1", "new1", "new2"])
    res = merge_new_obs(store, snapshot, [game])
    assert res["new_obs"] == 2
    assert seen["cfg"].incremental and seen["cfg"].new_keys == {"new1", "new2"}


def test_the_lesson_dedup_judges_only_the_lessons_synthesis_wrote(tmp_path, monkeypatch):
    (tmp_path / "observations.json").write_text(json.dumps({"namespaces": {}}))
    (tmp_path / "strategy_points.json").write_text(json.dumps({"namespaces": {}}))
    monkeypatch.setattr(store_ops, "synthesize",
                        lambda *a, **k: ({"added": 2, "added_keys": ["sp_a", "sp_b"]}, {}))
    seen = {}
    monkeypatch.setattr(store_ops, "_dedup_strategy_points",
                        lambda store_dir, model, new_keys=None: seen.setdefault("keys", new_keys) and {})
    stats = store_ops.consolidate(tmp_path, TickConfig(prune=False, evict=False, evict_observations=False))
    assert seen["keys"] == {"sp_a", "sp_b"}
    assert "added_keys" not in stats["synth"]  # the keys feed the dedup, not the tick's stats
