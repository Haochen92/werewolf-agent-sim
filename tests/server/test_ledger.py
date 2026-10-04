"""The claim ledger endpoint: each morning's ledger, rebuilt from the game's public events.

Pins that it is the agents' own ledger (same lines, same checks), dated to the morning it was
read (a day's claims show from the next morning, checked against the deaths announced by then,
and a summary no morning followed is left out), that it reads a running game's log, and that
the structured summary it rests on is public.
"""
from __future__ import annotations

from server.game.entitlement import entitled
from server.game.ledger import ledger_days
from server.schemas import events as ev
from tests.fixtures.server import FakeGraph


def _claims(*claims):
    return {"accusations": [], "role_claims": list(claims)}


def _game(*, ended_on_day_2=False):
    healer = {"player": "p6", "claimed_role": "healer", "kind": "claimed", "night_actions": [],
              "planned_actions": [{"action": "protect", "target": "p1"}]}
    later = {"player": "p6", "claimed_role": "healer", "kind": "claimed", "planned_actions": [],
             "night_actions": [{"night": 2, "action": "protect", "target": "p3", "result": "saved_from_attack",
                                "reason": ""}]}
    events = [
        ev.GameStarted(seq=1, day=1, seats=["p1", "p3", "p6"], cast_role_counts={"healer": 1, "villager": 2}),
        ev.PhaseChange(seq=2, day=1, phase="day"),
        ev.DaySummaryStructured(seq=3, day=1, data=_claims(healer)),
        ev.GmMessage(seq=4, day=1, channel_seq=1, text="Night of day 1: p1 was killed by the wolves last night."),
        ev.NightResult(seq=5, day=1, deaths=[ev.NightDeath(player="p1", role="villager", attacker_types=["wolves"])]),
        ev.PhaseChange(seq=6, day=2, phase="day"),
        ev.DaySummaryStructured(seq=7, day=2, data=_claims(later)),
    ]
    if not ended_on_day_2:
        events += [ev.GmMessage(seq=8, day=2, channel_seq=2, text="Night of day 2: No one died last night."),
                   ev.PhaseChange(seq=9, day=3, phase="day")]
    return events


def test_each_morning_reads_the_earlier_days_checked_against_the_deaths_by_then():
    day2, day3 = ledger_days(_game())
    assert (day2.day, day3.day) == (2, 3)
    [p6] = day2.players
    assert p6.history == "claimed healer (day 1)"
    [plan] = p6.entries
    assert (plan.reported, plan.planned, plan.text) == (False, "p1", "Night 1: on day 1 said they planned to protect p1.")
    assert [(c.text, c.fits) for c in plan.checks] == [("Record: p1 died that night.", None)]
    # the claimed save on night 2 is checked against night 2's announcement, from day 3 on
    saved = day3.players[0].entries[-1]
    assert saved.text == "Night 2: protected p3, says they saved them from an attack."
    assert [(c.text, c.fits) for c in saved.checks] == [("Record: no save of p3 was announced that night.", False)]


def test_a_summary_no_morning_followed_is_left_out():
    assert [d.day for d in ledger_days(_game(ended_on_day_2=True))] == [2]


def test_the_structured_summary_is_public():
    event = ev.DaySummaryStructured(seq=1, day=1, data=_claims())
    assert entitled(event, "", {}, game_over=False)


def test_a_running_game_serves_its_ledger(api_client, quiet_session):
    session = quiet_session(FakeGraph([]))
    session.log.extend(_game())
    api_client.app.state.resources.games._register(session)
    body = api_client.get(f"/games/{session.game_id}/ledger").json()
    assert [d["day"] for d in body] == [2, 3]
    assert body[0]["players"][0]["entries"][0]["checks"] == [{"text": "Record: p1 died that night.", "fits": None}]
