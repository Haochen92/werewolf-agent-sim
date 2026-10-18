"""The claims as the deduction engine reads them (slice 9a, Agents/deduction/claim_view.py): the claim
ledger's fold, typed (catalogue Table E's preamble), on the public record of every seat, today's
claims from the speakers' own fields included."""

from __future__ import annotations

from Agents.deduction import public_record, seat_view_from_payload
from Agents.schemas.deduction import ActionClaim, RoleClaim
from Agents.schemas.game_events import DayChannel, DaySummary


def _line(day, seq, player, message, claim="none", actions=(), passed=False) -> dict:
    # Stored as a stored game or a frozen replay keeps it: plain dicts.
    return DayChannel(day=day, seq=seq, player=player, message=message, claim=claim, passed=passed,
                      claimed_night_actions=[dict(zip(("night", "action", "target", "result", "seen"), a))
                                             for a in actions]).model_dump()


def _summary(day, *claims) -> dict:
    return DaySummary(day=day, summary="(text)", structured={"accusations": [], "role_claims": list(claims)}).model_dump()


# AC1's day 2 (2f19d908), with a day-1 summary before it: player_3 claims the Trailseer and its
# follow today, player_7 says it went to player_8, player_5 (a human: no field) was transcribed.
DAY_CHANNEL = [
    _line(1, 0, "player_5", "I'm the healer."),
    _line(2, 0, "player_3", "Trailseer here: I followed player_7 last night and they went to player_8.",
          claim="trailseer", actions=[(1, "follow", "player_7", "not_said", ["player_8"])]),
    _line(2, 1, "player_7", "Fine, I went to player_8, but I'm not the chanteuse.",
          actions=[(1, "no_action", "", "not_said", [])], passed=True),  # held: never heard
    _line(2, 2, "player_6", "I watched player_2 last night: nobody came.", claim="sentinel",
          actions=[(1, "watch", "player_2", "no_visitors", [])]),
    _line(2, 3, "player_6", "Sorry, it was player_4 I watched, and still nobody.",
          actions=[(1, "watch", "player_4", "no_visitors", [])]),
]
SUMMARIES = [
    {"day": 1, "summary": "Night of day 1: no one died.", "source": "game_master"},
    _summary(1, {"player": "player_5", "claimed_role": "healer", "kind": "claimed",
                 "night_actions": [{"night": 1, "action": "protect", "target": "player_1", "result": "not_said"}]}),
]


def _payload(player: str) -> dict:
    return {"player_id": player, "player_role": "healer", "current_day": 2, "day_channel": DAY_CHANNEL,
            "day_summaries": SUMMARIES, "surviving_players": [f"player_{i}" for i in range(1, 11)]}


def test_todays_claims_are_typed_with_their_history_and_flags():
    claims = {c.player: c for c in seat_view_from_payload(_payload("player_8")).claims}
    assert list(claims) == ["player_5", "player_3", "player_6"]  # the held line claimed nothing

    (follow,) = claims["player_3"].actions
    assert follow == ActionClaim(claimant="player_3", day=2, night=1, action="follow", target="player_7",
                                 result="not_said", seen=("player_8",), latest=True, blocked=False,
                                 completed=False, seen_complete=False, source="speaker")
    assert claims["player_3"].roles == (RoleClaim(2, "trailseer", False),)

    old, new = claims["player_6"].actions
    assert (old.target, old.latest, new.target, new.latest) == ("player_2", False, "player_4", True)
    assert new.history == (old,) and new.completed and new.seen_complete

    (protect,) = claims["player_5"].actions  # transcribed by the summariser on day 1 (no field)
    assert (protect.source, protect.day, protect.night) == ("summary", 1, 0)  # night 1 had not happened on day 1


def test_a_withdrawn_role_stays_in_the_history():
    summaries = [*SUMMARIES, _summary(2, {"player": "player_5", "claimed_role": "healer", "kind": "retracted"})]
    payload = {**_payload("player_8"), "day_summaries": summaries}
    (p5,) = [c for c in seat_view_from_payload(payload).claims if c.player == "player_5"]
    assert p5.current_role is None and p5.withdrawn_roles == ("healer",)
    assert p5.roles == (RoleClaim(1, "healer", False), RoleClaim(2, "healer", True))


def test_the_claims_are_public_the_same_for_every_seat():
    records = [public_record(seat_view_from_payload(_payload(f"player_{i}"))) for i in range(1, 11)]
    assert records[0].claims and all(r.claims == records[0].claims for r in records)


def test_a_payload_with_no_transcript_has_no_claims():
    assert seat_view_from_payload({"player_id": "player_1"}).claims == []


def test_a_claimed_visit_went_ahead_with_its_action_unknown():
    channel = [_line(2, 0, "player_7", "Yes, I went to player_8 on night 1.", actions=[(1, "visit", "player_8", "not_said", [])])]
    (p7,) = seat_view_from_payload({"player_id": "player_8", "day_channel": channel, "day_summaries": []}).claims
    (visit,) = p7.actions
    assert (visit.action, visit.target, visit.night, visit.completed, visit.blocked) == ("visit", "player_8", 1, True, False)
