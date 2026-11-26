"""Owner check of the accusation tags: does a speaker's own "accusation" tag match whom its message
accuses, as the owner reads it?

Each speaker tags its own day-discussion message with whom it addresses and a stance per target
(``Agents/schemas/game_events.py::AddressedTarget``). The accusation tags pick who gets a closing
defence (``Agents/rules/closing.py``) and open reply obligations (``Agents/turn/scheduler.py``); they
had never been checked against a person on the ten-seat game. The model source ``speaker_tag`` is
the message's own accusation targets as a label: ``"none"`` or the ids in seat order, comma-joined.

Candidates: every spoken agent message of the ten-seat AI games in ``GAME_DIRS`` (34 games; passes,
held lines, moderator lines and human seats left out). Strata: messages the speaker tagged with at
least one accusation, and messages tagged with none. At most ``PER_GAME_CAP`` message per game is
kept in each stratum before the draw, since messages from one game are not independent; then
``PER_STRATUM`` are drawn from each stratum with a fixed seed.

What the owner does: read ``GUIDE.md`` in the packet folder, label the messages in ``export/batch_*.md``
by filling the ``label`` of each row in ``export/answers_template.json``, save that file as
``human.json`` in the packet folder, then run ``score``.

    poetry run python -m evaluation.experiments.owner_check_accusation_tags build
    poetry run python -m evaluation.experiments.owner_check_accusation_tags score
"""
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

from Agents.rules.closing import Accused, closing_announcement
from evaluation.src.labeling.adapters.accusation_tags import (
    ACCUSATION_RUBRIC,
    AccusationCandidate,
    AccusationTagsAdapter,
    NO_ACCUSATION,
    ContextLine,
    accused_label_from_players,
    canonical_accused_label,
)
from evaluation.src.labeling.anchor import draw_stratified_sample, write_stratum_file
from evaluation.src.labeling.config import CalibrationConfig, ExportConfig
from evaluation.src.labeling.exporter import export_for_manual
from evaluation.src.labeling.pipeline import stage_calibrate
from evaluation.src.labeling.schemas import StratifiedSample

GAME_DATA = Path("evidence/gameplay/data")
GAME_DIRS = [
    GAME_DATA / "phase3_flash_games",
    GAME_DATA / "phase3_balance",
    GAME_DATA / "phase3_balance_2",
    GAME_DATA / "phase3_balance_3",
    GAME_DATA / "phase3_balance_4",
]
PACKET_DIR = Path("evidence/evaluation/labeling/owner_checks/accusation_tags")

MODEL_SOURCE = "speaker_tag"
TAGGED_ACCUSATION_STRATUM = "tagged_accusation"
TAGGED_NONE_STRATUM = "tagged_none"
PER_STRATUM = 25
PER_GAME_CAP = 1
SEED = 20261023
EXPORT_BATCH_SIZE = 5
MODERATOR = "game_master"

EXPORT_INSTRUCTIONS = f"""\
# Owner check: whom does each message accuse?

Read the lines before each message, then the message. Write your label in the matching row of
`answers_template.json` (same key), and save the filled file as `human.json` in the packet folder.
The full guide, with worked examples, is `GUIDE.md`.

{ACCUSATION_RUBRIC}

For example `player_4`, or `player_3,player_10` (seat 3 before seat 10)."""

GUIDE_TEMPLATE = """\
# Owner check: the accusation tags

## What this measures

In the day discussion every speaker tags its own message with the players it addresses and a stance
toward each: accusation, defense, agreement or neutral. The accusation tags decide who gets a closing
defence before the vote and whom the scheduler makes answer next. This check measures how often the
speaker's own accusation tags match whom you, reading the message, say it accuses. Your label is the
truth; the comparison is made afterwards and you never see the tags.

## What you do

1. Open `export/batch_01.md` to `export/batch_{last_batch:02d}.md` ({item_count} messages from
   {game_count} games, {batch_size} per batch).
2. For each message, read the lines before it, then the message, and decide whom it accuses.
3. Write your answer in the `label` of the row with the same key in `export/answers_template.json`
   (`note` is for anything you were unsure about). The rows are in the same order as the batches.
4. Save the filled file as `human.json` in this folder and run
   `poetry run python -m evaluation.experiments.owner_check_accusation_tags score`.
   A label written loosely (`player_10, player_3`) is rejected with the exact fix to make.

## The rubric

{rubric}

For example `player_4`, or `player_3,player_10` (seat 3 before seat 10).

## Worked examples

These are made up from the definitions the speakers were given; none is from the sample.

- *"player_4 says they are the healer but will not name one person they protected. I think that
  claim is a lie, and I'm voting player_4."* → `player_4`. It blames player_4 of lying.
- *"player_6 has been very quiet today. player_2, what did you see last night?"* → `none`. Noting
  that someone is quiet is passing commentary, and the question asks for information without
  casting suspicion.
- *"I trust player_3's check. That leaves player_9 or player_5 as our wolf: both pushed the same
  story yesterday."* → `player_5,player_9`. It suspects both (ids in seat order); supporting
  player_3 is a defence, not an accusation.
"""


