# Designing and validating LLM judges

*Level 2 · [Evaluation](../evaluation.md) · status: trial draft written with the second version of the write-portfolio-page skill on 2026-10-29; revised after the editorial and claims reviews the same day, open questions in the brief; brief: [`_authoring/llm_judges.skill_2.brief.md`](_authoring/llm_judges.skill_2.brief.md).*

## Page copy (draft)

Some evaluation questions are about meaning, which code cannot compute: whether a summary misstates who
accused whom, or whether a player's line adds anything to the discussion. There are usually too many
such outputs for a person to read, so a model reads them against a rubric.

Judges did two different jobs in this project. Some measured outputs offline: they scored summaries or
counted factual errors, and I decided what to do with the numbers. Others are classifiers inside the
live game, and their labels act directly. The echo gate, for example, decides whether a player's line
is published. A wrong measurement can mislead a decision; a wrong classification changes what the other
players hear.

The judges that held up asked a narrow question, were handed the facts needed to answer it, and could
be checked against something outside themselves. The broad 1–5 quality rubrics caught gross faults, but
their scores bunched near the top, partly on dimensions that only confirmed a required section was
there, and their differences between versions were too small to separate from rerun variation.

### When a model is the right reader

I settled on three conditions for using a model judge. The question is about meaning. There are more
items than a person can read. And the judge's answers can be checked against something outside it: a
person's labels on a sample, a recorded outcome, or a computation.

Where the game record supplies the answer, code comes first. The screen for
[factual errors](../factual_errors/factual_errors.md), for example, used code to select statements
matching known error patterns, such as references to dead players, and sent only those to a model.

A judge that fails the third condition can still work as a smoke alarm: it can flag a gross fault, but
it cannot rank two close versions. Without an outside check, its scores cannot show which version is
better; without repeated runs on the same outputs, they cannot show that a small difference is more
than noise. The quality judges for day summaries and memory notes, described next, had neither.

### High scores that could not rank versions

The game grew during the project from nine players to ten, with new roles, and a check made on one
version does not carry over to the other. In the earlier nine-player game, each day's discussion was
condensed into a day summary. Players never saw an earlier day's discussion again, so what they knew of
it came from the summary alone. To compare versions of the summary prompt, I scored 18
transcript–summary pairs with a judge that read each transcript beside its summary and gave five
dimensions a score from 1 to 5.

One dimension shows the problem. The rubric asked for a detailed account of the discussion's dynamics:

> **4. VILLAGE DYNAMICS:** Does the summary characterize the overall discussion dynamics? It should
> describe: (a) village alignment — unified push, fragmented suspicion, or split camps; (b) whether
> consensus is evidence-driven or social momentum; (c) who is driving the discussion vs. staying quiet.
> […]
> 5 = precise, game-state-specific dynamics covering all three aspects

*The rubric describes quality. The score was 5.00 on every pair, in every run, for every generating
model and prompt version.*

The summary prompt required a village-dynamics section, so the section was always there. The scores fit
one explanation: the judge was confirming that the section existed rather than grading it. A second
dimension, whether each accusation's type of evidence was labelled, sat between 4.89 and 5.00; the
summary's structured format required that label. The 18 pairs were not chosen to include difficult days,
so easy discussions may also have lifted the scores.

The dimensions that compared content against the transcript did move: completeness, accuracy, and
whether a claimed role was presented as a claim. They caught real failures as scores of 1 to 3: dropped
accusers, an invented announcement from the game master, and a role treated as confirmed when it had
only been claimed. As a smoke alarm, the judge worked.

Ranking versions was a different matter. Prompt versions differed by a tenth or two of a point on
average, but each was run only once, so nobody measured how far an average moves between runs; a single
pair's score moved by a full point when the same prompt was rerun. Each run also regenerated the
summaries before judging them, mixing the generating model's sampling with the judge's. The decisions
were made on other grounds:

| Change tested | What the scores showed | What decided |
|---|---|---|
| Word limit raised from 400 to 500 | Completeness 4.44 → 4.39 | Reverted: the model still wrote 130–230 words, so length was not the constraint |
| Structured output, one entry per accusation and role claim | Completeness 4.44 → 4.50 | Kept for its architecture: a fixed format, and fields later code can read |
| Choice of generating model | The highest-scoring model took about 120 minutes for 18 pairs | A faster model (about 10 minutes), chosen after reading its worst failures |

*Score changes were never shown to exceed run-to-run variation; each decision rested on word counts,
architecture, speed or a reading of the summaries.*

The judge for the memory notes written after each game bunched in a similar way: over 48 games, its
original five dimensions clustered at 4.00.

The summary was later rebuilt so that code checks its claims against the game record, and the
village-dynamics section was dropped. No current result rests on this judge, and because its rubric
still asks for that section, it should not be re-run as it is.

