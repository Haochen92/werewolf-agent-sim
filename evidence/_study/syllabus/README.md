# Syllabus for chapters 7 and 8: a study course, one chapter per unit

Personal learning material. Moved here from `interview_prep/syllabus/` on 2026-10-31 so it can be read through Claude Code on the web while travelling; it returns to `interview_prep/` afterwards. Not page copy and linked from no page. The goal is transferable understanding:
after a unit I can say "I understand checkpointing and replay, and here is how my project uses them",
and separately narrate what happens when this server restarts. Being able to explain the portfolio
pages follows from the first; the course is not organised around the pages.

Source: the working syllabus `writeup/_planning/ch7_ch8_syllabus.md` (2026-10-30), which fixed the
units, their order and the time budget. This folder turns each unit into a chapter that teaches the
concept, places this project inside it with the support behind each claim, and ends with checks and a
workbook. The treatment map `writeup/_planning/production_and_frontend_treatment.md` decides which
public documents get written; nothing here is page copy.

## How a chapter is built

Every chapter has the same seven parts, in this order (`_chapter_template.md`):

1. **Header**: time, category, depth, prerequisites, and the diagnostic question to answer first,
   in two sentences, with an example that is not from this project.
2. **The concept, taught**: the mechanism in plain words with a worked example from outside this
   project, then the field's terms attached to the parts of that example.
3. **Alternatives and trade-offs**: a short table of the designs a team could choose, with where this
   project sits marked. A project choice is never presented as the only design.
4. **This project**: the instance, with each claim tagged by its support and linked to the code or
   record. Support labels: **code** (inspected), **test** (named, not run unless stated), **incident**
   (a dated record), **none** (asserted somewhere, nothing found behind it).
5. **Reading**: the named sections, linked, with what to take from each.
6. **Checks**: a transfer scenario answered from the concept, and a project-evidence check (a draft
   claim: what stands behind it and the accurate wording). Answer keys sit at the end of the file;
   attempt first.
7. **Workbook**: slots for the concept in my own words, the transfer answer, the claim with its
   support, remaining gaps, time taken.

## Relevance categories and depths

| Category | Meaning |
|---|---|
| **1** | AI or agent engineering; likely in interviews and in the next job |
| **2** | General software engineering; likely in design exercises |
| **3** | Specific to this project; keep the lesson, not the mechanics |
| **4** | Specialist depth to defer |

| Depth | Meaning |
|---|---|
| **Explain** | Explain the mechanism and its limits, compare alternatives where there is a choice, apply it outside this project |
| **Recognise** | Name it, say where it is in this system and what it decided, know where to read more |
| **Reference** | Know a document exists; open it when a question needs it |

