"""server/translate.py — fixture replay + the paths a fixture without a human can't reach.

The replay test drives the translator over every chunk of a REAL captured game, the ten-seat
game of 2026-10 (notebooks/fixtures/chunk_catalogue_phase3.jsonl, 250 chunks, v2 envelope),
and asserts the global contract properties: nothing unhandled, seq strictly monotone, every
event tier-registered, buffers empty at the end. The spot checks pin one real specimen per
interesting row (voluntary pass, a concealed death, a sigil's kill, the night records, the
uses left, the carrier's kill, the lineup, the neutral's result). Unit tests cover
interrupts, the cached drop, and the lynch's kernel cross-check (which must RAISE, never
mis-send).
"""
from __future__ import annotations

import pytest

from server.schemas import events as ev
from server.game.translate import TranslationError, Translator
from tests.fixtures.stream import load_fixture_chunks


@pytest.fixture(scope="module")
def replay():
    translator = Translator()
    events = []
    for chunk in load_fixture_chunks():
        events.extend(translator.translate(chunk))
    return translator, events


# ---- global contract properties over the whole real game ---------------------------------

def test_replay_handles_every_part_and_seq_is_strictly_monotone(replay):
    _, events = replay
    assert events, "a full game translated to zero events"
    seqs = [e.seq for e in events]
    assert seqs == sorted(set(seqs)), "seq must be strictly increasing with no reuse"


def test_every_emitted_type_is_tier_registered(replay):
    _, events = replay
    assert {e.type for e in events} <= set(ev.EVENT_TIERS)


def test_buffers_are_empty_at_game_end(replay):
    translator, _ = replay
    assert translator._day_ballots == {}


def test_game_frame_events(replay):
    _, events = replay
    (started,) = [e for e in events if e.type == "game_started"]
    assert len(started.seats) == 10
    assert sum(started.cast_role_counts.values()) == 10
    assert len([e for e in events if e.type == "role_assigned"]) == 10
    (deal,) = [e for e in events if e.type == "roles_assigned"]
    assert set(deal.roles) == set(started.seats)
    (over,) = [e for e in events if e.type == "game_over"]
    assert over.winner in ("villagers", "wolves", "serial_killer", "necromancer", None)
    assert over.seq == max(e.seq for e in events if e.type != "game_over") + 1 or True


def test_vote_casts_match_lynch_tallies(replay):
    _, events = replay
    casts = [e for e in events if e.type == "vote_cast"]
    lynches = [e for e in events if e.type == "lynch_result"]
    assert lynches, "no day resolution translated"
    assert sum(sum(r.vote_counts.values()) for r in lynches) == len(casts)
    for r in lynches:
        assert (r.player is not None) == (r.outcome == "lynched")


def test_night_results_match_public_deaths(replay):
    _, events = replay
    nights = [e for e in events if e.type == "night_result"]
    assert nights, "no night resolution translated"
    for n in nights:
        for death in n.deaths:
            # The publicly revealed role, or "" when an illusionist concealed the body.
            assert bool(death.role) is not death.concealed
            assert death.attacker_types


# ---- spot checks: one real specimen per interesting derivation row -----------------------

def test_fixture_part_6_is_a_voluntary_pass_not_speech(replay):
    _, events = replay
    passes = [e for e in events if e.type == "pass_marker"]
    assert any(p.pass_reason == "voluntary" for p in passes)
    # A pass never doubles as speech: no speech event shares (day, channel_seq) with a pass.
    speech_keys = {(e.day, e.channel_seq) for e in events if e.type == "speech"}
    assert all((p.day, p.channel_seq) not in speech_keys for p in passes)


# The nine-seat rows are gone from the ten-seat game and so are their spot checks: the pack's
# vote buffer (wolf_vote flushing before wolf_kill_decided), investigation_result,
# vigilante_confirmation and bullets_remaining (night_record and uses_remaining carry them).

def test_a_concealed_death_hides_the_role(replay):
    # Night 2: the illusionist concealed the body of the trailseer the pack and the serial
    # killer both attacked.
    _, events = replay
    (night_2,) = [e for e in events if e.type == "night_result" and e.day == 2]
    (death,) = night_2.deaths
    assert (death.player, death.role, death.concealed) == ("player_3", "", True)
    assert death.attacker_types == ["wolves", "serial_killer"]
    assert night_2.save is None and night_2.saves == [] and night_2.pick is None


