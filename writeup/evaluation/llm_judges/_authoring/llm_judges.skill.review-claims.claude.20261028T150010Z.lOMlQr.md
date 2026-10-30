<!-- claims review of writeup/evaluation/llm_judges/llm_judges.skill.md by claude (claude-opus-5-5), 2026-10-28T15:00Z -->

## 1. Findings

**1.**
- **Claim:** "The judges and in-game classifiers used today have been checked only against other models; the check against a person is prepared but not yet done." (opening, second paragraph)
- **Source checked:** `evidence/evaluation/llm_judge/report.md`, "The full record" and "What the tables show"; `experiment_log.md` §7; `labeling/report.md` case 4.
- **Verdict:** conflicts with source
- **Why:** The factual-error judges are in use today, and they do have a person's check (nine-player game, earlier judge models). Every ten-player expectation-judge verdict was also read by hand. The page says so itself in §4 and §6, so the opening contradicts the sections below it. One live classifier, the human-seat addressing classifier, has no check at all, so "checked against other models" is not true of every classifier either.
- **Suggested scope:** "No judge or classifier used today has been checked by a person on the current game and judge model; the live classifiers have only been checked against other models."

**2.**
- **Claim:** "A check against a person draws a sample stratified by the judge's verdict … and the person labels it without seeing the judge's answer. … The check is repeated when the judge's model or rubric changes." (Checking a judge against something it never sees)
- **Source checked:** `llm_judge/report.md` workflow §4 and "What we would do differently" row 4; `gameplay/turn_prompt/validation/hallucination_baseline.md` (the 2026-07-08 read); `labeling/report.md` row 3.
- **Verdict:** overstated
- **Why:** This is the workflow's recommended procedure, but the present tense makes it read as what was done. The record says every judge moved to a new model on 2026-10-12 without a re-check. The one person's check described next, the census read, was not blind: the person read messages the judge had already flagged. The Level 2 prompt explicitly rules out turning an intended practice into a stated one.
- **Suggested scope:** Frame it as the procedure a check should follow ("should be stratified … should be repeated"), and note beside the census example that it read flagged items and was not repeated when the judge model changed.

**3.**
- **Claim:** "Broad 1–5 quality rubrics … could not tell versions apart, so those design decisions were made by other means." (opening). Also: "None of the project's current results rests on them." (§2)
- **Source checked:** `llm_judge/experiment_log.md` §1 ("Two design calls were judge-driven"); `report.md` case 5.
- **Verdict:** overstated
- **Why:** The detailed record says the 1–5 judges decided two calls: the extraction model (5–10 games) and locking version 2 of the application prompt. Both were May-era and were later superseded. The general wording in the opening says no rubric judge decided anything. The "current results" sentence does hold.
- **Suggested scope:** Limit the claim to the cases shown ("the day-summary versions were decided by other means"), or add that the two early calls that did rest on these judges used few games and have been superseded.

**4.**
- **Claim:** "Players never see an earlier day's discussion again, only a summary written by one model call at the end of that day. Every later decision about a past day rests on that summary." (Quality scores that could not rank versions)
- **Source checked:** `evidence/extraction/day_summary/experiment_log.md` ① and ③ (2026-10-04, claim ledger); `llm_judge/day_summary.md` L2 point 5.
- **Verdict:** wrong mechanism
- **Why:** This is written in the present tense but describes the May set-up. Even then, the game master wrote the vote tally, eliminations and revealed roles to a separate record that did not depend on the summary. Today players read three blocks: the game master's record, a claim ledger kept by code, and the accusations. A reader would take this as how the system works now.
- **Suggested scope:** Put it in the past tense and narrow it: "In May, players saw an earlier day's discussion only through one model-written summary, alongside the game master's record of votes and deaths."

**5.**
- **Claim:** "today's day summaries are checked by code against a record of the players' claims" (When a model should judge)
- **Source checked:** `factual_errors/experiment_log.md` §7 (the summary-claim replay); `factual_errors/report.md`, step 4.
- **Verdict:** overstated
- **Why:** The code check is a replay of selected failure days from captured games, five samples per case, scored by fixed patterns on the summary's fields and on the ledger code builds from them. It does not routinely check every summary, and it catches only the kinds of failure someone wrote a pattern for.
- **Suggested scope:** "Today, a replay of past failure days scores the summary's structured output with fixed code patterns, with no model judge."

