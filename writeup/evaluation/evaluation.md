# Evaluation chapter (draft)

Level 1 page copy. The chapter's structure is in [`content_plan.md`](content_plan.md); each Level 2 page
has its own folder here, with its Level 3 pages beside it; exhibits and where they come from are in
[`exhibits/source_map.md`](exhibits/source_map.md). The writing rules and the handle-with-care list are in
[`../map.md`](../map.md), "Chapter outline: Evaluation". Lines marked **Exhibit**, **Link** and
**Evidence** are specs for the page, not page copy.

---

## Level 1: the Evaluation page

### Evaluation: assessing the agents and the systems around them

The agents need to reason about incomplete information, discuss their suspicions, make decisions and
remember what happened. Their behaviour also depends on supporting components: a misleading day summary
or a filter that suppresses useful discussion can affect later decisions. Evaluation therefore covers
both individual components and the game as a whole.

The challenge is separating an improvement from variation between runs. The same input can produce
different responses, and one changed response can alter the rest of a game. I combined component-level
evaluations, including frozen-turn replays for diagnosing failures and testing fixes, with end-to-end
game evaluations to observe later consequences. Decision-level scores provided additional measures of
play quality when win rates alone required more games than the project could afford.

Where the game record supplied a checkable answer, I used deterministic code checks. Questions about
meaning required human review or LLM-as-a-judge: a model assessing another model's output against stated
criteria. That introduced another question: how reliable was the evaluator? Controlled comparisons and
checks of the evaluators supported decisions about prompts, supporting components and model choices.

The sections below explain those decisions, what the tests established and where the evidence remains
incomplete.

#### What makes the evaluation difficult

Repeated model calls can disagree, and one component's output becomes another's input. These challenges
also occur in other software systems; here they shape what an evaluation must hold fixed and what it
needs to observe.

| Challenge | Example in this project | Where it is addressed |
|---|---|---|
| Sampling variability | The same recorded turn can produce different votes | Turn replays and whole games; fair comparisons |
| Evaluator error | A model judge can assign an incorrect label | LLM judges; reference labels |
| Possible changes in the model service | A baseline shifted on identical prompts; the cause remained unresolved | Fair comparisons |
| Silent configuration failures | A requested thinking level produced no reasoning tokens, without an error | Fair comparisons; models before switching |
| Errors propagating between components | A false claim in a day summary becomes input to later players | Factual errors; turn replays and whole games |

**Exhibit (diagram).** Two separate choices, with validation and controls labelled alongside them.

- **Scope:** frozen turn → one day → whole game. The day is dashed and labelled "designed; not
  implemented".
- **Scoring:** code checks and play metrics, LLM judges, human reads. These can be used at different scopes.
- **Validation:** a labelled connection from human examples to the judges: "check judge accuracy".
  Mark the current game's calibration as pending, rather than implying that all judges are calibrated.
- **Controls:** a short caption, "Compare versions on matched inputs, under comparable conditions;
  account for sampling variation." These apply across scopes, rather than forming another rung.
- No costs on the diagram.

### Does each part do its job?

#### Finding and fixing factual errors

When an agent states something the game record contradicts, error analysis starts with the information
it received. In one game, the investigator announced a check it had never made, and the village voted
out an innocent player. I rebuilt that turn from the saved state to compare possible fixes on the same
situation.

With the original input, all 20 responses invented an investigation. With the results reworded, all 20
reported the real check. The turn was retained for regression testing: checking whether the failure
returns after later changes. This supported a fix for one recorded situation; it did not measure the
frequency of errors across games.

**Link:** Explore how failures become regression tests → [Level 2](factual_errors/factual_errors.md).

#### Measuring play quality beyond win rate

A win depends on the role deal and many interacting decisions, so small batches of games provide limited
evidence of playing strength. I therefore used decision-level scores as candidate proxy metrics for
play quality. Code checks, for example, whether a vote targeted an enemy or a protection saved a
townsperson.

I also checked whether those scores were associated with winning. After the game expanded from nine to
ten players, the healer's save rate no longer distinguished winning games from losing ones in the
analysed sample. A save remained a useful action, but counting saves accurately did not establish their
rate as a reliable proxy for winning in the new game.

**Link:** Explore how play metrics were defined and validated → [Level 2](play_metrics/play_metrics.md).

### Can the checks be trusted?

#### Checking agent outputs with code

When an answer can be computed from the game record, a deterministic check can assess it without a
model judge. One audit recomputed the situation fields a model supplied to memory search, then compared
them with its answers. The “swing vote” field was correct in 61% of 439 cases; always answering “no”
would have scored 83%.

That changed the interpretation of an earlier experiment. Ranking memories by unreliable fields
could not establish whether the matching idea itself was useful. The computable fields moved into
code. Those checks still depend on correct rules and complete inputs; testing them with known faults
helps establish that a passing result means something was actually checked.

**Link:** Explore code-based checks and how they were tested → [Level 2](code_checks/code_checks.md).

#### Designing and validating LLM judges

Whether a summary misrepresents a claim is a question of meaning. An LLM judge assesses such outputs
using a rubric: explicit criteria for assigning a label or score. The useful judges in this project
asked narrow questions and received the facts needed to answer them.

Broader 1–5 quality rubrics caught obvious defects, but their scores clustered near the top and could
not distinguish versions. A high score therefore did not establish which version was better, and those
design decisions needed other measures. The current game's judges still need validation against
human-labelled examples. Review packets are ready, but until that work is completed, their assessments
remain provisional.

