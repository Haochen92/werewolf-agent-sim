# Sequential Day Discussion (Agent Speaking Coherence)

> **⏩ READING GUIDE / CURRENT STATE (updated 2026-06-01). Start here if picking this up fresh.**
> Goal: replace the concurrent (everyone-speaks-once-per-round, generated in parallel against a
> frozen transcript) day-discussion model with a **sequential, scheduler-driven** one, so the
> conversation reads naturally (turn-taking, adjacency, tapering) while fairness is enforced only
> at the vote. Full design + phased build plan is in **`plan.md`** (verbatim from the design
> discussion). This log records (1) a grounding pass over the current codebase, (2) the analysis
> of the plan against that code, and (3) a **point-by-point review** that locks each design tension
> before moving on.
>
> **Process:** we walked the five tensions one at a time, locking each. **ALL 5 POINTS LOCKED +
> BOTH load-bearing LLM mechanisms smoke-tested (2026-06-01) — Phase 0 design VALIDATED & CLOSED.**
> Speech-acts: 100% valid, beats string-match (smoke test 1). Novelty labels: 100% clean separation
> at the extremes (smoke test 2). See **"Locked decisions"**, the two **smoke-test** sections, and
> **"Phase 0 — DESIGN VALIDATED & CLOSED"** near the bottom; those *supersede* the earlier "tensions"
> / "Proposed Phase 0 shape" trail. **Status: design done & de-risked, no implementation started.**
> Next: **build Phase 0 on a feature branch**, carrying build-time residuals (speech-act accusation
> over-labeling; novelty borderline calibration; both at temp-1.0/folded). Resume at "Phase 0 —
> DESIGN VALIDATED & CLOSED".

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

> ⚠️ **Partially superseded by "Locked decisions" (Point 1).** The single opaque `RUN_DISCUSSION`
> while-loop node below was replaced by a *self-looping subgraph* (per-utterance node boundaries);
> "repurpose `round`" was rejected (add `seq` instead); the generation-prompt gate removal is
> nuanced (only the `return null` is removed, the situation-summary novelty gate stays and moves
> into Phase 0). Read the Locked section for the current design.

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

## Locked decisions — point-by-point review (2026-06-01)

Walking the five tensions one at a time, locking each before moving on. **Point 1 (graph
architecture)** and the **silence-gate/novelty** question under it are locked below. Points 2–5
pending — next is **Point 2 (speech-act fields)**.

### Point 1 — graph architecture: self-looping scheduler, NOT a single opaque node

*Supersedes old "tension #1" and the single-`RUN_DISCUSSION`-node idea in "Proposed Phase 0 shape".*

- **Self-looping subgraph**, not one opaque while-loop node. Topology:
  `SCHEDULE (new node) → [route_speaker conditional] → exactly one of
  {villager,healer,wolf,investigator}_discuss (single Send) → back to SCHEDULE`; `route_speaker`
  routes to `SUMMARIZE_DAY_DISCUSSION` on terminate. **Voting nodes unchanged.**
- **Why self-looping, not opaque node:** a LangGraph checkpointer snapshots at *node boundaries*.
  One opaque node = whole-discussion granularity → mid-discussion reconnect and per-utterance
  `.stream()` would need hand-rolled persistence/emission, and `interrupt()` inside a looping node
  re-executes side effects on resume. Per-utterance nodes give durable reconnect, per-utterance
  streaming, and clean `interrupt()` at boundaries — all **drop-in later, no redesign**. Grounding
  confirmed the codebase currently uses `.invoke()` only (no `.stream()`, no `interrupt()`, no
  checkpointer — only a vector `store`), so nothing breaks now and the door stays open.
- **Scheduler is stateless between turns.** Pressure / debt / quiet-nudge are pure functions of the
  accumulated `day_channel` (+ speech-act fields). The checkpointed transcript fully determines the
  next speaker → resume = reload transcript, recompute, continue. Seeded-random tiebreak must seed
  off a stable key (e.g. `(game_id, day, seq)`) for reproducible resume.
- **Reuse / low blast radius:** the conditional edge emits a **single `Send`** to the existing role
  node (Send works for one target). Existing `villager_discuss`/… wrappers + per-speaker payload
  construction reused verbatim — send one instead of N. `SCHEDULE` writes `{next_speaker,
  firing_reason}`; role node reads via the Send payload.
- **Keep role nodes (not a generic node).** Role prompts stay role-specific either way; the choice
  is only graph topology + Langfuse span naming. Role nodes are *lower* blast radius (reuse
  wrappers) and give role-labeled spans.
- **Dynamic, not static round-robin.** Re-rank after every utterance; terminate on convergence/cap.
  Some agents speak many times, some zero. "Everyone exactly once" is explicitly NOT a goal (the
  day-start seed is the only place openers are deliberately primed).
- **`round` as control flow → gone**; loop uses a monotonic `seq` counter + eligibility recompute.
  (The `round` *field* itself is **dropped** — see Point 4 below.)
- **Feature branch.** Do the whole redesign on a branch off `main`; incremental commits inside it
  (schema → scheduler → graph rewiring → prompt edits) so it can be kept/dropped as a unit and
  steps stay revertable. Revertability comes from commit hygiene, not the commit message.

### Silence gate / novelty (resolved under Point 1 — ⚠️ SUPERSEDED 2026-06-02 by Smoke test 4)

