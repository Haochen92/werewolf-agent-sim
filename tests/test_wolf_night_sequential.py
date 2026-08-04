"""Wolf night sequential-talk -> parallel-vote: routing, round advance, tally, human contract.

The load-bearing invariants: talk rounds emit ONE Send at a time in surviving_wolves order (the
second speaker must be able to read the first), the vote round fans out every wolf in parallel,
the tally counts only binding-vote entries (talk entries and GM whiff notes carry vote=""), and a
lone wolf skips the talk entirely.
"""

import pytest

from Agents.nodes.night.wolf import (
    WOLF_TALK_ROUNDS,
    WOLF_VOTE_ROUND,
    collect_wolf_night_discussion,
    prepare_wolf_night,
    wolf_fan_out,
)
from Agents.schemas.game_events import DiscussionPassReason, WolfChannel
from Agents.schemas.human_player import HumanTurnRequest
from Agents.turn.human_turn import HumanTurnContractError, validate_human_response


def _entry(wolf, round_, message="...", vote="", day=1):
    return WolfChannel(day=day, round=round_, wolf=wolf, message=message, vote=vote)


def _state(wolf_channel=(), round_=1, wolves=("w1", "w2")):
    return {
        "day_channel": [], "day_summaries": [], "wolf_channel": list(wolf_channel),
        "surviving_wolves": list(wolves), "surviving_villagers": ["v1", "v2", "v3"],
        "agent_strategies": {}, "human_player": "", "current_day": 1,
        "current_round": round_,
    }


# ---- routing: sequential talk, parallel vote ------------------------------------------------------

def test_talk_round_sends_exactly_one_wolf_in_order():
    sends = wolf_fan_out(_state())
    assert len(sends) == 1
    assert sends[0].node == "WOLF_NIGHT_DISCUSS"
    assert sends[0].arg["player_id"] == "w1"


def test_second_speaker_fires_after_first_spoke():
    sends = wolf_fan_out(_state(wolf_channel=[_entry("w1", 1)]))
    assert [s.arg["player_id"] for s in sends] == ["w2"]


def test_generation_failure_pass_advances_to_next_wolf():
    failed = WolfChannel(
        day=1,
        round=1,
        wolf="w1",
        message="",
        vote="",
        passed=True,
        pass_reason=DiscussionPassReason.GENERATION_FAILED,
    )

    sends = wolf_fan_out(_state(wolf_channel=[failed]))

    assert [send.arg["player_id"] for send in sends] == ["w2"]


def test_vote_round_fans_out_every_wolf_in_parallel():
    sends = wolf_fan_out(_state(round_=WOLF_VOTE_ROUND))
    assert [s.node for s in sends] == ["WOLF_NIGHT_VOTE", "WOLF_NIGHT_VOTE"]
    assert [s.arg["player_id"] for s in sends] == ["w1", "w2"]


def test_lone_wolf_skips_talk_straight_to_vote():
    assert prepare_wolf_night(_state(wolves=("w1",)))["current_round"] == WOLF_VOTE_ROUND


def test_extinct_pack_emits_no_turns():
    # SK kill + lynch can wipe both wolves while the game continues (SK still alive): the
    # night must no-op, not crash. Regression: the sequential next() raised StopIteration here.
    assert wolf_fan_out(_state(wolves=())) == []


def test_extinct_pack_subgraph_runs_end_to_end_without_a_kill():
    # Zero wolves -> zero Sends -> zero LLM calls: safe to invoke the real compiled subgraph.
    from Agents.graphs.night.wolf import wolf_night_graph_compiled

    result = wolf_night_graph_compiled.invoke(_state(wolves=()))
    assert result.get("wolves_kill_target") is None


# ---- round advance: only when every wolf has spoken -----------------------------------------------

def test_partial_round_does_not_advance():
    assert collect_wolf_night_discussion(_state(wolf_channel=[_entry("w1", 1)])) == {}


def test_complete_round_advances():
    out = collect_wolf_night_discussion(
        _state(wolf_channel=[_entry("w1", 1), _entry("w2", 1)])
    )
    assert out == {"current_round": 2}


def test_last_talk_round_advances_into_the_vote_round():
    channel = [_entry(w, r) for r in (1, 2) for w in ("w1", "w2")]
    out = collect_wolf_night_discussion(_state(wolf_channel=channel, round_=WOLF_TALK_ROUNDS))
    assert out == {"current_round": WOLF_VOTE_ROUND}


# ---- tally: binding votes only --------------------------------------------------------------------

def test_tally_counts_only_vote_round_entries_with_a_vote():
    channel = [
        _entry("w1", 1, message="let's take v1"),                      # talk: no vote
        _entry("game_master", WOLF_VOTE_ROUND, message="whiff note"),  # GM note: vote=""
        _entry("w1", WOLF_VOTE_ROUND, message="", vote="v1"),
        _entry("w2", WOLF_VOTE_ROUND, message="", vote="v1"),
    ]
    out = collect_wolf_night_discussion(_state(wolf_channel=channel, round_=WOLF_VOTE_ROUND))
    assert out == {"wolves_kill_target": "v1"}


def test_split_vote_breaks_randomly_between_candidates():
    channel = [
        _entry("w1", WOLF_VOTE_ROUND, message="", vote="v1"),
        _entry("w2", WOLF_VOTE_ROUND, message="", vote="v2"),
    ]
    out = collect_wolf_night_discussion(_state(wolf_channel=channel, round_=WOLF_VOTE_ROUND))
    assert out["wolves_kill_target"] in {"v1", "v2"}


# ---- human contract for the split phases ----------------------------------------------------------

def _request(**over):
    base = dict(
        player_id="w1", role="wolf", phase="wolf_channel", day=1, instruction="",
        valid_targets=[], can_pass=False, dialogue="", day_summaries="",
        surviving_players=["w1", "w2", "v1"], dead_roster="", alive_roles="", firing_brief="",
        wolf_channel="", investigator_results="", vigilante_results="", previous_strategy="",
    )
    base.update(over)
    return HumanTurnRequest(**base)


def test_human_wolf_talk_is_message_only():
    assert validate_human_response(_request(), {"message": "v1 tonight?"}).message
    with pytest.raises(HumanTurnContractError):
        validate_human_response(_request(), {"message": "hi", "target": "v1"})
    with pytest.raises(HumanTurnContractError):
        validate_human_response(_request(), {"pass_turn": True})
    with pytest.raises(HumanTurnContractError):
        validate_human_response(_request(), {"message": "  "})


def test_human_wolf_vote_takes_a_valid_target_only():
    req = _request(phase="wolf_vote", valid_targets=["v1", "v2"])
    assert validate_human_response(req, {"target": "v2"}).target == "v2"
    with pytest.raises(HumanTurnContractError):
        validate_human_response(req, {"target": "w2"})
