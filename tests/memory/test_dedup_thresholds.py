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
from Agents.llm_factory.embeddings import SIMILARITY_THRESHOLDS

# The values the prefilter runs on, per embedding model. Pinned here so a threshold never moves
# by accident; the boundary tests below read the configured model's values.
PINNED = {
    "gemini-embedding-2": {"sp_action_discard": 0.93, "sp_action_keep": 0.81,
                           "obs_content_discard": 0.96, "obs_content_keep": 0.935},
    "qwen/qwen3-embedding-8b": {"sp_action_discard": 0.88, "sp_action_keep": 0.61,
                                "obs_content_discard": 0.94, "obs_content_keep": 0.72},
}
SP_D, SP_K = dedup.SP_ACTION_DISCARD_THRESHOLD, dedup.SP_ACTION_KEEP_THRESHOLD
OBS_D, OBS_K = dedup.OBS_CONTENT_DISCARD_THRESHOLD, dedup.OBS_CONTENT_KEEP_THRESHOLD


@pytest.mark.parametrize("model", sorted(PINNED))
def test_the_prefilter_thresholds_are_pinned(model):
    assert {k: SIMILARITY_THRESHOLDS[model][k] for k in PINNED[model]} == PINNED[model]


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


# --- strategy point: discard >= SP_D, keep < SP_K, else None (->LLM) --------

@pytest.mark.parametrize("sim,expected", [
    (SP_D + 0.02, "discard"),
    (SP_D, "discard"),          # boundary is inclusive (>=)
    (SP_D - 0.01, None),        # the LLM-decides band
    (SP_K, None),               # boundary is exclusive on the keep side
    (SP_K - 0.0001, "keep"),
    (SP_K - 0.10, "keep"),
])
def test_sp_single_candidate_thresholds(monkeypatch, sim, expected):
    decision, _ = sp(monkeypatch, [sim])
    assert decision == expected


def test_sp_uses_max_over_candidates(monkeypatch):
    # the max over candidates decides: one low, one above the discard line -> discard.
    decision, scores = sp(monkeypatch, [SP_K - 0.10, SP_D + 0.01])
    assert decision == "discard"
    assert scores["max_action_sim"] == round(SP_D + 0.01, 4)


def test_sp_all_low_keeps(monkeypatch):
    decision, _ = sp(monkeypatch, [SP_K - 0.10, SP_K - 0.05])
    assert decision == "keep"


# --- observation: discard >= OBS_D, keep < OBS_K, else None ------------------

@pytest.mark.parametrize("sim,expected", [
    (OBS_D + 0.01, "discard"),
    (OBS_D, "discard"),         # inclusive
    (OBS_D - 0.01, None),       # the LLM-decides band
    (OBS_K, None),              # exclusive on the keep side
    (OBS_K - 0.001, "keep"),
    (OBS_K - 0.10, "keep"),
])
def test_obs_single_candidate_thresholds(monkeypatch, sim, expected):
    decision, _ = obs(monkeypatch, [sim])
    assert decision == expected


def test_obs_uses_max_over_candidates():
    decision, scores = obs(pytest.MonkeyPatch(), [OBS_K - 0.10, OBS_D + 0.005])
    assert decision == "discard"
    assert scores["max_content_sim"] == round(OBS_D + 0.005, 4)


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
