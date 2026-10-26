# Evaluation exhibits: source map

Every exhibit planned for the Evaluation pages: the page and level it belongs to, its form, the evidence
it is built from, and its state. Built exhibit files (images, JSON exports, table files) go in this
folder, named after the row's id. An exhibit is drafted only from the source listed, never re-derived;
a number in the source that has been corrected since is taken from the correction.

Forms, as in the project exhibit menu ([`../../eval_exhibits.md`](../../eval_exhibits.md)): **content**
(a table, quote or number written into the page), **diagram**, **export** (an interactive piece fed by a
script-generated JSON, stamped with the commit), **link** (a replay on the live site).

States: **drafted** (in the page draft), **planned** (in the page brief, not built), **optional** (the
brief allows it if it clarifies).

Paths are from the repository root.

## Level 1: [Evaluation](../evaluation.md)

| Id | Exhibit | Form | Source | State |
|---|---|---|---|---|
| L1-challenges | What makes the evaluation difficult: five challenges, each with an example and the section that handles it | content | `evidence/evaluation/report.md`, "Why evaluating an LLM system is different" | drafted |
| L1-diagram | Scope (turn → day → game, the day dashed "designed; not implemented") separated from scoring, with validation (pending for the current game) and controls alongside; no costs | diagram | `evidence/evaluation/report.md`, the method diagram and calibration chain; `evidence/evaluation/evaluation_scopes/report.md` | planned |

## Level 2 and 3 pages

| Id | Page (level) | Exhibit | Form | Source | State |
|---|---|---|---|---|---|
| FE-quote-pair | [Finding and fixing factual errors](../factual_errors/factual_errors.md) (2) | The investigator's night-3 result as played and as reworded | content | `evidence/gameplay/discussion_evidence.md` §6.2 | drafted |
| FE-four-versions | same (2) | Four versions × 20 replies: inventing a check vs reporting the real one, with the caption on the two changes at once | content | same §6.2; `evidence/evaluation/factual_errors/experiment_log.md` §5 | drafted |
| FE-replay-link | same (2) | The game's replay on the live site (game `832404e9`) | link | the served game; confirm it is served | optional |
| FE-propagation | same (2) | Input → day summary → player: how one error becomes later players' input | diagram | `evidence/evaluation/factual_errors/report.md`, steps 1 and 3 | optional |
| FE-cause-fix | same (2) | Causes beside the fix that worked: missing input, misleading wording, reasoning slips | content | `evidence/evaluation/factual_errors/report.md`, step 3; `evidence/gameplay/report.md`, problem 1 | drafted |
| PM-worked-score | [Measuring play quality beyond win rate](../play_metrics/play_metrics.md) (2) | One vote or protection graded by the rules, against the true roles | content | `evidence/evaluation/metrics/report.md` §2 | planned |
| PM-contrast | same (2) | Lynch hits (+0.65, 50 games → +0.49, 78 games) beside healer saves (+0.36 → −0.03, 75 games, 95% interval −0.26 to +0.20), nine → ten players; associations, not effects | content | `evidence/evaluation/metrics/report.md` §3–4 | planned |
| PM-transfer | [Which play metrics transferred](../play_metrics/metric_transfer.md) (3) | The within-batch and memory-off checks, rare-role samples and intervals | content | `evidence/evaluation/metrics/report.md` §4; its experiment log | planned |
| CC-field-values | [Checking agent outputs with code](../code_checks/code_checks.md) (2) | A model-written field beside the value code recomputed from the game state | content | `evidence/evaluation/deterministic_audits/report.md`, case 3 | planned |
| CC-oracle | same (2) | A small view of the deduction oracle's possible deals | diagram | `evidence/evaluation/deterministic_audits/report.md`, case 2 | optional |
| CC-audit-table | [The field audit](../code_checks/field_audit.md) (3) | Each field with its own threshold and baseline: bucketed players alive 99% against 90%; swing vote 61% against 80% and the 83% always-no baseline; bullets left outside the rule | content | `evidence/evaluation/deterministic_audits/experiment_log.md`, "The rule set before the run fired" (corrected thresholds) | drafted |
| LJ-rubric | [Designing and validating LLM judges](../llm_judges/llm_judges.md) (2) | A rubric excerpt beside what it actually rewarded | content | `evidence/evaluation/llm_judge/report.md`, case 5; `llm_judge/extraction.md`, `llm_judge/day_summary.md` | planned |
| LJ-flat-scores | same (2) | Scores that sat at the top and did not move across versions | content | same, case 5 | planned |
| RL-packet | [Building reference labels](../reference_labels/reference_labels.md) (2) | A readable example review packet, version names hidden | content | `evidence/evaluation/labeling/sampled_reads/report.md` §2 | planned |
| RL-panel-flow | same (2) | Panel agreement → review → corrected labels | diagram | `evidence/evaluation/labeling/report.md`, case 2 | planned |
| RL-confusion | same (2) | A small confusion table with denominators, where the source supports one | content | `evidence/evaluation/labeling/report.md`; `labeling/dedup.md` | optional |
| RL-panel-review | [When three models agreed on the wrong label](../reference_labels/model_panel_review.md) (3) | 619 unanimous and 244 split; what was reviewed (617 records) and what was trusted (246 unanimous keeps); a discard majority wrong 37%, a keep majority 7%, 21% of unanimous discards flipped | content | `evidence/evaluation/labeling/report.md`, case 2 | planned |
| RG-held-fixed | [Choosing between turn replays and whole games](../replays_and_games/replays_and_games.md) (2) | What each scope holds fixed and what it lets unfold, the day scope visibly unbuilt | diagram | `evidence/evaluation/evaluation_scopes/report.md` | planned |
| FC-record | [Designing fair comparisons](../fair_comparisons/fair_comparisons.md) (2) | An annotated experiment record: matched inputs, the intended change, configuration, measurement; a fingerprint records facts, a guard enforces a rule | content | `evidence/evaluation/experimental_controls/report.md`; `evidence/tracing/fingerprinting/report.md` | planned |
| FC-transition | [What the paired baseline reanalysis changed](../fair_comparisons/paired_baseline.md) (3) | The 20 shared deals: town won both 5, first run only 7, second run only 2, neither 6 (exact McNemar p = 0.18), beside the independent reading (1 of 10 against 20 of 30) | content | `evaluation/experiments/june_baseline_shift_check.py` (output); `evidence/evaluation/experimental_controls/report.md` | planned |
| MA-flow | [Evaluating models before switching](../model_admission/model_admission.md) (2) | Question → check → finding → decision, integration failures kept apart from quality | content | `evidence/evaluation/model_admission/report.md` §1–2 | planned |

## Related entries in the project exhibit menu

The menu ([`../../eval_exhibits.md`](../../eval_exhibits.md)) spans the whole project, memory included.
Entries whose subject matches an Evaluation page, to check before building that page's exhibits:

| Menu entry | Page |
|---|---|
| 1. Replaying the turns that went wrong, instead of playing new games | Choosing between turn replays and whole games |
| 5. Checking the judge against a human read | Designing and validating LLM judges |
| 6. Where an error starts versus where it spreads | Finding and fixing factual errors (FE-propagation) |
| 8. A pre-registered negative result, and a scope condition found afterwards | Designing fair comparisons (method only; the result belongs to Memory) |
| 14. Checking a model-written field against the engine's own count | Checking agent outputs with code |

Entry 13's "30 → 52 of 96" conflicts with the v8 log (52 against 36, three changes bundled); check it
before any use.
