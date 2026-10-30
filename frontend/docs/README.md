# frontend/docs: the index

The record of how the server and the browser were designed, built and debugged, 2026-06-06 to
2026-10-24. Indexed and brought up to date on 2026-10-26 by the frontend docs pass
(`frontend/docs/frontend_pass/`): status lines and dated notes where a document no longer matched the code,
the browser's design record, the deploy log, nine learning tutorials and the playbook. The status
column below is as of that day.

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

"Learning" names a tutorial in [`learning/`](learning/README.md); "playbook §N" names a stage of
[`playbook/playbook.md`](playbook/playbook.md).

## Living specs

| Document | Status (2026-10-26) | Reader question | Feeds |
|---|---|---|---|
| `beat_sheet.md` | Living; the source of truth, beat by beat; both golden games named | What does the stage show at each event, for each viewer, for how long? | 3 (§10, §13), 4 and 7 (§12), 6 (head); playbook §4 |
| `stage_architecture.md` | Living, ruled 2026-09-25, sections dated to 2026-10-19; dated notes on §3, §4, §8, §9 and §11 | How is the stage built in code: the axes, the box, the assets, the motion, the workbench, the music? | 1, 3, 4 (§2); 10 (§6); playbook §2, §4, §5, §6; learning stage_motion, rendering_pipeline |
| `event_derivation.md` | Living; the translator's companion by node name; the pacing passages follow their 2026-10-11 ruling | What does each graph node send, and to whom? | 1, 3, 6 |
| `site_architecture.md` | Living, current to 2026-10-18; points to the cast record | How are the site pages built: routes, tokens, fonts, the controls kit, pages that come up whole? | playbook §5; learning loading_and_deploy |
| `typography.md` | Living, ruled 2026-10-16 on a mock with a switch per change; deployed 2026-10-16 (`87499f98`) | Which face sets which text, and how does a builder decide? | playbook §2 |
| `ux_journeys.md` | Status line says what is current: §0, D23 and D25; D1 to D7 moved to site_architecture and the platform; D8 to D22 describe the v1 theatre replaced 2026-09-25 | For every route and game state, what does each viewer see? | 1, 3, 4 (§0, D21 to D23); learning realtime_and_sync |
| `testing.md` | Living how-to for the owner; says what the goldens pin, what none of the suites covers, and that there is no CI | What does each kind of frontend test check, how is a run done, what can none of them see? | 6; learning testing; playbook §7 |
| `../../server/README.md` | Living map of `server/`, current; notes the leak-audit cron is not installed | Where is each part of the server, and which record explains it? | 6 (the coupling table); playbook §4 |

## Design records

