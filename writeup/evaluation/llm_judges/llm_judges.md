# Designing and validating LLM judges

*Level 2 · [Evaluation](../evaluation.md) · previous: [Checking agent outputs with code](../code_checks/code_checks.md) · next: [Building reference labels and reviewing outputs](../reference_labels/reference_labels.md) · status: rewritten 2026-10-29; for the owner’s review.*

## Historical brief (2026-10-25)

**Reader question:** How do you make a model's assessment useful enough to guide a decision?

Subsections: questions requiring meaning; choosing narrow labels or pairwise preferences; supplying
the right context and rubric; detecting a judge that cannot distinguish versions; checking verdicts
against human labels and after model changes; classifiers inside the live game, which must fail safe
(smaller example, added 2026-10-25: the echo gate and opening filter keep a line when they error and
never judge a human seat, so a mistake keeps a line rather than silencing it; the gate is checked only
against model readers, and the filter has not been re-measured since its fix. Source: LLM judges, case 2
and key learnings).

**Lead story:** the memory-quality judges caught gross defects but their high, flat scores could not
rank versions. Explain the mismatch between the intended measurement and what the rubric rewarded.
Use one narrow factual-error judge as a contrast. Distinguish judges used to measure from classifiers
whose decisions affect the product, such as the echo gate.

**Exhibits:** a rubric excerpt beside what it actually rewards, and a small score comparison showing
why a high score did not answer the design question. Verify any quoted output before publishing it.

**Sources:** [LLM judges](../../../evidence/evaluation/llm_judge/report.md), especially cases 1, 5 and 6;
the [extraction judge note](../../../evidence/evaluation/llm_judge/extraction.md),
[day-summary judge note](../../../evidence/evaluation/llm_judge/day_summary.md), and scoring guidance.

**Boundary:** explain how labels validate a judge, then link internally to page 5 for constructing those
labels. State current calibration limits here; do not send readers to GitHub to discover them.

**Level 3 reserve:** “Why the quality rubric could not rank versions.” Keep the useful example on
Level 2 first. Split only if reconstructing the rubric defects and score behaviour becomes a substantial
technical analysis; the source's length alone is not a reason.

Exhibits for this page are listed in [`../exhibits/source_map.md`](../exhibits/source_map.md).

---

<!-- Editorial review 2026-10-25: phrasing and structure revised; no independent factual
verification. Earlier completion notes below describe the pre-edit draft and are retained as history.
Verifier handoff: The single-item score fluctuation is no longer used to establish uncertainty in the 18-pair mean.
If repeated aggregate scores exist, supply them before making a stronger noise comparison. Confirm
that the shortened extraction example retains the rubric correction accurately.
Verified 2026-10-25 (main session): no repeated aggregate scores exist. Every version was one run of 18 pairs; the record's own upgrade ('judge one fixed set N times') was never done (llm_judge/day_summary.md L2 point 3 and upgrades). The narrowed wording stands. Extraction example matches llm_judge/extraction.md (epistemic scope 2.81 → 4.00, same extractions re-judged). No change needed.
-->

## Page copy (draft)

An **LLM judge** is a language model asked to assess an output against explicit criteria, called a
rubric. In this project, it answers questions such as whether a summary misrepresents an accusation
or an agent's response contradicts the information it received.

Model judging makes it practical to inspect more outputs than I could read individually. But a
plausible verdict is not enough to support an engineering decision. The judge needs a defined
requirement, the evidence needed to assess it, and checks of its own reliability. The earlier
quality judges showed why: they caught some obvious failures while producing scores that could
not reliably rank versions.

### Choosing when to use a model judge

The first choice is whether the answer requires interpreting language. Code can determine whether
an action was legal or a vote targeted an enemy from the structured game record. A model is useful
when the remaining question concerns meaning: whether a summary changes what someone said, for
example. Even then, code can do part of the work. The factual-error screen first selects candidate
statements, then supplies a model reader with facts computed from the game record.

The next consideration is volume. A person can inspect a few failures directly; reading thousands
of messages needs a repeatable process. Model judging provides that scale, while human review
helps define the criteria and check a sample of verdicts. The choice is therefore guided by three
questions: does the task need interpretation, is automated review worthwhile at this volume, and
can its answers be checked meaningfully?

That last question distinguishes a promising evaluator from a validated one. Human labels can
check individual verdicts. Recorded game outcomes can test whether a score is associated with
winning, but cannot establish whether a particular judgement was correct. Where validation is
missing, a judge may still suggest failures worth investigating; its scores need more support
before they can decide between close alternatives.

