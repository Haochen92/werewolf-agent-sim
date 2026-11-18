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
| 9 | Built on 2026-11-18; see the Done table below. The row as written: the real restart path has no automated test | — | Done | U3 3.8 gap 1; U13 |
| 10 | After a restart the event log and the engine can disagree about a line (read in code, not reproduced) | Reproduce it first; three candidate fixes in the note | Decision | U3 3.8 gap 2 |
| 11 | The turn cache is lost on a restart, so the step in flight is billed again | Save turn results where a restart can find them | Large | U3 3.8 gap 3 |
| 12 | Nothing deletes a finished game's checkpoints or events, and one game's size is not measured | Measure, then a retention rule | Decision | U3 3.8 gap 4 |
| 13 | A re-run turn may count twice in the lesson store | A guard on the counter update, keyed by turn | Decision | U3 3.8 gap 5; U4 |
| 14 | The engine is blocking code on threads | Rewrite the graph steps as async code. Buys: no thread budgets, no thread locks, cancellation (which row 1 wants). Costs: proving the engine behaves the same, and finding every blocking call on the path. First step: count the functions, call sites and library calls that would change | Large | U2 3.3; U15 seed |
| 15 | One engine test passes or fails by thread order (`test_a_human_vigilantes_shot_is_spent_once_across_the_pause_and_resume`) | Fix the situation the test sets up, or assert what holds in any game. *2026-11-17: repaired in the working tree by fixing the situation (no scripted player targets the Vigilante); not committed. Record: `vigilante_test/experiment_log.md`* | Small | U2 3.7 gap 5; U13 seed |
| 16 | Viewer queues have no size limit, so a slow viewer's events pile up in memory | A limit, with a rule for a viewer who falls behind | Decision | README open item for U6 |
| 17 | A batch run's night step has up to nine parts and probably runs on a default pool of 8 (not measured) | Measure; set the size if confirmed | Small | U2 3.7 gap 5 |
| 18 | Events are sent to viewers before they are saved, so a crash in between shows a viewer an event the log never holds (read in code, not reproduced) | Write the chunk's events, then send them; decide what a failed write does | Decision | U3 3.8 gap 7 |
| 19 | The checkpoint allow-list is written by hand, and its test checks Pydantic models and enums but not dataclasses (two state classes are dataclasses) | Build the list from the state types, with the walk extended to dataclasses; pin the derived set in a test. Smaller option: only extend the test's walk | Small | U3 3.7 |
| 20 | A human's answer carries no question id; the server matches it to the seat, so a late retry could be taken as the answer to the seat's next question (inferred from the code, not reproduced) | Send the question's id with the answer and refuse a mismatch, as the seat clocks already do | Small | U4 3.7 gap 1 |
| 21 | "Create a game" has no idempotency key: two requests make two games, and both count against the house's daily limit | A key from the browser, stored with the game row | Decision | U4 3.7 gap 2 |
| 22 | A failed save of a new game's row is ignored and the game starts anyway | Stop the launch when the save reports failure | Small | U4 3.7 gap 3 |
| 23 | The lesson write-back skips games marked as already folded into the store, and no code sets that mark | Set it in the tick, or remove the guard | Decision | U4 3.7 gap 4 |
| 24 | A game that finished just before a restart is completed by recovery without its extraction input, which was held in memory only (read in the code, not reproduced; whether offline extraction can still use such a game is not checked) | Save the extraction input when the post-game step produces it, not at completion | Small | U4 3.5 |
| 25 | A waiting seat's turn deadline is kept in memory, so a restart gives it a fresh 120 seconds | Save the deadline with the game's row and restore it | Small | U5 3.6 gap 3 |
| 26 | A one-human game whose player is connected but idle never times out: it has no turn clock, and the 1-hour rule counts only while nobody is connected | A long turn clock for that case | Decision | U5 3.6 gap 4 |
| 27 | Nothing notices a game that stops producing output without pausing for a human | A check for "no output for N minutes", with a decision about what it does | Decision | U5 3.6 gap 6; U8 |
| 28 | A random fallback vote or night action carries no marker; it looks like a chosen move in the events and the state | Mark the event, as a technical pass is marked | Small | U8 3.6 gap 2 |
| 29 | The engine's log lines carry no game id, so with several games running a rescue or fallback line cannot be tied to its game | Put the game id on every engine log line (a logging filter or context variable) | Small | U8 3.6 gap 3 |
| 30 | A turn-cache hit leaves no record, so a turn with no model call cannot be told from other causes without inference | Record the hit on the turn's span | Small | U8 3.6 gap 4 |
| 31 | `/health` always answers "healthy"; it does not check the database or the trace store | Check the dependencies the server needs | Small | U8 3.6 gap 9 |
| 32 | The prompt capture is written only when a game is over: a game that dies leaves none, and a resumed game's is partial | Write it as the game goes | Decision | U8 3.6 gap 5 |
| 33 | No trace id is stored with the game, and the `events` table has no time column | Store the trace id on the game's row; add a time column | Decision | U8 3.6 gap 6 |
| 34 | Hosted traces carry the release "unknown", so a hosted trace cannot be tied to the code that produced it (checked in the trace store 2026-11-16: 14 of 14 hosted traces among the latest 30) | Done in the build files on 2026-11-16 (see the Done table); it takes effect at the next deploy. Then check one hosted trace | Small | U8 3.6 |
| 35 | Results stamped before 2026-11-16 carry a prompt hash over the 14 top-level prompt files only; model-visible text outside the prompts folder (output schemas, the deduction engine's lines) is still outside the hash | The hash itself is fixed (see the Done table). Left: decide whether the text outside the folder belongs in it | Decision | U9 3.5 gap 1 |
| 36 | The rescue model is not recorded in the fingerprint (the backend half of this row was fixed on 2026-11-16) | Take it from the code that builds the models | Small | U9 3.5 gap 3 |
| 37 | A hosted game carries no fingerprint (the release stamp is row 34) | Pass the fingerprint as run metadata, as the command-line game does | Small | U9 3.5 gap 5 |
| 38 | Nothing compares fingerprints across two separate runs, and a run on a dirty tree cannot be recovered | A switch that refuses a run meant to be cited unless the tree is clean; a small tool that prints the differing fields of two runs | Decision | U9 3.4, 3.5 gap 4 |
| 39 | A failed model call logs the provider's exception without redacting the player's key, and redaction elsewhere matches the exact value only | Redact in the turn's log lines from the game's context variable; add a pattern for the known key shapes | Small | U10 3.6 gaps 1 and 2 |
| 41 | A room host's key travels in the URL; seat tokens are stored as plain text in the database and the browser | Header or body for the host key; a hash for stored tokens | Decision | U10 3.6 gaps 3 and 4 |
| 42 | No `.dockerignore`, no scan for committed secrets, no written rotation procedure | Add the file; a scanning hook; a short rotation page | Small | U10 3.6 gaps 5 and 6 |
| 43 | Not checked: whether a player with no backup key can have a rescue call paid by the house, when the rescue model is from another company | Read the catalogue's rescue rows, then decide | Decision | U10 3.6 gap 7 |
| 44 | A player can pose as the game master by typing `game_master: ...` inside their own message. Measured 2026-11-17: 26 of 27 town votes moved at one saved moment, against 6 of 27 for the same accusation made openly. Partial protection is in place (see Done): players' words in quotation marks with a caption, which roughly halves the effect (`evidence/agent_boundaries/forged_speaker/report.md`) | Make the name impossible to imitate in code: keep the game master's announcements out of the players' discussion section (a structural change), or stop a player's text containing a speaker name followed by a colon (a filter, so it can be reworded around). Then re-run the experiment | Medium | U11 3.3, 3.5 gap 1 |
| 45 | One path into the lesson store (per-game folders) has no check for games with a human seat, and lessons are read as strategy with no label that they may be wrong | Put the check in the path; label lessons as past observations | Small | U11 3.5 gaps 3 and 4 |
| 46 | An agent's message has no length limit in its schema; a person's turns and room creation have no rate limit | A maximum length on the field; a limit per seat and per address | Small | U11 3.5 gaps 5 and 6 |
| 47 | Built on 2026-11-18; see the Done table below. The row as written: model clients were looked up through global accessor functions that read a context variable | — | Done | U10 walkthrough, 2026-11-16; U10 Part 4 |
| 48 | Every release step is by hand; nothing runs the tests before one; the command for going back is not written down | One script for the steps; a test run on every push; a rollback line in the README | Small | U14 3.5 gap 1 |
| 49 | No database backup before a migration or on a schedule, and the server does not check the database's version at start-up | A dump before each migration and nightly; compare the version at start-up and refuse to start | Small | U14 3.5 gaps 2 and 3 |
| 50 | The admin endpoints are off in production (no token set), so the three house settings can be changed only in the database by hand | Set the token, or give the settings the catalogue's script | Small | U14 3.5 gap 4 |
| 51 | The nightly leak audit is documented and not installed on the host | Add the scheduled line; check that it ran | Small | U14 3.5 gap 6 |
| 52 | Two records disagree with the code and the database: `frontend/docs/server_design_notes.md` says the default model was changed through the stored setting (it was the catalogue), and `frontend/docs/build_plan.md` counts 72 releases where the deploy log's table has 76; the frontend release of 2026-10-22 has no log entry | Correct the two lines; add the entry | Small | U14 3.5 |
| 53 | The paid `live` model check (170 tests) runs only by hand, and no run is recorded since 2026-09-10 | Run it on a schedule; record each run's date and result | Small | U13 3.8 gap 4 |
| 54 | The browser test suite keeps its own copy of the server's rules for who may see which event, and it already lacks two event types (`uses_remaining`, `night_record`) | Generate the copy from the server, or check it against the server's rules in one test | Small | U13 3.8 gap 5 |
| 55 | The default test run covers more on my machine than on a clean one: some memory tests use a real Postgres when `WW_POSTGRES_DSN` is set and are skipped otherwise | Say so in the test documentation; give automated runs a test database | Decision | U13 3.1 |
| 56 | `frontend/docs/testing.md` lists 5 of the 8 browser test files | Add the three missing rows | Small | U13 3.8 gap 8 |

## Done while writing the notes

Changed in the working tree; none of it is committed or deployed as of 2026-11-12.

| What | When | Detail |
|---|---|---|
| One object per game, `GameModels` (`Agents/llm_factory/game_models.py`), holds the game's model names, the player's key, the stall count and the clients built on the key. The session and the batch runner build it and pass it to the engine in LangGraph's `context`; the context variable `GAME_LLM` is removed. The object refuses pickle and copy. Committed (`81348121`), not deployed | 2026-11-18 | Row 47; U10 Part 4 |
| A provider's error is scrubbed with the game's keys where it is caught, before it is logged or raised, in every model call of a game. Before, a refusal that quoted the key was saved in the game's checkpoint and logged. Found by a test that plants a key and searches every database table. Committed (`e1ca21fb`, `81348121`), not deployed | 2026-11-18 | U10 3.6 gap 1 |
| A restart test on real Postgres: a served game is stopped mid-game, the server object is rebuilt, and the game plays to its end with scripted players (`tests/server/integration/test_restart.py`). It stops the server object in one process; it does not kill a process. Committed (`1f263a3d`) | 2026-11-18 | Row 9; U3 3.8 gap 1 |
| The prompt hash covers every prompt source file, by path (39 of 41; the two left out are test fixtures), and the fingerprint carries a version number (`fingerprint_schema`: 2). Five tests | 2026-11-16 | Row 35; U9 3.1 |
| The fingerprint's backend field is read from the game model's name, so a Claude game is stamped `anthropic`, not `vertex` (`fingerprint_schema`: 3). Four test cases | 2026-11-16 | Row 36; U9 3.1 |
| In the day's discussion, each player's words are rendered inside quotation marks, with a one-line caption under the heading (`_quoted_text` in `Agents/prompts/prompt_formatters.py`, `PUBLIC_RECORD` in `Agents/prompts/layout.py`). Partial protection against a forged game-master announcement: roughly half as many votes moved. The leak checks were corrected to search plain text as well (`tests/leak_test.py`). 10 new tests; a check with no attack found no change in ordinary play | 2026-11-17 | Row 44; U11 3.3 |
| A player's message is rendered into prompt text as one line (`one_line` in `Agents/prompts/prompt_formatters.py`), so a typed line break can no longer forge a line from the game master or another seat. Applied in the discussion, the wolves' chat, the echo gate, the opening filter and the addressing check; the stored message and the game master's own entries are unchanged. 18 tests (`tests/engine/test_transcript_one_line.py`) | 2026-11-17 | Was row 44, first half; U11 3.3 |
| The game's model selection hides both keys from its printed form (`repr=False` on the main key, as the backup key already had). One test | 2026-11-16 | Was row 40; U10 Part 2 |
| The server image is built with the commit id (`GIT_COMMIT` build argument, set as `LANGFUSE_RELEASE`), so hosted traces stop saying "unknown" from the next deploy. Checked in a throwaway build | 2026-11-16 | Row 34; U8 3.6 |
| The Langfuse client is built by a call at start-up (`init_tracing()`), or on first use, where it was built when `Agents/tracing.py` was imported; the release is passed as an argument | 2026-11-16 | U8 Part 4 |
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
- *2026-11-17 note.* The diagnosis was re-checked and the test repaired (not committed): thread
  order confirmed as the source of the variation, with string hashing ruled out; the bullet was
  spent once in all 70 replays; after the repair, 100 of 100 runs passed, and the test still fails
  under two deliberate double spends. Before-and-after and the reasoning are in
  `vigilante_test/experiment_log.md`.

### What a restart costs (chapter 7 candidate, not ready)

- Findings are in U3 sections 3.6 and 3.8: AI turns of the step in flight are billed again, and
  the log and the engine can disagree about a line. Both are read in code or measured on a small
  stand-in graph (`measurements/u3_kill_resume_toy.py`); neither is reproduced on the real server.
  No fix chosen. Not a story until one is reproduced and fixed.
