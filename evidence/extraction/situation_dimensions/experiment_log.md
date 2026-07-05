# Situation Dimensions — design & reliability journey

**What this is.** The chronological record of how the memory system's *situation dimensions* — the
structured, state-describing fields attached to every stored observation and every live retrieval query —
grew from a single prose paragraph into a per-cell schema that does **triple duty** (retrieval key,
reranker/gating signal, criticality proxy), and how far each of those fields can actually be trusted. It
curates *one* arc across four dated records that remain the primary sources and are **not** restated here:
the situation-summary golden study ([`../situation_summary/experiment_log.md`](../situation_summary/experiment_log.md)),
the v6 build spec ([`../../phase_b/dimension_schema_build_spec.md`](../../phase_b/dimension_schema_build_spec.md)),
the phase-B screens ([`criticality_screen`](../../phase_b/criticality_screen/experiment_log.md),
[`forced_schema_screen`](../../phase_b/forced_schema_screen/experiment_log.md)), and the eval-hardening
audit ([`../../phase_b/dimension_accuracy_audit/experiment_log.md`](../../phase_b/dimension_accuracy_audit/experiment_log.md)).
It ends where [report.md](report.md) begins — the current shipped state.

**What a "situation dimension" is.** A dimension describes *what is true on the board, in the agent's
epistemic voice, with zero should/recommend language* — the invariant the build spec states as **"situation
= state, never prescription."** The prescription (how to act) is the retrieved *payload*, never a matching
field. That single rule is what lets the *same* fields serve retrieval, gating, and reward without
contradiction: all three **read** the situation; none of them *are* the advice.

**Reading contract.** Sections are in time order; each states what it changed and what it found. The arc
keeps its real corrections in place: a "core dilemma" dimension that felt right and scored net-negative
(§3); a criticality-conditioning lever that a same-game leak inflated and a temperature re-draw then
erased (§6); and a whole family of LLM-filled fields that a $0 audit found were, in two cases, *worse than
a constant* (§7). For the current shipped state, jump to [report.md](report.md).

**Provenance.** Curated 2026-07-04 on `feature-dimension-schema`; the underlying work spans 2026-05-24 →
2026-07-02. Live code is cited at its current path (verified against the working tree, 502 tests green);
the dated screens are cited to their frozen records above.

---

## §0 · Origin — one paragraph doing two jobs

Extraction and retrieval were built around a shared prose block, `SITUATION_STANDARDS`: a dimensional
framework — **information landscape, consensus texture, agent exposure, game phase** — composed into the
extraction prompt, the dedup prompt, and the situation-summary query alike, so all three judged "is this
situation distinctive" by one yardstick. It existed because the earliest extraction prompt produced
situations like *"after a mislynch"* that matched every mislynch ever stored, and the fix was to name the
*conditions* that made a situation distinctive (the full prompt lineage is
[`../post_game/experiment_log.md`](../post_game/experiment_log.md) §1). From the start the dimensions did
**two** jobs at once: tell extraction *what to notice*, and seed the RAG *query* — the same vocabulary on
both ends of the store so a query and the observation it should match would land near each other in
embedding space. That shared-vocabulary bet is the seed of everything below; the rest of the journey is
making it structural, then finding out where it holds.

## §1 · Motivation — prose drops information, and embeds worse

Two weaknesses in the prose form surfaced together during the situation-summary golden study
([`../situation_summary/experiment_log.md`](../situation_summary/experiment_log.md) §3):

- **Prose silently drops fields.** A free-form paragraph lets the model blur or omit a dimension it was
  asked to cover; nothing forces each dimension to be present. A structured object with one field per
  dimension makes omission impossible to hide.
- **Prose embeds worse than the store's own labels.** A hand A/B on a single healer case showed a query
  written with the store's *explicit* dimensional labels ("Consensus texture: …", "Game phase: …")
  out-scored the same query in natural prose on **every** retrieved item (+0.008 to +0.046 cosine, biggest
  on the item whose stored situation used those very labels). Same items, same ranking, higher similarity —
  the query and the store were closer in embedding space purely by sharing structure.

Root cause: alignment between the write side and the read side was carried by a *prose convention* both
prompts were merely asked to follow. A convention can be forgotten mid-generation; a schema cannot. The
fix that follows is to move the dimensions from a shared paragraph to shared **fields**.

## §2 · First design — promote dimensions to schema fields, compose back to prose

The dimensions became real schema fields, emitted as structured output and then **composed into the
labelled prose string** (`composed_situation`) at storage and injection time. This is the move the user's
framing names: *prose → structured output, composed as prose on injection.* It bought two things — a
guarantee that every dimension is emitted (no silent drop), and embedding alignment that no longer depends
on the model remembering a house style. The composed string is still what retrieval embeds; the structure
is what guarantees the string is complete and consistent.

