# Assessment: memory pipeline B (dedup, retrieval, store_curation)

## Summary table

| Folder / document | Editorial condition | Structural recommendation | Main issue | Proposed action |
|---|---|---|---|---|
| `dedup/report.md` | rewrite | keep (absorb `batch_architecture.md`, `README.md`) | The June body describes the live design, then a gap table and an October paragraph overrule it. Where online dedup runs, the thresholds and "zero-error" are all stated wrongly in the body | Rewrite as one present-tense reference doc (gate → prefilter → KEEP/DISCARD judge; fold triage-only; merge path off); move the 12-row gap table to the log |
| `dedup/experiment_log.md` | matches (journey overview) | keep | Sound spine; its opening still says the story "ends in a deliberate freeze" and leaves the October state to §10 | Light touch only: one orientation sentence pointing to §10 |
| `dedup/README.md` | — (index) | merge into report / delete | Duplicates the n=39 table and the log index; "83–85% accuracy" conflicts with the report's "~80%/83%" | Fold its one useful table into the report's evidence section; delete |
| `dedup/batch_architecture.md` | rewrite (if kept) | merge into `dedup/report.md` | Describes "two-pass" as a second pass over survivors; the code's two-pass is flash-lite triage → pro verify of MERGEs | Merge its rationale bullets into the report's batch section; drop the rest |
| `dedup/incremental_convergence.md` | historical | merge into `batch_dedup/experiment_log.md` | A diagnosis fragment that continues batch_dedup's idempotency test; banner already says Fix 2 shipped | Append as a dated entry after the idempotency test |
| `dedup/dedup_clustering_and_sp_extraction_plan.md` | historical | keep, mark historical | June plan that produced the gate and cluster-based SP synthesis; reads as a live plan | Add a one-line "historical: built as the gate (dedup §9) and v7 synthesis" header |
| `dedup/{batch_dedup,per_extraction,embedding_prefilter,store_retrieval_impact}/` | no report (not warranted) | keep as sub-logs | Each carries a June and an October "current live state" block, report-genre material inside logs | Leave the blocks as dated addenda; the folder report is the only present-tense home |
| `dedup/golden_eval/` | no report (not warranted) | relocate into `embedding_prefilter/data/` | One JSON (65-case embedding cache) whose only consumer is the prefilter calibration | Move the file; update the one artifact-table pointer |
| `retrieval/filtering/report.md` | rewrite | merge into a new `retrieval/report.md` | "The Solution" presents a configuration that never shipped; its headline example is contradicted by its own run 1 (the addendum says so); first-person blog voice; n=5 | Rewrite as one case in a merged retrieval report, approach-first, stating it is off by default |
| `retrieval/reranking/report.md` | rewrite | merge into `retrieval/report.md` | "Final Pipeline Configuration" never ran in the served game; n=5 stated as "doubled efficiency"; stale model and code refs | Same merge; state the result as a direction on 5 cases |
| `retrieval/capacity_limits/report.md` | light edit | merge into `retrieval/report.md` | The Decision section says top_k moved to 5, and the addendum says it never reached the prompt; the addendum's last sentence is now stale (comment fixed) | Restate the decision as "fetch widened, cap stayed 3"; drop the comment sentence |
| `retrieval/context_eval/` (log only, ~9.4k words) | missing report (not warranted here) | relocate to `evaluation/labeling/` | A labelling-methodology design whose findings (topical over-crediting, ~80% inter-judge ceiling) are about judges, not retrieval; `labeling/` already cites its §6 as its protocol | Move folder; make sure `labeling/report.md` states the two findings it relies on |
| `retrieval/per_day_discussion/` (log only) | missing report (not warranted) | keep; add addendum | Log says the variant "has not been built". Per-day lookup reuse with a refresh on any new role claim shipped 2026-10-12 (v8 D4) | Add a dated addendum pointing to `memory_system/v8/decisions.md` §10; cover cadence in the merged retrieval report |
| `store_curation/report.md` | rewrite | keep; trim dedup overlap | Describes the v7 loop (`evaluation/src/loop/`) in present tense. The live tick is `Agents/memory/consolidation/` (credit pass split from learning tick); the tell fold is not in it. §6 is a review agenda; status lines carry suite counts and an uncommitted branch | Rewrite to today's tick with v7 as history; move §6 agenda and suite/branch status to the log |
| `store_curation/experiment_log.md` | matches (review-and-ruling log) | keep | Dated, honest, entry per ruling | None |
| `store_curation/{observations,strategy_points,tells,knobs}.md` | light edit (obs, SP, knobs); historical (tells) | keep | All pinned to `evaluation/src/loop/` and "suite 684/690, uncommitted"; tells describe a v7-only fold | Repoint code anchors to `Agents/memory/consolidation/`; header tells.md "v7 loop only; the live game injects a fixed book" (verify first) |

