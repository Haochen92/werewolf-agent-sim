"""run_batch resolves the experiment-folder name: structured by default, --flat opts out."""

from __future__ import annotations

import argparse

from scripts.run_batch import resolve_experiment


def _args(flat=False, experiment=None):
    return argparse.Namespace(flat=flat, experiment=experiment)


def test_default_uses_session_prefix():
    # No --experiment, no --flat → structured under the session prefix (the default).
    assert resolve_experiment(_args(), "batch_20260629_x") == "batch_20260629_x"


def test_explicit_experiment_wins():
    assert resolve_experiment(_args(experiment="town_only_run3"), "batch_x") == "town_only_run3"


def test_flat_opts_out_even_with_experiment():
    # --flat is the escape hatch: legacy flat layout regardless of --experiment.
    assert resolve_experiment(_args(flat=True, experiment="town_only_run3"), "batch_x") is None


def test_paired_game_ids_refuse_more_than_one_config_per_process(tmp_path, monkeypatch, capsys):
    # Arms paired by game id share the checkpointer's thread and the node-cache key, both
    # process-wide: a second arm would resume on the first arm's finished game.
    import json
    import sys

    from scripts.run_batch import parse_args, run_batch

    ids = tmp_path / "ids.json"
    ids.write_text(json.dumps(["game-a", "game-b"]))
    monkeypatch.setattr(sys, "argv", ["run_batch", "--configs", "all_disabled", "town_only",
                                      "--game-ids-file", str(ids), "--dry-run"])
    assert run_batch(parse_args()) == 2
    assert "one process per config" in capsys.readouterr().err
