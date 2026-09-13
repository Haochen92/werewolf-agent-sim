# `server/` — the map

The FastAPI service that runs Werewolf games for a browser: it drives the LangGraph engine,
turns its stream into an event log, streams that log to viewers by entitlement, takes human
turns, and keeps every game durable across restarts. This page is the reading order and the
pointer to each decision record. It does not repeat the decisions — follow the links.

## Three nested lifecycles

```
process    boot ───── serve ───────────────────────────── shutdown       app.py, resources.py
live registry ids appear, move between stages, leave once ended         game/live_game_registry.py
one game         waiting ──▶ running ──▶ completed | dropped             game/lobby.py, game/game_session.py
```

The **root** holds what the process needs to exist. Each **package** holds one domain. The
registry is the layer in between: process-scoped, game-shaped. It holds only games that can
still move; an ended game is answered by its database row, and a finished one by its replay.

## Layout

| Path | Owns | Decision record |
|---|---|---|
| `app.py` | lifespan (recover → sweep → serve → stop), middleware, router registration | design notes §9 |
| `config.py` | deployment knobs from the environment — never game config; the `HOUSE_*` fallbacks and `ADMIN_TOKEN` | design notes §13 |
| `house.py` | **the house's purse**: who pays for a new game, the live default model, the daily cap; knobs read from the settings table | design notes §13 |
| `db.py` | the SQLAlchemy engine for the server-owned tables | design notes §8 |
| `graph_runtime.py` | the LangGraph checkpointer pool + compiled durable graph (db.py's twin) | design notes §5c mode 3 |
| `resources.py` | builds the resource tree once, closes it in reverse | design notes §9 |
| `dependencies.py` | request → resource providers; the fall-through from the live registry to the row for ended games; the one 404 | design notes §9, §11 |
| `routes/` | HTTP translation only: `system` (health, models + the purse), `games` (doors, status, turns, SSE, key), `rooms` (lobby), `replays`, `admin` (the live knobs, behind `ADMIN_TOKEN`) | transport §2, §7, §9; design notes §13 |
| `schemas/` | the wire: `events` (the durable union + tiers), `requests` (bodies/DTOs), `replays` | transport §5, §10 |
| `database_models/` | SQLModel mappings for `games`, `events` and `settings` | design notes §8, §13 |
| `game/live_game_registry.py` | **the middle lifecycle**: `LiveGameRegistry`, the table of every game that can still move and every transition that originates outside a game | design notes §10, §11 |
| `game/lobby.py` | the waiting stage: seats, host key, lock, listing TTL; memory only, no row until start, closes on restart | transport §6b, §6c; design notes §12 |
| `game/game_session.py` | the running stage: `GameSession` (task, log, viewers, human turns) | transport §3, §6, §8; design notes §5 |
| `game/entitlement.py` | `entitled()`: may this viewer see this event, by tier and seat; observer tier unlocks at game over | transport §6, §8 |
| `game/seat_clocks.py` | when an unanswered human turn is delegated or the table parks | `frontend/docs/seat_continuity.md` |
| `game/pacing.py` | progress bars from public knowledge only | transport §9 |
| `game/translate.py` | stream parts → tier-ready durable events, one instance per game | transport §5, §8; design notes §1–§3 |
| `game/model_catalog.py` | which models may be played, their rescue, whether the house *can* pay (whether it *will* is `house.py`) | design notes §13 |
| `game/key_check.py` | one trivial provider call to try a player's key before a game resumes on it | design notes §13 |
| `storage/game_repository.py` | write side + recovery reads of the game lifecycle | design notes §8 |
| `storage/replay_service.py` | the public read side (the feature is `routes/replays.py`) | design notes §9 |
| `storage/settings_repository.py` | the settings table: knobs an operator changes without a restart | design notes §13 |
| `housekeeping/recovery.py` | boot: hand every running row to `registry.revive` (a key-funded one waits for its key) | design notes §5c, §13; seat_continuity §6 |
| `housekeeping/sweeper.py` | timer: drop parked games nobody is watching | seat_continuity §7 |

Decision records live in `frontend/docs/`: `server_client_transport.md` (the wire),
`server_design_notes.md` (server rulings, dated), `seat_continuity.md` (absence and recovery),
`server_encountered_challenges.md` (what broke, in plain language).

## Reading order for a newcomer

1. `frontend/docs/server_client_transport.md`, the appendix first — the mental model in one
   paragraph: an event log the client folds, SSE plus POST, audience tiers, seat cookies.
2. `schemas/events.py` — the vocabulary everything else speaks.
3. `game/live_game_registry.py` — the state diagram in its docstring, then the transitions.
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
curl -H "X-Admin-Token: $ADMIN_TOKEN" -X PUT localhost:8001/admin/house \
     -H 'content-type: application/json' -d '{"games_per_day": 5}'   # live, no restart
```

Production is `docker compose build wolf-server && docker compose up -d wolf-server`; the
container logs at `LOG_LEVEL` (default INFO) show recovery, clocks, the sweep, and every
stream open/close.