## Per folder

### dedup/
- **Documents:** `report.md` (~2,400 words, authoritative but partly stale); `experiment_log.md` (~2,700, authoritative journey overview); `README.md` (~400, superseded index); `batch_architecture.md` (~1,150, reference doc, partly stale); `incremental_convergence.md` (~1,050, historical diagnosis); `dedup_clustering_and_sp_extraction_plan.md` (~970, historical plan). Sub-logs: `batch_dedup/` (~5,700), `per_extraction/` (~4,400 + `tricky_cases.md` ~2,500 historical labelling record + two superseded prompt drafts), `embedding_prefilter/` (~2,700), `store_retrieval_impact/` (~2,100 + two raw judge dumps, 29k words). `golden_eval/` holds one JSON.
- **Reader question:** How does the memory store keep near-duplicate lessons out today, and how good is each layer at telling a duplicate from a distinct lesson?
- **Scope and primary sources:** online per-entry dedup, the deterministic gate, the embedding prefilter, the batch (offline) pass with clustering, MERGE and freeze-old. Evidence: the 65-case and 111-key golden sets (per_extraction, batch_dedup), the 232-case cross-game set and the October re-embedding (`embedding_prefilter/data/cross_game_sims_by_embedder.json`), the n=5 → n=39 retrieval-impact study.
- **Condition, with justification:** rewrite. The report was a good reference doc in June. It has since become three eras stacked: the body (June), gap rows #1–8 (June audit), rows #9–12 and "Current live state, revisited" (October). A reader must cross-check the body against the gap table to learn what runs. Four body claims are overruled later in the same file:
  - "Zero-error similarity thresholds" and the constants table are overruled by gap #10 and by the prefilter log's October finding, where the May observation counts do not reproduce and the Qwen strategy-point line fails on the 232 cases.
  - "Two-pass is recommended" is overruled by gap #9: the merge path is off.
  - The online pipeline running in `post_game_analysis` is overruled by the October paragraph.

  The gap table also carries severity labels, which the style guide keeps out of reader-facing reports, and a stray blank line between rows 8 and 9 splits it into two tables. Terms such as `gate_key`, pair-checks and "v9d ordering" are used before they are explained. The Verification section says "store dedup improves retrieval when conservative (n=39)". The folder's own table shows relevance 4.51 → 4.44 with efficiency and unique lessons up and no test of significance. So the result is a trade, not an improvement; `batch_architecture.md` repeats it as "without losing relevance".
- **Suspected stale mechanisms:**
  - `report.md` § "The online pipeline": "Runs in `post_game_analysis` (`Agents/nodes/orchestrator.py`) after each game when `dump_enabled=True`". `post_game_analysis` (orchestrator.py:534) now only saves the extraction input. Dedup runs in `write_extracted_store` (`Agents/memory/extraction/offline.py:337`, calling `run_downstream_observation_dedup`).
  - `report.md` § "The embedding pre-filter" table (0.93/0.81/0.96/0.935) and "calibrated on a 65-case golden set + 232-case cross-game set". `Agents/memory/deduplication/config.py` now reads the per-model table in `Agents/llm_factory/embeddings.py:49–73`; on Qwen the values are 0.72/0.94 (observations) and 0.61/0.88 (strategy points), set on the 65 cases only.
  - `report.md` config table: `dump_enabled` "persistence/config.py:89" is now line 114; "Covered by `tests/test_batch_dedup.py`" is now `tests/memory/test_batch_dedup.py` (also in `batch_architecture.md` § "How it's verified").
  - `batch_architecture.md` § "Two knobs": "two-pass (`config.two_pass`, off by default): a second LLM pass over the survivors to catch duplicates the first pass missed across cluster boundaries". `TwoPassConfig` (`Agents/memory/batch_deduplication/config.py:43–61`) is triage → verify of MERGE-flagged entries, with `skip_verify` for triage-only. The fold uses `skip_verify=True` (`Agents/memory/consolidation/obs_fold.py:71`).
  - `batch_dedup/experiment_log.md` June block cites the loop at `evaluation/src/loop/consolidate.py`. The live fold is `Agents/memory/consolidation/` (the file still exists in `evaluation/src/loop/` for v7).
  - Checked and current: the gate key and pair-checks (`Agents/memory/dedup_gate.py:36–54, 139`), `_frozen_old_conflict` (`operations.py:146`), `cluster_mode="bounded"` and `gate_enabled=True` (`batch_deduplication/config.py:86, 92`), `IncrementalDedupConfig.enabled=False` (`persistence/config.py:52`).