The response format should fit the decision. A factual contradiction can receive a yes-or-no
verdict with the conflicting fact identified. Sorting contributions needs defined categories.
Comparing two outputs may call for a pairwise preference. A numerical quality scale is useful
only if its levels have meanings the judge can apply consistently. Choosing a simpler format
does not remove the need to test it.

### High scores did not answer the design question

In the original nine-player game, agents saw summaries of earlier discussions rather than the
full transcripts. A summary that dropped an accusation or presented a role claim as confirmed
could therefore change the information available to later decisions.

To compare summarising models and prompts, a judge read the transcript and summary together and
scored five dimensions from 1 to 5. The evaluation used 18 transcript–summary pairs. Some criteria
could be checked against the transcript; others produced almost uniformly high scores.

| Criterion | Behaviour in the recorded evaluations | What it established |
|---|---|---|
| Discussion dynamics | Scored 5.00 across the tested versions; the prompt already required a section describing those dynamics | The score did not distinguish how well versions described the discussion |
| Evidence type clarity | Scored 4.89–5.00; structured summaries already required an evidence-type label for each accusation | The presence of labels did not establish that their classification was accurate |
| Accuracy and completeness | Missing accusers, invented announcements and claims treated as confirmed received low scores | The judge detected concrete failures in these examples |

The first two criteria showed a **ceiling effect**: scores clustered at the top, leaving little
room to distinguish versions. Inspection of the rubric and results suggested that the judge was
rewarding required sections and labels without adequately assessing their content. The scores
had not been validated against human judgements, so they could not establish that those aspects
of the summaries were consistently excellent.

Even the criteria that caught failures did not provide a convincing ranking of nearby versions.
Moving from free text to structured output changed average completeness from 4.44 to 4.50. Each
version had only one run, and the harness regenerated summaries before judging them. The score
change therefore combined any effect of the format with variation in generation and judging;
there was no repeated estimate of the average to establish how stable that difference was.

Structured output was kept for a clearer reason: it supplied a fixed format, one entry per
accusation and fields that downstream code could read. Concrete failures also informed changes.
The judge helped locate defects, but its small score differences did not justify the design
choice. This historical rubric is no longer suitable for the current summary format, which
removed one of the sections it still grades.

### Give the judge a requirement it can check

The factual-error readers used a more specific task. A reader received a statement and a fact
sheet built by code from the game record, then decided whether the statement contradicted a
supplied fact. A flagged statement had to identify that fact. This made the verdict inspectable:
a reviewer could examine the alleged contradiction instead of interpreting a general quality score.

A replayed turn sometimes needs more than a fact sheet. True observations can support an invalid
conclusion, so each regression case can also specify what the response must not infer. For
example, a town observer saw another player visit someone during the night. The visitor claimed
to be the Investigator. The observation established a visit, but did not establish the visitor's
role; the case's expectation forbids using it to validate that claim or dismiss a rival claimant.

That expectation permits many valid responses. It checks a particular reasoning error without
requiring the agent to reproduce one reference answer. Passing the check means the output avoids
the specified failure, not that every statement in the response is correct.

References need scrutiny too. Reviewing verdicts once exposed an expectation saying that a
player had never claimed a role when the player had claimed Investigator. The apparent failures
came from the test's premise. A narrow question makes a judgement easier to inspect; it cannot
compensate for incorrect evidence.

The same principle applies to the rubric. Criteria should describe the output's requirements,
with written rules for what counts and evidence attached to the verdict. Sharing requirement
text between generator and evaluator reduces the risk of maintaining conflicting copies. It
still requires review when the task changes: the outdated day-summary rubric shows what happens
when the evaluator is left behind.

### Check correctness and consistency separately

A judge needs two different checks. Does its verdict agree with the intended judgement? And does
it give stable answers when nothing changes? Consistency alone cannot establish correctness: a
judge can repeat the same mistake reliably.

For correctness, the planned human check samples both flagged and unflagged outputs across games.
A person labels them without seeing the judge's answer. Reading only flagged outputs would reveal
**false positives**, cases incorrectly marked as failures, but miss **false negatives**, real
failures the judge passed. Both matter when deciding whether the evaluator can support a comparison.

The historical factual-error readers received checks of this kind. A 23-case labelled set helped
select the reader design, and I reviewed the 90 public messages it flagged. A separate sample of
private notes found that about four in five of 25 flags were real errors; reviewing 15 rejected
candidates found two or three missed errors. These were small checks on the earlier game and its
models, but they exposed both kinds of mistake rather than treating every verdict as correct.

