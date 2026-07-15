# Situation Dimensions — design & reliability journey

> **What this is.** The chronological record of how the memory system's *situation dimensions* — the
> structured, state-describing fields on every stored observation and every live retrieval query — grew from
> one prose paragraph into a per-cell schema, and how far each field can actually be trusted. It keeps its
> real corrections in place: a "core dilemma" dimension that felt right and scored net-negative (§3); a
> criticality-conditioning lever a same-game leak inflated and a temperature re-draw then erased (§6); and a
> family of LLM-filled fields a $0 audit found were, in two cases, *worse than a constant* (§7).
>
> **Companion docs.** The shipped design, stated destination-first, is in [report.md](report.md). The dated
> primary records this consolidates are linked at each section and gathered in [Sources](#sources): the
> situation-summary golden study, the v6 build spec, the phase-B screens, and the eval-hardening audit.
>
> **Guiding invariant.** A dimension states *what is true on the board, in the agent's epistemic voice, with
> zero should/recommend language* — **"situation = state, never prescription."** The advice ("how to act")
> is the retrieved *payload*, never a matching field; that one rule is what lets the same fields serve
> retrieval, gating, and reward without contradiction — all three *read* the situation, none of them *are*
> the advice.

## Where situation dimensions sit — and why they exist

Two processes touch the memory store, and they never meet. **Post-game extraction** reads a finished game
and writes lessons into the store, each lesson tagged with a *situation* — a description of the board state
the lesson applied in. **Live retrieval** runs on every agent turn: the agent describes its *current* board
state as a query, retrieval embeds the query and every stored situation into vectors, and returns the stored
lessons whose situation vector sits nearest the query's by cosine similarity.

The catch is that the stored situation and the query are written by **different processes, at different
times, from different viewpoints** — one by an offline extractor reading a whole finished game, the other by
a live agent mid-decision who can see only its own role's information. They only find each other in embedding
space if both describe the board in the **same vocabulary and structure**. That is the **alignment problem**,
and it is the one thread the whole journey follows: every design move below makes the write side and the read
side describe the same board the same way, so a query lands next to the lesson it needs.

The alignment problem is also why the two rules that govern every dimension are structural, not stylistic:

- **Epistemic voice — both sides speak from the same knowledge level.** A stored situation written
  *omnisciently* (naming the hidden wolves) could never be matched by a query written by an agent who cannot
  see them: the two descriptions would diverge exactly on the facts the live agent lacks. So every dimension
  is phrased in the agent's own epistemic voice, on the write side and the read side alike.
- **State, never prescription.** A dimension names board state, never advice. Advice in a matching field
  would make *every* query match the same generic counsel regardless of board — destroying the very
  discrimination retrieval exists to provide — and would leak "how to act" into the query prompt (the
  prompt-boundary leak the project guards elsewhere). The advice is the retrieved payload; the situation is
  only the address it is filed under.

*Provenance.* Curated 2026-07-04 on `feature-dimension-schema`; the underlying work spans 2026-05-24 →
2026-07-02. Live code is cited at its current path (paths re-verified against the working tree 2026-07-06;
583 tests collected); the dated screens are cited to their frozen records.

---

## §0 · Origin — one paragraph doing two jobs

Extraction and retrieval were built around a shared prose block, `SITUATION_STANDARDS`, composed into the
extraction prompt, the dedup prompt, and the situation-summary query alike, so all three judged "is this
situation distinctive" by one yardstick. It existed because the earliest extraction prompt produced
situations like *"after a mislynch"* — a string that matched every mislynch ever stored — and the fix was to
name the *conditions* that make one board distinctive from another.

Those conditions were factored into **four dimensions**, chosen as the axes along which two games showing
"the same event" actually differ — what makes one mislynch a different lesson from the next:

- **information landscape** — what is known, claimed, and still unknown on the board (a mislynch on hard
  evidence is a different lesson from one driven by pure tone);
- **consensus texture** — how the room is aligned and how the vote is forming (a lone accuser vs a
  near-unanimous pile-on);
- **agent exposure** — how visible or at-risk the deciding agent is (safe in the crowd vs the next likely
  target);
- **game phase** — early / mid / late, i.e. how far the board has narrowed.

Together they are the store's **indexing key**: "find a stored board like the one I am on now." The same
lesson is stored today as this real v6_1 villager·day_vote row:

> *"A near-unanimous consensus, fanned by a few vocal accusers, formed to eliminate a player whose only
> 'crime' was a single, clumsy, unsubstantiated attempt to clear another player's name."*

— behavioral-only evidence, a lone target, 7 alive: a fingerprint another game can actually match on,
where the bare label could not (the full prompt lineage is
[`../post_game/experiment_log.md`](../post_game/experiment_log.md) §1). From the start the dimensions did
**two** jobs at once: tell extraction *what to notice*, and seed the retrieval *query* — the same vocabulary
on both ends of the store, so a query and the observation it should match land near each other in embedding
space (the alignment problem above, in its first concrete form). That shared-vocabulary bet is the seed of
everything below; the rest of the journey makes it structural, then finds where it holds.

## §1 · Motivation — prose drops information, and embeds worse

Two weaknesses in the prose form surfaced together during the situation-summary golden study
([`../situation_summary/experiment_log.md`](../situation_summary/experiment_log.md) §3):

- **Prose silently drops fields.** A free-form paragraph lets the model blur or omit a dimension it was
  asked to cover; a structured object with one field per dimension makes omission impossible to hide.
- **Prose embeds worse than the store's own labels.** A hand A/B on a single healer·day-2 case ran the
  same query two ways:

  > **prose (A):** "The village's first vote is approaching with no prior records; the only concrete data is
  > a publicly announced healer save, and a fragile, tone-based consensus is forming against one player."
  > **labelled (B), lifted from `staging/case_1.json`:** "…Information landscape: Information-starved — the
  > only concrete data is a publicly announced healer save… Consensus texture: A fragile consensus is forming
  > against one player for deflection… Game phase: Early mid-game, first elimination pending."

  (A is the natural form reconstructed by stripping B's labels — the prose variant was not persisted.) The
  score is **cosine similarity**: each variant is embedded once, and its cosine is measured against a fixed
  set of stored items *already known to be the right ones* for this case. Retrieval ranks candidates by that
  cosine, so a query that scores higher against the items it *should* retrieve surfaces them nearer the top
  at recall — that is the good direction, and it is the direction B moved. B out-scored A on **every**
  retrieved item (+0.008 to +0.046 cosine, biggest on the item whose stored situation used those very
  labels): same items, same ranking, higher similarity — closer in embedding space purely by sharing
  structure.

Root cause: alignment between the write side and the read side was carried by a *prose convention* both
prompts were merely asked to follow. A convention can be forgotten mid-generation; a schema cannot. The
fix that follows is to move the dimensions from a shared paragraph to shared **fields**.

**The objection, and where the bet lands.** Shared label scaffolding raises the query's similarity to the
*right* items — but that scaffolding sits in *every* stored item too, so it also raises the baseline
similarity of stored memories *to each other*, making distinct lessons harder to tell apart. That is a real
cost, not a free win: it is the alignment bet's downside, and it is exactly where the bet later surfaces as
the **dedup over-merge problem** (§8 item 5) — the shared `Information landscape: … Stakes: …` prefix
inflates pairwise similarity enough that agglomerative clustering collapses whole *namespaces* (the store's
per-role×phase partitions) into one blob. So §1 buys retrieval alignment and books a known debt against the
dedup layer; the two are the same structural fact seen from the query side and the store side.

## §2 · First design — promote dimensions to schema fields, compose back to prose

The dimensions became real schema fields, emitted as structured output and then **composed into a labelled
prose string** (`composed_situation`) at storage and injection time — *prose → structured output, composed
back to prose on injection.* This composed string is the central artifact of the whole system, and it is
what retrieval embeds. One real instance (the same v6_1 villager·day_vote row, abbreviated):

> *"A near-unanimous consensus, fanned by a few vocal accusers, formed to eliminate a player whose only
> 'crime' was … **Information landscape:** Evidence was entirely behavioral … **Stakes:** At 7 players,
> eliminating a village power role would give the two wolves and serial killer a major advantage …
> **Consensus:** The room was almost entirely united … **My position:** With the majority. **Heat:**
> Minimal … **Target landscape:** There was only one target …"*

Composing back to prose bought two things — a guarantee that every dimension is emitted (no silent drop),
and embedding alignment that no longer depends on the model remembering a house style. This is the first
sighting of the thread that governs the rest — **alignment is the lever:** a query sharing the store's
structure matches better *by construction*, and v6 (§5) makes that a schema guarantee, not a prompt nudge.

## §3 · First iteration under a real anchor — and a dimension falsified in place

With the fields structured, the situation-summary study built the strongest anchor in the memory pipeline:
a **human-labelled retrieval golden** — a human reads each case, writes the ideal query, runs top-10
retrieval, and grades every returned memory 0/1/2 for relevance (~20 cases, 340 judgments). Graded labels
let the golden score **NDCG** (normalized discounted cumulative gain — a ranking metric that rewards putting
the most-relevant items highest), which came out at **NDCG@10 ≈ 0.83** on the `v4_deduped_v2` store. The
golden let dimensions be judged on whether they *retrieve* better, not whether they *read* better — and it
immediately overturned an intuition.

**"Core dilemma" — added, then falsified.** During labelling, one gap in the four dimensions stood out: they
describe the board *state* but not the *decision* on it. Two boards can be dimensionally identical yet pose
different choices —

> *"Should I follow a tone-based consensus when I have no unique info?"* vs.
> *"How do I share private findings without outing myself as investigator?"* vs.
> *"Should I reveal my role to prevent my own elimination?"*

— so a fifth dimension, **core dilemma**, was added: one sentence naming the agent's specific tradeoff at
that moment. The theory was clean — the four dimensions are the *indexing key* (find similar states), and
core dilemma would be the *discriminator* (find similar *choices* within a similar state), on the premise
that state alone under-determines which lesson is relevant. On **clean cases** (the subset with ≤4
unlabelled retrieved items, where the NDCG score is not distorted by the unlabelled-item penalty below) it
scored **net-negative: −0.084 NDCG@5.** The mechanism of the failure: asked for a *dilemma* rather than a
*state*, the model wrote the query as an abstract tradeoff — the "Should I follow a tone-based consensus…"
framing above — instead of the concrete board (who is accused, on what evidence, at what player count), and
abstract queries embed *further* from the concrete stored observations, not closer. *(Representative
reconstruction: the individual falsifying query texts were not persisted; the framing is lifted from the
field's own one-line spec and the golden study's diagnosis that removing it "stopped models from abstracting
and pushed toward concrete game events.")* Core dilemma was removed in v4 — the single biggest improvement
of the iteration. *Kept in place here because it is the cleanest evidence that a dimension has to earn its
place on retrieval, not on face plausibility.*

**The unlabeled-item trap.** The first golden-vs-captured gap (+0.112 NDCG) was partly an artifact:
captured queries retrieved items the golden never labelled, scored 0 by default. Union-labeling the 108
missing items settled the true gain at **+0.061** and flipped investigator from −0.040 to +0.042 — it had
been improving all along, masked by the penalty.

Shipped **v4b** (structured dims, no core dilemma, investigator-lens-first): +0.061 NDCG over the v1
baseline, largest gain on the weakest role (villager). **Apparatus reliability, stated once:** the NDCG
golden is the repo's best anchor *and* it is v4-store-stale, partly machine-augmented (108 auto-labels,
never human-re-validated), and cannot separate a bad *query* from a thin *store namespace* — the villager
"win" was largely an upstream coverage gap surfacing through it. Every later screen inherits that
last limitation.

## §4 · The v5→v6 trigger — the discriminator was too coarse

The flat four-dimension framework hit its ceiling during v5 store work, and the **decision-replay screen**
([`../../memory_system/effectiveness/decision_replay/experiment_log.md`](../../memory_system/effectiveness/decision_replay/experiment_log.md))
diagnosed *why*. The screen is the cheap way to ask "does memory change this decision, and toward the right
answer?" without paying for whole live games: it freezes one real decision point (board, transcript, private
info), swaps *only* the retrieved-memory block, regenerates just that one decision live, and scores the new
choice against the game's ground-truth roles. Paired at the decision, per-game role-luck cancels; run in one
sitting, overnight model drift cannot confound it. What sent us there: the earlier whole-game A/B said memory
*helped town* but was confounded by drift and store-volume, so we needed a drift-immune way to see *where*
memory actually acts.

The screen's **cheap-lever ladder** — four cheap interventions (reorder the output fields, link each memory
to the vote, force a per-memory applicability verdict, reframe the stored outcome) that all tried to make the
agent *use* its existing memory better *without changing the memory's content* — established one principle:
**memory helps only where the base prompt is thin, content is the whole lever, and every cheap way to make
the agent merely *use* memory came back null or harmful.** Within that, one probe named the specific defect
the dimensions had to fix:

