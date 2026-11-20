"""Tests for the echo-gate owner check: the adapter, the packet builder and the score step.

All data is a small synthetic silence-calibration folder written by ``_write_source_dir``: twelve
open-floor lines (six the readers judged D, six A–C; the gate held three of the D) and one opening
line that the gate never saw.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from evaluation.experiments.owner_check_echo_gate import (
    NOT_D,
    build_packet,
    collapse_kind_to_gate_scale,
    score_packet,
)
from evaluation.src.labeling.adapters.echo_gate import EchoGateAdapter

READER_KINDS = ["D", "B", "D", "C", "D", "A", "D", "B", "D", "C", "D", "B"]
"""The readers' kind of open-floor line n (reader item s00n)."""
GATE_HELD_LINES = {0, 4, 8}
"""Open-floor lines the gate held (all three judged D)."""
READER_NOTE_PREFIX = "reader-note-"
"""Every reader note starts with this, so a leak into the export is easy to find."""


def _turn_id(line_number: int) -> str:
    """Return the synthetic turn id of open-floor line ``line_number``."""
    return f"game-{line_number % 3}:2:player_{line_number + 1}:1"


def _packet_entry(reader_item: str, item: dict) -> str:
    """Return one item as the silence-calibration runner's ``packets`` writes it (copied layout)."""
    stage = "the opening round (each player speaks once, before seeing the others)" if item["round"] == "opening" \
        else "the day's discussion"
    return (
        f"### {reader_item}\nSpeaker: {item['player']}, during {stage}.\n\nEarlier days (summary, most recent part):\n"
        f"{item['context']['earlier_days']}\n\nToday's discussion so far, as the speaker saw it:\n"
        f"{item['context']['today']}\n\nTHE LINE:\n{item['line']}\n"
    )


def _write_source_dir(
    source_dir: Path,
    reader_kinds: list[str] = READER_KINDS,
    gate_held_lines: set[int] = GATE_HELD_LINES,
) -> Path:
    """Write a synthetic silence-calibration folder: items, blind key, verdicts, packet, gate check.

    Reader item s00n is open-floor line n; item s012 is an opening line with a verdict but no gate row.
    """
    source_dir.mkdir(parents=True, exist_ok=True)
    items = []
    blind_key = {}
    verdict_rows = []
    gate_rows = []
    for line_number, reader_kind in enumerate(reader_kinds):
        turn = _turn_id(line_number)
        items.append({
            "turn": turn, "player": f"player_{line_number + 1}", "round": "proactive", "kind": "posted",
            "line": f"Synthetic open-floor line number {line_number}.",
            "context": {"earlier_days": f"Day 1 summary for line {line_number}.",
                        "today": f"player_0: an earlier remark before line {line_number}."},
        })
        reader_item = f"s{line_number:03d}"
        blind_key[reader_item] = {"turn": turn, "kind": "posted", "round": "proactive"}
        verdict_rows.append({"item": reader_item, "kind": reader_kind, "worth_hearing": "no",
                             "note": f"{READER_NOTE_PREFIX}{line_number}"})
        held = f"player_{line_number}" if line_number in gate_held_lines else ""
        gate_rows.append({"turn": turn, "kind": reader_kind, "held": held})

    opening_item = {"turn": "game-9:1:player_1:0", "player": "player_1", "round": "opening", "kind": "posted",
                    "line": "An opening line.", "context": {"earlier_days": "", "today": "No messages yet."}}
    items.append(opening_item)
    blind_key["s012"] = {"turn": opening_item["turn"], "kind": "posted", "round": "opening"}
    verdict_rows.append({"item": "s012", "kind": "A", "worth_hearing": "yes", "note": f"{READER_NOTE_PREFIX}opening"})

    (source_dir / "items.jsonl").write_text("".join(json.dumps(item) + "\n" for item in items))
    (source_dir / "blind_key.json").write_text(json.dumps(blind_key))
    # Two verdict files, as the four readers wrote one each.
    (source_dir / "verdicts_1.jsonl").write_text("".join(json.dumps(row) + "\n" for row in verdict_rows[:7]))
    (source_dir / "verdicts_2.jsonl").write_text("".join(json.dumps(row) + "\n" for row in verdict_rows[7:]))
    (source_dir / "gate_check_ported.jsonl").write_text("".join(json.dumps(row) + "\n" for row in gate_rows))
    packet_entries = [_packet_entry(name, items[int(name[1:])]) for name in blind_key]
    (source_dir / "packet_1.md").write_text("\n".join(packet_entries))
    return source_dir