**Link:** Explore rubric design and judge validation → [Level 2](llm_judges/llm_judges.md).

#### Building reference labels and reviewing outputs

Checking a judge requires reference labels whose quality has also been examined. Three models labelled
863 memory cases as duplicates or useful additions. In the reviewed cases, a “discard” majority was
wrong 37% of the time; review also overturned about a fifth of unanimous discard decisions.

Agreement alone had hidden shared errors. Reviewing only disagreements would have missed them, so a
reference set needs scrutiny of agreed labels too. Later panels mixed vendors, which did not remove
the need for review. One-off comparisons used blind review: readers saw a fixed rubric and examples
with version names hidden. Those readers were models, so blinding reduced one source of bias without
establishing human agreement.

**Link:** Explore reference labels, model panels and blind review → [Level 2](reference_labels/reference_labels.md).

### Does a change make it better?

#### Choosing between turn replays and whole games

A turn-level evaluation holds a recorded situation fixed while generating responses under each version.
This makes it possible to test a proposed fix without replaying an entire game. When night-one attacks
favoured the lowest-numbered seat, a replay tested whether shuffling the player list would help. In that
screen, the attacks still followed the seat number, so shuffling did not address the bias.

A replay regenerates the selected response; it does not let later players react to it. End-to-end game
evaluations include those consequences, but require more calls and introduce more variation. Replaying
one live day could bridge the two scopes. That intermediate test is designed but not implemented.

**Link:** Explore what turn replays and whole games can establish → [Level 2](replays_and_games/replays_and_games.md).

#### Designing fair comparisons

A controlled comparison aims to isolate the intended change. Matched starting deals, unchanged settings
and one evaluator for both versions reduce confounding factors: other differences that could explain
the result. Sampling variability remains. Repeating an unchanged configuration, or re-judging the same
outputs, helps assess how much variation comes from generation or measurement alone.

A fresh baseline once produced fewer town wins despite identical prompts and code. A paired analysis,
comparing outcomes on the same starting deals, did not rule out chance; the cause remained unresolved.
That uncertainty established the requirement to run compared versions in the same time window. Some
runners enforce it; others still require manual scheduling.

**Link:** Explore baseline checks, experimental controls and paired comparisons → [Level 2](fair_comparisons/fair_comparisons.md).

#### Evaluating models before switching

Candidate evaluation has three stages: short integration probes, quality checks on saved turns, and
real games. Each answers a different question. One model passed all 27 short probes, then returned prose
instead of a usable move on three of six real turns. Passing a small format test had not established
that it could handle realistic game inputs.

Quality replays also have limits: two runs of the same model differed by about six percentage points
in error rate. They can identify large deficits, but cannot reliably rank close candidates. Admission
policy is separate: the experimental menu excludes models for cost, speed or integration problems;
quality findings are measured and recorded without automatically excluding a model.

**Link:** Explore model probes, replay quality and live-game checks → [Level 2](model_admission/model_admission.md).

<!-- Authoring sources for the revised Level 1 copy (2026-10-25):
Introduction and challenge table: evidence/evaluation/report.md; requested thinking level produced no
reasoning tokens, not evidence that the model performed no reasoning. Baseline cause remains unresolved.
Factual errors: four versions, 20 samples each (game_play_enhancement/discussion_evidence.md §6.2);
factual_errors/report.md steps 2–4 for diagnosis, retained cases and replay-versus-rate distinction.
Play quality: metrics/report.md §2–4; healer +0.36 nine-seat versus −0.03 ten-seat (75 games,
95% interval −0.26 to +0.20). Association, not causation; decision scores are candidate proxies.
Code checks: swing vote 61% of 439 versus always-no 83%; computable fields moved into code
(deterministic_audits/report.md, case 3). Threshold details, if expanded, come from the corrected
experiment_log.md: bucketed players alive ≥90%, swing vote ≥80%; bullets outside the predeclared rule.
LLM judges: llm_judge/report.md cases 1 and 5; broad scores caught gross faults but could not rank
versions. Current calibration packets pending (labeling/report.md). Fail-open claim removed here.
Reference labels: labeling/report.md case 2; 863 cases, discard majority wrong 37%, 21% of unanimous
discards flipped. Review by the owner with Claude; 246 unanimous keep cases were trusted. Mixed-vendor
panels still need review. sampled_reads/report.md §2 for hidden versions, rubric and model readers.
Scopes: evaluation_scopes/turn/experiment_log.md, "Night-1 target check": shuffle screen and seat-number
bias; evaluation_scopes/report.md for the designed but unbuilt day scope.
Fair comparisons: experimental_controls/report.md; paired shared-deal analysis 12 versus 7 wins,
p = 0.18, cause unresolved. Unchanged-arm repeats assess generation variation; re-judging saved outputs
assesses evaluator variation. Same-window enforcement varies by runner.
Models: model_admission/report.md §1–2; 27 probes, 3/6 real turns in prose; repeated quality runs differ
by about six percentage points. Cost, speed and integration determine exclusion; quality is recorded.
Featured story: discussion_evidence.md §6.2 (quote, note, four-version table, reading the replies, fix);
factual_errors/experiment_log.md §5 (one turn; two wording changes); shared prompt formatter.
-->
