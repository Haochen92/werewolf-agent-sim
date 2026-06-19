# Model drift — component surface map + guards

**Status: reference/design note (2026-06-12), not an experiment record.** Context: epoch drift on
the unpinnable `gemini-3.1-flash-lite` alias has been observed once for sure (67%→27% base villager
win between runs) and is suspected again during the nh town regression (adjudication: the
`ab_canary_0612` gate + pre-registered interim stop, see
`evidence/memory_system/effectiveness/paired_ab/experiment_log.md` — which also holds the
2026-06-11 pinning/detection investigation: alias drift is currently neither pinnable nor visible
in the runtime fingerprint). This note answers two recurring questions: *do we have to redo
baselines every time?* and *does drift also hit the classifiers/dedupers?*

## Structural fix for experiments: INTERLEAVE arms, never compare to historical runs

Drift only confounds when arm A is generated at time T and arm B at time T+Δ. If the runner
alternates games across arms within one run window, drift hits both arms equally — demoted from
*confounder* to *shared noise*; the paired contrast survives even a mid-run shift. This is the
generalization of the freeze-gate rule ("all-on + FRESH baseline, run TOGETHER, never reuse"):

- Any contrast intended to be READ must be generated interleaved/concurrently.
- Historical runs are context, never comparators.
- Ergonomics TODO (cheap): `run_batch.py` accepts multiple configs and alternates per game.
- With this discipline the "redo baseline each time" tax disappears — the baseline is always
  concurrent by construction. The $3 memory-off canary remains the detector for any cross-day
  reading we're forced into (never TRUST a cross-day comparison until the canary clears).

## Component drift map

### Immune: local fine-tuned models

CE dedup prefilter + CE reranker (MiniLM, ONNX, weights on our disk) and any local classifier.
They change only when WE retrain. Portfolio sentence: *the components we fine-tuned are the only
ones the vendor can't move under us* — distillation buys pinned behavior, not just cost.

### Most exposed (and silent): the EMBEDDING model

Unique asymmetry the LLM calls don't have: **store vectors were embedded at time T; every runtime
query embeds NOW.** If the embedding alias drifts, stored and fresh vectors no longer share quite
the same space — retrieval similarity quietly deflates, nothing errors. Worse: the dedup similarity
thresholds (0.93 / 0.81 / 0.96 / 0.935) were tuned against a specific embedding model's SCORE
DISTRIBUTION; embedding drift silently invalidates them while all tests still pass (tests pin the
threshold logic, not the distribution). Guards (cheap, do near-term):