- **Overlap:** the dedup report and `store_curation/observations.md` §4–5 and `strategy_points.md` §3 both describe observation admission (freeze-old, triage-only) and SP KEEP/DISCARD dedup. Note `store_retrieval_impact/` § "Filtering on a Clean Store" overlaps `retrieval/filtering` and `retrieval/reranking` § "Why filter + rerank over-corrects". `evaluation/labeling/dedup.md` covers the golden-set scorer as an instrument; the deterministic_audits exemplar cites it (89%, 99 of 111).
- **Proposed action:** rewrite `report.md` approach-first as the dedup reference:
  1. what counts as a duplicate;
  2. the layered stack as it runs in the ten-seat store build (gate → prefilter → KEEP/DISCARD judge; fold triage-only; SP dedup KEEP/DISCARD);
  3. evidence per layer with its N and the set it was measured on;
  4. the built-but-off merge path and why it is off (fabrication on about a third of merges);
  5. what is unmeasured (no non-Gemini judge on either golden set; Qwen thresholds rest on 65 cases).

  Move the gap table and the June/October overlays to the log (§10 already exists). Fold `README.md` and `batch_architecture.md`'s rationale into it. Merge `incremental_convergence.md` into `batch_dedup/experiment_log.md`.

### retrieval/filtering, retrieval/reranking, retrieval/capacity_limits
- **Documents:** `filtering/report.md` (~1,900, historical; its headline config never shipped) + four run dumps (76k words, raw); `reranking/report.md` (~1,100, historical recommendation) + two run dumps (24k, raw); `capacity_limits/report.md` (~570, historical decision; addendum says it never took effect) + configs/results.
- **Reader question:** After the vector search, what happens to the retrieved lessons before they reach the prompt, and what did testing each optional stage (filter, rerank, wider fetch) show?
- **Scope and primary sources:**
  - Filtering: cosine dedup, MMR λ=0.8 and the cap of 3, on 5 frozen cases from the v4 store, gemini-2.5-flash judge.
  - Reranking: LLM re-scoring on the clean and dirty v4 stores, same 5 cases.
  - Capacity: cap 3/5/7 on 120 frozen adoption cases.
  - Primary sources are the run dumps and `capacity_limits/eval_results/*.jsonl`.
- **Condition, with justification:**
  - filtering: rewrite. "The Solution" and "Results" present the end-of-study configuration as the design. The addendum then says it is off for every role and in the served game. The *Threshold tuning* example (0.85 removed an opposing healer pair) is contradicted by run 1, which kept that pair, and the addendum asks the reader to reread it as a hypothesis. A reader cannot tell what was measured from what was believed without the addendum. The voice ("I implemented", "The biggest insight") is portfolio copy, and the "What I Learned" lessons are stated more strongly than 5 scenarios support.
  - reranking: rewrite. On 5 cases, "doubled efficiency (1.80 → 3.60) and halved redundancy" is a magnitude claim. "Final Pipeline Configuration" reads as shipped, and the addendum says it is not. "Uses gemini-3.1-flash-lite — the same model the agents use" is no longer true (players run on Haiku), and "Essentially free" has no measurement behind it.
  - capacity_limits: light edit. The approach is clear and the n is stated. The Decision paragraph ("moves from 3 to 5… consistent with no downside… risk… is low") overstates +0.07 / +0.15 on n=120 with no test. The addendum reverses the decision's effect, so the Decision should state the outcome rather than leave the reader to reconcile it.
