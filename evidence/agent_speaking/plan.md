Werewolf, multi-agent + one human player. This document captures the design
discussion, the decisions, their trade-offs, and a concrete build plan for
replacing the concurrent (everyone-speaks-once-per-round) discussion model with
a sequential, scheduler-driven one.

Guiding principle throughout: **deterministic where reliable; LLM only where
necessary.**

---

## 1. Context and goals

The day discussion must:

- feel like a real conversation — proper turn-taking, replies that actually
respond to what was just said, varied participation, natural tapering;
- have **no inherent advantage to turn order**;
- terminate within a reasonable cutoff;
- integrate one human player (currently `player_5`) without requiring real-time
agent interruption. (When we implement it later, right now we have no human integration yet)

The core reframe that organizes everything below: **fairness and naturalness
matter at different moments.** Turn-order *advantage* only bites at the
decision (the vote), not the chatter. So we enforce fairness exactly once — at
the vote — and let the discussion be sequential and natural everywhere else.

---

## 2. Why the concurrent design fails

Current design: every agent speaks once per round, generated in parallel against
the same frozen transcript snapshot, revealed together. It is fair by
construction but reads as robotic. The failure modes, all traceable to the
frozen snapshot + simultaneous evaluation, are visible in real game logs:

- **Redundant convergence.** N agents reacting to the same snapshot produce N
near-duplicate takes (e.g. six players independently saying “watch who
downplays the save”).
- **Broken adjacency pairs.** A question asked in round *r* is answered in round
*r+1*, after the thread has moved on; the questioned player can’t respond in
the same round they’re attacked.
- **Flat participation.** Everyone speaks every round regardless of having
anything new, so there is no silence, no back-and-forth, no bursts.
- **No within-round reactivity.** A dogpiled player can’t defend until the next
round.

Root cause: a per-agent, self-judged decision evaluated *simultaneously* cannot
see redundancy, because redundancy is a **cross-agent property**. Three agents
each correctly conclude “I have a new accusation” because, at the shared
decision moment, none has spoken yet.

---

## 3. Core architectural decisions (discussion + trade-offs)

### 3.1 Sequential, continuous loop — no rounds

Rounds existed only to organize simultaneous generation. Once generation is
sequential and scheduling recomputes per utterance, rounds impose an artificial
cadence that fights naturalness. We drop them.

One continuous loop: recompute eligibility + pressure over available agents →
pick the top → generate at speak-time against the running transcript → append →
repeat.

**Trade-off accepted:** we lose parallelism (turns are sequential, hence higher
latency). For a turn-based game with a human in the loop this is acceptable and
even desirable — it paces the conversation at human reading speed.

What replaces rounds:

- **Speaking-debt and mention-decay** become rolling windows over the last *N*
utterances rather than per-round resets.
- **The day-start proactive boost** (investigator) is a *day* event — fires on
the first discussion turn of the day, not a round event.
- **Novelty is day-scoped**, not round-scoped: a point raised early in the day
is still “already discussed” later. The transcript grows monotonically across
the day.

### 3.2 Fairness lives only at the vote

The vote is **simultaneous, blind, and locked**: every agent (and the human)
commits independently against the frozen transcript without seeing others’
votes, then all are revealed at once. This kills the only turn-order advantage
that matters — “the last voter sees the tally and swings it.”

**Trade-off accepted:** a later speaker in discussion has a turn-to-turn
information edge. It averages out across the game and, crucially, cannot be
cashed in because the vote is locked. We accept it in exchange for natural flow.

### 3.3 The scheduler — deterministic turn order

Speaking order is a deterministic, tiered score:

```
score = pressure (mention-based) + intent (proactive) − speaking_debt + quiet_nudge + seeded_random
```

Organized as **tiers** so randomness can only break ties *within* a tier and
never reorders across hard signals:

- **Top tier:** an unanswered direct question to the agent. The strongest
turn-taking signal — ignoring it is what makes a conversation feel broken.
- Lower tiers: accused, referenced, agreed-with, proactive volunteer.

Pressure heuristic (deterministic string/keyword matching):

- **Weight by mention type:** questioned > accused (id near
“wolf”/“suspicious”/“lying”) > referenced > agreed-with.
- **Decay by recency** over a rolling window; within the current turn sequence,
more recent mentions outrank older ones.
- **Drop self-mentions.**

**Domination guard.** Pressure alone reproduces the dogpile: aggressive players
reference each other, the clique dominates, quiet players never speak. The
counterweights are a **speaking-debt penalty** (talked a lot recently → higher
bar) and a **quiet-agent nudge** (hasn’t spoken in a while → boost).

