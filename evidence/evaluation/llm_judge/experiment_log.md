# LLM judges: the detailed record

*Created 2026-10-23 from the previous `report.md`. Sections 1–6 are the memory-pipeline account written
2026-06-30 (nine-seat games, Gemini judges), kept as written with their dated corrections; sections 7–10
were added 2026-10-23. The current account is [report.md](report.md); section numbers below are the
old report's, which other records may cite.*

## 1. What the judge layer is, and what it decided

One judge grades every memory component. It is a single model, configured in one place, that scores each output in a fixed structure and retries once if parsing fails. It records its exact configuration with every run so two results can be compared fairly. Each component is judged against the standard it was built to meet, rather than against whatever the judge model happens to prefer. (How those standards are set is section 3.)

The fair test of whether this layer earned its place is simple: what did a judge actually decide? A judge whose scores changed no decision did nothing. Going through the record, the answer is modest.

- **Two design calls were judge-driven, and both rest on little data from the old pipeline.** A judge's scores were the deciding input in exactly two places: which model to use for extraction (compared on 5–10 games), and locking version 2 of the application prompt (120 cases, judge-scored only). Both were settled in May, on the pre-v7 pipeline, and neither was re-run on the current version. Real influence, thin evidence, and stale.
- **One finding mattered without settling anything.** The deduplication quality judge found that the merge-writing model invents game details on about a third of its merges (3 of 9 cases). Batch deduplication is already off by default for a plainer reason: it is expensive, so it runs as an occasional offline sweep rather than after every game. The fabrication finding is the reason that sweep will not be switched to run automatically until a safeguard is added.
- **Three calls were made without the judge, because the judge was too weak to make them.** The situation-summary design was settled by a human-labelled answer key, which dropped one prompt option (worth −0.08) and kept another (worth +0.06). Retrieval depth, how many notes to pull, was settled by a downstream outcome measure. The day-summary format was a design choice, because later code needs structured fields, and its model was picked by reading real summaries and weighing speed. The component itself was left on the pre-v6 situation framework — last and optional in the v6 migration — so whether its summaries carry enough for the newer dimensional consumers is untested; the hard facts it might drop (the vote tally, eliminations, revealed roles) are backstopped by a deterministic game-master channel, leaving only argumentative context at risk. The judge's scores were statistically flat across the prompt versions, and where they did separate the models, they pointed at the slow one that latency ruled out.

The pattern is the point. These judges are good at detecting problems but poor at ranking near-equal options, so the decisions that needed a reliable ranking went to better-anchored instruments, and the judges did the cheaper work of flagging faults.

On that flagging: the judges have no agency of their own. A person reading their output, noticing inconsistent scores or a dimension stuck at one value, is what caught the bugs since fixed. Two were in the extraction judge's own prompt: one applied a rule to the wrong field and deflated scores by 1.19; another, once fixed, raised a score by 0.69. One was a retrieval shortcut that inflated a score when too few notes were retrieved. One was an engagement number, later retracted from about 0.70 to 0.55. It had read high because an instruction buried in a structured-output field was being ignored: the model silently skipped about a third of the notes, and the skipped ones were disproportionately the inapplicable ones. Moving that instruction into the visible prompt body made it score every note, and the true rate came out lower.

The honest limit is that none of the live judges is calibrated. Each is one model scoring another, with no human-checked answer key behind the numbers, so they are best read as smoke alarms rather than gauges. The larger wins of the eval system (the head-to-head verdict that memory helps, and two configuration bugs the harness caught) come from other layers and are covered in the [parent report](../report.md).

- *Correction (2026-10-23).* "None of the live judges is calibrated" is true of these memory judges. It is not true of every judge in the project: §7 lists the ones with a human check. "The head-to-head verdict that memory helps" overstates the record:
  - The June A/B improved the town's decisions. Healer saves went from 37% to 60% (p=0.005) and town lynches on an enemy from 47% to 64% (p=0.028). The town win rate rose from 27% to 43%, which was not significant (p=0.27). The often-quoted p=0.013 belongs to the reranked arm's +33 points, not to the raw arm.
  - On the v6 store the town gain did not repeat (+6 points, p=0.77) (`memory_system/report.md`).
  - The pre-registered v7 endpoint test (2026-07-20, 30 paired boards) put the town's decision score 0.147 lower with memory (p≈0.06).
  - The owner closed the memory research on 2026-07-21 (`memory_system/v7/execution_plan/report.md`).

