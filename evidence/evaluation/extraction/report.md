# Extraction — Evaluation Apparatus Report

> **Scope: the apparatus, not the design.** Covers *how we measure* extraction quality (post-game mining of
> obs/SP + v7 synthesis) and *how far to trust it* (L1 + L2). The extraction **design** (per-role fan-out,
> v7 credit-aware synthesis) stays in [`../../extraction/quality/`](../../extraction/quality/),
> [`../../phase_b/`](../../phase_b/), [`../../v7_final/`](../../v7_final/). Lens + skeleton:
> [`../report.md`](../report.md); ledger: [`../source_map.md`](../source_map.md).
>
> **Verdict: 🟡 PARTIAL — DE-BUGGED, not calibrated** *(downgraded from ✅ VALIDATED — see corrections).*
> The engineering hygiene is genuinely strong, but the judge is machine-only with no golden/human anchor, the
> original dimensions are ceiling-saturated, and v7 synthesis quality is **not judged at all**.

## Objective the apparatus targets

Extraction decides what a finished game contributes to memory. The apparatus should answer *"is each mined
observation/strategy-point specific, grounded, epistemically honest, and useful as a retrieval target?"* —
and, for v7, *"is a credit-aware synthesised strategy-point any good?"*

## L1 — the instrument

- **Extraction judge** `judges/extraction.py` → console **`eval-extraction`** (`pyproject.toml:37`,
  confirmed real). `ExtractionScores` (`core/schemas.py:104-188`): **8 flat dims, each int 1-5** —
  `specificity · epistemic_compliance · grounding · coverage · diversity · perspective_compliance ·
  strategy_depth · novelty` + `brief_reasoning`. Model default gemini-2.5-pro (frozen 48-game runs used
  gemini-3.5-flash; model-comparison used 3.1-pro-preview). `max_retries=1`.
- **Per-role** (`per_role_extraction.py`) is **the same judge** applied to role-sliced inputs, aggregated by
  mean — not a different instrument.
- ⚠️ **Stale prompt header bug:** the user prompt says "Score the following **five** dimensions"
  (`prompts.py:470`) but the schema demands all **8**. Output unaffected (schema is the contract), but it's a
  live self-contradiction.
- **v7 SYNTHESIS quality has NO judge.** Zero references to `ExtractionScores`/`run_extraction_judge` in
  `evaluation/src/loop/`. Synthesised SPs are measured only by (a) the loop's **outcome** slope
  (`measure.py`) and (b) one **underpowered** offline lexical probe (`v7_final/sp_synthesis_quality_check.py`,
  token-Jaccard, self-reports "UNDERPOWERED"). An in-pipeline `with_track_record` counter flags credit-blind
  (halo-only) synthesis — honesty hook, not a quality measure.

## L2 — trust

**The 2 judge bugs + fixes (both real, verified live in code):**
1. **Epistemic scope** — judge applied `epistemic_compliance` to observations too (which legitimately use
   omniscient framing) → deflated −1.19 (2.81→4.00). Fixed: `prompts.py:482-484` scopes it to strategy
   points only.
2. **Specificity field** — judge scored `specificity` on the narrow `situation` field, but retrieval uses
   `composed_situation` (+ dimensional fields). Fixed: `extraction.py:22-32` emits the dimensional fields +
   prompt evaluates the composed query. Lifted +0.69 (3.19→3.88).
Both fixes shipped; the report's accounting matches the code. **These are genuine apparatus improvements —
the strength is real.**

**But — the trust gaps that pull it off ✅:**
- **Machine-only, NO golden/human anchor.** Grep finds zero golden/human/inter-rater mentions; "calibration"
  appears only re judge-model/backend drift. The judge was **de-bugged against design intent** and
  face-validated — never validated against labels. Per source_map's own legend, ✅ requires
  correlation/held-out/cross-method convergence; extraction meets none. (Inconsistent with neighbours: dedup
  is 🟡 *with* a human golden; application/day-summary are ⏸/⚠️ for being uncalibrated — extraction has the
  same uncalibrated property but was rated a tier higher.)
- **Player-ID leak "0%" is model-dependent.** 0% on 3.5-flash/flash-lite/preview/2.5-pro after the
  NAMING-RULE fix (was 84.3% on observations pre-fix) — but **gemini-2.5-flash still leaks** (3.4% single,
  5.1% per-role). It's a deterministic script check (sound), not a judge.