**Critical cap on the debt penalty:** debt must never demote an agent out of the
top (addressed) tier. If you’ve been talking a lot *and* someone asks you a
direct question, you still answer — going silent there is the unnatural outcome.
Debt suppresses volunteering and low-pressure turns; it does not silence a
direct question. However we need to ensure that the discussion doesn’t become a two and fro between 2-3 players only and other players have no chance to speak. 

**Live recompute.** Deterministic pressure is recomputed after *every* utterance
(no LLM, instant) and the remaining queue re-ranked. This restores adjacency for
free: when A attacks B mid-sequence, B’s pressure spikes immediately and B jumps
up the order.

### 3.4 Eligibility / the silence mechanism

The diagnosis (§2) gives the fix: **evaluate the silence decision sequentially,
at speak-time, against the updated transcript.** Once the first agent has made a
point, the second agent — re-evaluated against a transcript that now contains
it — finds the point is no longer new and self-silences. The “is my point still
new” check is not a diff algorithm; it is a property you get by evaluating the
gate at pop-time against the transcript-so-far. The redundancy collapses without
any global coordination.

The four silence rules, decomposed by cost:

| Rule | Condition | How evaluated |
| --- | --- | --- |
| 2 | Defend a *new* accusation | **Deterministic** — mention heuristic detects a fresh accusation since the agent’s last turn |
| 4 | Private info strategically necessary | **No extra state** — transcript is the “already shared” record; live recheck prevents re-reveals. Round-1 case is deterministic; rare late reveal folds into Rules 1/3 |
| (round-1) | Investigator night-result reveal | **Deterministic** — fires on first discussion turn of the day. However the investigator can choose not to reveal and there’s a random factor which prevents agents from detecting the first few speakers are always power roles one. Currently all players need to speak round 1.  |
| 1 | New observation not yet discussed | **LLM** — compares candidate read against the **transcript** |
| 3 | Changed suspicion with new reasoning | **LLM** — compares against the agent’s **own prior stance** |

Most legitimate Round-2+ speech is reactive and therefore covered by the
deterministic rules. **The cost savings come from the deterministic gate, not an
LLM gate** — it silences most of the table for free; the full pipeline runs only
for greenlit agents.

LLM novelty (Rules 1/3), when used:

- Folded as the **final fields** of the situation-summary call. Autoregressive
ordering means the situation extraction is committed before novelty is judged,
so it cannot bias the RAG query. It reuses inputs already in the prompt (the
transcript for Rule 1, last strategy_notes for Rule 3) — no added context.
- **Coarse 3-level rating**: `already-said` / `borderline` / `new`. (Booleans
calibrate better than scores on weak models; the borderline bucket is the
reason for 3 levels.)
- **Borderline → handed to the speaker cap** rather than forced to a hard
yes/no.
- **Capped to 1–2 proactive candidates per cycle.** A summary-cost gate run
across the whole silent majority destroys breakeven; running it for a couple
of plausible proactive speakers is affordable. (Though if 1-2 out of 8 is the right number)

Why not embedding/cross-encoder similarity for Rule 1: in this narrow on-topic
domain every message is similar, so the discriminative margin is thin and the
threshold brittle; the cross-encoder being fine-tuned is trained for a different
objective (situation→strategy relevance). Embeddings are a scale tool; this is
small-set fine paraphrase discrimination over ~handful of messages, which is the
LLM’s strength and a grounded reading task (“is this stated in this text”),
where weak models are reliable.

**Speaker cap** per discussion cycle remains as a dumb backstop for the model’s
residual bias toward speaking.

### 3.5 The silence rule in the generation prompt

By the time generation runs, “should I speak” is already decided (deterministic
gate + folded novelty). So:

- **Remove the gate** (`return null if none apply`) from the generation prompt.
Double-gating reintroduces the unreliable self-judgment we moved upstream.
- **Keep the content discipline**: “don’t restate what’s been said, don’t repeat
appeals, don’t agree without adding reasoning.” This is a style constraint on
the message, not a gate on its existence.
- **Pass the firing reason in as the message’s brief.** The gate knows *why* the
agent was cleared (“defending player_6’s accusation”, “revealing investigation
result”). Anchoring the message to that reason removes redundant re-derivation
and keeps the output non-redundant (this is what makes a piled-on agent
*defend* rather than re-issue the same appeal).
- A null-abort may remain as a harmless safety valve, but it is not the
mechanism.

### 3.6 Per-turn pipeline (at speak-time)

For the **selected** agent only (silent agents skip all of this — the cost
saving):