One more limit is worth stating plainly, because it is easy to miss: none of this reached the current version. The two judge-driven calls, and the situation-summary golden set that outranked the judge, all ran on the pre-v7 pipeline (v4-era stores, May prompts). The choices that survive into v7, per-role extraction and the 2.5 Pro extractor, were validated back then and carried forward, not re-judged. v7's genuinely new parts, the dimensional memory schema and the credit-aware synthesised strategy notes, have no LLM-judge score at all. On v7 specifically, the LLM-judge layer drove no design decision; what stands behind v7 is the outcome and deterministic instruments described in the [parent report](../report.md).

- *(2026-10-23.)* The ten-seat memory (v8, October 2026) uses none of these six judges. Its model checks are different: the de-halo pass, the decision tagger, the point-dedup judge and the tell detector, each rated in §7. v8 has run once as a demonstration and has not been tested at scale.

## 2. The harness

All six judges share one harness, so every component is scored the same way and any comparison is fair. Each choice below is a deliberate tradeoff, not incidental plumbing.

- **One model, chosen in one place.** The judge model is set centrally (in `judges/config.py`; default Gemini 2.5 Pro) rather than hard-coded in each judge, so a comparison can pin it in a single spot.
- **Each judge's model is matched to its rubric.** The stronger model, Gemini 3.1 Pro, judges the two rubrics that are holistic quality calls: the situation-summary and the extraction model bake-off. The cheaper 2.5 Flash judges the two that are closer to a factual check: retrieval and application. The rest run on 2.5 Pro. The rule is to spend model capacity where the rubric needs judgment, and where a dimension is purely checkable, to compute it rather than pay a model to estimate it (section 5).
- **The judge is a different model from the one it grades.** A model tends to prefer its own output, so wherever it can be, the judge and the generator are different models. Across the live pipeline they are: the agent plays on Flash-lite and is judged by Flash or Pro, Flash-lite situation summaries are judged by 3.1 Pro, and 2.5 Pro extractions are judged by Flash or 3.1 Pro. The one exception is batch deduplication, where 2.5 Pro both writes the merges and scores their quality; that is acceptable only because the decision-grade signal for dedup is the deterministic scorer, not this LLM layer (section 5). One constraint bounds all of it: every model is a Gemini tier, chosen so that backend, pricing, and tokenizer stay comparable, so "a different model" means a different tier rather than a different vendor.
- **The model is held fixed on both sides of a comparison.** As long as the same judge scores both options in a head-to-head, which the run log records, the model cancels out and the score gap still reflects the design change. The cost is that scores do not transfer across components or read as absolute levels: a 4.2 from Pro is not a 4.2 from Flash.
- **A failed score is dropped, not guessed.** Each judge asks for its scores as structured JSON, validates them against a fixed schema, and retries once. If that still fails it returns nothing, and the row is left out of the average. Silently dropping the row is a small risk, noted in section 6.
- **The configuration is recorded, not locked.** The model backend (Google AI or Vertex, which shift scores even at temperature 0) is read from the environment, but stamped into each run's record and checked to be constant within a run. Drift between runs is therefore detected rather than prevented, and a person still confirms the backend matches before comparing two runs.

*Correction (2026-10-23).* The models named above are the ones the recorded runs used. The code has changed since:
- **Every judge's default is now Claude Haiku 5.5.** The setting is `DEFAULT_JUDGE_MODEL = "anthropic/claude-haiku-5-5"` (`evaluation/src/judges/config.py:15`, with the comment "owner 2026-10-12: every judge on Haiku 5.5 for now (Gemini is retiring)"). The judges that set their own default were moved to Haiku 5.5 too: situation summary, golden expectation and the census reader.
- **The players' default is the same model** (`DEFAULT_GAME_MODEL`, `Agents/llm_factory/accessors.py:24`), and so are the in-game gates (`get_llm_judge` builds on the game's own model, `accessors.py:180-185`). So "a different model from the one it grades" no longer holds by default. A run that judges current games with the default judge should say so, or pass a different `--model`. The 2026-10-16 summariser comparison, for example, judged on Sonnet 5.5 (§7).
- **Every model is no longer a Gemini tier.** Recorded scores from the Gemini judges cannot be compared with a re-run on Haiku. This spoke's rule from section 2 ("a 4.2 from Pro is not a 4.2 from Flash") applies across vendors as well.

