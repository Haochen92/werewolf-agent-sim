"""The loop driver passes --experiment to its run_batch subprocess (so eval-case sidecars
nest under batch_results/<campaign>/) — verified without launching a game by stubbing
subprocess.run and inspecting the constructed command.
"""

from __future__ import annotations

from evaluation.src.loop import driver
from evaluation.src.loop.config import LoopConfig


def _capture_cmd(monkeypatch):
    captured = {}

    def fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        captured["kwargs"] = kwargs

    monkeypatch.setattr(driver.subprocess, "run", fake_run)
    return captured


def test_run_one_game_passes_experiment_flag(tmp_path, monkeypatch):
    captured = _capture_cmd(monkeypatch)
    driver._run_one_game(
        tmp_path / "out.jsonl", "pfx", LoopConfig(), "town_only", experiment="campaignX"
    )
    cmd = captured["cmd"]
    assert "--experiment" in cmd
    assert cmd[cmd.index("--experiment") + 1] == "campaignX"


def test_run_one_game_omits_experiment_when_absent(tmp_path, monkeypatch):
    captured = _capture_cmd(monkeypatch)
    driver._run_one_game(tmp_path / "out.jsonl", "pfx", LoopConfig(), "all_disabled")
    assert "--experiment" not in captured["cmd"]
