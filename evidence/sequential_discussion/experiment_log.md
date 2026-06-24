# Sequential Day Discussion — Build Journey (Phase A #1)

> **What this is.** The chronological record of replacing the **concurrent** day discussion
> (everyone speaks once per round, in parallel against a frozen snapshot) with a **sequential,
> scheduler-driven** one. It runs from the design reasoning through the smoke tests that resolved each
> open sub-question, the build, the live-run tuning, and the acceptance gate that closed Phase A #1.
> Later entries supersede earlier ones; where the design changed, the change is shown *in its place*
> rather than edited away — the point is the journey, including the design that got falsified.
>
> **Companion docs.** The shipped design, stated destination-first, is in [`report.md`](report.md). The
> acceptance study has its own record: [`quality_gate/`](quality_gate/experiment_log.md) (the
> concurrent-vs-sequential acceptance A/B). A generation-prompt cleanup done just after — originally a
> subfolder here — has since been hoisted out as its own concern (see §10). Guiding principle throughout:
> **deterministic where reliable; LLM only where necessary.**
>
> *This log absorbs the earlier `plan.md` (original design doc) and `phase0_build_checklist.md` (build
> trackpad) — both since removed as standalone files (git history preserves them); their content is folded
> into the chronological narrative below.*

---

## 1. Motivation — from parallel to sequential (and why parallel first)

The day discussion must read like a real conversation — proper turn-taking, replies that answer what was
just said, varied participation, natural tapering — while having **no inherent advantage to turn order**,
terminating within a sane cutoff, and (eventually) seating one human player.

Concurrent was the natural first design, and a defensible one — every agent speaks once per round,
generated in parallel against the same frozen snapshot. It was the **simplest to build** (one round, fan
out, no scheduler or per-utterance state), the **fastest** (agents generate concurrently → low latency),
and **fair by construction** (one shared snapshot, revealed together → no turn-order advantage). These
merits are real; the move to sequential trades them deliberately, it does not disown them. *(No design
note records this original rationale — it is reconstructed from the implicit "fair by construction" framing
and the latency cost the sequential design later concedes.)*

The organizing reframe: **fairness and naturalness matter at different moments.** Turn-order *advantage*
only bites at the decision — the vote — not the chatter. So enforce fairness exactly once, at the vote,
and let discussion be sequential and natural everywhere else.

The concurrent model generates every agent's utterance **in parallel against the same frozen transcript
snapshot**, once per round, revealed together. It is fair by construction but robotic, and every failure
traces to the frozen snapshot + simultaneous evaluation — visible in real game logs:

- **Redundant convergence** — N agents reacting to one snapshot produce N near-duplicate takes (six
  players independently "watch who downplays the save").
- **Broken adjacency** — a question in round *r* is answered in *r+1*, after the thread moved on; the
  questioned player can't respond in the round they're attacked.
- **Flat participation** — everyone speaks every round regardless of having anything new.
- **No within-round reactivity** — a dogpiled player can't defend until next round.

Root cause: redundancy is a **cross-agent property** invisible to a per-agent decision made
simultaneously. Three agents each correctly conclude "I have a new accusation" because, at the shared
decision moment, none has spoken yet.

---

## 2. The original design (as first drafted, ~2026-05-31; captured with the grounding pass on 2026-06-01)

The first design doc laid out the architecture below. Several pieces here were **later changed** — the
weighted-score scheduler and the LLM novelty gate especially — and those revisions appear in their
chronological place (§5–§8). Kept as written so the reasoning trail is honest.

**Sequential continuous loop, no rounds.** Rounds existed only to organize simultaneous generation. Once
generation is sequential and scheduling recomputes per utterance, rounds impose an artificial cadence.
Drop them: recompute eligibility/pressure over available agents → pick the top → generate at speak-time
against the running transcript → append → repeat. *Trade-off accepted:* lose parallelism (higher latency),
which for a turn-based game with a human in the loop is acceptable, even desirable (it paces to reading
speed). Speaking-debt and mention-decay become rolling windows; the day-start boost and novelty become
*day*-scoped rather than round-scoped.

**Fairness lives only at the vote.** The vote is simultaneous, blind, and locked — everyone commits
against the frozen transcript without seeing others', revealed at once. This kills the only turn-order
advantage that matters ("the last voter swings the tally"). *Trade-off accepted:* a later discussion
speaker has a turn-to-turn information edge, but it averages out and cannot be cashed in past the locked
vote.

