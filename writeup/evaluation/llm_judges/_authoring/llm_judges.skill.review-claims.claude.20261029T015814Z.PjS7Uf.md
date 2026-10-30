<!-- claims review of writeup/evaluation/llm_judges/llm_judges.skill.md by claude (claude-opus-5-5), 2026-10-29T01:58Z -->

## 1. Findings

**1.**
- **Claim:** "With 18 pairs and one run per version, no version could be told apart from another, and the decisions were made on other grounds", followed by the table row "Highest overall for the slowest model…" (*Quality scores that could not rank versions*)
- **Source checked:** `evidence/extraction/day_summary/experiment_log.md` ②; `evidence/evaluation/llm_judge/experiment_log.md` §1; `evidence/extraction/day_summary/eval_summary_{25-pro,35-flash,31-flash-lite_medium}.txt`
- **Verdict:** overstated
- **Why:** The record says the scores were flat across *prompt* versions. Across *models* the judge did separate them: completeness was 4.83 for the slowest model and 4.44 for the chosen one, about seven pair-points apart, well above the one-pair swing. §1 says that where the scores separated the models, "they pointed at the slow one that latency ruled out". So the model choice was made against the judge's ranking, not because the judge could not rank. The page's own third table row contradicts the sentence above it.
- **Suggested scope:** "No prompt version could be told apart from another; between models the judge did favour the slowest, and the choice went to speed and to reading the worst failures by hand."

**2.**
- **Claim:** "A person's measure of a judge's accuracy exists only for the earlier version. On the current one, no judge has yet been checked against a person's labels" (opening). Also: "every verdict on the current game's cases was read. Reading verdicts case by case … does not give an agreement rate" (*Checking a judge…*)
- **Source checked:** `evidence/evaluation/factual_errors/experiment_log.md` §6 "How far they were checked"; `evidence/evaluation/labeling/report.md` "What is missing"
- **Verdict:** unclear (needs the owner)
- **Why:** In the ten-player Haiku test set, "every visit sample was read by hand before the verdicts came back. The hand read found about 19 bad before and 6 after. The judge found 16 and 5." That is a blind hand label compared with the judge's verdicts on the current game. It compares counts, not items, but it is more than reading verdicts after the fact. The labelling report classifies no ten-player set as having a person's check, so the records disagree with each other. Who did the reading is not named.
- **Suggested scope:** If the owner counts it: "On the current one, a person's check is limited to blind hand counts on one test set (the judge found 16 and 5 bad samples where the hand read found about 19 and 6) and case-by-case reading; no item-level agreement rate exists." If not, keep the current wording and leave the hand count out.

**3.**
- **Claim:** "the line is held: kept in the record but shown to no one, its author included." (*When the verdict acts*)
- **Source checked:** `Agents/turn/echo_gate.py` docstring ("no prompt shows it, its author's included"); `server/game/translate.py:458-463` (the pass marker carries `gated_candidate`); `frontend/docs/build_plan.md:355-356` and `server_client_transport.md:666-668` (held lines are shown to observers in X-ray mode)
- **Verdict:** wrong mechanism
- **Why:** The code hides a held line from every player's prompt. The website sends it to observers, and the X-ray view shows "the vetoed speech". "No one" is wrong for website viewers.
- **Suggested scope:** "kept in the record but shown to no player, its author included."

**4.**
- **Claim:** "Three more choices keep a rubric checkable. … the criteria come from what the output was required to do, ideally from the same text: the judges for memory notes read the same situation and certainty rules as the models that wrote the notes" (*Narrow questions, with the facts handed over*)
- **Source checked:** `llm_judge/report.md` workflow §3 and case 5; `llm_judge/experiment_log.md` §3–§4
- **Verdict:** overstated (wrong support)
- **Why:** The section is about what "the judges that held up" did differently, but its one example of shared rules is the memory-notes (extraction) judge. That is one of the 1–5 rubric judges that did not hold up: its original dimensions clustered at 4.00 and it never had a person's check. A reader will take shared rules as part of what made judges reliable, which the record does not show. Shared text keeps a rubric in step with the generator; it did not make those scores discriminate.
- **Suggested scope:** Say these are workflow rules, and that the shared-text example is a memory-note judge whose scores still clustered: shared text stops drift, not saturation.

