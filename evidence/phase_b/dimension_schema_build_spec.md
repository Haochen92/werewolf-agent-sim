# Dimension Schema Build Spec — per-cell situation standard, composable schema + prompt

**Status:** DESIGN FINALIZED via first-principles cell-by-cell walkthrough (2026-06-15), NO code
written, pending sign-off. This supersedes the 2026-06-13 draft: the walkthrough merged the
discussion/vote phases (17→11 cells), pruned/added dimensions per cell from each role's actual goal,
and surfaced three cross-cutting rules (conditioners, the two shared profiles, descriptive-only
situations). Fork #2 (dimensions-first then freeze). Narrative: `decision_replay/experiment_log.md`.

---

## 0. The two rules that generate everything

1. **Gate vs soft / embed vs extract.** A field is a hard gate only when crossing it makes a lesson
   INVALID; else it's soft. Among soft: EMBED high-entropy free-text (near-miss is useful); EXTRACT to
   a structured field anything exact/ordinal/relational (numbers, signs) where approximation is the bug.
   (Bi-encoder = one pooled vector committed before the query → mean-pooling dilutes low-entropy
   fields, tokenizers aren't magnitude-aware, minimal-pair direction smears. Paradigm limits, not
   model-fixable.)
2. **Situation = state, never prescription.** Every dimension describes *what is true on the board*, in
   the agent's epistemic voice, with ZERO should/recommend language. The "how to act" is the agent's
   own reasoning; the objective function ("a good target maximizes info-gain") is **payload** (action /
   strategy-point), retrieved-and-gated-in, NEVER a matching field. The drivers/objectives we derived
   per cell choose *which fields and what state to surface* (and what to lead with) — they never become
   field text. (Guards against how-to/prescription leaking into memory fields + keeps the embedding state-only.)

---

## 1. Dimension dispositions (what changes vs the original library)

The first-principle pass **validated** the library — no new *kind* of situation dimension was needed
(the wolf cell converged with zero changes). Work is mostly re-allocation; only criticality is truly
rescoped.

| original | disposition | change |
|---|---|---|
| `situation` | KEEP | unchanged spine |
| `information_landscape` | KEEP | unchanged spine |
| `game_phase` | **RESCOPE → `criticality`** | label → `players_alive`/`distance_to_parity`/`is_swing` numbers + stakes-implication text; becomes a *conditioner* |
| `consensus_texture` | **SPLIT** | → `consensus_text` + `my_position` + `consensus_direction`[enum] |
| `agent_exposure` | **SPLIT** | → `heat_now` (universal) + `forward_exposure` (concealment profiles) |
| (in situation prose) | **PROMOTE → `target_landscape`** (E) | own descriptive field |
| (in investigator lens) | **PROMOTE → `public_private_text` + `divergence_sign`[enum]** (G) | own field + enum |
| — | **NEW conditioners** | `bullets_left` (vigilante), `ally_revealed` (wolf) — criticality-family |

The new *objectives* the walkthrough surfaced (info-gain, faction-balance, whiff-probe) are **payload**,
not matching fields.

### The embed ledger
| field | storage | in embed string? | note |
|---|---|---|---|
| `situation` | free-text | yes | recall driver |
| `information_landscape` | free-text | yes | observable |
| `consensus_text` | free-text | yes | descriptive room state |
| `my_position` | free-text (+opt enum) | yes | distinct values (driving/with-majority/holdout), not a minimal pair |
| `consensus_direction` | enum | **no** (phrased into `consensus_text`) | aligns/opposes my-read; enum→reranker, direction phrased into text for recall |
| `heat_now` | free-text | yes | suspicion on me; ALL roles |
| `forward_exposure` | free-text | yes | cost of a contemplated move; concealment profiles |
| `target_landscape` | free-text | yes | candidate set + role/status + evidence-vs-behavior basis |
| `public_private_text` | free-text | yes | private-vs-public gap narrative |
| `divergence_sign` | enum | **no** (phrased into `public_private_text`) | confirms/contradicts; enum→reranker, phrased for recall |
| `criticality` numbers (`players_alive`, `distance_to_parity`, `is_swing`) | numeric | **no** → reranker | + stakes-IMPLICATION phrased into embed (see §3) |
| `bullets_left`, `ally_revealed` | numeric/flag | **no** → reranker | conditioners; implication phrased into embed |

---

## 2. Cell structure — gate = (role × {day, night}), 11 cells

