"""Smoke test: can flash-lite reliably judge novelty (already_said/borderline/new)?

The Phase-0 proactive path + seeding + redundancy-collapse all depend on the
novelty gate (Rule 1: is a contribution new vs the transcript). We validated
speech-act fields already; this validates the OTHER load-bearing LLM mechanism.

v2 (after a confounded first run): the gate's job is "does this add anything NEW", not "is this
text present", so a long multi-point message that restates X but adds angle Y is correctly "new".
We therefore test the two error directions with candidates GENERATED to a clean ground truth,
conditioned on the real transcript:
  - PURE RESTATEMENT -> must be already_said. Catches the redundancy-suppression the gate exists
    for (agent B about to repeat A). A "new" label here = redundancy LEAKS (false-new).
  - GENUINELY NEW point -> must be new. Catches over-suppression. An "already_said" label here =
    the gate silences a legit contribution (false-already_said).

Judgments run at temp 0 (capability ceiling); production folds this into the situation
summary at game temp, so real-world reliability is <= what we measure here.
"""

from __future__ import annotations

import json
import os
from collections import Counter
from enum import Enum
from pathlib import Path

os.environ.setdefault("LLM_BACKEND", "vertex")
os.environ.setdefault("GOOGLE_GENAI_MODEL", "gemini-3.1-flash-lite")
os.environ["GOOGLE_GENAI_TEMPERATURE"] = "0.0"

from pydantic import BaseModel  # noqa: E402
from langchain_core.prompts import ChatPromptTemplate  # noqa: E402

from Agents.agents import get_llm  # noqa: E402

DATASET = Path("evidence/memory_system/strategy_adoption/eval_sets/phase1_adoption_v2.jsonl")
N_CASES = int(os.getenv("N_CASES", "20"))
OUT = Path("evidence/sequential_discussion/data/smoke_novelty_results.jsonl")


class NoveltyLabel(str, Enum):
    already_said = "already_said"
    borderline = "borderline"
    new = "new"


class NoveltyJudgment(BaseModel):
    label: NoveltyLabel
    reason: str


NOVELTY_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You judge whether a player's intended contribution to a Werewolf day "
     "discussion adds anything NOT already present in the discussion so far. "
     "Compare the candidate ONLY against the discussion so far.\n"
     "- already_said: the substantive point is already present (even if reworded); adds nothing new.\n"
     "- borderline: mostly overlaps, only a marginal new angle.\n"
     "- new: introduces a genuinely new observation, suspicion, or reasoning not yet present.\n"
     "Give the label and a one-sentence reason."),
    ("human", "Discussion so far:\n{transcript}\n\nA player is about to say:\n\"{candidate}\""),
])

RESTATE_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are a Werewolf player. Read the discussion so far. Write ONE short message that simply "
     "AGREES with and restates a point ALREADY MADE by someone — add NO new information, NO new "
     "suspicion, NO new analytical angle. Pure rephrasing of an existing point. Return ONLY the message."),
    ("human", "Discussion so far:\n{transcript}"),
])

NEW_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are a Werewolf player. Read the discussion so far. Write ONE short message that introduces "
     "a GENUINELY NEW suspicion or observation, with reasoning that is NOT already present anywhere "
     "in the discussion (a new target, a new pattern, or a new claim). Return ONLY the message."),
    ("human", "Discussion so far:\n{transcript}"),
])


def text_of(resp) -> str:
    c = getattr(resp, "content", resp)
    if isinstance(c, str):
        return c.strip()
    if isinstance(c, list):
        return "".join(b.get("text", "") if isinstance(b, dict) else str(b) for b in c).strip()
    return str(c).strip()


def fmt(msgs: list[dict]) -> str:
    return "\n".join(f"{m['player']}: {m['message']}" for m in msgs) or "(nothing yet)"


def load_cases() -> list[dict]:
    out = []
    with DATASET.open() as f:
        for line in f:
            raw = json.loads(line).get("eval_case", {})
            if raw.get("action_phase") != "day_discussion":
                continue
            vd = [m for m in raw.get("visible_discussion", []) if m.get("player") != "game_master"]
            if len(vd) < 5:
                continue
            out.append({"id": raw.get("observation_id", ""), "vd": vd})
            if len(out) >= N_CASES:
                break
    return out


def main() -> None:
    cases = load_cases()
    print(f"Loaded {len(cases)} cases (>=5 non-gm messages).", flush=True)
    llm = get_llm()
    judge = NOVELTY_PROMPT | llm.with_structured_output(NoveltyJudgment)
    gen_restate = RESTATE_PROMPT | llm
    gen_new = NEW_PROMPT | llm

    rows = []
    for i, c in enumerate(cases):
        transcript = fmt(c["vd"])
        try:
            restate = text_of(gen_restate.invoke({"transcript": transcript}))
            newcand = text_of(gen_new.invoke({"transcript": transcript}))
        except Exception as e:  # noqa: BLE001
            print(f"  gen failed case {i}: {e}")
            continue

        probes = {
            "pure_restatement": (restate, "already_said"),
            "genuinely_new": (newcand, "new"),
        }
        for probe, (candidate, gt) in probes.items():
            row = {"i": i, "case_id": c["id"], "probe": probe, "gt": gt, "candidate": candidate}
            try:
                res = judge.invoke({"transcript": transcript, "candidate": candidate})
                row["label"] = res.label.value
                row["reason"] = res.reason
            except Exception as e:  # noqa: BLE001
                row["error"] = f"{type(e).__name__}: {e}"[:200]
            rows.append(row)
        if (i + 1) % 5 == 0:
            print(f"  ...{i + 1}/{len(cases)} done", flush=True)

    OUT.write_text("\n".join(json.dumps(r) for r in rows) + "\n")

    def dist(probe):
        return dict(Counter(r.get("label", "ERR") for r in rows if r["probe"] == probe))

    print("\n=== LABEL DISTRIBUTION by probe ===")
    for p in ("pure_restatement", "genuinely_new"):
        print(f"  {p:18s}: {dist(p)}")

    rs = [r for r in rows if r["probe"] == "pure_restatement" and "label" in r]
    rs_caught = sum(1 for r in rs if r["label"] in ("already_said", "borderline"))
    rs_strict = sum(1 for r in rs if r["label"] == "already_said")
    print(f"\n  PURE RESTATEMENT -> already_said (redundancy caught):")
    print(f"    strict already_said={rs_strict}/{len(rs)} ({100*rs_strict/max(len(rs),1):.0f}%); "
          f"incl. borderline={rs_caught}/{len(rs)} ({100*rs_caught/max(len(rs),1):.0f}%)")
    print(f"    *** false-new (redundancy LEAKS) = {len(rs)-rs_caught}/{len(rs)} ***")

    nw = [r for r in rows if r["probe"] == "genuinely_new" and "label" in r]
    nw_ok = sum(1 for r in nw if r["label"] in ("new", "borderline"))
    nw_strict = sum(1 for r in nw if r["label"] == "new")
    print(f"\n  GENUINELY NEW -> new (not over-suppressed):")
    print(f"    strict new={nw_strict}/{len(nw)} ({100*nw_strict/max(len(nw),1):.0f}%); "
          f"incl. borderline={nw_ok}/{len(nw)} ({100*nw_ok/max(len(nw),1):.0f}%)")
    print(f"    *** false-already_said (over-suppress) = {len(nw)-nw_ok}/{len(nw)} ***")
    print(f"\nWrote rows -> {OUT}")


if __name__ == "__main__":
    main()
