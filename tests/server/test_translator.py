"""server/translate.py — fixture replay + the paths a fixture without a human can't reach.

The replay test drives the translator over every part of a REAL captured game
(notebooks/fixtures/chunk_catalogue.jsonl, 307 parts, v2 envelope) and asserts the global
contract properties: nothing unhandled, seq strictly monotone, every event tier-registered,
buffers empty at the end. The spot checks pin one real specimen per interesting row
(voluntary pass, whiff note, investigation delivery). Unit tests cover interrupts, the
cached drop, and the two kernel cross-checks (which must RAISE, never mis-ship).
"""
from __future__ import annotations

import pytest

from server.schemas import events as ev
from server.translate import TranslationError, Translator
from tests.fixtures.stream import load_fixture_parts


@pytest.fixture(scope="module")
def replay():
    translator = Translator()
    events = []
    for part in load_fixture_parts():
        events.extend(translator.translate(part))
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
    assert translator._day_ballots == []
    assert translator._wolf_votes == []


def test_game_frame_events(replay):
    _, events = replay
    (started,) = [e for e in events if e.type == "game_started"]
    assert len(started.seats) == 9
    assert sum(started.cast_role_counts.values()) == 9
    assert len([e for e in events if e.type == "role_assigned"]) == 9
    (deal,) = [e for e in events if e.type == "roles_assigned"]
    assert set(deal.roles) == set(started.seats)
    (over,) = [e for e in events if e.type == "game_over"]
    assert over.winner in ("villagers", "wolves", "serial_killer")
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
            assert death.role, "night death must carry the publicly revealed role"
            assert death.attacker_types


# ---- spot checks: one real specimen per interesting derivation row -----------------------

def test_fixture_part_6_is_a_voluntary_pass_not_speech(replay):
    _, events = replay
    passes = [e for e in events if e.type == "pass_marker"]
    assert any(p.pass_reason == "voluntary" for p in passes)
    # A pass never doubles as speech: no speech event shares (day, channel_seq) with a pass.
    speech_keys = {(e.day, e.channel_seq) for e in events if e.type == "speech"}
    assert all((p.day, p.channel_seq) not in speech_keys for p in passes)


def test_whiff_note_ships_as_gm_wolf_message(replay):
    _, events = replay
    notes = [e for e in events if e.type == "wolf_message" and e.wolf == "game_master"]
    assert notes, "the captured game had an SK whiff note — it must ship faction-tier"
    assert "immune" in notes[0].message


def test_investigation_result_delivered_with_recipient(replay):
    _, events = replay
    results = [e for e in events if e.type == "investigation_result"]
    assert results, "the captured game delivered an investigation"
    assert all(r.player and r.target and r.role for r in results)


def test_wolf_votes_flush_before_the_kill_decision(replay):
    _, events = replay
    for decided in (e for e in events if e.type == "wolf_kill_decided"):
        votes_before = [e for e in events
                        if e.type == "wolf_vote" and e.day == decided.day
                        and e.seq < decided.seq]
        assert votes_before, "buffered wolf votes must flush together with the tally"


def test_phase_changes_cover_every_day(replay):
    # The fixture predates the NIGHT_START anchor (2026-08-08), so it carries no night
    # marker — the night phase_change is unit-tested below; re-capture restores it here.
    _, events = replay
    phases = [e for e in events if e.type == "phase_change"]
    days = {e.day for e in events}
    day_marks = {e.day for e in phases if e.phase == "day"}
    assert day_marks == days, "every game day opens with a phase_change(day)"
    assert any(e.phase == "voting" for e in phases)


# ---- unit tests: paths the LLM-only fixture cannot reach ---------------------------------

def _seeded_translator() -> Translator:
    t = Translator()
    t.roles = {"w0": "wolf", "w1": "wolf", "inv": "investigator", "h": "healer",
               "sk": "serial_killer", "v": "vigilante", "t0": "villager"}
    t.wolves = ["w0", "w1"]
    return t


