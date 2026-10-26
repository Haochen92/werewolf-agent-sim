"""AC2 ablation: which added sentences in player_8's seat-block entry move the day-3 vote.

Record: evidence/gameplay/deduction/data/deduction_ac2_ablation/ (README there). Generation only. Wraps
deduction_placement_screen.py (its AC2 case, chain and settings; arm "before_note") and removes
sentences from the RENDERED human message by exact string removal, each checked to occur exactly once.

  poetry run python evaluation/experiments/deduction_ac2_ablation.py --render-only
  LANGFUSE_TRACING_ENABLED=false GOOGLE_GENAI_MODEL=anthropic/claude-haiku-5-5 GOOGLE_GENAI_THINKING_LEVEL=low \
    GAME_LLM_ATTEMPTS=1 GAME_LLM_TIMEOUT_S=180 poetry run python evaluation/experiments/deduction_ac2_ablation.py --n 10
"""

from __future__ import annotations

import argparse
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path

from evaluation.experiments import deduction_placement_screen as screen
from evaluation.src.replay.hallucination_bench import _usage_totals

OUT = screen.DATA / "deduction_ac2_ablation"
N10_PROMPT = screen.DATA / "deduction_placement_n10" / "prompts" / "AC2_before_note.txt"
ARM = "before_note"
MAX_CALLS = 45

E1 = (" player_2 says player_8 came to you on night 2, and player_8 says it protected you that night. These agree; "
      "the sighting does not show which action player_8 took.")
WILL = (" player_3's will shows player_7, the Chanteuse, went to player_8 on night 1. The pack's kill that night was "
        "on player_1, so that visit was her block on player_8.")
CLAIMS = ("- No one else claims the Investigator, the Sentinel, the Sigilist or the Healer. player_6 and player_10 "
          "have made no role claim.\n")
VARIANTS = {"V0": (), "V1": (E1,), "V2": (WILL,), "V3": (E1, WILL, CLAIMS)}


def _ablate(text: str, removals: tuple[str, ...]) -> str:
    for s in removals:
        assert text.count(s) == 1, ("removal string does not occur exactly once", s)
        text = text.replace(s, "", 1)
    return text


def render() -> tuple[dict, dict[str, str]]:
    name, source, case_id, fields, _ = next(c for c in screen.CASES if c[0] == "AC2")
    t = screen._turn(name, source, case_id, fields, ARM)
    live = t["human"]
    if live != N10_PROMPT.read_text():
        raise SystemExit("live AC2 render differs from the n10 prompt file; stopping")
    humans = {v: _ablate(live, r) for v, r in VARIANTS.items()}
    (OUT / "prompts").mkdir(parents=True, exist_ok=True)
    check = []
    for v, r in VARIANTS.items():
        (OUT / "prompts" / f"AC2_{v}.txt").write_text(humans[v])
        # nothing else changed: re-inserting is not unique, so check by length and by removing from V0 again
        check.append({"variant": v, "removed": list(r), "chars": len(humans[v]),
                      "chars_removed": len(live) - len(humans[v]),
                      "equals_sum_of_removals": len(live) - len(humans[v]) == sum(map(len, r)),
                      "remaining_counts": [humans[v].count(s) for s in r]})
    (OUT / "prompt_check.json").write_text(json.dumps(check, indent=1) + "\n")
    print(json.dumps(check, indent=1))
    return t, humans


def sample(t: dict, humans: dict[str, str], n: int, only: set[tuple[str, int]] | None = None,
           calls_so_far: int = 0) -> None:
    from langchain_core.callbacks import UsageMetadataCallbackHandler
    from langchain_core.prompt_values import ChatPromptValue
    from langchain_core.runnables import RunnableLambda

    from Agents.llm_factory import get_llm
    from Agents.llm_factory.accessors import _game_model, game_thinking_level
    from Agents.llm_factory.pricing import cost_usd
    from Agents.turn.action_space import output_schema_with_legal_targets, valid_targets_for_action

    model = _game_model()
    assert model == "anthropic/claude-haiku-5-5" and game_thinking_level(model) == "low", (model,)
    retry_log = screen._RetryCounter()
    for logger in ("anthropic", "anthropic._base_client"):
        logging.getLogger(logger).addHandler(retry_log)
        logging.getLogger(logger).setLevel(logging.INFO)
    bound = output_schema_with_legal_targets(t["schema"], t["key"], valid_targets_for_action(t["payload"], t["key"]))
    llm = get_llm().with_structured_output(bound)
    calls, total_cost = calls_so_far, 0.0
    with (OUT / "samples.jsonl").open("a") as fh:
        for v, removals in VARIANTS.items():
            def rendered(prompt_input, removals=removals, v=v):
                messages = t["template"].invoke(prompt_input).to_messages()
                human = _ablate(messages[-1].content, removals)
                assert human == humans[v]
                return ChatPromptValue(messages=[*messages[:-1], messages[-1].model_copy(update={"content": human})])
            chain = RunnableLambda(rendered) | llm
            for i in range(n):
                if only is not None and (v, i) not in only:
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
                written = sum((d.get(k) or 0) for u in usage.usage_metadata.values()
                              for d in [u.get("input_token_details") or {}]
                              for k in ("cache_creation", "ephemeral_5m_input_tokens", "ephemeral_1h_input_tokens"))
                cost = cost_usd(model.removeprefix("anthropic/"), datetime.now(timezone.utc),
                                input=tokens["input"], cached=tokens["cached"], output=tokens["output"],
                                written=written) or 0.0
                total_cost += cost
                row = {"case": "AC2", "case_id": t["case"]["case_id"], "variant": v, "arm": ARM, "sample": i,
                       "valid": out is not None, "error": err, "rerun": only is not None}
                if out is not None:
                    row |= {"vote_target": getattr(out, "vote_target", None),
                            "updated_strategy": out.updated_strategy,
                            "reads": [r.model_dump() for r in out.reads]}
                row["usage"] = {**tokens, "cache_written": written, "cost_usd": round(cost, 6)}
                fh.write(json.dumps(row) + "\n")
                fh.flush()
                print(f"{v} #{i}: valid={row['valid']} vote={row.get('vote_target')} {err[:80]} ${cost:.4f}",
                      flush=True)
    print(f"model requests: {calls} invokes + {retry_log.retries} SDK retries; cost ${total_cost:.4f}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--render-only", action="store_true")
    parser.add_argument("--n", type=int, default=10)
    parser.add_argument("--rerun-invalid", action="store_true")
    args = parser.parse_args()
    t, humans = render()
    if args.render_only:
        return
    if not args.rerun_invalid:
        sample(t, humans, args.n)
        return
    rows = [json.loads(line) for line in (OUT / "samples.jsonl").read_text().splitlines()]
    latest = {(r["variant"], r["sample"]): r for r in rows}
    sample(t, humans, args.n, only={k for k, r in latest.items() if not r["valid"]}, calls_so_far=len(rows))


if __name__ == "__main__":
    main()
