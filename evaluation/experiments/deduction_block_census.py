"""How long the deduction blocks are (slice 8 of the deduction engine), over every turn of the saved
Haiku games, before any model sees them.

Record: evidence/gameplay/deduction/deduction_catalogue.md ("Build status", slice 8) and the output
folder evidence/gameplay/deduction/data/deduction_block_census/. No model call: the renderer
(Agents/deduction/render.py) runs on each turn's payload as the checked-out engine builds it, in
"full" mode, and the public block and the seat block are measured apart (lines are the "- " lines
under the heading; characters are the whole block, heading included).

Two sources of turns:
- the frozen cases (evidence/gameplay/deduction/data/haiku_effort_replay/, deduction_injection/):
  each turn's own payload, rebuilt by the replay bench (`turn_payload`);
- captured server games (--captures): every prompt a seat was sent, its payload rebuilt from the
  game's final state as of that turn (the roster, mornings and wills up to it, the seat's own records
  before that night, today's transcript up to the line the prompt showed, the day summaries written
  by then, whose claims the joins and the conditionals read since slices 9b and 10; a vote turn
  is marked, as the vote's payload is). Prompts of the human seat
  (its drafts) are left out: a human seat never gets the blocks. A capture is exported read-only as

    psql -At -c "select encode(capture,'base64') from prompt_captures where game_id='<id>'" | base64 -d > <id>.json.gz

  next to <id>.meta.json holding {"human_players": [...]} from the games table.

  poetry run python evaluation/experiments/deduction_block_census.py --captures <dir>
"""

from __future__ import annotations

import argparse
import gzip
import json
import statistics
from pathlib import Path
from typing import Any

from Agents.deduction import deduction_blocks, fold_own_lines, own_result_lines, seat_view_from_payload
from Agents.prompts.prompt_formatters import format_day_channel
from Agents.rules.night_record import own_night_actions
from Agents.rules.public_prose import public_data_from_summaries
from Agents.rules.seats import seat_order
from Agents.schemas.game_events import DayChannel, DaySummary, DeathRecord, NightActionRecord
from Agents.schemas.roles import ROLE_SPECS, cast_role_counts

FROZEN = Path("evidence/gameplay/deduction/data")
FROZEN_FILES = ["haiku_effort_replay/turn_cases.jsonl", "haiku_effort_replay/vote_cases.jsonl",
                "deduction_injection/cases.jsonl", "deduction_injection/silence_cases.jsonl"]
OUT = FROZEN / "deduction_block_census"
CONDITIONAL_ROWS = ("F4", "F5", "F6")
EVIL_OWN_ROWS = ("F7+L8", "E4b+own", "E14+own", "E2a+own")
"""An evil seat's own lines (owner, 2026-10-17): a hidden body's role it can claim, and its own visits
against the claims it might make."""
COMPARISON_GROUPS = {"Table E": lambda row: row.startswith("E") and row not in EVIL_OWN_ROWS,
                     "claim status": lambda row: row == "F3+E15",
                     "evil seat's roles": lambda row: row == "F7+E15",
                     "evil seat's own lines": lambda row: row in EVIL_OWN_ROWS}
"""The comparisons (slice 11): a Table E line (a comparison of claims, a role claim the seat knows is
false), the role claims' status line, an evil seat's claimable roles, and its own lines."""
LEVEL_7 = {"F8": "seat", "F9": "public", "F1+C7": "seat"}
"""Slice 12: a claim's possible explanations (F8, seat block), a used-up budget (F9, public block), and
the known Chanteuse's visit read as her block (AC2 line 3, seat block)."""
DAY_KEYS = ("day_channel", "day_votes")
"""The output keys of day turns; every other key is a night turn (an action, the wolf chat, the kill)."""


# --- the turns ------------------------------------------------------------------------------------

def frozen_turns() -> list[dict[str, Any]]:
    from evaluation.src.replay.hallucination_bench import turn_payload

    turns = []
    for name in FROZEN_FILES:
        for line in (FROZEN / name).read_text().splitlines():
            if line.strip():
                case = json.loads(line)
                turns.append({"source": f"frozen:{name}", "game": case["game_id"], "day": case["day"],
                              "kind": case["phase"], "player": case["speaker"], "role": case["role"],
                              "payload": turn_payload(case)})
    return turns