## 3. How the rubric dimensions are chosen

The scoring dimensions are not invented separately for each judge. Two principles generate them.

**First, judge against the same standard the writer was given.** For the components that describe a game situation, the eval reuses the exact instructions the agent itself was written to follow. Two shared documents, one on how to describe a situation and one on how certain to be about who is what, are injected into both the generator's prompt and the judge's prompt. So the judge checks whether the output met the standard we set, not whether another model happens to like it. (The two documents are `SITUATION_STANDARDS` and `EPISTEMIC_STATUS_RULE` in `Agents/prompts/standards.py`.)

- The situation standard defines the descriptive dimensions (how much the village knows, how aligned it is, how exposed the agent is, what phase the game is in) plus a specificity test: used as a search query, would this description match only similar situations, or almost anything? That test is the source of the recurring specificity dimension, since a note is only useful if it can be retrieved at the right moment.
- The certainty rule defines a five-level scale, from "my own confirmed finding" down to "unknown", and forbids naming players by ID. It is the source of the epistemic and role-perspective dimensions. This is the pipeline's signature concern: in a hidden-role game, a note that leaks knowledge the role could not have is worse than no note at all.

**Second, for the remaining judges, work backward from what the consumer needs.** The day-summary, deduplication, and application judges use their own rubrics, and each dimension answers a single question: what must this component get right for whatever uses its output next? The day-summary rubric says this outright. It is scored on what "downstream consumers use for agent decisions, situation characterization, and post-game extraction", which is why it has a dimension for labelling the *type* of evidence behind each suspicion. Deduplication is scored on making the right keep-or-merge call and preserving information without inventing it. Application is scored on whether the agent actually used the notes it retrieved.

So the rubrics come from two clear sources, reusing the writer's standard or decomposing the consumer's needs, rather than from one master list or from ad-hoc choices.

## 4. The six judges at a glance

One rubric per component. The trust column uses five tags: ✅ validated, 🟡 partial, ⚠️ asserted but unverified, 🔴 weak or null, ⏸ designed but not run. Fuller detail is in the linked per-component notes.

| Judge | What it scores | Model | What it found | Trust |
|---|---|---|---|---|
| **Situation-summary** (pairwise + single-rubric) · [detail](agent_decision.md) | faithfulness, specificity, retrieval-usefulness, non-redundancy, role-perspective | 3.1 Pro (both modes) | drove no design call; a human-labelled key did (dropped a −0.08 option, kept a +0.06 one) | 🟡 an answer key exists but isn't wired to the live judge |
| **Retrieval** · [detail](agent_decision.md) | relevance, efficiency, redundancy of the retrieved notes | 2.5 Flash | the version actually shipping (plain similarity search, no reranking) is the least-measured | 🔴 uncalibrated, and inflates efficiency when few notes are returned (section 6) |
| **Application** · [detail](agent_decision.md) | action quality, use of strategy, grounding, adoption accuracy | 2.5 Flash | note adoption stays flat near 50% across prompt versions (the prompt changed accuracy, not volume); 120 cases from only 3 games, pre-v7 (v4 store, May prompts), one outlier swings it | ⏸ calibration designed, never run (section 6) |
| **Extraction** (8 dimensions) · [detail](extraction.md) | specificity, epistemic, grounding, coverage, diversity, perspective, strategy-depth, novelty | 2.5 Pro | two prompt bugs found by inspection and fixed; the original five dimensions cluster near 4.0 and barely discriminate; drove the extraction model choice (5–10 games) | 🟡 debugged, not calibrated; the newest synthesised notes are unjudged |
| **Dedup quality** · [detail](../labeling/dedup.md) | merge quality, information preservation, fabrication | 2.5 Pro | the merge-writing model it scores (also 2.5 Pro) invents details in 3 of 9 cases; a faster merge-writer (3.5 Flash) fabricates 0% but drops whole fields, so 2.5 Pro was chosen deliberately: losing fields was judged the worse defect than inventing them | 🟡 weak layer; dedup's strong instrument is the deterministic scorer, not this |
| **Day-summary** (5 dimensions) · [detail](day_summary.md) | completeness, accuracy, evidence-type, village-dynamics, epistemic | 2.5 Pro | the judge is shown the transcript, so the content dimensions move but the "is this section present" dimensions sit at the maximum; flat across versions | ⚠️ a smoke test, too weak to rank versions |