This is also the first sighting of the thread that governs the rest of the story: **alignment is the
lever.** A query that shares the store's structure matches better *by construction*. v6 (§5) turns that
from a prompt nudge into a schema guarantee.

## §3 · First iteration under a real anchor — and a dimension falsified in place

With the fields structured, the situation-summary study built the strongest anchor in the memory pipeline:
a **human-labelled retrieval golden** — graded relevance (0/1/2) over ~20 cases, 340 judgments,
NDCG@10 ≈ 0.83 on the `v4_deduped_v2` store. It let dimensions be judged on whether they *retrieve* better,
not whether they *read* better, and it immediately overturned an intuition:

- **"Core dilemma" — added, then falsified.** A fifth dimension (the agent's specific tradeoff) was added
  on the theory that two state-identical cases can face different *decisions*. On clean cases it scored
  **net-negative (−0.084 NDCG@5)** — it pushed the model toward abstract framing over concrete game events.
  It was removed in v4, the single biggest improvement of the iteration. *Kept in place here because it is
  the cleanest evidence that a dimension has to earn its place on retrieval, not on face plausibility.*
- **The unlabeled-item trap.** The first golden-vs-captured gap (+0.112 NDCG) was partly an artifact:
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

The flat four-dimension framework hit its ceiling during v5 store work, and the decision-replay screen
([`../../memory_system/effectiveness/decision_replay/experiment_log.md`](../../memory_system/effectiveness/decision_replay/experiment_log.md))
diagnosed *why*. Its cheap-lever ladder — reorder, memory-link, force-applicability, outcome-reframing —
established one principle: **memory helps where the base prompt is thin, and content is the whole lever;
every cheap way to make the agent merely *use* memory came back null or harmful.** Within that, one probe
named the specific defect the dimensions had to fix:

- **The force-applicability probe.** Planting an endgame memory into a mid-game decision and forcing the
  model to rule each memory applicable/not, the agent **correctly rejected the plant 13/20 times — on the
  numbers** ("we are still at 5 players, not final-three"). It *can* reason applicability; the discriminator
  it reached for was the player count. But the only field carrying that was `game_phase`, a coarse label
  ("early/mid/late"). **`game_phase` was too coarse to carry the distinction the model actually needed.**

Root cause for the rebuild: the framework encoded *regime* as a soft label when the decision turns on an
*exact number*, and a bi-encoder cannot recover the number from the label. That is the gap §5 is built to
close.

## §5 · The v6 design — a per-cell schema from two rules

A first-principles, cell-by-cell walkthrough (2026-06-15; design frozen in
[`../../phase_b/dimension_schema_build_spec.md`](../../phase_b/dimension_schema_build_spec.md)) rebuilt the
dimensions from two generative rules. Design virtues below are stated **by construction**; whether they
*hold* is §6–§7.

**Rule 1 — gate vs embed vs extract.** A field is a hard gate only when crossing it makes a lesson
*invalid*; otherwise it is soft. Among soft fields: **embed** high-entropy free-text (a near-miss is still
useful), but **extract** to a structured field anything exact/ordinal/relational — numbers, signs — where
approximation is the bug. The justification is a *paradigm* limit, not a model limit: a bi-encoder commits
one pooled vector before it sees the query, so mean-pooling dilutes low-entropy fields, tokenizers aren't
magnitude-aware, and minimal-pair directions smear. A stronger embedding model does not fix this.

**Rule 2 — situation = state, never prescription** (the invariant from the header). Every dimension is
board state in the agent's voice; the objective ("a good target maximizes info-gain") is payload. This
guards the prompt-boundary leak mode *and* keeps the embedding state-only.

From those two rules, the dispositions — **the library was validated, not replaced** (the wolf cell
converged with zero changes; "no new *kind* of dimension was needed"):

| original | disposition | why |
|---|---|---|
| `situation`, `information_landscape` | **KEEP** | the unchanged free-text spine |
| `game_phase` | **RESCOPE → `criticality`** | label → the numbers `players_alive`/`distance_to_parity`/`is_swing` + a stakes-implication phrase. **This is the only true rescope — and the moment a dimension stops being retrieval-only and becomes a proxy** |
| `consensus_texture` | **SPLIT** | compound → `consensus_text` + `my_position` + `consensus_direction`[enum] |
| `agent_exposure` | **SPLIT** | compound → `heat_now` (all roles) + `forward_exposure` (concealment) |
| (in situation prose) | **PROMOTE → `target_landscape`** | the candidate set was buried in prose; give it a field |
| (in investigator lens) | **PROMOTE → `public_private_text` + `divergence_sign`[enum]** | the private-vs-public gap is a decision input |
| — | **NEW conditioners** | `bullets_left` (vigilante), `ally_revealed` (wolf) — criticality-family regime-flippers |

**The embed ledger (Rule 1 applied).** Free-text fields fold into the embedding; numerics/enums do not —
they go to the reranker/gate. The one subtlety: a *direction* or *regime* (consensus_direction,
divergence_sign, criticality) is phrased **as an implication into the embedded text** *and* kept exact for
the reranker, because "a wrong-regime neighbour is not less applicable, it is the *opposite* lesson," and
**recall is the one stage no reranker touches.** So the embed carries "one death from a wolf win, every
vote decisive," not the bare label "endgame."

**Enum vs prose is one decision, applied uniformly.** That subtlety generalizes into a symmetry that makes
the whole split principled rather than per-field taste: **every prose field that also carries a low-entropy
sign or regime has an enum/numeric sibling** holding the exact value, while the prose holds the recall
narration — `information_landscape`↔`info_landscape_class`, `consensus_text`/`my_position`↔`consensus_direction`,
`heat_now`/`forward_exposure`↔`exposure_class`, `public_private_text`↔`divergence_sign`, and
`criticality_stakes`↔the three criticality numbers. Only `situation` and `target_landscape` are enum-less —
they carry no minimal-pair signal to lose. An enum is therefore reserved for exactly the case the bi-encoder
can't handle (a near-minimal-pair the embedding *smears* — aligns-vs-opposes, confirms-vs-contradicts) and
nothing gets one for tidiness. The one field the walkthrough deliberately left prose *without* its own enum
is `my_position` (driving / with-majority / holding-out): its three values are distinct content the
embedding separates on its own, not a minimal pair, and the directional sign it might encode is already
`consensus_direction`.

**The structure — a mixin DAG → 11 cells.** `BaseSituation` + optional mixins (`WithConsensus`,
`WithHeat`, `WithTargetLandscape`, `WithForwardExposure`, `WithPublicPrivate`, role conditioners) compose
into one `SituationSchema` **per (role × {day, night}) cell**. The 17 role×phase combinations collapse to
**11** because `day_discussion` and `day_vote` share a goal (the discussion *is* the target-finding for the
vote); **day-vs-night is the validity-breaking gate** (investigator proves it — its night cell is the
leanest, pure info-gain; its day cell the richest). Two profiles recur: `PowerRoleDay`
(healer/investigator/vigilante) and `DeceiverConcealment` (wolf/SK).

**The load-bearing symmetry.** One `SituationSchema` per cell is the single source of truth for three
things at once — post-game extraction output, live query output, and the embedding composition — so **query
and storage compositions cannot diverge.** Every row in a namespace is the same subclass, which is what
makes one-vector-per-cell safe. The prompt guidance *is* the Pydantic `Field(description=)` on each mixin,
so extraction and query read identical guidance for free.

**Triple duty (the "more than retrieval" the user flagged).** The same schema is (1) the retrieval key,
(2) the reranker/gate signal, and (3) the **procedural-memory reward**: the *valenced* subset (heat,
forward_exposure, standing, parity-progress, target-removed — the dims with a good/bad direction) is the
local reward for weighting strategy points, quasi-causally, with no game-outcome attribution. One schema,
three consumers. (The reward channel is *designed*, not yet exercised — see §8.)

**Two reversals, kept in place.** Both were argued one way, then flipped during the same walkthrough:
- Criticality went from *"pull the numbers fully out of the embed"* to *"numbers → reranker **and**
  stakes-implication → embed,"* once recall's regime-blindness was accounted for.
- Criticality derivation went from *"compute the numbers deterministically from game state"* to *"the LLM
  emits the numbers, and the prose is derived **from** those numbers within the same output"* — because
  post-game extraction synthesizes across moments and **cannot pin an extracted insight to one board
  state**, so there is no deterministic moment to stamp. (This reversal is exactly what §7's audit later
  puts under test — and it is why the *live query* side, which *does* have a pinned moment, ends up handled
  differently from the *stored* side.)

## §6 · Implement → verify → decide — the rewrite helps retrieval; the conditioning lever does not

The build was gated cheap-first (spec §9): build one cell, screen it, roll the rest only if a lever shows.

**Step 1–3 — villager·day cell → `v6_0` store → the criticality screen.** 119 raw villager·day
observations, re-mined from the 20 frozen v5 games. The screen
([`../../phase_b/criticality_screen/experiment_log.md`](../../phase_b/criticality_screen/experiment_log.md))
asks the schema's core question: *if you condition retrieval on the criticality regime, do villager
day-votes improve?* Both arms rank the same candidate pool with the same embedding; the only delta is a
conditioning term (`cosine − λ·|Δplayers_alive| … + μ·[is_swing match]`); query criticality is computed
deterministically from the frozen board; decisions are day-stratified and paired. **Triage, not a verdict
— it reads direction and the criticality signature, not significance.**

- **First run: a textbook signature, and a GO.** Gain concentrated exactly where the schema predicted — high-criticality stratum **cond−flat +0.25** (n=16), mid-game ~null (+0.068), day-2 ~null (+0.077, the
  falsification axis passing), causal flips **4 → threat / 0 away**. It looked like the lever.
- **Correction 1 — same-game leak.** The pool included memories mined from the *same game* the decision
  came from (20 of 30 town games *were* the v6 source games); "a memory from game G knows G's outcome;
  production never retrieves same-game memory." Excluding them, the endgame concentration **washed out**
  (+0.25 → +0.087 → returns only at n=7 held-out). Decision downgraded **GO → HOLD.** *The leak discovery
  is itself a kept methodology result.*
- **Correction 2 — it does not replicate.** After rolling the full DAG and re-running across the town
  faction held-out (n=125), the villager subset **sign-flipped across two identical runs** — same data,
  same store, same λ, only the temperature draws differed: **+0.061 → −0.037.** A ~0.1 swing on n=82 is
  ≈1–2 SE. **Verdict: the criticality-*conditioning* lever is not robustly demonstrated — any effect is
  below this instrument's noise floor.**

But the same screen isolated **two v6 wins that survive** the conditioning null — and these are what the
rewrite is actually credited on:

- **Aligning the query helps.** Regenerating the query in the *same v6 dimensions* as the store (rather
  than firing a v5-schema query at a v6 store) raised memory's lift over no-memory from **flat−off +0.088 →
  +0.120** (n=125, paired). The dimensional rewrite made *retrieval* genuinely better — "the win is better
  *situations* → better retrieval," independent of any conditioning.
- **The schema is safe where the old content was harmful** (the forced-schema screen,
  [`../../phase_b/forced_schema_screen/experiment_log.md`](../../phase_b/forced_schema_screen/experiment_log.md)).
  Forcing the model to rule each retrieved memory applicable **hurt the vote on v5 content (−0.104)** via
  over-caution, but was **neutral on v6 (+0.021)**, and v6 beat v5 *specifically under the forced schema*
  (paired flips 8→v6 vs 3→v5). The dimensions help when *engaged*, not when passively dumped.

That screen also produced a reliability finding that shaped production: the flash-lite "one verdict per
memory" under-emission was a **delivery** limit, not a capability or output-length limit — moving the
instruction from the Pydantic field description into the **prompt body** took coverage **0.27 → 0.97**. It
also forced an honest correction: under full coverage the engagement rate the screen first reported
(0.697) was **inflated by silently-skipped inapplicable memories** — the true applicable rate is **~0.55**
(the skipped ones were disproportionately the inapplicable ones). Forced per-memory reasoning was migrated
to production on that basis.

**Decision at the end of §6:** adopt the v6 schema and store (better-structured memory, criticality
metadata on every row, all roles, embed-aligned queries); **keep the criticality numbers in the store**
because they cost nothing and feed the reranker, the gate, and the reward channel — **but do not claim
criticality-conditioning as a retrieval lever.** The store was built out (17 namespaces, ~919 obs), with
two defects logged and one fixed: player-ID naming violations concentrated in night cells (**22.1%** —
degrade recall, no cross-game leak; accepted + flagged), and a `consensus_direction` hindsight leak (the
enum set against the outcome-correct read rather than the agent's expressed read) fixed to ~0% detectable
([`../../phase_b/v6_full_store.md`](../../phase_b/v6_full_store.md)).

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
catch was fixed in place before scoring, per the no-laundering rule: 176 wolf night cases persist an empty
roster, and scoring the fill against a bogus `0` had manufactured a wolf over-count; the runner now skips
criticality truth on those (`no_roster`), and corrected wolf `players_alive` is 0.97. **Scope, stated
honestly:** this re-opens the **gating** screen; it does **not** touch the **criticality screen**, whose
query side already computed truth deterministically — and it leaves the content-bottleneck conclusion
(which rests on the follow-rate result) standing.

**The $0 fix it authorized, done in place.** The three **agent-knowable** dims are now **computed from game
state at query time, never trusted from the LLM** — the override in
[`situation_agent.py`](../../../Agents/memory/enrichment/situation_agent.py) (`_override_deterministic_dims`,
`_computed_players_alive`): `players_alive` from the living roster (shape-robust — it repairs the off-by-one
where single-actor night payloads exclude the actor, which retroactively explains part of the LLM's 3%
error as *payload ambiguity*, not pure sloppiness), `bullets_left` from the vigilante's counter (threaded
through `DayGraphState`), `ally_revealed` from pack-size vs a scalar initial wolf count (no identity, so the
leak boundary is untouched). Because these carry no embed marker, the override changes only the *gating*
input — **the composed embed string and retrieval matching are unchanged.** `distance_to_parity`/`is_swing`
are deliberately **left LLM-filled**: they need the true role map the live agent cannot see, so their
offline substitution belongs to the held gating re-screen.

One residual is flagged, not fixed, and it is worth naming precisely because it points at the *correct*
design rather than the cheap one. This override is a **post-hoc stopgap**: the query LLM still *emits* the
three numbers (they are overwritten only when the payload carries the ingredients to compute them; the LLM
value survives as a fallback), and the *embedded* `criticality_stakes` prose was written from the LLM's own
**pre-override** numbers and is **not** re-derived — so a corrected `players_alive`/`bullets_left` can
disagree with its own embedded prose, and the number that prose lags was **0.164-accurate** for
`bullets_left`. The cleaner design is to **inject the deterministic numbers into the query prompt** so the
model writes the stakes implication *from truth* — which fixes the prose lag (the one that matters, because
`criticality_stakes` is *embedded* and so affects retrieval, not just gating), with no schema change. Note
what it does *not* do: the fields cannot simply be dropped from the output, because they live on shared
mixins (`BaseSituation` / `WithBulletsLeft` / `WithAllyRevealed`) that the extraction observation cells
*also* inherit — and extraction genuinely needs the LLM to fill them, since the stored side has no pinned
board moment to compute from (the §5 asymmetry: only the *query* has a "now"), while dedup partitions on
them (`dedup_gate.gate_key`). So the redundant emission stays; only its *correctness* is fixed. The $0
override shipped first (hardening pass, suite 421 → 431); the prompt-injection followed **2026-07-04** —
`_known_board_facts` now hands the query the computable numbers from the *same* `_computed_dims` source as
the override, so the number the model is told can never disagree with the one it is overridden to, and the
embedded stakes are written from truth for players_alive/bullets/ally. `distance_to_parity`/`is_swing`
remain LLM-estimated (uninjectable), so only the parity/swing wording of the stakes still lags (report
gap 4). Tests: `tests/test_situation_dim_override.py` (15 cases — override, injected facts, and the
single-source invariant); full suite green (507).

## §8 · Limitations & future work

Criticality-ordered by how much each caps a claim; freshness 2026-07-04.

1. **`is_swing` / `distance_to_parity` are still LLM-filled and unreliable, and the gating verdict is
   "unknown."** Wolf-side `is_swing` at 0.606 is worse than always-False; the gate keyed on it, so the
   default-off decision now rests on an *uninformative* null, not a negative one. The cheapest resolution
   is the **~$10–15 offline gating re-screen** with deterministic `players_alive` + offline `is_swing`
   substituted into the frozen cases — authorized by the RE-OPEN rule, **held on spend sign-off.** This is
   the single step that converts "unknown" back into a verdict. *(Likelihood the number is misleading a
   reader: high; it currently reads as a clean negative in older docs.)*
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

## Sources

- **Primary dated records** (this doc curates, does not restate): situation-summary golden study
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
  [`Agents/memory/enrichment/situation_agent.py`](../../../Agents/memory/enrichment/situation_agent.py).
  Gating (live-wired, default-off): [`Agents/memory/retrieval/dimension_gating.py`](../../../Agents/memory/retrieval/dimension_gating.py).
  Criticality truth fn: [`evaluation/src/loop/decision_scoring.py`](../../../evaluation/src/loop/decision_scoring.py)
  (`query_criticality`). Per-cell extraction: [`Agents/memory/extraction/cell_units.py`](../../../Agents/memory/extraction/cell_units.py),
  [`extraction_agent.py`](../../../Agents/memory/extraction/extraction_agent.py). Audit runner:
  [`evaluation/src/audits/dimension_audit.py`](../../../evaluation/src/audits/dimension_audit.py).
- **Destination:** [report.md](report.md) — how the dimensions work today + the freshness/gap ledger.
- **Reliability ledger:** [`../../evaluation/source_map.md`](../../evaluation/source_map.md).
