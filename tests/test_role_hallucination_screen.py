"""Logic tests for the role-hallucination screen v2 (synthetic fixtures, no LLM, no batch files).

Covers the death-timeline convention, each anchor class firing on a planted mention/claim, the
provable safe-drops staying quiet (GM messages, count claims matching the alive count, alive-player
mentions), the updated_strategy unit path, and the two structural checks (dead vote = deterministic
verdict; question/response addressed to a dead player = candidate).
"""

from __future__ import annotations

from evaluation.src.audits.role_hallucination_screen import death_timeline, screen_game

ROLES = {
    "player_1": "wolf", "player_2": "wolf", "player_3": "serial_killer",
    "player_4": "villager", "player_5": "healer", "player_6": "investigator",
    "player_7": "vigilante", "player_8": "villager", "player_9": "villager",
}


def _game(messages, night=None, days=None, summaries=None):
    return {
        "game_id": "g", "config_name": "test", "roles": ROLES,
        "night_resolutions": night or [],
        "day_resolutions": days or [],
        "day_summaries": summaries or [],
        "day_channel": messages,
    }


def _msg(day, seq, player, text, targets=None, passed=False):
    return {"day": day, "seq": seq, "player": player, "message": text,
            "passed": passed, "addressed_targets": targets or []}


NIGHT_KILL_P1 = [{"day": 1, "deaths": ["player_1"]}]          # p1 (wolf) dead from day 2
KILL_BOTH_WOLVES = [{"day": 1, "deaths": ["player_1", "player_2"]}]  # 0 wolves from day 2


def _screen(record):
    rows, counts, scanned = screen_game(record, strategy_units=[])
    return rows, counts, scanned


def _anchor_kinds(rows):
    return [a["kind"] for r in rows if r["row_type"] == "candidate" for a in r["anchors"]]


def test_death_timeline_night_and_lynch():
    tl = death_timeline(_game([], night=NIGHT_KILL_P1,
                              days=[{"day": 2, "voted_player": "player_5", "votes": []}]))
    assert tl == {"player_1": 2, "player_5": 3}


def test_dead_speaker_self_check_counts_violation():
    rec = _game([_msg(2, 0, "player_1", "I am alive, honest.")], night=NIGHT_KILL_P1)
    _, counts, _ = _screen(rec)
    assert counts["dead_speaker_violations"] == 1


def test_dead_id_anchor_fires_on_any_mention_alive_does_not():
    dead = _game([_msg(2, 0, "player_4", "Remember what player_1 said yesterday.")],
                 night=NIGHT_KILL_P1)
    rows, _, _ = _screen(dead)
    assert "dead_id" in _anchor_kinds(rows)  # even a retrospective mention is a candidate
    alive = _game([_msg(1, 0, "player_4", "Remember what player_1 said earlier.")])
    rows, _, _ = _screen(alive)
    assert rows == []


def test_dead_role_word_anchor_needs_all_holders_dead():
    both = _game([_msg(2, 0, "player_4", "The remaining wolf is hiding.")],
                 night=KILL_BOTH_WOLVES)
    rows, _, _ = _screen(both)
    assert "dead_role_word" in _anchor_kinds(rows)
    one_alive = _game([_msg(2, 0, "player_4", "A wolf walks among us still.")],
                      night=NIGHT_KILL_P1)
    rows, _, _ = _screen(one_alive)
    assert "dead_role_word" not in _anchor_kinds(rows)


def test_count_mismatch_generalizes_beyond_wolves_and_drops_matches():
    # day 2: 1 wolf alive, 3 villagers alive, healer alive
    wrong = _game([_msg(2, 0, "player_4", "There are two villagers left at most.")],
                  night=NIGHT_KILL_P1)
    rows, _, _ = _screen(wrong)
    assert "count_mismatch" in _anchor_kinds(rows)
    right = _game([_msg(2, 0, "player_4", "Only one wolf left among us.")], night=NIGHT_KILL_P1)
    rows, _, _ = _screen(right)  # matching count = provably consistent = safe drop
    assert "count_mismatch" not in _anchor_kinds(rows)


def test_definite_singular_and_vague_quantifier_are_count_claims():
    two_alive = _game([_msg(1, 0, "player_4", "The remaining wolf must be nervous.")])
    rows, _, _ = _screen(two_alive)  # "the remaining wolf" implies 1; 2 alive
    assert "count_mismatch" in _anchor_kinds(rows)
    vague = _game([_msg(2, 0, "player_4", "There are several wolves in this together.")],
                  night=NIGHT_KILL_P1)  # 1 alive; "several" impossible
    rows, _, _ = _screen(vague)
    assert "count_mismatch" in _anchor_kinds(rows)


def test_game_master_messages_are_safe_filtered():
    rec = _game([_msg(2, 0, "game_master", "player_1 the wolf died in the night.")],
                night=NIGHT_KILL_P1)
    rows, _, scanned = _screen(rec)
    assert rows == [] and scanned == 0


def test_claim_attrib_respects_logged_claims():
    summaries = [{"day": 1, "structured": {"role_claims": [
        {"player": "player_6", "claimed_role": "investigator"}]}}]
    logged = _game([_msg(2, 0, "player_4", "player_6 claimed investigator yesterday.")],
                   summaries=summaries)
    rows, _, _ = _screen(logged)
    assert "claim_attrib" not in _anchor_kinds(rows)
    unlogged = _game([_msg(2, 0, "player_4", "player_6 claimed healer yesterday.")],
                     summaries=summaries)
    rows, _, _ = _screen(unlogged)
    assert "claim_attrib" in _anchor_kinds(rows)


def test_addressed_dead_question_is_candidate_mention_is_not():
    q = _game([_msg(2, 0, "player_4", "Well?",
                    targets=[{"target": "player_1", "addressed_form": "question",
                              "stance": "accusation"}])], night=NIGHT_KILL_P1)
    rows, _, _ = _screen(q)
    assert "addressed_dead" in _anchor_kinds(rows)
    m = _game([_msg(2, 0, "player_4", "Thinking it over.",
                    targets=[{"target": "player_1", "addressed_form": "mention",
                              "stance": "neutral"}])], night=NIGHT_KILL_P1)
    rows, _, _ = _screen(m)
    assert "addressed_dead" not in _anchor_kinds(rows)


def test_dead_vote_is_deterministic_verdict():
    days = [{"day": 3, "voted_player": None,
             "votes": [{"voter": "player_4", "votee": "player_1"}]}]
    rec = _game([], night=NIGHT_KILL_P1, days=days)
    rows, counts, _ = _screen(rec)
    assert counts["verdict_dead_vote"] == 1
    assert any(r["row_type"] == "verdict" and r["kind"] == "dead_vote" for r in rows)


def test_updated_strategy_units_are_screened():
    rec = _game([], night=KILL_BOTH_WOLVES)
    units = [{"unit": "updated_strategy", "day": 2, "phase": "day_vote", "seq": None,
              "speaker": "player_4", "text": "Find the remaining wolf before night."}]
    rows, _, scanned = screen_game(rec, strategy_units=units)
    assert scanned == 1
    assert rows and rows[0]["unit"] == "updated_strategy"
    assert "dead_role_word" in _anchor_kinds(rows)