Two judges sit off this list: a turn-level pipeline judge used in the end-to-end runs, and per-role and pairwise variants of the extraction judge used for model ranking. A separate deterministic check, not a judge, found and fixed a player-ID leak in extraction (from 84% down to 0–3%); it is covered in [the extraction note](extraction.md).

*(2026-10-23.)* The "Model" column records the recorded runs; every default is now Haiku 5.5 (§2). One more memory-era judge sits off this list: the memory-adherence judge (`evaluation/src/loop/memory_adherence.py`). It is outcome-blind and labels, per retrieved note, whether the action followed it, on the decision-replay screen's side probes. I found no human check of it. All of these judges ran on nine-seat games.

## 5. Anchoring — deciding how much to trust a score

A judge's number is trustworthy only if it is anchored to something outside the judge. Without an anchor it can flag a problem but cannot reliably rank two options. There are three kinds of anchor, strongest first.

1. **A real outcome.** Does the dimension predict something that matters, such as winning the game or retrieving the right note? This is the strongest anchor, because an outcome cannot be wrong about what matters. It is why the game's outcome-based metrics, which track winning at a correlation around 0.6, are the most trusted numbers in the whole eval system.
2. **A human answer key.** How well does the judge agree with human labels on a sample? This is the fallback when there is no clean outcome, and it is what a golden set provides.
3. **A direct computation.** When the thing being measured is cheaply checkable, such as how many distinct notes were returned or whether a banned player-ID appears, compute it rather than ask a model to estimate it.

*(2026-10-23.)* The outcome-based metrics in item 1 were validated on the nine-seat game only (`../metrics/report.md`). Since July a fourth kind of check has been used often: **agreement with blind model readers.** Claude subagents label the same items without seeing the judge's answer (§7: the echo gate, the decision tagger, the tell detector). It catches a judge that disagrees with a stronger reader. It is weaker than item 2, because the readers themselves have not been checked against a human, except where §7 says so.

This turns "the score isn't anchored" from one complaint into five situations, and only the last is a real design failure:

| The dimension is… | The fix is… |
|---|---|
| cheaply checkable (player-ID leakage, distinct-note counts) | compute it directly; an LLM score here is a wasted opportunity |
| checkable in principle but hard to label (fabrication, whether a claim is grounded in the transcript) | an LLM judge is the best available proxy: a golden set is expensive and sometimes hard even to define, so an uncalibrated judge is a reasonable stand-in as long as you flag it as directional |
| subjective but consequential (specificity, strategy depth) | anchor to an outcome if possible, otherwise a human answer key |
| subjective with no outcome to tie to | a human answer key; this genuinely is not a counting problem |
| stuck at one value regardless of input | redesign or delete the dimension; no anchor fixes a gauge that never moves |

The deduplication fabrication check is the clearest case of the second row. Deciding whether a merged note introduced a fact that is not in the source entries is a genuine semantic judgment, not a lookup, and there is no obvious deterministic label to build. So an uncalibrated LLM judge earns its place there: the honest move is to read its number as directional and say so, not to pretend a computation was on offer.

The subjective extraction dimensions, novelty and strategy depth, sit in the same row: a person can rate them but there is no formula, so the extraction judge is legitimate proxy work there too. The difference is anchoring. Dedup pins its keep-or-merge *decision* to a human golden and lets only the fabrication content ride on the LLM; extraction has no golden beneath it at all, so its proxy is unchecked. That is why the two share a rubric quality but not a trust tag.

The way to tell an honestly subjective dimension from a badly designed one is whether it moves. A dimension that sits at the same value no matter how good or bad the input is measuring the format the prompt forces, not the quality. Four such failures recur across the judges.

- A dimension pinned near its maximum carries no information. Village-dynamics sits at 5.00, and extraction's original five dimensions cluster at 4.00.
- Saturation can be built in. When the judge is shown the ground truth, as the day-summary judge is shown the transcript, the dimensions that only check whether a section is present are forced high, and only the dimensions that compare content against the transcript actually vary.
- Generating and judging in one pass confounds the two. Where a harness both produces an output and scores it, a change in the score cannot be separated from a change in generation.
- Scoring on the outcome smuggles in a halo. A dimension conditioned on whether the side won measures the win, not the property it claims to measure.

## 6. Open gaps, and why each is open

In priority order. Current as of 2026-06-30.