- **The force-applicability probe.** *Catches:* can the agent recognize a memory that does *not* apply to
  its current board — and if so, on what feature? It planted one deliberately mismatched **endgame** memory
  (final-three-vs-serial-killer advice) into N=20 **mid-game** day-3 town decisions, and forced the model —
  via a structured field, one verdict per memory emitted before the vote — to rule each retrieved memory
  applies / partly / does-not. Why force it: a lightweight instruction in a field *description* had failed
  (flash-lite ignored it), so the structured field is what actually surfaces the judgment. The agent
  **correctly rejected the plant 13/20 times, and rejected it on the numbers** — "we are still at 5 players,
  not final-three." So the capability is real; the feature it reached for was the *exact player count*. But
  the only dimension carrying player count was `game_phase`, a coarse three-way label (early / mid / late)
  from which the exact number cannot be recovered — the agent needed a discriminator the schema did not
  expose. **That gap is precisely what the v6 rebuild (§5) closes:** promote the coarse label to exact
  criticality numbers.

Root cause for the rebuild: the framework encoded *regime* as a soft label when the decision turns on an
*exact number*, and a **bi-encoder** — the embedding model, which compresses each text into one fixed vector
before it ever sees the query — cannot recover that number from a coarse label. That gap is what §5 is built
to close.