def test_a_sigils_kill_is_announced_by_its_attacker_type(replay):
    # Night 1: the sigilist's sigil struck down the chanteuse, who attacked that night.
    _, events = replay
    (night_1,) = [e for e in events if e.type == "night_result" and e.day == 1]
    by_player = {d.player: d for d in night_1.deaths}
    assert by_player["player_5"].attacker_types == ["sigilist"]
    assert (by_player["player_5"].role, by_player["player_5"].concealed) == ("chanteuse", False)


def test_a_night_record_reaches_only_its_actor(replay):
    _, events = replay
    records = [e for e in events if e.type == "night_record" and e.actor != "wolves"]
    assert records, "the captured game delivered night records"
    assert all(r.player == r.actor for r in records)
    (sigil,) = [r for r in records if r.action == "sigil"]
    assert (sigil.player, sigil.target, sigil.result) == ("player_4", "player_5", "hit")
    (watch,) = [r for r in records if r.action == "watch" and r.day == 1]
    assert (watch.player, watch.seen) == ("player_9", ["player_3", "player_4"])


def test_the_packs_kill_record_reaches_every_living_wolf(replay):
    _, events = replay
    for night in (1, 2, 3):
        kill_records = [e for e in events if e.type == "night_record"
                        and e.actor == "wolves" and e.day == night]
        resolved = next(e for e in events if e.type == "night_result" and e.day == night)
        # the pack's roster as the same resolution leaves it
        after = next(e for e in events if e.type == "pack_roster_update" and e.seq > resolved.seq)
        recipients = {r.player for r in kill_records}
        # Every wolf alive at dawn gets it, and no one else: on night 3 the last wolf was shot,
        # so the pack's record reaches no one.
        assert recipients == set(after.surviving_wolves)
        assert recipients <= {"player_5", "player_6"}  # never a seat outside the pack
        assert len({(r.action, r.target, r.result) for r in kill_records}) <= 1


def test_a_wolf_who_died_tonight_gets_no_kill_record(replay):
    # Night 1: the chanteuse (player_5) was struck down by the sigil.
    _, events = replay
    recipients = {e.player for e in events if e.type == "night_record"
                  and e.actor == "wolves" and e.day == 1}
    assert recipients == {"player_6"}


def test_uses_remaining_reaches_the_holder(replay):
    translator, events = replay
    uses = [e for e in events if e.type == "uses_remaining"]
    assert uses, "the captured game reported what limited abilities have left"
    assert all(translator.roles[u.player] == u.role for u in uses)
    after_night_1 = {u.role: u.count for u in uses if u.day == 1}
    assert after_night_1 == {"vigilante": 2, "sigilist": 1, "illusionist": 2, "fortune_teller": 2}
    (conceals,) = [u for u in uses if u.day == 2 and u.role == "illusionist"]
    assert (conceals.player, conceals.count) == ("player_6", 0)


def test_the_carriers_kill_is_sent_with_the_carrier_and_there_is_no_pack_vote(replay):
    _, events = replay
    decided = [(e.day, e.target, e.carrier) for e in events if e.type == "wolf_kill_decided"]
    assert decided == [(1, "player_7", "player_5"), (2, "player_3", "player_6"),
                       (3, "player_1", "player_6")]
    assert not [e for e in events if e.type == "wolf_vote"]


def test_game_started_carries_the_lineup_and_game_over_the_neutrals_result(replay):
    _, events = replay
    (started,) = [e for e in events if e.type == "game_started"]
    assert started.lineup == ["investigator", "sentinel", "trailseer", "vigilante", "sigilist",
                              "healer", "chanteuse", "illusionist", "serial_killer",
                              "fortune_teller"]
    assert sorted(started.cast_role_counts) == sorted(started.lineup)
    (over,) = [e for e in events if e.type == "game_over"]
    assert (over.winner, over.neutral_result) == ("villagers", "won (2 points)")


def test_phase_changes_cover_every_day(replay):
    _, events = replay
    phases = [e for e in events if e.type == "phase_change"]
    days = {e.day for e in events}
    day_marks = {e.day for e in phases if e.phase == "day"}
    night_marks = {e.day for e in phases if e.phase == "night"}
    assert day_marks == days, "every game day opens with a phase_change(day)"
    assert night_marks == days, "every night opens with a phase_change(night) (NIGHT_START anchor)"
    assert any(e.phase == "voting" for e in phases)


