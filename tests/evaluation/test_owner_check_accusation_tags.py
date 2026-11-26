"""Tests for the accusation-tag owner check: the candidates and the speaker's labels built from a game
record, the blind export, the per-game-capped stratified draw, and scoring a filled-in answers file.

All data is synthetic: one small two-day record, copied as four games.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from evaluation.experiments.owner_check_accusation_tags import (
    TAGGED_ACCUSATION_STRATUM,
    TAGGED_NONE_STRATUM,
    build,
    build_candidates,
    closing_call_without_accusers,
    score,
)
from evaluation.src.labeling.adapters.accusation_tags import (
    AccusationTagsAdapter,
    canonical_accused_label,
)

GAME_NAMES = ["g01", "g02", "g03", "g04"]


def _channel_entry(
    day: int,
    seq: int,
    player: str,
    message: str = "",
    day_round: str = "discussion",
    passed: bool = False,
    accused: tuple[str, ...] = (),
    other_tags: tuple[tuple[str, str], ...] = (),
) -> dict:
    """Return one day-channel entry; ``accused`` become accusation tags, ``other_tags`` are (target, stance)."""
    addressed_targets = []
    for target in accused:
        addressed_targets.append({"target": target, "addressed_form": "mention", "stance": "accusation"})
    for target, stance in other_tags:
        addressed_targets.append({"target": target, "addressed_form": "mention", "stance": stance})
    return {
        "day": day,
        "seq": seq,
        "player": player,
        "message": message,
        "addressed_targets": addressed_targets,
        "day_round": day_round,
        "passed": passed,
        "gated": False,
    }


def _synthetic_record() -> dict:
    """Return a two-day record with 7 heard AI messages: 3 tagged with an accusation, 4 without.

    player_7 is accused in tags but never named in any line, so its id must not reach the export.
    """
    held_line = _channel_entry(1, 4, "player_5", day_round="proactive", passed=True, accused=("player_9",))
    held_line["gated"] = True
    day_channel = [
        _channel_entry(1, 0, "player_1", "Opening line from player_1.", day_round="opening"),
        _channel_entry(1, 1, "player_2", day_round="opening", passed=True),
        _channel_entry(1, 2, "player_3", "Opening line from player_3.", day_round="opening"),
        _channel_entry(
            1, 3, "player_4", "I have real doubts about what I just heard.",
            accused=("player_10", "player_2"), other_tags=(("player_1", "neutral"),),
        ),
        held_line,
        _channel_entry(1, 5, "player_6", "Agreed with player_1.", other_tags=(("player_1", "agreement"),)),
        _channel_entry(1, 6, "game_master", "\nThere is no vote on day 1, so no one is eliminated."),
        _channel_entry(1, 7, "game_master", "Night of day 1: no one died."),
        _channel_entry(2, 0, "player_1", "Day two opening.", day_round="opening", accused=("player_8",)),
        _channel_entry(2, 1, "player_3", "Following up on that."),
        _channel_entry(
            2, 2, "game_master",
            "Before the vote: player_8 has been accused by player_1 and player_3. player_8 gets a last word.",
            day_round="closing",
        ),
        _channel_entry(2, 3, "player_8", "I am not the wolf.", day_round="closing", accused=("player_7",)),
        _channel_entry(2, 4, "game_master", "\nHere's the vote result for day 2: player_8 was voted out."),
    ]
    return {"game_id": "synthetic", "humans": [], "day_channel": day_channel}


def _write_games(tmp_path: Path) -> Path:
    """Write the synthetic record as four games and return their folder."""
    game_dir = tmp_path / "games"
    game_dir.mkdir()
    for game_name in GAME_NAMES:
        (game_dir / f"{game_name}.record.json").write_text(json.dumps(_synthetic_record()))
    return game_dir


def _build_packet(tmp_path: Path) -> Path:
    """Build a packet from the four synthetic games (3 per stratum, 1 per game per stratum)."""
    packet_dir = tmp_path / "packet"
    build([_write_games(tmp_path)], packet_dir, per_stratum=3, per_game_cap=1, seed=1)
    return packet_dir


# --- Candidates and the speaker's labels ----------------------------------------------------


def test_candidates_are_the_heard_ai_messages_with_speaker_labels(tmp_path):
    game_dir = _write_games(tmp_path)
    candidates, speaker_tag_label_by_key = build_candidates([game_dir / "g01.record.json"])

    # Passes, the held line and moderator lines are left out.
    assert [candidate.key for candidate in candidates] == [
        "g01:d1:s0", "g01:d1:s2", "g01:d1:s3", "g01:d1:s5", "g01:d2:s0", "g01:d2:s1", "g01:d2:s3",
    ]
    assert [candidate.case_index for candidate in candidates] == list(range(7))
    # Only accusation stances count, in seat order (player_2 before player_10).
    assert speaker_tag_label_by_key == {
        "g01:d1:s0": "none",
        "g01:d1:s2": "none",
        "g01:d1:s3": "player_2,player_10",
        "g01:d1:s5": "none",
        "g01:d2:s0": "player_8",
        "g01:d2:s1": "none",
        "g01:d2:s3": "player_7",
    }


def test_candidate_context_is_what_the_table_had_heard(tmp_path):
    game_dir = _write_games(tmp_path)
    candidates, _ = build_candidates([game_dir / "g01.record.json"])
    candidate_by_key = {candidate.key: candidate for candidate in candidates}

    # The opening is spoken all at once: player_3's opening has heard no other opening line.
    assert candidate_by_key["g01:d1:s2"].earlier_today == []
    # A discussion line has heard every earlier heard line, but no pass and no held line.
    later_speakers = [line.speaker for line in candidate_by_key["g01:d1:s5"].earlier_today]
    assert later_speakers == ["player_1", "player_3", "player_4"]
    # Day 2 opens with the moderator lines that closed day 1.
    day_two_opening = candidate_by_key["g01:d2:s0"]
    assert [line.text for line in day_two_opening.since_last_discussion] == [
        "There is no vote on day 1, so no one is eliminated.",
        "Night of day 1: no one died.",
    ]
    assert candidate_by_key["g01:d1:s0"].since_last_discussion == []
    # The closing call reaches the closing speaker without its accusers.
    closing_context = [line.text for line in candidate_by_key["g01:d2:s3"].earlier_today]
    assert closing_context == [
        "Day two opening.", "Following up on that.", "Before the vote: player_8 gets a last word.",
    ]


def test_closing_call_drops_the_accusers():
    recorded_call = (
        "Before the vote: player_4 has been accused by player_2, player_9 and player_6; "
        "player_2 by player_4 and player_10. Each gets a last word."
    )
    assert closing_call_without_accusers(recorded_call) == (
        "Before the vote: player_4 and player_2 each get a last word."
    )
    assert closing_call_without_accusers("Night of day 1: no one died.") == "Night of day 1: no one died."


# --- Labels: canonical form and the model-side parser ---------------------------------------


def test_canonical_accused_label():
    assert canonical_accused_label(" Player_10, player_2 ") == "player_2,player_10"
    assert canonical_accused_label("NONE") == "none"
    assert canonical_accused_label("player_3,player_3") == "player_3"
    for bad_label in ("", "p3", "none,player_3"):
        with pytest.raises(ValueError):
            canonical_accused_label(bad_label)


def test_parse_response_reads_the_last_accused_line():
    adapter = AccusationTagsAdapter()
    assert adapter.parse_response("Reasoning...\naccused: player_7, player_3") == "player_3,player_7"
    assert adapter.parse_response("`accused: none`") == "none"
    assert adapter.parse_response("accused: none\naccused: player_4.") == "player_4"
    assert adapter.parse_response("I think player_3.") is None
    assert adapter.parse_response("accused: maybe") is None


# --- The packet: files, blindness and the draw ----------------------------------------------


def test_build_writes_the_packet(tmp_path):
    packet_dir = _build_packet(tmp_path)

    for file_name in ("candidates.json", "speaker_tag_labels.json", "strata.json", "GUIDE.md", "calib.json"):
        assert (packet_dir / file_name).exists()
    model_labels = json.loads((packet_dir / "speaker_tag_labels.json").read_text())
    assert model_labels["labeler"] == "speaker_tag"
    # 7 messages per game, 4 games: every candidate has a model label.
    assert len(model_labels["labels"]) == 28
    assert {"case_index": 2, "key": "g01:d1:s3", "label": "player_2,player_10"} in model_labels["labels"]
    # The candidates file never carries the tags.
    assert "addressed_targets" not in (packet_dir / "candidates.json").read_text()


def test_export_is_blind(tmp_path):
    packet_dir = _build_packet(tmp_path)
    export_text = ""
    for batch_path in sorted((packet_dir / "export").glob("batch_*.md")):
        export_text += batch_path.read_text()
    export_text += (packet_dir / "export" / "answers_template.json").read_text()
    export_text += (packet_dir / "GUIDE.md").read_text()

    assert "Whom does" in export_text
    # player_7 is accused only in tags, and the recorded closing call's accusers are dropped.
    leaked_texts = ("player_7", "player_2,player_10", "accused by", "addressed_targets", "speaker_tag",
                    TAGGED_ACCUSATION_STRATUM, TAGGED_NONE_STRATUM)
    for leaked_text in leaked_texts:
        assert leaked_text not in export_text


def test_draw_is_stratified_and_capped_per_game(tmp_path):
    packet_dir = _build_packet(tmp_path)
    stratum_by_key = json.loads((packet_dir / "strata.json").read_text())

    drawn_games_by_stratum: dict[str, list[str]] = {}
    for key, stratum in stratum_by_key.items():
        drawn_games_by_stratum.setdefault(stratum, []).append(key.split(":")[0])
    assert sorted(drawn_games_by_stratum) == [TAGGED_ACCUSATION_STRATUM, TAGGED_NONE_STRATUM]
    for drawn_games in drawn_games_by_stratum.values():
        # Three drawn per stratum, each from a different game (cap 1).
        assert len(drawn_games) == 3
        assert len(set(drawn_games)) == 3

    model_labels = json.loads((packet_dir / "speaker_tag_labels.json").read_text())
    for label_row in model_labels["labels"]:
        if label_row["key"] in stratum_by_key:
            expected_stratum = TAGGED_NONE_STRATUM if label_row["label"] == "none" else TAGGED_ACCUSATION_STRATUM
            assert stratum_by_key[label_row["key"]] == expected_stratum

    answers = json.loads((packet_dir / "export" / "answers_template.json").read_text())
    assert sorted(row["key"] for row in answers["labels"]) == sorted(stratum_by_key)


# --- Scoring ---------------------------------------------------------------------------------


def _fill_answers(packet_dir: Path, changed_keys: int) -> None:
    """Save the answers template as human.json, labelled as the speaker did except the first ``changed_keys`` rows."""
    model_labels = json.loads((packet_dir / "speaker_tag_labels.json").read_text())
    speaker_label_by_key = {row["key"]: row["label"] for row in model_labels["labels"]}
    answers = json.loads((packet_dir / "export" / "answers_template.json").read_text())
    for row_number, answer_row in enumerate(answers["labels"]):
        answer_row["label"] = speaker_label_by_key[answer_row["key"]]
        if row_number < changed_keys:
            answer_row["label"] = "player_1,player_9"
    (packet_dir / "human.json").write_text(json.dumps(answers))


def test_score_runs_calibration_on_a_filled_answers_file(tmp_path):
    packet_dir = _build_packet(tmp_path)
    _fill_answers(packet_dir, changed_keys=1)

    report_paths = score(packet_dir)

    report = json.loads((packet_dir / "reports" / "calibration_speaker_tag.json").read_text())
    assert packet_dir / "reports" / "calibration_speaker_tag.md" in report_paths
    # Six labelled, one changed: 5 of 6 agree.
    assert report["items"] == 6
    assert report["agreeing_items"] == 5
    assert {row["stratum"] for row in report["stratum_rows"]} == {TAGGED_ACCUSATION_STRATUM, TAGGED_NONE_STRATUM}


def test_score_rejects_a_label_out_of_seat_order(tmp_path):
    packet_dir = _build_packet(tmp_path)
    _fill_answers(packet_dir, changed_keys=0)
    answers = json.loads((packet_dir / "human.json").read_text())
    answers["labels"][0]["label"] = "player_10, player_2"
    (packet_dir / "human.json").write_text(json.dumps(answers))

    with pytest.raises(ValueError, match="write 'player_2,player_10'"):
        score(packet_dir)


def test_score_needs_the_owner_file(tmp_path):
    packet_dir = _build_packet(tmp_path)
    with pytest.raises(FileNotFoundError):
        score(packet_dir)
