# Assessment: client (area B)

Scanned 2026-10-26, read-only. Code checks were made by reading `frontend/src/`, `frontend/e2e/` and,
for one constraint, `server/game/run_config.py`. Nothing was run. "Feeds" uses the brief's numbering:
stories 1 to 10 (§5), the learning topics (§6), playbook items 1 to 6 (§7) and three new playbook
candidates numbered 7 to 9 below.

## Summary table

| Document | Kind and status | Main issue | Feeds | Proposed action |
|---|---|---|---|---|
| `build_plan.md` | Plan plus design record (§4, §5), ruled 2026-08-20; partly superseded. Holds a deploy log | 11,048 of its 14,954 words are the deploy record (about 70 entries, 2026-08-21 to 2026-10-22). §4 and §5 carry the client's load-bearing rulings, but with four stale passages (URL scrub state, the `GameView` sketch, the stream's error handling, the persistence table). §9's testing line is superseded | 1, 3, 4, 6, 8, 9; playbook 6 and new 7; `loading_and_deploy` | As-built status block at the head. Move the deploy record to a new `deploy_log.md` (journey log). Dated notes in §3, §4, §5, §8, §9 (named below) |
| `build_log.md` §0 to §7 | Journey log organised by kind of problem, 2026-08-21, amended 2026-09-27 and 2026-10-12 | No section index. Written in the first person by the AI builder ("I introduced"), which a write-up must not quote as the owner. §3.11's "failed tokens are cleared" and §6's "Standing gap" are superseded. §6.1 to §6.3 are server refactors | 1, 3, 4, 6; `realtime_and_sync`, `testing`; playbook new 9 | Keep whole. Add the section index below. Two dated notes (§3.11, §6 Standing gap). Placement note for §6.1 to §6.3 |
| `stage_architecture.md` §1, §2, §8 to §11 | Living spec, ruled 2026-09-25 | §2 (the axes) is current and is the best one-paragraph statement of "live and replay on one renderer". §8's tree omits the pure state files that make the stage testable without timers. §9 names nine seats. §11 is a finished work order | 1, 3, 4; playbook 1; `stage_motion` | Light edit: §8 gains one line each for the state and cache files; dated note on §9's seat row; mark §11 "done 2026-09-25" |
| `site_architecture.md` | Living spec for the site pages, sections dated 2026-10-14 to 2026-10-18 | None for chapter C. It is out of the chapter | playbook (controls kit); `loading_and_deploy` (PageGate) | Status line and index entry |
| `ux_journeys.md` | Living spec in part (ruled 2026-08-21 "provisional"); its game-screen decisions describe the v1 theatre deleted 2026-09-25 | The status line still calls D1 to D24 "the working spec for the v1 build". §0 cross-references are wrong (D20 for D22, D22 for D23). §8's completeness table is the nine-seat wire (27 events, 8 action kinds). D23 is the most current client account of reconnection | 1, 3, 4; `realtime_and_sync` | Status line naming what is living (§0, D23, D25, the site decisions) and what the stage replaced. Fix the two §0 references. Dated note on §8 |
| `ux_baseline.md` | Superseded (2026-09-25 by `stage_architecture.md` and `beat_sheet.md`; 2026-10-16 by `typography.md`; site pages by `site_architecture.md`) | Its header still reads as the binding v1 spec. Its §4 "SSE reconnect is silent" was overruled 2026-10-11 (ux_journeys D23) | 1 (§4 no token streaming), 3 (§4 never gate) | Four-line superseded card at the head. No rewrite |
| `testing.md` | Living how-to, written for the owner | Counts are stale (5 spec files; the folder holds 8). "people and CI alike" reads against the no-CI fact. Silent on the beat goldens, the fixtures' origin and the live spec's hand copy of the server's entitlement table | 6; `testing`; playbook new 8 | Light edit (named below). It seeds `learning/testing.md` (walk outline in the area section) |
| `ten_seat_pass.md` | Dated pass record with rulings, 2026-10-10 to 2026-10-16 | §8 and §9 say "uncommitted"; deployed 2026-10-11 at `74d8206b`. §6's draw gap closed 2026-10-17. §10 to §11 are an information-boundary ruling (the night bar must not leak who has uses left) with no link from the transport doc | 3, 6; playbook 6 | Status line; dated notes on §6, §8, §9 |
| `design_log.md` | Journey log of the June paper design (2026-06-06) | Status line "ideas only, nothing here is implemented or scheduled" is false today. §8 is the origin of story 1; its reason (a) names the novelty gate, which no longer exists | 1 (§8); 9 (§10); none else | Status line and the section index below |

## Per document

### build_plan.md

- **Kind and status.** Three things in one file: the plan (§1 rulings, §2 stack, §3 layout, §7
  phases), the client's design record (§4 state model, §5 wire integration), and a deploy log
  (from "Deploy record." in §7 to the 2026-10-22 `55b842fc` entry). Ruled 2026-08-20. The plan
  ran: P0 to P3 were built by 2026-08-21 (build_log head). The theatre it planned was replaced on
  2026-09-25 (`stage_architecture.md` §1 ruling 6). The header names no as-built state.
- **Reader question.** How is the browser app structured, what holds its state, and how does it
  talk to the server?
- **Plan against as-built**, section by section:

