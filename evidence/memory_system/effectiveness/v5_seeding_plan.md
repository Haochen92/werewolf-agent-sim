# v5 Store Seeding + A/B Validation — Plan (2026-06-10)

Forward plan for building the v5 memory store and running the "does memory work" A/B
on the rebuilt foundation (sequential discussion, 9-player / 3-faction casting, per-role
extraction). Extends `report.md` (the prior 8-player concurrent-system result); the
statistical design there is the authority and is referenced, not re-derived.

## Why now / what changed since the prior report

`report.md` proved memory *can* work (70%→97% at n=30 on the old system) but flagged the
result as configuration-sensitive and pre-current-config. Everything underneath has since
been rebuilt: sequential scheduler, 9p/3-faction roles, prompt-boundary cleanup, and —
most relevant here — **per-role extraction with Vertex prefix caching** (see
`evidence/extraction/` and the memory store work). So the old win-rates and per-role
baselines no longer transfer. This plan rebuilds the store and re-establishes the
baselines on v5 before any A/B claim.

## Seeding run

**~30 memory-off games** (`--configs all_disabled`, dump ON, a fresh `--memory-store-dir`
for `v5.0`). It does double duty:

1. **Builds the store.** v5 per-role extraction yields ~24 observations + ~25 strategy
   points per game → ~720 + ~750 raw → ~300–450 after a single **whole-store** dedup pass
   (not incremental — the incremental path is non-convergent; see
   `evidence/dedup/incremental_convergence.md`). Comparable to the v4 store (522 items)
   that drove the prior effectiveness result.
2. **Is the baseline / variance pilot.** Memory-off play on v5 gives the first real
   per-faction win-rates and per-role de-lucked proxy variances (`compute_metrics.py`).

Seeding games are **deliberately unseeded** — varied role draws give store diversity and
an unbiased baseline distribution across role configurations.

**Temperature = 1** for play (and extraction, which currently shares the same env var),
pinned identical across every run. temp=0 is rejected: it does not buy reproducibility on
Vertex (outputs still vary), it degenerates social play and collapses store diversity, and
it would break lineage with every prior baseline/frozen set. The resulting variance is
handled by the paired design + dense proxies, not by lowering temperature. Extraction temp
is **frozen at 1** for v5 (it conditions the store content about to be labelled).

## Sequencing decision (why we don't pre-commit the A/B shape)

The v5 per-role baselines **do not exist yet** — the only sequential SK data is ~3 games
from the role-set build (N=3, explicitly not a baseline). An earlier "SK 60–80% floor"
assumption was an unestablished import from the old system and is retracted. Consequently:

- **The A/B demonstration role is not picked a priori.** It's whichever role the seeding
  baseline shows has room (not pinned near 0/100%) and a dense, workable-variance proxy.
  Wolf-only memory → blending-rate (+36pp, config-insensitive on the old system) is the
  cheap-demonstrator *hypothesis*, to be re-confirmed on v5 — not a given.
- **The A/B game count is not fixed now.** Required N depends on baseline rate + effect
  size + proxy variance, none known on v5. Size the A/B *from the seeding numbers*
  (optionally a small memory-on pilot for the effect estimate), per `report.md`'s design.
- Win-rate alone is ~1 bit/game (hundreds of games for a moderate lift); statistical power
  comes from the **dense de-lucked proxies** (see `evidence/metrics/`).

## Seedability audit + fix (prerequisite for the *paired* A/B only)

The paired/seeded design in `report.md` requires the sim to be seedable end-to-end. Audit
(2026-06-10) of every stochastic source:

| source | site | seed-controlled? |
|---|---|---|
| Role draw (who is wolf/SK/…) | `orchestrator.initialize_game` `random.shuffle(roles)` | ❌ was unseeded global RNG — **the gap** |
| Scheduler turn-order tie-break | `turn/scheduler.py` via `cycle_seed(game_id,…)` (crc32) | ✅ already deterministic given `game_id` |
| Persona assignment | — | ✅ N/A — no personas in v5 |
| `human_player` | `initialize_game` `random.choice` | ❌ unseeded but vestigial (eval has no human) |
| night wolf-kill / agent-target fallbacks | `nodes/night/wolf.py`, `turn/agent.py` | ⚪ global RNG but **post-divergence + rare** → not required for pairing |

