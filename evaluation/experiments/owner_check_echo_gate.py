"""Owner check: the echo gate. How far can the silence calibration's blind readers, and the shipped
echo gate calibrated on them, be trusted to tell a restatement or filler from a line worth hearing?

The echo gate (`Agents/turn/echo_gate.py`) holds an open-floor line it judges a restatement or
filler. Its bar was set on 65 open-floor lines that four blind Sonnet readers sorted into kinds A–D
(evidence/gameplay/data/silence_calibration/, README step 4). The owner labels a
stratified draw of those same lines, shown exactly as the readers saw them, on the readers' scale.
Two sources are then compared with the owner's labels:
- ``readers``: the readers' kind per line (four-way, A / B / C / D);
- ``echo_gate``: the shipped gate's decision (`gate_check_ported.jsonl`), mapped to the owner's scale
  as D = held and "not D" = spoken. For this comparison the owner's A / B / C collapse to "not D";
  ``score`` writes that binary copy of the owner's answers as ``human_binary.json``.

What the owner does: read ``GUIDE.md``, label the batches in ``export/``, fill in
``export/answers_template.json`` and save it as ``human.json`` in the packet folder.

    poetry run python -m evaluation.experiments.owner_check_echo_gate build
    poetry run python -m evaluation.experiments.owner_check_echo_gate score

Packet: evidence/evaluation/labeling/owner_checks/echo_gate/.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from evaluation.src.labeling.adapters.echo_gate import (
    KIND_LABELS,
    KIND_RUBRIC,
    EchoGateAdapter,
    OpenFloorLine,
    render_reader_view,
)
from evaluation.src.labeling.anchor import draw_stratified_sample, write_stratum_file
from evaluation.src.labeling.config import CalibrationConfig, ExportConfig
from evaluation.src.labeling.exporter import export_for_manual
from evaluation.src.labeling.pipeline import stage_calibrate
from evaluation.src.labeling.schemas import StratifiedSample

SOURCE_DIR = Path("evidence/gameplay/data/silence_calibration")
"""The silence calibration's record: items, blind key, reader verdicts, packets, gate checks."""
OUT_DIR = Path("evidence/evaluation/labeling/owner_checks/echo_gate")
"""Where the packet is written."""
SEED = 20261023
LINES_PER_STRATUM = 25
"""25 lines from each stratum: 50 of the 65."""
EXPORT_BATCH_SIZE = 5
"""Lines per export batch (each line is its own case)."""

READER_SOURCE = "readers"
GATE_SOURCE = "echo_gate"
NOT_D = "not D"
"""The gate scale's other label: the gate let the line be spoken."""
GATE_LABELS = ["D", NOT_D]
WORTHWHILE_STRATUM = "A-C"
RESTATEMENT_STRATUM = "D"
OPEN_FLOOR_ROUND = "proactive"
"""The capture's name for the open floor's round."""

EXPORT_INSTRUCTIONS = f"""# Owner check: the echo gate

Each item below is one line a player wrote on the open floor of a Werewolf day, with what that
player saw: the most recent part of the earlier days' summary and today's discussion so far. Label
the KIND of THE LINE:

{KIND_RUBRIC}

Write your letter (A, B, C or D) as the `label` of the row with the item's key in
`export/answers_template.json` (a `note` is optional), and save that file as `human.json` in the
packet folder. The JSON block under each item is only a reminder of the key; the answers go in the
answers file. The full guide, with worked examples, is `GUIDE.md`."""

