"""Folded-novelty smoke test for the revised SituationSummary (novelty gate).

Two questions:
  Test 1 (DRIFT): does adding the `novelty`/`novelty_reasoning` fields perturb the
    generated situations? Old schema (situations only) vs new schema, SAME cases,
    temp 0 (isolate the schema effect). Floor = old-vs-old at temp 1.0 (natural
    sampling variance). If new-vs-old drift <= that floor, the fields are harmless.
  Test 2 (NOVELTY ACCURACY): paired A/B per case. NEW = transcript as-is (the agent's
    point is fresh). REPEATED = inject a PARAPHRASE of the agent's real message,
    attributed to another player, into the transcript (their point is now on the
    table). Same situation-summary call both ways; a working gate shifts the label
    toward `repeated` when injected. Tolerant scoring: `borderline` counts either way;
    the discriminating signal is the SHIFT.

No prompt edits — the novelty fields ride in via with_structured_output (as smoke_act_2d did).
Run with the poetry venv python (Vertex flash-lite).
"""

from __future__ import annotations

import json
import os
from collections import Counter
from pathlib import Path
from typing import Literal

os.environ.setdefault("LLM_BACKEND", "vertex")
os.environ.setdefault("GOOGLE_GENAI_MODEL", "gemini-3.1-flash-lite")

from pydantic import BaseModel, Field  # noqa: E402
from langchain_core.prompts import ChatPromptTemplate  # noqa: E402

from Agents.agents import _build_agent_prompt_input, get_llm  # noqa: E402
from Agents.schemas import DayChannel  # noqa: E402
from Agents.schemas.evaluation import EvalCase  # noqa: E402
from Agents.schemas.output import SituationEntry, SituationSummary  # noqa: E402
from Agents.prompts.memory import (  # noqa: E402
    HEALER_SITUATION_SUMMARY,
    INVESTIGATOR_SITUATION_SUMMARY,
    VILLAGER_SITUATION_SUMMARY,
    WOLF_SITUATION_SUMMARY,
)
from evaluation.components.situation_summary import eval_case_to_agent_payload  # noqa: E402
from Agents.memory import embeddings  # noqa: E402
from Agents.retrieval_filters import cosine_similarity, embed_texts  # noqa: E402

DATASET = Path("evidence/memory_system/strategy_adoption/eval_sets/phase1_adoption_v2.jsonl")
N_DRIFT = int(os.getenv("N_DRIFT", "12"))
N_NOV = int(os.getenv("N_NOV", "15"))
OUT = Path("evidence/agent_speaking/smoke_situation_novelty_results.jsonl")

PROMPTS = {
    "villager": VILLAGER_SITUATION_SUMMARY,
    "healer": HEALER_SITUATION_SUMMARY,
    "investigator": INVESTIGATOR_SITUATION_SUMMARY,
    "wolf": WOLF_SITUATION_SUMMARY,
}
PARA = ChatPromptTemplate.from_messages([
    ("system", "Reword the following Werewolf discussion message to make the SAME substantive point "
               "in clearly different words (different sentence structure, synonyms). Do not add or "
               "remove any claim. Return ONLY the reworded message."),
    ("human", "{msg}"),
])


class OldSituationSummary(BaseModel):
    situations: list[SituationEntry] = Field(min_length=1, max_length=2, description=(
        "1-2 distinct situations the player currently faces, each with structured "
        "dimensional fields for semantic search."))

    @property
    def composed_situations(self) -> list[str]:
        return [s.composed for s in self.situations]


class ContribSituationSummary(BaseModel):
    """Hypothesis fix: anchor novelty to an explicit prospective contribution, not the state recap."""
    situations: list[SituationEntry] = Field(min_length=1, max_length=2, description=(
        "1-2 distinct situations the player currently faces, each with structured "
        "dimensional fields for semantic search."))
    intended_contribution: str = Field(description=(
        "In ONE sentence: the single most useful point you could add to the discussion RIGHT NOW "
        "that is NOT already voiced — or 'nothing new to add' if everything you would say is already "
        "on the table."))
    novelty: Literal["repeated", "borderline", "new"] = Field(description=(
        "Judge YOUR intended_contribution above against the discussion so far (including your own "
        "earlier messages). new: it introduces a point not yet voiced. repeated: it restates a point "
        "already on the table, even if reworded. borderline: only a marginal new angle."))
    novelty_reasoning: str = Field(description="One sentence justifying the novelty label.")

    @property
    def composed_situations(self) -> list[str]:
        return [s.composed for s in self.situations]


def text_of(resp) -> str:
    c = getattr(resp, "content", resp)
    if isinstance(c, str):
        return c.strip()
    if isinstance(c, list):
        return "".join(b.get("text", "") if isinstance(b, dict) else str(b) for b in c).strip()
    return str(c).strip()


def run_summary(case: EvalCase, schema, temp: float, extra=None):
    payload = eval_case_to_agent_payload(case)
    if extra:
        payload["day_channel"] = list(payload["day_channel"]) + extra
    os.environ["GOOGLE_GENAI_TEMPERATURE"] = str(temp)
    prompt = PROMPTS.get(case.player_role, VILLAGER_SITUATION_SUMMARY)
    chain = prompt | get_llm().with_structured_output(schema)
    return chain.invoke(_build_agent_prompt_input(payload))


def emb(text: str):
    return embed_texts([text], embeddings)[0]


def composed_text(res) -> str:
    return " | ".join(res.composed_situations)


def load_cases(n):
    out = []
    with DATASET.open() as f:
        for line in f:
            raw = json.loads(line).get("eval_case", {})
            if raw.get("action_phase") != "day_discussion":
                continue
            am = raw.get("agent_message") or {}
            vd = [m for m in raw.get("visible_discussion", []) if m.get("player") != "game_master"]
            if not am.get("message") or len(vd) < 4:
                continue
            out.append((EvalCase.model_validate(raw), am))
            if len(out) >= n:
                break
    return out


