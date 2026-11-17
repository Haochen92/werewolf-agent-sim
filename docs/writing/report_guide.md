# Experiment report and log guide

*Draft of 2026-11-17, checked by a fresh reader, not yet read by the owner. Written to be copied
unchanged into another project.*

This guide covers the experiment log and the experiment report. `core_rules.md`, in this folder,
covers general writing quality and is read first. Examples come from the Werewolf project, a game
played by AI agents.

**Which document wins when two disagree:** the core rules, then this guide, then example records
the owner has approved.

## 1. Two records for each experiment

Every experiment has a log and a final record, kept in one folder. The final record is usually an
experiment report (section 3 lists the other kinds).

- **The log** is written while the work happens, in date order. Its header says what the
  experiment is, where its code is, and that later entries take precedence over earlier ones. An
  entry is never rewritten to reflect a later result; a correction is added as a new dated entry
  or a dated note. Each
  round of runs ends with its result and the decision taken.
- **The report** is written when the work ends and is organised by findings, not by the order of
  the work. It can be read without the log. Dead ends and minor mistakes stay in the log.

The code that ran the experiment lives with the project's evaluation code, and the records point
to it (section 7). Werewolf example: records in `evidence/<experiment>/`, code in
`evaluation/experiments/`.

## 2. The plan, written in the log before any run

Before the first run, the log states:

- the question, and the expected answer if there is one;
- the arms, meaning the versions being compared, and how each differs;
- what is held fixed (model, settings, data, prompts), and what cannot be held fixed, such as
  random variation between repeated model calls;
- the measures, the main one first, and the sample size for each arm;
- which results would support the expected answer, and which would count against it;
- the estimated cost in money, with an upper bound.

If the question is about a cause, include an arm that separates that cause from other
explanations. Before spending money, check that the arms differ only where intended, for example
by comparing their prompts line by line, and record that check.

Example: a Werewolf test asked whether a player could move the AI players' votes by typing a fake
game-master announcement into a message. In round 1, one arm saw 26 of 27 votes go to the accused
player. With no arm in which the player made the same accusation openly, round 1 could not show
whether voters were fooled about who spoke or only persuaded. Round 2 added that arm.

## 3. Choosing the kind of final record

| Kind | Use it when |
|---|---|
| Experiment report | Arms were run and an outcome was measured |
| Decision record | A design or method was chosen without a measurement |
| Negative finding | Without a controlled comparison, the work ruled an approach out |
| Reference document | Readers need the current design more than its history |

## 4. Outline of an experiment report

1. Title, then a short opening: the answer, its date and its scope.
2. The question: what the system does, and what was asked about it.
3. Setup: the arms, what was held fixed, the measures, the sample size and the cost.
4. Results: one subsection per finding.
5. How sure the findings are: what they rest on, and what was not checked.
6. Decision: what was adopted or rejected, and why.
7. Open items: questions still open, and planned work.
8. Artifacts: the code, the data and what produced them (section 7).

## 5. Presenting a result

Open each finding with its own question and a one-line answer in bold. A table holds one
comparison, such as the arms on one measure: state its takeaway before it, and explain any
surprise after it.

Explain each measure before the first table that uses it: what it counts, why it was chosen, and
how it was checked. A count not checked against hand labels, such as a keyword search, is called a
rough count and given with how often a hand check agreed with it.

Quote at least one real instance of what was measured, such as a model's stated reason. A reader should understand every result without opening a link.

## 6. How strongly to state a result

In addition to core rule 5 (sample size, untested explanations):

- Scope each verdict (the stated answer to a question) to what was tested: the model, the data,
  the system version, the sample size and the measure.
- Report a null result from a small sample as "no effect detected at this sample size", never as
  "no effect", and say what size of change it could have missed.
- State a design claim as a pair: what the design controls, and what it does not. Example:
  rerunning saved inputs fixes the data, but the model's answers still vary between calls.
- When any result in the experiment, even a weak one, points against an explanation, the verdict
  says so.

## 7. Traceability

Each result carries what produced it: the commit, any uncommitted changes, the configuration and
model settings, and where the data is stored. The experiment's code saves these with the data, and
the report lists them in its artifacts section, not in the middle of sentences.

Point to code by a name that stays valid when files move, such as a registered command name. Give
a line number only when that exact line is the point.

A retracted number gets a dated correction note where it appears, in either record, and is never
cited again. Apart from such notes, the report mentions a mistake only when it changed the method.

## 8. Checklist

1. Was the plan, with what would count against the expected answer, logged before the first run?
2. Are the log's earlier entries left as written, apart from dated corrections?
3. Does each table make one comparison, with its takeaway first?
4. Is each verdict scoped to the model, data, sample size and measure?
5. Is each small-sample null result stated as "no effect detected at this sample size"?
6. Can each number be traced to a commit, a configuration and a data file?
7. Are retracted numbers absent, except in their correction notes?