GUIDE_TEXT = f"""# Owner check: the echo gate

## What this measures

The echo gate (`Agents/turn/echo_gate.py`) holds an open-floor line it judges a restatement or
filler, so the table hears each point once. Its bar was set on open-floor lines that four blind
Sonnet readers sorted into four kinds. You label {2 * LINES_PER_STRATUM} of those same lines, blind,
on the readers' scale. Your labels then measure two things:

1. **The readers**: how often their kind matches yours (four-way, A / B / C / D).
2. **The shipped gate**: how often its decision matches yours on its own two-way scale: the gate
   **held** the line = **D**, the gate **let it be spoken** = **not D**. For this comparison your
   A, B and C all count as "not D"; `score` writes that binary copy of your answers to
   `human_binary.json` for you. Nothing to do by hand.

The lines are shown exactly as the readers saw them. Nothing in the packet says what the readers
or the gate decided, whether the line was spoken, or how the lines were drawn.

## What you do

1. Open `export/batch_01.md` and work through the batches in order.
2. For each item, decide its kind (A, B, C or D) using the rubric below.
3. Write the letter as the `label` of that item's row in `export/answers_template.json` (find the
   row by the key in the item's heading). Use `note` for anything worth remembering (optional).
4. Save the filled-in file as `human.json` in this folder (next to this guide).
5. Run `poetry run python -m evaluation.experiments.owner_check_echo_gate score`.

## What each item shows

- **Speaker** and the stage of the day.
- **Earlier days**: the most recent part of the earlier days' summary (it is cut to its last 3,000
  characters, so it may start mid-sentence).
- **Today's discussion** so far, as the speaker saw it.
- **THE LINE**: what you label.

Judge newness only against what is shown, as the readers did.

## The rubric (the readers' own wording)

{KIND_RUBRIC}

## Worked examples

These are made up from the rubric's own wording, not taken from the packet.

1. **D.** Today, player_2 has already said "we should hear claims before we vote". THE LINE, from
   player_7: "Nothing to go on yet, let's hear claims." It asks again for what was already asked,
   and the rest is filler. Kind D.
2. **B.** The summary shows player_4 voted to eliminate both seats that were later revealed as town;
   nobody has pointed this out today. THE LINE: "player_4 has now voted against two town seats in
   a row, and both times switched late, so I trust their reads least." The votes are known facts,
   but the reading and its reason are new. Kind B. Had another player already made that point
   today, it would be D, however well put.
3. **C (a line that does several things).** player_5 has said the day-2 vote looked coordinated.
   THE LINE: "I agree with player_5 about day 2. player_8, why did you switch to abstain at the last
   moment?" The agreement adds no new reason (D on its own), but nobody has asked player_8 that
   today. Pick the most valuable kind the line really delivers: C.

Whether the line is true, or a good move for the speaker's side, never matters.

## Files

| File | What it is |
|---|---|
| `export/batch_NN.md` | The lines to label, {EXPORT_BATCH_SIZE} per batch |
| `export/answers_template.json` | Your answers file (fill in `label`, save as `human.json`) |
| `candidates.json` | The lines with their context (the export's source) |
| `strata.json` | Which stratum each drawn line came from (do not open before labelling) |
| `labels_readers.json`, `labels_echo_gate.json` | The two sources compared (do not open before labelling) |
| `calib_readers.json`, `calib_echo_gate.json` | The calibration configs `score` runs |
| `reports/` | Written by `score`: one markdown and one JSON report per source |
"""


def reader_stage(round_name: str) -> str:
    """Return the stage line the readers' packet showed for a turn's round.

    Args:
        round_name: the capture's round, e.g. ``"proactive"`` or ``"opening"``.

    Returns:
        The same wording as ``silence_calibration.packets``, e.g. ``"the day's discussion"``.
    """
    if round_name == "opening":
        return "the opening round (each player speaks once, before seeing the others)"
    return "the day's discussion"


def read_gate_holds(source_dir: Path) -> dict[str, bool]:
    """Read the shipped gate's decision on each open-floor line.

    Args:
        source_dir: the silence calibration folder; reads ``gate_check_ported.jsonl``, whose rows
            look like ``{"turn": "voices-07.on:2:player_7:1", "kind": "D", "held": "player_5"}``
            (``held`` is the gate's return value: an echoed player, ``"filler"``, or ``""`` for spoken).

    Returns:
        Whether the gate held each line, by turn id. Raises ValueError if a turn appears twice.
    """
    held_by_turn: dict[str, bool] = {}
    for row_text in (source_dir / "gate_check_ported.jsonl").read_text().splitlines():
        if not row_text.strip():
            continue
        gate_row = json.loads(row_text)
        if gate_row["turn"] in held_by_turn:
            raise ValueError(f"Turn {gate_row['turn']!r} appears twice in gate_check_ported.jsonl")
        held_by_turn[gate_row["turn"]] = bool(gate_row["held"])
    return held_by_turn


def read_reader_verdicts(source_dir: Path) -> tuple[dict[str, str], dict[str, str]]:
    """Read each judged line's reader name and the readers' kind for it.

    Args:
        source_dir: the silence calibration folder; reads ``blind_key.json``
            (``{"s012": {"turn": "...", ...}}``) and every ``verdicts_N.jsonl``
            (``{"item": "s012", "kind": "B", ...}``).

    Returns:
        ``(reader_item_by_turn, reader_kind_by_turn)``, e.g. ``{"voices-02.off:4:player_10:2": "s012"}``
        and ``{"voices-02.off:4:player_10:2": "B"}``. Raises ValueError if an item is judged twice.
    """
    blind_key = json.loads((source_dir / "blind_key.json").read_text())
    reader_item_by_turn: dict[str, str] = {}
    reader_kind_by_turn: dict[str, str] = {}
    for verdict_path in sorted(source_dir.glob("verdicts_*.jsonl")):
        for row_text in verdict_path.read_text().splitlines():
            if not row_text.strip():
                continue
            verdict = json.loads(row_text)
            turn = blind_key[verdict["item"]]["turn"]
            if turn in reader_kind_by_turn:
                raise ValueError(f"Reader item {verdict['item']!r} (turn {turn!r}) is judged twice")
            reader_item_by_turn[turn] = verdict["item"]
            reader_kind_by_turn[turn] = verdict["kind"]
    return reader_item_by_turn, reader_kind_by_turn


