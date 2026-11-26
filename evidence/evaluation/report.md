# Evaluation: how the project checks its agents, and how far to trust each check

This report explains how the project evaluates its AI agents: what it measures, how it tests a change,
and how it checks whether the measurements are reliable. Each section introduces a method and its limits;
the linked method pages contain the experiments, results and code behind it.

## In short

- **The evaluation covers the agents and the system around them.** The agents play Werewolf, a game in
  which players hide their roles, discuss whom to trust and vote each other out. Other model calls summarise
  the discussion, select which lines are spoken, and build memories from past games. Evaluation asks
  whether each part does its job, whether a change improves play, and whether the checks used to reach
  those conclusions are reliable.
- **Different questions need different kinds of evidence.** Code checks facts that can be computed from
  the game record, such as whether a vote targeted an enemy or a prompt included private information from
  another seat. LLM judges and human readers assess meaning, such as whether a summary misrepresents a
  claim. Model-generated labels need checking against human-labelled examples; agreement between models
  alone does not establish that their labels are correct.
- **A replay isolates a change; a whole game shows what follows from it.** A frozen turn reconstructs
  what an agent saw and samples its response repeatedly under each version. This helps test a prompt fix
  or investigate a particular failure. Whole games are needed to observe wins and effects that accumulate
  across turns. Replaying a known failure can show whether it still occurs in that situation, but cannot
  establish how often it occurs in ordinary play.
- **A comparison must separate the change from sampling noise and changes in the model service.**
  Repeated samples show how much answers vary. Running both versions in the same time window reduces the
  risk of mistaking a provider change for an improvement. Configuration checks also test whether the run
  matches the intended experiment. These safeguards grew out of actual failures, including a shifted
  baseline, a misconfigured memory arm and leak checkers that received no inputs. Some safeguards are
  enforced by code; others still depend on the person running the experiment.
- **The evidence is strongest for checkable facts and controlled comparisons, with a clear gap in human
  calibration.** Code checks support claims within the rules they implement; repeated replays support
  findings about the cases tested when the difference exceeds measured noise. The current ten-seat
  game's model judges and readers have not yet been checked against human labels, so their assessments
  remain provisional. The labelling tools and review packets exist, but the human review is still needed.

## The system being checked

Model calls do four jobs in the game:
- **Playing:** each seat's turns: what it says, how it votes, its night action, and the private note and
  role guesses it keeps.
- **Running the game around the players:** the summariser that writes up each day; the echo gate and the
  opening filter, which decide which lines are said aloud; and, for human seats, a classifier that tags whom
  a message addresses and helpers that draft a line.
- **Building and serving memory:** a call that turns the situation into a memory search, extraction of
  lessons after each game, and passes that clean the lessons (removing an outcome bias, tagging decisions,
  merging duplicates, distilling strategy).
- **Measuring:** LLM judges and model readers that label the other calls' outputs.

Three pieces of ordinary code are evaluated alongside the model calls: the deduction engine, which writes
certain conclusions into each prompt; the code that builds each prompt, which decides what each seat may
see; and the scores computed from game records. A model catalogue sets which model does each job.

The game has had two versions. Until July 2026 it had nine seats, ran on Gemini flash-lite, and evaluation
centred on memory. Since October it has ten seats drawn from a larger cast and runs on Claude Haiku 5.5 by
default. This page calls them the **nine-seat** and the **ten-seat** game, because a result from one does
not automatically hold for the other.

**Every model call, by job, and where it is checked.** The code behind each is in the
[source map](source_map.md).

