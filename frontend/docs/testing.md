# How the frontend is tested

Written for the owner: what each kind of test checks, how a run is done here, and what none of
them can tell you. Commands run from `frontend/`.

## The layers

| Layer | Tool | What it checks | Size, time |
| --- | --- | --- | --- |
| Unit | Vitest, in Node (no browser) | The logic: the event fold and the store, the beat list, the live and replay reducers, the paint generators' markup, the dock's rules, the music's cue sheet. A small layer renders components to HTML on the server (`renderToStaticMarkup`) to prove private data reaches only the right reader. | About 20 s. `npm test` |
| Types, lint, format | `tsc`, ESLint (with React's hook rules), Prettier | Types; hook dependency lists (`react-hooks/exhaustive-deps`, which is what keeps a `useMemo` from serving stale data); formatting. | Seconds. `npm run typecheck`, `npm run lint`, `npm run format:check` |
| Build | `next build` | What the three above miss: a server component calling a client hook fails only here, when the page is prerendered. | About 2 min |
| Browser | Playwright, headless Chromium | The pages as a browser draws them, against a mocked API (below). | About 16 min. `npm run e2e` |
| Diagnostics | Scripts, not pass/fail | Measurements taken while working on performance (below). | As needed |
| The real phone | The owner's iPhone, Safari's Web Inspector over a cable | Memory crashes, frame rate, touch, sound. | By hand |

## What the goldens pin

A golden is a saved output that a test compares the new output with, whole. There are two kinds.

- **Beat goldens** (`src/stage/beats/__goldens__/`): the whole beat list that `beatsFor` cuts from
  a game, one line per beat, written by `toMatchFileSnapshot` in `src/stage/beats/beatsFor.test.ts`.
  Four files: the public cut and the X-ray cut of two games, the nine-seat fixture `9369a5c1` and
  the Phase 2 game. They hold the cutter to `beat_sheet.md`: change the sheet, change the cutter,
  regenerate (`npx vitest run -u`), and read the diff. The two ten-seat games
  (`replay-phase3.json`, `replay-phase3-necro.json`) have no whole golden; targeted assertions in
  the same file hold their beats.
- **Screenshot goldens** (`e2e/__screenshots__/`): pictures of the page, under "The browser suite"
  below.

The fixtures are real games, not hand-written ones: archived games in `src/stage/fixtures/`, the
593-event seed game in `src/game/__fixtures__/`, and the ten-seat game wrapped from the server's
translator golden (`ten_seat_pass.md` §4). So a golden pins what the stage does with games that
happened, and nothing about a shape of game no fixture holds.

## The browser suite

The browser suite is configured in `playwright.config.ts`, with its specs in `e2e/`.

**The specs:**

| Spec | What it covers |
| --- | --- |
| `site.spec.ts` | The site pages: nav, footer, landing, rooms, guide |
| `replay.spec.ts` | The replay: transport, chapters, Reveal, the night rooms, the drawer |
| `live.spec.ts` | A live game streamed to seat 7: catch-up, the deal, the dock and composer, drafts, sends, the card, the curtain |
| `workbench.spec.ts` | Single scenes at chosen beats |
| `phone-rule.spec.ts` | The phone's rule (below) |

**No server runs.** Every API call is answered by `page.route` from the bundled games in
`src/stage/fixtures/`. The live stream is served as one `text/event-stream` body, with the
status poll's `last_seq` setting what counts as history and what as news.

**Two kinds of test:**
- *Pictures:* `toHaveScreenshot` compares the page with a golden in `e2e/__screenshots__/`, and
  allows 0.5% of pixels to differ.
- *Behaviour:* clicks, keys and typing, then checks on attributes (`data-beat`,
  `data-open-prompt`), on text, and on what was posted to the mocked server.

**Phones** are covered in two ways, both in Chromium:
- smaller viewports;
- the workbench's phone frame (`frame=iphone14`), which draws the stage at an iPhone's size.

That is the phone's layout, not Safari. `phone-rule.spec.ts` is a gate on what crashed iPhones
before: nothing animating at rest, no `will-change` outside the world, no large mask, and no
large area moving while a beat arrives (`stage_architecture.md` §6).

## How a run is done here

Several agents work in this repo at once, so a run must test exactly one change and must not
disturb anyone's server.

1. **Build a scratch copy:** `git archive HEAD frontend` into a scratch folder, then copy in only
   the files of the change being tested. Where a file also holds someone else's unfinished
   edits, copy in only your own hunks. Link `node_modules`, copy `.env.local`, run `next build`.
   A separate folder keeps the build from overwriting a dev server's `.next`.
2. **Serve it on 3121**, the port kept for test runs. Check first that the port is free
   (`ss -ltnp`). Once started, check that the server answering is yours: `readlink
   /proc/<pid>/cwd` names its folder. A run against someone else's build proves nothing.
3. **Run the whole suite and regenerate every golden:** `WORKBENCH_URL=http://localhost:3121
   npx playwright test --update-snapshots=all`. Plain `--update-snapshots` rewrites only the
   goldens that fail, so a small deliberate change that stays under the 0.5% tolerance would
   never be written.
4. **Compare each rewritten golden with the commit the build was made from.** Keep only the
   ones your change explains. Put back the rest:
   - sub-pixel noise;
   - a clock that read a second later;
   - a lazily mounted section shot before it mounted;
   - goldens another agent's change left stale, which are theirs to update.
5. **Stop the server on 3121.**

Ports: 3000 is the owner's, 3117 and 3118 are dev servers, 3121 is for test runs. Never start
a server on a new port.

## Diagnostics

These are measurements, not tests. Run them before and after a change, under one script, in
one sitting (`frontend_lessons.md` 25).

- **`scripts/profile-theatre.mjs`:** the October audit's census of the DOM, pictures, animation
  and layers, in Chromium or WebKit.
- **A render census:** how often each component renders during an interaction. A stand-in
  React DevTools hook, installed before React loads, counts the components that did work in
  each commit (lesson 33). It runs on a dev build, where component names survive. It found
  that typing redrew the whole live stage.
- **A picture census:** the largest size each picture is drawn at, by component. This sized
  the phone copies of the heads (lesson 37).
- **A throttled phone profile** in Chromium (slow network, 4× CPU) for load order, as in the
  carriage case (lessons 29–31).

## What none of this covers

- **iOS Safari itself.** iPhone memory limits, Safari's compositor and real frame rate show up
  only on the phone. Every Safari crash this project had was found there.
- **WebKit at all.** The suite runs in Chromium only.
- **The real server.** The API is mocked, so a contract change on the server shows up only
  in a real game. `npm run generate-api-types` keeps the types in step.
- **The server's tiers.** `e2e/live.spec.ts` decides what seat 7 receives from its own copy of
  the server's entitlement (its `OBSERVER`, `FACTION` and `SEAT` sets, copied from
  `server/game/entitlement.py::entitled` and `server/schemas/events.py::EVENT_TIERS`). A change to
  the server's tiers passes the browser suite unchanged. On 2026-10-26 the copy already lacks two
  seat-tier types, `uses_remaining` and `night_record`, which the nine-seat game it streams never
  carries.