def find_record_paths(game_dirs: list[Path]) -> list[Path]:
    """Return every game record file in the given folders, sorted by path.

    Args:
        game_dirs: folders holding ``<game>.record.json`` files, e.g. ``GAME_DIRS``.

    Returns:
        The record paths. Raises FileNotFoundError when a folder has no record file.
    """
    record_paths: list[Path] = []
    for game_dir in game_dirs:
        dir_record_paths = sorted(game_dir.glob("*.record.json"))
        if not dir_record_paths:
            raise FileNotFoundError(f"No *.record.json in {game_dir}")
        record_paths.extend(dir_record_paths)
    return record_paths


def is_heard_agent_message(channel_entry: dict, human_seats: set[str]) -> bool:
    """Return whether a day-channel entry is an AI player's line the table heard.

    Args:
        channel_entry: one ``day_channel`` entry of a game record.
        human_seats: the player ids played by a person in that game.

    Returns:
        False for the moderator, a human seat, a pass, or a held line (held lines are passes with
        an empty message); True otherwise.
    """
    if channel_entry["player"] == MODERATOR or channel_entry["player"] in human_seats:
        return False
    if channel_entry.get("passed"):
        return False
    return bool(channel_entry.get("message", "").strip())


def is_heard_line(channel_entry: dict) -> bool:
    """Return whether the table heard a day-channel entry: a moderator line or any spoken line.

    Args:
        channel_entry: one ``day_channel`` entry of a game record.

    Returns:
        True for a non-pass entry with a message, whoever spoke it.
    """
    if channel_entry.get("passed"):
        return False
    return bool(channel_entry.get("message", "").strip())


def closing_call_without_accusers(moderator_text: str) -> str:
    """Return a recorded closing call in the current wording, which names only who speaks.

    The recorded games' call named the accusers ("player_4 has been accused by player_2, player_9
    and player_6; ..."). Those names are counted from the very tags under check, so showing them
    would unblind the owner; the current moderator wording leaves them out.

    Args:
        moderator_text: the recorded moderator line, e.g. ``"Before the vote: player_4 has been
            accused by player_2 and player_9; player_2 by player_4 and player_10. Each gets a last
            word."``.

    Returns:
        The current wording, e.g. ``"Before the vote: player_4 and player_2 each get a last
        word."``; any other moderator line unchanged.
    """
    if not moderator_text.startswith("Before the vote:") or "accused by" not in moderator_text:
        return moderator_text

    call_body = moderator_text[len("Before the vote:"):]
    accused_players: list[str] = []
    for accused_clause in call_body.split(";"):
        accused_player = accused_clause.split()[0]
        # closing_announcement reads only the player; the accusers and position are not used.
        accused_players.append(accused_player)
    return closing_announcement([Accused(player, (), 0) for player in accused_players])


def context_line(channel_entry: dict) -> ContextLine:
    """Return a heard day-channel entry as a context line, with closing calls stripped of accusers.

    Args:
        channel_entry: one heard ``day_channel`` entry.

    Returns:
        The speaker and the text as shown to the labeller.
    """
    line_text = channel_entry["message"].strip()
    if channel_entry["player"] == MODERATOR:
        line_text = closing_call_without_accusers(line_text)
    return ContextLine(speaker=channel_entry["player"], text=line_text)


def lines_since_last_discussion(day_channel: list[dict], day: int) -> list[ContextLine]:
    """Return the moderator lines that closed the previous day: its vote result and the night after.

    Args:
        day_channel: the game's whole ``day_channel``.
        day: the day of the message being labelled.

    Returns:
        The moderator lines of day ``day - 1`` that come after its last heard player line; empty
        on day 1.
    """
    previous_day_entries = [entry for entry in day_channel if entry["day"] == day - 1]
    last_player_line_index = -1
    for entry_index, entry in enumerate(previous_day_entries):
        if entry["player"] != MODERATOR and is_heard_line(entry):
            last_player_line_index = entry_index

    closing_moderator_lines: list[ContextLine] = []
    for entry in previous_day_entries[last_player_line_index + 1:]:
        if entry["player"] == MODERATOR and is_heard_line(entry):
            closing_moderator_lines.append(context_line(entry))
    return closing_moderator_lines