### Narrow questions with the facts handed over

The judges behind the factual-error work avoid those weaknesses. The screen's reader answers one
yes-or-no question: does this statement contradict a fact sheet? Code builds the fact sheet from the game
record, so the judge never has to reconstruct who died or which roles were revealed. It names the fact
the statement contradicts, which makes each verdict quick to check. A cheaper model reads every
candidate and is told to flag generously; a stronger model re-reads its flags.

On the earlier nine-player game, with the judge models of that time, I checked what the two-stage screen
finally flagged. All 90 flagged public messages were read, and 68 were real errors. In a sample of 25
flagged private notes, about four in five were real. A sample of 15 statements the stronger model
rejected still held two or three real errors, so the screen's counts are lower bounds.

What the judge is given matters as much as the question. The factual-error judges do not compare a reply
with a single model answer, because that marks down a correct reply worded differently. A second judge,
the expectation judge, checks the frozen-turn replays of recorded failures. For each test case a person
writes an expectation: the turn's facts and what a correct reply must not claim, such as citing a night
observation that only showed who visited a player as proof of that player's claimed role. Any reply that avoids those claims passes, whatever else it says.

The contrast gives the rules I take for writing a rubric:

- **Ask for content that can be checked against the source,** as the summary judge's moving dimensions
  did, not for the presence of a section the generator was required to write.
- **Hand the judge the facts** rather than asking it to work them out.
- **Ask for the evidence with the verdict,** so a person or code can check it.
- **Keep the rubric in step with what it grades,** ideally by sharing the generator's requirements
  text. The day-summary judge kept its own copy, so it still grades a dropped section.

The scale follows the question: yes-or-no or a fixed set of classes first, a 1–5 score last. A pairwise
judge, which only says which of two outputs is better, is meant to avoid bunching at the top; the one
used here, on two versions of the memory search query, regenerated and judged in a single pass, so it
could not separate a better prompt from sampling.

### Checking a judge against a person

A judge's number means something only when it is anchored: checked against something the judge never
sees, unlike a reference, which it is given in order to decide. For questions of meaning, the anchor is
a person's labels on a sample.

The planned check for the current game's judges was built into a calibration step in October 2026 and
has not yet been run on real labels. It draws 30 to 100 items, spread across games and stratified by
the judge's verdict so both kinds of mistake appear. A person labels them without seeing the judge's
answers, and cases that should pass are included to catch a judge that flags too much. The judge is
then scored against the labels with a pass bar fixed in advance: at least 80% agreement and no
significant lean towards flagging too much or too little. How those labels are made and scored is
explained in [Building reference labels and reviewing outputs](../reference_labels/reference_labels.md).

Two further checks are cheap. Re-judging the same outputs measures the judge's own variation: on the
nine-player factual-error test set, judging the same 267 replies a second time changed the count of
failing replies by 1 or 2. A comparison between versions also regenerates its replies, so it still needs
a paired test, not just a gap larger than that. Reading verdicts with their reasons finds faults in the
judge itself: the expectation judge once marked correct replies as failures because an expectation said
a player had "never claimed any role" on a day they had claimed investigator. A judge given a reference
is only as good as that reference. These checks should be repeated whenever the judge's model or rubric
changes; the factual-error judges have not yet been re-checked on the model they use today.

A cheaper first check uses blind model readers: a stronger model labels a sample on the judge's own
question without seeing its answers. That catches a judge that disagrees with a stronger reader. It
cannot catch a bias the two share, and the readers themselves still need a person's check. The echo
gate and the opening filter rest on this cheaper check.

### When a judge's label changes the game

When a player who has not yet spoken gets the floor, the echo gate reads the new line against the day's
earlier lines and decides whether it adds anything: a new fact, the player's own reading with its
reason, or a new question. A line that only restates, agrees without a reason or fills time is held:
kept in the record, shown to no one.

The two possible mistakes cost different amounts. Publishing a repeat costs the table some attention.
Holding a worthwhile line can remove evidence or a defence other players needed. The design limits
where that second mistake can happen. The gate fails open: if the model call errors, the line is
published. A human player's line never reaches it, and neither does a reply to a player who named the
speaker, since an answer is owed even if it repeats. Those rules are enforced in code; the prompt also
tells the model to keep a player's statement about their own role.

Failing open covers errors, not a wrong verdict the model returns cleanly, so the gate was measured.
After I widened its bar to hold restatements and filler, it held 10 of 29 lines that blind model
readers, one per line, labelled restatements, and none of the 36 they labelled worthwhile. It misses
most repetition, but in that sample it never held a line worth hearing.
[Deciding when an agent should speak](../../game_design_orchestration/conversation/silence_calibration.md)
explains how that bar was set.

