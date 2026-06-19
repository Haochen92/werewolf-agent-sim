# (c) Extraction A/B — RECALL + model-capability (spec, not yet run)

**Status:** spec only. Paid (fresh extraction over a corpus). Gated: extraction conditions Phase B gold
labels → deliberate versioned experiment, not a casual tweak. Run the **small-slice pre-gate** first so we
don't "spend money for nothing."

## Why this A/B (and not a de-halo A/B)
De-luck credit, synthesis, pruning — all of (a)/(b) — operate only on what extraction already captured.
**Omission is the one error the loop can never fix** (commission gets pruned; a never-extracted lesson is
permanent). So the first-order extraction question is **recall — "did we capture what's needed"**, not
framing/de-halo (which only matters for lessons already captured). Free screens established: the extractor
is **thin** (median 3 obs/cell, 98% below its own 6-floor) but **not temporally blind** (obs span
early/late/parity). "Captures what's *needed*" is NOT free-measurable (it's a counterfactual; the
leverage-labeled corpus never extracted obs) → it needs this paid run.

## Two factors
- **Factor A — prompt (recall lever):** `baseline` (current free-form "extract 6–12 from pivotal moments")
  vs `must-cover` (feed the deterministic leverage-flagged do-or-die turns as **must-cover anchors** +
  leverage-derived budget; keep whole-game read, still invite un-flagged lessons — per §3 D-anchor:
  soft prior, NOT a whitelist).
- **Factor B — model (capability/cost):** `gemini-2.5-pro` (current) · `gemini-3.5-flash` (the pro backup)
  · `gemini-3.1-flash-lite`. Motivation: the loop re-extracts **every game**, so extraction-model cost
  dominates the loop's recurring bill — a cheap model that's "good enough" makes the whole loop cheaper.

## Corpus + the leverage denominator
- Use the **v6ab games** (they carry per-decision eval cases with the validated leverage signal) and
  **re-extract obs on them** (they never had obs extracted → no contamination). The flagged pivotal turns
  = high-leverage decisions (low `P(win|miss)` floor / `is_swing`).
- ⚠ Leverage is validated **town day-votes only** → the **recall metric is scoped to town day-votes**.
  The model arm still yields signal on ALL cells (de-halo, parse-rate, volume/distinctness don't need
  leverage flags).

## Metrics (and the kill-tests)
1. **PRIMARY — capture-rate of leverage-flagged turns** (recall). `must-cover` directly measurable (flags
   are inputs); `baseline` via fuzzy post-hoc match (stage/situation). **Kill-test:** if `must-cover` does
   NOT raise capture-rate over `baseline`, the recall lever is dead — stop.
2. **Model capability/cost:** capture-rate + de-halo `corr(net_verdict, faction_won)` + structure-populate
   + **JSON parse-failure rate** per model. **Kill-test:** if 3.5-flash (or lite) capture-rate + de-halo
   land within ε of pro → adopt the cheaper model for the loop (big recurring saving). If it craters →
   keep pro. ⚠ flash-lite needs an **all-required schema variant** (the `str|None` dims break its JSON) or
   its parse-failures confound the read — build that variant or exclude lite.
3. **SECONDARY (free, reuse existing screens):** obs volume + intra-cell distinctness
   (`extraction_quota_screen.py`), de-halo corr.

## The small-slice PRE-GATE (do this before the full spend)
Run all arms on **3–5 games** first. Read: (i) does `must-cover` lift capture-rate at all; (ii) flash-lite
parse-failure rate (is the all-required variant even viable); (iii) rough de-halo per model. Only scale to
the full corpus if the pre-gate shows a live signal. This is the "don't pay for nothing" guard.

## Caveats
- **Epoch-conditional:** results hold for the run epoch only; backend fixed (Vertex — never compare across
  backends); flash-lite drifts ~daily. A capability verdict is "in this epoch."
- **Freeze-gate:** adoption (new model and/or prompt) re-conditions Phase B labels → adopt-then-label,
  versioned. The A/B itself is the deliberate experiment the freeze permits.
- **Recall ≠ full "needed":** capture-rate of *leverage-flagged* turns is the measurable subset; true
  coverage gaps only fully surface in the loop (decisions failing with no covering memory).
