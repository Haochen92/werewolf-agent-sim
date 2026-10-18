"""Score the persona-voice before/after games (evaluation/experiments/persona_voice_games.py): talk, the
reads, the votes, per arm, paired by game id. No model call.

Reads are scored as the read ledger scores them (evaluation/src/loop/read_ledger.py: a committed read
against the true role, Brier at the confidence's coarse probability, 'unclear' counted apart), with the
ten-seat knowledge mask: a pack seat's read on its packmate is not a read. Sides are the role sheet's
(town, wolves, lone killer, neutral).

  poetry run python -m evaluation.experiments.persona_voice_games_score
"""

from __future__ import annotations

import gzip
import json
import re
import statistics
from collections import Counter, defaultdict
from pathlib import Path

from Agents.prompts.voices import house_puppet
from Agents.schemas.roles import TOWN, side_of

DATA = Path("evidence/game_play_enhancement/data/persona_voice_games")
CONF_P = {"high": 0.85, "low": 0.65}
"""As the read ledger: the read schema's two confidence levels as claimed probabilities."""


def games() -> dict[str, dict[str, dict]]:
    out: dict[str, dict[str, dict]] = defaultdict(dict)
    for path in sorted(DATA.glob("*.capture.json.gz")):
        game_id, arm = path.name.removesuffix(".capture.json.gz").rsplit(".", 1)
        out[game_id][arm] = json.loads(gzip.open(path, "rt").read())
    return {g: arms for g, arms in out.items() if {"on", "off"} <= set(arms)}


def spoken(state: dict) -> list[dict]:
    return [e for e in state["day_channel"] if e["player"] != "game_master" and (e.get("message") or "").strip()]


def read_rows(capture: dict) -> list[dict]:
    roles = capture["final_state"]["roles"]
    pack = {p for p, r in roles.items() if side_of(r) == "wolves"}
    rows = []
    for entry in capture["reads_log"]:
        actor = entry["player_id"]
        for read in entry.get("reads") or []:
            target, suspected = read.get("player"), read.get("suspected_role")
            if target not in roles or (actor in pack and target in pack):
                continue
            row = {"day": entry["day"], "unclear": suspected == "unclear"}
            if not row["unclear"]:
                truth = roles[target]
                p = CONF_P.get(read.get("confidence"), 0.65)
                row |= {"role_hit": suspected == truth, "brier": (p - (suspected == truth)) ** 2,
                        "side_hit": suspected in roles.values() and side_of(suspected) == side_of(truth)}
            rows.append(row)
    return rows


def town_votes(state: dict) -> Counter:
    roles = state["roles"]
    tally = Counter()
    for day in state.get("day_resolutions") or []:
        for vote in day.get("votes") or []:
            voter, target = vote.get("voter"), vote.get("votee")
            if side_of(roles[voter]) != TOWN:
                continue
            if not target or target == "abstain":
                tally["abstain"] += 1
            else:
                tally["on_town" if side_of(roles[target]) == TOWN else "on_not_town"] += 1
    return tally


def summarize(rows: list[dict]) -> dict:
    committed = [r for r in rows if not r["unclear"]]
    n = len(committed)
    return {"reads": len(rows), "committed": n,
            "unclear_rate": round(1 - n / len(rows), 3) if rows else None,
            "role_acc": round(sum(r["role_hit"] for r in committed) / n, 3) if n else None,
            "side_acc": round(sum(r["side_hit"] for r in committed) / n, 3) if n else None,
            "brier": round(statistics.mean(r["brier"] for r in committed), 4) if n else None}


def main() -> None:
    paired = games()
    report: dict = {"pairs": len(paired), "per_game": {}, "arms": {}}
    pooled = {"off": [], "on": []}
    votes = {"off": Counter(), "on": Counter()}
    by_voice: dict[str, list[int]] = defaultdict(list)
    openers: dict[str, Counter] = defaultdict(Counter)
    for game_id, arms in paired.items():
        report["per_game"][game_id] = {}
        for arm, capture in arms.items():
            state = capture["final_state"]
            lines = spoken(state)
            rows = read_rows(capture)
            pooled[arm] += rows
            votes[arm] += town_votes(state)
            report["per_game"][game_id][arm] = {
                "winner": state.get("winner"), "days": state.get("current_day"), "spoken_lines": len(lines),
                "words_median": statistics.median(len(e["message"].split()) for e in lines) if lines else None,
                **summarize(rows)}
            if arm == "on":
                for e in lines:
                    puppet = house_puppet(game_id, e["player"])
                    by_voice[puppet].append(len(e["message"].split()))
                    first = re.split(r"[\s,.!?:;]+", e["message"].strip())[0].lower()
                    openers[f"{game_id}:{e['player']}:{puppet}"][first] += 1
    for arm in ("off", "on"):
        lines = [len(e["message"].split()) for arms in paired.values() for e in spoken(arms[arm]["final_state"])]
        report["arms"][arm] = {"spoken_lines": len(lines),
                               "words_median": statistics.median(lines) if lines else None,
                               "town_votes": dict(votes[arm]), **summarize(pooled[arm])}
    report["words_by_voice"] = {p: {"lines": len(w), "median": statistics.median(w)} for p, w in sorted(by_voice.items())}
    report["repeated_openers"] = {seat: c.most_common(1)[0] for seat, c in openers.items()
                                  if sum(c.values()) >= 3 and c.most_common(1)[0][1] / sum(c.values()) >= 0.5}
    (DATA / "scores.json").write_text(json.dumps(report, indent=1))
    print(json.dumps({k: report[k] for k in ("pairs", "arms")}, indent=1))


if __name__ == "__main__":
    main()
