# U0. System architecture orientation

**Time** 45 min · **Category** 2 · **Depth** Recognise · **Needs** none
**Chapters served:** 7 and 8

**Diagnostic (answer before reading, two sentences, example not from this project):** Draw a
component diagram of a system you know, and mark which store is the record of what.

## 1. The concept

A component diagram is a map of a running system. Each box is a part that runs or keeps data.
Each arrow is a call or a message between two parts.

Take an online ticket shop. A fan opens the shop in a browser, picks a seat and pays. A minute
later an email brings the ticket. Five kinds of part make that happen.

The browser is the **client**. It knows what the fan typed and what the shop sent back. It wants
to show the seats and take the order. It runs on the fan's machine, so the shop checks everything
it says.

The **API server** answers the client. It knows the rules: which seats are free and their price.
It wants to answer fast, so it hands slow work on.

The **worker** takes that work off a **queue**, renders the ticket and sends the email. It wants
to finish each job, however long it takes. A worker that does the system's main work is often
called the **engine**.

The card company is a **provider**: an outside service the shop calls and pays for. The shop
knows only what its reply says.

The **persistent stores** keep data when a process stops: the database, the queue, a bucket of
ticket files. For each one, ask what it is the record of. A store is the **record** for a fact
when it wins any disagreement about that fact. The orders table is the record of what each fan
bought. The provider's ledger is the record of what money moved. The queue is the record of work
still to do. A cache of free seats is the record of nothing: it is a **copy**, rebuilt from the
orders table when it drifts.

The last mark is the **trust boundary**, the line between the parts I run and the parts I don't.
The browser sits outside it, so the server reads the price from its own table. The provider sits outside it too, so the shop guards its key and checks each reply.

Why mark the records? Because a hard question is usually a question for one record. "Did this fan
pay?" goes to the ledger. "Which seat did they get?" goes to the orders table. When two records
disagree, the diagram says which one to believe and which one to repair.

### Terms

| Term | Meaning here |
|---|---|
| Component diagram | Boxes for parts that run or keep data, arrows for the calls between them |
| Client | The program on the user's device; outside the trust boundary |
| API server | Answers the client's requests and enforces the rules |
| Worker / engine | Does the slow or main work, often off a queue |
| Provider | An outside service the system calls and pays for (payments, a model API) |
| Persistent store | Keeps data after a process stops: a database, a queue, a file bucket |
| Record (authority) | The store that wins a disagreement about a given fact |
| Copy | Data rebuilt from a record; it loses any disagreement with that record |
| Trust boundary | The line between parts I run and parts I don't; every input crossing it gets checked |

### Depth boundary

Core: draw the diagram, place the trust boundary, name each store's record. Deferred: blocking
work on one loop (U2), logs and replay (U3), redelivery (U4), who reads which record (U7), traces
(U8), keys (U10).

## 2. Alternatives and trade-offs

| Design | What it buys | What it costs | Fits when |
|---|---|---|---|
| **Engine inside the server process** (this project) | One process to deploy; the engine's output streams straight to viewers with no broker | A restart stops every job at once; jobs and requests share one machine | Few jobs at a time, each watched live, one operator |
| **Engine as separate workers behind a queue** | Workers scale and restart on their own; the API server stays small | A broker to run, a message format between processes, and a human's answer must reach the right worker | Many jobs, or jobs that run with nobody watching |

My server runs the engine inside its own process: each game is a task on the event loop that
drives the engine. Only a few games run at once, and the design notes call workers behind a
broker a step this scale does not need. U2 takes up what the choice costs.

## 3. This project

My system is a browser, two app containers behind a proxy, model providers, and one Postgres
database that holds the records.

