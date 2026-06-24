"""Smoke test: can flash-lite reliably self-emit speech-act fields?

Decides Point 2 of the sequential-discussion redesign: model-emitted tiered
speech-acts (flat single `act`, or nested `addressed:[{target,act}]`) vs. plain
string matching. Replays the production day_discussion chain on frozen contexts
under 3 output schemas and measures structured-output validity + how the model's
self-report compares to a regex/heuristic baseline.

Run with the poetry venv python (Vertex flash-lite, production temp).
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from enum import Enum
from pathlib import Path

# Pin production backend before importing the LLM factory.
os.environ.setdefault("LLM_BACKEND", "vertex")
os.environ.setdefault("GOOGLE_GENAI_MODEL", "gemini-3.1-flash-lite")
os.environ.setdefault("GOOGLE_GENAI_TEMPERATURE", "1.0")

from pydantic import BaseModel  # noqa: E402

from Agents.agents import _build_agent_prompt_input, get_llm  # noqa: E402
from Agents.schemas.evaluation import EvalCase  # noqa: E402
from Agents.schemas.output import DayDiscussOutput  # noqa: E402
from evaluation.components.application import action_spec_for  # noqa: E402
from evaluation.components.situation_summary import eval_case_to_agent_payload  # noqa: E402

DATASET = Path("evidence/memory_system/strategy_adoption/eval_sets/phase1_adoption_v2.jsonl")
N_CASES = int(os.getenv("N_CASES", "30"))
OUT = Path("evidence/agent_speaking/smoke_act_results.jsonl")

PLAYER_RE = re.compile(r"[Pp]layer\s*_?(\d+)")
ACCUSE_KW = ("suspicious", "suspicion", "deflect", "dodg", "evasive", "avoid",
             "lying", "blatant lie", " lie", "bus-driv", "discord")


class Act(str, Enum):
    question = "question"
    accusation = "accusation"
    reference = "reference"
    agreement = "agreement"
    none = "none"


class AddressedTarget(BaseModel):
    target: str
    act: Act


class DayDiscussFlat(DayDiscussOutput):
    act: Act


class DayDiscussNested(DayDiscussOutput):
    addressed: list[AddressedTarget]


CONDITIONS = {"baseline": DayDiscussOutput, "flat": DayDiscussFlat, "nested": DayDiscussNested}


def regex_players(text: str) -> set[str]:
    return {f"player_{n}" for n in PLAYER_RE.findall(text or "")}


def heuristic_act(text: str, addressed_anyone: bool) -> str:
    t = (text or "").lower()
    if "?" in t and addressed_anyone:
        return "question"
    if any(k in t for k in ACCUSE_KW):
        return "accusation"
    if addressed_anyone:
        return "reference"
    return "none"


def load_cases() -> list[EvalCase]:
    cases: list[EvalCase] = []
    with DATASET.open() as f:
        for line in f:
            obj = json.loads(line)
            raw = obj.get("eval_case", obj)
            if raw.get("action_phase") != "day_discussion":
                continue
            if len(raw.get("visible_discussion", [])) < 2:  # need context to address
                continue
            cases.append(EvalCase.model_validate(raw))
            if len(cases) >= N_CASES:
                break
    return cases


def run_one(case: EvalCase, schema: type[BaseModel]):
    payload = eval_case_to_agent_payload(case)
    spec = action_spec_for(case)
    chain = spec.prompt_template | get_llm().with_structured_output(schema)
    prompt_input = _build_agent_prompt_input(payload)
    return chain.invoke(prompt_input)


def main() -> None:
    cases = load_cases()
    print(f"Loaded {len(cases)} day_discussion cases (visible_discussion >= 2).", flush=True)
    tally = {c: {"valid": 0, "invalid": 0} for c in CONDITIONS}
    rows = []

    for i, case in enumerate(cases):
        for cond, schema in CONDITIONS.items():
            row = {"i": i, "case_id": case.observation_id, "role": case.player_role,
                   "condition": cond, "valid": False}
            try:
                res = run_one(case, schema)
                row["valid"] = True
                tally[cond]["valid"] += 1
                msg = getattr(res, "message", None) or ""
                row["message"] = msg
                rx = regex_players(msg)
                row["regex_players"] = sorted(rx)
                row["heuristic_act"] = heuristic_act(msg, bool(rx))
                if cond == "flat":
                    row["model_act"] = getattr(res, "act", None)
                    if hasattr(res.act, "value"):
                        row["model_act"] = res.act.value
                if cond == "nested":
                    addr = getattr(res, "addressed", []) or []
                    row["addressed"] = [{"target": a.target, "act": a.act.value} for a in addr]
                    model_targets = {a.target.lower().replace(" ", "_") for a in addr}
                    # normalize "Player 3"/"player_3" forms already; recompute via regex on targets
                    norm = set()
                    for a in addr:
                        m = PLAYER_RE.findall(a.target)
                        norm.update(f"player_{n}" for n in m)
                    row["addressed_targets_norm"] = sorted(norm or model_targets)
                    row["target_in_message"] = sorted(norm & rx)
                    row["target_not_in_message"] = sorted(norm - rx)
            except Exception as e:  # noqa: BLE001
                tally[cond]["invalid"] += 1
                row["error"] = f"{type(e).__name__}: {e}"[:300]
            rows.append(row)
            time.sleep(0.3)
        if (i + 1) % 5 == 0:
            print(f"  ...{i + 1}/{len(cases)} cases done", flush=True)

    OUT.write_text("\n".join(json.dumps(r) for r in rows) + "\n")

    print("\n=== VALIDITY (valid / total) ===")
    for cond in CONDITIONS:
        v, iv = tally[cond]["valid"], tally[cond]["invalid"]
        print(f"  {cond:9s}: {v}/{v + iv}  ({100 * v / max(v + iv, 1):.0f}%)")

    # Nested target self-consistency
    nested = [r for r in rows if r["condition"] == "nested" and r["valid"]]
    addr_rows = [r for r in nested if r.get("addressed_targets_norm")]
    in_msg = sum(len(r.get("target_in_message", [])) for r in addr_rows)
    not_in = sum(len(r.get("target_not_in_message", [])) for r in addr_rows)
    print("\n=== NESTED target self-consistency ===")
    print(f"  rows with >=1 addressed target: {len(addr_rows)}/{len(nested)}")
    print(f"  addressed targets present in own message:  {in_msg}")
    print(f"  addressed targets NOT in own message (hallucination?): {not_in}")

    # Flat: model act vs heuristic act
    flat = [r for r in rows if r["condition"] == "flat" and r["valid"] and r.get("model_act")]
    agree = sum(1 for r in flat if r["model_act"] == r["heuristic_act"])
    print("\n=== FLAT model act vs '?'/keyword heuristic ===")
    print(f"  agreement: {agree}/{len(flat)}  ({100 * agree / max(len(flat),1):.0f}%)")
    from collections import Counter
    print("  model act dist:    ", dict(Counter(r["model_act"] for r in flat)))
    print("  heuristic act dist:", dict(Counter(r["heuristic_act"] for r in flat)))
    print(f"\nWrote per-case rows -> {OUT}")


if __name__ == "__main__":
    sys.exit(main())