## §5 · The v6 design — a per-cell schema from two rules

A first-principles, cell-by-cell walkthrough (2026-06-15; design frozen in
[`../../phase_b/dimension_schema_build_spec.md`](../../phase_b/dimension_schema_build_spec.md)) rebuilt the
dimensions from two generative rules — a **cell** being one situation schema per (role, phase), the unit the
rest of this section builds on. Design virtues below are stated **by construction**; whether they
*hold* is §6–§7.

**Rule 1 — gate vs embed vs extract.** A field is a hard gate only when crossing it makes a lesson
*invalid*; otherwise it is soft. Among soft fields: **embed** high-entropy free-text (a near-miss is still
useful), but **extract** to a structured field anything exact/ordinal/relational — numbers, signs — where
approximation is the bug. The justification is a *paradigm* limit, not a model limit: a bi-encoder commits
one pooled vector before it sees the query, so mean-pooling dilutes low-entropy fields and minimal-pair
directions smear — a stronger embedding model does not fix this.

**Rule 2 — situation = state, never prescription** (the invariant from the header). Every dimension is
board state in the agent's voice; the objective ("a good target maximizes info-gain") is payload. This
guards the prompt-boundary leak mode *and* keeps the embedding state-only.

From those two rules, the dispositions — **the library was validated, not replaced** (the wolf cell
converged with zero changes; "no new *kind* of dimension was needed"):

