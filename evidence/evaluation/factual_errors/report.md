# Factual errors: finding them, counting them, checking a fix

This page covers how the project finds and measures factual errors in what the agents say: why it
matters, the two questions the methods answer, where they were used, and how far each result can be
trusted. How this fits with the other ways the project evaluates is in [the hub](../report.md). The full
detail (every count, commit and correction, plus the October code audit and its fix check) is in
[the detailed record](experiment_log.md). What was tried against the errors, and what worked, is in
[the gameplay report](../../game_play_enhancement/report.md); the full detail is in the design records:
the [July validation plan](../../generation_prompt/validation_plan.md) and
[discussion_evidence](../../game_play_enhancement/discussion_evidence.md) §6 and §8.

## Why factual errors

A *factual error* is a statement the game record contradicts: a player claims a check it never made,
hunts "the last wolf" when both wolves are dead, or calls a revealed wolf the serial killer.

**They are not rare, and one can decide a game.** In July 2026 about 3% of public messages carried one.
In a live game on 2026-10-03, the investigator announced a check it never made, the village voted out an
innocent player on that claim, and the serial killer won.

**They are hard to measure for two reasons at once.** Whether a statement is wrong is a question of
meaning, so a reader has to decide it, and code cannot. But errors are rare, so reading every message to
find them is too much for a person. The methods below split the work: code narrows, models read, a
person checks.

**The work has two goals.** A *rate*: how often errors happen in real games. And a *regression set*:
failing turns frozen as test cases, replayed against every prompt or model change, so a fix can be
shown to work and a fixed failure stays fixed. Most of the method below serves the second.

## What counts as a factual error

### The rule, in plain words

A statement counts as a factual error when it says something the game record shows is false, or when
its reasoning only makes sense if something false were true.

**What "the game record" means here.** When a game finishes, the batch runner saves one record of it.
For each statement, code builds a fact sheet from that record, cut off at the day the statement was
made: everyone's true role, who died each night and who killed them, how everyone voted and who was
voted out, and what the speaker privately knew (its own night actions and results). Role claims are the
one exception to "recorded by the game". In the July census they came from the list of claims the day
summary wrote at the end of each day, so a claim made earlier the same day was not in it yet, and the
reader was told never to flag a claim about something said that day. That has since changed: in the
ten-seat game (from October 2026) each player states its own claim in a structured field on its
message, code keeps a claim ledger from those fields, and the summary's list is only a fallback for
players who filled none (a human, or games from before the field). The census has not been run on
games with the new field. Only these count as facts. A player's guesses,
opinions and unrecorded chat are not facts, so a statement about them cannot be an error.

**Two ways a statement can be wrong:**

1. **It says the false thing outright.** "player_3 was the healer", when player_3 was revealed as the
   investigator. Or "I abstained yesterday", when the record shows the player voted.
2. **It never says the false thing, but its reasoning depends on it.** Most errors look like this.
   - "We have to find the last wolf before tonight", when both wolves are already dead. It never says
     "a wolf is alive", but the plan only makes sense if one is.
   - "I'm suspicious of player_4", when player_4 is dead. It treats a dead player as someone still in
     the game.
   - Hedging does not excuse it: "if the wolf is still out there, it's probably player_2" still counts
     when no wolf can be alive, because the reasoning treats something impossible as possible.

**What does not count:**

- **Talking about the past.** "Who voted for the investigator?" after the investigator died is fine:
  those votes really happened. Getting the past wrong still counts ("the wolves killed player_6", when
  the serial killer did).
- **Being unsure about something still hidden.** "player_5 might be the sentinel", when that role has
  not been revealed, is a guess, which is how the game is played.
- **Loose wording.** "Let's find the remaining wolves" with one wolf alive is read as "at least one".
  Only an explicit number ("two wolves", "the last wolf") is a claim about how many. With no wolves
  alive, any "remaining" counts.