**5.**
- **Claim:** "The census reader has the fullest check in the project" (*Checking a judge…*)
- **Source checked:** `llm_judge/report.md` case 1 ("best-checked judges") and "The full record" (dedup decision: 65 online and 111 batch golden labels from a person)
- **Verdict:** overstated
- **Why:** The source ranks it best among *judges*. The page covers classifiers too, and the keep-or-discard dedup classifier has a larger person-labelled golden set, scored item by item.
- **Suggested scope:** "The census reader has the fullest check of any judge in the project."

**6.**
- **Claim:** "Four model readers labelled 65 lines of the gate's kind without knowing which ones the gate had held." (*When the verdict acts*)
- **Source checked:** `evidence/gameplay/data/silence_calibration/README.md:78` ("four blind Sonnet subagents divided the lines, one reader per line")
- **Verdict:** overstated (minor)
- **Why:** Each line had one reader, not four. The wording can be read as four labels per line, which would be a stronger check than the one done.
- **Suggested scope:** "Four model readers, one per line, labelled 65 lines…"

**7.**
- **Claim:** "re-judging the same outputs moved the count of bad samples by only one or two" (*Checking a judge…*)
- **Source checked:** `llm_judge/experiment_log.md` §7 (bench row: "65/151 and 67/151 bad notes"); `llm_judge/report.md` workflow §4 ("1 to 2 of 267")
- **Verdict:** unclear (needs the owner); open question 9, still open
- **Why:** The run record counts bad *notes* out of 151; only the summary reports say "samples" out of 267. The unit word "samples" depends on which reading is right, so the wording is not neutral between the two as the brief assumes.
- **Suggested scope:** Until settled: "moved the count of bad outputs by only one or two."

## 2. Checked and supported

