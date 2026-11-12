# Improvements found while writing the notes

One list of the limitations the notes have turned up, with what would fix each. Nothing here is
decided. I go through the list once all the notes are written and choose what to build before the
write-up is published. Each note's own gaps section has the detail; this file only gathers them.
A row is added when a note is written or a walkthrough finds something.

The size column is my sorting for that later decision:

- **Small**: hours, low risk, no design choice. Leaving one of these unfixed is hard to defend.
- **Decision**: needs a measurement or a choice first. Defensible as a stated limitation while the
  measurement is missing, as long as I can say what the measurement is.
- **Large**: days, or a risk to working behaviour. Defensible as a next step if I can say what it
  buys, what it costs beyond the typing, and what would make it worth doing.

## Open

| # | Limitation | What would fix it | Size | Detail |
|---|---|---|---|---|
| 1 | A whole turn has no time limit | A clock check between calls with a safe default past the budget; a real deadline needs the async engine (row 14) | Decision | U1 3.3 gap 1 |
| 2 | Nothing adds up the failures (rescues, safe defaults) | Counters, recorded per game | Small | U1 3.3 gap 2; U8 |
| 3 | House games have no rescue model | A second house key or model for the rescue | Decision | U1 3.3 gap 3 |
| 4 | The lesson store's lock is held across the embedding call, and one store serves every game | Get the embedding before taking the lock, and one store per game sharing today's pool (both are needed: the first for seats within a game, the second between games) | Chosen to build (2026-11-12) | U2 3.7 gap 1.1 |
| 5 | The checkpoint saver allows one save at a time for the whole server | A saver per game sharing today's pool, with the compiled graph copied per game (0.1 ms, about 4 KiB each, measured locally); untried on the server | Chosen to build (2026-11-12) | U2 3.7 gap 1.2; U3 3.7 |
| 6 | Nothing measures the thread pools or how long work waits | Record busy threads and wait time | Small | U2 3.7 gap 2; U8 |
| 7 | The trace send at the end of a game blocks the event loop (`flush()` in the `finally` of the game's task, `server/game/game_session.py`). Every viewer of every game waits while it runs; worst when the tracing service is slow or unreachable. Duration not measured | `await asyncio.to_thread(flush)`. One care: the call sits in a `finally`, which also runs when the task is cancelled at shutdown, so the hand-off must still complete then (or shutdown does its own final send). Independent of row 14: an async engine would not change this call, which is server code calling a blocking library function | Small; do first | U2 3.7 gap 3 |
| 8 | Nothing refuses a game, and the container has no memory limit | Measure memory per game, then set a cap on running games and a container limit together; derive the main pool's size from the cap | Decision | U2 3.7 gap 4, 3.8; U15 seed |
| 9 | The real restart path has no automated test | A kill-and-restart test on real Postgres with scripted players | Decision | U3 3.8 gap 1; U13 seed |
| 10 | After a restart the event log and the engine can disagree about a line (read in code, not reproduced) | Reproduce it first; three candidate fixes in the note | Decision | U3 3.8 gap 2 |
| 11 | The turn cache is lost on a restart, so the step in flight is billed again | Save turn results where a restart can find them | Large | U3 3.8 gap 3 |
| 12 | Nothing deletes a finished game's checkpoints or events, and one game's size is not measured | Measure, then a retention rule | Decision | U3 3.8 gap 4 |
| 13 | A re-run turn may count twice in the lesson store | A guard on the counter update, keyed by turn | Decision | U3 3.8 gap 5; U4 |
| 14 | The engine is blocking code on threads | Rewrite the graph steps as async code. Buys: no thread budgets, no thread locks, cancellation (which row 1 wants). Costs: proving the engine behaves the same, and finding every blocking call on the path. First step: count the functions, call sites and library calls that would change | Large | U2 3.3; U15 seed |
| 15 | One engine test passes or fails by thread order (`test_a_human_vigilantes_shot_is_spent_once_across_the_pause_and_resume`) | Fix the situation the test sets up, or assert what holds in any game | Small | U2 3.7 gap 5; U13 seed |
| 16 | Viewer queues have no size limit, so a slow viewer's events pile up in memory | A limit, with a rule for a viewer who falls behind | Decision | README open item for U6 |
| 17 | A batch run's night step has up to nine parts and probably runs on a default pool of 8 (not measured) | Measure; set the size if confirmed | Small | U2 3.7 gap 5 |

## Done while writing the notes

Changed in the working tree; none of it is committed or deployed as of 2026-11-12.

| What | When | Detail |
|---|---|---|
| The per-phase thread pool is one thread per seat, where it was Python's default of 8 | 2026-11-12 | U2 3.7 gap 5 |
| The request helpers in `server/dependencies.py` are `async def`, so they run on the event loop | 2026-11-12 | U2 3.3, Appendix B |
| Three fixes with tests from the earlier walkthroughs, in `Agents/llm_factory/embeddings.py`, `Agents/memory/retrieval/situation_agent.py` and `Agents/turn/echo_gate.py` | 2026-11-11 | U1 |

## Records for the write-up

For the few fixes worth telling on a write-up page as "the design, its problem, the fix". A fix
belongs here when the problem teaches something general, there is a measurement before and after,
and the first design was a reasonable one. Each record holds what the page will need, so the page
can be written without this conversation. Small fixes (the pool of 8, the `async def` helpers)
stay in the Done table only.

### The two library locks (chapter 7 candidate)

- **The first design.** One checkpoint saver and one lesson store, created at start-up and shared
  by every game, each with a pool of four connections. The ordinary way to set up both libraries.
- **The problem.** Each object holds a lock of its own for a whole operation, so four connections
  work as one, and every game queues behind every other. For the store the lock is held across
  the call to the embedding service.
- **How it was found.** By measuring while writing U2, not by an incident: nothing had failed,
  because few games ran at once.
- **Before.** Eight checkpoint saves of 0.2 s each for eight games: 1.6 s, where side by side they
  take 0.2 s. Four lesson lookups with a 1 s embedder: done at 1, 2, 3 and 4 s; with the lock
  removed, all at 1 s. Local, with the database and embedder replaced by fixed delays
  (`measurements/u2_saver_lock.py`, `measurements/u2_store_lock_overlap.py`).
- **Why the lock cannot simply be removed.** It is inside each library.
- **The fix.** The lock belongs to the object, not the pool. So: a saver and a store per game, all
  sharing the two pools, carried by a per-game copy of the compiled graph (0.1 ms and about 4 KiB
  each, `measurements/u2_compile_cost.py`); and for the store, the embedding fetched before the
  lock is taken, because seats of one game look up lessons in the same step.
- **Status.** Chosen to build on 2026-11-12. Not built.
- **Still needed before the page can state it as the design.** The fix built and deployed; the
  same two measurements repeated after it, on the real Postgres saver and store, not stand-ins;
  the commit. That the locks are per object and the pools shareable is read in the library's code,
  not yet run.
- **Detail.** U2 sections 3.5 and 3.7 gap 1; U3 section 3.7.

### The prompt that arrived late (already told in U2 3.1)

- Symptom, first guess, cause and fix are kept apart in U2 section 3.1. Commit `2814776d`
  (2026-10-17). Design record: `frontend/docs/server_client_transport.md` section 8b. The mechanism
  belongs to U5 (`u05_seed_notes.md`).

### A test that passed by thread order (U13 candidate)

- **What it claimed.** A human Vigilante's bullet is spent once across a pause and resume.
- **What was wrong with the test, not the engine.** Its scripted players share one random
  generator across threads, so the game played depends on thread order; and it counts shots from
  night records, which the engine drops for a seat that dies the same night.
- **Evidence.** Failed 2 of 10 runs with the pool setting and 4 of 10 without
  (`measurements/u2_diag_vig.py`, `measurements/u2_diag_runs.txt`). The bullet was spent once in
  every run examined.
- **Status.** Test unchanged. Two repairs in `u13_seed_notes.md`.

### What a restart costs (chapter 7 candidate, not ready)

- Findings are in U3 sections 3.6 and 3.8: AI turns of the step in flight are billed again, and
  the log and the engine can disagree about a line. Both are read in code or measured on a small
  stand-in graph (`measurements/u3_kill_resume_toy.py`); neither is reproduced on the real server.
  No fix chosen. Not a story until one is reproduced and fixed.