| Job | Model call | What it does | Where it is checked |
|---|---|---|---|
| **Playing** | A seat's turn | Its line, vote or night action, with the private note and role guesses it keeps | [factual_errors](factual_errors/report.md), [metrics](metrics/report.md), [turn replays](evaluation_scopes/turn/report.md), [sampled reads](labeling/sampled_reads/report.md), [model_admission](model_admission/report.md) |
| **Running the game** | Day summariser | Writes up each day; it transcribes accusations and role claims, and code keeps the record of claims | [factual_errors](factual_errors/report.md), [llm_judge](llm_judge/report.md) |
| | Echo gate | Holds back an open-floor line that adds nothing | [llm_judge](llm_judge/report.md) |
| | Opening filter | Keeps the opening lines that are claims, results or challenges | [llm_judge](llm_judge/report.md) |
| | Addressing classifier (human seats) | Tags whom a human's message addresses, which sets who must reply | [llm_judge](llm_judge/report.md) (not yet checked) |
| | Drafting helpers (human seats) | Draft a line for the player to send | Not evaluated: the player reads and sends the line |
| **Memory** | Memory search query | Turns the seat's situation into the query memory is searched by | [llm_judge](llm_judge/report.md), [deterministic_audits](deterministic_audits/report.md) |
| | Extraction | Writes lessons from a finished game | [llm_judge](llm_judge/report.md), [deterministic_audits](deterministic_audits/report.md) |
| | De-halo pass | Rewrites verdicts in lessons that the game record does not support | [llm_judge](llm_judge/report.md) |
| | Decision tagger | Says which decision a lesson describes | [llm_judge](llm_judge/report.md), [sampled reads](labeling/sampled_reads/report.md) |
| | Dedup decision | Keeps, discards or merges a new lesson | [labeling](labeling/report.md) |
| | Point dedup | Finds duplicate strategy points in the store | [llm_judge](llm_judge/report.md), [labeling](labeling/report.md) |
| | Strategy synthesis | Distils strategy points from groups of lessons | Outside this folder: the rule screen in [`memory_system/v8/`](../memory_system/v8/experiment_log.md) |
| | Reranker (off by default) | Reorders retrieved lessons by relevance | [labeling](labeling/report.md) |
| | Namespace augmentation (built, parked) | Re-mines one role and phase of a finished game | Not evaluated |
| **Measuring** | LLM judges, the labelling panel, blind model readers | Label or score the other calls' outputs | [llm_judge](llm_judge/report.md), [labeling](labeling/report.md), [sampled reads](labeling/sampled_reads/report.md) |

## Why evaluating an LLM system is different

Many conventional unit tests use a fixed input, a known expected output and a deterministic check. Model
calls often require a different approach: several answers may be acceptable, repeated calls can disagree,
and the model used to judge an answer may also make mistakes. A hosted model service can change even when
the application's code does not. These properties shaped the methods below.

| Evaluation challenge | How it appears in this project | What the project does about it |
|---|---|---|
| Outputs vary between runs | The same frozen turn can produce different answers, so one response gives limited evidence | Sample repeatedly and compare rates or scores, with uncertainty and a check on sampling noise |
| Several outputs may be acceptable | Two summaries can use different words and both preserve the important facts | Use code for checkable fields and a reader for meaning, with explicit criteria for an acceptable answer |
| The evaluator can make mistakes | A model judge can disagree with itself or confidently assign the wrong label | Compare judges with human labels and test code checks on known faults; human calibration remains incomplete |
| Dependencies can change without an application change | A hosted model or its serving behaviour may change between experiments | Run both versions in the same time window and record their configurations; enforcement varies by runner |
| Configuration can fail silently | A requested thinking level may produce no reasoning tokens while calls still succeed | Inspect what the setting produced, rather than relying on the requested value |
| Errors propagate between components | A false claim in a summary becomes an input to later players | Check the changed component, then the decisions it affects; use whole games for consequences that accumulate |
| Evaluation has a limited budget | Repeated model calls cost money, and full games require many calls | Choose the smallest scope that can answer the question |

The game provides a useful reference: the engine records deaths, votes, night actions and claims.
Structured outputs can be compared directly with those records. Free-text statements may still need a
reader to establish what they mean before deciding whether they contradict the record.

## What the evaluation is for

**1. Does each part do its job well enough to trust?** Each component needs criteria tied to its job,
though the coverage listed above is incomplete. Players should use the available facts correctly while
reasoning about hidden roles; deliberate deception is part of the game. The summariser should
record claims as they were made; the echo gate should hold back only lines that repeat; the extractor's
verdict on a play should follow the play, not who won; the deduction engine should never write a false
conclusion; no prompt should carry another seat's secrets.

**2. Can the checks themselves be trusted?** A judge, a label or a code check can be wrong too, and a wrong
check can make an unreliable result look precise. The methods for checking them differ: compare a model
judge with human labels, give a code check a known fault it must catch, and examine whether a play score
is associated with winning. The method pages distinguish checks already completed from those still needed.

**3. Does a change make it better?** A prompt fix, a model switch or a memory feature is judged by
measuring question 1 on both versions, under controls that keep everything else the same.

