"""The consolidation pipeline's database is its record (Agents/memory/consolidation/db.py), on a real
Postgres database in the test container: the store and its sidecars round-trip exactly, and the credit
pass and the learning tick run end to end, without a model, and freeze a demo_gen{k} snapshot.

(Moved here on 2026-11-18 from tests/memory/test_consolidation_graduation.py, where they ran against the
server `WW_POSTGRES_DSN` named and were skipped without it.)
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from Agents.memory.consolidation.config import TickConfig
from tests.factories.builders import (NO_LYNCH,
                                      credit_game_record as _game,
                                      day_vote_case as _vote_case,
                                      strategy_point as _sp)


# --- the window the tick test grades ---------------------------------------------------------------

def _window(tmp: Path) -> tuple[str, str]:
    on_cases = [
        _vote_case("sentinel", "player_1", "abstain", key="k_abstain"),
        _vote_case("trailseer", "player_3", "player_2", key="k_push"),
        _vote_case("investigator", "player_4", "abstain", key="k_abstain"),
    ]
    off_cases = [
        _vote_case("sentinel", "player_1", "abstain", mem=False),
        _vote_case("trailseer", "player_3", "player_2", mem=False),
    ]
    on = _game(tmp, "on", on_cases, day_res=[NO_LYNCH], night_res=[])
    off = _game(tmp, "off", off_cases, day_res=[NO_LYNCH], night_res=[])
    return on, off


# --- Postgres roundtrip + the tick ------------------------------------------------------------------

def test_db_roundtrip_in_temp_schema(postgres_dsn):
    import Agents.memory.consolidation.db as db
    with db.connect(postgres_dsn) as conn:
        conn.execute("SET search_path TO pg_temp")  # session-scoped tables, auto-dropped on close
        db.setup(conn)
        assert db.store_is_empty(conn)
        store = {"namespaces": {"strategy_points/villager/day_vote": [_sp("k1"), _sp("k2")]}}
        db.save_store(conn, "strategy_points", store)
        db.save_store(conn, "observations", {"namespaces": {}})
        assert db.load_store(conn, "strategy_points") == store
        db.save_base_rates(conn, {"villager/day_vote": [0.25, 8]})
        assert db.load_base_rates(conn) == {"villager/day_vote": [0.25, 8]}
        db.save_obs_sidecar(conn, {"o1": 1}, {"o1": 2}, {"o1": 3})
        assert db.load_obs_sidecar(conn) == ({"o1": 1}, {"o1": 2}, {"o1": 3})
        assert db.next_gen(conn) == 1
        db.record_tick(conn, 1, {"ok": True}, {"on_dumps": "x"}, "/snap/demo_gen1")
        assert db.next_gen(conn) == 2
        assert db.last_snapshot_dir(conn) == "/snap/demo_gen1"
        with pytest.raises(RuntimeError):
            db.bootstrap_from_dir(conn, ".")  # non-empty store: bootstrap must refuse


def test_tick_end_to_end_llm_free(tmp_path, monkeypatch, postgres_dsn):
    import psycopg

    from Agents.memory.consolidation.tick import run_credit_pass, run_tick
    from Agents.memory.persistence import postgres as pg

    # the publish step at the end of each pass embeds what changed; a fake embedder keeps the
    # test LLM-free while the served game's index is still built in the throwaway database
    monkeypatch.setattr(pg, "index_config", lambda: {
        "dims": 4, "embed": lambda texts: [[1.0, 0.0, 0.0, 0.0] for _ in texts], "fields": ["situation"]})

    # the test container's fresh database, so the tick exercises the REAL path (own connection, real tables)
    test_dsn = postgres_dsn
    boot = tmp_path / "boot_store"
    boot.mkdir()
    (boot / "strategy_points.json").write_text(json.dumps({"namespaces": {
        "strategy_points/sentinel/day_vote": [_sp("k_abstain", cell="sentinel/day_vote")],
        "strategy_points/trailseer/day_vote": [_sp("k_push", cell="trailseer/day_vote")]}}))
    (boot / "observations.json").write_text(json.dumps({"namespaces": {}}))
    on, off = _window(tmp_path)
    game_store = tmp_path / "game1_store"
    game_store.mkdir()
    (game_store / "observations.json").write_text(json.dumps({"namespaces": {
        "observations/sentinel/day_vote": [{"key": "obs_new", "value": {
            "observation_count": 1, "situation": "s", "observation": "o"}}]}}))

    # the credit pass: labels from the games, then prune and evict, recorded in credit_runs
    credit = run_credit_pass(on, off, dsn=test_dsn, bootstrap_store=boot)
    assert credit["games"] == 1 and credit["credit"]["credited"] == 2
    with psycopg.connect(test_dsn) as conn:
        assert conn.execute("SELECT count(*) FROM credit_runs").fetchone()[0] == 1

    # the learning tick folds and freezes; it reads the labels the pass left and never prunes
    cfg = TickConfig(synthesize=False, sp_dedup=False, obs_fold_dedup=False)
    stats = run_tick([str(game_store)], snapshot_root=tmp_path / "snaps",
                     bootstrap_store=boot, cfg=cfg, dsn=test_dsn)
    assert stats["gen"] == 1 and stats["fold"]["new_obs"] == 1
    assert stats["consolidate"]["prune_evict"] == {}
    snap = Path(stats["snapshot_dir"])
    assert snap.name == "demo_gen1" and (snap / "manifest.json").exists()
    manifest = json.loads((snap / "manifest.json").read_text())
    assert "hard-coded" in manifest["credit_rule"]
    sp = json.loads((snap / "strategy_points.json").read_text())
    by_key = {r["key"]: r["value"] for recs in sp["namespaces"].values() for r in recs}
    assert by_key["k_abstain"]["negative_count"] == 2   # both abstain follows on the no-lynch day
    assert by_key["k_push"]["positive_count"] == 1
    obs = json.loads((snap / "observations.json").read_text())
    assert [r["key"] for r in obs["namespaces"]["observations/sentinel/day_vote"]] == ["obs_new"]

    stats2 = run_tick([], snapshot_root=tmp_path / "snaps", bootstrap_store=boot, cfg=cfg, dsn=test_dsn)
    assert stats2["gen"] == 2 and Path(stats2["snapshot_dir"]).name == "demo_gen2"
