"""Publishing the tick's records into the served game's lesson store: only what changed is put
(the one embedding cost), what is gone is deleted, the index is signed with the embedder that
built it, and a store signed by another embedder is rebuilt whole and refused until it is."""

from langgraph.store.memory import InMemoryStore

from Agents.memory.persistence import postgres as pg


def _stores(sp: dict[str, dict], obs: dict[str, dict] | None = None) -> dict[str, dict]:
    def records(cell: dict[str, dict]) -> dict:
        return {"namespaces": {ns: [{"key": k, "value": v} for k, v in recs.items()]
                               for ns, recs in cell.items()}}
    return {"strategy_points": records(sp), "observations": records(obs or {})}


SP = {"strategy_points/healer/night_action": {
    "a": {"situation": "a wolf claim on day two", "action": "heal the claimant"},
    "b": {"situation": "two reports agree", "action": "heal neither"}}}


def test_a_first_publish_puts_everything_and_signs_the_index():
    store = InMemoryStore()
    stats = pg.publish(store, _stores(SP), source={"credit_run": 1})
    assert stats["put"] == 2 and stats["deleted"] == 0 and stats["reembedded_all"] is True
    marker = pg.read_marker(store)
    assert marker["embedding_model"] == pg.DEFAULT_EMBEDDING_MODEL
    assert marker["counts"] == {"strategy_points": 2, "observations": 0}
    assert marker["source"] == {"credit_run": 1}
    assert pg.unready_reason(store) is None
    assert store.get(("strategy_points", "healer", "night_action"), "a").value["action"] == "heal the claimant"


def test_a_second_publish_touches_only_what_changed():
    store = InMemoryStore()
    pg.publish(store, _stores(SP))
    changed = {"strategy_points/healer/night_action": {
        "a": {**SP["strategy_points/healer/night_action"]["a"], "action": "heal the accuser"},
        "c": {"situation": "a new lesson", "action": "wait"}}}
    stats = pg.publish(store, _stores(changed))
    assert stats == {"put": 2, "deleted": 1, "unchanged": 0, "reembedded_all": False,
                     "counts": {"strategy_points": 2, "observations": 0}}
    ns = ("strategy_points", "healer", "night_action")
    assert store.get(ns, "b") is None
    assert store.get(ns, "a").value["action"] == "heal the accuser"
    assert pg.publish(store, _stores(changed))["put"] == 0


def test_an_index_built_by_another_embedder_is_refused_then_rebuilt_whole(monkeypatch):
    store = InMemoryStore()
    pg.publish(store, _stores(SP))
    store.put(pg.MARKER_NAMESPACE, pg.MARKER_KEY,
              {**pg.read_marker(store), "embedding_model": "gemini-embedding-2"})
    assert "gemini-embedding-2" in pg.unready_reason(store)
    stats = pg.publish(store, _stores(SP))
    assert stats["put"] == 2 and stats["reembedded_all"] is True
    assert pg.unready_reason(store) is None


def test_an_unpublished_or_empty_store_is_not_ready():
    store = InMemoryStore()
    assert "published" in pg.unready_reason(store)
    pg.publish(store, _stores({}))
    assert "no strategy points" in pg.unready_reason(store)


def test_legacy_role_only_namespaces_fan_out_and_content_becomes_situation():
    store = InMemoryStore()
    stores = _stores({"strategy_points/healer": {"x": {"content": "an old record", "action": "do"}}})
    pg.publish(store, stores)
    namespaces = store.list_namespaces(prefix=("strategy_points", "healer"))
    assert len(namespaces) > 1 and all(len(ns) == 3 for ns in namespaces)
    assert store.get(namespaces[0], "x").value["situation"] == "an old record"
