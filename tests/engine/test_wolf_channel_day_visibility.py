"""Wolf `wolf_channel` visibility on DAY turns (extended 2026-07-05).

Wolves now carry their private night channel (coordination + GM whiff notes) into their day
discuss/vote turns, mirroring how the investigator/vigilante get their private results by day.
These tests pin: (1) both day builders attach the channel to wolves and to NO other role; (2) the
wolf day prompts render the content while a town prompt never does; (3) a whiff note written at
night N reaches a wolf's day-(N+1) payload; (4) the formatter's conditional vote suffix; (5) the
re-scoped leak check accepts legit wolf day exposure but still flags a town leak.
"""
from __future__ import annotations

from Agents.nodes.day.flow import build_speaker_send, fan_out_day
from Agents.nodes.night.resolution import night_resolution
from Agents.prompts.day_discuss import VILLAGER_DAY_DISCUSS, WOLF_DAY_DISCUSS
from Agents.prompts.day_vote import WOLF_DAY_VOTE
from Agents.prompts.prompt_formatters import format_wolf_channel
from Agents.prompts.prompt_inputs import build_agent_prompt_input
from Agents.schemas.game_events import (
    DiscussionPassReason,
    FiringReason,
    WolfChannel,
)
from tests.leak_test import check_wolf_channel_isolation

from tests.factories.builders import night_runtime as _runtime


NOTE = WolfChannel(
    day=1,
    round=2,
    wolf="game_master",
    message="your kill on sk failed — immune to night kills, which confirms sk is the serial killer",
    vote="",
)


def _day_state(**overrides) -> dict:
    s = {
        "current_day": 2,
        "current_round": 0,
        "roles": {"w0": "wolf", "w1": "wolf", "t0": "villager", "inv": "investigator"},
        "human_player": "",
        "day_channel": [],
        "day_summaries": [],
        "wolf_channel": [NOTE],
        "surviving_wolves": ["w0", "w1"],
        "surviving_villagers": ["t0", "inv"],
        "agent_strategies": {},
        "investigator_results": [],
        "vigilante_results": [],
        "vigilante_bullets": 0,
    }
    s.update(overrides)
    return s


def _fr() -> FiringReason:
    return FiringReason(tier="proactive", owes=[])


# --- (1) both builders attach to wolves and to nobody else ------------------

def test_speaker_send_wolf_carries_channel_others_do_not():
    state = _day_state()
    wolf = build_speaker_send(state, "w0", "wolf", _fr())
    assert wolf.arg["wolf_channel"] == [NOTE]

    for pid, role in (("t0", "villager"), ("inv", "investigator")):
        send = build_speaker_send(state, pid, role, _fr())
        assert "wolf_channel" not in send.arg


def test_fan_out_vote_wolf_carries_channel_others_do_not():
    sends = fan_out_day(_day_state(), "vote")
    by_player = {s.arg["player_id"]: s.arg for s in sends}
    assert by_player["w0"]["wolf_channel"] == [NOTE]
    assert by_player["w1"]["wolf_channel"] == [NOTE]
    assert "wolf_channel" not in by_player["t0"]
    assert "wolf_channel" not in by_player["inv"]


def test_fan_out_discuss_wolf_carries_channel_others_do_not():
    sends = fan_out_day(_day_state(), "discuss")
    by_player = {s.arg["player_id"]: s.arg for s in sends}
    assert by_player["w0"]["wolf_channel"] == [NOTE]
    assert "wolf_channel" not in by_player["t0"]


# --- (2) prompt render: wolf sees it, town never does -----------------------

def test_wolf_day_prompts_render_channel_town_does_not():
    wolf_input = build_agent_prompt_input(
        build_speaker_send(_day_state(), "w0", "wolf", _fr()).arg
    )
    discuss = "\n".join(m.content for m in WOLF_DAY_DISCUSS.format_messages(**wolf_input))
    vote = "\n".join(m.content for m in WOLF_DAY_VOTE.format_messages(**wolf_input))
    assert "confirms sk is the serial killer" in discuss
    assert "confirms sk is the serial killer" in vote
    # Confidentiality instruction is present in both.
    assert "never quote" in discuss.lower()
    assert "never quote" in vote.lower()

    town_input = build_agent_prompt_input(
        build_speaker_send(_day_state(), "t0", "villager", _fr()).arg
    )
    town = "\n".join(m.content for m in VILLAGER_DAY_DISCUSS.format_messages(**town_input))
    assert "confirms sk is the serial killer" not in town