**6.**
- **Claim:** "A player's claim about their own role is always kept." (When the verdict acts)
- **Source checked:** `Agents/turn/echo_gate.py` (prompt and `line_echo_of`); `Agents/turn/resolve.py:129-141`; `Agents/turn/round_filter.py:76-82`.
- **Verdict:** wrong mechanism
- **Why:** The sentence sits among the code-enforced exemptions (failing open, human seats, owed replies). The own-role rule is different: it is an instruction in the gate's prompt, so the model can miss it. The opening filter's own judge did mislabel claim lines as "other" until code began trusting the speaker's declared fields.
- **Suggested scope:** "The gate's rules tell it always to keep a player's claim about their own role" (keeping it apart from the code-enforced exemptions).

**7.**
- **Claim:** "A classifier in the game must be cheap enough to run on every turn, so each makes one call on the players' own model at low thinking." (When the verdict acts)
- **Source checked:** `Agents/turn/round_filter.py:114` (`get_llm_judge()`); `Agents/llm_factory/accessors.py:180` (default `"minimal"`); `echo_gate.py:97` (`"low"`).
- **Verdict:** wrong mechanism (minor)
- **Why:** Only the echo gate runs at low thinking. The opening filter runs at minimal thinking and makes one call per opening round, not one per turn.
- **Suggested scope:** "Each makes one cheap call on the players' own model, at low or minimal thinking."

**8.**
- **Claim:** "With 18 pairs and one run per version, the differences between versions were smaller than that swing." (Quality scores that could not rank versions)
- **Source checked:** `extraction/day_summary/experiment_log.md` ②; `day_summary.md` L2 point 3.
- **Verdict:** overstated (wrong unit)
- **Why:** "That swing" is one pair's one-point move. The version differences are averages over 18 pairs. Comparing the two is a unit mismatch that a technical reader will notice: an average over 18 pairs moves far less than a single pair. The record's actual claim is that no version could be told apart at 18 pairs with one run each, and that the deltas were within that noise.
- **Suggested scope:** "A single pair's score moved by a full point between identical runs, and at 18 pairs with one run per version, no version could be told apart from another."

**9.**
- **Claim:** "re-judging the same 267 samples moved the totals by one or two" (Checking a judge …)
- **Source checked:** `factual_errors/report.md` (bench summary, "1 to 2 of 267"); `llm_judge/experiment_log.md` §7 and `gameplay/discussion_evidence.md` §6.6 ("notes 65/151 against 67/151").
- **Verdict:** unclear (needs the owner)
- **Why:** The primary record of the re-judge reports a two-note move out of 151 checkable notes. The "1 to 2 of 267" all-samples figure appears only in the summary reports. The number may be right, but its denominator is not traceable to the run record.
- **Suggested scope:** Confirm which total moved; if only the note count is recorded, write "re-judging the same outputs moved the count of bad notes by two of 151".

## 2. Checked and supported

