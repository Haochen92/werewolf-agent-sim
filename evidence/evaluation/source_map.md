# Evaluation: source map

*Slimmed 2026-10-24. Each method page now ends with its own Sources table (code and record for every check
it covers), so this page keeps only what lives nowhere else: the data every method reads, the retired and
archived records, and the records outside version control. The full 2026-10-23 ledger, with a row per
instrument, its trust mark, what changed since July and the July verify-in-code results, is kept whole in
the [experiment log](experiment_log.md), Part 2.*

**Where things live (settled).** `evaluation/` holds the code and `evidence/` holds the record. The data
plane between them is `evaluation/{config,frozen_eval_sets,eval_results}/` and `batch_results/`
(`CLAUDE.md`, "Eval Architecture"; `evaluation/README.md`, Data plane). Code paths below are from the repo
root; record paths are from `evidence/`. The overview of all evaluation is [the hub](report.md).

## Data plane (the input substrate)

Mostly the capture side's output; listed because every instrument reads it. Marks here are July's and
no spoke re-rates them.

| Piece | Code | Game | Mark | Since July / notes |
|---|---|---|---|---|
| Frozen-set builders | `evaluation/src/data/builders/{agent_decision,extraction,dedup,hallucination_bench}.py` (`eval-build-dataset` at `pyproject.toml:39`, `eval-build-{extraction,dedup}-dataset`, `eval-build-hallucination-bench`) → `evaluation/frozen_eval_sets/<id>.jsonl` + manifest | both | July ✅ | **moved** (was `experiments/dataset_builder.py`). Tests `tests/evaluation/test_{eval_case_sink,local_case_source,langfuse_fetch}.py` |
| Stratified sampling | `evaluation/src/data/sampling.py` (`sample_cases`); test `tests/evaluation/test_sampling.py` | 9 | July ✅ | same. Default day-only. Also the cohort step of the case sampler |
| Converters and sources | `evaluation/src/data/{converters,sources}/`, `frozen_sets.py`, `batch_layout.py`; `sources/replay_api.py` (served games through the public replay endpoint) | both | July ✅/🟡 | **new**: `replay_api.py`, `batch_records.py`. Old formats in `evaluation/src/archive/legacy_cases.py` |
| Live-game checkpoints | `evaluation/experiments/haiku_game_turn_cases.py` (`day_states`; reads the server's Postgres without writing) | 10 | — | **new**. Case source for most October replays |
| Captures | `*.capture.json.gz` from the capture runners in `evaluation/experiments/`; served games' `prompt_captures` (`server/storage/prompt_captures.py`) | 10 | — | **new**. Source for the evil-cover and counter-claim screens and the block census |
| Provenance manifest | `evaluation/src/core/manifest.py`; test `tests/evaluation/test_manifest.py` | both | July ✅ | same. Methodology spoke: "drift-evident provenance, not byte-for-byte reproducibility" (`tracing/fingerprinting/report.md` §1, §5) |
| Cost estimates | `evaluation/src/core/costs.py` | both | 🟡 (model admission §9) | **changed**: prices now come from the model catalogue (`costs.py:13-14`). The 4-characters-per-token estimate remains (`costs.py:16`) |

## Records: retired, frozen and archived

| Record | Code | Record | Status |
|---|---|---|---|
| Discussion tagger | `evaluation/src/loop/discussion_tagger.py`; `evaluation/src/cli_runner/discussion_tagger_eval.py` (`eval-tagger`); `evaluation/src/instrument_validation/tagger/{tagger_validation,tagger_effectiveness}.py` | `evaluation/llm_judge/discussion_tagger.md` (moved 2026-10-23); `v7_final/experiment_log.md` §12g | **retired**. 🟡 as recorded in July. Credit mode deleted 2026-07-13 (`evaluation/src/loop/driver.py:373`, "since the tagger mode's retirement"); runs in no game; out of the write-up (owner, 2026-10-22, `writeup/map.md`). Its report's consumer table is stale and is left as a record |
| Hardening pass | — | `evaluation/hardening_pass/{report,experiment_log}.md` | dated record (2026-07-02, interim). Its fixes are rated where they now live |
| Archive | `evaluation/src/archive/{legacy_cases,legacy_retrieval_judge,eval_retrieval_v1,situation_summary_model_comparison,dedup_model_comparison,per_role_extraction,pairwise_extraction,pairwise_extraction_prompts}.py` | — | superseded; do not import live |
| Labelling and training structure (2026-06-29) | `training/` at the repo root; `evaluation/src/labeling/` | `evaluation/labeling/report.md` §1 | dated note: `training/` left `evaluation/` because it trains models rather than judging cases. `auto_dedup_labeler` was folded into the engine and adapter path (byte-identical prompts over 232 cases). `merger.merge` was retired after the staged pipeline showed it had never composed. Parked |

## Records outside version control (as of 2026-10-24)

`batch_results/` and `evaluation/eval_results/` are gitignored. The outputs the method pages cite were
copied into `evidence/` on 2026-10-23 (the admission records and replay summaries into
`evaluation/model_admission/data/`; the R1 samples and note-screen generations into
`reasoning_failures/data/`), and the files listed as untracked on 2026-10-23 were committed on 2026-10-24.
What remains outside git:

| What | Where | Cited by |
|---|---|---|
| June A/B game data | `batch_results/ab_*.jsonl` | evaluation_scopes/game, labeling/sampled_reads (sampler smoke) |
| v7 build run and endpoint, including the pre-registration amendment | `batch_results/v7_compound_town5/`, `batch_results/v7_endpoint_ab/` | loop, evaluation_scopes/game |
| v6 games read by the credit validators and proxy validations | `batch_results/v6ab_*.jsonl` | loop, metrics |
| Ten-seat games behind the 2026-10-24 win check and the v8 runs | `batch_results/{v8_demo,v8_seed_*,v8_gate_haiku,v8_luna_memory,ten_seat_pilot,cache_ab_2026_10_13}/` | metrics (the check's batch table is in `evaluation/metrics/data/ten_seat_win_check/`), loop |
| Raw replay outputs not copied | `evaluation/eval_results/hallucination_bench/` (other runs) | factual_errors |
| Code not found | the v7 endpoint's paired-statistic script; the reasoning-token probe; `evaluation/experiments/round_echo_filter_check.py`; the runner of the stored uses-left check | evaluation_scopes/game, experimental_controls, llm_judge, deterministic_audits |