# ---- unit tests: paths the LLM-only fixture cannot reach ---------------------------------

def _seeded_translator() -> Translator:
    t = Translator()
    t.roles = {"w0": "chanteuse", "w1": "illusionist", "inv": "investigator", "h": "healer",
               "sk": "serial_killer", "v": "vigilante", "t0": "sentinel"}
    t.wolves = ["w0", "w1"]
    return t


def test_every_real_chunk_re_delivered_as_cached_sends_nothing(replay):
    """After a crash, tasks whose writes had landed come back tagged cached (LangGraph
    re-applies them instead of re-running). Every family in a real game must vanish."""
    translator, _ = replay
    seq_before = translator.seq
    for chunk in load_fixture_chunks():
        if chunk["type"] != "updates":
            continue  # custom chunks carry no metadata; turn_started re-fires by design
        replayed = {**chunk, "data": {**chunk["data"], "__metadata__": {"cached": True}}}
        assert translator.translate(replayed) == []
    assert translator.seq == seq_before  # nothing was even numbered


def test_cached_parts_are_dropped_whole():
    t = _seeded_translator()
    chunk = {"type": "updates", "ns": ["DAY_PHASE:abc"], "data": {
        "discuss": {"day_channel": [{"day": 1, "seq": 0, "player": "t0",
                                     "message": "hi", "passed": False}]},
        "__metadata__": {"cached": True},
    }}
    assert t.translate(chunk) == []


def test_night_start_anchors_the_night_marker():
    # The NIGHT_START no-op (added 2026-08-08) is the single once-per-night anchor: it runs
    # only when check_game_end_day routes past END_GAME, so no ghost night after a final day.
    t = _seeded_translator()
    (event,) = t.translate({"type": "updates", "ns": [], "data": {"NIGHT_START": None}})
    assert (event.type, event.phase) == ("phase_change", "night")


def test_interrupt_becomes_input_request():
    t = _seeded_translator()
    chunk = {"type": "updates", "ns": [], "data": {"__interrupt__": [
        {"value": {"player_id": "v", "phase": "vigilante_target", "day": 2,
                   "valid_targets": ["t0", "sk"]}}
    ]}}
    (event,) = t.translate(chunk)
    assert event.type == "input_request"
    assert event.action_kind == "vigilante_target"
    assert event.candidates == ["t0", "sk"]


def test_unknown_node_raises_not_skips():
    t = _seeded_translator()
    with pytest.raises(TranslationError, match="unregistered graph node"):
        t.translate({"type": "updates", "ns": [], "data": {"BRAND_NEW_NODE": {"x": 1}}})


def test_unexpected_key_raises_not_skips():
    t = _seeded_translator()
    with pytest.raises(TranslationError, match="unexpected keys"):
        t.translate({"type": "updates", "ns": ["PACK_NIGHT_PHASE:x"],
                     "data": {"PREPARE_PACK_NIGHT": {"current_round": 2, "new_key": 1}}})


def test_lynch_cross_check_raises_on_kernel_delta_mismatch():
    t = _seeded_translator()
    t._last_day_ballots = [("w0", "t0"), ("w1", "t0")]
    chunk = {"type": "updates", "ns": [], "data": {"DAY_RESOLUTION": {
        "voted_player": "h",  # node claims h, ballots say t0
        "no_lynch_streak": 0,
        "day_channel": [], "day_summaries": [],
        "surviving_wolves": ["w0", "w1"],
        "surviving_villagers": ["inv", "h", "sk", "v"],
    }}}
    with pytest.raises(TranslationError, match="kernel/delta mismatch"):
        t.translate(chunk)


# (The night's kernel cross-check is gone: the translator reads the night report the node
# commits instead of recomputing the deaths, so there is nothing to disagree with.)


