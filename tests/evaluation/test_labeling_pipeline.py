"""Smoke tests for the assembled labeling pipeline (pipeline.stage_consolidate).

The LABEL stage needs live models, so these exercise the consolidation — the
integration that was never run before (engine output → vote → consensus + ties).
They prove the two composition gaps that blocked the old `merger` are fixed:
votes come straight off the engine entry's per-model `model_scores` (multi-model
single file), keyed by the entry's own `(case_index, key)` (so dedup's
`case_index`-only keys work), and human label files fuse as extra voters.
"""
from __future__ import annotations

import json
from pathlib import Path

from evaluation.src.labeling.config import LabelingPipelineConfig
from evaluation.src.labeling.pipeline import _load_voters, stage_consolidate

# 3-model panel; case0 majority-D, case1 unanimous-K, case2 deadlocked tie (one None).
ENGINE_SCORES = {
    "models": ["m1", "m2", "m3"],
    "total_items": 3,
    "results": [
        {"case_index": 0, "key": "0", "item_type": "observation",
         "model_scores": {"m1": "D", "m2": "D", "m3": "K"},
         "model_details": {"m1": {"reasoning": "dup", "duplicate_of_candidate": 1}}},
        {"case_index": 1, "key": "1", "item_type": "strategy_point",
         "model_scores": {"m1": "K", "m2": "K", "m3": "K"}},
        {"case_index": 2, "key": "2", "item_type": "observation",
         "model_scores": {"m1": "D", "m2": "K", "m3": None}},
    ],
}


def _config(tmp: Path, manual: list[Path] | None = None) -> LabelingPipelineConfig:
    (tmp / "model_scores.json").write_text(json.dumps(ENGINE_SCORES))
    return LabelingPipelineConfig(
        candidates_path=tmp / "model_scores.json",  # unused by consolidate
        adapter="dedup",
        output_dir=tmp,
        manual_sources=manual or [],
    )


def test_load_voters_expands_engine_models():
    voters, item_type, details = _load_voters_from(ENGINE_SCORES)
    assert set(voters) == {"m1", "m2", "m3"}  # each model is its own voter
    assert voters["m1"][(0, "0")] == "D"
    assert item_type[(1, "1")] == "strategy_point"
    assert details[(0, "0")]["m1"]["duplicate_of_candidate"] == 1


def test_consolidate_votes_off_engine_scores(tmp_path):
    config = _config(tmp_path)
    out = stage_consolidate(config)
    data = json.loads(out.read_text())
    by_case = {(r["case_index"]): r for r in data["results"]}

    assert by_case[0]["label"] == "D" and by_case[0]["confidence"] == "majority"
    assert by_case[1]["label"] == "K" and by_case[1]["confidence"] == "unanimous"
    assert by_case[2]["label"] is None and by_case[2]["confidence"] == "tie"
    # audit detail carried through from the engine file
    assert by_case[0]["model_details"]["m1"]["duplicate_of_candidate"] == 1
    # the tie is written out for human resolution
    ties = json.loads(config.ties_path.read_text())
    assert [t["case_index"] for t in ties] == [2]


def test_human_source_breaks_the_tie(tmp_path):
    manual = tmp_path / "human.json"
    manual.write_text(json.dumps(
        {"labeler": "human", "labels": [{"case_index": 2, "key": "2", "label": "D"}]}
    ))
    config = _config(tmp_path, manual=[manual])
    out = stage_consolidate(config)
    data = json.loads(out.read_text())
    case2 = next(r for r in data["results"] if r["case_index"] == 2)

    assert "human" in data["voters"]
    # m1=D, m2=K, m3=None, human=D → 2:1 majority D (previously a tie)
    assert case2["label"] == "D" and case2["confidence"] == "majority"
    assert not config.ties_path.exists() or json.loads(config.ties_path.read_text()) == []


def _load_voters_from(payload: dict):
    import tempfile

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(payload, f)
        path = Path(f.name)
    try:
        return _load_voters(path)
    finally:
        path.unlink()