```
 OUTSIDE (untrusted)              ┆  MY HOST (Docker)
                                  ┆
 Browser ───── HTTPS ────────────▶┆  Caddy ─┬─ other paths ─▶ wolf-frontend (Next.js pages)
   page + seat cookie             ┆         │
   GET  /games/{id}/events (SSE)  ┆         └─ /api/* ──────▶ wolf-server: FastAPI, one asyncio loop
   POST /games/{id}/turns         ┆                             LiveGameRegistry
                                  ┆                             └─ GameSession: one task per game
                                  ┆                                  │ graph.astream()
                                  ┆                                  ▼
                                  ┆                             LangGraph engine: sync nodes
                                  ┆                             on a 64-thread pool
 Model providers ◀─ prompts + key ┼──────────────────────────────────┤
 (Google, Anthropic, DeepSeek, …) ┼─ replies ───────────────────────▶│
                                  ┆                                  ▼ writes
                                  ┆   ww-postgres (one database)
                                  ┆     games ............ identity, seats, status (+ usage column)
                                  ┆     events ........... every event the game sent, in order
                                  ┆     checkpoints ...... where the engine is
                                  ┆     prompt_captures .. what each AI player was sent
                                  ┆     game_cast ........ which puppet stood at each seat
                                  ┆     + settings, models, model_prices, characters,
                                  ┆       game_lessons, the lesson store
                                  ┆   Langfuse (its own stack) .. a trace of each game run
```

**The parts.**

- Caddy sends `/api/*` to the server and every other path to the Next.js frontend. A browser
  watches a game over one SSE stream and sends a turn with a POST. **code**
  [docker-compose.yml](../../../docker-compose.yml) header comment;
  [games.py](../../../server/routes/games.py)::`event_stream`, `submit_turn`
- The server is FastAPI on one asyncio loop. At boot, `lifespan` gives the loop a 64-thread pool,
  recovers running games and starts the sweeper. **code** [app.py](../../../server/app.py)::`lifespan`
- Each running game is one `GameSession` with one asyncio task. `_drive_graph` reads the engine's
  `astream()`, and LangGraph runs the synchronous nodes on the thread pool. **code**
  [game_session.py](../../../server/game/game_session.py)::`start`, `_drive_graph`
- A human's turn is where browser and engine meet: `park` holds the question, `submit_turn` takes
  the POSTed answer, `_collect_answers` resumes the engine. **code**
  [game_session.py](../../../server/game/game_session.py)::`park`, `submit_turn`, `_collect_answers`
- The providers: Google, Anthropic, Mistral, and DeepSeek and others over the OpenAI protocol.
  **code** [providers/\_\_init\_\_.py](../../../Agents/llm_factory/providers/__init__.py)
- Each run of a game is one trace in a self-hosted Langfuse. **code**
  [game_session.py](../../../server/game/game_session.py)::`_run`

**The records, and the question each answers.**

- `games` row: which game, who sits where, and whether it is running, completed or dropped. It
  never holds a player's key. **code** [game.py](../../../server/database_models/game.py)::`GameRow`
- `events`: every event the game sent, by `seq`, each tagged with an audience. `entitled()`
  applies the audience per viewer at send time, so "what was this player shown?" is the events
  table read through that rule for their seat. **code**
  [game.py](../../../server/database_models/game.py)::`EventRow`;
  [entitlement.py](../../../server/game/entitlement.py)::`entitled`
- Checkpoints: LangGraph's own tables in the same database, keyed by game id. They say where the
  engine is, open questions included. **code**
  [graph_runtime.py](../../../server/graph_runtime.py)::`GraphRuntime.startup`
- `prompt_captures`: every prompt the AI players were sent and every private read they made,
  written when the game ends, for the leak audit. A resumed game's capture is marked `partial`;
  a dropped game gets none. **code**
  [capture.py](../../../server/database_models/capture.py)::`PromptCaptureRow`;
  [game_session.py](../../../server/game/game_session.py)::`_save_capture`
- Usage: tokens and call time per model and hour. The outline calls it a fifth record; in the code
  it is the `usage` column on the games row. **code**
  [game.py](../../../server/database_models/game.py)::`GameRow.usage`
- A sixth record the outline leaves out: `game_cast`, the puppet at each seat, written by the
  running game. The database also holds settings, the model menu, prices, characters and the
  lessons. **code** [database_models/\_\_init\_\_.py](../../../server/database_models/__init__.py);
  [game_session.py](../../../server/game/game_session.py)::`_persist_tail`