def build_open_floor_lines(
    source_dir: Path, open_floor_turns: list[str], reader_item_by_turn: dict[str, str]
) -> list[OpenFloorLine]:
    """Build the candidate record of each open-floor line from the calibration's items file.

    Args:
        source_dir: the silence calibration folder; reads ``items.jsonl`` (one turn per row, with
            ``line``, ``player``, ``round`` and ``context.earlier_days`` / ``context.today``).
        open_floor_turns: the turn ids to build, e.g. the gate-checked turns.
        reader_item_by_turn: each turn's reader name, e.g. ``{"voices-02.off:4:player_10:2": "s012"}``.

    Returns:
        One record per turn, sorted by case index (the readers' shuffled order). Raises ValueError
        if a turn is missing from the items file or has no reader name, or is not an open-floor turn.
    """
    item_by_turn: dict[str, dict] = {}
    for row_text in (source_dir / "items.jsonl").read_text().splitlines():
        if row_text.strip():
            calibration_item = json.loads(row_text)
            item_by_turn[calibration_item["turn"]] = calibration_item

    open_floor_lines: list[OpenFloorLine] = []
    for turn in open_floor_turns:
        if turn not in item_by_turn or turn not in reader_item_by_turn:
            raise ValueError(f"Turn {turn!r} is missing from items.jsonl or from the reader verdicts")
        calibration_item = item_by_turn[turn]
        if calibration_item["round"] != OPEN_FLOOR_ROUND:
            raise ValueError(f"Turn {turn!r} is a {calibration_item['round']!r} turn, not the open floor")
        reader_item = reader_item_by_turn[turn]
        open_floor_lines.append(
            OpenFloorLine(
                case_index=int(reader_item.removeprefix("s")),
                key=turn,
                reader_item=reader_item,
                speaker=calibration_item["player"],
                stage=reader_stage(calibration_item["round"]),
                earlier_days=calibration_item["context"]["earlier_days"],
                today=calibration_item["context"]["today"],
                line=calibration_item["line"],
            )
        )
    open_floor_lines.sort(key=lambda line_record: line_record.case_index)
    return open_floor_lines


def check_matches_reader_packets(open_floor_lines: list[OpenFloorLine], source_dir: Path) -> None:
    """Check that every line renders exactly as it appears in the readers' packets.

    Args:
        open_floor_lines: the candidate records.
        source_dir: the silence calibration folder; reads every ``packet_N.md``.

    Returns:
        None. Raises ValueError naming every item whose rendering is not found word for word.
    """
    packet_text = ""
    for packet_path in sorted(source_dir.glob("packet_*.md")):
        packet_text += packet_path.read_text() + "\n"
    mismatched_items: list[str] = []
    for line_record in open_floor_lines:
        reader_view = f"### {line_record.reader_item}\n{render_reader_view(line_record)}"
        if reader_view not in packet_text:
            mismatched_items.append(line_record.reader_item)
    if mismatched_items:
        raise ValueError(f"These items do not render as the readers' packets show them: {mismatched_items}")


def check_gate_rows_match_reader_kinds(source_dir: Path, reader_kind_by_turn: dict[str, str]) -> None:
    """Check that the gate-check file's copy of each line's kind equals the readers' verdict.

    The gate check joined the verdicts by turn when it ran; a mismatch here would mean this
    builder's join through the blind key is wrong.

    Args:
        source_dir: the silence calibration folder; reads ``gate_check_ported.jsonl``.
        reader_kind_by_turn: the readers' kind per turn, from ``read_reader_verdicts``.

    Returns:
        None. Raises ValueError naming every turn whose kinds differ or that has no verdict.
    """
    mismatched_turns: list[str] = []
    for row_text in (source_dir / "gate_check_ported.jsonl").read_text().splitlines():
        if not row_text.strip():
            continue
        gate_row = json.loads(row_text)
        if reader_kind_by_turn.get(gate_row["turn"]) != gate_row["kind"]:
            mismatched_turns.append(gate_row["turn"])
    if mismatched_turns:
        raise ValueError(f"Gate check and reader verdicts disagree on the kind of: {mismatched_turns}")


