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

## Foundation prompt cleanup before the baseline (why the v5.0 baseline is trustworthy)

Two pre-baseline fixes, both *faction-correctness* (4-role-era leftovers in a 3-faction
game), not strategy tuning — recorded here because they affect the validity of the SK-floor
/ memory-lift measurements:

1. **Role framing** (commit b9594e3): villager + investigator play prompts only mentioned
   "the wolves"; now name "the wolves and the serial killer" (town wins only when both are
   gone; the investigator's reveal surfaces the SK). Empirically the *players* already
   tracked the SK via the GM's announced kills, so this is defensibility, not a fix to
   broken play.
2. **⭐Day-vote de-bias** (commit 017940e) — a real **measurement confound**: the shared
   `DAY_VOTE_SYSTEM_SUFFIX` told *every* town role to "vote to eliminate a player you
   suspect is **a wolf**", and the SK *inherited the same suffix*. So town day-votes were
   systematically steered toward wolves and away from the SK (also a lynch-only threat) →
   the SK ate fewer votes, survived longer, and its apparent floor was **inflated by a
   prompt artifact, not structure**. Fixed: town targets "a wolf or the serial killer"; SK
   gets its own solo-objective vote system (no inherited wolf-hunt); wolf treats the SK as a
   removable competitor. **Measuring the SK floor under the old bias would have over-credited
   SK strength** — so this had to precede the baseline. (Pre-fix seeding attempts discarded.)

*Smoke checkpoint (not a measurement):* one post-overhaul game ran clean end-to-end —
villagers won d5, leak-check passed, play coherent, and the SK was reasoned about across all
roles (investigator, villager, healer included), confirming the de-bias renders correctly
in-engine. This is a single uncontrolled game, so no engagement figure is cited as evidence;
the de-bias effect is quantified for free by the 30-game off-memory seeding batch below
(SK-vote / engagement distribution at N=30).

## Generational seeding (v5_1+) — design + serialization

A *second-order, exploratory* track distinct from the Phase C A/B: **does memory compound
across generations?** Build a store from **memory-ON** play and ask whether it beats the
memory-off-built `v5_0`. Keep these separate in your head:

- **Phase C "does memory work" A/B does NOT use v5_1.** Both arms share the *same* seed
  (`v5_0`): memory-on reads it, memory-off reads nothing. `v5_0` is built memory-OFF *on
  purpose* so the seed/baseline is unbiased — a memory-on-built store would confound it.
- **v5_1 = a store built by memory-ON games** that read `v5_0` and dump forward. Different
  question (compounding / self-improvement), different artifact. Don't let it replace `v5_0`
  as the A/B seed.

**Store layout decision — separate dirs per generation, NOT in-place growth.** Run each
generation as:

```
--seed-store-dir v5_0  --dump-store-dir v5_1     # memory-ON games; v5_1 = v5_0 ∪ new
--seed-store-dir v5_1  --dump-store-dir v5_2     # next generation, etc.
```

The dump already carries the whole store forward — `dump_memory_to_json_files`
(`persistence/dump.py`) serializes the *entire in-memory store*, and at dump time that store
is `loaded seed ∪ new extractions` (`persistence/seed.py` loads the seed dir into the same
global store extraction writes to). So **`v5_1` is complete and self-contained**, and `v5_0`
is never mutated. Copy-pasting `v5_0`→`v5_1` first is redundant; in-place growth is rejected
— it destroys the immutable baseline + the lineage, and there is **no store-rebuild-from-record
harness** (rebuilding = re-running the expensive games), so immutable per-generation snapshots
are the only cheap way back to any prior state.

**Finalization before freezing (per generation).** Seeding batches dedup *incrementally*
(non-convergent — `evidence/dedup/incremental_convergence.md`), so before a generation is
frozen it gets **one whole-store dedup pass** (`scripts/dedup_memory_store.py --apply
--two-pass`, tuned-default thresholds) to converge it. That pass is **destructive and
in-place**, and there is no rebuild-from-record harness, so **snapshot the raw store first**:
`cp -r memory_stores/v5_0 memory_stores/v5_0_raw` (captures JSON + `indexed_cache.pkl`), then
dedup `v5_0` in place. Same for every later generation (`v5_1`→`v5_1_raw`, …). The `*_raw`
copy is the untouched pre-dedup fallback — re-runnable with different thresholds if the pass
over-merges.

**Serialization (why re-seeding isn't re-paid).** Two layers already exist: the JSON snapshot
is the serialized store *content*; `indexed_cache.pkl` is the serialized embedding *vectors*.
On load, if the JSON is unchanged, vectors load from the pickle → **zero embedding API calls**
(`seed_memory_from_json_files_cached`). So the rule is: **the moment a generation stops
seeding, freeze it and switch downstream runs to consumption mode** — `--seed-store-dir
<frozen vN> --no-memory-dump`: no extraction (the ~62%-of-cost part), no re-embedding, only
play cost. The expensive build is paid once per generation, then frozen.

## Future work — end-state replay extraction (decouple play from store-build)

Today each seeding game does double duty (play = baseline + extraction = store), so building
the store re-pays the full play cost every time. A **replay-to-store** pipeline would decouple
them: persist each game's frozen end-state, then `format_extraction_inputs(state)` → per-role
extraction → dedup → dump — i.e. the orchestrator's `postgame_extraction` path fed from a saved
state instead of a live runtime. Payoffs: (1) cheap extraction iteration (no replay of *play*);
(2) **closes the store-rebuild-from-record gap** (currently "re-run games to rebuild" — there is
no real rebuild harness; `evaluation/src/experiments/extraction_replay.py` is the old
single-prompt eval method with no store dump); (3) cleanly separates baseline-generation from
store-building per the eval-layer architecture. **Prerequisite = data persistence:** the batch
record must capture the *complete* extraction inputs — today it stores `day_channel` /
`day_summaries` / `*_resolutions` / `investigator_results` / `roles` but **NOT `wolf_channel` or
the strategy notes** (extraction needs the wolves' night reasoning). The replay runner itself is
thin (reuse the orchestrator path). **Prompt-freeze-safe** — it changes where extraction inputs
come from, not the extraction prompt (same category as `extract_without_dump`). Deferred, not
blocking the v5 seeding/baseline.

**Refinement — per-(role,phase) augmentation to deepen v5_0's thin buckets (no new games).** A
specialization aimed at v5_0's structural floor (e.g. `strategy_points/investigator/day_vote` ≈ 6):
a `namespace_augmentation_agent` (new module under `Agents/memory/extraction/`, `*_agent.py`
convention) with a prompt parameterized by the **`(role, action_phase)` pair** — NOT memory_type,
since observations + strategy points are related and co-extracted in one call (fills both
`observations/(role,phase)` and `strategy_points/(role,phase)`). Re-extract **v5_0's own 20
memory-off games** (frozen inputs), targeting one pair, "dig deep," narrow output → dump
genuinely-new items back into v5_0. ⭐**Methodological win:** v5_0 becomes deep AND unbiased
(still memory-off-built) → fixes the clean A/B seed directly, so v5_1 is no longer needed as a depth
hedge (reverts to the separate "does memory compound?" study). **~70% reuse:**
`extraction_replay.py` already replays `build_extraction_prompt` over a frozen dataset; reuse its
loop + `ExtractionCase`/`ExtractionDatasetRecord`. **3 gaps:** (1) the (role,phase) prompt + narrow
schema; (2) wire it to DUMP into the store (replay only writes a judging dataset); (3) a **v5_0
frozen dataset** built from the v5_0 games' Langfuse `ExtractionCase` spans (`extraction_v1.jsonl`
is STALE — old 8p/4-role, no SK/vigilante/wolf_channel; the builder exists, re-point it; Langfuse
has the full inputs the batch JSONL drops). ⚠️2026-06-11 readiness check: gate PASSES (single-trace
pull returns full 38k-char inputs; `extraction_builder` with `session_prefix: "v5_seed_b"` finds all
20 v5_0 traces) BUT the bulk pull hits a Langfuse **422** — `fetch_extraction_cases` →
`_fetch_all_observations` over-fetches ALL of a heavy game's spans (per-trace result too large;
short games work, long games 422 → `get_many` is a paginated table-query whose cost scales with
offset+table, NOT a whole-table scan; date-bounding does NOT help). **Fix (verified):** switch
`_fetch_all_observations` (`evaluation/src/data/langfuse.py`) from paginated `observations.get_many`
to a single `api.trace.get(trace_id).observations` point-lookup — returns the whole trace in one call
(1333 obs/235 span-types on a trace that 422'd), no pagination, and PRESERVES fetch-any-span (beats
name-scoping). Durable companion: emit eval cases locally at game-time (the original "emit→select"
intent; currently Langfuse-only). Local-hosted Langfuse = no rate limits. Target output:
`evaluation/frozen_eval_sets/extraction/extraction_v5_0.jsonl`. **⭐GATE BEFORE BUILDING:** thin buckets are low-VOLUME
not low-variety (the investigator/day_vote points are diverse) → augmentation helps ONLY IF the
general extraction under-extracted that namespace. Validate cheaply first: focused re-extraction on
2-3 v5_0 games, check for DISTINCT post-dedup new items vs the existing set. Duplicates → general
pass already covers it → skip (genuinely volume-bound). Win (if real) = across-games accumulation,
dedup-gated — NOT per-game squeezing (~3 vote-events/game → padding the prompt would invent).
Prompt-freeze: a new extraction prompt that adds to v5_0 = part of the frozen v5 definition →
validate + freeze before labelling.

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