| original | disposition | why |
|---|---|---|
| `situation`, `information_landscape` | **KEEP** | the unchanged free-text spine |
| `game_phase` | **RESCOPE → `criticality`** | one label → a *family*: the numbers `players_alive`/`distance_to_parity`/`is_swing` plus a `criticality_stakes` phrase **written from** them (not a peer field). **This is the only true rescope — and the moment a dimension stops being retrieval-only and becomes a proxy** |
| `consensus_texture` | **SPLIT** | compound → `consensus_text` + `my_position` + `consensus_direction`[enum] |
| `agent_exposure` | **SPLIT** | compound → `heat_now` (all roles) + `forward_exposure` (concealment) |
| (in situation prose) | **PROMOTE → `target_landscape`** | the candidate set was buried in prose; give it a field |
| (in investigator lens) | **PROMOTE → `public_private_text` + `divergence_sign`[enum]** | the private-vs-public gap is a decision input |
| — | **NEW conditioners** | `bullets_left` (vigilante), `ally_revealed` (wolf) — criticality-family regime-flippers |

From Rule 1 come two decisions that live in the shipped schema (the per-field representation-and-reliability
inventory is [report.md](report.md)'s job). Numerics/enums are pulled *out* of the embedding for the
**reranker** (a second-stage scorer that reads the query and a candidate memory *together* — a reasoning
judge or cross-encoder — and so can compare an exact number the one-vector embedding blurred) and the gate —
but a direction or regime is *also* phrased as an implication into the embedded text
("a wrong-regime neighbour is the *opposite* lesson," and recall is the one stage no reranker touches), so
the embed carries "one death from a wolf win, every vote decisive," not the bare label "endgame." And every
prose field carrying a low-entropy sign gets an exact enum/numeric sibling — only where the bi-encoder
smears a near-minimal-pair, never for tidiness.

**One schema, three consumers.** The fields compose through a mixin DAG into one `SituationSchema` per
(role × {day, night}) cell — the single source of truth for extraction, live query, *and* embedding
composition, so they **cannot diverge** — and that schema is simultaneously the retrieval key, the
reranker/gate signal, and the procedural-memory reward (the *valenced* subset, no game-outcome attribution;
designed, not exercised — §8). That is the schema's **triple duty** — one source serving retrieval, gating,
and reward, the three consumers named in the guiding invariant above.

**What "criticality" refers to.** The word carries three referents at once: the *regime* (endgame vs
mid-game), the three *number-tags* it is read from (`players_alive`/`distance_to_parity`/`is_swing`), and
the derived *stakes prose* (`criticality_stakes`). It is never one emitted label — the numbers are fixed
first and the prose is written *from* them. That is exactly what "criticality is derived from other tags"
means: the stakes sentence is composed from its own number-tags, not authored on its own. Who fixes the
numbers differs by side — the LLM on the stored side, the board on the query side (the reversal below; §7).

**Two reversals, kept in place.** Both were argued one way, then flipped during the same walkthrough:
- Criticality went from *"pull the numbers fully out of the embed"* to *"numbers → reranker **and**
  stakes-implication → embed,"* once recall's regime-blindness was accounted for.
- Criticality derivation went from *"compute the numbers deterministically from game state"* to *"the LLM
  emits the numbers, and the prose is derived **from** those numbers within the same output"* — because
  post-game extraction synthesizes across moments and **cannot pin an extracted insight to one board
  state**. (§7's audit puts this reversal under test — and it is why the *live query* side, which *does*
  have a pinned moment, ends up handled differently from the *stored* side.)

## §6 · Implement → verify → decide — the rewrite helps retrieval; the conditioning lever does not

The build was gated cheap-first (spec §9): build one cell, screen it, roll the rest only if a lever shows.

**Step 1–3 — villager·day cell → `v6_0` store → the criticality screen.** 119 raw villager·day
observations, re-mined from the 20 frozen v5 games. The screen
([`../../phase_b/criticality_screen/experiment_log.md`](../../phase_b/criticality_screen/experiment_log.md))
asks the schema's core question: *if you condition retrieval on the criticality regime, do villager
day-votes improve?* Both arms rank the same candidate pool with the same embedding; the only delta is a
conditioning term (`cosine − λ·|Δplayers_alive| … + μ·[is_swing match]`); query criticality is computed
deterministically from the frozen board; decisions are day-stratified and paired. **Triage, not a verdict
— it reads direction and the criticality signature, not significance.** *The ruler for every number in this
section:* a paired, per-decision vote-quality difference on a −1…+1 net-value scale (+1 hit a threat, −1
town mislynch, 0 abstain); the arm names are **cond** = criticality-conditioned ranking, **flat** =
unconditioned cosine ranking, **off** = no memory (the floor).

- **First run: a textbook signature, and a GO.** Gain concentrated exactly where the schema predicted — high-criticality stratum **cond−flat +0.25** (n=16), mid-game ~null (+0.068), day-2 ~null (+0.077, the
  falsification axis passing), causal flips **4 → threat / 0 away**. It looked like the lever.
- **Correction 1 — same-game leak.** The pool included memories mined from the *same game* the decision
  came from (20 of 30 town games *were* the v6 source games); "a memory from game G knows G's outcome;
  production never retrieves same-game memory." Excluding them, the endgame concentration **washed out**
  (+0.25 → +0.087 → returns only at n=7 **held-out**, i.e. the screen re-run on memories from *other* games
  than the decision's own, the same-game leak removed). Decision downgraded **GO → HOLD.** *The leak
  discovery is itself a kept methodology result.*
- **Correction 2 — it does not replicate.** After rolling the full DAG and re-running across the town
  faction held-out (n=125), the villager subset **sign-flipped across two identical runs** — same data,
  same store, same λ, only the temperature draws differed: **+0.061 → −0.037.** A ~0.1 swing on n=82 is
  ≈1–2 SE. **Verdict: the criticality-*conditioning* lever is not robustly demonstrated — any effect is
  below this instrument's noise floor.**

But the same screen isolated **two v6 wins that survive** the conditioning null — and these are what the
rewrite is actually credited on:

- **Aligning the query helps.** Regenerating the query in the *same v6 dimensions* as the store (rather
  than firing a v5-schema query at a v6 store) raised memory's lift over no-memory from **flat−off +0.088 →
  +0.120** (n=125, paired). The dimensional rewrite made *retrieval* genuinely better, independent of any
  conditioning.
- **The schema is safe where the old content was harmful** (the forced-schema screen,
  [`../../phase_b/forced_schema_screen/experiment_log.md`](../../phase_b/forced_schema_screen/experiment_log.md)).
  Forcing the model to rule each retrieved memory applicable **hurt the vote on v5 content (−0.104)** via
  over-caution, but was **neutral on v6 (+0.021)**, and v6 beat v5 *specifically under the forced schema*
  (paired flips 8→v6 vs 3→v5) — the dimensions help when *engaged*, not when passively dumped.

That screen also produced a reliability finding that shaped production: the flash-lite "one verdict per
memory" under-emission was a **delivery** limit (not capability) — moving the instruction from the Pydantic
field description into the **prompt body** took coverage **0.27 → 0.97**. It also forced an honest
correction: under full coverage the first-reported engagement rate (0.697) was **inflated by
silently-skipped inapplicable memories**; the true applicable rate is **~0.55**. Forced per-memory reasoning
was migrated to production on that basis.

**Decision at the end of §6:** adopt the v6 schema and store (all roles, criticality metadata on every row,
embed-aligned queries); **keep the criticality numbers in the store** because they cost nothing and feed the
reranker, the gate, and the reward channel — **but do not claim criticality-conditioning as a retrieval
lever.** The store was built out (17 namespaces, ~919 obs), with two defects logged and one fixed: player-ID
naming violations concentrated in night cells (**22.1%** — degrade recall, no cross-game leak; accepted +
flagged), and a `consensus_direction` hindsight leak (set against the outcome, not the agent's expressed
read) fixed to ~0% detectable ([`../../phase_b/v6_full_store.md`](../../phase_b/v6_full_store.md)).

## §7 · The reliability audit — the fills were never checked, and two are worse than a constant

Everything to §6 tested whether the dimensions *help*. The 2026-07 eval-hardening pass
([`../../evaluation/hardening_pass/experiment_log.md`](../../evaluation/hardening_pass/experiment_log.md)
§2.1) asked a prior question no one had: **are the filled values even correct?** Its finding: *every v6
dimension is LLM-filled at both extraction and query time, and no tool has ever compared a filled value to
ground truth — even where truth is deterministically computable from the board.* This is load-bearing
because production dimension gating keys on `players_alive`(bucketed) / `is_swing` / `exposure_class` /
`info_landscape_class`, and the gating and criticality screens returned ~0/negative. **If the fills are
inaccurate, those screens tested noise, and their nulls are *uninformative rather than negative*.**

The $0, deterministic audit that followed
([`../../phase_b/dimension_accuracy_audit/experiment_log.md`](../../phase_b/dimension_accuracy_audit/experiment_log.md))
scored ~20k query-side situation objects against truth computed from each case's own frozen board, with a
**pre-registered** rule (RE-OPEN if any gated dim < 0.80) and a mandatory epistemic split (agent-knowable
fill error vs vs-omniscient disagreement):

| dimension | epistemic class | accuracy | read |
|---|---|---|---|
| `players_alive` | agent-knowable | 0.970 exact / **0.990 bucket** | **sound** — the gate's primary key held |
| `ally_revealed` | agent-knowable | **0.975** | **sound** — wolves track partner liveness |
| `bullets_left` | agent-knowable | **0.164** (day-2 = 0.0) | **broken** — systematically under-counts a value the agent was handed |
| `is_swing` (wolf, ≈true fill) | ~true fill | **0.606** | **worse than a constant** — always-False scores 0.827 on a 0.173 base rate |
| `distance_to_parity` | vs-omniscient / ~true | 0.05–0.09 exact, MAE ≈2 | unusable as an exact key (already excluded from the gate) |

**RE-OPEN fired** on wolf-side `is_swing` (0.606 < 0.80). The consequence is quantified, not hand-waved:
mean gated-dim error ē ≈ 0.202 attenuates any true alignment tilt to ≈0.60 of nominal — so **the recorded
dimension-gating null is partly *uninformative*, "Unknown, not false,"** not a clean content verdict. One
catch was fixed in place before scoring — the correction is made in the open and the original wrong number
stays visible, never silently rewritten: 176 wolf night cases persist an empty roster, and scoring the fill
against a bogus `0` had manufactured a wolf over-count; the runner now skips criticality truth on those
(`no_roster`), and corrected wolf `players_alive` is 0.97. **Scope, stated
honestly:** this re-opens the **gating** screen; it does **not** touch the **criticality screen**, whose
query side already computed truth deterministically — and it leaves the content-bottleneck conclusion
(which rests on the follow-rate result) standing.

**The $0 fix it authorized, done in place.** The three **agent-knowable** dims are now **computed from game
state at query time, never trusted from the LLM** — the override in
[`situation_agent.py`](../../../Agents/memory/retrieval/situation_agent.py) (`_override_deterministic_dims`):
`players_alive` from the living roster (shape-robust — it repairs the off-by-one where single-actor night
payloads exclude the actor), `bullets_left` from the vigilante's counter (threaded through `DayGraphState`),
`ally_revealed` from pack-size vs a scalar initial wolf count (no identity, so the leak boundary is
untouched). These carry no embed marker, so the override changes only the *gating* input — **the composed
embed string and retrieval matching are unchanged.** `distance_to_parity`/`is_swing` are deliberately
**left LLM-filled**: they need the true role map the live agent cannot see, so their offline substitution
belongs to the held gating re-screen.

**The residual, and its resolution first.** The $0 override shipped first (hardening pass, suite 421 → 431)
as a **post-hoc stopgap**: it corrects the *number* the gate reads but not the LLM's *prose*. The
prompt-injection fix followed **2026-07-04** — `_known_board_facts` now hands the query the computable
numbers from the *same* `_computed_dims` source as the override, so the model writes the stakes implication
*from truth*, with no schema change. That closes the lag for `players_alive`/`bullets_left`/`ally_revealed`.
What remains: `distance_to_parity`/`is_swing` cannot be computed live (they need the hidden role map), so
**only the parity/swing wording of the stakes still lags** (report gap 4). Tests:
`tests/test_situation_dim_override.py` (15 cases — override, injected facts, single-source invariant); full
suite green (507).

**The lag it closed, concretely.** Before the injection fix, the *embedded* `criticality_stakes` prose was
written from the LLM's **pre-override** numbers and never re-derived, so a corrected number could disagree
with its own embedded sentence. Illustrative from the audit's `bullets_left` = 0.164 finding (day-2 accuracy
0.0: a vigilante holding 2 shots is filled as 1): the gate now reads a corrected `bullets_left = 2`, while
the pre-fix embedded prose, written from the LLM's "1," still said *"down to your last bullet"* — the number
the reranker gates on is right, the sentence retrieval embeds a shot behind. Injection closes this for the
three computable dims; the defect survives only where the number can't be computed live (parity/swing).

**Why the fields can't simply be dropped from the output.** They live on shared mixins (`BaseSituation` /
`WithBulletsLeft` / `WithAllyRevealed`) that the extraction observation cells *also* inherit — and
extraction genuinely needs the LLM to fill them, since the stored side has no pinned board moment to compute
from (the §5 asymmetry: only the *query* has a "now") — while dedup partitions on them
(`dedup_gate.gate_key`). So the redundant emission stays; only its *correctness* is fixed.

