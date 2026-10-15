"""Would a second "de-halo" judge after extraction fix outcome-halo verdicts, and at what cost?

One saved game is re-extracted with the current prompts (gemini-3.8-flash), then the same de-halo
prompt is run twice over its observations: once on gemini-3.8-flash (the extractor's family) and once
on Claude Sonnet 5 (a different family). Records the observations, both judges' verdicts and each
call's tokens and cost. One-off comparison for evidence/memory_system/v8 (2026-10-11).

    poetry run python -m evaluation.experiments.dehalo_compare <eval_cases.jsonl> <out_dir>
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv(".env")

from langchain_core.callbacks import get_usage_metadata_callback  # noqa: E402

from Agents.llm_factory import get_llm_pro  # noqa: E402
from Agents.memory.extraction.extraction_agent import EXTRACTION_ROLES, extract_postgame_per_cell  # noqa: E402
from Agents.memory.extraction.inputs import extraction_inputs_from_frozen_case  # noqa: E402
from Agents.prompts.compose import rules_block  # noqa: E402

# $ per 1M tokens (2026-10-11): 3.8 Flash at its promo price; Claude first-party API (Haiku 5.5 for
# prompts up to 100k tokens).
GEMINI_38 = {"input": 0.75, "cached": 0.075, "output": 3.75}
CLAUDE_PRICES = {"claude-sonnet-5": (2.00, 10.00), "claude-sonnet-5-5": (2.00, 10.00),
                 "claude-haiku-5-5": (0.10, 0.50)}

DEHALO_PROMPT = """You are checking the verdicts of lessons extracted from one finished game of a ten-seat
Werewolf variant. Each lesson records what one player did and judges its net effect on that player's
side: positive, negative, mixed or unclear.

Your only job is to catch HALO verdicts: a verdict that credits or blames a move for an outcome the
record does not connect to that move. The usual sign is a verdict that simply follows which side won:
a town move called positive because town won, an evil move called negative because evil lost, a vote
or an abstain credited with something another player did later for their own reasons.

For each lesson:
- KEEP the verdict when something in the record (a message, a vote, a night result, a strategy note)
  links this move to the outcome it is credited or blamed for. A mechanical consequence counts (a
  sigil struck the attacker; a watch caught a visitor who was then voted out on that evidence).
- Change it to "unclear" when the outcome merely followed the move, or came from other players'
  own decisions that the record does not tie to this move.
- Change it to the other direction only when the record directly shows the move worked against the
  player's own side (for example, a town player voting to eliminate a player later revealed as town).
Do not judge whether the move was wise, and never reason about what a different move would have done.

GAME RULES:
{rules}

GAME RECORD:
{record}

FINAL STRATEGY NOTES:
{notes}

GAME OUTCOME: {outcome}

LESSONS:
{lessons}

Return one judgment for every lesson, by its index."""


class Judgment(BaseModel):
    index: int = Field(description="The lesson's index.")
    halo: bool = Field(description="True when the original verdict is not supported by the record.")
    revised_verdict: Literal["positive", "negative", "mixed", "unclear"] = Field(
        description="The verdict the record supports; the original one when it holds.")
    reason: str = Field(description="One sentence: what in the record supports or fails to support the verdict.")


class Judgments(BaseModel):
    judgments: list[Judgment] = Field(description="One judgment per lesson.")


def _lessons(observations: list[dict]) -> str:
    rows = []
    for i, o in enumerate(observations, 1):
        rows.append(f"[{i}] {o['perspective']} / {o['action_phase']} — verdict: {o['net_verdict']}\n"
                    f"  did: {o['approach']}\n  immediately: {o['immediate_response']}\n"
                    f"  end of game: {o['impact_on_final_game_outcome']}")
    return "\n".join(rows)


def _gemini_cost(usage: dict) -> float:
    u = next(iter(usage.values()))
    cached = u.get("input_token_details", {}).get("cache_read", 0)
    return ((u["input_tokens"] - cached) * GEMINI_38["input"] + cached * GEMINI_38["cached"]
            + u["output_tokens"] * GEMINI_38["output"]) / 1e6


def main(cases_path: str, out_dir: str, claude_models: list[str]) -> None:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    case = next(json.loads(line)["output"]["extraction_case"] for line in open(cases_path)
                if json.loads(line)["kind"] == "postgame_extraction")
    inputs = extraction_inputs_from_frozen_case(case)
    dealt = set(case["roles"].values())

    # 1. Extraction with the current prompts (reused when already run, so every judge reads the same set).
    if (out / "extraction.json").exists():
        observations = json.loads((out / "extraction.json").read_text())["observations"]
    else:
        with get_usage_metadata_callback() as cb:
            res = extract_postgame_per_cell(inputs, roles=tuple(r for r in EXTRACTION_ROLES if r in dealt),
                                            cache_prefix=True)
        observations = [o.model_dump(mode="json") for o in res.output.observations]
        extraction = {"usage": cb.usage_metadata, "cost_usd": _gemini_cost(cb.usage_metadata),
                      "observations": observations}
        (out / "extraction.json").write_text(json.dumps(extraction, indent=1, default=str))
        print("extraction:", len(observations), "observations, $", round(extraction["cost_usd"], 3))

    prompt = DEHALO_PROMPT.format(rules=rules_block(inputs["lineup"]), record=case["formatted_discussions"],
                                  notes=case["formatted_strategy_notes"], outcome=case["game_outcome"],
                                  lessons=_lessons(observations))

    # 2. De-halo on the extractor's family (once).
    if (out / "dehalo_gemini.json").exists():
        claude_judges(prompt, out, claude_models)
        return
    with get_usage_metadata_callback() as cb:
        judged = get_llm_pro().with_structured_output(Judgments).invoke(prompt)
    gemini = {"model": os.getenv("GOOGLE_GENAI_PRO_MODEL", "gemini-3.8-flash"), "usage": cb.usage_metadata,
              "cost_usd": _gemini_cost(cb.usage_metadata), "judgments": judged.model_dump()["judgments"]}
    (out / "dehalo_gemini.json").write_text(json.dumps(gemini, indent=1, default=str))
    print("gemini de-halo: $", round(gemini["cost_usd"], 3))

    # 3. De-halo on a different family: Claude.
    claude_judges(prompt, out, claude_models)


def claude_judges(prompt: str, out: Path, models: list[str]) -> None:
    import anthropic

    client = anthropic.Anthropic(api_key=os.environ["CLAUDE_API_KEY"])
    for model in models:
        response = client.messages.parse(model=model, max_tokens=16000, output_format=Judgments,
                                         messages=[{"role": "user", "content": prompt}])
        usage = response.usage
        price_in, price_out = CLAUDE_PRICES[model]
        result = {"model": model, "stop_reason": response.stop_reason,
                  "usage": {"input_tokens": usage.input_tokens, "output_tokens": usage.output_tokens},
                  "cost_usd": (usage.input_tokens * price_in + usage.output_tokens * price_out) / 1e6,
                  "judgments": response.parsed_output.model_dump()["judgments"] if response.parsed_output else []}
        name = "dehalo_claude.json" if model == "claude-sonnet-5" else f"dehalo_{model}.json"
        (out / name).write_text(json.dumps(result, indent=1, default=str))
        print(model, "de-halo: $", round(result["cost_usd"], 4), result["stop_reason"], result["usage"])


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3].split(",") if len(sys.argv) > 3 else ["claude-sonnet-5"])
