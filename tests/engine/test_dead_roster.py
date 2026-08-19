"""Structured public dead-roster (added 2026-07-05).

Agents used to reconstruct who is dead + their revealed role by parsing the game_master's death
prose out of day summaries/transcripts. Both current death paths announce the role publicly — a
night kill ("... They were a {role}.") and a lynch ("... was a {role}.") — so the roster is public
info. These tests pin: (1) each death path appends an ordered DeathRecord with the revealed role;
(2) the roster is seeded onto EVERY role's day payload (discuss + vote) and rendered as a compact
block; (3) the formatter's compact rendering (night vs lynch, and the empty case); (4) a dead wolf
on the public roster does NOT trip the wolf-identity leak check (its role was announced).
"""
from __future__ import annotations

from tests.factories.builders import night_runtime as _runtime

from Agents.nodes.day.flow import build_speaker_send, fan_out_day
from Agents.nodes.night.resolution import night_resolution
from Agents.nodes.orchestrator import day_resolution
from Agents.prompts.day_discuss import VILLAGER_DAY_DISCUSS, WOLF_DAY_DISCUSS
from Agents.prompts.day_vote import VILLAGER_DAY_VOTE, WOLF_DAY_VOTE
from Agents.prompts.prompt_formatters import format_dead_roster
from Agents.prompts.prompt_inputs import build_agent_prompt_input
from Agents.schemas.game_events import DayVote, DeathRecord, FiringReason
from tests.leak_test import check_wolf_identity_isolation


def _fr() -> FiringReason:
    return FiringReason(tier="proactive", owes=[])


# --- (1) death paths append an ordered, role-revealing DeathRecord ----------

def test_night_kill_records_dead_with_revealed_role():
    night_state = {
        "current_day": 1,
        "roles": {"w0": "wolf", "t0": "villager", "h": "healer", "inv": "investigator"},
        "surviving_wolves": ["w0"],
        "surviving_villagers": ["t0", "h", "inv"],
        "serial_killer_player": None,
        "healer_player": "h",
        "investigator_player": "inv",
        "vigilante_player": None,
        "day_channel": [],
        "wolf_channel": [],
        "wolves_kill_target": "t0",
        "healer_target": None,
        "serial_killer_target": None,
        "vigilante_target": None,
    }
    update = night_resolution(night_state, _runtime())
    roster = update["dead_roster"]
    assert roster == [DeathRecord(player="t0", role="villager", day=1, phase="night")]


def test_healed_target_produces_no_dead_record():
    night_state = {
        "current_day": 1,
        "roles": {"w0": "wolf", "t0": "villager", "h": "healer"},
        "surviving_wolves": ["w0"],
        "surviving_villagers": ["t0", "h"],
        "serial_killer_player": None,
        "healer_player": "h",
        "investigator_player": None,
        "vigilante_player": None,
        "day_channel": [],
        "wolf_channel": [],
        "wolves_kill_target": "t0",
        "healer_target": "t0",  # saved -> no death
        "serial_killer_target": None,
        "vigilante_target": None,
    }
    update = night_resolution(night_state, _runtime())
    assert "dead_roster" not in update  # no death this night


def test_lynch_records_dead_with_revealed_role():
    state = {
        "current_day": 2,
        "roles": {"w0": "wolf", "t0": "villager", "t1": "villager"},
        "surviving_wolves": ["w0"],
        "surviving_villagers": ["t0", "t1"],
        "day_channel": [],
        "no_lynch_streak": 0,
        "healer_player": None,
        "investigator_player": None,
        "serial_killer_player": None,
        "vigilante_player": None,
        "day_votes": [
            DayVote(voter="t0", votee="w0"),
            DayVote(voter="t1", votee="w0"),
            DayVote(voter="w0", votee="t0"),
        ],
    }
    update = day_resolution(state, _runtime())
    assert update["dead_roster"] == [
        DeathRecord(player="w0", role="wolf", day=2, phase="day")
    ]


