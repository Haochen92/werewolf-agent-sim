# Paired memory A/B — run playbook

**Status: RUNNING (2026-06-11).** Baseline + 3 arms launched, parallel, 0 errors/429s.

## ⭐ Epoch-shift finding — baseline re-run fresh (2026-06-11)

The 10 fresh baseline games came back **villagers 10% / SK 60% / wolves 30%**, vs the
original 30 baseline's **67% / 27% / 7%** (Fisher **p=0.0028**) — a systematic shift
(town down, SK up), despite byte-identical play prompts and no game-rule/scheduler code
change since the baseline commit `b9756960`. Most likely cause: `gemini-3.1-flash-lite`
model drift (Vertex-side) or small-N variance. Either way the original-epoch baselines
can't serve as the off-control. **Fix:** re-run the 20 recovered `game_id`s as fresh
baseline in the current epoch (`ab_baseline_recovered.jsonl`, `recovered_ids.json`) so all
30 baselines are same-epoch AND carry full `computed_metrics` → clean paired win **and**
proxies at N=30. The original baseline + `seed_set.json` recovered winners are no longer
used for the comparison.

### Can we pin or detect the drift? (investigation 2026-06-11)

Probed whether `gemini-3.1-flash-lite` alias drift is preventable/detectable:

- **Not pinnable.** Vertex `models.list()` shows only `gemini-3.1-flash-lite` (alias) and
  `gemini-3.1-flash-lite-preview` (a preview — *less* stable) for this generation. No dated
  snapshot (no `-001`) exists to pin to, unlike older gens (`gemini-2.0-flash-lite-001`
  does exist). So Google can repoint the alias silently and we can't freeze it.
- **Not detectable from responses.** The served `model_version` (both langchain
  `response_metadata` and the raw `google.genai` response) just echoes the alias
  `gemini-3.1-flash-lite` — no underlying snapshot id. So there's nothing extra to log in
  `runtime_fingerprint` that would surface drift; the fingerprint's `game_model` already
  records the alias, and that's all Vertex exposes.
- **What the fingerprint DOES catch:** backend (`llm_backend`: vertex/google) and region
  (`vertex_location`). Those changes are visible; alias-snapshot drift is not.

**Consequences / standing rules:** (1) same-epoch fresh baseline is mandatory for any A/B —
never pair against historical-epoch outcomes; (2) optional active guard = a temp-0 canary
prompt set run alongside batches, watched for output-distribution shift (temp=1.0 can't
separate drift from variance); (3) revisit pinning once Google ships a dated
`gemini-3.1-flash-lite-NNN` snapshot.

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

## ⭐ Pre-registration — reranked-arm predictions (written 2026-06-11, BEFORE any reranked game completed; reranked arms at 0/30 at commit time)

Calling the shots before the data, to avoid the multiple-comparisons trap (~5 arms × ~8 proxies
≈ 40 tests → expect ~2 false positives at p<0.05 even if memory does nothing; the pilot's
"70%→97% proven" was the best of 6 cells and did NOT replicate).

- **PRIMARY endpoint = ONE validated proxy per arm (NOT win rate).** Win rate is underpowered at
  N=30 (~1 bit/game), so it is demoted to a directional co-read: reported, but a flat win rate is
  "underpowered," not "refuted." The powered primaries are the monotonicity-validated proxies
  (chosen by the INDEPENDENT proxy-monotonicity check, before any A/B result).
- **Called shots — reranked-observation arms (each vs its RAW counterpart):**
  - `rerank-town` (the strong bet) — PRIMARY `town_vote_accuracy`. PREDICT reranked-town > raw-town
    (sharper retrieval → less diluted town reasoning). Flat → raw retrieval was already adequate.
  - `rerank-wolf` — H: low raw-retrieval precision was the bottleneck. PRIMARY `town_vote_accuracy` /
    `mislynches`; PREDICT town detection DROPS vs raw-wolf (sharper wolf memory → wolves hide
    better). Win rate = underpowered headline. Flat → content, not precision, is the limit.
  - `rerank-sk` — exploratory (no strong prior); no called shot.
