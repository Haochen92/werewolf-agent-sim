# Engineering notes behind write-up chapters 7 and 8

My working notes on the sixteen engineering topics that the production chapter (7) and the frontend
chapter (8) of the write-up rest on. Each note does two things: it sets out a general concept in my
own terms, with an example from outside this project, and it reviews how my Werewolf system handles
that concept, including where it falls short. The first half is what carries over to the next
system I build; the second half is the checked material the write-up pages draw on.

Not page copy, and linked from no page. The topic list, its order and the time budget come from my
planning outline `writeup/_planning/ch7_ch8_syllabus.md` (2026-10-30). The treatment map
`writeup/_planning/production_and_frontend_treatment.md` decides which public documents get written.

## How a note is built

Revised 2026-11-11 after the first two notes: the first layout put the code evidence in the middle
of the explanation, which made a note read as an inventory. The explanation now comes first and the
evidence sits behind it. Every note has the same parts, in this order (`_note_template.md`):

1. **Header**: reading time, what it builds on, the question the note answers, my first answer
   before reading on, and what is covered in other notes.
2. **Part 1, the concept**: the whole in a few lines, then one idea per section, each starting from a
   problem in a worked example from outside this project and naming the term second. A short check
   with a hidden answer follows every one or two ideas. The part ends with one timeline that runs
   through every piece in order.
3. **Part 2, the choices**: tables grouped by the decision being made, with a last column
   saying where my system uses each row, since it can use several. Mechanisms that work together are not listed as alternatives. A project choice is never
   presented as the only design.
4. **Part 3, my system**: opens with a situation from the project that needs the concept, then walks
   the system through the same parts as Part 1. Every sentence states a specific fact read from the
   code or a dated record. Gaps are stated as facts.
5. **Part 4, a larger scale**: what the design leaves out or would outgrow.
6. **Part 5, worked problems**: the concept in another system, my system from memory, a draft claim
   that says slightly too much with its accurate wording, and the topic's sharp question.
7. **Part 6, summary**: the note's three or four core things in plain words, each with my system's
   answer, and my system in one paragraph. It is the page for a later read.
8. **Appendix A**: answers to the problems. **Appendix B**: the evidence, each claim tagged by its
   support and linked. Support labels: **code** (inspected), **test** (named, not run unless stated),
   **incident** (a dated record), **none** (asserted somewhere, nothing found behind it). Also the
   incidents on record, what is not established, and the reading list.

A note has two layers. The core path is the three or four ideas named in its header, taught
with the example and the checks. How a thing is built, and what belongs to another note, is marked
**Detail** and can wait for a second read. The first read is for learning and follows the core
path; later reads start from the summary.

Two rules hold the split together. The body never goes vague to avoid a detail: it states the
behaviour and the numbers, and the appendix holds the proof. And each note's Part 3 is written from
a fresh read of the code, not from memory of it.

## What goes in and what stays out

