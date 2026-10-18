"""Screen: a persona line in the seat's own discussion prompt, so the model that reasons also speaks
in a voice (2026-10-18; the follow-up to the voice rewrite screen, which drifted the facts in about one
rewrite in five: evidence/game_play_enhancement/data/voice_rewrite/README.md).

Record: evidence/game_play_enhancement/data/persona_line/ (README there). Generation only; the
samples are judged blind, separately.

The day-discussion cases of the frozen Haiku turn bench (haiku_effort_replay/turn_cases.jsonl),
rebuilt by the replay bench (``turn_payload`` / ``turn_template``) in "full" deduction mode, are
sampled in four arms: no persona (twice, so two plain samples give the sampling-noise baseline) and
each of three voices (once). The persona paragraph goes right after the tone block, in the seat's
part of the prompt (after the cache boundary; a seat's voice would be fixed for its game). Nothing
else differs between the arms.

  GOOGLE_GENAI_MODEL=anthropic/claude-haiku-5-5 GOOGLE_GENAI_THINKING_LEVEL=low GAME_LLM_ATTEMPTS=1 \
    GAME_LLM_TIMEOUT_S=180 LANGFUSE_TRACING_ENABLED=false \
    poetry run python evaluation/experiments/persona_line_screen.py           # sample
  poetry run python evaluation/experiments/persona_line_screen.py --packets # judging packets
"""

from __future__ import annotations

import json
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from evaluation.src.replay.hallucination_bench import _usage_totals, turn_payload, turn_template

OUT = Path("evidence/game_play_enhancement/data/persona_line")
CASES = Path("evidence/reasoning_failures/data/haiku_effort_replay/turn_cases.jsonl")
N_CASES = 15
SEED = 20261018
MAX_CALLS = 90

PERSONAS = {
    "blunt": "Blunt and brief. Short sentences, no pleasantries, gets straight to the point.",
    "warm": "Warm and chatty. Talks to the others like friends at a table, with a little humour.",
    "dry": "Dry and understated, with a wry, slightly sarcastic edge.",
}
"""The same three voices as the rewrite screen."""
ARMS = [("plain", 0), ("plain", 1), ("blunt", 0), ("warm", 0), ("dry", 0)]



def persona_input(prompt_input: dict, persona: str) -> dict:
    """The turn's prompt input with the voice in the template's slot (Agents/prompts/voices.py); the
    slot did not exist when the screen ran, and filling it gives the same prompt the screen sent."""
    from Agents.prompts.voices import PERSONA_PARAGRAPH

    if persona == "plain":
        return prompt_input
    return {**prompt_input, "persona_paragraph": PERSONA_PARAGRAPH.format(voice=PERSONAS[persona])}


def cases() -> list[dict]:
    rows = [json.loads(line) for line in CASES.read_text().splitlines() if line.strip()]
    return sorted(random.Random(SEED).sample(rows, N_CASES), key=lambda c: c["case_id"])


