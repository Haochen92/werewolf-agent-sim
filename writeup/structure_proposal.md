# Proposed structure for the portfolio write-up (v2)

Status: second version, 2026-10-26, after one external review and the owner's corrections. Not yet
adopted. Once agreed, it goes into `writeup/map.md` "Organisation" as the starting arrangement, and
each chapter gets a content plan like `writeup/evaluation/content_plan.md`. Subsections below are
first cuts; a chapter's content plan tests them against the map's blocks.

## The model this follows (agreed earlier; `writeup/map.md`, "The model", "Page levels")

- **Topics.** A topic is a component, or a skill broad enough that no single component owns it.
- **Segments.** Every topic is told through five: Problem, Design, Verification, Case study (holding
  the exhibit) and Gaps.
- **Levels.**
  - Level 1: one per chapter.
  - Level 2: one per substantial subject.
  - Level 3: optional, for one investigation.
  - Content decides the structure, not the folders.
- **Exhibits** are lifted from the record, never invented.
- **Testing is not a chapter.** It sits in each topic's Verification segment, plus Evaluation's
  "code checks" page.
- **Authorship is stated truthfully:**
  - the orchestration code: about 90% written by the owner;
  - the deduction engine, solver included: AI-written;
  - the tests: authorship is not mentioned on the page either way (owner, 2026-10-26). Verification
    segments describe what each test checks.
- **No title promises more than the record supports.** There is no ten-seat error rate, discussion
  quality was not measured against the nine-seat game, and "fun" was never measured.

## Overview page (above the chapters)

What the project is, the hooks in the order a newcomer asks them (what a game costs → how well the
agents play → …), and the chapter cards. Every cost figure is labelled measured or estimated, with
its configuration. Example: about $0.21–0.26 measured on Claude Haiku 5.5; about $8–10 *estimated*
for Opus 5.5, repricing two Haiku games' token counts. See the map, "Candidate hooks".

## Group A. How the game runs

### 1. Game design and orchestration: making ten agents play together

Opens with a short explanation of the game (ten seats, the sides, day and night) before any graph.

| Order | Level 2 page | What it covers | Main sources |
|---|---|---|---|
| 1 | What the game gives agents to argue about | The cast: three partial observers instead of one exact investigator; evil's true mechanics, never false results; the public lineup. The evil contest, from permission to planned covers (exhibit: claims 13 → 33 on 41 frozen turns). The balance hold, untested on Haiku. Discussion quality is stated as not measured. | `gameplay/roles` |
| 2 | Who speaks when | Openings, replies, the open floor, the closing defence; silence and the echo gate; held lines. | `gameplay/discussion` |
| 3 | How the game executes | The parent graph and two subgraphs; a subgraph where a phase has its own flow and a node where a turn is one step; parallel and sequential steps; state and fold-back; the recursion budget. | `gameplay/orchestration`; `refactor/node_factory_pattern.md` |
| 4 | How one turn works | Private payload → structured decision → resolution; the output contract and its validation (legal-target schemas, retries, the fallback move). Field order is in chapter 3. | `gameplay/orchestration`; `gameplay/turn_prompt` (the call) |
| 5 | How a human joins | Interrupt and resume; why the AI turns are cached; the uncached human twins. | `gameplay/orchestration`; `frontend/docs/server_encountered_challenges.md`, `server_design_notes.md` |

Level 3: **The cache key that crossed games.** The chain of choices, the served-game case (`51226f24`
replaying `14926d10`'s failed turn) and the before-and-after control. Its home is here; chapter 7
references its diagnosis, and chapter 6 distinguishes this node cache from the provider's prompt
cache.

### 2. Information boundaries: who may know what

One story in four steps: what the engine knows → what a seat receives → what the server sends → what
the browser reveals.

| Level 2 page | What it covers | Main sources |
|---|---|---|
| What a seat receives | The payload builder as the one boundary; the deduction engine's view built from it; the leak tests over every batch game; the leak-audit job on served games | `agent_boundaries/`; `evaluation/deterministic_audits` (cross-referenced with Evaluation's code checks) |
| What the server sends and the browser reveals | The wire per viewer (player, spectator, replay) and the Reveal switch | the server and frontend docs |
| Secrets and untrusted input (kept separate from the privacy guarantees) | **Secrets:** a player's API key held for one game and scrubbed everywhere. **Untrusted input:** the prompt-injection gap, scoped to its interface and consequence. A human's typed line enters other agents' prompts unlabelled; agents have no tools and every action is a legal-target structured output, so the worst case is a manipulated claim or vote; no incident on record. | map blocks 98–99 |

## Group B. Improving how agents play

**Group intro.** Improving play involved three approaches:
- make the information agents receive easier to use correctly;
- compute selected deductions explicitly in code;
- test whether agents can learn and apply lessons from past games. Technically, this is three
  capabilities: summing up each game reliably (extraction), developing useful strategies from those
  summaries, and applying them effectively in later games.

Each addressed a different limitation and needed its own evidence. The results differ in kind:
- replay wins for the context changes;
- uptake without changed behaviour for the deduction lines;
- for memory, a pre-registered self-improving loop that did not compound.

### 3. Context engineering: what each agent is given, and how

