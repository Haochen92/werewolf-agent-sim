"""An auto-DISCARD credits the entry that matched, not the top situation hit.

The store search ranks candidates by SITUATION alone, but the prefilter discards on the best
CONTENT (observation) or ACTION (strategy point) similarity over all of them. When the two
disagree, the count bump used to land on the top situation hit, an entry the new item was
never a duplicate of, while the real duplicate stayed at its old count.

Embeddings are stubbed the way ``test_dedup_thresholds`` does it: each candidate's vector is
``[sim]`` and cosine returns that value, so the test picks which candidate crosses the line.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

import Agents.memory.deduplication as dedup
from Agents.memory.deduplication.schemas import DedupAction


class _FakeStore:
    """Returns fixed situation-search hits and records every write."""

    def __init__(self, hits):
        self.hits = hits
        self.puts = {}

    def search(self, namespace, *, query, limit):
        return self.hits

    def put(self, namespace, key, value):
        self.puts[key] = value


def _hit(key, situation_score, **value):
    value = {"observation_count": 1, "last_observed": "2026-01-01T00:00:00", "situation": key, **value}
    return SimpleNamespace(key=key, score=situation_score, value=value)


def _patch_content_sims(monkeypatch, sims):
    vecs = [[0.0]] + [[s] for s in sims]
    monkeypatch.setattr(dedup.prefilter, "embed_texts", lambda texts, model: vecs)
    monkeypatch.setattr(dedup.prefilter, "cosine_similarity", lambda a, b: b[0])


def test_observation_discard_bumps_the_content_duplicate(monkeypatch):
    # "situation_top" leads the situation search but is not a content duplicate;
    # "content_dup" ranks second and is the one above the discard line.
    hits = [_hit("situation_top", 0.95, approach="a1", outcome="o1"),
            _hit("content_dup", 0.90, approach="a2", outcome="o2")]
    _patch_content_sims(monkeypatch, [dedup.OBS_CONTENT_KEEP_THRESHOLD + 0.001,
                                      dedup.OBS_CONTENT_DISCARD_THRESHOLD + 0.01])
    store = _FakeStore(hits)
    observation = SimpleNamespace(perspective="villager", action_phase="day_vote",
                                  composed_situation="s", approach="a", outcome="o")

    result = dedup.dedup_single_observation(store, observation, game_id="g1")

    assert result.action == DedupAction.DISCARD and result.auto
    assert list(store.puts) == ["content_dup"]
    assert store.puts["content_dup"]["observation_count"] == 2


def test_strategy_point_discard_bumps_the_action_duplicate(monkeypatch):
    hits = [_hit("situation_top", 0.95, action="a1"),
            _hit("action_dup", 0.90, action="a2")]
    _patch_content_sims(monkeypatch, [dedup.SP_ACTION_KEEP_THRESHOLD + 0.001,
                                      dedup.SP_ACTION_DISCARD_THRESHOLD + 0.01])
    store = _FakeStore(hits)
    point = SimpleNamespace(perspective="villager", action_phase="day_vote",
                            composed_situation="s", action="a")

    result = dedup.dedup_single_strategy_point(store, point, game_id="g1")

    assert result.action == DedupAction.DISCARD and result.auto
    assert list(store.puts) == ["action_dup"]
    assert store.puts["action_dup"]["observation_count"] == 2


@pytest.mark.parametrize("sims,expected_index", [
    ([0.5, 0.99, 0.7], 1),
    ([0.99, 0.5], 0),
])
def test_prefilter_returns_the_max_scoring_candidate(monkeypatch, sims, expected_index):
    _patch_content_sims(monkeypatch, sims)
    candidates = [SimpleNamespace(value={"situation": f"s{i}", "approach": "", "outcome": ""})
                  for i in range(len(sims))]
    observation = SimpleNamespace(composed_situation="s", approach="a", outcome="o")

    _, _, best_match = dedup._embedding_prefilter_observation(observation, candidates)

    assert best_match is candidates[expected_index]
