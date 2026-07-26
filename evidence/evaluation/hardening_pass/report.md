# Hardening Pass — what changed and what it means

> **Status: INTERIM (2026-07-02).** The pass's built half is complete; the paid half (two screens,
> one rerun) and the human-labeling half (judge calibration, enum spot-check) are **held by the
> user** and listed under *Open items*. This is the verdict-first skim layer; the full reasoning
> journey, per-fix detail, and provenance live in [`experiment_log.md`](experiment_log.md). Nothing
> from this pass is committed yet — the review surface is that log beside `git diff` at `4b1449e`.

## The one-paragraph verdict

An independent review of the four methodologies behind the memory-design conclusions found the
instruments mostly sound but with three classes of defect: silent failure paths in the tagger and
retrieval-judge layer, replay coverage missing exactly on the deceiver side where the open
questions live, and — the largest finding — the v6 situation dimensions being LLM-filled and never
checked against ground truth. All cheap fixes are built and tested (suite 405 → 445 passed). The
$0 dimension audit then fired its pre-registered **RE-OPEN** condition: the recorded
dimension-gating null was **partly uninformative, not a clean negative** — the gate keyed on an
`is_swing` fill that is worse than a constant (0.606 vs an 0.827 always-False baseline) and a
`bullets_left` fill that is right 16% of the time. Two of those fields are now computed rather
than LLM-filled. The re-screen that would settle whether structured gating actually helps is
authorized by the rule but awaits spend sign-off.

## What a reader should update

| Prior belief (recorded) | Status after this pass |
|---|---|
| "Dimension gating validated negative → default-off" | **Re-opened.** The screen tested a gate keyed partly on noise; tilt was attenuated to ≈0.60 of nominal. Unknown, not false. |
| "Criticality conditioning is within noise" | **Stands** — its query side was already deterministic; only its stored side inherits any doubt. |
| "Content is the bottleneck, not retrieval" (v6_1) | **Stands** — rests on the follow-rate result, not on the gating screen. |
| Town proxy basket trustworthy; wolf null = power + invalid runs | **Stands** — re-verified rather than assumed. |
| Per-turn replay can't see deceiver decisions | **Fixed** — wolf/vigilante/SK day-votes replayable with a faction-correct lens. |
| No detection for embedding drift / tagger silent failures / cross-arm tag-cache hits | **Fixed** — canary crashes loudly; tagger counts and can hard-fail; cache is provenance-checked. |

## What was built (all $0, all tested)

1. **Ten instrument fixes** (log §4): retrieval-judge fallback exclusion, tagger loud-failure +
   strict mode, tag-cache provenance, persisted tagger-validation artifacts, deceiver replay
   coverage + `--lens wolf`, day-stratified sampling, echo-proxy retirement, metric tiering with a
   `dnu_` quarantine, the embedding-canary check (live in `run_batch.py`), sidecar-shape docs.
2. **The dimension audit** (log §5; `evidence/extraction/situation_dimensions/dimension_accuracy_audit/`): 6,267 cases,
   pre-registered rule, RE-OPEN fired. Reusable runner + 8 tests.
3. **Computed fills** (log §6): `players_alive`/`bullets_left`/`ally_revealed` overridden from
   game state at query time; two payload defects found and fixed along the way (night-roster
   off-by-one, vigilante day payload dropping the bullets counter).
4. **The diagnosis sampler** (log §7; `evaluation/src/diagnosis/`): outcome-blind by construction
   (raises on outcome-named signals), deterministic, smoke-tested on real data. Rung ② of the
   modality ladder finally has an apparatus.
5. **The per-day replay design** (log §3;
   `evidence/memory_system/effectiveness/day_replay/design.md`): design-only per scope; feasible
   at ~20–30% of full-game cost with an unchanged-condition acceptance gate.

## Open items (held, in priority order)

1. **Gating re-screen (~$10–15)** — authorized by the RE-OPEN rule; substitutes deterministic
   dims into the frozen cases. The single cheapest step that converts "unknown" back into a
   verdict. *Held pending spend sign-off.*
2. **Enum spot-check (~$2–5 + ~2h human)** — the pending kappa clause of the §5 decision rule
   (`exposure_class`, `info_landscape_class`); runs on the now-built sampler. *Needs user
   labeling time.*
3. **Application-judge calibration (~half day human)** — the one load-bearing uncalibrated judge;
   protocol pre-designed. *Needs user labeling time.*
4. **Wolf replay screen (~$3–5)** — now enabled by the coverage fix; de-risks any future
   wolf-direct A/B (~$60–70, itself unscheduled). *Held.*
5. **Town-only compounding rerun (~$65)** — instrument gates cleared by §4; *held indefinitely by
   user decision.*
6. **Phase 7 verdict propagation** — updating `source_map.md` reliability tags and the
   `store_progression.md` Era-4 row waits on the user's review of this pass (and moves further if
   the held screens run).

## Provenance

Review + all changes at `4b1449e` (`feature-dimension-schema`), 2026-07-02. Test suite
405 → 445 passed, zero regressions, no paid generation calls spent (one embedding-fixture
generation for the canary pins). Implementation by delegated subagents from the approved plan;
per-beat provenance in [`experiment_log.md`](experiment_log.md).
