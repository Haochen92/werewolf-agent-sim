"""OQ21 screen: the seat's deduction block before or after its carried-forward strategy note.

Record: evidence/gameplay/deduction/data/deduction_placement/ (README there; catalogue OQ21 in
evidence/gameplay/deduction/deduction_catalogue.md). Generation only: the samples are judged blind,
separately. The four acceptance cases (AC1-AC4) on their frozen states, rebuilt by the replay bench
(evaluation/src/replay/hallucination_bench.py ``turn_payload`` / ``turn_template``) with
``deduction_mode`` "full" and the arm's ``deduction_placement``, then sampled on the process's game
model the way the bench's ``generate`` builds its chain (legal-target schema, structured output).

AC1's and AC3's same-day claims are in no frozen summary, so the speaker field is filled on the frozen
messages by hand from their words: the entries of tests/engine/deduction/test_joins.py
``_ac1_case`` / ``_ac3_case``, copied below and checked equal to the test's at render time.

  # render and verify both arms' prompts, no model call
  poetry run python evaluation/experiments/deduction_placement_screen.py --render-only
  # then sample (Haiku 5.5, thinking low, as the live site)
  GOOGLE_GENAI_MODEL=anthropic/claude-haiku-5-5 GOOGLE_GENAI_THINKING_LEVEL=low GAME_LLM_ATTEMPTS=1 \
    GAME_LLM_TIMEOUT_S=180 poetry run python evaluation/experiments/deduction_placement_screen.py --n 3
"""

from __future__ import annotations

import argparse
import copy
import difflib
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from evaluation.src.replay.hallucination_bench import _usage_totals, turn_payload, turn_template

DATA = Path("evidence/gameplay/deduction/data")
OUT = DATA / "deduction_placement"
ARMS = ("before_note", "after_note")
MAX_CALLS = 30


def _claims(*actions: tuple) -> list[dict]:
    return [dict(zip(("night", "action", "target", "result", "seen"), a)) for a in actions]


# (case, source file, case_id, hand-filled speaker fields by (day, seq), the lines the seat block must hold)
CASES = [
    ("AC1", "deduction_injection/cases.jsonl", "9b3219e5dc1eb831", {
        (2, 3): _claims((1, "investigate", "player_9", "suspicious", [])),
        (2, 10): _claims((1, "follow", "player_7", "not_said", ["player_8"])),
        (2, 12): _claims((1, "follow", "player_7", "not_said", ["player_8"])),
        (2, 15): _claims((1, "visit", "player_8", "not_said", [])),
    }, {
        "line 2": "player_3 says player_7 came to you on night 1, and player_7 agrees. If that is true, either "
                  "player_7 is the Chanteuse, or player_7 and the Chanteuse both came to you.",
    }),
    ("AC2", "haiku_effort_replay/vote_cases.jsonl", "9b827b695a61ece9", None, {
        "line 2": "You were roleblocked on night 2, so the Chanteuse came to you, and player_7 was the Chanteuse. "
                  "player_2's report that player_7 came to you that night is true. This does not show that player_2 "
                  "is the Sentinel.",
        "lines 4-5 (vote form)": "player_8 can be the Serial Killer only if player_2's watch is false.",
        "line 6": "If the current role claims are true, the Serial Killer is player_6 or player_10.",
    }),
    ("AC3", "haiku_effort_replay/turn_cases.jsonl", "c52500274ffeccf0", {
        (3, 3): _claims((2, "investigate", "player_6", "suspicious", [])),
        (3, 7): _claims((2, "watch", "player_6", "not_said", ["player_4", "player_8"])),
        (3, 9): _claims((2, "no_action", "", "not_said", [])),
    }, {
        "line 1": "player_6 is a wolf",
        "line 2": "player_9 says you came to player_6 on night 2. You did: you checked player_6 that night. This "
                  "confirms that part of player_9's report, not that player_9 is the Sentinel.",
    }),
    ("AC4", "haiku_effort_replay/vote_cases.jsonl", "5b11c9fd2f6b9b0e", None, {
        "line 1": "Both wolves are dead: player_6 and player_1. The Necromancer is alive: it killed through a body "
                  "on night 4. It is player_3, player_9 or player_10.",
        "line 2": "player_4's will shows player_4 checked player_6 on night 2, so player_4 went to player_6 that "
                  "night, as player_9's watch reported. This confirms that part of the report, not that player_9 "
                  "is the Sentinel.",
        "line 4": "If player_9's claim is true, the Necromancer is player_3 or player_10.",
    }),
]


def _case(source: str, case_id: str, fields: dict | None) -> dict:
    for line in (DATA / source).read_text().splitlines():
        case = json.loads(line)
        if case["case_id"] == case_id:
            break
    else:
        raise KeyError(case_id)
    case = copy.deepcopy(case)
    for message in case["state"]["day_channel"]:
        if fields and (actions := fields.get((message["day"], message["seq"]))) is not None:
            message["claimed_night_actions"] = copy.deepcopy(actions)
    return case


