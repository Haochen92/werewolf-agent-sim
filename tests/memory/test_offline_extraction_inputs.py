"""Games that ended before games saved their extraction input are rebuilt for the offline job
(decisions §11): a run_batch game from its record and decision cases, a served game from its wire
events. Both must give the input the post-game node would have saved."""

from Agents.memory.extraction.offline import input_from_event_log, input_from_run_records

_ROLES = {"player_1": "healer", "player_2": "chanteuse", "player_10": "illusionist"}
_LINEUP = ["healer", "chanteuse", "illusionist"]


def _night_record(day, actor, action, target, outcome):
    return {"day": day, "actor": actor, "action": action, "target": target, "outcome": outcome,
            "result": "", "seen": []}


def test_a_served_game_is_rebuilt_from_its_wire_events():
    events = [
        {"seq": 1, "type": "game_started", "day": 1, "lineup": _LINEUP},
        {"seq": 2, "type": "roles_assigned", "day": 1, "roles": _ROLES},
        {"seq": 3, "type": "speech", "day": 1, "channel_seq": 0, "player": "player_1", "message": "Hello.",
         "claim": "none"},
        {"seq": 4, "type": "strategy_update", "day": 1, "player": "player_1", "strategy": "old note"},
        {"seq": 5, "type": "wolf_message", "day": 1, "round": 1, "wolf": "player_2", "passed": False,
         "message": "Take player_1."},
        # the pack's record goes to each wolf; kept once
        *({"seq": 6 + i, "type": "night_record", "player": p, **_night_record(1, "wolves", "kill", "player_1", "Saved.")}
          for i, p in enumerate(("player_2", "player_10"))),
        {"seq": 8, "type": "night_result", "day": 1, "deaths": [{"player": "player_10", "role": "illusionist"}]},
        {"seq": 9, "type": "gm_message", "day": 2, "channel_seq": 1, "text": "Night of day 1: player_10 died."},
        {"seq": 10, "type": "strategy_update", "day": 2, "player": "player_1", "strategy": "new note"},
        {"seq": 11, "type": "game_over", "day": 2, "winner": "villagers"},
    ]
    case = input_from_event_log("g1", events)
    assert case.lineup == _LINEUP and case.roles == _ROLES and case.game_outcome == "villagers"
    assert "[Day 1] player_1 (healer): Hello." in case.formatted_discussions
    assert "[Day 2] game_master (unknown): Night of day 1: player_10 died." in case.formatted_discussions
    assert "[Day 1, Round 1] player_2: Take player_1." in case.formatted_discussions
    night = case.formatted_discussions.split("from the game engine) ===")[1]
    assert night.count("the wolves") == 1
    assert case.formatted_strategy_notes == "player_1 (healer): new note"


def test_a_run_batch_game_is_rebuilt_from_its_record_and_cases():
    game = {
        "game_id": "g2", "winner": "wolves", "roles": repr(_ROLES), "lineup": repr(_LINEUP),
        "day_channel": repr([{"day": 1, "seq": 0, "player": "player_1", "message": "Hi."}]),
        "night_resolutions": repr([{"day": 1, "deaths": ["player_1"],
                                    "records": [_night_record(1, "player_1", "protect", "player_2", "Quiet.")]}]),
    }
    chat = [{"day": 1, "round": 1, "wolf": "player_2", "message": "Go.", "vote": "", "passed": False}]
    cases = [
        {"player_id": "player_10", "updated_strategy": "wolf note", "private_context": {"wolf_channel": chat}},
        {"player_id": "player_1", "updated_strategy": "first"},
        {"player_id": "player_1", "updated_strategy": "last, written the night the seat died"},
        {"player_id": "player_2", "updated_strategy": "", "private_context": {"wolf_channel": chat}},
    ]
    case = input_from_run_records(game, cases)
    assert case.lineup == _LINEUP and case.game_outcome == "wolves"
    assert "[Day 1, Round 1] player_2: Go." in case.formatted_discussions
    assert case.formatted_discussions.count("player_2: Go.") == 1
    # seats in seat order (player_10 last); each seat's last note
    assert case.formatted_strategy_notes.splitlines() == [
        "player_1 (healer): last, written the night the seat died",
        "player_10 (illusionist): wolf note",
    ]