The questions apply to eight subjects. Memory came first; since its research closed in July 2026 most
evaluation work has been on the others. Each subject's design folder says whether the part works; the method
pages below say how it was checked and how far that check can be trusted.

| Subject | The question | Design verdict lives in |
|---|---|---|
| **Memory** | Do stored lessons improve play, and are the fields the models write right? | [`memory_system/`](../memory_system/report.md), [`memory_system/v7/execution_plan/`](../memory_system/v7/execution_plan/report.md), [`credit/`](../credit/report.md) |
| **Retrieval (memory as RAG)** | Does the memory search find lessons that fit the situation, and do the seats use what it finds? | [`retrieval/`](../retrieval/filtering/report.md), [`extraction/situation_summary/`](../extraction/situation_summary/report.md), [`memory_system/v8/`](../memory_system/v8/experiment_log.md) |
| **Play quality** | Do prompt, rule and card changes make the agents argue, vote and talk better? | [`gameplay/`](../gameplay/report.md), [`gameplay/discussion/`](../gameplay/discussion/report.md) |
| **Model calls that run the game** | Does the summariser keep claims straight; do the classifiers label lines as intended? | [`gameplay/`](../gameplay/report.md), [`gameplay/discussion/`](../gameplay/discussion/report.md) |
| **Factual errors** | How often do agents state something the record contradicts, and does a change reduce it? | [`gameplay/`](../gameplay/report.md), [`gameplay/turn_prompt/`](../gameplay/turn_prompt/validation_plan.md) |
| **The deduction engine** | Is every line it writes true in every legal game, and does it help the seat? | [`gameplay/deduction/`](../gameplay/deduction/report.md) |
| **Models and cost** | Can a candidate model play the game's turns, and what does a game cost? | [`caching/`](../caching/report.md), [`model_selection/`](model_admission/model_selection.md) |
| **The information boundary** | Does any prompt carry another seat's private information? | [`agent_boundaries/`](../agent_boundaries/report.md) |

**Retrieval, evaluated as RAG.** The memory is retrieval-augmented generation: lessons from past games are
searched and placed in each seat's prompt. The pages never call it RAG, so here is where each standard RAG
measure lives under the project's own names.

| RAG measure | What the project did | Where |
|---|---|---|
| **Ranking quality** (precision@k, NDCG@k) | The reranker scored against graded relevance labels (not relevant, partly, fully) | [scoring](scoring/report.md), [labeling](labeling/report.md); [`retrieval/`](../retrieval/reranking/report.md) |
| **Context relevance** | The lessons seats were actually shown, read for whether each fits the situation: the precision of the top few, under another name | [labeling](labeling/report.md), [turn replays](evaluation_scopes/turn/report.md); [`memory_system/v8/`](../memory_system/v8/experiment_log.md) |
| **Query quality** | A pairwise judge comparing two versions of the call that writes the search query, and a golden set built from the queries outward | [llm_judge](llm_judge/report.md); [`extraction/situation_summary/`](../extraction/situation_summary/report.md) |
| **Recall** | Attempted, and the attempt caught a trap: a new query brings back results nobody labelled, which count as irrelevant and distort the comparison until they are labelled too | [`extraction/situation_summary/`](../extraction/situation_summary/report.md) |
| **Retrieved-memory adherence** (utilization) | Did a decision follow, contradict or ignore each lesson it was shown. This is not faithfulness: a lesson is advice, and ignoring one can be the right move | [llm_judge](llm_judge/report.md); [`credit/`](../credit/report.md) |
| **Groundedness** | Measured for the facts in the prompt, not for retrieved lessons: the factual-error checks ask whether what an agent says is supported by the game record. The lessons themselves are checked against the rules and against the game they came from | [factual_errors](factual_errors/report.md), [deterministic_audits](deterministic_audits/report.md); [`memory_system/v8/`](../memory_system/v8/experiment_log.md) |
| **Quality of the stored documents** | Duplicates scored against golden sets, synthesized lessons screened for wrong rules, verdicts corrected for outcome bias | [labeling](labeling/report.md), [llm_judge](llm_judge/report.md) |
| **End-to-end effect** | Whole-game comparisons with memory on and off; the results belong to the memory chapter | [whole games](evaluation_scopes/game/report.md) |

What is missing: recall has never been measured against a complete set of relevance labels; the adherence
and query judges have not been checked against a person; and most of this work is from the nine-seat game.

