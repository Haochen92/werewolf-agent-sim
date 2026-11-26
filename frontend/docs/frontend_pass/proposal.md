# Frontend docs pass: proposal

Prepared 2026-10-26 for the owner's review. **Nothing in `frontend/docs/` has been changed except
one new file, `frontend/docs/README.md`, the index the scan produced.** This is the plan for the
folder's three uses: source material for chapter C of the portfolio, the owner's learning track, and
a playbook of methods for directing AI builders.

**How it was made.** Four read-only scans, one per area ([`assessments/`](assessments/): server,
client, lessons, design), under one brief ([`brief.md`](brief.md)) that typed every document before
grading it, hunted five named faults, tagged every row with the chapter C story it feeds, and checked
a constraint list against the code. Code was read, never run. One constraint in the brief was wrong
and all four scanners caught it against the code: puppet voices are ON in hosted games since
2026-10-19, not off. The brief is corrected; no document in the folder states the voices setting.

The evidence pass's rubric applies ([`../../../evidence/report_pass/proposal.md`](../../../evidence/report_pass/proposal.md) §0):
the four-line card on superseded records, `path::symbol` anchors, one detailed home per finding, and
the type decides the tense. What differs here: most of the folder is living specs and dated records,
not reports, so rewrites are few and the main work is dated notes, two new documents and the learning
hierarchy.

---

## 1. Decisions for the owner

**Ruled 2026-10-26:** yes to every recommendation. D5 keep `stage_fit/` where it is; D6 drop
`opening_round_brief.md` (the placard stands; deleted in the first commit, git keeps it); D2 amended:
the topic documents are tutorials, concept first, cases as examples (the form in §3.1); D1, D3, D4, D7,
D8, D9 as recommended.

| # | Decision | Recommendation |
|---|---|---|
| D1 | **Write the client design record**, `frontend/docs/client_design.md`, in the transport record's form: the fold and the store, live and replay on one renderer, catch-up, the boundary's client half, identity on the device, the stage pipeline's budget, the persistence inventory, the contract boundary. The passage list is in the client assessment, "The passages a new client design record would draw on" | Yes. It is chapter C's largest gap: the server has transport, design notes and challenges; the browser has §4 and §5 of a plan and a log. It opens with a ten-term glossary (beat, hold, tier, the dock, the strip, the fold, the X-ray and Reveal, the bar, seat token, park), which every other document then links to |
| D2 | **The learning hierarchy**: `frontend/docs/learning/` with nine topic documents (the brief's eight plus `css_layout.md` for six layout facts that fit nowhere else), each a **tutorial**: the concepts the topic's cases need, taught first, with the cases as worked examples (the form in §3.1; owner 2026-10-26). `principles.md` becomes the index. `phone_lessons.md` stays as the dated phone case study and the interview answer. `frontend_lessons.md` stays the log; lessons keep their numbers (29a and 29b labelled in place; the 23 small things numbered S1 to S23) | Yes. The lesson-by-lesson placement (76 rows) and each topic's source passages are in the lessons assessment, "§6 delivered". Server-side lessons (principles §7, the challenges' "what to know" lines) do not get a tenth document: `server_encountered_challenges.md` and the multiplayer audit are the server's lesson docs, and the index points at them |
| D3 | **Lift the deploy record out of `build_plan.md`** into `frontend/docs/deploy_log.md`, a journey log kept whole with a month index and a head paragraph naming the procedure | Yes. 11,000 of the plan's 15,000 words are about 70 dated deploy entries; the plan's own rulings (§4, §5) are what chapter C reads. A move, in its own commit |
| D4 | **Seat absence gets one home**: `seat_continuity.md`, amended with the two October rulings (a solo table suspends while its player is away, 2026-10-11; a seat gone two turns is taken to have left, 2026-10-15), and the failure story (the events table leads the checkpoint by up to one step) gets its detailed home as `server_encountered_challenges.md` §8 | Yes. Today the solo suspension exists only in code, a commit and one aside in the beat sheet, and the failure story only in the interview one-pager |
| D5 | **`stage_fit/`**: keep in `frontend/docs/` with a pointer from the evaluation README, or move to `evidence/` per the CLAUDE.md lifecycle | **Ruled: keep.** Its runner is already in `evaluation/experiments/`; a pointer from the evaluation README |
| D6 | **`opening_round_brief.md`**: dropped or deferred? The painting was never made; the stage shows the placard you chose on 2026-10-15 | **Ruled: drop.** Deleted in the first commit; git keeps it |
| D7 | **`build_log.md` §6.1 to §6.3** (three server refactors of 2026-08-22, in the client log because the same agent did them): leave with a pointer from `server_design_notes.md`, or move | Leave, with the pointer. Moving splits a dated log |
| D8 | **"The cast record"** at the end of `cast_expansion_brief.md` (tables, the picker, `resolveCast`): a pointer from `site_architecture.md`, or move it there | Pointer. The brief stays whole as the dated record |
| D9 | **Pilots**, one per new genre: `client_design.md` (design record) and `learning/react_identity.md` (topic doc). You read both before the rest are commissioned | Yes. The transport record is the exemplar for the first; `phone_lessons.md` plus the three added parts for the second |

