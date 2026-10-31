# Deterministic where reliable

**The lesson.** Where a rule could be code, it became code; the model kept only what no reliable rule
could do: "deterministic where reliable; LLM only where necessary" (`gameplay/discussion/experiment_log.md`,
header). The rule replaced a decision, supplied a fact or default, held or overrode output, or graded a
decision afterwards. No rule is free of error: each inherits its inputs' errors, and some are unvalidated.

Recorded 2026-10-14, from a review of the write-up plan.

## The instances, kept apart

| Instance | What the model decided | What code decides | What the model still does | Kind |
|---|---|---|---|---|
| Discussion scheduler | Next speaker (a score with one model term) | Turn order, from obligations | Writes the line and its tags | Replaces |
| Night record, dead roster | Deaths and its own nights, from prose | The facts, written by the engine | Reasons from them | Supplies facts |
| Claim ledger | The summariser's verdict on each claim | Each claim checked against the record | Transcribes claims | Checks |
| Night-1 lot | A target with nothing to go on | A default drawn by lot | Takes it, or gives a reason | Supplies a default |
| Situation dimensions | Board counts in the lookup query | The countable fields | Writes the rest | Overrides fields |
| Echo gate | Names a repeated line | Whether the line is held | Judges what it adds | Gates |
| Credit | Outcome verdicts; reported follows | Each decision's grade | Reports the follow | Grades afterwards |
| Eliminated-player check | None: a checker parsed prose | Reads the death records | Nothing | Replaces a parser |

## 1. The discussion scheduler

**Problem.** A weighted score with one model term could not guarantee that a questioned player answered
next, and its weights had nothing to be tuned against (`gameplay/discussion/experiment_log.md` §6).
**Rule.** Who speaks is a pure function of the transcript: a `question` or `accusation` opens an
obligation, any engagement of the creditor discharges it, the freshest debtor speaks first, a per-pair cap
ends feuds (`Agents/turn/scheduler.py`, `build_reactive_queue`; `Agents/nodes/day/flow.py`). The model
writes the line and tags whom it addresses; a regex agreed with its tags on 63% of 30 cases, and all 11
disagreements favoured the model (§5, Smoke 1). A human's message is tagged by a classifier that fails
open; the human's debts are cleared from `firing_reason.owes` in code either way
(`Agents/turn/addressing_agent.py`, `Agents/turn/human_turn.py`).

**Evidence.** Same-round echo rate 0.00 sequential against 0.05–0.06 concurrent, N=4 games per arm; high
confidence on the structure, low on any quantitative delta (§9). **Not fixed.** The rules are only as good
as the tags: a seat that owed A but tagged its reply a `mention` was picked 7 times running, twice word for
word, until discharge was widened (§8); on 24 of 183 messages the tags missed an accusation a judge saw,
and once named one it did not (`gameplay/discussion_evidence.md` §7.1). **Live.** Yes; the
quiet-turn tier is now a seat-order sweep, also code (`gameplay/discussion/report.md`, status note).

## 2. The night record and the dead roster

**Problem.** Agents re-derived who had died, and as what, from the game master's prose each turn: on the
nine-seat game about 3% of messages, 4% of notes and 10% of night notes carried a role-fact error, mostly
survivor arithmetic (`gameplay/turn_prompt/experiment_log.md` §10.1). The healer's only record of its own
protections was its prose note (`evaluation/factual_errors/experiment_log.md` §8, finding 1).
**Rule.** Each death appends a `DeathRecord`; the dead-roster board and the alive-roles line (the public
census `cast_role_counts` minus revealed deaths) are rendered from them (`Agents/schemas/game_events.py`;
`Agents/prompts/prompt_formatters.py`, `format_alive_roles`). Night resolution writes each actor a private
record with a fixed result word (`Agents/rules/night_record.py`, `Agents/nodes/night/resolution.py`).

**Evidence.** With a correct board showing no wolf alive, the model still hunted "the remaining wolf" (2
and 1 of 6 against 0 of 6 without, N=6) (`gameplay/turn_prompt/validation/t1b_results.md`). With the reads
list, the bundle cut bad outputs on 100 error-prone contexts from 48% to 30%, one-sided p = 0.003 (§12):
the bundle, not the board. The night record shipped with seven other fidelity changes: bad note statements
50% → 44%, 24 cases better, 14 worse, p = 0.14 (`discussion_evidence.md` §6.4–6.5). **Not fixed.** Facts
do not fix reasoning from them: ten audited ten-seat games had 28 invalid deductions against 2 invented
facts, most about what an ability observes (§8.4). **Live.** Yes.

## 3. The claim ledger

**Problem.** Summary v3 wrote its own verdict on each role claim; nearly all were "unverified", and the next
day's summariser never saw them (`discussion_evidence.md` §6.6). **Rule.** The summariser only transcribes;
a role claim comes from a field the speaker sets, and code folds claims across days and checks each against
engine facts, silent where the record allows two readings (`Agents/rules/claim_ledger.py`).

**Evidence.** No change in hallucination overall on the bench, 31% against 32% of samples bad; messages
possibly worse, 17% → 27%, p ≈ 0.13 (§6.6). A later code rule dropping a claimed action that can only have
been done to the speaker ended an invented-claim chain on both e06 speakers, 5 of 5 → 0 of 5 (§8.4).
**Not fixed.** It checks only what the summary kept, and the summariser still errs (22 summary errors in
ten audited games, §8.4); a human's line has no claim field. **Live.** Yes.

