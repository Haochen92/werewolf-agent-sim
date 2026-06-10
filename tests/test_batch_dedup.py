"""Deterministic-core tests for batch (cluster) dedup.

The *decision quality* of batch dedup — does the LLM merge the right entries — is
verified empirically in evidence/dedup/ (golden-label accuracy, retrieval impact).
These tests cover the part evals can't isolate: the deterministic mechanics that
silently mangle the store if they regress —

  clustering   which entries get grouped together before the LLM ever sees them
               (connected-components vs bounded-seed; size cap; threshold filter)
  operations   how a KEEP/DISCARD/MERGE verdict is applied — survivor selection,
               count merging, deletion of absorbed entries, and dry-run safety

Both are pure functions: clustering's store search is monkeypatched to a fixed
similarity graph, and operations run against a minimal fake store. No LLM, no
embeddings, no network.
"""

from types import SimpleNamespace

from Agents.memory.batch_deduplication import clustering
from Agents.memory.batch_deduplication.clustering import (
    _bounded_seed_clusters,
    _cluster_items,
)
from Agents.memory.batch_deduplication.operations import (
    _apply_observation_operation,
    _apply_strategy_operation,
)
from Agents.memory.batch_deduplication.schemas import (
    ObservationBatchOperation,
    StrategyBatchOperation,
)

NS = ("observations", "villager", "day_vote")


# --- fixtures / fakes -------------------------------------------------------


def _item(key, situation=None, obs_count=1, last_observed="2026-01-01T00:00:00", **extra):
    """A store item. ``situation`` defaults to the key so the fake search can key on it."""
    value = {
        "situation": key if situation is None else situation,
        "observation_count": obs_count,
        "last_observed": last_observed,
    }
    value.update(extra)
    return SimpleNamespace(key=key, value=value)


def _items(*keys):
    return {key: _item(key) for key in keys}


def _fake_search(similarity, items_by_key):
    """Stand in for ``_search_memory_with_retries`` using a fixed similarity graph.

    ``similarity`` maps a query (an item's situation, == its key here) to a list of
    ``(neighbour_key, score)`` — exactly what a vector search would return, minus the
    embeddings.
    """

    def search(_store, _namespace, *, query, limit, offset=0):
        neighbours = similarity.get(query, [])
        return [
            SimpleNamespace(key=nkey, score=score, value=items_by_key[nkey].value)
            for nkey, score in neighbours[:limit]
        ]

    return search


class FakeStore:
    """Records puts/deletes so a test can assert what the apply step wrote."""

    def __init__(self):
        self.data = {}
        self.deleted = []

    def put(self, namespace, key, value):
        self.data[(namespace, key)] = value

    def delete(self, namespace, key):
        self.deleted.append((namespace, key))
        self.data.pop((namespace, key), None)


# --- clustering: connected-components is transitive --------------------------


def test_connected_clustering_merges_transitively(monkeypatch):
    # A~B and B~C, but A is NOT directly similar to C.
    items = _items("A", "B", "C")
    similarity = {
        "A": [("B", 0.95)],
        "B": [("A", 0.95), ("C", 0.95)],
        "C": [("B", 0.95)],
    }
    monkeypatch.setattr(
        clustering, "_search_memory_with_retries", _fake_search(similarity, items),
    )

    clusters = _cluster_items(None, NS, items, threshold=0.9, search_limit=10)

    # The shared edge through B pulls all three into one connected component.
    assert clusters == [["A", "B", "C"]]


# --- clustering: bounded-seed does NOT chain (the contrast) ------------------


def test_bounded_clustering_does_not_chain(monkeypatch):
    items = _items("A", "B", "C")
    similarity = {
        "A": [("B", 0.95)],
        "B": [("A", 0.95), ("C", 0.95)],
        "C": [("B", 0.95)],
    }
    monkeypatch.setattr(
        clustering, "_search_memory_with_retries", _fake_search(similarity, items),
    )

    clusters = _bounded_seed_clusters(
        None, NS, items, threshold=0.9, search_limit=10, max_cluster_size=5,
    )

    # Seed A absorbs B; C's only neighbour (B) is already consumed, so C is left
    # alone and dropped. No transitive A-B-C cluster — this is why bounded is the
    # conservative default.
    assert clusters == [["A", "B"]]


# --- clustering: bounded respects the size cap and partitions ---------------