- **Sound.** The music's cue logic is unit-tested, but the browser suite never plays audio.

## Who runs the browser tests

Headless is the normal way to run Playwright for everyone (a CI would run it so too; this
project has no CI): it is faster,
and it is what a test machine has. A person debugging a failure adds:
- `--headed`, to watch the browser;
- `--ui`, to step through tests with a timeline;
- `--debug`, to pause on each action.

`npx playwright show-report` opens the last run's report, with traces.

In this project the suite was built so an agent can see the stage without the owner at the
screen (the config's header says so). The owner's own checks are by hand, on the phone and the
desktop, and they remain the final word on how it feels.

## Later, not now

- **WebKit for behaviour tests only.** Add a `webkit` project to `playwright.config.ts` running
  the behaviour tests (about 20–30: live, replay, composer), without screenshots. WebKit draws
  fonts differently, so pictures would need a second set of goldens. It would catch
  WebKit-only script and layout bugs. Linux WebKit is not iOS, so it would not catch memory
  crashes. Playwright's WebKit is already installed here.
- **Tests the October audit proposed** (`frontend-audit-2026-10-11.md`, "Tests to add"):
  - a visibility lifecycle;
  - picture density at several screen sizes;
  - a live burst and reconnect;
  - a soak of 15–30 minutes on a phone.
