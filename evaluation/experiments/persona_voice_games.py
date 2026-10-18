"""Before/after games for the speaking voices (RunConfig.persona_voices; owner, 2026-10-18): do the AI
seats still reason as well when every AI seat talks in its puppet's voice?

Record: evidence/game_play_enhancement/data/persona_voice_games/ (README there). One game per call, in
its own process: the in-memory checkpointer is keyed by the game id, and a pair's two arms share it,
so both deal the same roles and seats (the game id is the deal's seed). Memory off, deductions "full"
(the default), the live site's model and thinking level.

Writes, per game, under --out:
  <label>.capture.json.gz   {"prompt_log", "reads_log", "final_state"}: the server's capture format,
                            so the census and the read scoring read it as they read a served game
  <label>.manifest.json     git, fingerprint, model, the run config, usage, cost, winner, leak check

  GOOGLE_GENAI_MODEL=anthropic/claude-haiku-5-5 GOOGLE_GENAI_THINKING_LEVEL=low LANGFUSE_TRACING_ENABLED=false \
    poetry run python -m evaluation.experiments.persona_voice_games --game-id voices-01 --voices on
"""

from __future__ import annotations

import argparse
import gzip
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from evaluation.experiments.phase3_capture import REPO_ROOT, CallLog, jsonable

from Agents.config import RunConfig, build_runnable_config, normalize_run_config
from Agents.graphs.parent import parent_graph_compiled
from Agents.llm_factory.accessors import _game_model, game_thinking_level
from Agents.observability import EvalCaseSink
from Agents.run_fingerprint import runtime_fingerprint
from Agents.state import fresh_game_state
from Agents.tracing import Metrics
from Agents.turn import prompt_log, reads_log
from server.game.usage import UsageMeter, game_cost
from tests.leak_test import leak_inputs, run_leak_tests

OUT_DIR = REPO_ROOT / "evidence/game_play_enhancement/data/persona_voice_games"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--game-id", required=True, help="the pair's game id: the deal's seed")
    ap.add_argument("--voices", choices=("on", "off"), required=True)
    ap.add_argument("--out", default=str(OUT_DIR))
    args = ap.parse_args()
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    label = f"{args.game_id}.{args.voices}"

    model = _game_model()
    assert model == "anthropic/claude-haiku-5-5" and game_thinking_level(model) == "low", (model,)
    run = normalize_run_config(RunConfig(game_id=args.game_id, persona_voices=args.voices == "on",
                                         memory_persistence={"dump_enabled": False}))
    meter, call_log, fingerprint = UsageMeter(), CallLog(), runtime_fingerprint()
    config = build_runnable_config(run, callbacks=[meter, call_log], metadata={"runtime_fingerprint": fingerprint})
    metrics = Metrics()
    prompt_log.clear()
    reads_log.clear()

    started = time.time()
    for _ in parent_graph_compiled.stream(fresh_game_state(), config=config,
                                          context={"metrics": metrics, "eval_sink": EvalCaseSink()},
                                          stream_mode=["updates"], subgraphs=True, version="v2"):
        pass
    seconds = round(time.time() - started, 1)

    result = parent_graph_compiled.get_state(config).values
    public_text = " || ".join([m.message for m in result.get("day_channel") or []]
                              + [s.summary for s in result.get("day_summaries") or []]
                              + [w.message for w in result.get("wolf_channel") or []])
    leaks = run_leak_tests(prompt_log, result.get("roles") or {}, reads_log=reads_log,
                           public_text=public_text, **leak_inputs(result))
    final_state = jsonable({**result, "day_resolutions": metrics.model_dump(mode="json").get("day_resolutions"),
                            "night_resolutions": metrics.model_dump(mode="json").get("night_resolutions")})
    with gzip.open(out_dir / f"{label}.capture.json.gz", "wt") as f:
        json.dump({"prompt_log": jsonable(list(prompt_log)), "reads_log": jsonable(list(reads_log)),
                   "final_state": final_state}, f)
    usage = meter.snapshot()
    manifest = {
        "game_id": args.game_id, "voices": args.voices, "label": label,
        "git": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True, cwd=REPO_ROOT).strip(),
        "runtime_fingerprint": fingerprint, "model": model, "thinking_level": game_thinking_level(model),
        "run_config": run.model_dump(mode="json"),
        "ended_at": datetime.now(timezone.utc).isoformat(), "duration_seconds": seconds,
        "winner": result.get("winner"), "days": result.get("current_day"), "lineup": result.get("lineup"),
        "model_calls": len(call_log.rows), "usage": usage, "cost_usd": game_cost(usage),
        "leak_check": {"passed": not leaks, "leaks": leaks},
    }
    (out_dir / f"{label}.manifest.json").write_text(json.dumps(manifest, indent=1))
    print(f"{label}: winner={manifest['winner']} days={manifest['days']} {seconds}s ${manifest['cost_usd']}")


if __name__ == "__main__":
    main()
