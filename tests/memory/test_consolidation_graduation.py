"""The graduated production pipeline (Agents/memory/consolidation/) — the properties that gate go-live.

(a) FIXED RULE, HARD-CODED — production grades town abstains deadlock-negative and applies the
    conversion channel with NO keyword, flag, or config anywhere on the call path (owner ruling
    2026-07-21: the knobbed variants are eval-only).
(b) PARITY — the production grader is byte-equal to the eval grader pinned to the fixed settings
    on the same window (the lift changed homes, not semantics).
(c) POISONING GUARD — a game record with a human seat teaches nothing (ledger, base, conversion).
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
from Agents.memory.consolidation.conversion import conversion_apply as prod_conversion_apply
from Agents.memory.consolidation.credit import credit_apply as prod_credit_apply
from Agents.memory.consolidation.credit_rules import (
    _vote_credit as prod_vote_credit,
    compute_base_rates as prod_base_rates,
)
from Agents.memory.consolidation.store_ops import prune_and_evict as prod_prune_and_evict
from evaluation.src.loop.conversion_credit import conversion_apply as eval_conversion_apply
from evaluation.src.loop.credit import credit_apply as eval_credit_apply
from evaluation.src.loop.credit_backfill import compute_base_rates as eval_base_rates
from tests.factories.builders import (day_vote_case as _vote_case,
                                      eval_case_part as _ec,
                                      strategy_point as _sp)

load_dotenv()
DSN = os.environ.get("WW_POSTGRES_DSN")
needs_db = pytest.mark.skipif(not DSN, reason="WW_POSTGRES_DSN not set (ww-postgres container)")

ROLES = {"player_1": "villager", "player_2": "wolf", "player_3": "villager",
         "player_4": "investigator", "player_5": "serial_killer"}
NO_LYNCH = {"day": 2, "no_vote": True, "voted_player": None, "vote_counts": {}}
LYNCHED_THREAT = {"day": 2, "no_vote": False, "voted_player": "player_2",
                  "voted_player_role": "wolf", "vote_counts": {"player_2": 4}}


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
    assert prod_vote_credit("villager", "abstain", ROLES, day_res=NO_LYNCH) == "negative"
    assert prod_vote_credit("villager", "abstain", ROLES, day_res=LYNCHED_THREAT) == "neutral"
    assert prod_vote_credit("villager", "abstain", ROLES) == "neutral"  # missing row: degrade
    # deceivers keep their own abstain semantics under the town rule
    assert prod_vote_credit("serial_killer", "abstain", ROLES, day_res=NO_LYNCH) == "neutral"
    assert prod_vote_credit("wolf", "abstain", ROLES, majority="abstain", day_res=NO_LYNCH) == "positive"
    import inspect
    assert "abstain_rule" not in inspect.signature(prod_vote_credit).parameters
    assert "abstain_rule" not in inspect.signature(prod_credit_apply).parameters


def test_production_prune_applies_conversion_term_unconditionally(tmp_path):
    ns = {"strategy_points/investigator/day_vote": [
        _sp("k_silence", cell="investigator/day_vote", conversion_neg_count=5),
        _sp("k_proven", cell="investigator/day_vote", follow_count=8, positive_count=8,
            conversion_neg_count=5),
    ]}
    stats = prod_prune_and_evict(ns, {"investigator/day_vote": [0.0, 4]}, TickConfig())
    assert stats["pruned"] == 1  # no flag to turn on — the channel is part of the system
    assert [r["key"] for r in ns["strategy_points/investigator/day_vote"]] == ["k_proven"]
    import inspect
    assert not hasattr(TickConfig(), "conversion_credit")
    assert not hasattr(TickConfig(), "abstain_credit")
    del inspect


# --- (b) parity with the eval grader pinned to the fixed settings -----------------------------------

def _window(tmp: Path) -> tuple[str, str]:
    on_cases = [
        _vote_case("villager", "player_1", "abstain", key="k_abstain"),
        _vote_case("villager", "player_3", "player_2", key="k_push"),
        _vote_case("investigator", "player_4", "abstain", key="k_abstain"),
    ]
    off_cases = [
        _vote_case("villager", "player_1", "abstain", mem=False),
        _vote_case("villager", "player_3", "player_2", mem=False),
    ]
    on = _game(tmp, "on", on_cases, day_res=[NO_LYNCH], night_res=[])
    off = _game(tmp, "off", off_cases, day_res=[NO_LYNCH], night_res=[])
    return on, off


def test_credit_parity_with_pinned_eval_grader(tmp_path):
    sps = {"strategy_points/villager/day_vote": [_sp("k_abstain"), _sp("k_push")],
           "strategy_points/investigator/day_vote": [_sp("k_abstain", cell="investigator/day_vote")]}
    on, off = _window(tmp_path)
    prod_dir, eval_dir = tmp_path / "prod", tmp_path / "eval"
    prod_dir.mkdir(), eval_dir.mkdir()
    p_sp = _sp_store(prod_dir, "strategy_points.json", sps)
    e_sp = _sp_store(eval_dir, "strategy_points.json", sps)

    prod_credit_apply(p_sp, on, base_rates=prod_base_rates(off), off_window=off)
    eval_credit_apply(e_sp, on, base_rates=eval_base_rates(off, abstain_rule="deadlock_negative"),
                      off_window=off, abstain_rule="deadlock_negative")
    assert json.loads(p_sp.read_text()) == json.loads(e_sp.read_text())
    assert (json.loads((prod_dir / "base_rates.json").read_text())
            == json.loads((eval_dir / "base_rates.json").read_text()))

    prod_conversion_apply(p_sp, on, off_window=off, window_days=2)
    eval_conversion_apply(e_sp, on, off_window=off, window_days=2)
    assert json.loads(p_sp.read_text()) == json.loads(e_sp.read_text())


# --- (c) the poisoning guard ------------------------------------------------------------------------

def test_human_involved_games_teach_nothing(tmp_path):
    cases_on = [_vote_case("villager", "player_3", "player_2", key="k_push")]
    cases_off = [_vote_case("villager", "player_1", "abstain", mem=False)]
    human_on = _game(tmp_path, "hon", cases_on, day_res=[NO_LYNCH], human_player="player_1")
    human_off = _game(tmp_path, "hoff", cases_off, day_res=[NO_LYNCH], human_player="player_1")
    sp = _sp_store(tmp_path, "strategy_points.json", {
        "strategy_points/villager/day_vote": [_sp("k_push")]})
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

    from Agents.memory.consolidation.tick import run_tick

    # a throwaway database so the tick can exercise the REAL path (own connection, real tables)
    dbname = f"ww_tick_test_{uuid.uuid4().hex[:10]}"
    admin = psycopg.connect(DSN, autocommit=True)
    admin.execute(f'CREATE DATABASE "{dbname}"')
    test_dsn = DSN.rsplit("/", 1)[0] + f"/{dbname}"
    try:
        boot = tmp_path / "boot_store"
        boot.mkdir()
        (boot / "strategy_points.json").write_text(json.dumps({"namespaces": {
            "strategy_points/villager/day_vote": [_sp("k_abstain"), _sp("k_push")]}}))
        (boot / "observations.json").write_text(json.dumps({"namespaces": {}}))
        on, off = _window(tmp_path)
        game_store = tmp_path / "game1_store"
        game_store.mkdir()
        (game_store / "observations.json").write_text(json.dumps({"namespaces": {
            "observations/villager/day_vote": [{"key": "obs_new", "value": {
                "observation_count": 1, "situation": "s", "observation": "o"}}]}}))

        cfg = TickConfig(synthesize=False, sp_dedup=False, obs_fold_dedup=False)
        stats = run_tick(on, off, [str(game_store)], snapshot_root=tmp_path / "snaps",
                         bootstrap_store=boot, cfg=cfg, dsn=test_dsn)

        assert stats["gen"] == 1 and stats["fold"]["new_obs"] == 1
        assert stats["credit"]["credited"] == 2
        snap = Path(stats["snapshot_dir"])
        assert snap.name == "demo_gen1" and (snap / "manifest.json").exists()
        manifest = json.loads((snap / "manifest.json").read_text())
        assert "hard-coded" in manifest["credit_rule"]
        sp = json.loads((snap / "strategy_points.json").read_text())
        by_key = {r["key"]: r["value"] for recs in sp["namespaces"].values() for r in recs}
        assert by_key["k_abstain"]["negative_count"] == 2   # both abstain follows on the no-lynch day
        assert by_key["k_push"]["positive_count"] == 1
        obs = json.loads((snap / "observations.json").read_text())
        assert [r["key"] for r in obs["namespaces"]["observations/villager/day_vote"]] == ["obs_new"]

        stats2 = run_tick(on, off, [], snapshot_root=tmp_path / "snaps",
                          bootstrap_store=boot, cfg=cfg, dsn=test_dsn)
        assert stats2["gen"] == 2 and Path(stats2["snapshot_dir"]).name == "demo_gen2"
    finally:
        admin.execute(f'DROP DATABASE IF EXISTS "{dbname}" WITH (FORCE)')
        admin.close()