- The opening's description of the chapter excerpt (narrow judges useful; 1–5 rubrics clustered; packets ready; provisional) matches `writeup/evaluation/evaluation.md:105-115`.
- The live classifiers have at most a model check; the "at most" covers the unchecked addressing classifier (`llm_judge/report.md` "What the tables show").
- In May, on the nine-player game, seats never saw a past day's discussion again; the game master wrote votes, eliminations and revealed roles on a separate code-written channel (`extraction/day_summary/experiment_log.md` ①; `llm_judge/day_summary.md` L2 point 5).
- Five dimensions scored 1 to 5, the transcript shown, 18 pairs (`day_summary.md` L1; design log ②).
- The rubric excerpt matches dimension 4 word for word, with omissions marked (`evaluation/src/judges/prompts/day_summary.py:66-74`).
- Village dynamics scored 5.00 everywhere and evidence type 4.89–5.00. The section was forced by the prompt and the evidence label by structured output, and presence-checking is offered only as "the likely reading" (`day_summary.md` L2 point 2; score files).
- Content dimensions caught dropped accusers (5 of 18 in the first run), an invented announcement, and claimed roles written as confirmed (design log ②; `day_summary.md` L2 point 2).
- Each run regenerated the summaries, and one pair moved ±1 between identical runs. The arithmetic of one pair moving an 18-pair mean by about 0.056 matches the 0.05 and 0.06 deltas in the table (design log ②; `day_summary.md` L1 "The harness").
- Table rows: 400→500 words, 130–230 words written, 4.44→4.39, reverted. Structured output 4.44→4.50, kept for architecture. About 120 minutes for the slowest model. The faster model at medium thinking removed both worst failures of its minimal setting, in about 10 minutes, and was chosen (design log ②).
- Two early decisions rested on 1–5 judges, on few games: the extraction model on 5–10 games, and application prompt v2 on 120 cases from 3 games (`llm_judge/experiment_log.md` §1, §4).
- Census reader: one statement (public message or private note) against a code-built fact sheet of deaths, revealed roles and votes. Yes or no, naming the fact. A cheap over-flagging model, then a stronger re-read (`report.md` case 1; `role_fact_read.build_fact_sheet`; `hallucination_baseline.md`).
- Expectation judge: a person-written expectation of what a correct reply must not claim; any reply that avoids those claims passes; no reference answer, with the stated reason (`report.md` workflow §2).
- A written rule per criterion and a verdict with its evidence are workflow rules (`report.md` workflow §3). The day-summary judge still scores a section removed on 2026-10-04, and no current result uses it (`report.md` case 5; `day_summary.md` status note).
- The three kinds of check and what each misses (`report.md` workflow §4). The procedure is written as "should".
- Census check: a 23-case set chose the cascade; 90 public flags read, 68 genuine; about 0.8 precision on 25 of 278 note flags; 2–3 misses in 15 of 273 rejections by the precision stage. Not blind, nine-player, not repeated after the model change. "I read" is the owner's own default (`experiment_log.md` §7; `hallucination_baseline.md:84-111`; `report.md` "What we would do differently" row 4).
- 10 of 12 bench verdicts upheld; every ten-player verdict read by hand (`experiment_log.md` §7; `factual_errors/experiment_log.md` §6).
- The wrong expectation ("never claimed any role") was corrected and the samples re-judged (`factual_errors/experiment_log.md:371`; `phase3_turn_replay/README.md:49-52`).
- Echo gate: runs on sweep turns only and compares the line against the day's spoken lines. The own-role rule is a prompt instruction. It never weighs truth, fails open, and makes one call per sweep turn at low thinking. Human seats and replies to a player who named the speaker are exempted in code (`echo_gate.py`; `resolve.py:129-141`).
- Opening filter: an allow-list of claims, own night action or result, and challenges. One call per opening round at minimal thinking. Fails open on an error or a missing verdict. A human's line is never held, and it judges kind, not truth (`round_filter.py`).
- Gate as shipped: 10 of 29 restatements held and 0 of 36 worthwhile lines, readers blind to spoken, held or forced. Opening filter: 6 of 7 held lines judged worth hearing before its fix, not measured since (`experiment_log.md` §7, §9; silence README).
- Judges, gates and players share a default model, so self-preference is possible (`experiment_log.md` §2 correction; `report.md` "What is missing" row 7).
- Packets exist for accusation tags, the echo gate and the factual-error judges; the calibration step is built but not run; no claim that the judges are calibrated (`labeling/report.md` "What is missing" and "Golden sets against what is deployed today" rows 1–3).
- No off-page items: no model or vendor names, code names, missing runner, blank check lines or retired tagger in the page copy.

## 3. Not checked

- **Evidence-type scores before structured output:** only the three final-prompt score files survive, and all are structured-output runs. I could not confirm whether evidence type also scored 4.89–5.00 in the free-text runs. If it did, "required an evidence label" does not explain those runs.
- **Whether the May-era extraction-model choice still reaches a current result** (open question 7). The record says it carried into v7; I did not trace what the current ten-player memory uses. "None of the project's current results rests on them" follows `report.md` as written.
- **Opening filter's declared-field override** (`round_filter.py:76-82`, uncommitted): whether it is deployed is unconfirmed (open question 8). The page does not mention it, and nothing on the page conflicts with it.
- **The game master's channel in May:** taken from `day_summary.md` (written in July). I did not check the orchestrator's history to confirm it existed on 2026-05-27.
- **Who did the ten-player hand reads** (finding 2): the records say "by hand" without naming the reader.
- **Labelling packet files** (`labeling/owner_checks/`): not opened. "Ready" rests on the reports.
