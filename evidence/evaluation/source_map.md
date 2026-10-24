# Evaluation — source map and reliability ledger

*Rewritten 2026-10-23 as the ledger for all evaluation, beside the hub (was: the memory pipeline's
inventory, written 2026-06-27, verified in code 2026-06-28, paths updated 2026-07-02).*

> **What this is.** The receipts behind [`report.md`](report.md). For every instrument it gives the code,
> the record, the game it ran on, its trust mark and what changed since July. The marks come from the
> spokes; this file sets none of its own. Where a spoke rates parts of one instrument differently, the
> row says so.
>
> **Where things live (settled).** `evaluation/` holds the code and `evidence/` holds the record. The data
> plane between them is `evaluation/{config,frozen_eval_sets,eval_results}/` and `batch_results/`
> (`CLAUDE.md`, "Eval Architecture"; `evaluation/README.md`, Data plane). The July note calling this
> folder provisional is withdrawn.
>
> **Paths.** Code paths are from the repo root. Record paths are from `evidence/`. Paths and statuses
> were checked against the working tree on 2026-10-23 (branch `feature-frontend-v1`, HEAD `1a5c0da1`,
> with uncommitted edits in `Agents/deduction/`). The July verify-in-code results are kept as a dated
> record at the end, each with its status today.

## Legend