The opening filter shows why the measurement matters. It holds any line in the day's first round that is
not a role claim, the speaker's own night action or result, or a challenge, and it fails open in the same
way. Yet before a fix, blind readers judged 6 of the 7 lines it held worth hearing. The fix made it keep
every kind of night result, such as a watch; how often it errs since then has not been measured.

### What is established and what remains open

Of the judges on this page, only the factual-error judges have a person's check: the screen's reader on
the earlier game, and the expectation judge, whose verdicts on the current game's test cases are read by
hand:

| Judge or classifier | What it decides | Checked against | Game |
|---|---|---|---|
| Factual-error screen reader | Whether a statement contradicts the fact sheet | My check of its flags and a sample of its rejections, with the judge models of that time | Earlier nine-player |
| Expectation judge | Whether a replayed reply breaks a test case's written expectation | Every verdict read by hand before use; no agreement rate | Current ten-player test cases |
| Day-summary and memory-note quality judges | 1–5 quality scores | Nothing; no current result rests on them | Earlier nine-player |
| Echo gate | Whether an open-floor line adds anything | Blind model readers | Current ten-player |
| Opening filter | Whether an opening line is a claim, a night result or a challenge | Blind model readers, before its fix | Current ten-player |

The next step is ready. Labelling packets are prepared for the echo gate (on the lines its bar was set
on), the factual-error judge, and the tags each speaker puts on its own message to say whom it accuses,
which decide who must reply and have so far been compared only with another unchecked model judge. Once
I have labelled them, the calibration step will report whether each meets its bar. Offline judges such
as the factual-error judge should also run on a model different from the players', because the two now
share a default model and a model may favour its own output. Until the labels are done and acted on, the echo gate, the opening filter and the
accusation tags show what models agreed on, not what a person would decide.

