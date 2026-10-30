# Worked examples: same approach, different structures

Choose the closest example and read its **page copy** (the `## Page copy (draft)` section, not the historical brief or
the comments). A and B are Level 2 drafts the owner preferred after their 2026-10-28 revisions. C is a later
direct rewrite used for its opening and selection choices, not an independently verified exemplar.
They are examples of a process, not templates: do not copy their headings, section count or rhythm.

- A: `writeup/game_design_orchestration/day_and_night/day_and_night.md` (Multi-Agent Game Orchestration)
- B: `writeup/game_design_orchestration/evidence_design/evidence_design.md` (Designing evidence worth debating)
- C: `writeup/evaluation/llm_judges/llm_judges.md` (Defining and choosing an evaluation approach; limitations noted below)

## Why their structures differ

| | A: architecture | B: design decision tested by experiments |
|---|---|---|
| Reader's question | How do ten model-driven seats become one consistent game? | How do you give model players competing evidence, and get the evil side to contest it? |
| Central answer | Each kind of decision has its own dependency (in sequence, independent, simultaneous); the graph keeps those dependencies, and code, not the models, applies the rules and merges state. | Partial, truthful evidence gives the town something to cross-check; the evil side needed explicit instructions before it used false claims; a replay showed more claims, whole games showed claims entering play. |
| Structure | Follows the **execution order**: game loop → a day → a night → passing information in and out → what players read → ending the day → checks. | Follows **successive questions**: why was talk thin → what evidence to give → why it wasn't used → did the instruction change behaviour → what happened in games → what is established. |
| Why that fits | The reader needs the system's dependencies in the order they occur; each mechanism makes sense once the step before it is known. | Each finding is the reason for the next change or test; reading them out of order would hide why each step was taken. |
| Role of evidence | One failure (the private-note overwrite) is the worked example, placed where the concept it exposes (reducers) is explained. | Experiments carry the argument; each gets its setup and comparison before its numbers and its limit beside its result. |

## Argument outline that A embodies

| Section | Question | Main point | Carried by | Why the next follows |
|---|---|---|---|---|
| Opening | Why does a game of ten agents need orchestration? | Decisions have different dependencies; code keeps them whatever the model speed | Discussion vs votes vs night actions | Names the three dependencies the sections then handle |
| The game loop | What is the overall shape? | The main graph follows the game cycle; model calls sit inside phases, rules in code | Main graph diagram; node/subgraph introduced as needed | The day is the first phase in the loop |
| A day | How are independent and dependent turns run? | Rounds fan out and wait at a barrier; discussion loops one speaker at a time | Parallel agents repeated each other → sequential; day diagram | Collecting also orders entries: a state question, and the night has a different collection need |
| A night | How are simultaneous actions kept fair? | Choose in parallel, resolve once after all branches finish | A fast attack cannot beat a slower protection; the Illusionist's dependency | Phases need restricted inputs and their results merged back |
| Passing information in and out | How do phases get only what they may know, and how do results return? | A wrapper builds the input; that makes it responsible for returning updates; reducers decide how | The private-note overwrite, with a three-row table and its tests | State is preserved; agents still need a usable account of it |
| What every player reads | How does state become something an agent can reason from? | Records with different authority, labelled and kept apart | The summary error, with "illustrates, does not isolate" beside it | All of this has to terminate |
| Ending the day safely | What stops a loop running away? | Game rules end the day; a derived step budget keeps the framework limit out of reach | Budget as a design aim; the main graph's default limit stated plainly | How any of this is checked |
| Checking the wiring | What is established? | Scripted-model games and targeted tests check execution and state handling | Closing scope: play quality needs separate evaluation | — |

**What A does well**

- The opening states the central answer before any framework term. "Fan-out/fan-in", "barrier",
  "reducer" and "recursion limit" each appear at the moment a game need calls for them.