1. **The application judge is uncalibrated, and calibrating it is both the highest-value fix and a cheap one.** The procedure is already designed: about 28 cases, labelled blind, checked for agreement within one point and for directional bias. Roughly half a day, no new code. It is unfinished not because it is hard, but because it calibrates a secondary judge. The headline result of the project, whether memory raises the win rate, needs no judge at all, so under a finish-and-freeze deadline this loses to shipping. (Calibrating the judges against human labels in general is a larger program, deferred until the memory work proves out. The one answer key built regardless is for deduplication, because dedup ships in every store.)
2. **The answer keys that exist are not connected to the live judges.** A graded retrieval key could calibrate the retrieval judge, and a trained reranker key sits offline. Both need re-labelling against the current store, which has not been done.
3. **The retrieval judge inflates one score when too few notes are retrieved.** It sets efficiency to the maximum and pools that into the average with no counter, which can bias one side of a comparison. The fix is about two lines, and it is flagged so a future run does not misread the number.
4. **The newest synthesised notes have no quality judge.** Whether a synthesised strategy note is *good* is hard to label directly, so its quality is anchored to the outcome instead (the credit signal from the LLM-free loop measure), which is the correct anchor but is currently underpowered. The extraction judge could add a cheap directional read on top, and simply has not been pointed there yet.

The cheapest improvement in every case is the same move: calibrate one judge, or connect one answer key that already exists. None of it needs new machinery.

*Status (2026-10-23).*
- **Gap 1** is still open: no record of the application calibration exists. It no longer gates anything. The memory research closed on 2026-07-21, and the write-up plan lists the memory-era judges as "not cited, not served; stated as uncalibrated" (`writeup/map.md`, "Evaluation hardening tasks").
- **Gap 3 is fixed.** The judge marks its fewer-than-two-notes shortcut with `is_fallback=True` (`evaluation/src/judges/retrieval.py:30`). The runner excludes those rows from every judged average and reports them as a count (`evaluation/src/cli_runner/regen_replay/both/retrieval.py:97-110`, test `tests/evaluation/test_retrieval_judge_fallback.py`).
- **Gaps 2 and 4** stand as written for the nine-seat stores.
- **The calibration now planned** is for the hallucination-bench judge first. The plan is one owner labelling session on 50–100 verdicts. The silence-calibration readers and the rule-error screen readers follow, but only if the write-up keeps their numbers. That plan is pending (`writeup/map.md`, task 1).

## 7. Which judges are checked against human labels (2026-10-23)

**Three judges have a recorded human check.** They are the census reader and bench reader, the golden-expectation judge (through its hand-written expectations), and the dedup decision model, which is scored against a human key. The tell detector had one game read by the owner. Every other judge is checked against blind model readers, against an outcome, or not at all.

"Human check" below means a person compared the judge's verdicts with their own reading on a recorded sample. "Model readers" means blind Claude subagents did the labelling. Every row's code default is now Haiku 5.5 unless the row says otherwise.

