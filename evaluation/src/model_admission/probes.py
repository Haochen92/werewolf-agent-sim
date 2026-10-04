"""The admission run's probes: structured output per calling mode, and prompt caching.

Each call's tokens come from LangChain's usage metadata (``cache_read`` is the provider's cached
input, ``reasoning`` its thinking tokens, billed as output), so the record says what each mode
actually did rather than what it was configured to do: a thinking level a provider ignores
shows up as zero reasoning tokens.
"""

from __future__ import annotations

import copy
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from langchain_core.callbacks import UsageMetadataCallbackHandler

from Agents.llm_factory import create_chat_model
from evaluation.src.model_admission.seat_schemas import SEAT_SCHEMAS, TABLE, reply_problem

MODE_ORDER = ("native", "forced_tool", "json_schema", "auto_tool", "json_mode")


def modes_for(model: str) -> list[str]:
    """The calling modes a model's protocol allows: Gemini only has its own constrained output."""
    return ["native"] if "/" not in model else ["forced_tool", "json_schema", "auto_tool", "json_mode"]


def _llm(model: str, mode: str, thinking_level: str | None):
    kwargs = {} if mode == "native" else {"structured_mode": mode}
    return create_chat_model(model, temperature=1.0, thinking_level=thinking_level, **kwargs)


def _usage(handler: UsageMetadataCallbackHandler, seconds: float) -> dict[str, float]:
    totals = {"input": 0, "cached": 0, "output": 0, "reasoning": 0}
    for u in handler.usage_metadata.values():
        totals["input"] += u.get("input_tokens", 0)
        totals["cached"] += (u.get("input_token_details") or {}).get("cache_read", 0) or 0
        totals["output"] += u.get("output_tokens", 0)
        totals["reasoning"] += (u.get("output_token_details") or {}).get("reasoning", 0) or 0
    return {**totals, "seconds": round(seconds, 2)}


def _mean(rows: list[dict], key: str) -> float:
    return round(sum(r[key] for r in rows) / len(rows), 1) if rows else 0.0


# --- 1. structured output -------------------------------------------------------------------

def probe_structured(model: str, mode: str, thinking_level: str | None, samples: int,
                     workers: int = 4) -> dict[str, Any]:
    """Every seat schema ``samples`` times under one calling mode."""
    llm = _llm(model, mode, thinking_level)

    def one(job: tuple) -> dict[str, Any]:
        (schema, role_line, field, tokens), i = job
        usage, started = UsageMetadataCallbackHandler(), time.monotonic()
        try:
            out = llm.with_structured_output(schema).invoke(TABLE + role_line, config={"callbacks": [usage]})
            problem = reply_problem(schema, out, field, tokens)
        except Exception as e:  # a 400 or a parse failure: the mode failed this call
            problem = f"{type(e).__name__}: {str(e)[:240]}"
        return {"schema": schema.__name__, "sample": i, "problem": problem,
                **_usage(usage, time.monotonic() - started)}

    jobs = [(row, i) for row in SEAT_SCHEMAS for i in range(samples)]
    with ThreadPoolExecutor(max_workers=workers) as ex:
        calls = list(ex.map(one, jobs))
    failures = [c for c in calls if c["problem"]]
    return {
        "mode": mode,
        "passed": f"{len(calls) - len(failures)}/{len(calls)}",
        "all_passed": not failures,
        "failures": [{"schema": c["schema"], "problem": c["problem"]} for c in failures],
        "mean_per_call": {k: _mean(calls, k) for k in ("input", "cached", "output", "reasoning", "seconds")},
    }


def recommend_mode(results: list[dict[str, Any]], thinking_level: str | None) -> tuple[str | None, str]:
    """The mode to play on, and why. A mode must pass every call; when thinking is asked for, one
    that actually reasons beats one that silently doesn't; otherwise the earlier mode in
    MODE_ORDER (the provider's own enforcement before our parsing)."""
    passing = sorted((r for r in results if r["all_passed"]), key=lambda r: MODE_ORDER.index(r["mode"]))
    if not passing:
        best = max(results, key=lambda r: int(r["passed"].split("/")[0]))
        return None, f"no mode passed every call (best: {best['mode']} at {best['passed']})"
    wants_thinking = thinking_level not in (None, "minimal")
    reasoning = [r for r in passing if r["mean_per_call"]["reasoning"] > 0]
    if wants_thinking and reasoning:
        pick = reasoning[0]
        skipped = [r["mode"] for r in passing if r not in reasoning]
        why = f"passed every call and reasons ({pick['mean_per_call']['reasoning']} tokens a call)"
        return pick["mode"], why + (f"; {', '.join(skipped)} also passed but did not reason" if skipped else "")
    pick = passing[0]
    why = "passed every call"
    if wants_thinking:
        why += f"; no passing mode reasoned at thinking level {thinking_level!r}"
    return pick["mode"], why


# --- 2. caching -----------------------------------------------------------------------------

_FILLER = ("Table rule {i}: every seat speaks in turn, answers what was just said, and keeps the "
           "record of votes and deaths exactly as the moderator announced it. ")