---

## The method pages

The methods answer four separate questions. A frozen turn, for example, can be scored by code or by a
reader; choosing its scope does not determine how its output should be judged.

| Decision | Available methods | What the choice determines |
|---|---|---|
| **Scope: how much of the system runs?** | One frozen turn, one day (designed, not built), or whole games | Whether the test isolates one response or includes later consequences |
| **Scoring: how is the output assessed?** | Code checks, play metrics, LLM judges or human reads | Which facts, behaviours or outcomes the test measures |
| **Validation: why trust the assessment?** | Human-labelled reference sets, tests of code checks, and checks of metrics against winning | What supports the evaluator's verdict, and where its limitations remain |
| **Controls: is the comparison fair?** | Matched inputs, contemporaneous runs, configuration guards and noise checks | Whether an observed difference can reasonably be attributed to the intended change |

The factual-error and model-admission workflows below combine these methods for recurring tasks.

**The calibration chain.** A person's labels check the judges and model readers, which then label at a
scale no person could. The chain is only as strong as its first link: on the ten-seat game no person has
checked a judge yet. Completing the owner's labelling packets would provide the reference needed for that
comparison. Code checks require a different kind of validation: their rules, inputs and implementation
must be correct, and tests must show that they detect known faults without rejecting valid cases.

**Trust marks**, taken from each method page's own verdict: ✅ sound · 🟡 usable with caveats · ⚠️ a smoke
test only · ❌ does not hold · ⏸ designed, not built.

### Judging one output

#### Code checks with no model ([deterministic_audits](deterministic_audits/report.md))

**What it answers.** Is the output right, where code can work out the right answer for itself from the game
record or the rules? A code check adds no model-call cost and gives the same result on the same input.
It can cover every supplied item, but its correctness still depends on the rule, the implementation and
the completeness of its inputs.

**How it works.** The page shows five ways of using code, one case each:
- **Check every output against a rule.** The leak checks look for private information that the acting
  seat is not allowed to see, within the fields and leak patterns they cover.
- **Compare with independent test code.** The deduction engine's conclusions are tested against a
  brute-force search of every deal of roles a player's knowledge allows.
- **Score a model's structured output against the truth.** Numbers a model wrote are recomputed from the
  board. The pattern found: the model copied the numbers it was handed correctly and got the ones it had to
  work out wrong, so those moved into code.
- **Let code narrow and a reader judge.** Code flags statements matching known error patterns, and a
  model reads those candidates to decide whether they are errors.
- **Guard the experiment's own set-up**, such as stopping a run whose sides are configured differently from
  what was declared.

**How far to trust it.** ✅ The leak checks and the deduction engine's tests provide strong evidence for
the conditions they cover. A passing check does not establish that every possible fault is absent: an
unwritten rule is not tested, and missing inputs can make a check pass without examining anything.
Known-fault tests help establish that a checker actually detects the failures it was built to catch.

**Read it when** you want to know which conditions code checks, what inputs it covers, or how the checker
itself was tested.

#### LLM judges ([llm_judge](llm_judge/report.md))

**What it answers.** For questions of meaning (is this line new, does this summary mislead), how was each
model judge built, and how far can its labels be trusted? An *LLM judge* reads another model's output and
labels it against a rubric, a written statement of what to look for. The page also covers the *classifiers
in the product*, which label the same way but whose label changes the game or the memory. They are things
to be measured, not measurements.

**How it works.** Start with a question that requires interpretation, such as whether a line repeats an
earlier claim. Give the judge the relevant context and a rubric that defines the labels, including
borderline cases. Then compare its verdicts with reference labels and inspect disagreements before using
it at scale. The page records how this was done for each judge, what configuration was used, and where
validation stopped at comparison with another model rather than a person.

**How far to trust it.** 🟡 The judges that held up asked a narrow question against facts handed to them. ⚠️
The open 1–5 quality rubrics did not: their scores hardly moved, so they could not tell versions apart. The
classifiers in today's game have been checked only against other models, and every judge now runs on the
same model as the players. That creates a potential source of shared errors or preference for similar
outputs; its effect has not been measured.

**Read it when** you need to know how a model judge was built, what it was checked against, or whether its
score provides enough evidence to support a decision.

#### Labelling: golden sets ([labeling](labeling/report.md))

