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
> concurrent-vs-sequential acceptance A/B). A related generation-prompt cleanup that followed lives in
> [`prompt_boundary/`](../generation_prompt/prompt_boundary/experiment_log.md) (see §10). Guiding principle throughout:
> **deterministic where reliable; LLM only where necessary.**

---

## 1. Motivation — from parallel to sequential (and why parallel first)

The ideal day discussion channel should sound more like holding natural conversation flows— proper turn-taking, replies that answer what was
just said, varied participation, natural tapering. This typically requires a sequential talking design. However, sequential speaking has inherent turn advantage for later speaker, who simply has more information to work with and has the last say.

Concurrent was the natural first design, and a defensible one — every agent speaks once per round,
generated in parallel against the same frozen snapshot. A day's discussion runs after N rounds has passed or until no agent has anything new to add. Agents were instructed via prompt to not say anything if they have nothing new to add (Silence Rule). It was the **simplest to build** (one round, fan
out, no scheduler or per-utterance state), the **fastest** (agents generate concurrently → low latency),
and **fair by construction** (one shared snapshot, revealed together → no turn-order advantage).

However, the original simple concurrent design has a few weakness that makes it impossible for the conversation to sound natural. It generates every agent's utterance **in parallel against the same frozen transcript
snapshot**, once per round, revealed together. It is fair by construction but robotic, and every failure
traces to the frozen snapshot + simultaneous evaluation — visible in real game logs:

- **Redundant convergence** — N agents reacting to one snapshot produce N near-duplicate takes (six
  players independently "watch who downplays the save").
- **Broken adjacency** — a question in round *r* is answered in *r+1*, after the thread moved on; the
  questioned player can't respond in the round they're attacked.
- **Flat participation** — everyone speaks every round regardless of having anything new, leading to crowded low value dialogues.
- **No within-round reactivity** — a dogpiled player can't defend until next round, and dogpiling is one of the main lynch reason for agents powered by weak llm models.

Root cause: redundancy is a **cross-agent property** invisible to a per-agent decision made
simultaneously. Three agents each correctly conclude "I have a new accusation" at the start of each round, because they haven't seen other agent's speech for that round. They can only compare against what was spoken last round.

---

## 2. The original design: Using a weighted scoring system (as first drafted, ~2026-05-31; captured with the grounding pass on 2026-06-01)

The new sequential agent discussion design needs to mitigate the problems of concurrent design, while addressing the inherent turn advantage bias.

**Addressing turn advantage**

The simplest fix was to randomize each agent's turn each round, on the intuition that shuffling the order would average the advantage out across the day. But randomness does not remove the turn advantage — it only relocates it. Every round still ends with a last speaker who has heard everyone else before committing; a random order merely hands that informational edge to a different agent each round rather than eliminating it. And relocation is the *lesser* problem. The real cost is that a random order is allocated blind to the conversation: it decides who speaks next without regard to who the discussion actually demands, so a direct question can sit unanswered while its target waits for a slot that hasn't come up. Randomness pays the one thing sequential discussion was supposed to buy — responsiveness — and gets only diffusion in return.

The turn advantage is a genuine bias, and we do not fully solve it; we mitigate it on two fronts, and neither front is the speaking order. The informational edge inside discussion can't be designed out without flattening the conversation back into blind parallel turns — which is exactly the trade randomness makes and loses. So instead of fighting it in the ordering, we let it dilute on its own: once turns are taken one at a time with the order recomputed each utterance, no agent holds a fixed late slot, so the edge is spread thin across agents and across the day rather than banked by one player. This is the same diffusion randomness was reaching for — but here it falls out as a *byproduct* of an order that responds to the conversation, so we get the dilution without paying the responsiveness randomness paid for it.

**Fairness lives only at the vote.** The second front handles the part of the advantage that *can* be removed outright — the purely positional, decisive edge of the last voter watching the tally form. The vote is simultaneous, blind, and locked: everyone commits against the frozen transcript without seeing the others', revealed at once. There is no tally to read and no last mover to swing it, so that edge is gone. *Trade-off accepted:* a residual, diffused information edge remains in discussion — a later speaker really does speak better-informed — and we take it as the price of discussion that sounds like discussion

**Mitigating concurrent's failures — a pressure-driven sequential loop**

With fairness quarantined to the vote, discussion is free to be shaped purely for naturalness. That is what the rest of this section builds.

**Sequential continuous loop, no rounds.** A *round* was the concurrent model's unit of generation —
everyone speaks once, in parallel, then the next round begins. Sequential generation has no use for it: the
scheduler recomputes after every single message (one **utterance**) and picks who speaks next. So rounds are
dropped — rank the available agents, pick the top, generate that one utterance against the running
transcript, append it, repeat. *Trade-off — latency:* one speaker at a time is slower than firing all of them
at once, but for a turn-based game (eventually with a human in the loop) that is fine, even desirable — it
paces the game to reading speed. 

**The scheduler — a weighted tiered score.** The scheduler has one job each cycle: pick who speaks next. So the design question is what makes an agent the right next speaker — and in a real discussion two forces answer it. An agent speaks because the room *demands* them — they were just questioned or accused and owe a reply — or because they have something to *offer*: a fresh question or argument nobody asked for. Model both as magnitudes and pick the largest: the demand as **pressure**, the volunteered read as **intent**, giving a first cut of `score = pressure + intent`.