# --- (3) end-to-end-ish: night-N whiff note reaches a wolf's day-(N+1) payload ---

def test_night_whiff_note_reaches_wolf_next_day_payload():
    night_state = {
        "current_day": 1,
        "roles": {"w0": "wolf", "w1": "wolf", "sk": "serial_killer", "h": "healer", "t0": "villager"},
        "surviving_wolves": ["w0", "w1"],
        "surviving_villagers": ["sk", "h", "t0"],
        "serial_killer_player": "sk",
        "healer_player": "h",
        "investigator_player": None,
        "vigilante_player": None,
        "day_channel": [],
        "wolf_channel": [],
        "wolves_kill_target": "sk",
        "healer_target": None,
        "serial_killer_target": None,
        "vigilante_target": None,
    }
    update = night_resolution(night_state, _runtime())
    note = update["wolf_channel"][0]

    # Day N+1: the accumulated wolf_channel is seeded into the day state; a wolf speaker's payload
    # must carry the night's note.
    day_state = _day_state(
        current_day=2,
        wolf_channel=[note],
        roles={"w0": "wolf", "w1": "wolf", "t0": "villager"},
        surviving_wolves=["w0", "w1"],
        surviving_villagers=["t0"],
    )
    wolf_payload = build_speaker_send(day_state, "w0", "wolf", _fr()).arg
    assert note in wolf_payload["wolf_channel"]
    assert note.message in build_agent_prompt_input(wolf_payload)["wolf_channel"]


# --- (4) formatter: conditional vote suffix ---------------------------------

def test_format_wolf_channel_conditional_vote_suffix():
    with_vote = WolfChannel(day=1, round=2, wolf="w0", message="target t0", vote="t0")
    empty_vote = NOTE  # GM whiff note, vote=""

    rendered_vote = format_wolf_channel([with_vote])
    assert "vote: t0" in rendered_vote

    rendered_empty = format_wolf_channel([empty_vote])
    assert "vote:" not in rendered_empty
    # no dangling suffix, but the message itself still renders
    assert "confirms sk is the serial killer" in rendered_empty


def test_format_wolf_channel_hides_generation_failure_pass():
    technical_pass = WolfChannel(
        day=1,
        round=1,
        wolf="w0",
        message="",
        vote="",
        passed=True,
        pass_reason=DiscussionPassReason.GENERATION_FAILED,
    )

    assert format_wolf_channel([technical_pass]) == "No messages yet."
    assert "generation_failed" not in format_wolf_channel([NOTE, technical_pass])


# --- (5) re-scoped leak check -----------------------------------------------

def _entry(player_id: str, role: str, output_key: str, payload: dict) -> dict:
    return {
        "player_id": player_id,
        "player_role": role,
        "output_key": output_key,
        "prompt_input": build_agent_prompt_input({**payload, "player_role": role}),
    }


def test_leak_check_accepts_wolf_day_exposure():
    # Wolf day discuss + vote entries carrying the channel are legitimate now.
    entries = [
        _entry("w0", "wolf", "day_channel", {"wolf_channel": [NOTE]}),
        _entry("w0", "wolf", "day_votes", {"wolf_channel": [NOTE]}),
        _entry("w0", "wolf", "wolf_channel", {"wolf_channel": [NOTE]}),
        _entry("t0", "villager", "day_channel", {}),
    ]
    assert check_wolf_channel_isolation(entries) == []


def test_leak_check_still_flags_town_entry():
    # Negative control: the channel in a non-wolf entry is still a leak.
    leaked = [_entry("t0", "villager", "day_votes", {"wolf_channel": [NOTE]})]
    assert check_wolf_channel_isolation(leaked) != []
