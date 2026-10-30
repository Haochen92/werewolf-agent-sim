<!-- claims review of writeup/evaluation/llm_judges/llm_judges.skill_2.md by claude (claude-opus-5-5), 2026-10-29T03:09Z -->

## 1. Findings

**1.**
- **Claim:** "All of these checks are repeated when the judge's model or rubric changes." (*Checking a judge against a person*)
- **Source checked:** `evidence/evaluation/llm_judge/report.md`, case 1 ("the Haiku 5.5 default has no recorded check"), "What we would do differently" row 4 ("every judge moved to Haiku on 2026-10-12 without a re-check"), "What is missing" row 1; `labeling/report.md` "Golden sets against what is deployed today" row 3 (the 23-case gate has not been re-run). Level 2 prompt, CAUSAL AND EVIDENTIAL PRECISION ("Do not turn an intended practice into 'every change is tested'").
- **Verdict:** wrong status
- **Why:** The page states this as current practice. The records say the opposite happened at the one model change on record: every judge moved model, and none was checked again.
- **Suggested scope:** "These checks should be repeated whenever the judge's model or rubric changes; the factual-error judges have not yet been re-checked on the model they use today."

**2.**
- **Claim:** "Re-judging the same outputs shows how far totals move when nothing has changed: on the nine-player factual-error test set, 1 or 2 of 267 samples. A smaller difference between versions means nothing." (*Checking a judge against a person*)
- **Source checked:** `factual_errors/experiment_log.md` §4 "Its noise floor"; `factual_errors/report.md` lines 327–331.
- **Verdict:** unsupported inference
- **Why:** Re-judging fixed outputs measures only the judge's own variation. Every comparison between versions also regenerates its samples. The same source treats a gap of 15 (97 → 82 of 267, p = 0.14) as "a direction, not proof", so a gap larger than 1 or 2 does not by itself mean something. Two re-judgings also do not set a general cutoff.
- **Suggested scope:** "Re-judging the same outputs moved totals by 1 or 2 of 267, which is the judge's own variation. A difference between versions also carries the generating model's sampling, so it needs a paired test, not just a larger gap."

**3.**
- **Claim:** "Rerunning the same prompt moved one pair's score by a full point, while prompt versions differed by a tenth or two of a point. With 18 pairs and one run each, no version could be told apart from another." Also the caption "Score changes stayed within run-to-run variation". (*High scores that could not rank versions*)
- **Source checked:** `evidence/extraction/day_summary/experiment_log.md` ② ("one pair's score moved by ±1 between runs"); `llm_judge/day_summary.md` L2 point 3.
- **Verdict:** unsupported inference
- **Why:** One pair moving by one point shifts an 18-pair mean by about 0.06. That tells us nothing directly about how much the average varies between runs, and that variation was never measured, because each version ran once. "Stayed within run-to-run variation" asserts a measurement that does not exist. What the evidence supports is that the differences were never shown to be larger than noise.
- **Suggested scope:** "One pair's score moved by a full point between runs of the same prompt. With one run per version, differences of a tenth or two could not be shown to be more than run-to-run variation."

**4.**
- **Claim:** "their scores mostly rewarded sections the generating model had been told to write, so they could not say which of two versions was better." (opening). Related: "The same pattern appeared in the judge for the memory notes…" (*High scores…*)
- **Source checked:** `day_summary.md` L2 points 2–3; `extraction.md` L2 (a); the brief's open question 3.
- **Verdict:** overstated
- **Why:** Only 2 of the day summary's 5 dimensions are the presence type, and their cause is the records' explanation, not a tested one. The page itself hedges it later ("The scores fit one explanation"). The inability to rank came from the moving dimensions sitting within unmeasured noise, not from the presence dimensions. The records give no cause for extraction's clustering at 4.00, and 4.00 is not the top of the scale.
- **Suggested scope:** "Their scores bunched high, partly on dimensions that only confirmed a section the prompt required, and their differences between versions were too small to separate from rerun variation."