`day_discussion` + `day_vote` **merge** per role (same goal; the discussion/vote difference is the
*action*, which is payload, plus a heavier `forward_exposure`/reversibility on the vote — carried
*within* the cell, not by a split). The validity-breaking gate is **day vs night**. Investigator is the
clearest proof the day/night gate is real: its night cell is the leanest, its day cell the richest.

### Mixin DAG
```
BaseSituation            : situation, information_landscape, criticality(3 numeric + stakes-text)
  WithConsensus     (D)  : consensus_text, my_position, consensus_direction[enum]   # day cells
  WithHeat          (Fa) : heat_now                                                  # day cells, ALL roles
  WithTargetLandscape(E) : target_landscape                                          # target-selection (day-vote + night)
  WithForwardExposure(Fb): forward_exposure                                          # concealment / observable-act
  WithPublicPrivate (G)  : public_private_text, divergence_sign[enum]                # private-info, where the gap is a decision input
  + role conditioners    : bullets_left (vigilante), ally_revealed (wolf)            # criticality-family numerics
```

### Two composed profiles the walkthrough found
- **`PowerRoleDay`** = `WithHeat` + `WithConsensus` + `WithTargetLandscape` + `WithForwardExposure`
  (survival driver) + a **role-specific conditional G** keyed on that role's private asset
  (healer = save-knowledge · investigator = findings · vigilante = whiff-info). Healer/investigator/
  vigilante day cells share this shape.
- **`DeceiverConcealment`** = `WithForwardExposure` + `WithPublicPrivate` read as ONE coupled driver
  (the story *is* the heat management) + `WithConsensus` + `WithTargetLandscape`. Wolf/SK share it;
  wolf adds `ally_revealed`, SK swaps ally-coordination for a faction-balance objective (payload).

### The 11 cells
| cell | dims beyond spine | driver (lead with) | horizon |
|---|---|---|---|
| villager · day | criticality, D, heat, E | D / E (the hunt) | immediate |
| healer · night | criticality, E | E (value × predicted-threat) | immediate |
| healer · day | criticality, D, heat, E, F, **G-light** | **F** (survival) | immediate (claim-timing net rides in outcome text) |
| investigator · night | criticality, E | E (info-gain) | immediate |
| investigator · day | criticality, D, heat, E, F, **G** | **G** (findings vs public) | **net** (reveal-timing) |
| vigilante · night | criticality(reversibility), E, F-light, `bullets_left` | E (confidence × cost; whiff-probe) | immediate |
| vigilante · day | criticality, D, heat, E, F, **G-conditional** (post-whiff) | **F** (survival, while `bullets_left`>0) | immediate |
| wolf · night | criticality, E, F | E (value − pattern-risk; + ally) | **net** |
| wolf · day | criticality, D, heat, E, F, G, `ally_revealed` | **F+G** (concealment) | **net** |
| serial_killer · night | criticality, E, F | E (survival / faction-balance) | **net** |
| serial_killer · day | criticality, D, heat, E, F, G | **F+G** (solo concealment) | **net** |

**Horizon resolves per cell** by targeting/truth-finding (immediate) vs reveal-timing/concealment
(net) — no third "mixed" bucket. The outcome text always carries both halves; horizon only sets which
anchors the skim (role-aware `_compose_outcome`).

**Edge calls settled by the principle "a mixin attaches iff its dimension is a decision input for that
cell's action":** no night cell carries `WithConsensus`/`WithHeat` (day phenomena); `WithForwardExposure`
at night only on observable acts (wolf/SK kill, vigilante shot); night `WithPublicPrivate` = none of
the merged set needs it (investigator-night is pure info-gain — the gap is a *day* tool).

---

## 3. Conditioners (the regime-flippers) + criticality both-sides

Some numerics don't just rank — they **activate/deactivate whole dimensions** (flip the playbook):
- `distance_to_parity` / `players_alive` (all): early healer conceals, late healer reveals; the whole
  playbook pivots on the number.
- `bullets_left` (vigilante): `0` → reverts to a pure villager (power-role dimensions go dormant).
- `ally_revealed` (wolf): partner outed → vote calculus flips.

All conditioners get the **both-sides treatment**, same as the direction enums:
- **exact value → reranker** (the magnitude/flag the embedding mangles), for precise proximity/gating.
- **stakes-IMPLICATION phrased into the embedded text** so recall lands in the right regime — because a
  wrong-regime neighbor isn't "less applicable," it's the *opposite* lesson, and recall is the one
  stage no reranker touches. Phrase the *implication* ("one death from a wolf win, every vote decisive"
  / "no bullets left, playing as a regular villager"), NOT a bare label ("endgame") which is low-signal
  boilerplate that dilutes the mean.

