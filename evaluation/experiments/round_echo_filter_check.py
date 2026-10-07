"""Offline check of the proactive round's echo filter (Phase 2 step 4b, discussion_evidence.md §7.4).

Before the filter judges live rounds, see what it would hold on existing material:
- the June games' voting days: each day's spoken proactive lines, treated as if said at once
  (they were sequential, and the novelty gate had already removed some echoes, so this
  UNDERSTATES how much a true parallel round repeats itself);
- the Phase 2 smoke games' real proactive rounds (the better specimens, where they exist).

Writes every held line next to the line it was judged to repeat, for reading by hand, and a
hold rate per source. One cheap judge call per round.

    poetry run python evaluation/experiments/round_echo_filter_check.py --out evidence/game_play_enhancement/data/round_echo_check
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
from Agents.turn.round_filter import filter_round_echoes  # noqa: E402

JUNE_GAMES = "batch_results/wolf_sk_mining_p*/games/*.jsonl"
SMOKE_GAMES = [
    "evidence/game_play_enhancement/data/phase2_step4_smoke_game_2026-10-07.json",
    "evidence/game_play_enhancement/data/phase2_step4b_smoke_game_2026-10-07.json",
]


def june_rounds() -> list[dict]:
    """One pseudo-round per June voting day: the day's spoken proactive lines, in transcript order."""
    rounds = []
    for path in sorted(glob.glob(JUNE_GAMES)):
        for line in open(path):
            record = json.loads(line)
            state = record.get("final_state") or record
            channel = state.get("day_channel") or []
            for day in sorted({m["day"] for m in channel}):
                if day == 1:
                    continue
                lines = [
                    m for m in channel
                    if m["day"] == day and not m.get("passed") and m["player"] != "game_master"
                    and (m.get("firing_reason") or {}).get("tier") == "proactive"
                ]
                if len(lines) >= 2:
                    rounds.append({"source": "june", "game": Path(path).stem, "day": day, "lines": lines})
    return rounds


def smoke_rounds() -> list[dict]:
    """The real proactive rounds of the Phase 2 smoke games: each contiguous proactive block."""
    rounds = []
    for path in SMOKE_GAMES:
        if not Path(path).exists():
            continue
        channel = json.load(open(path))["day_channel"]
        block: list[dict] = []
        previous_round = None
        for m in channel + [None]:
            in_block = m is not None and m.get("day_round") == "proactive"
            if in_block and previous_round == "proactive":
                block.append(m)
            else:
                spoken = [x for x in block if not x.get("passed")]
                if len(spoken) >= 2:
                    rounds.append({"source": "smoke", "game": Path(path).stem, "day": block[0]["day"], "lines": spoken})
                block = [m] if in_block else []
            previous_round = m.get("day_round") if m is not None else None
    return rounds


def check_round(round_: dict) -> dict:
    entries = [DayChannel.model_validate({**m, "firing_reason": None}) for m in round_["lines"]]
    filtered = filter_round_echoes(entries)
    kept = {e.player: e.message for e in filtered if not e.passed}
    held = []
    for before, after in zip(entries, filtered):
        if after.passed and not before.passed:
            held.append({"player": before.player, "held": before.message})
    return {**round_, "lines": [{"player": e.player, "message": e.message} for e in entries],
            "kept": kept, "held": held}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--limit", type=int, default=0, help="cap the June rounds (0 = all)")
    args = parser.parse_args()
    load_dotenv()

    rounds = smoke_rounds() + june_rounds()
    if args.limit:
        rounds = [r for r in rounds if r["source"] == "smoke"] + [r for r in rounds if r["source"] == "june"][: args.limit]
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)

    with ThreadPoolExecutor(args.workers) as pool:
        results = list(pool.map(check_round, rounds))

    with open(out / "results.jsonl", "w") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")

    report = ["# Round echo filter: offline check\n"]
    for source in ("smoke", "june"):
        rs = [r for r in results if r["source"] == source]
        n_lines = sum(len(r["lines"]) for r in rs); n_held = sum(len(r["held"]) for r in rs)
        rate = (100 * n_held / n_lines) if n_lines else 0
        report.append(f"## {source}: {len(rs)} rounds, {n_lines} lines, {n_held} held ({rate:.0f}%)\n")
        for r in rs:
            if not r["held"]:
                continue
            report.append(f"### {r['game']} day {r['day']}\n")
            for h in r["held"]:
                report.append(f"- HELD {h['player']}: {h['held']}")
            report.append("- kept:")
            for player, message in r["kept"].items():
                report.append(f"  - {player}: {message}")
            report.append("")
    (out / "report.md").write_text("\n".join(report))
    print("\n".join(line for line in report if line.startswith("## ")))


if __name__ == "__main__":
    main()