def captured_turns(folder: Path) -> list[dict[str, Any]]:
    turns = []
    for path in sorted(folder.glob("*.json.gz")):
        game = path.name.removesuffix(".json.gz")
        capture = json.loads(gzip.decompress(path.read_bytes()))
        meta = json.loads((folder / f"{game}.meta.json").read_text())
        state = _final_state(capture["final_state"])
        for entry in capture["prompt_log"]:
            if entry["player_id"] in meta["human_players"]:
                continue
            turns.append({"source": "captured", "game": game[:8], "day": entry["day"], "kind": entry["output_key"],
                          "player": entry["player_id"], "role": entry["player_role"],
                          "payload": _payload_at(state, entry)})
    return turns


def _final_state(raw: dict[str, Any]) -> dict[str, Any]:
    summaries = [DaySummary.model_validate(s) for s in raw["day_summaries"]]
    mornings, wills = public_data_from_summaries(summaries)
    return {"roles": raw["roles"], "dead_roster": [DeathRecord.model_validate(d) for d in raw["dead_roster"]],
            "day_channel": [DayChannel.model_validate(m) for m in raw["day_channel"]],
            "night_actions": [NightActionRecord.model_validate(r) for r in raw["night_actions"]],
            "mornings": mornings, "wills": wills, "summaries": summaries}


def _known_then(day: int, phase: str, turn_day: int, night_turn: bool) -> bool:
    """Whether a death (or the will read out with it) of `day`/`phase` was public at the turn: the
    night deaths before it, and the lynches before its day (or of its day, at night)."""
    if phase == "night":
        return day < turn_day
    return day <= turn_day if night_turn else day < turn_day


def _payload_at(state: dict[str, Any], entry: dict[str, Any]) -> dict[str, Any]:
    """The seat's payload at that turn, as the payload builders made it (Agents/nodes/day/flow.py,
    Agents/nodes/night/solo.py, pack.py), with the engine's data fields set from the final state."""
    day, player, role = entry["day"], entry["player_id"], entry["player_role"]
    night_turn = entry["output_key"] not in DAY_KEYS
    dead = [d for d in state["dead_roster"] if _known_then(d.day, d.phase, day, night_turn)]
    living = seat_order(p for p in state["roles"] if p not in {d.player for d in dead})
    records = [r for r in state["night_actions"] if r.day < day]
    payload = {
        "player_id": player, "player_role": role, "current_day": day, "deduction_mode": "full",
        "cast_role_counts": cast_role_counts(state["roles"]),
        "dead_roster": dead,
        "night_announcements": [m for m in state["mornings"] if m.night < day],
        "read_out_wills": [w for w in state["wills"] if _known_then(w.day, w.phase, day, night_turn)],
        "night_actions": own_night_actions(records, player, role),
        "surviving_players": living,
        "day_channel": _transcript_then(state["day_channel"], day, entry["prompt_input"].get("day_channel", "")),
        # The claims of earlier days come from their summaries (slice 9b reads them); today's is written
        # after the discussion, before the vote, so a vote or a night turn has it too.
        "day_summaries": [s for s in state["summaries"] if s.day < day or (s.day == day and entry["output_key"] != "day_channel")],
        # A vote turn reads a conditional about a player as its contrapositive (slice 10, fold rule 3).
        "vote_turn": entry["output_key"] == "day_votes",
    }
    if ROLE_SPECS[role].pack:
        payload["pack_roles"] = {p: r for p, r in state["roles"].items() if p in living and ROLE_SPECS[r].pack}
    return payload


def _transcript_then(channel: list[DayChannel], day: int, shown: str) -> list[DayChannel]:
    """Today's transcript up to the line the prompt showed: the longest prefix whose published lines
    are exactly the ones in the prompt (passes add no line). Earlier days ride along unchanged."""
    earlier = [m for m in channel if m.day < day]
    today = [m for m in channel if m.day == day]
    for cut in range(len(today), -1, -1):
        if format_day_channel(today[:cut]) == shown:
            return earlier + today[:cut]
    raise ValueError(f"day {day}: no prefix of the transcript matches the prompt")


# --- the measurement ------------------------------------------------------------------------------

