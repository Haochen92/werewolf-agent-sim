"""How accurate are the decision tags? A blind read of a sample against the game record (2026-10-13).

Record: evidence/memory_system/v8/experiment_log.md (the decision tags entry); data:
evidence/memory_system/v8/data/decision_tags/. The tags come from scripts/tag_observation_decisions.py.

  draw   six games at random, 17 random observations from each (the accuracy sample) plus up to ten of
         each game's flagged ones (a tag matching no recorded decision, or disagreeing with the day the
         text states), written as one reader file per game WITHOUT the tags: the reader names each
         observation's decision from the record itself (one Sonnet reader per game).
  score  compare the readers' answers (<game>.answers.json beside the reader files) with the tags.

  poetry run python evaluation/experiments/v8_decision_tag_check.py draw --work <dir>
  poetry run python evaluation/experiments/v8_decision_tag_check.py score --work <dir>
"""

from __future__ import annotations

import argparse
import collections
import glob
import json
import math
import random
from pathlib import Path

MAIN = Path(__file__).resolve().parents[2]
RUNS = "batch_results/extraction_runs/*_2026-10-12"
OUT = MAIN / "evidence/memory_system/v8/data/decision_tags"
SEED, GAMES, PER_GAME, FLAGGED = 20261013, 6, 17, 10


def _tags() -> dict[tuple, dict]:
    return {(r["game_id"], r["index"]): r for f in glob.glob(str(MAIN / RUNS / "decisions.jsonl"))
            for r in map(json.loads, open(f))}


def draw(work: Path) -> None:
    random.seed(SEED)
    cases = {}
    for f in glob.glob(str(MAIN / RUNS / "extracted.jsonl")):
        for line in open(f):
            c = json.loads(line)["output"]["extraction_case"]
            cases[c["game_id"]] = c
    tags = _tags()
    work.mkdir(parents=True, exist_ok=True)
    manifest = []
    for gid in random.sample(sorted(cases), GAMES):
        c = cases[gid]
        idx = list(range(1, len(c["observations"]) + 1))
        sample = sorted(random.sample(idx, PER_GAME))

        def flagged(i: int) -> bool:
            t = tags[(gid, i)]
            return t["status"] == "not_recorded" or (t["stated_day"] is not None
                                                     and t["stated_day"] != t["decision_day"])
        items = [(i, "random") for i in sample] + [(i, "flagged") for i in idx if i not in sample and flagged(i)][:FLAGGED]
        lessons = [{"index": i, "role": c["observations"][i - 1]["perspective"],
                    "phase": c["observations"][i - 1]["action_phase"],
                    "situation": c["observations"][i - 1].get("situation", ""),
                    "did": c["observations"][i - 1].get("approach", ""),
                    "immediately": c["observations"][i - 1].get("immediate_response", "")} for i, _ in items]
        (work / f"{gid[:8]}.json").write_text(json.dumps({"game_id": gid, "roles": c["roles"],
                                                          "record": c["formatted_discussions"], "lessons": lessons}))
        manifest.append({"game_id": gid, "items": items})
    (work / "manifest.json").write_text(json.dumps(manifest))


def score(work: Path) -> dict:
    tags = _tags()
    manifest = json.loads((work / "manifest.json").read_text())
    counts = {"random": collections.Counter(), "flagged": collections.Counter()}
    disagreements = []
    for m in manifest:
        answers = {a["index"]: a for a in json.loads((work / f"{m['game_id'][:8]}.answers.json").read_text())}
        for idx, which in m["items"]:
            t, a = tags[(m["game_id"], idx)], answers[idx]
            pack = t["perspective"] in ("chanteuse", "illusionist") and t["action_phase"] == "night_action"
            day_ok = t["decision_day"] == a["decision_day"]
            result = "agree" if day_ok and (not pack or t["pack_turn"] == a["pack_turn"]) else (
                "pack_turn" if day_ok else "day")
            counts[which][result] += 1
            if result != "agree":
                disagreements.append({"set": which, "game_id": m["game_id"], "index": idx, "role": t["perspective"],
                                      "phase": t["action_phase"], "tag": [t["decision_day"], t["pack_turn"]],
                                      "reader": [a["decision_day"], a["pack_turn"]], "confidence": a["confidence"],
                                      "reader_note": a["note"], "approach": t["approach"]})
    summary = {}
    for which, c in counts.items():
        n = sum(c.values())
        p = c["agree"] / n
        summary[which] = {**c, "n": n, "agree_rate": round(p, 3),
                          "ci95": round(1.96 * math.sqrt(p * (1 - p) / n), 3)}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "manifest.json").write_text(json.dumps(manifest))
    for f in work.glob("*.answers.json"):
        (OUT / f.name).write_text(f.read_text())
    (OUT / "disagreements.json").write_text(json.dumps(disagreements, indent=2))
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2))
    return summary


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("step", choices=("draw", "score"))
    ap.add_argument("--work", type=Path, required=True)
    args = ap.parse_args()
    if args.step == "draw":
        draw(args.work)
    else:
        print(json.dumps(score(args.work), indent=2))


if __name__ == "__main__":
    main()
