# LLM judges: one model scoring another, and how far to trust it

This page covers the LLM judges in the project, and the model classifiers inside the game that judges are
used to check: what each one is for and what it decides, how one is built and checked, and how far each can
be trusted. An *LLM judge* is a language model that reads another model's output and labels or scores it
against a rubric, a written statement of what to look for, in order to measure it. A *model classifier in
the product* does the same kind of labelling, but its label changes the game or the memory (the echo gate
holds a line; the dedup decision drops a memory), so it is not a measurement but something to be measured.
Both are built and checked the same way, which is why they share this page. When code or a person is the
better tool is compared in
[deterministic_audits](../deterministic_audits/report.md); the scales judges score on, and how a judge is
scored against people, are in [scoring](../scoring/report.md); the golden sets judges are checked against are
in [labeling](../labeling/report.md). The full detail (the June 2026 memory-judge account, the
discussion-evidence judge, the echo gate's prompt versions) is in [the detailed record](experiment_log.md).
How it all fits together is in [the hub](../report.md).

## In short

The judges built on a narrow question against facts handed over are the ones that held up; the 1–5 quality
rubrics did not. The classifiers that run inside today's game and memory are a good use of a model but have
only been checked against other models, and every judge and classifier now runs on the same model as the
players. The eight cases below take one use case each: what is judged and how, whether a model was the right
tool, and what would strengthen it. [The full record](#the-full-record) lists every judge and classifier in
the code with its check.

---

## How we built them: the workflow

Every judge and classifier here went through the same five steps, whether it measures or sits in the
product. Where a step differs between the two, it says so; where a case fell short of a step, the case says
so, and [what we would do differently](#what-we-would-do-differently-next-time) names the change.

### 1. Deciding whether a model is the right tool

We use a model when three things hold:

- **The question is about meaning**, which code cannot compute: is this line new, does this summary mislead.
- **There are too many items for a person** to read every one.
- **Its answers can be checked** against something outside it: a person's labels on a sample, a real
  outcome, or a computation.

If code can compute the answer, we use code: the census screens statements by code first and sends only what
is left to the reader. If nothing can
check the judge, its number is a smoke alarm: it can catch a gross fault but cannot reliably rank two close
versions, which is what the memory-era rubric judges turned out to be. A classifier that runs inside the
live game must also be cheap and fast enough for every turn, and fail safe.

### 2. Choosing the kind of judging

| Kind | The question | Scale | Example here |
|---|---|---|---|
| **A narrow check against given facts** | Does this output contradict these facts, or break this expectation? | Yes or no | Census reader, expectation judge |
| **Classification** | Which of a fixed set of classes is this? | Categorical | Echo gate, opening filter, accusation tags, decision tagger, dedup |
| **Pairwise preference** | Which of two outputs is better? | One of two | Situation-summary judge |
| **A quality score on a rubric** | How good is this, on each of several dimensions? | 1–5 per dimension | Extraction and day-summary judges |
| **Judge and repair** | Is this supported? If not, rewrite it | Yes or no, then an edit | De-halo pass |

We choose the narrowest kind that answers the question. A yes-or-no or a fixed class with a written rule is
the easiest to label consistently and to check; a 1–5 score is the last choice (the scales are compared in
[scoring](../scoring/report.md)). The model also runs in one of two places: **offline**, where it measures or
labels and can afford a stronger model, or **in the live game**, where it shapes what players hear and must be
cheap, fast and fail open.

**What the judge is given besides the output.** A judge given only the output and the rubric is
*reference-free*: the echo gate, the opening filter and the pairwise situation-summary judge work this way.
Context is not a reference: the discussion-evidence judge sees the transcript and the public facts so it can
understand a message, but it only sorts the message and never decides whether it is right, so it is still
reference-free. A judge also given something to check the output against is *reference-based*, and the
reference takes one of three forms:

- **A reference answer:** one correct output, and the judge asks how close the output comes to it. It marks
  down a correct reply that is worded differently or makes another point, so the factual-error judges do not
  use one.
- **Reference facts:** the census reader's fact sheet, built by code from the game record, so it costs
  nothing per case and covers every statement. The day-summary judge's transcript plays the same part when it
  checks a summary's faithfulness.
- **Per-case criteria:** the expectation judge's expectation, written by a person for one test case: the
  turn's facts, and what a correct output must not claim. Any output that avoids those claims passes,
  whatever else it says. It catches what a fact sheet cannot express, such as a wrong conclusion drawn from
  true facts (treating a watch that saw a player visit as support for that player's role claim), but each one
  takes a person reading the turn, which is why the ten-seat test sets have 47 and not hundreds.

A reference-based judge is only as good as its reference: the hand read once caught an expectation that was
itself wrong.

### 3. Designing the rubric

- **The rubric is grounded in the output's requirements (its specification), not the judge's taste.** A
  judge grades what the output was required to do. Where the generator's prompt states those requirements,
  the judge reads the same text: the extraction and retrieval judges share the situation and certainty rules
  in `Agents/prompts/standards.py` with the generators they grade, so the two cannot drift apart. Elsewhere
  the requirements come from a ruling (the echo gate's bar), the game's rules (what an opening may hold), what
  the output's next reader relies on (the day summary), or the question a study asks (the discussion-evidence
  judge).
- **The judge is handed the facts** instead of being asked to work them out: the census reader gets a fact
  sheet built by code from the game record.
- **Each criterion has a written rule for what counts.** The echo gate scores one criterion, whether a line
  adds anything, and its prompt says what counts and what does not. Several criteria are fine when the output
  has several requirements, as long as each is defined this way and can be checked; the memory-era 1–5 judges
  fell short on that, not on the number of criteria (case 5).
- **The verdict comes with its evidence** (the quote that decided it, or the fact that was wrong). It ties the
  verdict to the source, which reduces invention, and it lets a person check the verdict by reading it, or
  code check that the quote is really in the record.
- **The rubric stays in step with what it grades.** When the requirements change, the rubric has to change
  with them, or the judge grades against the old version. Sharing one text, as above, does this by itself.
  Where a judge keeps its own copy, nothing here ties the two yet: the day-summary judge's copy was never
  updated, so it still grades a section the summary dropped on 2026-10-04 (case 5).

### 4. Validating and calibrating

A judge's number means something only if it is anchored outside the judge. An anchor is not a reference: a
reference is given to the judge to decide with, while an anchor is what the judge's labels are checked
against afterwards, and the judge never sees it.

There are two main ways, usually used together: a golden set calibrates a stronger model, and the stronger
model then checks the cheap judge on many more items. A third works only where the game records an
objective outcome.

| Anchor | What it checks | Where it stops | Example |
|---|---|---|---|
| **1. A golden set**: a person's labels on a sample ([labeling](../labeling/report.md)) | Item by item, the meaning the judge is asked about; the reference standard | Costly, so small; one person's reading | The census reader's flags read by the owner; the owner checks, packets ready |
| **2. A stronger model**, labelling a sample on the judge's own question without seeing its answer (the "blind model readers" in the cases below) | Item by item, at scale | Needs its own check against a golden set first, and can share the judge's bias, more so from the same vendor | Claude Sonnet and Opus subagents checking Haiku and flash-lite: the echo gate, the decision tagger, the tell detector. Most of today's classifiers rest on this alone, with the stronger model itself unchecked |
| **3. A real outcome**: an objective label the game already records, such as which side won | Whether the scores track something real: they should correlate with the outcome across many games | Only in aggregate, through a noisy link; says nothing of a single item | The retired discussion tagger's deceiver scores predicted the winning side, beyond the vote record |

The check itself:

- **Draw a sample of 30 to 100 items, stratified by the judge's verdict** (flagged and not flagged), so both
  kinds of mistake show up, and spread across games.
- **A person labels it without seeing the judge's answer.**
- **Score the judge against the person:** agreement with kappa, or precision and recall. The labelling
  pipeline's calibration stage (built 2026-10-23, not yet run on real labels) accepts a judge at 80%
  agreement or more, with the interval's lower bound at 75% or more and no significant lean towards
  flagging too much or too little.
- **Measure the noise floor:** re-judge the same outputs and see how far the totals move with nothing changed
  (1 to 2 of 267 on the nine-seat factual-error test set). Smaller differences mean nothing.
- **Include controls**, cases that should pass, to catch a judge that flags too much.
- **Let code flag likely mistakes first, where it can, and read them too.** In the decision tagger's check,
  code flagged tags naming a decision the seat never made, and those were read beside the random sample. They
  are reported apart from it: chosen because they look wrong, they would make the agreement rate look worse
  than it is.
- **Read a few verdicts and their reasons.** This found two bugs in the extraction judge's own prompt, and a
  wrong expectation in the factual-error cases.
- **If the judge fails, fix the rubric and check again on fresh items**, not the ones used to tune it.
- **Check again whenever the judge's model or rubric changes.**

### 5. Configuration, model and scoring

- **Configuration.** One model, set in one place (`evaluation/src/judges/config.py`), so a comparison can pin
  it. Output is structured, validated and retried once; a score that still fails to parse is dropped, not
  guessed. Each run records its settings (model, backend, prompt version), so two runs can be confirmed
  comparable before they are compared. A fixed set of outputs is judged separately from generating them, so
  a change in score can be put down to the version, not to sampling.
- **Model.** The judge should be a different model from the one it grades, because a model tends to prefer
  its own output. Offline, a cheap model can read everything and a stronger one re-read its flags, as the
  census does. In the live game, the gates use the players' model at low thinking, for speed.
- **Scoring.** The scale decides the score: precision and recall for yes or no, agreement and kappa for
  classes, NDCG for a ranking. Details are in [scoring](../scoring/report.md).

---

## The cases, one per use case

### Case 1. Finding factual errors: the census reader and the expectation judge

*Judges that measure · a narrow check against given facts · reference-based*

**What and why.** Whether a player's statement contradicts the game record is the most consequential
judgement in the project: one invented check decided a game. These judges give the error rate, and check
that a fix works on the frozen test cases.

**What is judged, and the rubric.**
- **Census reader:** does this statement contradict a fact sheet that code built from the game record? Yes
  or no, naming the wrong fact.
- **Expectation judge:** does a replayed output break the expectation a person wrote for that test case?
  Violates, meets or unclear, quoting the phrase that decided it.

**How it works.** The census reader gets the fact sheet and one statement; a cheap model reads every
candidate set to catch too much, and a stronger model re-reads its flags. The expectation judge gets one
expectation and one replayed output. In one ten-seat case, a sentinel's watch saw player_10 visit, and
player_10 claimed investigator; the expectation says the watch shows only who visited, so it must not be
used to back the claim or to dismiss the counter-claim. The original output, which used the watch to call the
counter-claim "rushed", violates it; a replay that keeps the visit and the claim apart ("my watch only proves
they visited, not that they are the investigator") meets it.

**Result.** These are the judges the factual-error work rests on: the July error rate, every comparison on
the nine-seat test set, and the ten-seat regression cases.

**Is a model the right tool?** Yes. The question is narrow and the reference is handed over, and code
screens first and catches what it can compute.

**How far to trust it.** 🟡 The best-checked judges in the project, but the checks are from the nine-seat
game and the Gemini readers; the Haiku 5.5 default has no recorded check. The expectation judge is only
as good as the expectation: the hand read once caught a wrong one. Detail:
[factual_errors](../factual_errors/report.md).

**What would strengthen it.** Re-run the census reader's 23-case gate on Haiku (top-up 1), and the owner
check on ten-seat statements (packet ready).

### Case 2. The live game, what the table hears: the echo gate and the opening filter

*Classifiers in the product · classification · reference-free*

**What and why.** When a silent player gets the floor, the echo gate decides whether the line adds
anything; if not, the line is held. The opening filter does the same for the day's first round. These run
in every live game, so their mistakes are what players hear, or don't.

**What is judged, and the rubric.**
- **Echo gate:** does the line add a new fact, a reading of the player's own with its reason, or a question
  nobody has asked, or does it only restate what was said? Restatements, agreement with no new reason,
  repeated requests and filler are held; a player's claim about their own role is always kept.
- **Opening filter:** is each opening line a role claim, the speaker's own night action or result, or a
  challenge to a claim? Everything else is held.

**How it works.** A call on the players' own model at low thinking. It fails open: an error keeps the line.
Two cases never reach the judge: a human seat, and a line answering a player who named the speaker.

**Result.** Three prompt versions were run on the same 146 nine-seat lines; held lines fell from 29% to
18%, and about half of the remaining holds were clear repeats. On 2026-10-18 the bar was widened to hold
restatements and filler, and against four blind Claude Sonnet readers the shipped gate held 10 of 29
restatements and none of 36 worthwhile lines.

**Is a model the right tool?** Yes: whether a line is new is a question of meaning, it is needed on every
turn, and both fail open, so a mistake keeps a line rather than silencing it.

**How far to trust it.** 🟡 for the gate, ⚠️ for the filter. Both are checked only against model readers,
and the filter has not been measured since a fix. Detail: [the detailed record](experiment_log.md) §9.

**What would strengthen it.** The owner check for the gate (packet ready), and a re-measure of the filter on
the lines the readers already labelled (top-up 4).

### Case 3. The live game, who must answer: the accusation tags and the addressing classifier

*Classifiers in the product · classification · reference-free*

**What and why.** Who must reply, and who gets a closing defence, both run on who accused whom. Each AI
speaker labels its own message as it writes it. A human types free text, so a model labels the human's
message the same way, and it drives the same reply obligations.

**What is judged, and the rubric.**
- **Accusation tags:** for each player a message addresses, the form (a question that expects a reply, a
  response, or a mention in the third person) and the stance: accusation (suspects or blames the target),
  defence, agreement, or neutral (passing commentary, such as noting that someone has been quiet).
- **Addressing classifier:** the same vocabulary, applied to a human's message.

**How it works.** The agents' tags are fields of their own structured output, so they cost no extra call. A
question or an accusation opens an obligation to reply; a response or a mention discharges one. A player
accused by at least two others gets a closing defence. The addressing classifier makes one call after each
human message and fails open to no tags, so an error never stalls the turn.

**Result.** The agents' tags agreed with the discussion-evidence judge on 145 of 183 nine-seat messages
(79%). Nothing has been measured for the human tags.

**Is a model the right tool?** Yes. The speaker knows whom it meant, and tagging inside its own output is
free; but a model labelling its own message is not an independent check, so it needs one from outside.

**How far to trust it.** ⚠️ for both. The 79% is against a judge that was itself never checked (case 7),
and the human tags have no check at all.

**What would strengthen it.** The owner check for the agents' tags (packet ready), and human messages from
website games drawn into an owner check (top-up 8).

### Case 4. The ten-seat memory, labelling at scale: decision tagger, de-halo pass and dedup

*Classifiers in the product · classification, and judge-and-repair · checked by blind readers or a computation*

**What and why.** The ten-seat memory needs labels on thousands of items before it can credit or merge
them. A model labels them all; a sample is checked.

**What is judged, and the rubric.**
- **Decision tagger:** which recorded decision does a memory note describe?
- **De-halo pass:** does the game record support this verdict? If not, rewrite it.
- **Dedup:** are two memories, or two strategy points, the same? Keep, discard or merge.

**How it works.** The labelling model works through every item. Separately, Claude subagents label a sample
without seeing the model's answers, and code compares the two. In the tagger's check, code also flagged tags
naming a decision the seat never made, and those were read as well (2026-10-13; new tags are not checked
today).

**Result.** The decision tagger agreed on 98 of 102 against a bar set beforehand. Point-dedup caught only 16
of 65 duplicate groups, which located the problem in the classifier. The de-halo pass cut the verdicts' lean
toward the winning side from +0.74 to +0.50, on one game.

**Is a model the right tool?** Yes for the tagger and for dedup: matching a note to a decision, or two
memories to each other, takes reading. Less clear for de-halo, chosen on one game.

**How far to trust it.** 🟡 to ⚠️. A blind reader catches a classifier that disagrees with a stronger model,
but not a bias both share, and none of these readers has been checked against a person. The keep-or-discard
decision has a person's 65 and 111 labels, from the nine-seat game. Detail:
[sampled reads](../labeling/sampled_reads/report.md).

**What would strengthen it.** Re-run the dedup checks on Haiku (top-ups 2 and 3); point-dedup itself needs
work.

### Case 5. Scoring memory quality on a 1–5 rubric: the extraction and day-summary judges

*Judges that measure · a quality score on a rubric · May–July 2026, nine-seat*

**What and why.** The memory pipeline writes notes after each game and summaries after each day. Their
quality has no cheap ground truth, so a judge scored each on several 1–5 dimensions.

**What is judged, and the rubric.** 1–5 on eight dimensions for extraction and five for the day summary
(such as specific, grounded and faithful); the retrieval and application judges worked the same way.

**How it works.** One call per output, with the source shown where it exists (the day-summary judge sees
the transcript).

**Result.** The judges caught gross faults: dropped accusers and an invented game-master announcement in
summaries; and reading their scores exposed two bugs in the extraction judge's own prompt (one deflated a
score by 1.19, the other, once fixed, raised one by 0.69). They could not rank versions: dimensions that
only check whether a section is present sat at 5.00, extraction's original five clustered at 4.00, and the
day-summary scores were flat across prompt versions. So the design decisions went to other instruments.

**Is a model the right tool?** Weak here: there was no ground truth to check the scores against, and the
scores bunched near the top or did not move.

**How far to trust it.** ⚠️ No person's check, nine-seat and Gemini only. The day-summary judge's rubric
still scores "village dynamics", a section the current summary (v4, from 2026-10-04) no longer has, so it
should not be re-run as it is. Today's summaries are checked by code instead
([factual_errors](../factual_errors/report.md), step 4). Detail: [extraction.md](extraction.md),
[day_summary.md](day_summary.md).

**What would strengthen it.** Nothing current rests on these judges. Retire the day-summary judge (top-up 5).

### Case 6. Comparing two memory queries: the pairwise situation-summary judge

*A judge that measures · pairwise preference · reference-free · nine-seat*

**What and why.** The situation summary is the agent's search query into its memory. Which of two prompt
versions writes the better query is a relative question, which a pairwise judge answers more steadily than
two separate scores.

**What is judged, and the rubric.** Which of two summaries is the better query for the situation.

**How it works.** The judge sees both summaries and picks the better one; the order of the two alternates
so a preference for one position cancels out.

**Result.** It drove no design call. A human-labelled retrieval set did, by ranking score: it dropped one
option (worth −0.08) and kept another (+0.06).

**Is a model the right tool?** Not for the decision: a labelled retrieval set answered the question directly.

**How far to trust it.** ⚠️ The harness generated and judged in one pass, so a change in the score cannot
be separated from a change in generation. Detail: [agent_decision.md](agent_decision.md).

**What would strengthen it.** Nothing needed; it is a record.

### Case 7. Answering one study's question: the discussion-evidence judge and the summariser comparison

*Judges that measure · classification, and a narrow check against the transcript · October 2026*

**What and why.** Two questions, each answered once. Did the discussion redesign move accusations off
turn-taking and silence (the talk had felt thin, resting on votes, quiet and speaking order)? And should the
day summary, one call a day, move from Haiku to Sonnet?

**What is judged, and the rubric.**
- **Discussion-evidence judge:** for each day message, what it rests on (one or more of nine bases: own night
  result, role claim, night events, voting record, speech content, manner, turn-taking, reveal timing, none),
  whom it accuses, and any role the speaker claims.
- **Summariser comparison:** for each day summary, errors that would mislead a later reader: misattributed,
  invented, a claim missed, a rebuttal dropped or a withdrawn accusation kept, a claim written as fact.

**How it works.** The discussion-evidence judge sees the public facts and the transcript up to the message,
never the true roles; code adds the roles afterwards, to score whether accusations on each basis hit evil
players. The summariser comparison re-summarised 6 days from two Haiku games 5 times on each model, kept the
summaries the games used as a third arm, and had Sonnet judge each against the transcript and the record.

**Result.**
- **Discussion-evidence:** turn-taking accusations fell to zero in the first redesigned game (against 3
  games before), a direction only; on the Phase 2 games the labels showed no clear change. Splitting one label
  in two moved another from 74% to 63% on the same messages, so shares compare only within one run.
- **Summariser:** Sonnet was no better, with 18 of 30 summaries flawed on each model, and all 27 `record_check`
  fields written were wrong. The summary stayed on Haiku and `record_check` was removed. Reading the first run
  found a flaw: the judge trusted the moderator's closing line, which the summariser never sees; it was rerun
  without it.

**Is a model the right tool?** Yes for a study: each asks one question about meaning, over more messages than a
person would read.

**How far to trust it.** ⚠️ for both. The discussion-evidence judge was never checked by a person: every
"check:" line in its review sheets is blank. It also knows only the nine-seat roles. The summariser comparison
has no person's check, and its judge, Sonnet, was one of the two models compared; the decision holds, because
that bias favours the model that lost. Detail: [the detailed record](experiment_log.md) §8;
[reasoning_failures](../../reasoning_failures/experiment_log.md) §3.

**What would strengthen it.** Neither is used today. Re-running the discussion-evidence judge would need the
ten-seat roles and a person's check; a summariser rerun should use a judge from neither model compared.

### Case 8. Memory research: the tell detector, same-tell, memory-adherence and coherence judges

*Judges that measure · classification · June–July 2026, nine-seat*

**What and why.** The July memory loop tried to learn which public behaviours (tells) give a role away. The
June decision-replay screen asked whether agents used the memories they were given.

**What is judged, and the rubric.**
- **Tell detector:** did a player show a listed public behaviour?
- **Same-tell judge:** do two wordings describe the same behaviour? It keeps the tell list from counting one
  behaviour twice.
- **Memory-adherence judge:** did a replayed decision follow, contradict or ignore each memory the agent was
  given?
- **Coherence judge:** which choice does the agent's reasoning conclude on?

**How it works.** A miner that sees the true roles proposes behaviours; the detector, kept blind to roles,
scans every player, day and channel for each, and arithmetic over many games decides which side each points
to. Every ten games, after an embedding search, the same-tell judge decides whether a new wording is an
existing entry. The adherence judge sees only what the agent had, the memories given and the action, never
the result. The coherence judge reads only the reasoning, and code compares its answer with the actual vote.

**Result.** The detector was right on 0.93 of its discussion detections and found 87% of the labelled ones
against five Opus readers on 40 cases (0.83 and 77% on votes), and the owner upheld 7 of 8 in one game. Votes
followed the reasoning in 92.5% of 40 decisions. The adherence judge tracked whether a memory was applied
where word overlap with the memory did not (40 decisions).

**Is a model the right tool?** Yes: questions of meaning over thousands of items. The detector is role-blind
on purpose: one that knows the roles approves "the wolf did wolf-things".

**How far to trust it.** 🟡 for the detector; ⚠️ for the other three, with no person's check. All are
nine-seat and Gemini-era. Detail: [tell_extraction](../../extraction/tell_extraction/report.md);
[decision_replay](../../memory_system/effectiveness/decision_replay/experiment_log.md).

**What would strengthen it.** None runs today: the tell pipeline is off and knows only the nine-seat roles,
and the decision-replay screen is a record.

## Key learnings from the cases

- **Narrow questions against facts handed over held up; 1–5 quality rubrics with no ground truth did not.** Dimensions
  that check only whether a section is present sat at 5.00 on every input (cases 1 and 5).
- **For a design call, a golden set or an outcome beat any judge.** The situation-summary prompts were
  settled by a human-labelled retrieval set, not by the pairwise judge (case 6).
- **Reading a judge's verdicts finds faults in the judge itself:** two bugs in the extraction judge's prompt,
  a wrong expectation, a summariser judge that trusted the moderator, and a dedup classifier that missed most
  duplicates (cases 5, 1, 7 and 4).
- **A judge that generates and judges in one pass, or whose scores never move, is measuring the format, not
  the quality** (cases 5 and 6).
- **Blind model readers are a cheap first check, not a replacement for a person:** they cannot see a bias
  they share with the judge (cases 2 and 4).
- **A live classifier must fail safe.** Before its fix, the opening filter held lines that readers judged
  worth hearing; failing open and never judging a human seat limit what such a mistake can cost (case 2).

---

## The full record

### Judges that measure

| Kind | Judge (code) | What it decides | Game · date | Checked against | Trust |
|---|---|---|---|---|---|
| **Narrow, against given facts** | Census reader (`judges/role_fact_read.py`) | Does a statement contradict the fact sheet | nine-seat · July 2026 | **A person:** a 23-case golden set chose it; the owner read 90 flagged public messages, 25 flagged notes (precision about 0.8) and 15 rejections (2–3 missed) | 🟡 |
| | The same reader on the nine-seat test set | Bad samples per version | nine-seat cases · Oct 2026 | **A person:** 10 of 12 verdicts upheld; 40 control cases; re-judging the same samples moved totals by 1 to 2 | 🟡 |
| | Expectation judge (`judges/golden_expectation.py`) | Does a text break a hand-written expectation | both · Oct 2026 | **A person, in part:** the expectation is written by hand, and every ten-seat verdict was read; no agreement rate | 🟡 |
| **Checking a classifier** | Blind model readers (Claude Sonnet subagents) | The classifier's own question, on a sample, without seeing its answer | ten-seat · Oct 2026 | **Nothing yet:** the owner checks would check the readers too | 🟡 |
| **Studies of play** | Discussion-evidence judge (`evaluation/experiments/discussion_evidence.py`) | What a message rests on, whom it accuses, what role it claims | nine-seat · Oct 2026 | **Nothing:** the planned owner check was never done; knows only nine-seat roles | ⚠️ |
| | Summariser comparison judge (`evaluation/experiments/haiku_summary_compare.py`) | Errors in day summaries that would mislead a player | ten-seat · Oct 2026 | **Nothing:** one flaw found by reading, and the run redone. The judge (Sonnet 5.5) was also one of the two models compared | ⚠️ |
| **Memory research** | Tell detector (`evaluation/src/loop/tells.py`) | Did a player show a listed public behaviour | nine-seat · July 2026 | **Model readers, and one game read by the owner** (7 of 8 upheld) | 🟡 |
| | Same-tell judge (`evaluation/src/loop/tell_fold.py`) | Do two wordings describe the same behaviour (every ten games, after an embedding search) | nine-seat · July 2026 | **Nothing recorded** | ⚠️ |
| | Memory-adherence judge (`evaluation/src/loop/memory_adherence.py`) | Per memory given: did the decision follow, contradict or ignore it; a second call labels a town player's stance in discussion | nine-seat · June 2026 | **A cheaper proxy:** it tracked application where word overlap did not (40 decisions, read by hand where the two disagreed); no person's labels | ⚠️ |
| | Coherence judge (`evaluation/src/replay/decision_screen/screens.py`) | Which choice an agent's reasoning concludes on, without seeing the vote | nine-seat · June 2026 | **Nothing:** used to find that votes followed the reasoning in 92.5% of 40 decisions | ⚠️ |
| | Discussion tagger (retired 2026-07-13) | Per-day deceiver skill | nine-seat · July 2026 | **An outcome:** predicts winning beyond the vote proxy | 🟡 retired; [note](discussion_tagger.md) |
| **Rubric quality scores (memory era)** | Situation-summary, retrieval, application, extraction, dedup-quality and day-summary judges, and a whole-turn judge over summary, retrieval and action (`judges/turn_pipeline.py`) | 1–5 scores on each component of the memory pipeline | nine-seat · May–July 2026 | **Nothing** (a retrieval golden set exists but is not wired to the judge) | ⚠️ / ⏸ |

### Model classifiers in the product

| Where | Classifier (code) | What it decides | Game · date | Checked against | Trust |
|---|---|---|---|---|---|
| **The live game** | Echo gate (`Agents/turn/echo_gate.py`; its candidate prompts were compared in `evaluation/experiments/silence_calibration.py`) | Does an open-floor line add nothing (then it is held) | ten-seat · Oct 2026 | **Blind model readers:** held 10 of 29 restatements and 0 of 36 worthwhile lines | 🟡 |
| | Opening filter (`Agents/turn/round_filter.py`) | Which opening lines are claims, results or challenges | ten-seat · Oct 2026 | **Blind model readers:** before a fix, 6 of the 7 lines it held were judged worth hearing; nothing measured since | ⚠️ |
| | The speakers' own accusation tags (each player's structured output) | Whom a message accuses; this picks who gets a closing defence and who must reply | both · Oct 2026 | **A judge:** 79% agreement with the discussion-evidence judge, which is itself unchecked | ⚠️ |
| | Addressing classifier for human seats (`Agents/turn/addressing_agent.py`) | Whom a human's message addresses, and the stance, in the agents' own tag vocabulary; drives the same reply obligations | ten-seat · live | **Nothing** | ⚠️ |
| **The memory** | Decision tagger (`Agents/memory/extraction/decision_tags.py`) | Which decision a memory observation describes | ten-seat · Oct 2026 | **Blind model readers:** 98 of 102 agree, against a bar of 90% set beforehand | 🟡 |
| | De-halo pass (`Agents/memory/extraction/dehalo.py`; prototype `evaluation/experiments/dehalo_compare.py`) | Rewrite verdicts in memories that the record does not support | ten-seat · Oct 2026 | **A computation:** the verdicts' lean toward the winning side fell from +0.74 to +0.50; chosen on one game | ⚠️ |
| | Point-dedup (the batch-dedup cluster agent, `Agents/memory/batch_deduplication/cluster_agent.py`, run by the memory tick) | Are two strategy points duplicates | ten-seat · Oct 2026 | **Blind model readers:** caught 16 of the readers' 65 duplicate groups (on flash-lite) | ⚠️ |
| | Dedup decision (`Agents/memory/deduplication/dedup_agent.py`, scored by `audits/dedup_score.py`) | Keep, discard or merge a new memory | nine-seat · May 2026 | **A person:** 65 online and 111 batch golden labels | 🟡 |
| | LLM reranker (`Agents/memory/retrieval/rerank_agent.py`), off by default | Reorder retrieved memories by relevance to the situation | nine-seat · May 2026 | **A model panel's labels, partly reviewed by a person:** scored by NDCG; 84 of the labels were reviewed and 14 corrected ([labeling](../labeling/report.md)) | 🟡 |

The labelling engine's model panel (`evaluation/src/labeling/engine.py`), which labels items for golden sets
before a person reviews them, is described in [labeling](../labeling/report.md). These tables list every judge and
classifier found in the code on 2026-10-24; prototypes and variants are named inside their parent's row.

✅ sound · 🟡 usable with caveats · ⚠️ smoke test only · ⏸ designed but never run.

**What the tables show.** Of the judges, only the factual-error judges have a person's check, from the
nine-seat game; the memory-era rubric judges are records, and no current number rests on them. Of the
classifiers, only the dedup decision has a person's check, and the reranker one in part, both nine-seat. The classifiers
behind today's live game (the echo gate, the opening filter, the accusation tags and the human seats' tags)
and the ten-seat memory are checked against blind model readers or not at all.

## What is missing, and the top-ups for today's game

| # | Judge | What is out of date | Top-up | Kind | Cost |
|---|---|---|---|---|---|
| 1 | Census reader on Haiku 5.5 | Its 23-case gate was never run on Haiku | Re-run the gate (`role_fact_read.py --golden`) | Re-run, no labels | Cents |
| 2 | Point-dedup in the memory tick (now Haiku 5.5) | The dry run against the readers' duplicate groups used flash-lite | Re-run the dry run on Haiku (`v8_sp_dedup_dry_run.py`) | Re-run, no labels | Under a dollar; estimate before running |
| 3 | Keep-or-discard dedup in the memory tick (Haiku 5.5) | The 65-pair golden set was never run on a non-Gemini model | Re-run the scorer on Haiku | Re-run, no labels | Cents |
| 4 | Opening filter | Not measured since its fix | Run the current filter over the opening-round lines the blind readers already labelled, and compare | A small runner (none exists for the filter), then a re-run | Cents |
| 5 | Day-summary judge | Grades a section v4 removed | Mark retired; today's check is the code-scored summary replay | A note, no run | — |
| 6 | Echo gate, accusation tags, factual-error judges | Checked only against model readers, or not on ten-seat | The owner checks in [labeling](../labeling/report.md) ("Golden sets against what is deployed today") | Owner labels | 30–100 items each |
| 7 | Every judge and classifier | Since 2026-10-12 they and the players all default to Claude Haiku 5.5 (in the Gemini era they differed), so a run that keeps the default may grade its own model's output | Pass a different judge model on runs that grade Haiku games and say so in the run, or change the default | A choice for the owner | — |
| 8 | Addressing classifier for human seats | Never checked; the accusation-tags packet leaves human seats out | Draw the human messages from website games into an owner check, labelled like the agents' tags | A builder change, then owner labels | As many human messages as the games hold; count them first |

Not topped up, because nothing current rests on them: the memory-era rubric judges, the discussion-evidence
judge (it would need the ten-seat roles first), the memory-research judges, and the retired tagger.

## What we would do differently next time

| Stage | Change | What was done | What it would buy |
|---|---|---|---|
| 1. Decide | **1. Ask first whether code can answer the question, and judge only what is left** | The day summaries were first graded by a 1–5 judge; their claims are now checked by code against the claim record | Checks that cost nothing and cannot drift, with judges kept for questions of meaning |
| 2. Kind | **2. A narrow question against given facts before a 1–5 quality rubric; where several criteria are needed, a written rule and a check for each** | The memory judges scored five to eight loosely defined 1–5 dimensions, with no ground truth to check them | The judges that held up here are the narrow yes-or-no ones; the loosely defined dimensions saturated |
| 3. Rubric | **3. Version a judge's rubric with the component it grades** | The day-summary rubric outlived the summary format it scores | No judge grading sections that no longer exist |
| 4. Validate | **4. A small gold sample and a noise floor before a judge's number is used, repeated when its model or rubric changes** | Done for the factual-error judges, on Gemini; every judge moved to Haiku on 2026-10-12 without a re-check | Every cited judge number backed by the same checks, on the model that runs today |
| 5. Configure | **5. A judge model different from the generator, recorded per run** | All judges moved to the players' model on 2026-10-12 | No self-preference risk to argue away |
| 5. Configure | **6. Judge a fixed set of outputs, separately from generating them** | The pairwise and application harnesses generated and judged in one pass | A score change that can be attributed to the version, not the sampling |

**Bottom line.** The judges that matter most, the factual-error judges, are narrow, fact-based and checked
by a person, on the nine-seat game. The classifiers inside today's live game and the ten-seat memory are
checked only against model readers, and every judge and classifier now runs on the players' own model. The top-ups above bring
them up to date cheaply; the owner checks in [labeling](../labeling/report.md) give them a person's check.

*Rewritten 2026-10-23 and checked against the code of that date; restructured around the workflow on
2026-10-24. The previous version, with the June account of the memory judges and its corrections, is
[the detailed record](experiment_log.md).*
