# Read/tactic decomposition — retiring the fused merit judge in discussion & night credit

> **What this is.** A design record for the successor to the discussion_tagger's credit mechanism.
> The 2026-07-10 draft was a proposal with five open gates; a 2026-07-11 design review resolved the
> open day-credit questions and scoped a **v1 build** (§8) — what ships, what is accepted as a named
> limitation, and what stays future work. It supersedes the credit approach documented in
> [report.md](report.md) (the shipped tagger) and its trust apparatus in
> [../evaluation/discussion_tagger/report.md](../evaluation/discussion_tagger/report.md); the tagger
> itself survives as a diagnostic instrument (§7).
> **Guiding principle:** a skill you can score against ground truth should never be credited by an LLM
> merit judge; the tagger uses a judge only because it fused two such skills into one verdict.
>
> **Date:** 2026-07-10, revised 2026-07-11 (v1 scope) · **Status:** design record, v1 not yet built ·
> **Store cited for current content:** `memory_stores/v6_1` (SP/observation examples below are sampled
> from it, illustrative of the current extraction — not an exhaustive audit).

---

## 0. TL;DR

- The tagger credits discussion and night play with **one omniscient LLM verdict per player per day**.
  That verdict fuses two separable skills: **reading** (inferring who holds which role) and **tactics**
  (choosing what to do given a belief). Because the two are fused, a bad outcome cannot be attributed to
  a bad read versus a bad tactic, so the only available scorer is a holistic judge — which is why the
  verdict stayed a correlational metric and the night override was never validated.
- The redesign **splits the two skills into two memory types with two credit mechanisms**:
  - **Reads become facts.** A read heuristic is a falsifiable `behavior → role` claim (a *tell*),
    credited by its **empirical accuracy against revealed roles**, agent-independent. No judge.
  - **Tactics stay situation-specific memories**, credited by **outcome, signed by the faction-relative
    value of the target and partitioned by read-correctness** — a wrong read never poisons a tactic's
    ledger. No judge.
- The decomposition is what **retires the LLM merit judge**: the fusion was the only thing forcing it.
- **Day-tactic credit is decided (2026-07-11):** the validated **day-vote endpoint** carries credit in
  v1; the finer **first-link read-delta** runs alongside as a diagnostic and earns graduation on the
  run's own data (§3). Diffuse concealment gets a guarded deterministic **floor** (§3); the
  un-boundable residual is assigned to the tagger-as-diagnostic, never to credit.
- **Injection becomes two channels (2026-07-11):** the tell book and strategy points. Observations
  leave the prompt and remain the synthesis substrate (§4). Tells carry no semantic retrieval — a
  deterministic filter (roles still in play) and rank (shrunk lift) select a small book per turn.
- What gates the build is now short (§8): one load-bearing golden set (the role-blind behavior
  detector), two cheap screens (injection-channel replay, cross-epoch tell transfer), and the
  downstream A/B that was never cleanly run for the tagger either.

---

## 1. The tension

The tagger is one omniscient end-of-day LLM pass. For each player it emits a holistic **discussion
verdict** and, for night actors, a **read-quality verdict** that overrides the deterministic night
credit (the full mechanism is in [report.md](report.md)). Both verdicts answer the same shape of
question: *did this player advance their faction, judged on merit rather than luck?*

That question silently bundles two different competences:

- **Reading** — "player_5 is the wolf." A judgment about hidden state, true or false at reveal.
- **Tactics** — "given that read, shoot player_5 / defend player_3 / widen the suspicion." A choice of
  action given a belief.

These are different skills that fail independently. A player can read perfectly and act badly, or read
wrongly and execute a sound decision procedure on the wrong premise. The tagger cannot tell those apart,
because it collapses them into one verdict. And once they are collapsed, **no deterministic scorer can
recover the credit** — you cannot ask "was the read right" and "was the tactic right" separately of a
number that already blended them. The only instrument left is a holistic LLM judge.

This is the root cause behind the honest caveats the tagger's own reports carry. Its discussion verdict
is validated only as a *correlational metric* (partial *r* with the faction win, N=24, single-epoch),
never as a credit signal that demonstrably improves agents. Its **night override — the one place it
discards a working deterministic signal — has no accuracy check at all** ([report.md](report.md),
gap 4). Both gaps trace to the same source: a fused verdict is un-attributable, so it can only be
trusted correlationally, never decomposed and checked.

The tension, stated plainly: **the tagger needs an LLM merit judge only because it fused two skills that
are each independently scoreable against ground truth.** Un-fuse them and the judge is unnecessary.

## 2. The principle: two skills, two axes, two ledgers

Split every unit of discussion/night merit along the read/tactic seam and score each half by the
instrument that fits it.

| Axis | What it is | Scope | How it is credited |
|---|---|---|---|
| **Read** | what to believe (who holds which role) | universal across roles; **cross-phase** (a read helps discuss, vote, and night alike) | empirical accuracy against revealed roles — deterministic |
| **Tactic** | what to do given a belief | **situation-specific**; phase-partitioned; rich in day, thin at night | outcome, signed by faction-relative target value and **partitioned by read-correctness** — deterministic |

Two facts make the read axis universal rather than a town-only concern. Every role reads; only the
*target* differs — town reads for evil, a wolf reads for the healer and investigator it wants to kill,
a serial killer reads for the wolves. And the measurement is uniform: score the agent's read against the
revealed role, **masking what the role already knows** (a wolf's packmates, an investigator's checks)
and reusing those masked cells as golden probes, since a wolf's read on its own packmate must be correct
or the field is noise.

### The current memory already lies along this seam

The decomposition is not imposed; it surfaces a split the store already half-embodies. Sampling the
`v6_1` store:

- **Day strategy points are almost pure tactic.** A wolf SP: *"acknowledge the vote but frame it as a
  plausible villager error, then pivot suspicion to the voting bloc."* The object-level read ("who is
  the wolf") appears nowhere — synthesis abstracts it out, because an SP must generalize across games
  and cannot name a specific player.
- **Observations are also tactic-shaped**, not read-shaped: every one is `situation → approach →
  outcome`, the same axis as an SP with the outcome still attached.