def lines_heard_earlier_today(day_channel: list[dict], message_index: int) -> list[ContextLine]:
    """Return the lines heard today before a message, in order.

    The opening round is spoken all at once, so an opening message gets no other opening line.

    Args:
        day_channel: the game's whole ``day_channel``, in transcript order.
        message_index: the position of the labelled message in ``day_channel``.

    Returns:
        The heard lines (players and moderator) of the same day that precede the message.
    """
    message_entry = day_channel[message_index]
    earlier_lines: list[ContextLine] = []
    for entry in day_channel[:message_index]:
        if entry["day"] != message_entry["day"] or not is_heard_line(entry):
            continue
        if message_entry["day_round"] == "opening" and entry["day_round"] == "opening":
            continue
        earlier_lines.append(context_line(entry))
    return earlier_lines


def speaker_tag_label(channel_entry: dict) -> str:
    """Return the speaker's own accusation tags on a message as a label.

    Args:
        channel_entry: one ``day_channel`` entry, with ``addressed_targets`` like
            ``[{"target": "player_3", "addressed_form": "mention", "stance": "accusation"}]``.

    Returns:
        ``"none"`` or the accused ids in seat order, e.g. ``"player_3,player_7"``.
    """
    accused_players: list[str] = []
    for addressed_target in channel_entry.get("addressed_targets", []):
        if addressed_target["stance"] == "accusation":
            accused_players.append(addressed_target["target"])
    return accused_label_from_players(accused_players)


def build_candidates(record_paths: list[Path]) -> tuple[list[AccusationCandidate], dict[str, str]]:
    """Return every heard AI message of the games as a candidate, and the speaker's label for each.

    Args:
        record_paths: game record files, e.g. ``[.../f01.record.json]``; the file name before
            ``.record.json`` names the game in each key.

    Returns:
        ``(candidates, speaker_tag_label_by_key)``: candidates in game then transcript order with
        ``case_index`` counting from 0, and ``{"f01:d2:s15": "player_3", ...}``. Raises ValueError
        if two messages get the same key.
    """
    candidates: list[AccusationCandidate] = []
    speaker_tag_label_by_key: dict[str, str] = {}
    for record_path in record_paths:
        game = record_path.name.removesuffix(".record.json")
        game_record = json.loads(record_path.read_text())
        human_seats = set(game_record.get("humans", []))
        day_channel = game_record["day_channel"]

        for message_index, channel_entry in enumerate(day_channel):
            if not is_heard_agent_message(channel_entry, human_seats):
                continue
            key = f"{game}:d{channel_entry['day']}:s{channel_entry['seq']}"
            if key in speaker_tag_label_by_key:
                raise ValueError(f"Two messages share the key {key}")
            candidates.append(
                AccusationCandidate(
                    key=key,
                    case_index=len(candidates),
                    game=game,
                    day=channel_entry["day"],
                    seq=channel_entry["seq"],
                    day_round=channel_entry["day_round"],
                    speaker=channel_entry["player"],
                    message=channel_entry["message"].strip(),
                    since_last_discussion=lines_since_last_discussion(day_channel, channel_entry["day"]),
                    earlier_today=lines_heard_earlier_today(day_channel, message_index),
                )
            )
            speaker_tag_label_by_key[key] = speaker_tag_label(channel_entry)
    return candidates, speaker_tag_label_by_key


def stratum_of_label(speaker_label: str) -> str:
    """Return the stratum of a message from the speaker's label.

    Args:
        speaker_label: ``"none"`` or accused ids.

    Returns:
        ``TAGGED_NONE_STRATUM`` for ``"none"``, else ``TAGGED_ACCUSATION_STRATUM``.
    """
    if speaker_label == NO_ACCUSATION:
        return TAGGED_NONE_STRATUM
    return TAGGED_ACCUSATION_STRATUM