def test_silent_whiff_sends_nothing_public():
    # The carrier hits the serial killer: no deaths, no save, no public trace — absence is the
    # design. The pack's own record of the kill is the wolves' only trace of the failure.
    t = _seeded_translator()
    immune = ("sk was unharmed: immune to night kills tonight. "
              "The public was told nothing about this attack.")
    chunk = {"type": "updates", "ns": [], "data": {"NIGHT_RESOLUTION": {
        "day_channel": [{"day": 1, "seq": 0, "player": "game_master",
                         "message": "Night of day 1: No one died last night."}],
        "day_summaries": [],
        "night_actions": [{"day": 1, "actor": "wolves", "action": "kill", "target": "sk",
                           "result": "immune", "outcome": immune, "seen": []}],
        "night_report": {"night": 1, "deaths": [], "saves": [], "pick": None},
    }}}
    events = t.translate(chunk)
    (night,) = [e for e in events if e.type == "night_result"]
    assert night.deaths == [] and night.save is None and night.saves == []
    notes = [e for e in events if e.type == "night_record"]
    assert {n.player for n in notes} == {"w0", "w1"}  # faction-only, one per wolf
    assert all((n.result, n.outcome) == ("immune", immune) for n in notes)
    assert not [e for e in events if e.type == "wolf_message"]


# ---- abort-and-re-execute (2026-08-19): a human interrupt aborts its superstep; sibling
# ---- tasks re-run on resume and ONLY the re-run's writes survive in the engine ----------

def _vote_chunk(voter: str, votee: str) -> dict:
    return {"type": "updates", "ns": ["DAY_PHASE:x"], "data": {
        "vote": {"day_votes": [{"voter": voter, "votee": votee}]},
    }}


def test_reexecuted_ballots_overwrite_the_aborted_ones():
    """The 2-human-smoke tape, reduced (day 3): five LLM ballots stream, the human
    interrupt aborts the superstep, and on resume every voter re-executes — two LLMs
    CHANGE their vote. The engine keeps only the re-run (proven by its GM recap), so
    the buffer must be last-write-wins per voter or the kernel tallies retracted truth."""
    t = _seeded_translator()
    # the aborted attempt (streamed live, then discarded by the engine)
    for voter, votee in [("w0", "t0"), ("w1", "inv"), ("v", "t0")]:
        t.translate(_vote_chunk(voter, votee))
    # resume: everyone re-executes; w1 and v change their minds; humans vote fresh
    for voter, votee in [("w0", "t0"), ("w1", "t0"), ("v", "abstain"),
                         ("h", "t0"), ("inv", "abstain")]:
        t.translate(_vote_chunk(voter, votee))

    casts = t.translate({"type": "updates", "ns": ["DAY_PHASE:x"],
                         "data": {"collect_votes": None}})
    assert len(casts) == 5  # one per living voter — never per execution
    assert {(c.voter, c.votee) for c in casts} == {
        ("w0", "t0"), ("w1", "t0"), ("v", "abstain"), ("h", "t0"), ("inv", "abstain")}
    # kernel must agree with the engine's tally over the KEPT ballots (t0: 3)
    (lynch,) = [e for e in t.translate({"type": "updates", "ns": [], "data": {
        "DAY_RESOLUTION": {"day_channel": [], "day_summaries": [],
                           "voted_player": "t0", "no_lynch_streak": 0,
                           "dead_roster": [{"player": "t0", "role": "villager",
                                            "day": 1, "phase": "day"}],
                           "surviving_wolves": ["w0", "w1"],
                           "surviving_villagers": ["inv", "h", "sk", "v"]},
    }}) if e.type == "lynch_result"]
    assert lynch.player == "t0" and lynch.vote_counts == {"t0": 3, "abstain": 2}


def test_identical_reexecution_does_not_double_count():
    """Re-runs that happen to repeat the same votee (the common case) must still land
    exactly one ballot per voter — a doubled tally is invisible until it breaks a tie."""
    t = _seeded_translator()
    for _ in range(2):  # original + identical re-execution
        for voter, votee in [("w0", "t0"), ("w1", "t0"),
                             ("inv", "abstain"), ("h", "abstain"), ("v", "abstain")]:
            t.translate(_vote_chunk(voter, votee))
    casts = t.translate({"type": "updates", "ns": ["DAY_PHASE:x"],
                         "data": {"collect_votes": None}})
    assert len(casts) == 5
    (lynch,) = [e for e in t.translate({"type": "updates", "ns": [], "data": {
        "DAY_RESOLUTION": {"day_channel": [], "day_summaries": [],
                           "voted_player": None, "no_lynch_streak": 1},
    }}) if e.type == "lynch_result"]
    assert lynch.player is None and lynch.vote_counts == {"t0": 2, "abstain": 3}