> The "keep the situation-summary novelty gate" decision below was **falsified** when we tested the
> folded config (Smoke test 4): self-judged novelty doesn't discriminate. The novelty gate is
> **dropped**; silence is now deterministic (reactive obligations + budget-capped ranked proactive).
> Read Smoke test 4 for the replacement. The text below is kept as the reasoning trail.

- **Two gates, only one removed.** (1) Upstream **novelty gate** driven by the situation summary's
  emitted labels (`already-said` / `borderline` / `new`) — **KEPT**; it decides whether the agent
  speaks. (2) The `return message=null` instruction in the **generation** prompt — **REMOVED**
  (redundant double self-judgment after the decision is already made upstream). "Remove the gate"
  in plan §3.5 means only (2).
- **Novelty gate pulled into Phase 0** (was Phase 2 in the plan). It is fundamental to how speaking
  is decided, not an optional add-on. This also **dissolves the under-talking risk (old tension
  #3)** — there is a proactive path from day one.
- **Gate applies to proactive candidates only.** Pressure-driven speakers (Rule 2 —
  questioned/accused) bypass it and always speak. This keeps `SCHEDULE` deterministic/LLM-free; the
  situation-summary + novelty check live inside the speaker node, which for a proactive candidate
  may return *silent* and flag itself so `SCHEDULE` doesn't immediately re-pick it until the
  transcript advances.
- **Phase 0 novelty mechanism = LLM labels as currently designed** — folded into the situation
  summary, computed against the transcript (so it sees raw dialogue). **No bi-encoder in Phase 0**
  (avoids a second blind spot + another free parameter that would confound scheduler tuning).

### Deferred (write-down now, build post-sequential)

- **Encoder-based novelty gate** as a cheaper cross-check / eventual replacement for the LLM labels:
  tune a dedicated **observer cross-encoder** + a **strategy_points (situation-to-situation)
  encoder** under fine-tuning project 2, repurposing the reranker's situation-to-situation
  strategy_points relabelling. Rationale: barely-distinguishable situation → same retrieval → same
  action ≈ "nothing new."
  - **Caveat its eval MUST check:** summary-vs-prior-summary similarity is **lossy** — novelty can
    live in a dialogue nuance the situation summary dropped, which the agent itself would act on. So
    encoder-similarity risks **false `already-said`**. The LLM labels see the transcript directly,
    so they don't share this blind spot. Eval question: does encoder-similarity produce false
    `already-said` relative to the transcript-aware LLM labels?
  - Use a **bi-encoder / embedding cosine** for the sim-sim comparison — NOT the current reranker CE
    as-is (trained for situation→strategy *relevance*, wrong objective). The **dedup classifier is
    NOT the reuse target** (D/K-bias; it compares situation+action / whole-context for auto-dedup —
    different granularity).

## Smoke test — flash-lite speech-act capability (2026-06-01)

Ran to decide Point 2: model-emitted tiered speech-acts vs. plain string matching. Script:
`smoke_act_fields.py`; per-case rows: `smoke_act_results.jsonl` (both colocated here).

**Method.** Replayed the production `day_discussion` chain (Vertex flash-lite, temp 1.0) on 30 frozen
`phase1_adoption_v2` cases with `visible_discussion >= 2` (so there's context to address), under 3
output schemas: **baseline** `DayDiscussOutput`, **flat** (+`act` enum), **nested**
(+`addressed: list[{target, act}]`). Auto-metrics: structured-output validity; nested target
self-consistency (model `addressed` vs `[Pp]layer\s*_?\d+` regex on its own message); flat model-act
vs a "?"/keyword heuristic act. Plus a manual read of all act disagreements.

**Results.**
- **Validity: 30/30 (100%) in ALL three conditions** — incl. nested object-list. The flash-lite
  nested-object fear was unfounded; validity does not constrain schema shape. (n=30, temp 1.0,
  one sample each — confirm at scale, but 90/90 is strong.)
- **Targets: 27/27 addressed targets grounded in the model's own message, 0 hallucinated.** Model
  self-report ≈ regex reliability, and can catch indirect/role refs regex misses → regex demoted to
  a cross-check, not the source.
- **Act: model beats string-matching decisively.** 63% agreement with the heuristic, but **all 11
  disagreements favored the model** (manual read; not a blind judge): heuristic systematically
  under-reads accusations — accusatory questions ("…why did you defend a wolf?") it files as
  `question`; keyword-missed accusations ("…you keep trying to pivot…") it files as `reference`.
  Both errors are the costly direction for tiering (under-pressuring the accused). Model act dist
  {accusation 19, question 6, none 5}; heuristic {question 11, accusation 8, reference 6, none 5}.

**Decision → Point 2 (LOCKED 2026-06-01 — ⚠️ SUPERSEDED 2026-06-02 by the 2-D revision below).**
Adopt **model-emitted `addressed: list[{target, act}]`** (nested, all-required, `act` enum incl.
`none`), folded into the generation call (zero added cost). Reject pure string-match (mislabels
intent ~1/3 of the time, systematically). Regex kept only as an eval-time consistency monitor.
Ping-pong damping: dedupe pressure by `(speaker→target, act)` within window. Human messages still
need extraction (Phase 1). **Residuals to validate at scale:** accusation over-labeling (model never
used `reference`, 19/30 accusation — needs a blind-judged larger sample); validity at larger N;
indirect-reference handling. → *The accusation-over-labeling residual turned out to be the headline
finding: the 1-D enum is structurally lossy. See the revision.*

## Smoke test 1b — 1-D `act` is lossy → **2-D `(form, stance)` (REVISED, LOCKED 2026-06-02)**

Re-opened Point 2 on a build-time question (is a 4-way `act` enum too subtle?) and a content audit
the original run hadn't done: reading each message *against* its label, not just the label
distribution. Scripts/results colocated: `smoke_act_2d.py` + `smoke_act_2d_results.jsonl`,
`smoke_act_2d_distribution.py` + `smoke_act_2d_distribution_results.jsonl`.

**Finding 1 — the 1-D label is *under-determined*, not inaccurate.** Reading the 25 nested messages
against their labels: nearly every werewolf utterance is *simultaneously* a question (by form) and an
accusation (by stance) — e.g. "Player 1, why are you burying the voting record? That's what a wolf
would do." Forcing one `act` makes the model coin-flip on *which true aspect* to report (hence the
~even 13 question / 12 accusation split, and `reference` only ever on the *secondary* target). `act`
collapses two orthogonal axes. This is why the "accusation over-labeling" residual appeared.

**Finding 2 — two axes, both reliably emitted.** Decoupled into `address_form ∈
{question, response, mention}` (does it demand a reply?) × `stance ∈
{accusation, defense, agreement, neutral}` (valence). flash-lite self-emit (24 cases): **100% valid,
0 hallucination.** Both axes vary; the joint shows they're independent.

**Finding 3 — stance is NOT accusation-dominated (the tier-1-flood worry).** The first self-emit run
looked all-accusation, but that was a **sampling artifact** — first-24 = an endgame cluster.
Labelling 48 REAL `agent_message`s **stratified across `round`** (71 engagements):

| | values |
|---|---|
| form | mention 41 (58%), question 18 (25%), response 12 (17%) |
| stance | accusation 38 (54%), neutral 20 (28%), defense 9 (13%), agreement 4 (6%) |
| per-round stance arc | r1: neutral 7 / acc 4 / def 1 → r2: neu 7 / acc 9 / agr 3 / def 3 → r3: acc 12 / def 3 / neu 2 → r4: acc 13 / neu 4 / def 2 / agr 1 |

Discussion **opens exploratory (mention×neutral), heats into a hunt** — matching the P3 "day-start
has no pressure" lock. Joint dist (independence proof): mention×neutral 19, question×accusation 17,
mention×accusation 11, response×accusation 10, mention×defense 8, mention×agreement 3,
question×neutral 1, response×defense 1, response×agreement 1. Labels eyeball as accurate
("rally around player_1"→mention/defense; "I agree with player_8"→mention/agreement).

**Tier-1 flood resolved.** tier-1 = `form==question OR stance==accusation` = union **≈ 39/71 (55%)**,
NOT everyone; the other **~45% are low-pressure mentions** (`mention` × {neutral, defense, agreement})
that must *not* force a turn. The fields genuinely discriminate; the flood only appears if you sample
endgame, which is *supposed* to be a hunt.

**Decision → Point 2 REVISED (LOCKED 2026-06-02).** Replace the 1-D `act` with **two fields**:
```
AddressedTarget { target: str,
                  address_form: 'question' | 'response' | 'mention',          # scheduler-primary
                  stance:       'accusation' | 'defense' | 'agreement' | 'neutral' }  # brief + tracing
```
All-required; `addressed: list[AddressedTarget]` required (empty list = addressed nobody; **no
`none`**, the old enum value is dropped). Folded into the generation call (zero added cost). Regex
stays an eval-time cross-check only. **Scheduler mapping (feeds Stage 2):** tier-1 (owes a turn) =
`form==question` ∨ `stance==accusation`; **discharge** (closes a loop → debt relief / freshness) =
`form==response`; **low-pressure** (no forced turn) = `form==mention` ∧ `stance ∈ {neutral, defense,
agreement}`. **Freshness dedup keys on `(speaker→target, stance)` — form EXCLUDED** (the axes aren't
orthogonal: a re-accusation rephrased statement→question must not read as "fresh"; questions create
fresh response-obligation per ask, their looping bounded by per-pair max-K + global cap, not freshness).
`stance` is scheduler-secondary (accusation→"defend" brief; agreement≈neutral for obligation) but
kept for the firing-reason brief + coalition/defense **tracing**. **Residuals:** at-scale validity of the 2-field structure;
`response`/`mention` rare in endgame slices (well-represented early); same blind-judge-at-scale caveat.

## Smoke test 2 — flash-lite novelty-label capability (2026-06-01)

Validates the OTHER load-bearing Phase-0 LLM mechanism (the novelty gate carries the proactive path,
seeding, and redundancy-collapse). Script: `smoke_novelty.py`; rows: `smoke_novelty_results.jsonl`.

**v1 was confounded — and the confound was instructive.** First design judged a real (longest)
transcript message as "new vs the full transcript that contains it," expecting `already_said`; got
65%. Inspection showed the model was *right*: long messages are multi-point ("repeats the save
sentiment **but** introduces a new angle: who targeted player_2"), and the gate's job is "does this
add anything new," not "is this text present." So labeling restate-plus-new-angle `new` is correct.
Lesson: the clean test is *generated* candidates with polar ground truth.

**v2 method.** flash-lite (Vertex, **temp 0** = capability ceiling) on 20 transcripts (≥5 non-gm
msgs). Two generated probes, conditioned on the real transcript: **pure restatement** (agree/restate
an existing point, add nothing → GT `already_said`) and **genuinely new** (introduce a suspicion/
observation absent from the discussion → GT `new`).

**v2 results — clean separation, both directions:**
- pure restatement → `already_said`: **20/20 (100%), 0 false-new** (no redundancy leaks)
- genuinely new → `new`: **20/20 (100%), 0 false-already_said** (no over-suppression)

**Verdict → novelty gate GREEN for Phase 0** on the must-not-fail directions. **Caveats / build-time
residuals (NOT design blockers):** (1) **borderline untested** — model used `borderline` 0× because
candidates were polar; the restate-plus-marginal-angle middle (the reason for 3 levels) and its
calibration remain open; (2) **permissive lean** — v1 shows errors go toward `new` (let people speak
→ redundancy-leak, bounded by speaker cap + debt), not toward silence; (3) **temp-0 ceiling +
standalone-vs-folded** — production folds labels into the situation-summary call at game temp 1.0;
real reliability ≤ this, needs a folded check at build.

## Smoke test 3 — temp 0 vs temp 1.0 for the novelty gate (2026-06-01)

Question raised: should the situation summary (which will carry the folded novelty labels) run at
temp 0? Test: candidates fixed (generated at temp 0), each judged at temp 0 (1 sample) and temp 1.0
(k=3) to measure accuracy **and** label instability. Script: `smoke_novelty_temp.py`; rows:
`smoke_novelty_temp_results.jsonl`.

**Result: temp made NO difference.** Both probes: temp0 20/20, temp1 majority 20/20, temp1 per-sample
60/60, **temp1 instability 0/20 flips**. flash-lite is confident enough that temp 1.0 doesn't perturb
the label.

**Decision: do NOT change the summary temp.** (a) My a-priori "classification calibrates better at
low temp" isn't supported — there's no instability to fix; (b) this **closes the folded/temp-1.0
residual** — the gate is reliable at *production* temp 1.0 on clear cases, so no temp change is needed
for Phase 0; (c) temp would only matter on *borderline* cases (untested, and they route to the cap
anyway); (d) the real low-temp argument was always the free-text **RAG query** stability, NOT the
labels — that's a separate untested question, not blocking, and not worth churning the retrieval
distribution speculatively. **Keep summary at game temp; generation stays at game temp too.**

## Smoke test 4 — folded novelty gate FAILS → silence-rule REDESIGN (2026-06-02)

The biggest design change of the workstream. Smoke tests 2–3 validated the novelty label as a
**standalone judge** (fixed external candidate, disinterested). The silence-gate lock then assumed we
could **fold** that label into the situation-summary call (zero extra cost) and gate proactive speech
on it. Before building Stage 3 we tested the *folded* config — the actual production shape — and it
does not hold. Scripts/results colocated: `smoke_situation_novelty.py` +
`smoke_situation_novelty_results.jsonl`.

**What we tested.** (1) **Drift** — old schema (situations only) vs new schema (situations + novelty),
same cases, temp 0 to isolate the schema effect, with old-vs-old @temp 1.0 as the sampling-noise
floor. (2) **Novelty accuracy** — a paired A/B per case: `NEW` = transcript as-is (the agent's point is
fresh); `REPEATED` = inject a *paraphrase* of the agent's real message attributed to another player
(their point is now on the table). A working gate shifts the label toward `repeated` when injected.

**Results.**
- **Drift:** old-vs-new @temp0 cosine **0.976** (min 0.962) vs old-vs-old @temp1 floor **0.997**.
  Adding the fields perturbs the situations *slightly more than sampling noise* — substantively fine,
  but not free.
- **Variant A — situation-anchored (the locked schema):** `NEW` → repeated 10 / new 2; `REPEATED` →
  repeated 11 / new 1; injection shift **1/12**. It labels ~everything `repeated` regardless of
  freshness — because it judges the **situation recap**, and a mid-game recap is definitionally "a
  continuation of the established discussion" (the model's own reasoning). Would silence almost
  everyone.
- **Variant B — contribution-anchored (a `intended_contribution` draft field, hypothesis fix):**
  `NEW` → new 12/12; `REPEATED` → new 12/12; shift **0/12**. Fails the *opposite* way — when the agent
  both **picks** its contribution and **judges** its novelty, it is optimistically sure its own point
  is new, even with a paraphrase of it sitting in the transcript.

**Diagnosis.** Self-judged novelty is biased in both framings (state-recap pessimism / self-authorship
optimism). The standalone smoke worked only because the candidate was **fixed + external** and the
judge **disinterested**. Folding the judgment into the agent's own generation destroys that.

**Candidate solutions evaluated.**
1. *Folded self-label* (the locked design) — **broken** (above). 0 extra calls but useless.
2. *Per-turn disinterested judge on a folded draft* — draft rides the situation summary (free); a
   separate small judge call rates it. +1 *cheap* call per proactive candidate, partly self-funding
   (silencing skips the generation call). No staleness. Untested.
3. *Two-list / wave batch + disinterested judge* (the double-buffer idea) — one judge per wave + cross-
   candidate dedup, but needs draft calls at swap (live situations run later) and adds bounded
   staleness. Real payoff is dedup, not cost.
4. *Embedding similarity on a folded draft* — embed the 1-line draft, cosine vs transcript (embeddings
   already computed for retrieval). **0 extra LLM calls**, disinterested by geometry. The deferred
   encoder plan, as a simple threshold. Untested.
5. *No novelty detection at all — ranked-heuristic proactive opportunity* (CHOSEN). Reframe:
   **reactive = message-created obligation; proactive = scheduler-created opportunity.** Proactive
   candidates do **not** prove novelty; we just cap the number of opportunities and rank by cheap
   deterministic signals.

**DECISION (LOCKED 2026-06-02) — drop the novelty gate; adopt #5.** It sidesteps all three problems at
once (broken self-novelty, call cost, staleness) by removing the mechanism that caused them, and trades
"prove novelty" for "limit opportunities + cheap ranking." Concretely:
- **Reactive path** — deterministic queue of *undischarged* obligations over a window: addressed with
  `form==question` → owes an answer; `stance==accusation` → owes a defense. Cleared when answered
  (`form==response` toward the asker). No LLM.
- **Proactive path** — fires **only when the reactive queue is empty** (a quiet cycle), budget-capped
  (Phase 0 = **1**), candidate ranked by three cheap deterministic heuristics: (a) **has unrevealed
  private info** (heavy weight, *not* a strict first-sort — a guaranteed slot would be a power-role
  tell, see P3), (b) **hasn't spoken recently** (the locked `DebtTracker`), (c) **suspicion-graph
  centrality among players NOT already in the reactive queue** (uses the locked `addressed_targets`
  edges; restrict to non-targeted to avoid double-counting reactive). Seeded-random tiebreak.
- **Load-bearing dependency:** the anti-ping-pong caps (per-pair-K + freshness) are what guarantee the
  reactive queue *drains* so proactive can ever fire — otherwise continuous accusations starve it.
- **Drop** the `novelty`/`novelty_reasoning` fields from `SituationSummary`. Situation summary +
  generation stay **live per-turn** (no staleness).

**Virtue:** Phase 0 now has **no fragile LLM mechanism left to validate** — reactive and proactive are
both deterministic, unit-testable in Stage 2. We removed the one piece we couldn't make reliable.

**Future refinements (deferred, add only if run logs show proactive redundancy the budget+content-
discipline didn't contain):** embedding-similarity novelty (#4, 0 extra calls — the natural first add);
then the heavier deferred heuristics (stance-vs-majority, strategy-profile "push", info-value); and
cross-candidate dedup via the wave/batch judge (#3) if two agents pile the same point. The standalone
novelty label (smokes 2–3) remains valid as a *disinterested external* judge — it's only the *folded
self-judgment* that failed, so it could return in form #2/#3 later.

## Phase 0 — DESIGN VALIDATED & CLOSED (2026-06-01; novelty gate REVISED 2026-06-02 — see Smoke 4)

> **Build from `phase0_build_checklist.md`** — the consolidated, dependency-ordered build sequence
> (Stage 0 branch → 1 schema → 2 scheduler primitives incl. proactive ranking → 4 graph rewiring →
> 5 prompts → 6 termination; **Stage 3 novelty gate is REMOVED — see Smoke 4**), each with touchpoints
> + acceptance criteria. Remaining ⚠️ CONFIRM
> build-time details: role-node gating flag (proactive vs reactive). (Message nullability
> RESOLVED 2026-06-02 → `message: str` required. Point 2 speech-acts REVISED to 2-D — see smoke 1b.)

All 5 tensions locked. Smoke tests (4 runs): speech-acts 100% valid + beats string-match (revised to
2-D, smoke 1b); standalone novelty 100% clean separation + temp-robust (smokes 2–3); **but the
*folded* novelty gate FAILED (smoke 4) → the silence rule was redesigned: no novelty detection,
deterministic reactive obligations + budget-capped ranked proactive opportunity (see Smoke test 4).**
Phase 0 is design-complete and — after dropping the folded gate — has **no fragile LLM mechanism left
to validate**; reactive + proactive are both deterministic. Build it on the feature branch. Remaining
build-time residuals (NOT design blockers): speech-act accusation over-labeling at scale (resolved by
2-D, watch validity@scale); **proactive redundancy** — OBSERVE in runs; if the budget-cap +
content-discipline don't contain it, add embedding-similarity novelty (smoke 4 future refinement #4,
0 extra calls). Optional free-text RAG-query stability vs temp (separate, not blocking). Summary &
generation both stay at game temp (smoke test 3).

### After Phase 0 (roadmap map)

**Within this workstream** (plan §4.4, re-mapped since novelty moved into Phase 0):
1. **Build Phase 0** on the feature branch (schema → scheduler → graph rewiring → prompt edits).
2. **Discussion-quality gate** — the go/no-go: does sequential read better than concurrent
   (turn-taking, adjacency, less redundancy, tapering) + how much is generation reduced? Method =
   **worktree-on-tag**, NOT a config flag (concurrent is structurally divergent + won't survive to
   production — see versioning policy in CLAUDE.md / [[reference-variant-versioning-policy]]): tag the
   pre-merge concurrent baseline, `git worktree` it, generate fresh games on the same seeds in both,
   then judge both transcript sets with ONE judge (post-hoc) + diff call counts. Fresh-generation A/B,
   not a frozen replay.
3. **Phase 1 — human integration** (floor offers, timers, addressed-signal, pacing) + **human
   speech-act extraction** (the one spot self-report doesn't apply).
4. **Phase 2 — novelty (deferred refinement, only if logs show proactive redundancy)**: embedding-
   similarity novelty (0 extra LLM calls — Smoke 4), then heavier deferred proactive heuristics
   (stance-vs-majority, strategy-push, info-value) + cross-candidate dedup. The folded LLM novelty
   gate is NOT revisited (falsified, Smoke 4).
5. **Phase 3 — voice/persona** (prompting; persona/voice firewall, §5).
6. **Phase 4 — style fine-tune** (optional; only if drift test shows voice decay).

**Within the ship roadmap:** this is **Phase A #1**, goes first, with the discussion-quality gate
before the rest. Closing it unblocks parked Phase A items — **+roles** (Role Set decision is parked
behind this), **consolidated tracing**, **night memory**, **v5 DB** (fold `round→seq` here). Phase A
gates **Phase B** (label-once-on-v5) → **Phase C** (win-rate A/B) → **ship**.

## Open decisions (still to resolve, in review order)

- **Folder name** — currently `agent_speaking/`; alternative `sequential_discussion/`. Cosmetic;
  rename trivial. Not blocking.
- **Point 2 — speech-act fields** — ✅ **LOCKED (REVISED 2026-06-02 to 2-D; see Smoke test 1b).**
  Model-emitted nested `addressed: list[AddressedTarget]`, all-required, `addressed` required (empty
  list = nobody). Each target carries **two** fields: `address_form ∈ {question, response, mention}`
  (scheduler-primary) × `stance ∈ {accusation, defense, agreement, neutral}` (brief + tracing). The
  old 1-D `act` enum (incl. `none`) is **dropped** — it conflated two orthogonal axes and forced a
  lossy coin-flip (audit + stratified real-message distribution proved it). Regex = eval cross-check
  only; ping-pong dedup by `(speaker→target, stance)` (form excluded); human extraction deferred to Phase 1.
  Scheduler mapping: tier-1 = `form==question ∨ stance==accusation`; discharge = `form==response`;
  low-pressure = `form==mention ∧ stance≠accusation`. Residuals: at-scale validity of the 2-field
  structure; blind-judge-at-scale.
- **Point 3 — Phase 0 seeding** — ✅ **LOCKED (2026-06-01).** At day start there is *no* pressure
  (mention-based; on a kill night the named player is dead) — the `game_master` night announcement
  (`nodes.py:504-551`) is the *topic* in-transcript, not a pressure source. The opening is carried
  by the **proactive novelty path** (day-scoped → the first candidate passes the gate naturally),
  plus a **1-utterance forced-opener floor** that bypasses the gate for the day's first utterance,
  to prevent zero-discussion days. Opener chosen **seeded-random**; **investigator-fresh-result is a
  priority *boost*, not a guaranteed first slot** (masks the "first speaker = power role" tell) and
  is still novelty-gated (optional reveal). **No** special pressure injected from the announcement
  or the saved player — the organic loop surfaces focal points. **Most agents may speak zero times
  on a quiet day — intended; "everyone speaks ≥once" is the old flat model and explicitly rejected.**
  Discussion length self-regulates by day eventfulness.
  - **Opener-floor count = 1 for now; escalate to 2–3 IF** the validation hook shows discussions
    dying too fast (1–2 utterances). Other tunables: investigator boost magnitude, proactive cap (1–2/cycle).
  - **Validation hook:** in the first Phase 0 runs, measure *discussion length vs day eventfulness*
    — does it cascade (smoke-test openers were nearly all addressing/accusatory → likely) or die at
    1–2 utterances? That metric drives the 1→2–3 escalation.
- **Point 4 — `round` field handling** — ✅ **LOCKED (2026-06-01). DROP `round`, add `seq`.** Earlier
  hedge ("keep benign for eval-data compat") reversed: the eval data / memory store / tracing that
  `round` is load-bearing for are *themselves* being rebuilt in Phase A (v5 DB, +roles, regenerated
  golds — context-eval already deferred to "label once on v5"), so preserving a vestigial field for
  soon-to-be-regenerated artifacts is cruft.
  - **New schema:** `DayChannel(day, seq, player, message, addressed)`. `seq` = monotonic **per-day**
    utterance index, paired `(day, seq)` mirroring old `(day, round)`, **stored explicitly** (stable
    per-utterance key for the new tracing; reproducible `(game_id, day, seq)` seed for the
    seeded-random opener on resume).
  - **Low-risk to drop:** `round` had no semantic role in a sequential model; legacy frozen sets
    still load (Pydantic v2 ignores unknown fields → old `round` is just dropped, situation cache
    key changes shape = cache miss, not error); other consumers (`StrategyAdoption.round`,
    `EvalResult.round`, batch readers) are being regenerated anyway.
  - **Coordination:** fold `round→seq` into the broader Phase A schema/tracing migration so
    output/log/trace schemas move in one coherent pass. On the sequential branch: change
    `DayChannel` + day-path consumers (formatter, scheduler, termination logic); let
    `StrategyAdoption`/`EvalResult`/tracing ride the v5 migration. **At implementation: enumerate
    every `.round` reader first** so nothing silently breaks.
- **Point 5 — ping-pong / termination** — ✅ **LOCKED (2026-06-01).** Frame: **two paths to the
  floor** — *reactive* (addressed → tier-1, *fresh* triggers only) and *proactive* (novelty-gated,
  capped 1–2/cycle; third-party "I want to weigh in on A-vs-C" lives here, via Rule 1/3 new
  content; pure agreement suppressed by content discipline).
  - **Terminate** on convergence (recompute → no fresh pressure **and** proactive novelty exhausted)
    or global cap.
  - **Ping-pong:** *pure repetition* killed by the freshness check (restated `(speaker→target, act)`
    = no fresh tier-1 trigger). *Genuine escalation* (new angle each time) is **NOT** bounded by debt
    — **correcting an earlier error: debt is barred from demoting out of tier-1, so it cannot stop a
    mutual back-and-forth.** The only deterministic lever is a **per-pair max-K re-engagement cap**
    (≈2, tunable): after K `(A→B)` re-triggers in the window, further mutual triggers stop creating
    tier-1, letting quiet-nudge rotate the floor. Global cap is the final backstop.
  - **Reconciles tier-1 inviolability:** "always answer a direct question" = answer a *fresh* address
    **once**, not the same opponent infinitely; ≥K re-engagements yield the floor.
  - Deferred to Phase 2: thread-relevance weighting of proactive-candidate selection if third-party
    interventions get under-surfaced.
  - Tunables (all later): per-pair K, global cap, recency window, debt magnitude, quiet-nudge.

## Phase 0 design — COMPLETE (2026-06-01); remaining = build tasks + one validation

All 5 architectural tensions locked (Points 1–5 above) plus the two-gate/novelty decisions. What
remains is **not open design** — it's implementation spec (flows directly from the locks) and
parameter tuning (explicitly deferred):

- **Build-spec tasks** (follow from decisions, no new decision needed): exact generation-prompt edits
  (drop `DISCUSSION_SILENCE_RULE` null-return, keep content discipline, consume `brief`); add
  speech-act fields to `DayDiscussOutput`; `DayChannel` `round→seq` + day-path consumers; the
  `SCHEDULE` node + `route_speaker` single-`Send` wiring; PressureCalculator / DebtTracker /
  EligibilityGate as pure functions of the transcript; per-turn score function (strict tiers,
  random breaks ties within a tier); firing-reason brief wording.
- **⚠️ One validation gap before build:** we smoke-tested **speech-act** reliability but **NOT** the
  **novelty-label** reliability (already-said / borderline / new) that the proactive path + seeding +
  redundancy-collapse now depend on (the gate was pulled into Phase 0). The plan *asserts* weak
  models are reliable at this grounded reading task, but it's unvalidated. **Recommend a parallel
  novelty-label smoke test** (same frozen-context approach) before committing it as load-bearing.
- **Sequencing:** feature branch off `main`; incremental commits (schema → scheduler → graph
  rewiring → prompt edits). Fold `round→seq` output/trace-schema changes into the broader Phase A
  v5 migration.

## Stage 2 design pass — selection model reconciliation + queue data shape (2026-06-03)

Pre-build alignment for the scheduler primitives. Stage 1 schema + downstream integration are committed
(feature-branch, 5 commits, `concurrent-baseline` tag @ d7415d0); this pass settles *how* the pure-fn
scheduler selects a speaker before any code. No LLM, no smoke test needed — this is logic, unit-testable
in Stage 2. Two things resolved: (1) which selection model, (2) the queue's data shape.

### Decision: reactive/proactive model (drop the vestigial weighted score)

The checklist carried **two** selection models layered from two eras, and they're incompatible as
written: an **old unified weighted score** (`pressure + intent − debt + quiet_nudge + seeded_random`,
strict tiers, pick max — predates Smoke 4) and the **Smoke-4 reactive/proactive** model (a deterministic
obligation queue that bypasses scoring; proactive ranking only on quiet cycles). The weighted score is a
**vestige** — once Smoke 4 made reactive obligations a hard gate, a blended per-agent score has nothing
left to do (you owe a turn or you don't; the `intent` term never had a source). Comparison on the four
axes that matter here:

| Axis | Weighted score | Reactive/proactive (CHOSEN) |
|---|---|---|
| Natural-sounding | Weaker — a direct question can hang unanswered if another agent out-scores the addressee → reads as people talking past each other. | **Stronger** — encodes turn-taking "adjacency pairs" (question→answer, accusation→defense are near-obligatory); being addressed forces you to the front. |
| Dynamic strategy on latest state | Fully dynamic | **Identical** — both recompute from `day_channel` each turn; the agent's situation/reasoning is generated at **dispatch time** in both. This axis does **not** differentiate. |
| LLM cost | — | **Identical — zero.** Both are pure functions over the transcript; the only call is the chosen speaker's generation. Total-utterance count (hence cost) is a function of the **termination rule**, not the selection model. |
| Other | Tuning hell (interacting weights); "why did X speak?" = "the sum"; cannot *guarantee* a question is answered; hard to unit-test. | More rigid (proactive rationed to budget/quiet-cycle) — but that rationing **is** the feature, and it's explainable + unit-testable. |

**LOCKED: reactive/proactive.** It wins on naturalness + testability, ties on dynamism + cost; its only
"cost" (rationed proactive creativity) is the mechanism that stops everyone speaking at once. The unified
weighted score and the `intent` term are **dropped**. This also collapses the primitive set — there is no
single blended score; selection is (a) an obligation queue + (b) a proactive ranking run only when the
queue is empty.

### Queue data shape (resolved here; dictates the Stage-2 types)

1. **Obligations are per-`addressed_target`, not per-message.** A `DayChannel` carries a *list* of
   targets, so one message both **discharges** and **creates**: e.g. B's reply `[{A, response, defense},
   {C, mention, accusation}]` clears B's debt to A *and* puts C on the hook. We iterate targets; each one
   independently discharges (`addressed_form==response` toward someone the speaker owed) or creates
   (`question`→owes-answer, `accusation`→owes-defense). This per-target rule **is** the ping-pong engine
   (a "response" that counter-accuses keeps the thread alive) — intended; bounded by freshness + K.
2. **The reactive queue is keyed by the *obligated agent*, obligations grouped.** B appears **once**,
   carrying the set `owes=[{from:A,kind:answer},{from:C,kind:answer}]`. When B is scheduled the
   `firing_reason` brief is *"A and C both questioned you — address them"* → **B answers both in one
   turn**, discharging all open obligations toward the people he addresses. Grouping doubles as natural
   dedup (no N separate turns for N accusers).
3. **Empty `addressed_targets` = inert for scheduling.** "Anyone have clues?" / an opening read addresses
   nobody → creates **no** obligation (a room-question shouldn't force one specific answerer — that would
   flood). It's a valid proactive/broadcast utterance; if nobody bites it dies, like a rhetorical
   question. No schema change. The proactive "lane" is **not** a pre-populated queue — when the reactive
   queue is empty the selector ranks all eligible non-owing agents **on demand** and takes the top 1.
4. **Stateless = one transcript pass scores *all* agents (not N per-agent scans).** Each SCHEDULE cycle
   does a single `O(messages)` pass over today's `day_channel` that simultaneously fills, for every
   agent, `last_spoke_seq` (→ recency = `current_seq − last_spoke_seq`, ∞ if silent) and the obligation
   set. ~9 players × ~25 msgs = microseconds, zero LLM. "Stateless" means *derive the whole picture from
   the transcript each cycle*, not *one agent at a time* — there is no mutable per-turn counter dict to
   desync on resume. Fully assertable in unit tests with hand-built transcripts.

### Confirmed sub-decisions

- **Proactive ranking = recency + private-info weight + small seeded-random tiebreak.** Private-info is a
  *weight*, never a strict first-sort (a guaranteed slot is a power-role tell — P3). **Centrality
  (accusation-graph in-degree) is DROPPED for Phase 0** — most abstract of the three signals, mild
  over-engineering for a first cut. *Future refinement:* if run logs show proactive picks wandering off
  the live controversy, add accusation-graph centrality among non-reactive players.
- **K=2 is per *directed pair* (A→B), not per agent** — bounds total A→B re-engagements in the window;
  a hot A↔B feud re-engages ~2 rounds each way, then freshness + K starve it and proactive takes over.
- **Same accusation, different angle — handled by freshness, not K.** The freshness key
  `(speaker→target, stance)` excludes `addressed_form` *and wording* → a rephrased re-accusation has the
  **same key** → creates **no fresh obligation** → the target is not forced to re-defend, *by
  construction* (the angle is irrelevant because the key ignores content). K=2 is the harder backstop.
  **Honest residual:** freshness stops a repeat from *obligating* anyone, but can't stop an agent from
  being *proactively* picked and choosing to restate — that leak is owned by the content-discipline
  prompt now, and by the deferred embedding-novelty (0 extra calls, Smoke 4 #4) later if logs show it.
- **Silence rule, restated post-Smoke-4:** silence is now **structural, not self-selected** — if the
  scheduler doesn't pick you, that's your silence (most agents speak 0× on a quiet day — P3, intended).
  When a role node runs, the agent **always** speaks (`message: str`, no null). Split cleanly into two
  deterministic non-LLM pieces: *who speaks* = scheduler; *quality of what they say* = the
  content-discipline prompt (kept; only the `return null` instruction is removed in Stage 5).

**Net:** the Stage-2 primitives are now (1) `build_reactive_queue` (per-target discharge/create, grouped
by obligated agent, freshness + per-pair-K), (2) `speech_recency` (derived, feeds proactive only),
(3) `rank_proactive` (recency + private-info + seeded random), (4) `select_next` (reactive-first →
budget-1 proactive → opener-floor → terminate). All pure functions of `day_channel`; unit-testable
without any LLM.

### Alternative weighed: "naive sequential round-robin" (rejected for production; kept as an A/B arm)

A simpler midpoint between concurrent and the scheduler surfaced: keep generation **sequential against a
live transcript** (drop `fan_out_day`, loop the existing role nodes), but pick the next speaker by
**fixed seat order**, keep the **existing self-selected silence rule** to thin dialogue, and terminate on
total-dialogue / token cap. No scheduler primitives.

- **What it fixes:** concurrent's worst flaw — the frozen-snapshot redundancy (N agents reacting to the
  same stale transcript → simultaneous duplicate accusations). Live sequential generation removes it, and
  it's cheap to build. This is the bulk of concurrent's quality gap.
- **Order advantage — not eliminated, and mis-axised.** Self-silence lets a seat *yield*, never
  *preempt*: P1 holds right-of-first-refusal every cycle, so low-index seats keep an agenda-setting
  advantage whenever they use it. Worse, it **mis-orders by urgency** — an accused P2 can't respond until
  their slot returns, while un-accused P3..P7 speak first. Priority is keyed on an **arbitrary** axis
  (seat index) where the natural one is conversational relevance. Reactive/proactive replaces seat- with
  relevance-priority and uses seeded-random only for genuine ties.
- **Disqualifier for production:** it **retains the self-selected silence rule — the exact mechanism
  Smoke 4 falsified.** "Do I have something new to add?" *is* the self-judged-novelty call that didn't
  discriminate, so its termination + redundancy control sit on the broken primitive (self-authorship
  optimism → nobody passes → runs to the token cap with filler).
- **Cost:** worst per useful utterance — every seat's turn is an LLM call **even on a pass** (a null is
  still a call), and it can't parallelize. Ranking: reactive/proactive (1 call/utterance, never a
  non-speaker) < concurrent (parallel fan-out) < naive round-robin (wasted pass-calls, serial).
- **Disposition:** rejected as the production model; **kept as an optional third arm in the
  discussion-quality A/B** (worktree-on-tag, like concurrent). It's the clean ablation isolating
  *sequential generation* (concurrent→naive) from *smart scheduling* (naive→reactive/proactive) — if the
  scheduler barely beats naive-sequential there, the complexity isn't paying off.