- **Suspected stale mechanisms:**
  - filtering "Code References" (`Agents/retrieval_filters.py`, `Agents/memory.py`, `Agents/agents.py`) and reranking "Code References" (`Agents/reranker.py`, `eval_configs/`) point at files that no longer exist. The addenda give the current paths (`Agents/memory/retrieval/filters.py`, `rerank_agent.py`), and I confirmed those exist.
  - filtering pipeline diagram "Retrieve (wide, 10/situation)". `RERANK_TOP_K = 10` is used only on the wide path. The default fetch is 5, and `STAGE_FILTER_TOP_K = 50` when the stage filter is on (`Agents/memory/retrieval/pipeline.py:84–85`, `dimension_gating.py:82`).
  - capacity_limits addendum: "The comment above the fetch in `pipeline.py` that calls 5 a 'cap' is misleading". The comment at `pipeline.py:79–81` now says the cap of 3 still applies, so the sentence is stale.
  - Checked and current: `RETRIEVAL_KEEP_PER_SITUATION = 3` (`accessors.py:16`), MMR `lambda_=0.8` (`filters.py:38`), `RERANK_KEEP = 3`.
- **Overlap:** the three reports share one harness and one pipeline. Reranking § "Why filter + rerank over-corrects" re-argues the filtering-on-clean-store finding owned by `dedup/store_retrieval_impact/`. Filtering § "What I Learned" (content-coverage gap) is also argued in dedup/experiment_log §5 and dedup/report "What dedup can't do". Reranking's addendum points to `fine_tuning/cross_encoder/` (the trained replacement, not wired) and `memory_system/effectiveness/` (the reranked arm).
- **Proposed action:** write one `retrieval/report.md` as a reference doc.
  1. The read path today: situation call → search at width 5 → cap 3 per situation, strategy points only in the served game, lookup reused within a day or night per D4.
  2. One case per optional stage (filter, rerank, wider fetch): approach, result with "5 scenarios, one judge" beside each number, and what shipped.
  3. A short "what is not measured" section.

  Turn the three current reports into dated entries of a `retrieval/experiment_log.md`, or keep them as historical records under their subfolders. Leave the run dumps in place.

### retrieval/context_eval
- **Documents:** `experiment_log.md` (~9,400 words, design spec for a deferred labelling program plus May diagnostics; historical/deferred). It also holds `labels/` (JSON) and `scripts/` (frozen study code).
- **Reader question:** Can a cheap model label memory relevance well enough to train and evaluate a reranker, and what ground truth does each retrieval question need?
- **Scope and primary sources:** a 1,848-item drift diagnostic (query-only vs context labels), a 400-item CoT follow-up, a v4 reranker re-score under strict labels (n=13 → n=25), and the two-gold opposite-blinding design. Sources: `labels/drift_report.json`, `cot_report.json`, `reeval_v4_clean_{obs,sp}.json`.
- **Condition, with justification:** missing report, and none is warranted in `retrieval/`. The material is a judge- and label-validity study. Its findings are the strong judges' ~80% binary agreement ceiling, topical over-crediting (93% of disagreements), and flash-lite with context at 77%; none of them concerns how retrieval works. The log opens with two banners that conflict: "EXECUTION DEFERRED (2026-06-01)", then a "READING GUIDE (2026-05-31)" that says to start at the Forward Plan. The Forward Plan's §7 "Status" (2026-05-31) predates its own §5 update (2026-06-01). A reader cannot tell which plan is current without the memory note that execution stays deferred.
- **Suspected stale mechanisms:** none checked in code. This is a design log, and its substrate (`v4_deduped_v2`, day-only, four roles) is stated as superseded in its own banner.
- **Overlap:** `evaluation/labeling/plan.md` and `labeling/experiment_log.md` cite this log's §6 as the protocol spec; `fine_tuning/cross_encoder/reranker/experiment_log.md` holds the reranker label set this diagnoses.
- **Proposed action:** relocate the folder to `evaluation/labeling/context_eval/`, and fix the three inbound links. Replace the two opening banners with one dated status line ("deferred since 2026-06-01; §6 protocol is reused by labeling/"). Check that `labeling/report.md` states the over-crediting and ceiling findings with their N.