Two failures force a correction. Pressure alone reproduces the dogpile — a clique references each other, their mutual pressure spikes, and they monopolize the floor while quiet agents never clear the bar. So a **domination guard**: `speaking_debt` penalizes whoever has been hogging the floor, `quiet_nudge` lifts whoever has been silent. And a fully deterministic order is rigid and replayable to a fault — it would even leak a power-role tell in the day's opening sequence — so a small **seeded\_random** term breaks ties without making the order predictable. The full score: `score = pressure + intent − speaking_debt + quiet_nudge + seeded_random`. Crucially, **only `intent` touches an LLM — every other term is a deterministic function of the transcript**, recomputed after each utterance

- **pressure** — the demand signal, and the primary one. An unanswered direct question to you is the single thing that most makes a conversation feel *broken*, so the room's demand on an agent has to dominate the order. It takes **no model call**: a scan straight off the transcript weights each mention of the agent by **kind** — *questioned* > *accused* > *referenced* > *agreed-with* — decays it by recency over a rolling window, and drops self-mentions. The kind is read from the text directly (an *accused* hit, for instance, is the agent's id sitting near "wolf"/"suspicious"/"lying"). One property is load-bearing and worth stating on its own: pressure is **recomputed every turn**, which restores adjacency for free — A attacks B, B's pressure spikes, B jumps up the order.
- **intent** — the volunteer signal, and the one term an LLM supplies. A loop that only answers demands never
  *originates* anything: with nobody addressed it has nothing to surface and converges instantly, so it needs
  a volunteer signal or it's dead on arrival. `intent` asks whether a quiet agent has a genuinely new read,
  answered by the folded novelty gate (below) as a coarse **3-level label** — `already-said` / `borderline` /
  `new` — with `already-said` skipped. So it acts less as a number than as a **gate** on the lowest
  (volunteer) tier.
- **speaking_debt** (subtracted) and **quiet_nudge** (added) — the correction pressure alone *forces*.
  Pressure on its own visibly reproduces the dogpile: an aggressive clique references each other, their mutual
  pressure compounds, and they own the floor while quiet agents never get a turn. The counterweight is a
  rolling per-agent `DebtTracker` over the last N utterances — debt penalizes whoever's been hogging the
  floor, the nudge boosts whoever's been silent (both magnitudes hand-tuned).