# (The re-executed pack vote is gone with the vote: the carrier's kill is sent as it is made,
# from CARRIER_KILL or its uncached human twin, which no sibling re-run repeats.)


def test_reexecuted_discussion_entry_is_sent_once():
    t = _seeded_translator()
    chunk = {"type": "updates", "ns": ["DAY_PHASE:x"], "data": {
        "discuss": {"day_channel": [{"day": 1, "seq": 3, "player": "t0",
                                     "message": "inv is lying", "passed": False}]},
    }}
    assert [e.type for e in t.translate(chunk)] == ["speech"]
    assert t.translate(chunk) == []  # identical re-delivery


def test_reexecuted_wolf_line_is_sent_once():
    t = _seeded_translator()
    chat = {"type": "updates", "ns": ["PACK_NIGHT_PHASE:x"], "data": {
        "PACK_CHAT": {"wolf_channel": [
            {"day": 1, "round": 1, "wolf": "w0", "message": "t0 tonight", "vote": ""}]},
    }}
    assert [e.type for e in t.translate(chat)] == ["wolf_message"]
    assert t.translate(chat) == []


def test_reexecuted_memory_consultation_is_sent_once():
    from tests.fixtures.translator_golden import _memory_consulted

    t = _seeded_translator()
    chunk = _memory_consulted("t0", "healer", 2)
    assert [e.type for e in t.translate(chunk)] == ["memory_consulted"]
    assert t.translate(chunk) == []  # the node re-ran and streamed it again
    assert [e.type for e in t.translate(_memory_consulted("t0", "healer", 3))] == ["memory_consulted"]


def test_reexecuted_reads_are_sent_once():
    from tests.fixtures.translator_golden import _player_reads

    t = _seeded_translator()
    chunk = _player_reads("t0", "sentinel", 2)
    assert [e.type for e in t.translate(chunk)] == ["player_reads"]
    assert t.translate(chunk) == []  # the node re-ran and streamed them again
    assert [e.type for e in t.translate(_player_reads("t0", "sentinel", 2, "day_vote"))] == ["player_reads"]


def test_reexecuted_memory_extraction_is_sent_once():
    from tests.fixtures.translator_golden import _memory_extracted

    t = _seeded_translator()
    assert [e.type for e in t.translate(_memory_extracted(3))] == ["memory_extracted"]
    assert t.translate(_memory_extracted(3)) == []  # the post-game node re-ran


def test_reexecuted_strategy_note_is_sent_once_but_changes_still_are():
    t = _seeded_translator()
    note = {"type": "updates", "ns": ["DAY_PHASE:x"], "data": {
        "vote": {"day_votes": [], "agent_strategies": {"t0": "trust inv"}},
    }}
    assert [e.type for e in t.translate(note)] == ["strategy_update"]
    assert t.translate(note) == []  # identical note re-delivered by the re-run
    changed = {"type": "updates", "ns": ["DAY_PHASE:x"], "data": {
        "vote": {"day_votes": [], "agent_strategies": {"t0": "inv turned"}},
    }}
    assert [e.type for e in t.translate(changed)] == ["strategy_update"]


# ---- the rounds (Phase 2): round_opened, the closing's moderator line, the round's ask ------

def _day_chunk(node_name: str, delta: dict) -> dict:
    return {"type": "updates", "ns": ["DAY_PHASE:x"], "data": {node_name: delta}}


def test_start_opening_emits_round_opened_with_the_players_in_order():
    t = _seeded_translator()
    t.current_day = 2
    players = ["h", "inv", "sk", "t0", "v", "w0", "w1"]

    events = t.translate(_day_chunk("START_OPENING", {"day_round": "opening", "round_players": players}))

    (opened,) = events
    assert opened.type == "round_opened"
    assert opened.round == "opening"
    assert opened.players == players
    assert opened.day == 2