## 4. The night-1 lot

**Problem.** With nothing to go on, the model took the lowest seat: in 28 June games seat 1 was checked on
night 1 in 21, protected in 25; shuffled lists still gave the lowest number 95 of 96 times (`discussion_evidence.md` §7.5).
**Rule.** On night 1 only, the engine draws a default seat by lot, seeded per game, night and player, and
the prompt offers it unless the actor has a reason (`Agents/prompts/prompt_inputs.py`, `night_one_lot`).

**Evidence.** On 32 replayed boards: without the lot seat 1 took 78 of 96 actions; with it the agents took
the lot in 95 of 96, actions landed on all nine seats, and no board had check, save and kill on one player (§7.5).
**Not fixed.** Agents almost never decline the lot; nine seats only; night-1 play quality unmeasured. **Live.** Yes (`95e2b4df`).

## 5. The situation dimensions

**Problem.** The memory lookup's query carried board counts the model filled. Against each case's frozen
board: `players_alive` 0.990 (bucketed), `ally_revealed` 0.975, `bullets_left` 0.164, wolf `is_swing`
0.606, below always guessing False (0.827) (`extraction/situation_dimensions/report.md`, case study).
**Rule.** The countable fields are computed from state, given to the model as facts, then re-asserted on
its output (`Agents/memory/retrieval/situation_agent.py`, `_computed_dims`, `_override_deterministic_dims`).
`distance_to_parity` and `is_swing` joined on 2026-07-11 from the public census (per the docstring; the
report predates it). The model writes the free-text fields.

**Not fixed.** The override cannot correct prose already written from a wrong number, so the facts are
injected too; the gating result keyed on the bad fills is "unknown, not false" (report, gap 1). **Live.**
In games with memory on; dimension gating is off by default.

## 6. The echo gate's hold rule

The judge names a repeated line; code holds it only on that pair, checks the named line was really spoken,
and exempts human seats and replies to an accuser (`separating_generation_from_checking.md` §3). **Live.** Yes.

## 7. Credit

**Problem.** The extraction verdict follows the side's win: per observation, weight +0.80 on the side
winning against +0.40 on the decision's grade (`memory_system/v8/decisions.md` §13); a seat's "followed"
says it adopted a lesson, not that it helped (`credit/report.md` §1). **Rule.** Each decision is graded
from the game record by a fixed table (decisions §12; `Agents/memory/consolidation/grading.py`); a lesson is
credited by lift over memory-off turns of its kind, and the grade is stored beside the verdict (§13). Read
accuracy is diagnostic; the nine-seat scorer used reads only to exclude some failures (`credit/report.md` §4).

**Evidence.** 13 of 15 sampled follows were enacted (`credit/report.md` §5); 49 lessons credited on 7
ten-seat gate games, none prunable (`memory_system/v8/experiment_log.md`, 2026-10-13); no play benefit
measured. **Not fixed.** Deterministic is not correct: the nine-seat rules rewarded concealment and
abstention advice that hurt the town (closure −0.147, p ≈ .06, 30 paired boards; `credit/report.md` §6).
The ten-seat table is the owner's judgement, and v7's prune and evict thresholds are unvalidated for ten
seats (decisions §12, §14). **Live.** Offline only: a pass over game records (`d9141ce2`), not a turn.

## 8. The eliminated-player leak check

It parsed deaths from the game master's prose, whose ten-seat night wording it no longer matched, and was
fed nothing on live games; it now reads the `DeathRecord`s (`tests/leak_test.py`, `check_eliminated_players_excluded`;
`agent_boundaries/experiment_log.md` §6). Evidence: unit tests only. **Live.** Not yet: uncommitted on 2026-10-14.

## What the instances show together

- **The rule sits in different places.** It replaces a decision (turn order, the leak parser), supplies facts
  or a default (the records, the lot), checks or holds output (the ledger, the echo gate), overrides fields
  (the dimensions), or grades a decision afterwards (credit).
- **Measurement drew the boundary, both ways.** Tagging went to the model because the regex was worse; board
  counts left it because its fills were wrong. Where no rule was reliable (what a line adds), it kept the job.
- **A rule inherits its inputs, and is a judgement too.** The scheduler runs on tags whose errors run one
  way; the ledger checks the summary it is given; the leak check was correct and fed nothing. Credit's table
  is one view of good play, its nine-seat ancestor rewarded advice that hurt, its thresholds unvalidated.

## Where it goes in the write-up

Each instance stays in its own segment: the scheduler under discussion, the records and ledger under information
fidelity, the lot under prompt biases, the dimensions under retrieval, credit under memory, the leak check
under agent boundaries. Draft for the engineering-lessons section:

> Where a rule could be code, it became code, and the model kept only what no reliable rule could do. Who
> speaks next is computed from the obligations the agents' own tags open; the dead roster, each night actor's
> record and the claim checks come from engine records, not prose; on night 1 the engine draws the default
> target a model would otherwise take from the lowest seat number. Measurement drew the boundary both ways:
> a regex lost to the model at tagging, and the model lost to arithmetic at counting the board. The rules
> have limits of their own: the scheduler is only as good as tags that missed an accusation on 24 of 183
> messages, and the credit table is a judgement whose thresholds are not yet validated for ten seats.