def cap_keys_per_game(
    candidates: list[AccusationCandidate], stratum_by_key: dict[str, str], per_game_cap: int, seed: int
) -> list[str]:
    """Return the candidate keys left after keeping at most ``per_game_cap`` per game in each stratum.

    Messages of one game share a discussion and speakers, so they are not independent; capping
    each game before the draw spreads the sample over many games.

    Args:
        candidates: every candidate message.
        stratum_by_key: the stratum of each candidate key.
        per_game_cap: how many keys one game may keep in each stratum (at least 1).
        seed: the random seed; each (game, stratum) group gets its own generator.

    Returns:
        The kept keys, sorted. Raises ValueError if ``per_game_cap`` is below 1.
    """
    if per_game_cap < 1:
        raise ValueError(f"per_game_cap must be at least 1, got {per_game_cap}")

    keys_by_game_and_stratum: dict[tuple[str, str], list[str]] = {}
    for candidate in candidates:
        group = (candidate.game, stratum_by_key[candidate.key])
        keys_by_game_and_stratum.setdefault(group, []).append(candidate.key)

    kept_keys: list[str] = []
    for (game, stratum), group_keys in sorted(keys_by_game_and_stratum.items()):
        group_rng = random.Random(f"{seed}:{game}:{stratum}")
        kept_keys.extend(group_rng.sample(sorted(group_keys), min(per_game_cap, len(group_keys))))
    return sorted(kept_keys)


def write_candidates(candidates: list[AccusationCandidate], path: Path) -> Path:
    """Write the candidates file the adapter reads.

    Args:
        candidates: every candidate message.
        path: where to write.

    Returns:
        The path written, holding ``{"candidates": [...]}``.
    """
    candidate_records = [candidate.model_dump(mode="json") for candidate in candidates]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"candidates": candidate_records}, indent=2) + "\n")
    return path


def write_model_labels(
    candidates: list[AccusationCandidate], label_by_key: dict[str, str], labeler: str, path: Path
) -> Path:
    """Write one model source's labels for every candidate, in the pipeline's simple-golden shape.

    Args:
        candidates: every candidate message (supplies each key's ``case_index``).
        label_by_key: the source's label per key.
        labeler: the source's name, e.g. ``"speaker_tag"``.
        path: where to write.

    Returns:
        The path written, holding ``{"labeler": ..., "labels": [{"case_index", "key", "label"}]}``.
    """
    label_rows = []
    for candidate in candidates:
        label_rows.append(
            {"case_index": candidate.case_index, "key": candidate.key, "label": label_by_key[candidate.key]}
        )
    path.write_text(json.dumps({"labeler": labeler, "labels": label_rows}, indent=2) + "\n")
    return path


def calibration_config(packet_dir: Path) -> CalibrationConfig:
    """Return the ready calibration config for a packet folder.

    Args:
        packet_dir: the packet folder; its ``human.json`` is the owner's file.

    Returns:
        The config: ``speaker_tag`` against the owner, per stratum, reports in ``reports/``.
        The labels are open (no ``allowed_labels``), so the directional-bias test is skipped.
    """
    return CalibrationConfig(
        human_labels_path=packet_dir / "human.json",
        model_label_paths=[packet_dir / f"{MODEL_SOURCE}_labels.json"],
        model_sources=[MODEL_SOURCE],
        stratum_path=packet_dir / "strata.json",
        allowed_labels=None,
        positive_label=None,
        output_dir=packet_dir / "reports",
    )


def build(
    game_dirs: list[Path], packet_dir: Path, per_stratum: int, per_game_cap: int, seed: int
) -> StratifiedSample:
    """Build the owner's packet: candidates, model labels, strata, export, guide and calibration config.

    Args:
        game_dirs: folders of ten-seat game records.
        packet_dir: the packet folder to write, e.g. ``PACKET_DIR``.
        per_stratum: how many messages to draw from each stratum.
        per_game_cap: how many messages one game may give each stratum.
        seed: the random seed for the cap and the draw.

    Returns:
        The drawn sample. Prints the corpus and sample sizes per stratum.
    """
    record_paths = find_record_paths(game_dirs)
    candidates, speaker_tag_label_by_key = build_candidates(record_paths)

    stratum_by_key: dict[str, str] = {}
    for key, speaker_label in speaker_tag_label_by_key.items():
        stratum_by_key[key] = stratum_of_label(speaker_label)

    capped_keys = cap_keys_per_game(candidates, stratum_by_key, per_game_cap, seed)
    sample = draw_stratified_sample(capped_keys, stratum_by_key, per_stratum, seed)

    candidates_path = write_candidates(candidates, packet_dir / "candidates.json")
    write_model_labels(
        candidates, speaker_tag_label_by_key, MODEL_SOURCE, packet_dir / f"{MODEL_SOURCE}_labels.json"
    )
    write_stratum_file(sample.drawn_keys, stratum_by_key, packet_dir / "strata.json")
    batch_paths = export_for_manual(
        ExportConfig(
            candidates_path=candidates_path,
            output_dir=packet_dir / "export",
            batch_size=EXPORT_BATCH_SIZE,
            keys=sample.drawn_keys,
            write_answers_template=True,
        ),
        AccusationTagsAdapter(),
        EXPORT_INSTRUCTIONS,
    )

    drawn_games = {key.split(":")[0] for key in sample.drawn_keys}
    guide_text = GUIDE_TEMPLATE.format(
        last_batch=len(batch_paths),
        item_count=len(sample.drawn_keys),
        game_count=len(drawn_games),
        batch_size=EXPORT_BATCH_SIZE,
        rubric=ACCUSATION_RUBRIC,
    )
    (packet_dir / "GUIDE.md").write_text(guide_text)
    (packet_dir / "calib.json").write_text(calibration_config(packet_dir).model_dump_json(indent=2) + "\n")

    _print_sizes(record_paths, candidates, stratum_by_key, capped_keys, sample)
    return sample