**What it answers.** What reference labels exist to score a cheaper check against, who made them, and how
far can they be trusted? A *golden set* is a set of items with trusted labels. **Gold** labels are made or
checked by a person; **silver** labels are made by models alone, so they are a reference, not ground truth.

**How it works.** The page explains five techniques that make labels trustworthy: draw the items without
seeing the outcome, hide which version produced each item, fix the rubric and the pass bar before reading,
measure agreement between readers, and check against a person. It then lists every golden set by how it was
made: a person labelling everything, a panel of models with a person settling disagreements, models only, or
a written expectation per case. One lesson recurs: models agreeing with each other is not the same as being
right. A panel's confident majority was often wrong when a person reviewed it.

**How far to trust it.** 🟡 Gold sets exist only for the nine-seat game. ⚠️ Every ten-seat set is silver,
and some of them back live features. The tooling to check model labels against a person is built, and the
owner's first packets are waiting.

**Read it when** you need the reference a check was scored against, or want to know how a label set was
made.

#### Labelling: sampled reads ([sampled_reads](labeling/sampled_reads/report.md))

**What it answers.** When two versions of a prompt or feature need judging and no golden set exists, which
is better? A *sampled read* labels a sample of cases once, for that decision, and is not kept as a
reference.

**How it works.** Cases are drawn by a fixed seed, packed so the reader cannot see which version wrote each
line, read against a fixed list of questions, and scored by code. The readers are Claude subagents, not
people. Most qualitative design calls in the project were made this way.

