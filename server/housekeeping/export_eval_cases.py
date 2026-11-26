"""Write the stored evaluation cases of served games to files the evaluation code reads.

A finished served game saves its evaluation cases in the database
(server/storage/eval_cases.py). The evaluation code reads cases from files laid out the way a
batch run writes them: one JSON-lines file per game, and one results file whose records point
at those files. This command writes that layout into a folder:

    <out>/games.jsonl                 one record per game, with ``eval_cases_path``
    <out>/eval_cases/<game_id>.jsonl  the game's cases, one per line

``evaluation.src.data.sources.sidecar.LocalCaseSource(<out>/games.jsonl)`` then reads served
games exactly as it reads a batch. Run it from a checkout on the host, where the database can
be reached:

    poetry run python -m server.housekeeping.export_eval_cases --out batch_results/hosted_2026_11
    poetry run python -m server.housekeeping.export_eval_cases --out ... --since 2026-11-01

Without ``--since`` or ``--game`` it exports every game that still has stored cases. The server
deletes a game's cases after ``EVAL_CASES_TTL_DAYS``, so export before then what must be kept.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

from server.config import ServerSettings, server_settings
from server.db import Database
from server.storage.eval_cases import RECORD_FORMAT, EvalCaseArchive


async def export_cases(archive: EvalCaseArchive, out: Path, *, since: datetime | None = None,
                       game_ids: Sequence[str] = ()) -> int:
    """Write each chosen game's cases under ``out`` and return how many games were written.
    A row in a format this code does not know is reported and left out."""
    listings = await archive.list_games(since=since, game_ids=game_ids)
    cases_dir = out / "eval_cases"
    cases_dir.mkdir(parents=True, exist_ok=True)
    written = 0
    with (out / "games.jsonl").open("w", encoding="utf-8") as results:
        for game in listings:
            if game.record_format != RECORD_FORMAT:
                print(f"{game.game_id}  skipped: stored in format {game.record_format!r}",
                      file=sys.stderr)
                continue
            records = await archive.load_cases(game.game_id)
            path = (cases_dir / f"{game.game_id}.jsonl").resolve()
            with path.open("w", encoding="utf-8") as file:
                for record in records:
                    file.write(json.dumps(record, sort_keys=True) + "\n")
            results.write(json.dumps({
                "game_id": game.game_id,
                "status": "success",
                "source": "hosted",
                # A game played with tracing off has no trace id; the reader groups a game's
                # cases under this key, so the game id stands in.
                "trace_id": (records[0].get("trace_id") if records else None) or game.game_id,
                "eval_cases_path": str(path),
                "n_cases": game.n_cases,
                "partial": game.partial,
                "saved_at": game.saved_at.astimezone(timezone.utc).isoformat(),
            }, sort_keys=True) + "\n")
            note = "  (partial: resumed after a restart)" if game.partial else ""
            print(f"{game.game_id}  {game.n_cases} cases{note}")
            written += 1
    print(f"exported {written} game(s) to {out}")
    return written


def _since(value: str) -> datetime:
    when = datetime.fromisoformat(value)
    return when if when.tzinfo else when.replace(tzinfo=timezone.utc)


async def _main(args: argparse.Namespace) -> int:
    url = ServerSettings(WW_POSTGRES_DSN=args.dsn).replay_database_url if args.dsn \
        else server_settings.replay_database_url
    if not url:
        print("export: WW_POSTGRES_DSN is not set", file=sys.stderr)
        return 2
    database = Database(url)
    await database.startup()
    try:
        await export_cases(EvalCaseArchive(database), args.out, since=args.since,
                           game_ids=args.game or ())
        return 0
    finally:
        await database.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--out", type=Path, required=True, help="the folder to write into")
    parser.add_argument("--since", type=_since, default=None,
                        help="only games saved since this time (ISO, UTC if no zone)")
    parser.add_argument("--game", nargs="+", default=None, help="these game ids only")
    parser.add_argument("--dsn", default=None, help="database address; default: the server's")
    sys.exit(asyncio.run(_main(parser.parse_args())))


if __name__ == "__main__":
    main()