For consistency, hold the outputs fixed and judge them again. On the original game's factual-error
test set, repeated judging changed the total flagged count by one or two out of 267 responses.
That gives a limited view of variability in the evaluator; it does not measure variability from
generating new responses, or establish a universal threshold below which differences are meaningless.

When review leads to changing the rubric, testing it on fresh items matters. Examples used to tune
a judge are a **calibration set**; an untouched, **held-out set** tests whether the revised behaviour
extends beyond those examples. Changing the judge's model or the task also calls for another check.
Agreement measured on the earlier configuration does not automatically transfer.

Other model readers can help find disagreements and inspect more cases. Their agreement is not
human validation: they may share mistakes, including with the model being evaluated. A different
judge model can reduce reliance on the generator's own assessments, but still needs checking.
[Building reference labels and reviewing outputs](../reference_labels/reference_labels.md)
explains how the review samples are prepared.

### When a verdict changes the game

Some model classifications affect play directly. The echo gate decides whether an agent player's
completed contribution adds enough to publish. Unlike an offline judge whose labels enter a
report, its decision changes what other players hear.

The two mistakes have different costs. Letting repetition through adds unnecessary discussion;
withholding a useful contribution removes information from the game. The gate therefore keeps a
line if its model call fails, a policy called **fail-open**. This handles a failed call, not an
incorrect verdict returned in the expected format. That second failure still needs evaluation.

On the 65 lines used for calibration, the implemented gate withheld 10 of 29 lines that model
readers labelled repetition and none of 36 labelled worthwhile. This supported the chosen rule on
those examples, while showing that much repetition remained. The same examples helped select the
rule, and their labels had not been checked by a person. The result therefore does not establish
general accuracy or an improvement in gameplay.

[Deciding which contributions to publish](../../game_design_orchestration/conversation/silence_calibration.md)
covers the policy and calibration in detail. Here, the additional requirement is that a live
classifier needs both operational failure handling and checks of the consequences of its verdicts.

### What remains unvalidated

The earlier factual-error checks do not validate the judges used on the current ten-player game.
Individual replay verdicts have been inspected, but there is no completed human-labelled sample
establishing their agreement with a person on the current setup. Until that check is done,
reported rates describe what the judge labelled, with the reliability limits of that evaluator.

The prepared labelling packets cover factual-error judges, the echo gate and the accusation tags
that drive reply obligations and closing defences. The next step is to complete those labels,
inspect both kinds of disagreement and evaluate any revisions on fresh cases. Re-running the
historical factual-error set can provide an earlier regression check, but cannot replace coverage
of the current game's situations.

**Evidence.**

- [LLM judges and their validation](../../../evidence/evaluation/llm_judge/report.md): evaluator
  choice, factual-error readers, live classifiers and outstanding checks.
- [The day-summary judge](../../../evidence/evaluation/llm_judge/day_summary.md) and
  [summary design experiments](../../../evidence/extraction/day_summary/experiment_log.md):
  ceiling effects, concrete failures and the structured-output comparison.
- [Reference labels](../../../evidence/evaluation/labeling/report.md): prepared human-review packets.
- [Silence calibration record](../../../evidence/gameplay/data/silence_calibration/README.md):
  the echo gate's calibration results and model-reader labels.

<!-- Direct editorial rewrite 2026-10-29, without the skill workflow, per owner.
Approved outline retains definition and evaluator choice before the main example. Progression:
choice -> ceiling-effect case -> grounded criteria -> correctness versus consistency -> live
classification -> current human-validation gap. Earlier prose and source mappings retained below.
Selected source check, not a fresh implementation audit. No experiments or reviewers run.
The echo-gate result is explicitly calibration, not held-out accuracy, following the current
silence_calibration.md and its linked README. Noise-floor language no longer asserts a universal
minimum meaningful difference. Sharing requirements reduces drift; it does not guarantee alignment.
Removed version/latency inventory, extraction-rubric incident, pairwise-query history, opening-filter
history and acceptance-threshold details from public copy; full records remain in evidence.
-->

<!-- Prior page copy; superseded 2026-10-29.
Some questions about an agent's output can only be answered by reading it. Does a day summary
misrepresent who accused whom? Does a player's line add anything the table has not already heard? An
LLM judge answers questions like these at scale: a language model reads another model's output and
labels or scores it against a rubric, a written statement of what to look for. The judge's answer is
itself a model output, so it raises two engineering questions: what should the judge be asked, and how
do you know its answers are right?

