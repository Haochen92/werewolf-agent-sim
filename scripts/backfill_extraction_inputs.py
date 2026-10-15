"""Write the extraction inputs of games that ended before games saved them (one-off, 2026-10-12).

Since decisions §11 a game saves its extraction input when it ends and an offline batch job extracts
it. Older games are rebuilt (Agents/memory/extraction/offline.py):

- run_batch games, from their game record and decision cases (``--runs``: batch record globs);
- served games, from their durable event log (``--server``: completed ten-seat games with no human
  seat, read-only).

Output: one record per game in the eval-case sink format (``kind: extraction_input``), with the game's
model and source in ``metadata``, the format the offline job reads.

  poetry run python scripts/backfill_extraction_inputs.py --server \\
      --runs 'batch_results/v8_seed_*/games/*.jsonl' 'batch_results/ten_seat_pilot/*.jsonl' ...
"""

from __future__ import annotations

import argparse
import ast
import glob
import json
from pathlib import Path

from Agents.memory.extraction.offline import input_from_event_log, input_from_run_records

OUT = Path("batch_results/extraction_inputs/backfill_2026-10-12.jsonl")


def _record(case, **metadata) -> dict:
    return {"kind": "extraction_input", "id": "", "name": case.span_name, "trace_id": "",
            "parent_observation_id": None, "metadata": metadata, "input": None,
            "output": {"extraction_case": case.model_dump(mode="json")}}


def _cases_file(game: dict, batch_file: Path) -> Path:
    """The game's decision-case file: where run_batch wrote it, or beside the batch file when the
    run's worktree is gone and the file was copied in."""
    path = Path(game["eval_cases_path"])
    return path if path.exists() else batch_file.parent / path.relative_to("batch_results")


def from_runs(patterns: list[str]) -> list[dict]:
    out = []
    for batch_file in sorted({Path(p) for pattern in patterns for p in glob.glob(pattern)}):
        for line in batch_file.read_text().splitlines():
            game = json.loads(line)
            if game.get("status") != "success":
                continue
            records = [json.loads(r) for r in _cases_file(game, batch_file).read_text().splitlines()]
            cases = [next(iter(r["output"].values())) for r in records if r["kind"] == "agent_action_eval"]
            fingerprint = game.get("runtime_fingerprint") or {}
            if isinstance(fingerprint, str):
                fingerprint = ast.literal_eval(fingerprint)
            out.append(_record(input_from_run_records(game, cases), source=str(batch_file),
                               game_model=fingerprint.get("game_model", ""),
                               finished=game.get("ended_at", "")))
    return out


def from_server() -> list[dict]:
    import psycopg
    from dotenv import dotenv_values
    from psycopg.rows import dict_row

    dsn = dotenv_values(".env")["WW_POSTGRES_DSN"]
    out = []
    with psycopg.connect(dsn, autocommit=True, row_factory=dict_row,
                         options="-c default_transaction_read_only=on") as conn:
        games = conn.execute(
            "select game_id, model, finished_at from games where status = 'completed' and n_humans = 0 "
            "and cast_role_counts ? 'healer' and jsonb_array_length(coalesce("
            "  (select payload->'lineup' from events e where e.game_id = games.game_id and e.seq = 1), '[]')) = 10 "
            "order by finished_at").fetchall()
        for g in games:
            events = [r["payload"] for r in conn.execute(
                "select payload from events where game_id = %s order by seq", (g["game_id"],)).fetchall()]
            out.append(_record(input_from_event_log(g["game_id"], events), source="server",
                               game_model=g["model"], finished=g["finished_at"].isoformat()))
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--runs", nargs="*", default=[], help="run_batch game record globs")
    parser.add_argument("--server", action="store_true", help="served AI-only ten-seat games")
    args = parser.parse_args()
    records = from_runs(args.runs) + (from_server() if args.server else [])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("".join(json.dumps(r) + "\n" for r in records))
    by_source: dict[str, int] = {}
    for r in records:
        key = f"{r['metadata']['source']} ({r['metadata']['game_model']})"
        by_source[key] = by_source.get(key, 0) + 1
    for key, n in sorted(by_source.items()):
        print(f"{n:3} {key}")
    print(f"{len(records)} games -> {OUT}")


if __name__ == "__main__":
    main()