| Judge (code) | What it decides | Game · date | Checked against | Mark | Home |
|---|---|---|---|---|---|
| Census reader (`judges/role_fact_read.py`) | does a text unit contradict the fact sheet | nine-seat · July 2026 | **Human.** 23-case golden set used to choose the two-model cascade. The owner read all 90 public-message positives (68 genuine), 25 of 278 private-note positives (precision about 0.8) and 15 of 273 rejections (2–3 misses) on 2026-07-08 (`gameplay/turn_prompt/validation/hallucination_baseline.md`). Run then on Gemini flash-lite + 3.5-flash; I found no record of the golden re-run on Haiku 5.5. | 🟡 | [`factual_errors/`](../factual_errors/report.md) |
| Bench reader (same code, on bench cases) | bad samples per arm | nine-seat cases · 2026-10-03 | **Human:** 10 of 12 hand-checked verdicts upheld, plus 40 control cases for false alarms. Re-judging identical samples gave 65/151 and 67/151 bad notes, a measure of the judge's own noise (`discussion_evidence.md` §6.6). | 🟡 | [`factual_errors/`](../factual_errors/report.md) |
| Golden-expectation judge (`judges/golden_expectation.py`) | does a text break a hand-written expectation | nine- and ten-seat · October 2026 | **Human in part.** The expectation is written by a person. Verdicts used in §8.4–8.7 were "read by hand first", which caught a wrong expectation (§8.5 item 4) and one wrong judge call (§8.7). No agreement rate. | 🟡 | [`factual_errors/`](../factual_errors/report.md) |
| Dedup decision model (production dedup; scored by `audits/dedup_score.py`) | keep, discard or merge | nine-seat · May 2026 | **Human key:** 65 online and 111 batch golden keys. The keys calibrate the decision, not the quality judges. The scores predate v6 and today's Haiku default. | 🟡 | [`labeling/dedup.md`](../labeling/dedup.md) |
| Tell detector (`loop/tells.py`) | did a player show a listed public behaviour on a day | nine-seat · July 2026 | **Model readers + one human game.** 40 cases labelled by five Opus adjudicators: discussion 0.93 precision, 87% recall; votes 0.83 and 77%. The owner reviewed one game end to end, 7 of 8 detections upheld. The six-game owner benchmark "was relaxed, not completed" (`extraction/tell_extraction/experiment_log.md`). | 🟡 | [`labeling/`](../labeling/report.md) |
| Echo gate (production, `Agents/turn/echo_gate.py`) | does a sweep-turn line add nothing | ten-seat · 2026-10-18 | **Model readers:** four blind Sonnet subagents labelled 65 open-floor lines. The gate as shipped held 10 of 29 restatements and 0 of 36 worthwhile lines (§9). | 🟡 | here §9; readers in [`labeling/sampled_reads/`](../labeling/sampled_reads/report.md) |
| Opening filter (production, `Agents/turn/round_filter.py`) | which opening lines are claims, results or challenges | ten-seat · 2026-10-18 | **Model readers:** of the 7 lines it held before a fix, the same readers judged 6 worth hearing (`data/silence_calibration/README.md`). No later measure found. | ⚠️ | [`labeling/sampled_reads/`](../labeling/sampled_reads/report.md) |
| Decision tagger (`scripts/tag_observation_decisions.py`, Haiku 5.5) | which decision an observation is about | ten-seat · 2026-10-13 | **Model readers:** 98 of 102 agree with blind Sonnet readers (bar set at 90%), plus free checks against the record. | 🟡 | [`labeling/sampled_reads/`](../labeling/sampled_reads/report.md), the decision-tag read |
| De-halo pass (production, `Agents/memory/extraction/dehalo.py`, Haiku 5.5) | rewrite verdicts the record does not support | ten-seat · 2026-10-11 | **Deterministic grade:** the verdict's weight on the side winning fell from +0.74 to +0.50, against +0.33 for the grade (482 observations, 19 games). The model was chosen on one smoke game ("most precise judge", `Agents/memory/persistence/config.py:75`). No human labels. | ⚠️ | [`deterministic_audits/`](../deterministic_audits/experiment_log.md) §5d; comparison in `../model_admission/` |
| Point-dedup judge (v8 synthesis) | are two strategy points duplicates | ten-seat · October 2026 | **Model readers:** caught 16 of the readers' 65 duplicate groups on flash-lite in the dry run (`memory_system/v8/experiment_log.md`). | ⚠️ | [`labeling/`](../labeling/report.md) |
| Summariser comparison judge (`experiments/haiku_summary_compare.py`, Sonnet 5.5) | errors in day summaries that would mislead a reader | ten-seat · 2026-10-16 | **None.** One flaw was found by reading (the judge trusted a moderator line) and the run was redone without it (`gameplay/deduction/experiment_log.md` §3). | ⚠️ | `../model_admission/` |
| Discussion-evidence judge (`experiments/discussion_evidence.py judge`) | what a message rests on, whom it accuses, what it claims | nine-seat · 2026-10-03 to 07 | **None.** The planned owner hand-check was not done (§8). | ⚠️ | here §8 |
| Discussion tagger (`loop/discussion_tagger.py`) | per-day deceiver-skill verdict | nine-seat · July 2026 | **Outcome:** predicts win beyond the vote proxy (wolf +0.56, serial killer +0.60, N=24). Per-field accuracy uncalibrated. Retired from credit 2026-07-13; out of the write-up. | 🟡 (retired) | [`discussion_tagger.md`](discussion_tagger.md) |
| Memory-component judges (§4) + turn-pipeline + memory-adherence | memory component quality | nine-seat · May–July 2026 | **None.** The situation-summary golden is a retrieval key (about 20 human cases, the rest machine-added), not wired to the judge. | ⚠️ / ⏸ | here §1–6 |
| Blind packet readers (Claude subagents in replay screens and reads) | labels on replayed or sampled lines | both · July–October 2026 | **Mostly none.** The owner read behind some of them, for example the v8 gate relevance read. | see home | [`labeling/sampled_reads/`](../labeling/sampled_reads/report.md) |

