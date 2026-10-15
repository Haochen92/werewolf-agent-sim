"""Offline check of the sweep turns' echo gate (Phase 2 step 4c, discussion_evidence.md §7.4).

Before the gate judges live turns, see what it would hold on existing material: every spoken
proactive line of a voting day, judged against the lines said before it that day, the way the gate
sees them live. Sources: the June games' voting days (sequential proactive picks, so the shape is
the gate's own; the novelty gate of the time had already removed some echoes, so this UNDERSTATES
the live hold rate) and the Phase 2 chunk catalogue's game (its proactive lines were the parallel
round's, judged here one at a time).

Writes every held line next to the line it was judged to repeat, for reading by hand, and a hold
rate per source. One cheap judge call per line.

    poetry run python evaluation/experiments/line_echo_gate_check.py --out evidence/game_play_enhancement/data/line_echo_check --limit 20
"""

from __future__ import annotations

import argparse
import glob
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from Agents.schemas.game_events import DayChannel  # noqa: E402
from Agents.turn.echo_gate import line_echo_of  # noqa: E402

JUNE_GAMES = "batch_results/wolf_sk_mining_p*/games/*.jsonl"
CATALOGUE = "notebooks/fixtures/chunk_catalogue_phase2.jsonl"


def june_days() -> list[dict]:
    """One item per June voting day: the day's spoken lines in transcript order, with the
    proactive ones marked as the lines to judge."""
    days = []
    for path in sorted(glob.glob(JUNE_GAMES)):
        for line in open(path):
            record = json.loads(line)
            state = record.get("final_state") or record
            channel = state.get("day_channel") or []
            for day in sorted({m["day"] for m in channel}):
                if day == 1:
                    continue
                spoken = [
                    m for m in channel
                    if m["day"] == day and not m.get("passed") and m["player"] != "game_master"
                ]
                judged = [m for m in spoken if (m.get("firing_reason") or {}).get("tier") == "proactive"]
                if judged:
                    days.append({"source": "june", "game": Path(path).stem, "day": day,
                                 "spoken": spoken, "judged_seqs": [m["seq"] for m in judged]})
    return days


def catalogue_days() -> list[dict]:
    """The Phase 2 catalogue game's voting days: the published lines, with the proactive round's
    lines (and its held ones, as if they had been said) as the lines to judge."""
    path = Path(CATALOGUE)
    if not path.exists():
        return []
    channel: list[dict] = []
    for raw in path.read_text().splitlines()[1:]:
        part = json.loads(raw)
        if part["type"] != "updates":
            continue
        for node, delta in part["data"].items():
            if node in ("COLLECT_ROUND", "discuss", "START_CLOSING") and delta:
                channel.extend(delta.get("day_channel") or [])
    days = []
    for day in sorted({m["day"] for m in channel}):
        if day == 1:
            continue
        spoken = []
        judged = []
        for m in channel:
            if m["day"] != day or m["player"] == "game_master":
                continue
            if not m.get("passed"):
                spoken.append(m)
            elif m.get("gated_candidate"):
                spoken.append({**m, "message": m["gated_candidate"], "passed": False})
            else:
                continue
            if m.get("day_round") == "proactive":
                judged.append(m["seq"])
        if judged:
            days.append({"source": "catalogue", "game": path.stem, "day": day,
                         "spoken": spoken, "judged_seqs": judged})
    return days


def check_day(day: dict) -> dict:
    """Replay the day: each judged line is gated against the lines before it, held lines
    excluded from what later lines are judged against (as live)."""
    entries = [DayChannel.model_validate({**m, "firing_reason": None, "pass_reason": None,
                                          "gated": False, "gated_candidate": ""})
               for m in day["spoken"]]
    judged = set(day["judged_seqs"])
    earlier: list[DayChannel] = []
    held = []
    kept = []
    for entry in entries:
        if entry.seq in judged:
            echo_of = line_echo_of(entry.message, entry.player, earlier)
            if echo_of:
                matched = ""
                for previous in earlier:
                    if previous.player == echo_of:
                        matched = previous.message  # the player's latest line before this one
                held.append({"player": entry.player, "held": entry.message,
                             "same_point_as": echo_of, "matched_line": matched})
                continue
            kept.append({"player": entry.player, "message": entry.message})
        earlier.append(entry)
    return {**{k: day[k] for k in ("source", "game", "day")},
            "lines": [{"player": e.player, "message": e.message} for e in entries],
            "judged": len(judged), "kept": kept, "held": held}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--limit", type=int, default=0, help="cap the June days (0 = all)")
    args = parser.parse_args()
    load_dotenv(".env")

    days = catalogue_days()
    june = june_days()
    if args.limit:
        june = june[: args.limit]
    days += june
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    with ThreadPoolExecutor(args.workers) as pool:
        results = list(pool.map(check_day, days))

    with open(out / "results.jsonl", "w") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")

    report = ["# Echo gate: offline check, one line at a time\n"]
    for source in ("catalogue", "june"):
        rs = [r for r in results if r["source"] == source]
        n_judged = sum(r["judged"] for r in rs)
        n_held = sum(len(r["held"]) for r in rs)
        rate = (100 * n_held / n_judged) if n_judged else 0
        report.append(f"## {source}: {len(rs)} days, {n_judged} lines judged, {n_held} held ({rate:.0f}%)\n")
        for r in rs:
            if not r["held"]:
                continue
            report.append(f"### {r['game']} day {r['day']}\n")
            for h in r["held"]:
                report.append(f"- HELD {h['player']}: {h['held']}")
                report.append(f"  - same point as {h['same_point_as']}: {h['matched_line']}")
            report.append("")
    (out / "report.md").write_text("\n".join(report))
    print("\n".join(line for line in report if line.startswith("## ")))


if __name__ == "__main__":
    main()