def test_bounded_clustering_caps_size_and_partitions(monkeypatch):
    items = _items("A", "B", "C", "D", "E")
    similarity = {
        "A": [("B", 0.99), ("C", 0.98), ("D", 0.97), ("E", 0.96)],
        "D": [("E", 0.99)],
    }
    monkeypatch.setattr(
        clustering, "_search_memory_with_retries", _fake_search(similarity, items),
    )

    clusters = _bounded_seed_clusters(
        None, NS, items, threshold=0.9, search_limit=10, max_cluster_size=3,
    )

    # A has four neighbours but the cap holds the cluster to 3 (A + top-2 by score).
    # D and E are left unprocessed and form their own cluster — every item lands in
    # exactly one cluster.
    assert clusters == [["A", "B", "C"], ["D", "E"]]


# --- clustering: below-threshold neighbours are excluded --------------------


def test_bounded_clustering_excludes_below_threshold(monkeypatch):
    items = _items("A", "B", "C")
    similarity = {"A": [("B", 0.95), ("C", 0.50)]}
    monkeypatch.setattr(
        clustering, "_search_memory_with_retries", _fake_search(similarity, items),
    )

    clusters = _bounded_seed_clusters(
        None, NS, items, threshold=0.9, search_limit=10, max_cluster_size=5,
    )

    # C scores 0.50 < 0.9, so it never joins A's cluster and is dropped.
    assert clusters == [["A", "B"]]


# --- operations: strategy DISCARD merges counts onto the chosen survivor ----


def test_strategy_discard_keeps_survivor_and_sums_counts():
    store = FakeStore()
    items = {
        "k1": _item("k1", situation="s1", action="a1", obs_count=2, retrieved_count=3),
        "k2": _item("k2", situation="s2", action="a2", obs_count=5, retrieved_count=4),
    }
    operation = StrategyBatchOperation(
        action="DISCARD",
        reasoning="duplicate",
        source_keys=["k1", "k2"],
        survivor_key="k2",
    )

    status, deleted = _apply_strategy_operation(
        store, NS, operation, {"k1", "k2"}, items, apply=True,
    )

    assert (status, deleted) == ("discarded", 1)
    survivor = store.data[(NS, "k2")]
    assert survivor["situation"] == "s2"          # survivor's own text (no merged_*)
    assert survivor["action"] == "a2"
    assert survivor["observation_count"] == 7      # 2 + 5 summed across the cluster
    assert survivor["retrieved_count"] == 7        # 3 + 4
    assert (NS, "k1") in store.deleted             # absorbed entry deleted
    assert "k1" not in items                       # and dropped from the working set


# --- operations: observation MERGE adopts merged text, reports 'merged' -----


def test_observation_merge_uses_merged_text_and_reports_merged():
    store = FakeStore()
    items = {
        "k1": _item("k1", situation="s1", approach="ap1", outcome="o1"),
        "k2": _item("k2", situation="s2", approach="ap2", outcome="o2"),
    }
    operation = ObservationBatchOperation(
        action="MERGE",
        reasoning="combine",
        source_keys=["k1", "k2"],
        survivor_key="k1",
        merged_situation="S*",
        merged_approach="A*",
        merged_outcome="O*",
    )

    status, deleted = _apply_observation_operation(
        store, NS, operation, {"k1", "k2"}, items, apply=True,
    )

    assert (status, deleted) == ("merged", 1)
    survivor = store.data[(NS, "k1")]
    assert (survivor["situation"], survivor["approach"], survivor["outcome"]) == (
        "S*", "A*", "O*",
    )
    assert survivor["observation_count"] == 2
    assert (NS, "k2") in store.deleted


# --- operations: dry-run counts but never touches the store -----------------


def test_dry_run_counts_without_mutating_store():
    store = FakeStore()
    items = {"k1": _item("k1", action="a1"), "k2": _item("k2", action="a2")}
    operation = StrategyBatchOperation(
        action="DISCARD",
        reasoning="duplicate",
        source_keys=["k1", "k2"],
        survivor_key="k1",
    )

    status, deleted = _apply_strategy_operation(
        store, NS, operation, {"k1", "k2"}, items, apply=False,
    )

    assert (status, deleted) == ("discarded", 1)   # still reports what it *would* do
    assert store.data == {}                         # but writes nothing
    assert store.deleted == []                       # and deletes nothing
    assert set(items) == {"k1", "k2"}                # working set untouched


# --- operations: a survivor the LLM invented fails safely (no data loss) ----


def test_invalid_survivor_key_fails_without_mutation():
    store = FakeStore()
    items = {"k1": _item("k1", action="a1")}
    operation = StrategyBatchOperation(
        action="DISCARD",
        reasoning="x",
        source_keys=["k1"],
        survivor_key="ghost",  # not a real key in the cluster
    )

    status, deleted = _apply_strategy_operation(
        store, NS, operation, {"k1"}, items, apply=True,
    )

    assert (status, deleted) == ("failed", 0)
    assert store.data == {} and store.deleted == []
    assert "k1" in items  # nothing absorbed
