# U13. Testing: what a passing test shows, and what it does not

**Reading time:** about 35 minutes for Parts 1, 3 and 5 (estimate) · **Builds on:** U0 (which part holds which fact) · **Related:** U3 (the restart path, tested against stand-ins), U9 (what a result was made of), U10 (the planted-key test), U11 (the forged game-master line), U14 (no tests before a release) · **Feeds write-up chapters:** 7 and 8

**The question:** the tests pass. What do I now know, and what do I still not know?

**First answer, before reading on:** two or three sentences, with an example that is not from
this project.

**Suggested first read (2026-11-17).** Parts 1, 3 and 5. Parts 2 and 4 and Appendix B are
reference. A coding agent writes most of my test code, so the aim of this reading is to judge
and direct tests well enough, not to learn a catalogue of test types: what to test, how to read
a test, and what a run in which every test passes establishes. Setting up continuous
integration is a separate build task after this note.

## The core idea

A test runs some code under conditions it sets up, and checks one claim about the result. A
pass is a fact about that run only.

```text
A pass establishes:   for this revision of the code,
                      in this environment,
                      on these inputs,
                      with these parts replaced by stand-ins,
                      the property the test checks held.

It says nothing about: other inputs, the parts that were replaced,
                       and any property the test does not check.
```

An LLM application needs two kinds of verification. Tests check the code around the model:
how the prompt is built, how the answer is validated, what each user is allowed to do. They
give the same result every time, so they can run on every change. Evaluations send real inputs
to the real model and count what it does. They cost money, they give rates rather than pass or
fail, and they are the only way to learn whether a change altered the model's behaviour.

---

# Part 1 — Fundamentals

Throughout Part 1, the example is the support assistant from U8 to U11. A language model reads
customer emails and decides what to do: look up an order, request a refund, send a reply. The
model's requests go to ordinary code, and a refund service in that code checks every refund
before it is paid.

## 1.1 What a passing test establishes

A test has three parts: it sets up a situation, performs an action, and checks the result
with an **assertion**, a statement in code that must be true or the test fails. For the
support assistant:

```text
Set up:  an order of 100 euros
Action:  ask the refund service to refund 150 euros
Assert:  the refund is refused
```

When this test passes, it establishes that the refund service refused that request, in that
run. It does not establish that the service refuses 101 euros, that no money reaches the real
payment provider when a refund is refused, or that the model ever asks for the right amount.
Each of those is a separate claim, and needs its own check.

Three questions decide what a test is worth. They matter most when someone else, or a coding
agent, wrote it:

| Question | Why it matters |
|---|---|
| Can it fail? | A test whose assertion is true whatever the code does proves nothing. The usual check is to break the code on purpose and see the test fail |
| Does it check the claim, or the implementation? | "The refund is refused" is the claim. "The function called `check_limit` once" is the implementation. A test of the implementation fails when the code is reorganised and still passes when the rule is wrong |
| What does a pass not prove? | The inputs not tried, the parts replaced by simplified stand-ins during the test (1.3), and everything the assertion does not mention |

Because a pass is so narrow, two claims about a change must be kept apart. **Deployed** means
it is running where users can reach it. **Validated** means a test or a measurement has shown
that it works. A change can be deployed without being validated, and validated on one machine
without being deployed.

## 1.2 Levels of verification

Tests are grouped by how much of the system each one runs.

| Level | What it runs | What it is for | What it misses, or costs |
|---|---|---|---|
| **Unit test** | One function or class, with its dependencies replaced | A rule or calculation, checked on many inputs in milliseconds | Whether the parts work together |
| **Integration test** | Several real parts together, such as the code and a database, or two services | The boundaries between parts: formats, order of calls, error handling | Any part that is still replaced, and the user's task as a whole |
| **End-to-end test** | The whole system as a user meets it, usually through a browser | That a complete task works from the outside | Each test takes seconds or minutes, and a failure does not say which part is at fault |

The usual advice is many unit tests, fewer integration tests and a few end-to-end tests,
because the lower levels are fast and point at the fault, and the higher levels catch what the
lower levels cannot. This shape is often called the **test pyramid**.

Two kinds of test sit at the boundaries. A **contract test** checks that both sides of an
interface still agree, for example that the order service's response still has the fields the
assistant's code reads. A **smoke test** (U14) sends a few real requests to a newly started
system to check that it is serving at all.

## 1.3 Test doubles: what a stand-in hides

A dependency that is slow, costs money, or gives a different answer each time is usually
replaced in tests. The general term for the replacement is a **test double**; this note also
calls it a stand-in. There are several kinds:

| Kind | What it does | Support-assistant example |
|---|---|---|
| **Stub** | Returns fixed answers | A model that always replies `{"action": "refund", "amount": 40}` |
| **Mock** | Records how it was called, so the test can check the calls | A payment client; the test asserts it was called once with 40 euros |
| **Fake** | A working but simplified implementation | An order store held in a Python dictionary instead of the database |

A stand-in makes a test fast and repeatable. The cost is that the test says nothing about the
real dependency. A stub model always produces a valid refund request, so the test cannot show
what the real model asks for, how often its answer is malformed, or how long it takes. A fake
order store does not have the real database's constraints or its behaviour under two writes at
once.

