"""How much of each game's input a provider served from cache, read from the games' Langfuse traces.

Record: evidence/caching/experiment_log.md (§11, the first whole-game cached shares). Read-only, no
model calls. For each session it sums every generation's tokens and splits input three ways: read from
cache, written to cache, and neither. Providers name these differently in the traces, so each name is
mapped to one of the three (Anthropic's raw names appear on Claude seats traced before 2026-10-12).

  poetry run python evaluation/experiments/game_cache_share.py batch_results/v8_luna_memory/run2/game_*.jsonl
  poetry run python evaluation/experiments/game_cache_share.py --session v8_gate_haiku_0_all_enabled

Games that share a session (two per session in some batch runs) come out as one row.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

READ = ("input_cache_read", "cache_read_input_tokens", "input_cached_tokens", "prompt_cache_hit_tokens",
        "cached_content_token_count")
WRITTEN = ("input_cache_creation", "cache_creation_input_tokens")
UNCACHED = ("input",)


def _session_ids(paths: list[str]) -> list[str]:
    from evaluation.src.data.sources.langfuse import read_session_ids_from_batch_results

    ids: list[str] = []
    for p in paths:
        ids += [s for s in read_session_ids_from_batch_results(Path(p)) if s not in ids]
    return ids


def _generations(api, trace_id: str):
    from evaluation.src.data.sources.langfuse import _field

    page = 1
    while True:
        data = _field(api.observations.get_many(trace_id=trace_id, type="GENERATION", page=page, limit=100),
                      "data", [])
        yield from data
        if len(data) < 100:
            break
        page += 1


def session_share(session_id: str) -> dict:
    """Calls, input tokens and the read / written / neither split for one session, per model."""
    from evaluation.src.data.sources.langfuse import (_field, _require_langfuse_api,
                                                      fetch_trace_ids_for_session_id)

    api = _require_langfuse_api()
    by_model: dict[str, dict] = defaultdict(lambda: defaultdict(int))
    for trace_id in fetch_trace_ids_for_session_id(session_id):
        for g in _generations(api, trace_id):
            row = by_model[_field(g, "model") or "?"]
            row["calls"] += 1
            for name, n in (_field(g, "usage_details") or {}).items():
                kind = "read" if name in READ else "written" if name in WRITTEN else \
                    "neither" if name in UNCACHED else None
                if kind:
                    row[kind] += int(n or 0)
    out = {}
    for model, r in by_model.items():
        total = r["read"] + r["written"] + r["neither"]
        out[model] = {"calls": r["calls"], "input": total, **{
            k: r[k] for k in ("read", "written", "neither")},
            **{f"{k}_share": round(r[k] / total, 3) if total else None for k in ("read", "written", "neither")}}
    return out


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
