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
  vs `suggestive-anchor` — provide the deterministic leverage-flagged do-or-die turns as a
  **RECOMMENDATION**, not a command: *"these turns were pivotal by the game's math — give them attention,
  extract the lesson genuinely there, and still surface anything else you find."* Keep the whole-game read.
  Per §3 D-anchor: **soft prior, NOT a whitelist, NOT imperative.**
  - ⚠ Why not `must-cover`: an imperative ("emit a lesson per flag") FORCES a lesson onto a
    flagged-but-empty turn = **manufacture** (the confabulation failure mode) and re-imposes the whitelist
    spirit we rejected. The flags raise *attention*, not a quota.
  - **Manufacture guard:** pair the capture-rate read with a check that newly-captured flagged-turn obs
    survive a validity/credit screen — i.e. recall went up because real lessons surfaced, not because the
    model padded the suggested turns.
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
1. **PRIMARY — capture-rate of leverage-flagged turns** (recall). `suggestive-anchor` directly measurable
   (flags are provided as input → check an obs surfaced per flag); `baseline` via fuzzy post-hoc match
   (stage/situation). **Kill-test:** if `suggestive-anchor` does NOT raise capture-rate over `baseline`,
   the recall lever is dead — stop. Read it WITH the manufacture guard (Factor A) so a capture-rate gain
   isn't just padding the suggested turns.
2. **Model capability/cost:** capture-rate + de-halo `corr(net_verdict, faction_won)` + structure-populate
   + **JSON parse-failure rate** per model. **Kill-test:** if 3.5-flash (or lite) capture-rate + de-halo
   land within ε of pro → adopt the cheaper model for the loop (big recurring saving). If it craters →
   keep pro. ⚠ flash-lite needs an **all-required schema variant** (the `str|None` dims break its JSON) or
   its parse-failures confound the read — build that variant or exclude lite.
3. **SECONDARY (free, reuse existing screens):** obs volume + intra-cell distinctness
   (`extraction_quota_screen.py`), de-halo corr.

## The small-slice PRE-GATE (do this before the full spend)
Run all arms on **3–5 games** first. Read: (i) does the recall lever lift capture-rate at all; (ii)
flash-lite parse-failure rate (is it even viable); (iii) rough de-halo per model. Only scale if a live
signal. This is the "don't pay for nothing" guard.

**PRE-GATE RUN (2026-06-19, MODEL arm only, 3 games, `extraction_model_ab_compare.py`):** CLEARED.
| arm | obs/cell | meanJac | near-dup | de-halo r |
|---|---|---|---|---|
| pro-2.5 | 2.82 | 0.21 | 0% | +0.43 |
| flash-3.5 | 3.24 | 0.22 | 0% | +0.64 |
| flash-lite | 3.1 | 2.46 | 0.18 | 0% | +0.50 |
- **flash-lite VIABLE** — the `str|None` parse-failure did NOT materialize (langchain coerces); thinnest,
  dropped 1/51 cells. **Capability comparable** across all three (same volume band, distinct/non-padded).
- **De-halo INCONCLUSIVE on 3 games** (2-town/1-SK, low variance): pro marginally cleanest (+0.43),
  flash-3.5 most haloed (+0.64) — directional only. Scale-up needed (pro@20 ≈ +0.45 known).
- ⇒ live signal (cheap models extract comparably) → scaling justified; open Q = does a cheap model trade
  de-halo for cost.

**RECALL-ARM PRE-GATE RUN (2026-06-19, built + spent, `recall_flags.py` + `--anchors-from` +
`recall_capture_metric.py`, flash-lite ± suggestive-anchor, 3 games, 12 flagged pivotal turns):** WEAK /
does-not-clear.
| arm | flags hit | capture% | obs on flags | stageJac |
|---|---|---|---|---|
| pro-2.5 | 12 | 100% | 47 | 0.19 |
| flash-lite | 3 | 25% | 4 | 0.32 |
| flash-lite+anchor | 3 | 25% | 4 | 0.18 |
- **The suggestive anchor does NOT rescue flash-lite's recall.** Within-model (the clean read) anchor
  on=off by the metric; reading shows only ~+1 obs on a flagged context (e.g. a "post-healer-death Day 2"
  obs baseline lacked). Marginal, not gap-closing.
- **Manufacture guard CLEAN** (anchored stageJac 0.18 < baseline 0.32 → more distinct, not padding).
- **pro vs lite recall gap is real** (47 vs 4 obs on flags; capture% is verbosity-flattered for pro, but
  the ~10× density gap is robust). Anchoring doesn't move lite toward it.
- ⇒ **don't scale this lever.** Combined with the model arm (flash-3.5 ≈ pro quality/recall), the cheaper
  loop path is **flash-3.5**, not anchored-flash-lite. Metric caveat: parse-based capture is
  verbosity-sensitive → would need a semantic-match hardening before any pro-vs-lite recall scale-up.

**AMPLIFY-ARM RUN (2026-06-19, `--amplify` exhaustive-deep cell pass on flash-lite, 3 games):** NULL.
| arm | tot obs | flags hit | capture% | obs on flags |
|---|---|---|---|---|
| pro-2.5 | 144 | 12 | 100% | 47 |
| flash-lite | 123 | 3 | 25% | 4 |
| flash-lite+anchor | 128 | 3 | 25% | 4 |
| flash-lite+amplify | 116 | 3 | 25% | 3 |
- **Amplify did NOT lift pivotal recall** — total obs even DROPPED (116<123); it added some early-game
  lessons (villager/day_discussion 6→10) but nothing on flagged turns. The "be exhaustive" instruction
  doesn't transfer to flash-lite (its quality-bar conservatism dominates). Neither prompt lever moves it.
- ⭐**THE METRIC IS UNRELIABLE (verbosity-confounded).** Manual read: on the heavily-flagged SK
  night_action cell, flash-lite (base AND amplify) capture the SAME night-kill sequence as pro (3 obs
  each) — yet the metric scored flash-lite 25%. It only counts obs that STATE a parseable alive-count;
  pro's verbose situations do, flash-lite's terse ones don't → false "miss." The 10× gap is largely
  artifact. **Trust the read, not this metric.**
- ⇒ **Revised conclusion:** flash-lite already covers the critical pivotal turns ~comparably to pro
  (mildly thinner in some cells, equal in others); neither anchor nor amplify is needed. The cost-saver
  (flash-lite) is more defensible than the metric implied; flash-3.5 stays the safe near-pro pick. The
  binding lever remains **synthesis (a)+(b)**, not extraction or its model.

## Caveats
- **Epoch-conditional:** results hold for the run epoch only; backend fixed (Vertex — never compare across
  backends); flash-lite drifts ~daily. A capability verdict is "in this epoch."
- **Freeze-gate:** adoption (new model and/or prompt) re-conditions Phase B labels → adopt-then-label,
  versioned. The A/B itself is the deliberate experiment the freeze permits.
- **Recall ≠ full "needed":** capture-rate of *leverage-flagged* turns is the measurable subset; true
  coverage gaps only fully surface in the loop (decisions failing with no covering memory).
