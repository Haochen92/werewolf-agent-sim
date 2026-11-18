# U13 working map: the backend tests, folder by folder

<!-- Writing rules: docs/writing/core_rules.md. -->

A map of `tests/engine`, `tests/server`, `tests/memory`, `tests/evaluation`, `tests/live` and the
shared setup, made on 2026-11-17 for the review that follows U13
([13_testing_and_verification.md](13_testing_and_verification.md)). It is a working record, not a
note: it lists what each group of tests protects, what is real in it, and what is wrong with the
structure, so that I can decide which set each group belongs to and which tests to read closely.

**How it was made.** Two read-only passes by coding agents, which read the test files and ran
only `poetry run pytest --collect-only`. No test was run for this map, so it says nothing about
whether a test passes. Durations come from the saved full run of 2026-11-17. Ten findings were
then checked against the code by a second read; those are marked **checked**. Everything else is
the agents' reading. "Inferred" marks a conclusion drawn from the code without a run.

**Counts.** 2,652 tests: engine 1,436 (72 files plus 16 in `deduction/`, by the agent's count),
server 311 (19 files), memory 334 (35 files), evaluation 392 (41 files), live 179 (170 marked
`live`).

## 1. Findings that matter most

Ordered by what they cost if left alone.

| # | Finding | Step | Status |
|---|---|---|---|
| 1 | **One default test connects to the database the development `.env` points at, creates tables and commits.** `test_db_roundtrip_in_temp_schema` ([test_consolidation_graduation.py:137](../../../tests/memory/test_consolidation_graduation.py#L137)) relies only on `SET search_path TO pg_temp` to keep its tables temporary. Three more memory tests create and drop a throwaway database on the same server. The testing guide says a test must never write to that database | 4 | **checked** (the code); that `pg_temp` keeps the tables temporary is not verified |
| 2 | **No test reads a real Postgres checkpoint back and resumes a game.** In every recovery test the checkpoint is a hand-built object and the stored events are an empty list. The one real-Postgres server test (`test_postgres_round_trip`) is skipped here and does not cover the functions recovery uses | 2 | agent's reading |
| 3 | **Four of the nine batch leak checks have no test showing they can find a leak.** Two of them look for fields of the old nine-seat game, by their own descriptions ([leak_test.py:105](../../../tests/leak_test.py#L105), [:138](../../../tests/leak_test.py#L138)). The agent infers that three checks can only return "no leak" on a ten-seat game | 5 | descriptions **checked**; the inference is not |
| 4 | **A stub is left in place for the rest of the run.** [test_dedup_thresholds.py:113](../../../tests/memory/test_dedup_thresholds.py#L113) creates `pytest.MonkeyPatch()` and never undoes it, so the embedding and similarity stubs stay for every later test | 4 | **checked** |
| 5 | **A fresh clone gives a different result.** [test_memory_persistence.py:158](../../../tests/memory/test_memory_persistence.py#L158) asserts that `memory_stores/v6_1` exists, and that folder is git-ignored. Two evaluation tests skip without notice when a data file is absent. This will show on the first CI run | 4 | **checked** (the first); the two skips are the agent's reading |
| 6 | **The `slow` marker is declared and used by no test.** The ten slowest tests are all deduction tests over random games: six take 73 to 101 s, four take 22 to 26 s, about 9.5 minutes together | 4 | **checked** (the marker) |
| 7 | **Some tests cannot fail.** [test_byok.py:82](../../../tests/server/test_byok.py#L82) asserts only when the Gemini client carries a key, and on this machine it is built without one (inferred). [test_retrieval_judge_fallback.py:30](../../../tests/evaluation/test_retrieval_judge_fallback.py#L30) sets a field to False and asserts it is False. [test_ten_seat_game.py:349](../../../tests/engine/test_ten_seat_game.py#L349) matches a player's name with `in` on a string, so `player_1` would match `player_10` | 5 | **checked** (all three passages) |
| 8 | **Whole-game tests share one process-wide checkpoint store, keyed by game id.** The seeds were chosen by hand so that no two tests use the same id. A reused id would resume another test's game | 4 | agent's reading |
| 9 | **Timer tests in `test_game_session.py` wait real time** (0.2 to 0.6 s) and assert narrow windows. They could fail on a loaded machine (inferred, not measured) | 4 | agent's reading |
| 10 | **The nightly leak audit of hosted games exists and is tested, and is not scheduled on this machine.** U13 step 1 says hosted games are not checked; more exactly, the check exists (`server/housekeeping/leak_audit.py`, 7 tests) and nothing runs it. Production code there imports from `tests/leak_test.py` | 1 | not scheduled: **checked** |

## 2. `tests/engine` (1,436 tests, 14 groups)

No engine test connects to a database or the network, and none carries a marker other than
`parametrize`.

| Group | Tests | What it protects | What is replaced | Problems |
|---|---|---|---|---|
| 1. Night rules and resolution | 124 | Night precedence, the vote, who wins, the same game id deals the same roles | No model is called; one helper and Langfuse are replaced | Private copies of the shared night runtime |
| 2. The public record as data | 90 | Morning announcements, wills, the dead roster, the claim ledger | The scripted model, in the one whole game it plays | Reads `evidence/...` by a relative path |
| 3. Day flow and turn order | 103 | The order of opening, discussion, closing and vote; who gets the floor | The whole agent turn, by a scripted table, so no prompt is built; the judges | Uses no shared setup |
| 4. Prompt assembly and the prompt golden | 101 | The day-discussion prompt of every role; quoting; the shared prefix; private records reach only their owner | The model, by one that records what it was sent | The golden covers one hand-built board and one lineup |
| 5. What the model is asked to return | 55 | Output schemas; reads are given only to their author | A third private scripted model | |
| 6. Memory and extraction schemas | 126 | Schema field order; lesson verdict counters; extraction cells | A private fake store | **Belongs in `tests/memory`** |
| 7. Leak checks on the payload builders | 31 | A seat's payload carries only that seat's private fields | Nothing; states are written by hand | See finding 3 |
| 8. Whole games and rules random play cannot reach | 35 | A whole game runs on the real graph; the Vigilante's bullet; uses spent once a night; a dead player gets no record | The model, by the scripted model; four helper calls | One file mixes whole games, pause and resume, and 31 rule tests. Findings 7 and 8 |
| 9. Human seat and pause and resume | 76 | A resumed answer is validated; a human turn is announced; every model in the state survives a checkpoint round trip | The pause itself (`interrupt` is replaced); one test uses a toy graph, not the game | The only resume of the real game graph is the Vigilante test |
| 10. Model selection, fallback, prices | 83 | A failing seat is rescued before a random action; a schema break is retried; prices by date | Every model accessor; no real database | The repository's `.env` is loaded at import, so real keys are in the process |
| 11. Run setup, records, tracing, metrics | 66 | The run configuration's shape; the prompt hash; tracing is built by a call, not on import | Up to eight dependencies in one file, the graph included | `test_import_order` starts a new Python process per module, about 35 s in all |
| 12. Deduction, own results | 120 | Every line a seat reads about its own night is true in the real game | Nothing | One of the ten slowest |
| 13. Deduction, levels 2 to 7 and the evil seat | 212 | Every public fact, candidate, join, conditional and comparison holds; no possible deal is left out | Nothing | **Nine of the ten slowest** |
| 14. Deduction rendering, acceptance, role traits | 214 | Lines fold and order as specified; the role-traits table matches the night rules | The scripted model, in two whole games | Reads `evidence/...` by a relative path |

## 3. `tests/server` (311 tests)

All of `server/` is deployed code. Whether the deployed revision equals the working tree was not
compared.

| Group | Tests | What it protects | What is real, what is replaced |
|---|---|---|---|
| Game session | 61 | Each event reaches only the seats allowed to see it; a person's turn pauses, is validated and resumes; timers and presence; a failure before the end ends the game with its error | Real session, translator and seat clocks. The graph is replaced by one that replays chunks recorded from a real game. Finding 9 |
| HTTP API and lobby | 63 | Create, join and start; the seat cookie; a turn needs a proven seat; the status shows only the viewer's own pending turn; key rules | Real application and lobby behind a test client. Key checks always succeed |
| Translator and events | 58 | Every chunk of a real game is handled; sequence numbers increase; a night record reaches only its actor; the output equals the two goldens; the server's copied lists match the engine | Real translator over recorded chunks. Nothing replaced |
| Contracts | 35 | Every event class has a tier and survives a JSON round trip; the API description equals the saved one | Real schemas. The saved description is compared with the server, not with the generated TypeScript types |
| Durability, recovery, sweeper | 27 | The write path, retries of unsaved events, revival of parked games, expiry | Real recovery logic. The graph, the checkpoint and the database are all replaced. Finding 2 |
| Player keys and crash reports | 17 | A key goes only to its own provider; a dead game's error text never holds the key; a crash report carries no keys | Real client objects with no network call; the real Sentry SDK with a capturing transport. Finding 7 |
| House and usage limits | 17 | Who pays; the daily cap and the kill switch; token counts survive a restart | Real policy and meter; private fake settings and repository |
| Replays, storage, cast | 26 | Replay objects drop private fields; a failed write is not acknowledged; the cast is drawn without repeats | Mostly fakes. One real-Postgres test, skipped unless `WW_REPLAY_TEST_DSN` is set; it deletes nothing, so a second run on one database would fail (inferred) |
| Leak audit of hosted games | 7 | The audit finds a clean game clean and flags a planted leak | Real payload builders and checks; fake stores. Imports helpers from two other test files |

**The guard against the development database** (`tests/fixtures/server.py`) blanks the server's
setting for every test. It does not change the environment variable, so the four memory tests
that read the variable directly are not covered by it (finding 1).

## 4. `tests/memory` (334 tests) and `tests/evaluation` (392 tests)

The "Runs today?" column answers the question for deciding sets: does the code under test still
run in the server, in the consolidation tick, or in an evaluation runner the README names?

| Folder | Group | Tests | Runs today? |
|---|---|---|---|
| memory | Extraction | 46 | Partly: input formatting runs after each game; extraction itself is offline; one function has no caller (inferred) |
| memory | Duplicates | 79 | Offline only: the consolidation tick and evaluation |
| memory | Storage and publishing | 17 | Yes: the server opens the store with this code |
| memory | Retrieval | 102 | **Yes, in hosted games** |
| memory | Grading and credit | 75 | The tick; part is also used by the engine's board clocks |
| memory | Synthesis | 15 | The tick |
| evaluation | Data plane | 40 | Yes: used by the batch runner and at run time |
| evaluation | Judges and labelling | 32 | Mixed: one judge serves closed research; one builder has no importer (inferred) |
| evaluation | Owner checks | 31 | Not determined |
| evaluation | Hallucination bench and screen | 28 | Yes: named in the README |
| evaluation | Model admission | 15 | Yes |
| evaluation | Audits and instrument validation | 66 | Mixed |
| evaluation | Credit, tagger, tells and reads | 82 | **Mostly closed research** (the frozen nine-seat graders) |
| evaluation | The frozen v7 loop and replay | 98 | **Mostly closed**, except `test_loop_merge` and `test_board_clocks`, which test production code |

So about 180 evaluation tests guard research code that is closed, and nearly all memory tests
guard code that still runs somewhere.

## 5. `tests/live`

- `test_model_structured_output.py` (170, marked `live`): one paid call for each pair of a menu
  model (10) and a seat schema (17), asserting that the reply validates. The model list comes from
  the seed in code, not from the database's menu (inferred). The only record of a run is the
  note in the file: 2026-09-10.
- `test_credential_missing.py` (9, not marked, free): runs by default. The testing guide says
  every test in this folder carries the marker, so this file is in the wrong folder.

## 6. Shared setup

- `tests/conftest.py` registers three plugins and pins four environment variables with
  `setdefault`, so a value already set in the shell wins over the pin.
- `tests/fixtures/`: the recorded game chunks, the server fixtures (session, API client, fake
  graphs), and the two golden modules. `tests/factories/`: builders, event factories, random
  nights, random claims, and the brute-force oracle. Every fixture and builder has a user.
- **Copies kept in test files instead of the shared modules:** three scripted models; the night
  runtime (written inline eight times in one file); at least twelve private state builders; six
  fake repositories in the server tests; fake stores in the memory tests.
- **Test files used as libraries.** Helpers such as `_play`, `night_state`, `Table` and
  `RecordingGameRepository` live in test files and are imported by other test files, in all four
  folders.

## 7. Structure, against `docs/testing.md`

- **Wrong folder:** engine group 6 (126 tests) belongs in memory; `test_board_clocks` and
  `test_loop_merge` in evaluation test production code; a few memory files test the provider layer
  and tracing.
- **Names that are not sentences:** few in engine and server; about a third of the memory tests;
  about 60 to 80 of the evaluation tests.
- **Files that mix subjects:** `test_ten_seat_game.py`, `test_game_session.py` (53 tests on nine
  subjects), `test_draft_preview.py`.
- **Skipped without notice:** the real-Postgres tests when their variable is unset, and two
  evaluation tests when a data file is absent. A skip shows only with `-rs`.

## 8. Decisions for me

1. **Sets.** Which groups run on every push, which on a schedule, which by hand. The candidates
   for a `slow` set are the ten deduction tests of finding 6. The candidates for a set outside
   the default are the roughly 180 evaluation tests on closed research.
2. **The database tests.** Whether the four memory tests that reach the `.env` server stay in the
   default set, move behind a marker, or get a fixture that refuses that address (finding 1).
3. **Which findings to fix before CI.** Findings 4 and 5 will affect a clean machine. Finding 7
   is three small assertion fixes.
4. **Shared setup.** Whether to move the scripted model and the fake repositories into
   `tests/factories` and `tests/fixtures` now. A kill-and-restart test (finding 2) would need the
   scripted model there, and a test-database fixture that does not exist yet.

## 9. Candidates for a close reading

Three kinds: a costly claim, a story I already know, and a weak test.

| Test | Why |
|---|---|
| [test_ten_seat_game.py:160](../../../tests/engine/test_ten_seat_game.py#L160) the Vigilante test, with the scripted model at lines 42 to 86 | The story I know; the only resume of the real game graph |
| [test_night_payload_leaks.py:185](../../../tests/engine/test_night_payload_leaks.py#L185) a full run of the leak checks is clean | Costly claim; for four of the nine checks this assertion cannot fail (finding 3) |
| [test_byok.py:169](../../../tests/server/test_byok.py#L169) a dead game's error never holds the key | Costly claim; it checks the session's error only |
| [test_durability.py:322](../../../tests/server/test_durability.py#L322) a parked game revives and resumes | The main restart test; shows the registry's logic, not a real checkpoint |
| [test_draft_preview.py:45](../../../tests/engine/test_draft_preview.py#L45) the prompt golden | Costly claim; read with the board it is built from to see which sections stay empty |
| [test_subgraph_interrupt.py:58](../../../tests/engine/test_subgraph_interrupt.py#L58) a pause inside a subgraph | Weak by its own description: it passes even if the helper it exercises returns nothing |
| [test_ten_seat_game.py:341](../../../tests/engine/test_ten_seat_game.py#L341) a dead player gets no record | Weak assertion (finding 7); it is the example name in the testing guide |

## Not checked

- No test was run or timed for this map.
- The agents did not read every test body. Groups and claims rest on file descriptions, test
  names, imports and searches; the passages cited by line were read.
- Whether the random-game tests change with Python's string-hash seed.
- Whether any result in engine group 10 depends on the real keys loaded from `.env`.
- Which server revision is deployed.
- The engine file count: the agent reports 88 files, and my own count of file names gave 86.