**The scheduler — *originally* a weighted tiered score.** The first design ordered speakers by
`score = pressure + intent − speaking_debt + quiet_nudge + seeded_random`, organized as tiers so
randomness only breaks ties within a tier. Top tier = an unanswered direct question; lower tiers =
accused / referenced / agreed-with / proactive volunteer. A **domination guard** (speaking-debt penalty +
quiet-agent nudge) was to counter the dogpile, with a hard rule that debt must **never** demote an agent
out of the addressed tier. *(This weighted score was dropped in the Stage-2 design pass, §7 — once
reactive obligations became a hard gate, a blended per-agent score had nothing left to do.)*

**The silence mechanism — *originally* an LLM novelty gate.** The plan decomposed four silence rules by
cost: Rule 2 (defend a new accusation) and the round-1 investigator reveal were **deterministic**; Rules
1/3 (a genuinely new observation / a changed suspicion) were **LLM**, folded as the final fields of the
situation-summary call, rated on a coarse 3-level scale (`already-said / borderline / new`), capped to 1–2
proactive candidates per cycle. The savings were to come from the *deterministic* gate silencing most of
the table for free. *(The folded novelty gate was falsified in Smoke 4, §5, and removed; it returned much
later only as a disinterested external judge, §8.)*

**Termination** was to be convergence (recomputed eligible set empties) or a hard cap, with the **novelty
gate as the real ping-pong terminator** (a restated accusation isn't new → suppressed → loop dies). *(With
the novelty gate gone, termination became per-pair K-cap + freshness + trailing-passes, §7.)*

