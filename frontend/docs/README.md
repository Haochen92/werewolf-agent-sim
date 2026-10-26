# frontend/docs: the index

The record of how the server and the browser were designed, built and debugged: 42 files, about
170,000 words, 2026-06-06 to 2026-10-24. Indexed 2026-10-26 by the frontend docs pass
(`writeup/frontend_pass/`); the proposed edits are in its `proposal.md` and are not applied yet.

**Where the truth lives.** For what the stage shows: `beat_sheet.md`, pinned by goldens. For how the
stage is built: `stage_architecture.md`. For what each graph node sends and to whom:
`event_derivation.md`, pinned by the translator goldens. For the faces: `typography.md`. Where any
other document disagrees with these four, or with the code, the four and the code win.

**The five kinds.** A *living spec* is mirrored by code or goldens. A *design record* holds a decision
with its reasons, alternatives and trade-offs. A *journey log* is dated and chronological and is never
rewritten. A *lesson doc* generalises for the owner. A *dated brief or audit* is a record of one day.

**The chapter C stories** the "Feeds" column refers to (the fullstack chapter of the portfolio):

1. Streaming an agent system to a browser: the event log the client folds; events, not tokens.
2. Human turns inside a running LangGraph graph: Futures, interrupts, the cached twins, the tally.
3. The information boundary on the wire: four tiers, whole-event filtering, the side channels.
4. Reconnection and state synchronisation: replay the log, the history line, membership dedupe.
5. Failure handling as a layered fault model: client, game, process; presence, park, sweeper.
6. Contract-first with alarms on silent couplings; goldens that pin the spec.
7. Latency as tempo: the stage reads slower than agents speak; read or jump, never hurry.
8. Identity without accounts: the seat cookie, two copies, the reclaim door.
9. A public AI demo that is not bankrupted or abused: the cap, the switch, BYOK, the draft cap.
10. The live view had to survive a phone (optional Level 3 page).

"Learning" names a topic of the planned `learning/` hierarchy; "playbook" names a section of the
planned `playbook.md` (both in the proposal).

## Living specs

| Document | Status (2026-10-26) | Reader question | Feeds |
|---|---|---|---|
| `beat_sheet.md` | Living; the source of truth, beat by beat. Head names one golden game; there are two | What does the stage show at each event, for each viewer, for how long? | 3 (§10, §13), 4 and 7 (§12), 6 (head); playbook 1 |
| `stage_architecture.md` | Living, ruled 2026-09-25, sections dated to 2026-10-19. §3 still names a retired font; §9's seat row and §11's work order are dated | How is the stage built in code: the axes, the box, the assets, the motion, the workbench, the music? | 1, 3, 4 (§2); 10 (§6); playbook 1, 4, 5, 7; learning stage_motion, rendering_pipeline |
| `event_derivation.md` | Living; the translator's companion by node name. Two pacing passages contradict their own 2026-10-11 ruling | What does each graph node send, and to whom? | 1, 3, 6 |
| `site_architecture.md` | Living, current to 2026-10-18 | How are the site pages built: routes, tokens, fonts, the controls kit, pages that come up whole? | playbook (controls kit); learning loading_and_deploy |
| `typography.md` | Living, ruled 2026-10-16 on a mock with a switch per change. Header says "not yet deployed"; the owner's records say deployed | Which face sets which text, and how does a builder decide? | playbook 5 |
| `ux_journeys.md` | §0 binding and current; D23 and D25 current as built; D1 to D7 moved to site_architecture; D8 to D22 describe the v1 theatre replaced 2026-09-25 | For every route and game state, what does each viewer see? | 1, 3, 4 (§0, D21 to D23); learning realtime_and_sync |
| `testing.md` | Living how-to for the owner; counts stale (8 specs, 73 unit files); silent on the beat goldens and the live spec's blind spot | What does each kind of frontend test check, how is a run done, what can none of them see? | 6; learning testing; playbook 11 |
| `../../server/README.md` | Living map of `server/`; layout table misses six modules; test count stale | Where is each part of the server, and which record explains it? | 6 (the coupling table); playbook 9 |

## Design records