A stand-in can also make a test pass for the wrong reason. Suppose the assistant holds an API key
for its model provider, and the code removes the key from any error message before the message
is logged. U10 described a **planted-key test** for this: a made-up key is used for a whole
conversation, and every place the system writes to (logs, database, error reports) is searched
for that exact string. It is also called a canary, after the bird miners used to detect gas: it
reveals a leak that would otherwise go unseen. To test the failing path, the stand-in provider
must fail with an error that contains the key, as a real provider's error may. A stand-in that
fails with a clean message passes the test without ever running the code that removes the key.

## 1.4 Deterministic tests and evaluations of the model

A test is **deterministic** when the same code and inputs give the same result every time. A
model's answer is not: the same prompt can give a different answer on each call. So an LLM
application is checked in two different ways.

| | Deterministic test | Evaluation with the real model |
|---|---|---|
| What it checks | The code around the model: prompt assembly, validation, permissions | What the model does with that prompt |
| Result | Pass or fail | A count or a rate with its sample size, such as "an over-large offer in 7 of 50 test emails" |
| Cost and speed | Free, seconds | Model calls that cost money, minutes or hours |
| When it runs | On every change | When a change is meant to alter behaviour, or on a schedule |

Neither replaces the other. Suppose the support assistant's prompt gains the sentence "Never
offer a refund larger than the order total." A unit test can check that the sentence is in the
prompt, in the right place. Only an evaluation can show whether the model now offers smaller
refunds. And the guarantee that matters does not come from either: it comes from the refund
service refusing large refunds in code (U11, section 1.5).

## 1.5 Exact-text tests: what a golden protects

A **golden test**, also called a **snapshot test**, saves an approved output once and compares
every later output with it, whole. For the support assistant, the golden could be the complete
prompt sent to the model for one saved email. Any change to the prompt, intended or not, makes
the test fail.

That is what a golden protects: it detects a change anywhere in a long output that nobody
would think to check line by line. A golden is said to **pin** the output: the output cannot
change without the test failing. A prompt is a good candidate, because a stray change to one
sentence changes the model's behaviour and is easy to miss.

It does not establish that the saved output was correct. It establishes only that the output
has not changed since someone last approved it.

A golden stops protecting in two ways:

- **It is regenerated without being read.** An intended change makes the test fail, and the
  fix is to regenerate the golden. If regenerating becomes routine and nobody reads the
  difference, an unintended change is approved along with the intended one.
- **Its input is not representative.** A golden built from one saved email pins what happens
  to that email. It says nothing about an email with an attachment, if none of the saved
  inputs has one.

## 1.6 Flaky tests

A **flaky test** passes on some runs and fails on others, with the same code. The usual
causes:

| Cause | Example |
|---|---|
| Shared random state | A test fixes the generator's starting value (its **seed**) so that every run draws the same numbers. But two threads draw from that one generator, so which thread gets which number depends on which runs first, and the runs differ after all |
| Timing | A test waits a fixed half second for work that sometimes takes longer |
| Order between tests | One test leaves data behind that another test depends on |
| Outside services | A test calls a real model or a real network service |

A flaky failure does not mean the rule under test is broken. It means the test does not
control everything its result depends on. The cost is that people learn to rerun a failed test
until it passes, and then a real failure is rerun and ignored too.

There are two ways to repair one. Either control the source of variation, for example by giving
each thread its own generator or by setting up a situation where the variation cannot matter.
Or change the assertion to a property that holds in every run: for a refund test, "the
customer's balance went up by exactly the refund", not "the third log line says refunded".

## 1.7 Regression tests and finding edge cases

A **regression** is something that used to work and stopped. A **regression test** is written
from a real fault: first a test that fails because of the fault, then the fix, then the same
test passing. Writing the test first shows that it can fail, and it stays in the suite so the
same fault cannot return unnoticed.

The cases most worth testing are the rules that must always hold (called **invariants**), the
boundaries between components, and past faults. Edge cases can be found by asking four
questions of each step in a piece of work, such as "pay the refund, then send the reply":

1. What if the process dies here?
2. What if this runs twice?
3. What if two of these happen at once?
4. Was the result confirmed, or only assumed?

For the support assistant: what if the server restarts after the refund is paid and before the
reply is sent? What if the customer clicks "refund" twice? What if two refund requests for one
order arrive together? Does the reply say "refunded" because the payment provider confirmed
it, or because the request was sent?

## 1.8 Continuous integration, and what coverage measures

**Continuous integration** (CI) is a service that runs the tests automatically on every change
pushed to the shared repository, on a clean machine, and marks the change as failed when a test
fails. Without it, three things are lost:

- **The tests run only when someone remembers.** A broken test can sit unnoticed for weeks.
- **A pass describes the developer's machine.** Installed packages, environment variables and
  files left over from earlier work can make a test pass locally and fail anywhere else.
- **There is no record of which revision passed.** A pass on a working folder with uncommitted
  edits says nothing about the commit that was released.