1. **Situation summary** generated against the *current* transcript (fresh by
construction — no staleness, because it’s produced at the agent’s turn, after
everything said this cycle). Emits the Rule 1/3 novelty fields if enabled.
2. **RAG** retrieval of relevant strategy suggestions / facts from prior games
(cheap).
3. **Decision**: adopt the retrieved strategy or not.
4. **Generation**: write the dialogue, anchored to the gate’s firing reason,
under the content discipline, in the agent’s voice.

Moving the situation summary to speak-time (rather than batching at round start)
is what eliminated staleness. It is also *cheaper*, not more expensive: with the
participation gate, fewer agents speak than the full table, so per-speaker
summaries are fewer calls than batching all eight up front. The only thing given
up is parallelism, which we already accepted.

### 3.7 Human player integration

Real-time open mic was rejected (it requires agents to respond to interruptions
mid-generation). Instead:

- The human can **always speak** and is **never gated to silence**. They sit in
the ordering via the seeded random factor like any agent.
- **Floor offers**: offer the human the floor (a) after any utterance that
addresses them, (b) periodically every few AI turns, each with a short timer.
If they don’t engage within the window, the loop proceeds.
- **Surface the “directly addressed” signal** to the human prominently — the
mirror of the top-tier signal that would bump an AI. Otherwise the human
misses the cue an AI would act on.
- **Pacing**: a minimum gap between AI turns (simulated read time); cap AI turns
between human opportunities; hold AI generation while the human is typing if a
typing indicator is available.
- **Fairness equalizer**: the human’s standing information edge in discussion is
the price of a humane UX. It is neutralized at the **blind simultaneous vote**,
which the human takes like everyone else.

### 3.8 Termination

End the discussion when **either**:

- **Convergence**: after appending the last utterance, the *recomputed* eligible
set is empty (nobody has a trigger). Note: this is recompute-then-check-empty,
not draining a pre-built queue — eligibility is reactive, so an utterance can
*create* a new eligible speaker. ( need clarification here)
- **Cap**: a hard max-utterance / max-token (and optionally wall-clock) budget is
hit.

**Ping-pong guard.** Two agents accusing each other could loop (each accusation
re-triggers the other’s defense). The novelty gate is the real terminator: a
*restated* accusation is not new → suppressed → the loop dies. Debt slows it; the
cap is the final backstop.

---

## 4. Implementation plan

### 4.1 Components

- **Scheduler** — owns the per-utterance loop; computes tiered scores; selects
the next speaker or terminates.
- **PressureCalculator** — deterministic mention/accusation/question extraction
from the transcript; type-weighted, recency-decayed; recomputed after every
utterance.
- **DebtTracker** — rolling per-agent speaking-debt and quiet-nudge over the last
*N* utterances.
- **EligibilityGate** — deterministic rules (Rule 2, round-1 reveal,
pressure-rank threshold); decides whether an agent may speak before any LLM
call.
- **NoveltyChecker** (optional, Phase 2) — the folded Rule 1/3 fields on the
situation summary; 3-level; capped candidate set.
- **GenerationPipeline** — situation summary → RAG → adopt decision →
generation, run only for the selected speaker.
- **HumanFloorManager** — floor offers, timers, addressed-signal surfacing, AI
pacing.
- **VoteManager** — simultaneous blind locked vote + reveal.

### 4.2 Main loop (spec)

```
start_day_discussion(day):
    if day > 1 and investigator has fresh result:
        mark investigator eligible (round-1 proactive boost)

    utterances = 0
    loop:
        # human opportunity (addressed / periodic), with timer
        if human_should_be_offered_floor():
            msg = await_human(timeout)
            if msg: append(msg); recompute(); utterances += 1; continue

        # deterministic pass — free
        pressure = PressureCalculator.recompute(transcript)
        eligible = EligibilityGate.eligible(agents, pressure, debt)   # Rule 2, round-1, pressure-rank
        candidates = pick_proactive_candidates(eligible, cap=2)        # Phase 2 only

        if eligible is empty and no proactive candidates:
            break                                # convergence
        if utterances >= MAX_UTTERANCES:
            break                                # cap

        speaker = top_by_tiered_score(eligible)  # tiers; random breaks ties only
        # for a proactive candidate, NoveltyChecker (folded in summary) may gate here

        summary = GenerationPipeline.situation_summary(speaker, transcript)  # fresh
        if Phase2 and summary.novelty == already-said: continue              # skip, pop next
        if Phase2 and summary.novelty == borderline and cap_exceeded: continue

        strat = GenerationPipeline.rag_and_decide(speaker, summary)
        msg   = GenerationPipeline.generate(speaker, strat, brief=firing_reason)
        append(msg); DebtTracker.update(speaker); utterances += 1

    VoteManager.run_blind_simultaneous_vote()
```

