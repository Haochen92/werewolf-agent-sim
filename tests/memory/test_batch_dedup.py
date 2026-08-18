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


# --- clustering: seed_keys restricts which items may SEED (synth: new arrivals only) --------


def test_bounded_seed_keys_absorbs_old_neighbour(monkeypatch):
    # only the NEW arrival seeds, but an OLD obs still joins it as a neighbour.
    items = _items("new1", "old1")
    similarity = {"new1": [("old1", 0.95)], "old1": [("new1", 0.95)]}
    monkeypatch.setattr(
        clustering, "_search_memory_with_retries", _fake_search(similarity, items),
    )

    clusters = _bounded_seed_clusters(
        None, NS, items, threshold=0.9, search_limit=10, max_cluster_size=5, seed_keys={"new1"},
    )

    assert clusters == [["new1", "old1"]]


def test_bounded_seed_keys_excludes_old_only_cluster(monkeypatch):
    # two old obs that WOULD cluster under full seeding: with seed_keys excluding both, no seed iterates.
    items = _items("old1", "old2")
    similarity = {"old1": [("old2", 0.95)], "old2": [("old1", 0.95)]}
    monkeypatch.setattr(
        clustering, "_search_memory_with_retries", _fake_search(similarity, items),
    )

    clusters = _bounded_seed_clusters(
        None, NS, items, threshold=0.9, search_limit=10, max_cluster_size=5, seed_keys={"new_absent"},
    )

    assert clusters == []


def test_bounded_seed_keys_none_reproduces_full_seeding(monkeypatch):
    # seed_keys=None (default) = today's behavior: every key may seed, so the old-only pair clusters.
    items = _items("old1", "old2")
    similarity = {"old1": [("old2", 0.95)], "old2": [("old1", 0.95)]}
    monkeypatch.setattr(
        clustering, "_search_memory_with_retries", _fake_search(similarity, items),
    )

    clusters = _bounded_seed_clusters(
        None, NS, items, threshold=0.9, search_limit=10, max_cluster_size=5, seed_keys=None,
    )

    assert clusters == [["old1", "old2"]]


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


def test_strategy_discard_preserves_survivor_structured_fields():
    # Regression: the survivor rewrite used to whitelist situation/action/metadata only, silently
    # dropping direction/honesty/dimensions + verdict counters on every absorbed survivor.
    store = FakeStore()
    items = {
        "k1": _item(
            "k1", situation="s1", action="a1",
            direction="offensive", honesty="deceptive", dimensions={"x": 1},
            follow_count=2, override_count=1, not_relevant_count=0,
        ),
        "k2": _item(
            "k2", situation="s2", action="a2",
            direction="offensive", honesty="deceptive", dimensions={"y": 9},
            follow_count=3, override_count=0, not_relevant_count=4,
        ),
    }
    operation = StrategyBatchOperation(
        action="DISCARD", reasoning="dup", source_keys=["k1", "k2"], survivor_key="k2",
    )

    status, _ = _apply_strategy_operation(
        store, NS, operation, {"k1", "k2"}, items, apply=True,
    )

    assert status == "discarded"
    survivor = store.data[(NS, "k2")]
    assert survivor["direction"] == "offensive"      # carried from survivor, not dropped
    assert survivor["honesty"] == "deceptive"
    assert survivor["dimensions"] == {"y": 9}          # survivor's own dims preserved
    assert survivor["follow_count"] == 5               # 2 + 3 summed across the cluster
    assert survivor["override_count"] == 1             # 1 + 0
    assert survivor["not_relevant_count"] == 4         # 0 + 4


def test_observation_discard_does_not_inject_strategy_counters():
    # The verdict counters are strategy-only: an observation survivor must never gain them.
    store = FakeStore()
    items = {
        "k1": _item("k1", situation="s1", approach="ap1", outcome="o1",
                    dimensions={"d": 1}, distance_to_parity=2),
        "k2": _item("k2", situation="s2", approach="ap2", outcome="o2",
                    dimensions={"d": 3}, distance_to_parity=0),
    }
    operation = ObservationBatchOperation(
        action="DISCARD", reasoning="dup", source_keys=["k1", "k2"], survivor_key="k1",
    )

    status, _ = _apply_observation_operation(
        store, NS, operation, {"k1", "k2"}, items, apply=True,
    )

    assert status == "discarded"
    survivor = store.data[(NS, "k1")]
    assert survivor["dimensions"] == {"d": 1}          # structured fields preserved
    assert survivor["distance_to_parity"] == 2
    assert "follow_count" not in survivor              # SP-only counters never injected
    assert "override_count" not in survivor


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


# --- operations: incremental freeze-old (#2) --------------------------------
# new_keys = keys created since the last incremental cutoff (the "new" entries).
# Anything NOT in new_keys is a frozen "old" entry that may be absorbed-INTO but
# never absorbed-away. new_keys=None is system-wide (#3) — no freeze at all.


