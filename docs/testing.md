# Testing guide

For anyone changing code in this repository, including coding agents. It says what to test, how
the tests are organised and run, and what to report before a change counts as finished. The
frontend's own procedures are in [`../frontend/docs/testing.md`](../frontend/docs/testing.md);
this page covers the Python side and the rules common to both.

*Written 2026-11-17. The reasoning behind these rules is in
`evidence/_study/engineering_notes/13_testing_and_verification.md`.*

## 1. What to test

**State the claim before writing the test.** A claim is one sentence about what the system
does, such as "a dead player gets no record of its last night". Write the expected behaviour
and its failure cases first, then the tests. The test's name is the claim, written as a
sentence: `test_a_dead_player_gets_no_record_of_its_last_night`.

**Assert the behaviour, not the implementation.** Check the result a caller or a player would
see. Do not assert that a particular internal function was called.

**For each change, ask these questions and add a test where the answer matters.**

- For each input: what if it is empty, a single item, at a limit, invalid, or a duplicate?
- For each step that writes or sends something: what if the process dies here, the step runs
  twice, or two of them run at once? Was the result confirmed, or only assumed?

**For a fault being fixed, write the test first and see it fail.** Then fix the fault and see
the same test pass. If the test cannot be written first, break the fixed code on purpose
afterwards and confirm that the test fails.

**The claims that cost most if false.** A change that touches one of these needs a test of the
claim itself, and the existing checks for it must still be able to fail:

| Claim | Where it is checked |
|---|---|
| An AI seat's prompt never contains another seat's private information | `tests/leak_test.py`, used by the engine tests and by `scripts/run_batch.py` |
| Each night's actions are settled by the rules | `tests/engine` (the resolution and night tests) |
| Every fact the deduction engine writes into a prompt is true | `tests/engine/deduction` |
| A player's own API key is never written out | `tests/server/test_byok.py` (the error text, the crash report, the model clients); `tests/server/integration/test_planted_key.py` (every table of the database, after a whole game and after a game killed by a provider's error) |
| A prompt changes only on purpose | The prompt golden (section 4) |
| The server and the browser agree on the API | `tests/server/test_openapi_snapshot.py` |
| A game survives a server restart | `tests/server/test_durability.py`, against test doubles (a test double is any replacement for a real dependency in a test: a stub, a mock or a fake); `tests/server/integration/test_restart.py`, a real game stopped and recovered on a real Postgres database |

`run_leak_tests` in `tests/leak_test.py` runs seven checks over every prompt of a game. The
file holds more checks than these seven; the payload leak tests in `tests/engine` call the
others directly.

**A test cannot show what a model does.** The default tests replace the model with a scripted
one (`tests/factories/scripted_model.py`). They show that a prompt is built as intended, and
nothing about how a real model responds to it. A change that is meant to alter a model's behaviour needs a measured run with the real
model, with its sample size stated. Those runs belong in `evaluation/` and `evidence/`, are not
part of the test suite, and cost money: ask before running one.

## 2. How the tests are organised and run

**Commands.** Always through Poetry, from the repository root.

| Command | What it runs | Time |
|---|---|---|
| `poetry run pytest tests/<folder>` or a single file | The tests for the part being changed | Seconds to a few minutes |
| `poetry run pytest` | The quick default set: everything except the tests marked `contract` and those marked `slow`. It includes the `integration` tests, so Docker must be running | About 3 minutes (3 min 12 s on 2026-11-18) |
| `poetry run pytest -m "not contract"` | The full local run: the default set and the `slow` tests | About 9 to 10 minutes (9 min 22 s on 2026-11-18, on a quiet machine) |
| `poetry run pytest -m slow` | The `slow` tests alone: the ten deduction tests over random games | About 6 minutes (the ten took 6 min 9 s of the full run on 2026-11-18) |
| `poetry run pytest -m contract` | Tests that call paid models with real credentials | Costs money. Never run without the owner's agreement |
| In `frontend/`: `npm test`, `npm run typecheck`, `npm run lint` | The frontend's unit tests, types and lint | About a minute |
| The browser suite | See `frontend/docs/testing.md`, "How a run is done here" | About 16 minutes |

