# Running it in production: portfolio content plan

Status: candidate plan, 2026-10-29, from a subagent pass checked against the record. The owner chose to keep the default recommendations for now and review all plans later; nothing here is approved. The open questions at the end stay listed; the defaults taken are below.

## Defaults taken (owner 2026-10-29: keep the recommendations for now)

- The fault model, restart recovery and absent-player clocks stay here (the server's side); chapter 8 shows what the player sees and links here.
- The lesson-store outage lives here, on L2 B; the memory chapter links to it.
- Group order: Serving → Dependency failures → Seeing → Credentials and input.
- Revised 2026-10-30 after an outside review (owner approved): four L1 sections, one per responsibility, replace seven; the opening table is dropped; "recovery was the easier part" is dropped as the thesis (wrong as worded) and detection-vs-recovery becomes one lesson in the dependency section; groups renamed; altitude fixes (only "30 seconds" stays as a number); tags Reliability engineering + LLM observability.
- The runtime fingerprint keeps its own Level 2 page (D).
- Error reporting and the usage ledger fold into L2 C.
- Server authorship: decisions in first person ("I chose / ruled / designed"); the code is not claimed as written by the owner (`server_talking_points.md`).
- The house cap and off switch go to chapter 6 (cost).
- The deploy procedure stays off the page for now.
- The 2026-07-21 loss of the trace store stays off the page.
- Prompt injection shares the credentials section on Level 1 (a short, explicit statement of the limit); keys and injection share L2 E.
- No Level 3 for now; the event log running ahead of the saved state is the first candidate.
- Recheck at drafting: no rescue model on the house default; whether hosted games trace to Langfuse; the cache fix's deploy state; whether the 64 threads and the key check before a game opens are live.

---

Planning note, 2026-10-29. Not page copy. Built from `writeup/_planning/structure_proposal.md` (read as it stood
on disk on 2026-10-29, including that day's chapter 2 change: the served-game audit stays off the page
until it runs), `writeup/_planning/map.md` (blocks 96–101, 104, 106, 111, 115–116, 153–165, "Covered outside
the map", topic hooks), the two approved Level 1 pages and their content plans,
`human_in_the_loop.md`, `cache_key.md`, `fair_comparisons.md`, and the sources named under
"Disposition". Code was opened in two places only, to check claims (the rescue setting, the Langfuse
env names); nothing in the repo was edited.

---

## 1. Frame

*Revised 2026-10-30 after an outside review, approved by the owner. Four sections replace seven, the
opening table is dropped, and "recovery was the easier part" is no longer the thesis. That line was wrong
as worded: only a process restart is recovered (the game resumes from its last saved step, so an
unfinished step runs again); a crash inside one game is not resumed and the player starts a new game
("deliberately unwired", `server_design_notes.md` §5c mode 2); a player-funded game waits for its key
after a restart. Detection versus recovery stays as one lesson, inside the dependency section.*

**Reader's question.** *How did you turn a locally running agent system into a service that people can
use, and diagnose when it fails?*

**Central answer.** Running a game locally let me inspect failures and start again. Hosting it meant
four responsibilities:
1. keeping the site responsive while agents and humans take their turns, and preserving progress across
   restarts;
2. deciding what happens when a dependency stops responding or breaks;
3. keeping records that can explain a failed turn afterwards;
4. using players' API keys without storing them, and recognising the limits around their typed words.

**L1 shape: an intro and four sections, one per responsibility; the section headings are the groups.**
Each section gives its main point, one supporting example where one pushed the design, its limit beside
it, and the Level 2 link. No opening table: the four headings give the navigation, and the first-cut
table mixed things that do not stop a game (a closed tab) with things that are not recovery (a key
refused before a game opens). Sections are not chained by "each failure explains the next safeguard";
each stands on its own responsibility.

**Group names** (owner 2026-10-30; the first cut's "When it broke" and "Keeping keys and input safe"
are renamed, the second because it promised a safety the injection gap does not support):
Serving the engine · Handling dependency failures · Seeing what happened · Handling player credentials
and input.

**Altitude rules (from the Game design L1, owner 2026-10-26).** On Level 1: timeouts, checkpoints,
fallback, the circuit breaker and credential handling, where they explain a decision. One number stays:
30 seconds, because it is the decision itself ("time became a failure"). Retry counts, the cooldown, the
thread count, the record inventory and the fingerprint's fields go to Level 2. No dates or scope clauses
inside an explanation; each caveat once, beside its claim.

**Facts the short sections must keep exact:**
- **Restart:** "a server restart resumes every running game" is about process restarts; a crash inside
  one game is not resumed.
- **Fallback:** "a model from another provider where the game has one, otherwise the turn's legal
  fallback". The house default (Haiku) has no rescue model, so never "every stalled turn moves to a
  rescue model".
- **Fingerprint:** it stamps batch runs. Hosted games are not stamped, so it is never presented as a
  hosted-service capability.

**Tags.** Public: Reliability engineering, LLM observability. Supporting terms where demonstrated:
secrets handling, credential redaction, checkpointing, asynchronous execution, experiment provenance. No
broad security tag.

**Length:** intro 150–200 words; four sections of about 90–130 words (the dependency section may run a
little longer for its second case); about 600–750 words in all.

---

## 2. Sections in order

### Intro: "Running it in production"

- **Main point:** the review's opening, in plain words. Running a game locally let me inspect failures
  and start again. Hosting it meant keeping the site responsive while agents and humans took their
  turns, preserving progress across restarts, and deciding what happens when a provider stops
  responding. It also required records that could explain a failed turn afterwards, and a way to use
  players' API keys without storing them.
- **No table, no lead example, no caveat bundle.**

---

### Serving the engine: "Keeping live games responsive and recoverable"

- **Main point:** a step in a game blocks for seconds on a model or minutes on a person, and the web
  server answers every viewer from one loop. I kept one engine for batch and hosted games and let
  LangGraph run the blocking steps off that loop. Each game is saved as it runs, so a server restart
  resumes every running game from its last saved step. A human who stops answering is handled by two
  clocks, after which the seat's own agent takes the turn (one clause, linking chapter 1's human-seat
  page).
- **Example:** none on Level 1. The thread-pool incident (a human wolf's prompt arriving late) and the
  three records behind a restart go to L2 A.
- **Limit beside it (one clause):** a restart resumes from the last saved step, so an unfinished step
  runs again; a crash inside one game is reported cleanly but not resumed.
- **L2 link:** **A. "Hosting live games in the web server".**
- Sources: block 111; `frontend/docs/server_design_notes.md` §5, §5c; `seat_continuity.md` §4–§5b.

---

### Handling dependency failures: "Giving dependency failures a defined outcome"

- **Main point:** a failing dependency has to fail in a bounded, defined way. The fallback was keyed on
  errors, and a hang is not an error, so I made time a failure: a request that takes over 30 seconds
  counts as a stall, like a rate limit or a server error. A stalled turn goes to a model from another
  provider where the game has one, otherwise to the turn's legal fallback, and repeated stalls make turns
  start on the fallback for a while (a circuit breaker). Here the lesson lands: crashes were the
  recoverable failures; the hard ones raised no error and had to be made detectable.
- **Lead example: the stalled call.** One agent's turn took 301 seconds, 282 of them inside a single
  call, while a person watched a frozen table, and the rescue never fired. Source:
  `docs/agentic_ai_encountered_issues.md` §1; block 97.
- **Second case, two sentences: the lesson-store outage.** A change of embedding model made the stored
  index stale, and every new game failed at start, memory on or off. Now a game without memory never
  touches the store, and a game that asks for memory while the store is not ready is refused clearly.
  Source: block 101; deploy log 2026-10-14; commit `923fc968`.
- **Limit beside it (one sentence):** how often turns stall since the fix has not been measured, and
  there is no whole-game watchdog.
- **L2 link:** **B. "When a dependency fails".**

---

### Seeing what happened: "Recording enough to explain a failed turn"

- **Main point:** different records answer different diagnostic questions: what each player was sent,
  where the engine is, what prompt a turn read, how many calls and failures each model had, and what
  errors occurred (reported without request bodies, model inputs or keys). Written independently, they
  disagree when something is wrong. For batch runs, a configuration stamp (the runtime fingerprint) ties
  each result to the code, prompts and models behind it, so differences between runs can be explained
  (one clause; L2 D; hosted games are not stamped, said on L2 D, not here).
- **Lead example: the turn that failed without calling a model.** In one hosted game a seat passed with
  "generation failed", yet the prompt copy held no prompt for that seat and the usage ledger counted no
  failed call. The cause was the engine's cache of finished AI turns, which returned another game's
  failure. This section tells only how the records showed it; the mechanism and fix are chapter 1's
  Level 3, "The cache key that crossed games". Source: block 163; `evidence/tracing/report.md`.
- **Gap (one clause):** a cache hit and a hang still leave no record of their own.
- **L2 links:** **C. "What a game leaves behind"**; **D. "Tying a result to its build"** (with the bridge
  to chapter 5's "Designing fair comparisons").

---

### Handling player credentials and input: "Handling player keys and untrusted messages"

- **Main point:** a key needs a controlled lifecycle: sent once, held in memory for one game, dropped
  when it ends, never stored, removed from error reports, traces and logs, and tried with one trivial
  call before the game opens. A player's typed words are a separate trust problem: they enter every
  agent's prompt unmarked.
- **Lead example: the wrong-key routing.** Four provider connections silently used the server's own
  key, so a player's game would have been billed to the house and any key would have passed the check.
  Source: block 99; commit `8cd83ba7`; `frontend/docs/server_design_notes.md` §13.
- **The input limitation, stated plainly (two or three sentences):** nothing marks a human's line as
  untrusted, so this is an open gap. It is bounded by design (agents have no tools, every action is a
  legal choice checked by code, a prompt holds no keys or other players' secrets, each game is its own
  context). What remains is impersonation inside one game. No incident is on record. Never "defended".
- **L2 link:** **E. "A player's key and a player's words".**
- **End of chapter:** no summary paragraph; the page ends on the gap and its bound.

---

## 3. Narrative check (the main points in order, as one paragraph)

Running a game locally let me inspect failures and start again; hosting it added four responsibilities.
The site has to stay responsive while a game waits on models and people, so the blocking steps run off
the server's loop, and each game is saved as it runs so a restart resumes it. Dependencies fail, so each
failure needs a defined outcome: a hung model call now counts as a failure after 30 seconds and the turn
moves on, and an optional feature can no longer stop games that never use it. Some failures leave no
error at all, so the game keeps independent records whose disagreement is the signal, as when a turn
"failed" without any model call. And players bring keys and words: a key is held for one game and never
kept, while their words reach every agent's prompt, an open gap bounded by the design.

(Four responsibilities, each standing on its own; detection versus recovery is one lesson inside the
dependency section, not the spine.)

---

## 4. Level 2 pages

| L2 | Title (working) | Group | Page type | What it holds | Why it deserves a page |
|---|---|---|---|---|---|
| A | Hosting live games in the web server | Serving the engine | Architecture/mechanism, with one design-decision subsection | One engine and two hosts: the three options (block 111, design notes §5). The parity check before migrating. The 8 → 64 threads. A game as a live machine with one task (§5b in one paragraph). Surviving a restart: three records, each the authority on one thing, and a key-funded game waiting for its key (§5c mode 3, §8, §11; talking points). The event log can run one step ahead of the saved state: the belief corrected by reading the framework's loop, a test that replays every chunk of a real game as already sent, and why a blanket dedup was rejected (challenges §8). Absent humans: two clocks, then the seat's agent takes the turn, or the game parks (seat_continuity §4–§5b, in one subsection). Limits: a step in flight re-runs, so a turn's wording can differ from what a viewer briefly saw; no exactly-once claim | It answers the interview's most likely server questions, "what happens when the server restarts?" and "why not async all the way down?", with decisions, rejected alternatives and one corrected belief. That is several connected explanations, not one finding |
| B | When a dependency fails | Handling dependency failures | Incident and reliability case study (two incidents, one principle) | **The stall:** impact (301 s, a frozen table); mechanism (stacked retries, a hang is not an error; the misleading log banner); containment and the permanent fix (budget, stall classification, rescue from another company, circuit breaker; day summary 90 s with the raw transcript as its fallback); the extension caught three weeks later, when a key-funded game that looked hung (the frontend, in the end) showed that the budget had reached only one provider's clients and another provider's calls still waited 600 s a try, three tries (deploy log 2026-10-21); the backup key. **The lesson store:** cause chain in three lines; three guards (published index, signed by its embedder, refused with a clear message); memory-off games independent. **Verification:** what was deployed and how each was checked (tests for the stall path; one memory-on game). **Remaining exposure:** no whole-game watchdog; stall rate unmeasured; the viewer is not told about the rescue; the house default model has no rescue, so a stalled turn there becomes a legal pass | Two real production incidents with the same lesson: a failing dependency must fail in a bounded, defined way. This is the chapter's reliability core and the map's topic hook. One page with two cases avoids a thin page for block 101, and the shared principle keeps it from reading as a catalogue |
| C | What a game leaves behind | Seeing what happened | Mechanism, with a diagnostic case | Four questions, each with its reader (block 153). Two paths, batch and hosted, and why they record differently (154): the eight-row record × path table. The evaluation case shaped at decision time, and the local file primary since the 422 collapse (155, 161; the collapse in one paragraph as the reason). One shape for both copies (156, briefly). The prompt copy saved at game end (158; **no audit claim**, see §7 below). The usage ledger, which keeps counts and works out cost when read, so a corrected price corrects every game (159; chapter 6 reads costs from it). Error reports with collection limits (159). The diagnostic case: the three records side by side for the cross-game turn (163), and the earlier misread absence, an empty trace that was a human's turn (challenges §7). Gaps: no explicit cache-hit or hang record; hosted evaluation cases kept only in the tracer | Observability is a broad skill no single component owns (the map's topic rule). The page shows records doing a job, not a list of logging tools. The 422 collapse and the two absences are distinct decisions, so it is a full L2 |
| D | Tying a result to its build | Seeing what happened | Design decision, with limits | Three provenance records, none a substitute for another (RunConfig, the fingerprint, the artifact manifest); code identity in the fingerprint and data identity on each case (157); the confound that forced it; the refactor accepted on an identical fingerprint, and what that match did and did not show (162); the code-versus-record rule in one clause (its home is Evaluation's architecture); limits: drift-evident, not reproducible; the uncommitted-changes flag records the fact, not the diff; the backend field mislabels runs on Claude; the prompt hash misses the role cards; hosted games unstamped (164) | The structure proposal makes the fingerprint chapter 7's. Its limits change how every result in chapters 4 and 5 is read. Chapter 5 uses it, but does not explain what is in it or what it cannot prove. *Alternative: fold into C as a closing subsection (open question 4)* |
| E | A player's key and a player's words | Handling player credentials and input | Design and threat model, with a stated gap | **Who pays:** the house's daily cap and off switch, as the reason a player brings a key (design notes §13; one paragraph). **The key's lifecycle:** sent once, held for one game, dropped, never stored, waiting after a restart, scrubbed from errors, traces and logs, tried before the game opens; the backup key under the same rules; the two incidents (block 99). **Untrusted input:** how a line enters the prompts; the bounded-by-design list beside the one open path, impersonation in one game, and the framing path through the claim ledger (read from code, untested); fixes considered, not planned (block 98) | Secrets handling and prompt injection are what a hiring reader checks on any public LLM app. Two blocks with real incidents on one side and an honest, bounded gap on the other make one complete page about the system's trust boundary |

**Dropped as a separate L2:** "Error reporting and the usage ledger" (first cut). It is one block (159),
and both parts serve the records page's question. The ledger's cost use is chapter 6's.

### Level 3 candidates (assess after the L2 pages are drafted)

| Candidate | Anchor | Assessment |
|---|---|---|
| **The event log that ran ahead of the saved state** | L2 A, restart subsection | **Possible.** A distinct follow-up question (can a restart send an event twice?). It has a method (reading the framework's loop, not testing), a check (replaying every chunk of a real game as already sent), a rejected fix with its reason (dedup would swallow events that legitimately repeat), and an accepted window. It adds depth L2 cannot carry |
| **Why async was not the end state** (the sync-over-async decision in depth: ~89 functions and 23 call sites, executor behaviour, the 0.51 s parity measurement) | L2 A, first subsection | **Possible, weaker.** Listed as possible in chapter 1's plan. It risks being a longer restatement of L2 A; take it only if L2 A has to cut the arithmetic |
| **Why the evaluation record left the tracer** (the 422 collapse) | L2 C | **Possible.** A clean diagnostic with a before/after (3 of 5 built → all 20 seed games built). It fits chapter 5's readers as much as this chapter's |
| The cache diagnosis | — | **Not a chapter 7 L3.** Its home is chapter 1's L3; L2 C tells only the three records |
| The 301-second turn's anatomy | — | **Stays on L2 B.** The page needs the same timeline |
| The refactor gate | — | **Stays on L2 D.** One paragraph |

Recommendation: no L3 is needed for the chapter to stand. If one is added, the event-log ordering is
the strongest.

---

## 5. Disposition of every source and block

### Map blocks

| Block | Disposition |
|---|---|
| 96 (model per job) | Chapter 6. Chapter 7 cites only "a rescue from another company", in L2 B, and links |
| 97 (the stall) | L1 §2 lead; L2 B home |
| 98 (prompt injection) | L1 §7; L2 E home |
| 99 (player keys) | L1 §6 lead; L2 E home. Sentry's share of the scrubbing is mentioned once in L2 C |
| 100 (model admission) | Evaluation (admission) and chapter 6. L2 B mentions only that each model's rescue is set in the live catalogue |
| 101 (lesson-store outage) | L1 §3; L2 B second case (open question 2) |
| 104 (turn fallback) | Chapter 1 page 4. L2 B points to it for "a stalled turn with no rescue becomes a legal pass" |
| 106, 115 (node cache, cross-game key) | Chapter 1 page 5 and its L3. L1 §4 and L2 C tell only the diagnosis |
| 111 (async host) | L1 §1 lead; L2 A home (moved from chapter 1's page 5) |
| 116 (limits: the event log leads the saved state; re-run on resume) | The event-log ordering moves home to L2 A, with chapter 1 page 5 keeping one clause. The re-run on resume stays in chapter 1 |
| 153–156 | L2 C |
| 157 | L1 §5 lead; L2 D |
| 158 | L2 C (the prompt copy). **No audit claim** (structure proposal 2026-10-29: the served-game audit stays off the page until it runs) |
| 159 | L2 C (ledger and error reports); chapter 6 reads the ledger |
| 160 (verification) | Split: L2 C and L2 D each describe what their tests check, in the Verification segment. No authorship, no counts |
| 161 (the 422 collapse) | L2 C, one paragraph as the reason the local file is primary; possible L3 |
| 162 (refactor gate) | L2 D |
| 163 (the cache diagnosis) | L1 §4 lead; L2 C case |
| 164 (gaps) | L1 §5 (hosted games unstamped); L2 C and D limits |
| 165 (limited uses across a pause) | Chapter 1 page 5. Not chapter 7 |

### Sources

| Source | Disposition |
|---|---|
| `evidence/tracing/report.md` | L2 C (main); L2 D (decisions 7–8); L1 §4. Incident "Disk full": at most one clause on L2 C (the local copy survived the trace store's loss). It is recorded in the operations notes, outside `evidence/`, so it is handled with care and not led with |
| `evidence/tracing/fingerprinting/report.md`, `experiment_log.md` | L2 D (main); L1 §5 |
| `evidence/tracing/implementation_notes/` (`ISSUE_frozen_set_fetch.md`, `frozen_set_fetch_explained.md`, `experiment_log.md` sufficiency audit, smoke logs) | L2 C (the 422 paragraph, the June sufficiency audit in the Verification segment); possible L3. Smoke logs unused |
| `docs/agentic_ai_encountered_issues.md` §1 | L2 B (the stall); L1 §2 |
| same, §2 (draft credit cap, line cap) | Line cap → L2 E's bounds; credit cap → chapter 8 or chapter 1 page 5 (the human seat) |
| same, §3 (stage tempo) | Chapter 8 |
| `frontend/docs/server_design_notes.md` §5, §5b, §5c, §8, §10–§11 | L2 A (and the intro's table from §5c) |
| same, §6 "Stalls" | Pointer only; the detailed home is the agentic log |
| same, §7 (absent players) | L2 A subsection (with `seat_continuity.md`); see open question 1 |
| same, §13 (funding, BYOK, backup key) | L2 E (who pays, key lifecycle); L2 B (backup key as a rescue) |
| same, §1–§4, §6 wire items, §9, §12 | Chapter 8 (the translator, the wire, rooms, HTTP composition) |
| `frontend/docs/server_encountered_challenges.md` §1–§6 | Chapter 1 page 5 |
| same, §7 (the seat cookie behind the proxy) | Chapter 8 (identity). L2 C uses only its observability lesson: an empty trace said only that no model was called |
| same, §8 (the event log leads the saved state) | L2 A; possible L3 |
| `frontend/docs/seat_continuity.md` | L2 A (fault model, clocks, restart). The intro table takes its §1 statuses |
| `frontend/docs/build_plan.md` deploy entries → now `deploy_log.md` | 2026-10-14 outage → L2 B and L1 §3; 2026-10-17 (64 threads, key tried before the game, error reporting on) → L2 A, E, C; 2026-10-21 (budget reaching all providers, backup key) → L2 B; 2026-10-26 (cache fix) → chapter 1's L3. The Cloudflare SSE buffering → chapter 8. The deploy procedure (clean build, check in the image, smoke, rollback image) → open question 8 |
| `interview_prep/server_talking_points.md` | Interview notes, not page copy. It feeds L2 A (restart, the ordering story) and the gaps ("what would you change": the stall watchdog). Its authorship answer feeds open question 6 |
| `writeup/game_design_orchestration/human_in_the_loop/human_in_the_loop.md`, "Keep the server available while a game waits" | Moves to L2 A. Page 5 keeps one sentence and a link. Its "What the checks establish" sentence on duplicate events keeps one clause, linking to L2 A |
| `…/human_in_the_loop/cache_key.md` | Chapter 1's L3; it already tells the three records in "Two games, one answer". Chapter 7 links to it and does not retell. **Its link spec (line 112) to chapter 7 should point to L2 C** once that exists |
| `writeup/evaluation/fair_comparisons/fair_comparisons.md` | Uses the fingerprint ("Recording a configuration versus enforcing it"). L2 D must not repeat that table. Chapter 5 owns record-vs-guard, chapter 7 owns contents and limits; each links to the other |

### Bridges

- **Chapter 1** (human seat, page 5): the pause, the checkpoint and the node cache are explained there.
  L1 §1 assumes them and says "saved as it runs" without re-explaining. L1 §4 links to the cache-key
  L3 for the mechanism. Page 5's "Security" note (a human's line enters other prompts unlabelled)
  should point to L2 E, not chapter 2 (the placement table now says chapter 7). Page 4 (the turn's
  legal fallback) is linked from L2 B.
- **Chapter 2** (information boundaries): chapter 7 does not re-tell what an agent may know. L2 E
  lists "a prompt holds no other player's secrets" as one bound, and links to chapter 2 for why.
- **Chapter 4** (memory): L1 §3 and L2 B link to the memory chapter for what the lesson store is.
  Memory's v8 serving note links back to L2 B for the outage.
- **Chapter 5** (evaluation): L1 §5 → "Designing fair comparisons" (fingerprint plus guard); L2 C →
  turn replays (captures and saved state rebuild a turn) and factual errors (how a turn is rebuilt).
- **Chapter 6** (cost and latency): the two caches are told apart there (the provider's prompt cache
  against the engine's cache of AI turns). L1 §4 says "not the provider's prompt cache" in one clause
  and links. The usage ledger (L2 C) is where chapter 6's per-game costs come from. The 30-second
  budget's latency evidence (stage fit, slowest 5% of discussion calls 10.8 s on 13 hosted games) is
  chapter 6's figure, cited on L2 B. Model choice by job, and why the rescue comes from another
  company, is chapter 6's page.
- **Chapter 8** (frontend): the intro table's row 1 (reconnect and replay) and row 5's browser half;
  what each viewer is sent; the missing "this turn ran on the rescue" notice, which is a frontend
  gap; the seat cookie behind the proxy.

---

## 6. Claims to handle with care

1. **The house default has no rescue model.** The live catalogue sets none for Claude Haiku 5.5
   ("No rescue (owner 2026-10-12)", `Agents/llm_factory/catalog.py` notes; map blocks 96 and 104).
   The agentic log's 2026-10-22 update says "Sonnet 5.5 as its rescue", which contradicts the
   catalogue and the no-Sonnet-for-player-turns rule. **The page must not say every stalled turn
   moves to a rescue model.** "Where the game has one, otherwise the turn's legal fallback" is the
   accurate wording. Recheck the live catalogue at drafting.
2. **The budget's reach.** It applied to one provider's clients from 2026-10-01 and to all providers
   from 2026-10-21. Tell this as caught and fixed on L2 B. Do not imply it covered every provider from
   day one.
3. **"The worst normal turn was 11 s, so 30 s loses nothing."** The N behind the 11 s was never
   recorded (dated note in the agentic log). Use chapter 6's stage-fit figure instead, with its scope.
4. **Deployed ≠ validated.** The stall fix: one incident, diagnosed from logs, and the stall rate since
   is unmeasured. The lesson-store fix: smoke-checked with one memory-on game. The cache fix: deployed,
   with nothing said about hosted games since (owner, 2026-10-26).
5. **Prompt injection is not defended.** Say "bounded by design", "no incident on record", "an open
   gap". Never "defended", "secure" or "mitigated". The framing path is read from the code and
   untested.
6. **Key scrubbing is a set of explicit safeguards,** not proof that no exception can ever carry
   sensitive text (the tracing report's own wording). Say what is removed, not that leaks are
   impossible.
7. **No audit claim for hosted games.** The captures exist, but the nightly audit is not installed
   (structure proposal, 2026-10-29). Keep the audit job off every page of this chapter, including
   "so the same checks can run over them".
8. **Langfuse on hosted games.** The 2026-09-15 deploy entry says production had never traced. Langfuse
   variables are now in the production environment file (names only checked), but no trace from a
   hosted game was verified. The L1 lead (§4) uses only database records: the prompt copy, the event
   log and the ledger. Verify before L2 C says hosted games are traced.
9. **Counts of hosted games** (68 games, 51 completed, 11 with prompt copies) are as of 2026-10-26, and
   many may be the owner's own test games. **Never call them "users".** Keep the 11 of 68 off L1.
10. **Exactly-once.** A restart re-runs the step in flight, and the event log can lead the saved state
    by one step. Never claim exactly-once execution or delivery.
11. **The 64 threads** are reasoned from one observed wait. No load test is recorded.
12. **Fingerprint wording:** "drift becomes visible", never "reproducible". Its backend field is wrong
    for runs on Claude, and the prompt hash misses the role cards. These go on L2 D, and any "identical
    fingerprint" claim is scoped to the fields it covers.
13. **Stays off the page:** missing CI; test authorship and audit status; whether the nightly leak
    audit is installed; runs or builds from uncommitted trees; the "not pushed" deploys; the trace
    data deleted on 2026-07-21, beyond the one clause that the local copy survived it (and only if the
    owner agrees, open question 9).
14. **Model names.** No family names in L1 explanations: "the provider", "a model from another
    company". L2 B may name the provider route only where it explains the mechanism.

---

## 7. Open questions for the owner

1. **Fault model, restart recovery and absent players: chapter 7 or chapter 8?** The frontend pass's
   chapter C brief (`frontend/docs/frontend_pass/brief.md` §5, stories 5 and 9) claims the layered fault
   model, the house cap and the key lifecycle. The structure proposal gives the keys to chapter 7 and
   says nothing on the fault model. Proposed: chapter 7 owns keeping a game running on the server
   (the fault model as the intro table, restart, clocks, the event-log ordering), and chapter 8 owns
   the browser's half (reconnect and replay, the stage, identity).
2. **The lesson-store outage (block 101): chapter 7 (proposed, L1 §3 and L2 B) or the memory
   chapter?** Proposed here because its lesson, that an optional feature must fail on its own, is a
   production one.
3. **Settled 2026-10-30:** Serving → Dependency failures → Seeing → Credentials and input. *Was:* **Group order:** Serving → When it broke → Seeing → Keys (proposed), or the first cut's Seeing
   first?
4. **The fingerprint: its own L2 (D, proposed) or a closing subsection of C?** D risks overlap with
   chapter 5's fair-comparisons table. The split proposed is that chapter 5 owns record-vs-guard and
   chapter 7 owns contents and limits.
5. **Error reporting and the usage ledger folded into C** (proposed) instead of their own page?
6. **Authorship wording for the server.** `server_talking_points.md` says the server code was written
   by AI agents to the owner's specs and rulings, with three core files reviewed line by line. The
   structure proposal's authorship rule covers the orchestration code (about 90% the owner's) and the
   deduction engine (AI-written), but not the server. Proposed: "I chose / ruled / designed" for
   decisions on chapter 7 pages, and "I built" only for engine-side code. Please rule.
7. **The house cap and off switch:** inside L2 E as "who pays" (proposed), or chapter 6?
8. **The deploy procedure** (a clean build, a check run inside the new image, smoke checks, a rollback
   image kept beside it) is strong operations evidence, but it sits next to the absence of CI. Is it a
   subsection of L2 A, one sentence, or off the page?
9. **The trace store's loss (2026-07-21):** one clause on L2 C ("the local copy survived"), or off the
   page?
10. **Injection as its own L1 section (§7, proposed) or merged with the key section?** A separate
    section names the gap clearly, which is the honest choice and a good signal, but it puts an open
    gap at the end of the chapter.
11. **Level 3:** none, or the event-log ordering?
12. **Recheck at drafting:** no rescue on the house default (claim 1); whether hosted games trace to
    Langfuse (claim 8); the 2026-10-26 deploy state of the cache fix; whether the 64 threads and the
    "key tried before the game opens" are still live.
