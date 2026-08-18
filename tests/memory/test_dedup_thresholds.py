"""Unit tests for the dedup embedding pre-filter thresholds (Agents/memory_deduplication.py).

These thresholds silently shape what ends up IN v5: over-discard -> thin memory,
under-discard -> noise. No test currently pins them, so an embedding change (or a
fat-fingered constant) would shift the keep/discard boundary invisibly. We drive
the two ``_embedding_prefilter_*`` functions at and around each cutoff.

Determinism: ``embed_texts``/``cosine_similarity`` are monkeypatched so each
candidate's similarity is exactly the value we pass — embeddings are represented
as single-element vectors ``[sim]`` and cosine just returns the candidate's value.
This isolates the threshold BRANCHING from real embedding/cosine internals (those
are a separate concern; what's eval-critical here is which side of the cutoff fires).
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

import Agents.memory.deduplication as dedup


def patch_sims(monkeypatch, sims):
    """Make the prefilter see exactly ``sims`` as per-candidate similarities."""
    vecs = [[0.0]] + [[s] for s in sims]
    monkeypatch.setattr(dedup.prefilter, "embed_texts", lambda texts, model: vecs)
    monkeypatch.setattr(dedup.prefilter, "cosine_similarity", lambda a, b: b[0])


def sp_candidates(n):
    return [SimpleNamespace(value={"action": f"a{i}"}) for i in range(n)]


def obs_candidates(n):
    return [
        SimpleNamespace(value={"situation": f"s{i}", "approach": f"a{i}", "outcome": f"o{i}"})
        for i in range(n)
    ]


def sp(monkeypatch, sims):
    patch_sims(monkeypatch, sims)
    point = SimpleNamespace(action="new action")
    return dedup._embedding_prefilter_strategy_point(point, sp_candidates(len(sims)))


def obs(monkeypatch, sims):
    patch_sims(monkeypatch, sims)
    observation = SimpleNamespace(composed_situation="s", approach="a", outcome="o")
    return dedup._embedding_prefilter_observation(observation, obs_candidates(len(sims)))


# --- strategy point: discard >= 0.93, keep < 0.81, else None (->LLM) --------

@pytest.mark.parametrize("sim,expected", [
    (0.95, "discard"),
    (0.93, "discard"),   # boundary is inclusive (>=)
    (0.92, None),        # the LLM-decides band
    (0.81, None),        # boundary is exclusive on the keep side (< 0.81)
    (0.8099, "keep"),
    (0.50, "keep"),
])
def test_sp_single_candidate_thresholds(monkeypatch, sim, expected):
    decision, _ = sp(monkeypatch, [sim])
    assert decision == expected


def test_sp_uses_max_over_candidates(monkeypatch):
    # max(0.5, 0.94) = 0.94 >= 0.93 -> discard.
    decision, scores = sp(monkeypatch, [0.5, 0.94])
    assert decision == "discard"
    assert scores["max_action_sim"] == 0.94


def test_sp_all_low_keeps(monkeypatch):
    decision, _ = sp(monkeypatch, [0.5, 0.70])
    assert decision == "keep"


# --- observation: discard >= 0.96, keep < 0.935, else None ------------------

@pytest.mark.parametrize("sim,expected", [
    (0.97, "discard"),
    (0.96, "discard"),   # inclusive
    (0.95, None),        # the LLM-decides band
    (0.935, None),       # exclusive on the keep side (< 0.935)
    (0.934, "keep"),
    (0.50, "keep"),
])
def test_obs_single_candidate_thresholds(monkeypatch, sim, expected):
    decision, _ = obs(monkeypatch, [sim])
    assert decision == expected


def test_obs_uses_max_over_candidates():
    decision, scores = obs(pytest.MonkeyPatch(), [0.5, 0.965])
    assert decision == "discard"
    assert scores["max_content_sim"] == 0.965


# --- fall-through safety: no candidates / embedding failure -> None ----------

def test_sp_no_candidates_returns_none(monkeypatch):
    decision, _ = sp(monkeypatch, [])  # only the new vec -> len(vecs) < 2
    assert decision is None


def test_sp_embedding_failure_falls_through_to_llm(monkeypatch):
    def boom(texts, model):
        raise RuntimeError("embedding backend down")

    monkeypatch.setattr(dedup.prefilter, "embed_texts", boom)
    point = SimpleNamespace(action="x")
    decision, scores = dedup._embedding_prefilter_strategy_point(point, sp_candidates(1))
    assert decision is None  # never auto-discards on an embedding error
    assert scores == {}


def test_obs_embedding_failure_falls_through_to_llm(monkeypatch):
    def boom(texts, model):
        raise RuntimeError("embedding backend down")

    monkeypatch.setattr(dedup.prefilter, "embed_texts", boom)
    observation = SimpleNamespace(composed_situation="s", approach="a", outcome="o")
    decision, scores = dedup._embedding_prefilter_observation(observation, obs_candidates(1))
    assert decision is None
    assert scores == {}
