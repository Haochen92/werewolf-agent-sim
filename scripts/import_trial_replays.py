"""Add captured AI-only games to the replay archive, as if the server had played them.

A capture (``evaluation/experiments/phase3_capture.py``) holds a game's raw stream chunks and a
manifest with its model and recorded token usage. Each is run through the server's translator,
written with the server's repository and completed by it, so a game that imports is one the
replay API serves like any other: its winner and length from its events, its cost and average AI
time from its usage, its dates from the capture's own wall times. A game's id is derived from its
capture path, so importing twice changes nothing.

    poetry run python scripts/import_trial_replays.py --dry-run \\
        evidence/game_play_enhancement/data/phase3_balance_4/e0*.chunks.jsonl
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dotenv import load_dotenv  # noqa: E402

from scripts.export_replay_fixture import events_from_chunks, read_chunks  # noqa: E402
from server.config import ServerSettings  # noqa: E402
from server.db import Database  # noqa: E402
from server.storage.game_repository import GameRepository, derive_completion_metadata  # noqa: E402


def game_id_for(chunks_path: Path) -> str:
    """The same id for the same capture on every run."""
    rel = chunks_path.resolve().relative_to(REPO_ROOT)
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"werewolf-trial-capture/{rel}"))


def _at(t: float) -> datetime:
    return datetime.fromtimestamp(t, tz=timezone.utc)


async def import_one(repo: GameRepository, chunks_path: Path, dry_run: bool) -> str:
    manifest = json.loads(chunks_path.with_name(
        chunks_path.name.replace(".chunks.jsonl", ".manifest.json")).read_text())
    chunks = read_chunks(chunks_path)
    events = events_from_chunks(chunks)
    meta = derive_completion_metadata(events)
    if meta is None:
        return f"skip {chunks_path}: no clean ending"
    game_id = game_id_for(chunks_path)
    started, finished = _at(chunks[0]["t"]), _at(chunks[-1]["t"])
    line = (f"{game_id} {chunks_path.parent.name}/{chunks_path.name.split('.')[0]} "
            f"{manifest['model']} {meta['winner']} {meta['days']} days {meta['n_events']} events "
            f"{started:%Y-%m-%d %H:%M}")
    if dry_run:
        return "would import " + line
    if await repo.load_game(game_id) is not None:
        return "already there " + line
    ok = await repo.create_game(game_id, status="running", model=manifest["model"],
                                usage=manifest.get("usage"), created_at=started)
    if not ok or not await repo.record_events(game_id, events):
        return "FAILED " + line
    await repo.complete_game(game_id, events, n_humans=0)
    await repo.update_game(game_id, finished_at=finished)
    row = await repo.load_game(game_id)
    return f"{row.status if row else 'missing'} " + line


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("chunks", nargs="+", type=Path, help="captures (*.chunks.jsonl)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    load_dotenv(REPO_ROOT / ".env")
    database = Database(ServerSettings().replay_database_url)
    await database.startup()
    try:
        repo = GameRepository(database)
        for path in args.chunks:
            print(await import_one(repo, path, args.dry_run), flush=True)
    finally:
        await database.close()


if __name__ == "__main__":
    asyncio.run(main())
