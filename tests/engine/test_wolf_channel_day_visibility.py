"""Wolf `wolf_channel` visibility on DAY turns (extended 2026-07-05).

Wolves carry their private night channel (the pack's chat and the carrier's kill) into their day
discuss/vote turns, mirroring how every night actor gets its private record by day. The pack is
every role with ROLE_SPECS[role].pack: the chanteuse and the illusionist. These tests pin: (1)
both day builders attach the channel to the pack's roles and to NO other role; (2) the wolf day
prompts render the content while a town prompt never does; (3) the pack's whiff on an immune
target at night N reaches a wolf's day-(N+1) payload (in the pack's night record now: the
ten-seat engine writes no game-master note into the channel); (4) the formatter's conditional
vote suffix; (5) the re-scoped leak check accepts legit wolf day exposure but still flags a town
leak.
"""
from __future__ import annotations

from Agents.nodes.day.flow import build_speaker_send, fan_out_day
from Agents.nodes.night.resolution import night_resolution
from Agents.prompts.day_discuss import day_discuss_template
from Agents.prompts.day_vote import day_vote_template
from Agents.prompts.prompt_formatters import format_wolf_channel
from Agents.prompts.prompt_inputs import build_agent_prompt_input
from Agents.schemas.game_events import (
    DiscussionPassReason,
    FiringReason,
    WolfChannel,
)
from Agents.schemas.night import NightChoice
from Agents.schemas.roles import ROLE_SPECS, lineup, roles
from tests.leak_test import check_wolf_channel_isolation

from tests.factories.builders import night_runtime as _runtime

LINEUP = lineup("serial_killer", "speculator")

NOTE = WolfChannel(
    day=1,
    round=2,
    wolf="w1",
    message="sk shrugged off our kill last night, so sk must be the serial killer",
    vote="",
)


def _day_state(**overrides) -> dict:
    s = {
        "current_day": 2,
        "current_round": 0,
        "roles": {"w0": "chanteuse", "w1": "illusionist", "t0": "sentinel", "inv": "investigator"},
        "lineup": LINEUP,
        "human_players": [],
        "day_channel": [],
        "day_summaries": [],
        "wolf_channel": [NOTE],
        "surviving_wolves": ["w0", "w1"],
        "surviving_villagers": ["t0", "inv"],
        "agent_strategies": {},
        "night_actions": [],
        "uses_left": {"illusionist": 2},
    }
    s.update(overrides)
    return s


def _fr() -> FiringReason:
    return FiringReason(tier="proactive", owes=[])


# --- (1) both builders attach to wolves and to nobody else ------------------

def test_speaker_send_wolf_carries_channel_others_do_not():
    state = _day_state()
    for pid, role in (("w0", "chanteuse"), ("w1", "illusionist")):
        assert build_speaker_send(state, pid, role, _fr()).arg["wolf_channel"] == [NOTE], role

    # Every other role of the pool, on the same board.
    for role in roles:
        if ROLE_SPECS[role].pack:
            continue
        send = build_speaker_send({**state, "roles": {**state["roles"], "t0": role}}, "t0", role, _fr())
        assert "wolf_channel" not in send.arg, role


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
    for pid, role in (("w0", "chanteuse"), ("w1", "illusionist")):
        wolf_input = build_agent_prompt_input(
            build_speaker_send(_day_state(), pid, role, _fr()).arg
        )
        discuss = "\n".join(m.content for m in day_discuss_template(role).format_messages(**wolf_input))
        vote = "\n".join(m.content for m in day_vote_template(role).format_messages(**wolf_input))
        assert "sk must be the serial killer" in discuss, role
        assert "sk must be the serial killer" in vote, role
        # Confidentiality instruction is present in both.
        assert "never quote" in discuss.lower(), role
        assert "never quote" in vote.lower(), role

    town_input = build_agent_prompt_input(
        build_speaker_send(_day_state(), "t0", "sentinel", _fr()).arg
    )
    town = "\n".join(m.content for m in day_discuss_template("sentinel").format_messages(**town_input))
    assert "sk must be the serial killer" not in town


# --- (3) end-to-end-ish: the pack's night-N whiff reaches a wolf's day-(N+1) payload ---

def test_night_whiff_reaches_wolf_next_day_payload():
    roles_ = {"w0": "chanteuse", "w1": "illusionist", "sk": "serial_killer", "h": "healer", "t0": "sentinel"}
    night_state = {
        "current_day": 1,
        "roles": roles_,
        "lineup": LINEUP,
        "surviving_wolves": ["w0", "w1"],
        "surviving_villagers": ["sk", "h", "t0"],
        "day_channel": [],
        "wolf_channel": [],
        "night_choices": [NightChoice("w0", "chanteuse", "kill", "sk")],
    }
    update = night_resolution(night_state, _runtime())
    assert "wolf_channel" not in update  # the engine writes no note into the channel
    record = next(r for r in update["night_actions"] if r.actor == "wolves")
    assert record.result == "immune"

    # Day N+1: the night record is seeded into the day state; each wolf speaker's payload carries
    # the pack's record of the failed attack, and the town's does not.
    day_state = _day_state(
        current_day=2,
        roles=roles_,
        night_actions=update["night_actions"],
        surviving_wolves=["w0", "w1"],
        surviving_villagers=["sk", "h", "t0"],
    )
    for pid, role in (("w0", "chanteuse"), ("w1", "illusionist")):
        wolf_payload = build_speaker_send(day_state, pid, role, _fr()).arg
        assert record in wolf_payload["night_actions"], role
        assert record.outcome in build_agent_prompt_input(wolf_payload)["night_actions"], role
    town_payload = build_speaker_send(day_state, "t0", "sentinel", _fr()).arg
    assert record not in town_payload.get("night_actions", [])


# --- (4) formatter: conditional vote suffix ---------------------------------

def test_format_wolf_channel_conditional_vote_suffix():
    with_vote = WolfChannel(day=1, round=2, wolf="w0", message="target t0", vote="t0")
    empty_vote = NOTE  # a chat line, vote=""

    rendered_vote = format_wolf_channel([with_vote])
    assert "vote: t0" in rendered_vote

    rendered_empty = format_wolf_channel([empty_vote])
    assert "vote:" not in rendered_empty
    # no dangling suffix, but the message itself still renders
    assert "sk must be the serial killer" in rendered_empty


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
        "prompt_input": build_agent_prompt_input({**payload, "player_role": role, "lineup": LINEUP}),
    }


def test_leak_check_accepts_wolf_day_exposure():
    # Wolf day discuss + vote entries carrying the channel are legitimate, and so are the pack's
    # night turns: the chat, the carrier's kill and each wolf's skill.
    entries = [
        _entry("w0", "chanteuse", "day_channel", {"wolf_channel": [NOTE]}),
        _entry("w0", "chanteuse", "day_votes", {"wolf_channel": [NOTE]}),
        _entry("w0", "chanteuse", "wolf_channel", {"wolf_channel": [NOTE]}),
        _entry("w0", "chanteuse", "kill_target", {"wolf_channel": [NOTE]}),
        _entry("w0", "chanteuse", "block_target", {"wolf_channel": [NOTE]}),
        _entry("w1", "illusionist", "conceal", {"wolf_channel": [NOTE]}),
        _entry("t0", "sentinel", "day_channel", {}),
    ]
    assert check_wolf_channel_isolation(entries) == []


def test_leak_check_still_flags_town_entry():
    # Negative control: the channel in a non-wolf entry is still a leak.
    leaked = [_entry("t0", "sentinel", "day_votes", {"wolf_channel": [NOTE]})]
    assert check_wolf_channel_isolation(leaked) != []