This is the uniform pattern across every pulled-out dimension:

| dimension | embedded (recall) | exact (reranker) |
|---|---|---|
| consensus | `consensus_text` + `my_position` | `consensus_direction` enum |
| public-private | `public_private_text` | `divergence_sign` enum |
| criticality / conditioners | stakes-implication phrasing | `players_alive`/`distance_to_parity`/`is_swing`/`bullets_left`/`ally_revealed` |

**The real work is the extraction/situation prompt phrasing criticality as the implication** (embeds)
while emitting the exact numbers (reranker).

**Derivation — single-source, but LLM-generated (NOT game-state-deterministic).** Earlier draft said
"compute the numbers from game state" — REVERSED 2026-06-15: (a) a reasoning extractor handles
numbers/negation reliably (no need to avoid letting it), and (b) post-game extraction **can't pin an
extracted insight to a specific board-state/phase** — the extractor synthesizes across moments, so
there is no deterministic moment to stamp `players_alive` from. So the LLM emits the numbers. Keep the
two representations consistent by deriving the **prose FROM the numbers within the same LLM output**
(state the numbers, then the implication that follows) — never generate the two independently, or they
drift ("tense endgame" prose vs `players_alive=7`). The clean **pure-numeric + extracted-negation**
discipline matters **ONLY for the FT cross-encoder fusion path (fork-#3)** — the default reasoning-judge
reranker reads the prose+numbers holistically and needs no separate clean extraction.

---

## 4. Composable per-cell schema — single source of truth

One `SituationSchema` per cell (the mixin DAG above). It drives THREE things at once: post-game
**extraction** output fields, live **situation-summary query** output fields, and the **embedding
composition** — so query and storage compositions cannot diverge (the load-bearing symmetry that makes
one-vector-per-cell safe: every row in a namespace is the same subclass). `Observation` =
`SituationSchema` + `approach` + outcome fields; live `SituationEntry` *is* `SituationSchema`.

`_compose_situation` becomes a generic prefix serializer: walk the instance's `embed=True` fields,
prefix-label each present field, join. Auto-tailors per cell because the field set does.

> Inheritance shares field *definitions*, not stored *rows*: a role-invariant read is re-extracted into
> each namespace that needs it. Per-cell siloing is the deliberate choice (the prescription differs per
> cell); mitigation is cheap extraction (cached prefix), not a shared pool.

---

## 5. Composable prompt (kills the 3× repeated dimension blob)

Each dimension owns its **descriptive** guidance once. For the structured-output paths (extraction +
situation-summary) the guidance IS the Pydantic `Field(description=)` on the mixin — both get it free,
cannot drift. For the dedup prompt (compares composed strings) assemble the same fragments from a
registry / read off the schema descriptions. Every fragment obeys Rule 2 (state, not prescription).
The old `SITUATION_ROLE_LENS` prose folds into these fields **with its prescriptive bleed stripped**
(e.g. healer "whether it's time to claim" → "how exposed my role currently is").

---

## 6. Horizon (role-aware `_compose_outcome`, per-cell)

Per §2's per-cell horizon column. Immediate-first → villager, healer(both), investigator-night,
vigilante(both). Net-first → investigator-day, wolf(both), SK(both). 2-way, no "mixed" bucket; both
outcome halves always present, horizon only sets the skim anchor.

---

## 7. Reranker fork — why the structured fields exist (fields IN scope; fusion DEFERRED)

The numerics/enums are dual-purpose: a **reasoning judge** reads them in-model (numbers + signs, no
fusion); a **FT cross-encoder** can't (architectural) → needs external `|Δ|` + exact enum-match = the
**FT-CE-≈-flash-lite-cheaper USP (fork-#3, DEFERRED)**. This build only EXPOSES the fields. Recall
asymmetry: phrase direction/criticality-implication into embedded text (recall is sign/regime-blind
otherwise) + exact values to the reranker; generous top-k so the pool spans the regime range.

---

## 8. Modules / prompts touched + downstream ripple

| file | change | sensitivity |
|---|---|---|
| `Agents/schemas/memory.py` | per-cell `SituationSchema` mixin DAG; `Observation`/`StrategyPoint` rebuilt; generic `_compose_situation`; role-aware `_compose_outcome` | **model-visible/FROZEN** |
| `Agents/schemas/output.py` | `SituationEntry` = per-cell `SituationSchema`; vote field-order flip (`updated_strategy` before `vote_target`) | **model-visible + live** |
| `Agents/prompts/extraction.py` + `memory/extraction/inputs.py` | per-cell tail + criticality-as-implication phrasing + horizon framing | model-visible |
| `Agents/memory/extraction/extraction_agent.py` | fan-out binds per-cell schema; merge | plumbing |
| `Agents/memory/enrichment/situation_agent.py` | live query becomes **phase-aware** (was role-only), emits the cell schema | **live runtime** |
| `Agents/prompts/memory.py` | dimension-guidance registry (descriptive-only); `SITUATION_ROLE_LENS` folded into fields + deleted | model-visible + live |
| `Agents/prompts/day.py` | vote contract field-order flip | live runtime |

**Downstream consequences:** (1) `_compose_situation` signature change → all callers (situation_agent,
dedup prefilter/agent/store_ops/pipeline, `SituationEntry.composed`, auto_dedup_dataset_builder).
(2) Dedup thresholds tuned on old composed string → may drift; freezing, screen reads retrieval not
dedup. (3) Reranker input shifts but rerank≈raw → screen uses raw obs-only top-k. (4) Stores → legacy;
fresh re-extraction → new `v5_x`. (5) Leak checks on new G/forward_exposure fields (per-role namespaced
→ no cross-agent leak, still run `check_*`). (6) Tests: schema-shape + determine_winner/dedup guards.
(7) Screen harness already reads `SituationEntry`.

---

## 8b. Cheap-first slice — change-NOW vs DEFER decision per affected file (2026-06-15)

The screen is **self-contained** (it computes the query-side criticality deterministically from the
frozen board and does its own retrieval against `v6_0` — both arms share one embedding + one candidate
pool, the only delta is criticality conditioning). The re-extraction is a **focused offline runner**
mirroring `augment_agent.py`. Consequence: the cheap-first slice touches ONLY the schema (additively),
a scoped re-extraction prompt+runner, and the screen. Every LIVE-path edit in §8 defers to step-4
("roll the full DAG", after the screen shows the lever). New store name = **`v6_0`** (whole pipeline
changes extraction→retrieval→adoption; not a v5 point release).

| §8 file | spec change | cheap-first decision | why |
|---|---|---|---|
| `schemas/memory.py` | mixin DAG; Observation/StrategyPoint rebuilt; generic compose; role-aware `_compose_outcome` | **PARTIAL NOW (additive)** — add `_Embed`+`compose_situation_embed`, `BaseSituation`+`WithConsensus`/`WithHeat`/`WithTargetLandscape`, `VillagerDayObservation`/`VillagerDayExtraction`, `cell_observation_schema_for`, `StoredObservation` +4 optional v6 fields. **DEFER** replacing legacy `Observation`/`StrategyPoint` + role-aware `_compose_outcome` | additive keeps v5 pipeline + other roles live; villager·day horizon = immediate (screen scores votes directly, no net-first outcome reorder needed) |
| `schemas/output.py` `SituationEntry` + vote field-order flip | per-cell `SituationSchema`; `updated_strategy` before `vote_target` | **DEFER (both)** | `SituationEntry` is the LIVE query schema — screen self-computes query criticality, doesn't use it. Field-order flip = the *separate* reorder experiment, not the criticality lever |
| `prompts/extraction.py` + `memory/extraction/inputs.py` | per-cell tail + criticality-as-implication + horizon | **NEW SCOPED NOW** — add a villager·day extraction tail (criticality-as-implication) used ONLY by the re-extraction runner; do NOT edit live `POSTGAME_*`/`ROLE_EXTRACTION_*`; do NOT feed old `SITUATION_STANDARDS` dim prose with the new schema (mismatch) | guidance carried by schema `Field(description=)` (single source); live prompt-freeze preserved |
| `memory/extraction/extraction_agent.py` | fan-out binds per-cell schema; merge | **DEFER live fan-out** — runner invokes extraction directly with `VillagerDayExtraction` (own thin invoker, mirrors `augment_agent`) | step 4 |
| `memory/enrichment/situation_agent.py` | live query phase-aware; emits cell schema | **DEFER** | live runtime; screen self-computes query criticality |
| `prompts/memory.py` | dimension-guidance registry; `SITUATION_ROLE_LENS` fold+delete | **DEFER** | re-extraction guidance lives in schema `Field(description=)`; fold/delete is a live + model-visible edit = step 4 |
| `prompts/day.py` | vote contract field-order flip | **DEFER** | separate reorder fix, not the criticality lever; live runtime |
| downstream `_compose_situation` callers (situation_agent, dedup_agent/store_ops/pipeline/prefilter, `SituationEntry.composed`, auto_dedup_dataset_builder, components/situation_summary) | signature ripple | **NO CHANGE NOW** | legacy `_compose_situation` kept intact; v6 uses a *separate* `compose_situation_embed` → zero ripple |
| dedup thresholds | tuned on old composed string → may drift | **N/A NOW** — `v6_0` written RAW (no production dedup); screen reads retrieval not dedup | rerank≈raw; dedup re-tune = Phase B track 2 |
| reranker | input shifts but rerank≈raw | **N/A NOW** — screen uses raw obs-only top-k; conditioned arm = screen-local criticality rerank, not the production CE | fork-#3 deferred until after screen |
| leak checks (`check_*`) | new G/forward_exposure fields | **N/A NOW** — villager·day adds no concealment fields; re-extraction is offline (no live Send payload) | add `check_*` when wiring live (step 4) |
| tests | schema-shape + guards | **ADD NOW** — villager·day schema-shape test (all-required, numbers-excluded-from-embed, `_Embed` no-leak, embed order) | new code needs a guard; determine_winner/dedup guards untouched |

## 9. Build order (gate the re-extraction bill behind a signal)

1. `BaseSituation` + `WithConsensus` + `WithHeat` + `WithTargetLandscape` → **villager·day cell only**. ✅ DONE (2026-06-15, `Agents/schemas/memory.py`, additive; commit 2b57911).
2. Re-extract that cell. ✅ DONE — `memory_stores/v6_0`, 119 RAW villager·day obs / 20 games (`evaluation/src/experiments/reextract_villager_day.py`; commit 684f39c).
3. Screen: criticality-conditioned vs flat, town day-vote, **stratified by day** (falsifiable at day-2),
   paired, one sitting/pinned model, per-stratum, reads direction + causal-flip-rate (not significance).
   ✅ DONE → **GO**. Signature confirmed: high-criticality cond−flat +0.25 vs mid-game/day-2 ~null;
   flips 4→threat / 0 away. Full record `criticality_screen/experiment_log.md` (commit 7c00c9d).
4. Only if the lever shows → roll the full DAG (the two profiles, F/G on wolf·day) + re-extract the rest.
   **← NOW UNLOCKED by the step-3 GO** (the live-path rewiring deferred in §8b also lands here). A
   confirmatory second batch / λ-sweep before rolling is optional but cheap; the full build is gated by
   the mandatory freeze-time regression gate regardless.

Interview frame = the ladder + method (paired/stratified/drift-immune/judge-free; triage not verdict),
not a big N quoted as proof.

## 10. Open items (all resolved 2026-06-15)
1. **"mixed" outcome order** — DISSOLVED (horizon resolves per cell, no third bucket).
2. **Fork-#3 (FT-CE-fusion USP)** — **LOCKED: go/no-go decided only AFTER the screen.** Build exposes
   the fields; the pure-numeric/clean-negation extraction (§3) is needed only if fork-#3 goes.
3. **healer·day G** — **LOCKED: keep light** (save-knowledge as a late-game reveal asset).

## 10a. Cross-link — the situation schema is also the PROCEDURAL-memory reward signal
The valenced subset of these dimensions (heat, forward_exposure, standing, parity-progress,
target-removed — the ones with a good/bad direction; the descriptive dims are context, no valence) is
the **local reward** for evaluating/weighting `strategy_points` (procedural memory): reward(rule P) =
**role-signed difference-in-deltas** on the valenced subset between adopters and non-adopters of P in
matched situations (quasi-causal, no game-outcome attribution). So one schema does triple duty:
retrieval key + embedding match + reward. Full design + the deceiver-first experiment that gates it →
`evidence/phase_b/procedural_memory_experiment.md`.

## 11. Pointers
- Narrative + walkthrough: `evidence/memory_system/effectiveness/decision_replay/experiment_log.md`.
- Phase B plan: `evidence/phase_b/plan_review.md`. Roadmap: `project-ship-roadmap`.
- Screening-layer report: `evidence/memory_system/effectiveness/decision_replay/report_screening_layer.md`.