- Each section opens by answering what the previous one left open ("Preserving state is only part of
  the problem").
- The featured failure sits inside the concept it teaches, with the damage, the fix and the tests
  in one place. The fault is told as caught and fixed, not dramatised.
- Limits sit beside their claims: the summary example "does not isolate the summary's effect"; the
  step budget is "an aim", and the main graph's default limit is stated rather than hidden.

## Argument outline that B embodies

| Section | Question | Main point | Carried by | Why the next follows |
|---|---|---|---|---|
| Opening | What was wrong with the earlier game's evidence? | One exact source, no rival accounts; the redesign changed both sides; opportunity alone was not enough | The two questions the tests examine | Sets up the diagnosis |
| The earlier game | What did the old design give agents to contest? | Exact roles in one agent, no evil claims | 24 of 28 Investigator claims, 0 evil claims; labelled exploratory, "my reading" | The diagnosis motivates two changes |
| Partial evidence | What should the town know instead? | Three observers each see something true but incomplete; the engine stays truthful | Three-row observer table; one worked reasoning example; the rejected alternative (fabricated results) | A cover is now possible, but is it used? |
| A plausible cover | Did evil use the new opportunity? | Permission was not enough; explicit cover instructions followed | Specific failures (revealing the real action, denying sightings) | The instruction change needs an isolated test |
| Isolating the instruction change | Did the card text alone change behaviour? | More claims, fewer denials on frozen turns | Method before numbers; 13 → 33 table; a claim vs a *consistent* claim; the judging revision explained | Contradictions led to an engine change; whole games test the bundle |
| In whole games | What happened when claims met other agents? | Competing accounts entered play and sometimes persuaded the town | Bundled-change caveat **before** the table; one false-claimant case | The next question is how the town weighs rival accounts |
| Establishes / open | What does this add up to? | Rule correctness and balance are separate; the narrower conclusion stated | Balance not tested on today's rules | — |

**What B does well**

- Each section ends on the question the next one answers, so the experiments read as one line of
  reasoning, not a log of trials.
- The comparison is explained before its numbers, and each result's limit is beside it (41 turns
  sampled twice are not 82 independent situations; the paired games bundle several changes).
- A distinction that changes the reading ("producing a claim" vs "producing a consistent claim") is
  drawn before the reader can over-read the table.
- A later correction to the judging is told as what the better check found, not hidden and not
  presented as a retraction.

**Apply examples critically:** B names the models used in its comparisons. Keep that context where
it changes interpretation; avoid repeating names where they add no explanatory value. Neither
example is a template or an exemption from checking scope and clarity.

## What both share (this is the transferable part)

1. The opening gives the reader the central answer, not a list of methods.
2. The section order comes from the subject (dependencies or successive questions), and each section
   answers what the previous one left open.
3. Terms arrive when a need calls for them, defined by what they do.
4. One featured example per point, placed where it explains the concept.
5. Each claim's limit sits beside it; the closing section states what is established, not a
   repeated summary.
6. Detail that answers another question is linked or kept in notes, not compressed onto the page.

## C: introducing an approach before evaluating it

Page: `writeup/evaluation/llm_judges/llm_judges.md`, 2026-10-29 direct revision.

- **Opening:** defines LLM judging, then explains code vs interpretation, volume and checkability.
  The reader understands why the method is chosen before meeting its historical failures.
- **Progression:** evaluator choice -> broad-rubric failure -> grounded criteria -> correctness and
  consistency -> live consequences -> remaining validation. Each section adds a distinct requirement.
- **Selection:** one rubric table and the structured-output comparison carry the ranking limitation.
  The word-limit trial, model-latency inventory and extraction-rubric incident remain in evidence.
  Their removal leaves room to explain the retained comparison rather than compress it.
- **Depth:** the echo gate illustrates the cost of acting on a verdict; its policy/calibration page
  supplies optional depth. This page keeps the tuning-set and model-label limitations beside its result.
- **Do not copy uncritically:** the historical human-check paragraph needs explicit scope: review was
  not blind, rejected candidates were sampled at the stronger second stage, and earlier-stage misses
  were not sampled. Use the evidence for claims, not this example as an authority.

A model-admission exemplar can be added after a trial rewrite. Its likely organising question is
what each test establishes before accepting a candidate, not a catalogue of runner steps. Do not
create a new exemplar merely to fill a category.
