"""Replay the roleblocked healer's key turn (game 2f19d908, case R1) with the deduction engine on or off,
or render it for a model run outside the game path.

Record: evidence/gameplay/deduction/experiment_log.md §8. The turn is the healer's day-2 turn right after
player_7 admitted visiting it (case 9b3219e5dc1eb831 in data/deduction_injection/cases.jsonl, "as
played"). Today's code renders the engine's roleblock line into the night record; ``--engine off`` sets
the game's deduction mode to "off" on the payload, which the bench does not do itself (it builds the
prompt without the pipeline step that copies RunConfig.deduction_mode), so the night record falls back
to the wording the game showed.

The seat model, thinking level and output mode come from the environment, as for a bench arm:

    GOOGLE_GENAI_MODEL=anthropic/claude-haiku-5-5 GOOGLE_GENAI_THINKING_LEVEL=low \\
    LLM_STRUCTURED_MODE=json_mode poetry run python evaluation/experiments/healer_model_compare.py \\
        run --engine off --n 10 --out <samples.jsonl>

    poetry run python evaluation/experiments/healer_model_compare.py render --engine on --out <turn.md>

``render`` writes the system message, the user message and the output schema to one file: the input the
subagent arm of §8 read.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import evaluation.src.replay.hallucination_bench as bench  # noqa: E402
from Agents.prompts.prompt_inputs import build_agent_prompt_input  # noqa: E402
from Agents.turn.action_space import (  # noqa: E402
    output_schema_with_legal_targets,
    valid_targets_for_action,
)

CASES = Path("evidence/gameplay/deduction/data/deduction_injection/cases.jsonl")
CASE_ID = "9b3219e5dc1eb831"


def main() -> None:
    """Parse the command line and run ``render`` or ``run``."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("command", choices=["render", "run"])
    parser.add_argument("--engine", choices=["on", "off"], required=True)
    parser.add_argument("--n", type=int, default=10, help="samples to generate (run only)")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    case = load_case()
    if args.engine == "off":
        switch_engine_off()
    if args.command == "render":
        args.out.write_text(render_turn(case))
    else:
        samples = bench.generate(case, args.n)
        args.out.write_text("".join(json.dumps(s) + "\n" for s in samples))
    print(f"wrote {args.out}")


def load_case() -> dict[str, Any]:
    """The frozen turn.

    Returns:
        The case record for ``CASE_ID``, as frozen from the game's checkpoints.
    """
    for line in CASES.read_text().splitlines():
        case = json.loads(line)
        if case["case_id"] == CASE_ID:
            return case
    raise ValueError(f"{CASE_ID} not in {CASES}")


def switch_engine_off() -> None:
    """Make every payload the bench builds carry the game setting deduction_mode="off"."""
    build_payload = bench.turn_payload

    def payload_without_engine(case: dict[str, Any], memory: str = "none",
                               summaries: dict[str, dict] | None = None) -> dict[str, Any]:
        payload = build_payload(case, memory, summaries)
        payload["deduction_mode"] = "off"
        return payload

    bench.turn_payload = payload_without_engine


def render_turn(case: dict[str, Any]) -> str:
    """The turn as the game model receives it, for a model run outside the game path.

    Args:
        case: the frozen turn.

    Returns:
        The system message, the user message and the output schema, as one Markdown text.
    """
    payload = bench.turn_payload(case)
    template, schema, key = bench.turn_template(case, payload)
    bound = output_schema_with_legal_targets(schema, key, valid_targets_for_action(payload, key))
    messages = template.format_messages(**build_agent_prompt_input(payload))
    system = next(m.content for m in messages if m.type == "system")
    user = next(m.content for m in messages if m.type == "human")
    return ("# SYSTEM MESSAGE\n\n" + system + "\n\n# USER MESSAGE\n\n" + user
            + "\n\n# OUTPUT SCHEMA (reply with one JSON object that validates against this schema)\n\n"
            + json.dumps(bound.model_json_schema(), indent=1))


if __name__ == "__main__":
    main()