def _read_labels(path: Path) -> dict[str, str]:
    """Return a simple-golden file's labels by key."""
    label_file = json.loads(path.read_text())
    return {label_row["key"]: label_row["label"] for label_row in label_file["labels"]}


# --- build: candidates and model labels ---------------------------------------------------------


def test_build_writes_blind_candidates_and_both_label_sources(tmp_path):
    source_dir = _write_source_dir(tmp_path / "source")
    out_dir = tmp_path / "packet"
    build_packet(source_dir, out_dir, seed=1, lines_per_stratum=3)

    candidates = json.loads((out_dir / "candidates.json").read_text())["cases"]
    # The twelve gate-checked lines only; the opening line is not one of them.
    assert [record["key"] for record in candidates] == [_turn_id(n) for n in range(12)]
    assert candidates[5]["case_index"] == 5
    assert candidates[5]["reader_item"] == "s005"
    assert candidates[5]["stage"] == "the day's discussion"
    for record in candidates:
        assert set(record) == {"case_index", "key", "reader_item", "speaker", "stage", "earlier_days", "today", "line"}

    readers_labels = _read_labels(out_dir / "labels_readers.json")
    assert readers_labels == {_turn_id(n): READER_KINDS[n] for n in range(12)}
    gate_labels = _read_labels(out_dir / "labels_echo_gate.json")
    assert [gate_labels[_turn_id(n)] for n in range(12)] == [
        "D" if n in GATE_HELD_LINES else NOT_D for n in range(12)
    ]
    assert json.loads((out_dir / "labels_echo_gate.json").read_text())["labeler"] == "echo_gate"

    gate_config = json.loads((out_dir / "calib_echo_gate.json").read_text())
    assert gate_config["allowed_labels"] == ["D", NOT_D]
    assert gate_config["positive_label"] == "D"
    readers_config = json.loads((out_dir / "calib_readers.json").read_text())
    assert readers_config["allowed_labels"] == ["A", "B", "C", "D"]
    assert readers_config["positive_label"] is None


def test_build_rejects_a_line_that_does_not_match_the_readers_packet(tmp_path):
    source_dir = _write_source_dir(tmp_path / "source")
    packet_path = source_dir / "packet_1.md"
    packet_path.write_text(packet_path.read_text().replace("line number 3.", "line number 3, edited."))
    with pytest.raises(ValueError, match="s003"):
        build_packet(source_dir, tmp_path / "packet", seed=1, lines_per_stratum=3)


# --- the draw -----------------------------------------------------------------------------------


def test_draw_is_stratified_on_the_readers_d_versus_a_to_c(tmp_path):
    out_dir = tmp_path / "packet"
    sample = build_packet(_write_source_dir(tmp_path / "source"), out_dir, seed=1, lines_per_stratum=3)

    assert sample.drawn_count_by_stratum == {"A-C": 3, "D": 3}
    stratum_by_key = json.loads((out_dir / "strata.json").read_text())
    assert sorted(stratum_by_key) == sample.drawn_keys
    for key, stratum in stratum_by_key.items():
        line_number = [_turn_id(n) for n in range(12)].index(key)
        assert stratum == ("D" if READER_KINDS[line_number] == "D" else "A-C")
    answers = json.loads((out_dir / "export" / "answers_template.json").read_text())["labels"]
    assert sorted(answer_row["key"] for answer_row in answers) == sample.drawn_keys
    assert all(answer_row["label"] is None for answer_row in answers)


# --- blindness ----------------------------------------------------------------------------------


def test_export_is_blind_to_reader_kinds_and_gate_decisions(tmp_path):
    # Every line drawn in both builds, so the only difference between them is the model labels.
    first_out = tmp_path / "first"
    build_packet(_write_source_dir(tmp_path / "source_a"), first_out, seed=1, lines_per_stratum=12)
    flipped_kinds = ["B" if kind == "D" else "D" for kind in READER_KINDS]
    flipped_holds = {n for n in range(12) if flipped_kinds[n] == "D"}
    second_out = tmp_path / "second"
    build_packet(_write_source_dir(tmp_path / "source_b", flipped_kinds, flipped_holds), second_out, seed=1,
                 lines_per_stratum=12)

    first_batches = sorted((first_out / "export").glob("batch_*.md"))
    assert first_batches
    for batch_path in first_batches:
        batch_text = batch_path.read_text()
        assert batch_text == (second_out / "export" / batch_path.name).read_text()
        assert READER_NOTE_PREFIX not in batch_text
        assert "worth_hearing" not in batch_text
    assert (first_out / "candidates.json").read_text() == (second_out / "candidates.json").read_text()


