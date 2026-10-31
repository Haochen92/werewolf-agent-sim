# Chapters 7 and 8: topics and their treatment (working map)

Status: working map for the owner, 2026-10-30, revised the same day after an outside review. Not a
writing plan yet: the editorial choices below are proposals, and the next step is to pilot report B
and see how much concept a self-sufficient report can carry before the rest is settled.

Built from the chapter 7 content plan, the chapter 8 story spine (`frontend/docs/frontend_pass/brief.md`
§5), the frontend docs index and learning index, and a read-only code sweep of twenty production topics.
The sweep read code, not docs; nothing was run. "Support" below says what each row rests on.

## The three treatments

| Treatment | What qualifies | Where it lives | Its reader |
|---|---|---|---|
| **Page** | A skill to demonstrate, with a clear example as evidence | `writeup/<chapter>/` L1, L2, L3 | the hiring reader |
| **Report** | Concept and problem → this project's design or incident → implementation and supporting records → what the checks establish → limits and open questions. **Every claim needs identifiable support**: code for implementation, incident or deploy records for what happened, tests or experiments for what was checked | `evidence/production/` (ch 7, proposed); `frontend/docs/` design records already serve ch 8 | the owner, to go deeper than the page |
| **Lesson** | The larger concept the project shows one segment of, written **only when a named learning gap** makes the report's own concept section insufficient | `interview_prep/lessons/` (ch 7); `frontend/docs/learning/` (ch 8, nine exist) | the owner |

Revision note. The first draft's rule was the owner's "a report must be supported by implementation in
code". The review proposed widening it to "claims need identifiable supporting evidence", because code
shows that something is implemented but cannot show that an incident happened or a deploy succeeded, and
a procedural record (the deploy log) is evidence too. The wider rule is used below; **the owner should
confirm the change.**

Lessons are conditional extensions of reports, not scheduled by default. A report's concept section comes
first; a lesson is split out only when the concept needs more than the report can hold or serves several
reports. Outside material (other patterns, other systems) is an optional direction, included when it
resolves the owner's understanding or enables a useful comparison, never a prerequisite.

**Support codes:** `code` = inspected in the sweep · `test` = a test named, **not run** · `incident` =
an incident record (deploy log, agentic-issues log, challenges) · `experiment` = a measured record ·
`docs` = design notes only · `open` = unresolved.

---

## Chapter 7: Running it in production

Page column: the L1 section (S = serving, D = dependency failures, R = records, K = keys and input) and
the L2 page. Page placements are the content plan's as it stands; where this map proposes a change it
says "proposal".

