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
