# Experiment log and report guide

*Draft 4, 2026-11-17. Examples come from the Werewolf project, a game played by AI agents.*
<!-- Written to be copied unchanged into another project. -->

`core_rules.md`, in this folder, covers general writing quality and is read first. When documents
disagree, the order of precedence is: the core rules, then this guide, then existing records.
Existing records show the depth and content expected. They are not models of prose; the core rules
are.

## 1. The records, and what they are for

The records preserve the reasoning behind how the software changed. Months later I should be able
to answer: what problem I was solving, which alternatives I considered, what the evidence showed,
why the current design was chosen, and what I can claim about it.

Records are organised by the question they investigate. One folder holds the records for one
question:

| Record | What it is | When it is written |
|---|---|---|
| **The log** | The investigation as it happened, in date order, including approaches that failed and the reasoning at the time | Continuously. New entries are added; earlier entries are not rewritten |
| **An experiment report** | The answer to one question that was investigated through a defined comparison, or through a related series of them | When the experiment ends. Afterwards it changes only by dated correction notes |
| **A topic report** | The current design of one part of the system, and the decisions and evidence behind it, drawn from several experiments | Maintained: revised whenever the design or the evidence changes |
| **A decision record** | A choice made without a measurement, including a choice not to pursue an approach | When the choice is made |

A folder has one log and usually one report. Which report depends on the work: one comparison
gives an experiment report; a design that developed over many experiments gives a topic report.

**Before creating a folder, check whether the work continues an existing investigation.** Add to
the existing log when the work extends the same question or decision. Create a sub-folder, with
its own log and report, when the work asks a distinct question that needs its own evidence and
conclusion. The report of the parent folder then gives each sub-folder's conclusion in a sentence
or two and links to it.

The code that ran an experiment is kept with the project's evaluation code, and the records point
to it. Links between files in the repository are relative paths.

## 2. The log

**An entry is never rewritten to match a later result.** A correction is a new dated entry, or a
dated note beside the original. Only the log preserves what I believed before the evidence changed
my mind, and that earlier belief is what explains why an abandoned design was reasonable.

**An entry about something I ran or decided lets a future reader reconstruct the reasoning and
the outcome.** It records the question; the approach and why I chose it; the alternatives I
considered, when there were any; what actually happened; how I interpret that; and what I decided.
Say which stage each thing reached: proposed, implemented, tested or deployed. Keep the
interpretation separate from the result, so the reader can see which statements were measured.
Headings are optional, and something I merely noticed needs only a few sentences.

**Write each entry so that it can be understood months later by someone who was not there.** It
is not shorthand for what the writer currently has in mind. A later report may be written by
someone, or by an agent, with no access to that context, so the entry keeps the causal reasoning
and the background needed to understand the result.

**Work is either a planned comparison or exploratory.**

| | Planned comparison | Exploratory work |
|---|---|---|
| What it is | Runs made to answer a stated question by comparing versions | Looking: debugging, or re-running something unexpected to see whether it happens again |
| What the log needs first | The agreed plan, written before the first run | Nothing. It is recorded as it happens and labelled exploratory |
| What its result may be called | A finding, limited to what was compared | It depends on the claim, as the next paragraph explains |
| Where it is recorded | The folder for its question | The log of the work during which it came up |

**What exploratory work can establish.** A defect that was reproduced directly, or behaviour of
the code that was verified, is a finding: no comparison is needed to say that a crash happens. An
observation that suggests a cause or an improvement is a hypothesis until suitable evidence tests
it. An uncontrolled comparison is never presented as proof of a cause.

**The plan for a planned comparison** is the design as finally agreed, not the discussion that
led to it. If a detailed plan is saved elsewhere, link to it; do not rely on anything that is not
saved. The entry after the run records what was actually run and any departure from the plan. The
plan states:

- the question, and the expected answer if there is one;
- the versions being compared, called arms, and how each differs;
- what is held fixed, and what cannot be held fixed (for example, a model's answers vary between
  repeated calls);