### 4.3 Signals and where they live

- Pressure, debt, quiet-nudge, Rule 2, round-1, termination, ping-pong guard,
vote → **deterministic** (no LLM).
- Rule 1/3 novelty → **LLM**, folded into the situation summary, capped.
- Persona/voice → **generation step only** (see §5).

### 4.4 Phased rollout

- **Phase 0 — sequential core.** Replace concurrent generation with the
continuous loop. Deterministic scheduler (pressure + debt + tiers + seeded
random). Deterministic eligibility (Rule 2, round-1, pressure-rank). Speaker
cap. Convergence + cap termination. Simultaneous blind vote. Remove the silence
gate from the generation prompt; keep content discipline; pass firing reason as
brief. **No LLM novelty yet.**
- **Phase 1 — human integration.** Floor offers, timers, addressed-signal
surfacing, AI pacing.
- **Phase 2 — proactive novelty.** Add folded Rule 1/3 (3-level, borderline →
cap, 1–2 candidates) *only if* Phase 0/1 shows agents staying silent when they
visibly should speak.
- **Phase 3 — voice (experience).** Persona/voice via prompting (see §5).
- **Phase 4 — style fine-tune (optional).** Only if the drift test (§6) shows
prompted voice decaying across a game, or prompt-scaffolding cost is too high.

### 4.5 Parameters to tune

Pressure type-weights; recency-decay window; debt magnitude (capped below the
addressed tier); quiet-nudge; speaker cap size; novelty thresholds; max-utterance
cap; human floor timer and AI min-gap.

---

## 5. Adjacent decisions (out of core scope, recorded for completeness)

These concern *how the message is produced*, not the speaking architecture, but
were decided in the same discussion.

**Persona / voice firewall.** Personas vary *voice* (register, sentence length,
tics, humor), never *disposition* (aggression, trust, paranoia) — dispositional
traits bias play. Decisions are made persona-blind; persona is injected at the
**realization step** only. Personas are assigned **independently of role** (so
voice carries no role tell) and are **stable within a game**.

**Experience mode (post-evaluation).** Richer disposition genuinely deepens the
deduction loop (gives the human patterns to read). If added, use **game-relevant
behavioral dials** (aggression, talkativeness, trust-default, risk, lead/follow),
**not MBTI** (abstract, stereotype-inducing on weak models, bundles dimensions).
Route by layer: tone → realization; argument disposition → decision;
**participation disposition → scheduler parameters** (or it fights the gate).
Guardrails: a competence floor (personality flavors, never tanks play),
role-independent assignment, consistency over richness.

**Prompting for voice on a weak model.** Concrete surface instructions beat
abstract traits; ban assistant-isms; use a *few* (not many) in-character
examples; re-anchor the persona near the generation point (the bland transcript
is itself an implicit few-shot pulling toward assistant register).

**Fine-tuning.** Naturalness has two axes: *flow* (solved by this architecture)
and *voice* (a model property). Style is the strongest fine-tuning target
(distributional, moves the prior instead of fighting it, cheap data via
distillation) — it beats prompted-flash on voice, consistency, and cost, **not
on play**. The cost savings require a **single model** doing decide+write in one
call, fine-tuned for style *without degrading decisions*. This is de-risked by
the fact that RAG supplies the strategic substance, so the model’s residual job
(adopt + phrase) sits close to the style task. Preserve capability via data
mixing/rehearsal, voice-paired-with-substance exemplars, conservative training,
and regression-testing decision quality. The decide-on-base / style-on-fine-tune
**split protects decisions but adds a call → no cost savings**; keep it only as a
fallback, and in its cheap form (“decide-and-draft → restyle the finished draft”,
where the restyler reads the draft not the transcript), used only if regression
testing shows unacceptable degradation.

---

## 6. Open questions / things to validate

- **Drift test** — does prompted-flash hold a distinct voice across a full game,
or decay back to assistant register? This decides whether Phase 4 is needed.
- **Regression test** — if fine-tuning, measure win rate, structured-output
validity, and adoption sensibility against the base before shipping. Watch
structured-output validity especially; it degrades quietly.
- **Ping-pong stress test** — confirm the novelty gate + cap terminate
adversarial mutual-accusation loops.
- **Threshold tuning** — pressure weights, debt magnitude, cap, novelty levels,
human timing — all need empirical tuning against real games.
- **Human pacing feel** — confirm the floor-offer cadence and AI min-gap don’t
leave the human either steamrolled or waiting.