| Document | Status | Reader question | Feeds |
|---|---|---|---|
| `server_client_transport.md` | Ruled 2026-07-28, built August, sections added to 2026-10-17; status line still says "not yet built"; ten passages describe the July plan where the build departed | How does a LangGraph game reach a browser, who may see what, how does a client stay in step? | 1, 3, 4, 6, 8 (the spine's main source); 2 (§8b) |
| `server_design_notes.md` | Thirteen dated rulings, 2026-08-08 to 2026-09-12; one (§6 BYOK restart packet) reversed by §13 without a pointer | Why is the server shaped as it is, ruling by ruling? | 2, 5, 9; learning (the owner's code walks, §10 to §12) |
| `seat_continuity.md` | Ruled 2026-09-09, built, amended to 2026-09-17; the two October absence rulings (solo suspension 2026-10-11, gone after two turns 2026-10-15) are not in it | When a human seat goes silent, what does the system do at each layer, and why? | 5 (the spine), 4, 8 |
| `live_timing_sheet.md` | Rulings 2026-10-01, living; measurements are one flash-lite game's; head note mis-states what stage_fit replaced; extraction rows stale since 2026-10-12 | When does the server emit each event, what does each viewer's stage do with it, how far behind does it run? | 7 (the spine), 4 (ruling 6); learning realtime_and_sync |
| `stage_fit/README.md` + `results.json` | Measured 2026-10-24 on 13 served games; rerunnable (`evaluation/experiments/stage_fit.py`) | Does the model keep ahead of the stage, and where does the stage wait? | 7 (the measured figures) |
| `build_plan.md` §4, §5 | The client's design rulings (state model, wire integration), 2026-08-20; four passages stale (URL scrub state, the view sketch, stream error handling, persistence keys) | What holds the browser's state, and how does it talk to the server? | 1, 3, 4, 6, 8, 9 |
| `build_plan.md` (the rest) | The plan, ruled 2026-08-20, P0 to P3 built by 2026-08-21; the deploy record lifted to `deploy_log.md` on 2026-10-26; §8, §9 superseded | How was the build phased? | playbook 6; learning loading_and_deploy |

## Journey logs

| Document | Status | Reader question | Feeds |
|---|---|---|---|
| [`deploy_log.md`](deploy_log.md) | 72 dated deploys, 2026-08-21 to 2026-10-22, lifted whole from `build_plan.md` §7 on 2026-10-26; appended to | What was deployed when, how was it checked, and how is a deploy done here? | playbook 11; learning loading_and_deploy |
| `build_log.md` §0 to §7 | 2026-08-21, amended 2026-09-27 and 2026-10-12; by kind of problem, not date; the "I" is the AI builder | Where did reality disagree with the specs while the client was built, and what did it cost? | 1, 3, 4, 6, 8; learning realtime_and_sync, testing; playbook 12 |
| `build_log.md` §8 | 2026-10-01 to 10-02, the stage on a phone; the home of the numbers (534 MB of layers to 114); four later-overturned claims lack dated notes | What happened, in what order, with what numbers, when the stage met an iPhone? | 10 (primary); five learning topics |
| `server_encountered_challenges.md` | Seven debugging records, 2026-08-19 and 2026-08-24, undated per entry; all checked current | What broke while making the server host real humans, and what was it? | 2 (§1 to §5), 5, 8 (§7); learning (server-side lessons); playbook 10 |
| `design_log.md` | The June 2026 paper design; status line "nothing implemented" is false now | What was the frontend meant to be before any of it was built? | 1 (§8), 9 (§10) |
| `ten_seat_pass.md` | 2026-10-10 to 10-16; deployed 2026-10-11; §8 and §9 still say "uncommitted" | What did the frontend change for the ten-seat cast, and what was ruled? | 3 (§1, §10 to §11), 6; playbook 6 |
| `cast_expansion_brief.md` (the rounds) | Shipped 2026-10-03; the template at the head supersedes the "Process" below it; "The cast record" at the end is a server and site design record with no other home | How were four puppets designed to the house style, and how does a game remember its cast? | playbook 2 |
| `../../docs/agentic_ai_encountered_issues.md` | 2026-10-01, updated 2026-10-22; entry 3 still "OPEN" though the timing sheet and the turn jump followed | What went wrong with the models while people played? | 7, 5 |

## Lesson docs

| Document | Status | Reader question | Feeds |
|---|---|---|---|
| `frontend_lessons.md` | The log of lessons: 50 numbered (29 used twice) plus 23 small things, 2026-10-02 to 10-22; living | What general frontend rule did each mistake teach, and where in the code can I see it? | every learning topic; 10 |
| `phone_lessons.md` | Twelve lessons (head says eleven), 2026-10-01 to 10-02; the walk form the topic docs adopt; the first crash is told wrong | Why did the stage die on an iPhone, what was the browser doing, how do I see it myself? | 10; learning rendering_pipeline, memory_and_pictures, performance_method |
| [`learning/README.md`](learning/README.md) | The learning index, from `principles.md` (2026-10-15) on 2026-10-26: one section per tutorial, every lesson placed, reading lists kept | What general rules did this project teach, by topic, and what should I read? | the learning track |
| [`playbook/playbook.md`](playbook/playbook.md) | Draft 2026-10-26, awaiting the owner's review of its working rules: the end-to-end workflow in eight stages, what was done here and the (next time) steps a team would add | How was this built with AI tools, and how would I do it again? | the interview's process answer; the next project |

## Dated audits

| Document | Status | Reader question | Feeds |
|---|---|---|---|
| `multiplayer-audit-2026-10-15.md` | Executed; eight fixes with commits and tests; three accepted or left | What can go wrong when several friends play one game? | 3, 4, 5, 7, 8, 9; learning realtime_and_sync; playbook 8 |
| `frontend-audit-2026-10-11.md` + `-evidence.json` | Audit 2026-10-11 with a follow-up 2026-10-15; items 1, 3, 5 done, 2, 4, 6 partly; the dead-stream item was fixed the same day | Is the stack viable and the frontend ownable, and what are the prioritised improvements? | 10; 1 and 4 (client side); six learning topics |
| `rendering-audit-2026-10-02.md` | Superseded the same day by build_log §8.9 and §8.10 | What does the stage's rendering cost in a controlled browser? | 10; learning performance_method; playbook 8 |
| `design_2026-09-26/pages_review.md` | Executed 2026-09-26 to 09-29; §F holds the site's rulings (the product name among them) | Can five mockups be built on the code and server as they stand, and what did the owner rule? | playbook 3, 6, 13 |

## Dated briefs and design

| Document | Status | Reader question | Feeds |
|---|---|---|---|
| `design_2026-09-25/HANDOFF.md` | The design chat's decisions, 2026-09-25, amended 2026-09-29; superseded as the spec by the beat sheet and stage_architecture; §6's pacing is the before-picture of story 7 | What did the design chat agree for the live game and the replay, and why? | playbook 1 |
| `design_2026-09-25/BUNDLE_README.md`, `landing-handoff-2026-09-22.md` | Superseded; the benches they describe live in `frontend/claude_artifacts/design/`, not in git | How were the benches opened and handed on? | playbook 1, 7 |
| `design_2026-09-25/kits/*.js`, `sprites-manifest.json` | Frozen copies from the benches; the manifest describes the sprite set replaced 2026-09-28 | — | — |
| `design_2026-09-28/landing_features.md` | Built 2026-09-28; "why this wording" predates the Postgres store (2026-10-14), the copy did not need to change | What do the landing's feature cards say, and why that wording? | playbook 13 |
| `design_2026-09-28/scorecards_plan.md` | Not built (checked 2026-10-26) | How would every seat get a score and the site publish per-role results? | playbook 13 (the parity test) |
| `role_cards_brief.md` | Shipped 2026-10-07; header still says DRAFT; the card text's truth is `src/stage/card-text.ts` | How were the eight role figures specified, generated and shipped? | playbook 2, 6 |
| `night_rooms_brief.md` | Shipped 2026-10-07; header still says DRAFT | How were six night rooms painted to differ in shape but keep every measure the code relies on? | playbook 2 |
| `music_brief.md` | Written 2026-10-15; the four stings and the morning loop delivered, the two optional pieces not; no status line | What music was missing, and to what measured standard was it ordered? | playbook 2 |
| `opening_round_brief.md` | 2026-10-11, not built; the stage shows the placard of beat sheet §2 row 7 (owner 2026-10-15); dropped or deferred is unruled | What single painting would replace the opening round's notice? | playbook 7 (acceptance as workbench views) |
| `ux_baseline.md` | Superseded: the theatre 2026-09-25, the type 2026-10-16, the site pages by site_architecture; two cross-page rules survive (§4) | What did v1 of the app look like and promise? | 1, 3 (§4) |

## Outside the folder, part of the same record

| Document | What it is | Feeds |
|---|---|---|
| `../../writeup/server_talking_points.md` | The server as the owner would tell it in an interview, 2026-09-13; three answers need the October rulings and the authorship wording | 2, 3, 4, 5, 6, 9 |
| `../../evidence/gameplay/` | The gameplay record the ten-seat pass and the role sheet rest on | — |