## §8 · Limitations & future work

Criticality-ordered by how much each caps a claim; freshness 2026-07-04.

1. **`is_swing` / `distance_to_parity` are still LLM-filled and unreliable, and the gating verdict is
   "unknown."** Wolf-side `is_swing` at 0.606 is worse than always-False; the gate keyed on it, so the
   default-off decision now rests on an *uninformative* null, not a negative one. The cheapest resolution
   is the **~$10–15 offline gating re-screen** with deterministic `players_alive` + offline `is_swing`
   substituted into the frozen cases — authorized by the RE-OPEN rule, **held on spend sign-off.** This is
   the single step that converts "unknown" back into a verdict. *(Likelihood the number is misleading a
   reader: high; it currently reads as a clean negative in older docs.)*
   **→ 2026-07-11 (§9): half-RESOLVED.** The query-side fills are now computed from the public census
   (`Agents/board_clocks.py`), so the "still LLM-filled" premise is dead going forward; what survives of
   this item is the gating *verdict* itself (screened on the old fills) and the stored-side extraction
   fills in pre-existing stores. A fresh-store run with computed fills may settle the gate for free.
2. **The two enum gate keys were never validated at all.** `exposure_class` and `info_landscape_class`
   have no deterministic truth, so the audit could report only their (heavily skewed) distributions. The
   diagnosis sampler that would spot-check them is **built** (`eval-case-sample`, forced ~half
   predicted-`exposed`/`info_rich` for off-diagonal power), but the ~2h human labeling pass is **pending**.
   Until then even the RE-OPEN is conservative — it fired on the deterministic dims alone.