- **Called shot — raw all-on arm (`all_enabled`, no reranker), vs the same-epoch baseline:**
  - H (derived from the isolation arms): town memory *helped* town and evil memory *didn't help*
    evil, so if effects compose additively, all-on leaves town **neutral-to-better** — which
    CONTRADICTS the pilot's confounded "all-on → town collapses −32pp, wolves flip to 40%."
    PRIMARY `town_vote_accuracy` + villager win rate. **PREDICT all-on does NOT replicate the pilot's
    town collapse: town proxies/win hold or improve vs baseline.** If town instead collapses → a
    destructive interaction the isolation arms can't see (and the pilot effect is real, not just the
    confound). This is the clean same-epoch replication test of the finding that started the whole
    investigation.
- **Decision rule:** a called shot that hits = confirmatory evidence. Any OTHER metric that lights
  up = exploratory lead ("needs its own follow-up"), not a conclusion. p-values uncorrected AND with
  a Bonferroni note over the pre-specified primaries (≤3 tests). The raw arms already ran, so their
  proxy hits inherit the validated-basket protection but are reported with the multiplicity
  caveat — not as called shots.

## Analysis

Per arm, pair each of the 30 arm games to its baseline by `game_id`: the 20 recovered ids
pair against `seed_set.json` recorded winners; the 10 fresh ids pair against the `ab_baseline`
run. McNemar on the arm's faction win (wolf-faction for wolf_only, SK for serial_killer_only,
town for town_only) + the validated de-lucked proxies. Reuse `evaluation/src/core/stats.py`.

## Raw results — N=30 paired, FINAL (2026-06-11)

Same-epoch baseline (villagers 27% / SK 40% / wolves 33%). Numbers in `report.md`.

- **town_only:** villager win 27%→43% (+17pp, McNemar p=0.27, underpowered). Validated proxies move
  together, several significant: `correct_elimination_rate` +0.17 (p=0.028), `town_mislynch_rate`
  −0.17 (p=0.036), `healer_town_save_rate` +0.23 (p=0.005), `town_vote_accuracy` +0.15 (p=0.053).
  ⭐Cleanest positive: town memory improves town decision quality.
- **wolf_only:** wolf win FLAT 33%→30% (p=1.000) — no evidence memory helps wolves; the pilot's
  "wolf memory is powerful" does NOT replicate. Town proxies nominally up (mislynch p=0.042).
- **serial_killer_only:** SK win 40%→20% (p=0.146, suggestive-not-sig); SK memory didn't help SK.
- **Cross-arm pattern + multiplicity:** town decision-quality proxies improve in ALL arms; ~7 of 24
  tests p<0.05 vs ~1.2 expected by chance → a real signal exists, but NO single hit survives
  Bonferroni (0.05/24 = 0.002) — the town arm's CONSISTENCY (4 directional hits) is the strongest
  evidence, not any one p. Diagnosed: retrieval works (~3.4 obs/decision), store not dup-cluttered
  (0% near-dups) but semantically dense → low raw-retrieval precision is the leading suspect for the
  weak/absent evil-arm effects. Win rate underpowered in every arm (the proxies carry the signal).
- **Headline (raw):** memory helps TOWN decision quality (multiple validated proxies significant,
  consistent, with a directional +17pp win); no detectable benefit to wolf or SK. The reranked and
  all-on arms (pre-registered above) test the precision hypothesis and the interaction/replication.

## Code pointers

- Seed pinning: `scripts/run_batch.py --game-ids-file` → `run_game(game_id=…)` →
  `build_game_config` → `initialize_game` (role draw `crc32(game_id)`).
- Seed-set generator: `scripts/make_ab_seed_set.py`.
- Treatment presets: `MEMORY_CONFIGS` / `RETRIEVAL_TYPES_CONFIGS` in `run_batch.py`; `top_k`
  in `Agents/memory/enrichment/pipeline.py`.
