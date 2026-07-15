"""Injection-channel replay screen (±tell book) — design record §8 gate 3, the hedge behind dropping
observation injection: does a tell book move decisions AT ALL? Frozen v6ab day-vote decisions are
regenerated twice on a bare memory block (no obs, no SPs — the contrast isolates the book), once with
WW_TELL_BOOK set and once without, through the SAME live injection path the run will use
(Agents/memory/tell_book.py -> build_agent_prompt_input -> the {tell_book} slot). Scored by the
deterministic vote facts; paired per decision (McNemar counts).

It answers channel-liveness only — "with the book, do decisions change, and do correct ones become
more frequent" — not compounding, not lift quality. The replayed decisions are OLD-epoch (v6ab), so a
positive here still leaves cross-epoch transfer as a first-generation readout (accepted 2026-07-13).

The v6ab cases predate the public-census fields, so the screen reconstructs cast_role_counts and the
day's dead roster from the game record before replay (the book's roles-alive filter needs them; an
empty census deliberately renders no book — the legacy-replay guard this screen must overcome, not
inherit).

  PYTHONPATH=. poetry run python evaluation/src/replay/decision_screen/tell_book_screen.py \
      --cases 40 --book <book.json> --out evidence/extraction/tell_extraction/outputs/book_screen.json
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from Agents.memory.tell_book import _load as _book_cache  # noqa: E402
from Agents.schemas.evaluation import EvalCase  # noqa: E402
from evaluation.src.loop.decision_scoring import (  # noqa: E402
    allow_abstain_for, score_vote, wolf_vote_is_good,
)
from evaluation.src.loop.tells import load_games  # noqa: E402
from evaluation.src.replay.decision_screen.replay import _replay_vote  # noqa: E402

DECEIVERS = {"wolf", "serial_killer"}


def _dead_roster_before(g: dict, day: int) -> list[dict]:
    """Public dead roster entering `day`, rebuilt from the record (night k deaths + day k lynch are
    dead from day k+1)."""
    dead = []
    for nr in g.get("night_resolutions", []):
        if nr.get("day", 0) < day:
            for p in nr.get("deaths") or []:
                dead.append({"player": p, "role": g["roles"].get(p), "day": nr.get("day")})
    for dr in g.get("day_resolutions", []):
        if dr.get("day", 0) < day and dr.get("voted_player"):
            dead.append({"player": dr["voted_player"], "role": g["roles"].get(dr["voted_player"]),
                         "day": dr.get("day")})
    return dead


def _collect_cases(dumps_glob: str, n: int, seed: int = 20260713) -> list[tuple]:
    pool = []
    for g in load_games(dumps_glob):
        path = g.get("eval_cases_path")
        if not path or not os.path.exists(path):
            continue
        for cl in open(path):
            if not cl.strip():
                continue
            ec = (json.loads(cl).get("output") or {}).get("eval_case") or {}
            if ec.get("action_phase") == "day_vote" and ec.get("agent_vote") and ec.get("day", 0) >= 2:
                pool.append((g, ec))
    return random.Random(seed).sample(pool, min(n, len(pool)))


def _replay_one(g: dict, ec: dict) -> str | None:
    case = EvalCase.model_validate(ec)
    case.private_context.cast_role_counts = dict(Counter(g["roles"].values()))
    case.private_context.dead_roster = _dead_roster_before(g, case.day)
    allow = allow_abstain_for(case.day, g.get("day_resolutions", []))
    votee, _ = _replay_vote(case, [], allow, strategy_points=[])
    return votee


def _score(role: str, votee: str | None, roles: dict) -> bool:
    o = score_vote(votee, roles)
    return wolf_vote_is_good(o) if role in DECEIVERS else o.hit_threat


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dumps", default="batch_results/v6ab_town*.jsonl")
    ap.add_argument("--cases", type=int, default=40)
    ap.add_argument("--book", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    cases = _collect_cases(args.dumps, args.cases)
    print(f"{len(cases)} frozen day-vote decisions; arm A (no book) then arm B (book={args.book})",
          flush=True)

    rows = []
    os.environ.pop("WW_TELL_BOOK", None)
    _book_cache.cache_clear()
    for i, (g, ec) in enumerate(cases):
        rows.append({"i": i, "game_id": g["game_id"][:8], "day": ec["day"],
                     "role": ec["player_role"], "player": ec["player_id"],
                     "original": (ec.get("agent_vote") or {}).get("votee"),
                     "no_book": _replay_one(g, ec)})
        print(f"  A {i + 1}/{len(cases)}", flush=True)

    os.environ["WW_TELL_BOOK"] = args.book
    _book_cache.cache_clear()
    for i, (g, ec) in enumerate(cases):
        rows[i]["book"] = _replay_one(g, ec)
        print(f"  B {i + 1}/{len(cases)}", flush=True)
    os.environ.pop("WW_TELL_BOOK", None)

    scored = []
    for (g, ec), row in zip(cases, rows):
        if row["no_book"] is None or row["book"] is None:
            continue
        row["correct_no_book"] = _score(row["role"], row["no_book"], g["roles"])
        row["correct_book"] = _score(row["role"], row["book"], g["roles"])
        scored.append(row)
    changed = sum(1 for r in scored if r["no_book"] != r["book"])
    b01 = sum(1 for r in scored if not r["correct_no_book"] and r["correct_book"])
    b10 = sum(1 for r in scored if r["correct_no_book"] and not r["correct_book"])
    summary = {
        "n": len(scored), "changed": changed, "changed_rate": round(changed / len(scored), 3),
        "correct_no_book": sum(r["correct_no_book"] for r in scored),
        "correct_book": sum(r["correct_book"] for r in scored),
        "mcnemar_b01_wrong_to_right": b01, "mcnemar_b10_right_to_wrong": b10,
        "book": args.book, "dumps": args.dumps, "epoch_note": "replayed decisions are v6ab (old epoch)",
    }
    print(json.dumps(summary, indent=1))
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps({"summary": summary, "rows": rows}, indent=1))
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
