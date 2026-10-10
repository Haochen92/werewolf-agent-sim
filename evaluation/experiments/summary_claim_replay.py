"""Replay the day summaries that went wrong in the Phase 3 games, without playing new games.

Each case is one day of one captured game (evidence/game_play_enhancement/data/phase3_*): the
summariser is handed exactly what production handed it that day (the day's lines, the earlier
summaries, the dead roster, the cast and lineup, the earlier days' spoken claims) and run ``n``
times. The checks are on the structured output and the ledger built from it, so they are field
checks, not readings of prose:

- invented_claim: the summary credits a role to a player who claimed none that day (e06 day 2,
  "I was roleblocked" became a chanteuse claim).
- self_action: the summary credits a player with an action on themselves that can only have been
  done to them (a block, watch, follow, check, sigil, attack or conceal on oneself).
- record_check: an accusation's record check says "no attack on X was ever announced" when the
  record shows an attack on X (the copied example).
- control: a true claim the speaker made by describing its action without setting its claim field;
  the summary and the ledger must keep it.

The arm is the checkout: ``--tree`` points at a worktree (the committed code) or the main checkout
(the working tree), and that tree's Agents package is imported, so each arm runs its own prompt,
schema and ledger. One process per arm.

  poetry run python evaluation/experiments/summary_claim_replay.py --tree <checkout> --arm <name> --n 5
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

MAIN = Path(__file__).resolve().parents[2]
DATA = MAIN / "evidence/game_play_enhancement/data"
OUT_DIR = DATA / "phase3_summary_replay"

# The cases, by hand from the reads and the scan of all 31 games (phase3_reads/README.md).
CASES = [
    {"game": "phase3_balance_4/e06", "day": 2, "kind": "invented_claim", "player": "player_2"},
    {"game": "phase3_balance_3/d06", "day": 3, "kind": "self_action", "player": "player_3"},
    {"game": "phase3_balance_4/e01", "day": 3, "kind": "self_action", "player": "player_2"},
    {"game": "phase3_balance/b02", "day": 2, "kind": "record_check", "player": "player_6"},
    {"game": "phase3_balance/b09", "day": 2, "kind": "record_check", "player": "player_1"},
    {"game": "phase3_balance_2/c03", "day": 2, "kind": "record_check", "player": "player_6"},
    {"game": "phase3_balance_4/e02", "day": 3, "kind": "control", "player": "player_9"},
    {"game": "phase3_balance_4/e03", "day": 2, "kind": "control", "player": "player_4"},
    {"game": "phase3_balance_4/e05", "day": 2, "kind": "control", "player": "player_2"},
    {"game": "phase3_balance_4/e06", "day": 3, "kind": "control", "player": "player_5"},
]

_ACTED_ON = r"(blocked|watched|followed|checked|set a sigil on|attacked|shot|concealed)"


def _inputs(record: dict, day: int):
    """What production handed the summariser on ``day``, rebuilt from the record."""
    from Agents.schemas.roles import cast_role_counts
    from Agents.schemas.game_events import DayChannel, DaySummary, DeathRecord

    roles = record["roles"]
    concealed = set()
    for m in record["day_channel"]:
        if m["player"] == "game_master":
            concealed |= set(re.findall(r"(player_\d+) was [^.]*? last night\. Their role is hidden", m["message"]))
    dead = []
    for n in record["night_resolutions"]:
        if n["day"] < day:
            for p in n["deaths"]:
                dead.append(DeathRecord(player=p, role="" if p in concealed else roles[p], day=n["day"],
                                        phase="night", concealed=p in concealed))
    for d in record["day_resolutions"]:
        if d["day"] < day and d.get("voted_player"):
            p = d["voted_player"]
            dead.append(DeathRecord(player=p, role=roles[p], day=d["day"], phase="day"))
    channel = [DayChannel.model_validate(m) for m in record["day_channel"]]
    today = [m for m in channel if m.day == day and m.player != "game_master"]
    earlier = [m for m in channel if m.day < day]
    summaries = [DaySummary.model_validate(s) for s in record["day_summaries"] if s["day"] < day]
    return today, summaries, dead, cast_role_counts(roles), record["lineup"], earlier


def _check(case: dict, record: dict, structured: dict, ledger: str) -> dict:
    p = case["player"]
    roles = record["roles"]
    claims = [c for c in structured.get("role_claims", []) if c.get("player") == p]
    section = re.search(rf"^{p}: .*?(?=^\S|\Z)", ledger, flags=re.M | re.S)
    section = section.group(0) if section else ""
    if case["kind"] == "invented_claim":
        summary_bad = any(c.get("kind", "claimed") == "claimed" for c in claims)
        ledger_bad = section.startswith(f"{p}: claimed")
    elif case["kind"] == "self_action":
        summary_bad = any(a.get("target") == p and a.get("action") in
                          ("block", "watch", "follow", "investigate", "sigil", "kill", "shoot", "conceal")
                          for c in claims for a in c.get("night_actions", []))
        ledger_bad = bool(re.search(rf": {_ACTED_ON} {p}\b", section))
    elif case["kind"] == "record_check":
        checks = [a.get("record_check") or "" for a in structured.get("accusations", [])]
        summary_bad = any(re.search(rf"no attack on {p}\b", rc) for rc in checks)
        ledger_bad = summary_bad  # the record check is the summary's own text, shown beside the ledger
    else:  # control: the true role, by the summary and by the ledger
        role = roles[p]
        summary_bad = not any(c.get("claimed_role") == role for c in claims)
        ledger_bad = f"{p}: claimed {role.replace('_', ' ')}" not in ledger
    return {"summary_bad": summary_bad, "ledger_bad": ledger_bad}


def _one(case: dict, sample: int) -> dict:
    from Agents.nodes.day.summary_agent import run_day_summary_agent
    from Agents.rules.claim_ledger import format_claim_ledger
    from Agents.schemas.game_events import DaySummary

    record = json.load(open(DATA / f"{case['game']}.record.json"))
    today, summaries, dead, cast, lineup, earlier = _inputs(record, case["day"])
    text, model, structured = run_day_summary_agent(
        case["day"], today, 1, day_summaries=summaries, dead_roster=dead,
        cast_role_counts=cast, lineup=lineup, earlier_messages=earlier)
    stored = DaySummary(day=case["day"], summary=text, structured=structured)
    ledger = format_claim_ledger([*summaries, stored], dead, cast, [*earlier, *today])
    return {**case, "sample": sample, "model": model, "ok": bool(structured), "structured": structured,
            "ledger": ledger, **(_check(case, record, structured, ledger) if structured else {})}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tree", required=True, help="the checkout whose Agents package this arm runs")
    ap.add_argument("--arm", required=True)
    ap.add_argument("--n", type=int, default=5)
    ap.add_argument("--workers", type=int, default=6)
    args = ap.parse_args()
    from dotenv import load_dotenv
    load_dotenv(MAIN / ".env")
    sys.path.insert(0, str(Path(args.tree).resolve()))
    import Agents
    assert Path(Agents.__file__).resolve().is_relative_to(Path(args.tree).resolve()), Agents.__file__

    jobs = [(c, i) for c in CASES for i in range(args.n)]
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        rows = list(ex.map(lambda job: _one(*job), jobs))
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"generations_{args.arm}.jsonl"
    out.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    print(f"{args.arm}: {len(rows)} samples -> {out}")


if __name__ == "__main__":
    main()