In this project, the judges that proved useful asked narrow questions and were given the facts needed to
answer them. Broad 1–5 quality rubrics caught obvious defects, but their scores sat near the top of the
scale and could not distinguish versions. This page explains that difference, how a judge is checked
against something outside itself, and why model classifiers inside the live game need an additional
safeguard. The judges used on the current game have not yet been checked against human labels; the last
section describes that next step.

### When is a model the right evaluator?

A model judge was used when three conditions held. The question required interpretation that the
project's code checks did not provide. There were too many items for a person to read. And the
judge's answers could be checked against something outside it: a person's labels on a sample, a real
game outcome or a computation. When the game record already contains the answer, code checks it
instead ([Checking agent outputs with code](../code_checks/code_checks.md)). Even where a model
reads, code can narrow the work first: the screen that counted factual errors used code to select
candidate statements before any model read them.

The same kind of model call can play two different roles. A judge *measures*: its labels go into a
report or a comparison between versions. A classifier in the product *acts*: the echo gate, for
example, decides whether a player's line is heard at all. A classifier's labels change the game, so it
is something to be measured rather than a measurement. Both are designed and checked in the same way,
but a classifier's mistakes reach players, which adds a requirement covered later on this page.

### Featured story: high scores that could not rank versions

#### What the rubric asked, and what it rewarded

In the original nine-player game, players never saw an earlier day's discussion again, only a summary of
it. Every later decision about a past day therefore rested on one summarising call. To evaluate it, a
judge read each day's transcript and its summary and scored five dimensions from 1 to 5, over 18
transcript–summary pairs. A similar judge scored the notes the memory pipeline extracted after each game
on eight dimensions.

The rubric asked about quality. In practice, two of the day-summary dimensions rewarded something the
summary format already guaranteed.

| Dimension | What the rubric asked | What the judge actually rewarded |
|---|---|---|
| Village dynamics | “Does the summary characterize the overall discussion dynamics?”: alignment, whether consensus was evidence-driven, who drove the discussion | The section's presence. The summariser's prompt required that section, and the score was 5.00 in every run, for every model and prompt version |
| Evidence type clarity | “Does the summary distinguish the TYPE of evidence behind each accusation?” | The label's presence. The structured output required one label per accusation; scores sat between 4.89 and 5.00 |
| Completeness, accuracy, epistemic correctness | Whether accusations, attributions and role claims match the transcript, and whether claims are distinguished from confirmed roles | Checkable content. These scores moved, and caught real failures |

*Rubric wording quoted from the day-summary judge's prompt; scores from the nine-player game, May–July
2026.*

A score that stays at the ceiling cannot distinguish the versions tested. The judge could confirm
that a required section existed, but without labelled examples it had nothing against which to grade
how good that section was. The near-perfect scores did not show that the summaries were excellent.

The dimensions the judge could check against the transcript were useful. Dropped accusers, an invented
game-master announcement and claimed roles described as confirmed all received scores of 1 to 3. As a
detector of gross failures, the judge worked; it acted as a smoke alarm rather than a ruler.

#### Why the differences could not be trusted

The intended use was to choose between prompt versions. The changes tested on the same 18 pairs moved
the scores very little:

| Change tested | Completeness score | What the decision rested on |
|---|---|---|
| Word limit raised from 400 to 500 | 4.44 → 4.39 | The model still wrote 130–230 words, so length was not the constraint; reverted |
| Free text → structured output | 4.44 → 4.50 | Kept for architecture: a fixed format, one entry per accusation and fields later code can read |
| Choice of summarising model | Highest for a model that took about 120 minutes for 18 pairs | The two worst failures, read by hand; a faster model at a higher thinking setting removed both in about 10 minutes |

*Day-summary judge, 18 transcript–summary pairs, one run per version.*

The harness regenerated each summary before judging it, so changes in score mixed variation in the
summaries with variation in the judge. One pair's score moved by a full point between runs, but that
single-item movement does not quantify the uncertainty of the average across 18 pairs. Without a
repeat-run estimate for that average, the small differences were difficult to interpret. The design
decisions rested on the concrete failures and implementation requirements described above.

The extraction judge exposed a related problem: a rubric can measure the wrong requirement. It applied
a rule about certainty to observations, even though that rule was intended for strategy advice.
Re-judging the same extractions after correcting the rule raised the score from 2.81 to 4.00. The outputs
had not improved; the measurement had changed.

These judges belong to the original game, and no current result rests on them. The day-summary judge
still grades a section the summary dropped in October 2026, so it should not be re-run as it stands. The
current summaries are checked by code against a claim record
([Finding and fixing factual errors](../factual_errors/factual_errors.md)). The general lesson was to
ask what a dimension can actually observe before relying on its average, and to version a rubric with
the component it grades.