CI does not make untested behaviour correct. It runs the same tests, with the same stand-ins,
as a developer would run by hand; what it adds is that they run every time, on a known
revision. Tests that need credentials or cost money are usually
left out of it, or run on a schedule.

**Test coverage** is the share of the code's lines that the tests executed, or of its
branches (both sides of every `if`). A
high number proves little, because a line can run without any assertion checking its result:
a test that calls the refund service and checks nothing raises the coverage as much as one
that checks the refusal. Coverage is more useful the other way round: a line that no test runs
is certainly not tested.

### Check your understanding

The support assistant's team adds the sentence "Never offer a refund larger than the order
total" to the prompt. A unit test checks that the sentence appears in the prompt, and it
passes in CI. The release note says: "The assistant no longer offers refunds above the order
total." What does the test establish, and what would support the release note?

<details>
<summary>Answer</summary>

The test establishes that the prompt is built with the sentence, on the revision CI ran. It
says nothing about what the model does with it.

To support the release note, an evaluation is needed: a set of saved emails that tempt the
model to offer too much, run against the real model before and after the change, with the
number of over-large offers counted each time and the sample size stated. Even a good result
would be a rate, not a guarantee. The guarantee comes from the refund service refusing any
amount above the order total in code, and a unit test of that check is the test that matters
most.
</details>

## 1.9 A checklist for a new system

| Question | What it establishes |
|---|---|
| 1. Which rules must always hold? | The invariants (1.7) that deserve unit tests over many inputs |
| 2. Where are the boundaries between components? | Where integration and contract tests are needed |
| 3. Which dependencies are replaced by stand-ins, and what does each hide? | The list of behaviours no test checks |
| 4. Which past faults have a test? | Whether each fault can return unnoticed |
| 5. What is measured with the real model, and when? | Which behaviour claims are supported, and how old the evidence is |
| 6. What runs automatically on each change, and on which machine? | Whether a pass describes the released revision |
| 7. Does every test control its own randomness and timing? | Whether a failure can be trusted |

---

# Part 2 — What the tools do, and what my application does

| Responsibility | The tool | My application |
|---|---|---|
| Find and run the Python tests; select by marker | pytest, configured in `pyproject.toml` | Marks tests that call paid models as `live`, and excludes them by default |
| Replace a dependency for one test | pytest's `monkeypatch` | Decides which dependency is replaced, and writes the stand-ins (a scripted model, stand-in graphs) |
| Run the frontend's logic tests | Vitest, in Node with no browser | Chooses the fixtures: real games saved from the server |
| Drive a browser and compare screenshots | Playwright, with a pixel tolerance | Answers every API call from saved games, so no server runs |
| Run the game's graph in a test | LangGraph, with its in-memory checkpoint saver | Runs whole games on the real graph with the model scripted |
| Decide what counts as correct | No tool | The assertions, the goldens, and the leak checks |
| Run the tests on every change | None configured | Nothing runs them automatically (3.6) |

---

# Part 3 — How my Werewolf system does it

**The system in brief.** A game has ten **seats**, each played by a model agent (an AI seat) or
by a person. The game itself is a **graph** (LangGraph): each step of the game, such as one
seat's turn, is a **node**, and the game's state is saved after each step. The **game master**
is the game's own voice: its announcements, such as who died in the night, appear in the same
discussion the players write in. Each AI seat's prompt is built from the state it is allowed to
see. The server turns the graph's output into events for the browser (the **translator**) and
decides which seat may see which event. Games are played in two ways: **hosted games** on the
website, and **batch games** run from the command line for experiments. Finished games also
feed **lessons**, strategy notes extracted by a model and read by AI seats in later games.

**The case at the centre.** On 2026-11-17 I changed how a player's words appear in the AI
seats' prompts: each message is now one line inside quotation marks, and a fixed caption line
under the discussion heading says that a player's words are inside quotation marks. The change
was a defence against a person typing a fake game-master announcement into their own message,
which AI seats had believed (U11, section 3.3). Four questions had to be answered about the
change, and tests answered only the first. That case (3.5) is the centre of this part. Sections
3.1 to 3.4 describe the suite it ran in.

## 3.1 What the suite contains

The Python tests are in four folders by the part of the system they test, plus one folder for
tests that call paid models. One command, `poetry run pytest`, runs everything except those.

| Folder | Tests | What they test |
|---|---|---|
| `tests/engine` | 1,436 | The game: its rules, the step that settles each night's actions, the deduction engine (code that writes facts a seat can deduce into its prompt), prompt assembly, whole games with a scripted model (3.2) |
| `tests/memory` | 334 | The lessons: extraction from finished games, removal of duplicates, storage and retrieval |
| `tests/evaluation` | 392 | The evaluation code itself: sampling, scoring and judging pipelines, and the loop that credits and prunes lessons |
| `tests/server` | 311 | The game session, the API, the translator into browser events, durability |
| `tests/live` | 170 paid, 9 free | Every model a player can choose, asked for every seat's output format (170 cases, excluded by default); 9 free tests that a model is skipped when its provider's key is absent |