def sample() -> None:
    from langchain_core.callbacks import UsageMetadataCallbackHandler

    from Agents.llm_factory import get_llm
    from Agents.llm_factory.accessors import _game_model, game_thinking_level
    from Agents.llm_factory.pricing import cost_usd
    from Agents.prompts.prompt_inputs import build_agent_prompt_input
    from Agents.turn.action_space import output_schema_with_legal_targets, valid_targets_for_action

    model = _game_model()
    assert model == "anthropic/claude-haiku-5-5" and game_thinking_level(model) == "low", (model,)
    OUT.mkdir(parents=True, exist_ok=True)
    calls, total = 0, 0.0
    with (OUT / "samples.jsonl").open("w") as fh:
        for case in cases():
            payload = {**turn_payload(case), "deduction_mode": "full"}
            template, schema, key = turn_template(case, payload)
            bound = output_schema_with_legal_targets(schema, key, valid_targets_for_action(payload, key))
            prompt_input = build_agent_prompt_input(payload)
            for persona, i in ARMS:
                if calls >= MAX_CALLS:
                    raise SystemExit(f"call cap {MAX_CALLS} reached")
                calls += 1
                chain = template | get_llm().with_structured_output(bound)
                usage, started, out, err = UsageMetadataCallbackHandler(), time.monotonic(), None, ""
                try:
                    out = chain.invoke(persona_input(prompt_input, persona), config={"callbacks": [usage]})
                except Exception as e:  # recorded; the sample counts as invalid
                    err = str(e)[:300]
                tokens = _usage_totals(usage, time.monotonic() - started)
                written = sum((d.get(k) or 0) for u in usage.usage_metadata.values()
                              for d in [u.get("input_token_details") or {}]
                              for k in ("cache_creation", "ephemeral_5m_input_tokens", "ephemeral_1h_input_tokens"))
                cost = cost_usd(model.removeprefix("anthropic/"), datetime.now(timezone.utc), input=tokens["input"],
                                cached=tokens["cached"], output=tokens["output"], written=written) or 0.0
                total += cost
                row = {"case_id": case["case_id"], "role": case["role"], "speaker": case["speaker"],
                       "persona": persona, "sample": i, "valid": out is not None, "error": err}
                if out is not None:
                    row |= {"pass_turn": out.pass_turn, "message": out.message, "claim": out.claim,
                            "claimed_night_actions": [c.model_dump() for c in out.claimed_night_actions],
                            "updated_strategy": out.updated_strategy}
                row["usage"] = {**tokens, "cache_written": written, "cost_usd": round(cost, 6)}
                fh.write(json.dumps(row) + "\n")
                fh.flush()
                print(f"{case['case_id'][:8]} {persona}#{i}: valid={row['valid']} "
                      f"pass={row.get('pass_turn')} {err[:60]} ${cost:.4f}", flush=True)
    print(f"{calls} calls, ${total:.4f}")


def packets(judges: int = 2) -> None:
    """Naturalness: each voiced message against the case's first plain one, blind X/Y. Stance: the same
    pairs plus plain against plain (the sampling-noise baseline), blind A/B. Pairs need two messages."""
    rng = random.Random(SEED)
    rows = [json.loads(line) for line in (OUT / "samples.jsonl").read_text().splitlines()]
    spoken = {(r["case_id"], r["persona"], r["sample"]): r["message"] for r in rows
              if r["valid"] and not r["pass_turn"] and (r["message"] or "").strip()}
    pairs = []
    for case_id in sorted({r["case_id"] for r in rows}):
        plain = spoken.get((case_id, "plain", 0))
        if plain is None:
            continue
        for persona in ("plain", *PERSONAS):
            other = spoken.get((case_id, persona, 1 if persona == "plain" else 0))
            if other is not None:
                pairs.append({"case_id": case_id, "persona": persona, "plain": plain, "other": other})
    rng.shuffle(pairs)
    key, natural, stance = {}, [[] for _ in range(judges)], [[] for _ in range(judges)]
    for n, pair in enumerate(pairs):
        name = f"q{n:02d}"
        first_is_other = rng.random() < 0.5
        key[name] = {"case_id": pair["case_id"], "persona": pair["persona"],
                     "first": "other" if first_is_other else "plain"}
        a, b = (pair["other"], pair["plain"]) if first_is_other else (pair["plain"], pair["other"])
        if pair["persona"] != "plain":
            natural[n % judges].append(f"### {name}\nX: {a}\n\nY: {b}\n")
        stance[n % judges].append(f"### {name}\nA: {a}\n\nB: {b}\n")
    (OUT / "blind_key.json").write_text(json.dumps(key, indent=1))
    for j in range(judges):
        (OUT / f"naturalness_packet_{j + 1}.md").write_text("\n".join(natural[j]))
        (OUT / f"stance_packet_{j + 1}.md").write_text("\n".join(stance[j]))


if __name__ == "__main__":
    if sys.argv[1:] == ["--packets"]:
        packets()
    else:
        sample()