- **(a) Flat dims — YES.** The 48-game runs cluster hard at 4.00 (coverage 48×4, grounding 47×4, epistemic
  48×4 post-fix); the original 5 dims are **ceiling-saturated / near-zero-information**. Only the two **added**
  dims (`strategy_depth` 3.95, `novelty` 2.95) produce differentiated scores. Per-role coverage/diversity are
  **self-admittedly mis-calibrated** for per-role output.
- **(b) Gen+judge variance blend** in the model-comparison phases: the *model ranking* varies the extraction
  model AND re-judges, so it blends extraction-gen + judge variance — though, unlike the day-summary harness,
  gen and judge are **separate passes** (`extraction_model_comparison.py` extracts; `eval-extraction` judges),
  not a single regen+judge harness. The 2-bug finding (Runs 1-3, fixed extractions, only judge prompt changed)
  is **clean** on this axis.
- **(d) Staleness:** frozen runs 2026-05-24/26 on 3.5-flash/3.1-pro-preview judges across a **Google→Vertex
  backend shift** the report says invalidates absolute-score comparison; the 48-case set predates the v6
  schema + per-role write-path.
- **(e) Small-N:** judge-bug runs n=48 (solid); every model/mode recommendation rests on **n=5-10 games**.

**Adjacent apparatus findings (the selection + screen threads):**
- **`extraction_selection` — net_verdict = outcome-halo.** The extraction prompt selects items for
  pivotalness but conditions on GAME OUTCOME; net_verdict separates won/lost at +0.84 — i.e. it validates
  *labeling* (faithful use of the injected outcome) but **NOT selection** (it largely answers "did your side
  win?", stamped on every action). Observations aren't deterministically turn-anchored, so per-action causal
  discrimination is unconfirmed. Fix (deterministic leverage anchor) is gated/unbuilt.
- **`criticality_screen` 🔴.** Conditioning retrieval on criticality is within ±0.03 **temperature noise**;
  the villager subset **sign-flipped** across two identical runs. A same-game-leakage bug was found+fixed
  mid-screen. The instrument is too noisy (single-draw-per-arm at temp 1.0) for effects <~0.06; high-crit
  stratum data-starved (N=7-23).
- **`forced_schema_screen` — a measurement diagnosis.** "One verdict per memory" instruction lived only in a
  pydantic `Field(description=)` (invisible to the model) → coverage 0.27; moving it to the prompt body lifted
  it to 0.97. It also **retracted an inflated metric** (the earlier "v6 engages more 0.697" was partial-
  coverage inflation; true applicable-rate ≈0.55) and ran same-epoch. High apparatus hygiene; n=48, n.s.

## Verdict + cheapest upgrade

**🟡 PARTIAL (de-bugged, not calibrated).** Strength = genuine engineering hygiene (2 verified bug fixes,
sound player-ID check, same-epoch screens, self-caught artifacts, honest retractions, halo named). Gaps =
machine-only/uncalibrated, ceiling-saturated original dims, n=5-10 + regen/backend-confounded model ranking,
and **v7 synthesis quality entirely unjudged**.

**Cheapest upgrade:** label a small human golden (~20-30 items, 2-3/role) and report judge-vs-human agreement
on the 8 dims — ~an afternoon; converts "de-bugged" → "calibrated" and exposes whether the ceiling-saturation
is real or leniency. **Second-cheapest:** point the existing `run_extraction_judge` at the v7 synthesised SP
store — the instrument exists; it's simply never aimed at synthesis (which is currently outcome-only).

## Evidence (code + L2 artifacts)

- **Code:** `evaluation/src/judges/extraction.py`, `judges/per_role_extraction.py`, `judges/prompts.py`,
  `experiments/extraction_eval.py`, `experiments/extraction_builder.py`,
  `core/schemas.py::{ExtractionScores,PerRoleExtractionScores}`; v7 probe
  `../../v7_final/sp_synthesis_quality_check.py`.
- **L2 artifacts (no golden — the gap; results pointed-at):** `../../extraction/quality/eval_results/*.jsonl`
  (Runs 1-3), `../../extraction/quality/model_comparison/`, the player-ID verification txts;
  `../../extraction_selection/experiment_log.md` (net_verdict halo);
  `../../phase_b/{criticality_screen,forced_schema_screen}/experiment_log.md`. ⚠️ the evidence manifest's
  `dataset_path` is a stale absolute path; the report's `scripts/per_role_*` paths graduated to
  `evaluation/src/experiments/`.

## Colocation call (JIT, 2026-06-28)

**Stays put — pointed-at.** Design-dominated folders (→ ch.3); there is **no golden** to colocate (its
absence is the finding), and the result JSONs are referenced by their L0 logs + live runners. Key numbers
distilled above.

*(Inspected 2026-06-28.)*
