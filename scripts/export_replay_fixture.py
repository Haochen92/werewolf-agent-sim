"""Wrap a game's durable events in the replay envelope, for a frontend fixture.

The stage's bundled games (frontend/src/stage/fixtures/replay-*.json) are what
``GET /replays/{id}`` returns: a ``ReplayGame`` with every durable event. This builds one
offline, from either source:

- ``--from-golden <jsonl>``: a translator golden (one event per line), e.g.
  tests/fixtures/translator_golden.jsonl.
- ``--from-chunks <chunks.jsonl>``: a captured game's raw stream chunks, run through the
  server's translator the way tests/fixtures/translator_golden.py drives it. A capture with
  a ``_header`` line (notebooks/fixtures) is read by ``load_fixture_chunks``; a batch capture
  (evidence/.../e0N.chunks.jsonl) has no header and is read line by line.

The summary fields (winner, days, ended phase, event count, cast) come from the events by the
server's own ``derive_completion_metadata``, and the whole envelope is validated by the
server's ``ReplayGame``, so a fixture that builds is one the API could have sent.

    poetry run python scripts/export_replay_fixture.py \\
        --from-golden tests/fixtures/translator_golden.jsonl \\
        --game-id phase3-translator-golden-2026-10 \\
        --out frontend/src/stage/fixtures/replay-phase3.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pydantic import TypeAdapter  # noqa: E402

from server.game.translate import Translator  # noqa: E402
from server.schemas import events as ev  # noqa: E402
from server.schemas.replays import ReplayGame  # noqa: E402
from server.storage.game_repository import derive_completion_metadata  # noqa: E402
from tests.fixtures.stream import load_fixture_chunks  # noqa: E402


def read_chunks(path: Path) -> list[dict]:
    """The capture's chunks. A batch capture has no header line; its chunks carry a wall
    time ``t`` the translator does not read."""
    with path.open() as f:
        first = json.loads(f.readline())
    if "_header" in first:
        return load_fixture_chunks(path)
    with path.open() as f:
        return [json.loads(line) for line in f if line.strip()]


def events_from_chunks(chunks: list[dict]) -> list[ev.DurableEvent]:
    """Every event the translator produces for the capture (an AI-only game: no deadlines)."""
    translator = Translator()
    return [e for chunk in chunks for e in translator.translate(chunk)]


def events_from_golden(path: Path) -> list[ev.DurableEvent]:
    adapter = TypeAdapter(ev.DurableGameEvent)
    with path.open() as f:
        return [adapter.validate_python(json.loads(line)) for line in f if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--from-golden", type=Path, help="a translator golden, one event per line")
    source.add_argument("--from-chunks", type=Path, help="a captured game's raw stream chunks")
    parser.add_argument("--game-id", required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--model", default="gemini-3.5-flash-lite")
    parser.add_argument("--memory", action="store_true", help="the game ran with memory on")
    parser.add_argument("--n-humans", type=int, default=0)
    parser.add_argument("--finished-at", default=None,
                        help="ISO time; for --from-chunks the last chunk's wall time by default")
    args = parser.parse_args()

    finished_at = args.finished_at
    if args.from_golden:
        events = events_from_golden(args.from_golden)
    else:
        chunks = read_chunks(args.from_chunks)
        events = events_from_chunks(chunks)
        if finished_at is None and "t" in chunks[-1]:
            finished_at = chunks[-1]["t"]

    meta = derive_completion_metadata(events)
    if meta is None:
        raise SystemExit("the log has no game_started or no game_over: not a finished game")
    replay = ReplayGame(
        game_id=args.game_id,
        finished_at=finished_at,
        n_humans=args.n_humans,
        model=args.model,
        memory=args.memory,
        events=events,
        **meta,
    )
    args.out.write_text(json.dumps(replay.model_dump(mode="json"), separators=(",", ":")) + "\n")
    print(f"wrote {args.out}: {meta['n_events']} events, winner {meta['winner']}, "
          f"{meta['days']} days")


if __name__ == "__main__":
    main()
