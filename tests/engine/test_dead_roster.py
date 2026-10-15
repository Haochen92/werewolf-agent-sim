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
from Agents.prompts.day_discuss import day_discuss_template
from Agents.prompts.day_vote import day_vote_template
from Agents.prompts.prompt_formatters import format_dead_roster
from Agents.prompts.prompt_inputs import build_agent_prompt_input
from Agents.schemas.game_events import DayVote, DeathRecord, FiringReason
from Agents.schemas.night import NightChoice
from Agents.schemas.roles import lineup, roles as POOL
from tests.leak_test import check_wolf_identity_isolation

LINEUP = lineup("serial_killer", "speculator")


def _fr() -> FiringReason:
    return FiringReason(tier="proactive", owes=[])


# --- (1) death paths append an ordered, role-revealing DeathRecord ----------

def test_night_kill_records_dead_with_revealed_role():
    night_state = {
        "current_day": 1,
        "roles": {"w0": "chanteuse", "t0": "sentinel", "h": "healer", "inv": "investigator"},
        "lineup": LINEUP,
        "surviving_wolves": ["w0"],
        "surviving_villagers": ["t0", "h", "inv"],
        "day_channel": [],
        "wolf_channel": [],
        "night_choices": [NightChoice("w0", "chanteuse", "kill", "t0")],
    }
    update = night_resolution(night_state, _runtime())
    roster = update["dead_roster"]
    assert roster == [DeathRecord(player="t0", role="sentinel", day=1, phase="night")]


def test_healed_target_produces_no_dead_record():
    night_state = {
        "current_day": 1,
        "roles": {"w0": "chanteuse", "t0": "sentinel", "h": "healer"},
        "lineup": LINEUP,
        "surviving_wolves": ["w0"],
        "surviving_villagers": ["t0", "h"],
        "day_channel": [],
        "wolf_channel": [],
        "night_choices": [
            NightChoice("w0", "chanteuse", "kill", "t0"),
            NightChoice("h", "healer", "protect", "t0"),  # saved -> no death
        ],
    }
    update = night_resolution(night_state, _runtime())
    assert "dead_roster" not in update  # no death this night


def test_lynch_records_dead_with_revealed_role():
    state = {
        "current_day": 2,
        "roles": {"w0": "chanteuse", "t0": "sentinel", "t1": "trailseer"},
        "lineup": LINEUP,
        "surviving_wolves": ["w0"],
        "surviving_villagers": ["t0", "t1"],
        "day_channel": [],
        "no_lynch_streak": 0,
        "day_votes": [
            DayVote(voter="t0", votee="w0"),
            DayVote(voter="t1", votee="w0"),
            DayVote(voter="w0", votee="t0"),
        ],
    }
    update = day_resolution(state, _runtime())
    assert update["dead_roster"] == [
        DeathRecord(player="w0", role="chanteuse", day=2, phase="day")
    ]


def test_no_lynch_day_produces_no_dead_record():
    state = {
        "current_day": 2,
        "roles": {"w0": "chanteuse", "t0": "sentinel", "t1": "trailseer"},
        "lineup": LINEUP,
        "surviving_wolves": ["w0"],
        "surviving_villagers": ["t0", "t1"],
        "day_channel": [],
        "no_lynch_streak": 0,
        "day_votes": [  # tie -> no lynch
            DayVote(voter="t0", votee="w0"),
            DayVote(voter="w0", votee="t0"),
        ],
    }
    update = day_resolution(state, _runtime())
    assert "dead_roster" not in update


# --- (2) roster on EVERY role's day payload + rendered block -----------------

_ROSTER = [
    DeathRecord(player="player_2", role="sentinel", day=1, phase="night"),
    DeathRecord(player="player_5", role="chanteuse", day=2, phase="day"),
]

# One living player per role of the pool: every role's payload is checked.
_PLAYERS = {f"p_{role}": role for role in POOL}
_WOLVES = [p for p, role in _PLAYERS.items() if role in ("chanteuse", "illusionist")]


def _day_state(**overrides) -> dict:
    s = {
        "current_day": 3,
        "current_round": 0,
        "roles": dict(_PLAYERS),
        "lineup": list(POOL),
        "human_players": [],
        "day_channel": [],
        "day_summaries": [],
        "dead_roster": _ROSTER,
        "wolf_channel": [],
        "surviving_wolves": list(_WOLVES),
        "surviving_villagers": [p for p in _PLAYERS if p not in _WOLVES],
        "agent_strategies": {},
        "night_actions": [],
        "uses_left": {"vigilante": 1, "sigilist": 2, "illusionist": 2, "speculator": 1, "fortune_teller": 1},
    }
    s.update(overrides)
    return s


def test_speaker_send_every_role_carries_roster():
    state = _day_state()
    for pid, role in _PLAYERS.items():
        send = build_speaker_send(state, pid, role, _fr())
        assert send.arg["dead_roster"] == _ROSTER, role


def test_fan_out_discuss_and_vote_every_role_carries_roster():
    for phase in ("discuss", "vote"):
        sends = fan_out_day(_day_state(), phase)
        assert len(sends) == len(_PLAYERS), phase
        assert all(s.arg["dead_roster"] == _ROSTER for s in sends), phase


def test_roster_block_rendered_in_discuss_and_vote_prompts_all_roles():
    state = _day_state(lineup=LINEUP)
    expected = "player_2 (sentinel, night 1), player_5 (chanteuse, lynched day 2)"
    for pid, role in _PLAYERS.items():
        if role not in LINEUP:
            continue
        pi = build_agent_prompt_input(build_speaker_send(state, pid, role, _fr()).arg)
        discuss = "\n".join(m.content for m in day_discuss_template(role).format_messages(**pi))
        vote = "\n".join(m.content for m in day_vote_template(role).format_messages(**pi))
        assert expected in discuss, role
        assert expected in vote, role


# --- (3) formatter: compact rendering + empty case --------------------------

def test_format_dead_roster_compact_and_empty():
    assert format_dead_roster([]) == "No one has died yet."
    assert (
        format_dead_roster(_ROSTER)
        == "player_2 (sentinel, night 1), player_5 (chanteuse, lynched day 2)"
    )
    # A death that did not reveal the role (a body the illusionist concealed) reads as such.
    unknown = [DeathRecord(player="p9", role="", day=1, phase="night", concealed=True)]
    assert format_dead_roster(unknown) == "p9 (role not revealed, night 1)"


# --- (4) leak sanity: a dead wolf on the public roster is not a leak ---------

def test_dead_wolf_on_roster_does_not_trip_wolf_identity_leak():
    # player_5 is a dead wolf publicly announced when lynched; it lives on the public roster but
    # NOT in any non-wolf's surviving_wolves field, so the living-ally leak check stays clean.
    state = _day_state(roles={**_PLAYERS, "player_5": "chanteuse"})
    entries = []
    for pid, role in _PLAYERS.items():
        pi = build_agent_prompt_input(build_speaker_send(state, pid, role, _fr()).arg)
        entries.append({"player_id": pid, "player_role": role, "prompt_input": pi})
    assert check_wolf_identity_isolation(entries, state["roles"]) == []
