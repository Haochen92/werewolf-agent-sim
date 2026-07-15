# A/B variance-reduction levers — audit (CUPED · pairing · CIs)

**What this is.** A standalone audit of three *statistical* variance-reduction levers that an external
advisor proposed for the budget-constrained win-rate A/B, recorded on 2026-06-06 alongside the caching
cost analysis and **freshness-rechecked 2026-06-25**. The two *caching* levers from that same advice
live in [`../caching/`](../caching/report.md); the three statistical ones are kept here because they
bear on how the A/B is analyzed.

**Scope note (read first).** This is **not** the authoritative A/B statistical design — that is
specified in [`../memory_system/effectiveness/report.md`](../memory_system/effectiveness/report.md),
with the proxy-side analysis plan in [`experiment_log.md`](experiment_log.md) (§ *Statistical analysis
plan*). Those describe the **current, plumbed** paired/seeded A/B. This doc is a separate, dated
*audit* — kept apart deliberately so the 2026-06-06 findings are not conflated with the newer design
(one of them, below, has since been superseded by it).

---

## Lever 1 — pairing / seedability  *(verdict: original finding SUPERSEDED; one residual nuance holds)*

**Original finding (2026-06-06).** True paired design wasn't actually available: the only seed in the
system was `game_id` → scheduler `cycle_seed`, which pins *speaking-order tie-breaks* only; LLM sampling
is unseeded, so paired games diverge at the first sampled token. And `game_id` itself wasn't plumbed —
`run_game` didn't expose it, `run_batch` never passed it, and it wasn't written to the batch JSONL (it
lived only in Langfuse trace metadata).

**Update (verified 2026-06-25): the plumbing gap is closed.** The paired-A/B work since added it —
`scripts/run_batch.py` now loads a pinned seed set via `--game-ids-file` (`load_game_ids`, *"for the
paired A/B"*) and `Agents/main.py` threads `game_id` through the run config and records it. So a paired
A/B over a fixed `game_id` set **is** now supported; the original "not plumbed" verdict no longer holds.

**Residual nuance (still true).** `game_id` pins the **board / config** (and the scheduler tie-break),
not **LLM sampling** (temp 1.0 is unseeded). So paired arms play the *same boards* — which cancels
board/config variance, the point of pairing — but the two arms still diverge in play; seeding does not
make a run bit-for-bit reproducible. *Claim accordingly:* pairing reduces between-board variance, not
sampling noise — don't claim "full reproducibility from seeding."

## Lever 2 — CUPED / regression adjustment  *(verdict: not applicable)*

CUPED needs a **pre-treatment covariate** that predicts the outcome; none exists here. Games are
structurally identical (same 9-player cast, same line-up, same config within an arm) → no scenario
difficulty to adjust for. All between-game variance is temp=1.0 **sampling**, which is exactly what
CUPED cannot touch (not predictable from anything observable pre-game). The covariates we *do* record
(game length, vote counts, role exits) are **post-treatment** — adjusting on them would bias the
memory-on/off comparison, not sharpen it. *Becomes relevant only* if a later phase introduces real
scenario heterogeneity (varied castings, seeded store variants) — then the scenario ID is the covariate
and CUPED is a few lines on the existing JSONL.

## Lever 3 — bootstrap / Bayesian CIs instead of p-values  *(verdict: adopt; partly already planned)*

Worth adopting at analysis time, and **already in the proxy analysis plan**
([`experiment_log.md`](experiment_log.md) § *Statistical analysis plan*: effect sizes + bootstrap CIs
per de-lucked proxy). Recorded here for completeness: the deps (`scipy` / `numpy` / `pandas`) are
present, and `scripts/analyze_batch.py` currently computes **no inferential statistics at all**, so this
is an *add*, not a replacement — no methodological debt to unwind. A percentile bootstrap over any
per-game metric is ~20 lines; a beta-binomial posterior for win rate, less.

---

## Provenance

Audited 2026-06-06 (originally embedded in the now-consolidated `evidence/caching` cost analysis;
git history preserves the original). Freshness-rechecked against the repo 2026-06-25 — Lever 1's
plumbing claim was re-verified and marked superseded. The two caching levers from the same advice
are at [`../caching/report.md`](../caching/report.md) + [`../caching/experiment_log.md`](../caching/experiment_log.md).