**5.**
- **Claim:** "Only the factual-error judges have a person's check, and it was made on the earlier game". The table row "Expectation judge … Expectations written by hand; every verdict read by hand | Both". The closing line "the current game's judge results show what model readers agreed on". (*What is established and what remains open*)
- **Source checked:** `llm_judge/report.md` full-record row ("every ten-seat verdict was read; no agreement rate"); `factual_errors/experiment_log.md` §4 point 3 and §6 "How far they were checked"; `llm_judge/experiment_log.md` §7.
- **Verdict:** conflicts with source
- **Why:** There are four problems here.
  - The source says every *ten-seat* verdict was read. On the nine-seat game, only the pinned cases were read, and that reading found the judge unreliable on the cheaper model ("a presupposition as an assertion, and at least one outright error").
  - The hand-read ten-seat verdicts contradict both "made on the earlier game" and the closing line.
  - Listing "expectations written by hand" under *Checked against* contradicts the page's own rule that a reference is not an anchor.
  - The person check of the census reader was also made on earlier judge models, which the page omits.
- **Suggested scope:** Census reader: "a person's check on the earlier game and the earlier judge models". Expectation judge: "every current-game verdict read by hand before use; no agreement rate". Then narrow the closing line to the echo gate, the opening filter and the accusation tags.

