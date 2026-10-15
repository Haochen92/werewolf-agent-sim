"""Extraction on Claude models, against the gemini-3.8-flash extraction of the same saved game.

Runs the live per-cell extraction (same prefix, cell tails and output schemas as
``extract_postgame_per_cell``) on each Claude model through the Anthropic SDK: the shared prefix is
a cached system message, each cell's tail the user message. The day cells' phase tag is set from
the call, as the live extractor does. Records observations, tokens (cache reads and writes) and cost.
One-off comparison for evidence/memory_system/v8 (2026-10-11).

    poetry run python -m evaluation.experiments.claude_extraction_compare <eval_cases.jsonl> <out_dir> \
        claude-haiku-5-5,claude-sonnet-5-5
"""

from __future__ import annotations

import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(".env")

import anthropic  # noqa: E402

from Agents.memory.extraction.cell_units import ROLE_UNITS  # noqa: E402
from Agents.memory.extraction.extraction_agent import EXTRACTION_ROLES  # noqa: E402
from Agents.memory.extraction.inputs import (  # noqa: E402
    build_cell_extraction_prefix,
    build_cell_observation_tail,
    extraction_inputs_from_frozen_case,
)
from Agents.schemas.memory import cell_observation_schema_for, cell_observations_extraction_schema  # noqa: E402

# $ per 1M tokens (2026-10-11, Anthropic pricing page): input, output, cache read; a 5-minute cache
# write is 1.25x input. Haiku 5.5 rates are for prompts up to 100k tokens.
PRICES = {"claude-haiku-5-5": (0.10, 0.50, 0.01), "claude-sonnet-5-5": (2.00, 10.00, 0.10)}


def _cell(client, model: str, prefix: str, role: str, wording: str, rep: str):
    schema = cell_observations_extraction_schema(role, rep)
    tail = build_cell_observation_tail(role, wording, rep, cell_observation_schema_for(role, rep))
    response = client.messages.parse(
        model=model, max_tokens=16000, output_format=schema,
        system=[{"type": "text", "text": prefix, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": tail}],
    )
    observations = list(response.parsed_output.observations) if response.parsed_output else []
    if rep in ("day_discussion", "day_vote"):
        for o in observations:
            o.action_phase = rep
    return [o.model_dump(mode="json") for o in observations], response.usage, response.stop_reason


def main(cases_path: str, out_dir: str, models: list[str]) -> None:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    case = next(json.loads(line)["output"]["extraction_case"] for line in open(cases_path)
                if json.loads(line)["kind"] == "postgame_extraction")
    inputs = extraction_inputs_from_frozen_case(case)
    prefix = build_cell_extraction_prefix(inputs)
    dealt = set(case["roles"].values())
    cells = [(role, wording, rep) for role in EXTRACTION_ROLES if role in dealt
             for (_group, wording, rep) in ROLE_UNITS.get(role, [])]
    client = anthropic.Anthropic(api_key=os.environ["CLAUDE_API_KEY"])

    for model in models:
        price_in, price_out, price_read = PRICES[model]
        # The first cell writes the cache; the rest read it, in parallel.
        results = [_cell(client, model, prefix, *cells[0])]
        with ThreadPoolExecutor(max_workers=8) as pool:
            results += list(pool.map(lambda c: _cell(client, model, prefix, *c), cells[1:]))
        observations = [o for obs, _u, _s in results for o in obs]
        tokens = {"input": 0, "output": 0, "cache_read": 0, "cache_write": 0}
        for _obs, u, _s in results:
            tokens["input"] += u.input_tokens
            tokens["output"] += u.output_tokens
            tokens["cache_read"] += u.cache_read_input_tokens or 0
            tokens["cache_write"] += u.cache_creation_input_tokens or 0
        cost = (tokens["input"] * price_in + tokens["cache_write"] * price_in * 1.25
                + tokens["cache_read"] * price_read + tokens["output"] * price_out) / 1e6
        stops = sorted({s for _o, _u, s in results})
        (out / f"extraction_{model}.json").write_text(json.dumps(
            {"model": model, "tokens": tokens, "cost_usd": cost, "stop_reasons": stops,
             "observations": observations}, indent=1, default=str))
        print(model, len(observations), "observations, $", round(cost, 4), tokens, stops)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3].split(","))