def _turn(name: str, source: str, case_id: str, fields: dict | None, arm: str) -> dict[str, Any]:
    from Agents.prompts.prompt_inputs import build_agent_prompt_input

    case = _case(source, case_id, fields)
    payload = {**turn_payload(case), "deduction_mode": "full", "deduction_placement": arm}
    template, schema, key = turn_template(case, payload)
    prompt_input = build_agent_prompt_input(payload)
    messages = template.invoke(prompt_input).to_messages()
    seat = (prompt_input["deduction_seat_before_note"] or prompt_input["deduction_seat_after_note"]).strip()
    return {"case": case, "payload": payload, "template": template, "schema": schema, "key": key,
            "prompt_input": prompt_input, "human": messages[-1].content, "system": messages[0].content,
            "seat_block": seat, "night_actions": prompt_input.get("night_actions") or ""}


def _check_hand_fills() -> None:
    """The copied entries are the test's, exactly."""
    from tests.engine.deduction import test_joins

    for name, source, case_id, fields, _ in CASES:
        if fields:
            ours = _case(source, case_id, fields)["state"]["day_channel"]
            theirs = getattr(test_joins, f"_{name.lower()}_case")()["state"]["day_channel"]
            assert ours == theirs, f"{name}: hand-filled fields differ from test_joins"


def render() -> dict[str, dict[str, dict]]:
    """Both arms' prompts per case, saved and verified: the arms differ only in where the seat block sits,
    and the block (or, for a level-1 line, the private night record) holds the case's lines."""
    _check_hand_fills()
    (OUT / "prompts").mkdir(parents=True, exist_ok=True)
    turns: dict[str, dict[str, dict]] = {}
    report = []
    ok = True
    for name, source, case_id, fields, lines in CASES:
        turns[name] = {arm: _turn(name, source, case_id, fields, arm) for arm in ARMS}
        a, b = turns[name]["before_note"], turns[name]["after_note"]
        for arm in ARMS:
            (OUT / "prompts" / f"{name}_{arm}.txt").write_text(turns[name][arm]["human"])
        same_system = a["system"] == b["system"]
        same_block = a["seat_block"] == b["seat_block"] and bool(a["seat_block"])
        rest_a = a["human"].replace(a["seat_block"], "<SEAT BLOCK>", 1)
        rest_b = b["human"].replace(b["seat_block"], "<SEAT BLOCK>", 1)
        # the slot carries its own newlines, so compare the rest with the block's own line removed
        moved_only = (rest_a.replace("<SEAT BLOCK>", "").split() == rest_b.replace("<SEAT BLOCK>", "").split())
        diff = [d for d in difflib.unified_diff(rest_a.splitlines(), rest_b.splitlines(), lineterm="", n=0)
                if d.startswith(("+", "-")) and not d.startswith(("+++", "---"))]
        note_at = a["human"].find("Adaptive Strategic thinking:")
        order_a = a["human"].find(a["seat_block"]) < note_at
        order_b = b["human"].find(b["seat_block"]) > b["human"].find("Adaptive Strategic thinking:")
        found = {}
        for label, text in lines.items():
            where = ("seat block" if text in a["seat_block"] else
                     "night record" if text in a["night_actions"] else
                     "elsewhere in prompt" if text in a["human"] else "MISSING")
            found[label] = where
            ok &= where != "MISSING"
        ok &= same_system and same_block and moved_only and order_a and order_b
        report.append({"case": name, "case_id": case_id, "same_system": same_system,
                       "same_seat_block": same_block, "only_the_block_moves": moved_only,
                       "block_before_note_in_A": order_a, "block_after_note_in_B": order_b,
                       "seat_block_lines": len(a["seat_block"].splitlines()),
                       "seat_block_chars": len(a["seat_block"]),
                       "human_chars": [len(a["human"]), len(b["human"])],
                       "diff_lines_besides_block": diff, "key_lines": found})
    (OUT / "prompt_check.json").write_text(json.dumps(report, indent=1) + "\n")
    print(json.dumps(report, indent=1))
    if not ok:
        raise SystemExit("verification failed: see prompt_check.json; no model call made")
    return turns


class _RetryCounter(logging.Handler):
    """The Anthropic SDK's own retries are requests too: count them from its log."""

    def __init__(self) -> None:
        super().__init__(logging.INFO)
        self.retries = 0

    def emit(self, record: logging.LogRecord) -> None:
        if "Retrying request" in record.getMessage():
            self.retries += 1


