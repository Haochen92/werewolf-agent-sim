"""The leak audit for the website's games: did any AI player's prompt carry information that
only another player should know?

The batch runner checks every game it plays this way (tests/leak_test.py); the website's games
were never checked. Now each finished game saves the prompts its AI players were sent, their
private reads and its final state (server/storage/prompt_captures.py), and this job runs the same
nine checks over those saved games after the fact. It prints one line per game, writes the
verdict back on the game's capture row (``audited_at`` and ``leaks``), and exits 1 if any game
leaked, 2 if a game could not be read, 0 when every game is clean.

Which games: by default every game not audited yet, so a nightly run picks up exactly the games
finished since the last one; ``--since`` re-checks every game captured since a time, and
``--game`` checks the named games. ``--no-record`` leaves the verdicts unwritten.

    poetry run leak-audit                       # every game not audited yet
    poetry run leak-audit --since 2026-10-01 -v # re-check, and print each leak found
    poetry run python -m server.housekeeping.leak_audit --game <game_id>

It runs from a checkout of the repository on the host, not inside the server's container: the
checks live in tests/leak_test.py, which the server image does not include. The database is
WW_POSTGRES_DSN from .env, or ``--dsn``.

Nightly at 04:15 (crontab -e on the host; the log keeps each night's lines). The ``python -m``
form works before the ``leak-audit`` entry point is installed into the environment:

    15 4 * * * cd /home/ubuntu/projects/werewolf-agent-sim && /home/ubuntu/.local/bin/poetry run python -m server.housekeeping.leak_audit >> /home/ubuntu/leak_audit.log 2>&1

or as a systemd timer: a oneshot service with that ``ExecStart`` and ``WorkingDirectory``, and a
timer with ``OnCalendar=*-*-* 04:15:00`` and ``Persistent=true``.
"""

from __future__ import annotations

import argparse
import asyncio
import io
import sys
from contextlib import redirect_stdout
from datetime import datetime, timezone
from typing import Any

from server.config import ServerSettings, server_settings
from server.db import Database
from server.schemas.leak_audit import GameCapture
from server.storage.prompt_captures import CaptureAuditRepository
from tests.leak_test import leak_inputs, run_leak_tests

LEAKED, UNREADABLE = 1, 2


def public_text(state: dict[str, Any]) -> str:
    """What every player could see: the day's talk, the day summaries and the pack's chat, the
    same text the batch runner gives the reads check, so a private reason that also appears
    here counts as shared wording rather than a leak."""
    return " || ".join(
        [m["message"] for m in state.get("day_channel") or []]
        + [s["summary"] for s in state.get("day_summaries") or []]
        + [w["message"] for w in state.get("wolf_channel") or []]
    )


def audit_capture(capture: GameCapture) -> list[str]:
    """Run the batch runner's nine leak checks over one saved game; one line per leak found."""
    state = capture.final_state
    with redirect_stdout(io.StringIO()):  # the checks print as they go; the audit prints its own line
        return run_leak_tests(
            capture.prompt_log,
            state.get("roles") or {},
            reads_log=capture.reads_log,
            public_text=public_text(state),
            **leak_inputs(state),
        )


async def run_audit(store: CaptureAuditRepository, *, since: datetime | None = None,
                    game_ids: list[str] | None = None, record: bool = True,
                    verbose: bool = False) -> int:
    """Audit the chosen games one at a time (a capture can be megabytes) and return the exit code."""
    listings = await store.list_captures(since=since, game_ids=game_ids or ())
    if not listings:
        print("leak audit: no games to audit")
        return 0
    leaked = unreadable = 0
    for game in listings:
        when = game.captured_at.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M")
        note = "  (partial: resumed after a restart)" if game.partial else ""
        try:
            leaks = audit_capture(await store.load_capture(game.game_id))
        except Exception as exc:
            unreadable += 1
            print(f"{when}  {game.game_id}  ERROR  could not audit: {exc!r}")
            continue
        if record:
            await store.record_verdict(game.game_id, leaks)
        if leaks:
            leaked += 1
            print(f"{when}  {game.game_id}  LEAK   {len(leaks)} leak(s) in "
                  f"{game.n_prompts} prompts{note}")
            if verbose:
                for leak in leaks:
                    print(f"    {leak}")
        else:
            print(f"{when}  {game.game_id}  clean  {game.n_prompts} prompts{note}")
    print(f"leak audit: {len(listings)} game(s), {leaked} leaked, {unreadable} unreadable")
    return LEAKED if leaked else UNREADABLE if unreadable else 0


def _since(value: str) -> datetime:
    when = datetime.fromisoformat(value)
    return when if when.tzinfo else when.replace(tzinfo=timezone.utc)


async def _main(args: argparse.Namespace) -> int:
    url = ServerSettings(WW_POSTGRES_DSN=args.dsn).replay_database_url if args.dsn \
        else server_settings.replay_database_url
    if not url:
        print("leak audit: WW_POSTGRES_DSN is not set", file=sys.stderr)
        return UNREADABLE
    database = Database(url)
    await database.startup()
    try:
        return await run_audit(CaptureAuditRepository(database), since=args.since,
                               game_ids=args.game, record=not args.no_record,
                               verbose=args.verbose)
    finally:
        await database.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--since", type=_since, default=None,
                        help="re-check every game captured since this time (ISO, UTC if no zone)")
    parser.add_argument("--game", nargs="+", default=None, help="check these game ids only")
    parser.add_argument("--no-record", action="store_true", help="do not write the verdicts")
    parser.add_argument("-v", "--verbose", action="store_true", help="print every leak found")
    parser.add_argument("--dsn", default="", help="Postgres DSN (default: WW_POSTGRES_DSN)")
    sys.exit(asyncio.run(_main(parser.parse_args())))


if __name__ == "__main__":
    main()