| Section | As planned | As built (checked by reading) |
|---|---|---|
| §1 ruling 8, §9 | Vitest on `src/game/` only; no component tests; no E2E | Superseded. 73 unit test files across `src/` and 8 Playwright specs in `e2e/`, Playwright brought in by `stage_architecture.md` §1 ruling 1 (2026-09-25). Home: `testing.md` |
| §2 | Playwright skipped; no `motion` | `motion` added (stage_architecture §1 ruling 2); Sentry added 2026-10-17 (deploy record, `ac7acec7`) |
| §3 type codegen | `openapi-typescript http://localhost:8000/openapi.json` (a running server) | `package.json` `generate-api-types` runs `python -m server.openapi` into a committed `src/types/contracts/openapi.json`, then `openapi-typescript`; no server needed. The façade (`src/types/contracts/index.ts`) holds |
| §3 routes | `/rooms/new`; `useFilterState` | `/play/room` since 2026-10-18 (`/rooms/new` redirects 308); `useFilterState` deleted 2026-09-25 (stage_architecture §10); a `(site)` route group (site_architecture "Routes") |
| §4 plane 2 | "one Zustand store per open game" | One module-level store, `src/game/store.ts::useGameSession`, hydrated and reset per game. The design (append-only log, folded view, live-seq ledger, monotonic pacing, per-slice selectors) holds |
| §4 plane 3 | URL search params own the scrubber (`?day=3&seq=214`), shareable deep links | Not built after the stage replaced the scrubber. `TheaterClient` reads only `from` and `still` |
| §4 `GameView` sketch | `transcript`, `votes`, `nights`, `xrayUnlocked` | `src/game/types.ts::GameView` has `days`, `timeline`, `over`, `lineup`, `neutralResult`, `thinking`, and `xray.available` in place of `xrayUnlocked` (an "arrived" flag, not a permission: `foldEvents.ts` head). The sketch said "refine while implementing"; it was |
| §4 rules | fold is the heart; never gate; `day_summary_structured` never fires | First two hold (`foldEvents.ts` head; `FoldOptions.mySeat`). Third superseded 2026-10-04: the carried summary is public (beat_sheet §13) |
| §5 `useGameStream` steps 1, 2, 4 | snapshot, then stream; poll ~10 to 15 s as the dead-game detector | Hold. `useGameStream` polls 3 s while waiting, 12 s while running |
| §5 step 3 | `onerror`: ignore when hidden; log on CONNECTING; close and surface otherwise | Superseded (2026-10-11, 10-15, 10-17). The page reopens the stream itself on `visibilitychange` and `online`; a watch reopens a stream silent past 40 s (`STREAM_SILENT_MS`) or closed for 10 s; a drop under 20 s is a blip (`BLIP_MS`); catch-up frames are folded in blocks (`catchUpBatch`). All in `src/hooks/catch-up-boundary.ts` and `useGameStream` |
| §5 seat identity | cookie loss → `POST /rejoin` | Holds, with one correction (2026-10-15, multiplayer audit): the token is forgotten only on a definite refusal, 403, 404 or 410 (`src/lib/request.ts::ApiError.refusesToken`; `GameClient`; `LiveTheatre.tsx::asSeat`) |
| §5 persistence inventory | eight keys, "one `lib/storage.ts` module owns the key names" | Three rows stale. `byok_key` is now `byok_key:{provider}`, one per company (2026-10-21), the old slot migrated. `told_{gameId}_{seat}` is not in the code; `live_{gameId}` (`liveSeen`) and `away_{gameId}` (`awayTold`), both sessionStorage, are missing from the table. Two keys live outside `storage.ts`: `ninth-express:home-screen-tip` (`src/stage/HomeScreenTip.tsx`) and `music-bench-keep` (the music workbench) |
| §5 draft | "server landed 2026-09-17, UI pending" | Built (ux_journeys D25, as built 2026-09-29). §8's "❌ UI" is stale too |
| §7 deploy notes 1 to 3 | Cloudflare, Google credentials, `memory_stores/` mount | Repeat build_log §1.4, §1.2, §1.3. Note 3 superseded 2026-10-14 (the Postgres store; the mount is gone, deploy record `344b9e58`) |
| §8 matrix "as of 2026-08-20" | "live is memory-OFF (research closure)" | Superseded: memory is a per-game choice since 2026-09-17 (`223fc9b`), default off; available on the ten-seat cast since 2026-10-14 |

- **Currency** (story 1, 3, 4 claims): checked above against `src/game/store.ts`,
  `src/game/foldEvents.ts`, `src/hooks/useGameStream.ts`, `src/hooks/catch-up-boundary.ts`,
  `src/lib/storage.ts`, `src/lib/request.ts`. The mechanism as ruled holds; the four departures
  are the stream's error handling, URL scrub state, the view's shape and the persistence keys.
- **One-home conflicts.**
  - Deploy notes 1 to 3 against build_log §1.2 to §1.4: home build_log §1; the plan keeps a
    one-line pointer.
  - The fold rule (one reducer, three surfaces) is also in build_log §4.1, `foldEvents.ts` head and
    stage_architecture §2: home the new client design record (area section); here a summary.
  - "Never gate" is also in build_log §4.3 and §3.10, ux_journeys §0, ux_baseline §4: same home.
  - The persistence inventory against `lib/storage.ts`: the code is the truth; the corrected table
    moves to the client design record and this file links to it.
  - The draft (§5) against ux_journeys D25: home D25.
- **Feeds.** Story 1 (§4 fold, §5 snapshot then stream, §2 "no WebSocket" reasoning); 3 (§4 last
  paragraph); 4 (§5 seat identity and status poll); 6 (§3 façade, §6 typed events reach OpenAPI,
  drift 500s loudly); 8 (§5 cookie `Path=/games/{id}`, same-site requirement, localStorage
  backup); 9 (§5 BYOK remember is client-only). Playbook 6 (the §1 rulings table, re-ruled in
  place with dates). Playbook new 7 (the deploy record's procedure). `loading_and_deploy` (deploy
  notes; the `next/font` build failure, entry `b203158e`, 2026-10-18).