def sample(turns: dict[str, dict[str, dict]], n: int, only: set[tuple[str, str, int]] | None = None,
           calls_so_far: int = 0) -> None:
    """``only``: regenerate just these (case, arm, sample) rows, e.g. an invalid one (appended, marked
    ``rerun``); ``calls_so_far`` counts the requests already spent against MAX_CALLS."""
    from langchain_core.callbacks import UsageMetadataCallbackHandler

    from Agents.llm_factory import get_llm
    from Agents.llm_factory.accessors import _game_model, game_thinking_level
    from Agents.llm_factory.pricing import cost_usd
    from Agents.turn.action_space import output_schema_with_legal_targets, valid_targets_for_action

    model = _game_model()
    assert model == "anthropic/claude-haiku-5-5" and game_thinking_level(model) == "low", (model,)
    retry_log = _RetryCounter()
    for name in ("anthropic", "anthropic._base_client"):
        logging.getLogger(name).addHandler(retry_log)
        logging.getLogger(name).setLevel(logging.INFO)
    calls, total_cost = calls_so_far, 0.0
    path = OUT / "samples.jsonl"
    with path.open("a") as fh:
        for name, *_ in CASES:
            for arm in ARMS:
                t = turns[name][arm]
                bound = output_schema_with_legal_targets(
                    t["schema"], t["key"], valid_targets_for_action(t["payload"], t["key"]))
                chain = t["template"] | get_llm().with_structured_output(bound)
                for i in range(n):
                    if only is not None and (name, arm, i) not in only:
                        continue
                    if calls + retry_log.retries >= MAX_CALLS:
                        raise SystemExit(f"call cap {MAX_CALLS} reached")
                    calls += 1
                    usage, started, out, err = UsageMetadataCallbackHandler(), time.monotonic(), None, ""
                    try:
                        out = chain.invoke(t["prompt_input"], config={"callbacks": [usage]})
                    except Exception as e:  # recorded; the sample counts as invalid
                        err = str(e)[:300]
                    tokens = _usage_totals(usage, time.monotonic() - started)
                    # langchain-anthropic files a write under its TTL key and then zeroes cache_creation
                    written = sum((d.get(k) or 0) for u in usage.usage_metadata.values()
                                  for d in [u.get("input_token_details") or {}]
                                  for k in ("cache_creation", "ephemeral_5m_input_tokens", "ephemeral_1h_input_tokens"))
                    cost = cost_usd(model.removeprefix("anthropic/"), datetime.now(timezone.utc),
                                    input=tokens["input"], cached=tokens["cached"], output=tokens["output"],
                                    written=written) or 0.0
                    total_cost += cost
                    row = {"case": name, "case_id": t["case"]["case_id"], "arm": arm, "sample": i,
                           "phase": t["case"]["phase"], "speaker": t["case"]["speaker"], "role": t["case"]["role"],
                           "valid": out is not None, "error": err, "rerun": only is not None}
                    if out is not None:
                        row |= {"pass_turn": getattr(out, "pass_turn", None),
                                "message": getattr(out, "message", None),
                                "claim": getattr(out, "claim", None),
                                "claimed_night_actions": [c.model_dump() for c in getattr(out, "claimed_night_actions", [])],
                                "vote_target": getattr(out, "vote_target", None),
                                "updated_strategy": out.updated_strategy,
                                "reads": [r.model_dump() for r in out.reads]}
                    row["usage"] = {**tokens, "cache_written": written, "cost_usd": round(cost, 6)}
                    fh.write(json.dumps(row) + "\n")
                    fh.flush()
                    print(f"{name} {arm} #{i}: valid={row['valid']} {err[:80]} ${cost:.4f}", flush=True)
    print(f"model requests: {calls} invokes + {retry_log.retries} SDK retries; cost ${total_cost:.4f}")


def main() -> None:
    global OUT, MAX_CALLS
    parser = argparse.ArgumentParser()
    parser.add_argument("--render-only", action="store_true")
    parser.add_argument("--n", type=int, default=3)
    parser.add_argument("--rerun-invalid", action="store_true",
                        help="regenerate the samples whose latest row in samples.jsonl is invalid")
    parser.add_argument("--out", type=Path, default=OUT, help="output folder (prompts, check, samples)")
    parser.add_argument("--max-calls", type=int, default=MAX_CALLS, help="cap on model requests, reruns included")
    args = parser.parse_args()
    OUT, MAX_CALLS = args.out, args.max_calls
    turns = render()
    if args.render_only:
        return
    if not args.rerun_invalid:
        sample(turns, args.n)
        return
    rows = [json.loads(line) for line in (OUT / "samples.jsonl").read_text().splitlines()]
    latest = {(r["case"], r["arm"], r["sample"]): r for r in rows}
    sample(turns, args.n, only={k for k, r in latest.items() if not r["valid"]}, calls_so_far=len(rows))


if __name__ == "__main__":
    main()