---

## 2. Summary of the condition

42 files plus three outside the folder that belong to the same record. By kind: 8 living specs, 7
design records, 7 journey logs, 3 lesson docs, 4 dated audits, 11 dated briefs and design files, 5
frozen artefacts. Two documents need rewriting (`principles.md` as the index; nothing else). Two
documents are new (D1, and `learning/testing.md` from the walk outlined in the client assessment).
Nine topic documents are new but written from placed material. The rest is status lines, section
indexes and dated notes.

The faults, in order of how often they appeared:

1. **The record stops at the day it was written.** The transport record's status line (2026-07-28)
   says the server and frontend are not built; ten of its passages describe the July plan where the
   build departed (route names, the event bus, the phase marker table, the exhaustiveness alarms, the
   named leak test that does not exist, the cookie path, the room TTL). `seat_continuity.md` lacks two
   October rulings. `build_plan.md` has no as-built line. Three briefs say DRAFT after shipping;
   `typography.md` says "not yet deployed"; `ten_seat_pass.md` says "uncommitted" after deploying;
   lesson 39 says "not deployed yet". The remedy is dated notes and status lines, not rewrites: the
   mechanisms as ruled hold, checked against the code in every case a story depends on.
2. **One ruling told in several places.** The AFK clocks in four documents; the fault model in three;
   the fonts in four; the jump in three; the phone numbers in three; the lighting cache key in five.
   Each gets one home (§3.4).
3. **No current account of the client** (D1).
4. **Homeless lessons.** `principles.md` cites 30 of the 50 numbered lessons and none of the 23 small
   things (D2).
5. **Terms before definition** everywhere: beat, hold, tier, dock, strip, fold, X-ray and Reveal (the
   same thing, said to be so in two places only), bar, car, set, seat token, park, R7, golden. The
   glossary in D1 is the fix; the learning docs link to it.

Three findings the chapter must not get wrong, all checked against the code: the brief's own voices
constraint (now corrected); `testing.md`'s "people and CI alike" and the audits' "CI gates" read as if
a CI exists (there is none; the suite runs when a person or agent runs it); and the client's stream
watch (reopen after 40 s of silence) is not the server's stall watchdog, which is still unbuilt.

---

## 3. Structure

### 3.1 The learning hierarchy (D2)