### retrieval/per_day_discussion
- **Documents:** `experiment_log.md` (~3,600 words, journey log; its status section is superseded), plus a frozen script and a JSON.
- **Reader question:** Should a seat retrieve its discussion lessons once per day rather than every turn, and does the per-turn churn reflect real adaptation?
- **Scope and primary sources:** a $0 recompute over 19 cells of existing retrieval traces (`data/within_day_retrieval_diversity.json`). It finds within-day sets differ on 91–100% of multi-turn agent-days and that churn is weakly tied to the query.
- **Condition, with justification:** missing report, and none is warranted. The log is well built: it states its instrument, its falsified branch is kept in place (§3.3), and its limits are stated in §3.5c and §5. But §1 ("Every one of those turns runs the full memory-retrieval pipeline") and §5 ("parked as a config-flag candidate… not built") are now false. The project shipped per-day reuse for discussion, per-night reuse, and a refresh on a new role claim (`Agents/memory/retrieval/lookup_cache.py`; `memory_system/v8/decisions.md` §10, 2026-10-12). It shipped as the default, not behind a flag, and without the paired A/B the log said a design change needs. The log's §1 also says "top 3 memories after reranking", but reranking is off by default.
- **Suspected stale mechanisms:** as above; checked `lookup_cache.py` docstring and `pipeline.py:68–76`.
- **Overlap:** `memory_system/v8/decisions.md` §10 and `plan.md` D4 own the shipped decision.
- **Proposed action:** append a dated addendum. Per-day reuse shipped in v8 D4 as a cost decision with a claim-triggered refresh. The semantic-equivalence read (§5 step 1) and the A/B were not run. Name the cadence in the merged retrieval report.

### store_curation/
- **Documents:** `report.md` (~6,850 words, framework doc; authoritative for v7, partly stale for today); `experiment_log.md` (~2,400, review-and-ruling log, historical record); `observations.md` (~2,600), `strategy_points.md` (~3,000), `tells.md` (~3,700) per-store mechanism docs (v7-era; obs/SP mechanisms largely graduated, tells v7-only); `knobs.md` (~1,850, knob provenance ledger; values still current, file of record moved).
- **Reader question:** How do the stored lessons enter, survive and leave each store, and what stops each store from growing without bound or keeping harmful entries?
- **Scope and primary sources:** observation decay, SP synthesis/credit/prune/evict and the exploration slot, the tell ledger/fold/book; the 11-row pathology table (§5) drawn from v7 runs and reviews; `heldout_credit_reproduction` (Pearson +0.54, n=31) for `prune_tau`; the 30-game tell ledger simulation.
- **Condition, with justification:** rewrite. Five problems:
  - The opening runs a 12-term glossary and two navigation blocks before any mechanism. Its thesis ("compounding mechanically *is* this curation") presents compounding as the frame. v7 compounding closed negative; §5 notes the runs are invalid for the thesis, but the framing never says so up front.
  - The whole document describes "the loop" in generations, with code anchors in `evaluation/src/loop/` (§2.1 table, §3, Sources).
  - The "About this document" status line ("Suite 684 green… uncommitted, `feature-dimension-schema`") is repo bookkeeping, not a reader fact.
  - §6 is the 2026-07-14 walkthrough agenda with frozen numbering and RESOLVED stamps, which is log genre. Its "still open" items (§6.2, §6.4, §6.5) are pre-run v7 items whose status today is not stated.
  - §5 "Not yet verified: no fold has run inside a live generation loop" may be stale; I did not check it.

  The per-store docs are clearer, but each carries the same v7 anchors and suite-count status.
- **Suspected stale mechanisms:**
  - §2.1 table "Code anchors" and Sources: `evaluation/src/loop/consolidate.py`, `merge.py`. The live SP/observation tick is `Agents/memory/consolidation/tick.py`, with `store_ops.py` and `obs_fold.py`. It is split into a credit pass (prune and evict, no model call, every memory-on game) and a learning tick (fold, decay, synthesis, dedup, every N games). The tick "never prunes or evicts" (tick.py docstring, lines 1–11).
  - Two passages describe one tick doing all the steps: §5 row 4 ("prune runs last, on post-dedup counts") and `strategy_points.md` §1 ("The tick — four steps, order load-bearing"). In the live code, prune and evict are in a separate pass.
  - Glossary "cluster… above cosine 0.70". Synthesis clustering now reads `synth_cluster` per embedding model: 0.65 on gemini-embedding-2 and 0.46 on Qwen (`Agents/llm_factory/embeddings.py:57, 71`; `store_ops.py:189`).
  - Tells: the fold, credit and mining remain in `evaluation/src/loop/` (`tell_fold.py`, `tell_credit.py`, `tells.py`) and are not part of the live tick. A tell book is still read by live prompts (`Agents/prompts/day_discuss.py`, `day_vote.py`, `night.py` import `tell_book`). The report's lifecycle ("a fresh book… injected at the start of every game" after each fold) therefore describes the v7 loop, not the served game. Verify which book the served game loads before rewriting.
  - Checked and current: `prune_tau=-0.15`, `prune_min_follow=8`, `protect_min_follow=2`, `synth_cell_unproven_cap=12`, `synth_every_k_gens=2`, `sp_dedup=True`, `obs_fold_dedup=True` (`Agents/memory/consolidation/config.py:23–53`).