- **seeded_random** — reproducible plumbing. A small pseudo-random value off a stable per-utterance seed keeps
  the order replayable yet not rigid; it breaks ties *within* a tier only, and doubles as the power-role-tell
  mask (otherwise the day's first speakers would look fixed) and the slot a human sits in.

**Why a tiered score, and not a flat blend or a plain decision tree.** All five terms bear on one decision — who speaks next — which argues for making them one commensurable magnitude and picking the max. But a flat sum is wrong in one direction: it lets an accumulation of soft signals outvote a single hard one, and an unanswered direct question must beat any pile of mild references, not lose to enough of them. A plain decision tree fixes that — ask "anyone questioned? else anyone accused?..." in priority order — but throws away too much in the other direction: within a group of equally-questioned agents it has nothing left to say, and the domination guard and recency have real work to do there. So the design is both, layered. Mention kind sets a hard **tier** — top is an unanswered direct question, then accused, referenced, agreed-with, volunteer — and no number from a lower tier can cross into a higher one; that's the tree, and it protects the hard signals. *Within* a tier the numeric terms compose and pick the max — debt and nudge spread the floor, recency restores adjacency, seeded-random breaks the final ties; that's the blend, and it's where the soft forces do their ordering.

One rule guards the floor against its own counterweight: debt is **capped** so it can never demote an agent out of the addressed tier. Talk a lot *and* get asked a direct question, and you still answer — debt suppresses *volunteering*, not a direct reply

**The silence mechanism — an LLM novelty gate.** Inside the weighted score, this is the
component that fills the `intent` term — and it's the **anti-parroting machinery**. The reason it exists is
§1's core failure: when everyone speaks every round, N agents reacting to the same state produce N redundant
takes. The fix is to let most of the table *stay silent* — an agent should speak only
when it has something the transcript doesn't already hold. Sequencing alone buys much of that for free
(re-evaluated against a transcript that now contains the first agent's point, the second agent finds its own
point no longer new and self-silences, so the redundancy collapses with no global coordination); a set of
silence *rules* decides the rest.

The four rules enumerate the only *legitimate reasons to break silence* — you're defending a fresh
accusation (Rule 2), you owe a required reveal (the round-1 investigator result), you have a genuinely new
observation (Rule 1), or your suspicion has changed with new reasoning (Rule 3) — and they split by **cost**:

- Rule 2 and the investigator reveal are **deterministic**, because both are cheaply detectable *structural*
  events (a fresh accusation since your last turn is a mention-heuristic hit; the reveal fires on the day's
  first turn) — no model needed.
- Rules 1/3 need *semantic* judgment ("is this actually new against the transcript / against my own prior
  stance?"), so they fall to the **LLM**.

The cost win comes from the *deterministic* gate, not the LLM one: most legitimate discussion is reactive
and caught by the cheap rules, which silences most of the table for free. The LLM check then runs on only the
**top 1–2 quiet agents the score surfaces each cycle** — purely a **cost bound** (a summary-cost novelty
check across the whole silent majority would destroy breakeven; running it for the one or two most plausible
volunteers is affordable). What it decides — does this agent actually have something new? — is exactly the
score's `intent` term, and so whether the agent speaks at all.

Two narrower choices, called out because they otherwise look arbitrary: the LLM rules were **folded as the
final fields of the situation-summary call** — reusing inputs already in that prompt (no added context),
with autoregressive ordering committing the summary *before* the novelty judgment so it can't bias the RAG
query the summary drives. And novelty was rated on a coarse **3-level scale** — `already-said` (the point is
in the transcript → stay silent), `new` (a genuinely new read → speak), and `borderline` (ambiguous → not
forced to a hard yes/no, handed to the speaker cap) — rather than a boolean or a fine score, because booleans
calibrate better than fine scores on weak models and the `borderline` bucket is the whole reason for three
levels.

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

**Point 2 — speech-act fields**.  Model-emitted
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

**Point 5 — ping-pong / termination.** Two things this point settles: how a day's discussion *ends*, and how
to keep two players from locking into an endless feud. **Termination:** the day is over when no one has a
reason left to speak (the eligible set has emptied) or a hard utterance cap fires. Convergence is trickier
than draining a fixed list, because the discussion can re-ignite — a reply can put a fresh question to a
player who'd gone quiet, reviving them — so the scheduler has to re-check after every utterance whether the
latest line gave anyone a new reason to speak.

Two ways a discussion can spin without progressing are ruled out by hand:

- **Pure repetition** — an agent restating the same accusation in new words. A restatement of an
  *already-open* accusation creates no new obligation, so re-wording can't keep the loop alive. (The check
  keys on *who accused whom of what*, ignoring wording on purpose, so no model has to judge "is this a new
  angle?".)
- **An endless feud** between two players. After a set number of back-and-forths on the same directed pair
  (A onto B), further rounds between them are blocked until the pair has cooled off. The speaking-debt
  penalty couldn't do this job: it was forbidden from silencing a *directly-addressed* agent (you always
  answer a question put to you), so two players locked onto each other could trade blows indefinitely — the
  per-pair cap is what actually stops it.

So "always answer a direct question" means answer a *fresh* question once — not re-litigate with the same
opponent forever.

---

## 5. The smoke tests — probing the LLM-dependent pieces (2026-06-01 → 06-02)

Five empirical probes resolved the questions the design couldn't settle by reasoning. They all target one
risk: the design leans on a **weak, cheap model** (flash-lite) for two jobs that reasoning can't vouch for —
labeling who each message addresses or accuses (the foundation of the reactive path), and judging whether a
point is genuinely *new* (the proactive silence gate). Whether a small model is actually *good enough* at
these is an empirical question, so each smoke isolates one such uncertainty and asks "can the model really do
this?" before anything is built on it. The scripts live in [`scripts/`](scripts/) (`smoke_*.py`), their
per-case results in [`data/`](data/) (`smoke_*_results.jsonl`).

**Smoke 1 — speech-act capability (flash-lite, temp 1.0, 30 frozen cases).** *Catches:* can flash-lite
reliably tag who a message addresses or accuses — and does it beat the regex heuristic? The whole reactive
path rests on this label; if the model mislabels or invents targets, the scheduler mis-fires at exactly the
strongest signal (an unanswered direct question). Result: structured-output validity
**30/30 in all three schema shapes** (incl. a nested object-list — the flash-lite nested-object fear was
unfounded); **27/27 addressed targets grounded in the model's own message, 0 hallucinated**; on the act
label the model **beat string-matching decisively** — 63% agreement with a keyword heuristic but **all 11
disagreements favored the model** (the heuristic systematically under-reads accusatory questions as plain
questions). Decision: adopt model-emitted acts; regex demoted to an eval cross-check.

**Smoke 1b — 1-D `act` is lossy → 2-D `(form, stance)` (2026-06-02).** *Catches:* is a single `act` label
enough, or does it force the model into a coin-flip on messages that are two things at once? Reading each
message *against* its label (not just the distribution) showed the 1-D act was **under-determined**, not
inaccurate: nearly
every werewolf line is *simultaneously* a question (by form) and an accusation (by stance), so forcing one
`act` made the model coin-flip — the source of the earlier "accusation over-labeling" residual. Decoupled
into two orthogonal axes, both reliably emitted (100% valid, 0 hallucination). A worry that stance would
be accusation-flooded turned out to be a **sampling artifact** (the first run sampled an endgame cluster);
labelling 48 real messages **stratified by round** showed discussion *opens exploratory
(mention×neutral) and heats into a hunt*, with tier-1 (`question ∨ accusation`) ≈ 55% — the fields
genuinely discriminate. Freshness dedup keys on `(speaker→target, stance)`, **form excluded** (a reworded
re-accusation must not read as fresh).

**Smoke 2 — standalone novelty label (2026-06-01).** *Catches:* can the model judge novelty — is *this*
point genuinely new versus what's already been said? This is the heart of the proactive silence gate: a
volunteer should stay quiet if its point is already on the table. A first design was confounded (judging a
real long message as "new vs the transcript that contains it" — the model was *right* that multi-point
messages add
a new angle), which taught the clean test: *generated* candidates with polar ground truth. v2 (temp 0, 20
transcripts, pure-restatement vs genuinely-new probes) gave **clean separation both ways: 20/20 / 20/20,
no redundancy leaks, no over-suppression.** Two caveats carried forward: the `borderline` middle was
untested (the probes were polar); and — the load-bearing one — this measured the label in its **cleanest
possible setup**, a *standalone* judge rating a *fixed, external* candidate. The original design doesn't run
it that way — it **folds** the label into the agent's own situation-summary call — so this standalone result
is only an **upper bound** on real reliability; the folded production shape still needs its own check.

**Smoke 3 — temp 0 vs 1.0 for the novelty gate (2026-06-01).** *Catches:* does sampling temperature
destabilize the novelty label? The game runs at temp 1.0, so if the judgment flips run-to-run the gate is
unreliable in production. A kept **null result**: temp made **no difference** (temp0 20/20, temp1 majority
20/20, **0/20 label flips**). flash-lite is confident enough
that temp 1.0 doesn't perturb the label on clear cases. Decision: don't change the summary temp — the
a-priori "low temp calibrates better" wasn't supported, and it closed the folded/temp-1.0 residual for
*clear* cases.

**Smoke 4 — the folded novelty gate FAILS (2026-06-02).** *Catches:* does the novelty judge survive being
**folded into the agent's own call**? Smokes 2–3 validated it as a *standalone disinterested* judge — but
that costs a dedicated LLM call per candidate. To get it for **free**, the plan was to fold the judgment
into the agent's own situation-summary call (zero extra cost) — and a judge rating the novelty of *its own*
point is a different test. This is the biggest design change of the workstream. Tested in that actual
production shape, it does not hold:

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

## 6. The selection model redesigned — a brittle weighted score gives way to reactive/proactive (2026-06-02)

The existing scheduler design up to this point was the weighted score of §2 — a *tiered* blend
(`pressure + intent − speaking_debt + quiet_nudge + seeded_random`, with mention-kind setting the hard tiers)
deciding who talks next. Even granting the tiering, as a selection mechanism it had four weaknesses:

- **No hard guarantee** (the decisive one). §2's tiering *tries* to protect the answer — a questioned agent
  sits in the top tier and debt is capped from demoting them — but that protection is only as good as the
  brittle detection underneath it. A question phrased as a statement may never be classified as "questioned"
  (Smoke 1), so the agent never enters the top tier at all; and the tier cutoffs themselves are hand-set. The
  one thing a discussion *must* do — answer what was just asked — ends up held by *configuration*, not by
  construction: makeable *likely*, never *certain*.
- **Brittle scores, and the tuning hell that follows.** A correct ordering needs two fragile things to both
  be right: each per-agent magnitude captured accurately (pressure, debt, nudge), *and* the weights that
  trade them off chosen well. Both are hand-set with no ground truth to calibrate against, so the table is
  always one re-weight away from a different ordering — there is no stable target to tune toward.
- **Opaque — no answer to "why did X speak before Y?"** The order is the joint output of several continuous
  terms, the tier boundaries, *and* the detection heuristic's per-mention judgment calls; to reconstruct one
  decision you have to replay that whole computation and verify that all of the judgement are correct individually against another agent. There's no single easily derivable reason to point at — which makes the
  behaviour impossible to explain to a player, or to reason about when it misfires.
- **Hard to unit-test — no tuning-independent assertion.** You can't write "given *this* transcript, X speaks
  next" as a clean test, because the expected pick is a function of the exact weight values and the
  recency-decay window. Any test you write bakes in the current tuning and breaks the moment a weight moves —
  there is no stable, weight-free behaviour to lock down.

**Smoke 4 (§5) means folding novelty judgement into the same prompt as situation summary isn't feasible.** The novelty gate has to be an independent extraction requiring an additional llm call every agent's turn, which we would prefer to avoid for cost reason.

Both pressures point the same way — the four weaknesses are intrinsic to *scoring*, and Smoke 4 just
stripped the one LLM signal (novelty → `intent`) the score leaned on. So the redesign drops scoring
outright: the weighted blend of §2 gives way to a model **derived from it but with no numerical terms left**
— every agent reaches the floor in exactly one of two ways, *reactive* or *proactive*, and which one is a
hard property of the transcript, never a tunable weight.

**Reactive-Proactive Model**

> **Reactive = a message created an obligation. Proactive = the scheduler created an opportunity.**
> Proactive candidates do **not** prove novelty; we cap the number of opportunities and rank by cheap
> deterministic signals.

**The two paths, mechanically** (both pure functions of the transcript — no LLM in selection):

- **Reactive path** — a deterministic queue of *undischarged* obligations, read straight off the
  model-emitted speech-act tags (Smoke 1): a `question` owes an answer, an `accusation` owes a defense; the
  obligation clears when the owing agent answers. No model call.
- **Proactive path** — fires only on a *quiet* cycle (the reactive queue is empty), is **budget-capped**, and
  ranks candidates by one cheap deterministic signal — **recency** (who has been silent longest) — with a
  seeded-random tiebreak. A proactive pick proves no novelty; the cap, not a score, is what bounds it.
- **Load-bearing dependency** — the anti-ping-pong caps (per-pair K + freshness, §4) are what let the
  reactive queue *drain*, so the proactive path can ever fire.

**How the two paths dissolve the four weaknesses** (and buy one thing the score couldn't):

- **No hard guarantee → a guarantee by construction.** Being addressed is a *hard obligation*, not a high
  score, so the scheduler serves it before anyone else and the question is answered *next* — not made merely
  *likely* by a hand-set tier cutoff the brittle detection could miss.
- **Brittle scores / tuning hell → nothing left to tune.** No numerical terms, no weights — so no calibration
  to get right and no re-weight that can silently re-order the table.
- **Opacity → a one-line reason.** Selection is an obligation queue plus a single transparent signal, so "why
  did X speak?" always has a one-sentence answer — "X was owed a reply", or "X had been quiet longest".
- **Untestable → a clean, tuning-free assertion.** Both paths are pure functions of the transcript, so "A
  questions B → B speaks next" is a unit test with no weights baked in — it can't be broken by a future
  re-tune.
- **(bonus, beyond the four) Cost.** No LLM runs anywhere in *selection* — recency is free — so the per-turn
  novelty call the score leaned on leaves the hot path entirely.

**The silence rule falls out of the same move.** Dropping the score also drops the novelty gate it leaned on,
so *how an agent stays silent* had to be re-decided. Five fixes were weighed:

1. **Folded self-label** (the locked design) — *broken* (Smoke 4): zero extra calls, but useless.
2. **Per-turn disinterested judge on a draft** — the draft rides the situation-summary call (free), then a
   *separate* cheap call judges it. The judge is sound (Smoke 2/3 validated it); what's open is only this
   per-turn wiring on real drafts. Marks against: +1 call per candidate, a fragile LLM gate.
3. **Wave/batch judge** — one judge per wave; adds staleness, and its real payoff is cross-candidate dedup,
   not cost.
4. **Embedding similarity on a draft** — cosine of the draft against the transcript, reusing the retrieval
   embeddings: 0 extra LLM calls, disinterested by geometry — but genuinely untested (the deferred encoder
   plan as a bare threshold).
5. **No novelty detection at all** — *chosen*: the silence-side of the same deterministic reframe, removing
   the mechanism that caused the trouble (broken self-novelty, per-candidate cost, staleness) in one move.

Naming what the novelty gate *was for* shows why dropping it ripples so far. In the original design it was
the **brain of the proactive path**, doing three jobs at once: judging "does this quiet agent have something
genuinely new?" decided both *whether* a volunteer speaks (the silence gate) and — feeding the `intent` term
— *how high they rank* (priority); and a restated point scoring "not new" was the ping-pong **terminator**.
The reframe hands each job to a cheaper owner: priority → role-blind recency, speak-or-stay-silent → the
budget cap (plus the deterministic reactive gate), termination → per-pair-K + freshness. So novelty isn't
*relocated*, it's **removed** — every role it held now has a deterministic owner. (It returns much later, §8,
but in just one of those roles — a narrow proactive-*echo* silencer — never again touching priority or
termination. The build, §7, reconciles the two layered models term by term.)

**Virtue:** Phase 0 now has **no fragile LLM mechanism left to validate** — reactive and proactive are both
deterministic and unit-testable. We removed the one piece we couldn't make reliable. (The standalone
novelty label from Smokes 2–3 remains valid as a *disinterested external* judge — it is only the *folded
self-judgment* that failed, which is why novelty could return later in that form, §8.)