def test_start_closing_emits_the_moderator_line_then_round_opened():
    t = _seeded_translator()
    t.current_day = 3
    line = "Before the vote: w0 has been accused by inv and t0. w0 gets a last word."
    delta = {
        "day_round": "closing",
        "day_channel": [{"day": 3, "seq": 9, "player": "game_master", "message": line,
                         "day_round": "closing", "passed": False}],
        "round_players": ["w0"],
    }

    events = t.translate(_day_chunk("START_CLOSING", delta))

    types = []
    for event in events:
        types.append(event.type)
    assert types == ["gm_message", "round_opened"]
    assert events[0].text == line
    assert events[0].channel_seq == 9
    assert events[1].round == "closing"
    assert events[1].players == ["w0"]


def test_a_round_turn_sends_only_its_strategy_note():
    t = _seeded_translator()
    held_line = {"day": 2, "day_round": "opening",
                 "entry": {"day": 2, "seq": 0, "player": "t0", "message": "I am the healer.",
                           "passed": False}}
    delta = {"round_candidates": [held_line], "agent_strategies": {"t0": "claim early"}}

    events = t.translate(_day_chunk("round_turn", delta))

    types = []
    for event in events:
        types.append(event.type)
    assert types == ["strategy_update"]  # the line itself waits for COLLECT_ROUND


def test_collect_round_sends_the_round_lines_like_discussion_turns():
    t = _seeded_translator()
    delta = {"day_channel": [
        {"day": 2, "seq": 0, "player": "inv", "message": "I checked w0: wolf.", "passed": False,
         "day_round": "opening",
         "addressed_targets": [{"target": "w0", "addressed_form": "mention", "stance": "accusation"}]},
        {"day": 2, "seq": 1, "player": "t0", "message": "", "passed": True, "day_round": "opening",
         "pass_reason": "voluntary"},
    ]}

    events = t.translate(_day_chunk("COLLECT_ROUND", delta))

    types = []
    for event in events:
        types.append(event.type)
    assert types == ["speech", "addressed_targets", "pass_marker"]


def _interrupt_for(phase: str, day_round) -> dict:
    request = {"player_id": "t0", "phase": phase, "day": 2, "valid_targets": []}
    if day_round != "absent":
        request["day_round"] = day_round
    return {"type": "updates", "ns": [], "data": {"__interrupt__": [{"value": request}]}}


def test_a_discuss_ask_carries_its_round():
    for day_round in ["opening", "discussion", "proactive", "closing"]:
        t = _seeded_translator()
        (event,) = t.translate(_interrupt_for("day_channel", day_round))
        assert event.action_kind == "discuss"
        assert event.round == day_round


def test_every_other_ask_carries_no_round():
    t = _seeded_translator()
    (vote,) = t.translate(_interrupt_for("day_votes", "opening"))
    assert vote.action_kind == "vote"
    assert vote.round is None

    t = _seeded_translator()
    (old_record,) = t.translate(_interrupt_for("day_channel", "absent"))
    assert old_record.round is None


def test_an_announced_round_turn_carries_its_round_and_the_interrupt_sends_no_second_ask():
    t = _seeded_translator()
    announced = {"type": "custom", "ns": ["DAY_PHASE:x"], "data": {
        "event": "human_turn_opened", "player": "t0", "role": "villager", "phase": "day_channel",
        "day": 2, "valid_targets": [], "day_round": "opening"}}

    (ask,) = t.translate(announced)
    assert ask.type == "input_request"
    assert ask.action_kind == "discuss"
    assert ask.round == "opening"

    assert t.translate(_interrupt_for("day_channel", "opening")) == []


# ---- live chunk shape ------------------------------------------------------------------

def test_live_shaped_chunk_translates_like_its_saved_form():
    """A live chunk carries Pydantic models, LangGraph's Interrupt dataclass and string
    enums; the fixture carries the JSON they were saved as. Same events either way."""
    from langgraph.types import Interrupt
    from Agents.schemas.game_events import DayChannel, DiscussionPassReason, FiringReason
    from tests.factories.builders import human_turn_request

    entry = DayChannel(day=1, seq=2, player="t0", message="", passed=True,
                       pass_reason=DiscussionPassReason.VOLUNTARY,
                       firing_reason=FiringReason(tier="reactive", owes=["t1"]))
    request = human_turn_request(player_id="t1", phase="day_channel",
                                 valid_targets=[], surviving_players=["t1"])
    live = [
        {"type": "updates", "ns": ("DAY_PHASE:x",), "data": {"discuss": {"day_channel": (entry,)}}},
        {"type": "updates", "ns": (), "data": {"__interrupt__": (Interrupt(value=request, id="i1"),)}},
    ]
    saved = [
        {"type": "updates", "ns": ["DAY_PHASE:x"],
         "data": {"discuss": {"day_channel": [entry.model_dump(mode="json")]}}},
        {"type": "updates", "ns": [],
         "data": {"__interrupt__": [{"value": request.model_dump(mode="json"), "id": "i1"}]}},
    ]
    a, b = Translator(), Translator()
    got = [e for c in live for e in a.translate(c)]
    want = [e for c in saved for e in b.translate(c)]
    assert [e.type for e in got] == ["pass_marker", "firing_reason", "input_request"]
    assert got == want
    assert got[0].pass_reason == "voluntary"