That is 2,652 Python tests, of which 2,482 run by default. On 2026-11-17 the default run
passed: 2,481 passed and 1 was skipped, in 13 minutes 38 seconds (on a machine also running the
frontend tests and another agent's work). A few memory tests use a real Postgres database
whenever a database address is set, as it is on my machine, and are skipped otherwise; the one
skipped test is a replay test of the same kind that needs its own address. So the same command
tests more on my machine than it would on a clean one. Ten tests that check the deduction engine
on thousands of random games took about 10 of the 13 minutes.

The frontend has its own tests:

| Kind | Size | Run for this note? |
|---|---|---|
| Unit tests (Vitest, no browser) | 73 files, 1,607 tests | Yes: all passed, in 56 seconds (while the Python suite was running alongside) |
| Browser tests (Playwright) | 8 spec files, about 115 tests, 99 saved screenshots | No. It needs a server started by hand first; the frontend's testing guide estimates about 16 minutes |
| Types, lint, production build | One command each | No |

Test names are written as sentences that state the claim, for example
`test_a_dead_player_gets_no_record_of_its_last_night`. A failure then says which rule broke
without opening the file. A shared setup file pins the environment for every test: tracing is
switched off, a paid model call made after each game is switched off, and the list of models
comes from the code instead of the live database. A test therefore does not depend on my
machine's database, and does not send traces to the tracing service.

## 3.2 Levels, and what each stand-in hides

| Level | In my system | What is replaced |
|---|---|---|
| Unit | Most of the engine tests: the night rules, the deduction engine, the code that formats prompts | Nothing, or small inputs built by hand |
| Integration: the engine | Whole ten-seat games run on the real graph, streamed through the server's translator | The model, by a **scripted model** that fills any output format with legal values chosen at random. The day's summary, and two checks on what a seat says, are replaced by stubs |
| Integration: the server | A real game session; the real application behind a test client for the API | The game graph, by a stand-in that yields scripted output. The database writes are recorded instead of sent |
| Browser tests | The real pages, driven in a headless Chromium browser | The whole server: every API call is answered from saved games. So these are not end-to-end tests in the sense of 1.2: they test the pages, not the system |
| End-to-end | A hosted game, or a batch run of games with real models | Nothing. Not automated as a test |

The deduction engine's unit tests generate thousands of random legal nights from fixed seeds,
settle each one with the real game code, and check that every fact the engine writes into a
seat's prompt is true in that night.

What the stand-ins hide, row by row:

- **The scripted model** proves that a whole game can be played to the end on the real graph
  with legal moves, and that the browser accepts every event. It cannot show what a real model
  says, how often its answer fails validation, or how long a turn takes.
- **The stand-in graph** in the server tests means that bringing games back after a server
  restart is tested without the code that saves game state to Postgres (the checkpoint saver).
  No test uses that saver. A real kill and restart was last checked by hand in August (U3,
  section 3.8).
- **The browser suite's answers** come from its own copy of the server's rules for which seat
  may see which event. If those rules change on the server, the browser suite still passes,
  because its copy has not changed. The copy already lacks two event types that only their own
  seat may see, `uses_remaining` and `night_record` (checked 2026-11-17).

The **planted-key test** from 1.3 exists for one path. In
`test_dead_game_error_never_echoes_the_key`, the stand-in graph fails with the error
`401: API key not valid: sk-player-123`, the way a provider's error can. The test checks that
the game's stored error text no longer contains the key. That is the correct form of the test.
It covers the error text and the error report sent to Sentry only. It does not search the other
places the key could be written: the database tables, the saved game state, the trace, or the
log line of a failed model call (U10, section 3.2).

**Where the model is tested for real.** Two places, both run by hand:

- The `live` tests ask every model a player can choose for every seat's output format. They
  exist to catch a provider change that breaks structured output. The test file's own
  description records a first run on 2026-09-10. Whether they have been run since was not
  checked.
- Everything about behaviour, such as whether a prompt change moves votes, is measured by
  evaluations in `evaluation/` and by experiment scripts in `evaluation/experiments/` (62 of
  them), with the results and their sample sizes recorded in `evidence/`.

## 3.3 Golden tests

| Golden | What it pins | Built from |
|---|---|---|
| The day-discussion prompt | The exact prompt each of the ten roles is sent on a discussion turn, in one fixed game state on day 3 | A game state written by hand to have something in every section of the prompt, run through the real discussion step with the model replaced by one that only records what it was sent |
| Two translator goldens | Every browser event the server's translator produces for a whole game | Two real games, one of them with a human seat |
| The saved API description | The server's API description, which the frontend's types are generated from | The server itself. A changed route or response fails the test until the types are regenerated. This is a contract test (1.2) |
| Frontend beat goldens | The list of moments the replay shows one after another (each called a beat), cut from a saved game | Real games |
| Screenshot goldens | 99 pictures of pages and scenes, with 0.5% of pixels allowed to differ | The rendered pages |

The prompt golden fails on a change of one character in any role's prompt. A prompt change
alters the AI's behaviour, so this test makes every such change deliberate: the golden is
regenerated by a command, and the difference is read. What it cannot show is that the new
prompt is better. And it pins one game state: a section of the prompt that this state leaves
empty is not pinned.

## 3.4 The leak checks

The leak checks search what each AI seat was given for private information it must not have:
the wolves' identities, another seat's night results, the wolves' private chat. There are
eleven checks in `tests/leak_test.py`. They return a list of leaks instead of failing, so that
one function can be used in two places:

- in engine tests, over games played with the scripted model;
- in the batch runner, over every game it plays with real models. Nine of the eleven run there;
  the other two check data that only specific engine tests produce. A game with a leak is
  recorded and the batch exits with an error.

The batch run is the only place where a check runs automatically on games with real models. A
nightly audit of hosted games is written but not scheduled on the host (U14). The checks
inspect what goes into a seat's prompt. They do not inspect what a seat says.

## 3.5 Case one: a prompt change, what the tests showed, and what they could not

The change of 2026-11-17 renders each player's message as one line inside quotation marks, and
adds a caption under the discussion heading. Each question about it needed a different kind of
check:

| Question | What answered it | Result |
|---|---|---|
| Does the prompt render as intended? | 10 new tests of the quotation marks and 18 of the one-line rendering; the day-discussion golden regenerated and its difference read | Passed. A double quotation mark typed by a player becomes a single one, so it cannot end the quotation early, and a forged `game_master:` line stays inside the attacker's quoted message |
| Is the prompt in the game the prompt the experiment measured? | The experiment had built its prompts with its own copy of the quoting. A script rebuilt the 22 attacked prompts through the game's code and compared them with the experiment's | Identical, character for character, in all 22 |
| Does it reduce the effect of a forged announcement? | An experiment with real model calls: 438 calls, $0.34 | Across three saved moments, the town votes cast for the innocent player named in the forged line fell roughly by half (24 of 33 to 14 of 33). The attack still worked often |
| Does it change ordinary play? | A second experiment with no attack: 112 calls, $0.11 | No change it could detect. With 27 votes at the main moment, it could miss a change of a few votes |

The tests answered the first question completely and could say nothing about the third: a
test with a scripted model cannot show whether a real model believes a forged line.

**The fault the full run caught.** Three of the leak checks turned a seat's prompt input into
one string with Python's `repr` and searched that string for private text. `repr` puts a string
inside single quotation marks, and when the string itself contains both a single and a double
quotation mark, it writes each apostrophe as `\'`. Once the discussion always contains double
quotation marks, every apostrophe in it was written as `\'`. A leaked line such as `I'm the
healer` would then appear as `I\'m the healer`, and a search for the original text would not
have found it. The full engine test run caught this, and the checks now search the plain text
as well. The game was not at fault. The change to the game had quietly weakened a check on the
game, and only running every test, not just the ones written for the change, showed it.

## 3.6 Case two: a test whose failure did not mean the rule was broken

`test_a_human_vigilantes_shot_is_spent_once_across_the_pause_and_resume` plays a whole game in
which seat 1 is a human Vigilante, a role with one bullet to fire at night. When a person's
seat has a turn, the game stops and waits for their answer, then carries on from where it
stopped (U5). In the test, the answer at each stop is scripted. The test checks that the bullet
is spent exactly once across these stops.

It failed in 2 of 10 runs in one measurement and 4 of 10 in another (2026-11-12, U2 section
3.7), and in 1 of 30 on 2026-11-17. Two things in the test caused it, not the game:

- **Shared random state.** The scripted players draw from one random-number generator with a
  fixed seed, but the seats' night turns run on several threads. Which seat receives which
  number depends on which thread runs first, so a different game is played on each run.
- **The count it relied on.** It counts shots from the night records, and the engine, by its
  own rule, keeps no record of that night for a seat that dies the same night. In such a game
  the shot was fired and the test counted zero.

The bullet was spent once in every run examined. The rule held; the test did not control what
its result depended on.

**How the cause was confirmed (2026-11-17).** A second explanation fitted the same symptom:
Python changes how it orders sets of strings from one process to the next. A script replayed
the test's game under four settings to separate the two.

| Setting | Runs | Different sets of night choices | Bullet spent once |
|---|---|---|---|
| Normal threads, string ordering varying | 20 | 20 | 20 of 20 |
| Normal threads, string ordering fixed | 20 | 20 | 20 of 20 |
| One thread at a time, either ordering | 30 | 1 | 30 of 30 |

Fixing the string ordering changed nothing, and running one thread at a time made every run
make the same night choices. So thread order is the cause. This is debugging, not an experiment, and it
still establishes a finding, because the cause was reproduced directly.

**The repair, and the alternatives.** Section 1.6 gives two repairs for a test like this. I
chose the first: fix the situation. No scripted player may now choose the Vigilante as a target,
so it cannot die or be stopped from acting, its shot always goes ahead, and its record is always
kept. The games still differ from run to run; the test no longer depends on which one is played.
The cost is scope: this test no longer plays a game in which the Vigilante is killed or stopped
on the night it fires, and I have not checked that another test covers the bullet count there.

| Alternative | Why it was not chosen |
|---|---|
| Assert only that the remaining bullets went down by one | In a game where no shot goes ahead, the test would pass while checking nothing about a second spend |
| Give each seat its own random-number generator | Each seed would then play one fixed game. That hides the dependence on thread order without removing it, and it changes the games of the other tests in the file |
| Run the night turns on one thread | The test exists to check turns that run in parallel around a pause, so this changes what it tests |

**Can the repaired test still fail?** This is the first question of section 1.1, and a repair
that removes a failure has to answer it. The engine was broken on purpose in two ways, inside
the test process: the bullet spent twice for one shot, and the bullet spent once for each time
the Vigilante's turn starts, which is the fault the test exists to catch, because a person's
turn starts once before the pause and again after it. The repaired test failed on its bullet
count under both, and passed on the unbroken engine.

After the repair the test passed in 100 of 100 runs, and the full engine suite passed. The
stronger evidence is not the count but the reason: in 40 replays the Vigilante was never
targeted, so the event behind every observed failure can no longer happen. The record is
[vigilante_test/experiment_log.md](vigilante_test/experiment_log.md).

One thing is left open. The other whole-game tests in that file use the same scripted players,
so their games also vary by thread order. They passed, and whether any of them can fail by
chance was not examined.

The deduction engine's random tests show the deterministic version: they draw thousands of
random nights from a fixed seed, on one thread, so every run draws the same nights.

## 3.7 What runs automatically

Nothing. There is no CI configuration in the repository, no active git hook and no Makefile.
The tests run when I or an agent runs them, on this machine, against the working folder, which
often holds uncommitted edits from several pieces of work at once. Releases are made by hand,
and no step of the release runs the tests (U14, section 3.1).

So a pass in my system means: on my machine, on the files in the working folder at that moment,
with the paid tests left out. It is not a record that the released revision passed.

## 3.8 Known limitations and possible improvements

| Gap | Why it matters | Possible improvement |
|---|---|---|
| 1. Nothing runs the tests automatically, and no release step runs them | A broken test can go unnoticed, and no pass is tied to the revision that was released | CI on every push running the default suite; a release step that refuses a revision without a recorded pass |
| 2. The restart path is tested against stand-ins only | A fault in the real Postgres saver or a real restart would not be caught | A kill-and-restart test on a test Postgres with scripted players. It needs no model calls |
| 3. **Repaired 2026-11-17.** One engine test failed on some runs because its result depended on thread order | The other whole-game tests in the same file use the same scripted players, so their games also vary by thread order; none was seen to fail | A scripted player that does not depend on thread order, for the whole file |
| 4. The `live` model check is run by hand; its last run is not recorded since 2026-09-10 | A provider change can break structured output until a real game fails | Run it on a schedule, and record each run's date and result |
| 5. The browser suite uses its own copy of the server's rules for who sees what, already two event types behind | A change on the server passes the browser suite | Generate the copy from the server, or test it against the server's rules in one test |
| 6. The planted-key test covers the error text and the error report only | The key could reach the database, the saved game state, the trace or a log line unnoticed | Search those places in the same test (U10 gap 1) |
| 7. No accessibility check runs | Nothing would catch a page that cannot be used by keyboard | axe (an automated accessibility checker) in the browser tests, and one keyboard-only test (the frontend testing guide's plan) |
| 8. The frontend testing guide lists 5 browser spec files; the folder has 8 | The record of what is tested is incomplete | Add the three missing rows |

---

# Part 4 — Design choices

**Replace the dependency, or use the real one?**

| Design | Benefit | Cost | My system |
|---|---|---|---|
| A stand-in | Fast, free, repeatable | Says nothing about the real dependency | The model in every default test; the graph in the server tests; the server in the browser tests |
| The real dependency | Tests what will actually run | Slow, may cost money, may vary between runs | The paid `live` tests and the experiments, both by hand |

**Where do golden inputs come from?**

| Design | Benefit | Cost | My system |
|---|---|---|---|
| Real games | Realistic: they hold the situations that actually occur | A situation no saved game reached is not covered; a change to the game makes many goldens differ at once | Translator goldens, frontend beat goldens |
| A game state written by hand | Can put something in every section on purpose | Only as realistic as its author made it | The day-discussion prompt golden |

**How do the server and the browser stay in agreement?**

| Design | Benefit | Cost | My system |
|---|---|---|---|
| Types generated from the server's description, with a test that fails when the saved description is out of date | A changed field fails a test on the day it changes | A regeneration step after every API change | Yes |
| A contract written by hand on both sides | No generation tooling | The two copies drift apart unnoticed | The browser suite's copy of who sees what (gap 5) |
| Checking only at run time | Nothing to maintain | A mismatch is found by a user | Not used alone |

**How is a prompt change verified?**

| Design | Benefit | Cost | My system |
|---|---|---|---|
| Tests and a prompt golden | Free, on every run; prove the prompt is the intended text | Nothing about behaviour | Yes |
| An evaluation with the real model | Measures the effect on behaviour | Money, time, and a result with a sample size | Yes, for changes meant to alter behaviour |

---

# Part 5 — Review

## In 30 seconds: five ideas

1. **A pass is a fact about one run.** It holds for that revision, environment, set of inputs
   and set of stand-ins, and for the property asserted, and for nothing else.
2. **Each level catches what the others miss.** Unit tests point at the fault, integration
   tests check the boundaries, end-to-end tests check the user's task. A stand-in at any level
   is a part that level does not test.
3. **An LLM application needs tests and evaluations.** Tests check the code around the model
   on every change. Only an evaluation with the real model shows what a change did to its
   behaviour.
4. **A golden pins the output, not its correctness.** It is useful only while each difference
   is read before the golden is regenerated.
5. **A flaky failure means the test does not control its result.** Find the source, then
   control it or assert something that holds in every run.

## My Werewolf system in one paragraph

I have 2,652 Python tests, 2,482 of which run by default, and 1,607 frontend unit tests, plus
a browser suite that answers every API call from saved games. Whole games run on the real graph
with a scripted model that picks legal moves at random, so the rules, the event stream and the
prompts are tested without a model call; the prompt each role is sent is pinned by a golden. The
leak checks run in the tests, and nine of the eleven also run on every batch game played with
real models. Nothing runs
automatically: there is no CI, and a pass describes my machine and my working folder. The
2026-11-17 quoting change shows the split: the tests proved the prompt renders as intended, an
experiment with real models was needed to show it roughly halves a forged announcement's
effect, and the full test run caught a leak check the change had weakened. The restart path is
tested against stand-ins only, and one engine test fails by thread order (repair in progress).

## Stopping check

Without looking back at the note, explain:

- what a pass of the day-discussion prompt golden establishes, and what remains untested even
  if CI ran it on every push;
- why the scripted model cannot tell me whether the quotation marks work as a defence;
- why the Vigilante test's failures did not mean the bullet rule was broken.

Then answer Problem B. That is enough for this first reading. Problem A is an optional transfer
check.

## Problems

**Problem A: transfer to another application.** A Python API and its TypeScript client drifted
apart for a week: the server renamed a field, and the client kept reading the old name. Which
test would have caught it on the first day? What would a run in which every test passed on the
developer's machine not have proved?

**Problem B: my own system.** For each sentence, say what kind of evidence stands behind it:
code that I have read and that does what the sentence says, a named test, a run with real
models, or nothing.

1. "The AI seats' prompts never contain another seat's private information."
2. "A game survives a server restart."
3. "Putting players' words in quotation marks roughly halves the effect of a forged
   game-master line."

---

# Appendix A — Answers to the problems

**Problem A.** A contract test: the server's API description is saved beside the client, the
client's types are generated from it, and a test fails when the server's live description no
longer matches the saved one. The rename fails that test on the day it is made, before any
user sees it. A test that only checks the client against its own hand-written types would
still pass.

A run in which every test passes on the developer's machine does not prove that the committed revision passes, that
the client and server that are deployed are the ones tested, or that the tests ran at all for
the other developer's change. CI on every push removes the first and third of these.

**Problem B.**

1. *A named test and a run, for prompt inputs only.* The leak checks search every seat's prompt
   input, in engine tests over scripted games and in the batch runner over games with real
   models. They do not cover hosted games (the audit is not scheduled), and they do not check
   what a seat says. Accurate wording: "In every batch game, an automatic check searches each
   seat's prompt input for nine kinds of private information; hosted games are not checked."
2. *Code and tests against stand-ins; a manual check in August.* The recovery logic is tested
   with a stand-in graph and recorded database writes; no test uses the real Postgres saver.
   Accurate wording: "The recovery logic is tested against stand-ins; a real restart was last
   checked by hand in August."
3. *A run with real models.* 438 calls at three saved moments from two games, one model. It
   shows an effect, not a rate. The tests show only that the shipped prompt is the measured one.

---

# Appendix B — Implementation and evidence reference

*Each claim carries its support: **code** (the file and symbol were read), **test** (named;
not run unless stated), **run** (executed for this note), **doc** (a written record, not
re-checked in the code). Read and run on 2026-11-17. Paths are from the repository root.*

**The suite (3.1)**

- Test counts per folder, 2,652 in all, 170 marked `live`: **run**
  (`poetry run pytest --collect-only -q`, per folder and with `-m live`)
- `live` excluded by default; the repository root on the import path: **code**
  `pyproject.toml` (`[tool.pytest.ini_options]`, `addopts = "-m 'not live'"`)
- The full default run: **run** (`poetry run pytest -q --durations=25`, 2026-11-17): 2,481
  passed, 1 skipped, 170 deselected, 818 s. The ten slowest are deduction-engine tests over
  random games, 73 to 101 s each for the six slowest
- The skipped test: **run** (`-rs`) `tests/server/test_replays.py` line 202, "set
  WW_REPLAY_TEST_DSN to run the real-Postgres round-trip"
- Memory tests that run on a real Postgres when `WW_POSTGRES_DSN` is set, skipped otherwise:
  **code** `tests/memory/test_consolidation_graduation.py`, `tests/memory/test_served_extraction.py`
  (`needs_db`); that they ran here is inferred from the single skip. Which database they used
  was not checked
- Frontend unit tests, 73 files, 1,607 tests, all passed in 56 s: **run** (`npx vitest run` in
  `frontend/`, alongside the Python run)
- Browser spec files (8), `test(` declarations (115, counted by a text search, so tests
  generated in loops are not counted separately), screenshots (99): **code**
  `frontend/e2e/`, `frontend/playwright.config.ts`; not run
- The browser suite's time (about 16 min) and the guide's list of 5 specs: **doc**
  [`frontend/docs/testing.md`](../../../frontend/docs/testing.md)
- The environment pinned for every test: **code**
  [`tests/conftest.py`](../../../tests/conftest.py)

**Levels and stand-ins (3.2)**

- Random legal nights from fixed seeds, thousands per test: **code**
  `tests/factories/random_nights.py`, `tests/engine/deduction/test_own_results.py`
- The scripted model and the stubbed helpers: **code**
  [`tests/engine/test_ten_seat_game.py`](../../../tests/engine/test_ten_seat_game.py)
  (`_fill`, `_FakeLLM`, `_script_the_model`)
- The stand-in graph and the API test client: **code**
  [`tests/fixtures/server.py`](../../../tests/fixtures/server.py) (`FakeGraph`, `api_client`)
- The restart path without real Postgres: **code** `tests/server/test_durability.py` (module
  note: "The real-Postgres path is exercised by the manual restart smoke, not here"); the
  August manual check: **doc** U3 section 3.8
- The browser suite answers API calls from saved games: **doc** `frontend/docs/testing.md`;
  its own copy of the entitlement sets, without `uses_remaining` or `night_record`: **code**
  `frontend/e2e/live.spec.ts` (`OBSERVER`, `FACTION`, `SEAT`), read 2026-11-17
- The planted-key test and its failing stand-in: **code** `tests/server/test_byok.py`
  (`_AuthBoomGraph`, `test_dead_game_error_never_echoes_the_key`); the places it does not
  cover: **doc** U10 section 3.2
- The paid model check and its first recorded run: **code**
  `tests/live/test_model_structured_output.py` (module note); later runs not checked
- Evaluation runners: **code** `evaluation/README.md`, `evaluation/experiments/` (62 files)

**Goldens (3.3)**

- The day-discussion prompt golden: **code** `tests/fixtures/day_discuss_prompt_golden.py`,
  `.json`; **test** `tests/engine/test_draft_preview.py::test_ai_discuss_prompt_is_byte_identical_to_the_golden`;
  regenerated in commit `6577f79c` (20 lines changed)
- Translator goldens from two real games: **code** `tests/fixtures/translator_golden.py`,
  `translator_golden.jsonl`, `translator_golden_human.jsonl`
- The API description test: **code** `tests/server/test_openapi_snapshot.py`
- Beat and screenshot goldens, the 0.5% tolerance: **code** `frontend/playwright.config.ts`;
  **doc** `frontend/docs/testing.md`

**Leak checks (3.4)**

- Eleven `check_` functions returning lists; nine in `run_leak_tests`: **code**
  [`tests/leak_test.py`](../../../tests/leak_test.py)
- Run on every batch game; a leak recorded and the batch exits non-zero: **code**
  `scripts/run_batch.py`
- The hosted audit not scheduled: **doc** U14 section 3.5 gap 6

**Case one (3.5)**

- The change and its tests: **code** commit `6577f79c`; **test**
  `tests/engine/test_transcript_quoting.py` (10), `tests/engine/test_transcript_one_line.py` (18)
- The experiment, the equivalence check and the adoption check: **doc**
  [`evidence/agent_boundaries/forged_speaker/report.md`](../../agent_boundaries/forged_speaker/report.md)
  and its `experiment_log.md`; no model calls were made for this note
- The `repr` fault and the fix: **code** `tests/leak_test.py::_searchable`; **doc** the report,
  "One fault the change exposed". Which test failed in that run is not recorded

**Case two (3.6)**

- The test, its shared generator and its two assertions: **code**
  `tests/engine/test_ten_seat_game.py`, read 2026-11-17 before the repair
- 2 of 10 and 4 of 10 failures; the bullet spent once in every run examined: **doc** U2
  section 3.7, `measurements/u2_diag_runs.txt`
- Its result in this note's run: **run**, passed. The test file was edited at 05:09 by the
  repair in progress, after this run had started and collected its tests, so the run is taken
  to have used the unrepaired version (not confirmed)

**What runs automatically (3.7)**

- No CI workflow, `.pre-commit-config.yaml`, Makefile or husky folder; `core.hooksPath` points
  at `.git/hooks`, which holds only the sample files: **run** (a file search and `git config`)
- No coverage tool configured: **code** `pyproject.toml`, `frontend/package.json`
- No tests in the release procedure: **doc** U14 section 3.1

**Not checked**

- The browser suite, the type check, the lint and the production build.
- Whether the `live` tests have been run since 2026-09-10.
- Which test caught the `repr` fault on 2026-11-17.

**Further reading, only when needed:** the "Practical Test Pyramid" by Ham Vocke on Martin
Fowler's site, the sections on unit, integration and contract tests. Martin Fowler's
"Eradicating Non-Determinism in Tests", for the causes of flaky tests.