**What the table shows.**
- The judges with a human check are the factual-error judges, which the write-up leans on most. Even there, the July check was on Gemini readers and nine-seat games, and the planned bench calibration is pending (§6 status).
- The October play-quality checks rest on blind model readers. That catches disagreement with a stronger model, but it cannot catch a bias both share.
- Since the judge, the players and the in-game gates all default to Haiku 5.5, a self-preference bias is now possible wherever a run keeps the default (§2 correction).

## 8. The discussion-evidence judge (2026-10-03 to 2026-10-07, nine-seat) — ⚠️

**What it is.** An LLM reads every agent message in the day discussion and records three things: what the message rests on, whom it accuses, and any role the speaker claims for itself. There are nine possible bases, and a message may have several: `own_night_result`, `role_claim`, `night_events`, `voting_record`, `speech_content`, `manner`, `turn_taking`, `reveal_timing` and `none`. It was built as the independent measure for the discussion redesign, because the in-game census labels come from the playing model (`../metrics/experiment_log.md` B5).

**How it works.**
- The judge sees the public facts as of that day and the day's transcript up to the message. The facts come from the same fact-sheet builder as the census reader (`role_fact_read.build_fact_sheet`).
- It never sees true roles, so knowing who is evil cannot colour the labels. Code joins the roles in afterwards to score accusation accuracy by basis and to spot fake claims.
- It runs at temperature 0 with structured output. It reads batch records, or website games through the public replay endpoint, where human seats stay in the transcript but are not judged.
- It writes `reads.jsonl`, `summary.json` and `review.md`. The review sheet has a "check:" line under each message for a person to mark the labels.
- Every recorded run used `gemini-2.5-pro` (the `summary.json` files in `gameplay/data/{baseline_smoke,live_baseline,live_v2,live_v2_game2}/` and `data/phase2_step8_games/judge/`). The code default is now Haiku 5.5 (§2).

**What it was used for.**
- Phase 1 baseline against the first v2 game: 3 games and 117 agent messages against 1 game and 30 (`discussion_evidence.md` §6.1).
- The Phase 2 step 8 games, with the v2 game re-read by the same judge so both sides match (`data/phase2_step8_games/README.md`).

**What it can claim.** The direction of label shares across a handful of games, when both sides are judged with the same rubric in the same run.

**What it cannot claim.**
- Sizes.
- **Results on ten-seat games.** The role join uses `EVIL = {"wolf", "serial_killer"}`, and the claimed-role field allows only the nine-seat roles (`discussion_evidence.py:47-57`). On a ten-seat game it would count no pack seat as evil and could not record a claim of a new role.
- **Stable shares across rubric versions.** Splitting one label ("participation") into turn taking and reveal timing moved another label on the same baseline messages from 74% to 63% (§6.1). Shares are comparable only within one run.

**How far it was checked.**
- **Repeatability on one game.** The step 8 re-read of game 832404e9 matched the 2026-10-03 read.
- **Agreement with the speakers' tags.** The speakers' own accusation tags agreed with the judge on 145 of 183 messages (79%) (§7.1). That check used the judge as the reference to trust the tags. It is not a check of the judge.
- **No human check.** The measurement plan named the owner's hand-check as "how far the judge's numbers can be trusted" (§4). Every "check:" line in the four review sheets is blank, and the record's open question "How reliable is the judge? It is unvalidated until the owner's hand-check" (§9) still stands.

**Code · record.** `evaluation/experiments/discussion_evidence.py` (`judge`; reused unchanged by `phase2_step8_counts.py --judge`) · `gameplay/discussion_evidence.md` §4–6, §7.1, §9; `data/{baseline_smoke,live_baseline,live_v2,live_v2_game2}/`, `data/phase2_step8_games/judge/`.

## 9. Echo-gate offline checks (2026-10-07, nine-seat material; recalibrated 2026-10-18, ten-seat) — 🟡

**What it is.** The echo gate is an LLM judge inside the live game. When a player who has not spoken gets the floor (a *sweep turn*), the gate reads the new line against the day's earlier lines. If the line adds nothing, it is held instead of published. It runs on the game's own model at low thinking (`Agents/turn/echo_gate.py`; `get_llm_judge`). It fails open: an error keeps the line. Two exemptions are deterministic and not left to the judge: a human seat, and a line answering a player who named the speaker. The offline check runs the gate over lines that already exist and writes every held line next to the line it was judged to repeat, for reading by hand.