- **Proposed action.**
  1. Status block under the title: "Plan ruled 2026-08-20; P0 to P3 built by 2026-08-21, P4
     deployed. The v1 theatre was replaced on 2026-09-25 (`stage_architecture.md`). §4 and §5 are
     the client's design rulings and hold with the dated notes below; §9 is superseded by
     `testing.md`."
  2. Move the deploy record to `frontend/docs/deploy_log.md`, kept whole, with a month index
     (August, September, October) and a head paragraph naming the procedure (clean detached
     worktree, `:prev` tags as rollback, migration first, pre-flight in the new image, smoke list,
     no rooms or games running). Leave one line and a link in §7.
  3. Dated notes in place: §3 (codegen, routes), §4 plane 3 and the sketch (point at
     `game/types.ts::GameView`), §5 step 3 (point at `catch-up-boundary.ts`), §5 persistence
     table (corrected, or moved and linked), §5 draft, §8 memory and draft rows, §9 (superseded).
- **Terms used before definition.** R7 (§4 "Post-game R7 flush": a server ruling, never
  explained here), tier (§4), the X-ray (§3, defined only in P1), seat token, `host_key`, park
  (§8 "re-parks pending turns"), the car and the set (deploy record), Reveal (deploy record
  2026-10-22, the X-ray's name in the UI since 2026-09-29; beat_sheet §0 says so, this file
  does not).

### build_log.md §0 to §7

- **Kind and status.** Journey log, organised by kind of problem, not by date. Written
  2026-08-21; §3.13 and §3.14 added 2026-09-27, §3.15 on 2026-10-12. The header's "amendments
  ... are not committed, deployed, or live-played yet" reads as current. It is not: every fix
  in §3.8 to §3.11 is in today's code (checked below).
- **Reader question.** Where did reality disagree with the specs while the client was built, and
  what did each disagreement cost?
- **Currency** (story 4 depends on §3.2, §3.8, §3.9, §3.11):
  - §3.2, history against news by a boundary taken at connect: holds in
    `src/hooks/catch-up-boundary.ts::catchUpBoundary`. It was extended on 2026-10-11 to cover a
    reconnect (everything is history from the drop until a fresh status), and on 2026-10-17 a
    drop under 20 s plays as news (`briefDrop`).
  - §3.8, dedupe by membership: holds in `src/game/store.ts::addDurable` (a binary search,
    `holds`; an insert below the head re-folds the sorted log).
  - §3.9, a status may clear only requests at or below its own `last_seq`: holds in
    `store.ts::syncPending`. A second guard was added on 2026-10-15: a status older than the
    request does not set its deadline either.
  - §3.11, rejoin reopens the stream: holds. `useGameStream`'s effect depends on `status?.you`,
    so a seat appearing closes the anonymous source. Departed: "failed tokens are cleared". Since
    2026-10-15 only a refusal clears one (`ApiError.refusesToken`).
- **One-home conflicts.**
  - §1.2 to §1.4 against build_plan's deploy notes: home here.
  - §3.2 and §4.1 to §4.3 restate ux_journeys §0: the ruling's home is ux_journeys §0; these are
    the build's account of meeting it.
  - §3.12's server clock (`GameStatus.server_time`) touches the AFK-clock ruling whose server
    home is area A's; here it is only the client half.
  - §3.15 against beat_sheet §2 row 3 and §12: home beat_sheet §12 (the living rule); §3.15 keeps
    the case (game 403f4dbc).