**How far to trust it.** 🟡 Each item had one model reader, and agreement between readers was never
measured. When fresh readers re-read the same items by chance, labels about a plain act ("did the seat claim
a role?") held, while labels needing judgment drifted.

**Read it when** a design call was made by reading cases and you want to know how the read was run.

#### Scales and scores ([scoring](scoring/report.md))

**What it answers.** How is one label recorded, how is a judge scored against a golden set, and how are two
versions compared beyond chance? These are separate questions: a label describes an output, a validation
score describes the evaluator's agreement with a reference, and a statistical comparison assesses the
evidence for a difference between versions.

**How it works.** Consider a factual-error check:

1. **Record a label:** does this response contain a factual error, yes or no?
2. **Check the judge:** compare its labels with human-labelled examples. Precision measures how many
   flagged errors are real; recall measures how many real errors it finds.
3. **Compare versions:** run two prompts on the same cases and compare their error outcomes. A paired
   test uses the cases where those outcomes differ to assess whether the improvement exceeds what chance
   could plausibly explain.

An error rate alone answers neither how accurate the judge is nor whether a difference between prompts
is convincing. Sample size, uncertainty and variation in the judge's own verdicts matter too.

**How far to trust it.** 🟡 The project uses precision and recall, confusion tables, ranking scores and
statistical tests for version comparisons. Their interpretation still depends on the reference labels and
sampling design. ⚠️ No 1–5 rubric judge has been scored against human labels, so a higher rubric score is
not established evidence of better quality.

**Read it when** a report quotes a score or a test and you want to know what it measures.

### Testing a change

**A change raises two questions: did the component improve, and did that improve play?** The first can be
tested by freezing the component's input, running both versions and scoring their outputs against its job.
The second requires following the output into the decisions it affects. A player's turn replay can test
the immediate decision, but later consequences still need a broader test. Some components have only been
checked in isolation, as the table shows.

| Component | Its own unit, re-run on frozen inputs | Its effect on play |
|---|---|---|
| **Day summariser** | One day's summary, re-run on exactly the input production gave it, checked by code for known failures | The player turn that read the summary, replayed |
| **Dedup decision** | One candidate lesson, scored against human-labelled golden sets | Through retrieval checks and whole-game memory comparisons |
| **Extraction** | One finished game, re-extracted and scored by a judge and against the record | Memory lookups searched again against the rebuilt store; extraction alone was never isolated |
| **Echo gate, opening filter** | One candidate line, read blind | Not measured separately |

#### Evaluation scopes: one turn, one day, whole games ([evaluation_scopes](evaluation_scopes/report.md))

**What it answers.** How much of the game should a test hold fixed? The same experiment (change one thing,
run both versions, compare) can be run at three scopes, much like unit, integration and end-to-end tests.
Unlike software tests they are statistical: a model's answer varies, so each input is sampled many times and
the versions are compared by rate.

**How it works.**
- **[One frozen turn](evaluation_scopes/turn/report.md)** rebuilds a recorded turn exactly (the board, the
  transcript, the seat's private record) and lets each version answer it many times. It is cheap and sharp,
  and it is where most changes were tested. It estimates the change in responses on the selected cases,
  not the improvement across ordinary games. It also stops at the response: later turns do not play out
  under the intervention. Repeated samples of one turn measure variation within that situation; they do
  not provide evidence from additional situations.
- **One day** would replay a day live with the earlier days frozen, to see effects that build within a day.
  ⏸ It is designed, not built.
- **[Whole games](evaluation_scopes/game/report.md)** play the same deals with and without the change. They
  are the only way to see who wins and effects that cascade across days, and they are noisy and costly, so
  only large effects show at the sizes the project could afford.

**When to move up a scope:** when the question is an outcome over a game, when the effect builds across
turns, or when a feature must be shown running in the real game.

**How far to trust it.** ✅ Turn replays can isolate a change's effect on the cases tested. 🟡 Whole-game
comparisons include later consequences, but the small batches run here leave substantial uncertainty
about the size of an effect on winning.

**Read it when** you want to know which scope a question needs, or what a replay or a whole-game comparison
can claim.

#### Play metrics ([metrics](metrics/report.md))

**What it answers.** How well did the agents play, beyond who won? A win carries a lot of luck, so code
scores each decision instead: was the vote on a real threat, did the save keep a townsperson alive, how
close were a player's role guesses to the truth.

**How it works.** The rules define a good move; each decision is graded by them against the true roles. Each
score can then be checked for association with its side winning. That is a separate validation step:
correctly counting a useful action does not establish how strongly it contributes to winning. The healer's
save rate illustrates the distinction. It was associated with town wins in the nine-seat game, but no
clear association appeared in the ten-seat sample. There, healers made similar numbers of saves in wins
and losses; some saved players died later, and some saves coincided with another player's death. A save
remained useful without separating winning games from losing ones in that sample.

**How far to trust it.** ✅ The town's voting scores go with winning on both games. 🟡 Most new roles' scores
are graded by the rules but have too few games to check. ⚠️ The ten-seat decision grades have never been
tested against winning as a whole.

**Read it when** a report says agents played better or worse, and you want to know what was scored.

#### Experimental controls ([experimental_controls](experimental_controls/report.md))

**What it answers.** When two versions are compared, do they differ only in the change? The comparisons are
small and the models sample at random, so one silent change underneath can fake a result.

**How it works.** Two problems need separate treatment. Unintended differences between versions can
create an apparent improvement: perhaps the provider changed, or one version was scored by a different
judge. Sampling variation can also create an apparent difference or hide a real one. Matching the setup
addresses the first problem; repeated samples and uncertainty estimates address the second.

The controls have three jobs:

- **Record what ran.** Each game's runtime fingerprint identifies the model, backend, settings, prompts
  and code revision. This makes differences inspectable; a record alone does not prevent them.
- **Enforce the intended experiment.** The loop driver stops if fingerprints change within a run, and
  memory-specific guards check that the roles receiving memory match the declaration. Both versions use
  matched inputs and the same evaluator. Coverage varies by runner, as the method page records.
- **Keep the baseline current.** If a new prompt runs today, comparing it only with last week's results
  mixes the prompt change with anything the provider changed in between. Run the old prompt again beside
  the new one, preferably interleaving calls or games. Two versions already run in the same session do not
  automatically need a third run, but still need enough samples to assess noise.

A check against an absolute criterion fixed in advance does not necessarily need a baseline. For example,
a regression check can ask whether a known error recurs under the new prompt. But a criterion such as
"no worse than the current model" is a comparison and does require results from that model under comparable
conditions. Pinning a model version reduces one source of change; it does not eliminate sampling variation
or every possible change in the serving system.

The rule came from a real case. A fresh baseline once came back with the town winning far less often than
before, on identical prompts and code. Whether the model had changed or it was chance could never be
settled. That uncertainty established the rule that comparative experiments should run both versions in
the same time window. The method page records where code enforces it and where it remains a manual step.

**How far to trust it.** ✅ The controls are strong where code enforces them. 🟡 They are weaker where a
person must remember a step: interleaving a hand-run batch, never comparing across prompt versions, and
checking that a setting really did what it names.

**Read it when** you want to know why a comparison can be believed, or which control a given comparison had.

### Two worked workflows

A *workflow* is a fixed sequence of the methods above, run again and again for one recurring question. Most
subjects have one: the leak checks for the information boundary live in
[`agent_boundaries/`](../agent_boundaries/report.md), the deduction engine's tests in
[`gameplay/deduction/`](../gameplay/deduction/report.md), and the memory comparisons under memory. These two
have their own pages because they answer questions for the whole project and show the methods working
together.

#### Factual errors ([factual_errors](factual_errors/report.md))

**What it answers.** How often do agents state something the game record contradicts, and does a fix reduce
it? A *factual error* is a statement the record shows is false, or reasoning that only makes sense if
something false were true ("we must find the last wolf" when both wolves are dead). Guesses about hidden
roles and deliberate lies are not errors; they are the game.

**How it works.** Four steps:
1. **Find** errors, by screening a sample of games (code flags candidates, a cheap model reads them, a
   stronger model rechecks, a person checks the result) or by playing and reading games.
2. **Freeze** each failing turn as a test case with a written expectation.
3. **Diagnose** the cause: was the fact in the agent's input, and how was it worded? Replaying the turn with
   one thing changed tells a misleading input from a reasoning slip.
4. **Check** a fix by replaying the frozen cases to detect whether a known failure returns.

**How far to trust it.** 🟡 The frozen cases are regression checks, not a rate. The only measured rate is
from the nine-seat game, about 3 in 100 public messages. No rate has been measured on the ten-seat game.
What was tried against the errors, and what worked, is in [the gameplay report](../gameplay/report.md).

**Read it when** you want to know how a hallucination was found, counted, diagnosed or shown fixed.

#### Model admission ([model_admission](model_admission/report.md))

**What it answers.** May a model do one of the game's jobs, and with which settings? In industry this is
model migration, and the page asks it as five questions: quality, integration, cost and speed, reliability,
and rollout.

**How it works.** Candidate evaluation has three stages: short test prompts, then a replay of saved game
turns against the current model, then real games. Each catches what the one before cannot; a model can pass
every test prompt and still fail on real turns. Since late October one command runs the checks for a
candidate, with its pass criteria written down before the run. The method page records that this combined
command has not yet been run on a candidate.

**How far to trust it.** 🟡 The replay can identify a large quality deficit, but cannot reliably rank
close models: repeated runs of the same model already differ by several points. Measurement and admission
policy are separate here. While the project is experimental, quality findings are recorded but do not
exclude a model from the menu; cost, speed and integration determine exclusion. The quality check could
support a stricter admission policy later, within the limits of its cases and judge.

**Read it when** you want to know why a model is on the menu, or what a switch would need.

### Other records in this folder

- [experiment_log.md](experiment_log.md): every earlier version of this page and of the source map, kept
  whole.
- [source_map.md](source_map.md): the data every method reads, the code behind each model call, the retired
  records, and the records outside version control.
- Dated records, kept for provenance and not part of the current methods: [`loop/`](loop/report.md) (the
  checks on the July 2026 learning loop; part of the memory chapter), [`hardening_pass/`](hardening_pass/report.md)
  (the July review of the memory methods), and the retired discussion tagger
  ([llm_judge/discussion_tagger.md](llm_judge/discussion_tagger.md)).

---

## Choosing the method: two rules

**1. Code checks what has an answer it can compute; meaning needs a reader.** Code can check a structured
field against the true roles, a forbidden term in a text, a number recomputed from the board, a claim
against the engine's record, and the format of a reply. Free text often needs interpretation first. In
this project, keyword counts included matches that did not express the intended meaning, and pattern
matching could not reliably identify whom a message addressed. A reader was needed to resolve those cases.

**2. When a person reviews the flags, favour finding possible errors over eliminating every false alarm.**
A reviewer can dismiss a false alarm, but an unflagged error may never reach them. A generous screen is
therefore useful when the review workload is manageable. Also inspect a sample of unflagged items: that
is how the project can discover errors the screen misses, rather than measuring only the quality of its flags.

## What the methods caught about themselves

Auditing the evaluation changed both the tooling and the interpretation of results. The following cases
show the faults found, the safeguards added and the limits that still apply:
- **A baseline that shifted** on identical prompts, its cause never settled, which made running both sides
  together the rule.
- **A memory side set up differently from what was declared**, which became a guard that stops such a run
  before it spends anything.
- **Leak checkers that checked nothing**, because the runner never passed them their inputs; found and fixed
  the same day.
- **A thinking setting that produced no reasoning tokens.** The same behaviour occurred in both arms,
  so it did not introduce that particular difference between them. The historical memory findings apply
  to those settings; they do not establish how memory performs with a different reasoning budget.
- **A test case that let a replayed vote see its own result**, caught by reading the controls by hand.
- **A model that passed every test prompt and failed on real turns**, so real turns now count in admission.
- **An apparent benefit from later investigator discoveries weakened in a larger sample.** The early
  association with town wins was no longer statistically significant when more games were included, so
  it did not support treating later discovery as better play.
- **The healer's save rate did not retain its association with winning after the game changed.** It
  remained a count of useful actions, but needed reassessment as evidence of overall play quality.

## What holds across the methods

**What has the strongest support.** Tested code checks provide repeatable answers within their encoded
rules and supplied inputs. A vote can be scored against the true roles without asking a model to judge it.
Controlled comparisons support findings on the cases tested when the difference is distinguishable from
sampling and measurement noise. Human-reviewed reference sets support validation on the kinds of examples
they contain; they do not guarantee accuracy on every new situation.

**What remains provisional.** The ten-seat game's model judges and readers have not been compared with
human labels. Their verdicts can guide investigation, but neither the size nor the direction of an apparent
quality difference is independently validated. Using the same model family to play and judge also creates
a risk of shared errors that has not been measured.

**Where validation is incomplete.** The ten-seat game's model-generated labels lack human calibration,
and its combined decision grade has not been tested against winning. Factual-error rates have been
measured only on the nine-seat game. The deduction engine's soundness checks support the conclusions it
does emit, but evidence about useful conclusions it misses comes from only a few real cases. Replays
also have a coverage limit: many samples of one turn still represent only one situation.

**What is not running.** The nightly leak audit of games on the website is built but not installed, and the
tests run only by hand, with no continuous integration.

**Recurring interpretation errors.**

- **High scores can fail to distinguish versions.** If a judge gives nearly every output the same score,
  the score provides little evidence for choosing between them.
- **Knowing the winner can bias a judgement of an earlier move.** A judge may reward a poor decision
  because its team eventually won; this is the outcome halo.
- **Requested settings do not prove actual behaviour.** Check the returned output and usage records
  when the experiment depends on a setting taking effect.
- **Repeated samples do not expand case coverage.** Twenty replies to one turn show variation in that
  situation, not performance across twenty different situations.
- **Keyword matches need interpretation.** A role name appearing in a sentence does not establish that
  the speaker claimed that role.
- **A frozen-turn test stops before the consequences.** Changes to later replies, votes or survival
  require a test that lets those events unfold.

## What we would do differently next time

| Stage | Change | What it would buy |
|---|---|---|
| Design | **Check every judge and reader against human-labelled examples when it is built** | An estimate of its errors on the reviewed sample, with uncertainty and examples of disagreement |
| Design | **Use the role registry for faction membership, with explicit rules for role-specific actions** | Fewer errors when the cast changes; new abilities still need their own scoring rules and tests |
| Testing | **Choose the measure and decision criterion in advance, and establish the relevant noise floor** | Less freedom to select a favourable result after seeing the data, and a basis for interpreting small differences |
| Records | **Preserve each cited run's outputs and the script behind each statistic** | Reported statistics can be recomputed from saved outputs, even when new model calls would differ |
| Operations | **Run code checks automatically, and install the leak audit with the server** | Covered regressions and leaks can be detected without someone remembering to run the checks |

The next priority is to complete human review of the ten-seat labelling packets and measure where the
model judges agree or disagree with those labels. That would strengthen the assessments of meaning that
code cannot resolve. It would not replace the need for broader game samples, regression coverage or
automatic execution of the existing checks; each addresses a different gap.

*Rewritten 2026-10-24 as a standalone overview; restructured 2026-10-25 into one block per method page, then
rewritten the same day to explain the methods conceptually, with the numbers left to the method pages. Every
earlier version is kept whole in the [experiment log](experiment_log.md). The memory campaign's verdicts live
in [`memory_system/report.md`](../memory_system/report.md) and
[`../memory_system/v7/execution_plan/report.md`](../memory_system/v7/execution_plan/report.md).*