def measure(turn: dict[str, Any]) -> dict[str, Any]:
    payload = turn["payload"]
    view = seat_view_from_payload(payload)
    lines = fold_own_lines(view.night_records, own_result_lines(view))
    blocks = deduction_blocks(view, lines, payload.get("day_channel", []), payload.get("current_day", 1),
                              vote=bool(payload.get("vote_turn")))
    row = {key: turn[key] for key in ("source", "game", "day", "kind", "player", "role")}
    for name in CONDITIONAL_ROWS:  # the conditionals (slice 10): how many of the seat block's items
        row[name] = sum(1 for item in blocks.seat.shown if item.row == name)
    for name, of in COMPARISON_GROUPS.items():  # the comparisons (slice 11)
        row[name] = sum(1 for item in blocks.seat.shown if of(item.row))
    row["comparison_rows"] = sorted(item.row for item in blocks.seat.shown
                                    if item.row.startswith("E") or item.row in EVIL_OWN_ROWS)
    for name, block in LEVEL_7.items():  # slice 12
        row[name] = sum(1 for item in getattr(blocks, block).shown if item.row == name)
    for name, block in (("public", blocks.public), ("seat", blocks.seat)):
        row[f"{name}_lines"] = sum(1 for line in block.text.splitlines() if line.startswith("- "))
        row[f"{name}_chars"] = len(block.text)
        row[f"{name}_text"] = block.text
    return row


def _spread(values: list[int]) -> dict[str, float]:
    ordered = sorted(values)
    p90 = ordered[min(len(ordered) - 1, int(round(0.9 * (len(ordered) - 1))))]
    return {"median": statistics.median(ordered), "p90": p90, "max": ordered[-1], "mean": round(statistics.mean(ordered), 1)}


def summarise(rows: list[dict[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {"turns": len(rows)}
    groups = {"all": rows, "frozen": [r for r in rows if r["source"].startswith("frozen")],
              "captured": [r for r in rows if r["source"] == "captured"]}
    for label, group in groups.items():
        if not group:
            continue
        out[label] = {"turns": len(group)}
        for measure_ in ("public_lines", "public_chars", "seat_lines", "seat_chars"):
            out[label][measure_] = _spread([r[measure_] for r in group])
        out[label]["both_chars"] = _spread([r["public_chars"] + r["seat_chars"] for r in group])
        out[label]["empty_seat_block"] = sum(1 for r in group if not r["seat_lines"])
        out[label]["turns_with"] = {name: sum(1 for r in group if r[name]) for name in CONDITIONAL_ROWS}
        out[label]["turns_with"]["any conditional"] = sum(1 for r in group if any(r[n] for n in CONDITIONAL_ROWS))
        out[label]["conditional_items"] = {name: sum(r[name] for r in group) for name in CONDITIONAL_ROWS}
        out[label]["turns_with_comparisons"] = {name: sum(1 for r in group if r[name]) for name in COMPARISON_GROUPS}
        rows_seen: dict[str, int] = {}
        for r in group:
            for name in r["comparison_rows"]:
                rows_seen[name] = rows_seen.get(name, 0) + 1
        out[label]["table_e_items"] = dict(sorted(rows_seen.items()))
        out[label]["turns_with_level_7"] = {name: sum(1 for r in group if r[name]) for name in LEVEL_7}
    out["games"] = sorted({r["game"] for r in rows})
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--captures", type=Path, help="folder of exported server captures (<id>.json.gz, <id>.meta.json)")
    args = parser.parse_args()

    from Agents.run_fingerprint import git_revision

    turns = frozen_turns() + (captured_turns(args.captures) if args.captures else [])
    rows = [measure(turn) for turn in turns]
    summary = {"pointer": {"code": "evaluation/experiments/deduction_block_census.py", **git_revision()},
               **summarise(rows)}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "census.json").write_text(json.dumps(summary, indent=1) + "\n")

    longest, shown = [], set()
    for row in sorted(rows, key=lambda r: r["public_chars"] + r["seat_chars"], reverse=True):
        if (row["public_text"], row["seat_text"]) not in shown:  # a seat's turns of one day often repeat a block
            shown.add((row["public_text"], row["seat_text"]))
            longest.append(row)
        if len(longest) == 3:
            break
    parts = ["# The three longest distinct deduction blocks (public + seat characters)\n",
             "Written by `evaluation/experiments/deduction_block_census.py`; numbers in `census.json`.\n"]
    for rank, row in enumerate(longest, 1):
        parts.append(f"## {rank}. {row['game']} day {row['day']}, {row['kind']}, {row['player']} ({row['role']})\n")
        parts.append(f"Public block: {row['public_lines']} lines, {row['public_chars']} characters. "
                     f"Seat block: {row['seat_lines']} lines, {row['seat_chars']} characters.\n")
        parts.append("```\n" + row["public_text"] + "\n```\n")
        parts.append("```\n" + (row["seat_text"] or "(no seat block)") + "\n```\n")
    (OUT / "longest_blocks.md").write_text("\n".join(parts))
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