- **Night SPs are read plus a thin, specific tactic layer.** The *target* is chosen by the read, but a
  real residual tactic survives: risk/timing (*"conserve the bullet early; take the shot at parity —
  the risk of inaction exceeds the risk of a misfire"*), game mechanics (*"in a 1v1v1, shoot the wolf,
  not the night-immune serial killer"*), and threat-prioritization (*"kill the most analytical player,
  not the quiet one"*). None of these is a role-read; each is a decision procedure over the read.

So the read axis is currently **not stored at all** — it is dissolved into SP prose and never credited
as its own thing. That absence is the gap the redesign fills.

## 3. The credit method

Three layers, kept strictly apart, plus a partition rule for tactics.

### Layer 1 — Facts (tells): credited by accuracy, never by application

A **tell** is a discrete `behavior → role` claim, stored as an atomic list item (never fused prose — see
§5). It is credited by its **empirical hit-rate, lifted over the cast base-rate**. "Lift over base-rate"
here means the raw hit-rate minus the prior probability of that role in the cast; a tell that predicts
"wolf" at the ~2/9 base rate carries no information, so only the excess above base is credit. This is
computed **omnisciently and agent-independently**: of all players who exhibited the behavior, what
fraction actually held the role.

Because small samples flatter, the ranked quantity is a **shrunk lift**: the lift pulled toward zero in
proportion to how little support (instance count) backs it, behind a minimum-support floor. A tell that
went 2-for-2 must not outrank one that went 70-for-100. This is not new machinery or a new idea — the SP
prune already ranks on exactly this construction (`shrunk_lift` with a follow floor, held-out
reproduction r=+0.54, n=31 SPs;
`evaluation/src/instrument_validation/credit/heldout_credit_reproduction.py`), and the
concepts are standard: support/confidence/lift from association-rule mining, with an empirical-Bayes
shrinkage against low support. An illustrative entry (no real tells exist yet — the system is unbuilt):

> *"deflected onto their accuser when directly challenged" → wolf · 11 exhibitors, 7 wolves · hit-rate
> 0.64 vs base 0.22 · shrunk lift +0.31*

The direction of the ratio is deliberate: a tell is scored by the **precision** of its rule —
P(role | behavior) — never the recall direction ("of all wolves, how many deflect?"), because the claim
a tell makes is "deflectors tend to be wolves," not "wolves tend to deflect." What a recall metric
would have guarded — does this tell fire often enough to matter — is the support floor's job instead.
The same arithmetic makes vagueness self-punishing: a behavior phrased so broadly that everyone
exhibits it collects the whole cast as exhibitors, its hit-rate collapses to the base rate, and its
lift goes to zero. An over-broad tell never has to be argued out of the book; it prices itself out.

The load-bearing decision here is that **a fact is credited by how accurate it is, never by how well any
agent applies it.** A high-confidence wrong read does not lower a tell's credit — that is an application
failure, handled at Layer 2. This keeps the fact ledger stable: it does not oscillate as the agent
learns, and it never blames a true fact for an agent's misweighting.

One consequence of agent-independence deserves its own sentence, because it simplifies the delivery
design (§4): **tell credit is off-policy.** A tell accumulates support and lift from every game whether
or not it was ever shown to an agent, because the scoring counts exhibitors, not users. A fact the
system just mined can therefore mature in the background and enter the book only once it clears the
support floor — unlike an SP, which must be injected and *followed* before it can earn anything.

Tells are **non-stationary** by construction, and that is the mechanism, not a bug. The same tell that
tells a villager "suspect the deflector" tells a wolf "stop deflecting" — the store improves both
detection and concealment, so its facts shift as both sides adapt. Credit is therefore computed over a
**decay-weighted recent window**: a tell that stops holding as agents adapt sees its recent hit-rate
fall and ages out on its own. The role-constrained core of behavior (a healer must play protectively, an
investigator hoards knowledge it wants to spend) is the durable layer that keeps the store from churning
to noise.

### Layer 2 — Application (the agent's read): Brier, a separate ledger

How well the agent *uses* facts is its own measurement: Brier score of its reads against revealed roles,
knowledge-masked. This is deterministic and **never touches a tell's credit**. It answers "is the agent
reading well," a question about the agent, not about any fact.

The reads themselves ride existing calls (the per-turn read list shipped 2026-07-09; no dedicated
snapshot calls). A stale or lazily-unchanged read simply scores worse at reveal — that is the agent's
deficiency, fairly measured, so read-list laziness does not bias this ledger. Where laziness *does*
matter is the first-link diagnostic, and it is quarantined there (below).

### How the two ledgers separate a bad fact from bad reasoning

The separation is structural, and it is the thing the fused verdict could never do: each failure mode
leaves its fingerprint on a different meter. An **untrue tell** shows up as low lift, computed from
detector counts against revealed roles — no agent's reasoning is in that loop, so no amount of agent
misreading can make a true tell look false, and a false tell looks false even while every agent trusts
it. A **vague tell** is punished twice without a judge: over-broad phrasing collapses its hit-rate to
the base rate (Layer 1 above), and undetectable phrasing is what the detector golden set flags. A
**memorized tell** — true only on its mining distribution — is the cross-epoch gate's target (§8).
**Agent-side failure** is the remaining cell: an accurate book alongside a flat or negative Brier delta
(the free book-versus-no-book readout, §4/§8) says the facts are fine and the application side — model
capacity, attention, the injection interface — is the cap. That last cell is also the honest, testable
form of the project's standing content-versus-capability question.

The limit, stated plainly: the separation is **statistical, not per-instance**. For one specific wrong
read, the system cannot say whether the agent misapplied a good tell or faithfully applied a bad one,
because reads do not cite which tell they used. A citation field could add that and is rejected for v1
(§5) — it re-imports self-report confabulation at the read grain. The aggregate meters are what the
credit system actually needs: it prunes tells and measures agents in bulk, never adjudicating single
reads.

### The tactic ledger: outcome, partitioned by read-correctness

A tactic is a mapping `read → action`; its value is whether that mapping is a good decision procedure.
The problem the tagger could not solve: outcome depends on the read being right, so scoring a tactic by
raw outcome lets a wrong read poison it. The fix the decomposition unlocks is a **partition**:

- **Credit a tactic only on read-correct instances**, where the outcome cleanly reflects the tactic.
- **On read-wrong instances, penalize the read (Layer 2) and exclude the instance from the tactic
  ledger.** Do not ask "was the tactic right for the wrong read" — that counterfactual has no observable
  outcome and would reintroduce a subjective judge. Decline it.

Worked example (vigilante, tactic "at parity, shoot your highest-confidence threat"):

- Reads X as the serial killer, shoots X, X **is** the serial killer → read-correct → **credit the
  tactic**.
- Reads Y as the serial killer, shoots Y, Y is **town** → read-wrong → **penalize the read**; the tactic
  ledger gets **nothing**. The shot failed because the read failed, not because "shoot at parity" is a
  bad procedure.

Tactics whose whole point is handling uncertainty ("shoot only above confidence C") are scored by a
different **aggregation**, not a different mechanism. An ordinary tactic is judged instance by instance
under the partition above. A risk-policy tactic's entire claim is about the average across hits *and*
misses — "at parity, shoot even when unsure" prices its misses in — so excluding the read-wrong
instances would delete exactly the cases the tactic exists to manage, and make every reckless policy
look perfect. Such tactics are scored as a **policy over aggregate outcomes**: the mean de-lucked
outcome over every instance where the policy fired, no exclusion, never a per-instance merit call. The
join is deterministic because the read list records per-target confidence, so "shot X while holding a
high-confidence SK read on X" is a lookup. Synthesis is not being asked to produce this class — it
already does (the `v6_1` parity example above); the open implementation detail is how an SP is flagged
as a risk policy, cheapest as a synthesis-time tag.

### Day-tactic credit — decided: the day-vote endpoint carries it, first-link rides as a diagnostic

Night tactics have a literal outcome: the kill lands or it does not, the shot hits or misses. Day
discussion tactics — deflect, frame, accuse, defend — have no such result, so the day outcome has to be
constructed. The 2026-07-10 draft left this open between two candidates; the 2026-07-11 review resolved
it as **both, with only one credited**:

- **The credited outcome (v1) is the day-vote endpoint**, at two grains. *Day grain:* every discussion
  SP an agent followed that day receives one credit tick, signed by what the day's lynch was worth to
  that agent's faction — the same faction-relative valuation vote credit uses. *Move grain, where a
  target exists:* when a followed SP produced a stance-tagged accusation at a specific player, that
  instance is instead scored against the target's true value (the previously-validated advocacy signal),
  under the valence rule below. The endpoint is the validated free floor (held-out Pearson +0.51, n=51
  SPs, v6ab; [experiment_log.md](experiment_log.md) §1).
- **First-link read-delta runs as a diagnostic, uncredited.** It is computed on the same run data
  (mechanics below), its snapshots riding existing calls — an addressee's next speaking turn or, failing
  that, its vote-time read list; the daily vote covers non-addressed players at day grain. Its
  graduation question is exactly the endpoint's weakness: does move-grain attribution discriminate
  driver from rider, and does that added discrimination predict held-out outcomes better than the smear?
  The arbitration therefore happens on the run's own records instead of needing a dedicated experiment —
  the two candidates were never mutually exclusive as *instruments*, only as the credited channel.

**What day-grain credit means from each seat.** Concretely: a villager who followed two discussion SPs
on a day the town lynched a wolf gets +1 on both — without consulting its reads, and whether or not its
own words helped; on a mislynch day, −1 on both. A wolf's day is positive when the town mislynched, and
also when the serial killer was lynched (the SK is the wolves' rival faction, and it is night-immune —
the vote is the only weapon against it); negative when a packmate fell. The serial killer's day is
positive when it survived the vote and the lynch removed someone else, negative when it was voted out.
Reads barely enter this layer, by design: a deceiver's read skill is measured at Layer 2 and its night
ledger, and its self-heat management by the concealment floor below. Why so coarse a signal ranks SPs
at all: one day says nothing, but an SP is followed across many days and games, and systematically bad
advice accumulates more negative days — the held-out +0.51 is the evidence that day grain still
separates good discussion SPs from bad ones. What it structurally cannot see is driver versus rider:
whether *this* move diverted heat onto *this* target. That gap is precisely the first-link diagnostic's
job.

**The valence rule for targeted day moves (unified, deterministic).** A targeted move is scored on two
independent questions, both answerable from recorded data without an LLM: **did it work**
(persuasion-success — at day grain, did the lynch land where the move pushed; at first-link grain, did
the addressees' reads shift that way) and **was the target worth pushing** (what the target's lynch
would be worth to the mover's faction — a true-roles lookup). The draft's open problem was that
read-correctness gating seemed to split by faction: town persuasion of a misread target is bad play,
while a wolf framing an innocent has no genuine read to gate on. The resolution is that the second
question, answered by **each faction's own vote-credit valuation, reused**, already carries everything
the gate was for:

- **A deceiver's move is scored by the two questions alone — no gate.** The wolf valuation covers the
  cases faction-splitting got wrong: pushing the room onto any town player is positive value (a
  mislynch), pushing it onto the serial killer is positive value, and pushing onto a packmate is scored
  by the wolf vote channel's **bussing-aware** form — steering with the room's plurality counts
  positive even at a packmate, so a deliberate bus is not mis-punished as treason. (The raw roles-lookup
  alone would score a dead packmate negative; the bussing-aware scorer, already shipped in the vote
  channel, is what handles it.)
- **For town, the read gate falls out as a special case**, because "the target is worth pushing" and
  "the mover's read on the target was correct" are the same lookup — the target really is a threat. On
  the read-wrong case (a villager gets the room to pile onto another villager), the instance is
  **excluded** from the tactic ledger and the read is penalized at Layer 2, per the partition rule: the
  component that failed was the belief, not the decision procedure, so the target's negative value is
  never used to write a minus against the tactic.
- **Self-defense needs no gate** — the mover knows its own role, so the goal is legitimate by
  construction and only persuasion-success is in question. A deflection that redirects at a third
  player is an accusation at the redirect target, scored as offense.

Worked micro-examples (illustrative): a villager accuses the real wolf and the room lynches it → worked
× good target → tactic credited. The same villager accuses another villager and the room follows →
worked × misread target → instance dropped, read penalized. A wolf frames a villager and the room
follows → worked × positive wolf value → tactic credited. A wolf leads the pile onto the serial killer
→ tactic credited, no read consulted.

**Intent comes from different fields by faction, deliberately.** Persuasion-success needs a direction —
what the mover *wanted* the audience to believe. For town, the mover's own structured read list declares
it: accusing T while privately reading T as wolf means the intended direction is "T reads more wolf." A
deceiver's private read cannot serve as intent, because deception decouples belief from move by design —
a wolf can privately (and correctly) read T as villager while publicly pushing T toward wolf, and
scoring against its private read would grade its most successful frame as a failure. So deceiver intent
is read off the **stance tag** of the move itself: accusation-stance intends the target to read more
evil, defense-stance intends the target (or self) to read more town. Both sources — the read list and
the `addressed_targets` stance tags — are structured output already on the record; neither needs an
LLM.

**The herding adjustment (applies to the diagnostic).** The raw first-link delta systematically flatters
the least skilled move: joining an existing pile-on collects the room's momentum as if the mover caused
it. The fix is a **momentum-adjusted delta**: subtract the target's pre-utterance read trajectory (the
shift predicted by prior accusations on that target that day), so a bandwagon move scores near zero and
a move that starts or reverses a trend keeps its delta. A within-day control using non-addressed players
was considered and rejected — the day channel is public, so bystanders hear the utterance too and are
treated, not controls (§5). What remains after the adjustment is a residual the design accepts and
names: "persuaded the room" and "read the room about to turn and spoke first" are not fully separable.
That residual confuses two *skills* with each other, not skill with luck, which is why it is tolerable
in a diagnostic.

**Two instrument caveats, quarantined to the diagnostic.** First, the read list under-reports change:
under the shipped reads-first ordering, roughly 40% of "unchanged" entries were diagnosed as cold filler
rather than honest no-update (replay probes,
[../generation_prompt/validation/](../generation_prompt/validation/)), which undercounts deltas — the
diagnostic must be interpreted alongside the filler rate, and the already-planned composition-coherence
re-arbitration of read ordering is its upstream fix. Second, the delta lattice is coarse
(`{unclear|role} × {low|high}` over 1–3 addressees), so per-tactic instance density may be thin; a free
census (instances per tactic per run) is a pre-registered readout that qualifies any conclusion drawn
from the diagnostic.

### The concealment floor — a guarded deterministic slice of the diffuse residual

Diffuse deceiver skill — never becoming worth accusing at all — produces no targeted move, so neither
the endpoint refinement nor first-link can see it. The tagger's post-mortem showed why the obvious
deterministic score is a trap: "concealed = low heat + survived" collapses into "won," most completely
for the serial killer, whose heat, lynch, and death are one channel
([experiment_log.md](experiment_log.md) §2). v1 still credits a bounded slice of it, with the guards
that keep the floor from becoming that tautology:

- **The signal:** per-day heat-delta (suspicion drawn that day), credited to a followed
  **concealment-type SP** — intent is declared by the agent's own adoption, not inferred.
- **Guard 1 — normalize by opportunity.** Heat is scored relative to the day's total accusation volume.
  A day when the room was busy elsewhere gives every deceiver zero heat for free; normalization stops
  quiet days from crediting anyone's concealment.
- **Guard 2 — participation required.** The agent must have spoken that day for the concealment SP to
  score. Without this, silence farms the credit, and the store re-learns the passive play the credit
  prune just removed.
- **The named confound, accepted:** luck-of-attention. Low heat can mean the town had better targets
  rather than that the agent concealed well; the guards bound this, they do not remove it. The floor is
  most halo-prone for the SK (one channel), least for wolves. The residual — believed-because-plausible
  versus believed-because-unscrutinized — is assigned to the tagger-as-diagnostic (§7), never credited.

### Attribution — v1 uses self-report, bounded, with the matcher deferred

Crediting a tactic asks two questions: *which* tactic did the agent apply (attribution), and *was it
good* (valence). Valence is the read-partitioned, value-signed outcome above, and it is deterministic —
no LLM ever decides it. For attribution, v1 uses the agent's **self-report** — which is not new
machinery but the existing follow join (`strategy_verdicts` → key), the same one vote credit already
rides. Its known weakness is calibrated rather than ignored: agents follow ~99% of applicable SPs
(v6ab eval-cases, `evaluation/src/instrument_validation/credit/g3a_verdict_validity.py`), so
"I followed it" barely discriminates, and some credited decisions were not genuinely shaped by the
tactic. Because valence is deterministic, the damage is **dilution, not bias** — smeared credit, the
same failure mode the endpoint already accepts. The v1 bound: hand spot-check ~15 self-reports against
what the action actually did and record the rule-of-three error bound alongside the ledger. The
alternative — an **outcome-blind matcher** that decides which tactic an action instantiates — answers
*which*, never *whether it was good*, so it stays a detector rather than a judge; it is deferred to
future work because it is the fuzzier detection problem and earns the harder golden-set gate.

### Scoring mechanics (post-game)

Two passes per game:

1. **Tell mining** (rides the existing post-game observation extraction) — cluster observed behaviors
   against revealed roles into `behavior → role` tells. Reuses the existing dedup/clustering machinery,
   partitioned by the tell, not by situation regime.
2. **Behavior detection** (one **role-blind** LLM pass) — for each player, which trigger-behaviors are
   present in their transcript, checked against the **active checklist**, not only the injected book
   (*amended 2026-07-12 from "full tell corpus": the 5-game probe measured mining yield at ~40
   tells/game, so an unbounded scan is a long-input attention failure and a linear cost leak; the
   bounded active tier below preserves what the original rule protected — uninjected-but-active
   candidates still accumulate counts off-policy*). Role-blindness is the leak-guard: if the detector saw that a player was a
   wolf, it could rubber-stamp "yes, they did wolf-behavior," and the hit-rate would be circular. Detect
   from the transcript alone; compare to revealed roles only afterward. The match is **binary** —
   behavior present or absent, per player per game — and the "similar enough" threshold lives inside
   this pass, which is why it carries the build's one load-bearing golden set (§8). **Scheduling
   (decided 2026-07-11):** the detector runs per-game at loop credit time — one cheap call per game — and its
   counts accumulate under the same windowed set-not-accumulate semantics as every other credit counter,
   so tell credit ages consistently with SP credit.

A tell is then scored on **every player whose behavior triggers it** — many instances per game, not one
— and co-applying tells each score independently on the same player. The agent's reads never enter this
computation.

### The tell ledger spec (decided 2026-07-12, from the 5-game probe's dedup + distinctness findings)

The probe (`evidence/extraction/tell_extraction/`) forced the storage design early: 5 games mined to
213 instances → 107 audited-distinct tells, so an unmanaged store grows fast and the scan cost must be
decoupled from store size. Three tiers, with the strict bound exactly where the per-game cost is:

| Tier | Bound | Role |
|---|---|---|
| **Book** (injected) | ~3 per unrevealed role | what agents read; top of the incumbents by shrunk lift |
| **Active checklist** (detector-scanned) | **hard cap N per channel** (vote / discussion) | the only place counts accumulate; two lanes — *incumbents* (earned discrimination: shrunk lift over a support floor, with a direction-balanced quota so every role's book has candidates) + *probation* (every newly mined tell, scanned for K games regardless of rank — entry can never require counts, because scanning is what produces them) |
| **Archive** (everything else) | unbounded | full record, instances retained; zero scan cost |

- **Dedup is drop-or-keep, never merge** (owner ruling, mirroring the SP/obs online pass): a newly
  mined behavior that matches an existing tell has its *wording dropped at the door* — canonical text
  is never rewritten — while its **instance row is always kept** and credited to the surviving tell
  (for tells the instance IS the product; a discarded instance is a lost count). Wording repair is a
  manual/audit-pass prerogative only.
- **Dedup runs at epoch boundaries, not online** (amended 2026-07-12 after the 30-game ledger
  simulation, log §10–12): the online LLM judge was the costliest per-game component (~178
  flash-lite calls/game) *and* the least accurate (pairwise, top-5 neighborhood — it fragmented
  head-tell support ~2×, which the whole-family batch pass then had to repair). Nothing time-critical
  consumes its output: tells have no same-game consumer (unlike observations, which inject into the
  next prompt and therefore keep their online pass), and a ≤10-game entry delay is immaterial against
  a K=12 probation window and n≥20 lift floor. Between epochs only free normalized **exact-match**
  runs; the LLM judgment happens once per fold, with full-family context.
- **Instance schema:** `tell_id · game_id · exhibitor (player_id) · revealed_role (joined
  deterministically from the record) · source (MINED | DETECTED) · quote (mined only)`. All tallies
  are **recomputed from instance rows** (set-not-accumulate, windowable) — never incremented counters.
  **Only DETECTED rows feed lift** (role-blind, complete denominators); MINED rows are discovery and
  recurrence evidence only (omniscient mining is salience-biased — the in-sample halo).
- **Retention:** probation tell still a singleton after K scanned games → archive (selection on
  evidence volume, direction-neutral). Incumbent with **fat support + null lift** (evil share of
  exhibitors ≈ cast prior at trusted n) → **split-check first** (re-cluster its retained instances;
  a null blend can hide two directional sub-tells, e.g. motive-attacking deflection vs
  record-citing deflection), then archive as measured-and-uninformative. Never retain-rank by lift
  at thin support — that selects on noise and locks in early luck; the probe's cleanest town tell
  (accuse-then-vote, 0/6 evil) began as a lift≈0 singleton that a top-N-by-lift rule would have
  culled unseen.
- **Promotion back from archive:** (a) mining recurrence — a new mined match against an archived tell
  re-enters it into probation at the next fold (mining runs every game anyway, so re-discovery is
  ambient); (b)
  **spare-slot rotation** — unused checklist budget is filled with least-recently-*scanned* archive
  entries, so every archived tell eventually re-earns or re-fails on fresh counts at zero marginal
  cost; (c) the periodic strong-model distinctness audit (the batch pass of the house dedup
  architecture, first run 2026-07-12) may promote, split, or re-word by judgment.
- **The lifecycle is quantized to checklist epochs** (amended 2026-07-12; replaces the per-game loop).
  *Per game:* mine (2 flash-lite calls/day, channel-split) → exact-match accumulate into raw rows →
  detector scans the **frozen checklist v_k** per player. *Every N=10 games (the fold):* LLM dedup
  folds the epoch's new wordings into the frozen canon (**freeze-old**: new either dies into an
  existing canonical or becomes a new one — proven text never rewritten, so detected counts stay
  valid across versions) → recompute tallies from instance rows → probation verdicts, admissions,
  retirements, archive re-entries → publish **checklist v_k+1**. *Every ~30 games (the audit):* the
  strong-model pass — re-cluster within canon, split-check fat nulls, wording repair by judgment
  (first run 2026-07-12: 740→596, log §11). A frozen checklist per window also gives the detector
  clean, comparable denominators — no mid-window churn in what was scannable.
- **Store size itself is never capped; each scale cost has its own bound.** The checklist cap bounds
  attention and credit; the fold + audit bound head fragmentation; and the **dedup match index**
  (the only component that rots with store growth — stale singletons crowd the embedding
  neighborhood and worsen under-merge) sheds singletons not re-seen for ~40–50 games (≈ a prompt
  epoch). Index retirement drops the tell from *comparison only* — rows stay; the accepted cost is
  losing recurrence re-entry for late bloomers beyond that horizon (measured cohort recurrence was
  already down to ~11% within 10 games).
- The tell's shrunk lift over the cast prior IS its credit; the agent-skill Brier ledger is untouched
  by any of this. Credit-eligible tiers: the incumbent lane and the book. Probation and rotation
  slots accrue detected counts but never charge an agent's read — they are evidence-gathering only.

### The shared substrate: observations, tells, and tactics are three annotations

The two passes above are not new machinery. They are re-keys of the post-game behavior extraction the
observation pipeline already runs. Observations, tells, and tactics are three annotations over one
extracted behavior:

| Artifact | = behavior + … | keyed by | perspective |
|---|---|---|---|
| Observation | situation + **outcome** | how it went | first-person (what the actor did) |
| Tell | **revealed role** | what the actor is | third-person (behavior → role) |
| Tactic (SP) | generalized situation → behavior | the prescription | distilled from observation clusters |

So a tell is an observation's *behavior* re-keyed by the actor's revealed role, and the counting is
identical: an observation dedups by incrementing a recurrence count, and a tell's hit-rate is that same
count split by the revealed role into hits and misses. The behavior-detector is therefore not a wholly
new component. It is observation extraction re-keyed, which lowers both its cost and its risk.

Three constraints keep the reuse sound:

- **Behaviors must be objectively described, not role-inferential.** "Stayed quiet" or "deflected onto
  the accuser" can be correlated with a role; "acted wolfish" cannot, because the label already encodes
  the answer. Objective description is what lets a tell be mined even from role-aware observation
  extraction.
- **Each pass is blind to what it would leak.** Tell detection is blind to the role; a tactic-matching
  pass is blind to the outcome. Without the blind, the credit is circular.
- **Tactic credit never reads the observation's stored outcome.** The observation carries a `net_verdict`
  calibrated to who won, which is the outcome halo. Tactic credit uses the read-partitioned outcome
  instead, or it re-imports the very halo the redesign removes. And because an observation also records
  the actor's private intent, tell mining uses only its observable slice, never the reasoning.

### Why this retires the LLM judge

The argument is one line: **the tagger needed a merit judge only because read and tactic were fused into
one verdict with one outcome; separating them lets every half be scored against ground truth.** Reads
become facts with a truth value (accuracy). Tactics become procedures scored on value-signed,
read-partitioned outcomes. Read-quality of the acting agent becomes Brier. None of the three needs a
judge.

What remains are **detectors, not judges**: a role-blind pass for which behavior a player showed, and —
when matching replaces self-report — an outcome-blind pass for which tactic an action instantiated. Both
answer a *checkable* question against the record; a human can verify them and a golden set can grade
them. Neither decides *whether the play was good*. That is the line the redesign holds: merit leaves the
LLM entirely, and only detection stays.

## 4. The tell book at generation time

Credit determines which tells are trusted; this section is the delivery design — how trusted tells reach
a live agent. All decisions here are from the 2026-07-11 review.

**Injection becomes two channels: the tell book and strategy points.** Observations leave the prompt and
remain the synthesis substrate — still extracted, still stored, still the raw material SPs are distilled
from, just no longer injected. Three reasons. Prompt load: three memory blocks alongside the read-list
task is more context than the generation model handles well. Functional overlap: injected observations
and SPs serve the same prescriptive intention from two directions, where tells + SPs make one clean
pair — *how to read, and what to do with your read*. And test scope: the loops under credit-and-compound
test are the tell and SP ledgers; observations ride frequency and decay, not credit, so keeping them
injected adds load without adding to what the run measures. One boundary sentence this swap obligates:
the project's validated static-memory result rode **observation** injection, so that claim attaches to
the old architecture and is not re-proven here — this system's effectiveness claims start from its own
runs. The residual risk is hedged rather than assumed away (§8): a cheap frozen-decision replay screen
confirms the tell channel moves decisions at all before any paid run, and the Brier delta (book present
vs absent on the same reads) is a free in-run readout of the same question.

**Placement: immediately above the agent's private reads block.** Evidence before belief — the book is
the how-to-read manual and the read list is the output it should improve, which is also what makes the
Brier delta a direct measurement of the book's value. It is a dynamic per-turn block and sits with the
other per-turn state, after the stable prompt prefix (cache-layout rule,
[../../docs/generation_prompt.md](../../docs/generation_prompt.md)).

**Selection is a deterministic filter and rank, not retrieval.** Filter: drop tells about roles already
revealed dead (the dead-roster state makes "roles not yet revealed" a free lookup — a healer-tell after
the healer's public death is dead weight). Rank: shrunk lift (§3), behind the support floor. Cap: ~3
tells per unrevealed role (≈15–18 on day 1, shrinking as roles reveal), with token cost and book
composition checked in the build smoke. The cap is a knob, not a finding.

**No exploration slot.** The SP retrieval design reserves slots for unproven entries because SP credit
is usage-gated — an SP never injected can never be followed, so never earns; that is a bandit problem,
and exploration is its price. Tell credit is **off-policy** (§3, Layer 1): a new tell accumulates
support from every game's exhibitors whether or not it was ever injected. Exploration therefore buys
nothing for tell credit and costs something real — an unvalidated tell in the book actively misleads
live reads and degrades Brier. The book injects only support-cleared tells; candidates mature in the
background for free.

**No stage-segmented selection.** Segmenting the book by game stage or situation dimensions was
considered and rejected for v1 on three grounds. The project already screened structured
dimension-matching for retrieval and it was flat (does_not_apply 38%→36%, n=24 held-out town day-votes,
`evaluation/src/instrument_validation/dimensions/dimension_gating_screen.py`) — a scoped precedent, not
a closed question: that screen predates the deterministic-dims fix, so its query-side enums were
LLM-extracted, and the decision here rests mainly on the two grounds that follow. Segmentation fragments the hit-rate counts, so
every cell's credit converges slower on the same games. And a tell's condition belongs in its *text*
("deflects **when accused at parity**") — the detector detects the conditioned behavior, so conditioning
needs no retrieval machinery. The escape hatch is free and pre-registered: stage-conditional hit-rates
are computable post-hoc from the same counts (hit-rate by alive-bucket), and a tell whose rates diverge
by stage is **split** into conditioned variants. Measure the need before building the machinery.

**No synthesis pass for tells.** SPs need batch synthesis because raw observations do not generalize —
an LLM must abstract clusters into a portable directive, and that new text then earns trust through
follows. A tell is born general: `behavior → role` names no player and no game, so generalization
already happened at mining time. "Synthesizing" tells — merging several into a broader claim — breaks
three things at once: the merged claim is new text, so its parents' accumulated hit-rates do not
transfer (the same credit-continuity argument that rejected SP merge); prose fusion destroys per-claim
falsifiability (§5); and lumping heterogeneous behaviors averages their hit-rates, destroying exactly
the calibration the book exists to provide. The aggregation tells need is already in the machinery:
dedup-merge of same-claim duplicates pools counts (evidence pooling, like observation merge), and the
one synthesis-shaped future op is the conditioned **split** above — the opposite direction from merge.

## 5. Alternatives considered and rejected

- **Keep the fused LLM verdict (status quo).** Rejected as the whole premise: un-attributable, so
  trustable only correlationally, and its night override is unvalidated. The decomposition exists to
  remove the fusion that forces the judge.
- **Score a tell by how many of the agent's read-errors it would fix (net-error-reduction).** Considered
  and rejected. It makes a fact's credit depend on *whose* agent applies it, so the same fact scores
  differently for a strong and a weak agent; it oscillates (a tell "helps less" once the agent learns
  it, gets dropped, the agent forgets, it "helps again"); and it blames a true fact for the agent's
  misweighting. A fact's credit must be its accuracy. Utility is a separate, application-layer question.
- **Score a tell only where the agent actually used it.** Rejected: the agent's reads are a biased,
  incomplete sample, so a valid tell the agent never happens to use would look worthless. Score tells on
  all applicable players instead.
- **A "which tell did you use" citation field on the read list** (per-instance attribution of reads to
  tells). Rejected for v1: it re-imports self-report confabulation at the read grain and spends output
  tokens on it; the two-ledger separation is statistical by design (§3), which is sufficient for
  pruning tells and measuring agents.
- **Store tells as prose (a paragraph of behavioral patterns per role).** Rejected: prose fuses many
  claims into one blob that cannot be scored per-claim, reintroducing exactly the smearing the
  decomposition removes. Tells must be a discrete, individually falsifiable list.
- **Credit day tactics by first-link read-deltas.** Resolved 2026-07-11 from "leading candidate" to
  **diagnostic-only in v1**: the day-vote endpoint carries credit, and first-link's graduation case is
  argued and bounded at §3 — including the herding adjustment it would need and the read-list filler
  rate that currently degrades it.
- **A bystander contrast as the herding control.** Rejected: the day channel is public, so non-addressed
  players hear the utterance too — they are treated, not controls, and "everyone moved" is genuinely
  ambiguous between broad persuasion and room momentum. Only the temporal baseline (the target's
  pre-utterance trend) distinguishes those, hence the momentum adjustment (§3).
- **An exploration slot in the tell book** (the SP retrieval pattern: mostly-proven plus one novel
  entry). Rejected as unnecessary for tells and mildly harmful: tell credit is off-policy, so novel
  tells mature without injection, and injecting unvalidated reads degrades live Brier (§4).
- **Stage/dimension-segmented tell selection.** Rejected for v1 — screened-flat precedent, count
  fragmentation, condition-in-text; revisit on the free stage-conditional hit-rate check (§4).
- **A batch synthesis pass for tells** (the SP pattern). Rejected: generalization already happened at
  mining; merge breaks credit continuity, falsifiability, and calibration (§4). Dedup-merge and the
  conditioned split cover legitimate aggregation.
- **Keep observations in the prompt alongside tells and SPs.** Rejected: prompt load, functional overlap
  with SPs, and observations are not under credit test (§4). They remain the synthesis substrate.
- **Staged retrieval (retrieve reads, form the read, then retrieve tactics conditioned on it).**
  Rejected: it doubles the generation call, and it is unnecessary because tactics are keyed by situation,
  not by the read. Retrieve both memories in parallel, in one call.
- **Collapse tactics to a wholesale-injected book like tells.** Rejected: what a player should *do* is
  genuinely situation-specific, so the tactic corpus is large and only a situation-matched subset is
  relevant per decision. That is precisely the condition RAG exists for; tactics keep it.

## 6. The decision and its named tradeoffs

Adopt the two-axis decomposition, scoped as the v1 build in §8: reads as accuracy-credited facts ranked
by shrunk lift, tactics as outcome-credited procedures (value-signed, read-partitioned), application
quality as a separate Brier ledger, day credit on the endpoint with first-link diagnostic, a guarded
concealment floor, self-report attribution, and two-channel injection. The tradeoffs, named:

- **Excluding read-wrong instances shrinks the tactic-credit sample.** A tactic that was sound but rode
  a wrong read contributes nothing to its ledger. Accepted: a clean deterministic signal on a subset
  beats a subjective signal on all instances, and tactic credit accumulates across games where reads are
  right often enough.
- **Endpoint credit smears within a day.** The credited day outcome cannot separate the player who drove
  a lynch from one who rode it; every followed SP on a won day shares the credit. Accepted for v1
  because the endpoint is the validated instrument and the smear is dilution, not bias; the first-link
  diagnostic exists precisely to show whether finer attribution is worth graduating.
- **Self-report attribution dilutes.** Near-ceiling follow rates mean some credited decisions were not
  genuinely shaped by the tactic. Accepted with a measured bound (the n≈15 spot-check) because valence
  stays deterministic, so the failure mode is smearing rather than wrong-signed credit; the outcome-blind
  matcher is the future upgrade.
- **The concealment floor can credit luck-of-attention.** The two guards (opportunity normalization,
  participation) bound the halo, they do not remove it, and the SK cell is the most exposed. Accepted
  because the alternative is either crediting nothing for concealment or re-admitting a judge; the
  un-boundable residual goes to the diagnostic tagger, never to credit.
- **Dropping observation injection risks the delivery channel, not the measurement.** If tell injection
  turns out not to move decisions, a flat compounding result would be misread as "the loop doesn't
  compound" when the channel was dead. Accepted only behind the §8 hedges: the injection-channel replay
  screen before spend, and the in-run Brier delta.
- **A true-but-useless tell still scores well.** Accuracy credits a fact for being correct even if every
  agent already knows it. Accepted because the capped book makes a redundant fact nearly free, and the
  aggregate Brier delta catches a book that adds no lift.
- **The detectors are the remaining subjective components.** v1 rests on one: the role-blind behavior
  detector behind every hit-rate — partly de-risked as a re-key of observation extraction, but still the
  single point of failure, and it gets the one load-bearing golden set (§8). The tactic matcher, the
  fuzzier second detector, is deferred along with its harder gate.

## 7. Consequence: the tagger's status, and where RAG concentrates

**The tagger is demoted from credit to diagnostic — a decision now, not a speculation.** Two concrete
changes ship with the v1 build. Its **night read-quality override is retired from loop credit**: night
credit returns to the deterministic de-luck scorer, refined by the read-partition of §3, so the loop
carries one night credit mechanism instead of two. And its per-day verdict keeps running as a **standing
diagnostic metric** — a diagnostic may explain a result and flag what credit cannot see; it never feeds
prune, protect, or synthesis track records. This keeps the one validated instrument for deceiver
day-craft (discussion verdict partial *r* +0.56 wolf / +0.60 SK with faction win, blinded and
verbosity-controlled, N=24, single epoch — [report.md](report.md)) pointed at exactly the residual the
credited channels do not cover: believed-vs-unscrutinized credibility, tone, the concealment beyond the
§3 floor. Because it no longer carries credit, its uncalibrated sub-tags stop being load-bearing, and
its golden set stops gating anything. The decomposition itself still owes the downstream comparison
(§8, gate 5) — demotion is a design decision; superiority is a result the run has to produce.

**RAG's justification concentrates in day discussion.** Retrieval earns its keep only where the corpus
is too large to inject wholesale and only a situation-matched subset is relevant per decision. Day
tactics meet that test; night tactics are thin, and tells meet neither — a small fact book selected by
deterministic filter and rank (§4), no semantic retrieval at all. So the decomposition does not diminish
RAG so much as localize it to day discussion — which is where the memory system's measured lift always
lived.

## 8. The v1 build scope, and what still gates it

The 2026-07-11 review's output is this line between built, bounded, and deferred.

**Ships in v1:** the tell ledger (mining re-key, per-game role-blind detector, shrunk-lift ranking,
windowed counts) · the Brier ledger · night tactic credit, read-partitioned, replacing the tagger
override · day tactic credit on the day-vote endpoint with the target-value refinement · the concealment
floor with both guards · self-report attribution with the spot-check bound · two-channel injection
(tell book: placement, roles-alive filter, ~3/role cap) · first-link computed as a diagnostic with the
momentum adjustment · the tagger running as a diagnostic metric.

**Accepted limitations (named in §3/§6, summarized):** endpoint smear · self-report dilution (bounded) ·
concealment luck-of-attention (guarded, SK-heaviest) · herding residual in the diagnostic ·
read-list filler degrading the diagnostic (upstream fix is the read-ordering re-arbitration) ·
no credit channel for diffuse credibility/tone (diagnostic coverage only).

**Future work:** the outcome-blind tactic matcher and its golden set · first-link graduation to a
credited channel if the diagnostic earns it · the conditioned tell split if stage-conditional hit-rates
diverge · tell retrieval only if the book outgrows its cap's usefulness.

**What must still happen before credit is trusted (the surviving gates, re-statused from the
2026-07-10 draft's five):**

1. **The behavior-detector golden set — open, load-bearing, first.** 30–50 stratified cases grading
   detection accuracy plus a check that role-blindness holds. Every hit-rate rides this pass; nothing
   downstream is trustworthy until it is bounded. (Replaces the tagger golden that the demotion made
   moot.) The tell **dedup judge** is the second LLM in the counting path — same-claim merging, reusing
   the existing two-stage pattern (embedding prefilter → LLM judge; cosine is never the judge). Its
   asymmetry sets its bar: a missed merge only splits support (conservative), a wrong merge pools counts
   of *different* claims and miscalibrates hit-rates. New prompt to engineer; earns a spot-check bound
   (n≈15–20), not a full golden.
2. **Cross-epoch tell transfer — open, cheap.** Mine tells on the v6ab archive, score their hit-rates on
   current-epoch games. A tell that only works on its mining distribution is a memorizer, not a
   read-learner; tells sit on top of the meta, so this is the difference between learnable and
   memorized.
3. **The injection-channel replay screen — open, cheap, before any paid run.** Frozen decisions replayed
   with and without a tell book, on the existing decision-replay engine. It answers only "does the
   channel move decisions at all" — the hedge §6's observation-drop tradeoff requires.
4. **Tell-book size — resolved by construction, watched in smoke.** The cap and roles-alive filter bound
   the prompt cost; what the smoke still checks is composition (does a top-K book keep useful coverage
   across target roles) and token load. **Detection is the separate scale surface:** the detector scores
   the full corpus each game (see Scoring mechanics), so corpus growth is a first-run readout — dedup
   and claim saturation are expected to bound it, and tells persistently below the support/lift floor
   can be archived out of active detection if it does not.
5. **The day-tactic outcome — resolved by scoping.** Endpoint credits, first-link diagnoses; graduation
   criteria live in §3. No pre-build experiment required.
6. **The downstream A/B — open, the run itself.** Decomposed credit versus the fused verdict, measured
   by agent improvement over generations, was never cleanly run for the tagger either. It is the final
   gate, and the run that answers it pre-registers its arm composition (tells + SPs injected,
   observations as substrate), one primary endpoint, and a stopping rule before launch.

Free pre-registered readouts that ride the run: the Brier delta (book vs no book), the per-tactic
instance-density census, and the endpoint-vs-first-link comparison.

## 9. Lessons

- **A fused signal forces a judge; decomposition removes it.** When two independently-scoreable skills
  are collapsed into one number, no deterministic scorer can recover them, so the only instrument left
  is a holistic judge. The judge is a symptom of the fusion, not a necessity of the problem.
- **Credit a fact by its accuracy, never by how well someone applies it.** Mixing application quality
  into a fact's credit makes the credit depend on the applier, oscillate as the applier learns, and
  misattribute the applier's mistakes to the fact. Keep the knowledge layer and the application layer
  strictly apart.
- **Partitioning on a cleanly-measurable variable de-confounds without a judge.** A tactic's outcome is
  confounded by read quality; conditioning credit on the read-correct subset isolates the tactic
  deterministically, at the cost of a smaller sample — a trade worth making to avoid a subjective signal.
- **Off-policy credit removes the exploration problem.** A ledger scored on all exhibitors (tells) needs
  no explore slot: entries mature without being served. Only usage-gated memory (SPs, follow-credited)
  faces the bandit trade, and porting exploration machinery across that line adds risk with no return.
- **When a finer instrument is unproven, credit the coarse validated one and let the finer one ride as a
  diagnostic.** The endpoint-vs-first-link fork never needed deciding by argument: crediting the
  validated floor while computing the candidate alongside turns the run itself into the arbitration —
  and keeps an unvalidated instrument from ever touching the store.
- **Retrieval is justified by corpus shape, not by reflex.** RAG earns its place only where the corpus is
  large and per-decision relevance is narrow. The same project can justify RAG for one memory type
  (situation-specific tactics), rule it out for another (a small fact book, filtered and ranked
  deterministically), and demote a third from the prompt entirely (observations, substrate-only).