def gate_label(held: bool) -> str:
    """Return the gate's decision on the owner's scale.

    Args:
        held: True when the gate held the line.

    Returns:
        ``"D"`` for held, ``"not D"`` for spoken.
    """
    return "D" if held else NOT_D


def collapse_kind_to_gate_scale(kind: str) -> str:
    """Return a kind on the gate's two-way scale.

    Args:
        kind: one of ``"A"``–``"D"``.

    Returns:
        ``"D"`` for D, ``"not D"`` for A, B or C. Raises ValueError for anything else.
    """
    if kind == "D":
        return "D"
    if kind in ("A", "B", "C"):
        return NOT_D
    raise ValueError(f"Not a kind: {kind!r}")


def write_simple_golden(
    path: Path, labeler: str, label_by_key: dict[str, str], case_index_by_key: dict[str, int]
) -> Path:
    """Write one label source in the pipeline's simple-golden shape.

    Args:
        path: where to write.
        labeler: the source name, e.g. ``"readers"``.
        label_by_key: the source's label per key, e.g. ``{"voices-02.off:4:player_10:2": "B"}``.
        case_index_by_key: each key's case index, the same as in the candidates file.

    Returns:
        The path written, holding ``{"labeler": ..., "labels": [{"case_index", "key", "label"}]}``
        sorted by case index.
    """
    label_rows = []
    for key in sorted(label_by_key, key=lambda item_key: case_index_by_key[item_key]):
        label_rows.append({"case_index": case_index_by_key[key], "key": key, "label": label_by_key[key]})
    path.write_text(json.dumps({"labeler": labeler, "labels": label_rows}, indent=2) + "\n")
    return path


def write_calibration_configs(out_dir: Path) -> tuple[Path, Path]:
    """Write the two calibration configs ``score`` runs, one per comparison.

    Args:
        out_dir: the packet folder; every path in the configs is under it.

    Returns:
        ``(readers_config_path, gate_config_path)``: ``calib_readers.json`` (four-way, the owner's
        ``human.json``) and ``calib_echo_gate.json`` (binary, positive label D, ``human_binary.json``).
    """
    readers_config = CalibrationConfig(
        human_labels_path=out_dir / "human.json",
        model_label_paths=[out_dir / "labels_readers.json"],
        model_sources=[READER_SOURCE],
        stratum_path=out_dir / "strata.json",
        allowed_labels=KIND_LABELS,
        output_dir=out_dir / "reports",
    )
    gate_config = CalibrationConfig(
        human_labels_path=out_dir / "human_binary.json",
        model_label_paths=[out_dir / "labels_echo_gate.json"],
        model_sources=[GATE_SOURCE],
        stratum_path=out_dir / "strata.json",
        allowed_labels=GATE_LABELS,
        positive_label="D",
        output_dir=out_dir / "reports",
    )
    readers_config_path = out_dir / "calib_readers.json"
    gate_config_path = out_dir / "calib_echo_gate.json"
    readers_config_path.write_text(readers_config.model_dump_json(indent=2) + "\n")
    gate_config_path.write_text(gate_config.model_dump_json(indent=2) + "\n")
    return readers_config_path, gate_config_path