- **Overlap:** The admission row of §2.2, `observations.md` §4–5 and `strategy_points.md` §3 re-describe dedup (freeze-old, triage-only, batch dedup as repair, incremental non-convergence in §5 row 10). They should point to `dedup/report.md` instead. The credit layer is in `credit/report.md`, the SP design lineage in `v7_final/consolidation_design.md`, and the tell build journey in `extraction/tell_extraction/`. The v8 rulings on SP dedup and merged-duplicate credit are in `memory_system/v8/decisions.md` §14, which this folder never cites.
- **Proposed action:** rewrite `report.md` as the present-tense reference for today's two passes (credit pass and learning tick) over observations and strategy points. Add a short section placing the v7 loop and the tell fold as the design they graduated from. Keep the §5 pathology table, since it is the strongest material, and add which guards survived graduation. Move §6 and every suite-count or branch status line to the log. In the per-store docs, update code anchors only, and header `tells.md` as v7-loop scope.

## Area-level structure

**Overlaps across folders.**
1. Observation and SP admission are described in both `dedup/` and `store_curation/` (observations.md §4–5, strategy_points.md §3, report §2.2 and §5 row 10). Dedup should own the mechanism, and store_curation should reference it in one line per store.
2. The "filtering does not stack on a clean store" finding is argued in `dedup/store_retrieval_impact/`, `retrieval/reranking/` and `retrieval/filtering/`'s addendum. Its one home should be the merged retrieval report, citing the dedup sub-log as the measurement.
3. "Strategy points are a coverage gap, not a duplication gap" appears in dedup/report, dedup/experiment_log §5, store_retrieval_impact and filtering. Argue it once in the retrieval report and point back from dedup.
4. Retrieval cadence (per_day_discussion) is decided in `memory_system/v8/decisions.md` §10. The retrieval report should state it, and the log should point to it.

**Recommended grouping.** Keep three folders, each tied to one intervention: dedup = keeping duplicates out of the store; store_curation = the store lifecycle (growth, removal, bounding); retrieval = the read path. Inside `retrieval/`, merge the three short reports into one `retrieval/report.md`; they test stages of one pipeline on one harness. If the owner wants one grouped folder, its purpose would be "how lessons are written into, kept in, and read back out of the memory store". The layout would be `evidence/memory_store/{curation, dedup, retrieval}/`, with `curation/report.md` as the hub that links the other two. I would not do this move before the rewrites; the rewrites fix the reader's problem and the move does not.

**Do not move.** The four dedup sub-logs and their data, `per_extraction/tricky_cases.md` (the labelling record behind the decision rules), the retrieval run dumps, `store_curation/experiment_log.md`, and `knobs.md`.

**Placement unclear.**
- `retrieval/context_eval/`: labelling methodology, not retrieval. Recommend `evaluation/labeling/`.
- `dedup/dedup_clustering_and_sp_extraction_plan.md`: half gate design (dedup), half cluster-based SP synthesis (store_curation / v7_final). Keep in dedup as historical, linked from log §9 and from `strategy_points.md` §2.
- `dedup/store_retrieval_impact/`: measures a dedup intervention with the retrieval harness, and also tests retrieval filtering. It stays in dedup; the retrieval report cites its filtering phase.
- `retrieval/per_day_discussion/`: the shipped decision lives in `memory_system/v8/`. The pre-test stays in retrieval as the record of why per-turn churn was judged mostly noise.
- `store_curation/tells.md`: the tell fold is v7-loop machinery that did not graduate into the live tick. It may belong with `extraction/tell_extraction/` or `credit/`. Decide after checking which book the served game loads.

**Constraint check.** No instance of the retracted "+17pp p=0.013", a 0.14% rate, "v8 negative" or asserted provider drift appears anywhere in the area. The only constraint-adjacent issue is store_curation's opening framing of compounding (above).
