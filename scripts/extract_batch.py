"""Extract saved game inputs offline: in Claude Message Batches, or online on Gemini (decisions §11).

Reads extraction inputs (the post-game node's ``extraction_input`` records in a run's case files, or
a backfill file), extracts every dealt role's discussion, vote and night as one batch (each game's
first call direct, to write its prefix to the cache), runs the de-halo pass as a second batch, and
writes ``extracted.jsonl`` (extraction cases, the eval-case format), ``dehalo.jsonl`` and
``summary.json`` (counts, tokens and cost at the catalogue's batch prices). A ``gemini-*`` model runs
the live extractor's path instead, online, with its explicit prefix cache (Gemini batch is not
built). Writing the lessons into a store or a served game's replay is a separate step.

  poetry run python scripts/extract_batch.py --inputs batch_results/extraction_inputs/backfill_2026-10-12.jsonl \\
      --games 286816b0 cc80ecdf --model claude-haiku-5-5 --thinking off --name check_haiku
  ... --dry-run   # count the calls and estimate the input tokens; no model is called
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from Agents.llm_factory.providers import anthropic as claude_structured
from Agents.memory.extraction.offline import (
    cell_calls,
    dehalo_cases,
    extract_cases,
    extract_cases_gemini,
    load_inputs,
)
from Agents.memory.persistence.config import DehaloConfig

OUT = Path("batch_results/extraction_runs")


def _record(metadata: dict, case, kind: str = "postgame_extraction") -> dict:
    return {"kind": kind, "id": "", "name": case.span_name, "trace_id": "", "parent_observation_id": None,
            "metadata": metadata, "input": None, "output": {"extraction_case": case.model_dump(mode="json")}}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--inputs", nargs="+", required=True, help="case files holding extraction inputs")
    parser.add_argument("--games", nargs="*", default=[], help="game id prefixes (default: every input)")
    parser.add_argument("--sources", nargs="*", default=[],
                        help="keep inputs whose recorded source contains one of these (e.g. v8_seed)")
    parser.add_argument("--model", default="claude-haiku-5-5")
    parser.add_argument("--thinking", default=None, help="off, or an effort level (low..max); default: the model's")
    parser.add_argument("--no-warm", action="store_true", help="send every call in the batch")
    parser.add_argument("--no-dehalo", action="store_true")
    parser.add_argument("--name", default=time.strftime("run_%Y%m%d_%H%M%S"))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    loaded = [(m, c) for m, c in load_inputs(args.inputs)
              if (not args.games or any(c.game_id.startswith(g) for g in args.games))
              and (not args.sources or any(src in m.get("source", "") for src in args.sources))]
    cases = [c for _m, c in loaded]
    calls = {c.game_id: cell_calls(c) for c in cases}
    n_calls = sum(len(v[1]) for v in calls.values())
    prefix_tokens = sum(len(v[0]) for v in calls.values()) // 4
    tail_tokens = sum(len(p) - len(v[0]) for v in calls.values() for _r, _ph, p, _s in v[1]) // 4
    print(f"{len(cases)} games, {n_calls} calls; about {prefix_tokens:,} prefix tokens (one write per game) "
          f"and {tail_tokens:,} uncached tail tokens")
    if args.dry_run:
        return

    started = time.time()
    gemini_usage = None
    if args.model.startswith("gemini"):
        import os
        os.environ["GOOGLE_GENAI_PRO_MODEL"] = args.model
        extracted, gemini_usage = extract_cases_gemini(cases)
    else:
        extracted = extract_cases(cases, args.model, args.thinking, warm=not args.no_warm)
    dehalo_config = DehaloConfig(enabled=not args.no_dehalo)
    dehalo = dehalo_cases(cases, extracted, dehalo_config)

    out = OUT / args.name
    out.mkdir(parents=True, exist_ok=True)
    rows, dehalo_rows = [], []
    for metadata, case in loaded:
        result = extracted[case.game_id]
        model_used = f"{args.model} (thinking: {args.thinking or 'default'})" + (
            f" (missing: {','.join(sorted(result['missing']))})" if result["missing"] else "")
        filled = case.model_copy(update={
            "observations": [o.model_dump(mode="json") for o in result["observations"]], "model_used": model_used})
        rows.append(_record({**metadata, "extraction_model": args.model, "thinking": args.thinking}, filled))
        if case.game_id in dehalo:
            dehalo_rows.append({"kind": "dehalo", "game_id": case.game_id, "output": {"dehalo": dehalo[case.game_id]}})
    (out / "extracted.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    (out / "dehalo.jsonl").write_text("".join(json.dumps(r) + "\n" for r in dehalo_rows))
    summary = {
        "games": len(cases), "calls": n_calls, "model": args.model, "thinking": args.thinking,
        "warm": not args.no_warm, "dehalo_model": dehalo_config.model if dehalo_config.enabled else None,
        "observations": {c.game_id: len(extracted[c.game_id]["observations"]) for c in cases},
        "missing": {g: r["missing"] for g, r in extracted.items() if r["missing"]},
        "usage": {f"{m}{' (batch)' if b else ''}": u for (m, b), u in claude_structured.usage_by_model.items()},
        "gemini_usage": gemini_usage,
        "cost_usd": claude_structured.usage_cost_usd(), "minutes": round((time.time() - started) / 60, 1),
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps({k: summary[k] for k in ("games", "calls", "missing", "usage", "cost_usd", "minutes")}, indent=2))


if __name__ == "__main__":
    main()