def probe_cache_floor(model: str, sizes: list[int], wait_s: float) -> list[dict[str, Any]]:
    """For each target size, an identical prompt sent until the provider serves part of it from
    cache (at most three sends, waiting between them, since a cache takes a moment to build).
    A fresh nonce leads each prompt so no earlier probe's cache can answer for it."""
    llm = _llm(model, "native" if "/" not in model else "forced_tool", "minimal")
    rows = []
    for size in sizes:
        text = f"[probe {uuid.uuid4().hex}] "
        i = 0
        while len(text) < size * 4:  # ~4 characters a token; the provider's count is recorded
            text += _FILLER.format(i=i)
            i += 1
        messages = [("system", text), ("user", "Reply with the single word OK.")]
        sends = []
        for attempt in range(3):
            usage, started = UsageMetadataCallbackHandler(), time.monotonic()
            llm.invoke(messages, config={"callbacks": [usage]})
            sends.append(_usage(usage, time.monotonic() - started))
            if (attempt and sends[-1]["cached"]) or attempt == 2:
                break
            time.sleep(wait_s * (attempt + 1))
        rows.append({"target_tokens": size, "input_tokens": sends[0]["input"],
                     "cached_tokens": max(s["cached"] for s in sends[1:]), "sends": len(sends)})
    return rows


def _alive(state: dict) -> list[str]:
    return list(dict.fromkeys([*state.get("surviving_villagers", []), *state.get("surviving_wolves", [])]))


def turn_variants(case: dict) -> dict[str, dict]:
    """Three real prompts from one frozen discussion case: the speaker's turn, the same speaker's
    next turn after one more message, and another living seat at the first moment."""
    state = case["state"]
    others = [p for p in _alive(state) if p != case["speaker"]]
    next_turn = copy.deepcopy(case)
    channel = next_turn["state"]["day_channel"]
    channel.append({
        "player": others[0], "day": state["current_day"], "passed": False, "addressed_targets": [],
        "firing_reason": {"owes": [], "tier": "proactive"},
        "seq": max((m.get("seq", 0) for m in channel), default=-1) + 1,
        "message": "I want to hear from everyone who has not spoken yet today before we vote.",
    })
    other_seat = copy.deepcopy(case)
    other_seat["speaker"], other_seat["role"] = others[-1], state["roles"][others[-1]]
    other_seat["firing_reason"] = {"owes": [], "tier": "proactive"}
    return {"first": case, "next_turn": next_turn, "other_seat": other_seat}


def _render(case: dict) -> tuple[Any, type, dict]:
    """The production template, its legal-target schema and its input for one discussion turn."""
    from Agents.nodes.day.actors import DISCUSS_PROMPTS
    from Agents.prompts.prompt_inputs import build_agent_prompt_input
    from Agents.schemas import DayDiscussOutput
    from Agents.turn.action_space import output_schema_with_legal_targets, valid_targets_for_action
    from evaluation.src.replay.hallucination_bench import turn_payload

    payload = turn_payload(case)
    bound = output_schema_with_legal_targets(
        DayDiscussOutput, "day_channel", valid_targets_for_action(payload, "day_channel"))
    return DISCUSS_PROMPTS[case["role"]], bound, build_agent_prompt_input(payload)


def _text(template: Any, prompt_input: dict) -> str:
    return "\n".join(f"{m.type}: {m.content}" for m in template.invoke(prompt_input).to_messages())


def _shared_prefix(a: str, b: str) -> int:
    n = 0
    for x, y in zip(a, b):
        if x != y:
            break
        n += 1
    return n


def probe_real_prompts(model: str, mode: str, thinking_level: str | None, case: dict,
                       wait_s: float) -> dict[str, Any]:
    """Send the three variants in order, waiting between them. ``cached`` on the next turn is what
    the provider reused from the first prompt; on the other seat, what two seats share.
    ``shared_prefix_est`` is our own count: the characters two rendered prompts share from the
    start, in tokens at the first prompt's characters-per-token (the schema, sent as a tool or
    instruction, is not in the text, so this is an estimate)."""
    llm = _llm(model, mode, thinking_level)
    rendered = {name: _render(c) for name, c in turn_variants(case).items()}
    texts = {name: _text(t, i) for name, (t, _, i) in rendered.items()}
    out: dict[str, Any] = {"case_id": case["case_id"]}
    for k, (name, (template, schema, prompt_input)) in enumerate(rendered.items()):
        if k:
            time.sleep(wait_s)
        usage, started = UsageMetadataCallbackHandler(), time.monotonic()
        error = None
        try:
            (template | llm.with_structured_output(schema)).invoke(prompt_input, config={"callbacks": [usage]})
        except Exception as e:  # tokens were still billed; the call is kept for its usage
            error = f"{type(e).__name__}: {str(e)[:200]}"
        out[name] = {**_usage(usage, time.monotonic() - started), "error": error}
    tokens_per_char = out["first"]["input"] / max(1, len(texts["first"]))
    for name in ("next_turn", "other_seat"):
        out[name]["shared_prefix_est"] = round(_shared_prefix(texts["first"], texts[name]) * tokens_per_char)
    return out