```
frontend/docs/learning/
  README.md                 the index (rewritten from principles.md): one section per topic, each
                            principle line kept, the "Read" lists kept, linking the topic doc
  react_identity.md         keys, memo, effects, where state lives            12 rows
  rendering_pipeline.md     layers, paint rectangles, transforms, filters     12
  memory_and_pictures.md    decoded bytes, picture sizing, decode-ahead, sound 8
  loading_and_deploy.md     deferral, hydration, headers, the CDN, PageGate   12 (+ the carriage case)
  performance_method.md     subtract, census, gate, measure the attractive answer 12
  realtime_and_sync.md      the history line, backlog batching, caches over a log, the client halves
                            of the multiplayer findings                        4 from the log + the audit
  testing.md                the walk (outline in the client assessment)       7
  stage_motion.md           the stage's motion policy, the beat cutter        3 (+ stage_architecture §6)
  css_layout.md             six layout and stacking facts                     6
frontend/docs/phone_lessons.md   stays: the dated phone case study, linking the topics
frontend/docs/frontend_lessons.md  stays: the log
```

Each topic document is a tutorial, not a log (owner 2026-10-26: phone_lessons' symptom, mechanism,
fix shape explains one incident and teaches nothing that transfers). The form:

1. What this teaches, and what you need first (one line, linking the docs it builds on).
2. One section per concept: the mechanism in plain words; then "in this project", the cases as worked
   examples with the lesson number, the code symbol and the number with its N; then "see it yourself";
   then the rule.
3. A case index at the end, lesson number to section, so the log maps onto the tutorial.
4. "If you are asked about it": the one-minute answer.
5. Reading.

Two rules keep the tutorials short and defensible. **The cases set the syllabus:** a doc teaches only
the concepts its cases need, to the depth at which the case becomes obvious; a concept with no case
from this project goes to the reading list. **Prerequisites are explicit:** react_identity and
rendering_pipeline are the foundations; memory_and_pictures, loading_and_deploy and stage_motion build
on rendering; performance_method builds on all of those; realtime_and_sync stands alone; testing last.
Four over-claims the 2026-10-11 audit named recur in the lessons and are stated as observed
conditions and intended policy, never as guarantees: a cache that reuses across instances (lessons 12
and 36, told as one), a remount meaning a re-decode (lesson 13, build_log §8.8), the box alone being
repainted (lesson 8), a steady 24 frames a second (lesson 14). Where a "see it yourself" step has no
committed script (the render census of lesson 33, the day-4 walk of §8.10), the doc says so.

### 3.2 The playbook

`frontend/docs/playbook.md`: thirteen methods, the owner's working rules placed under the method each
belongs to. Table of contents with exemplars: [`playbook_toc.md`](playbook_toc.md); the working rules
with their reasons: [`playbook_working_rules.md`](playbook_working_rules.md). The owner reads the rules
once and strikes any no longer held.

### 3.3 New and lifted documents

| Document | Type | From |
|---|---|---|
| `client_design.md` (D1) | design record | build_plan §4, §5; build_log §2, §3, §4; stage_architecture §2, §8; ux_journeys §0, D22, D23; beat_sheet §11 to §13; the code (`foldEvents`, `store`, `useGameStream`, `catch-up-boundary`, `live-state`, `lib/storage`) |
| `deploy_log.md` (D3) | journey log | build_plan §7's deploy record, whole |
| `learning/*.md` (D2) | lesson docs | the placement table |
| `learning/testing.md` | lesson doc | `testing.md` (corrected), build_log §6, the goldens, `e2e/live.spec.ts` head, the audits' test critiques |
| `playbook.md` | method | the table of contents |
| `server_encountered_challenges.md` §8 (D4) | journey entry | the talking points' failure story, `translate.py`'s docstring, the cached-drop test |

No folder regrouping. The README carries the hierarchy; the four server documents stay in
`frontend/docs/` because chapter C reads them beside the client's. Moves: the deploy record only.

### 3.4 One detailed home per finding

