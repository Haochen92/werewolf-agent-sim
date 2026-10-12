"""Switching the embedding model: an OpenRouter model id gets the OpenRouter client pinned to fixed
hosts, every model carries its own complete set of similarity thresholds, and a store cache built
under another embedding model is never loaded (its vectors would be meaningless to the new one)."""

import pickle
import tempfile
from pathlib import Path

from langgraph.store.memory import InMemoryStore

import Agents.llm_factory as llm_factory
from Agents.llm_factory import embeddings as emb
from Agents.memory.persistence import cache


def test_a_model_id_with_a_slash_is_served_through_openrouter_on_pinned_hosts(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test")
    model = emb.create_embeddings("qwen/qwen3-embedding-8b", output_dimensionality=1536)
    assert isinstance(model, emb._RetryingOpenRouterEmbeddings)
    assert model.dimensions == 1536 and model.check_embedding_ctx_length is False
    provider = model.model_kwargs["extra_body"]["provider"]
    assert provider == {"order": emb.OPENROUTER_EMBEDDING_PROVIDERS, "allow_fallbacks": False}


def test_every_embedding_model_has_the_same_threshold_names():
    names = {frozenset(t) for t in emb.SIMILARITY_THRESHOLDS.values()}
    assert len(names) == 1
    assert emb.similarity_threshold("retrieval_dedup_gate", "gemini-embedding-2") == 0.87


def _write_cache(tmp: Path, signature: dict | None) -> tuple[Path, Path, Path]:
    obs, sp = tmp / "o.json", tmp / "s.json"
    obs.write_text("{}")
    sp.write_text("{}")
    payload = {"version": 1, "observations_sha256": cache._file_sha256(obs),
               "strategy_points_sha256": cache._file_sha256(sp), "data": {}, "vectors": {}}
    if signature:
        payload.update(signature)
    path = tmp / "indexed_cache.pkl"
    path.write_bytes(pickle.dumps(payload))
    return path, obs, sp


def test_a_cache_from_another_embedding_model_is_stale(monkeypatch):
    monkeypatch.setattr(llm_factory, "DEFAULT_EMBEDDING_MODEL", "qwen/qwen3-embedding-8b")
    with tempfile.TemporaryDirectory() as t:
        path, obs, sp = _write_cache(Path(t), {"embedding_model": "gemini-embedding-2", "embedding_dims": 1536})
        assert cache.load_indexed_store_cache(path, InMemoryStore(), obs, sp) is False
        assert cache.load_cached_vectors(path) == {}


def test_a_cache_without_a_signature_counts_as_gemini_embedding_2(monkeypatch):
    with tempfile.TemporaryDirectory() as t:
        path, obs, sp = _write_cache(Path(t), None)
        monkeypatch.setattr(llm_factory, "DEFAULT_EMBEDDING_MODEL", "gemini-embedding-2")
        assert cache.load_indexed_store_cache(path, InMemoryStore(), obs, sp) is True
        monkeypatch.setattr(llm_factory, "DEFAULT_EMBEDDING_MODEL", "qwen/qwen3-embedding-8b")
        assert cache.load_indexed_store_cache(path, InMemoryStore(), obs, sp) is False