Category 3 material (exact clocks, cooldowns, the tier of each event, the record inventory, the
fingerprint's fields) appears only as this project's instance inside a chapter. Category 4 material
(framework internals, the sync-over-async arithmetic, exactly-once as a protocol) is pointed to, not
taught. Framework-specific behaviour lives where it is already documented:
`../../../interview_prep/langgraph_langfuse_issues.md`, `../../../frontend/docs/server_encountered_challenges.md`,
`../../../frontend/docs/frontend_lessons.md`, `../../../frontend/docs/deploy_log.md`.

## Diagnostic before each chapter

Nothing is assumed known, including the incidents I was present for. Judge the answer for a correct
mechanism, a relevant boundary or failure case, and a valid application, not confidence or
vocabulary. A correct answer permits a shorter concept read, then the project part and the checks; a
gap means reading the concept part in full. Record unresolved questions rather than rehearsing an
answer from the key.

| Unit | Diagnostic question |
|---|---|
| 0 | Draw a component diagram of a system you know, and mark which store is the record of what. |
| 1 | What is a circuit breaker for, and when is it the wrong tool? |
| 2 | When does a synchronous call block other tasks on the same event loop, and what are two fixes? |
| 3 | What can an event log tell you that a state snapshot cannot, and what does it cost? |
| 4 | What does "at-least-once delivery" oblige the receiver to do? |
| 5 | How does a long-running workflow wait days for a human and survive a redeploy? |
| 6 | Why does a reconnecting client send a cursor, and what goes wrong if it dedupes by "highest id seen"? |
| 7 | Where must per-viewer authorization happen in a streaming system, and name one side channel. |
| 8 | What does a trace establish about a failed LLM call that a log line does not, and what can neither establish? |
| 9 | What must be recorded so that a change in an eval score can be attributed to a cause? |
| 10 | What is the lifecycle of a customer-supplied API key in a well-run service? |
| 11 | What bounds the damage of prompt injection in an agent, and why is filtering alone insufficient? |
| 12 | What makes a React component re-render, and what stops it? |
| 13 | What does a passing golden test establish, and what remains untested even with CI? |
| 14 | Which settings would you choose to change without a deploy, and what controls should protect them? |

## Dependency order

```
U0  System architecture orientation
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
 ├─ U12 Client-side state and rendering                      (tutorials; needs U6)
 ├─ U13 Testing strategies and levels of verification       (concept paragraph after U0; checks later)
 └─ U14 Operations: deployment, live configuration, cost control  (needs U1, U2, U10)
```

Chapter 7 needs U0 to U5, U8 to U11, U13 and U14. Chapter 8 needs U0, U2 to U7, U12 and U13.

## Blocks and time

First-pass estimates sum to 15 h 20 min; allow 20 to 21 hours with practice and revisiting, about
eleven two-hour sessions. Calibrate after U1 and record the real time in the progress table.

| Block | Units | First pass |
|---|---|---|
| 1 | U0, U1 | 135 min |
| 2 | U2, U3 | 135 min |
| 3 | U4, U5 | 105 min |
| 4 | U6, U7 | 135 min |
| 5 | U8, U9 | 115 min |
| 6 | U10, U11 | 120 min |
| 7 | U12 | 90 min |
| 8 | U13, U14 | 85 min |

## Reading rules

A chapter is complete when I can explain the mechanism, handle its transfer scenario with
assumptions stated, and distinguish the project's evidence from its gaps. Outside reading is a named
section, never a whole book, and only where the project material cannot carry the learning outcome.
Finishing a chapter does not promote a project story to portfolio evidence; the evidence reports do
that, and once they exist they replace the raw reading lists here.

## Progress

| Unit | Chapter | Status | Date read | Time taken | Open questions |
|---|---|---|---|---|---|
| U0 | [System architecture orientation](u00_system_architecture.md) | drafted 2026-10-31 (pilot) | | | |
| U1 | [Resilience patterns for remote calls](u01_resilience_patterns.md) | drafted 2026-10-31 (pilot) | | | |
| U2 | Concurrency models and executors | not started | | | |
| U3 | Snapshots, event logs and replay | not started | | | |
| U4 | Delivery semantics and idempotency | not started | | | |
| U5 | Durable execution and human-in-the-loop | not started | | | |
| U6 | Real-time transport and client sync | not started | | | |
| U7 | Server-side authorization and side channels | not started | | | |
| U8 | LLM observability | not started | | | |
| U9 | Experiment provenance | not started | | | |
| U10 | Secrets management in LLM apps | not started | | | |
| U11 | Prompt injection and trust boundaries | not started | | | |
| U12 | Client-side state and rendering | not started | | | |
| U13 | Testing strategies and verification levels | not started | | | |
| U14 | Operations and cost control | not started | | | |

## Open items

- The syllabus's U6 reading cites `frontend/docs/client_design.md`, which no longer exists under that
  name after the frontend docs reorganisation; re-point it when U6 is drafted.
- After the U0 and U1 pilot: fix the chapter depth and length, then draft the remaining blocks in
  dependency order.