### Narrow questions, with the facts supplied

The judges behind the factual-error work were designed differently. The screen that estimated how often
public messages contained factual errors used a reader that asked one question: does this statement
contradict a fact sheet built by code from the game record? It answered yes or no and named the
contradicted fact. A cheap model read every candidate and was set to over-flag; a stronger model
re-read its flags. A 23-case labelled set was used to choose this design, and I read the 90 flagged
public messages myself. Those checks provided a sampled view of its errors: on private notes, about four in five
flags were real, and 2 to 3 of 15 sampled rejections were errors the reader had missed.

A replayed turn needs a different reference, because a fact sheet cannot express every wrong
conclusion. For each test case, a person writes an expectation: the facts of that turn and what a
correct response must not claim. In one case from the expanded ten-player game, a sentinel (a town role
that watches a player at night and learns who visited them) saw player_10 visit, and player_10 claimed
to be the investigator. The expectation says the watch shows only a visit, so it must not be used to
support that claim or to dismiss a rival claim. The original response, which used the watch to call the
rival claim “rushed”, violates it. A response that keeps the two apart passes, however it is worded.

That is why the expectation names what must not be claimed rather than supplying a model answer: a
single reference answer could penalise valid replies that make a different point. Either kind of reference
is only as good as itself. Reading verdicts once found an expectation stating that a player had “never
claimed any role” on a day the player had claimed investigator; the apparent model failures came from
the test.

Pairwise preference is another way to avoid bunched scores, because the judge only has to say which of
two outputs is better. A pairwise judge compared versions of the query an agent uses to search its
memory, alternating the order of the two outputs so a preference for one position would cancel out. It
did not settle the design. That harness generated and judged in a single pass, so a change in score
could not be separated from sampling. A human-labelled retrieval set answered the question directly, by
measuring whether each query version ranked the relevant memories first.



### Writing a rubric that measures the requirement

A useful rubric starts from what the output was required to do, not from a general idea of quality.
Where the generating prompt states those requirements, the judge reads the same text: the extraction
and retrieval judges share the generators' rules for describing a situation and expressing certainty,
so the two cannot drift apart. The day-summary judge kept its own copy, which is how it came to grade a
section that no longer exists.

Each criterion also needs a written rule for what counts. The echo gate scores one criterion, whether a
line adds anything, and its prompt lists what does and does not count. Several criteria are acceptable
when each is defined that way; the memory-era judges fell short on definition, not on the number of
dimensions. Finally, the judge returns its evidence with each verdict, such as the phrase that decided
it, so a person can audit the verdict by reading it and code can confirm the quote exists.

### Checking a judge against an anchor outside it

A judge's number means something only when it is anchored outside the judge. An anchor differs from a
reference: the judge uses a reference to decide, while an anchor is what its labels are compared with
afterwards, without the judge seeing it.

| Anchor | What it can show | Where it stops |
|---|---|---|
| A person's labels on a sample | Item by item, whether the judge answers the question it was asked | Small, costly, and still one reader's interpretation |
| A stronger model, labelling the same items without seeing the judge's answers | Item by item, at a larger scale | Needs its own check against people; can share the judge's biases, especially from the same vendor |
| A recorded game outcome, such as which side won | Whether scores track something real across many games | Only in aggregate; says nothing about a single item |

The planned check draws 30 to 100 items, stratified so that both flagged and unflagged items appear and
both kinds of mistake can show up. A person labels them without seeing the judge's answers. The
judge's agreement with the person is scored, together with Cohen's kappa, a measure of agreement beyond
chance. The calibration stage built for this accepts a judge at 80% agreement or more, with the lower
bound of its 95% interval at 75% or more, and no significant tendency to flag too much or too little.
That stage exists but has not yet been run on real labels.

The check also needs a noise floor: how far the totals move when the same outputs are judged again with
nothing changed. On the original game's factual-error test set, re-judging moved the count of bad
responses by only one or two out of 267, so differences smaller than that could not be attributed to a
change. Control cases that should pass reveal a judge that flags too much. Any of these checks must be
repeated when the judge's model or rubric changes, because agreement measured with one model does not
transfer automatically to another.

Model readers can help inspect a judge, but agreement between models is not human validation. A judge
from the same family as the model it grades may share preferences or errors. Its labels still need an
independent check, even when they look plausible.

**Link:** Explore how reference labels are sampled, blinded and reviewed →
[Building reference labels and reviewing outputs](../reference_labels/reference_labels.md).