def _print_sizes(
    record_paths: list[Path],
    candidates: list[AccusationCandidate],
    stratum_by_key: dict[str, str],
    capped_keys: list[str],
    sample: StratifiedSample,
) -> None:
    """Print the corpus, the capped pool and the draw, per stratum.

    Args:
        record_paths: the game records read.
        candidates: every candidate message.
        stratum_by_key: the stratum of each candidate key.
        capped_keys: the keys left after the per-game cap.
        sample: the draw.

    Returns:
        None.
    """
    print(f"\n{len(record_paths)} games, {len(candidates)} heard AI messages")
    for stratum in (TAGGED_ACCUSATION_STRATUM, TAGGED_NONE_STRATUM):
        corpus_count = sum(1 for candidate in candidates if stratum_by_key[candidate.key] == stratum)
        capped_count = sum(1 for key in capped_keys if stratum_by_key[key] == stratum)
        drawn_count = sample.drawn_count_by_stratum.get(stratum, 0)
        print(f"  {stratum}: {corpus_count} in corpus, {capped_count} after the per-game cap, {drawn_count} drawn")
    for note in sample.short_stratum_notes:
        print(f"  short: {note}")

    drawn_count_by_game: dict[str, int] = {}
    for key in sample.drawn_keys:
        game = key.split(":")[0]
        drawn_count_by_game[game] = drawn_count_by_game.get(game, 0) + 1
    print(
        f"  drawn: {len(sample.drawn_keys)} messages from {len(drawn_count_by_game)} games, "
        f"at most {max(drawn_count_by_game.values(), default=0)} from one game"
    )


def check_owner_labels_canonical(human_labels_path: Path) -> None:
    """Check every filled label in the owner's file is written in canonical form.

    Calibration compares labels as text, so ``player_10,player_2`` would count as a disagreement
    with ``player_2,player_10``. Empty labels are left to the calibration's own check.

    Args:
        human_labels_path: the owner's ``human.json``.

    Returns:
        None. Raises ValueError listing every label to rewrite, with its canonical form.
    """
    owner_file = json.loads(human_labels_path.read_text())
    problems: list[str] = []
    for label_row in owner_file.get("labels", []):
        owner_label = label_row.get("label")
        if owner_label is None or not str(owner_label).strip():
            continue
        try:
            canonical_label = canonical_accused_label(str(owner_label))
        except ValueError as label_error:
            problems.append(f"key {label_row.get('key')!r}: {label_error}")
            continue
        if canonical_label != owner_label:
            problems.append(f"key {label_row.get('key')!r}: write {canonical_label!r}, not {owner_label!r}")
    if problems:
        raise ValueError(f"Fix these labels in {human_labels_path}:\n  " + "\n  ".join(problems))


def score(packet_dir: Path) -> list[Path]:
    """Score the speaker tags against the owner's labels with the pipeline's calibrate stage.

    Args:
        packet_dir: the packet folder holding ``calib.json`` and the owner's ``human.json``.

    Returns:
        The report paths written under ``reports/``. Raises FileNotFoundError when ``human.json``
        is missing, ValueError when a label is not canonical or the file fails calibration's checks.
    """
    config = CalibrationConfig.model_validate_json((packet_dir / "calib.json").read_text())
    if not config.human_labels_path.exists():
        raise FileNotFoundError(
            f"{config.human_labels_path} not found: fill export/answers_template.json and save it there"
        )
    check_owner_labels_canonical(config.human_labels_path)
    return stage_calibrate(config)


def main() -> None:
    """Run the ``build`` or ``score`` command on the default packet folder."""
    parser = argparse.ArgumentParser(description="Owner check of the speakers' accusation tags.")
    parser.add_argument("command", choices=["build", "score"])
    args = parser.parse_args()
    if args.command == "build":
        build(GAME_DIRS, PACKET_DIR, PER_STRATUM, PER_GAME_CAP, SEED)
    else:
        score(PACKET_DIR)


if __name__ == "__main__":
    main()