- **Feeds.** Story 1 (§1.4 Cloudflare buffering; §2.6 the frame names; §4.1); 3 (§3.3 the
  observer map, §3.10, §4.3); 4 (§3.1, §3.2, §3.8, §3.9, §3.11, §3.12, §3.13); 6 (§2 whole: the
  593-event game read before code; §6 the verification table); 8 (§3.1, §3.13). Learning:
  `realtime_and_sync` (§3.2, §3.8, §3.9), `testing` (§6), `loading_and_deploy` (§1). Playbook
  new 9 (independent cross-layer review: §3.8 to §3.12 and §6's last row).
- **Proposed action.** Keep whole. Add this index at the head, after the header:

| Section | Content | Feeds |
|---|---|---|
| §1.1 to §1.7 | Deploy and environment: wrong service on port 8000, eager credentials, the missing store mount, Cloudflare buffering SSE, the compose file, the database outside compose, tooling friction | story 1 (§1.4); `loading_and_deploy` |
| §2.1 to §2.6 | The wire against the docs, read off a real 593-event game: a day is slots, nights belong to the day before, phases can be absent, no `can_pass`, an untyped turn endpoint, small contract facts | story 6; client design record (fold) |
| §3.1 to §3.7 | Client bugs: seat recovery that never fired, a refresh replaying the drama, a useful wrong test, health check on IPv6, white flash, invisible night tint, small slips | stories 3, 4; `testing` |
| §3.8 to §3.12 | The independent review's cross-layer finds: R7 backlog dropped, stale turn dock, the private data the UI hid, rejoin without the stream, smaller finds | stories 3, 4; playbook new 9 |
| §3.13 | Coming back to your own room made a second passenger (2026-09-27) | stories 4, 8 |
| §3.14 | The carriage's sides on a phone (2026-09-27) | none |
| §3.15 | The ballot opened among the day's passes (2026-10-12) | story 7 |
| §4.1 to §4.6 | Judgement calls: the reducer knows no time, "who am I" passed in, X-ray is arrangement, two takeovers, deviations, missed scope | stories 1, 3; client design record |
| §5.1 | Portrait generation blocked, then landed | none (art; superseded by the cast puppets) |
| §6 | What verification caught, by method | story 6; `testing` |
| §6.1 to §6.3 | Server refactors (2026-08-22): one game table, the durability split, the router split | area A (see placement) |
| §7 | Handoff notes | `loading_and_deploy` |

  Dated notes: §3.11 ("since 2026-10-15 a token is cleared only on a refusal"), §6 "Standing gap"
  ("closed from 2026-09-25 by the Playwright suite and the owner's checks on the running app;
  see `testing.md`"), §7 item 5 ("the portraits were removed 2026-10-17; the seats are the cast
  puppets").
- **Attribution.** The log's "I" is the AI builder ("Client bugs I introduced and caught",
  "I wired that recovery"). The write-up may cite its findings, never its voice as the owner's.
- **Terms used before definition.** the dock (§2.4, never defined), the beat layer (§3.2), R7
  (§3.8), the cutter and hold (§3.15), the X-ray (§3.10), the platform and the manifest (§3.13).

### stage_architecture.md §1, §2, §8 to §11

- **Kind and status.** Living spec, ruled 2026-09-25; the code-shape half of the stage. Its own
  head says it wins over the handoff.
- **Reader question.** How is the stage built in code: what does a scene render from, where does
  each piece live, and what did it replace?
- **Currency** (stories 1 and 3 lean on §2):
  - §2, a scene is `Scene({view: fold(events ≤ cursor), beat, me, presentation})` and reads no
    store: holds. Scenes take `SceneProps`; `stage/containers/` own the store, the stream and the
    queue; `foldEvents` never gates (`foldEvents.ts` head). The live cursor "the tail behind a
    catch-up queue" is what `stage/containers/live-state.ts` describes at its head.
  - §8 tree: every folder it names exists. It omits the files that carry the design's testable
    half: `containers/live-state.ts` and `replay-state.ts` (pure reducers, no timers, "so a test
    can feed a game in one event at a time"), `live-queue.ts`, `transport.ts`, `fold-cache.ts`
    (the fold remembered per beat, 96 kept), `warm-reel.ts`, and `stage/set.ts`, `slot.ts`,
    `motion.tsx`.
  - §9 row "the wire's seats are `player_1..player_9`": nine seats; the stage lays out nine or
    ten from `game_started.seats` since 2026-10-10 (ten_seat_pass §1).
  - §11 is a work order, done 2026-09-25 (§10 says so).
- **One-home conflicts.** §2's tier axis restates the never-gate rule: home the client design
  record. §8's mini-mode paragraph and site_architecture's carriage section describe the landing
  preview from two sides; both are fine as they are (code shape here, page there).
- **Feeds.** Story 1 (§2: live and replay on one renderer); 3 (§2 tier axis: "the X-ray is a
  lens on observer tier, and an agent has no client"); 4 (§2 cursor); playbook 1 (§1 ruling 1
  workbench, §11's split of steps between Opus agents and the main loop, the beat sheet's
  order rule); `stage_motion` (§6, area C and D).
- **Proposed action.** Light edit: §8 gains one line each for the state, queue, transport, cache
  and warm-reel files; dated note on §9's seat row; §11 headed "done 2026-09-25, kept as the
  record of who built what".
- **Terms used before definition.** beat (§2, defined only by pointer to the beat sheet), the
  slot, the drawer, the film and the File (§2 Presentation row), the wing (§8), the HUD, the
  bleed (§1, defined in §3).

### site_architecture.md

- **Kind and status.** Living spec for the pages around the theatre. Sections dated 2026-10-14
  to 2026-10-18; no status line.
- **Reader question.** How are the site pages built: routes, tokens, fonts, the controls kit,
  the walls, and how a page comes up whole?
- **Currency.** Not checked; no chapter C story depends on it.
- **One-home conflicts.** "Pages come up whole" (PageGate) is also told in five deploy entries of
  2026-10-18 (`1290eddb` to `ac97363c`) and, per area C, in `frontend_lessons.md`: home here for
  the mechanism; the deploy log keeps the dated steps.
- **Feeds.** Playbook (the controls kit's rule "a new background needs a surface block, not a
  new button": area D to place); `loading_and_deploy` ("Pages come up whole"). Nothing in
  chapter C.
- **Proposed action.** Status line: "Living spec for the site pages, current to 2026-10-18."
  Index entry.
- **Terms used before definition.** the bench (a claude.ai artifact link), `cqi`, 9-slice, the
  carriage, the departures hall.

### ux_journeys.md

- **Kind and status.** Ruled 2026-08-21 as "provisional defaults". Its status line promises an
  as-built update post-MVP. That happened only in places: D13, D23 and D25 carry as-built notes
  (2026-09-29 to 2026-10-11). D8 to D22 describe the v1 transcript theatre (day pages, banners,
  `TurnDock`, `WinnerTakeover`), deleted 2026-09-25. The stage realises those moments through
  `beat_sheet.md` §1 to §10.
- **Reader question.** For every route and game state, what does each kind of viewer see, and
  which decision was ruled?
- **Currency** (story 4 depends on §0 and D23):
  - §0 "beats fire on live arrival only; the store flags live seqs": holds, cited in
    `store.ts`'s header and `foldEvents.ts`'s head.
  - D23 reconnect (as built 2026-10-11): holds in `useGameStream` (reopen on visibility and
    online) and `lib/storage.ts::liveSeen`, `awayTold` (the "You're back" notice).
  - §0's own cross-references are wrong: "the game-over banner (D20)" is D22, and "refresh-mid-game
    safe (D22)" is D23 (`store.ts` cites D23 correctly).
  - §8's completeness table lists 27 event types and 8 action kinds: the nine-seat wire of
    2026-08-21. The ten-seat wire has 17 kinds (ten_seat_pass §2) and new events
    (`night_record`, `uses_remaining`, the memory events).
- **One-home conflicts.**
  - §0 is the ruling's home for live-against-history and never-gate. build_log §3.2 and §4.1 to
    §4.3, ux_baseline §4 and the store's header summarise it.
  - D23's reconnect account against beat_sheet §12: the beat sheet holds what the stage does
    with catch-up; D23 holds the notice and its words. Both link; no change.
  - D25 is the draft's home; build_plan §5 should link to it.
- **Feeds.** Story 1 (§0); 3 (§0 first rule, D21 "no new information is revealed by dying"); 4
  (§0, D22, D23); `realtime_and_sync` (§0, D23).
- **Proposed action.** Status line: "§0 is binding and current. D23 and D25 are current as
  built. D1 to D7 describe the site pages (now `site_architecture.md`). D8 to D22 and §9 describe
  the v1 theatre, replaced 2026-09-25; the stage's truth is `beat_sheet.md`. §8 is the nine-seat
  wire as of 2026-08-21; the ten-seat kinds are `ten_seat_pass.md` §2." Fix the two §0 references.
- **Terms used before definition.** the strip's door (D23), the wing and the drawer (D23), the
  File, Reveal, R7 (D22), the dock (§0 by reference).

### ux_baseline.md

- **Kind and status.** Superseded, though its header still reads as the binding v1 spec. The
  game-route layout (§2 "mobile-first, one column") was overruled by `stage_architecture.md` §1
  ruling 3 (2026-09-25). The theatre (§3, §5) was replaced on 2026-09-25. The aesthetic (§1 pixel
  avatars, the pixel display face) gave way to the Playhouse and `typography.md` (2026-10-16;
  "the Silkscreen pixel face is gone", site_architecture "Fonts"). Its §4 "SSE reconnect is
  silent" was overruled by ux_journeys D23 (2026-10-11).
- **Reader question.** What did v1 of the app look like and promise, page by page?
- **Currency.** Not checked; superseded record.
- **Feeds.** Story 1 (§4 "no token streaming anywhere"); 3 (§4 "never hide data that arrived,
  never fake data that didn't"). Nothing else.
- **Proposed action.** The four-line card at the head:
  - *Question:* what should v1 of the app look like and do, page by page?
  - *Decision:* ruled 2026-08-20, refined 2026-08-22.
  - *Answer:* built as v1 (build_log); the theatre replaced 2026-09-25, the type 2026-10-16.
  - *What followed:* `stage_architecture.md`, `beat_sheet.md`, `site_architecture.md`,
    `typography.md`. Two cross-page rules survive (§4: no token streaming; the client never gates).
- **Terms used before definition.** séance noir, the machine world (§1), the inspector.

### testing.md

- **Kind and status.** Living how-to, written for the owner; no date in the file.
- **Reader question.** What does each kind of frontend test check, how is a run done here, and
  what can none of them see?
- **Currency** (story 6 leans on "goldens pinned the spec"):
  - "5 spec files, 173 tests": `e2e/` holds 8 spec files today (`panel-persistence`,
    `vote-performance`, `wing-persistence` added). Deploy entries report 183 of 183 (2026-10-17),
    193 of 193 (2026-10-21) and 185 of 195 with known failures (2026-10-22). "About 63 files":
    73 unit test files today.
  - "Headless is the normal way ... for everyone, people and CI alike" is a general statement,
    but read in this repo it suggests a CI. There is none; `playwright.config.ts`'s header says
    "not a CI gate until the scenes stop moving".
  - Missing: the beat goldens (`src/stage/beats/__goldens__/`, `toMatchFileSnapshot` in
    `beatsFor.test.ts`, which hold the beat list to `beat_sheet.md` on the nine-seat fixture
    9369a5c1 and the Phase 2 game; the ten-seat game is held by targeted assertions, not a whole
    golden); where fixtures come from (real archived games in `src/game/__fixtures__/` and
    `src/stage/fixtures/`, the ten-seat one from the translator golden, ten_seat_pass §4); and
    the live spec's blind spot: `e2e/live.spec.ts` decides what seat 7 receives from its own copy
    of the server's entitlement (`OBSERVER`, "the server's live entitlement ...
    `server/game/entitlement.py`"), so a change to the server's tiers passes the browser suite.
- **One-home conflicts.** "How a run is done here" (scratch build, port 3121, regenerate every
  golden, keep only the explained ones) repeats the owner's working rules in memory (picture swap
  means targeted tests; ports). Home here for the procedure; the playbook links.
- **Feeds.** Story 6 (the honest "how much did I write": the suite is AI-written to the owner's
  spec, and this doc says what it proves); `testing` (the walk); playbook new 8.
- **Proposed action.** Light edit: replace the counts with a dated line or drop them (the
  evidence pass dropped counts of the unaudited AI-written suites); reword the CI sentence ("CI
  would too; this project has none"); add a short "What the goldens pin" paragraph and the
  entitlement blind spot under "What none of this covers". Then it becomes the source of
  `learning/testing.md` (outline below).
- **Terms used before definition.** golden, the workbench, `frame=iphone14`, the phone's rule.

### ten_seat_pass.md

- **Kind and status.** Dated pass record with its rulings, 2026-10-10 to 2026-10-16. §8 "uncommitted,
  P0 met" and §9 "uncommitted" read as current; the pass deployed on 2026-10-11 at `74d8206b`
  (build_plan deploy record). §6 "drawn games are not archived" closed on 2026-10-17 (`cca44ed8`).
  §1 "memory stays off ... until a store exists" was overtaken on 2026-10-14 (the Postgres store,
  memory available, default off).
- **Reader question.** What did the frontend have to change for the ten-seat cast, and what was
  ruled on the way?
- **Currency.** Not checked beyond the deploy record; dated record.
- **One-home conflicts.** §10 and §11 rule that the live night bar counts every living seat, so
  the bar cannot leak which roles still have uses. That is a side channel of story 3, and the
  server half lives in `server/game/pacing.py`. Home for the ruling: here. The transport doc's
  side-channel list (area A, transport §6) should summarise it in one line and link.
- **Feeds.** Story 3 (§1 "a concealed body stays concealed everywhere the viewer is not the
  X-ray"; §10 and §11); 6 (§1 "a no-action answer is the server's word, never derived"; §2 the
  turn table); playbook 6 ("Mine, flagged for the owner (change here first if overruled)"); a
  possible playbook step list for a wiring pass: census, rulings, slices in dependency order,
  P0/P1/P2 readiness, acceptance with what was fixed and what is left to rule.
- **Proposed action.** Status line: "Deployed 2026-10-11 at `74d8206b`; §6's draw gap closed
  2026-10-17; the claim selector still open." Dated notes on §6, §8 and §9.
- **Terms used before definition.** the wing's band, the plate, sealed plates, the lobby (here the
  night lobby, not the rooms lobby), the pill, the bar.

### design_log.md (June paper design; index only)

- **Kind and status.** Journey log of the 2026-06-06 discussion. Its status line ("ideas only,
  nothing here is implemented or scheduled") was true then and is false now.
- **Reader question.** What was the frontend meant to be, before any of it was built?
- **Currency.** Not checked. One note for story 1: §8 reason (a) for streaming events, not tokens,
  is that the novelty gate vetoes speeches after generation. The novelty gate is gone; the echo
  gate (`Agents/turn/echo_gate.py`, per the gameplay assessment) still holds a generated line
  back, so the reason survives under a different gate. The write-up must name the current one.
- **Proposed action.** Status line: "The June 2026 paper design. §8 became the shipped transport;
  §2 and §6 became build_plan's phases; most of §7, §9, §10 and §11 stayed ideas." And this
  index:

| Section | Content | What became of it |
|---|---|---|
| §1 | Identity: "watch AIs deceive each other, and see exactly why" | the landing's line; the X-ray as the product |
| §2, §6 | Feature tiers; the owner's MVP cut | build_plan P1 to P3 |
| §3, §7 | Séance noir; pixel art | ux_baseline §1, then replaced by the Playhouse |
| §4 | The one artifact if only one is built | the replay theatre first (build_plan P1) |
| §5 | Competitive landscape | none |
| §8 | Events not tokens, the log as the replay, SSE + POST, web not native, one process | story 1; `server_client_transport.md` |
| §9 | Human play as a model signal | not built |
| §10 | Daily puzzle; cost and scale posture | puzzle not built; story 9's origin |
| §11 | Rigor boundary; ghost mode | ghost guesses (build_plan ruling 7) |
| §12 | Phasing and effort estimate | superseded by build_plan §7 |
| §13 | Multi-human tables | build_plan P3, rooms |
| §14 | Backend touchpoints | none |

## Area-level

### Overlaps, one home each

| Ruling or finding | Told in | Home | The others |
|---|---|---|---|
| Live against history: beats fire only on live arrival | ux_journeys §0, build_log §3.2, `store.ts` header, beat_sheet §12, live-state.ts head | ux_journeys §0 (ruling); the client design record (mechanism) | summarise and link |
| One fold serves replay, live and the R7 reveal | build_plan §4, build_log §4.1, stage_architecture §2, `foldEvents.ts` head | client design record | one sentence and a link |
| The X-ray is arrangement, never permission | build_plan §4, build_log §3.10 and §4.3, ux_journeys §0, ux_baseline §4, stage_architecture §2 | client design record (client half); transport §5 and §6 (server half, area A) | link |
| Persistence inventory | build_plan §5, `lib/storage.ts` | the code, mirrored once in the client design record | build_plan links |
| Seat recovery and rejoin | build_plan §5, build_log §3.1 and §3.11, ux_journeys D23, `GameClient`, `LiveTheatre.tsx::asSeat` | client design record (client half); transport §6b (area A) | link |
| Reconnect and the "You're back" notice | ux_journeys D23, beat_sheet §12, `catch-up-boundary.ts` | ux_journeys D23 (words and ruling); beat_sheet §12 (stage) | client design record summarises |
| Deploy notes (Cloudflare, credentials, store mount) | build_plan §7, build_log §1.2 to §1.4 | build_log §1 | build_plan one line |
| Prompt after its announcement; solo waits for the stage | build_log §3.15, beat_sheet §2 and §12, live-state.ts head | beat_sheet §12 | build_log keeps the case |
| The draft helper | build_plan §5 and §8, ux_journeys D25, stage_architecture §9 | ux_journeys D25 | link |
| The live night bar's total | ten_seat_pass §10 and §11, `server/game/pacing.py` | ten_seat_pass §10 to §11 | transport's side-channel list links (area A) |

### Placement unclear

- **build_log §6.1 to §6.3** (2026-08-22) are server refactors: the single game table, the
  durability split, the router split. They sit in the client log because the same agent did
  them. They belong with area A (`server_design_notes.md` or `server_encountered_challenges.md`),
  and story 5's "process by persistence" may draw on §6.1. Leave them in place with a pointer
  from area A's home, or move them; the owner rules.
- **The deploy record** has no home once lifted out of build_plan. `deploy_log.md` beside
  `build_log.md` is proposed; it is a journey log and is kept whole.
- **ux_journeys D1 to D7** (site pages) overlap `site_architecture.md`, which never cites them.
  They can stay as the August record.

### Constraint check against brief §8

- **General jump not built.** No area B document claims it. Not touched.
- **Stall watchdog not built.** No area B document claims it. Risk of a false sentence: the
  client has a stream watch (`useGameStream`'s 5 s interval with `streamStalled`, reopening a
  stream silent past 40 s). That is not the server's stall watchdog; the write-up must not call
  it one.
- **Served games carry no runtime fingerprint.** Not mentioned in area B.
- **No CI.** One reading risk: `testing.md` "people and CI alike". Proposed rewording above.
- **Persona voices are OFF.** **The record and the code contradict this constraint.**
  build_plan's deploy entry of 2026-10-19 (`5b5a23e4`) says hosted games enable
  `persona_voices=True`, and `server/game/run_config.py::game_run_config` sets
  `persona_voices=True` for every served game (solo, rooms, recovery); its docstring says "AI
  seats use their dealt puppet's speaking voice in served games". The entry of the same morning
  (`334a56e1`, "Persona voices stay off") is the earlier state. The brief's line should read
  "voices ON in hosted games since 2026-10-19, off in batch runs"; the silence ruling was not
  checked here. Nothing in `frontend/docs` needs changing for it.
- **Music deployed 2026-10-15.** Consistent (deploy entry `d4295e49` names the music bench; the
  `music` key is in `lib/storage.ts`).
- **The beat sheet and stage_architecture are the truth for the stage.** ux_journeys D8 to D22 and
  ux_baseline §2, §3, §5 still present themselves as the working spec for game screens. The
  status lines proposed above remove the contradiction. The goldens pin the beat list on the
  nine-seat fixture and the Phase 2 game; ten-seat beats are held by targeted unit tests.
- **Default seat model Haiku 5.5 since 2026-10-15.** Area B documents name no current default.
  The flash-lite mentions (the seed game, the 2026-10-04 thinking levels) are dated history.
- **Memory off by default, per game.** build_plan §8 ("live is memory-OFF (research closure)")
  and ten_seat_pass §1 read as standing rules. Both need the dated notes above.
- **Who wrote what.** build_log speaks as "I", the AI builder; ten_seat_pass's "Mine" and
  stage_architecture §11's "Who" column are the same. None of them claims the owner wrote the
  code. The write-up must cite them as the builder's record, with the owner as the author of the
  event schema, the co-author of the beat sheet, and the one who ruled.
- **One game's numbers.** build_log §1.4 (~400 events streamed), §2 (the 593-event seed game),
  §3.3 (149 annotations) and §3.15 (game 403f4dbc) are single-game figures and say so in place.
  The 2026-10-22 phone measurements in the deploy record are one session's.

### The passages a new client design record would draw on

Proposed: `frontend/docs/client_design.md`, a design record in the transport doc's form, the
browser's half of stories 1, 3 and 4. Its parts and sources:

1. **The fold and the store** (what the browser keeps, and why one pure function).
   - build_plan §4 (three planes; the fold is the heart; never gate) with its dated notes.
   - build_log §2.1 (a day is slots; annotations join by `channel_seq`), §2.2, §2.3, §3.3 (the
     observer map from observer data only), §4.1, §4.2.
   - Code: `src/game/foldEvents.ts` (head comment), `src/game/types.ts::GameView` and
     `FoldOptions`, `src/game/store.ts` (header, `addDurable`, `setMySeat`'s re-fold).
   - `frontend_lessons.md` 32 (catch-up in blocks) and 35 (a cache grown with the log); area C
     places them.
2. **Live and replay on one renderer.**
   - build_plan §4 ("The play UI is the replay UI plus input affordances"); build_log §4.1.
   - stage_architecture §2 (the five axes and the scene as a pure function) and §8 (containers own
     store, stream, transport and queue; scenes take props; the preview's `mini` mode).
   - beat_sheet head ("Change the table, change the code, regenerate the golden"), §11 (the
     replay container), §12 (live pacing), §13 (viewers and tiers).
   - Code: `src/stage/beats/beatsFor.ts` (head: pure, prefixes never shrink, "never in a live
     cut"), `src/stage/containers/live-state.ts` (head: the rules for how a beat gets on the
     stage), `replay-state.ts` (head), `fold-cache.ts` (head), `transport.ts`.
3. **Catch-up: refresh, reconnect and the R7 reveal.**
   - ux_journeys §0, D22, D23 (as built 2026-10-11).
   - build_log §3.2, §3.8, §3.9, §3.11, §3.12 (status errors surfaced; the server clock).
   - build_plan §5 steps 1 to 4, with the step 3 note.
   - Code: `src/hooks/useGameStream.ts` (head and the connect effect),
     `src/hooks/catch-up-boundary.ts` (`catchUpBoundary`, `briefDrop`, `streamStalled`,
     `catchUpBatch`), `store.ts::applyCatchUp`, `applyLive`, `syncPending`;
     `lib/storage.ts::liveSeen`, `awayTold`.
   - The server half is transport §7 (area A); the record links rather than restates it.
4. **The information boundary, client half.**
   - build_plan §4 last paragraph; build_log §3.10, §4.3; ux_journeys §0 and D21;
     stage_architecture §2 (tier axis); beat_sheet §13; ten_seat_pass §1 (concealed bodies) and
     §10 to §11 (the bar).
   - Code: `foldEvents.ts` head (`xray.available` is "arrived", not "allowed"); `beatsFor.ts`
     head; `live-state.ts` (`seesXray`: the X-ray waits for the stage to reach the ending).
5. **Identity and recovery on the device.**
   - build_plan §5 (seat identity flow); build_log §3.1, §3.11, §3.13 (`you_aboard`).
   - Code: `app/games/[gameId]/_components/GameClient.tsx` (seat recovery comment and effect),
     `stage/containers/LiveTheatre.tsx::asSeat`, `lib/request.ts::ApiError.isSeatLost`,
     `refusesToken`.
6. **The stage pipeline and its memory budget.** (Area C owns the measurements.)
   - stage_architecture §2, §3 (the 1600×900 box), §6 (the GPU rules and the phone rule entries
     from "The car's set is a baked picture" to "The next speaker's poses are decoded a turn
     ahead"), §8.
   - build_log §8.1, §8.3, §8.8 to §8.10; `phone_lessons.md`; `e2e/phone-rule.spec.ts` head.
   - Code: `src/stage/Stage.tsx`, `src/stage/set.ts`, `scenes/CarScene.tsx`,
     `instruments/Bounded.tsx`, `cast/DecodeAhead.tsx`, `containers/warm-reel.ts`.
7. **The persistence inventory.** build_plan §5's table, corrected against `lib/storage.ts`
   `KEYS` (one company per BYOK key, the two sessionStorage keys), plus the two keys outside it.
8. **The contract boundary.** build_plan §3 (type codegen and the façade, with the note), §6;
   build_log §2 whole (§2.4 `can_pass`, still absent from `server/schemas/events.py::InputRequest`
   today; §2.5 the untyped turn body); `package.json` `generate-api-types`; ten_seat_pass §1
   ("the server's word, never derived").

### Outline of the testing walk (`learning/testing.md`)

In `phone_lessons.md`'s form: the question, what is actually going on, this project's instance
with the lesson number and the code, how to see it yourself, the rule, the reading.

1. **The question.** What does a passing run prove, and about what? Start from build_log §6's
   table: the type checker and the build caught two invented field names and nothing else; the
   serious defects were found by real data, the served bytes, the public URL and a cross-layer
   review. The further a check sat from the running system, the less it found.
2. **The layers, from cheap to dear** (`testing.md` "The layers").
   - Pure reducers first: the fold and the store (`game/*.test.ts`), the beat list, and the live
     and replay reducers (`live-state.test.ts`, `replay-state.test.ts`). Why the stage was split
     into pure state plus a container that runs the clock: a test can feed a game one event at a
     time with no timers (`live-state.ts` head).
   - Fixtures are real games: the 593-event seed game, the ten-seat translator golden, the
     archived games in `src/stage/fixtures/` (ten_seat_pass §4). Why: build_log §2 found six
     contract facts in real data that no doc stated.
   - Text goldens: the beat list dumped to `__goldens__/*.txt` and compared whole. What it pins
     (the beat sheet on two fixtures) and what it does not (the ten-seat game, held by targeted
     assertions). The order rule: change the table, change the code, regenerate the golden.
   - Server-rendered component tests (`renderToStaticMarkup`) for who sees private data
     (build_log §3.10).
   - Types, lint, build: what only `next build` catches (`testing.md`).
3. **The browser suite.** Playwright against a mocked API (`page.route`), the live stream as one
   SSE body with `last_seq` setting history against news (`e2e/live.spec.ts` head). Pictures
   (`toHaveScreenshot`, 0.5% of pixels) against behaviour (attributes such as `data-beat`, text,
   what was posted). The phone frame and the phone rule as a gate (`phone-rule.spec.ts`).
   Lessons 18 and 20 (area C places them): a gate read at the end of a window, and tests that
   fail only in parallel.
4. **How to run one change here.** The scratch build, port 3121, `--update-snapshots=all`, then
   compare every rewritten golden with the commit and keep only those the change explains
   (`testing.md` "How a run is done here"). A picture swap runs only the specs that show the
   pictures (deploy entries of 2026-10-18).
5. **How to read a failure.** `show-report` and its traces, `--ui`, `--debug`. Sort a failure
   into: the change; a known flake (the landing-1440 load, the guide's case-file test, per the
   deploy entries of 2026-10-18 to 2026-10-22); a golden someone else left stale; a build that
   failed in `next/font` (entry `b203158e`: read the log for it first and retry).
6. **What it is blind to.** iOS Safari and WebKit; the real server (the API is mocked, and the
   live spec's `OBSERVER` set is a hand copy of `server/game/entitlement.py`, so a tier change on
   the server passes the browser suite); sound; and there is no CI, so a check runs only when a
   person or an agent runs it. The owner's phone and desktop checks remain the final word.
7. **The rule and the reading.** Test the pure part hard, test the drawn part by picture, and
   check on the real phone what only the phone can show. Reading: `testing.md`, build_log §6,
   `frontend-audit-2026-10-11.md` "Tests to add" (area C).

### Playbook candidates found in area B (for area D)

- **7. Deploy from a clean detached worktree.** Exemplar: build_plan's deploy record (to become
  `deploy_log.md`), e.g. the entries `a651988` (2026-10-01) and `344b9e58` (2026-10-14). Steps:
  push or note the commit; build each image from a clean detached worktree so another session's
  uncommitted work stays out; run the migration first, from inside the new image; pre-flight in
  the new image; check no rooms or games are running; swap with `compose up -d --no-build`; keep
  the old images as `:prev`; run the smoke list; record what was not yet run. The rule it taught:
  a build is of a commit, never of the working tree.
- **8. Test one change in a shared tree.** Exemplar: `testing.md` "How a run is done here".
  Steps: scratch copy from `git archive HEAD`, only your hunks copied in, its own build, the
  reserved port, confirm the server answering is yours, regenerate every golden, keep only the
  explained ones, stop the server. The rule: a run against someone else's build proves nothing.
- **9. An independent cross-layer review before calling a build done.** Exemplar: build_log
  §3.8 to §3.12 and §6's last row. Steps: hand the finished build to a reviewer that did not
  write it; ask for defects that cross layers (server ordering against client dedupe, fold
  against render); write an exact-order regression for each. The rule: event identity and event
  recency are different facts, and only a reviewer reading both sides found that.
- Confirmations for the existing list: playbook 1's exemplar sections include stage_architecture
  §1 ruling 1 and §11; playbook 6's include build_plan §1 and ten_seat_pass §1 ("Mine, flagged
  for the owner").

### Terms used before definition, across area B

beat, hold, tier, the dock, the strip, the fold, the X-ray, Reveal (the X-ray's name in the UI
since 2026-09-29; only beat_sheet §0 and stage_architecture §3 say they are the same), the bar, the car and the set, seat token, park, R7, the
wing, the slot, the drawer, the File, the plate, the platform, the pill, golden. The client design
record should define the first ten in its opening, and the learning docs should link there.