- What a judge is, and the three conditions for using a model; the census screens by code first. (`report.md` intro and workflow §1)
- The day-summary judge: five 1–5 dimensions, the transcript shown, 18 pairs. (`day_summary.md` L1; design log ②)
- The rubric excerpt matches dimension 4 word for word, with omissions marked. (`evaluation/src/judges/prompts/day_summary.py:66-74`)
- Village dynamics at 5.00 in every run, model and version; evidence type at 4.89–5.00; the summariser's prompt forced the section and structured output forced the label; presence-checking stated only as "the likely reading". (`day_summary.md` L2 point 2)
- The grounded dimensions caught dropped accusers (5 of 18 in the first run), an invented game-master announcement, and claims written as confirmed. (`day_summary.md` L2 point 2; design log ②)
- Each run regenerated the summaries; one pair moved ±1 between identical runs. (design log ②; `day_summary.md` L1 "The harness")
- Table rows: word limit 4.44 → 4.39, 130–230 words, reverted; structured output 4.44 → 4.50, kept for its architecture; highest-scoring model about 120 minutes; faster model at medium thinking removed both worst failures, about 10 minutes. (design log ②)
- Extraction judge: clustering at 4.00 across 48 games; two added dimensions spread the scores; two prompt bugs (−1.19 and +0.69) found by reading; "debugged, not validated". (`extraction.md` L2; `experiment_log.md` §1)
- The census reader's set-up: a fact sheet built by code, a yes/no verdict naming the fact, a cheap model set to over-flag and a stronger one re-reading its flags. (`report.md` case 1; `role_fact_read.build_fact_sheet`)
- The sentinel/player_10 expectation example and both quoted replies. (`report.md` case 1)
- No model answer to compare against, and why. (`report.md` workflow §2)
- Extraction judges share the situation and certainty rules with the generators; the day-summary judge still scores a section dropped on 2026-10-04, and it is not called "retired". (`report.md` workflow §3, case 5)
- Pairwise judge: order alternated, it settled nothing, a labelled retrieval set decided, and generation and judging ran in one pass. (`report.md` case 6)
- The three kinds of check and what each misses. (`report.md` workflow §4)
- Census check: a 23-case set chose the design; 90 public flags read, 68 genuine; precision about 0.8 on 25 notes; 2–3 misses in 15 rejections; scoped to the earlier game and earlier models; "I" matches the owner's default. (`experiment_log.md` §7; `hallucination_baseline.md`)
- The wrong expectation ("never claimed any role"). (`labeling/report.md` case 4)
- The moderator-line flaw and rerun; the self-preference bias favouring the change; 18 of 30 flawed on each model; the summary stayed on the cheaper model. (`report.md` case 7)
- Echo gate: runs on sweep turns only; a held line is kept in the record, shown to no prompt including its author's; fails open; human seats and replies to a player who named the speaker are never gated; judges kind, never truth. (`echo_gate.py` docstring and code; `resolve.py:129-141`)
- Opening filter: an allow-list (claims, own night action or result, challenges); fails open; a human's line is never held; judges kind, not truth. (`round_filter.py`)
- Echo-gate history: 29% → 18% on 146 lines; credit-then-add lines were held; the owner widened the bar; four blind readers on 65 lines; the shipped gate held 10 of 29 and 0 of 36. (`experiment_log.md` §9)
- Opening filter held 6 of 7 lines judged worth hearing before a fix, with no measure since. (`report.md` full record)
- Judges, gates and players share one default model, so self-preference is possible. (`experiment_log.md` §2 correction; `report.md` "What is missing" row 7)
- Packets ready for accusation tags, the echo gate and the factual-error judges; the calibration step is built but not run. Status is stated correctly and nothing implies the judges are calibrated. (`labeling/report.md` "Golden sets against what is deployed today", "What is missing")
- Off-page items: no model or vendor names, no missing runner, no blank check lines, no retired tagger, no AI-written-test bookkeeping in the page copy.

## 3. Not checked

- **Per-run score tables** (`evidence/extraction/day_summary/eval_summary_*.txt`): not opened. "5.00 on every pair, in every run" and "4.89–5.00" are taken from `day_summary.md`. I also did not confirm that the per-accusation evidence label was forced in every run that scored 4.89–5.00, or only after the move to structured output.
- **Extraction raw results** (`extraction/post_game/eval_results/*.jsonl`): not opened. The 4.00 clustering and the −1.19 and +0.69 figures are taken from `extraction.md`.
- **Pairwise details:** "avoids the bunching of 1–5 scores" (`scoring/report.md` Layer 1) and the order alternation (`agent_decision.md`) rest on `report.md` case 6. Neither file was opened.
- **Silence calibration** (`gameplay/data/silence_calibration/README.md`, step 4): the 10 of 29 / 0 of 36 figure and the readers' blinding were taken from `experiment_log.md` §9. The README has uncommitted changes in the working tree.
- **Summariser comparison** (`gameplay/deduction/experiment_log.md` §3): not opened. The comparison is checked against `report.md` case 7 only.
- **Labelling packets** (`labeling/owner_checks/`): I did not open the folder to confirm the three packets exist. "Ready" rests on `labeling/report.md`.
- **Code in the working tree:** `Agents/turn/round_filter.py` and `Agents/day/flow.py` have uncommitted changes. The checks in findings 6 and 7 were made against the working tree as it is now, not against the deployed server.