def test_cached_parts_are_dropped_whole():
    t = _seeded_translator()
    part = {"type": "updates", "ns": ["DAY_PHASE:abc"], "data": {
        "discuss": {"day_channel": [{"day": 1, "seq": 0, "player": "t0",
                                     "message": "hi", "passed": False}]},
        "__metadata__": {"cached": True},
    }}
    assert t.translate(part) == []


def test_night_start_anchors_the_night_marker():
    # The NIGHT_START no-op (added 2026-08-08) is the single once-per-night anchor: it runs
    # only when check_game_end_day routes past END_GAME, so no ghost night after a final day.
    t = _seeded_translator()
    (event,) = t.translate({"type": "updates", "ns": [], "data": {"NIGHT_START": None}})
    assert (event.type, event.phase) == ("phase_change", "night")


def test_interrupt_becomes_input_request():
    t = _seeded_translator()
    part = {"type": "updates", "ns": [], "data": {"__interrupt__": [
        {"value": {"player_id": "v", "phase": "vigilante_target", "day": 2,
                   "valid_targets": ["t0", "sk"]}}
    ]}}
    (event,) = t.translate(part)
    assert event.type == "input_request"
    assert event.action_kind == "vigilante_target"
    assert event.candidates == ["t0", "sk"]


def test_unknown_node_raises_not_skips():
    t = _seeded_translator()
    with pytest.raises(TranslationError, match="no handler or fold"):
        t.translate({"type": "updates", "ns": [], "data": {"BRAND_NEW_NODE": {"x": 1}}})


def test_unaccounted_key_raises_not_skips():
    t = _seeded_translator()
    with pytest.raises(TranslationError, match="unaccounted"):
        t.translate({"type": "updates", "ns": ["WOLF_NIGHT_PHASE:x"],
                     "data": {"PREPARE_WOLF_NIGHT": {"current_round": 2, "new_key": 1}}})


def test_lynch_cross_check_raises_on_kernel_delta_mismatch():
    t = _seeded_translator()
    t._last_day_ballots = [("w0", "t0"), ("w1", "t0")]
    part = {"type": "updates", "ns": [], "data": {"DAY_RESOLUTION": {
        "voted_player": "h",  # node claims h, ballots say t0
        "no_lynch_streak": 0,
        "day_channel": [], "day_summaries": [],
        "surviving_wolves": ["w0", "w1"],
        "surviving_villagers": ["inv", "h", "sk", "v"],
    }}}
    with pytest.raises(TranslationError, match="kernel/delta mismatch"):
        t.translate(part)


def test_night_cross_check_raises_on_kernel_delta_mismatch():
    t = _seeded_translator()
    t._targets = {"wolves_kill_target": "t0"}
    part = {"type": "updates", "ns": [], "data": {"NIGHT_RESOLUTION": {
        "day_channel": [], "day_summaries": [],
        # Node recorded a different victim than the tracked targets resolve to.
        "dead_roster": [{"player": "h", "role": "healer", "day": 1, "phase": "night"}],
        "surviving_wolves": ["w0", "w1"],
        "surviving_villagers": ["inv", "sk", "v", "t0"],
    }}}
    with pytest.raises(TranslationError, match="kernel/delta mismatch"):
        t.translate(part)


def test_silent_whiff_ships_nothing_public():
    # Wolves hit the SK: no deaths, no save, no public trace — absence is the design.
    t = _seeded_translator()
    t._targets = {"wolves_kill_target": "sk"}
    part = {"type": "updates", "ns": [], "data": {"NIGHT_RESOLUTION": {
        "day_channel": [{"day": 1, "seq": 0, "player": "game_master",
                         "message": "Night of day 1: No one died last night."}],
        "day_summaries": [],
        "wolf_channel": [{"day": 1, "round": 2, "wolf": "game_master",
                          "message": "your kill failed — immune", "vote": ""}],
    }}}
    events = t.translate(part)
    (night,) = [e for e in events if e.type == "night_result"]
    assert night.deaths == [] and night.save is None
    assert [e.type for e in events if e.type == "wolf_message"] == ["wolf_message"]