- **A deliberate lie.** If a player says something in public that contradicts what it privately knows
  (a wolf lying about its packmate's role), that is deception, which is part of the game, and it is
  labelled separately. A private note has no audience, so a wrong private note is always counted as a
  genuine mistake.

**Why it happened does not matter to the count.** A miscount, a forgotten death and an invented event
all count the same. Finding out why is a separate step (step 3 below).

### Why almost everything can be checked

People usually split hallucinations in two. One kind contradicts the information the model was given.
The other kind adds something the information neither confirms nor denies, which is much harder to
check.

This game makes the first kind almost universal, because the engine writes everything down: every
death, role reveal, vote, night action and claim. So when an agent invents something, the record
contradicts it, and the invention can be caught by comparison. The statements the record cannot check
are not treated as errors: guesses about who holds which role are the point of the game (they are scored
separately, as reads), what someone said earlier the same day is not in the record yet, and nothing in a
game needs knowledge from outside it.

## The workflow

Every factual error the project dealt with went through the same steps, whatever its cause:

1. **Find errors**, by counting them on a sample of games, or by playing games and reading them.
2. **Turn them into test cases**: freeze each failing turn so it can be replayed, and keep only the
   errors that reproduce.
3. **Find the cause** of an error: check whether the fact was in the agent's input. If not, find where
   the code lost it; if it was, replay the turn with one thing changed.
4. **Run the test set** to check a fix or choose a model: the same cases before and after the change,
   scored by the same judge.

The table lists every method by the step it serves:

| Step | Method | What it produced | Trust | Detail |
|---|---|---|---|---|
| 1. Find | The census (July 2026, nine-seat) | The only error rate: about 3% of public messages (68 of 2,292), 4% of private notes | ✅ code screen · 🟡 model reader | log §1 |
| 1. Find | Playing games as a human, and reading games against a rubric (October 2026) | Specific failures from real games, sorted by kind for ten games; no rate | 🟡 (rated in [sampled_human_review](../sampled_human_review/report.md)) | log §6 |
| 2. Freeze | The nine-seat test set (built 2026-10-03) | 129 cases: turns that still fail, controls, a random slice, pinned failures | 🟡 | log §3 |
| 2. Freeze | Ten-seat pinned cases (October 2026) | Failing turns from ten-seat games, each with a written expectation | 🟡 | log §6 |
| 3. Diagnose | Reading each failing turn's input by hand | The cause of most errors: whether the fact was given, and how it was worded | 🟡 (one reader) | step 3 |
| 3. Diagnose | The code audit and its fix check (2026-10-03 and 04) | 12 places where facts were lost on the way into a prompt; 8 fixed in a day, 4 partly | — (a code reading, not a measurement) | log §8–9 |
| 3. Diagnose | The invented-check replay (2026-10-03) | The cause of one invented check: the wording of its results (20 of 20 against 0 of 20) | ✅ for that one turn | log §5 |
| 4. Check | The July ship test, T1c (nine-seat) | The July prompt change: 48% of error-prone turns wrong before, 30% after (p=0.003) | 🟡 | log §2 |
| 4. Check | Versions run on the nine-seat test set (October 2026) | A noise floor, and the first clear effect: a higher thinking budget cut bad samples 82 → 27 of 267 | 🟡 | log §4 |
| 4. Check | Ten-seat pinned replays and the summary-claim replay | Whether known ten-seat failures still happen after a fix | 🟡 | log §6–7 |
| — | A rate on the ten-seat game | Never measured | ⛔ | below |

✅ sound · 🟡 usable with caveats · ⛔ underbuilt.

---

## Step 1. Finding errors

There are two ways to find errors, and they answer different questions.

### Counting them on a sample of games: the census

**What it answers.** How often errors happen: the only rate in the project, over 50 nine-seat games in
July 2026.

**How it works.** A cascade, each layer doing what it is good at.
1. **Code narrows.** Four rules, each comparing the text with the game record, pass a statement on
   only if it names a dead player, uses a role word whose holders are all dead, states a count of a
   role that does not match how many are alive, or credits someone with a claim not in the claims list.
   Of 7,846 statements, 2,461 went on.
2. **A cheap model reads every candidate, set to catch too much**, against the fact sheet. It writes
   the decisive phrase, a reason, a verdict, and which fact was wrong.
3. **A stronger model re-reads what the first one flagged.**
4. **The owner checks:** all 90 flagged public messages, a sample of 25 flagged private notes, and a
   sample of 15 statements the stronger model threw out.

**What it found.** About 3.0% of public messages (68 of 2,292) and about 4.0% of private notes carried
an error; night-action notes were the worst (9.6%). The 368 errors the models confirmed, sorted by which
fact was wrong:

| Kind | How many | Example |
|---|---|---|
| Wrong count of who is left | 221 | Hunting "the remaining wolf" when none can be alive |
| Something invented | 59 | "I abstained" when the record shows a vote; an attack that never happened |
| A dead player treated as alive | 57 | Suspecting someone who already died |
| A claim credited to the wrong player | 18 | "player_2 claimed healer" when player_2 never did |
| A dead player's role misstated | 13 | Calling a dead player the healer when they were revealed as something else |

**How far to trust it.** The public rate rests on a full hand read of its flagged messages; the private
rate on a sample of 25. In the sample of thrown-out statements, 2 to 3 of 15 were real errors, so the
counts are floors. The class each error was given was never checked by hand.

Each statement is judged on its own, so an error that other players repeat counts again each time.
Errors cluster (the worst game-day had 24), because one player's false premise becomes the room's
starting point. The rate is therefore how often a false statement appears, not how often a model
invents one on its own, and many of the errors were made on input that already carried the false fact.

The screen sees only what its four rules cover. An error that names nothing ("the guy we lynched") is
outside it by design, and so is a statement like "I investigated player_9" about a living player,
although the game records every check, vote and kill. It ran once, on the nine-seat game; its role list
cannot read the ten-seat roles.

### Playing and reading games

**What it answers.** Which specific errors happen in real games, how they unfold, and what they cost.
It gives no rate.

**How it works.**

- **The owner plays a seat** on the live site, with AI players in the other seats, and flags errors or
  odd behaviour as they happen. Afterwards the game is read with every agent's private notes and reads,
  to find the statement behind each flag. Four games in October 2026 started most of the later work:
  - `832404e9` (owner as a villager): the investigator announced a check it never made, the village
    voted out an innocent player on it, and the serial killer won.
  - `8e26fd3b` (owner as the vigilante): the second game on the new prompts.
  - `46355b89` (owner as the serial killer): the town won on a premise the wolves had fabricated, and
    agents cited private or missing information as if it were public.
  - `403f4dbc` (owner as the necromancer, Claude Haiku 5.5 in the other seats): visits read the wrong
    way round, replies repeated, votes cast with no reason.
- **AI readers audit AI-only games against a rubric**, a fixed list of kinds of error. Ten ten-seat
  games were read this way (about 345 lines heard):

| Kind of error | How many |
|---|---|
| A conclusion that does not follow from the facts | 28 |
| An error in a day summary | 22 |
| A night error | 6 |
| An invented fact | 2 |
| An evil player misstating a rule it believed | 2 |

Inventing facts had become rare on the ten-seat game. The commonest errors were bad reasoning about what
an ability can see, and the summariser distorting plain claims
([discussion_evidence](../../game_play_enhancement/discussion_evidence.md) §8.4, §8.6).

**How far to trust it.** Playing finds the errors that cost the most, but only in the games that were
played, and only what caught the owner's eye. Ten audited games are too few for a rate, and the readers
did not always keep a fair hunch ("they helped catch a killer, so I trust them more") apart from a wrong
proof. The reads are rated in [sampled_human_review](../sampled_human_review/report.md).

### How each symptom is found and judged

Each kind of error has its own path. Code takes the part it can decide, by comparing the text with the
game record; a reader takes what needs meaning or logic.

| Symptom | Found by | Code's part | Judged in replays by |
|---|---|---|---|
| Wrong count of who is left; a dead player treated as alive; a dead player's role misstated | The census | A rule narrows by comparing with the record; a reader decides the meaning (past tense, a kill count against an alive count) | The census reader |
| A claim credited to the wrong player | The census; the rubric audit | A rule narrows (nine-seat). On the ten-seat game claims are structured, so code checks them in the claim ledger | Code for summaries; the expectation judge for turns |
| An invented result or action | Playing only: no census rule covers it | None | The expectation judge, and a hand read |
| A visit read the wrong way round; a conclusion that does not follow | The rubric audit; playing | None: the facts are right and the logic is wrong | The expectation judge, and a hand read |
| A day-summary error | The rubric audit | The summary is structured, so code checks it against fixed signatures | Code, no judge |

## Step 2. Turning errors into test cases

**What it is for.** A failure seen once cannot show whether a fix works. It has to be replayable, under
any prompt or model, as often as needed, and it has to be a real failure, not a one-off draw.

**How it works.**
- **A case is one agent turn frozen as game state,** not as a prompt: the transcript so far, deaths and
  revealed roles, the agent's private results. Each version under test rebuilds its own prompt from that
  state.
- **Keep only errors that reproduce.** Players run at temperature 1.0, so an error seen once may be a
  chance draw. Replayed, three of four July errors never happened again. So each candidate was replayed
  three times on today's prompts and kept only if it went wrong at least twice. On the cases kept, 22%
  of samples still went wrong (153 of 684).
- **Pin specific failures** with a written expectation of what a correct turn must not say ("the only
  checks it made were…"). Day summaries are pinned differently: their structured output is checked by
  code against fixed signatures, such as a role credited to someone who claimed none.

**What it produced.** Two nine-seat sets (125 and 129 cases, `evaluation/frozen_eval_sets/`), and
per-study ten-seat sets built from October games.

**How far to trust it.**
- **Cases that inherited their error were not separated out.** A turn where the speaker repeats a false
  premise already in its transcript or summary tests something different from a turn where the speaker
  makes the error itself. The nine-seat sets mix the two. One ten-seat set (the Haiku game) labels each
  turn by hand as an origin or a repeat, and has only three origin turns.
- The nine-seat cases are today's turns on June boards, so the history they carry was written under
  older prompts.
- The nine-seat test set replays day turns only, not night turns, where July found the most errors.

## Step 3. Finding the cause of an error

**What it is for.** What step 1 finds is a symptom: the kind of wrong statement. The same symptom can
come from different causes, and the cause decides the fix. A wrong count of who is left, for example,
can be a slip in counting or a fact the agent was never given.

**How it works.** One question first, then one of two paths:

1. **Was the fact in the agent's input, correct and clearly stated?** The input the agent saw for that
   turn is read beside the error, by hand. This settled most cases.
2. **If the fact was missing or wrong**, the cause is the input. What is left is to find where it was
   lost or corrupted: in the code that assembles the prompt's inputs from the game state, or in an
   earlier model's output that feeds them (a day summary that invented a claim). After game
   `46355b89`, where agents cited private or missing information as if it were public, that path was
   read end to end (2026-10-03). It found the source and 11 more holes of the same kind: for example,
   the healer's prompt had no record of its own past protections, and facts from the engine looked the
   same as a model's summary. A day later 8 were fixed and 4 only partly (the detailed record §8–9).
3. **If the fact was there and correct**, the model failed on good input, and reading cannot say why:
   it may have slipped in reasoning, misread the fact, or been misled by its wording. The turn is
   rebuilt from the game's saved state and replayed many times with one thing changed per version.
   If rewording the fact fixes it, the cause was the wording; if more thinking or a stronger model
   fixes it, a reasoning slip.

**The worked example.** In game `832404e9` the investigator announced a check it never made. Its input
listed all its real checks, so the fact was given, and reading alone could not say whether the model
made the claim up or was misled. The turn was replayed 20 times under four versions. As played, 20 of 20
samples invented the check; with the results reworded, 0 of 20; removing its previous note changed
nothing. So the cause was the wording. Its real night-3 check was on player_5, who was also killed that
night with the healer role announced, and the prompt listed the check as *"Day 3: player_5 was revealed
as healer"*: the word used for roles shown at death, dated by day, with no "you investigated". It read
as public news, so the agent, which had promised to share last night's check, saw nothing to share and
invented one. The fix writes every result as *"Night 3 (last night): you investigated player_5, who is
the healer"*.

**What was found, symptom by symptom:**

| Symptom | How often | Possible causes | How it was told apart | Cause found | Fix (where recorded) |
|---|---|---|---|---|---|
| **A wrong count of who is left** ("the remaining wolf") | 221 of 368 (July census) | A reasoning slip; losing track | The count was not in the prompt, only workable out from the list of deaths. The board of the dead alone did not stop the one recurring case (July replay); the July bundle, which also printed the count, took error-prone turns from 48% to 30% wrong; more thinking cut bad samples from 82 to 27 of 267 | A reasoning slip | A printed line of which roles are still alive; a higher thinking budget ([validation plan](../../generation_prompt/validation_plan.md); log §2, §4) |
| **A dead player treated as alive, or a dead player's role misstated** | 57 and 13 of 368 (July) | Losing track; the fact not given | Not told apart: the board of the dead shipped in the July bundle as cheap hygiene, not as a tested fix | Not established | A board of the dead with their revealed roles in every prompt (validation plan) |
| **A claim credited to the wrong player** ("player_2 claimed chanteuse") | 18 of 368 (July); within the 22 summary errors in ten ten-seat games | The player made it up; the day summary did, and players repeated it | The summary was read against the transcript: the summariser had turned "I was roleblocked" into a chanteuse claim, and two players repeated it. In replay, the fix took the repeat from 5 of 5 samples to 0 | Wrong input (a summary error) | The summariser is told what is not a claim; the claim ledger, kept by code, drops a claim that can only come from a block (discussion_evidence §6.6, §8.4) |
| **An invented result or action** ("I investigated player_9") | 59 inventions of 368 (July); 2 in ten ten-seat games | The model made it up; a misleading wording; its own previous note | Replay with one change each (the worked example) | A misleading wording | The results reworded (discussion_evidence §6.2) |
| **A visit read the wrong way round** ("I visited nobody" taken as "nobody visited me"; an empty watch read as an empty house) | The commonest player error in the ten-seat audit, within the 28 bad conclusions | Misreading; the rule not stated | The prompts were read: they defined a visit only by implication and never said what a watch cannot see | Misreading, invited by an unstated rule | The rules now state which way a visit goes and what a watch cannot see (discussion_evidence §8.4, §8.6) |
| **A conclusion that does not follow from correct facts** ("a watch and a protection prove my results") | 28 in ten ten-seat games | A reasoning slip; a corrupted summary underneath | Replay of ten frozen turns on the same prompts: 6 bad samples in 40 on flash-lite, 1 on gemini-3.5-flash; flash-lite made them as often on the control turns | A reasoning slip | A stronger model or more thinking; the deduction engine, which hands the player the conclusion (discussion_evidence §8.4; [reasoning_failures](../../reasoning_failures/report.md)) |
| **A fact the agent should have known, stated wrongly or not used** (private information cited as public; a rule the engine applied) | 12 holes in the code audit; two ten-seat games turned on unstated rules | The fact not given, or given in a confusing form | Reading the code that builds each prompt, and the prompts of the two games | Missing or confusing input | Each agent's own night record; engine facts labelled apart from summaries; the missing rules written in (discussion_evidence §6.4–6.5, §8.4; the detailed record §8–9) |

**The causes, across all rows.** Five causes cover what was found: *making things up* (hallucination in
the strict sense), *a reasoning slip*, *misreading* correct information, *losing track* of what has
happened, and *missing or confusing input*. They overlap: a player reasoning well from a corrupted
summary makes no reasoning error of its own. Each case was diagnosed on its own route (some replayed,
some settled by reading, one fix shipped untested), so the causes were never counted across cases.

## Step 4. Running the test set: checking a fix, or choosing a model

**What it is for.** Showing that a change reduced errors on the same cases, or that one model makes
fewer than another, beyond the noise of sampling.

**How it works.** Each version under test is an *arm*: a model plus a prompt version, or an older
version of the code run from a git worktree. Every arm runs on the same cases, and the same judge scores
them all; the two arms are compared case by case.

**How the samples are judged, and the guardrails on the judge.** Most cases are read by the census
reader; pinned cases by a narrow judge that compares each sample with its written expectation. Three
guardrails sit around it:
- **Controls**, turns that were right, catch a judge raising false alarms (3% of control samples went
  wrong, 4 of 120, against 22% on the kept cases).
- **A noise floor**: the same outputs re-judged, to see how far the totals move with no change at all.
- **A hand read** of the verdicts, for the ten-seat sets every one.

Models are compared on a **random slice** of cases, because the kept cases lean toward the screening
model's own mistakes.

**What it showed.**
- **The July ship test** (T1c) on error-prone turns: 48% went wrong on the old prompt, 30% on the new
  bundle (29 cases better, 11 worse, p=0.003). Its measure was fixed before its data existed.
- **The nine-seat test set's noise floor:** re-judging the same outputs moved totals by only 1 to 2 of 267. Four
  wording changes stayed inside it, including the October fixes from the code audit (97 → 82 of 267,
  24 cases better and 14 worse, p=0.14): a direction, not proof.
- **The first change clearly beyond it:** raising the players' thinking budget cut bad samples from 82
  to 27 of 267 (36 cases better, 4 worse).
- **Ten-seat failures, after fixes:** per-case counts, with every verdict read by hand. The hand read
  caught a wrong expectation once, and in one set its counts (about 19 and 6) differed from the judge's
  (16 and 5). The summary replay, scored by code with no judge, caught one regression (a true vigilante
  claim dropped) before it shipped.
- **Choosing a model or a thinking level** helps one kind of error much more than the others. More
  thinking or a stronger model fixed reasoning slips and some misreadings on frozen turns (the thinking
  budget above; on the ten-seat failure turns with the same prompts, 1 bad sample in 40 on
  gemini-3.5-flash against 6 on flash-lite). It did not fix errors that came from the input (the
  invented check needed a rewording, the invented claim a pipeline fix) or from rules nobody had written
  down. And its gain in full games was smaller than on frozen turns: over six games, invalid deductions
  went from about one line in 12 to one in 15, and summary errors from 2.2 a game to 1.5, at about $2.72
  a game against $0.72. So the rule of thumb is: the model fixes reasoning and interpretation, the prompt
  or pipeline fixes input. Runs on the nine-seat test set to admit a new player model are rated in
  [model_admission](../model_admission/report.md).

**How far to trust it.** 🟡. The judge agreed with a hand check on 10 of 12 verdicts. A replay of known
failures shows whether they still reproduce, not how often errors happen: "0 of 10" means the failure
stopped reproducing. Full games still find new failures. Since 2026-10-12 the judges default to Claude
Haiku 5.5, which has no recorded check against people.

**What reduced the errors** (telling the model to take care did not; giving it the fact, or moving the check
into code, did) is the problem side, not the measurement, and is in
[the gameplay report](../../game_play_enhancement/report.md), problem 1.

## What the labels can and cannot say

Who labels the symptom, and when, differs by source:

| Source | Who flags the error | Who labels the symptom | When |
|---|---|---|---|
| The census | Code rules, then the model reader | The cheap model reader, in the same call (which fact was wrong). The owner checked whether each was an error, never the label | At collection |
| The rubric audit | AI readers | The same readers, from the rubric's fixed list of kinds | At collection |
| The owner playing | The owner, in free text ("why did they vote for 8?") | Nobody: the game is read to find the statement, which gets no fixed label | Never |
| Test cases | — | Nine-seat cases keep the census label (of the 141 original statements, 80 wrong counts, 14 inventions, 40 controls); pinned cases carry a written expectation; ten-seat cases a description, and one set an origin-or-repeat label | When frozen |

So no single label covers everything, and causes are labelled nowhere. To say what share of errors were
made up and what share were reasoning slips, every case would need the same record (change 4 below).

## What we would do differently next time

Changes by stage of the workflow: what could be standardised so the work is cheaper, faster or scales,
and so the test cases make a sound regression set. Each could have been chosen at the start; lessons
that needed test results first are left out.

| Stage | Change | What was done | What it would buy |
|---|---|---|---|
| Design | **1. Design the agents' output so checkable facts come out structured**: claims, check results, votes and night targets as fields with fixed values (an enum of roles, a player id), beside the free speech | Turns were judged by a model against a written expectation, and every verdict read by hand | Code scores those facts, with no judge cost or judge error. Trade-off: more output tokens per turn, weaker models fail on complex fields, and reasoning cannot be a field, so only for the facts that decide votes |
| Find | **2. A census rule for every kind of fact the game records**: own night results and actions, votes, how each player died | Four rules (a dead player named, a role word for a dead role, a wrong count, a claim not in the list) | Invented results and actions, today found only by playing, counted in the rate. A reader still decides each candidate |
| Find | **3. A census that reruns on any version** (roles read from the game, not typed into the script) | Ran once, July, nine-seat only | A rate in real games after each big change, for about $2–3 a run. Replays of chosen failures overstate gains: the stronger model's gain was much smaller in full games |
| Label | **4. One record for every error, whoever finds it**: the statement, the fact it contradicts, what the fact is about, which player, whether the speaker started it or repeated it, and the cause once tested. A reader fills it in the same call that flags the error, or from the owner's one-line flag; the owner's hand read checks the label along with the verdict | Each source labelled its own way, or not at all (the table above); census labels were never checked | One count across the project, with repeats counted once, at no extra model calls |
| Freeze | **5. One maintained regression set**, versioned, that every study adds its cases to, with night turns as well as day turns | The ten-seat cases are separate sets, one per study; the nine-seat test set cannot replay night turns | Every change is checked against all known failures, not only its own study's, including night notes, the worst surface in July (9.6%) |
| Freeze | **6. Cases that inherited their error kept in a separate slice**: before freezing, code checks the case's transcript and summaries for the same false fact, using the record's fields | The nine-seat sets mix the two; one ten-seat set labels origin and repeat turns by hand | A slice that tests the model on clean input, and one that tests whether a player resists a false premise. Today a summary fix and a player fix move the same number |
| Diagnose | **7. One route for every case, starting with a code check**: code looks the error's fact up in the frozen input and labels it stated, derivable, missing or conflicting; missing and conflicting go to the input fix, the rest to a replay with one version per possible cause | Read by hand, case by case, on a route chosen per case; the board of the dead shipped untested | Input errors sorted at no model cost, replays spent only where the fact was given, and every cause backed by the same kind of evidence, so causes can be counted. The check cannot see a misleading wording; a replay still finds that |
| Check | **8. The cheapest scorer that can decide each symptom, fixed in advance**: code for structured output, the census reader for fact errors, the expectation judge with a hand read only for logic errors | Every ten-seat verdict was read by hand, whatever the symptom | Owner time spent where the judge was shown to err, and the rest scaled without it |

## What is not measured

- **No error rate on the ten-seat game.** The census never ran on it (estimated at $2–3), and its role
  list knows only the nine-seat roles. Every ten-seat number above is a replay of known failures or a
  hand audit.
- **No night turns in the nine-seat test set**, though July found night notes the worst surface.
- **The readers' checks are from the Gemini era.** The current Claude Haiku 5.5 default has no recorded
  check against people. Calibrating the test set's judge on a blind, owner-labelled sample is the first item
  on the owner's pending list ([`writeup/map.md`](../../../writeup/map.md)).

**Bottom line.** The only error rate on record is about 3% of public messages, nine-seat, July 2026, and
its counts are floors. Everything since asks a narrower question, whether a change stopped a known
failure, and answers it on replayed turns read by hand.

*Written 2026-10-23 and checked against the records named above. Which commit and judge each run used is
in the detailed record and [the source map](../source_map.md).*
