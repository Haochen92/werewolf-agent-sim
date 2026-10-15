"""Play one AI-only Phase 2 game for the step 8 comparison and keep everything the counts need.

Copied from the step 6 capture script (which mirrors Agents.main.run_game's setup and streams the
production way: stream_mode=["updates", "custom"], subgraphs=True, version="v2") and changed in
three ways: every chunk carries the time it arrived, every model call is logged with its node and
its start/end times (so calls and seconds can be attributed to days afterwards), and the final
state is written out as a batch-shaped game record. Memory off, dump off.
Record: evidence/game_play_enhancement/data/phase2_step8_games/README.md.

  poetry run python evaluation/experiments/phase2_step8_capture.py --label game1
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(REPO_ROOT / ".env")

from langchain_core.callbacks import BaseCallbackHandler  # noqa: E402
from pydantic_core import to_jsonable_python  # noqa: E402

from Agents.config import RunConfig, build_runnable_config, normalize_run_config  # noqa: E402
from Agents.graphs.parent import parent_graph_compiled  # noqa: E402
from Agents.llm_factory.accessors import _game_model, game_thinking_level  # noqa: E402
from Agents.memory import store  # noqa: E402
from Agents.memory.persistence import seed_memory_from_config  # noqa: E402
from Agents.observability import EvalCaseSink  # noqa: E402
from Agents.run_fingerprint import runtime_fingerprint  # noqa: E402
from Agents.state import fresh_game_state  # noqa: E402
from Agents.tracing import Metrics  # noqa: E402
from Agents.turn import prompt_log, reads_log  # noqa: E402
from server.game.usage import UsageMeter, game_cost  # noqa: E402
from tests.leak_test import run_leak_tests  # noqa: E402

OUT_DIR = REPO_ROOT / "evidence/game_play_enhancement/data/phase2_step8_games"


class CallLog(BaseCallbackHandler):
    """One row per model call: the graph node that made it, its namespace, start and end time."""

    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.open: dict[UUID, dict] = {}
        self.rows: list[dict] = []

    def on_chat_model_start(self, serialized: dict, messages: list, *, run_id: UUID,
                            metadata: dict | None = None, **kwargs: Any) -> None:
        metadata = metadata or {}
        row = {
            "node": metadata.get("langgraph_node"),
            "checkpoint_ns": metadata.get("checkpoint_ns") or metadata.get("langgraph_checkpoint_ns"),
            "model": metadata.get("ls_model_name"),
            "started": time.time(),
        }
        with self.lock:
            self.open[run_id] = row

    def _close(self, run_id: UUID, ok: bool) -> None:
        with self.lock:
            row = self.open.pop(run_id, None)
            if row is None:
                return
            row["ended"] = time.time()
            row["ok"] = ok
            self.rows.append(row)

    def on_llm_end(self, response: Any, *, run_id: UUID, **kwargs: Any) -> None:
        self._close(run_id, True)

    def on_llm_error(self, error: BaseException, *, run_id: UUID, **kwargs: Any) -> None:
        self._close(run_id, False)


def jsonable(value: Any) -> Any:
    return to_jsonable_python(value, fallback=repr)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--label", required=True, help="file stem under the output folder, e.g. game1")
    ap.add_argument("--out", default=str(OUT_DIR))
    args = ap.parse_args()
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    game_id = f"phase2-step8-{args.label}-{uuid4().hex[:8]}"
    run = normalize_run_config(RunConfig(game_id=game_id, memory_persistence={"dump_enabled": False}))
    seed_memory_from_config(run.memory_persistence, target_store=store)
    meter = UsageMeter()
    call_log = CallLog()
    fingerprint = runtime_fingerprint()
    config = build_runnable_config(run, callbacks=[meter, call_log],
                                   metadata={"runtime_fingerprint": fingerprint})
    metrics = Metrics()
    context = {"metrics": metrics, "eval_sink": EvalCaseSink()}
    prompt_log.clear()
    reads_log.clear()

    model = _game_model()
    manifest = {
        "game_id": game_id,
        "label": args.label,
        "git": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True, cwd=REPO_ROOT).strip(),
        "git_dirty_paths": subprocess.check_output(["git", "status", "--porcelain"], text=True,
                                                   cwd=REPO_ROOT).splitlines(),
        "runtime_fingerprint": fingerprint,
        "langgraph": version("langgraph"),
        "model": model,
        "thinking_level": game_thinking_level(model),
        "memory": "off (memory_config all False, dump off)",
        "run_config": run.model_dump(mode="json"),
        "stream": {"stream_mode": ["updates", "custom"], "subgraphs": True, "version": "v2"},
        "started_at": datetime.now(timezone.utc).isoformat(),
    }

    chunks_path = out_dir / f"{args.label}.chunks.jsonl"
    started = time.time()
    count = 0
    with chunks_path.open("w") as f:
        for part in parent_graph_compiled.stream(
            fresh_game_state(), config=config, context=context,
            stream_mode=["updates", "custom"], subgraphs=True, version="v2",
        ):
            record = {"i": count, "t": time.time(), "type": part["type"], "ns": list(part["ns"]),
                      "data": jsonable(part["data"])}
            f.write(json.dumps(record) + "\n")
            f.flush()
            count += 1
            if count % 25 == 0:
                print(f"[{count}] {round(time.time() - started)} s {part['ns']}", flush=True)
    seconds = round(time.time() - started, 1)

    result = parent_graph_compiled.get_state(config).values
    public_text = " || ".join(
        [m.message for m in result.get("day_channel") or []]
        + [s.summary for s in result.get("day_summaries") or []]
    )
    leaks = run_leak_tests(prompt_log, result.get("roles") or {}, reads_log=reads_log,
                           public_text=public_text)
    raw_metrics = metrics.model_dump(mode="json")
    usage = meter.snapshot()
    game_record = {
        "game_id": game_id,
        "winner": result.get("winner"),
        "current_day": result.get("current_day"),
        "duration_seconds": seconds,
        "roles": result.get("roles"),
        "investigator_results": jsonable(result.get("investigator_results")),
        "day_channel": jsonable(result.get("day_channel")),
        "day_summaries": jsonable(result.get("day_summaries")),
        "day_resolutions": raw_metrics.get("day_resolutions"),
        "night_resolutions": raw_metrics.get("night_resolutions"),
        "humans": [],
        "leak_check": {"passed": not leaks, "leaks": leaks},
    }
    (out_dir / f"{args.label}.record.json").write_text(json.dumps(game_record, indent=1))
    (out_dir / f"{args.label}.calls.json").write_text(json.dumps(call_log.rows, indent=1))
    manifest |= {
        "ended_at": datetime.now(timezone.utc).isoformat(),
        "duration_seconds": seconds,
        "chunks": count,
        "winner": game_record["winner"],
        "days": game_record["current_day"],
        "model_calls": len(call_log.rows),
        "usage": usage,
        "cost_usd": game_cost(usage),
        "leak_check_passed": not leaks,
        "files": {"chunks": chunks_path.name, "record": f"{args.label}.record.json",
                  "calls": f"{args.label}.calls.json"},
    }
    (out_dir / f"{args.label}.manifest.json").write_text(json.dumps(manifest, indent=1))
    print(f"{game_id}: winner {game_record['winner']}, day {game_record['current_day']}, "
          f"{seconds} s, {len(call_log.rows)} calls, cost {manifest['cost_usd']}", flush=True)


if __name__ == "__main__":
    main()
