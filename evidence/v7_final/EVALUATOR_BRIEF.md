# v7 Memory System — Evaluator Brief

> **Purpose.** A self-contained entry point for an external evaluator agent auditing the v7
> memory system. Read §0–§4 in full (compact, judgment-critical). Use §5 to drill into primary
> sources **only where forming a specific verdict needs the raw data** — that is the whole token
> strategy. This brief states facts and open questions only; it deliberately supplies **no author
> verdict** (§6 poses the questions; the conclusions are yours to reach).

---

## §0 — Charge & rules of engagement

**Your role:** a read-only design / apparatus / evidence auditor.

**Assess, in order:**
1. **Design soundness** — are the *principles* behind v7 (§3) sound in their own right?
2. **Evidence credibility** — does the evidence trail (§2, §5) support what it claims?
3. **Apparatus validity** — are the instruments (§4) trustworthy enough to carry those claims?
4. **Gaps** — what is missing or under-measured?
5. **Alternatives** — what other designs / cheaper tests are worth considering?

**Hard constraints:**
- **Do NOT re-run any experiment.** The two paid runs are inconclusive for a *configuration*
  reason (§2), not because a rerun is needed from you.
- **Do NOT change code.** No edits, no fixes.
- **Output = a report + plan only.** A verdict per axis above, a ranked list of gaps, and
  alternatives to consider.

**Read economically.** The three load-bearing primary files, if you read nothing else:
- `evidence/v7_final/report.md` — the canonical v7 report (claims + post-mortem).
- `evidence/v7_final/experiment_log.md` — the journey, incl. the invalidation corrections (§11j, §12f).
- `evidence/evaluation/source_map.md` — the apparatus reliability **ledger of record** (code-verified 2026-06-28).

---

## §1 — The v7 thesis, in one page