- the measures, the most important first, and the sample size for each arm;
- which results would count against the expected answer;
- the estimated cost in money, with the most I am willing to spend.

If the question is about a cause, include an arm that separates that cause from other
explanations. Before spending money, check that the arms differ only where intended, for example
by comparing their prompts line by line, and note the check in the log.

*Example.* A test asked whether a player could move the AI players' votes by typing a fake
game-master announcement. In round 1, 26 of 27 votes went to the accused player. Round 1 had no
arm in which the player made the same accusation openly, so it could not show whether voters were
deceived about who spoke or only persuaded. Round 2 added that arm.

## 3. The reports

**Outline of an experiment report:** the answer, with its date and what was tested; the question;
the setup (arms, what was fixed, measures, sample size, cost); the results, one subsection per
finding; how sure the findings are, in plain words (what they rest on and what was not checked);
the decision; open items; the code and data.

**Outline of a topic report:** the current design, described as it behaves today; the problem and
the requirements; the important mechanisms; the decisions; the limitations; links to the detailed
records.

In a topic report, write each decision in this order: the decision and the reason for it, the
alternatives considered, the finding the decision rests on, the supporting experiments one at a
time, and then what the decision costs and what it leaves unresolved. The reader should be able to
see which result supports which conclusion.

**A topic report states which version of the system it describes.** At the top it gives the commit
of the implementation it describes (or the date, if there is no single commit) and the date it was
last reviewed. When the design changes, revise the report and update both. Describe past
experiments in the past tense with their dates, so that the current design and the history cannot
be confused.

**A decision record** gives the options, the reason for the choice, and what evidence would change
it. It may rest on a hypothesis if it labels it as one.

## 4. Presenting a result

These are defaults. Use each where it makes the result clearer.

- Open a finding with its question and a one-line answer.
- Give a table one comparison. State what it shows before it, and explain any surprise after it.
- Explain a measure before the first table that uses it: what it counts and how it was checked.
- When a count comes from an automatic method that was not checked item by item, such as a keyword
  search, call it a rough count. Give it with the result of a hand check on a sample, for example
  "a hand check of 16 agreed on 14".
- Quote a real instance of what was measured when it helps the reader picture the result.
- State each result and what it applies to in the report itself. A link gives the detail; the
  reader should not need to open it to understand the result.

## 5. How strongly to state a result

These add to core rule 5, which covers sample size and untested explanations.

- Limit each conclusion to what was tested: the model, the data, the version of the system, the
  sample size and the measure.
- A failed version shows that the tested version failed. It does not show that the approach cannot
  work. A decision not to pursue the approach says so in those terms.
- When a small sample shows no difference, write "no difference observed in this sample". Write
  "no effect detected" only when a statistical test was run. Give the size of effect that could
  have been missed only when an analysis supports that number; otherwise say that it is unknown.
- State what the design of an experiment controls and what it does not. Example: replaying saved
  inputs fixes the data, but the model's answers still vary between calls.
- When any result, even a weak one, points against an explanation, say so where the explanation is
  given.

## 6. Traceability

Each result is recorded with enough to reproduce it: the commit, whether there were uncommitted
changes, the configuration and model settings, and where the data is stored. Where code runs the
experiment, the code saves these with the data. For an investigation done by hand, write them in
the log entry. An experiment report lists them in its last section. A topic report links
each result to the record that holds them.

Point to code by a name that stays valid when files move, such as a command name. Give a line
number only when that exact line is the point.

A retracted number gets a dated correction note where it appears and is never cited again. Apart
from such notes, a report mentions a mistake only when the mistake changed the method, the
results, how the results are interpreted, or the current implementation.

## 7. Checklist

1. Is this the right record: a log entry, an experiment report, a revision of a topic report, or a
   decision record?
2. For a planned comparison, was the plan in the log before the first run?
3. Is exploratory work labelled, and is a hypothesis not presented as a finding?
4. Could someone who was not there understand each new log entry, including why the approach was
   chosen?
5. Can the reader see which result supports each decision?
6. Does a topic report state the version it describes?
7. Can each number be traced to a commit, a configuration and a data file?