1. **Provenance**: record the embedding model ID in store metadata + runtime fingerprint (verify
   it's there — LLM IDs are; the embedding ID is the one that matters for this failure mode).
2. **Embedding canary test**: ~a dozen fixed text pairs with similarity scores recorded at
   tuning time; assert at batch start that fresh embeddings reproduce them within epsilon. Converts
   silent retrieval decay into a loud failure.
3. **Recovery is mechanical**: re-embed the whole store (~431 entries, pennies) and re-check
   thresholds against the canary pairs.

### Exposed but lower stakes: LLM-in-the-loop components

Dedup KEEP/DISCARD/MERGE calls, novelty gate, situation summary, extraction, judges. Drift shifts
their calibration like any LLM call, but blast radius is bounded by structure we already have:

- **Stores are built once and frozen** — drift during construction changes the snapshot's content,
  but the snapshot doesn't rot afterward; store lineage records which epoch built it.
- **Interleaved experiments cover them**: both arms share the same store and same-epoch
  summaries/judges.
- Residual risk = **cross-time golden-set claims** ("the batch merger is 85% accurate" is a
  statement about an epoch). Guard: keep a ~20-case golden subset; re-score it BEFORE
  drift-sensitive work (e.g. the Phase B dedup re-tune); a drop means recalibrate before trusting.
  Run-before-use, NOT standing machinery — per the "no machinery that changes no decision" rule.

## Posture summary

| Component | Drift risk | Guard |
|---|---|---|
| Local CE/ONNX models | none | — |
| Embedding model | HIGH, silent (store-vs-query asymmetry; thresholds conditioned on score dist) | provenance ID + canary pairs test + re-embed on failure |
| Game/judge/dedup LLM calls | real, bounded | interleaved arms; frozen stores; golden-subset re-score before dedup-sensitive work |
| Cross-day experiment reads | known killer | interleave by default; $3 memory-off canary gate otherwise |

Revisit pinning whenever Google ships dated flash-lite snapshots (tracked in the paired_ab log's
2026-06-11 investigation).

## ⭐ Internal-variation audit (2026-06-12): drift survives elimination — every controllable factor pinned

Challenge: is the Jun-12 epoch shift really endpoint drift, or uncontrolled internal variation?
Checked every factor across baseline/arms/canaries/nh runs:

| Factor | Verdict | Evidence |
|---|---|---|
| Seed → role draw | deterministic ✓ | 78 cross-run game_id repeats, 0 roles mismatches |
| Prompt surface | pinned ✓ (one change, game-neutral) | `prompt_bundle_hash` content-hash; changed ONCE Jun-11→Jun-12-morning, diff = `extraction.py` only (postgame, never model-visible in play; it IS the nh treatment). Behavior shift occurred ~10:25–14:36 WITHIN a constant hash |
| Game runtime code | identical ✓ | `git diff <morning-commit> <canary-commits> -- Agents/` = EMPTY |
| Configs (memory/retrieval/filtering/rerank/persistence/game_config) | identical ✓ | 1 distinct config per run, canaries == baseline |
| Backend / region / temp / models | identical ✓ | vertex / global / 1.0 / same IDs in every fingerprint |
| Leak checks | clean ✓ | 0 flags all runs |
| Uncommitted tracked edits (`git_dirty=True` on several runs) | residual, low-risk | dirty bool only — file list not recorded (gap, see below); current dirty = evidence/*.md; canaries agree with each other from different commits/dirty states |

Conclusion: the Jun-12 shift has **no surviving internal explanation** — endpoint drift by
elimination, not by assumption. Also note the nh arms vs Jun-11 comparators differ ONLY by store
content + the postgame extraction prompt (the treatment itself) → verdicts unconfounded.

**Fingerprint gaps to close (cheap, provenance-only, freeze-safe):**
1. Record the dirty **file list**, not just a bool — kills the last unfalsifiable cell above.
2. Add a game-runtime code hash (`Agents/` minus prompts, or rely on clean-tree discipline for
   eval runs) so future audits are one field-compare, not a git archaeology session.
3. Treat a `prompt_bundle_hash` change mid-experiment as a LOUD event (here it was benign because
   the diff was the treatment; that was luck, not design).

## ⭐ Variance constants (measured 2026-06-12, canary pair: same seeds, same config, same epoch)

Two back-to-back all-off runs on shared seeds decomposed the noise (canary1 N=10, canary2,
8 common seeds):

- **Seed (role-draw) effect ≈ ZERO**: within-seed gameplay-only per-game sd 0.249 vs across-seed
  sd 0.211–0.262 on `town_vote_accuracy`. ALL the variance is in the gameplay (temp>0
  trajectories), none in the draw. Consequences: (a) pairing on game_id adds ~no power (it never
  hurt validity — the Jun-11 p-values embed the true noise; same-epoch was the load-bearing part
  of "paired/seeded"); (b) "multiple runs per seed" has no statistical advantage — for power only
  total N matters, fresh seeds ≥ repeated seeds; repeated seeds are a DIAGNOSTIC tool (noise-floor
  measurement, paired debugging) only.
- **Per-game sd**: ~0.25 (vote accuracy), 0.5 (binary win). Arm-mean SE at N=30: ~0.046 / 0.091.
- **Minimum detectable effect, two-arm N=30, 80% power @ p<0.05**: ~**0.18 vote-acc**,
  ~**36pp win rate** — the quantified form of "win cells were never the instrument." Subtle
  effects (Δ≈0.10 vote-acc) cost ~100 games/arm → measure at component level instead.
- **Faction win cells**: SK/wolf wins are competing risks (anti-correlated within a run; the
  evil-allocation is a near-coin-flip decided by high-leverage trajectory events) → SK win rate =
  noise² (evil-beats-town × SK-beats-wolf). Evil-vs-town is the only halfway-stable win-level
  read. Empirics: same-config run pairs swung SK 0.60→0.30 (Jun-11 baseline sub-runs) and
  0.50→0.00 (canary pair) at N≤20, while all N=30 runs cluster within binomial bands.
- **Run-level random effect: none detected** — across 8 same-epoch run pairs/groups the N=30 runs
  agree within binomial noise; all dramatic swings are N≤20 small-sample artifacts.
