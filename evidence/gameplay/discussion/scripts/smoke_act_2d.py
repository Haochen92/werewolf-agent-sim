"""Smoke test (follow-up to smoke_act_fields): 2-DIMENSION speech-act fields.

Motivation: the 1-D `act` enum (question/accusation/reference/agreement) was
under-determined — inspection of smoke_act_results showed nearly every utterance
is BOTH a question (by form) AND an accusation (by stance), so the single label
coin-flips. This tests decoupling into two orthogonal axes:

  address_form : question | response | mention   (does it demand a response?)
  stance       : accusation | defense | agreement | neutral  (valence toward target)

Measures: structured-output validity, target grounding (reuse), the JOINT
(form, stance) distribution, and rough content-consistency flags for eyeballing
accuracy (not just granularity).

Run with the poetry venv python (Vertex flash-lite, production temp 1.0).
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from collections import Counter
from enum import Enum
from pathlib import Path

os.environ.setdefault("LLM_BACKEND", "vertex")
os.environ.setdefault("GOOGLE_GENAI_MODEL", "gemini-3.1-flash-lite")
os.environ.setdefault("GOOGLE_GENAI_TEMPERATURE", "1.0")

from pydantic import BaseModel, Field  # noqa: E402

from Agents.agents import _build_agent_prompt_input, get_llm  # noqa: E402
from Agents.schemas.evaluation import EvalCase  # noqa: E402
from Agents.schemas.output import DayDiscussOutput  # noqa: E402
from evaluation.components.application import action_spec_for  # noqa: E402
from evaluation.components.situation_summary import eval_case_to_agent_payload  # noqa: E402

DATASET = Path("evidence/memory_system/strategy_adoption/eval_sets/phase1_adoption_v2.jsonl")
N_CASES = int(os.getenv("N_CASES", "24"))
OUT = Path("evidence/sequential_discussion/data/smoke_act_2d_results.jsonl")

PLAYER_RE = re.compile(r"[Pp]layer\s*_?(\d+)")
ACCUSE_KW = ("suspicious", "suspicion", "deflect", "dodg", "evasive", "avoid",
             "lying", " lie", "wolf would", "deflection", "shift", "bury", "stifle",
             "obfuscat", "minimiz")


class AddressForm(str, Enum):
    question = "question"   # demands a response from the target
    response = "response"   # answers a question/accusation the target made earlier
    mention = "mention"     # refers to the target without demanding a reply


class Stance(str, Enum):
    accusation = "accusation"  # casts suspicion on the target
    defense = "defense"        # defends the target (or self against target)
    agreement = "agreement"    # endorses/sides with the target
    neutral = "neutral"        # no valence


class AddressedTarget2D(BaseModel):
    target: str = Field(description="player ID or name being addressed")
    address_form: AddressForm = Field(
        description="question = you demand a response from them; response = you are answering "
                    "something they said earlier; mention = you refer to them without demanding a reply")
    stance: Stance = Field(
        description="your valence toward this target: accusation, defense, agreement, or neutral")


class DayDiscuss2D(DayDiscussOutput):
    addressed: list[AddressedTarget2D] = Field(
        description="Every player engaged by this message; empty list if none.")


def regex_players(text: str) -> set[str]:
    return {f"player_{n}" for n in PLAYER_RE.findall(text or "")}


def load_cases() -> list[EvalCase]:
    cases: list[EvalCase] = []
    with DATASET.open() as f:
        for line in f:
            obj = json.loads(line)
            raw = obj.get("eval_case", obj)
            if raw.get("action_phase") != "day_discussion":
                continue
            if len(raw.get("visible_discussion", [])) < 2:
                continue
            cases.append(EvalCase.model_validate(raw))
            if len(cases) >= N_CASES:
                break
    return cases


def run_one(case: EvalCase):
    payload = eval_case_to_agent_payload(case)
    spec = action_spec_for(case)
    chain = spec.prompt_template | get_llm().with_structured_output(DayDiscuss2D)
    return chain.invoke(_build_agent_prompt_input(payload))


def main() -> None:
    cases = load_cases()
    print(f"Loaded {len(cases)} day_discussion cases.", flush=True)
    rows, valid = [], 0
    for i, case in enumerate(cases):
        row = {"i": i, "role": case.player_role, "valid": False}
        try:
            res = run_one(case)
            row["valid"] = True
            valid += 1
            msg = getattr(res, "message", None) or ""
            row["message"] = msg
            rx = regex_players(msg)
            addr = getattr(res, "addressed", []) or []
            row["addressed"] = [
                {"target": a.target, "form": a.address_form.value, "stance": a.stance.value}
                for a in addr
            ]
            norm = set()
            for a in addr:
                norm.update(f"player_{n}" for n in PLAYER_RE.findall(a.target))
            row["target_not_in_message"] = sorted(norm - rx)
            # rough content-consistency flags
            t = msg.lower()
            flags = []
            for a in row["addressed"]:
                if a["form"] == "question" and "?" not in msg:
                    flags.append(f"{a['target']}:question-but-no-?")
                if a["stance"] == "neutral" and any(k in t for k in ACCUSE_KW):
                    flags.append(f"{a['target']}:neutral-but-accuse-kw")
            row["flags"] = flags
        except Exception as e:  # noqa: BLE001
            row["error"] = f"{type(e).__name__}: {e}"[:300]
        rows.append(row)
        time.sleep(0.3)
        if (i + 1) % 5 == 0:
            print(f"  ...{i + 1}/{len(cases)}", flush=True)

    OUT.write_text("\n".join(json.dumps(r) for r in rows) + "\n")

    ok = [r for r in rows if r["valid"]]
    print(f"\n=== VALIDITY === {valid}/{len(rows)} ({100*valid/max(len(rows),1):.0f}%)")
    targets = [a for r in ok for a in r["addressed"]]
    print(f"\n=== {len(targets)} addressed targets ===")
    print("  form dist:  ", dict(Counter(a["form"] for a in targets)))
    print("  stance dist:", dict(Counter(a["stance"] for a in targets)))
    print("  JOINT (form, stance):")
    for k, v in Counter((a["form"], a["stance"]) for a in targets).most_common():
        print(f"    {k[0]:9s} x {k[1]:10s}: {v}")
    not_in = sum(len(r.get("target_not_in_message", [])) for r in ok)
    print(f"\n  targets NOT in own message (hallucination?): {not_in}")
    flagged = [r for r in ok if r.get("flags")]
    print(f"  rows with content-consistency flags: {len(flagged)}/{len(ok)}")
    for r in flagged:
        print(f"    case {r['i']}: {r['flags']}")
    print(f"\nWrote rows -> {OUT}")


if __name__ == "__main__":
    sys.exit(main())