**Fix:** make the role draw derive from `game_id` (crc32 → `random.Random`), reusing the
scheduler's existing pattern, and expose `game_id` through `run_game`. This makes `game_id`
the **single master seed** — unique uuid4 per game by default (so seeding stays varied),
pinnable across a pair (identical role draw + scheduler tie-break pre-divergence). The
fallbacks are left global (post-divergence, fine to diverge; optional hardening later).

This is **not a blocker for the 30 seeding games** (they don't need seeding). It gates only
the later paired A/B. The paired-run *harness* (two `run_game` calls sharing
`game_id`, differing only in `memory_config`; McNemar / paired-Wilcoxon analysis) is built
when the A/B is run.

## Extract-without-dump (cost-measurement plumbing)

`ExtractionConfig.extract_without_dump` decouples *running* extraction (to exercise/measure
the per-role fan-out + cache) from *persisting* it to the store: the orchestrator runs
extraction and traces the ExtractionCase, then skips dedup/dump/batch-dedup when dump is
off. Prompt-freeze-safe (pure dump-gate plumbing). Used for the post-change end-to-end
verification game before committing to the 30-game batch.

## Cost (measured, verification game) + the decouple refinement

One end-to-end memory-off game (day 5): **play $0.1995** (flash-lite 3.1, Langfuse-priced,
207 calls) **+ extraction $0.333** (2.5-pro, 6 roles, 98.9% input cached) = **≈$0.53**. Cache
cut extraction *input* ~73% but extraction is **output-bound** (31k out × $10/1M = ~78% of
extraction), so net cache saving is **~16% of extraction (~$0.066/game)** — caching neutralizes
the per-role *input* multiplication; output is the price of the quality upgrade. Extraction is
**62% of the game cost**. (Caveat: re-measured from the saved record, which omits
`wolf_channel`/strategy notes → input slightly under-counted; output faithful.)

**Refinement — decouple store-build from baseline.** Extraction doesn't affect *play*, so an
extraction-off memory-off game is a valid baseline point. So: run **N_store extraction-ON 2.5-pro
games** (`all_disabled`, dump ON) to build `v5.0` (store quality matters → keep 2.5-pro, not
flash-lite — a weak store risks a false-negative "memory doesn't work"), then **pad the baseline
with extraction-OFF games** (`all_disabled --no-memory-dump`, ~$0.20 each). Baseline = all
memory-off games. A/B + ablation run extraction-OFF (they read the store). No new code — existing
run_batch invocations.

**N_store — don't fix a priori; watch saturation.** Fixed casting + memory-off games being more
self-similar → store saturates fast and dedup absorbs recurrence. Run extraction-on games in
batches of ~5, count deduped store items after each, **stop at the knee (<~10% growth / 5 games)**
— estimate ~15–20 (≈200–300 deduped items, in range of the old 300–522 stores). ~15 store + pad
to ~30 memory-off ≈ **$11**, a bigger baseline for less than the flat-30.

## Instrumentation fixes made this session
- **Extraction tracing restored**: the concurrent fan-out ran in ThreadPool workers where
  contextvars (langchain callback + Langfuse span) don't propagate → per-role generations were
  untraced (cost hidden). Fixed via `copy_context().run` per worker (output-neutral).
- **Dedup stats in the record**: per-game `DedupStats` (was log-only) now rides
  `Metrics.dedup_stats` → `raw_metrics` → the batch record `dedup_stats` field → per-game
  absorption / saturation is queryable without Langfuse.

## Order of operations

1. Seedability fix (engine-level) + extract-without-dump flag. ✅ small, prompt-neutral.
2. **One end-to-end verification game** via `run_batch` (memory-off, dump-off,
   extract+cache ON) — confirms the game runs after all the extraction/refactor changes and
   yields a per-game cost + cache-saving estimate.
3. **30-game seeding batch** → `v5.0` store + memory-off baseline.
4. (Phase B) labelling on v5 — reranker NDCG cases (~40) + panel-validation human judgments
   (~96); see `retrieval/context_eval/`.
5. (Phase C) paired A/B sized from the seeding baseline; headline win-rate, power on dense
   proxies.
