# The knob ledger — every curation threshold, its provenance, and why they are pinned

> **Scope:** the complete inventory of the configuration knobs ("hyperparameters") that shape the
> three stores' curation and consumption, under the framework in [`report.md`](report.md). Each
> knob carries a **provenance** class and a **validation** status, because the honest answer to
> "were these optimized?" is *no — and deliberately so* (§1). This is the doc the pre-registration
> config pin points at; report §6.2 holds the walkthrough-agenda version of the provenance question.
> **Status:** compiled 2026-07-15 from the working tree (values verified at their file of record;
> `evaluation/src/loop/config.py` carries per-knob rationale comments — this doc classifies, the
> comments argue). Suite 690 green.

**Provenance classes** (used in every table):

- **measured** — a run or experiment picked the value (the value traces to a number in a record).
- **checked** — a zero/cheap-spend test validated the *direction* of the rule at this value
  (not a sweep; neighboring values untested).
- **sim-informed** — the 30-game ledger simulation replayed real mined rows through exactly this
  value and the dynamics held (tell-extraction log §10).
- **ruled** — an owner design ruling with its reason on record (log entry cited).
- **default** — chosen by design reasoning, never swept. Pinned in the pre-reg as such.

## 1. Why the knobs are pinned, not optimized

No knob-optimization run has happened, and none is planned before the v7 run. That is a policy,
not an oversight, resting on three arguments:

1. **The power math forbids it.** The MDE analysis (execution plan §0.1) shows the *main* effect
   is barely detectable at every affordable run size. A knob sweep multiplies arms, and detecting
   the difference between neighboring knob values (cap 12 vs 16) is strictly harder than detecting
   the main effect — so a live optimization run would spend the entire budget to learn nothing
   distinguishable from noise.
2. **Tuned values would not transfer.** Cross-epoch comparisons are banned in this project for
   measured reasons (model drift, backend sensitivity); a knob tuned on this epoch's data carries
   no guarantee into the next prompt epoch, so optimization now buys precision that expires.