**Human player integration (designed up front, deferred to Phase 1).** Real-time open-mic was rejected
(it would force agents to respond to mid-generation interruptions). Instead: the human can **always
speak** and is **never gated to silence**, sitting in the ordering via the seeded-random factor like any
agent. **Floor offers** — offer the floor (a) after any utterance that addresses them, (b) periodically
every few AI turns, each on a short timer; if they don't engage in the window, the loop proceeds.
**Surface the "directly addressed" signal** prominently (the mirror of the top-tier bump an AI would get,
so the human doesn't miss the cue). **Pacing** — a minimum gap between AI turns (simulated read time), a
cap on AI turns between human opportunities, and hold AI generation while the human is typing if a typing
indicator exists. **Fairness equalizer** — the human's standing information edge in discussion is the
price of a humane UX, neutralized at the blind simultaneous vote they take like everyone else.

**Adjacent decisions, recorded but out of core scope** (these still stand):
- **Persona/voice firewall.** Personas vary *voice* (register, tics, humor), never *disposition*
  (aggression, trust, paranoia) — dispositional traits bias play. Decisions are persona-blind; persona is
  injected only at the realization step; assigned independently of role (no role tell); stable within a
  game.
- **Experience-mode dials** (post-eval): if richer disposition is ever added, use game-relevant behavioral
  dials (aggression, talkativeness, trust-default), **not MBTI**; route tone → realization, argument
  disposition → decision, participation disposition → scheduler params.
- **Fine-tuning** is the strongest lever for *voice* (a model property), not *flow* (solved by this
  architecture); style FT beats prompted-flash on voice/consistency/cost but **not on play**, and only
  pays off as a single decide+write model — kept as a deferred, regression-gated option.

**Open questions flagged at design time** (all later resolved or deferred): the drift test (does prompted
voice decay across a game → decides whether style FT is needed), a fine-tuning regression test, a
ping-pong stress test, threshold tuning, and human-pacing feel.

---

## 3. Grounding the design against the code (2026-05-31)

Mapped the existing concurrent implementation so the deltas were concrete. Key findings that **de-risked**
the build:

- **The vote is already simultaneous + blind** (`fan_out_vote`) — correct for a blind vote; the sequential
  work doesn't touch voting.
- **The per-turn pipeline already exists as a per-agent unit** (`_run_memory_informed_action`: situation
  summary → memory retrieval/rerank → generation). "Run the pipeline only for the selected speaker" is
  mostly *calling this existing function once per popped speaker* instead of fanning out — strong reuse.
- **The human flag is already plumbed** (`human_player`), so later human integration builds on real
  scaffolding.

The real tensions surfaced here: (1) the biggest change is LangGraph fan-out → a sequential loop; (2) the
riskiest deterministic piece is detecting questioned/accused by string-matching free text — brittle
exactly at the strongest signal (an unanswered direct question), which motivated **moving extraction into
a structured speech-act header the generator emits** rather than regex-on-free-text; (3) without a
proactive path the loop could *under*-talk and converge instantly; (4) dropping rounds needs a schema
decision; (5) Phase-0 ping-pong has no real terminator but the cap.

---

## 4. Locking the design — Points 1–5 (2026-06-01)

Walked the five tensions one at a time, locking each.

**Point 1 — graph architecture: a self-looping scheduler subgraph, not one opaque node.** Topology:
`SCHEDULE → [route_speaker] → exactly one role node (single Send) → back to SCHEDULE`; route to
`SUMMARIZE` on terminate; voting untouched. *Why self-looping:* a LangGraph checkpointer snapshots at
node boundaries, so per-utterance nodes give durable reconnect, per-utterance streaming, and clean
`interrupt()` later with no redesign (the codebase uses `.invoke()` only today, so nothing breaks now and
the door stays open). The scheduler is **stateless between turns** — pressure/recency/obligations are pure
functions of the accumulated `day_channel`, so resume = reload transcript + recompute. Seeded-random
tiebreak seeds off a stable key (`game_id, day, seq`). Single-`Send` reuse of the existing role nodes
keeps blast radius low. Whole redesign on a feature branch, incremental commits.

**Point 2 — speech-act fields** (locked, then **revised to 2-D** — see Smoke 1/1b, §5). Model-emitted
structured tags beat string-matching; the final shape is `addressed: list[AddressedTarget]` (all-required,
empty list = addressed nobody), each target carrying `address_form ∈ {question, response, mention}`
(scheduler-primary) × `stance ∈ {accusation, defense, agreement, neutral}` (brief + tracing). Regex kept
only as an eval-time cross-check; human extraction deferred.

**Point 3 — Phase-0 seeding.** At day start there is *no* pressure (the night-killed player is dead; the
GM announcement is the topic, not a pressure source). The opening is carried by the proactive path plus a
small forced-opener floor so a day never has zero discussion. Opener chosen seeded-random;
**investigator-fresh-result is a priority *boost*, not a guaranteed slot** (a guaranteed slot is a
power-role tell). Most agents may speak zero times on a quiet day — intended; "everyone speaks ≥once" is
the rejected flat model.

**Point 4 — drop `round`, add `seq`.** `round` had no semantic role in a sequential model; `seq` is a
monotonic per-day utterance index, stored explicitly (stable per-utterance key + reproducible resume
seed). Legacy frozen sets still load (Pydantic v2 ignores unknown fields). The decision: enumerate every
`.round` reader before cutting; fold the output/trace-schema part into the broader Phase-A migration.

**Point 5 — ping-pong / termination.** Two paths to the floor: *reactive* (addressed → owes a turn, fresh
triggers only) and *proactive* (capped, ranked). Terminate on convergence or global cap. Pure repetition
is killed by a **freshness check** (a restated `(speaker→target, stance)` creates no fresh trigger);
genuine escalation is bounded not by debt but by a **per-pair max-K re-engagement cap** (debt is barred
from demoting out of tier-1, so it *cannot* stop a mutual back-and-forth — corrected here). "Always answer
a direct question" means answer a *fresh* address once, not the same opponent infinitely.

---

## 5. The smoke tests — probing the LLM-dependent pieces (2026-06-01 → 06-02)

Five empirical probes resolved the questions the design couldn't settle by reasoning. The scripts live in
[`scripts/`](scripts/) (`smoke_*.py`), their per-case results in [`data/`](data/) (`smoke_*_results.jsonl`).

**Smoke 1 — speech-act capability (flash-lite, temp 1.0, 30 frozen cases).** Structured-output validity
**30/30 in all three schema shapes** (incl. a nested object-list — the flash-lite nested-object fear was
unfounded); **27/27 addressed targets grounded in the model's own message, 0 hallucinated**; on the act
label the model **beat string-matching decisively** — 63% agreement with a keyword heuristic but **all 11
disagreements favored the model** (the heuristic systematically under-reads accusatory questions as plain
questions). Decision: adopt model-emitted acts; regex demoted to an eval cross-check.

**Smoke 1b — 1-D `act` is lossy → 2-D `(form, stance)` (2026-06-02).** Reading each message *against* its
label (not just the distribution) showed the 1-D act was **under-determined**, not inaccurate: nearly
every werewolf line is *simultaneously* a question (by form) and an accusation (by stance), so forcing one
`act` made the model coin-flip — the source of the earlier "accusation over-labeling" residual. Decoupled
into two orthogonal axes, both reliably emitted (100% valid, 0 hallucination). A worry that stance would
be accusation-flooded turned out to be a **sampling artifact** (the first run sampled an endgame cluster);
labelling 48 real messages **stratified by round** showed discussion *opens exploratory
(mention×neutral) and heats into a hunt*, with tier-1 (`question ∨ accusation`) ≈ 55% — the fields
genuinely discriminate. Freshness dedup keys on `(speaker→target, stance)`, **form excluded** (a reworded
re-accusation must not read as fresh).

**Smoke 2 — standalone novelty label (2026-06-01).** A first design was confounded (judging a real long
message as "new vs the transcript that contains it" — the model was *right* that multi-point messages add
a new angle), which taught the clean test: *generated* candidates with polar ground truth. v2 (temp 0, 20
transcripts, pure-restatement vs genuinely-new probes) gave **clean separation both ways: 20/20 / 20/20,
no redundancy leaks, no over-suppression.** Caveat carried: the `borderline` middle was untested (probes
were polar), and this was a *standalone disinterested* judge, not yet the folded production shape.

**Smoke 3 — temp 0 vs 1.0 for the novelty gate (2026-06-01).** A kept **null result**: temp made **no
difference** (temp0 20/20, temp1 majority 20/20, **0/20 label flips**). flash-lite is confident enough
that temp 1.0 doesn't perturb the label on clear cases. Decision: don't change the summary temp — the
a-priori "low temp calibrates better" wasn't supported, and it closed the folded/temp-1.0 residual for
*clear* cases.

**Smoke 4 — the folded novelty gate FAILS (2026-06-02).** The biggest design change of the workstream.
Smokes 2–3 validated the label as a **standalone disinterested judge**; the locked design assumed we could
**fold** it into the agent's own situation-summary call. Tested in that actual production shape, it does
not hold:
- *Variant A — situation-anchored* (the locked schema): labels **~everything `repeated`** (injection shift
  1/12) — a mid-game recap is definitionally "a continuation of the established discussion," so it would
  silence almost everyone.
- *Variant B — contribution-anchored* (a hypothesis fix): labels **~everything `new`** (shift 0/12) —
  self-authorship optimism; the agent is sure its own point is new even with a paraphrase of it already in
  the transcript.

**Diagnosis:** self-judged novelty is biased in both framings; the standalone smoke worked *only* because
the candidate was fixed + external and the judge disinterested. Folding the judgment into the agent's own
generation destroys both properties. The drift cost was also non-zero (adding the fields perturbed the
situation summary slightly more than sampling noise: cosine 0.976 vs a 0.997 floor).

---

## 6. Silence-rule redesign — drop novelty, go deterministic (2026-06-02)

Five candidate fixes were weighed (folded self-label = broken; per-turn disinterested judge = +1 cheap
call, untested; wave/batch judge = staleness + complexity; embedding similarity on a draft = 0 LLM calls,
untested; **no novelty detection at all** = chosen). The chosen reframe:

> **Reactive = a message created an obligation. Proactive = the scheduler created an opportunity.**
> Proactive candidates do **not** prove novelty; we cap the number of opportunities and rank by cheap
> deterministic signals.

- **Reactive path** — a deterministic queue of *undischarged* obligations: a `question` owes an answer, an
  `accusation` owes a defense; cleared when answered. No LLM.
- **Proactive path** — fires only on a quiet cycle (reactive queue empty), budget-capped, candidate ranked
  by cheap deterministic heuristics, seeded-random tiebreak.
- **Load-bearing dependency:** the anti-ping-pong caps (per-pair K + freshness) are what let the reactive
  queue *drain* so proactive can ever fire.

**Virtue:** Phase 0 now has **no fragile LLM mechanism left to validate** — reactive and proactive are both
deterministic and unit-testable. We removed the one piece we couldn't make reliable. (The standalone
novelty label from Smokes 2–3 remains valid as a *disinterested external* judge — it is only the *folded
self-judgment* that failed, which is why novelty could return later in that form, §8.)

