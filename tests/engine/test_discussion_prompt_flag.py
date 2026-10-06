"""WW_DISCUSSION_PROMPT (evidence/game_play_enhancement/discussion_evidence.md §3).

The switch is read once at import, so each setting runs in a fresh interpreter. v2 is the default
(2026-10-06; production had run it since 2026-10-03): each of its changes must land where the
agents will read it. v1 keeps the earlier prompts, for a comparison. (P2, the summary's drivers
question, left the switch in v3, and the v4 summary dropped village dynamics.)
"""
import json
import os
import subprocess
import sys

import pytest

_PROBE = """
import json
from Agents.prompts.common import GAME_RULES
from Agents.prompts.day_discuss import TONE_INSTRUCTION
from Agents.prompts.roles import ROLE_CORE_STRATEGY
from Agents.nodes.day.summary_agent import _SUMMARY_SCHEMA

print(json.dumps({
    "turn_order": "Turn order: the moderator decides who speaks next" in GAME_RULES,
    "short_target": "about 40-80 words" in TONE_INSTRUCTION,
    "old_cap": "under about 120 words" in TONE_INSTRUCTION,
    "claiming": {role: "Claiming a role:" in text for role, text in ROLE_CORE_STRATEGY.items()},
    "summary_fields": sorted(_SUMMARY_SCHEMA.model_fields),
}))
"""


def _probe(flag: str | None) -> dict:
    env = {k: v for k, v in os.environ.items() if k != "WW_DISCUSSION_PROMPT"}
    if flag is not None:
        env["WW_DISCUSSION_PROMPT"] = flag
    result = subprocess.run([sys.executable, "-c", _PROBE], capture_output=True, text=True, env=env)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout.strip().splitlines()[-1])


def test_v1_keeps_the_earlier_prompts():
    got = _probe("v1")
    assert not got["turn_order"]
    assert not got["short_target"] and got["old_cap"]
    assert not any(got["claiming"].values())
    # The day summary is unswitched: v4 (2026-10-04) records accusations and role claims only.
    assert got["summary_fields"] == ["accusations", "role_claims"]


@pytest.mark.parametrize("flag", [None, "v2"], ids=["default", "v2"])
def test_v2_the_default_applies_all_its_changes(flag):
    got = _probe(flag)
    assert got["turn_order"]
    assert got["short_target"] and not got["old_cap"]
    # only the two evil roles are told they may claim
    assert {r for r, on in got["claiming"].items() if on} == {"wolf", "serial_killer"}
    assert got["summary_fields"] == ["accusations", "role_claims"]


def test_investigator_results_name_the_night_and_the_check():
    from Agents.prompts.prompt_formatters import format_investigator_results
    from Agents.schemas.game_events import InvestigatorResult

    results = [InvestigatorResult(day=1, player_investigated="player_1", role_revealed="wolf"),
               InvestigatorResult(day=3, player_investigated="player_5", role_revealed="serial_killer")]
    assert format_investigator_results(results, current_day=4).splitlines() == [
        "Night 1: you investigated player_1, who is the wolf",
        "Night 3 (last night): you investigated player_5, who is the serial killer",
    ]
    assert "(last night)" not in format_investigator_results(results)  # no day known: no tag
    assert format_investigator_results([]) == "No investigations yet."