3. **Every retrieval number predates the live schema.** The NDCG golden and the criticality/forced screens
   were tuned on `v4`/`v6_0` stores; the live store is `v6_1`. The golden is also partly machine-augmented
   and not wired into the live retrieval judge. The free next step is a **v6_1 re-baseline of the NDCG
   golden** before any further prompt tuning is credited (`../situation_summary` gap 1).
4. **The stored-side fills are only weakly bounded.** The audit checks the *query* side (a pinned board
   moment exists); a stored observation carries no frozen board, so its extraction-time fills pass only
   internal-consistency bounds (`|distance_to_parity| ≤ players_alive`, `players_alive ∈ [3,9]`, 100% on
   `v6_1`) — which would pass under a systematic bias. Their real check is the deferred sampled review.
5. **The dedup layer over-merges on the composed prose blob.** Agglomerative clustering at the default
   threshold collapses whole namespaces into one blob, because the shared section-label scaffolding
   ("Information landscape: … Stakes: …") inflates baseline similarity. The structured gate-fields are
   well-distributed and the fix is an *explicit predicate over the structured fields* rather than a cosine
   threshold — designed ([`../../phase_b/dedup_clustering_and_sp_extraction_plan.md`](../../phase_b/dedup_clustering_and_sp_extraction_plan.md)),
   not built. It also implies the embed text should be a label-stripped representation distinct from the
   display text.