**Deferred (a design-time write-down).** An **encoder-based novelty gate** was noted as a cheaper
cross-check / eventual replacement for the LLM labels: a dedicated observer **cross-encoder** plus a
situation-to-situation `strategy_points` **encoder** (repurposing the reranker's sim-to-sim relabelling) —
rationale: a barely-distinguishable situation → same retrieval → same action ≈ "nothing new." **Caveat its
eval must check:** summary-vs-prior-summary similarity is **lossy** — novelty can live in a dialogue nuance
the situation summary dropped — so encoder-similarity risks a **false `already-said`** that the
transcript-aware LLM labels don't share. Use a **bi-encoder / embedding cosine** for the comparison, *not*
the reranker CE as-is (trained for situation→strategy *relevance* — wrong objective) and *not* the dedup
classifier (different granularity). *(This is the rationale behind the embedding pre-filter named as the
deferred next step in [`report.md`](report.md) §5.)*

---

## 7. The build — scheduler primitives, parameters, wiring (2026-06-03 → 06-04)

Stage 1 schema landed first (`831b908..e4d4d21`): `DayChannel{day, seq, player, message,
addressed_targets}`, `AddressedTarget{target, addressed_form, stance}`, `DayDiscussOutput` gains
`addressed_targets` (right after `message`) + `pass_turn` (both required — flash-lite chokes on nullable
fields, and in the sequential model silence is an upstream scheduler decision, so `message: str` is
required and the prompt's `return null` is dropped). `round → seq` with every `.round` reader enumerated
first.

**Selection model reconciled — reactive/proactive, the weighted score dropped (Stage 2 design pass).** The
checklist carried two incompatible models from two eras: the old unified weighted score and the Smoke-4
reactive/proactive model. Once reactive obligations became a hard gate, the blended score had nothing left
to do (you owe a turn or you don't; the `intent` term never had a source). Reactive/proactive wins on
naturalness (encodes adjacency pairs) and testability, ties on dynamism and cost (both recompute from the
transcript; both make exactly one generation call per utterance). The naive "round-robin against a live
transcript" alternative was weighed and **rejected for production** (it keeps the self-selected silence
rule Smoke 4 falsified, and pays an LLM call even on a pass) but **kept as an optional third A/B arm** —
the clean ablation isolating *sequential generation* from *smart scheduling*.

**Stateless recompute chosen over stateful incremental.** The scheduler could recompute its view (recency
+ grouped obligations) from `day_channel` each cycle, or keep stateful dicts in graph state and mutate them
per utterance. At N=9, U≈22 the stateless scan is ~O(U²)≈500 pure-Python ops/day vs a corrected stateful
~O(N·U)≈200 (store *absolute* seq for recency, don't sweep +1 each turn) — both microseconds, dwarfed by
the ~U LLM calls, so **compute is not the deciding axis.** Stateless wins on two *non-compute* grounds, and
the honest tally is **2 wins, not 3** ("resume-safety" and "no-drift" are the same property — derived state
desyncing from the source of truth — wearing two hats): **correct-by-construction** (a fresh scan can't
disagree with the transcript; the dangerous half of stateful — in-place obligation mutation that never
self-heals if one update is missed — simply doesn't exist) and **trivially-valid test fixtures**
(hand-build a `day_channel`, assert the pick; no replaying an update sequence to reach a state first). The
verdict is load-bearing on one assumption — `day_channel` + within-day-immutable night state fully
determines scheduling — **verified for all-agent games** (the one break, a human turn carrying no
speech-acts, is on the Phase-1 list). **No-regret + reversible:** if scale ever made the scan hot (it won't
until U is in the thousands, or LLM cost stops dominating), the stateful version drops in with *stateless
kept as the oracle to validate it against* — and you'd migrate recency first (low-risk, monotonic) and
leave obligations as a fresh scan, since going *half*-stateful just buys back a desync surface for a win we
don't need.

**The four scheduler primitives** (pure functions over the transcript; unit-testable, no LLM):
- `build_reactive_queue` — nets open obligations from one transcript pass, **grouped by the obligated
  agent** (a multi-accused agent answers everyone in one turn). Freshness skips a re-open while open;
  per-pair K blocks the (K+1)th open in a burst; a cooldown resets the cap once the pair has cooled.
- `speech_recency` — derived (`current_seq − last_spoke_seq`, ∞ if silent); a pass marker advances
  recency. *(Shipped inlined into `rank_proactive` rather than as a standalone fn.)*
- `rank_proactive` — **role-blind: recency + seeded-random only.** Private-info and centrality were both
  dropped (below).
- `select_next` *(shipped as `select_next_speaker`)* — reactive-first → trailing-pass termination →
  proactive; cap backstop.

**Two refinements made the same day:**
- **`pass_turn` valve (proactive-only).** Smoke 4 dropped the *structured novelty label*, not the
  lightweight "say nothing if you'd only restate" valve. A proactive pick may set `pass_turn=true`; a
  reactive speaker always speaks. *Honest caveat:* self-authorship optimism means agents under-use the
  pass, so it's a weak filter — but cheap, and it yields a cleaner convergence signal than inference; the
  global cap is the backstop.
- **Proactive budget 1 → 3, passes recorded in `day_channel`.** A single agent's pass shouldn't end the
  day. Give up to P=3 distinct proactive picks the floor; **terminate only when P pass in a row.** A pass
  is a **hidden `DayChannel(passed=True)` marker, not a no-append** — the stateless scheduler can only
  react to what's in the transcript, so the pass must live there (it advances recency → next pick rotates;
  inert for obligations; skipped by the formatter; excluded from the cap). This reinforces statelessness:
  a pass is a first-class hidden event, and **SCHEDULE owns all termination** (the role node always loops
  back).

**Private-info dropped to zero — the scheduler is role-blind.** A volunteer-boost would only ever apply to
the investigator (healer info is ~worthless to volunteer; SK/vigilante have no shareable info) — a genuine
power-role tell with no clean subtle implementation. So leave it out: the investigator's reveal becomes a
strategic *agent* decision (prompt/strategy), not a scheduling one, and **role-blind needs no change when
SK/vigilante land.**

**Freshness vs per-pair-K are two different mechanisms** (the common muddle): freshness stops
double-counting an *open* edge (a reworded restatement creates no second obligation — the key ignores
wording by design, so no LLM judges "new angle?"); per-pair-K caps re-engagements of a directed pair
*after* discharge within a consecutive burst.

**K made consecutive, not total-per-day — `reengagement_cooldown` (M) added (2026-06-04).** Total-per-day
K left an exhausted `(A→B)` edge dead for the rest of the day even after the room moved on; the escape
route (re-engage via the proactive tier) doesn't hold (proactive is role-blind recency+random, so it keeps
the *room* alive but won't reliably reunite a *pair*). Fix: a pair's K-count resets once it has sat
`M = ceil(reengagement_cooldown_multiplier · survivors)` utterances untouched (multiplier `1.0` →
M ≈ one full table). Inside a burst K=2 still caps consecutive ping-pong; only a genuine lull reopens it.

> ⚠️ **Parameter bug, found later during the 2026-06-24 consolidation review — not during the build.** The
> shipped default `reengagement_cooldown_multiplier` read **`3`, not the `1.0` this note and the field's
> own comment both specify.** At `3`, `M = ⌈3·N⌉ ≈ the whole-day utterance cap`, so the cooldown almost
> never fired and the per-pair K-cap silently behaved as **total-per-day** — the exact behavior this design
> chose *against*. A ~3× mis-tune that shipped from `23959b2` and sat unnoticed ~20 days because nothing
> ever swept the scheduler knobs. **Corrected to `1.0`** (22/22 `test_scheduler.py` green). The
> documentation pass is what surfaced it — see [`report.md`](report.md) §5 for the lesson (unswept tunables).

**Config landed** (`game_config.py`, `c25a675`): `discussion_utterance_multiplier=3.0`,
`min_discussion_utterances=6`, `per_pair_reengagement_cap=2`, `proactive_budget=3`, `opener_floor=1`
*(later 3, §8)*, `reengagement_cooldown_multiplier=1.0`, plus `utterance_cap(n)=max(6, ⌈3·n⌉)` and
`discussion_recursion_limit(n)` *(later made pass-aware: `2·proactive_budget·cap+10`, §8)*.

**Graph wiring (Stage 4).** Stateless → no new shared `DayGraphState` field; `firing_reason` rides the
transient `Send` payload (tracing copy → Langfuse span). New `SCHEDULE` node runs `select_next` and emits a
single `Send` to the chosen role node (reusing per-speaker payload construction); the role node always
loops back; voting untouched. `recursion_limit` derived from the cap so the graceful cap fires before a
`GraphRecursionError`.

**Storage vs display — trim the biggest token source.** The Pydantic model is *storage*, the formatter is
*display* (already decoupled → this is formatter-only, state untouched). `addressed_targets` already never
render; drop `seq` from display (ordering is implicit in the list) and drop `day` from the agent-facing
transcript (verified today-only — prior days arrive compressed via `format_day_summaries`), so the
agent-facing render becomes plain `player_id: message` lines, trimming ~10–12 chars × ~U lines off every
agent call. `day` stays in the postgame/summary formatters, which genuinely span days.

**Per-stage acceptance criteria** (the build trackpad's spec — how each stage was validated, no LLM):
schema compiles + legacy frozen sets still load + a smoke replay produces `addressed`; scheduler unit tests
over synthetic transcripts (A questions B ⇒ B reactive; B responds ⇒ cleared; restated-while-open ⇒ no
fresh obligation; (K+1)th `A→B` ⇒ none; `C→B` ⇒ fresh; reactive non-empty ⇒ no proactive;
`proactive_budget` passes ⇒ terminate; cap reached ⇒ terminate); a day runs sequentially with
per-utterance Langfuse spans; generated messages are non-redundant and anchored to the firing-reason
brief; ping-pong stress test terminates via K + freshness before the global cap.

---

## 8. First live runs + tuning — the rewrite validated, two real problems found (2026-06-04)

First time the loop ran **live** (real LLM, 8-player games). **Verdict: functionally correct and produces
good discussion; the real issues are tunable, not architectural.**

- **Smoke A (memory off)** — wolves win, day 3, exit 0. Every designed behavior confirmed in vivo:
  sequential loop spins & terminates (no `GraphRecursionError`); per-day `seq` resets; proactive rotation
  (distinct openers); **K-cap bounds ping-pong live** (player_2↔player_8 traded 2 each way then stopped).
- **Smoke B (memory on, cached seed)** — villagers correctly lynch the wolf, day 4, **0× 429**. The memory
  pipeline + new universal payload ran clean; the **scheduler is memory-agnostic** (identical flow;
  memory changed *content depth*, not who-speaks-when).

**Two problems surfaced — and the second reprioritized the work:**

1. **Domination / verbatim repetition** (the first-noticed issue). An agent that owes A but keeps
   `response`-ing B (only `mention`-ing A) never discharges → stays the top reactive pick → re-selected
   turn after turn (observed: one agent ×7, with **seq 14 == seq 15 verbatim**). Root cause = the
   self-labeled speech-act unreliability Smoke 4 flagged, now live: form mislabel + wrong-creditor
   discharge; K-cap makes it worse by suppressing competing obligations.
2. **⭐ Proactive echo / dogpile** (the *bigger*, systematic issue, found on baseline inspection). A
   cleanly-scoring game (no domination) was still low-value: days 1–2 were ~95% proactive — an agreement
   pile, ~20 turns recycling "watch for forced narratives" with no new info (the agents narrate it
   themselves: *"stuck in a cycle of agreeing… which itself is a trap"*). **Mechanism:** the proactive
   tier picks *who* but nothing about *what*, with no novelty constraint — the gap the dropped novelty
   gate left. The deterministic metrics (`max_consecutive`, `verbatim_dups`) catch the *re-pick* artifact
   but **miss semantic echo entirely**, so this scored "clean" while being low-value.

**The fixes (committed `1ea5c9a..`, validated over 4 live games):**
- **A+B fixes domination** (`5672e22`). A = a `firing_reason` brief in the prompt ("you were addressed by
  X — respond"); B = a `mention` of the creditor **discharges** the debt, not just a `response`. Result:
  max-consecutive 1, dups 0, discharge 1.0 — the re-pick loop is gone. Reactive turns are never
  gated/passed (forced answers exposed both wolves in one game).
- **Proactive echo → the novelty gate returns, as a disinterested *external* judge** (`b9c3b30`). Exactly
  the Smoke-2/3 form (external, disinterested), **not** the falsified self-judgment: it runs
  post-generation on proactive turns only and converts low-novelty echo into a hidden pass. Memory-off:
  day-2 24→9 utterances, and **3 of 4 days now terminate by trailing-passes** (convergence) instead of
  grinding to the cap. `opener_floor` raised **1 → 3** (`c1c4dc2`) so the gate can't collapse a day's
  opening. Value is variance-dependent — heavy gating + early termination on echo-heavy days
  (cost-*favorable*), ~16% gating on substantive reactive-heavy games (mostly overhead). The judge is
  deliberately lenient ("lean novel when uncertain"); strictness is a one-line knob deferred to the gate.
- **Crash fix** (`e20eb63`): an agent addressing `target="all"` made the scheduler pick `'all'` →
  `KeyError`; `build_reactive_queue` now filters to valid survivors (+ regression tests). **`recursion_limit`
  made pass-aware** (`1ea5c9a`): `2·proactive_budget·cap+10` (passes burn super-steps without advancing the
  cap).

**Net:** the headline discussion-quality issue is **proactive echo, not domination** — echo is systematic
+ proactive-side and dragged most days; domination is intermittent + reactive-side. Both addressed;
remaining tuning (judge strictness, an embedding pre-filter, a multi-game runner) deferred.

---

## 9. The acceptance gate — Phase A #1 closed (2026-06-05)

The go/no-go: does sequential read *better* than concurrent? Full record + verdict in
[`quality_gate/`](quality_gate/experiment_log.md) (rubric, deterministic metrics, transcripts). Cheaper than the original
plan: because the wins are **structural** (concurrent parroting is architectural; sequential
responsiveness is mechanically forced), existing frozen concurrent games are valid evidence and no LLM
judge was needed. The gate collapsed to: re-run the **sequential** arm, read matched **concurrent**
transcripts, hand-judge against the rubric.

**Result — sequential clears the bar; adopt it.** echo_rate **0.00** (sequential, both memory on/off) vs
**0.05–0.06** (concurrent, 16 same-round echoes over 8 games, concentrated on day 1); responsiveness
forced by reactive obligations; turn-fairness + volume comparable. Confidence **HIGH on the structural
dimensions** (reproduced across all games), **LOW on any quantitative delta** (N=4/arm). Concurrent is not
*broken* — with strong evidence it still converges and wins — but it reads as parallel monologues where
sequential reads as a conversation. **Closes Phase A #1**, unblocking A#2 (roles), #3 (tracing), #4 (night
memory), #5 (v5 DB). Two harness bugs were found + fixed during the gate (`run_batch.py` was dropping the
transcript; the runtime retrieval-query embedding had no 429 retry).

---

## 10. Prompt-boundary cleanup — a separate concern, done next (2026-06-05)

Immediately after the gate (before Phase A #2 roles) a generation-prompt cleanup was done: the role prompts
were prescribing a degenerate "tone/silence policing" pseudo-strategy, which floods transcripts and would
contaminate the memory store. It enforces **prompt = how to talk + the rules; memory = what to conclude** —
a prompt/memory concern, not a scheduler one, so it has since been **hoisted out of this folder to its own
home at [`evidence/prompt_boundary/`](../prompt_boundary/experiment_log.md)**. It does *not* reopen the gate
(that was concurrent-vs-sequential on identical prompts — internally valid); it is noted here only because
it followed chronologically. Full record, method, and the honest board-confound caveat live in that folder.

---

## 11. Status and what's next

**Phase A #1 is closed** — the sequential scheduler-driven day discussion shipped and cleared its
acceptance gate. The shipped design and its guarantees are documented destination-first in
[`report.md`](report.md); the open gaps (human speech-act extraction, the self-labeled-speech-act
domination residual, proactive-echo judge leniency, the unswept tunables, wolf-night still concurrent) are
tracked there, criticality-ordered and freshness-dated.

Within the broader roadmap, closing Phase A #1 unblocked the rest of Phase A — and as of this write-up
(2026-06-24) some of those have since shipped: **roles A#2 landed** (the 3-faction, 9-player casting is now
in `game_config`), and the **v5 DB rebuild shipped and is now `v6_1`** (the `round→seq` migration folded
into it). Consolidated tracing and night memory are further along the same roadmap. Deferred within *this*
workstream: human integration (Phase 1, where external speech-act extraction belongs), the proactive
embedding-novelty pre-filter (Phase 2), voice/persona (Phase 3), and optional style fine-tuning (Phase 4,
only if a drift test shows prompted voice decaying).
