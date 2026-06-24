"""Natural stance/form distribution of REAL day-discussion messages (stratified).

The self-emit smoke (smoke_act_2d) ran on the first-24 cases — all endgame, so
stance collapsed to 100% accusation. That risks: (a) `stance` is dead weight,
(b) tier-1 floods if everything is an accusation. This test checks whether that
is a SAMPLING artifact or the real game distribution.

Method: stratified sample across `round` (within-day depth) of the dataset's
stored REAL `agent_message`s, then label each with the 2-D judge (form x stance)
given the prior discussion. Reports the joint distribution + a readable dump.

Run with the poetry venv python (Vertex flash-lite, temp 0 for stable labels).
"""

from __future__ import annotations

import json
import os
import re
import textwrap
from collections import Counter, defaultdict
from enum import Enum
from pathlib import Path

os.environ.setdefault("LLM_BACKEND", "vertex")
os.environ.setdefault("GOOGLE_GENAI_MODEL", "gemini-3.1-flash-lite")
os.environ.setdefault("GOOGLE_GENAI_TEMPERATURE", "0")

from pydantic import BaseModel, Field  # noqa: E402
from langchain_core.prompts import ChatPromptTemplate  # noqa: E402

from Agents.agents import get_llm  # noqa: E402

DATASET = Path("evidence/memory_system/strategy_adoption/eval_sets/phase1_adoption_v2.jsonl")
PER_ROUND = int(os.getenv("PER_ROUND", "10"))
OUT = Path("evidence/agent_speaking/smoke_act_2d_distribution_results.jsonl")
PLAYER_RE = re.compile(r"[Pp]layer\s*_?(\d+)")


class AddressForm(str, Enum):
    question = "question"
    response = "response"
    mention = "mention"


class Stance(str, Enum):
    accusation = "accusation"
    defense = "defense"
    agreement = "agreement"
    neutral = "neutral"


class AddressedTarget2D(BaseModel):
    target: str = Field(description="player ID being addressed")
    address_form: AddressForm = Field(
        description="question = demands a response from them; response = answers something they said "
                    "earlier; mention = refers to them without demanding a reply")
    stance: Stance = Field(
        description="valence toward them: accusation (casts suspicion), defense (defends them or "
                    "self against them), agreement (endorses/sides with them), neutral (none)")


class ActLabels(BaseModel):
    addressed: list[AddressedTarget2D] = Field(
        description="Every player the message engages; empty list if none.")


JUDGE = ChatPromptTemplate.from_messages([
    ("system",
     "You label a Werewolf day-discussion message. Given the discussion so far and the new message, "
     "list every OTHER player it engages, and for each give the address_form and stance. "
     "Do not invent players not referenced by the message. Empty list if it engages no one specific."),
    ("human", "Discussion so far:\n{transcript}\n\nNew message by {speaker}:\n\"{message}\""),
])


def fmt(vd):
    rows = [f"{m['player']}: {m['message']}" for m in vd if m.get("player") != "game_master"]
    return "\n".join(rows) or "(start of day — nothing said yet)"


def load_stratified():
    by_round = defaultdict(list)
    for line in DATASET.open():
        c = json.loads(line).get("eval_case", {})
        if c.get("action_phase") != "day_discussion":
            continue
        am = c.get("agent_message") or {}
        if not am.get("message"):
            continue
        by_round[c.get("round")].append(c)
    sample = []
    for rnd in sorted(by_round):
        # spread across the round's cases rather than taking the head cluster
        cs = by_round[rnd]
        step = max(1, len(cs) // PER_ROUND)
        sample += [(rnd, cs[i]) for i in range(0, len(cs), step)][:PER_ROUND]
    return sample


def main():
    sample = load_stratified()
    print(f"Sampled {len(sample)} real messages across rounds.", flush=True)
    judge = JUDGE | get_llm().with_structured_output(ActLabels)
    rows = []
    for i, (rnd, c) in enumerate(sample):
        am = c["agent_message"]
        inp = {"transcript": fmt(c.get("visible_discussion", [])),
               "speaker": am["player"], "message": am["message"]}
        row = {"i": i, "round": rnd, "day": c.get("day"), "role": c.get("player_role"),
               "speaker": am["player"], "message": am["message"]}
        try:
            res = judge.invoke(inp)
            row["addressed"] = [{"target": a.target, "form": a.address_form.value,
                                 "stance": a.stance.value} for a in res.addressed]
        except Exception as e:  # noqa: BLE001
            row["error"] = f"{type(e).__name__}: {e}"[:200]
        rows.append(row)
        if (i + 1) % 10 == 0:
            print(f"  ...{i+1}/{len(sample)}", flush=True)

    OUT.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    targets = [a for r in rows for a in r.get("addressed", [])]
    print(f"\n=== {len(targets)} addressed targets over {len(rows)} messages ===")
    print("  form dist:  ", dict(Counter(a["form"] for a in targets)))
    print("  stance dist:", dict(Counter(a["stance"] for a in targets)))
    print("  JOINT:")
    for k, v in Counter((a["form"], a["stance"]) for a in targets).most_common():
        print(f"    {k[0]:9s} x {k[1]:11s}: {v}")
    print("\n  per-round stance:")
    for rnd in sorted(set(r["round"] for r in rows)):
        sub = [a for r in rows if r["round"] == rnd for a in r.get("addressed", [])]
        print(f"    round {rnd}: {dict(Counter(a['stance'] for a in sub))}")
    # readable dump of non-accusation cases (the ones we care about)
    print("\n=== non-accusation / non-question examples ===")
    shown = 0
    for r in rows:
        na = [a for a in r.get("addressed", []) if a["stance"] != "accusation" or a["form"] != "question"]
        if na and shown < 12:
            shown += 1
            print(f"\n[r{r['round']} {r['role']} {r['speaker']}] {textwrap.shorten(r['message'],150)}")
            for a in na:
                print(f"   -> {a['target']:10s} {a['form']}/{a['stance']}")
    print(f"\nWrote rows -> {OUT}")


if __name__ == "__main__":
    main()
