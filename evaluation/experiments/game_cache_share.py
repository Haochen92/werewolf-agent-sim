"""How much of each game's input a provider served from cache, read from the games' Langfuse traces.

Record: evidence/caching/experiment_log.md (§11, the first whole-game cached shares). Read-only, no
model calls. For each session it sums every generation's tokens and splits input three ways: read from
cache, written to cache, and neither. Providers name these differently in the traces, so each name is
mapped to one of the three (Anthropic's raw names appear on Claude seats traced before 2026-10-12).

  poetry run python evaluation/experiments/game_cache_share.py batch_results/v8_luna_memory/run2/game_*.jsonl
  poetry run python evaluation/experiments/game_cache_share.py --session v8_gate_haiku_0_all_enabled

Games that share a session (two per session in some batch runs) come out as one row. Each row is also
split by call type (discussion, vote, night, lookup, the day summary, the echo gate and opening filter),
read from the name of the span each model call sits under.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

READ = ("input_cache_read", "cache_read_input_tokens", "input_cached_tokens", "prompt_cache_hit_tokens",
        "cached_content_token_count")
WRITTEN = ("input_cache_creation", "cache_creation_input_tokens", "input_ephemeral_5m_input_tokens",
           "input_ephemeral_1h_input_tokens")
UNCACHED = ("input",)
OUTPUT = ("output", "output_reasoning", "output_reasoning_tokens")


def _session_ids(paths: list[str]) -> list[str]:
    from evaluation.src.data.sources.langfuse import read_session_ids_from_batch_results

    ids: list[str] = []
    for p in paths:
        ids += [s for s in read_session_ids_from_batch_results(Path(p)) if s not in ids]
    return ids


def _generations(api, trace_id: str) -> list:
    """The trace's model calls, with their token counts (filtered by type: an unfiltered listing of
    a long game's trace is refused with a 422)."""
    from evaluation.src.data.sources.langfuse import _field

    out, page = [], 1
    while True:
        data = _field(api.observations.get_many(trace_id=trace_id, type="GENERATION", page=page, limit=100),
                      "data", [])
        out += data
        if len(data) < 100:
            return out
        page += 1


def call_type(span: str) -> str:
    """The kind of call a model call was, from the name of the span it sits under (the turn's span is
    named after its output channel and player; a lookup's after the situation summary)."""
    if span.startswith("situation_summary"):
        return "lookup"
    if span.startswith("day_channel"):
        return "discussion"
    if span.startswith("day_votes"):
        return "vote"
    if span.startswith(("wolf_channel", "kill_target")) or span.endswith("_target") \
            or span in ("conceal", "speculator_pick") or "_target_player" in span:
        return "night"
    if span.startswith(("echo_gate", "opening_filter")):
        return "gate/filter"
    if span == "RunnableSequence":
        return "day summary"
    return "other"


def session_share(session_id: str) -> dict:
    """Calls, input tokens and the read / written / neither split for one session, per model."""
    from evaluation.src.data.sources.langfuse import (_field, _require_langfuse_api, enumerate_observations,
                                                      fetch_trace_ids_for_session_id)

    api = _require_langfuse_api()
    by_model: dict[str, dict] = defaultdict(lambda: defaultdict(int))
    by_call: dict[tuple[str, str], dict] = defaultdict(lambda: defaultdict(int))
    for trace_id in fetch_trace_ids_for_session_id(session_id):
        # span names (for the call type) from the whole trace; token counts from the model calls
        names = {o["id"]: o["name"] or "" for o in enumerate_observations(trace_id)}
        for g in _generations(api, trace_id):
            model = _field(g, "model") or "?"
            kind_of_call = call_type(names.get(_field(g, "parent_observation_id"), ""))
            for row in (by_model[model], by_call[(model, kind_of_call)]):
                row["calls"] += 1
            for name, n in (_field(g, "usage_details") or {}).items():
                kind = "read" if name in READ else "written" if name in WRITTEN else \
                    "neither" if name in UNCACHED else "output" if name in OUTPUT else None
                if kind:
                    by_model[model][kind] += int(n or 0)
                    by_call[(model, kind_of_call)][kind] += int(n or 0)
    out = {}
    for model, r in by_model.items():
        out[model] = {**_split(r, model), "by_call": {
            call: _split(c, model) for (m, call), c in sorted(by_call.items()) if m == model}}
    return out


def _split(r: dict, model: str) -> dict:
    """The counts, the input shares, and the cost at today's catalogue prices (a write at its premium)."""
    from datetime import datetime, timezone

    from Agents.llm_factory.pricing import cost_usd

    total = r["read"] + r["written"] + r["neither"]
    usd = cost_usd(model, datetime.now(timezone.utc), input=total, cached=r["read"], written=r["written"],
                   output=r["output"])
    return {"calls": r["calls"], "input": total, **{k: r[k] for k in ("read", "written", "neither", "output")},
            **{f"{k}_share": round(r[k] / total, 3) if total else None for k in ("read", "written", "neither")},
            "cost_usd": round(usd, 4) if usd is not None else None}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("batch_results", nargs="*", help="run_batch JSONL files; their session ids are read")
    ap.add_argument("--session", action="append", default=[], help="a Langfuse session id (repeatable)")
    args = ap.parse_args()
    sessions = args.session + _session_ids(args.batch_results)
    print(json.dumps({s: session_share(s) for s in sessions}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