**The reframe that motivated v7.** Everything measured *before* v7 tested a **static, one-shot-extracted
store** — effectively a frozen retrieval index. Two failure modes were therefore never on trial:
(#1) **no adaptivity / compounding** — bad lessons never de-rank or stale out; (#2) **single-game
extraction bias** — with no cross-game outcome signal, the store can't tell good play from lucky play.
v7 is the **final memory-research iteration**, built to put both on trial. It rests on three pillars:

1. **Dimensions** — a structured schema on memory cells, keyed by (role × phase). The *same* schema
   drives extraction, the live query situation, dedup, and retrieval — one shared key across the stack.
2. **Derived proxies** — a **de-lucked, per-decision outcome credit** (explicitly **not** game win/loss,
   **not** the LLM's `net_verdict`), expressed as **lift** over a memory-off baseline. This is what
   grades a note.
3. **Compounding store** — a generational loop: **re-mine → credit → consolidate**
   (synthesize / prune / evict / decay), with success measured as the **slope** of decision quality
   across generations vs a matched memory-off arm.

**Trust stack** (from `plan.md` §1b): substrate → extraction → **credit** → **consolidation**, with the
**dimensions** as the shared key that ties them together. Work lives on branch `feature-dimension-schema`.

---

## §2 — State-of-knowledge ledger  ⭐ *read before any primary source*

The archive contains claims that are **live in the record but corrected in reality.** Anchor here first,
or you risk mistaking *"the experiment failed to execute"* for *"the design was tested and lost."*

### ✅ Established (valid)
| Fact | Basis | Note |
|---|---|---|
| **Static memory helps town** | Paired, same-epoch, pre-registered A/B, N=30: raw town **+17pp** (p=0.267); reranked **+33pp** (p=0.013); proxy basket significant (Wilcoxon). | This measures **having** memory — a **different experiment** from the compounding loop. Does not by itself support the compounding thesis. `memory_system/effectiveness/paired_ab/report.md` |
| **Derived-proxy validation** | Town outcome basket point-biserial vs own-faction win **\|r\|≈0.55–0.65**, both pooled (N=50) and OFF-only (N=30), reconfirmed N=180. | The trustworthy scoring core. `evidence/evaluation/metrics/report.md` |
| **The mechanism runs** | Smokes + `loop_gate/` show re-mine→credit→consolidate produce a compounding-*shaped* store end-to-end. | Mechanism validated, **not** the effect. |
| **Held-out credit reproduction** | Losers stay negative 89% vs 61% base; Pearson **+0.54** (paired, static). | Valid **within the v6ab epoch**; not epoch-stable. |
| **Arm-guard shipped** | `--expect-factions` / `invariants.assert_arm_factions` hard-fails on arm≠intent; `arm_factions` recorded in `loop_history`. | The process fix that closes the config-slip class below. |

### ⚠️ Invalid / retracted (with *why*)
- **Both paid loop runs (~$130 total) are INCONCLUSIVE due to run-configuration mistakes — not a
  negative result on the design:**
  - `town_only_run1` / `run2` (~$100): the de-luck **baseline was distorted** — run-1 sourced the base
    rate from incidental memory-off decisions *inside* the ON games; run-2 used a dedicated OFF arm but
    it was **unpaired** (different boards → biased per-cell means). → every lift / synthesis / prune
    read is invalid, not merely noisy. (`experiment_log.md` §11j)
  - `v2_full` ($15): the ON arm ran **`all_enabled`** (every faction had memory) instead of the intended
    **`town_only`**. Town then faced memory-*improved* wolves → an **arms-race confound** mechanically
    depresses town accuracy. Invalid for the town / compounding question. (`experiment_log.md` §12f,
    `report.md` §5c)
- **The "+0.41 town / +0.556 discussion" lift was a HALO — RETRACTED.** It was a raw `(pos−neg)/follow`
  level with the tagger base pinned to 0 (never differenced against no-memory), compounded by a
  game_id/tag-cache collision in the first salvage. Differenced against the valid day-vote floor, town
  discussion on−off is noise (~−0.12). *(Do not confuse this retracted **town credit-level** with the
  separately-validated **tagger-as-deceiver-skill** metric in §4 — different quantity, similar number.)*

### ❓ Open (not answered)
- **Does town memory COMPOUND across generations?** OPEN. No post-hoc analysis repairs a board that
  already contained memory-wolves; only a valid `town_only` rerun could answer it. (`report.md` §8)
- **v2 repositioned** as an all-memory-on per-faction A/B (`v2_full/v2_salvage.py`): **wolf**
  tentative-positive / compounding-shaped (on−off +0.077, slope +0.086); **town** confounded; **SK**
  null — **all underpowered at 4 games/gen.**
- **The architecture is NOT frozen.** The compounding question remains the live open question.

---

## §3 — Design principles (judge these independent of the botched runs)

### Pillar 1 — Dimensions
- **Cells** keyed by (role × {day, night}) — 11 concrete cells; each a Pydantic schema composed from a
  `BaseSituation` spine + dimension mixins (`WithConsensus`, `WithHeat`, `WithTargetLandscape`,
  `WithForwardExposure`, `WithPublicPrivate`, + role conditioners `bullets_left` / `ally_revealed`).
- **Load-bearing symmetry:** the *same* schema emits the stored observation **and** the live query
  situation → query and stored embeddings compose identically (`compose_situation_embed`).
- **Field disposition (3 ways):** embed high-entropy free text (recall); **extract** exact
  numeric/ordinal/relational values as reranker-only fields (a bi-encoder mangles magnitudes/signs —
  "approximation is the bug"); a few coarse enums act as **hard dedup gates**.
- **Two generating rules:** (1) a field is a **hard gate only when crossing it makes a lesson *invalid***
  (the opposite lesson, not merely less applicable), else soft; (2) **situation = state, never
  prescription** (guards the prompt-boundary leak mode; keeps embeddings state-only).

### Pillar 2 — Derived proxies / credit
- **Reward = a de-lucked per-decision PROXY, never the halo.** Three things "outcome" could mean; only
  one is allowed: game win/loss (halo ✗), `net_verdict` (halo ✗), **de-lucked proxy (✓)**.
- **Lift** = an SP's mean followed-decision outcome − the **memory-off base rate** of the same cell,
  then **shrunk** toward 0 by follow count (`shrunk = lift × follow/(follow+5)`) as a small-sample CI
  stand-in. Separates genuinely-helpful notes from ones that merely rode along with good decisions.
- **Faction-relative:** town = threat-hit vote; **wolf = blend-with-room-plurality** (a concealment
  proxy, bussing-aware, r≈+0.20 — not target-based); SK = any non-self lynch.
- **Deliberate cuts / guards:** LLM valence is **de-haloed and weighted, not discarded** (trust it more
  where it *disagrees* with outcome); a deterministic **delayed/windowed** credit was **rejected**
  (survival ⊥ decision quality); per-SP grading stays **coarse** (density guard — median ~3 follows/SP);
  offense/defense is a **diagnostic**, not a policy constraint. Rationale for de-luck at all: the
  follow/override choice is degenerate (~99% follow, no variance) → credit the *realized outcome*, not
  the choice.

### Pillar 3 — Compounding store
- **Per generation (~5 games):** (1) **re-mine** — on-policy extraction rebuilt every game, freeze-old
  merge folds new observations in; (2) **credit** — recompute the de-luck ledger over a **rolling
  window** (recompute-not-accumulate = the non-stationarity guard; baseline from the **same-epoch OFF
  arm** = drift-free by construction); (3) **consolidate** — synthesize → SP-dedup → prune (shrunk
  lift < τ, follow ≥ N) → evict (surfaced-but-never-followed) → observation decay (age × frequency), with
  a **proven-SP exemption** protecting positive-lift SPs with ≥2 follows.
- **Architecture splits:** **fast-cull / slow-synth** (cull every gen, paid LLM synthesis only every
  k gens); **incremental synthesis** (re-synth only cells with new observations); **SPs never MERGE**
  (combining directives is incoherent — keep/discard/drop/revise only).
- **Success criterion:** the **slope** of decision quality across generations vs a matched memory-off arm.
- **Safety framing:** compounding is **double-edged** — a mis-credit drives a vicious spiral a static
  store cannot produce; the de-luck credit + guards are the rails. Thermometer (credit measures) →
  thermostat (consolidation acts), store = shared state.
- **Production form (designed, not built):** an async, batch-discounted, out-of-band pipeline;
  idempotency the one hard requirement. Not part of the current synchronous experiment.

---

## §4 — Apparatus reliability inventory

Ledger of record (with dated code-verification): **`evidence/evaluation/source_map.md`**. The recurring
theme: **every *live* LLM judge is uncalibrated (machine scoring machine, no human/golden anchor); the
trustworthy numbers are the deterministic and outcome-anchored ones.**

### Trust (validated / convergent)
| Instrument | What it anchors on | Caveat |
|---|---|---|
| Town outcome-proxy basket | point-biserial vs win, \|r\|≈0.6 | the scoring core both tiers depend on |
| Dedup deterministic golden scorer (`eval-dedup-score`) | human goldens, deterministic scoring | strongest L2 artifact; **goldens stale on v4 store** |
| LLM-free loop measure (`loop/measure.py::generation_score`) | de-luck slope, deterministic, unit-tested | soundest instrument in the loop |
| Paired-A/B machinery + hard-fail arm-guards | same-epoch control; roles lookup | caught both invalid runs |
| Discussion **tagger** *as a deceiver-skill metric* | blinded + verbosity-controlled partial-r vs **won** | +0.56 wolf / +0.60 SK / +0.02 town (N=24). Validates a **metric**, not a memory effect |

### Do NOT over-read (the ceiling)
- **Every live LLM judge is uncalibrated:** extraction (de-bugged ≠ calibrated; original dims
  ceiling-saturated ≈4.0); day-summary ("smoke test, not a metric"); retrieval (**active bug** —
  `<2 items` short-circuit sets efficiency=5, silently pooled → arm-asymmetric inflation);
  application/adherence (**calibration designed, never run** — the one load-bearing uncalibrated judge).
- **Win-rate is underpowered** (MDE ~36pp) — the *proxies* carry the signal, not the win column.
- **v7 synthesis quality and consolidation quality are entirely UNJUDGED** — no judge/score path exists.
- **The wolf-memory null** is a power + invalid-runs + no-direct-wolf-arm problem, **not** a missing
  instrument.
- **The live v6 shipping path (plain similarity, reranking OFF) is the least-measured** — diagnostic
  confidence is highest where the code isn't running.

### Named failure modes baked into the apparatus
- **Flat / ceiling-saturated dimensions** = zero-information gauges.
- **Regen-and-judge in one harness** confounds generation with scoring.
- **Outcome-halo selection** — a proxy conditioned on winning measures the win (the `net_verdict`
  selection trap).
- **Silent-N paths** — parse-fail rows silently dropped from averages; retrieval efficiency fallback
  pooled; a structured-field instruction ignored → ~⅓ of notes silently skipped (several since fixed).
- **What LLM judges structurally MISS:** information gain, subtle fabrication, "does this read right to a
  person" → the **sampled-human-review rung is underbuilt** (`sampled_human_review/report.md`).

---

## §5 — Evidence & code pointer map (drill down only as needed)

### Evidence (read order; validity tagged)
1. `evidence/v7_final/report.md` — canonical v7 report. §5c = invalid-run post-mortem; §8 = still-open;
   §9 = artifacts table. **[valid narrative + retractions]**
2. `evidence/v7_final/experiment_log.md` — the journey. §11j (run-1/2 invalid); §12f (v2 `all_enabled`
   confound + halo retraction); §12g (tagger validity). **[authoritative record]**
3. `evidence/memory_system/effectiveness/paired_ab/report.md` — Claim-1 standing positive (N=30).
   **[valid; a *different* experiment — measures having memory, not compounding]**
4. `evidence/evaluation/source_map.md` — apparatus ledger of record. **[trust ledger]**
5. Design docs: `evidence/v7_final/{plan.md, consolidation_design.md, discussion_credit_design.md,
   production_design.md}`, `evidence/phase_b/dimension_schema_build_spec.md`. **[design current-state]**
6. Raw invalid-run data: `evidence/v7_final/{town_only_run1, town_only_run2, v2_full}/`
   (`v2_full/v2_salvage.py` = the repositioned all-memory-on A/B). **[invalid / confounded]**
7. Executed validation harnesses (what actually *ran* vs what is specced):
   `heldout_credit_reproduction.py`, `synth_deluck_ab.py`, `windowed_credit.py`, the `g2_*`/`g3*` gates,
   `loop_gate/`, `*smoke*/`. **[valid but epoch-provisional / non-inferential by design]**

### Code (the implementation under audit)
- **Dimensions:** `Agents/schemas/memory.py` (schema), `Agents/memory/extraction/cell_units.py`
  (cell fan-out), `Agents/memory/dedup_gate.py` (gates), `Agents/memory/retrieval/dimension_gating.py`.
- **Proxies / credit:** `evaluation/src/loop/{decision_scoring.py, credit_backfill.py, credit.py,
  discussion_tagger.py, measure.py}`; `evidence/v7_final/credit_backfill_ledger.json` (materialized).
- **Compounding loop:** `evaluation/src/loop/{driver.py, consolidate.py, config.py, merge.py,
  invariants.py}`; `Agents/memory/strategy_synthesis.py` (LLM synthesis).

---

## §6 — Your charge, as specific questions (neutral; no answers supplied)

**Design soundness**
- Is **lift = mean followed outcome − same-epoch memory-off base rate, shrunk by follow** a sound credit
  signal? De-luck removes *outcome* luck but explicitly **not opponent strength** — does that leave a
  hidden confound in the baseline?
- Is (role × phase) the right cell granularity? Does the extraction-query schema **symmetry** buy
  retrieval quality, or over-constrain what can be recalled?
- Is a **slope vs a matched OFF arm** the right — and *falsifiable* — success criterion for compounding?
- Are "SPs never merge / coarse per-SP grading / offense-defense as diagnostic" mutually consistent with
  a compounding thesis, or in tension with it?

**Evidence credibility**
- Do the documented retractions/invalidations fully account for the halo and confound risks, or do
  residual halo paths survive anywhere in the credit or synthesis chain?
- Does the standing Claim-1 positive (static memory helps town) bear on the compounding thesis at all, or
  is it orthogonal?
- Is the wolf "tentative-positive / compounding-shaped" read defensible at 4 games/gen, or is it inside
  its own noise floor?

**Apparatus validity**
- Given every live LLM judge is uncalibrated, **which v7 conclusions actually rest on an LLM judge** vs a
  deterministic/outcome anchor?
- Is the discussion tagger's deceiver-skill validation (blinded partial-r) strong enough to carry the
  credit it feeds into consolidation?
- Does "consolidation quality entirely unjudged" threaten the compounding claim *specifically*, or only
  the efficiency of the loop?

**Gaps & alternatives**
- What single cheapest measurement (analysis/design, **not** a rerun) would most reduce uncertainty about
  compounding?
- Which unvalidated instrument, if calibrated, unlocks the most downstream trust?
- Are there alternative credit-assignment or consolidation designs more robust to the noise floor / the
  arms-race confound at feasible N?
- Is there a cheaper experimental design that isolates compounding from single-game extraction bias?

**Deliver:** a report + plan — a verdict on each of the five axes in §0, a ranked list of gaps, and
alternatives worth considering. No code changes, no reruns.