| Ruling or finding | Home | The others summarise and link |
|---|---|---|
| The fault model, five modes | `seat_continuity.md` §1 | design notes §5c (dated text), talking points |
| AFK clocks, delegate or park, the solo suspension, gone after two turns | `seat_continuity.md` §4, §5, new §5b | design notes §7, transport §6d, multiplayer finding 5, talking points, HANDOFF §4.1 |
| Retention and the sweeper | `seat_continuity.md` §7 | design notes §8, transport §4 (M2 note) |
| Reconnect cursors and suffix replay | transport §7 | design notes §6 (dated originals), build_plan §5 |
| Seat identity, the cookie path, the reclaim door | transport §6b | seat_continuity §2, challenges §7, multiplayer 11, build_log §3.1, §3.11 |
| Rooms: not persisted, TTL, leave, close | design notes §12 | transport §6c, seat_continuity §7 |
| BYOK restart, the catalogue, the backup key | design notes §13 (with a 2026-10-21 amendment) | design notes §6 (four-line card) |
| Stall rescue and the request budget | `docs/agentic_ai_encountered_issues.md` §1 | design notes §6 (pointer) |
| Coupling alarms as built | `server/README.md` "When the engine changes" | transport §8 (policy) |
| Phase markers and `turn_started` placement | `event_derivation.md`; design notes §4 | transport §5, §8, §9 (dated notes) |
| The events table leads the checkpoint | challenges §8 (new) | talking points |
| Live against history; the client never gates | ux_journeys §0 (ruling); `client_design.md` (mechanism) | build_log §3.2, §4.1 to §4.3, ux_baseline §4, stage_architecture §2 |
| One fold for replay, live and the reveal | `client_design.md` | build_plan §4, build_log §4.1, stage_architecture §2 |
| The persistence inventory | `lib/storage.ts`, mirrored once in `client_design.md` | build_plan §5 |
| The draft helper | ux_journeys D25 | build_plan §5, §8 |
| The night bar's total (a side channel closed) | ten_seat_pass §10 to §11 | transport §6's side-channel list |
| The jump | live_timing_sheet ruling 3 | multiplayer 10, beat_sheet §12 |
| The phone numbers (534 MB to 114; the raster tables) | build_log §8 | phone_lessons, frontend_lessons 10, 17 |
| The lighting cache key | lesson 36 (the fix) | lesson 12 (dated note), build_log §8.10 |
| Catch-up batching | lesson 32 (rule); the 2026-10-15 follow-up (measurement) | build_log §8.10 |
| The Cloudflare header | build_log §1.4 (the story); lesson 31 (header scope) | §1.4 gets a dated note: route-scoped since 2026-10-15, mechanism unproven |
| Fonts | `typography.md` | stage_architecture §5 (links), §3 (stale, to point at §5) |
| The product name and mark | pages_review F2 | site_architecture |
| The costume rule | cast_expansion_brief, with its reason in the playbook | role_cards_brief intro |

---

## 4. Work list

Size: **S** = status line, a card, or a few sentences; **M** = several passages or a section index;
**L** = a new document.

### Fix regardless of the rest (one small commit, first)

Status lines and sentences that state something false today.

| Where | Problem | Fix |
|---|---|---|
| `typography.md` head | "built, not yet deployed" | the deploy date (owner confirms) |
| `role_cards_brief.md`, `night_rooms_brief.md` heads | "DRAFT" after shipping 2026-10-07 | "Shipped 2026-10-07"; the card text's truth is `src/stage/card-text.ts` |
| `ten_seat_pass.md` §8, §9 | "uncommitted" | deployed 2026-10-11 at `74d8206b`; §6's draw gap closed 2026-10-17 |
| `frontend_lessons.md` 39 | "Not deployed yet" | the deploy state and date |
| `testing.md` | "5 spec files, 173 tests", "people and CI alike" | drop the counts; "this project has no CI" |
| `phone_lessons.md` 10; `frontend-audit` follow-up | the gate holds "without anyone remembering"; "hard CI gates" | a clause: it runs only when someone runs it |
| `frontend-audit` follow-up | the half-open stream "Open" | fixed the same day, multiplayer finding 7 |
| `live_timing_sheet.md` head note; `stage_fit/README.md` | stage_fit "measured the lag again" / "replaces the one earlier measurement" | it measured the waits; the lag rows are still the one flash-lite game's; 5.5 s to 5.4 s |
| `event_derivation.md` pacing channel, "Derived (night)" | the night denominator as the role census | one padded unit per living seat (its own 2026-10-11 ruling) |
| `design_log.md`, `ux_baseline.md`, `HANDOFF.md`, `music_brief.md`, `scorecards_plan.md`, `landing_features.md`, `opening_round_brief.md`, `landing-handoff`, `multiplayer-audit`, `rendering-audit`, `site_architecture.md`, `pages_review.md` | no status line, or one that reads as current | one dated status line each (the wording is in the assessments); ux_baseline and the rendering audit get the four-line card |
| `interview_prep/server_talking_points.md` | the "walks away" answer omits the October rulings; the credit date; "how much did you write" | three answers rewritten to the facts, the last to: the owner wrote the event schema and co-wrote the beat sheet, the rest was AI-built to those specs and reviewed |