- After a restart, `revive` rebuilds each running game from its row, events and cast; the engine
  carries on from its checkpoint. **code**
  [live_game_registry.py](../../../server/game/live_game_registry.py)::`revive`. **test**
  `test_parked_game_revives_reparked_and_resumes_on_the_answer` (not run; no real Postgres)
  [test_durability.py](../../../tests/server/test_durability.py)

**Incidents on record:**

- 2026-08-20 to 22: the durability row records "restart smoke passed" on real Postgres; its
  sentence on key-funded games predates resuming with the key. **incident**
  [build_plan.md](../../../frontend/docs/build_plan.md) "Session durability"
- 2026-09-12: the events table can run one engine step ahead of the checkpoint. **incident**
  [server_encountered_challenges.md](../../../frontend/docs/server_encountered_challenges.md) §8
- 2026-10-17: a human's prompt surfaced seconds late with 8 pool threads; the pool went to 64.
  **incident** (dated comment) [app.py](../../../server/app.py)::`lifespan`

**Not established:**

- How many games one process can hold: no load test in what I read.
- A nightly leak audit over the captures: the cron is not installed. **incident** (note dated
  2026-10-26) [server/README.md](../../../server/README.md) "Running it"
- What a player's screen rendered. The events table records what the server sent their seat.

**Framework specifics, pointed to:** how LangGraph orders its checkpoint write and runs sync nodes
on threads: [server_design_notes.md](../../../frontend/docs/server_design_notes.md) §5 "The machinery";
[langgraph_langfuse_issues.md](../../../interview_prep/langgraph_langfuse_issues.md).

## 4. Reading

- [server/README.md](../../../server/README.md), "Layout": every module and what it owns.
- [server_talking_points.md](../../../interview_prep/server_talking_points.md), once through; reread "What happens when
  the server restarts mid-game?".
- [server_design_notes.md](../../../frontend/docs/server_design_notes.md) §5b: the scaling story
  behind part 2.
- [server_encountered_challenges.md](../../../frontend/docs/server_encountered_challenges.md) §8: two
  records of one game disagreeing.

## 5. Checks

**Transfer.** Lawyers upload contracts through a web page, and the API server queues a review job.
A worker sends the clauses to an LLM provider and saves the ones it flags, which the lawyer
accepts or rejects in the page. Draw the diagram, mark the trust boundary, and name each store's
record.

**Project evidence.** Draw my system with its records. Then judge this draft claim: "My server
keeps five records in Postgres, and the events table tells you exactly what each player saw."

## 6. Workbook

- **The concept in my own words:**
- **My transfer answer:**
- **The project claim and its support:**
- **Remaining gaps / questions to record:**
- **Time taken:**

---

## Answer keys

**Transfer.** Assumptions: one database, one queue, a file bucket, one model provider.

```
 OUTSIDE                  ┆  MINE
                          ┆
 Browser ──── HTTPS ─────▶┆  API server ── put job ──▶ Queue ── take job ──▶ Worker
                          ┆      │                                            │  │
                          ┆      ▼                                            │  │
                          ┆  Database ◀──────────── saves flags ──────────────┘  │
                          ┆    jobs ....... each review's status                 │
                          ┆    findings ... what the model flagged               │
                          ┆    decisions .. what the lawyer accepted             │
                          ┆  Bucket ....... the uploaded contracts               │
                          ┆  Prompt log ... what each model call was sent        │
                          ┆                                                      │
 LLM provider ◀───────────┼─────────────── clauses / flags ──────────────────────┘
```

The jobs table is the record of each review's status; the queue holds only work still to do, so
the jobs table wins a disagreement. The contract text sits outside the boundary with the browser
and the provider: it can carry instructions (U11).

**Project evidence.** Compare your drawing with the part 3 diagram. Four of the five records are
tables: the games row, events, checkpoints and prompt captures. Usage is a column on the games
row, and `game_cast` is a further record. The events table holds everything the game sent, tagged
by audience. Accurate wording: "One Postgres
database holds my game records: the game row, the event log, LangGraph's checkpoints and the
prompt captures. Filtering the event log by one seat's audience gives what that player was sent."