def build_packet(
    source_dir: Path = SOURCE_DIR,
    out_dir: Path = OUT_DIR,
    seed: int = SEED,
    lines_per_stratum: int = LINES_PER_STRATUM,
) -> StratifiedSample:
    """Write the whole owner-check packet: candidates, both label sources, strata, export, guide, configs.

    Args:
        source_dir: the silence calibration folder.
        out_dir: the packet folder (created if missing).
        seed: the draw's seed.
        lines_per_stratum: how many lines to draw from each of the readers' A–C and D strata.

    Returns:
        The draw. Raises ValueError if a line does not render as the readers saw it, or the gate
        check and the reader verdicts disagree on a line's kind.
    """
    held_by_turn = read_gate_holds(source_dir)
    reader_item_by_turn, reader_kind_by_turn = read_reader_verdicts(source_dir)
    open_floor_lines = build_open_floor_lines(source_dir, sorted(held_by_turn), reader_item_by_turn)
    check_matches_reader_packets(open_floor_lines, source_dir)
    check_gate_rows_match_reader_kinds(source_dir, reader_kind_by_turn)

    out_dir.mkdir(parents=True, exist_ok=True)
    candidates_path = out_dir / "candidates.json"
    candidate_records = [line_record.model_dump() for line_record in open_floor_lines]
    candidates_path.write_text(
        json.dumps(
            {
                "description": "Open-floor lines of the silence calibration, as its blind readers saw them "
                "(owner_check_echo_gate build). No reader kind or gate decision.",
                "cases": candidate_records,
            },
            indent=2,
        )
        + "\n"
    )

    case_index_by_key: dict[str, int] = {}
    reader_kind_by_key: dict[str, str] = {}
    gate_label_by_key: dict[str, str] = {}
    stratum_by_key: dict[str, str] = {}
    for line_record in open_floor_lines:
        key = line_record.key
        case_index_by_key[key] = line_record.case_index
        reader_kind_by_key[key] = reader_kind_by_turn[key]
        gate_label_by_key[key] = gate_label(held_by_turn[key])
        if reader_kind_by_turn[key] == "D":
            stratum_by_key[key] = RESTATEMENT_STRATUM
        else:
            stratum_by_key[key] = WORTHWHILE_STRATUM
    write_simple_golden(out_dir / "labels_readers.json", READER_SOURCE, reader_kind_by_key, case_index_by_key)
    write_simple_golden(out_dir / "labels_echo_gate.json", GATE_SOURCE, gate_label_by_key, case_index_by_key)

    sample = draw_stratified_sample(list(stratum_by_key), stratum_by_key, lines_per_stratum, seed)
    write_stratum_file(sample.drawn_keys, stratum_by_key, out_dir / "strata.json")

    export_for_manual(
        ExportConfig(
            candidates_path=candidates_path,
            output_dir=out_dir / "export",
            batch_size=EXPORT_BATCH_SIZE,
            keys=sample.drawn_keys,
            write_answers_template=True,
        ),
        EchoGateAdapter(),
        EXPORT_INSTRUCTIONS,
    )
    (out_dir / "GUIDE.md").write_text(GUIDE_TEXT)
    write_calibration_configs(out_dir)

    print(f"{len(open_floor_lines)} open-floor lines; drawn per stratum: {sample.drawn_count_by_stratum}")
    for note in sample.short_stratum_notes:
        print(f"  short stratum: {note}")
    return sample


def write_binary_owner_answers(human_path: Path, binary_path: Path) -> Path:
    """Write the owner's answers on the gate's scale: A, B and C become "not D", D stays D.

    Args:
        human_path: the owner's ``human.json`` (simple-golden shape, labels A–D).
        binary_path: where to write the binary copy.

    Returns:
        The path written; every row keeps its case index, key and note. Raises ValueError for a
        label that is not a kind (run the four-way calibration first: it lists every such problem).
    """
    owner_answers = json.loads(human_path.read_text())
    binary_rows = []
    for answer_row in owner_answers["labels"]:
        binary_row = dict(answer_row)
        binary_row["label"] = collapse_kind_to_gate_scale(str(answer_row["label"]).strip())
        binary_rows.append(binary_row)
    binary_answers = {"labeler": owner_answers.get("labeler", "owner"), "labels": binary_rows}
    binary_path.write_text(json.dumps(binary_answers, indent=2) + "\n")
    return binary_path


def score_packet(out_dir: Path = OUT_DIR) -> list[Path]:
    """Compare the readers and the gate with the owner's labels and write both reports.

    The four-way readers comparison runs first, because its check of ``human.json`` (every drawn
    key labelled once, with A–D) is what makes the binary collapse safe.

    Args:
        out_dir: the packet folder, holding ``human.json`` and the two configs.

    Returns:
        The report paths (markdown and JSON per source) under ``out_dir/reports``. Raises
        FileNotFoundError when ``human.json`` is missing, ValueError when it has problems.
    """
    human_path = out_dir / "human.json"
    if not human_path.exists():
        raise FileNotFoundError(
            f"{human_path} not found: fill in {out_dir / 'export' / 'answers_template.json'} and save it there"
        )
    readers_config = CalibrationConfig.model_validate_json((out_dir / "calib_readers.json").read_text())
    gate_config = CalibrationConfig.model_validate_json((out_dir / "calib_echo_gate.json").read_text())

    report_paths = stage_calibrate(readers_config)
    write_binary_owner_answers(human_path, gate_config.human_labels_path)
    report_paths += stage_calibrate(gate_config)
    return report_paths


def main() -> None:
    """Run ``build`` or ``score`` from the command line.

    Returns:
        None.
    """
    parser = argparse.ArgumentParser(description="Owner check of the echo gate and its readers.")
    parser.add_argument("command", choices=["build", "score"])
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR)
    args = parser.parse_args()
    if args.command == "build":
        build_packet(out_dir=args.out_dir)
    else:
        score_packet(args.out_dir)


if __name__ == "__main__":
    main()