<!-- Sources for the page copy (drafted 2026-10-29; not independently verified):
Opening, two uses (measure vs act; echo gate holds a line): evidence/evaluation/llm_judge/report.md
intro paragraph and "In short"; key learnings 1.
When a model is the right reader: report.md workflow §1 (three conditions; code first; census screens by
code; smoke alarm). "I settled on": the conditions are the report's stated practice ("We use a model when
three things hold"); the memory-era judges predate it (case 5).
Factual-error screen by code first: writeup/evaluation/factual_errors/factual_errors.md "Estimating
frequency with a systematic screen"; evidence/evaluation/factual_errors/report.md step 1.
Featured story setup: evidence/extraction/day_summary/experiment_log.md ① (seats never saw an earlier
day again) and ② (judge, five dimensions 1–5, 18 pairs, May 2026, nine-seat; judge model in the log).
Rubric excerpt: evaluation/src/judges/prompts/day_summary.py, DAY_SUMMARY_RUBRIC dimension 4, quoted
verbatim and truncated (levels 1–4 omitted). Village dynamics 5.00 every run/model/version; evidence
type 4.89–5.00; section forced by SITUATION_STANDARDS, label by the structured per-accusation output:
evidence/evaluation/llm_judge/day_summary.md L2 point 2; log ② "the prompt forced the section to exist".
The cause is the records' explanation, not a tested one (brief, open question 3).
Unstratified 18 pairs: day_summary.md L1 "The dataset".
Grounded dimensions caught dropped accusers, fabricated game-master announcement, confirmed-vs-claimed as
1–3: day_summary.md L2 point 2; report.md case 5.
Noise: log ② ("one pair's score moved by ±1 between runs of the same prompt"; −0.11, −0.22);
day_summary.md L2 point 3 (no version distinguishable at n=18 single-run; decisions on architecture and
latency); regenerate-then-judge harness: day_summary.md L1 "The harness" and upgrade 2.
Version table: log ② (word limit 4.44→4.39, 130–230 words, reverted; structured output 4.44→4.50,
architectural reasons; highest-scoring model about 120 min for 18 pairs; faster model at medium thinking
removed the fabricated game-master announcement and the dropped primary accuser of its minimal setting,
about 10 min).
Extraction: evidence/evaluation/llm_judge/extraction.md L2 (a): original five dimensions at 4.00 over 48
games; strategy_depth 3.95 and novelty 2.95 the differentiated ones.
Rebuilt summary; rubric still scores village dynamics; no current result rests on it: report.md case 5;
day_summary.md status note (v4, 2026-10-04; "should not be re-run as it is"); log ③.
Census reader: report.md case 1 and full-record table (fact sheet built by code; yes/no naming the wrong
fact; cheap model set to over-flag, stronger re-read; the owner read 90 flagged public messages, 25
flagged notes with precision about 0.8, 15 rejections with 2–3 missed; nine-seat, July 2026).
Reference answer rejected; per-case expectations; the watch example (a sentinel's watch used to back a
claim): report.md workflow §2 and case 1. The fuller sentinel case moved out of the page copy 2026-10-29
for length.
Rubric rules: report.md workflow §3. Scale order and pairwise bunching: report.md workflow §2;
evidence/evaluation/scoring/report.md Layer 1. Pairwise judge generated and judged in one pass; a
human-labelled retrieval set decided: report.md case 6.
Anchor vs reference; check procedure: report.md workflow §4 (30–100 stratified; blind; controls; gate
80% / interval lower bound 75% / no lean; noise floor 1–2 of 267; re-check on model or rubric change).
Gate thresholds in code: evaluation/src/labeling/config.py (min_agreement 0.80, min_ci_lower 0.75,
bias_alpha 0.05). Calibration step built 2026-10-23, not run on real labels: report.md §4;
evidence/evaluation/labeling/report.md "What is missing".
Wrong expectation: evidence/evaluation/factual_errors/experiment_log.md "How far they were checked";
evidence/gameplay/discussion_evidence.md learning 4; reader not named, so no first person.
Blind model readers: report.md workflow §4 anchor table row 2; key learnings ("cannot see a bias they
share").
Echo gate: report.md case 2; Agents/turn/echo_gate.py docstring and prompt (sweep turns only; reactive
turns and human seats never gated; held line is a pass marker shown to no prompt; own-role statements
always add something, by the prompt's rule; fail open on exception). Bar widened by the owner 2026-10-18;
four blind Sonnet readers, 65 lines; shipped gate 10 of 29 and 0 of 36:
evidence/evaluation/llm_judge/experiment_log.md §9 (12 of 29 was the pre-port low-thinking bar).
Opening filter: Agents/turn/round_filter.py (allow-list; fails open; a human's line never held); 6 of 7
before a fix, not measured since: report.md full-record table and case 2.
Status table: report.md "The full record" and "What the tables show"; expectation judge "every ten-seat
verdict was read" (reader unnamed); accusation tags 79% of 183 nine-seat messages against the unchecked
discussion-evidence judge (case 3).
Next step: labeling/report.md "Golden sets against what is deployed today" rows 1–3 (packets for
accusation tags, echo gate, factual-error judges); report.md "What is missing" row 7 (judges and players
default to the same model since 2026-10-12); map.md handle-with-care "central open gap" and "the gap
closes only when the labels are done and acted on".
Revised after review (2026-10-29):
Game versions sentence: the ten-seat redesign (content plan; map.md "the original nine-player game" and
"the expanded ten-player game" allowed). Day summary as the only view of a past day's DISCUSSION; hard
facts on the game master's channel: day_summary.md L2 point 5.
Noise reworded: one pair ±1 between reruns; each version run once, so the variation of a version's mean
was never measured (claims review finding 3; day_summary.md L2 point 3).
Census check: evidence/evaluation/factual_errors/experiment_log.md §1 table (public messages 68 genuine
of 2,292, all 90 positives read by hand; private notes from a sampled precision of about 0.8; "in the
sample of 15 rejected units, 2 to 3 ... were real errors"; counts are floors); factual_errors/report.md
step 1 item 4 ("The owner checks"). Judge models of that time: report.md case 1.
Noise floor unit: factual_errors/experiment_log.md §4 point 1 ("judging identical generations a second
time moved the totals by 1 to 2 bad samples of 267"; a sample is one generated reply); version gaps
inside it, e.g. 97 → 82 of 267, p = 0.14, "a direction, not proof": factual_errors/report.md.
Not re-checked on today's model: report.md case 1 ("the Haiku 5.5 default has no recorded check");
labeling/report.md "Golden sets against what is deployed today" row 3.
Expectation judge, current game: report.md full record ("every ten-seat verdict was read; no agreement
rate"). On the nine-seat pinned cases the hand read found it unreliable on the cheaper model
(factual_errors/experiment_log.md §4 point 3): left off the page, not cited.
Opening filter fix: evidence/gameplay/data/silence_calibration/README.md "Draw" (the 2026-10-18 fix
"now keeps a follow, a watch and every other night result").
Blind readers one per line: silence_calibration README "Judging".
Echo-gate packet drawn from the calibration lines: labeling/owner_checks/echo_gate/GUIDE.md (per the
claims review; not opened by the writer).
Live classifier status: report.md "Model classifiers in the product" (echo gate and opening filter on
model readers; accusation tags against the unchecked discussion-evidence judge, 79% of 183 nine-seat
messages; the addressing classifier unchecked, not on the page).
Pairwise judge used on the memory search query (situation summary): report.md case 6.
Moved out (supporting notes, not page copy): the extraction judge's two prompt bugs (−1.19, +0.69); the
census reader's 23-case golden set (labeller unnamed); 10 of 12 test-set verdicts upheld; the echo
gate's three prompt versions (29% → 18% held); the summariser comparison judged by one of the two models
compared; the addressing classifier for human seats (never checked).
-->