def test_manual_rendering_matches_the_readers_view(tmp_path):
    source_dir = _write_source_dir(tmp_path / "source")
    out_dir = tmp_path / "packet"
    build_packet(source_dir, out_dir, seed=1, lines_per_stratum=3)
    items = EchoGateAdapter().load_items(out_dir / "candidates.json")
    rendered = EchoGateAdapter().format_for_manual(items[2])
    packet_text = (source_dir / "packet_1.md").read_text()
    reader_body = rendered.split("\n\n", 1)[1]
    assert f"### s002\n{reader_body}" in packet_text


# --- adapter prompt (rubric parity) -------------------------------------------------------------


def test_prompt_carries_the_rubric_and_parse_reads_the_kind(tmp_path):
    out_dir = tmp_path / "packet"
    build_packet(_write_source_dir(tmp_path / "source"), out_dir, seed=1, lines_per_stratum=3)
    adapter = EchoGateAdapter()
    prompt = adapter.format_prompt(adapter.load_items(out_dir / "candidates.json")[0])
    assert "pick the most valuable kind it really delivers" in prompt
    assert "Synthetic open-floor line number 0." in prompt

    assert adapter.parse_response('{"kind": "C", "note": "a new test"}') == "C"
    assert adapter.parse_response("B") == "B"
    assert adapter.parse_response("no idea") is None


# --- score --------------------------------------------------------------------------------------


def test_collapse_kind_to_gate_scale():
    assert collapse_kind_to_gate_scale("D") == "D"
    for kind in ("A", "B", "C"):
        assert collapse_kind_to_gate_scale(kind) == NOT_D
    with pytest.raises(ValueError):
        collapse_kind_to_gate_scale("E")


def test_score_needs_the_owners_answers(tmp_path):
    out_dir = tmp_path / "packet"
    build_packet(_write_source_dir(tmp_path / "source"), out_dir, seed=1, lines_per_stratum=3)
    with pytest.raises(FileNotFoundError, match="human.json"):
        score_packet(out_dir)


def test_score_compares_both_sources_on_a_filled_in_answers_file(tmp_path):
    out_dir = tmp_path / "packet"
    build_packet(_write_source_dir(tmp_path / "source"), out_dir, seed=1, lines_per_stratum=12)

    # The owner agrees with the readers on every line except line 1, which they call D (readers: B).
    answers = json.loads((out_dir / "export" / "answers_template.json").read_text())
    readers_labels = _read_labels(out_dir / "labels_readers.json")
    for answer_row in answers["labels"]:
        answer_row["label"] = readers_labels[answer_row["key"]]
        if answer_row["key"] == _turn_id(1):
            answer_row["label"] = "D"
            answer_row["note"] = "only repeats player_0"
    (out_dir / "human.json").write_text(json.dumps(answers))

    report_paths = score_packet(out_dir)
    assert {path.name for path in report_paths} == {
        "calibration_readers.md", "calibration_readers.json",
        "calibration_echo_gate.md", "calibration_echo_gate.json",
    }

    readers_report = json.loads((out_dir / "reports" / "calibration_readers.json").read_text())
    assert readers_report["items"] == 12
    assert readers_report["agreeing_items"] == 11

    binary_answers = json.loads((out_dir / "human_binary.json").read_text())["labels"]
    binary_by_key = {answer_row["key"]: answer_row["label"] for answer_row in binary_answers}
    assert binary_by_key[_turn_id(1)] == "D"
    assert binary_by_key[_turn_id(5)] == NOT_D  # the readers' A
    assert {answer_row["key"]: answer_row["note"] for answer_row in binary_answers}[_turn_id(1)] == "only repeats player_0"

    # Owner D on lines 0, 1, 2, 4, 6, 8, 10; the gate held 0, 4 and 8: 4 misses, 0 false alarms.
    gate_report = json.loads((out_dir / "reports" / "calibration_echo_gate.json").read_text())
    assert gate_report["items"] == 12
    assert gate_report["agreeing_items"] == 8
    assert gate_report["bias_test"]["human_only_positive"] == 4
    assert gate_report["bias_test"]["model_only_positive"] == 0