| # | Topic (the general concept) | This project's instance | Code anchor | Support | Page | Report | Lesson |
|---|---|---|---|---|---|---|---|
| 1 | Deadlines and attempts on remote calls; a hang is not an error | 30 s and 2 attempts per model call, 90 s for the day summary; timeout, 408/429/5xx and marker strings count as a stall | `Agents/llm_factory/accessors.py::_request_budget`, `chat.py::_request_limits`, `embeddings.py::is_transient_provider_error` | code; incident (agentic log §1, deploy log 2026-10-01, 10-21). The Mistral client has no limit, but no catalogue, server or eval config names a `mistral/` model (checked 2026-10-30), so no hosted game can reach it; the budget claim is scoped to the catalogue's providers | L1 D lead; L2 B | **B** | concept section of B; extension only if named |
| 2 | Fallback to another provider; circuit breaker | A stall goes once to the catalogue's rescue; after 2 stalls in a row turns start on the rescue for 300 s. House default Haiku has no rescue, so the breaker does nothing there | `health.py::ModelHealth`, `agent_player.py::run_agent`, `catalog.py::SEED_MODELS` | code; test (stall path tests named in the plan, not run); stall rate since the fix unmeasured | L1 D; L2 B | **B** | as row 1 |
| 3 | Degrade to a safe default action | A failed turn becomes a pass, a random legal target, or the role's no-action word | `agent_player.py::run_agent` tail | code | one clause on L2 B; mechanism is ch 1 page 4 | B, one paragraph | as row 1 |
| 4 | An optional dependency fails on its own; derived data is bound to what derived it | Published index carries the embedder's signature; a memory game is refused (409) when the store is unready; memory-off games never search | `persistence/postgres.py::publish`, `::unready_reason`, `routes/_shared.py::require_memory_available`, `plan_gating.py::retrieval_plan` | code; incident (deploy log 2026-10-14, commit `923fc968`); checked with one memory-on game | L1 D second case; L2 B | **B** | as row 1 |
| 5 | A second credential for a second provider | **Correction to the plan:** the backup key is the *player's* key for a second company, sent with their main key; that company's model becomes the rescue. No house backup key | `chat.py::GameLLM.backup_key`, `routes/_shared.py::resolve_backup`, `model_catalog.py::backup_model` | code; incident (deploy log 2026-10-21) | proposal: notes only | E, one paragraph | none |
| 6 | Blocking work under an async server; bounded concurrency; capacity needs evidence | The synchronous engine runs under `astream` as a task; nodes run on the loop's default executor, a 64-thread pool; other blocking work via `to_thread`. 64 was reasoned from one observed wait; no load test | `server/app.py::lifespan`, `game_session.py::_drive_graph` | code; incident (deploy log 2026-10-17, the late wolf prompt); parity check 0.51 s (docs, block 111) | L1 S; L2 A | **A** | concept section of A; extension only if named |
| 7 | Checkpointing and restart recovery: what is persisted, where execution resumes, what runs twice | On boot every running row is rebuilt from three records (games row, events table, LangGraph checkpoint); pending interrupts re-parked; a key-funded game waits for its key | `housekeeping/recovery.py::recover_registry`, `live_game_registry.py::revive`, `::_resume_from_checkpoint`, `AsyncPostgresSaver` | code; test (`tests/server/test_durability.py`, named, not run); no recorded restart drill | L1 S; L2 A | **A**, opened by a concept section (what a checkpoint keeps, why a step re-runs) | extension of A if the concept section strains |
| 8 | Event log ahead of the checkpoint; at-least-once; idempotent re-runs; why no blanket dedup | Three separate claims, each with its own support: (a) cached chunks re-emitted on resume produce no events; (b) the events table can lead the checkpoint by up to one step; (c) a blanket dedup would swallow two event types that legitimately repeat | (a) `translate.py::is_cached`, `::restore_cached_inputs`; (b) none (LangGraph's loop); (c) `translate.py` event types | (a) test (`test_translator.py::test_every_real_chunk_re_delivered_as_cached_sends_nothing`, named, not run); (b) **docs only**: read from the framework's loop, `server_encountered_challenges.md` §8, no test; (c) docs. The test supports (a) only; restart safety in general needs (b) and the durability tests | one sentence on L2 A; proposal: no L3 | A, one section with the three claims kept apart | as row 7 |
| 9 | Timeouts for a human in the loop; park and expire | 120 s connected, 30 s disconnected, only with more than one human; the seat's AI plays or the game parks; gone after 2 turns; sweeper at 1 h solo, 24 h table | `seat_clocks.py`, `game_session.py::_wait_for_absent_player`, `housekeeping/sweeper.py` | code; docs (`seat_continuity.md`); multiplayer audit finding 5 | L2 A subsection (ch 8 story 5 shares) | A, one section | none |
| 10 | Pausing a graph for a human; interrupt and resume | `interrupt()` per human seat; one Future per seat; one resume with the whole batch | `turn/human_turn.py::_human_player_action`, `game_session.py::park`, `::submit_turn`, `::_collect_answers` | code; incident (challenges §1–5) | ch 1 page 5 owns; ch 8 story 2 | ch 8 report S2 | concept section of S2 |
| 11 | Records that explain an agent's turn; disagreement between records as the signal | Prompt copy at game end (gzip; marked partial after a restart), event log, usage ledger, error reports; the turn that failed without a model call | `storage/prompt_captures.py::build_capture`, `game/usage.py::UsageMeter`, `error_reporting.py` | code; incident (`evidence/tracing/report.md`, block 163). The June report predates today's records: re-verify | L1 R lead; L2 C | **C** | concept section of C; extension only if named |
| 12 | Trace store versus local record; a case frozen when the decision is made | `freeze_case` stamps trace and span ids, dumps once to the span and the sink; batch writes the file, served games never do; the 422 collapse made the file primary | `observability/case_sink.py::freeze_case`, `scripts/run_batch.py::write_eval_cases_sidecar` | code; incident (`tracing/implementation_notes/ISSUE_frozen_set_fetch.md`, 3 of 5 → 20 of 20) | L2 C, one paragraph | C | as row 11 |
| 13 | Store counts, derive cost at read time | Tokens, calls, failures, seconds per model per UTC hour; `game_cost` prices them when read | `game/usage.py::game_cost` | code | L2 C, one paragraph; ch 6 reads it | C | none |
| 14 | Error reporting with explicit collection limits; redaction at each sink | No bodies, headers, cookies, frame variables, model inputs or outputs; private fields filtered; game keys scrubbed; off unless the DSN is set | `error_reporting.py::_drop_private`, `::_scrub` | code. **Scope:** the report must list which sinks were examined (Sentry events, log tracebacks, Langfuse error output) and say "these safeguards", not "redacted everywhere" | L2 C and E | C | as row 11 |
| 15 | Provenance of a result: code, prompts, models | Git SHA, dirty flag, prompt-module hash, backend, models, temperature, embedder; stamped on batch, CLI, tick and admission runs. Served games get only the git SHA as the trace release | `Agents/run_fingerprint.py::runtime_fingerprint`; callers in `run_batch.py`, `main.py`, `tick.py`, `model_admission.py` | code; experiment (`tracing/fingerprinting/report.md`, owner read pending); known limits (backend field, role cards) | proposal: fold D into C as a closing subsection (plan's open question 4) | the fingerprinting report, re-verified | as row 11 |
| 16 | A cache key must contain exactly what the result depends on | Turn cache keyed on canonical JSON of the payload; the game id added so two games cannot share an answer; human seats on uncached twins | `config/langgraph.py::turn_cache_key`, `graphs/day.py`, `nodes/day/flow.py` | code; incident (`evidence/tracing/report.md` block 163; commit `fd07c0f8`; deployed 2026-10-26, nothing observed since) | ch 1 L3 exists; L2 C tells the diagnosis only | ch 1's L3 `cache_key.md` is the account; its evidence is the tracing report and the fix commit, which the report links so evidence → page stays the direction | already a line in the React identity tutorial; cross-link |
| 17 | Secrets handling: lifetime, never persisted, redacted at each sink, verified in use | Key in a per-game ContextVar, row stores a boolean, clients dropped at game end, `***` in error text, trace error output and log tracebacks, removed from Sentry; one "OK" call before a game opens; the fix that routed four providers to the player's key | `chat.py::GAME_LLM`, `::_game_key_for`, `game_session.py::_end`, `::_redact`, `game/key_check.py::check_key` | code; incident (block 99; commit `8cd83ba7`; deploy log 2026-10-17). **Scope:** name the paths and sinks examined; intended safeguards versus demonstrated coverage kept apart | L1 K lead; L2 E | **E** | concept section of E |
| 18 | A public demo that cannot be bankrupted; live settings | House games counted from the games table since UTC midnight, default 10; switch and default model set live; the cap is best-effort, no atomic reservation | `server/house.py::HousePolicy`, `routes/admin.py::update_house` | code; multiplayer audit finding 4 (the draft-cap race, same shape) | ch 6; one paragraph on L2 E | E, one paragraph | none |
| 19 | Untrusted text in agent prompts; an input trust boundary | A human's line enters every prompt unmarked. Bounds, each to be scoped in the report: no tools (by construction); every action a schema-checked legal choice; which secrets a prompt does and does not hold (to be listed, not asserted); one context per game. No defence; no incident on record; the framing path through the claim ledger read from code, untested | bounds: `agent_player.py::run_agent`, `Agents/schemas/output.py`; no injection-specific code | code (bounds only); **open:** the framing path | L1 K; L2 E | E, a report of the bounds, never of a defence | **the one likely separate lesson** (see Lessons): the project illustrates an input trust boundary, not the consequences in agents with tools and private data |
| 20 | Deploy procedure; no CI | Clean build, a check run inside the new image, smoke checks, a rollback image kept | none (procedural) | incident (`deploy_log.md`, 72 entries) | off the page for now (plan's open question 8) | A, a short section: the deploy log is the record | none |

### Corrections and discrepancies for the content plan

- The backup key is the player's second-company key, never a house key (row 5). L2 B's "the backup key
  as a rescue" must say whose.
- **Resolved 2026-10-30:** the request budget's reach. The Mistral client has no limit, but no model in the
  seed catalogue, the server or any eval config is a `mistral/` model; it is an unused provider path only a
  CLI run could name. The plan's "all providers from 2026-10-21" stands, scoped to the providers a hosted
  game can select. Report B says so in one clause.
- The house cap is best-effort with no atomic reservation (row 18), the same check-then-act shape as
  the draft-cap race in the multiplayer audit.
- The prompt copy is marked partial when a game was resumed after a restart (row 11).
- The absent-player clocks run only in games with more than one human; a solo game suspends (row 9).
- Served games carry only the git SHA as the trace release and nothing else of the fingerprint (row 15).
- Row 8's one test supports cached-replay suppression only. The ordering window has no test and rests
  on a reading of the framework's loop.

### Open implementation issue (separate from this map)

- CLI and batch runs fall back to `GAME_FALLBACK_MODEL` = Sonnet 5.5 when a model has no rescue. This
  touches the no-Sonnet-for-player-turns rule. It is a runtime question for the owner, not something this
  map resolves; recorded here so it is not lost.

---

## Chapter 8: Frontend, the live stage and replays

The spine's ten stories, same columns. "Design record" means the document written from the code on
2026-10-26 already does a report's job; it is named rather than rewritten. Lessons marked "exists" are
tutorials in `frontend/docs/learning/`.

| # | Story (the general concept) | This project's instance | Code anchor | Support | Page | Report | Lesson |
|---|---|---|---|---|---|---|---|
| S1 | An event log the client folds; events, not state and not tokens; one log for live, reconnect and replay | Numbered typed events born at commit points; the fold is one pure function | `server/game/translate.py`; the stage store and fold | code (sweep, server side); goldens (`tests/fixtures/translator_golden.py`) | ch 8 L1 spine; L2 | design records: `client_design.md` §1, `server_client_transport.md` §2–3, §8–9 | exists: realtime_and_sync |
| S2 | Human turns inside a running graph | Row 10 plus: redo AI votes after a human answers, cached and uncached twins, the cache key from pickle to canonical JSON | rows 10 and 16 | code; incident (challenges §1–5) | ch 8 L2 (ch 1 page 5 owns the pause) | **new report S2**: a synthesis of five debugging records | concept section of S2 |
| S3 | The authoritative server decides what each viewer sees, per event, at send time; side channels | Four tiers; whole-event filtering per connection; audience never on the wire; status, refusal text and night length checked as side channels | `server/game/entitlement.py::entitled`, `routes/games.py::_sse` | code; multiplayer audit 1–3; leak tests | ch 8 L2 (moved from ch 2) | design record `server_client_transport.md` §5–6 + the audit | candidate **L-server** (the learning index's "server's half" has five lines and no tutorial) |
| S4 | Reconnection and sync: replay from a cursor, history versus news, dedupe by membership, stale answers lose | status gives the newest seq at connect; silent landing below it; 40 s stream watchdog | `useGameStream`, `store.ts`, `catch-up-boundary.ts::streamStalled` | not in the sweep (frontend); design record from code 2026-10-26 | ch 8 L2 | design record `client_design.md` §3–4 | exists: realtime_and_sync |
| S5 | A layered fault model: client heals by replay, game by checkpoint, process by boot recovery | Rows 7, 8, 9; the two detection gaps (presence; no stall watchdog) | rows 7–9 | as rows 7–9 | ch 8 L1 one section pointing at ch 7 L2 A; ch 8 keeps the browser's half | ch 7 report **A** serves both | as row 7; realtime_and_sync for the client half |
| S6 | Contract-first with alarms on silent couplings; goldens pin the spec | Pydantic → openapi.json → generated TS with a drift test; translate() exhaustiveness over state keys and node names | drift test; `tests/server/test_translator.py` goldens | test (named, not run) | ch 8 L2, one paragraph | `testing.md` + `build_log.md` §2 | exists: testing tutorial |
| S7 | Latency as tempo; the server's clock is the authority | ~6 s to speak, 12–15 s to read; stage fit on 13 served games; the turn jump | `evaluation/experiments/stage_fit.py` | experiment (`stage_fit/`, rerunnable) | ch 6 owns stage fit; ch 8 one paragraph | `stage_fit/README.md` | none |
| S8 | Identity without accounts; tell rejected from failed | Seat token in an HttpOnly cookie; two copies and a reclaim door; credentials destroyed only on 403/404/410 | cookie routes | incident (challenges §7; audit 11) | ch 8, one paragraph | transport §6b + challenges §7 | segment of candidate L-server |
| S9 | A public demo not bankrupted or abused | Rows 17 and 18; the draft cap raced across an await | rows 17–18 | as rows 17–18; audit 4 | ch 6 (cap) and ch 7 L2 E (keys); ch 8 one paragraph | ch 7 report **E** serves | as rows 17, 19 |
| S10 | The live view had to survive a phone | Set-and-beat split, layer census, baked backdrops, 534 MB to 114 | stage code | experiment (rendering audit; build_log §8) | optional L3 | `build_log.md` §8 and `phone_lessons.md` | exists: rendering_pipeline, memory_and_pictures, performance_method |

Chapter 8's record is in better shape than chapter 7's: nine tutorials and two design records already
do the lesson and report jobs for stories 1, 4, 6, 7, 10. Its gaps are server-side and are chapter 7's
gaps too: one new report (S2) and the server-half concepts.

---

## What gets written

### Reports

All five follow one structure: concept and problem → this project's design or incident → implementation
and supporting records → what the checks establish → limits and open questions. The concept section is
where the teaching happens; it is expected to absorb most of what the first draft scheduled as lessons.

| Report | Serves | Rows | Note |
|---|---|---|---|
| **B. When a dependency fails** | ch 7 L2 B | 1–4 | **The pilot.** Two incidents, one principle; a marked paragraph on pattern pieces not used here (optional, only if it helps the comparison) |
| **A. Serving the engine and surviving a restart** | ch 7 L2 A; ch 8 S5 | 6–9, 20 | Concept section on checkpoints and what runs twice; row 8's three claims kept apart with their own support; the deploy procedure as a short section with the deploy log as its record |
| **C. What a game leaves behind** | ch 7 L2 C (with D, proposal) | 11–15 | A re-verification of the June tracing report against today's code, extended to the hosted path; the fingerprinting report folded or linked (owner's call, question 4) |
| **E. A player's key and a player's words** | ch 7 L2 E; ch 8 S9 | 5, 14, 17–19 | Scoped wording throughout: which secrets, paths and sinks were examined; intended safeguards versus demonstrated coverage; the injection part reports bounds, never a defence |
| **S2. The session and the human turn** | ch 8 L2 | 10, 16; challenges §1–5 | Chapter 8's only new report |

### Lessons (conditional; none scheduled)

A lesson is written when, after a report's concept section is drafted, a named gap remains. The
candidates, with the gap that would trigger each:

| Candidate | Would extend | Trigger |
|---|---|---|
| Failure handling for remote calls | B | B's concept section cannot explain the retry-storm and breaker interaction without a comparison the project lacks |
| Durable execution for long-running agents | A, S2 | A's intro strains, or an expected question reaches side effects across external systems |
| Blocking work and the event loop | A | A's concept section cannot carry the executor and capacity material |
| LLM observability and provenance | C | C's concept section cannot say what each record establishes without a general frame |
| **Trust boundaries: untrusted input in agents** | E | **Likely.** The project illustrates an input trust boundary; it does not illustrate the consequences in agents with tools and private data, which is what interview questions reach for. Still written only after E's concept section shows the gap |
| The authoritative server | S3, S8, S9 | The learning index's five-line "server's half" is not enough for the chapter 8 page |

Existing tutorials cover the rest of chapter 8. One cross-link: row 16's cache-key lesson is already a
line in react_identity.

### What has to be established, not assumed

Being present for an incident does not establish understanding of the mechanism or ownership of the
decision. For each report the owner marks, before drafting:
- **Understanding to establish:** which mechanisms the owner can currently explain unaided, and which the
  concept section has to teach.
- **Decision ownership to confirm:** which rulings were the owner's (dated in the design notes and the
  talking points) and which were the builder's, so the page's "I ruled" is accurate.

### Order of work

1. Write report **B** as the pilot, complete, in the five-part structure. Judge from it how much concept
   a report carries.
2. Report **A**, complete: concept section, the six sections for rows 6–9 and 20, checks, limits.
3. Report **C**: re-verify the June tracing report against today's code, then extend.
4. Report **E**; then decide the trust-boundary lesson from E's concept section.
5. Report **S2** when chapter 8 starts; the server-half lesson decided from S3's page needs.
6. Revisit the content plan's proposals (fold D into C; no event-ordering L3; backup key in notes) once
   A and C exist, since each depends on what those reports turned out to hold.

---

## For the owner to rule

1. The report rule: the owner's "backed by code" or the review's "claims need identifiable supporting
   evidence"? The map uses the wider one.
2. `evidence/production/` as the home for chapter 7's reports, or a folder under `frontend/docs/`?
3. Report C: revise `evidence/tracing/report.md` in place (dated), or a new report that points at it?
4. Whether the fingerprint keeps its own page or folds into C can wait for report C; confirm that order.
5. The open implementation issue above (the Sonnet batch fallback) is logged, not decided here.