### Server (chapter C's spine)

| Document | Size | Action |
|---|---|---|
| `server_client_transport.md` | M | Status line ("ruled 2026-07-28; built August; sections added to 2026-10-17; dated notes mark where the build departed"). Ten dated notes, listed in the server assessment: routes, no event bus, M2 never built, 33 event types not 12, NIGHT_START replaced the DAY_RESOLUTION rule, the real tier tests in place of the named leak test, the cookie path and the rejoin trigger, the room TTL now closes rooms, the alarms as built, `turn_started` from the edge and the union's OpenAPI route. Keep every mechanism as ruled |
| `server_design_notes.md` | M | Status line; the thirteen-row section index (drafted in the assessment); the four-line card on §6's BYOK packet; dated notes on §3, §5c, §6 (catalogue, stalls to a pointer), §10, §13 (Haiku default; a 2026-10-21 amendment for the backup key and the database catalogue) |
| `seat_continuity.md` | M | Status line; §4 gains the gone rule and the draft cap; new §5b "A solo table suspends" (2026-10-11, with its reason: a human killed during a two-minute phone sleep); §7's table gains the suspended row and the corrected room row; §10 lists the October sources (D4) |
| `server_encountered_challenges.md` | M | A date per entry; "LangGraph 1.1.10" on §1, §3, §4; new §8, the events table leads the checkpoint, in the same form (D4) |
| `event_derivation.md` | S | The two pacing passages (on the fix list) |
| `multiplayer-audit-2026-10-15.md` | S | Status line naming the deploy |
| `server/README.md` | S | Layout table: six modules and four tables; drop the test count; the cron sentence |
| `docs/agentic_ai_encountered_issues.md` | S | Dated status on entry 3 (the sheet written, the turn jump built, the general jump not); the N on the 11 s figure |

### Client

| Document | Size | Action |
|---|---|---|
| `client_design.md` | L | **Pilot.** D1. Design record in the transport record's form; the glossary first; eight parts per the client assessment's passage list; the server half linked, never restated |
| `build_plan.md` | M | As-built status block under the title; deploy record lifted to `deploy_log.md` (D3, own commit); dated notes on §3 (codegen, routes), §4 (plane 3, the view sketch), §5 (stream error handling, the persistence table, the draft), §8 (memory, draft rows), §9 (superseded by `testing.md`) |
| `build_log.md` §0 to §7 | S | The section index at the head (drafted in the assessment); dated notes on §3.11 and §6 "Standing gap"; §7 item 5; a line that its "I" is the AI builder |
| `stage_architecture.md` §8, §9, §11 | S | §8 one line each for the state, queue, transport, cache and warm-reel files; §9 seat row dated; §11 "done 2026-09-25" |
| `ux_journeys.md` | S | Status line naming what is living and what the stage replaced; fix the two §0 cross-references; §8 dated |
| `testing.md` | M | The fix-list items, plus "What the goldens pin" and the live spec's entitlement blind spot under "What none of this covers". Then it seeds `learning/testing.md` |
| `design_log.md` | S | Status line and the section index (drafted in the assessment); note that §8's reason now rests on the echo gate, the novelty gate being gone |
| `site_architecture.md` | S | Status line; a pointer to "The cast record" (D8) |

