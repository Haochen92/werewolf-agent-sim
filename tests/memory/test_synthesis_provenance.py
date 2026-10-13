"""Synthesis keeps provenance for a worked example: each new strategy point records the observation
cluster it came from, and each synthesis call's input and output is logged beside the store. The LLM
synthesis and the clustering are stubbed the same lazy-imported way store_ops reaches them."""

import json
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from Agents.memory.consolidation import store_ops
from Agents.memory.consolidation.config import TickConfig

_OBS = {"o1": SimpleNamespace(value={"situation": "s", "net_verdict": "positive",
                                     "approach": "voted the quiet one", "outcome": "o"})}


class _FakeSP:
    action_phase = "night_action"
    composed_situation = "sit"
    action = "act"
    direction = "offensive"
    honesty = "honest"

    def model_dump(self, mode: str = "json") -> dict:
        return {"action_phase": self.action_phase}


def test_a_new_strategy_records_its_source_cluster_and_the_call_is_logged():
    import Agents.memory.persistence as persist_mod
    import Agents.memory.strategy_synthesis as synth_mod
    import Agents.schemas.roles as roles_mod

    ns: dict = {}
    with tempfile.TemporaryDirectory() as t, \
            patch.object(roles_mod, "roles", ["sentinel"]), \
            patch.object(roles_mod, "VALID_ACTION_PHASES_BY_ROLE", {"sentinel": ["night_action"]}), \
            patch.object(persist_mod, "memory_store_paths", lambda d: (Path(t) / "o.json", Path(t) / "s.json")), \
            patch.object(persist_mod, "seed_memory_from_json_files_cached", lambda **kw: None), \
            patch.object(synth_mod, "fetch_observations_for_synth", lambda store, nskey: _OBS), \
            patch.object(synth_mod, "cluster_observations_for_synth",
                         lambda store, nskey, cfgd, items=None, seed_keys=None: (_OBS, [["o1"]])), \
            patch.object(synth_mod, "synthesize_cluster_sps",
                         lambda role, phase, live, items, max_retries=1, track_record="", model=None, outcome="verdict": [_FakeSP()]):
        store_ops.synthesize(Path(t), ns, {}, TickConfig(credit=False, incremental=False))
        log = [json.loads(line) for line in (Path(t) / "synthesis_log.jsonl").read_text().splitlines()]

    new = ns["strategy_points/sentinel/night_action"]
    assert new[0]["value"]["source_observations"] == ["o1"]
    assert len(log) == 1 and log[0]["source_observations"] == ["o1"]
    assert "approach: voted the quiet one" in log[0]["observations_text"]
    assert log[0]["strategy_points"][0]["key"] == new[0]["key"]


def test_the_tick_snapshot_keeps_the_synthesis_log():
    from Agents.memory.consolidation.db import export_snapshot

    with tempfile.TemporaryDirectory() as scratch, tempfile.TemporaryDirectory() as out:
        for name in ("observations.json", "strategy_points.json", "synthesis_log.jsonl"):
            (Path(scratch) / name).write_text("{}")
        snap = export_snapshot(scratch, Path(out) / "gen1", manifest={})
        assert (snap / "synthesis_log.jsonl").exists()