### Classifiers inside the live game must fail safe

When a player who has not spoken is given the floor, the echo gate decides whether their line adds a
new fact, a reasoned reading of their own or an unasked question, or only restates what was said. A held
line is not published, but its author sees on the next turn that it was never heard. A player's claim
about their own role is always kept. Replies owed to another player are not gated, and a human seat's
line is never judged. If the call fails, the line is kept.

Those rules limit the cost of a failed call: the line is kept rather than silenced. They do not
prevent a valid but wrong decision, so the gate's accuracy still had to be measured. On 2026-10-18 I
widened its bar to hold restatements and filler. Four stronger models, reading blind, then labelled 65
lines from the open floor. The gate as shipped held 10 of the 29 lines they labelled as restatements and
none of the 36 they labelled worthwhile. It let most repetition through, but in that sample it silenced
nothing worth hearing, which is the direction in which a live filter should err. Those labels came from
models, and no person has checked them yet.

The opening filter, which allows only role claims, a player's own night result and challenges to claims
into the day's first round, shows why such a measurement matters. Before a fix, model readers judged 6 of
the 7 lines it held to be worth hearing. It has been fixed, but has not been measured again since.

### The open gap: checking the current game's judges

No person has yet checked the judges used on the current ten-player game against a labelled sample.
Individual replay verdicts have been read, which can catch a wrong verdict but does not measure how
often the judge agrees with a person. The judges with such a check are the factual-error readers,
and those checks were made on the original nine-player game, with the models the project used before
October 2026. The judges and classifiers now run on a different default model, the same one the
players use, and the earlier checks have not been repeated on it. Until they are, reported rates
describe what the current judge labelled. They do not establish the underlying error rate against a
human reference.

The next step is to label samples for three sources that current decisions or players depend on: the
factual-error judges, the echo gate, and the accusation labels that decide which players must reply and
who receives a closing defence. The labelling packets are prepared; the gap closes only when the labels
are complete and each source has been scored against the acceptance criteria. Two cheaper steps can
come first: re-running the factual-error reader's 23-case set on the current model, and grading
players' outputs with a different model from the one that produced them.

**Evidence.**