6. **The reward channel is designed, not exercised.** The valenced-subset procedural reward (§5) is the
   untested deceiver channel — every effectiveness measurement to date used *observations* only, so the
   wolf/SK null is plausibly a channel mismatch, not a ceiling. Unbuilt.
7. **The FT cross-encoder fusion the numerics were pulled out *for* is deferred.** The whole gate-vs-embed
   split exposes exact numbers/signs so a fine-tuned cross-encoder can fuse them (fork-#3); the reasoning-
   judge reranker in production reads them holistically and needs no separate clean extraction, so the
   fusion path is exposed-but-unbuilt.

## §9 · 2026-07-11 — the omniscient truth was narrower than the instruction it graded

An owner probe during the credit-layer review ("criticality for town is…? for SK?") surfaced a
truth-side mismatch that §7's audit had silently inherited: the model-facing field descriptions were
already faction-neutral — `distance_to_parity` says "the leading remaining **evil faction**", `is_swing`
says "flips **which faction** is winning" — but the omniscient truth `query_criticality` computed **wolf
parity only**. Two real costs: an agent correctly filling `is_swing=True` on an SK-endgame board (wolves
swept, SK one elimination from winning — the wolf clock reads that board as maximally safe) was graded
*wrong* by the audit; and lesson-selection weighting rated deceiver do-or-die boards near a town win as
filler. *Catches: grading fills against a narrower definition than the prompt teaches is a silent
truth-function bug — audit the ruler's definition against the instruction, not just the fills against
the ruler.*

**Fix (same day, implemented, suite green):** the truth now mirrors `determine_winner`'s three terminal
clocks — wolf `(town+SK)−wolves` (exact: wolves cannot win while the SK lives), SK `(town+wolves)−1`,
town `wolves+SK`. `distance_to_parity` = min of the two evil clocks (now matching its field
description); `is_swing` = min of all three ≤ 1 (faction-neutral "the game can end within one
elimination"). Ruling + the clock table: [`../../credit/report.md`](../../credit/report.md) §6.
Consequence for records: every audit/screen number above (§7, and the gating screens) was computed
against the wolf-only truth — direction unaffected for the town-side conclusions, but SK-endgame rows
were mis-graded; the held §8.1 gating re-screen would use the new truth.

**Same-day follow-up — the owner then falsified the epistemic premise itself.** The doc family (and
§7's audit design) held that these two dims "need the true role map the live agent cannot see." But the
cast is fixed and public, and every death path announces the dead player's role (the attacker-typed
role-revealing deaths; `format_alive_roles` already computed the survivors' census from exactly this) —
and the clocks need only *counts*, never identities. So both dims are **agent-knowable**, and the worst
two rows of the §7 reliability table were LLM-filled for no epistemic reason — the same class of finding
as §7's own `players_alive` result, one level deeper: the premise exempting them from the deterministic
override was itself never audited after deaths became role-revealing. *Catches: when a role-set or
disclosure rule changes, re-audit which quantities are still "hidden" — an epistemic exemption is a
claim about the game rules, and it goes stale silently when the rules move.*

**Promotion (implemented same day, suite 631 green):** the clock arithmetic moved to a shared live-side
home, `Agents/board_clocks.py` (census subtraction reused by `format_alive_roles`;
`criticality_from_census` = the agent-knowable derivation; eval's `query_criticality` now delegates to
the same function, so live fill and audit truth cannot diverge by construction). `distance_to_parity` /
`is_swing` joined `_override_deterministic_dims` + `_known_board_facts` — computed and injected at query
time, LLM fill kept only for legacy census-less payloads. Stored-side (extraction-time) computed fills
ride the v1 credit-wiring batch; existing stores keep their LLM-era fills.

## Sources

- **Primary dated records** (the sources; one representative artifact from each is pulled inline above):
  situation-summary golden study
  [`../situation_summary/experiment_log.md`](../situation_summary/experiment_log.md) · v6 build spec
  [`../../phase_b/dimension_schema_build_spec.md`](../../phase_b/dimension_schema_build_spec.md) · design
  walkthrough [`../../memory_system/effectiveness/decision_replay/experiment_log.md`](../../memory_system/effectiveness/decision_replay/experiment_log.md)
  · screens [`criticality_screen`](../../phase_b/criticality_screen/experiment_log.md) /
  [`forced_schema_screen`](../../phase_b/forced_schema_screen/experiment_log.md) · store build
  [`../../phase_b/v6_full_store.md`](../../phase_b/v6_full_store.md) · hardening pass
  [`../../evaluation/hardening_pass/experiment_log.md`](../../evaluation/hardening_pass/experiment_log.md) ·
  dimension audit [`../../phase_b/dimension_accuracy_audit/experiment_log.md`](../../phase_b/dimension_accuracy_audit/experiment_log.md).
- **Live code (current paths).** Schema + mixin DAG + `compose_situation_embed`:
  [`Agents/schemas/memory.py`](../../../Agents/schemas/memory.py). Live query + deterministic override:
  [`Agents/memory/retrieval/situation_agent.py`](../../../Agents/memory/retrieval/situation_agent.py).
  Gating (live-wired, default-off): [`Agents/memory/retrieval/dimension_gating.py`](../../../Agents/memory/retrieval/dimension_gating.py).
  Criticality truth fn: [`evaluation/src/loop/decision_scoring.py`](../../../evaluation/src/loop/decision_scoring.py)
  (`query_criticality`). Per-cell extraction: [`Agents/memory/extraction/cell_units.py`](../../../Agents/memory/extraction/cell_units.py),
  [`extraction_agent.py`](../../../Agents/memory/extraction/extraction_agent.py). Audit runner:
  [`dimension_audit.py`](../../../evaluation/src/instrument_validation/dimensions/dimension_audit.py).
- **Destination:** [report.md](report.md) — how the dimensions work today + the freshness/gap ledger.
- **Reliability ledger:** [`../../evaluation/source_map.md`](../../evaluation/source_map.md).