**How it works.** `evaluation/experiments/line_echo_gate_check.py` judges each proactive line of a voting day against the lines said before it that day, the way the gate sees them live. It made one cheap call per line. It ran over two sources: the first 20 June voting days (146 lines) and the Phase 2 chunk-catalogue game (16 lines). An earlier check of the parallel round's filter (`data/round_echo_check/`) names a runner, `evaluation/experiments/round_echo_filter_check.py`, that is not in the repo. It was replaced by the line check when the round went sequential (`discussion_evidence.md` §7.4 step 4c).

**What it found about its own judge.** Three prompt versions were run on the same 146 June lines.

| Prompt | Held | What reading the holds showed |
|---|---|---|
| v1 (the parallel round's criterion) | 43 (29%) | lines that credit a speaker and then add to the point were held as repeats |
| v2 (criterion spelled out) | 39 (27%) | the wording alone changed little |
| v3 (states the line's point and what it adds before naming a repeat; code holds only on "adds nothing") | 27 (18%) | about half clear repeats; shipped |

In the four step 8 games, about 12 of the 19 holds in games 1, 2 and 4 were clear repeats. Once, the gate held an accused player's own defence because the accusations were untagged (`data/phase2_step8_games/report.md`).

**What it can claim.** What the gate would hold on given material, and what kinds of mistakes it makes. The finding that a small judge errs toward holding came from reading.

**What it cannot claim.**
- A live hold rate. The June lines had already passed the earlier novelty gate, so the rate understates (README).
- A precision. "About half" is one reading, not labels.

**The later calibration.** On 2026-10-18 the owner widened the gate's bar to hold restatements and filler, and the gate was measured against blind labels in the silence calibration. Four Sonnet subagents labelled 65 open-floor lines without knowing whether each was spoken, held or forced. At low thinking, the v3 bar held 12 of 29 restatements and 0 of 36 worthwhile lines. As ported into `echo_gate.py`, it held 10 of 29 and 0 of 36 (`data/silence_calibration/README.md`, step 4). Those labels come from model readers. Checking them against the owner is a pending hardening task, conditional on the write-up keeping the numbers (`writeup/map.md`, task 1(b)). The method and the readers belong to [`../labeling/sampled_reads/`](../labeling/sampled_reads/report.md).

**Code · record.** `Agents/turn/echo_gate.py`, `Agents/turn/round_filter.py`, `evaluation/experiments/line_echo_gate_check.py`, `evaluation/experiments/silence_calibration.py` (`gate_check`) · `gameplay/data/{line_echo_check,round_echo_check,silence_calibration}/`; `discussion_evidence.md` §7.4.

## 10. Two memory screens filed here that use no judge (June 2026, nine-seat)

The inventory filed the criticality screen and the forced-schema screen under this spoke. Neither scores with an LLM judge. Both are frozen-turn replays: a recorded town day-vote is regenerated under each arm and scored against the true roles with `score_vote` / `hit_threat` (`criticality_screen.py:222`, `forced_schema_screen.py:95-112`).
- The **criticality screen** (`evaluation/src/studies/criticality_screen.py`) compares retrieval ranked by plain similarity with retrieval that adds a term for how critical the board is. Record: `extraction/situation_dimensions/criticality_screen/`.
- The **forced-schema screen** (`evaluation/src/studies/forced_schema_screen.py`) makes the player give an applies / partly / does-not verdict on each retrieved note before voting. It crosses v5 and v6 stores with plain and forced schemas. Record: `memory_system/strategy_adoption/forced_schema_screen/`.

Its "engagement" figure is the player's own self-report, not a judge's. Its record holds the delivery finding behind §1's retracted engagement number. With the one-verdict-per-note instruction only in a field description, the model emitted 168 of 300 verdicts (reliability 0.27). With the same instruction also in the prompt body it emitted 302 of 300 (reliability 0.97) (`forced_schema_screen/experiment_log.md`, 2026-06-16, n=60).

Their trust is a replay screen's: direction and mechanism at a frozen board, scored exactly. They are catalogued in [`../evaluation_scopes/turn/report.md`](../evaluation_scopes/turn/report.md).
