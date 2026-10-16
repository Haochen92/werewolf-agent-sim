"""Day summaries on Haiku 5.5 (live) against Sonnet 5.5: which records the day more faithfully?

Record: evidence/reasoning_failures/experiment_log.md. Owner, 2026-10-16: Sonnet is too
dear for player turns, but the summary is one call a day, so it may run on Sonnet if it judges better.
Game 2f19d908's day-3 summary is the case that raised it: its record_check said the record was
"consistent with" an argument that misread the rules.

Every day with a spoken line in the two Haiku games (403f4dbc, 2f19d908) is re-summarised from its
own checkpoint, the state the summary node held: that day's whole discussion, the game master's
record and the earlier days' summaries as played, so each day is tested on the same context in both
arms. The live summary is kept beside them as a third, unsampled arm. Every summary is judged by
Claude Sonnet 5.5 in one Message Batch, against the day's transcript and the record, for the errors
that would mislead a player who reads the summary instead of the day: misattributed or invented
statements, claims left out, rebuttals dropped or withdrawn accusations kept, a claim written as
fact, and a record_check that is not a conflict with the record.

  poetry run python evaluation/experiments/haiku_summary_compare.py generate [--n 5]
  poetry run python evaluation/experiments/haiku_summary_compare.py judge
  poetry run python evaluation/experiments/haiku_summary_compare.py report
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import evaluation.experiments.haiku_game_turn_cases as turns  # noqa: E402

GAMES = ["403f4dbc-4a16-45fc-bb22-1c5e67bd5936", "2f19d908-a6b3-4faf-8f16-c2a009bb0428"]
ARMS = {"haiku": "anthropic/claude-haiku-5-5", "sonnet": "anthropic/claude-sonnet-5-5"}
JUDGE = "claude-sonnet-5-5"
OUT = Path("evidence/reasoning_failures/data/haiku_summary_compare")


# --- the days -------------------------------------------------------------------------------

def summary_inputs() -> list[dict]:
    """One entry per (game, day) with a spoken line: the arguments the live summary node passed."""
    days = []
    for game in GAMES:
        states = turns.day_states(game)
        for day in sorted({s["current_day"] for s in states if s.get("current_day")}):
            today = [s for s in states if s.get("current_day") == day and s.get("surviving_villagers")]
            if not today:
                continue
            longest = max(len([m for m in s["day_channel"] if m["day"] == day]) for s in today)
            done = [s for s in today if len([m for m in s["day_channel"] if m["day"] == day]) == longest]
            before = [s for s in done if not any(x["day"] == day and x.get("source") == "discussion"
                                                 for x in s.get("day_summaries", []))]
            after = [s for s in done if s not in before]
            if not before:
                continue
            state = before[0]
            spoken = [m for m in state["day_channel"] if m["day"] == day and m["player"] != "game_master"]
            if not any(not m.get("passed") for m in spoken):
                continue
            live = next((x for s in after for x in s["day_summaries"]
                         if x["day"] == day and x.get("source") == "discussion"), None)
            days.append({"game": game[:8], "day": day, "state": state, "live": live})
    return days


def _summarise(entry: dict) -> dict:
    from Agents.nodes.day.summary_agent import run_day_summary_agent
    from Agents.schemas.game_events import DayChannel, DaySummary, DeathRecord
    from Agents.schemas.roles import cast_role_counts

    state, day = entry["state"], entry["day"]
    channel = [DayChannel.model_validate(m) for m in state["day_channel"]]
    text, model_used, structured = run_day_summary_agent(
        day, [m for m in channel if m.day == day and m.player != "game_master"], 1,
        day_summaries=[DaySummary.model_validate(s) for s in state.get("day_summaries", [])],
        dead_roster=[DeathRecord.model_validate(d) for d in state.get("dead_roster", [])],
        cast_role_counts=cast_role_counts(state["roles"]),
        lineup=state.get("lineup", []),
        earlier_messages=[m for m in channel if m.day < day],
    )
    return {"text": text, "model_used": model_used, "structured": structured, "valid": bool(model_used)}


def generate(n: int) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    days = summary_inputs()
    path = OUT / "summaries.jsonl"
    rows = []
    for d in days:
        if d["live"]:
            rows.append({"game": d["game"], "day": d["day"], "arm": "live", "sample": 0, "valid": True,
                         "text": d["live"]["summary"], "structured": d["live"].get("structured") or {}})
    for arm, model in ARMS.items():
        # the summary model is read from the env on every call (accessors._game_model)
        os.environ["GOOGLE_GENAI_MODEL"] = model
        jobs = [(d, i) for d in days for i in range(n)]
        print(f"{arm}: {len(jobs)} summaries over {len(days)} days")
        with ThreadPoolExecutor(max_workers=4) as ex:
            for (d, i), out in zip(jobs, ex.map(lambda job: _summarise(job[0]), jobs)):
                rows.append({"game": d["game"], "day": d["day"], "arm": arm, "sample": i, **out})
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    print(f"{len(rows)} summaries -> {path}")


# --- the judge ------------------------------------------------------------------------------

class SummaryError(BaseModel):
    quote: str = Field(description="the part of the summary that is wrong, copied verbatim")
    kind: Literal["misattributed", "invented", "missed_claim", "dropped_rebuttal", "claim_as_fact",
                  "record_check", "other"] = Field(description="the kind of error, as defined in the instructions")
    explanation: str = Field(description="one sentence: what the transcript or the record actually says")


class SummaryVerdict(BaseModel):
    errors: list[SummaryError] = Field(description="every error found; an empty list if there are none")
    verdict: Literal["clean", "flawed"] = Field(description="flawed if errors is not empty, else clean")


RUBRIC = """You check a summary of one day's discussion in a Werewolf game. On later days the players read this summary instead of the discussion, so an error in it misleads them. You get the game master's record (exact public facts), the day's full transcript, and the summary as structured JSON (accusations, and role claims with their claimed night actions).

