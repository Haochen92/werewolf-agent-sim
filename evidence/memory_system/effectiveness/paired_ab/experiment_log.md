# Paired memory A/B — run playbook

**Status: NOT RUN YET.** Harness + seed set are ready; this folder is the design +
playbook + (later) results. Arm plan is discussion-only per the user.

## Design

Per-role memory ablation on the frozen **v5_0** store (consumption mode), paired on a
shared seed set so each arm replays identical role draws → McNemar.

- **Arms (memory-on for the named role(s) only):**
  - `wolf_only` — resolves whether the pilot's wolf lift is empowerment vs town degradation
  - `serial_killer_only`
  - `town_only` — villager + healer + investigator + vigilante (full town faction; where the
    validated proxies live: vote accuracy, mislynches, |r|≈0.6)
- **Baseline:** `all_disabled` (memory off).
- **Treatment (all arms):** `--retrieval-types observations_only --reranking rerank_disabled
  --filtering filter_disabled`, `top_k=5` (observations-only saturation point,
  evidence/retrieval/capacity_limits). `--no-memory-dump` so the store can't grow → constant treatment.

## Seed set (`seed_set.json`, frozen by `scripts/make_ab_seed_set.py`)

30 game_ids = **20 recovered** baseline game_ids (from `extraction_v5_0.jsonl`, with recorded
baseline winner: 12 villagers / 7 serial_killer / 1 wolves) + **10 fresh** uuid4s. Verified
2026-06-11: a game_id reproduces its exact role draw (`crc32(game_id)` → choice → shuffle, 20/20),
and all play-path code is unchanged since the baseline commit b9756960 (only behavior-neutral
eval plumbing changed) → pairing arm games against the recorded baseline outcomes is clean.

- `arms_game_ids.json` — all 30, for the arms.
- `baseline_fresh_ids.json` — the 10 fresh, for the baseline top-up (the 20 recovered already
  have recorded outcomes in `seed_set.json`).

## Run commands

1. **10 fresh baseline games** (memory off, cheap ~$0.20/game):
   ```
   poetry run python scripts/run_batch.py --configs all_disabled \
     --game-ids-file evidence/memory_system/effectiveness/paired_ab/baseline_fresh_ids.json \
     --no-memory-dump --session-prefix ab_baseline --output batch_results/ab_baseline.jsonl
   ```
2. **3 arms × 30 games** (read-only on frozen v5_0 → parallel-safe):
   ```
   poetry run python scripts/run_batch.py \
     --configs wolf_only serial_killer_only town_only \
     --retrieval-types observations_only --reranking rerank_disabled --filtering filter_disabled \
     --game-ids-file evidence/memory_system/effectiveness/paired_ab/arms_game_ids.json \
     --no-memory-dump --memory-store-dir memory_stores/v5_0 \
     --session-prefix ab_arms --output batch_results/ab_arms.jsonl
   ```

## Analysis

Per arm, pair each of the 30 arm games to its baseline by `game_id`: the 20 recovered ids
pair against `seed_set.json` recorded winners; the 10 fresh ids pair against the `ab_baseline`
run. McNemar on the arm's faction win (wolf-faction for wolf_only, SK for serial_killer_only,
town for town_only) + the validated de-lucked proxies. Reuse `evaluation/src/core/stats.py`.

## Code pointers

- Seed pinning: `scripts/run_batch.py --game-ids-file` → `run_game(game_id=…)` →
  `build_game_config` → `initialize_game` (role draw `crc32(game_id)`).
- Seed-set generator: `scripts/make_ab_seed_set.py`.
- Treatment presets: `MEMORY_CONFIGS` / `RETRIEVAL_TYPES_CONFIGS` in `run_batch.py`; `top_k`
  in `Agents/memory/enrichment/pipeline.py`.