- [LLM judges: one model scoring another, and how far to trust it](../../../evidence/evaluation/llm_judge/report.md)
  (the workflow; cases 1, 2, 5, 6 and 7; key learnings; the gaps for today's game).
- [The day-summary judge](../../../evidence/evaluation/llm_judge/day_summary.md) and
  [the day summary's build log](../../../evidence/extraction/day_summary/experiment_log.md), part ② (the
  saturated dimensions and the version tests).
- [The extraction judge](../../../evidence/evaluation/llm_judge/extraction.md) (the clustered dimensions
  and the two judge-prompt faults).
- [Scales and scores](../../../evidence/evaluation/scoring/report.md) (choosing a scale, scoring a judge
  against a person, the noise floor).
- [Reference labels](../../../evidence/evaluation/labeling/report.md), "Golden sets against what is
  deployed today" (the owner-check packets).
-->

<!-- **Link (planned):** Explore how a labelled ranking overturned a query design → the Memory chapter's
retrieval page. -->

<!-- Sources for the page copy (checked 2026-10-25):
Opening, judge definition, narrow vs 1–5: llm_judge/report.md "In short", key learnings 1.
When a model is right: report.md workflow §1 (three conditions; code first; census screens by code).
Measure vs act distinction: report.md intro paragraph ("a model classifier in the product ... something
to be measured").
Featured story setup: extraction/day_summary/experiment_log.md ① (seats never saw an earlier day again)
and ② (five dimensions 1–5, 18 pairs). Extraction judge eight dimensions: llm_judge/extraction.md L1.
Rubric excerpts: evaluation/src/judges/prompts/day_summary.py (DAY_SUMMARY_RUBRIC, dimensions 3 and 4),
quoted verbatim, truncated. Village dynamics 5.00 every run/model/version; evidence type 4.89–5.00;
forced by SITUATION_STANDARDS and the structured per-accusation label: day_summary.md L2 point 2.
Grounded trio caught dropped accusers, fabricated GM announcement, confirmed-vs-claimed as 1–3:
day_summary.md L2 point 2; report.md case 5. "Smoke alarm": report.md workflow §1; day_summary.md verdict.
Version table: day_summary/experiment_log.md ② (word limit 4.44→4.39, 130–230 words, reverted;
structured output 4.44→4.50, architectural reasons; model choice: highest-scoring model ~120 min for 18
pairs, faster model at medium thinking removed the fabricated GM announcement and dropped primary
accuser at ~10 min). Noise: same log ② ("one pair's score moved by ±1 between runs of the same prompt";
−0.11, −0.22); day_summary.md L2 point 3 (version deltas within noise; decisions on architecture and
latency); regenerate-then-judge harness: day_summary.md L1 "The harness" and upgrade 2.
Extraction: extraction.md L2 (a) clustering at 4.00 over 48 games, strategy_depth 3.95, novelty 2.95;
two bugs: epistemic scope 2.81→4.00 (−1.19), specificity on narrow field vs composed query 3.19→3.88
(+0.69); "Runs 1–3, fixed extractions, only judge prompt changed".
No current result rests on them; day-summary judge grades a section removed 2026-10-04; should not be
re-run; today's summaries checked by code: report.md case 5; day_summary.md status note.
Census reader: report.md case 1 and full-record table (fact sheet built by code; yes/no naming the
wrong fact; cheap model set to over-flag, stronger re-read; 23-case golden set chose it; owner read 90
flagged public messages; precision about 0.8 on 25 flagged notes; 2–3 missed in 15 rejections). "I
read" matches factual_errors.md ("I checked the flagged public messages") and report.md "the owner read".
Expectation judge and sentinel example: report.md workflow §2 (per-case criteria) and case 1; sentinel
rule from the game's rules text (a watch learns who visited the watched player). Reference answer
rejected: workflow §2. Wrong expectation ("never claimed any role"): discussion_evidence.md §8.6
learning 4 / report.md workflow §2 end.
Pairwise: report.md case 6 (order alternated; drove no design call; generated and judged in one pass;
human-labelled retrieval set decided); scoring/report.md Layer 1 (pairwise avoids bunching).
Rubric design: report.md workflow §3 (specification; shared standards text; one criterion with written
rule; several criteria fine if defined; evidence with verdict; rubric in step; day-summary copy).
Anchors table: report.md workflow §4 table. Check procedure: §4 bullets (30–100 stratified; blind;
kappa; gate 80% / lower bound 75% / no lean; built 2026-10-23 not yet run on real labels; noise floor
1–2 of 267; controls; re-check when model or rubric changes). Gate thresholds confirmed in code:
evaluation/src/labeling/config.py (min_agreement 0.80, min_ci_lower 0.75, bias_alpha 0.05) and
calibration.py (exact McNemar on the disagreements for the bias condition).
Summariser comparison: report.md case 7 (Sonnet judged; 18 of 30 flawed on each; decision holds because
the bias favours the model that lost; moderator closing line; rerun).
Echo gate: report.md case 2; Agents/turn/echo_gate.py docstring and code (sweep turns only; reactive
turns and human seats never gated; held line becomes a pass marker its author sees; own-role claims
always kept; fail open on exception). 2026-10-18 bar widened by the owner; four blind Sonnet readers,
65 lines; shipped gate 10 of 29 and 0 of 36: llm_judge/experiment_log.md §9 (the docstring's 12 of 29 is
the pre-port low-thinking bar; the report's 10 of 29 is the shipped gate).
Opening filter: Agents/turn/round_filter.py (allow-list: role claim, own night action or result,
challenge; fails open; human line never held; live via Agents/nodes/day/flow.py); 6 of 7 before a fix,
not measured since: report.md full-record table and case 2.
Open gap: report.md "What the tables show", "What is missing" rows 1, 6, 7; workflow §5 (same model as
players); labeling/report.md "Golden sets against what is deployed today" rows 1–3 (packets for
accusation tags, echo gate, factual-error judges); map.md handle-with-care "central open gap" and
"labelling packets enable ... gap closes only when the labels are done and acted on".
-->

<!-- Completion note
Structure. Follows the brief's subsection list, with two local changes: (1) "choosing narrow labels or
pairwise preferences" and the factual-error contrast share one subsection ("Narrow questions, with the
facts supplied"), because the narrow judge is the brief's named contrast to the lead story; (2) the
featured story comes second, straight after the short "when is a model right" framing, so the reader
meets the measure/act distinction before the story and the live classifiers later. "Checking verdicts
against human labels and after model changes" became "Checking a judge against an anchor outside it",
plus the closing gap section, which states the next step plainly and links to reference_labels.md.
No Level 3 page; the brief's Level 3 reserve ("why the quality rubric could not rank versions") stays
on this page: the two exhibits and three paragraphs carry it without a separate technical analysis.

Exhibits. LJ-rubric is the first table (rubric wording beside what it rewarded). LJ-flat-scores is the
version table: the source records no version-by-version table of all five dimensions, so I used the
completeness changes the build log reports, with the decision each rested on, rather than invent a
fuller grid. Also added a compact anchors table (from report.md workflow §4).

Claims I was unsure of:
- Rubric excerpt is quoted from today's prompt file. The status note in day_summary.md says the rubric
  is unchanged ("still scores village_dynamics"), but I could not run git history to confirm the May
  wording is identical (git log needed approval). Verify before publishing the quotation.
- "the score was 5.00 in every run, for every model and prompt version" is day_summary.md's wording; the
  build log says "5.00 on every pair" for the first run. Consistent, but the stronger form is from the
  apparatus note.
- Model-choice row: the log names the models (Gemini 2.5 Pro scored highest, ~120 min for 18 pairs;
  3.1 Flash-Lite at medium thinking removed the two worst failures of its minimal setting, ~10 min).
  Names kept off. "The two worst failures" = the fabricated game-master announcement and the dropped
  primary accuser of Flash-Lite's minimal setting, per the log; the row compresses that.
- The extraction bug arithmetic: the source says "deflated −1.19 (2.81→4.00)" and "lifted +0.69
  (3.19→3.88)", on n=48 with only the judge prompt changed. "Strategy lessons" = the source's
  "strategy points".
- "about four in five flags were real" restates "precision about 0.8" on 25 flagged private notes.
- "that bias could not explain the decision to keep the cheaper model": the source says "the decision
  holds, because that bias favours the model that lost". The summary model choice there was
  Haiku vs Sonnet on 6 days × 5 resamples; I kept that sample off the page and said "18 of 30".
- "I widened its bar": the experiment log says "the owner widened the gate's bar" (2026-10-18). The
  "I read the 90 flagged public messages" is "the owner read 90 flagged public messages".
- The echo-gate "direction a live filter should err" is an interpretation of the fail-safe design
  principle, labelled as such by "which is the direction ... should err"; not a measured claim.
- Open-gap wording: report.md's full record says every ten-seat expectation-judge verdict "was read"
  (reader unnamed; no agreement rate). So the page says no person has checked the current judges
  "against a labelled sample", and that reading individual verdicts does not measure agreement, rather
  than a flat "no person has checked", which that record would contradict.
- "Replies owed to another player are not gated": code says reactive turns are never gated; report.md
  says "a line answering a player who named the speaker". Verify the plain phrasing.

Mechanisms checked in code (today's code; the memory-era judges are historical): day-summary judge
prompt (evaluation/src/judges/prompts/day_summary.py); extraction judge prompt's epistemic scoping and
composed query (evaluation/src/judges/prompts/extraction.py lines 40–53); echo gate
(Agents/turn/echo_gate.py: fail open, human and reactive turns skipped, pass marker); opening filter
(Agents/turn/round_filter.py; still called from Agents/nodes/day/flow.py); calibration gate thresholds
(evaluation/src/labeling/config.py, calibration.py). Sentinel rule from the rules goldens.

Handle-with-care, deliberately left off: the missing filter-check runner named in the experiment log;
the discussion-evidence judge's blank review lines; labellers unnamed for some sets; the 79% accusation
tag agreement against an unchecked judge (dropped as a weak number, not a damaging one); model and
vendor names for the judges; costs. The "same model as the players" point is kept because it changes how
to read current judge numbers (self-preference), stated as a limitation and a next step, not a fault.
No retracted numbers used. Tests not mentioned.

Rubric self-scores (Level 2): reader orientation 2; added depth 2; conceptual coverage 2 (measure vs
act, reference-free vs reference-based, the three anchors, live fail-safe all distinct); paragraph
clarity 2; narrative economy 2 (the day-summary judge's stale section is told once in the featured
story; the rubric subsection refers back in one clause); experimental separation 2
(day-summary versions, extraction re-judging, census checks, echo-gate calibration, summariser
comparison each named with its own sample); interpretation 2 (smoke alarm vs ranking; fail-open does not
prevent a wrong but valid label; model readers are not validation); evidence and ownership 2 (first
person only for the owner's read of flags and widening the gate bar); technical accessibility 2 (rubric,
reference, anchor, kappa, noise floor explained in place); exhibits and links 2.
Word count of page copy: roughly 2,300 including tables (estimated; file total minus comments), above
the 1,200–2,000 guide. Each subsection explains a different decision, so I did not cut to the count.
Candidates if the owner wants it shorter: the summariser-comparison paragraph, or folding "Writing a
rubric" into the narrow-questions subsection.
-->
