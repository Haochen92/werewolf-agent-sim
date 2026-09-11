# `server/` — the map

The FastAPI service that runs Werewolf games for a browser: it drives the LangGraph engine,
turns its stream into an event log, streams that log to viewers by entitlement, takes human
turns, and keeps every game durable across restarts. This page is the reading order and the
pointer to each decision record. It does not repeat the decisions — follow the links.

## Three nested lifecycles

```
process    boot ───── serve ───────────────────────────── shutdown       app.py, resources.py
registry      ids appear, move between stages, disappear                 game/registry.py
one game         waiting ──▶ running ──▶ completed | dropped             game/lobby.py, game/game_session.py
```

The **root** holds what the process needs to exist. Each **package** holds one domain. The
registry is the layer in between: process-scoped, game-shaped.

## Layout

| Path | Owns | Decision record |
|---|---|---|
| `app.py` | lifespan (recover → sweep → serve → stop), middleware, router registration | design notes §9 |
| `config.py` | deployment knobs from the environment — never game config | — |
| `db.py` | the SQLAlchemy engine for the server-owned tables | design notes §8 |
| `graph_runtime.py` | the LangGraph checkpointer pool + compiled durable graph (db.py's twin) | design notes §5c mode 3 |
| `resources.py` | builds the resource tree once, closes it in reverse | design notes §9 |
| `dependencies.py` | request → resource providers; the one 404 | design notes §9 |
| `routes/` | HTTP translation only: `system` (health, models), `games` (doors, status, turns, SSE), `rooms` (lobby), `replays` | transport §2, §7, §9 |
| `schemas/` | the wire: `events` (the durable union + tiers), `requests` (bodies/DTOs), `replays` | transport §5, §10 |
| `database_models/` | SQLModel mappings for `games` and `events` | design notes §8 |
| `game/registry.py` | **the middle lifecycle**: the table of every game and every transition that originates outside a game | design notes §10 |
| `game/lobby.py` | the waiting stage: seats, host key, lock, listing TTL | transport §6b, §6c |
| `game/game_session.py` | the running stage: `GameSession` (task, log, viewers, human turns) and `entitled()` | transport §3, §6, §8; design notes §5 |
| `game/seat_clocks.py` | when an unanswered human turn is delegated or the table parks | `frontend/docs/seat_continuity.md` |
| `game/pacing.py` | progress bars from public knowledge only | transport §9 |
| `game/translate.py` | stream parts → tier-ready durable events, one instance per game | transport §5, §8; design notes §1–§3 |
| `game/model_catalog.py` | which models may be played, their rescue, who pays | — |
| `storage/game_repository.py` | write side + recovery reads of the game lifecycle | design notes §8 |
| `storage/replay_service.py` | the public read side (the feature is `routes/replays.py`) | design notes §9 |
| `housekeeping/recovery.py` | boot: hand every open row to `registry.revive` | design notes §5c; seat_continuity §6 |
| `housekeeping/sweeper.py` | timer: drop parked games nobody is watching | seat_continuity §7 |

Decision records live in `frontend/docs/`: `server_client_transport.md` (the wire),
`server_design_notes.md` (server rulings, dated), `seat_continuity.md` (absence and recovery),
`server_encountered_challenges.md` (what broke, in plain language).

## Reading order for a newcomer

1. `frontend/docs/server_client_transport.md`, the appendix first — the mental model in one
   paragraph: an event log the client folds, SSE plus POST, audience tiers, seat cookies.
2. `schemas/events.py` — the vocabulary everything else speaks.
3. `game/registry.py` — the state diagram in its docstring, then the transitions.
4. `game/game_session.py` — `GameSession`'s field guide, then `_drive_graph`, `_on_part`, `submit_turn`.
5. `routes/games.py` `_sse` — how one viewer's stream is filtered and resumed.
6. Then only what a task takes you to. Do not read `translate.py` cold; read it beside
   `tests/server/test_translator.py`, whose names are the spec.

## Re-entering after months

Read the decision record for the area, skim the test names in `tests/server/`, read the
module docstring, open code only where the task lands. Never reread everything.

## Running it

```
poetry run uvicorn server.app:app --port 8001     # 8000 belongs to another project on this host
poetry run pytest tests/server -q                 # ~140 tests, no network, no LLM
poetry run alembic upgrade head                   # WW_POSTGRES_DSN from .env
```

Production is `docker compose build wolf-server && docker compose up -d wolf-server`; the
container logs at `LOG_LEVEL` (default INFO) show recovery, clocks, the sweep, and every
stream open/close.
