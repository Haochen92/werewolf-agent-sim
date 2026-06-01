# Sequential Day Discussion (Agent Speaking Coherence)

> **⏩ READING GUIDE / CURRENT STATE (updated 2026-05-31). Start here if picking this up fresh.**
> Goal: replace the concurrent (everyone-speaks-once-per-round, generated in parallel against a
> frozen transcript) day-discussion model with a **sequential, scheduler-driven** one, so the
> conversation reads naturally (turn-taking, adjacency, tapering) while fairness is enforced only
> at the vote. Full design + phased build plan is in **`plan.md`** (verbatim from the design
> discussion). This log records (1) a grounding pass over the current codebase, (2) the analysis
> of the plan against that code — what's already done, the real tensions — and (3) the **three
> open decisions to resolve before building Phase 0**. **Status: design captured, codebase mapped,
> no implementation started.** Resume at "Open decisions for Phase 0" at the bottom.

## Motivation

The current day discussion generates every agent's utterance **in parallel against the same frozen
transcript snapshot**, once per round, revealed together. It is fair by construction but reads as
robotic: redundant convergence (N agents independently produce near-duplicate takes), broken
adjacency (a question in round *r* is answered in *r+1*), flat participation (everyone speaks every
round), and no within-round reactivity (a dogpiled player can't defend until next round). Root
cause: redundancy is a cross-agent property invisible to a per-agent decision made simultaneously.
See `plan.md` §2 for the full diagnosis.

## Codebase grounding (current concurrent model, as of 2026-05-31)

Mapped the existing implementation so the plan's deltas are concrete:

- **Discussion loop** — LangGraph state machine in `Agents/graphs/day.py:29-72`:
  `PREPARE_ROUND → fan_out(4 role nodes in parallel) → COLLECT_DISCUSSION → check_round → loop`.
  Round control in `Agents/nodes.py:85-206` (`prepare_round`, `check_round`); loops until no one
  speaks in a round or `max_discussion_rounds_per_day`.
- **Parallelism** — `fan_out_day` (`Agents/nodes.py:88-176`) uses LangGraph `Send` to fan all
  surviving players out concurrently, each handed a **frozen `day_channel` snapshot**. Outputs
  merge via the `add` reducer on `day_channel`.
- **Silence gate** — prompted, LLM-self-judged. `DISCUSSION_SILENCE_RULE` (`Agents/prompts/common.py:39-48`)
  lists the 4 rules and instructs `return message = null` if none apply. Gate enforcement in
  `Agents/agents.py:244-252` (treats `None`/`"null"` as silence). No deterministic checking of the
  rules — fully trusts the model.
- **Per-turn pipeline** — `_run_memory_informed_action` (`Agents/agents.py:655`) already does, per
  agent: situation summary (`_generate_situations_for_agent`, ~`:364`) → memory retrieval +
  rerank (`_enrich_payload_with_memory`, ~`:439`) → generation (`_run_agent`, ~`:200`). Output
  schema `DayDiscussOutput(adopted_strategy_keys, message, updated_strategy)` in
  `Agents/schemas/output.py:16-22`.
- **Voting** — `fan_out_vote` (`graphs/day.py:61-70`) — **already simultaneous + blind**: all roles
  vote in parallel against the frozen snapshot, collected in `COLLECT_VOTES`. Resolution in
  `nodes.py:373-461`.
- **Transcript** — `DayChannel(day, round, player, message)` (`Agents/schemas/game_events.py:6-10`),
  accumulated in `DayGraphState.day_channel` via `add` (`Agents/state.py:45-62`). Formatted by
  `format_day_channel` (`Agents/formatters.py:11-20`) as `[Day X, Round Y] player: message`.
- **Personas / voice** — none. Only generic `TONE_INSTRUCTION` + role strategy prompts.
- **Human player** — `human_player` randomly assigned (`nodes.py:47-82`), threaded as a boolean
  through every state payload, but **currently unused** in prompts/logic. Scaffolding exists.

## Analysis of the plan against the code

### What's already done (de-risks Phase 0)

1. **The vote is already simultaneous + blind** (`fan_out_vote`). §3.2 is satisfied today, and
   parallel is *correct* for a blind vote. **Phase 0 does not need to touch voting.**
2. **The per-turn pipeline already exists as a per-agent unit** (`_run_memory_informed_action`).
   §3.6's "run the pipeline only for the selected speaker" is mostly *calling this existing
   function once per popped speaker* instead of fanning it out — strong reuse.
3. **The human flag is already plumbed** (`human_player`), so Phase 1 builds on real scaffolding.

### The real tensions to resolve

1. **Biggest structural change: LangGraph fan-out → sequential loop.** Per-utterance recompute is
   finer-grained than graph edges. Cleanest shape: **collapse `PREPARE_ROUND`/`fan_out`/`COLLECT`/
   `check_round` into a single `RUN_DISCUSSION` node** that runs the scheduler `while`-loop in plain
   Python, calling `_run_memory_informed_action` once per selected speaker. Voting nodes untouched.
   Minimal blast radius; keeps checkpointing intact.
2. **Riskiest new deterministic piece: PressureCalculator keyword matching.** §3.3 detects
   questioned/accused/referenced by string-matching free text — brittle exactly at the top tier
   ("unanswered direct question"), the strongest signal. **Proposed amendment:** have the generator
   emit a structured **speech-act header** (`addressed_to: [player_ids]`, `act: question|accusation|
   reference|agreement|none`) alongside the message. Nearly free (the generator already emits
   structured output), and makes pressure *genuinely* reliable instead of NLP-on-free-text. Keeps
   "deterministic where reliable" — moves extraction into the LLM output the model is best at
   producing, rather than re-deriving it with regex.
3. **Phase 0 risks the *opposite* failure — under-talking / instant convergence.** Phase 0 has **no
   proactive path** (Rule 1 "new observation" is LLM, deferred to Phase 2). An agent speaks only if
   addressed (pressure), it's the round-1 forced reveal, or it clears the pressure-rank threshold.
   On a quiet Day 2 with no investigator result, nothing seeds the conversation → convergence fires
   immediately. Need either a minimal deterministic day-start seed (N forced openers per day) or to
   accept very short Day-2+ discussions as the empirical trigger-signal that Phase 2 is needed.
4. **Dropping "rounds" needs a schema decision.** `DayChannel.round` is persisted and filtered on
   (`check_round`, `format_day_channel`). Cleanest: repurpose `round` as a **monotonic per-day
   utterance index** so recency windows have a key; update the formatter and `.round` consumers.
5. **Ping-pong in Phase 0 has no real terminator except the cap.** §3.8's guard is the *novelty
   gate* = Phase 2. In Phase 0, mutual accusations re-trigger each other; only debt (slows) + the
   hard cap (stops) bound it. Acceptable (cap backstops), but "natural convergence" is really a
   Phase 2 property — Phase 0 adversarial days will tend to run to the cap.

### Proposed Phase 0 shape (concrete)

- `Agents/discussion/scheduler.py` — `RUN_DISCUSSION` loop: recompute pressure → eligibility →
  tiered pick → dispatch existing pipeline → append → repeat until convergence or cap.
- `PressureCalculator` + `DebtTracker` over `day_channel`, keyed on the (repurposed) utterance
  index — fed by structured speech-act fields if amendment #2 is accepted.
- `EligibilityGate`: Rule 2 (defend new accusation), round-1/day-start reveal, pressure-rank
  threshold.
- Generation-prompt edit: drop `DISCUSSION_SILENCE_RULE`'s `return null` gate from `common.py`/
  `prompts/day.py`; keep content discipline; pass firing reason as `brief`. Add speech-act fields
  to `DayDiscussOutput`.
- Day graph: replace the 4-node fan-out with the single `RUN_DISCUSSION` node. **Leave voting alone.**

## Open decisions for Phase 0 (resolve before building — RESUME HERE)

1. **Folder name** — this folder is currently `agent_speaking/`; considered alternative
   `sequential_discussion/` (the defining change is the sequential scheduler). Rename is trivial.
2. **Pressure inputs** — accept amendment #2 (structured speech-act fields from the generator) vs.
   the plan's free-text keyword matching. *Recommendation: speech-act fields.*
3. **Phase 0 seeding** — add a deterministic per-day opener seed vs. accept short reactive Day-2+
   discussions as the trigger-signal for Phase 2. *Recommendation: minimal day-start seed (cheap
   insurance against dead discussions).*

(Recommendations above are the assistant's; not yet confirmed with the user. Continuing afresh next session.)
