# Hardening Pass — what changed and what it means

*Added 2026-10-23: of the held items, only the compounding rerun went ahead (redesigned as v7 in July
2026; it closed negative). The gating re-screen, the label spot-check, the judge calibration and the wolf
screen never ran.*

**What this page covers.** This is a dated record: the interim report of 2026-07-02, kept as
history. It covers a review of the four methods behind the memory-design conclusions. The free
half of the work was built and tested, and the test suite went from 405 to 445 passing. The owner
held the rest. That is the paid half (two replay screens and one rerun) and the half that needs
human labelling (a judge calibration and a spot-check of LLM-filled labels). Both are listed under
*Open items*.

The review found the checking tools mostly sound, with three kinds of fault:

1. **Silent failures.** Could the discussion tagger (an LLM that labels discussion lines) or the
   retrieval judge (an LLM that scores fetched memories) fail without anyone noticing? Yes. Both
   now count their failures, and the tagger can be set to stop the run.
2. **Replay gaps.** Could the per-turn replay test the deceivers' decisions? (The replay re-runs one
   saved turn with and without memory.) It could not, and that is exactly where the open questions
   were. Wolf, vigilante and serial-killer day votes can now be replayed, each seen from its own
   faction's side.
3. **Unchecked situation labels: the largest finding.** Were the v6 "dimensions" filled in
   correctly? These are labels describing each game moment, used to choose which memories to
   fetch. An LLM filled them in, and no one had checked them against the game. A $0 audit of 6,267
   cases says no. `is_swing` scored 0.606, which is worse than always answering "no" (0.827).
   `bullets_left` was right 16% of the time.

Because of that audit, a rule written down before it ran (a pre-registered rule) fired **RE-OPEN**.
The old result "dimension gating doesn't help" is partly uninformative, not a clean negative.
(Dimension gating means fetching memories by those labels.) The fields that can be read off the game
state are now computed instead of filled by the LLM. The rule allows a re-screen that would settle
the question, but it is waiting on spend sign-off.

This page records what the pass changed. Each fix is rated for trust in the report that now owns
it, not here. For the full reasoning, the detail of each fix and the provenance, see
[the journey log](experiment_log.md). When this was written, nothing from the pass had been
committed, and the review was done against `git diff` at commit `4b1449e`. How all the evaluation
reports fit together: [the hub](../report.md).

| What was built (all $0, all tested) | State on 2026-07-02 | Main limit |
|---|---|---|
| Ten fixes to checking tools (item 1; log §4) | Built | The embedding check is live in `run_batch.py` |
| Situation-label audit (item 2; log §5) | Done, RE-OPEN fired | Its labels part waits on a human spot-check |
| Computed labels (item 3; log §6) | Built | Also fixed two bugs in what players are told |
| Sampler that picks moments for a human to read (item 4; log §7) | Smoke-tested | Blind to who won by design; not yet used |
| Per-day replay (item 5; log §3) | Design only | Estimated at ~20–30% of a full game's cost |

**Bottom line.** The cheap fixes are in, and most of the earlier beliefs stand (see the next
table). The one big change is that "dimension gating doesn't help" is now unknown, not false, until
a ~$10–15 re-screen runs.

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
   `memory_system/report.md` Era-4 row waits on the user's review of this pass (and moves further if
   the held screens run).

## Provenance

Review + all changes at `4b1449e` (`feature-dimension-schema`), 2026-07-02. Test suite
405 → 445 passed, zero regressions, no paid generation calls spent (one embedding-fixture
generation for the canary pins). Implementation by delegated subagents from the approved plan;
per-beat provenance in [`experiment_log.md`](experiment_log.md).