3. **Most knobs are guards, not optimizers.** Caps, floors, and windows exist to bound a named
   failure mode (report §5's pathology table), not to maximize a metric. The right validation
   standard for a guard is "anchored to the pathology it prevents and observable when it bites" —
   and the loop prints its guard activity per generation (`cells_capped`, decay drops, exploration
   slot fires, probation rotation), which is what makes the **post-run sensitivity readout** cheap:
   the run itself records which knobs were binding.

So the policy is: **pin every value in the pre-registration with its provenance class, run, then
read sensitivity from the run's own counters.** The two genuinely cheap pre-run checks that
existed have been done (§5); the one remaining candidate is listed there and deliberately parked.

## 2. Cadence knobs (the loop's clock)

| Knob | Default | Controls | Provenance |
|---|---|---|---|
| `games_per_generation` | 5 | batch size = one curation tick's worth of games | default — "small N = more frequent boundaries, finer learning" (config comment); the run shape doubles it to 10 |
| `generations` | 10 | number of curation ticks in a run | default — 10 slope points |
| `synth_every_k_gens` | 2 | SP synthesis (the paid LLM step) runs every k gens; culls run every gen | default — the fast-cull / slow-synth split (`strategy_points.md` §1) |
| tell fold cadence | every generation | one fold per generation = the ledger design's N=10 games at run shape | sim-informed — the sim ran the N=10 cadence; online per-game curation was measured worse (2× head fragmentation) and retired |
| strong-model audit | every ~3 epochs | merge/split repair pass over the tell canon | sim-informed — consolidation №1 found batch cadence ~every 25–30 games |
| `window_generations` | 6 | rolling credit window the lifts are computed over | measured-adjacent — arithmetic from credit density: W=6 pools ~30 games/tick so SPs can clear the follow≥8 prune floor (config comment) |

## 3. SP-store knobs

| Knob | Default | Controls | Provenance |
|---|---|---|---|
| `synth_min_new_obs` | 4 | new-evidence gate: cell re-synthesizes only at ≥4 new obs | default |
| `synth_replenish_floor` | 3 | depleted-cell exemption (below 3 SPs, gates waive) | default |
| `synth_cell_unproven_cap` | 12 | contested-lane ceiling on synthesis | **measured** — the §12 bloat record: healthy cells ~5, runaway ~34; 12 ≈ 2.4× healthy, well under runaway (report §5 row 1) |
| `synth_track_min_follow` | 5 | follows before realized lift enters the synthesis prompt | default — "the noise floor" |
| `prune_tau` | −0.15 | lift threshold for pruning | **checked** — held-out reproduction 2026-07-14: flagged losers stay negative 8/9 on the unseen half, Pearson +0.54 at n=31 (`strategy_points.md` §6); direction, not calibration |
| `prune_min_follow` | 8 | follows before a negative-lift SP is prunable | checked jointly with τ (the one held-out flip sat below this floor — the floor did its job) |
| `evict_min_retrieved` | 8 | retrievals before an unfollowed SP is evictable | default |
| `evict_require_override` | True | mercy rule: only override-dominant rejection evicts | ruled — the wrong-blame pathology (report §5 row 6) |
| `protect_min_follow` | 2 | proven exemption floor | default — "kept low on purpose: positive signal, however sparse, beats deletion" |
| SP dedup on flash-lite | — | KEEP/DISCARD only, freeze-old | ruled — no merge text to get wrong (`strategy_points.md` §3) |
| synth clustering: similarity 0.70, bounded, max cluster 15 | — | how obs group into synthesis inputs | default — see §5 on the absolute-threshold caveat |

## 4. Observation-store and consumption-layer knobs

| Knob | Default | Controls | Provenance |
|---|---|---|---|
| `obs_evict_min_age` | 4 | decay allowance per reinforcement count (`observations.md` §3) | **measured** — a window of 2 dropped ~250 obs/gen and starved synthesis (config comment) |
| `obs_dedup_merge` | False | online obs fold is triage-only (no merge text) | ruled — flash-lite triage reliable, merge-writing is where nuance dies (`observations.md` §4) |
| `dedup_gate` similarity | 0.92 | near-duplicate cosine gate on retrieved obs | default |
| `retrieval_types` | strategy_points_only | what the ON arm injects (obs retired) | ruled — 2026-07-15, report §6.8 |
| `RETRIEVAL_KEEP_PER_SITUATION` | 3 | per-situation injection cap (obs and SPs) | **measured** — capacity_limits: cap 7 regressed action quality below cap 3 (`evidence/retrieval/capacity_limits`) |
| narrow-path top_k | 5 | fetch cap without rerank | measured — same capacity record (the obs saturation point) |
| `RERANK_TOP_K` / `RERANK_KEEP` | 10 / 3 | wide-path fetch and keep (rerank arms only; rerank default-off) | default |
| `SP_PROVEN_MIN_FOLLOW` | 5 | game-side proven predicate floor | default — deliberately matches `synth_track_min_follow` (shared noise floor; comment at both sites) |
| `sp_proven_tiering` / `sp_exploration_slot` | on / on | proven-first ordering + contested-lane slot | ruled — §6.7, log §5 |
| MMR `lambda_` / top_k | 0.8 / 5 | diversity filter (filtering arms only; default-off) | default |

## 5. Tell-store knobs

| Knob | Default | Controls | Provenance |
|---|---|---|---|
| `K_PROBATION` | 12 | scanned games before a still-singleton probation tell archives | **sim-informed** — funnel healthy: probation absorbed ~12%, recurrence re-entry fired (tell-extraction log §10) |
| `INCUMBENT_CAP` / `PROBATION_CAP` / `CHECKLIST_CAP` | 25 / 15 / 48 | published checklist composition per channel | sim-informed — the ledger-spec values the sim replayed; the 48 bound is THE tell-side cost control (`tells.md` §5) |
| `NULL_LIFT_EPS` / `NULL_SUPPORT` | 0.03 / 20 | measured-and-uninformative archive verdict | default |
| `PREFILTER_THRESHOLD` / `PREFILTER_TOP` | 0.80 / 3 | embedding nomination before the LLM same-tell judge | default — **the one tracked calibration gap** (report §6.2): the sim's resolved rows could calibrate it, but a replay harness is a new instrument and the closing rule is no new complications pre-run |
| `INDEX_PROBATION_RECENT` / `INDEX_ARCHIVE_RECENT` | 30 / 10 | bounded match-index windows | ruled — hard cap over unseen-based retirement, "easy to build, easy to explain" (log §7); windows unswept |
| `HEAD_N` | 10 | how many top incumbents the publication tripwire guards | default |
| `SHRINK_K` | 5 | empirical-Bayes pseudo-exhibitors toward the cast prior | default, informed by the held-out lift table's behavior |
| credit `support_floor` | 8 | support before a positive-lift tell charges credit | ruled — §6.5 (what pays); same floor reused for the book (what informs) |
| book `per_role_cap` | 3 | tells per (subject role, channel) in the injected book | ruled — role-grain book, 2026-07-14 (log entry 3); the v2 tail being near-prior is the open §6.6 floor question |
| detector config | k=2 union, cached, thinking=low, temp 0 | the detection instrument | **checked** — golden accuracy-parity 2026-07-13 (disc 0.93/87%, vote 0.77/77%, N=40, direction-grade; k=2→k=1 is an open cost decision) |

**The absolute-threshold caveat (applies to 0.70 / 0.80 / 0.92 above).** The tell campaign found
the production embedding scale is compressed (pairwise cosines cluster high — p50 ≈ 0.84 in that
store), which made *absolute* thresholds meaningless there and forced rank-based selection
(tell-extraction log §3.6). The obs/SP side still uses absolute cosine knobs (batch/synth
clustering 0.70, obs dedup gate 0.92) chosen before that finding. A $0 distribution check —
percentile-locate each threshold in its own store's similarity distribution — exists and has not
been run; it is the strongest remaining cheap-test candidate, parked pre-run under the
no-new-complications rule and queued for the post-run sensitivity readout.

## 6. What has been tested, what is parked, what the run itself will answer

- **Cheap tests already done:** the prune threshold held-out reproduction (τ at −0.15/≥8 —
  direction-credible); the 30-game ledger simulation (all the tell funnel values at once); the
  detector golden-parity check (the k=2 cached config); the retrieval capacity experiment (the
  injection cap of 3); the bloat-record anchoring of the synthesis cap and decay window. These
  cover the knobs most able to flip a run conclusion — that ranking was itself a review exercise
  (report §6.2 names `prune_tau` as the only such knob, and it is the one that got the test).
- **Parked, with the data to close them named:** prefilter calibration (sim rows exist);
  match-index windows 30/10; the absolute-threshold percentile check (§5). All pinned as
  design-anchored in the pre-reg.
- **Answered by the run for free:** which caps bind (`cells_capped`), decay pressure
  (`obs_dropped`), exploration-slot fire rate, probation rotation/starvation beyond 30 games
  (report §6.5), and the book floor question (§6.6) — the post-run sensitivity readout reads
  these counters before any paid re-tuning is considered.

## Sources

Values verified in: `evaluation/src/loop/config.py` (knob comments = the rationale of record) ·
`tell_fold.py` · `tell_credit.py` · `tells.py` · `Agents/memory/retrieval/{accessors,filters,rerank_agent,pipeline}.py` ·
`Agents/memory/batch_deduplication/config.py` · `Agents/tracing.py` · `Agents/memory/tell_book.py`.
Tests cited: [`strategy_points.md`](strategy_points.md) §6 (held-out) · tell-extraction log §10/§13
([`../extraction/tell_extraction/experiment_log.md`](../extraction/tell_extraction/experiment_log.md)) ·
`evidence/retrieval/capacity_limits` · the MDE table
([`../execution_plan/power_analysis/mde_table.md`](../execution_plan/power_analysis/mde_table.md)).