### Lessons and audits

| Document | Size | Action |
|---|---|---|
| `learning/react_identity.md` | L | **Pilot.** D2. The tutorial form on the richest topic: six concepts (identity is position plus key; render versus commit; re-render versus remount; memo and referential equality; effects and their dependencies; where state lives) and twelve cases (the set-and-beat split, the countdown leaf, the lighting cache key told as 12 with 36) |
| the other eight topic docs | L | After the pilot, from the placement table and source lists |
| `learning/README.md` (from `principles.md`) | M | The index: one section per topic, the principle lines and "Read" lists kept, the principles for lessons 38 to 49 added, "the October audit" and "the survey" resolved (the "a tenth too big" figure sourced or removed) |
| `frontend_lessons.md` | S | 29a and 29b labelled; S1 to S23 numbered; dated notes on 12, 14, 39; the head pointer corrected (the numbers for 32 to 37 are in the 2026-10-15 follow-up); lesson 23's reference |
| `phone_lessons.md` | M | The mask crash (build_log §8.1) added as the first crash; lesson 2 and the closing paragraph corrected; "eleven" to twelve; lessons 5, 10, 11, 12 qualified as the assessment names |
| `build_log.md` §8 | S | The section index; dated notes on §8.2 (motion is script, not compositor), §8.6 (CDP counts layers), §8.8 (the re-decode caveat), §8.10 (three of five "next" items done); the §8.3 placeholder replaced |
| `live_timing_sheet.md` | S | The head note (fix list); dated notes on extraction (offline since 2026-10-12, three places) and the §4 solo row |
| `stage_fit/README.md` | S | Two sentences (fix list). Optional M: report the simulated lag at each human prompt from the same run, which would make "the lag is bounded by the stretch between human turns" a measured claim on 13 games |
| the two frontend audits | S | Status lines (fix list) |

### Design and art

| Document | Size | Action |
|---|---|---|
| `playbook.md` | M | From the table of contents and the working rules; the owner strikes rules no longer held |
| `HANDOFF.md` | S | Status line; §11 says where the bundle went (`frontend/claude_artifacts/design/`, not in git; `README.md` is `BUNDLE_README.md`) |
| `cast_expansion_brief.md` | S | Section index at the head; status line; "Process" headed as the first method the template replaced |
| `stage_architecture.md` §3, §4 | S | §3 "The HUD's look" points at §5 instead of naming Young Serif; §4's location list gains the six rooms and four characters |
| `beat_sheet.md` head, §15 | S | The second golden game named; §15's two items closed with pointers (F7; the rejoin door, once area A's reading is confirmed) |
| the remaining briefs | S | Status lines (fix list); `opening_round_brief.md` deleted (D6) |

---

## 5. Order

1. **The fix list**, one commit: wrong status lines and false sentences across the folder.
2. **The two pilots** (D9): `client_design.md` and `learning/react_identity.md`. You read both; the
   two forms are adjusted before the rest is commissioned.
3. **The server's dated notes and `seat_continuity.md`** (D4), because chapter C's spine reads them
   first. Then the talking points.
4. **The remaining topic documents and the learning index.** Headless drafting in parallel, one topic
   per agent, from the placement table; I check each mechanism claim against the code and each
   over-claim against the audit's list; you read the pilots' siblings only where a topic is new to you.
5. **The deploy record lifted** (D3), its own commit, links updated.
6. **The client's and the design area's dated notes and indexes**, one commit per area.
7. **The playbook**, after the rules have been read and struck.
8. **Close-out:** the README's status column updated row by row; `frontend/docs/learning/` and
   `playbook.md` added to it; chapter C's content plan opened from the story spine, the way the
   evaluation chapter's was.
