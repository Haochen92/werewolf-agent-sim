# Assessment: memory pipeline A (extraction, credit, discussion_tagger, caching)

## Summary table

| Folder / document | Editorial condition | Structural recommendation | Main issue | Proposed action |
|---|---|---|---|---|
| `extraction/post_game/report.md` | light edit | keep | §4 repeats the halo finding in coefficients and contradicts selection §4 on the winning side | Cut §4's halo subsection to a pointer to selection §4; fix the §6 memory bullet and the cost figure |
| `extraction/selection/report.md` | matches | keep | None in the report (it is the style guide's plain-presentation exemplar) | None |
| `extraction/selection/outcome_halo_case_study.md` | light edit | keep | Its 2026-10-14 note quotes the 482-observation fit as if it were the 1,472-observation result | Rewrite the closing note to match report §4 |
| `extraction/situation_summary/report.md` | light edit | keep | Its stage-filter numbers conflict with situation_dimensions §5 | Give the stage-filter result one home, with one set of numbers |
| `extraction/situation_dimensions/report.md` | light edit | keep | §4 repeats situation_summary §4; §5's stage-filter paragraph conflicts with it | Replace §4's query paragraph with a pointer; reconcile §5 |
| `extraction/situation_dimensions/` side documents (README, build spec, v6 store, two sub-logs) | historical; README light edit | keep | README calls the June build spec "finalized" and uses "Phase B" | Mark the spec and the v6 store record as historical in the README |
| `extraction/day_summary/report.md` | light edit | relocate (low priority) | "66 summaries" in §4 does not match the run described in §6; it is not a memory-pipeline component | Fix the §4 count; consider moving next to the information-fidelity work |
| `extraction/tell_extraction/report.md` | matches | keep | Overlaps `store_curation/tells.md` on the fold | None beyond a cross-link check |
| `credit/report.md` | matches | keep | §4's tell paragraph repeats the tell report | Optional: trim §4's tell paragraph to two sentences |
| `credit/read_tactic_credit_redesign.md` | light edit | keep | Editorial bookkeeping on the page (§8, header); calls nine-seat code "current" (§3) | Delete the bookkeeping sentences; date the §3 "legacy scorer" sentence |
| `credit/blindspot_fix/experiment_log.md` (+ `step1_validation.md`, replay `.md`s) | log; constraint violation | keep | Cites the retracted "+17/+33pp; reranked p=0.013" as a result (§④c, §⑥, §⑦) | Add an in-place correction note at each citation that points to the static-memory correction |
| `discussion_tagger/report.md` | rewrite | relocate to `credit/discussion_tagger/` | Describes a credit mode the code retired on 2026-07-13 as "how it works today" | Rewrite as a short decision record ending in the retirement; add a 07-13 entry to the log |
| `caching/report.md` | light edit | keep | Stale since 2026-10-15 (site default, the post-game report's status, the retry change); the production schema mode lives in a database row the code seed contradicts | Update §3.5, §6 and the links; state where the catalogue's truth lives |

## Per folder

### extraction/post_game
- **Documents:** `report.md` (~3,370 words, authoritative); `experiment_log.md` (~2,530, the journey, authoritative history); `flash_extraction_5games.txt`, `pro_reextraction_playerid_fix.txt` (run notes, historical); data subfolders `eval_sets/`, `eval_configs/`, `eval_results/`, `model_comparison/` (listed only).
- **Reader question:** How does a finished game become stored observations, and how do we know they are usable?
- **Scope and primary sources:** observation format, the offline per-role-and-phase job, Claude batching, quality checks (seat-id count, fact reads, halo, May judge), cost, and the May per-role case study. Evidence: v8 log 2026-10-11..13, `model_comparison/`, May `eval_results/`.
- **Condition, with justification:** The report is approach-first with an orientation line, §1 defines observation and lesson before use, and §5 is verdict-first. Three passages need edits. (1) §4 "The verdict follows who won (the halo)" states the finding as fitted weights (+0.74/+0.33, +0.50/+0.29), which goes against plain-presentation habit 3. It also says de-halo worked "on one side only… the winning side's positives barely moved", then that the 1,472-observation repeat "was the same". Selection §4, on those 1,472 observations, reports that de-halo halved the praise for winners' bad moves (18% to 9%). (2) §4 Cost gives the Gemini 19-game run as $10.42; caching §4.1 gives the same run as $10.33. (3) §6 bullet 1, "the nine-seat test leaned negative", does not name the test. It should name the July town-only endpoint (p≈.06), because the June paired A/B was positive for town.
- **Suspected stale mechanisms:** none found. Checked: `DEFAULT_PRO_MODEL = "anthropic/claude-sonnet-5-5"` (`Agents/llm_factory/accessors.py:49`); `scripts/extract_batch.py --model` default `claude-sonnet-5-5`; warm-up call then `batch_parse(..., cache_ttl="1h", schema_in_prompt=True)` and a second batch for retries (`Agents/memory/extraction/offline.py:229-238`); `tick learn --extracted` (`Agents/memory/consolidation/tick.py`); served `retrieval_types_config` strategy points only (`server/game/run_config.py:40`).
- **Overlap:** §4 halo with selection §4 (selection is the home). §3 "How the job runs on Claude" and §4 Cost overrun with caching §3.6/§4.6 (caching owns cache writes and the overrun; post_game needs one sentence each). The §4 May judge passage overlaps `evaluation/llm_judge/extraction.md`.
- **Proposed action:** Replace §4's halo subsection with two sentences and a link to selection §4. Pick one cost figure for the Gemini run, or say the two figures were measured differently. Name the test in §6 bullet 1.

### extraction/selection
- **Documents:** `report.md` (~3,010, authoritative); `experiment_log.md` (~1,820, journey, authoritative history); `outcome_halo_case_study.md` (~1,140, historical exhibit, still the only known-intent case); `netverdict_calibration.py` and `outcome_halo_human_game.json` (frozen records).
- **Reader question:** Does the extraction model's verdict grade the move or the result, and what does the pipeline do about it?
- **Scope and primary sources:** the verdict, the halo measurement (1,472 observations, 40 games), de-halo, the rule-based grade beside the verdict, and the June selection test. Evidence: `evaluation/experiments/v8_verdict_halo.py`, `memory_system/v8/data/halo/`, v8 decisions §13.
- **Condition, with justification:** The report matches the exemplars. It asks the question plainly, uses counts in a 2×2 table, keeps a separate "how sure we are" list, and §6 states what is not established with the exact missing evidence. The case study needs a light edit. Its "What happened since (note added 2026-10-14)" combines two fits. It gives the 1,472-observation coefficients (+0.80/+0.40), then "negatives fell from 53% to 27%, the winning side's positives barely moved", which are the 482-observation figures from the log's 2026-10-13 entry. On the winning side this contradicts report §4. The log's halo table is in coefficients, which is acceptable in a log.
- **Suspected stale mechanisms:** none found. Checked: `DehaloConfig` defaults to enabled on `claude-haiku-5-5` (`Agents/memory/persistence/config.py:66-78`); `synth_outcome: str = "verdict"` (`Agents/memory/consolidation/config.py:50`), passed to `_format_cluster` (`store_ops.py:289`); the "OUTCOME IS NOT CREDIT" rule (`Agents/prompts/extraction/cell.py:46`); the grading, tagging and store scripts exist.
- **Overlap:** post_game §4 (see above); credit §2 shares the grading table (credit is its home; selection links to it correctly).
- **Proposed action:** Rewrite the case study's closing note in three sentences, using report §4's counts or simply pointing to report §4.

### extraction/situation_summary
- **Documents:** `report.md` (~3,830, authoritative); `experiment_log.md` (~2,410, journey); data `staging/`, `outputs/` (holds `retrieval_golden_labels.json`, which reranker training reads), `model_comparison/`, `prompt_versions/`.
- **Reader question:** How does a seat turn its live situation into a memory search, and how good are the searches?
- **Scope and primary sources:** the situation call, when it runs (gating and reuse), how it is built, the 96-query read, the stage-filter replays, and the May labelled ranking test (case study). Evidence: v8 log 2026-10-12/13, `evaluation/experiments/v8_gate_lookups.py`, `v8_stage_filter_replay.py`, `outputs/`.
- **Condition, with justification:** Approach-first, with a real example in §2 and the NDCG score defined in a box before use. The §6 case study is verdict-first and its limits are specific. One light edit: §5 "What helped was a retrieval change" says fit rose "from 15% to 24–27%" and lookups with a fitting lesson "from 36 to 52 of the 96". situation_dimensions §5 says "to 25%" and "52 of 96 against 41 without the filter". The two baselines (36 against 41) cannot both be right for the same comparison.
- **Suspected stale mechanisms:** none found. Checked: the day-1 and town-day skips (`Agents/memory/retrieval/plan_gating.py:78,85`); fetch 5 (`pipeline.py:85`) and keep 3 (`accessors.py` `top_k=3`, `RETRIEVAL_KEEP_PER_SITUATION`); `DEFAULT_STAGE_FILTER = False` (`Agents/config/run.py:63`); served strategy points only (`server/game/run_config.py:40`).
- **Overlap:** §4 "Numbers are computed, not estimated" and §5 "Why the numbers are computed" with situation_dimensions §4–5. The July number audit is also deterministic_audits Case 3 (fine as a pointer). The stage-filter result appears in both reports.
- **Proposed action:** Keep the stage-filter result here, where the 96-query read lives, with one set of numbers checked against the v8 log. situation_dimensions should then link to it.

### extraction/situation_dimensions
- **Documents:** `report.md` (~4,730, authoritative); `experiment_log.md` (~2,690, journey that condenses the rest); `README.md` (~90, folder map); `dimension_schema_build_spec.md` (~2,920, historical: the 2026-06-15 design, "NO code written, pending sign-off"); `v6_full_store.md` (~745, historical: the June store build and its seat-id defect, superseded by `ten_seat_v2`); `criticality_screen/experiment_log.md` (~1,900, historical; corrections kept in place under ⚠ headings); `dimension_accuracy_audit/experiment_log.md` (~2,960, authoritative record of the July fill audit, cited by deterministic_audits Case 3).
- **Reader question:** What fields describe a situation on lessons and queries, and how far can their values and their use in ranking be trusted?
- **Scope and primary sources:** the field set and cells, the stakes arithmetic, who reads the fields, the value audits, three ranking tests, and the gating case study. Evidence: `dimension_accuracy_audit/`, `criticality_screen/`, `v7_final/plan.md` (G3), the v8 stage-filter replay.
- **Condition, with justification:** The report is clearly organised. §1 states the rules, §3's table shows each field's embedding and query-side status, and §6 is an honest negative finding ("no benefit measured, not proven useless"). It is long because §4 "How a query is built" repeats situation_summary §4 almost line for line (computed facts, overwrite, fallback). §5 "Dropping lessons from another stage" conflicts with situation_summary §5 (see above). §5 also correctly withdraws the old "new query beat old" claim. The README is accurate as a map but calls the build spec "finalized" and uses the internal label "Phase B".
- **Suspected stale mechanisms:** none found. Checked: `STAGE_FILTER_TOP_K = 50` and the tilt in `Agents/memory/retrieval/dimension_gating.py`; stage filter off by default (`Agents/config/run.py:63,99`); the stakes formula's source file `Agents/rules/board_clocks.py` exists.
- **Overlap:** situation_summary §4–5 (query build, stage filter); deterministic_audits Case 3 (fill audit; this folder holds the record); post_game §1 example (shared fields, no conflict).
- **Proposed action:** Replace report §4's first paragraph with a link to situation_summary §4, keeping the "what reads the fields" table. Replace §5's stage-filter bullet with one sentence and a link. Mark the build spec and the v6 store record as historical in the README and drop "Phase B".

### extraction/day_summary
- **Documents:** `report.md` (~3,390, authoritative); `experiment_log.md` (~2,520, journey); May data (`eval_results*.jsonl`, `eval_summary*.txt`, `regen_comparison.json`, `prompt_versions/`, historical).
- **Reader question:** How does a past day reach later prompts, and what stops a summary error from spreading?
- **Scope and primary sources:** the two-list summary, the three-block "Previous days" section, the claim ledger, rescue and fallback, the bench and replay checks, and the `e06` case. Evidence: `game_play_enhancement/discussion_evidence.md` §6.4–6.6 and §8.4; `reasoning_failures/` §3 and its data.
- **Condition, with justification:** Strong reference shape: §3 shows the actual prompt block, §4 states the governing rule (the model transcribes, code checks), and §7 is verdict-first. Light edits: (1) §4 says "In a test of 66 summaries, all 27 checks it wrote were judged wrong (§6)". §6 describes 6 days × 5 samples × 2 models (60 summaries, "18 of 30" each), so the count needs reconciling. (2) §1 lists "the tagger, which labels what each player did" among readers without saying which tagger. The discussion tagger of this area is a nine-seat diagnostic, so the reference is ambiguous. (3) §8 bullet 1 says the ledger takes "accusations" from the summary, while §3 says accusations go to the prompt directly, not through the ledger.
- **Suspected stale mechanisms:** none found. Checked: `DEFAULT_SUMMARY_TIMEOUT_S = 90.0` and `get_llm_summary_fallback` (`Agents/llm_factory/accessors.py:40,166`); Claude Haiku 5.5's catalogue row has no rescue model (`Agents/llm_factory/catalog.py:66-72`).
- **Overlap:** discussion_evidence §6, §8 (where it was built; this report is the reference); factual_errors Step 3 table (summary-claim row).
- **Proposed action:** Fix the three passages. Structurally, the summary is in-game context compression, not memory extraction (it sits here because its prompt file is in `Agents/prompts/extraction/`). Moving the folder next to the information-fidelity work is a reasonable, low-priority relocation.

### extraction/tell_extraction
- **Documents:** `report.md` (~2,990, authoritative; research-only component); `experiment_log.md` (~2,630, journey); `outputs/`, `scripts/`, `prompt_versions/` (frozen records).
- **Reader question:** How were behavioural tells discovered and measured without letting hindsight set the counts, and what do they show?
- **Scope and primary sources:** miner, role-blind detector and code join; the book; the fold; the checks (detector accuracy on 40 cases, the 60-game association table, the 40-vote replay); and the growing-vocabulary case study.
- **Condition, with justification:** Matches. It opens with why discovery cannot be the measurement, defines the score with a worked example, gives every result its sample, and §3 says plainly that the hook renders nothing in the ten-seat game and why. §6 states the gameplay gap precisely: tells were bundled with lessons in the one full test.
- **Suspected stale mechanisms:** none found. Checked: `WW_TELL_BOOK` is read only in `Agents/memory/tell_book.py` and set only by the loop driver (`evaluation/src/loop/driver.py:319`) and tests; `LoopConfig.tells = False` (`evaluation/src/loop/config.py:157`).
- **Overlap:** credit §4 (summary of tells); `credit/read_tactic_credit_redesign.md` §3 (method, from the design side); `store_curation/tells.md` (the fold); caching §4.7 (detector caching; both link correctly).
- **Proposed action:** none required.

### credit
- **Documents:** `report.md` (~4,200, authoritative); `read_tactic_credit_redesign.md` (~2,700, decision record, historical but still explains the current split); `attribution_spot_check.json` (data); `blindspot_fix/experiment_log.md` (~4,000, CLOSED July log plus an October addendum, historical); `blindspot_fix/step1_validation.md` (generated table, data); `blindspot_fix/replay*/checkpoint_replay_*.md` (generated summaries, data). There is no top-level log; the ten-seat build path is in v8 decisions §12–14. A separate credit log is not needed.
- **Reader question:** How does memory decide which lessons to keep without an AI judge, and how do we know the scores mean anything?
- **Scope and primary sources:** the ten-seat grading table, the lift-and-shrink score, prune/protect/evict, the belief/action split, three checks (attribution 13 of 15, split-half repeatability on 31 lessons, unit tests), the 20-game demonstration, and the abstain blind-spot case. Evidence: `consolidation/` code, `attribution_spot_check.json`, `store_curation/strategy_points.md` §6, `blindspot_fix/`.
- **Condition, with justification:** The report matches. §1 rules out the two obvious signals before giving the design, §2's tables are read from code, §5 states each check's sample and what it does not show (for example "the true mismatch rate could be as high as about 36%"), and §6 is a clear case with its limits. The design record needs a light edit. Its header ("Editorial review: October 13, 2026") and §8 ("The earlier 'v1 not yet built' status no longer describes that outcome") are repository bookkeeping. §3's "The current legacy scorer does not implement a per-strategy `risk_policy` exception" uses "current" for the frozen nine-seat loop. The blind-spot log is a log, dense with shorthand (SP, obs, v6ab, gen-4, epoch). It cites the retracted static-memory figure as a result in three places: §④c "the June static-obs result (+17/+33pp)", §⑥ "(+17/+33pp; reranked p=0.013 …) is real but EPOCH-STAMPED", and §⑦ "The June +17/+33pp result".
- **Suspected stale mechanisms:** none found in `report.md`. Checked: `prune_tau = -0.15`, `prune_min_follow = 8`, `protect_min_follow = 2`, `evict_min_retrieved = 8`, `synth_track_min_follow = 5` (`Agents/memory/consolidation/config.py:27-48`); `sp_lift` = (pos − neg)/follow − base, shrunk by follow/(follow+5), unscored when the base is None (`credit.py:408-417`); human-seat games dropped in `_iter_game_records` (`credit_rules.py:37-44`); `_spoke` gate present.
- **Overlap:** credit §4 with tell_extraction (short, acceptable); read_tactic §1 with discussion_tagger; credit §2 grading table shared with selection §3 (credit is the home).
- **Proposed action:** Add a dated correction line at each "+17/+33pp" citation in the blind-spot log that points to the static-memory correction, without editing the history away. Delete the two bookkeeping sentences in the design record and date its §3 "legacy scorer" sentence. Optionally trim credit §4's tell paragraph to two sentences and a link.

### discussion_tagger
- **Documents:** `report.md` (~2,710, superseded as a description of current behaviour); `experiment_log.md` (~5,330, journey to 2026-07-04, historical; it never records the retirement).
- **Reader question:** Can an LLM judge score day discussion for memory credit where no deterministic rule can, and what became of it?
- **Scope and primary sources:** two failed deterministic attempts, the post-mortem, the tagger design, the v2-run retraction (+0.556) and the validation (partial r +0.56 wolf / +0.60 SK / +0.02 town, N=24), and the hardening. Evidence: `v7_final/experiment_log.md` §11–12, `v7_final/runs/v2_full/` scripts, `evaluation/llm_judge/discussion_tagger.md`.
- **Condition, with justification:** Rewrite. The report describes a design the code no longer has. It calls itself "how it works today" and "the current shipped mechanism", says the credit step invokes the tagger, gives `discussion_mode = "tagger"` as the default, and says its night verdict "overrides" deterministic night credit. The code says the tagger credit mode "was RETIRED 2026-07-13 (owner ruling)… never feeds prune" (`evaluation/src/loop/credit.py:17-18`; same in the `config.py` comment above `discussion_credit`), and `LoopConfig` has no `discussion_mode` field. It also uses terms before defining them: de-luck, halo, floor, pre-A4, v6ab epoch, SP, L1/L2. Its gap table carries severity grades, which the style guide reserves for a risk register. Its Verification section repeats `evaluation/llm_judge/discussion_tagger.md`. The underlying findings are sound and worth keeping: the post-mortem on deterministic proxies, and the +0.556/+0.56 retraction.
- **Suspected stale mechanisms:** yes, throughout. `report.md` "Orientation", "The mechanism / model", "Config / defaults" and the signal-inventory "Consumer" column all describe the retired credit wiring. Line anchors such as `credit.py:73-84`, `credit.py:102-106`, `credit.py:124-128` and `config.py:108-118` no longer point at tagger code. Checked `evaluation/src/loop/credit.py` and `evaluation/src/loop/config.py:146-151`.
- **Overlap:** `evaluation/llm_judge/discussion_tagger.md` (trust and validation, same numbers); `credit/read_tactic_credit_redesign.md` §1 and §7 (the replacement decision); `metrics/report.md` §5 and §7.
- **Proposed action:** Rewrite as a short decision or negative-finding record. Cover the gap (discussion had no credit signal), why the deterministic proxies failed for deceivers, the tagger and its validated metric, the retracted number, and the 2026-07-13 retirement in favour of the deterministic rules, with the tagger kept as a post-hoc diagnostic. Leave trust detail to the llm_judge document, and add a closing 07-13 entry to the log. Relocate the folder to `credit/discussion_tagger/`, since it was a credit-signal intervention.

### caching
- **Documents:** `report.md` (~5,000, authoritative, reviewed 2026-10-14); `experiment_log.md` (~7,730, journey through 2026-10-14 §16); `scripts/` (frozen June probes).
- **Reader question:** Where does the pipeline pay for repeated input, how does each provider's cache behave, and what did caching actually save?
- **Scope and primary sources:** the shared-prefix layout for turns and lookups, Claude marks, OpenAI breakpoints, the schema-mode trade-off, extraction caching and batching, the tell detector, and cost accounting. Evidence: `batch_results/cache_ab_2026_10_13/`, `evaluation/experiments/game_cache_share.py`, admission results, the hallucination bench run.
- **Condition, with justification:** Light edit. The opening states the two clearest results with their scope. §2 explains provider behaviour before using it, §3.3 shows the walk-back mechanism with a worked two-turn example, and §4.3–4.4 give N with each result ("two games per arm… cannot size Haiku's small differences"). Stale or inconsistent passages: (1) §6 bullet 1, "the Gemini players, including the site's default": the default has been Claude Haiku 5.5 since 2026-10-15. (2) The evidence links call the post-game report a "historical extraction report… an earlier pipeline version", but it was revised 2026-10-22 and describes the current job. (3) §3.5 says unenforced failures cost "one retry". Log §16 records that the retry is now enforced, and that 74 schema breaks and copied verdicts appeared in 20 games; the report omits both. (4) §4.1 gives $10.33 for the 19-game Gemini run; post_game says $10.42.
- **Suspected stale mechanisms:** §3.5 "Since 2026-10-14, Luna and Haiku use the unenforced schema in production". The seeded catalogue in code sets `structured_mode="json_schema"` (enforced) for both (`Agents/llm_factory/catalog.py:61,68`). Log §15 says the switch was made in the model catalogue, which is loaded from the database (`catalog.py:124`). The claim may be true of production, but a reader checking the code sees the opposite, so the report should say where the truth lives. Checked and current: `prompt_cache_breakpoint` (`providers/openai_compat.py:65,76`); `cache_control` marks (`providers/anthropic.py:59-76`); Claude offline jobs forced to `json_mode` (`accessors.py:_offline_mode`); the layout boundary (`Agents/prompts/layout.py:7,37`).
- **Overlap:** post_game §3/§4 (Claude batch, overrun: caching is the home for cache writes); tell_extraction §4 last paragraph (caching §4.7 is the home).
- **Proposed action:** Update §3.5 (the enforced retry, the 20-game break rate, and where the schema mode is set), §6 bullet 1 and the post-game link. Reconcile the Gemini cost with post_game. Re-stamp the review date.

## Area-level structure

**Overlaps to resolve, with one home each:**
- *The outcome halo:* selection §4 is the home. post_game §4 and the case study's closing note should point to it and must not restate different numbers.
- *Query construction and the stage filter:* situation_summary owns the call and the stage-filter result. situation_dimensions owns the fields, their trust, and the gating case.
- *Claude batching and cache-write overrun:* caching §3.6/§4.6 is the home; post_game keeps one sentence.
- *Tells:* tell_extraction is the home; credit §4, the design record and caching §4.7 summarise and link.
- *Discussion-tagger validation:* `evaluation/llm_judge/discussion_tagger.md` is the home; the tagger report should not repeat it.

**Grouping.** The area does not need to become one folder. If it were grouped, its purpose would be: how the agents' memory writes, describes, retrieves and scores its records. The layout would be:
- `extraction/post_game` (write)
- `extraction/selection` (verdict quality)
- `extraction/situation_dimensions` (the shared description)
- `extraction/situation_summary` (read-side query)
- `credit/` (scoring), with `credit/blindspot_fix/` and `credit/discussion_tagger/` (the retired judge)
- `extraction/tell_extraction` (research-only belief channel)

**Placement unclear, and why:**
- `extraction/day_summary`: an in-game context step read by every prompt, not a memory component. It sits here only because of where its prompt file lives.
- `extraction/tell_extraction`: "extraction" in mechanism but a scoring and belief channel in purpose. It belongs equally with credit (the design record) or `store_curation/tells.md`. Leave it in place unless the area is regrouped.
- `situation_dimensions/criticality_screen/` and the gating screen: retrieval-ranking experiments that could sit with the reranking evidence. They test the fields' use, so they can stay.
- `caching/`: a cross-cutting cost lever (game turns, extraction, tell detector). It should stay top-level, not inside extraction.

**What I would not move:**
- `situation_summary/outputs/retrieval_golden_labels.json`, which reranker training reads (the report says "do not move").
- `dimension_accuracy_audit/`, cited by deterministic_audits Case 3 and the graduated runner.
- Frozen artifacts: `outcome_halo_human_game.json`, `netverdict_calibration.py`, `caching/scripts/`, `tell_extraction/scripts/`.
- The historical side documents in situation_dimensions: the log condenses them, and they are dated records of the June design.

**Constraint checks:**
- The retracted "+17/+33pp; reranked p=0.013" appears as a result in `credit/blindspot_fix/experiment_log.md` §④c, §⑥ and §⑦.
- `extraction/post_game/model_comparison/v7_refresh/README.md:36` asserts "flash-lite drifts ~daily" as established. It should be phrased as suspected provider drift.
- No 0.14% rate appears.
- v8 is described everywhere as "not tested at scale", never as negative.
- The v7 town result is described consistently as negative-leaning (p≈.06).
