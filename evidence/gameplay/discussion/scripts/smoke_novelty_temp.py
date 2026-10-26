"""Temp 0 vs temp 1.0 for the novelty gate.

Decides whether the (folded-into-situation-summary) novelty labels should run at low temp.
Holds candidates FIXED (generated once at temp 0), then judges each at temp 0 (1 sample) and
temp 1.0 (k=3 samples) to measure both accuracy AND label instability (flips across samples).

Probes (clean generated GT, same as smoke_novelty v2):
  pure_restatement -> already_said ;  genuinely_new -> new
"""

from __future__ import annotations

import json
import os
from collections import Counter
from pathlib import Path

os.environ.setdefault("LLM_BACKEND", "vertex")
os.environ.setdefault("GOOGLE_GENAI_MODEL", "gemini-3.1-flash-lite")

from pydantic import BaseModel  # noqa: E402
from enum import Enum  # noqa: E402
from langchain_core.prompts import ChatPromptTemplate  # noqa: E402

from Agents.agents import get_llm  # noqa: E402

DATASET = Path("evidence/memory_system/strategy_adoption/eval_sets/phase1_adoption_v2.jsonl")
N_CASES = int(os.getenv("N_CASES", "20"))
K_T1 = 3
OUT = Path("evidence/sequential_discussion/data/smoke_novelty_temp_results.jsonl")


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


def fmt(msgs):
    return "\n".join(f"{m['player']}: {m['message']}" for m in msgs) or "(nothing yet)"


def load_cases():
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


def build(temp, structured=False):
    os.environ["GOOGLE_GENAI_TEMPERATURE"] = str(temp)
    llm = get_llm()
    if structured:
        return NOVELTY_PROMPT | llm.with_structured_output(NoveltyJudgment)
    return llm


def main():
    cases = load_cases()
    print(f"Loaded {len(cases)} cases.", flush=True)
    # candidates generated deterministically at temp 0
    gen_restate = RESTATE_PROMPT | build(0.0)
    gen_new = NEW_PROMPT | build(0.0)
    judge_t0 = build(0.0, structured=True)
    judge_t1 = build(1.0, structured=True)

    rows = []
    for i, c in enumerate(cases):
        transcript = fmt(c["vd"])
        try:
            cands = {
                "pure_restatement": (text_of(gen_restate.invoke({"transcript": transcript})), "already_said"),
                "genuinely_new": (text_of(gen_new.invoke({"transcript": transcript})), "new"),
            }
        except Exception as e:  # noqa: BLE001
            print(f"  gen failed {i}: {e}")
            continue
        for probe, (cand, gt) in cands.items():
            inp = {"transcript": transcript, "candidate": cand}
            row = {"i": i, "probe": probe, "gt": gt, "candidate": cand}
            try:
                row["t0"] = judge_t0.invoke(inp).label.value
            except Exception as e:  # noqa: BLE001
                row["t0"] = f"ERR:{type(e).__name__}"
            t1 = []
            for _ in range(K_T1):
                try:
                    t1.append(judge_t1.invoke(inp).label.value)
                except Exception as e:  # noqa: BLE001
                    t1.append(f"ERR:{type(e).__name__}")
            row["t1_samples"] = t1
            rows.append(row)
        if (i + 1) % 5 == 0:
            print(f"  ...{i+1}/{len(cases)}", flush=True)

    OUT.write_text("\n".join(json.dumps(r) for r in rows) + "\n")

    def correct(label, gt):
        return label == gt or label == "borderline"

    print("\n=== TEMP 0 vs TEMP 1.0 (k=3) ===")
    for probe in ("pure_restatement", "genuinely_new"):
        sub = [r for r in rows if r["probe"] == probe]
        n = len(sub)
        t0_ok = sum(1 for r in sub if correct(r["t0"], r["gt"]))
        # temp1: majority vote per candidate + instability
        maj_ok = 0
        flips = 0
        all_samples = []
        for r in sub:
            s = r["t1_samples"]
            all_samples += s
            if len(set(s)) > 1:
                flips += 1
            maj = Counter(s).most_common(1)[0][0]
            if correct(maj, r["gt"]):
                maj_ok += 1
        sample_ok = sum(1 for r in sub for s in r["t1_samples"] if correct(s, r["gt"]))
        print(f"\n  {probe} (GT={sub[0]['gt']}, n={n}):")
        print(f"    temp0 correct (incl borderline): {t0_ok}/{n} ({100*t0_ok/max(n,1):.0f}%)")
        print(f"    temp1 majority-correct:          {maj_ok}/{n} ({100*maj_ok/max(n,1):.0f}%)")
        print(f"    temp1 per-sample correct:        {sample_ok}/{n*K_T1} ({100*sample_ok/max(n*K_T1,1):.0f}%)")
        print(f"    temp1 unstable (non-unanimous):  {flips}/{n} ({100*flips/max(n,1):.0f}%)")
        print(f"    temp0 label dist: {dict(Counter(r['t0'] for r in sub))}")
        print(f"    temp1 label dist: {dict(Counter(all_samples))}")
    print(f"\nWrote rows -> {OUT}")


if __name__ == "__main__":
    main()
