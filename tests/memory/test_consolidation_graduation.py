"""The graduated production pipeline (Agents/memory/consolidation/) — the properties that gate go-live.

(a) FIXED RULE, HARD-CODED — production grades town abstains deadlock-negative with NO keyword,
    flag, or config anywhere on the call path (owner ruling 2026-07-21: the knobbed variants are
    eval-only). The conversion channel was dropped with the ten-seat port (plan §9.6 item 3), and with
    it the parity test against the eval grader, which stays nine-seat for the frozen runs; the
    ten-seat table is tested in test_ten_seat_grading.py.
(c) POISONING GUARD — a game record with a human seat teaches nothing (ledger, base).
(d) DB IS THE RECORD — Postgres roundtrips the store/sidecars exactly; the tick runs end-to-end
    against a throwaway database and freezes a demo_gen{k} snapshot. Skipped when WW_POSTGRES_DSN
    is absent (the DB tests need the ww-postgres container).
"""

from __future__ import annotations

import json
import os
import uuid
from pathlib import Path

import pytest
from dotenv import load_dotenv

from Agents.memory.consolidation.config import TickConfig
from Agents.memory.consolidation.credit import credit_apply as prod_credit_apply
from Agents.memory.consolidation.credit_rules import compute_base_rates as prod_base_rates
from Agents.memory.consolidation.grading import GameView
from tests.factories.builders import (day_vote_case as _vote_case,
                                      eval_case_part as _ec,
                                      strategy_point as _sp)

load_dotenv()
DSN = os.environ.get("WW_POSTGRES_DSN")
needs_db = pytest.mark.skipif(not DSN, reason="WW_POSTGRES_DSN not set (ww-postgres container)")

ROLES = {"player_1": "sentinel", "player_2": "chanteuse", "player_3": "trailseer",
         "player_4": "investigator", "player_5": "serial_killer"}
NO_LYNCH = {"day": 2, "no_vote": True, "voted_player": None, "vote_counts": {}}
LYNCHED_THREAT = {"day": 2, "no_vote": False, "voted_player": "player_2",
                  "voted_player_role": "chanteuse", "vote_counts": {"player_2": 4}}


def _game(tmp: Path, name: str, cases: list, *, roles: dict = ROLES, day_res=None, night_res=None,
          human_player=None) -> str:
    ecp = tmp / f"{name}_cases.jsonl"
    ecp.write_text("\n".join(json.dumps(_ec(c)) for c in cases))
    rec = {"roles": roles, "eval_cases_path": str(ecp), "game_id": f"gid_{name}"}
    if day_res is not None:
        rec["day_resolutions"] = day_res
    if night_res is not None:
        rec["night_resolutions"] = night_res
    if human_player is not None:
        rec["human_player"] = human_player
    gp = tmp / f"{name}.jsonl"
    gp.write_text(json.dumps(rec))
    return str(gp)


def _sp_store(tmp: Path, name: str, sps: dict) -> Path:
    p = tmp / name
    p.write_text(json.dumps({"namespaces": sps}))
    return p


# --- (a) the fixed rule is the ONLY rule ------------------------------------------------------------

def test_production_abstain_rule_needs_no_switch():
    view = GameView({"roles": ROLES})
    assert view.vote_grade("player_1", "sentinel", 2, "abstain", day_res=NO_LYNCH) == "negative"
    assert view.vote_grade("player_1", "sentinel", 2, "abstain", day_res=LYNCHED_THREAT) == "neutral"
    assert view.vote_grade("player_1", "sentinel", 2, "abstain") == "neutral"  # missing row: degrade
    # evil seats keep their own abstain semantics under the town rule
    assert view.vote_grade("player_5", "serial_killer", 2, "abstain", day_res=NO_LYNCH) == "neutral"
    assert view.vote_grade("player_2", "chanteuse", 2, "abstain", majority="abstain", day_res=NO_LYNCH) == "positive"
    import inspect
    assert "abstain_rule" not in inspect.signature(view.vote_grade).parameters
    assert "abstain_rule" not in inspect.signature(prod_credit_apply).parameters
    assert not hasattr(TickConfig(), "conversion_window_days")


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


# --- (c) the poisoning guard ------------------------------------------------------------------------

def test_human_involved_games_teach_nothing(tmp_path):
    cases_on = [_vote_case("trailseer", "player_3", "player_2", key="k_push")]
    cases_off = [_vote_case("sentinel", "player_1", "abstain", mem=False)]
    human_on = _game(tmp_path, "hon", cases_on, day_res=[NO_LYNCH], human_player="player_1")
    human_off = _game(tmp_path, "hoff", cases_off, day_res=[NO_LYNCH], human_player="player_1")
    sp = _sp_store(tmp_path, "strategy_points.json", {
        "strategy_points/trailseer/day_vote": [_sp("k_push", cell="trailseer/day_vote")]})
    assert prod_base_rates(human_off) == {}
    stats = prod_credit_apply(sp, human_on, base_rates={}, off_window=None)
    assert stats["ledger_keys"] == 0 and stats["credited"] == 0


# --- (d) Postgres roundtrip + the tick --------------------------------------------------------------

@needs_db
def test_db_roundtrip_in_temp_schema():
    import Agents.memory.consolidation.db as db
    with db.connect(DSN) as conn:
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


@needs_db
def test_tick_end_to_end_llm_free(tmp_path):
    import psycopg

    from Agents.memory.consolidation.tick import run_credit_pass, run_tick

    # a throwaway database so the tick can exercise the REAL path (own connection, real tables)
    dbname = f"ww_tick_test_{uuid.uuid4().hex[:10]}"
    admin = psycopg.connect(DSN, autocommit=True)
    admin.execute(f'CREATE DATABASE "{dbname}"')
    test_dsn = DSN.rsplit("/", 1)[0] + f"/{dbname}"
    try:
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
    finally:
        admin.execute(f'DROP DATABASE IF EXISTS "{dbname}" WITH (FORCE)')
        admin.close()