**Where a test goes.**

| Folder | Holds |
|---|---|
| `tests/engine` | The game: rules, night resolution, deduction, prompt assembly, whole games with a scripted model (`tests/engine/test_whole_game.py` and a few others) |
| `tests/memory` | Lessons: extraction, duplicates, storage, retrieval, and the schemas of lessons and extraction (seven files moved here from `tests/engine` on 2026-11-18) |
| `tests/evaluation` | The evaluation code |
| `tests/server` | The game session, the API, the translator, durability |
| `tests/<component>/integration/` | Tests that need a service started for the test run. Today the service is a Postgres database in a container. `tests/server/integration` holds the replay storage round trip, the restart test, the planted-key test, the evaluation-case storage tests and the game-record storage test; `tests/memory/integration` holds the consolidation database tests and the served-game extraction tests. Every test in a folder named `integration` gets the `integration` marker from `tests/fixtures/collection.py`, so the files do not mark themselves |
| `tests/contract` | Paid checks of an outside provider, such as whether each menu model still returns valid structured output; each carries `@pytest.mark.contract` |
| `tests/fixtures` | Fixtures, one module per resource, registered in `tests/conftest.py`; the golden files |
| `tests/factories` | Functions that build test data. Import them; they are not fixtures |

The component folders (`engine`, `memory`, `evaluation`, `server`) hold every test that runs
in one process. This includes the whole-game tests: they run several real parts together (the
game graph, the rules, the prompts, the server's translator), but they need nothing outside the
process, so they are not integration tests. A test goes into an `integration/` folder only when
it needs a service that is started for the run.

`tests/contract/test_credential_missing.py` costs nothing and carries no marker, so it runs in
the default set; it checks the skip rule of the paid test beside it.

Before writing a new fixture, builder or test double, look in `tests/fixtures` and
`tests/factories` for one that already does the job. A test file must not import helpers from
another test file: a helper that two test files need goes into `tests/factories`.

**Shared setup for whole games.**

- `tests/factories/scripted_model.py`: the scripted model. It fills any output schema with a
  valid object drawn from a seeded generator. Its module docstring says what it returns for each
  field type and what a test that uses it cannot show. The same file holds `ScriptedModels` and
  `FakeModels`, two kinds of `GameModels` (`Agents/llm_factory/game_models.py`): the object
  through which the game's code receives its models. The game reads it from the graph context
  (`context["models"]`); a function called on its own takes it as the argument `models=`. A test
  hands its fake models over this way and does not patch the functions that build the real ones.
  `FakeModels(seat=..., judge=..., ...)` returns the fake given for each kind of model.
  The same object holds what belongs to one game: the player's key, the count of stalled
  turns (`models.health`) and the scrubbing of a key from an error text (`models.redact`).
  So a test of stalls asserts `health` on the object it passed in, and a test about a key
  gives its fake the key: `FakeModels(seat=..., api_key=..., model=...)`. For a hosted game,
  `give_models(session, models)` (`tests/factories/served_game.py`) copies the session's
  model names and keys onto the test's object before it takes the session's place.
- `tests/fixtures/model.py`: the fixture `scripted_model`. It returns a function; call it with a
  seed (and, optionally, the seats no scripted player may choose). It returns a `ScriptedModels`,
  which the test puts in the graph context: every seat's turn then runs on the scripted model,
  with no rescue model. The function also replaces three functions of the game with
  `monkeypatch`, undone when the test ends: the day summary (returns a fixed text), the opening
  filter (keeps every line) and the echo check (finds no echo). These three stay replacements
  of whole functions because a scripted model would answer them with random verdicts, which
  would hold random lines and change every game the tests play.
- `tests/fixtures/graph.py`: the fixture `game_graph`. It gives each test the game graph compiled
  with its own in-memory checkpoint store. The graph that production compiles at import keeps one
  store for the whole process, keyed by game id, so two tests that played the same game id
  shared one game's state.
- `tests/factories/whole_game.py`: `play_game(graph, game, seed, models=...)` plays one game to
  its end on the models given (the fixture's `ScriptedModels`) and returns the final state, the
  events the translator made and the night branches that reported.

**Shared setup for a real database.** Nothing here is autouse: the container starts only when a
test asks for a database, and a run that selects no such test needs no Docker.

- `tests/fixtures/database.py`: `postgres_container` starts one Postgres container for the run
  (the image production's database runs, `pgvector/pgvector:pg17`) and stops it at the end. If
  Docker cannot be reached, the test that asked for it fails with a message saying so; it is not
  skipped. `postgres_dsn` gives each test a fresh, empty database in that container, as a
  `postgresql://` address, and drops it after the test. `server_tables_dsn` is the same database
  with the server's tables made by its migrations (`alembic upgrade head`), which also seed the
  puppet and model catalogues. `sqlalchemy_url(dsn)` turns an address into the form the server's
  SQLAlchemy engine takes. Each test gets its own database, not a rolled-back transaction,
  because the checkpoint saver, the lesson store and the game repository commit on connections
  of their own.
- `tests/factories/served_game.py`: `open_server(dsn)` builds what the server's startup builds
  (the graph runtime with the Postgres checkpoint saver and the lesson store, the game
  repository, the live game registry), and `stop()` shuts it down the way the server does. The
  same file has the steps of playing a hosted game: put the test's models in a session's graph
  context, wait for a human seat's question, hand every question to the seat's agent until the
  game ends.
- `tests/fixtures/model.py` also has `refuse_real_models`: while it is in use, building any
  real chat model raises. The integration tests that play a game use it, so a code path that
  misses the test's models fails instead of calling a provider.
- Never change engine or server code to make a test fail (to show the test can fail) while
  another test run is in progress in the same folder: the other run sees the broken code. On
  2026-11-18 this sent one real request to a provider. Use `refuse_real_models` in the test
  first, and check that no other run is going.

**Markers.** A marker is a label on a test that a command can select or leave out with `-m`.

| Marker | What it means | In the quick default |
|---|---|---|
| `slow` | The test takes over 20 seconds in the full run on the development machine. The 20 seconds is a starting value | No |
| `timing` | The test waits real time and asserts a time window, so it can fail on a slow machine | Yes |
| `integration` | The test needs a service started for the run (a Postgres container, so Docker must be running) | Yes |
| `contract` | The test calls a real outside provider and costs money | No |

Mark a new test `slow` when it passes the 20-second line, and run `-m "not contract"` before
reporting a change to the code a `slow` test covers. When a `timing` test fails, run it alone
once. If it then passes, report the failure with the load on the machine at the time; if it
fails again, investigate it like any other failure. No plugin reruns a failed test
automatically.

**A test must give the same result on every run and on any machine.**

- No call to a real model, a real network service or the live database in the default set.
  `tests/conftest.py` switches tracing off and fixes the model list; do not undo that in a test.
- A test that needs a real Postgres database takes it from the fixtures in
  `tests/fixtures/database.py`, which put it in a container started for the run. No test reads
  the development database address (`WW_POSTGRES_DSN` in `.env`), and no test may write to that
  database.
- Fix the seed of anything random. If code under test runs on several threads, do not let the
  result depend on which thread draws from a shared generator first: either give the test a
  situation where the order cannot matter, or assert something that holds in every order.
- No fixed waits for work that can take longer.

## 3. How a test is written

- The name is a sentence that states the claim (section 1).
- The body is in three blocks marked `# Arrange`, `# Act` and `# Assert`, with a blank line
  between blocks and one step per line. A test of three statements or fewer needs no block
  comments.
- A test with several rounds (act, assert, act again) labels each round with a comment.
- A short comment beside an expected value says why it is expected, when that is not obvious.
- Use plain pytest functions and fixtures, not `unittest` classes.
- Before adding a test that differs from another only in its inputs, parametrise the existing
  test with `@pytest.mark.parametrize`.
- Never write a test whose only assertion is that a mock was called. Assert what the caller or
  the player would see.
- Assert the claim, not the current value of a setting. A test that reads a setting and asserts
  today's value fails when the setting changes and says nothing about the code. The cost-guard
  tests in `tests/memory/test_store_ops.py` are the example: they set the models explicitly and
  assert how those models reach the three environment variables a tick sets.

**Names of fixtures and test doubles.**

- A fixture that returns a real object gets a plain name: `api_client`, `game_graph`.
- A fixture that returns an object made with the mock library is named `mock_<thing>`.
- A hand-written test double is a class named `Fake<Thing>`. When it exists for one behaviour, the
  name says which: `HangingGraph`, `FailingStore`, `RecordingGameRepository`.
- A test double used in one file only starts with an underscore.
- A stand-in for a model is called a model, not an LLM: `ScriptedModel`, `_StalledModel`.

## 4. Goldens

A golden is a saved output that a test compares with the new output, whole. Regenerate one only
after a change that was meant to alter it, and read the whole difference before keeping it.

| Golden | Regenerate with |
|---|---|
| The day-discussion prompt | `poetry run python -m tests.fixtures.day_discuss_prompt_golden` |
| The translator's events | `poetry run python -m tests.fixtures.translator_golden` |
| The API description and the frontend's types | `npm run generate-api-types` in `frontend/`; commit both files |
| Frontend beat goldens and screenshots | See `frontend/docs/testing.md` |

A change to the prompt golden changes what every AI seat is sent. Evaluation results from
before and after it are not comparable, so say so in the report.

## 5. Before a change counts as finished

**What to run.**

- While working: the tests for the part being changed.
- Before reporting a change to `Agents/`, `server/`, `evaluation/` or `tests/` as finished: the
  whole default set, once. A change can weaken a check elsewhere, and only the full run shows
  it.
- For a frontend change: the unit tests, the type check and the lint, plus the browser specs
  the change affects.
- A change to documents only needs no test run.

**What to report.**

1. The commands that were run, and the counts: passed, failed, skipped.
2. Each new test, with the claim it checks, and how it was shown able to fail.
3. What the new tests replace with a test double, and so do not check.
4. Each golden that was regenerated, and the reason for each difference.
5. Anything that was not run, and why.

**When a test fails.**

- Do not weaken, skip or delete a failing test to make the run pass. If the test is wrong, say
  why and change it as its own step.
- Do not rerun a test until it passes. A test that passes on some runs and fails on others has
  a cause; report it with the number of runs and failures.
- Several agents work in this folder at once. If a failure comes from someone else's
  uncommitted edits, report it and leave their files alone.

**A passing run is evidence about the working folder on this machine.** No service runs the
tests automatically, and no release step runs them. Say "the tests pass on the working folder",
not "validated", unless the claim was measured.

## 6. What CI runs

`.github/workflows/ci.yml` (GitHub Actions) runs the backend's tests from a clean checkout:
no `.env`, made-up provider keys, and the packages of `poetry.lock`.

| When | What runs |
|---|---|
| Every push to any branch | The lock check (`poetry check --lock`), the lint report, the quick tests, the timing tests |
| A push to `main`, a pull request to `main`, or "Run workflow" by hand | The same, then the integration tests, the slow tests, and a build of the server image in which the server must start and answer |

A push that changes only Markdown files, `writeup/`, `frontend/` or `evidence/` starts no run.
The exception is `evidence/gameplay/deduction/data/`, which four test files read.

What this means for a test:

- It must pass without `.env` and without a real provider key. A test that needs one belongs
  in `tests/contract`, which CI never runs.
- A data file it reads must be committed. A test that reads a file git ignores skips in CI
  (one does today: `tests/evaluation/test_model_admission_pipeline.py`, which says so in its
  skip reason).
- The lint report and the timing tests are shown and do not fail the run. Everything else does.

CI does not replace the full local run before a change is reported as finished: on a branch
other than `main`, CI runs the quick tests only.