def test_freeze_old_forces_old_survivor_over_llm_pick():
    # old + new cluster; the LLM picked the NEW key as survivor. Freeze-old must
    # override so the OLD entry survives and the new one is folded into it.
    store = FakeStore()
    items = {
        "old1": _item("old1", situation="s_old", approach="ap_old", outcome="o_old", obs_count=2),
        "new1": _item("new1", situation="s_new", approach="ap_new", outcome="o_new", obs_count=1),
    }
    operation = ObservationBatchOperation(
        action="MERGE",
        reasoning="dup",
        source_keys=["old1", "new1"],
        survivor_key="new1",  # LLM wants the new one to win
        merged_situation="S*",
        merged_approach="A*",
        merged_outcome="O*",
    )

    status, deleted = _apply_observation_operation(
        store, NS, operation, {"old1", "new1"}, items, apply=True, new_keys={"new1"},
    )

    assert (status, deleted) == ("merged", 1)
    assert (NS, "old1") in store.data       # old entry survived...
    assert (NS, "new1") in store.deleted    # ...and the new one was absorbed
    assert store.data[(NS, "old1")]["observation_count"] == 3  # counts still summed


def test_freeze_old_rejects_old_into_old_merge():
    # Two old entries in one operation → applying it would delete an old lesson
    # no matter who survives. Reject wholesale, mutate nothing.
    store = FakeStore()
    items = {
        "old1": _item("old1", approach="a1", outcome="o1"),
        "old2": _item("old2", approach="a2", outcome="o2"),
        "new1": _item("new1", approach="a3", outcome="o3"),
    }
    operation = ObservationBatchOperation(
        action="MERGE",
        reasoning="dup",
        source_keys=["old1", "old2", "new1"],
        survivor_key="old1",
    )

    status, deleted = _apply_observation_operation(
        store, NS, operation, {"old1", "old2", "new1"}, items, apply=True, new_keys={"new1"},
    )

    assert (status, deleted) == ("frozen", 0)
    assert store.data == {} and store.deleted == []
    assert set(items) == {"old1", "old2", "new1"}  # all three preserved


def test_freeze_old_allows_new_into_new():
    # An all-new cluster has no frozen entries — behaves exactly like system-wide.
    store = FakeStore()
    items = {
        "new1": _item("new1", approach="a1", outcome="o1", obs_count=1),
        "new2": _item("new2", approach="a2", outcome="o2", obs_count=1),
    }
    operation = ObservationBatchOperation(
        action="DISCARD",
        reasoning="dup",
        source_keys=["new1", "new2"],
        survivor_key="new2",
    )

    status, deleted = _apply_observation_operation(
        store, NS, operation, {"new1", "new2"}, items, apply=True, new_keys={"new1", "new2"},
    )

    assert (status, deleted) == ("discarded", 1)
    assert (NS, "new2") in store.data        # LLM's pick honored when both are new
    assert (NS, "new1") in store.deleted


def test_system_wide_mode_ignores_freeze_and_honors_llm_pick():
    # new_keys=None → #3 system-wide. No freeze; even an "old-looking" key may be absorbed.
    store = FakeStore()
    items = {
        "k1": _item("k1", approach="a1", outcome="o1"),
        "k2": _item("k2", approach="a2", outcome="o2"),
    }
    operation = ObservationBatchOperation(
        action="DISCARD",
        reasoning="dup",
        source_keys=["k1", "k2"],
        survivor_key="k2",
    )

    status, deleted = _apply_observation_operation(
        store, NS, operation, {"k1", "k2"}, items, apply=True, new_keys=None,
    )

    assert (status, deleted) == ("discarded", 1)
    assert (NS, "k1") in store.deleted   # absorbed per the LLM, no freeze interference


# --- two-pass: skip_verify runs triage only (obs no-merge) --------------------


def test_two_pass_skip_verify_downgrades_merge_and_skips_verify(monkeypatch):
    # Obs no-merge mode: run pass 1 (triage) only. MERGE verdicts downgrade to KEEP (near-dups kept,
    # merge text cleared); DISCARD stands (exact dups collapse). The verify model is never called.
    from Agents.memory.batch_deduplication import cluster_agent as ca
    from Agents.memory.batch_deduplication.config import TwoPassConfig
    from Agents.memory.batch_deduplication.schemas import (
        ObservationBatchDedupOutput,
        ObservationBatchOperation,
    )

    models_called = []

    def fake_agent(memory_kind, role, action_phase, entries, index_to_key,
                   model, thinking_level, prompt_variant="default"):
        models_called.append(model)
        return ObservationBatchDedupOutput(operations=[
            ObservationBatchOperation(action="MERGE", reasoning="near-dup", source_keys=["k1", "k2"],
                                      survivor_key="k1", merged_situation="m",
                                      merged_approach="a", merged_outcome="o"),
            ObservationBatchOperation(action="DISCARD", reasoning="exact", source_keys=["k3", "k4"],
                                      survivor_key="k3"),
        ])

    monkeypatch.setattr(ca, "_cluster_agent", fake_agent)
    monkeypatch.setattr(ca, "_format_cluster_entries", lambda *a, **k: ("entries", {}))

    out = ca._two_pass_cluster_dedup(
        "observations", "villager", "day_vote", ["k1", "k2", "k3", "k4"], {},
        TwoPassConfig(triage_model="flash-lite", skip_verify=True),
    )

    assert models_called == ["flash-lite"]                  # verify model never called
    assert sorted(op.action for op in out.operations) == ["DISCARD", "KEEP"]   # MERGE -> KEEP
    keep = next(op for op in out.operations if op.action == "KEEP")
    assert keep.merged_situation is None                    # merge text cleared by the downgrade