def test_no_lynch_day_produces_no_dead_record():
    state = {
        "current_day": 2,
        "roles": {"w0": "wolf", "t0": "villager", "t1": "villager"},
        "surviving_wolves": ["w0"],
        "surviving_villagers": ["t0", "t1"],
        "day_channel": [],
        "no_lynch_streak": 0,
        "healer_player": None,
        "investigator_player": None,
        "serial_killer_player": None,
        "vigilante_player": None,
        "day_votes": [  # tie -> no lynch
            DayVote(voter="t0", votee="w0"),
            DayVote(voter="w0", votee="t0"),
        ],
    }
    update = day_resolution(state, _runtime())
    assert "dead_roster" not in update


# --- (2) roster on EVERY role's day payload + rendered block -----------------

_ROSTER = [
    DeathRecord(player="player_2", role="villager", day=1, phase="night"),
    DeathRecord(player="player_5", role="wolf", day=2, phase="day"),
]


def _day_state(**overrides) -> dict:
    s = {
        "current_day": 3,
        "current_round": 0,
        "roles": {"w0": "wolf", "t0": "villager", "inv": "investigator", "vig": "vigilante"},
        "human_players": [],
        "day_channel": [],
        "day_summaries": [],
        "dead_roster": _ROSTER,
        "wolf_channel": [],
        "surviving_wolves": ["w0"],
        "surviving_villagers": ["t0", "inv", "vig"],
        "agent_strategies": {},
        "investigator_results": [],
        "vigilante_results": [],
        "vigilante_bullets": 1,
    }
    s.update(overrides)
    return s


def test_speaker_send_every_role_carries_roster():
    state = _day_state()
    for pid, role in (("t0", "villager"), ("w0", "wolf"), ("inv", "investigator"), ("vig", "vigilante")):
        send = build_speaker_send(state, pid, role, _fr())
        assert send.arg["dead_roster"] == _ROSTER


def test_fan_out_discuss_and_vote_every_role_carries_roster():
    for phase in ("discuss", "vote"):
        sends = fan_out_day(_day_state(), phase)
        assert sends, phase
        assert all(s.arg["dead_roster"] == _ROSTER for s in sends), phase


def test_roster_block_rendered_in_discuss_and_vote_prompts_all_roles():
    state = _day_state()
    expected = "player_2 (villager, night 1), player_5 (wolf, lynched day 2)"
    for pid, role, discuss_tmpl, vote_tmpl in (
        ("t0", "villager", VILLAGER_DAY_DISCUSS, VILLAGER_DAY_VOTE),
        ("w0", "wolf", WOLF_DAY_DISCUSS, WOLF_DAY_VOTE),
    ):
        pi = build_agent_prompt_input(build_speaker_send(state, pid, role, _fr()).arg)
        discuss = "\n".join(m.content for m in discuss_tmpl.format_messages(**pi))
        vote = "\n".join(m.content for m in vote_tmpl.format_messages(**pi))
        assert expected in discuss, role
        assert expected in vote, role


# --- (3) formatter: compact rendering + empty case --------------------------

def test_format_dead_roster_compact_and_empty():
    assert format_dead_roster([]) == "No one has died yet."
    assert (
        format_dead_roster(_ROSTER)
        == "player_2 (villager, night 1), player_5 (wolf, lynched day 2)"
    )
    # A path that did not reveal the role (defensive: no current path does) degrades gracefully.
    unknown = [DeathRecord(player="p9", role="", day=1, phase="night")]
    assert format_dead_roster(unknown) == "p9 (role not revealed, night 1)"


# --- (4) leak sanity: a dead wolf on the public roster is not a leak ---------

def test_dead_wolf_on_roster_does_not_trip_wolf_identity_leak():
    # player_5 is a dead wolf publicly announced when lynched; it lives on the public roster but
    # NOT in any non-wolf's surviving_wolves field, so the living-ally leak check stays clean.
    state = _day_state(roles={"w0": "wolf", "player_5": "wolf", "t0": "villager"})
    entries = []
    for pid, role in (("t0", "villager"), ("w0", "wolf")):
        pi = build_agent_prompt_input(build_speaker_send(state, pid, role, _fr()).arg)
        entries.append({"player_id": pid, "player_role": role, "prompt_input": pi})
    assert check_wolf_identity_isolation(entries, state["roles"]) == []