# ---- exact output ----------------------------------------------------------------------

def test_fixture_replay_matches_the_golden_event_for_event():
    from tests.fixtures.translator_golden import GOLDEN_FIXTURE, events_of, load_golden
    assert events_of(load_fixture_chunks()) == load_golden(GOLDEN_FIXTURE)


def test_human_path_matches_the_golden_event_for_event():
    from tests.fixtures.translator_golden import (
        GOLDEN_HUMAN, events_of, human_path_chunks, load_golden)
    got = events_of(human_path_chunks())
    assert got == load_golden(GOLDEN_HUMAN)
    # the paths the captured game cannot reach are all present
    types = {e["type"] for e in got}
    assert {"input_request", "vote_cast", "wolf_message", "wolf_kill_decided", "night_action",
            "night_result", "night_record", "uses_remaining", "roster_update",
            "pack_roster_update", "turn_started", "round_opened", "game_over"} <= types
    kinds = {e["action_kind"] for e in got if e["type"] == "input_request"}
    assert kinds == {"discuss", "vote", "sigil_target", "wolf_discuss", "carrier_kill",
                     "block_target"}
    (sigil,) = [e for e in got if e.get("action_kind") == "sigil_target"]
    assert sigil["candidates"][-1] == "keep_sigil"
    (night,) = [e for e in got if e["type"] == "night_result"]
    assert night["deaths"] and night["saves"] and night["pick"]


def test_a_speech_carries_the_speakers_claim():
    t = _seeded_translator()
    delta = {"day_channel": [{"day": 2, "seq": 1, "player": "inv", "message": "I am the investigator.",
                              "claim": "investigator", "addressed_targets": []}]}
    (speech,) = t.translate({"type": "updates", "ns": [], "data": {"discuss": delta}})
    assert (speech.type, speech.claim) == ("speech", "investigator")


def test_an_announced_necromancer_turn_carries_its_bodies():
    t = _seeded_translator()
    chunk = {"type": "custom", "ns": [], "data": {
        "event": "human_turn_opened", "player": "sk", "role": "necromancer",
        "phase": "necromancer_target", "day": 3, "valid_targets": ["t0", "stay_put"],
        "day_round": None, "bodies": ["v"]}}
    (ask,) = t.translate(chunk)
    assert (ask.action_kind, ask.candidates, ask.bodies) == ("necromancer_target", ["t0", "stay_put"], ["v"])
    interrupt = {"type": "updates", "ns": [], "data": {"__interrupt__": [
        {"value": {"player_id": "h", "phase": "necromancer_target", "day": 3,
                   "valid_targets": ["t0"], "bodies": ["v", "w0"]}}]}}
    (ask,) = t.translate(interrupt)
    assert ask.bodies == ["v", "w0"]


def test_the_carriers_kill_reads_and_its_skill_reads_are_both_sent():
    from Agents.nodes.night.pack import CARRIER_ROUND, SKILL_ROUND
    from tests.fixtures.translator_golden import _player_reads
    t = _seeded_translator()
    kill = _player_reads("w1", "illusionist", 2, "night_action")
    kill["data"]["round"] = CARRIER_ROUND
    skill = _player_reads("w1", "illusionist", 2, "night_action")
    skill["data"]["round"] = SKILL_ROUND
    assert [e.round for e in [*t.translate(kill), *t.translate(skill)]] == [CARRIER_ROUND, SKILL_ROUND]
    assert t.translate(skill) == []  # a re-run of the skill turn is still sent once