| Document | Status | Reader question | Feeds |
|---|---|---|---|
| [`client_design/client_design.md`](client_design/client_design.md) | Written 2026-10-26 from the code at HEAD, with seven figures; the browser's half of the transport record | What does the page do with the events it receives: the fold, catch-up, what it may show, who it is? | 1, 3, 4, 6, 8; learning realtime_and_sync |
| `server_client_transport.md` | Ruled 2026-07-28, built August, sections added to 2026-10-17; every mechanism kept as ruled, with dated notes where the build departed | How does a LangGraph game reach a browser, who may see what, how does a client stay in step? | 1, 3, 4, 6, 8 (the spine's main source); 2 (§8b) |
| `server_design_notes.md` | Dated rulings, 2026-08-08 to 2026-09-30, with a section index; the reversed BYOK restart packet carries a four-line card | Why is the server shaped as it is, ruling by ruling? | 2, 5, 9; learning (the owner's code walks, §10 to §12) |
| `seat_continuity.md` | Ruled 2026-09-09, amended to 2026-10-15; the one home for absence and recovery, with §5b (a solo table suspends) and the gone-after-two-turns rule | When a human seat goes silent, what does the system do at each layer, and why? | 5 (the spine), 4, 8 |
| `live_timing_sheet.md` | Rulings 2026-10-01, living; measurements are one flash-lite game's; the extraction rows and the solo row dated | When does the server emit each event, what does each viewer's stage do with it, how far behind does it run? | 7 (the spine), 4 (ruling 6); learning realtime_and_sync |
| `stage_fit/README.md` + `results.json` | Measured 2026-10-24 on 13 served games; rerunnable (`evaluation/experiments/stage_fit.py`) | Does the model keep ahead of the stage, and where does the stage wait? | 7 (the measured figures) |
| `build_plan.md` §4, §5 | The client's design rulings, 2026-08-20; dated notes where the build departed; the account as built is `client_design` | What holds the browser's state, and how does it talk to the server? | 1, 3, 4, 6, 8, 9 |
| `build_plan.md` (the rest) | The plan, ruled 2026-08-20, with an as-built status block; the deploy record lifted to `deploy_log.md`; §9 superseded by `testing.md` | How was the build phased? | playbook §1; learning loading_and_deploy |

## Journey logs

| Document | Status | Reader question | Feeds |
|---|---|---|---|
| [`deploy_log.md`](deploy_log.md) | 72 dated deploys, 2026-08-21 to 2026-10-22, lifted whole from `build_plan.md` §7 on 2026-10-26; appended to | What was deployed when, how was it checked, and how is a deploy done here? | playbook §7; learning loading_and_deploy |
| `build_log.md` §0 to §7 | 2026-08-21, amended 2026-09-27 and 2026-10-12; by kind of problem, with a section index; the "I" is the AI builder | Where did reality disagree with the specs while the client was built, and what did it cost? | 1, 3, 4, 6, 8; learning realtime_and_sync, testing; playbook §6 |
| `build_log.md` §8 | 2026-10-01 to 10-02, the stage on a phone; the home of the numbers (534 MB of layers to 114); four later-overturned claims carry dated notes | What happened, in what order, with what numbers, when the stage met an iPhone? | 10 (primary); five learning topics |
| `server_encountered_challenges.md` | Eight debugging records, 2026-08-19 to 2026-09-12, dated per entry; all current | What broke while making the server host real humans, and what was it? | 2 (§1 to §5), 5, 8 (§7); learning (server-side lessons); playbook §8 |
| `design_log.md` | The June 2026 paper design, with an index of what became of each section | What was the frontend meant to be before any of it was built? | 1 (§8), 9 (§10) |
| `ten_seat_pass.md` | 2026-10-10 to 10-16; deployed 2026-10-11 (`74d8206b`) | What did the frontend change for the ten-seat cast, and what was ruled? | 3 (§1, §10 to §11), 6; playbook §1 |
| `cast_expansion_brief.md` (the rounds) | Shipped 2026-10-03; indexed; the template at the head replaced the "Process" below it; "The cast record" at the end is linked from site_architecture | How were four puppets designed to the house style, and how does a game remember its cast? | playbook §3 |
| `../../docs/agentic_ai_encountered_issues.md` | 2026-10-01, updated 2026-10-22; entry 3 partly built (the seat's own-turn jump; the general jump is not) | What went wrong with the models while people played? | 7, 5 |

## Lesson docs

| Document | Status | Reader question | Feeds |
|---|---|---|---|
| `frontend_lessons.md` | The log of lessons: 50 numbered (29a and 29b) plus S1 to S23, 2026-10-02 to 10-22; living; taught by topic in `learning/` | What general frontend rule did each mistake teach, and where in the code can I see it? | every learning topic; 10 |
| `phone_lessons.md` | Twelve lessons, 2026-10-01 to 10-02; the dated case study, with the mask crash told as the first crash | Why did the stage die on an iPhone, what was the browser doing, how do I see it myself? | 10; learning rendering_pipeline, memory_and_pictures, performance_method |
| [`learning/README.md`](learning/README.md) | The learning index, from `principles.md` (2026-10-15) on 2026-10-26: one section per tutorial, every lesson placed, reading lists kept | What general rules did this project teach, by topic, and what should I read? | the learning track |
| `learning/<topic>/` | Nine tutorials, 2026-10-26, each with five or six figures: React identity, the rendering pipeline, pictures and memory, loading and deploys, stage motion, performance method, real time and sync, CSS layout, testing | What is the concept behind each case, and how would I explain it? | every story; 10 |
| [`playbook/playbook.md`](playbook/playbook.md) | Draft 2026-10-26, working rules confirmed by the owner the same day: the end-to-end workflow in eight stages, what was done here and the (next time) steps a team would add | How was this built with AI tools, and how would I do it again? | the interview's process answer; the next project |

## Dated audits

| Document | Status | Reader question | Feeds |
|---|---|---|---|
| `multiplayer-audit-2026-10-15.md` | Executed; eight fixes with commits and tests; three accepted or left | What can go wrong when several friends play one game? | 3, 4, 5, 7, 8, 9; learning realtime_and_sync; playbook §6 |
| `frontend-audit-2026-10-11.md` + `-evidence.json` | Audit 2026-10-11 with a follow-up 2026-10-15; items 1, 3, 5 done, 2, 4, 6 partly; the dead-stream item dated as fixed the same day | Is the stack viable and the frontend ownable, and what are the prioritised improvements? | 10; 1 and 4 (client side); six learning topics |
| `rendering-audit-2026-10-02.md` | Superseded the same day by build_log §8.9 and §8.10; a four-line card at the head | What does the stage's rendering cost in a controlled browser? | 10; learning performance_method; playbook §6 |
| `design_2026-09-26/pages_review.md` | Executed 2026-09-26 to 09-29; §F holds the site's rulings (the product name among them) | Can five mockups be built on the code and server as they stand, and what did the owner rule? | playbook §1, §2, §7 |

## Dated briefs and design

| Document | Status | Reader question | Feeds |
|---|---|---|---|
| `design_2026-09-25/HANDOFF.md` | The design chat's decisions, 2026-09-25, amended 2026-09-29; superseded as the spec by the beat sheet and stage_architecture; §11 says where the bundle went | What did the design chat agree for the live game and the replay, and why? | playbook §4 |
| `design_2026-09-25/BUNDLE_README.md`, `landing-handoff-2026-09-22.md` | Superseded; the benches they describe live in `frontend/claude_artifacts/design/`, not in git | How were the benches opened and handed on? | playbook §4, §5 |
| `design_2026-09-25/kits/*.js`, `sprites-manifest.json` | Frozen copies from the benches; the manifest describes the sprite set replaced 2026-09-28 | — | — |
| `design_2026-09-28/landing_features.md` | Built 2026-09-28; "why this wording" predates the Postgres store (2026-10-14), the copy did not need to change | What do the landing's feature cards say, and why that wording? | playbook §7 |
| `design_2026-09-28/scorecards_plan.md` | Not built (checked 2026-10-26) | How would every seat get a score and the site publish per-role results? | playbook §7 (the parity test) |
| `role_cards_brief.md` | Shipped 2026-10-07; the card text's truth is `src/stage/card-text.ts` | How were the eight role figures specified, generated and shipped? | playbook §1, §3 |
| `night_rooms_brief.md` | Shipped 2026-10-07 | How were six night rooms painted to differ in shape but keep every measure the code relies on? | playbook §3 |
| `music_brief.md` | Written 2026-10-15; the four stings and the morning loop delivered, the two optional pieces not | What music was missing, and to what measured standard was it ordered? | playbook §3 |
| `ux_baseline.md` | Superseded (a four-line card at the head): the theatre 2026-09-25, the type 2026-10-16, the site pages by site_architecture; two cross-page rules survive (§4) | What did v1 of the app look like and promise? | 1, 3 (§4) |

## Outside the folder, part of the same record

| Document | What it is | Feeds |
|---|---|---|
| `../../interview_prep/server_talking_points.md` (private, gitignored) | The server as the owner would tell it in an interview, 2026-09-13; three answers rewritten 2026-10-26 for the October rulings and who wrote what | 2, 3, 4, 5, 6, 9 |
| `../../evidence/gameplay/` | The gameplay record the ten-seat pass and the role sheet rest on | — |