def main():
    rows = []

    # ---- Test 1: drift ----
    print(f"=== Test 1: drift (n={N_DRIFT}) ===", flush=True)
    drift = load_cases(N_DRIFT)
    schema_sims, floor_sims = [], []
    for i, (case, _) in enumerate(drift):
        try:
            old0 = composed_text(run_summary(case, OldSituationSummary, 0.0))
            new0 = composed_text(run_summary(case, SituationSummary, 0.0))
            old1a = composed_text(run_summary(case, OldSituationSummary, 1.0))
            old1b = composed_text(run_summary(case, OldSituationSummary, 1.0))
            s_schema = cosine_similarity(emb(old0), emb(new0))
            s_floor = cosine_similarity(emb(old1a), emb(old1b))
            schema_sims.append(s_schema)
            floor_sims.append(s_floor)
            rows.append({"test": "drift", "i": i, "role": case.player_role,
                         "sim_old_vs_new_t0": round(s_schema, 4),
                         "sim_old_vs_old_t1": round(s_floor, 4)})
        except Exception as e:  # noqa: BLE001
            rows.append({"test": "drift", "i": i, "error": f"{type(e).__name__}: {e}"[:200]})
        if (i + 1) % 4 == 0:
            print(f"  ...{i+1}/{len(drift)}", flush=True)

    # ---- Test 2: novelty accuracy (paired) ----
    print(f"\n=== Test 2: novelty paired A/B (n={N_NOV}) ===", flush=True)
    nov = load_cases(N_NOV)
    para_chain = PARA | get_llm()
    # two gate variants: A = current (situation-anchored), B = contribution-anchored (hypothesis fix)
    labels = {"A_new": [], "A_rep": [], "B_new": [], "B_rep": []}
    for i, (case, am) in enumerate(nov):
        try:
            payload = eval_case_to_agent_payload(case)
            others = [p for p in payload.get("surviving_players", []) if p != case.player_id]
            if not others:
                continue
            os.environ["GOOGLE_GENAI_TEMPERATURE"] = "0"
            para = text_of(para_chain.invoke({"msg": am["message"]}))
            _seq = sum(1 for m in payload["day_channel"] if m.day == case.day)
            inject = [DayChannel(day=case.day, seq=_seq, player=others[0], message=para)]
            a_new = run_summary(case, SituationSummary, 0.0)
            a_rep = run_summary(case, SituationSummary, 0.0, extra=inject)
            b_new = run_summary(case, ContribSituationSummary, 0.0)
            b_rep = run_summary(case, ContribSituationSummary, 0.0, extra=inject)
            labels["A_new"].append(a_new.novelty); labels["A_rep"].append(a_rep.novelty)
            labels["B_new"].append(b_new.novelty); labels["B_rep"].append(b_rep.novelty)
            rows.append({"test": "novelty", "i": i, "role": case.player_role,
                         "A_NEW": a_new.novelty, "A_REP": a_rep.novelty,
                         "B_NEW": b_new.novelty, "B_REP": b_rep.novelty,
                         "B_NEW_contrib": b_new.intended_contribution[:200],
                         "B_REP_contrib": b_rep.intended_contribution[:200],
                         "agent_msg": am["message"][:160], "paraphrase": para[:160]})
        except Exception as e:  # noqa: BLE001
            rows.append({"test": "novelty", "i": i, "error": f"{type(e).__name__}: {e}"[:200]})
        if (i + 1) % 5 == 0:
            print(f"  ...{i+1}/{len(nov)}", flush=True)

    OUT.write_text("\n".join(json.dumps(r) for r in rows) + "\n")

    # ---- report ----
    print("\n================ RESULTS ================")
    if schema_sims:
        print(f"\nTest 1 DRIFT (cosine sim of composed situations):")
        print(f"  old-vs-new @temp0 (schema effect): mean {sum(schema_sims)/len(schema_sims):.4f}  "
              f"min {min(schema_sims):.4f}")
        print(f"  old-vs-old @temp1 (sampling floor): mean {sum(floor_sims)/len(floor_sims):.4f}  "
              f"min {min(floor_sims):.4f}")
        verdict = "WITHIN NOISE" if (sum(schema_sims)/len(schema_sims)) >= (sum(floor_sims)/len(floor_sims)) - 0.02 else "DRIFT > NOISE"
        print(f"  -> {verdict}")
    order = ["new", "borderline", "repeated"]
    for variant, name in (("A", "A: situation-anchored (current schema)"),
                          ("B", "B: contribution-anchored (hypothesis fix)")):
        nl, rl = labels[f"{variant}_new"], labels[f"{variant}_rep"]
        if not nl:
            continue
        toward = sum(1 for a, b in zip(nl, rl) if order.index(b) > order.index(a))
        new_ok = sum(1 for a in nl if a in ("new", "borderline"))
        rep_ok = sum(1 for b in rl if b in ("repeated", "borderline"))
        print(f"\nTest 2 NOVELTY — {name} (paired, n={len(nl)}):")
        print(f"  NEW  (point fresh)  dist: {dict(Counter(nl))}   -> new/borderline {new_ok}/{len(nl)}")
        print(f"  REP  (point voiced) dist: {dict(Counter(rl))}   -> repeated/borderline {rep_ok}/{len(rl)}")
        print(f"  injection shifted toward repeated: {toward}/{len(nl)}  (discrimination signal)")
    print(f"\nWrote rows -> {OUT}")


if __name__ == "__main__":
    main()