A note explains a mechanism and its limits, compares the alternatives where there is a choice, and
applies it outside this project. Material specific to this project (exact clocks, cooldowns, the
tier of each event, the record inventory, the fingerprint's fields) appears only in Part 3 and
Appendix B. Specialist depth (framework internals, the sync-over-async arithmetic, exactly-once as a
protocol) is pointed to, not written up again. Framework-specific behaviour lives where it is
already documented: `../../../frontend/docs/server_encountered_challenges.md`,
`../../../frontend/docs/frontend_lessons.md`, `../../../frontend/docs/deploy_log.md`.

## The sixteen topics on one screen

Sixteen notes, but not sixteen separate subjects. They fall into five themes between an opening
note and a closing one. Notes in a theme are parts of one story.

| Theme | Notes | What the theme is about |
|---|---|---|
| The map | U0 | Which parts exist, which record holds which fact, and where the trust boundary runs. Every later note takes one part of this map and looks inside it. |
| Work that waits or fails | U1, U2 | A call to another service can hang or fail (U1), and while it waits it can hold up everything else on the server (U2). |
| State that survives an interruption | U3, U4, U5 | One story in three steps: what to save so work can be rebuilt (U3), how to stay correct when something is therefore done twice (U4), and how the two let a workflow wait for a person across a restart (U5). |
| What each viewer sees | U6, U12 | The same story from the browser's side: catching up after a dropped connection (U6), and turning a stream of changes into a correct screen (U12). |
| Who may know or do what | U7, U10, U11 | Three kinds of thing that must not get out or get in: another player's information (U7), a user's API key (U10), and instructions hidden in text the agent reads (U11). |
| Knowing what happened | U8, U9, U13 | Recording enough to explain a failure (U8) or a changed score (U9) afterwards, and knowing what a passing test does and does not show (U13). |
| Running it | U14, U15 | Changing and paying for a live service without breaking what is running (U14), and knowing how much it can take and what gives way first (U15). U15 was added on 2026-11-12, when the capacity material proved too large to sit inside U14; it is not in the planning outline. |

The themes show how the notes connect. The writing and reading order is the dependency order below,
which cuts across them.

### Failure patterns, and where each is covered

The notes are arranged by question, not by failure. A small number of failure patterns run across
them, and this table is the way in by pattern. A row is added to or extended when a note is written.

| Pattern | What goes wrong | Covered in | In my system |
|---|---|---|---|
| Partial failure | Two records that must agree are written in separate steps, and a crash lands between them | U3 sections 1.5, 3.6 and 3.8; U4 sections 1.3 and 3.5 | The events table can be one step ahead of the checkpoint (U3 gap 2). dota2pred: Postgres and Redis at every stage (U4 3.6) |
| Repeated work | The same operation runs twice, after a retry or a restart | U3 section 3.6; U4 sections 1.2 and 3.2 | The step in flight is re-run and billed again after a restart; a lesson counter may be bumped twice (U3 gaps 3 and 5) |
| Unknown outcome | A request times out and the caller cannot tell whether it took effect | U1; U4 sections 1.1 and 3.4 | A model call the provider finished after the client gave up: nothing is done, and it is recorded as failed with zero tokens |
| Race | Two things happen in an order the code did not expect | U2 | |
| Stale copy | A cache or a derived view no longer matches its source | U3 section 1.5; U6 and U12 (to write) | |
| Work lost since the last save | A crash takes whatever was done after the last save that succeeded | U3 sections 1.3 and 3.4 | Up to 30 seconds of usage counts; a human answer not yet saved (U3 gap 6) |

## Each note's guiding question, and its sharp question

A note has three things that are easy to confuse:

- its **subject**, which is its title;
- its **guiding question**, a problem broad enough that the whole note is the answer. I write a
  first answer to it, two or three sentences, before reading on;
- its **sharp question**, which goes deep into one mechanism. It is a good test of the detail and a
  poor summary of the subject, so it sits inside the note as a check or a worked problem.

A first answer is judged for a correct mechanism, a relevant boundary or failure case, and a valid
application outside this project, not for vocabulary. The aim is a connected picture of each
subject, not sixteen stock answers; open questions go in the progress table.

| Note | Guiding question | Sharp question |
|---|---|---|
| U0 | When two parts of a system disagree about a fact, how do you know which one to believe? | Draw a component diagram of a system you know, and mark which store is the record of what. |
| U1 | A service you depend on is slow, failing or gone. How does your system still end somewhere sensible? | What is a circuit breaker for, and when is it the wrong tool? |
| U2 | One slow piece of work is holding up everything else on the server. Why does that happen, and how do you stop it? | When does a synchronous call block other tasks on the same event loop, and what are two fixes? |
| U3 | The process dies in the middle of a task. What must already have been saved, and what can be rebuilt from it? | What can an event log tell you that a state snapshot cannot, and what does it cost? |
| U4 | The same message or job arrives twice. How do you make sure its effect happens once? | What does "at-least-once delivery" oblige the receiver to do? |
| U5 | A workflow must wait hours for a person, and the process running it is restarted in the meantime. How does it carry on correctly? | How does a long-running workflow wait days for a human and survive a redeploy? |
| U6 | A browser loses its connection and comes back. How does it end up showing what it would have shown, with nothing missing and nothing doubled? | Why does a reconnecting client send a cursor, and what goes wrong if it dedupes by "highest id seen"? |
| U7 | Several people watch the same stream but may not see the same things. How do you make sure nobody receives, or can work out, what is not theirs? | Where must per-viewer authorization happen in a streaming system, and name one side channel. |
| U8 | Something went wrong inside a run of hundreds of model calls. How do you find out what happened and why? | What does a trace establish about a failed LLM call that a log line does not, and what can neither establish? |
| U9 | An eval score moved between two runs. How do you know what caused it? | What must be recorded so that a change in an eval score can be attributed to a cause? |
| U10 | A user hands your service their API key. What can go wrong with it between that moment and the moment it is gone? | What is the lifecycle of a customer-supplied API key in a well-run service? |
| U11 | Text your agent reads may contain instructions written by someone else. How do you limit what that text can make the agent do? | What bounds the damage of prompt injection in an agent, and why is filtering alone insufficient? |
| U12 | The data changes many times a second. How does the screen stay correct without redrawing everything each time? | What makes a React component re-render, and what stops it? |
| U13 | The tests pass. What do you now know, and what do you still not know? | What does a passing golden test establish, and what remains untested even with CI? |
| U14 | The service is live and every call costs money. How do you change it, and keep it within its limits, without breaking what is running? | Which settings would you choose to change without a deploy, and what controls should protect them? |
| U15 | How many games can this server run at once, and what gives way first? | For each resource a game uses, what is the limit, where is it set, and is the figure measured or arithmetic? |

For U5 and U9 the two questions are close, because the sharp question was already broad.

## Dependency order

```
U0  System architecture
 ├─ U1  Resilience patterns for remote calls              (no other prerequisite)
 ├─ U2  Concurrency models: event loops and blocking work
 │    └─ U5  Durable execution and human-in-the-loop       (needs U2, U3, U4)
 ├─ U3  State persistence: snapshots, event logs, replay
 │    ├─ U4  Delivery semantics and idempotency
 │    ├─ U6  Real-time transport and client synchronisation
 │    │    └─ U7  Server-side authorization and side channels
 │    └─ U8  LLM observability
 │         └─ U9  Experiment provenance
 ├─ U10 Secrets management in LLM applications
 │    └─ U11 Prompt injection and trust boundaries in agents
 ├─ U12 Client-side state and rendering                      (needs U6)
 ├─ U13 Testing strategies and levels of verification
 ├─ U14 Operations: deployment, live configuration, cost control  (needs U1, U2, U10)
 └─ U15 Capacity: limits, the bottleneck, a cap on games      (last; needs U2, U3, U6, U8, U14)
```

Write-up chapter 7 draws on U0 to U5, U8 to U11 and U13 to U15. Chapter 8 draws on U0, U2 to U7, U12
and U13.

## Time

The planning outline's reading estimates sum to 15 h 20 min. The current layout runs longer; the
real time for U0 and U1 goes in the progress table and the estimates are adjusted from there.

| Block | Notes | Estimate |
|---|---|---|
| 1 | U0, U1 | 135 min |
| 2 | U2, U3 | 135 min |
| 3 | U4, U5 | 105 min |
| 4 | U6, U7 | 135 min |
| 5 | U8, U9 | 115 min |
| 6 | U10, U11 | 120 min |
| 7 | U12 | 90 min |
| 8 | U13, U14 | 85 min |
| 9 | U15 (added 2026-11-12, not in the outline's sum) | 45 min |

## Rules for the notes

A note is done when it explains the mechanism, handles its problem in another system with
assumptions stated, and separates what the project's records establish from what they don't.
Outside reading is a named section, never a whole book, and only where the project material cannot
carry the point. A note does not promote a project story to portfolio evidence; the evidence
reports do that, and once they exist they replace the raw reading lists here.

Three rules on accuracy, added 2026-11-11 after an outside review of U2:

- **An incident keeps four things apart:** what was seen, what was guessed, what was changed, and
  what was established as the cause.
- **A local or faked measurement is called one in the main text,** not only in Appendix B. It shows
  how a mechanism behaves, never how production performs.
- **A general rule states when it holds.** If the rule fails for the note's own example, it is the
  wrong rule.

## Progress

| Note | Title | Status | Date read | Time taken | Open questions |
|---|---|---|---|---|---|
| U0 | [System architecture](00_system_architecture.md) | written 2026-10-31; revised 2026-11-11 | | | |
| U1 | [Resilience patterns for remote calls](01_resilience_patterns.md) | written 2026-10-31; revised 2026-11-11 | | | |
| U2 | [Concurrency, blocking work and shared limits](02_concurrency_models.md) | written 2026-11-11; revised through the walkthrough | 2026-11-11 and 11-12 (Parts 1 and 3; Part 2 and the Problems skipped) | 5 to 6 hours over two days, most of it questions and corrections, against a 90 min reading estimate | My own estimate: 60 to 70% understood. A second, faster read later. Problems B and C still to do |
| U3 | [State persistence: snapshots, event logs, replay](03_state_persistence.md) | written 2026-11-12; revised through the walkthrough; seed points in [u03_seed_notes.md](u03_seed_notes.md) | 2026-11-12 (Parts 1 to 3; Parts 4 and 5 left as optional) | One evening | Went deeper than needed into crash-window cases. Core and detail are now marked, and Part 6 is the page for a second read |
| U4 | [Delivery and repeated work](04_delivery_and_idempotency.md) | drafted 2026-11-13, first in the core-and-detail layout; section 1.3 and sections 3.1 to 3.5 rewritten through the walkthrough; seed points in [u04_seed_notes.md](u04_seed_notes.md) | 2026-11-13 (sections 1.1 to 1.4 and 3.1 to 3.5; 1.5, Part 2, 3.6, 3.7 and Parts 4 to 6 not read) | About 4 hours | Understanding of the system not complete. To carry: the engine re-runs a paused step from its start; the three ways to handle a dual write; what makes a key too narrow or too broad |
| U5 | [Waiting for a person: durable execution and human-in-the-loop](05_durable_execution_and_human_in_the_loop.md) | drafted 2026-11-13 from a fresh code read, restructured 2026-11-14; seed points in [u05_seed_notes.md](u05_seed_notes.md) | | | |
| U6 | Real-time transport and client synchronisation | not started | | | |
| U7 | Server-side authorization and side channels | not started | | | |
| U8 | [Observability: finding out what happened in a run of model calls](08_llm_observability.md) | drafted 2026-11-14 from a fresh code read; 1.6a, 1.8a, 1.9, 3.5a and the third choice in Part 4 added 2026-11-16 while reading; Part 1 and Part 3 up to 3.5a read 2026-11-16, about 3.5 hours with the walkthrough; stopped there. Left: 3.6 to 3.8, the first two tables of Part 4, the two summaries in Part 5 (about 20 minutes) | | | |
| U9 | [Experiment provenance: knowing what a result was made of](09_experiment_provenance.md) | drafted 2026-11-16 from a fresh code read, at a smaller size by my choice (about 35 minutes); the full mechanism stays in the fingerprinting report; 1.5 (designing it for a new system), the manifest and dirty-stamp passages added 2026-11-16 while reading | 2026-11-16 (Part 1 to section 3.4; 3.5, Part 4 and Part 5 left) | | |
| U10 | Secrets management in LLM applications | not started | | | |
| U11 | Prompt injection and trust boundaries in agents | not started | | | |
| U12 | Client-side state and rendering | not started | | | |
| U13 | Testing strategies and levels of verification | seed points in [u13_seed_notes.md](u13_seed_notes.md) | | | |
| U14 | Operations: deployment, live configuration, cost control | not started | | | |
| U15 | Capacity: limits, the bottleneck, a cap on games | seed points in [u15_seed_notes.md](u15_seed_notes.md); the worker design, moved out of U5 on 2026-11-14, is in [u15_detail_workers_and_leases.md](u15_detail_workers_and_leases.md) | | | |

## Open items

Limitations of the system, what would fix each, and the records a write-up page will need are in one list,
[improvements.md](improvements.md), which I go through once all the notes are written. The items
below are about the notes themselves: what a later note has to cover.

- The planning outline's U6 reading cites `frontend/docs/client_design.md`, which no longer exists
  under that name after the frontend docs reorganisation; re-point it when U6 is written.
- Note layout fixed on 2026-11-11 (see "How a note is built"); U0 and U1 follow it. The remaining
  notes are written in dependency order.
- For U8, a case from U1: rescued turns and safe defaults are logged one by one and a failed
  discussion turn is recorded as a technical pass, but nothing totals them, and a call whose first
  attempt times out and whose second answers leaves no mark at all. U8 takes it as a Part 3 case
  for the difference between a log, a trace and a metric: what the traces already hold (call
  durations), what a count would add, and where it would be kept. U1 section 3.3, gap 2, points
  here.
- For U8, from the same U1 gap: the breaker's two numbers (2 stalls, 300 s) need three figures that
  only measurement gives: calls per game per minute, the stall rate on a normal day, and how long a
  stall episode lasts. U8 should say which of the three the existing traces can already answer, and
  what would have to be recorded for the rest (U1 section 3.2, the table against the four inputs).
- For U8, from U4: dota2pred's dead-letter queues (one Redis hash per stream) have an interactive
  tool to read them (`scripts/dqltool.py`) and no count or alert; I have never read them. U8 can
  use it as the case for "a store of failures is not seen until something counts it" (U4 section
  3.7).
- For U8, from U2: nothing records how many threads of the main pool are busy or how long work
  waits for one, and the trace flush at a game's end runs on the event loop for an unmeasured time
  (U2 section 3.7, gaps 2 and 3).
- For U8 (noted 2026-11-14): the planning outline's U8 covers the server only. The frontend
  also has Sentry (`frontend/src/instrumentation-client.ts`, `frontend/src/app/global-error.tsx`;
  the files exist, their configuration is not read). U8 should have one section that follows a
  single failure across both sides: what the player saw, what the server did, what the model
  saw, and which record answers each. Open question for the treatment map: whether testing and
  observability sit in chapter 7 once, for the whole system, with chapter 8 pointing to it.
- For U6, from the U2 walkthrough (checked in the code, 2026-11-12): each viewer has its own
  `asyncio.Queue`, with no size limit. All three places that put onto one run on the event loop:
  `subscribe` (from the stream route), `_deliver` (from `_on_chunk`, inside the game task's
  `async for` over the graph's stream) and `publish_pacing` (from the pacing tracker, called from
  those two and from `loop.call_later`). No worker thread touches a queue, and the server has no
  thread-safe hand-off of its own; the graph library carries the engine threads' output back to
  the game's task. U6 should cover what a slow or stuck viewer costs with unbounded queues.
- For U6, from the U3 walkthrough (2026-11-12): the browser's catch-up is a plain replay of the
  log (U3 section 1.4), and its hard part was showing, not rebuilding. U6 should cover the split
  between history and news (`frontend/src/hooks/catch-up-boundary.ts`): old events are folded
  silently and the stage lands still, only news plays as beats, and history is applied in blocks
  because one render per old event froze a phone on a long game (`frontend_lessons.md` item 32).
  The reason no state snapshot is sent to the browser is `server_client_transport.md` section 7.
- For U14, from the U2 walkthrough (2026-11-12): "why Docker Compose for the whole deployment?"
  needs a checked answer. U14 should cover what Compose gives (one file, one command, services
  isolated on one host), what it does not (several machines, updates without a restart,
  autoscaling), the alternatives (bare host, Kubernetes, a managed container platform, a managed
  database) and why each was not taken, and the actual deploy and rollback steps on the host, which
  have not been read yet. Process, container and virtual machine as levels of isolation belong
  there too.
- For U15 and U8, from the U2 walkthrough (2026-11-12): the server container has no memory limit
  and nothing limits running games (U2 sections 3.7 gap 4 and 3.8). The two numbers are a pair:
  memory limit = idle use + (memory per running game x the most games allowed) + a margin. Known:
  about 256 MB idle, host 23 GB with about 12 GB available. Not known: memory per running game,
  which needs the container watched with one game and with several. U8 says how to record it; U15
  sets the two limits and says what a refused game is told.
- For U15, from the U2 walkthrough (2026-11-12): one capacity table for the whole server (started in [u15_seed_notes.md](u15_seed_notes.md)). No note
  is about scale; each has its own "what breaks" section, so the limits are scattered. U15 should
  gather them in one table: each resource (main-pool threads, per-phase threads, memory, checkpoint
  connections, lesson-store connections, the server's own connections, open browser connections,
  model calls in flight against the provider's rate limit, processor time for Python code), what one
  game uses of it, the limit and where it is set, what a caller sees when it is used up, and whether
  the figure is measured or arithmetic. Dividing each limit by the per-game use gives the number of
  games at which that resource runs out; the smallest of those is the bottleneck and the basis for
  a cap on running games. U2 section 3.4 is the first half of this table. The main pool's 64 came
  from one incident, not from a game cap: once a cap exists, the pool should be derived from it
  (cap x 9 for a night step, plus room for route jobs and checkpoint saves), not the other way
  round. Threads are started only when needed, so a high maximum costs nothing while idle.
- Answered in U3 (written 2026-11-12), from the two items U2 left for it: a saver can be supplied
  per game through an internal setting of the library, untried (U3 section 3.7); games are brought
  back after a restart, by logic that is tested against stand-ins only (U3 sections 3.5 and 3.8).
  Still open after U3: an automated kill-and-restart test on real Postgres; whether the log and the
  engine can disagree about a line after a restart (read in the code, not reproduced); the size of
  one game's saved state; retention.
- A source every remaining note should check first (found 2026-11-12; the folder is ignored by
  git, so a file search that respects the ignore list misses it):
  `interview_prep/langgraph_langfuse_issues.md`, written 2026-10-26, ten sections of problems met
  with LangGraph and Langfuse, each with what happened, the fix, the lesson and its source record.
  By note: sections 6 and 7 (checkpointing, node caching) for U3; 5 (interrupts) and 8.4 for U5;
  8.3 (what streams) for U6; 9 (Langfuse) for U8; 10.1 and 10.3 (stalls, no watchdog for a hung
  game) against U1. The same folder holds `server_talking_points.md`, `engineering_practices.md`,
  `decision_cards.md`, `fullstack_cards.md` and `one_level_deeper.md`, not yet read against U0 to
  U2.