**Trust marks (current, the hub's):** ✅ sound · 🟡 usable with caveats · ⚠️ smoke-test only · ⏸
design-only (or built and never used, where the row says so) · ⛔ underbuilt · "—" no mark in any spoke.

**July marks**, kept in the dated sections: ✅ VALIDATED · 🟡 PARTIAL · ⚠️ CLAIMED-UNVERIFIED · 🔴
WEAK/NULL · ⏸ DEFERRED · 🔍 NEEDS-CODE-READ. 🔴 has no current equivalent. July 🔴 rows now carry the
spoke's ⚠️ or 🟡, or are recorded as a result rather than an instrument mark.

**Since July:** **new** (not in the July map) · **moved** (code path changed) · **re-rated** (mark
changed) · **fixed** · **retired** · **same**.

**Game:** 9 = the nine-seat game (through July 2026); 10 = the ten-seat game (live since 2026-10-09).

**Tests** named below are cited for what they pin. The suite is largely AI-written and unaudited, so a
passing test is not evidence of quality.

## The spine

```
Data plane         frozen cases · batch records · captures · checkpoints → sampled sets
Rung 0             code checks, no model                        (deterministic_audits/)
Rung ①             LLM judges                                    (llm_judge/)
Rung ②             sampled and blind reads                       (sampled_human_review/)
Rung ③             golden labels                                 (labeling/)
Instrument layer   factual errors · replays · paired games · metrics · memory-field
                   audits · v7 loop · methodology · model admission and cost
Records            hardening pass (July) · discussion tagger (retired) · archive
```

---

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

---

## Rung 0 — code checks with no model (new)

Spoke: [`deterministic_audits/report.md`](deterministic_audits/report.md). The July map had no rung 0. The
embedding canary was built on 2026-07-02, superseding the July line that alias drift was undetectable.

| Instrument | Code | Record | Game | Mark | Since July / notes |
|---|---|---|---|---|---|
| Batch leak checks | `tests/leak_test.py` (`run_leak_tests`, `leak_inputs`); wired in `scripts/run_batch.py` and the capture runners | `agent_boundaries/report.md` §3–5, `experiment_log.md`, `leakwire_smoke.log`, `leakfix_smoke.log` | both | ✅ | **new**. Nine checks per game. One true positive (109 → 0, 2026-06-06). Three checkers were no-ops on live games until 2026-10-14 |
| Payload leak tests | `tests/engine/test_{round,night}_payload_leaks.py`, `test_wolf_channel_day_visibility.py`, `test_night_whiff_disclosure.py` | `agent_boundaries/report.md` §3, §5 | 10 | ✅ | **new**. Each plants a leak and asserts the check catches it |
| Served-game leak audit | `server/housekeeping/leak_audit.py`, `server/storage/prompt_captures.py`; `tests/server/test_leak_audit.py` | `agent_boundaries/report.md` §3, §5; `server/README.md`; cron status `writeup/map.md` | 10 | 🟡 | **new**. Built and tested. The cron was found not installed on 2026-10-23 (no crontab entry, no log); no served game is known to have been audited |
| Information-fidelity pins | `tests/engine/test_information_fidelity.py` | `game_play_enhancement/discussion_evidence.md` §6.4–6.5; `evaluation/factual_errors/experiment_log.md` §8 | 10 | ✅ (narrow) | **new**. Module docstring on held drafts is stale; the test asserts the current rule |
| Deduction soundness, random nights | `tests/engine/deduction/test_{own_results,public_events,candidates,conditionals}.py`; `tests/factories/{random_nights,random_claims}.py` | `reasoning_failures/report.md` §1, §3; `reasoning_failures/deduction_catalogue.md` "Build verification", "Build status" | 10 | ✅ | **new**. 20,000 nights per test at fixed seeds. Mutation checks at build were one-time |
| Brute-force oracle and metamorphic leak test | `tests/factories/role_assignments.py`; `test_candidates.py`, `test_own_results.py`, `test_role_traits.py` | same | 10 | ✅ | **new**. Oracle and engine share the written rules, so a fact neither encodes is invisible to both |
| Acceptance cases AC1–AC4 | `tests/engine/deduction/test_acceptance.py` | catalogue "Acceptance cases" | 10 | 🟡 | **new**. The only test of coverage; four hand-written goldens |
| Solver census | `evaluation/experiments/deduction_solver_census.py` (untracked) | `reasoning_failures/data/solver_census/census.json` (untracked); `reasoning_failures/report.md` §3 (untracked) | 10 | ✅ (one run) | **new**. 150 games, 3,408 seat views, 0 misses. Commit `e765a18e`, dirty |
| Block census | `evaluation/experiments/deduction_block_census.py` | `reasoning_failures/data/deduction_block_census/`; catalogue slice 8 | 10 | 🟡 | **new**. 278 turns over 4 games, 2026-10-18; not re-run since slice 17 |
| Scheduler access audit | `evaluation/src/audits/scheduler_access_audit.py`; `tests/evaluation/test_scheduler_access_audit.py` | `metrics/metrics_audit/scheduler_bias_log.md` §3 A–C | 9 | 🟡 | **new** to this map. Hard-codes nine-seat roles and fields |
| Whiff conversion audit | `evaluation/src/audits/whiff_conversion_audit.py`; `tests/evaluation/test_whiff_conversion_audit.py` | `scheduler_bias_log.md` ③.E | 9 | 🟡 | **new** to this map. Its premise no longer holds since the failed kill is disclosed |
| Pivotal-turn flags | `evaluation/src/audits/recall_flags.py` | `v7_final/extraction_coverage_ab_spec.md`; `v7_final/experiment_log.md` | 9 | ⚠️ | **re-rated** (July: diagnosis-funnel step 1, unrated). Never validated as a definition; no tests |
| Embedding canary | `evaluation/src/audits/embedding_canary.py`, `embedding_canary_pins.json`; call site `scripts/run_batch.py` | `evaluation/hardening_pass/experiment_log.md` §4.9 | both | ✅ (batch only) | **new**. Pins re-made 2026-07-16 and 2026-10-12 (`qwen/qwen3-embedding-8b`). The server never runs it. No record of it firing |

Code checks homed elsewhere: the census screen (factual errors), the dedup golden scorers (rung ③), the
arm guard, fingerprint, seedability and prompt golden (methodology), and the summary-claim replay's
field checks (factual errors).

---

## Rung ① — LLM judges

Spoke: [`llm_judge/report.md`](llm_judge/report.md). The shared default is
`DEFAULT_JUDGE_MODEL = "anthropic/claude-haiku-5-5"` (`evaluation/src/judges/config.py:15`, owner
2026-10-12, commit `e70f1627`). Players and the in-game gates default to the same model. Every recorded
memory-judge score came from Gemini judges and cannot be compared with a re-run on Haiku. The spoke rates
the memory-component judges ⚠️ as a group; its per-judge table keeps the July tags, given in brackets.

| Judge | Code | Record | Game | Mark | Since July / notes |
|---|---|---|---|---|---|
| Situation-summary (pairwise + rubric) | `evaluation/src/judges/situation_summary{,_pairwise}.py`; `evaluation/src/cli_runner/regen_replay/both/situation_summary_{pairwise,rubric}.py` (`eval-summary`, `eval-summary-rubric`); `evaluation/src/replay/situation_summary.py` | `extraction/situation_summary/`; `evaluation/llm_judge/agent_decision.md` | 9 | ⚠️ (July 🟡) | **moved**, **re-rated**. A golden retrieval key exists, not wired to the judge |
| Retrieval | `judges/retrieval.py`; `cli_runner/regen_replay/both/retrieval.py` (`eval-retrieval`); `replay/retrieval.py` | `retrieval/`; `agent_decision.md` | 9 | ⚠️ (July 🔴 in the spoke's table, 🟡 here) | **moved**, **fixed**: fallback rows carry `is_fallback` (`judges/retrieval.py:30`) and are excluded from every average (`both/retrieval.py:97-110`; `tests/evaluation/test_retrieval_judge_fallback.py`) |
| Application and adherence | `judges/turn_action.py`; `cli_runner/regen_replay/both/turn_eval.py` (`eval-application`); `replay/turn_action.py`; `evaluation/src/loop/memory_adherence.py` | `memory_system/strategy_adoption/{report,judge_validation_protocol}.md` | 9 | ⏸ calibration never run | **moved**. Still uncalibrated; no longer gates anything |
| Extraction | `judges/extraction.py`; `cli_runner/regen_replay/judge/extraction_judge.py` (`eval-extraction`, `pyproject.toml:49`); `evaluation/src/archive/per_role_extraction.py` | `extraction/post_game/`; `evaluation/llm_judge/extraction.md` | 9 | ⚠️ (July 🟡, de-bugged not calibrated) | **moved**. v7 synthesis unjudged |
| Dedup quality (online, batch) | `judges/{dedup,batch_dedup}.py`; `cli_runner/regen_replay/judge/dedup_judge.py` (`eval-dedup`), `both/batch_dedup_judge.py` (`eval-batch-dedup`) | `evaluation/labeling/dedup.md`; `dedup/` | 9 | ⚠️ | **moved**. `batch_dedup.py` swallow-all fix of 2026-06-28 (not re-checked) |
| Day-summary | `judges/day_summary.py`; `cli_runner/regen_replay/both/day_summary_judge.py` (`eval-day-summary`) | `extraction/day_summary/experiment_log.md`; `evaluation/llm_judge/day_summary.md` | 9 | ⚠️ smoke test | **moved** |
| Turn-pipeline | `judges/turn_pipeline.py` (`eval-turn`, `eval-e2e`) | — | 9 | ⚠️ (group) | **new** to this map |
| Census and bench reader | `judges/role_fact_read.py` (`eval-role-hallucination-read`) | `generation_prompt/validation/hallucination_baseline.md`; `discussion_evidence.md` §6.6 | 9 cases | 🟡 | **new**. Owner hand check 2026-07-08 on the Gemini cascade; 10 of 12 bench verdicts upheld; no record of the 23-case gate on Haiku |
| Golden-expectation | `judges/golden_expectation.py` | `discussion_evidence.md` §8.4–8.7 | both | 🟡 | **new**. Expectations hand-written; verdicts read by hand; no agreement rate |
| Discussion-evidence | `evaluation/experiments/discussion_evidence.py` (`judge`) | `discussion_evidence.md` §4–6, §7.1, §9; `game_play_enhancement/data/{baseline_smoke,live_baseline,live_v2,live_v2_game2}/`, `data/phase2_step8_games/judge/` | 9 | ⚠️ | **new**. Every "check:" line in the review sheets blank. Role join is nine-seat only |
| Echo gate and offline checks | `Agents/turn/echo_gate.py`; `evaluation/experiments/line_echo_gate_check.py`, `silence_calibration.py` (`gate_check`) | `game_play_enhancement/data/{line_echo_check,round_echo_check,silence_calibration}/`; `discussion_evidence.md` §7.4 | 9 → 10 | 🟡 | **new**. As shipped: held 10 of 29 restatements, 0 of 36 worthwhile lines, against four blind Sonnet readers. Its June predecessor, the standalone novelty label, separated constructed pure-restatement from genuinely new probes 20 of 20 both ways (`sequential_discussion/experiment_log.md`, Smoke 2, 2026-06-01): labelled by construction, an upper bound. `round_echo_filter_check.py`, named in a README, is not in the repo |
| Opening filter | `Agents/turn/round_filter.py` | `game_play_enhancement/data/silence_calibration/README.md` | 10 | ⚠️ | **new** |
| Decision tagger | `scripts/tag_observation_decisions.py` | `memory_system/v8/data/decision_tags/` | 10 | ✅ in sampled_human_review (beat a pre-set bar) · 🟡 in llm_judge §7 (model readers only) | **new**. The two spokes differ; see rung ③ note below |
| De-halo pass | `Agents/memory/extraction/dehalo.py` | `memory_system/v8/decisions.md` §13; `memory_system/v8/data/dehalo_compare/` | 10 | ⚠️ | **new**. Checked against the deterministic grade, not people |
| Point-dedup judge (v8 synthesis) | via `evaluation/experiments/v8_sp_dedup_dry_run.py` | `memory_system/v8/experiment_log.md` | 10 | ⚠️ | **new** |
| Summariser comparison judge | `evaluation/experiments/haiku_summary_compare.py` (Sonnet 5.5) | `reasoning_failures/experiment_log.md` §3 | 10 | ⚠️ | **new**. First judging invalid (judge saw the moderator's line); rerun |

The criticality and forced-schema screens use no judge; they are replays (below).

---

## Rung ② — sampled and blind reads

Spoke: [`sampled_human_review/report.md`](sampled_human_review/report.md). Readers are Claude subagents
(Sonnet or Opus) unless a row says otherwise. July rated this rung ⛔ underbuilt; the spoke now rates it
🟡.

| Instrument | Code | Record | Game | Mark | Since July / notes |
|---|---|---|---|---|---|
| Case sampler | `evaluation/src/diagnosis/sampler.py`; `evaluation/src/cli_runner/diagnosis/case_sampler.py` (`eval-case-sample`); `tests/evaluation/test_diagnosis_sampler.py` | `evaluation/sampled_human_review/{plan.md,sampler_smoke/}`; `writeup/triage.md` row 68 | 9 | unrated (built, tested, never used) | **new**: the July "planned build" (below), built 2026-07-02. `assert_outcome_blind` raises on outcome-named signals |
| Blind packet reads | runners in `evaluation/experiments/`: `silence_calibration`, `evil_cover_screen`, `voice_rewrite_screen`, `persona_line_screen`, `visit_wording_cases`, `note_prompt_cases`, `deduction_placement_screen` | their `game_play_enhancement/data/` and `reasoning_failures/data/` folders (packets, keys, verdicts) | 10 | 🟡 | **new**. One reader per item; agreement never measured; no owner calibration |
| Phase 3 hand-read games | `evaluation/experiments/phase3_render_transcript.py` | `game_play_enhancement/data/phase3_reads/README.md` | 10 | 🟡 failure modes · ⚠️ counts | **new**. Not blind; rubric and reader reports not kept |
| Discussion-quality gate | `evidence/sequential_discussion/quality_gate/scripts/metrics.py` (study code in the record) | `sequential_discussion/quality_gate/{experiment_log,rubric}.md` | eight-seat | 🟡 structural claim · ⚠️ deltas | **new**. Read by the implementer, arm known |
| v8 retrieval and store reads | `evaluation/experiments/{v8_gate_lookups,v8_reextract_reads}.py` | `memory_system/v8/experiment_log.md`; `memory_system/v8/data/{gate,reextract}/` | 10 | 🟡 | **new**. The planned owner pass after the subagents was not found |
| Credit attribution spot-check | — (sampling recorded in the file) | `credit/attribution_spot_check.json`; `credit/report.md` §5 | 9 | ⚠️ | **new**. 13 of 15; true mismatch could be up to about 36% |

---

## Rung ③ — golden labels

Spoke: [`labeling/report.md`](labeling/report.md); dedup scorers in [`labeling/dedup.md`](labeling/dedup.md).

| Instrument | Code | Record | Game | Mark | Since July / notes |
|---|---|---|---|---|---|
| Labelling pipeline | `evaluation/src/labeling/{engine,voter,exporter,base,config,pipeline}.py`, `adapters/`, `dedup_golden_builder.py`, `manual_labelers/`; `tests/evaluation/test_labeling_pipeline.py`, `test_dedup_golden_builder.py` | `evaluation/labeling/{report,plan,experiment_log}.md` | 9 | 🟡 | **moved** (test path). No `calibration.py`; none of the seven gaps closed. `dedup_golden_builder` default moved to Haiku 5.5 on 2026-10-12; no golden minted with it |
| NDCG and reranker scorers | `evaluation/src/labeling/label_scorer/` (`situation_retrieval_ndcg`, `reranker_comparison`, …) | `llm_judge/golden_set_method.md`; `fine_tuning/cross_encoder/reranker/` | 9 | part of the pipeline row | **moved** into the labelling package. Situation golden: about 20 human cases, the rest machine-added; not wired to the judge |
| Dedup golden scorers | `evaluation/src/audits/{dedup_score,batch_dedup_score}.py` (`eval-dedup-score`) | `evaluation/labeling/dedup.md`; `evaluation/frozen_eval_sets/dedup_v2_golden_labels.json` | 9 | 🟡 | same. 65 online / 111 batch human keys. Scores predate v6, the Vertex shift and the Haiku default. `dedup.md` still cites old `evaluation/src/experiments/` paths |
| Prefilter calibration sets | `evaluation/src/studies/{eval_auto_dedup,auto_dedup_dataset_builder,batch_dedup_merge_eval}.py`; `scripts/sweep_2d_thresholds.py`; `evaluation/experiments/prefilter_similarity_exhibit.py` | `dedup/embedding_prefilter/experiment_log.md`; `memory_system/v8/data/embedder_migration/` | 9 content | 🟡 | **new** to this map. 65 human labels; the 232-case set is model-labelled. Qwen thresholds fail on the 232 |
| Tell-detector cases | `evaluation/src/loop/tells.py`; probes frozen in `extraction/tell_extraction/scripts/` | `extraction/tell_extraction/report.md` §4, `experiment_log.md` ⑧ ⑩ ⑪; `outputs/owner_golden/` | 9 | ⚠️ | **new**. 40 cases by five Opus adjudicators; one game owner-checked (7 of 8) |
| Readers' duplicate groups | `evaluation/experiments/v8_sp_dedup_dry_run.py` | `memory_system/v8/data/reextract/{points,dedup_dry_run}/` | 10 | ⚠️ | **new**. One pass by model readers; applied as labels without a check |

---

## Instrument layer

### Factual errors

Spoke: [`factual_errors/report.md`](factual_errors/report.md). All **new** to this map. The run
templates under `evaluation/config/template/hallucination_bench_*.json` were edited on 2026-10-12 to
Haiku judges, so they no longer reproduce their recorded runs.

| Instrument | Code | Record | Game | Mark |
|---|---|---|---|---|
| Census screen | `evaluation/src/audits/role_hallucination_screen.py` (`eval-role-hallucination`) | `generation_prompt/validation/hallucination_baseline.md` | 9 | ✅ within its scope (`ROLE_ALIASES` holds the six nine-seat roles only) |
| Census reader | see rung ① | same | 9 | 🟡 |
| T1b counterfactual replay | `generation_prompt/validation/t1b_replay.py` (frozen study code) | `generation_prompt/validation/t1b_results.md` | 9 | ⚠️ no power per case |
| T2 regression replay | `generation_prompt/validation/regression_replay.py` (frozen) | `generation_prompt/validation/t2_results.md` | 9 | 🟡 |
| T1c ship test | `generation_prompt/validation/t1c_ab_replay.py` (frozen) | `generation_prompt/experiment_log.md` §12; `validation/t1c{,2}_outputs.jsonl` | 9 | 🟡 (vote turns saw their result) |
| The bench | `evaluation/src/cli_runner/regen_replay/both/hallucination_bench.py` (`eval-hallucination-bench`); `evaluation/src/data/builders/hallucination_bench.py`; `evaluation/src/replay/hallucination_bench.py`; `evaluation/frozen_eval_sets/hallucination_bench_v{1,2}.jsonl` (125, 129 cases) | this spoke; its `experiment_log.md` §8–9 (the code audit and fix check, folded in 2026-10-23); `discussion_evidence.md` §6.5–6.7; screen run `evaluation/eval_results/hallucination_bench/screen_v1/` (gitignored) | 9 cases | 🟡 (day turns only) |
| Invented-check replay | `evaluation/experiments/investigator_claim_replay.py` | `game_play_enhancement/data/investigator_replay/` (no README); `discussion_evidence.md` §6.2 | 9 | ✅ for that one turn |
| Ten-seat pinned cases | `evaluation/experiments/{phase3_turn_cases,haiku_game_turn_cases}.py`; configs `evaluation/config/hallucination_bench_phase3_*.json`, `hallucination_bench_haiku_game{,_vote_v2}.json` | `game_play_enhancement/data/{phase3_turn_replay,haiku_turn_replay}/`; `discussion_evidence.md` §8.4, §8.6 | 10 | 🟡 regression only |
| Summary-claim replay | `evaluation/experiments/summary_claim_replay.py` | `game_play_enhancement/data/phase3_summary_replay/` | 10 | 🟡 regression only |
| Ten-seat population rate | — | — | 10 | ⛔ none exists |

### Frozen-turn replays

Spoke: [`replay_screens/report.md`](replay_screens/report.md). Shared engine for the October screens:
`evaluation/src/replay/hallucination_bench.py` (`turn_payload`, `turn_template`, `hydrate_state`).

| Instrument | Code | Record | Game | Mark | Since July / notes |
|---|---|---|---|---|---|
| Decision-replay screen | `evaluation/src/studies/decision_replay.py`; engine `evaluation/src/replay/decision_screen/`; lenses `Agents/memory/consolidation/decision_scoring.py` (shim `evaluation/src/loop/decision_scoring.py`) | `memory_system/effectiveness/decision_replay/` | 9 | ✅ triage | **moved** (was `experiments/studies/`). Converges with June's decision measures, not a win gain. Reruns need a `phase2-baseline` checkout |
| Checkpoint replay | `evaluation/src/replay/decision_screen/checkpoint_replay.py` (`eval-checkpoint-replay`) | `credit/blindspot_fix/experiment_log.md` ④–④d | 9 | 🟡 | **new**. Never run on generation snapshots; model not in the manifest |
| Tell-book screen | `evaluation/src/replay/decision_screen/tell_book_screen.py` | `extraction/tell_extraction/experiment_log.md` ⑫ | 9 | ⚠️ | **new** |
| Stage-filter replay | `evaluation/experiments/v8_stage_filter_replay.py` | `memory_system/v8/experiment_log.md`; `data/gate/stage_filter{,_40games}/` | 10 | 🟡 | **new** |
| Criticality screen | `evaluation/src/studies/criticality_screen.py` | `extraction/situation_dimensions/criticality_screen/` | 9 | — (July 🔴: the result, within ±0.03 noise) | **moved**. No judge; scored by `hit_threat` |
| Forced-schema screen | `evaluation/src/studies/forced_schema_screen.py`; `evaluation/src/instrument_validation/dimensions/dimension_gating_screen.py` | `memory_system/strategy_adoption/forced_schema_screen/experiment_log.md` | 9 | — (July 🟡 directional) | **moved** |
| Night-1 target check | `evaluation/experiments/night1_target_bias_check.py` | `game_play_enhancement/data/night1_target_bias/`; `discussion_evidence.md` §7.5 | 9 | ✅ | **new** |
| Evil cover screen | `evaluation/experiments/evil_cover_screen.py` | `game_play_enhancement/data/evil_cover_screen/` | 10 | 🟡 | **new** |
| Private-note screen | `evaluation/experiments/note_prompt_cases.py` | `reasoning_failures/experiment_log.md` §6; `reasoning_failures/data/note_prompt/`; generations in `eval_results/note_prompt_screen/` (gitignored) | 10 | ⚠️ | **new** |
| Haiku vote replay | `evaluation/experiments/haiku_vote_{cases,score}.py` (untracked); `evaluation/config/hallucination_bench_haiku_vote_compare.json` (untracked) | `discussion_evidence.md` §8.7; `data/haiku_vote_replay/`, `data/haiku_sentinel_vote/` (untracked) | 10 | 🟡 | **new** |
| Visit-wording A/B | `evaluation/experiments/visit_wording_cases.py` | `game_play_enhancement/data/visit_wording_ab/` | 10 | 🟡 | **new** |
| Persona line screen | `evaluation/experiments/persona_line_screen.py` | `game_play_enhancement/data/persona_line/` | 10 | 🟡 | **new**. The one screen with a designed noise baseline |
| Voice rewrite screen | `evaluation/experiments/voice_rewrite_screen.py` | `game_play_enhancement/data/voice_rewrite/` | 10 | 🟡 | **new** |
| Deduction injection (R1) | `evaluation/experiments/deduction_injection_{cases,score}.py` | `reasoning_failures/experiment_log.md` §4–5; `reasoning_failures/data/deduction_injection/`; samples in `eval_results/hallucination_bench/{deduction_injection,healer_silence}/` (gitignored) | 10 | 🟡 | **new** |
| Placement and AC2 series | `evaluation/experiments/deduction_placement_screen.py`, `deduction_ac2_{ablation,2x2,closing_fixed}.py` | `reasoning_failures/data/deduction_placement{,_n10}/`, `deduction_ac2_*/` | 10 | 🟡 | **new**. Uncommitted trees, diff hashed |
| Counter-claim vote screen | `evaluation/experiments/counter_claim_vote_screen.py` | `game_play_enhancement/data/counter_claim_votes/` | 10 | ⚠️ | **new**. The engine change was never committed; cannot rerun at HEAD |
| Per-day replay | none | `memory_system/effectiveness/day_replay/design.md` | 9 | ⏸ | same (still not built) |

### Paired game A/B

Spoke: [`whole_game_evaluation/report.md`](whole_game_evaluation/report.md).

| Instrument | Code | Record | Game | Mark | Since July / notes |
|---|---|---|---|---|---|
| June memory on/off A/B | `scripts/run_batch.py`, `scripts/make_ab_seed_set.py`; `evidence/memory_system/effectiveness/paired_ab/analyze_ab.py`, `evidence/memory_system/effectiveness/regenerate_stats.py`; `evaluation/src/core/stats.py` | `memory_system/effectiveness/paired_ab/{report,experiment_log}.md`; `memory_system/store_progression.md` (correction 2026-10-22); data `batch_results/ab_*.jsonl` (gitignored) | 9 | 🟡 | **re-rated** (July ✅ VALIDATED). The headline is corrected: decisions improved (healer saves p=0.005, correct eliminations p=0.028, Wilcoxon), wins did not significantly (p=0.27). Never pair "+17pp" with p=0.013 |
| Older does-memory-help batches | `run_batch` arms | `memory_system/effectiveness/report.md` | 9 | July ⚠️ | same; not re-examined. Batch A 70 → 97% not replicated in Batch B; the 23-point swing was a store and namespace confound |
| v6 strategy-point A/B | `evidence/memory_system/effectiveness/v6_sp_ab/launch_arms.sh`; `scripts/run_batch.py` | `memory_system/effectiveness/v6_sp_ab/experiment_log.md` | 9 | 🟡 | **new** row (July verify #10). Town and serial killer only; the wolf was excluded |
| v7 endpoint A/B | `evaluation/src/loop/measure.py` (`game_score`); the run driver and the paired-statistic script: not found | `execution_plan/report.md` §4–5, `experiment_log.md`; `batch_results/v7_endpoint_ab/` (gitignored: `PREREG_AMENDMENT.md`, `config.json`, `endpoint_result.json` with pooled per-decision scores only) | 9 | 🟡 | **new** |
| Persona-voice games | `evaluation/experiments/persona_voice_games.py`, `persona_voice_games_score.py` | `game_play_enhancement/data/persona_voice_games/` | 10 | ⚠️ | **new**. 8 pairs, one-flag difference on one commit |
| Evil-cover games | `evaluation/experiments/evil_cover_screen.py` (`games`) | `game_play_enhancement/data/evil_cover_games/` | 10 | ⚠️ | **new**. Three changes bundled; dirty trees |

### Play metrics

Spoke: [`metrics/report.md`](metrics/report.md).

| Instrument | Code | Record | Game | Mark | Since July / notes |
|---|---|---|---|---|---|
| Nine-seat de-lucked basket | `Agents/compute_metrics.py`; `Agents/schemas/metrics.py:254` (84 fields, was 63); `evaluation/src/instrument_validation/proxies/`; `evaluation/src/core/stats.py` (`point_biserial`) | `metrics/{proxy_win_monotonicity,experiment_log}.md`; `metrics/design/`; `metrics/metrics_audit/` | 9 | ✅ town · 🟡 investigator · ⚠️ deceiver · 🟡 town discussion | **re-rated**: discussion July 🔴 → 🟡 (town diagnostic proxy found 2026-07-02); harness **moved** to `instrument_validation/proxies/proxy_win_monotonicity.py`. Validated on nine seats only |
| Trust tiering and push | `Agents/compute_metrics.py:688-776` (`VALIDATED_ON_TEN_SEAT_METRICS` at :728, empty; `_metric_tier` :731; push :741) | `memory_system/v8/plan.md` §8.4 | 10 | — | **changed**: the July "indiscriminate push" became tiered on 2026-07-02; since the ten-seat port nothing pushes as "validated" |
| Ten-seat metrics and decision grades | `Agents/ten_seat_metrics.py`; `Agents/memory/consolidation/grading.py`; `scripts/grade_observations.py`; `tests/memory/test_ten_seat_grading.py` | `memory_system/v8/{plan.md §8.1–8.4 and §9.6, decisions.md §8 and §12–13, experiment_log.md}` | 10 | ⚠️ | **new** |
| Read Brier | `evaluation/src/loop/read_ledger.py` (nine-seat); `evaluation/experiments/persona_voice_games_score.py` (ten-seat) | `credit/report.md` §1, §4; `game_play_enhancement/data/persona_voice_games/` | both | 🟡 | **new** |
| Vote-target accuracy | `Agents/compute_metrics.py:536`; `decision_scoring.py` (`score_vote`, nine-seat threat set); `evaluation/experiments/haiku_vote_score.py` | Part A of the spoke; `discussion_evidence.md` §8.7 | both | ✅ as a count | **new** |
| Leverage anchor | `evaluation/src/instrument_validation/proxies/leverage_anchor_separation.py` | `v7_final/plan.md`; `v7_final/experiment_log.md` | 9 | 🟡 | **new** |
| Discussion census | `evaluation/experiments/discussion_evidence.py` (`census`) | `discussion_evidence.md` §2 | 9 | ✅ counts · 🟡 labels | **new** |
| Phase 2 step 8 counts | `evaluation/experiments/phase2_step8_{capture,counts}.py` | `game_play_enhancement/data/phase2_step8_games/` | 9 | ✅ counts · 🟡 reading | **new** |
| Balance batches | `evaluation/experiments/phase3_capture.py` | `game_play_enhancement/data/phase3_{games,balance,balance_2,balance_3,balance_4}/`; `discussion_evidence.md` §8.3 | 10 | ✅ counts · 🟡 reading | **new**. 31 games on flash-lite; none on Haiku |
| Blend-tactic check | `evidence/generation_prompt/prompt_claims_audit/blend_claim_test.py` (study code in the record) | same folder, `experiment_log.md` | 9 | 🟡 | **new** |
| Investigator transmission | `evaluation/src/studies/investigator_transmission.py` | `memory_system/effectiveness/v6_sp_ab/experiment_log.md` | 9 | ⚠️ | **new**. Records cite the old `experiments/` path |
| Batch summary | `scripts/analyze_batch.py` | none | both | no trust of its own | **new** |

### Memory-field audits

Was the spoke `dimension_extraction/`, dissolved 2026-10-23: the code checks are now in
[`deterministic_audits/`](deterministic_audits/report.md) (case 3; detail in its `experiment_log.md` §5), and
the decision-tag read in [`sampled_human_review/`](sampled_human_review/report.md) (Instrument 4).

| Instrument | Code | Record | Game | Mark | Since July / notes |
|---|---|---|---|---|---|
| Query-side dimension audit | `evaluation/src/instrument_validation/dimensions/dimension_audit.py`; computed fills in `Agents/memory/retrieval/situation_agent.py` (`_override_deterministic_dims`, `_known_board_facts`) | `extraction/situation_dimensions/dimension_accuracy_audit/` | 9 | ✅ as a record | **re-rated** (July hub ⚠️). Every query-side numeric now computed by code; parity and swing joined 2026-07-11 |
| Stored uses-left check | no standalone runner found | `memory_system/v8/experiment_log.md`, 2026-10-12 | 10 | 🟡 | **new** |
| Verdict halo | `evaluation/experiments/v8_verdict_halo.py` | `memory_system/v8/data/halo/`; `memory_system/v8/decisions.md` §13 | 10 | 🟡 | **new**. Least squares, no intervals |
| Decision tags | `scripts/tag_observation_decisions.py`; `evaluation/experiments/v8_decision_tag_check.py` | `memory_system/v8/data/decision_tags/` | 10 | ✅ (llm_judge §7: 🟡) | **new** |
| Category labels on stored lessons | — | — | 9 | ⏸ never validated | same (the kappa clause never ran) |

### v7 loop and credit

Spoke: [`loop/report.md`](loop/report.md). All nine-seat.

| Instrument | Code | Record | Mark | Since July / notes |
|---|---|---|---|---|
| Measure | `evaluation/src/loop/measure.py`; `tests/evaluation/test_loop_measure.py` | `execution_plan/report.md` | ✅ (LLM-free) | same. `game_score` is the endpoint's primary, pinned to the legacy abstain rule |
| Credit engine | `evaluation/src/loop/{credit_backfill,credit,conversion_credit}.py`; `tests/evaluation/test_credit_blend.py` | `credit/report.md` | spoke: sound, with stated limits | **changed**: `discussion_mode` is gone; tagger credit deleted 2026-07-13; `abstain_credit` (default `neutral`) and the conversion channel added 2026-07-21, off by default |
| Invariants | `evaluation/src/loop/invariants.py` (`assert_arm_factions`, `assert_arm_declared`, `assert_fingerprint_consistent`, `assert_observations_retired`) | — | ✅ | **moved** line refs → function names. `assert_observations_retired` **new** (2026-07-15) |
| Driver and config | `evaluation/src/loop/driver.py` (`run_loop`, `_run_arms_parallel`), `config.py` | — | July 🟡 | same. Dead toggles `arm` (label only) and `frozen_base_rates` (declared, unwired) were still unwired on 2026-10-23 |
| Consolidate and merge | `evaluation/src/loop/{consolidate,merge}.py` | — | ✅ mechanics | evict rule can now fire (`credit.py::_adoption_counts`); evicted nothing in the July run |
| July 19 build run | `run_loop` | `execution_plan/report.md` §5, `experiment_log.md`; `batch_results/v7_compound_town5/` (gitignored) | part of ✅ mechanics | **new** |
| Credit validators | `evaluation/src/instrument_validation/credit/{g2_separability,g3a_verdict_validity,heldout_credit_reproduction,windowed_credit}.py` | `v7_final/experiment_log.md` §1–2, §6 | 🟡 | **new** (promoted 2026-07-04). `v7_final/review_map.md` mislabels G3a as "tagger verdict validity" |
| Blind-spot fix validation | `evaluation/experiments/credit_blindspot_validation.py`; `tests/evaluation/test_credit_blindspot_fix.py` | `credit/blindspot_fix/step1_validation.{md,json}`, `experiment_log.md` | 🟡 | **new** |
| Tell lift and fold | `evaluation/src/loop/{tell_credit,tell_fold}.py` | `extraction/tell_extraction/report.md` §2–4; `store_curation/tells.md` | 🟡 | **new** |
| First link | `evaluation/src/loop/first_link.py`; `tests/evaluation/test_read_ledger_first_link.py` | `credit/read_tactic_credit_redesign.md` §3 | ⏸ (never run on record) | **new** |
| Synthesis A/B and offline prune | `evaluation/src/studies/{synth_deluck_ab,consolidation_prune}.py` | `v7_final/runs/synth_deluck_ab{,_flite}/` | ⚠️ | **moved**; July: named in the diagnosis funnel, unrated |

### Methodology

Spoke: [`methodology/report.md`](methodology/report.md).

| Instrument | Code | Record | Game | Mark | Since July / notes |
|---|---|---|---|---|---|
| Fingerprint and drift guards | `Agents/run_fingerprint.py` (`runtime_fingerprint`); `evaluation/src/loop/invariants.py` | `model_drift/drift_surfaces_and_guards.md`; `tracing/fingerprinting/report.md` | both | ✅ in-run · manual cross-epoch | same. The prompt-bundle hash misses nested prompt packages |
| Interleaved arms | `evaluation/src/loop/driver.py` (`_run_arms_parallel`); not in `scripts/run_batch.py` | — | 9 | — | same; per-game alternation in `run_batch` still unbuilt |
| Paired statistics | `evaluation/src/core/stats.py` (`mcnemar_exact`, `wilcoxon_paired`, `binomial_ci`, `point_biserial`) | — | both | July ✅ | same (verify #1) |
| Power (MDE) gate | `evaluation/src/instrument_validation/power/mde_simulation.py` | `execution_plan/report.md` §2 (full table at `24dfd3a7`) | 9 | ✅ | **new**. Not run for the paired endpoint design |
| Seedability | `Agents/nodes/orchestrator.py` (`initialize_game`); `tests/engine/test_seedability.py` | `memory_system/effectiveness/paired_ab/experiment_log.md` (20 of 20 by hand, 2026-06-11) | both | ✅ | **new** |
| Prompt golden | `tests/fixtures/day_discuss_prompt_golden.{py,json}`; `tests/engine/test_draft_preview.py` | — | 10 | 🟡 | **new**. Day-discussion turn only; regenerated in 34 commits 2026-09-29 to 10-21 |
| Run graduation | `evaluation/src/cli_runner/graduate_run.py` (`eval-graduate`); `tests/evaluation/test_graduate.py` | `tracing/fingerprinting/report.md` | — | ⏸ built, never used | **new** |
| Reasoning-token scope probe | no committed script found; bench token recording since `3e05e8a7` | `credit/blindspot_fix/experiment_log.md` §⑦; `discussion_evidence.md` §6.7 | 9 | 🟡 | **new**. Game records still carry only the configured level |
| Variance-levers audit | — | `evaluation/methodology/variance_reduction_levers.md` | 9 | — | **moved** 2026-07-07 |

### Model admission and cost

Spoke: [`model_admission/report.md`](model_admission/report.md) (untracked on 2026-10-23). All **new**.

| Instrument | Code | Record | Game | Mark |
|---|---|---|---|---|
| Admission run | `evaluation/src/cli_runner/model_admission.py` (`eval-model-admission`); `evaluation/src/model_admission/{probes,seat_schemas}.py`; configs `evaluation/config/model_admission/*.json`; `tests/evaluation/test_model_admission.py` | 20 records in `evaluation/eval_results/model_admission/` (gitignored); the spoke is the first written record | both | 🟡 |
| Live schema gate | `tests/live/test_model_structured_output.py` | docstring note of 2026-09-10 only | 10 | ⚠️ (no `anthropic/` credential branch) |
| Bench arms for admission | `eval-hallucination-bench`; configs `evaluation/config/hallucination_bench_phase3_*.json`, `model_admission/bench_*.json`, `hallucination_bench_shared_prefix_luna.json` | summaries in `evaluation/eval_results/hallucination_bench/` (gitignored) | both | 🟡 |
| Thinking-budget replay | `evaluation/experiments/haiku_effort_{cases,score}.py` | `reasoning_failures/experiment_log.md` §2; `reasoning_failures/data/haiku_effort_replay/` | 10 | 🟡 |
| Summariser comparison | `evaluation/experiments/haiku_summary_compare.py` | `reasoning_failures/experiment_log.md` §3; `reasoning_failures/data/haiku_summary_compare/` | 10 | ⚠️ |
| Seat-model games | `evaluation/experiments/phase3_capture.py` | `game_play_enhancement/data/phase3_{flash,luna}_games/` | 10 | ⚠️ |
| Memory-job model comparisons | `evaluation/experiments/{claude_extraction_compare,dehalo_compare}.py`; v5 `evaluation/src/studies/extraction_model_comparison.py` | `memory_system/v8/data/{extraction_model_comparison,dehalo_compare}/`; `v7_final/extraction_screens/` | 10 / 9 | ⚠️ |
| July seat-model selection | none | `model_selection/report.md` | 9 | ⚠️ (historical) |
| Cost and cache accounting | `Agents/llm_factory/{pricing,catalog}.py`; `server/game/usage.py`; `evaluation/src/core/costs.py`; `evaluation/src/loop/cost.py`; `evaluation/experiments/game_cache_share.py`; `scripts/model_catalog.py`; `tests/engine/test_{pricing,langfuse_prices,shared_prefix_layout}.py` | `caching/report.md` §4–5; `caching/experiment_log.md` §11 | both | 🟡 |

---

## Records: retired, frozen and archived

| Record | Code | Record | Status |
|---|---|---|---|
| Discussion tagger | `evaluation/src/loop/discussion_tagger.py`; `evaluation/src/cli_runner/discussion_tagger_eval.py` (`eval-tagger`); `evaluation/src/instrument_validation/tagger/{tagger_validation,tagger_effectiveness}.py` | `evaluation/llm_judge/discussion_tagger.md` (moved 2026-10-23); `v7_final/experiment_log.md` §12g | **retired**. 🟡 as recorded in July. Credit mode deleted 2026-07-13 (`evaluation/src/loop/driver.py:373`, "since the tagger mode's retirement"); runs in no game; out of the write-up (owner, 2026-10-22, `writeup/map.md`). Its report's consumer table is stale and is left as a record |
| Hardening pass | — | `evaluation/hardening_pass/{report,experiment_log}.md` | dated record (2026-07-02, interim). Its fixes are rated where they now live |
| Archive | `evaluation/src/archive/{legacy_cases,legacy_retrieval_judge,eval_retrieval_v1,situation_summary_model_comparison,dedup_model_comparison,per_role_extraction,pairwise_extraction,pairwise_extraction_prompts}.py` | — | superseded; do not import live |
| Labelling and training structure (2026-06-29) | `training/` at the repo root; `evaluation/src/labeling/` | `evaluation/labeling/report.md` §1 | dated note: `training/` left `evaluation/` because it trains models rather than judging cases. `auto_dedup_labeler` was folded into the engine and adapter path (byte-identical prompts over 232 cases). `merger.merge` was retired after the staged pipeline showed it had never composed. Parked |

---

## Records outside version control (as of 2026-10-23)

| What | Where | Cited by |
|---|---|---|
| June A/B game data | `batch_results/ab_*.jsonl` (gitignored) | whole_game_evaluation, sampled_human_review (sampler smoke) |
| v7 build run and endpoint, including the pre-registration amendment | `batch_results/v7_compound_town5/`, `batch_results/v7_endpoint_ab/` (gitignored) | loop, whole_game_evaluation |
| v6 games read by the credit validators and proxy validations | `batch_results/v6ab_*.jsonl` (gitignored) | loop, metrics |
| Admission records and admission bench summaries | `evaluation/eval_results/model_admission/`, `evaluation/eval_results/hallucination_bench/*/summary.json` (gitignored) | model_admission, `caching/report.md` |
| Bench screen run, R1 samples, note-screen generations, Haiku vote outputs | `evaluation/eval_results/{hallucination_bench,note_prompt_screen}/` (gitignored) | factual_errors, replay_screens |
| Solver census runner and output; `reasoning_failures/report.md` | untracked files | deterministic_audits |
| Haiku vote replay runners, config and data | untracked files | replay_screens, metrics |
| The spokes `deterministic_audits/` and `model_admission/` | untracked folders | this hub |
| Code not found | the v7 endpoint's paired-statistic script; the reasoning-token probe; `evaluation/experiments/round_echo_filter_check.py`; the runner of the stored uses-left check | whole_game_evaluation, methodology, llm_judge, deterministic_audits |

---

## Superseded July sections (dated)

**The v7-run trust scorecard (2026-06-28).** It was written to gate a v7 run that has since happened. Its
five points, and what became of each:

| July point | Status on 2026-10-23 |
|---|---|
| "Town memory helps": paired A/B (N=30) and the replay screen converge | Corrected. June improved the town's decisions, not significantly its wins (p=0.27). v6 did not repeat it (+6 points, p=0.77). The v7 endpoint was 0.147 lower with memory (p≈0.06, 19 of 30 boards). Research closed 2026-07-21 |
| The wolf-memory null is power plus invalid runs; the tagger is a validated deceiver metric | Moot. The wolf-direct arm never ran and will not. The tagger was retired from credit on 2026-07-13 |
| Config sensitivity: lock `expect_factions` with matching `configs`, `base_store`, `model`/`dedup_model`, and `off_baseline=True` before a v7 run | The locks held in the July 19 run (`expect_factions: town_only`, verified per generation). No loop run is planned |
| Retrieval levers (criticality, core dilemma) are within noise | Stands, as a nine-seat result |
| The application judge is human-uncalibrated | Still true; gates nothing |

**The planned build (2026-06-27): the case-pull sampler.** Built on 2026-07-02 as
`evaluation/src/diagnosis/sampler.py` with `eval-case-sample`. Never used for a real review.

**The eval-report skeleton (2026-06-27/28).** It organized the hub by memory case type × modality. The
hub now organizes by subject × rung, with the A/B and instrument layer on top.

**The diagnosis funnel (memory, nine-seat), paths updated.** How a memory null was drilled into:
(1) did retrieval fire → EvalCase fields + `evaluation/src/audits/recall_flags.py`; (2) was it
relevant → `evaluation/src/judges/retrieval.py` + the situation NDCG golden; (3) was it used →
`judges/turn_action.py` + `evaluation/src/loop/memory_adherence.py`; (4) did the decision change →
`evaluation/src/replay/turn_action.py`; (5) did the outcome change → metrics, the paired A/B and the
decision-replay screen (`evaluation/src/studies/synth_deluck_ab.py` is a synthesis study, not an outcome
test).

---

## Verify-in-code pass — results (2026-06-28), with status on 2026-10-23

The July pass read the code behind the 🔍 flags and folded corrections into the July tables. Each item
gives the July verdict in brief, then its status today.

1. **`core/stats.py`: confirmed as the primary home.** Clopper–Pearson CIs (analytic, not bootstrap),
   Fisher exact, exact McNemar and Wilcoxon signed-rank, point-biserial; two-sided; no built-in
   multiple-comparison correction. The paired-A/B figures are Wilcoxon; the metric validations are
   point-biserial. *Status:* unchanged. `diagnose_wolf_sk_proxies.py` now lives in
   `evaluation/src/instrument_validation/proxies/`; `town_echo_read.py` is still in
   `memory_system/effectiveness/paired_ab/`; bootstrap CIs are still only in `training/evaluator.py`.
2. **Retrieval fallback: bias confirmed.** Fewer than two items gave relevance 1 but efficiency 5, pooled
   with no counter. *Status:* **fixed** (`is_fallback`, excluded at
   `cli_runner/regen_replay/both/retrieval.py:101,109`).
3. **`Agents/compute_metrics.py`: confirmed, one rename** (`town_mislynch_rate`; `suspicion_drawn` split
   by faction); the push was indiscriminate. *Status:* the push has been tiered since 2026-07-02, and
   since the ten-seat port nothing pushes as validated. 84 fields.
4. **Arm guard: confirmed, location corrected** (the loop, not `run_batch.py`). *Status:* held in the
   July 19 run. The July line refs (`driver.py:331`, `invariants.py:185-210`, `config.py:19`) have moved;
   `config.py:19` is now `retrieval_types`. The functions are `assert_arm_factions` and
   `assert_arm_declared` in `invariants.py`.
5. **Loop toggle matrix: confirmed and mapped** (32 config fields; both arms share generation and
   boards). *Status:* the field count was not re-checked. The dead toggles `arm` and
   `frozen_base_rates` are still unwired.
6. **Dedup and day-summary judges: resolved** (dedup 🟡; day-summary ⚠️; the `batch_dedup.py` silent
   failure fixed 2026-06-28). *Status:* both now in the spoke's ⚠️ memory-judge group; the fix was not
   re-checked.
7. **`eval-extraction` is a real entry.** *Status:* now `pyproject.toml:49`, pointing at
   `cli_runner/regen_replay/judge/extraction_judge.py`.
8. **Backend consistency: nuanced.** Env-driven, recorded in `runtime_fingerprint.llm_backend`,
   hard-asserted constant within a loop run; across runs a human must check. *Status:* unchanged in
   mechanism. The judge default is now Claude Haiku 5.5, so July Gemini scores and today's re-runs differ
   by vendor as well as backend.
9. **Tagger-validity tension: resolved, no contradiction** (the +0.56/+0.60 wolf/SK figures and the
   retracted +0.556 town figure are different quantities). *Status:* moot; the tagger is retired and out
   of the write-up.
10. **`v6_sp_ab`: wolf scope overstated.** The deceiver arm was the serial killer; the wolf was excluded.
    *Status:* holds. The direct wolf A/B will not run.

**Residuals from the July pass:**
- 🔧 retrieval fallback pooling → **fixed**.
- ✅ `batch_dedup.py` swallow-all-exceptions → fixed 2026-06-28.
- 🔧 dead toggles `arm` and `frozen_base_rates` → still unwired.
- ⏳ uncalibrated: application judge (⏸), day-summary judge, dedup quality scores → still uncalibrated;
  none gates anything now.
- ⏳ direct wolf strategy-point/observation A/B never run → will not run.

*Ledger rewritten 2026-10-23 from the spokes, their records and the working tree of that date. The
spokes own the marks; the design folders own the verdicts.*