| Order | Level 2 page | What it covers | Main sources |
|---|---|---|---|
| 1 | Make facts available and unambiguous | The board, results worded as the seat's own action on a named night, its own night record, labelled sources, the rules stated in full, the night-1 lot | `gameplay/turn_prompt` (decisions 1–5) |
| 2 | Preserve them across days | The day summary and the claim ledger | `extraction/day_summary` |
| 3 | Test instructions, answer order and thinking effort | Per-turn briefs; conditional composition; the field order (reads before the act); sentences tried and dropped; the thinking level as a lever | `gameplay/turn_prompt` (decisions 6–15) |
| 4 | Compute selected implications in code (a distinct section) | Why after the earlier levers; the high-level algorithm (constraint propagation, three grades of statement); validation and its limits; the cost in complexity; AI-assisted authorship | `gameplay/deduction` |
| 5 (candidate) | Prompting methods across the project's model calls | An overview of the methods (presentation order, example bias, directional calibration, conditional composition, generator-verifier separation, rubric prompting), each with a short case linking to its home: the seat prompt (this chapter), the extraction and dedup prompts (chapter 4), the judges (chapter 5). Decided in this chapter's content plan | map blocks 30–33 (dedup prompts, now in the memory consolidation topic), 140–152, the extraction and judge blocks |

- **Level 3:** *The roleblocked healer.* The agent records the deduction in its notes and still
  stays silent, so the case shows both the gain and the limit.
- **Bridge to Evaluation:** Evaluation owns how an error was identified and measured; this chapter
  owns why it happened and what changed. Each has a short bridge to the other.
- **Cross-reference:** the shared-prefix prompt layout, whose cost case lives in chapter 6.

### 4. Memory: learning and applying lessons from past games

- **Opening:** the problem first (agents repeat the same mistakes every game; a person would learn
  from the last one), then a small diagram of today's pipeline: **extract → consolidate and credit →
  retrieve and apply**. Each iteration is placed on that diagram.
- **Iterations,** each told as: the problem → what we tried → how we found out → what it revealed.
  1. One document overfit.
  2. Duplicates (dedup).
  3. Retrieval precision, with **Training a reranker for retrieval (trained, not deployed)** placed
     here or as an optional Level 3 page.
  4. The content of the lessons (extraction quality, credit).
  5. The self-improving loop: pre-registered, tested, and not found to compound. This stays in the
     main narrative, with its conclusion kept to what was tested.
  6. v8, rebuilt for ten seats, live as an opt-in, not tested at scale.
- **Main sources:** `memory_system/` (v7, v8, effectiveness, ablation, strategy_adoption),
  `extraction/` (all but day_summary), `dedup/`, `retrieval/`, `store_curation/`, `credit/`,
  `fine_tuning/`.

## Group C. Knowing whether it worked

### 5. Evaluation (first draft done: `writeup/evaluation/`, commit `abfdf984`)

- **Level 2 pages:** code checks, factual errors, fair comparisons, LLM judges, model admission, play
  metrics, reference labels, replays and games.
- **Level 3 pages:** the field audit, the paired baseline, metric transfer, the model panel review.
- **What it owns:** model admission; the evaluation architecture (from `refactor/`); how runtime
  fingerprints support fair comparisons (the fingerprint itself is chapter 7's).
- **Main sources:** `evaluation/`, `metrics/`. A light reconcile pass is due against the gameplay
  reports revised on 2026-10-26.

## Group D. Serving it to people

### 6. Cost and latency: can the experience be delivered within budget and wait?

| Level 2 page | What it covers |
|---|---|
| What a game costs | Measured per-game costs per model, each labelled with its configuration; the Opus figure labelled as an estimate |
| The prompt-cache layout | The provider's prompt cache, distinguished from the graph's node cache (chapter 1) |
| Batch and offline work | Extraction run offline in batch |
| Model choice by job | Job-specific model selection; admission itself is Evaluation's |
| Stage fit | How often the live stage waits for the model |

Main sources: `caching/`, the batch extraction records.

### 7. Running it in production: can we detect, explain and recover when it fails?

| Group | Level 2 pages |
|---|---|
| Seeing what happened | Tracing and prompt captures; the runtime fingerprint (provenance, with the rationale from `refactor/`); error reporting and the usage ledger |
| When it broke | Provider stalls and the 30-second request budget; the rescue model and backup key; the cache bug's diagnosis from captures (its home is chapter 1); the missing hang watchdog as a gap |

Main sources: `tracing/` (with `fingerprinting/`), `docs/agentic_ai_encountered_issues.md`, the
server records.

### 8. Frontend: the live stage and replays

`frontend/docs/`, which is another session's area.

## Placement rules (one main home per overlapping item)

| Item | Main home | Referenced from |
|---|---|---|
| The evil contest | Ch 1, the cast page | Ch 3's deduction section (the cover lines) |
| Context isolation (what an agent may not see) | Ch 2 | Ch 3, which covers what it can use |
| Output guardrails (schemas, validation, echo gate) | Ch 1, one turn; the echo gate on "who speaks when" | — |
| Field order | Ch 3 | Ch 1 |
| Factual errors | Evaluation (identification and measurement); Ch 3 (causes and fixes) | each to the other |
| The node-cache bug | Ch 1, a human joins (Level 3) | Ch 7 (diagnosis), Ch 6 (the two caches told apart) |
| Model admission / model choice by job | Evaluation / Ch 6 | each to the other |
| The runtime fingerprint | Ch 7 | Evaluation (fair comparisons) |
| `refactor/` | distributed: node factories → Ch 1; eval architecture → Evaluation; provenance rationale → Ch 7 | — |

## Still open

1. Whether the balance hold and the untested-on-Haiku caveat sit on the cast page or in chapter 1's
   Gaps.
2. Memory's internal grouping beyond the iterations: the pipeline diagram may be enough.
3. The overview's hook order once the chapter pages exist.