The summariser's job: transcribe, attributed to the speaker, every accusation with all its accusers, the target's defence and anyone else's rebuttal; and every role claim made today with each claimed night action (night, target, result, who they say they saw). A player who describes doing a role's action ("my visit was protection") is claiming that role. A plan for tonight is a planned action, not a night action. record_check is only for an accusation that rests on a public event the record contradicts, or one the game master would have announced but did not; otherwise it must be empty. Private night results are never announced, so their absence is not a conflict.

Error kinds:
- misattributed: a statement, accusation, claim, night action, target, result or night credited to the wrong player or with the wrong details.
- invented: something nobody said in the transcript.
- missed_claim: a role claim or claimed night action made in today's transcript that is missing from role_claims.
- dropped_rebuttal: an accusation recorded without a defence or rebuttal the transcript contains, or recorded as standing when its accuser withdrew it later in the day.
- claim_as_fact: a player's claim, or the premise of an accusation, written as fact instead of as what a player said.
- record_check: a non-empty record_check that reports no real conflict with the record, states something the record does not say, or reads as the record supporting or refuting a player's argument.
- other: any other error that would mislead a reader.

Flag only errors that would mislead a player reading the summary later. Ignore wording, length, and minor commentary left out. Quote the wrong part, say in one sentence what the transcript or record says, then give the verdict."""


def _day_block(state: dict, day: int) -> str:
    from Agents.prompts.prompt_formatters import format_day_channel
    from Agents.schemas.game_events import DayChannel

    record = "\n".join(f"[Day {s['day']}] {s['summary'].strip()}" for s in state.get("day_summaries", [])
                       if s.get("source") == "game_master") or "Nothing announced yet."
    # The day's lines as the summariser got them: without the moderator's (the closing call named
    # accusers from the tags, and a judge shown it took it as the truth about who accused whom).
    channel = [DayChannel.model_validate(m) for m in state["day_channel"]
               if m["day"] == day and m["player"] != "game_master"]
    return (f"{RUBRIC}\n\n== The game master's record before this day's vote ==\n{record}\n\n"
            f"== Day {day} transcript (entries in order; passes are not shown) ==\n{format_day_channel(channel)}\n\n")


def judge() -> None:
    from Agents.llm_factory.providers.anthropic import batch_parse, parse_with_claude, usage_cost_usd

    rows = [json.loads(line) for line in (OUT / "summaries.jsonl").read_text().splitlines()]
    states = {(d["game"], d["day"]): d["state"] for d in summary_inputs()}
    requests = {}
    for i, r in enumerate(rows):
        if not r["valid"]:
            continue
        prefix = _day_block(states[r["game"], r["day"]], r["day"])
        summary = json.dumps(r["structured"], indent=1) if r["structured"] else r["text"]
        requests[str(i)] = (prefix + f"== The summary to check ==\n{summary}", SummaryVerdict, prefix)
    print(f"judging {len(requests)} summaries on {JUDGE} (one batch)")
    out = batch_parse(requests, JUDGE)
    for k, v in out.items():
        if v is None:
            out[k] = parse_with_claude(requests[k][0], SummaryVerdict, JUDGE, cache_prefix=requests[k][2])[0]
    with open(OUT / "verdicts.jsonl", "w") as f:
        for i, r in enumerate(rows):
            v = out.get(str(i))
            f.write(json.dumps({**{k: r[k] for k in ("game", "day", "arm", "sample")},
                                "verdict": v.model_dump() if v else None}) + "\n")
    print(f"judge cost: ${usage_cost_usd():.2f}")


def report() -> None:
    verdicts = [json.loads(line) for line in (OUT / "verdicts.jsonl").read_text().splitlines()]
    by_arm: dict[str, list[dict]] = defaultdict(list)
    for v in verdicts:
        if v["verdict"]:
            by_arm[v["arm"]].append(v)
    for arm in ("live", *ARMS):
        rows = by_arm.get(arm, [])
        if not rows:
            continue
        flawed = sum(r["verdict"]["verdict"] == "flawed" for r in rows)
        kinds = Counter(e["kind"] for r in rows for e in r["verdict"]["errors"])
        n_err = sum(kinds.values())
        print(f"== {arm}: flawed {flawed}/{len(rows)}, {n_err} errors ({n_err / len(rows):.1f} a summary) "
              f"{dict(kinds.most_common())}")
        per_day = defaultdict(list)
        for r in rows:
            per_day[r["game"], r["day"]].append(r)
        for (game, day), rs in sorted(per_day.items()):
            bad = sum(r["verdict"]["verdict"] == "flawed" for r in rs)
            errs = sum(len(r["verdict"]["errors"]) for r in rs)
            print(f"  {game} day {day}: flawed {bad}/{len(rs)}, {errs} errors")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("step", choices=["generate", "judge", "report"])
    ap.add_argument("--n", type=int, default=5)
    args = ap.parse_args()
    {"generate": lambda: generate(args.n), "judge": judge, "report": report}[args.step]()