**6.**
- **Claim:** "Those runs should name a judge model different from the players', because judges and players now default to the same model" (*What is established…*). "Those runs" follows the packets for the echo gate, the accusation tags and the factual-error judge.
- **Source checked:** `llm_judge/report.md` "What is missing" row 7 ("runs that grade Haiku games"), §5 "Model" ("In the live game, the gates use the players' model"); report case 3 (the tags are the speaker's own output).
- **Verdict:** overstated
- **Why:** The remedy fits offline judges that grade games, such as the factual-error judge. The echo gate runs on the game's model by design, and the accusation tags *are* the player's output. Their calibration checks them as deployed, so a different judge model does not apply to them.
- **Suggested scope:** "Offline judges, such as the factual-error judge, should be run on a model different from the players'; the live classifiers are checked as they run."

**7.**
- **Claim:** "It cannot work as a gauge that ranks two close versions, because nothing shows whether its small differences are real. The memory-quality judges described next lacked that check." (*When a model is the right reader*)
- **Source checked:** `llm_judge/report.md` workflow §1 and §4; `day_summary.md` L2 points 1 and 3 and the upgrade section.
- **Verdict:** unsupported inference
- **Why:** This mixes up correctness and consistency. An outside check tells you whether verdicts are *right*. Whether small differences are *real* is a question of repeatability, which re-judging a fixed set can measure without labels; `day_summary.md` names "decouple regeneration from judging" as a separate fix. The featured story's ranking failure is diagnosed through noise, not through the missing anchor.
- **Suggested scope:** "Without an outside check its scores cannot show which version is better, and without repeated runs on fixed outputs they cannot show that a small difference is more than noise. The memory-quality judges had neither."

**8.**
- **Claim:** "From these cases came the rules I apply to a rubric: … **Change the rubric when the output's requirements change.**" (*Narrow questions…*)
- **Source checked:** `llm_judge/report.md` workflow §3 ("Where a judge keeps its own copy, nothing here ties the two yet") and "What we would do differently" row 3.
- **Verdict:** wrong status
- **Why:** Versioning the rubric with what it grades is recorded as a change for next time, not a rule in use. The day-summary rubric was never updated.
- **Suggested scope:** "the rules I take from these cases", or mark the last rule as one the day-summary judge did not follow.

**9.**
- **Claim:** "Players never saw an earlier day's discussion again, only its summary, so every later decision about a past day relied on it." (*High scores…*)
- **Source checked:** `day_summary/experiment_log.md` ①; `day_summary.md` L2 point 5 (the vote tally, the elimination and revealed roles came from the game master's record on a separate channel).
- **Verdict:** overstated
- **Why:** The hard facts about a past day did not depend on the summary. Only what was said did.
- **Suggested scope:** "so what later players knew of a past day's discussion came from the summary alone."

**10.**
- **Claim:** "The design keeps that second mistake rare and bounded. … Its rule also keeps any statement a player makes about their own role." (*When a judge's label changes the game*)
- **Source checked:** `Agents/turn/echo_gate.py` (docstring, `LINE_ECHO_PROMPT`, `line_echo_of`).
- **Verdict:** overstated
- **Why:** The design limits *where* a wrong hold can happen. Whether such holds are rare is a measured result, and only against model readers. Failing open and exempting humans and replies are enforced in code, but the own-role rule is an instruction to the model. A wrong verdict can therefore still hold such a line, and the prompt also says that repeating an earlier line "is not a new fact".
- **Suggested scope:** "The design limits where that mistake can happen… and its prompt tells the model to keep a player's claim about their own role or night action."

**11.**
- **Claim:** "it held 10 of 29 lines that four blind model readers labelled restatements, and none of the 36 they labelled worthwhile." (*When a judge's label changes the game*)
- **Source checked:** `evidence/gameplay/data/silence_calibration/README.md` Step 1 method ("four blind Sonnet subagents divided the lines, one reader per line") and the Step 4 table.
- **Verdict:** unclear (needs the owner)
- **Why:** The numbers match the source. But the wording reads as four readers agreeing on each line, when each line had a single reader.
- **Suggested scope:** "lines that blind model readers, one per line, labelled restatements".

**12.**
- **Claim:** "I rejected a single model answer as the reference" (*Narrow questions…*)
- **Source checked:** `llm_judge/report.md` workflow §2 ("the factual-error judges do not use one"); a search of `evidence/` found no record of the decision or who made it.
- **Verdict:** ownership
- **Why:** The records give the reason not to use a reference answer, but they do not record that one was considered and rejected, or by whom.
- **Suggested scope:** "The factual-error judges do not use a single model answer as the reference, because…", unless the owner confirms the decision was theirs.

**13.**
- **Claim:** "once I have labelled them the calibration step will report whether each meets its bar" (*What is established…*)
- **Source checked:** `labeling/owner_checks/echo_gate/GUIDE.md` ("You label 50 of those same lines"); `llm_judge/report.md` workflow §4 ("check again on fresh items").
- **Verdict:** unclear (needs the owner)
- **Why:** The echo-gate packet is drawn from the same 65 lines the gate's bar was set on. Passing would confirm the bar against a person on its tuning lines. It would not be a check on new lines, and a reader may take it for one.
- **Suggested scope:** Add "on the lines its bar was set on" for the echo gate, or leave as is if the owner judges it immaterial at this level.

**14.**
- **Claim:** "A pairwise judge, which only says which of two outputs is better, avoids bunching at the top" (*Narrow questions…*)
- **Source checked:** `evidence/evaluation/scoring/report.md` "Choosing a scale"; `llm_judge/report.md` case 6.
- **Verdict:** unsupported
- **Why:** This is the design reasoning. The project's only pairwise judge was confounded and decided nothing, so the property was never observed here.
- **Suggested scope:** "is meant to avoid bunching at the top".

**15.**
- **Claim:** "Most classifiers inside today's game rest on this cheaper check." (*Checking a judge against a person*)
- **Source checked:** `llm_judge/report.md` "Model classifiers in the product" table.
- **Verdict:** overstated
- **Why:** Of the four live-game classifiers, two rest on model readers, the accusation tags rest on another unchecked judge, and the addressing classifier has no check. "Most" holds only if the memory classifiers are counted too.
- **Suggested scope:** "The echo gate and the opening filter rest on this cheaper check."

**16.**
- **Claim:** "The judge's rubric still asks for that section, so no current result rests on this judge." (*High scores…*)
- **Source checked:** `llm_judge/report.md` case 5; `day_summary.md` status note.
- **Verdict:** unsupported inference
- **Why:** The causation is reversed. No current result rests on the judge because nothing current uses it. The stale rubric is why it should not be re-run as it is.
- **Suggested scope:** "No current result rests on this judge, and its rubric still asks for that section, so it should not be re-run as it is."

## 2. Checked and supported

- The three conditions for using a model; code screens first and only what is left goes to a model; the smoke-alarm reading of an unchecked judge (`llm_judge/report.md` workflow §1).
- The census screen's code rules (a dead player named, a dead role's word, a wrong count, a claim not in the list) pass only matching statements to the reader (`factual_errors/report.md` Step 1).
- A day summary was the only view of a past day's discussion (`day_summary/experiment_log.md` ①).
- The judge scored 18 pairs on five dimensions from 1 to 5, reading each transcript beside its summary (log ②; `day_summary.md` L1).
- The rubric excerpt matches `DAY_SUMMARY_RUBRIC` dimension 4 in today's code, quoted verbatim.
- Village dynamics was 5.00 with minimum and maximum both 5 in every stored summary file; evidence type was 4.89–5.00; the summary prompt required the section (`eval_summary*.txt`; `day_summary.md` L2 point 2).
- The 18 pairs were not stratified by difficulty (`day_summary.md` L1 "The dataset").
- The grounded dimensions caught dropped accusers, an invented game-master announcement and confirmed-vs-claimed errors as 1–3 scores (`day_summary.md` L2 point 2).
- The harness regenerated summaries before judging them, mixing generation and judge variation (`day_summary.md` L1 and the upgrade section).
- The version table: 4.44 → 4.39 and 130–230 words, reverted; 4.44 → 4.50 and kept for architecture; about 120 minutes against about 10, with the faster model avoiding the two worst failures of its lowest setting (log ②).
- Extraction's original five dimensions clustered at 4.00 over 48 games, and only the two added dimensions varied (`extraction.md` L2 (a)).
- The summary was rebuilt with code checking claims against the record and the village-dynamics section dropped (log ③, v4 on 2026-10-04).
- The census reader is a yes/no question against a fact sheet built by code, names the wrong fact, and uses a cheap over-flagging pass followed by a stronger re-read (`llm_judge/report.md` case 1; `factual_errors/report.md` Step 1).
- The owner ("I") read the flagged public messages, 25 flagged notes (precision about 0.8) and 15 rejections (2–3 missed), on the nine-player game (`llm_judge/experiment_log.md` §7; `factual_errors/report.md` Step 1).
- Per-case expectations and the watch example; why a reference answer is unsuitable (`llm_judge/report.md` workflow §2).
- Rubric rules 1–4 (`llm_judge/report.md` workflow §3); scale order (workflow §2); the pairwise judge generated and judged in one pass (case 6).
- Anchor versus reference; 30–100 items stratified by verdict, labelled blind, with controls; the bar of 80% agreement and no significant lean (`labeling/config.py`: 0.80, 0.75, 0.05); the calibration step built but not run on real labels (`labeling/report.md` "What is missing").
- The wrong expectation ("never claimed any role" when the speaker had claimed investigator) marked correct samples bad (`gameplay/discussion_evidence.md` learning 4; `factual_errors/experiment_log.md` §6).
- Blind model readers catch disagreement but not a shared bias (`llm_judge/report.md` workflow §4 table).
- Echo gate mechanism:
  - it runs on sweep turns only and judges the line against the day's earlier spoken lines;
  - a held line becomes a pass marker kept for the record and shown to no prompt;
  - it fails open on an exception;
  - human seats and reactive turns are exempt;
  - its bar covers restatement, agreement without a new reason, and filler.

  Sources: `Agents/turn/echo_gate.py`; `llm_judge/experiment_log.md` §9.
- The owner widened the bar on 2026-10-18; the shipped gate held 10 of 29 and 0 of 36 (silence_calibration README, Step 4 table, `_ported` row).
- The opening filter keeps only claims, the speaker's own night actions and challenges, and fails open on an error or a missing verdict (`Agents/turn/round_filter.py`).
- Before its fix, readers judged 6 of the 7 lines it held worth hearing, and it has not been measured since (silence_calibration README; `llm_judge/experiment_log.md` §7).
- Accusation tags: 79% agreement with an unchecked judge, on the nine-player game (report case 3).
- Labelling packets exist for the echo gate, the accusation tags and the factual-error judge (`evidence/evaluation/labeling/owner_checks/{echo_gate,accusation_tags,factual_errors}/`); judges and players share a default model (report "What is missing" row 7).
- Off-page items: no AI-written-test, CI, missing-script, uncommitted-run, "+17pp" or 0.14% material is on the page. The packets are described as enabling the check, with the gap closing only when labels are done and acted on, as `map.md` asks.

## 3. Not checked

- **Whether the quoted rubric is the May 2026 text.** I checked it against today's `evaluation/src/judges/prompts/day_summary.py` only. Shell access was disabled, so I could not read the file's git history or the older log at `2382b34c`.
- **Whether the evidence-type label was required in the free-text prompt versions,** not only in the structured one. `day_summary.md` ties the label to the structured output. I did not read `prompt_versions/v1–v3`.
- **"I scored 18 transcript–summary pairs".** The records do not name who ran the May judge. I accepted it under the brief's ruling to use first person for choices and uses.
- **The 23-case golden set and the 90 public-message flags (68 genuine).** The page does not cite them, so I did not trace them past `llm_judge/experiment_log.md` §7.
- **Whether the "fix" to the opening filter is the `_declared_kind` change in today's code.** The README names commit `5cc25d67`, which I could not inspect. `round_filter.py` also has uncommitted changes in the working tree, which I could not diff. The page's description matches the file as it stands on disk.
