# U13 seed notes: accessibility as a level of verification

Not a note yet. Points from 2026-11-11, kept so U13 covers them. Accessibility is a clean example of
U13's guiding question: a passing check establishes the mechanical part and leaves out the part that
needs a person. The plan for my frontend is in `frontend/docs/testing.md` ("What none of this covers"
and "Later, not now").

## Three levels, from mechanical to human

| Level | What checks it | What it establishes |
|---|---|---|
| Mechanical rules | axe-core: about 90 rules run against the rendered page (a button has a name, text contrast is at least 4.5:1, an `<img>` has `alt`, ARIA attributes are valid, IDs are unique) | Each listed rule holds on the pages and states the test visited. Roughly a third to a half of real accessibility problems |
| Task-level behaviour | A scripted test that does a task with the keyboard only (join a game, cast a vote with `Tab`, `Enter`, `Escape`); an accessibility-tree snapshot (`toMatchAriaSnapshot`) pinning roles and names | That one path works by keyboard and that the tree a screen reader reads has not changed. Not that the order makes sense or that other paths work |
| Judgment | A person (or, partly, an agent driving a browser): is the focus order logical, is the alt text meaningful, does a live region announce too much | What the rules cannot express. An agent's judgment is a model's reading of the accessibility tree, not a screen reader and not a disabled user |

Lighthouse's accessibility score is axe-core underneath, a subset of its rules weighted into one
number. Same level as axe, less detail.

## Where an agent fits

- **Fixing mechanical violations** fits well. axe's output is precise (rule, selector, HTML, a fix
  link), so the loop is the same as fixing failing tests: run, fix, run again. A person reviews the
  diffs, since colour fixes change the look.
- **Writing the task-level test** fits well too. The agent explores once, and the result is a
  deterministic test that runs without it.
- **Judgment** is where it stops. Same limit as an LLM judge in my evals: it reads well and misses
  what it cannot observe.

## The claim each level supports

- axe clean: "checked with axe", for the pages and states the suite visits.
- Plus the keyboard test: "keyboard-tested on the main path".
- Neither supports "accessible". That needs real assistive technology and real users.

## My frontend as of 2026-11-11

From a scan of `frontend/src`, not an audit: real `<button>`s and links, no clickable `<div>`s found;
about 550 `aria-*`/`role=` attributes; `aria-live` on the turn dock, notices, departures board and
archive count; `prefers-reduced-motion` handled in about ten places; `:focus-visible` styles in most
places that remove the default outline. Gaps: the lobby inputs remove the outline with no
replacement (`Lobby.module.css`), no skip link, no axe and no `jsx-a11y` lint rules, and no check
has ever run.

## Reading the tests myself (from the U3 handover, 2026-11-12)

- Before U13 is written I read the test code myself. It is the first project code I read directly
  for these notes, so U13 should be built around that reading, not around a summary handed to me.
- Where to start, because U3 already raised it: the restart path. `tests/server/test_durability.py`
  uses a stand-in graph (`FakeDurableGraph`) and records database writes instead of sending them.
  `tests/server/test_game_session.py` and `tests/engine/test_subgraph_interrupt.py` use the real
  LangGraph with the in-memory saver. No test uses the Postgres saver. `tests/live/` has two tests,
  both about model calls.
- The question to carry into the reading: for each of these files, what does a pass establish, and
  what does the stand-in hide? U3 section 3.8 names the missing test (kill and restart on real
  Postgres). It needs no model calls, so cost is not what blocks it; a test database and a way to
  kill and restart the process are.
- A worked example found on 2026-11-12 (U2 section 3.7, gap 5):
  `test_a_human_vigilantes_shot_is_spent_once_across_the_pause_and_resume` in
  `tests/engine/test_ten_seat_game.py` fails in roughly a third of runs. Its scripted players share
  one random generator across threads, so the game played depends on thread order; and it counts
  shots from night records, which the engine rightly drops for a seat that dies the same night.
  The rule it means to check (the bullet is spent once) held in every run looked at. Two repairs:
  fix the situation (a night in which the Vigilante cannot die or be blocked), or assert what holds
  in any game (`uses_left` goes down by exactly one). Unchanged so far; my call.
  *2026-11-17: repaired with the first option, not committed; the reasons for not choosing the
  second, and the evidence, are in `vigilante_test/experiment_log.md`.*

## Scope for U13 (my ruling, 2026-11-14)

U13 is not a catalogue of test types. With agents writing most test code, the skill I need is
judging and directing tests, to a sufficient level, not an optimal one:

1. **What to test.** Rules that must always hold, boundaries between components, past incidents.
2. **Edge cases.** A repeatable way to find them (the four questions: dies here, runs twice,
   two at once, was it confirmed).
3. **Setting tests up so an agent can work with them.** Fast and deterministic, clear names and
   failure messages, reusable fixtures, one command, a written rule for "done".
4. **Reading and debugging a test an agent wrote.** Can it fail? Does it test the claim or the
   implementation? What does a pass not prove? (The Vigilante test above is my example.)
5. **What a green run establishes.** My machine against CI; "deployed" against "validated".

It covers backend, frontend and the boundary between them. It feeds a planned write-up section
on how I use agentic coding, where testing is one of the practices shown. Setting up CI is a
separate build task after the note.

## From the U10 walkthrough (2026-11-16): the planted-key test

A worked example for "what to test" and "what does a pass not prove". U10 section 1.3 has the
technique: a made-up key, run through every path with the provider replaced by a stand-in,
then every sink searched for the exact string. My tests do this for a dead game's error text,
its traceback and the Sentry report. They do not search the database tables, the checkpoint,
the trace, or the log line of a failed model call (U10 section 3.2 and gap 1). Two points to
carry into U13:

- For the failing paths, the stand-in has to raise an error that contains the key. A stand-in
  that fails with a clean message passes the test and proves nothing about scrubbing.
- It is the same idea as the leak checks over prompts: search every output for a value that
  must not be there.
