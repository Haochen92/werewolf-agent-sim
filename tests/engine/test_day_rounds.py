"""The day with rounds (Phase 2): the opening, the discussion, the closing, run through the real day graph.

The day's shape lives in the graph's wiring and the routers, which no unit test of a single node
sees; here the graph runs for real with scripted players (no model), so the order of turns, the
transcript and the rounds' bookkeeping are the engine's own. The round nodes' units follow.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from Agents.config.langgraph import discussion_recursion_limit
from Agents.game_config import GameConfig
from Agents.graphs.day import build_day_graph
from Agents.nodes.day import actors, flow
from Agents.schemas import AddressedTarget, DayChannel, DayVote, RoundCandidate
from Agents.schemas.roles import lineup
from Agents.schemas.turn import ResolvedDayVote
from Agents.tracing import Metrics
from Agents.turn import resolve


ROLES = {
    "player_1": "sentinel",
    "player_2": "investigator",
    "player_3": "healer",
    "player_4": "chanteuse",
    "player_5": "illusionist",
}
LINEUP = lineup("serial_killer", "speculator")
SEATS = ["player_1", "player_2", "player_3", "player_4", "player_5"]
NO_REASONING = {"strategy": None, "strategy_verdicts": [], "memory_verdicts": [], "reads": []}


def accusation(target: str) -> AddressedTarget:
    return AddressedTarget(target=target, addressed_form="mention", stance="accusation")


def response(target: str) -> AddressedTarget:
    return AddressedTarget(target=target, addressed_form="response", stance="defense")


class ScriptedTable:
    """Stands in for every model call of the day. ``rounds`` maps (round, player) to a line;
    ``sweep`` maps a player to the lines they say on their sweep turns, in order; a reactive turn
    always answers its creditors. Anything unscripted is a pass. Every call is recorded."""

    def __init__(self, rounds=None, sweep=None):
        self.rounds = rounds or {}
        self.sweep = {}
        for player, lines in (sweep or {}).items():
            self.sweep[player] = list(lines)
        self.calls: list[dict] = []

    def turn(self, payload, config, runtime, phase, prompt, schema, output_key):
        firing = payload.get("firing_reason")
        call = {
            "player": payload["player_id"],
            "output_key": output_key,
            "day_round": payload.get("day_round"),
            "tier": firing.tier if firing is not None else None,
            "sweep": firing.sweep if firing is not None else None,
            "owes": list(firing.owes) if firing is not None else [],
        }
        self.calls.append(call)

        if output_key == "day_votes":
            return ResolvedDayVote(entry=DayVote(voter=payload["player_id"], votee="abstain"))

        line = self.line_for(payload, call)
        if line is None:
            decision = SimpleNamespace(pass_turn=True, message="", addressed_targets=[])
        else:
            message, targets = line
            decision = SimpleNamespace(pass_turn=False, message=message, addressed_targets=targets)
        return resolve.resolve_decision(decision, NO_REASONING, "day_channel", payload, [])

    def line_for(self, payload, call):
        player = payload["player_id"]
        if call["day_round"] in ("opening", "closing"):
            return self.rounds.get((call["day_round"], player))
        if call["tier"] == "reactive":
            targets = []
            for creditor in call["owes"]:
                targets.append(response(creditor))
            return ("That is not true.", targets)
        queued = self.sweep.get(player) or []
        if queued:
            return queued.pop(0)
        return None

    def calls_where(self, **match) -> list[dict]:
        found = []
        for call in self.calls:
            keep = True
            for key, value in match.items():
                if call[key] != value:
                    keep = False
            if keep:
                found.append(call)
        return found


@pytest.fixture
def play_day(monkeypatch):
    """Run one day of the real day graph with a scripted table; returns (final state, table)."""
    summaries: list[int] = []

    def fake_summary(current_day, messages, max_retries=1, **kwargs):
        summaries.append(current_day)
        return ("the day in brief", "fake-model", {})

    monkeypatch.setattr(flow, "run_day_summary_agent", fake_summary)
    monkeypatch.setattr(flow, "filter_openings", lambda entries: entries)
    monkeypatch.setattr(resolve, "line_echo_of", lambda message, player, earlier: "")

    def run(day: int, table: ScriptedTable, game_config: GameConfig | None = None):
        if game_config is None:
            game_config = GameConfig()
        monkeypatch.setattr(actors, "run_memory_informed_action", table.turn)
        state = {
            "current_day": day,
            "day_channel": [],
            "day_summaries": [],
            "dead_roster": [],
            "wolf_channel": [],
            "roles": dict(ROLES),
            "lineup": LINEUP,
            "human_players": [],
            "night_actions": [],
            "uses_left": {"illusionist": 2},
            # The engine's two buckets, wolves apart; the rounds must not follow this order.
            "surviving_villagers": ["player_1", "player_2", "player_3"],
            "surviving_wolves": ["player_5", "player_4"],
            "no_lynch_streak": 0,
            "agent_strategies": {},
            "day_votes": [],
        }
        config = {
            "configurable": {"game_config": game_config.model_dump(), "game_id": "rounds-test"},
            "recursion_limit": discussion_recursion_limit(game_config, len(SEATS)),
        }
        graph = build_day_graph().compile()
        final = graph.invoke(state, config=config, context={"metrics": Metrics()})
        return final, summaries

    return run


def todays_entries(final: dict, day: int) -> list[DayChannel]:
    entries = []
    for entry in final["day_channel"]:
        if entry.day == day:
            entries.append(entry)
    return entries


# --- day 1 ----------------------------------------------------------------------------------

def test_day_one_is_the_opening_and_the_summary_only(play_day):
    table = ScriptedTable(rounds={("opening", "player_2"): ("I am the investigator.", [])})

    final, summaries = play_day(1, table)

    opening_calls = table.calls_where(day_round="opening")
    asked = []
    for call in opening_calls:
        asked.append(call["player"])
    assert sorted(asked) == SEATS                       # every living player, once each
    assert len(table.calls) == len(opening_calls)        # no discussion, no closing, no vote
    assert table.calls_where(output_key="day_votes") == []
    assert summaries == [1]

    entries = todays_entries(final, 1)
    players = []
    seqs = []
    for entry in entries:
        players.append(entry.player)
        seqs.append(entry.seq)
        assert entry.day_round == "opening"
    assert players == SEATS                              # seat order, not the engine's buckets
    assert seqs == [0, 1, 2, 3, 4]                       # each its own position
    assert final["round_players"] == SEATS


# --- day 2: the opening feeds the discussion --------------------------------------------------

def test_a_player_accused_in_an_opening_answers_first(play_day):
    table = ScriptedTable(rounds={
        ("opening", "player_2"): ("I checked player_4 last night: Suspicious.", [accusation("player_4")]),
    })

    final, _ = play_day(2, table)

    discussion_calls = []
    for call in table.calls:
        if call["output_key"] == "day_channel" and call["day_round"] not in ("opening", "closing"):
            discussion_calls.append(call)
    first = discussion_calls[0]
    assert first["player"] == "player_4"
    assert first["tier"] == "reactive"
    assert first["owes"] == ["player_2"]

    # Then the sweep asks those who have not spoken: player_2 spoke in the opening and player_4
    # answered, so player_1, player_3 and player_5, in seat order.
    swept = []
    for call in discussion_calls[1:]:
        assert call["tier"] == "proactive"
        swept.append(call["player"])
    assert swept == ["player_1", "player_3", "player_5"]

    # One accuser is not a trial: no closing, straight to the vote.
    assert table.calls_where(day_round="closing") == []
    assert len(table.calls_where(output_key="day_votes")) == 5


# --- day 2: the closing --------------------------------------------------------------------

def test_the_closing_follows_a_discussion_that_ran_out_and_gets_no_replies(play_day):
    table = ScriptedTable(
        sweep={
            "player_1": [("player_5 voted against the healer.", [accusation("player_5")])],
            "player_3": [("player_5 is dodging every question.", [accusation("player_5")])],
        },
        rounds={
            ("closing", "player_5"): ("I am town, and player_1 is steering this.", [accusation("player_1")]),
        },
    )

    final, summaries = play_day(2, table)

    entries = todays_entries(final, 2)
    moderator_lines = []
    for entry in entries:
        if entry.player == "game_master":
            moderator_lines.append(entry)
    (announcement,) = moderator_lines
    assert announcement.message == ("Before the vote: player_5 has been accused by player_1 and "
                                    "player_3. player_5 gets a last word.")
    assert announcement.day_round == "closing"

    closing_calls = table.calls_where(day_round="closing")
    assert len(closing_calls) == 1
    assert closing_calls[0]["player"] == "player_5"
    assert final["round_players"] == ["player_5"]

    # The closing line is the day's last entry: its new accusation of player_1 opened no turn.
    last = entries[-1]
    assert last.player == "player_5"
    assert last.day_round == "closing"
    assert last.message == "I am town, and player_1 is steering this."
    assert announcement.seq == last.seq - 1

    closing_index = table.calls.index(closing_calls[0])
    after_closing = table.calls[closing_index + 1:]
    for call in after_closing:
        assert call["output_key"] == "day_votes"
    assert len(after_closing) == 5
    assert summaries == [2]


def test_the_closing_follows_a_discussion_that_hit_the_cap(play_day):
    # A cap of three real lines: player_1 accuses, player_5 answers, player_2 accuses (the cap),
    # player_5 answers the debt opened at the cap, and the day stops before the sweep reaches
    # player_3 and player_4.
    small_cap = GameConfig(min_discussion_utterances=3, discussion_utterance_multiplier=0.1)
    table = ScriptedTable(sweep={
        "player_1": [("player_5 voted against the healer.", [accusation("player_5")])],
        "player_2": [("player_5 changed their story.", [accusation("player_5")])],
    })

    final, _ = play_day(2, table, small_cap)

    discussion_players = []
    for call in table.calls:
        if call["output_key"] == "day_channel" and call["day_round"] not in ("opening", "closing"):
            discussion_players.append((call["player"], call["tier"]))
    assert discussion_players == [
        ("player_1", "proactive"),
        ("player_5", "reactive"),
        ("player_2", "proactive"),
        ("player_5", "reactive"),
    ]

    closing_calls = table.calls_where(day_round="closing")
    assert len(closing_calls) == 1
    assert closing_calls[0]["player"] == "player_5"
    entries = todays_entries(final, 2)
    moderator_lines = []
    for entry in entries:
        if entry.player == "game_master":
            moderator_lines.append(entry.message)
    assert moderator_lines == ["Before the vote: player_5 has been accused by player_1 and "
                               "player_2. player_5 gets a last word."]


# --- the round nodes, one at a time -------------------------------------------------------

def round_state(**over) -> dict:
    state = {
        "current_day": 2,
        "day_channel": [],
        "day_summaries": [],
        "roles": dict(ROLES),
        "lineup": LINEUP,
        "human_players": [],
        "surviving_villagers": ["player_1", "player_2", "player_3"],
        "surviving_wolves": ["player_5", "player_4"],
        "agent_strategies": {},
    }
    state.update(over)
    return state


def test_start_opening_lists_every_survivor_in_seat_order():
    update = flow.start_opening(round_state())

    assert update == {"day_round": "opening", "round_players": SEATS}


def test_fan_out_round_sends_one_turn_per_round_player_and_the_human_to_the_twin():
    state = round_state(day_round="opening", round_players=SEATS, human_players=["player_3"])

    sends = flow.fan_out_round(state, {})

    players = []
    for send in sends:
        players.append(send.arg["player_id"])
        assert send.arg["day_round"] == "opening"
        if send.arg["player_id"] == "player_3":
            assert send.node == "round_turn_human"
        else:
            assert send.node == "round_turn"
    assert players == SEATS


def test_fan_out_round_for_the_closing_sends_only_the_accused():
    state = round_state(day_round="closing", round_players=["player_5"])

    sends = flow.fan_out_round(state, {})

    assert len(sends) == 1
    assert sends[0].arg["player_id"] == "player_5"
    assert sends[0].arg["day_round"] == "closing"


def candidate(player: str, day_round: str, message: str, day: int = 2) -> RoundCandidate:
    entry = DayChannel(day=day, seq=0, player=player, message=message, day_round=day_round)
    return RoundCandidate(day=day, day_round=day_round, entry=entry)


def test_collect_round_plays_the_lines_in_round_order_and_numbers_them_after_today():
    earlier_today = [DayChannel(day=2, seq=0, player="player_1", message="earlier"),
                     DayChannel(day=2, seq=1, player="player_2", message="earlier")]
    yesterday = [DayChannel(day=1, seq=0, player="player_3", message="yesterday")]
    state = round_state(
        day_round="closing",
        round_players=["player_5", "player_4"],
        day_channel=yesterday + earlier_today,
        round_candidates=[
            candidate("player_1", "opening", "this morning's opening"),   # an earlier round today
            candidate("player_4", "closing", "my last word"),
            candidate("player_5", "closing", "and mine"),
            candidate("player_4", "closing", "last week", day=1),          # another day
        ],
    )

    update = flow.collect_round(state, {})

    written = update["day_channel"]
    summary = []
    for entry in written:
        summary.append((entry.player, entry.seq, entry.message))
    assert summary == [("player_5", 2, "and mine"), ("player_4", 3, "my last word")]


def test_collect_round_with_no_candidates_writes_nothing():
    state = round_state(day_round="opening", round_players=SEATS, round_candidates=[])

    assert flow.collect_round(state, {}) == {}


def test_route_after_round():
    config = {"configurable": {"game_config": GameConfig().model_dump()}}

    day_one_opening = round_state(current_day=1, day_round="opening")
    day_two_opening = round_state(current_day=2, day_round="opening")
    day_two_closing = round_state(current_day=2, day_round="closing")

    assert flow.route_after_round(day_one_opening, config) == "SUMMARIZE_DAY_DISCUSSION"
    assert flow.route_after_round(day_two_opening, config) == "SCHEDULE"
    assert flow.route_after_round(day_two_closing, config) == "SUMMARIZE_DAY_DISCUSSION"


def test_route_after_discussion_goes_to_the_closing_only_with_two_accusers():
    config = {"configurable": {"game_config": GameConfig().model_dump()}}
    one_accuser = [DayChannel(day=2, seq=0, player="player_1", message="x",
                              addressed_targets=[accusation("player_5")])]
    two_accusers = one_accuser + [DayChannel(day=2, seq=1, player="player_2", message="y",
                                             addressed_targets=[accusation("player_5")])]

    assert flow.route_after_discussion(round_state(day_channel=one_accuser), config, False) == \
        "SUMMARIZE_DAY_DISCUSSION"
    assert flow.route_after_discussion(round_state(day_channel=two_accusers), config, False) == \
        "START_CLOSING"
    assert flow.route_after_discussion(round_state(day_channel=two_accusers), config, True) == \
        "START_CLOSING"


def test_start_closing_writes_the_announcement_and_lists_the_accused_as_called():
    channel = [
        DayChannel(day=2, seq=0, player="player_1", message="a", addressed_targets=[accusation("player_4")]),
        DayChannel(day=2, seq=1, player="player_2", message="b", addressed_targets=[accusation("player_4")]),
        DayChannel(day=2, seq=2, player="player_1", message="c", addressed_targets=[accusation("player_5")]),
        DayChannel(day=2, seq=3, player="player_3", message="d", addressed_targets=[accusation("player_5")]),
    ]

    update = flow.start_closing(round_state(day_channel=channel), {})

    # Two accusers each; player_5 was accused more recently, so is called first.
    assert update["round_players"] == ["player_5", "player_4"]
    assert update["day_round"] == "closing"
    (announcement,) = update["day_channel"]
    assert announcement.player == "game_master"
    assert announcement.seq == 4
    assert announcement.message == ("Before the vote: player_5 has been accused by player_1 and player_3; "
                                    "player_4 by player_1 and player_2. Each gets a last word.")


def test_start_closing_refuses_to_run_with_nobody_on_trial():
    with pytest.raises(RuntimeError):
        flow.start_closing(round_state(), {})


def test_the_recursion_budget_allows_a_passing_turn_per_survivor_per_sweep():
    # A sweep turn that passes or is held consumes no cap, so each sweep needs its own room:
    # two super-steps (SCHEDULE, discuss) per survivor per sweep.
    no_sweeps = discussion_recursion_limit(GameConfig(max_proactive_sweeps=0), 7)
    two_sweeps = discussion_recursion_limit(GameConfig(max_proactive_sweeps=2), 7)

    assert two_sweeps - no_sweeps == 2 * 2 * 7