**Deferred (a design-time write-down).** The novelty judge was an LLM, not embeddings, by deliberate choice:
in this narrow on-topic domain every message is similar, so an embedding margin is thin and a similarity
threshold brittle — fine-paraphrase discrimination over a handful of messages is the LLM's strength as a
grounded reading task ("is this stated in this text"), reliable even on weak models. Even so, an
**encoder-based novelty gate** was noted as a cheaper cross-check / eventual replacement for the LLM labels: a dedicated observer **cross-encoder** plus a
situation-to-situation `strategy_points` **encoder** (repurposing the reranker's sim-to-sim relabelling) —
rationale: a barely-distinguishable situation → same retrieval → same action ≈ "nothing new." **Caveat its
eval must check:** summary-vs-prior-summary similarity is **lossy** — novelty can live in a dialogue nuance
the situation summary dropped — so encoder-similarity risks a **false `already-said`** that the
transcript-aware LLM labels don't share. Use a **bi-encoder / embedding cosine** for the comparison, *not*
the reranker CE as-is (trained for situation→strategy *relevance* — wrong objective) and *not* the dedup
classifier (different granularity). *(This is the rationale behind the embedding pre-filter named as the
deferred next step in [`report.md`](report.md) §5.)*

---

## 7. The build — schema, scheduler, wiring (2026-06-02 → 06-04)

§6 settled *what* to build; this is the build itself, in dependency order (schema → scheduler → graph),
plus the refinements that only surfaced once real code forced the details. **One principle runs through all
of it: every selection decision is a pure function of the transcript — no LLM, no hidden state.**

**Schema first** (`831b908..e4d4d21`). A new `DayChannel{day, seq, player, message, addressed_targets}`
replaces the round-based record; `AddressedTarget{target, addressed_form, stance}` carries the speech-act
tags; `DayDiscussOutput` gains `addressed_targets` and `pass_turn`. Both new fields are **required, never
nullable** — flash-lite chokes on optional fields, and in a sequential model silence is the *scheduler's*
call, not the agent's, so `message` is always a string and the old "return null to stay silent" is gone.
Every `.round` reader was found and cut over to `seq` first.

**Mapping the old blend onto the new mechanism** (Stage 2 design pass). The build checklist still carried
§2's weighted score. Reconciling it with §6's reactive/proactive model showed there was nothing left to
compute — every term had already become a hard mechanism or lost its source:

| Weighted-score term | Where it went in the build |
|---|---|
| `pressure` (who is owed a reply) | the **reactive queue** — a binary obligation, not a magnitude |
| `intent` (volunteer novelty) | **removed** — its only source was the folded gate Smoke 4 killed; the proactive path is a budget cap with no per-agent score |
| `speaking_debt` / `quiet_nudge` | split — "stop a pair hogging" → **per-pair K-cap**; "give quiet agents a turn" → **recency**, now the proactive rank itself |
| `seeded_random` | unchanged — still the proactive tiebreak |

(*Why* this is the better design — naturalness, the hard guarantee, tunability — is argued in §6; this
section is just the bookkeeping.) One collapse is worth a sentence: `speaking_debt` was always **barred from
silencing an addressed agent** (you answer a question put to you, however much you've already talked), so
its only real job was suppressing *volunteer* turns — and once volunteering became its own budget-capped
path, it had nothing left to subtract from. A simpler **round-robin-against-a-live-transcript** scheme was
rejected for production (it keeps the self-novelty rule Smoke 4 falsified and pays an LLM call even to stay
silent) but **kept as an optional A/B arm** — the clean ablation isolating *sequential generation* from
*smart scheduling*.

**The scheduler — three pure functions** (`Agents/turn/scheduler.py`, no LLM, unit-tested):

- `build_reactive_queue` — one pass over the transcript nets the open obligations, **grouped by who owes**
  (a player questioned by three answers all three in a single turn). A `question`/`accusation` opens a
  debt; a `response` *or* `mention` of the creditor clears it.
- `rank_proactive` — **role-blind**: quietest-first (recency), seeded-random tiebreak. (Recency is computed
  inline here rather than as a separate `speech_recency` function.)
- `select_next_speaker` — the whole decision, in strict priority order: **cap → reactive → trailing-pass
  termination → proactive**.

**Stateful counters would silently drift — so the scheduler is stateless.** The alternative, mutating
per-agent dicts each turn, has one fatal failure mode: a single missed update desyncs from the transcript
and never self-heals. So instead every cycle recomputes the whole view from `day_channel` from scratch. The
scan is trivially cheap next to the one LLM call per turn it sits inside, and it buys two things a stateful
version can't: a fresh scan **cannot drift from the transcript**, and a unit test can **hand-build a
transcript and assert the pick** with no replay. It rests on one assumption — the transcript (plus
within-day-fixed night state) fully determines scheduling — **verified for all-agent games**; the one
break, a human turn that carries no speech-act tags, is on the Phase-1 list. If scale ever made the scan
matter, a stateful version drops in with the stateless one kept as its oracle.

**Refinements that surfaced during the build** (each a problem the first cut hit, then the fix):

- **A proactive agent needed a way to decline.** Dropping the novelty label (Smoke 4) removed an agent's
  only way to stay quiet when it had nothing new. Fix: a lightweight **`pass_turn` valve**, proactive-only
  — a proactive pick may pass; a reactive speaker always answers. It's a weak filter (agents tend to think
  their own point is new) but cheap, with the global cap as the backstop.
- **One agent's pass would end the whole day.** With a budget of 1, the first proactive decline terminated
  discussion prematurely. Fix: raise the **proactive budget to 3** — up to three picks get the floor, and
  the day ends only when three pass in a row. A pass is a real but hidden `DayChannel(passed=True)` marker:
  the stateless scheduler can only see the transcript, so the pass has to live there — it advances recency
  (the next pick rotates), is invisible to agents, and doesn't count against the cap. `SCHEDULE` owns all
  termination.
- **A volunteer boost would leak a power-role tell.** The only role with information worth volunteering is
  the investigator, so any private-info priority bump would single them out. Fix: the scheduler stays
  **role-blind** — revealing a result becomes the *agent's* strategic choice, not the scheduler's, and
  nothing has to change when SK/vigilante land.
- **A per-day K-cap left dead pairs dead all day.** Once A→B hit its budget, the edge stayed blocked for
  the rest of the day even after the room had moved on. Fix: make K **consecutive, not per-day** — a pair's
  count resets after it sits untouched for `M = ⌈reengagement_cooldown_multiplier · survivors⌉` turns (≈ one
  full table), so K=2 still stops live ping-pong but a genuinely re-surfacing topic gets back in.
  (**Freshness and K are different jobs:** freshness stops a *reworded* restatement from opening a second
  obligation while the first is still open; K caps *re-engagements after discharge*.)

**Config** (`game_config.py`, `c25a675`): `utterance_cap = max(6, ⌈3·survivors⌉)` (≈3 turns per player,
with a floor of 6 so even a tiny endgame table gets a real exchange), `per_pair_reengagement_cap = 2`,
`proactive_budget = 3`, `opener_floor = 1` *(raised to 3 in §8)*, `reengagement_cooldown_multiplier = 1.0`,
and `recursion_limit = 2·budget·cap + 10`. The cap's *shape* encodes the intent; the individual numbers are
**hand-set and never swept** — honest defaults, not tuned optima (and the soil the cooldown slip in §11 grew
in).

**Wiring & display.** A new `SCHEDULE` node runs `select_next_speaker` and emits a single `Send` to the
chosen role node (reusing the existing per-speaker payload — one `Send` where the concurrent design fanned
out N); the role node always loops back; voting is untouched; `firing_reason` rides the transient `Send`
payload into a Langfuse span. Separately, the agent-facing transcript was trimmed to plain
`player_id: message` lines (`seq`/`day`/`addressed_targets` are storage, not display), shaving ~10
characters off every line of every agent call.

**How each stage was validated** (deterministic, no LLM): schema compiles and legacy frozen sets still
load; scheduler unit tests assert the obligation logic over hand-built transcripts (A questions B ⇒ B is
reactive; B answers ⇒ cleared; reworded re-accusation ⇒ no new debt; the (K+1)th A→B ⇒ blocked but C→B ⇒
fresh; reactive pending ⇒ no proactive; P passes ⇒ terminate; cap ⇒ terminate); and a full day runs
end-to-end with per-utterance Langfuse spans.

---

## 8. First live runs + tuning — validated, with two real problems (2026-06-04 → 06-05)

The loop ran **live** for the first time (real LLM, 8-player games). **Verdict: the architecture is sound
and the discussion reads well; the problems that showed up are tunable, not structural.** Two smoke games
confirmed the design in vivo:

- **Memory off** — wolves win, day 3, clean exit. The sequential loop spins and terminates (no recursion
  blow-up), `seq` resets each day, proactive picks rotate, and the **K-cap visibly bounds ping-pong**
  (player_2 ↔ player_8 traded two each, then stopped).
- **Memory on** — villagers correctly lynch the wolf, day 4, no rate-limit errors. The **scheduler is
  memory-agnostic**: identical turn-taking, with memory changing *what* agents said, not *who* spoke when.

Then two problems surfaced — and the second mattered more than the first:

1. **Domination / verbatim repetition** (reactive-side, intermittent). An agent who owes A but keeps
   *responding to B* (only *mentioning* A) never discharges its debt, stays the top reactive pick, and gets
   re-selected turn after turn — observed once at **×7, with two consecutive turns word-for-word
   identical**. The root cause is exactly the self-labeled-speech-act unreliability Smoke 4 warned about,
   now live: a mislabeled form means the debt is never cleared.
2. **⭐ Proactive echo / dogpile** (proactive-side, systematic — the bigger issue). A game with *no*
   domination was still low-value: days 1–2 ran ~95% proactive, ~20 turns piling agreement on the same
   point with no new information (the agents even narrated it — *"stuck in a cycle of agreeing… which itself
   is a trap"*). **This is the hole the dropped novelty gate left:** the proactive path chooses *who* speaks
   but says nothing about *whether they have anything new*. Worse, the deterministic metrics
   (`max_consecutive`, `verbatim_dups`) only catch the *re-pick* artifact, so this scored "clean" while
   reading as filler.

**The fixes** (committed 06-05, validated over 4 live games):

- **Domination → a two-part fix** (`5672e22`). (A) A **`firing_reason` brief** in the prompt ("you were
  addressed by X — respond"): without it a cleared agent re-derives what to say from scratch and re-lands on
  the same generic line, so pinning the turn to its actual obligation is what makes a piled-on player
  *defend* instead of re-accuse. (B) A **`mention` of the creditor now discharges** the debt, not just a
  `response` — so a correctly-aimed turn clears it even when the model mislabels the form. Result:
  max-consecutive back to 1, zero dups. Reactive turns are *never* gated — forced answers exposed both
  wolves in one game.
- **Proactive echo → the novelty gate returns, proactive-only** (`b9c3b30`). This is the one piece of §6's
  dropped novelty detection coming back — but in the **disinterested external** form Smoke 2/3 validated,
  never the self-judgment Smoke 4 killed. A separate judge reads the transcript and the freshly-generated
  proactive message *after* it's written; if it's pure echo, the turn becomes a hidden pass. It touches
  **only proactive turns** (reactive answers are sacrosanct) and owns **only silencing** — never priority
  (recency does that) or termination (deterministic). To stop it muting a day's opening, the first
  **`opener_floor`** real utterances skip it (raised **1 → 3**, `c1c4dc2`). Effect: an echo-heavy day's
  second round collapsed 24 → 9 turns, and 3 of 4 days now end by *convergence* (trailing passes) instead
  of hitting the cap. Its payoff is variance-dependent — large on echo-heavy days, mostly overhead on
  reactive-heavy ones — and the judge is deliberately lenient ("lean novel when unsure"); tightening it is
  a one-line knob left for later.
- **A `target="all"` crashed the scheduler** (`e20eb63`). An agent addressing `target="all"` made the
  scheduler try to pick `'all'` → `KeyError`. Fix: the reactive queue now ignores non-survivor targets.
  The recursion limit was also made **pass-aware** (`1ea5c9a`) so burned pass-cycles don't trip the graph's
  safety stop.

**Net:** the real discussion-quality lever turned out to be **proactive echo, not domination** — echo is
systematic and dragged most days; domination is intermittent. Both are addressed; the remaining tuning
(judge strictness, an embedding pre-filter, a multi-game runner) is deferred.

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
sequential reads as a conversation. **Closes Phase A #1.** Two harness bugs were found + fixed during the
gate (`run_batch.py` was dropping the transcript; the runtime retrieval-query embedding had no 429 retry).

---

## 10. Prompt-boundary cleanup — a separate concern, done next (2026-06-05)

Immediately after the gate (before the role-casting work) a generation-prompt cleanup was done: the role prompts
were prescribing a degenerate "tone/silence policing" pseudo-strategy, which floods transcripts and would
contaminate the memory store. It enforces **prompt = how to talk + the rules; memory = what to conclude** —
a prompt/memory concern, not a scheduler one, so it has since been **hoisted out of this folder to its own
home at [`evidence/generation_prompt/prompt_boundary/`](../generation_prompt/prompt_boundary/experiment_log.md)**. It does *not* reopen the gate
(that was concurrent-vs-sequential on identical prompts — internally valid); it is noted here only because
it followed chronologically. Full record, method, and the honest board-confound caveat live in that folder.

---

## 11. Status and what's next

**Phase A #1 is closed** — the sequential scheduler-driven day discussion shipped and cleared its
acceptance gate. The shipped design and its guarantees are documented destination-first in
[`report.md`](report.md); the open gaps (human speech-act extraction, the self-labeled-speech-act
domination residual, proactive-echo judge leniency, the unswept tunables, wolf-night still concurrent) are
tracked there, criticality-ordered and freshness-dated.

As of this write-up (2026-06-24), the downstream work this gate cleared the way for has largely since
shipped: **role-casting landed** (the 3-faction, 9-player casting is now in `game_config`), and the **v5 DB
rebuild shipped and is now `v6_1`** (the `round→seq` migration folded into it); consolidated tracing and
night memory are further along the same roadmap.

One correction landed during this consolidation pass itself: the `reengagement_cooldown_multiplier` in the
§7 config shipped at the field default `3`, not the `1.0` the design intended — detuning the cooldown ~3×
(`M ≈ whole-day cap`), so the per-pair K-cap silently behaved as the *total-per-day* rule the design had
rejected. It sat unnoticed ~20 days because nothing ever swept the scheduler knobs. Fixed to `1.0` (22/22
`test_scheduler.py` green); [`report.md`](report.md) §5 carries it as the unswept-tunables lesson.

**Future work** (none blocks shipping the sequential design; ordered roughly by value):

1. **Retire the residual `current_round`.** Day discussion runs on `seq`, but `current_round`/`round` still
   appear in the situation-summary and night/wolf-channel prompts (`Agents/prompts/`) — folding the last of
   it out pairs with the wolf-night migration below.
2. **Wolf-night discussion → sequential.** The night still uses the old concurrent 2-round fan-out
   (`Agents/graphs/night/wolf.py`) — the last `round`-based code path; the same reactive/proactive scheduler
   would bring the same coherence win.
3. **Novelty-gate hardening (Phase 2).** The proactive gate runs a deliberately lenient external LLM judge;
   a cheap embedding pre-filter *before* it (the encoder-gate design in §6) would cut cost on echo-heavy days.
4. **Scheduler tunable sweep.** `per_pair_reengagement_cap`, `proactive_budget`, `opener_floor`,
   `reengagement_cooldown_multiplier` were hand-set during tuning; a small grid sweep could confirm the
   defaults — the cooldown slip above is the standing argument for doing it.
5. **Human integration (Phase 1).** Where external speech-act extraction belongs — the stateless scheduler's
   one unverified assumption is a human turn carrying no `addressed_targets` (§7).
6. **Voice/persona firewall (Phase 3)** and **optional style fine-tuning (Phase 4)** — both about *voice*,
   not *flow* (which this architecture already solves); FT only if a drift test shows prompted voice decaying.
7. **Quantitative A/B (only if ever needed).** This workstream's gate is structural/qualitative; if a
   defensible *number* is ever required, run pinned fresh concurrent games from the `concurrent-baseline`
   tag + a win-rate / judged A/B.

---

*Sources — this log consolidates the workstream's scattered records into one chronological narrative: it
absorbs the original design doc (`plan.md`) and the build trackpad (`phase0_build_checklist.md`), both since
removed as standalone files (git history preserves them). Their content is folded into the sections above.*
