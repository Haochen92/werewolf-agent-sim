"""Throwaway tuning harness for the sequential discussion scheduler.

NOT part of the eval — these are scheduler *mechanical-health* diagnostics (domination,
verbatim dups, response-discharge), separate from ComputedGameMetrics (agent performance).
Run a memory-off game and dump its day_channel, or analyze an existing transcript JSON.

  python scripts/smoke_discussion.py --run --out /tmp/dc.json     # run + dump + analyze
  python scripts/smoke_discussion.py --transcript /tmp/dc.json    # analyze existing
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from itertools import groupby
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]  # …/scripts → …/sequential_discussion → …/evidence → repo root
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

ROLES = ("wolf", "villager", "healer", "investigator")


def _real(messages: list[dict]) -> list[dict]:
    """Player utterances only — drop game_master announcements and pass markers."""
    return [m for m in messages if m.get("player") != "game_master" and not m.get("passed")]


def compute_metrics(day_channel: list[dict]) -> dict:
    by_day: dict[int, list[dict]] = defaultdict(list)
    for m in _real(day_channel):
        by_day[m["day"]].append(m)

    per_day = {}
    for day, msgs in sorted(by_day.items()):
        msgs = sorted(msgs, key=lambda m: m["seq"])
        speakers = [m["player"] for m in msgs]
        max_run = max((len(list(g)) for _, g in groupby(speakers)), default=0)

        # verbatim dups: a message identical to an earlier one by the same player this day
        seen: set[tuple[str, str]] = set()
        dups = 0
        for m in msgs:
            key = (m["player"], m["message"].strip())
            if key in seen:
                dups += 1
            seen.add(key)

        # response-discharge: of reactive turns, did the speaker address an owed creditor
        # with form=="response"? (measures whether agents actually answer who they owe)
        reactive = [m for m in msgs if (m.get("firing_reason") or {}).get("tier") == "reactive"]
        proactive = sum(1 for m in msgs if (m.get("firing_reason") or {}).get("tier") == "proactive")
        discharged = 0
        for m in reactive:
            owed = set((m.get("firing_reason") or {}).get("owes", []))
            responded = {
                t["target"] for t in m.get("addressed_targets", [])
                if t.get("addressed_form") == "response"
            }
            if owed & responded:
                discharged += 1

        per_day[day] = {
            "utterances": len(msgs),
            "reactive": len(reactive),
            "proactive": proactive,
            "max_consecutive_same_speaker": max_run,
            "verbatim_dups": dups,
            "response_discharge_rate": round(discharged / len(reactive), 2) if reactive else None,
        }

    totals = {
        "utterances": sum(d["utterances"] for d in per_day.values()),
        "max_consecutive_same_speaker": max((d["max_consecutive_same_speaker"] for d in per_day.values()), default=0),
        "verbatim_dups": sum(d["verbatim_dups"] for d in per_day.values()),
    }
    return {"per_day": per_day, "totals": totals}


def run_game_and_dump(out_path: Path, memory: bool = False) -> list[dict]:
    from Agents.config import RunConfig
    from Agents.main import run_game

    if memory:
        memory_config = {r: True for r in ROLES}
        mpc = {
            "seed_enabled": True,
            "dump_enabled": False,
            "seed_store_dir": "memory_stores/v4_deduped_v2",  # cached vectors -> no re-embed
        }
    else:
        memory_config = {r: False for r in ROLES}
        mpc = {"seed_enabled": False, "dump_enabled": False}

    outcome = run_game(
        RunConfig(
            memory_config=memory_config,
            session_id="smoke_discussion",
            memory_persistence=mpc,
        )
    )
    day_channel = [
        m.model_dump() if hasattr(m, "model_dump") else m
        for m in outcome.result["day_channel"]
    ]
    out_path.write_text(json.dumps(day_channel, indent=2, default=str), encoding="utf-8")
    print(f"winner={outcome.result.get('winner')} day={outcome.result.get('current_day')} "
          f"-> transcript dumped to {out_path}")
    return day_channel


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--run", action="store_true", help="run a game first")
    p.add_argument("--memory", action="store_true", help="enable memory retrieval + cached seed")
    p.add_argument("--out", type=Path, default=Path("/tmp/smoke_dc.json"))
    p.add_argument("--transcript", type=Path, help="analyze an existing transcript JSON")
    args = p.parse_args()

    if args.transcript:
        day_channel = json.loads(args.transcript.read_text(encoding="utf-8"))
    elif args.run:
        day_channel = run_game_and_dump(args.out, memory=args.memory)
    else:
        p.error("pass --run or --transcript")

    print(json.dumps(compute_metrics(day_channel), indent=2))


if __name__ == "__main__":
    main()
