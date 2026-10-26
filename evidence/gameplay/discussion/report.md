# The day discussion: who speaks, when, and when the day ends

This page covers how a day's discussion runs in the game today, then the decisions that produced it:
what each one chose, what it was chosen over, and what it cost. The build journey of June 2026 is in
[the experiment log](experiment_log.md), and the June acceptance study in
[`quality_gate/`](quality_gate/experiment_log.md). The October 2026 rebuild is recorded step by step in
[discussion_evidence](../discussion_evidence.md) §7, and the voice and silence
studies of 2026-10-18 in the linked study records below.

**Reading this report.** [A day today](#a-day-today) describes the current behaviour;
[the decision index](#decision-index) leads to the reasons and alternatives;
[the checks](#how-it-was-checked) separate implementation checks from behavioural evidence;
[revision criteria](#when-to-revisit-the-design) identify what would justify changing a choice.

**Version.** The implementation described here is the 2026-10-26 snapshot at
`db63a77b2984b0af4725f22d5e5504aa011bc3c6`. Historical results belong to the models, prompts,
and configurations recorded in each study; they are not all measurements of this snapshot.
Hosted games use voices by default; batch games do not. The linked study records and run manifests
are needed to reproduce an experiment.

**Assessment.** The design makes turn allocation inspectable and gives tagged questions and
accusations a direct route to a response opportunity. Small studies support the choices around
repetition and silence. They do not establish overall discussion fairness, a reliable semantic
answer rate, or an improvement in game outcomes.

## The problem

In Werewolf the town must find the evil players by talking, then vote one out. Every AI player is a
model call. The models decide what each player says. The engine decides everything else about the
conversation: who speaks next, whether a line is published, and when the talking stops.

A good day needs four things:

- **A player who is asked or accused gets a prompt opportunity to answer.**

- **Every living player gets a chance to speak**, including a player sitting on a night result.

- **Repetition does not crowd out useful contributions.** Seven players repeating the same suspicion is noise, and it
  piles votes onto one name.

- **No voter can adapt to votes already revealed.** Discussion-order effects are a separate concern.

Two distinctions shape the whole design:

- **Discussion order and vote visibility are separate choices.** Sequential discussion lets a player
  respond to what was just said. Blind, simultaneous voting prevents adaptation to revealed votes.
  It does not remove discussion-order effects: earlier speakers may frame the debate, and later
  speakers have more information. Those effects have not been quantified.

- **Code decides the flow; a model judges meaning.** Who speaks and when the day ends are computed
  from the transcript. A model is used only where code cannot answer: what a line says, and whether
  it adds anything.

## A day today

```
Day 1      opening round → day summary → night
Day 2 on   opening round → discussion → closing defence (if anyone has two accusers) → day summary → vote
                           │
                           ├─ reactive turns: whoever owes an answer speaks next
                           └─ sweeps: when nobody owes, the floor goes round the players who have not spoken
```

Day 1 has no discussion and no vote. The parts below follow the order a day runs them.

### The opening round

Every living player is sent an opening turn at the same time. An opening may contain only three
kinds of statement:

- a role claim, or a counterclaim to someone else's claim on the same role;

- the speaker's own night action or its result, if the morning report did not already make it
  public;

- a challenge to a claim made on an earlier day, with a reason.

Passing is the normal answer, and the prompt says so. After the openings are collected, one cheap
model call labels each line's kind. Lines of the three kinds are published in seat order; anything
else (a deduction, advice, padding) is held. The call judges only the kind of a statement, never
whether it is true, so a false claim is published. It fails open: an error or a missing verdict
keeps the line. A human player's line is never held.

### Reactive turns

Every spoken message carries **speech-act tags**: for each player it addresses, the form
(`question`, `response` or `mention`) and the stance (`accusation`, `defense`, `agreement` or
`neutral`). An AI player writes them as part of the same structured output as its message. A human
types free text, so a separate model call tags the human's message the same way afterwards.

The tags drive the scheduler. A question to a player, or an accusation of a player, **opens a debt**:
that player owes the speaker an answer. Any later line by the player who owes that engages the speaker
(a response, a mention or a counter-question) **discharges** it. Whoever owes an answer speaks before
anyone else, the most recently opened debt first, and a player who owes three accusers is asked to
address all three in one turn. These are scheduling rules, conditional on the tags and the limits
below; they do not establish whether a reply answers the substance of a question.
A real exchange from one of the October test games (`phase2-step8-game1`, day 2):

```
player_7 (open floor)  → player_9: question, accusation
  "Checking someone who died on night one is awfully convenient since it can't be cross-checked.
   Player_9, if you're the real investigator, who are you looking at tonight?"
player_9 (reactive, owes player_7) → player_7: response, defense
  "Player_7, I didn't plan for player_1 to get hit by both the wolves and the serial killer on
   night one. It's just bad luck that my first check died right away."
```

Player_9 spoke next because player_7's tags opened a debt, not because a model chose it. Its prompt
named the debt: "You were directly addressed by player_7. Respond to them this turn."
The reply defends the previous check but does not answer whom player_9 will investigate tonight.
This example demonstrates immediate turn allocation, not a complete answer.

Two limits keep a feud from taking over the day:

- **Freshness.** While player B still owes player A an answer, another question or accusation from
  A to B, however reworded, opens nothing new.

- **A cap per pair.** After two completed cycles of A pressing B and B answering, further questions
  or accusations from A to B open no debt. Once the pair has gone untouched for as many turns as
  there are living players, the count resets.

A turn whose model call fails closes the debts that called it.

### The sweeps (the open floor)

When nobody owes an answer, the **sweep** gives the floor to the living players who have not spoken
today, one at a time in seat order. After each line, any debts it opened are answered before the next
player is asked. A second sweep goes round the players who have been silent since the first began,
but only if the first produced a new line. There are at most two sweeps a day.

On the open floor a player **speaks by default**. Whether the line is published is decided by the
**echo gate**: one cheap model call, at a low thinking level, that reads the new line against the
day's spoken lines. It holds a restatement (of an earlier line or of the record), an agreement with no
new reason, a request someone already made, and filler. It keeps a new fact, a reading of the player's
own with its reason (even against the table), and a question or test nobody has asked. Code, not the
judge, exempts two cases: a line answering a player who named the speaker, and a human's line. The
gate fails open.

A held line is not published. It becomes a pass marker that keeps the text for its author, whose next
prompt shows that it was never said. A held line opens no debt and counts for nothing in the closing,
and its author is not asked again that day.

On a voting day, a town player who would vote for someone and has not said why is told to say it
rather than pass. Evil players are not told this: for them silence can be the better play.

### Ending the day

The discussion ends when nobody owes an answer and the sweeps are done. Behind that sits a hard cap:
three real lines per living player (30 with ten alive), never fewer than six. When the cap is reached
the day **drains**: debts already open are answered, each player who owes answers at most once more,
and debts opened during the drain are left for the closing.

### The closing defence

When the discussion ends, the one or two players accused today by at least two different players
each get one last turn, sent at the same time. They may not make new accusations, and nobody
replies. The accused are counted from the speech-act tags on spoken lines. A moderator line, written
by code, names who is called. If nobody has two accusers, the day goes straight to the summary.

### The vote

Every living player votes against the same transcript, at the same time, and the votes are revealed
together.

### The voices

In games on the website, each AI player speaks in its puppet's voice: one line in the player's own
prompt says how it sounds ("Brisk and polite, like a porter on a busy shift: short and practical").
A voice may not lean on suspicion, firmness or a side, or hint at a role. Voices have been on in
hosted games since 2026-10-19; in batch games and experiments they are off by default. A human
player is never given one.

### Who decides what

| Decision | Made by | Model calls |
|---|---|---|
| Who speaks next; when the discussion ends; who gets a closing turn | Code, from the transcript and its tags | None |
| Whom a message addresses or accuses | The speaker, in its own structured output; for a human, a tagging call afterwards | None extra for AI players |
| Whether an opening line is of an allowed kind | One cheap call over all the openings | One call |
| Whether a sweep line adds anything | The echo gate | One call per sweep turn |
| The moderator's closing line | Code | None |
| What each player says, and its vote | The player's model | One call per turn |

A voting day with a full table costs about 30 model calls (four nine-seat test games, October 2026).

---

## The decisions behind it

Grouped by the question each answers. Each gives the choice, what it was chosen over and why, the cost
accepted, and the evidence. Dates are given where a decision replaced an earlier one.

### Decision index

All choices below describe the current design or the historical decision it replaced. Evidence
strength varies: a rule can be tested deterministically while its effect on discussion remains open.

| Question | Decisions | Evidence and remaining uncertainty |
|---|---|---|
| Who gets the floor? | [1–7](#decision-1): sequential turns, reactive priority, sweeps, transcript-derived state | Explicit routing rules; small comparative studies; order effects unmeasured |
| How are response obligations represented? | [8–11](#decision-8): tags, discharge, freshness, pair limits | Format tests and judge agreement; semantic misses and hand-set limits remain |
| Who speaks, and what gets published? | [12–15](#decision-12): separate novelty judge, default speech, held-line markers | Frozen-line and game studies; suppression risk remains |
| What frames the discussion? | [16–18](#decision-16): opening, night-1 target fix, closing defence | Small game samples; closing effect unmeasured |
| When does discussion stop? | [19–20](#decision-19): bounded drain and sweeps | Implementation checks; thresholds not swept |
| How do players sound? | [21](#decision-21): voice in the player's own prompt | Preference and gameplay studies; behavioural equivalence unestablished |
| How can a structural change be reversed? | [22](#decision-22): tagged baseline | Versioning choice; no behavioural claim |

### How the floor is given

<a id="decision-1"></a>

#### 1. Sequential discussion with blind, simultaneous voting.

- *Instead of:* concurrent rounds, the first design: every player spoke once per round, all
  generated in parallel against the same snapshot and revealed together. It was a sound first
  choice: simple to build, fast, and symmetric in what each player could see within a round.

- *Why:* answering the same snapshot is also what made repetition invisible. No player could see
  that another was about to make the same point, so a round produced near-identical lines, and an
  accused player could answer only after the round, to everyone at once. On day 1 of one concurrent
  game, five of eight players opened like this:

  ```
  player_2: "…Does anyone have any initial thoughts on how we should handle the first vote?"
  player_5: "…Does anyone have any initial thoughts on who to look out for?"
  player_6: "…Does anyone have any initial leads or thoughts?"
  player_7: "…Does anyone have a theory on who we should look at first?"
  player_8: "…Does anyone have any initial thoughts on who to look out for…?"
  ```

  Concurrent generation prevents a player from checking its line against unseen lines in the same
  round. Sequential generation removes that constraint: each player can read the lines before it.
  This enables avoiding repetition; it does not guarantee that the model will do so.

- *Cost accepted:* a later speaker still speaks better informed, and the day is slower, since turns
  run in series. Blind, simultaneous voting removes access to a developing vote tally. It leaves
  possible framing, persuasion and information advantages during discussion unmeasured.

- *Evidence:* the [June acceptance study](quality_gate/experiment_log.md). Four sequential games (`gemini-3.1-flash-lite`, two with
  memory off and two on) against eight concurrent games already on disk from the same model family,
  read by hand against a written rubric. The lexical echo metric detected no echoes in sequential
  games (0.00 of lines against 0.05–0.06). It uses a similarity threshold of 0.60 and misses
  paraphrases, so zero does not mean no semantic repetition. The qualitative read also found
  accused players responding to their accusers in turn. Concurrent still reached
  the right lynch when the evidence was strong; it read as parallel monologues, not as a broken game.
  The study was unpaired, the concurrent games' backend and temperature were not recorded, and the
  reader had built the sequential design, so its numbers are descriptive. The decision rested on what
  the design enables, illustrated in the sampled games, and it was reversible: the concurrent design is kept
  at the tag `concurrent-baseline`. Adopted 2026-06-05.

<a id="decision-2"></a>

#### 2. The order follows the conversation, not a random draw.

- *Instead of:* shuffling the speaking order, the obvious answer to a later speaker's advantage.

- *Why:* a shuffle does not remove the advantage, it hands it to someone else each round, and it is
  blind to the conversation: a player asked a direct question waits for a slot that may not come.
  Recomputing the order after every line prioritises a response to a tagged question or accusation.
  Reactive turns can interrupt the seat-order sweep, but that does not establish that order
  advantages are evenly distributed.

- *Cost accepted:* residual discussion-order effects remain unmeasured. A randomised sweep with
  reactive priority is a possible future comparison; randomness and responsiveness need not conflict.

<a id="decision-3"></a>

#### 3. Two hard paths to the floor, not a weighted score.

- *Instead of:* the first sequential draft, a score per player (pressure from being addressed, a
  volunteer's novelty, a penalty for talking a lot, a boost for quiet players, a random tiebreak),
  with the highest score speaking.

- *Why:* in that draft, response priority competed with the other terms in the score. Its weights
  had no established calibration target, and explaining a pick required explaining their combined
  effect. The replacement makes response obligations and open-floor eligibility explicit, so tests
  can assert those rules without depending on a particular set of weights. A player reaches the
  floor because it owes a response, or because it is eligible for the sweep and nobody owes one. "A tags a question to B, so eligible B speaks next"
  is a unit test with no weights in it. Missing or incorrect tags can still prevent that turn.

- *Cost accepted:* no gradation. A player with a strong point and one with a weak point wait the
  same way in the sweep.

<a id="decision-4"></a>

#### 4. A stateless scheduler.

- *Instead of:* counters kept and updated after each turn (who owes whom, who has spoken).

- *Why:* one missed update and the counters disagree with the transcript, and they never correct
  themselves. Recomputing everything from the day's transcript before each turn cannot drift from it,
  and a test can write a transcript by hand and check the pick. The scan is trivially cheap next to
  the model call in every turn.

- *Cost accepted:* the transcript must hold everything the scheduler needs. That held for AI
  players from the start; a human's line had no tags until the tagging call was added (decision 8).

<a id="decision-5"></a>

#### 5. One graph node per turn, looping back to the scheduler.

- *Instead of:* one node that runs the whole discussion inside a loop.

- *Why:* LangGraph checkpoints at node boundaries. A node per turn means each turn can be streamed
  as it happens, a game can resume after any turn, and the graph can pause for a human's turn
  (`interrupt()`) without a redesign. The human seat uses exactly that today. The scheduler is a
  routing step that sends one turn to one player's node (a single `Send`), reusing the per-player
  payload builder that also guards what each player may see.

- *Cost accepted:* more graph steps per day, which the recursion limit has to allow for.

<a id="decision-6"></a>

#### 6. No guaranteed slot for the investigator; every player asked instead.

- *In June:* the scheduler stayed blind to roles. The investigator is the only role with a result
  worth volunteering, so any priority for "has private information" would single it out. Revealing a
  result was left to the player.

- *In October:* the opening round gives the guarantee without the tell, because every player is asked
  at the start of every day (decision 16).

<a id="decision-7"></a>

#### 7. The open floor goes one player at a time, in seat order (2026-10-07, replacing a parallel round).

- *Instead of:* a parallel round of every silent player at once, with a filter that kept the first of
  each group of near-identical points. It was built first, on the same day, because a round of quiet
  players at once is faster than asking them one by one.

- *Why it was reverted:* in its first game it generated seven lines to keep two in a day's first
  round. In that sample, parallel turns produced overlapping points, repeating the concurrent
  design's failure mode. The filter removed the duplication after paying to generate those lines. One at a time, each player reads the lines before it, and debts its line opens are answered
  before the next player is asked.

- *Cost accepted:* the open floor takes as many model calls in series as there are silent players.
  The parallel version is kept at the tag `phase2-parallel-proactive`.

### Who owes whom: the tags

<a id="decision-8"></a>

#### 8. The speaker tags its own message.

- *Instead of:* finding questions and accusations in the text with string matching, or tagging every
  message with a second model call.

- *Why:* string matching is weakest at the strongest signal: it read accusatory questions as plain
  questions, and all 11 of its disagreements with the model favoured the model (Smoke 1). A second
  call would add one call per line. The speaker already writes structured output, so the tags require
  no extra model call, although they add output tokens. A human's free text is the exception,
  tagged by a separate call after the line.

- *Cost accepted:* the scheduler is only as good as the tags. Against the judge, the tags missed
  accusations on 24 of 183 evaluated messages (13%); this is a message-level rate, not the fraction
  of all accusations missed.

- *Evidence:* Smoke 1 (June, `gemini-3.1-flash-lite`, 30 frozen cases): 30 of 30 valid outputs, and
  27 of 27 tagged players named in the message itself, none invented. Against an LLM judge's reading
  of 183 messages (nine-seat, 2026-10-03), the tags named the same accused player, or none, on 145
  (79%); they missed an accusation on 24 and added one on 1. Accuser counts run low more often than
  high. The [study summary](../discussion_evidence.md#71-what-the-game-records-say-2026-10-03)
  does not classify the remaining 13 disagreements; these counts are not a complete confusion
  matrix and do not establish accusation recall.

<a id="decision-9"></a>

#### 9. Two tag dimensions, form and stance, not one.

- *Instead of:* one label per target (question, accusation, defence…).

- *Why:* most lines in this game are a question and an accusation at once ("why did you vote for a
  villager?"). One label forced a coin flip, which showed up as accusation over-labelling. Splitting
  form from stance allowed both labels to be expressed. Smoke 1b found 100% valid outputs and no
  invented targets; those checks establish format validity and target grounding, not semantic
  accuracy for both dimensions.

<a id="decision-10"></a>

#### 10. Any engagement discharges a debt.

- *Instead of:* only a line tagged `response` to the creditor.

- *Why:* models mislabel the form. A player that answered A while tagging the line as a mention never
  cleared its debt, stayed first in line and was picked again and again: seven times in a row once in
  June, with two turns word for word. A mention of the creditor discharged from June; a counter-question
  from 2026-07-26, after a player whose replies were all tagged as questions re-fired three times in a
  row, each turn insisting "you haven't answered".

- *With it:* the reactive prompt names whom the player owes. Without that line, a player picked to
  answer re-derives what to say from scratch and lands on the same generic accusation; with it, an
  accused player defends.

<a id="decision-11"></a>

#### 11. Freshness and a pair cap, not a talk-time penalty.

- *Instead of:* the first draft's penalty on players who had talked a lot.

- *Why:* the penalty was never allowed to silence a player who had been addressed, since a direct
  question must be answered, so two players locked on each other could trade lines forever. Two
  separate limits do the job. Freshness stops a reworded repeat from opening a second debt while the
  first is open; it keys on who pressed whom, ignoring wording, so no model has to judge whether a
  re-accusation is a new angle. The pair cap stops the back-and-forth after two cycles.

- *Changed in June:* the cap was first per day, which left a pair shut out after the room had moved
  on. It now resets after a pair sits untouched for a table's worth of turns, so a topic that comes
  back can be taken up again.

- *Cost accepted:* the numbers (two cycles, one table's worth) were set by hand and never swept. One
  shipped wrong: the reset sat at three tables' worth against an intended one for about 20 days,
  found on a later read of the code (2026-06-24).

### Silence and repetition

<a id="decision-12"></a>

#### 12. Novelty is judged after the line is written, by a call that did not write it.

- *Instead of:* a novelty label (already said / borderline / new) added to each player's own call,
  which would have cost no extra call.

- *Why:* run as a separate judge on a fixed line it had not written, the label worked: 20 of 20
  restatements and 20 of 20 new points labelled correctly, at temperature 0 and 1.0 alike (Smokes 2
  and 3). Folded into the player's own call, it failed both ways (Smoke 4). Asked whether the situation
  had moved on, the player called almost everything a repeat, since a mid-game recap is a continuation
  by definition. Asked whether its own point was new, it called almost everything new, even with a
  paraphrase already in the transcript. A plausible explanation is that judging a fixed line separately
  is easier than assessing novelty during generation. These tests changed the task and its prompting
  as well as the call structure, so they do not isolate the cause of the difference.

- *What followed:* the label was dropped and silence went fully structural, which the first live
  games showed was not enough: on quiet days, players given the floor piled agreement onto the same
  point ("stuck in a cycle of agreeing… which itself is a trap", one said). A separate judge came back
  on volunteer turns only, never on an answer. An echo-heavy day's second round fell from 24 turns to 9.

- *What it cost, found in October:* that judge was the main source of silence. Of 517 passes in 28
  June games, 367 were the judge holding a line, and nobody at the table could tell
  (discussion_evidence §2.4). Today's echo gate is its descendant, with a narrower scope (sweep lines
  only) and a marker its author can see.

<a id="decision-13"></a>

#### 13. Players speak by default on the open floor, and the gate sorts (2026-10-18).

- *Instead of:* tuning the rule that tells a player when to pass.

- *Why:* in the tested prompts, the player's speak-or-pass decision did not reliably separate
  useful lines from restatements. The [silence calibration](../data/silence_calibration/README.md)
  (2026-10-18) drew 162 turns from 16 ten-seat Haiku games and replayed each sampled voluntary pass
  once with "do not pass this time". Six replays failed, leaving 156 lines. Four blind Sonnet judges
  divided the lines between them, with one judge per line, classifying each as a new fact,
  a new reading, a new question, or a restatement or filler. On the open floor, the lines players had
  held back were worth hearing 57% of the time (23 of 40), and the lines they posted 52% (13 of 25):
  speaking or passing did not separate value. Rewriting the rule around those kinds moved no decision.
  One sentence moved everything: cutting "a pass costs nothing here" doubled open-floor speech (20 of
  64 turns to 41 of 64), but restatements rose with the worthwhile lines (the player spoke on 66% of
  worthwhile turns and 62% of restating ones, against 37% and 24% before). It was a volume knob, not a
  filter. So the sorting moved after the line is written.

- *Cost accepted:* more restatement reaches the table than a perfect filter would allow, and one more
  model call per sweep turn.

- *Evidence:* on the 65 judged open-floor lines, the gate as shipped holds 10 of 29 restatements and
  none of 36 worthwhile lines; the previous bar ("the same point as an earlier line") held none of
  either. In four ten-seat Haiku games on the deals of four earlier ones, the share of open-floor turns
  spoken rose from 41 of 100 to 54 of 93, and all 7 held lines restated a line spoken shortly before.
  One reader per line, 23 to 46 turns per cell, and a forced line may differ from what a player would
  say by choice.

<a id="decision-14"></a>

#### 14. What happens to a held line.

- *Its author is told.* A held line stays on the transcript as a marker its author sees. The October
  fidelity audit named the risk this removes: a suppressed line surviving as the author's private
  belief that it was said.

- *It opens no debt,* so nobody is asked to answer a line the table never saw.

- *It counts for nothing in the closing (2026-10-07).* Held lines first kept their accusation tags
  for the closing count, so two players making the same accusation counted as two accusers. In one
  test game the moderator then named four accusers of six whose lines nobody had heard.

- *Its author is not asked again that day (2026-10-07).* In the first game under the sweep, the
  second sweep re-asked the two held players and both repeated themselves: four calls, nothing kept.

<a id="decision-15"></a>

#### 15. Players are told that speaking order means nothing.

- *Why:* the engine decides who speaks and when, and the players cannot see how. So they may read the
  machinery as behaviour: "player_7 has been very quiet", "player_2 jumped in first". The game rules
  every player receives say that the order of speech is the moderator's doing and says nothing about a
  player's role. It is stated as a fact about the game, not as an instruction, because the discussion
  prompt's existing instruction not to read suspicion into how quiet someone is had not held.

- *How much it mattered:* less than expected. Of 517 passes in the June games, 71% were the engine's;
  quietness drove something like one accusation in eight; and a keyword search found speaking order
  cited as evidence on only 5 of 95 days, never checked by a judge (discussion_evidence §2.4).

### The rounds (October 2026)

<a id="decision-16"></a>

#### 16. An opening round for every player, at once and restricted.

- *Why a round:* in the June design a day ended after three passes in a row. On day 1 almost everyone
  passed, so the day ended after three players: in 28 of 28 June games, and 8 of 9 games on the
  website. On 8 of 96 June voting days a living player was never offered a turn. The opening round
  asks every player at the start of every day, so a player with a result gets an opportunity to
  submit it. Publication still depends on the opening filter.
  Informal game readings also suggested that the order of result declarations might affect trust;
  that impression was not measured (decision 15).

- *Why at once:* a round of mostly passes played one seat at a time is close to a minute of
  "player_x passes" before anything happens; at once, the wait is about one model call.

- *Why restricted:* the concurrent design had shown that open statements made at once come out
  near-identical. Claims and private results differ from seat to seat, so the opening allows only
  those.

- *Why an allow-list filter, and not the echo gate:* "is this line one of these three kinds?" is a
  steadier question for a cheap model than "is this new?", and it enforces what the opening is for. A
  repeated claim is kept, since two players claiming one role is the contest the opening exists for.

- *Day 1:* the opening and the summary only, with no discussion and no vote: there is almost nothing
  on the record yet.

- *Evidence:* offline on two test games' 13 real openings plus one planted padding line: all 13 kept,
  the padding held. In the four nine-seat test games, only 5 of 106 opening turns were spoken, all by
  the investigator or the vigilante.

<a id="decision-17"></a>

#### 17. What the opening first got wrong: the investigator's lynch.

In the first games on the new
day (2026-10-07, nine-seat, `gemini-3.5-flash-lite`), every investigator who claimed in a day-2 opening
was voted out that day: three times of three, 7 votes to 1 each time. Reading the games showed a
chain:

1. Night-1 targets fell mostly on seat 1 (in all four test games the investigator checked player_1),
   because with nothing to go on the model takes the lowest player number.

2. So the investigator's first result was about the player most likely to be dead by morning, and the
   opening rule told it to announce that result even when the morning had already revealed it.

3. Everyone else passed, so the investigator's was the only name on the table, and the open floor
   and the vote piled onto it.

Two fixes shipped. On night 1 the engine draws a default target by lot, which a player takes unless it
has a reason not to; a shuffled list had been tried first and changed nothing, because the model
follows the seat number, not the list order (95 of 96 picks still went to the lowest seat). And the
opening rule now says a result the morning already made public is not news
([discussion_evidence](../discussion_evidence.md) §7.4 step 8, §7.5).

<a id="decision-18"></a>

#### 18. A closing defence for the most-accused, without a second vote.

- *Design intent:* the most-accused player gets a last word before the vote, as in Town of Salem,
  without adding a trial mechanism or a second round of voting to every day.

- *Trigger:* the one or two players with the most different accusers, at least two. "An accusation
  still unanswered" was the first idea, but in the June records, open accusation debts at day end
  occurred only on capped days. This counts tagged debts, not whether every accusation received
  a substantive answer. Accuser count was a useful proxy for the likely elimination target in that sample: the lynched player was among the day's most-accused on 61 of
  67 June voting days.

- *Picked from the tags, not the players' private reads:* private reads could expose suspicions
  players had not voiced. Because the choice of closing speakers is public, using those reads would
  risk leaking what players secretly think.

- *A moderator line written by code, not a model's summary of the case:* players and humans take the
  moderator's lines as fact, so any mistake in a summary would become a "fact" and read as the game
  endorsing the case. The line names only who is called. It first named the accusers too; a tag can
  be wrong or out of date, and a count of accusers in the moderator's voice was read as fact, so the
  names were dropped (2026-10-16).

- *Considered and dropped:* a closing turn for each accused player's top accuser before the defence.
  It would add two calls and give a pushing wolf one more prominent turn.

- *Evidence:* in the four test games the closing ran on 7 of 12 voting days, and the defended player
  was voted out all 7 times. Whether it ever changes a vote is open.

### Ending the day

<a id="decision-19"></a>

#### 19. The cap drains instead of cutting (2026-10-07).

- *Instead of:* stopping the discussion the moment the cap is reached.

- *Why:* a hard stop left the last accusations unanswered: every June day that ended with an open
  accusation debt was a capped day (10 of them). Draining offers turns for existing debts, bounded so a reply
  that fails to tag its creditor cannot re-fire forever.

- *The cap itself* is three real lines per living player, with a floor of six so a small endgame
  table still gets an exchange. It is a backstop: in the four October test games it was never reached
  (the closest day had 11 lines of 12); days ended because the sweeps ran out.

<a id="decision-20"></a>

#### 20. The day ends when the sweeps run out, not after three passes (2026-10-07).

- *Replaced:* the June rule ended the day after three passes in a row. It was simple and stateless,
  but it ended day 1 after three players, and it left players unasked on some voting days (decision
  16). The sweeps end the day once every player has had the floor, at most twice.

### Voices

<a id="decision-21"></a>

#### 21. The voice goes in the player's own prompt, not in a rewrite.

- *Instead of:* a second model call rewriting each line in a voice.

- *Why:* the [rewrite study](../data/voice_rewrite/README.md) found that
  rewrites read better (74 of 90 preferred by blind judges), but 19 of the 90 changed
  something a listener could act on: "your watch showing me at their door" became "your watch has you
  at their door", and "I'd vote you" became "I'm voting you". A check on names and nights caught 1 of
  the 19. With the voice in the player's own prompt, the model that reasons also speaks, so there is
  no second text to drift.

- *Evidence:* in the [line study](../data/persona_line/README.md),
  blind judges preferred voiced lines to plain ones 25 times in 30. Judged on what a line
  argued, a voiced and a plain line differed in 9 of 30 pairs, and two plain samples of the same turn
  in 3 of 10. The observed proportions were the same, but these small samples do not establish
  equivalent reasoning with and without voices.
  In [eight pairs of ten-seat Haiku games](../data/persona_voice_games/README.md)
  on the same deals, voices off in one and on in the other, several gameplay measures favoured
  voices on: the players' guesses about each other's roles scored better
  in 7 of 8 pairs (a sign test gives p ≈ 0.07), and town won 7 of 8 games with voices on against 4 of
  8 with them off. That is a lean, not a result: eight pairs, games that diverge after the first
  different line, and a voiced side that talked about 19% more. The study did not observe worse
  role-reading performance with voices, but does not establish that voices cannot impair it.

- *Cost accepted:* voices are tone only, which rules out personas with a disposition (aggressive,
  trusting), since those would change play. Two stock phrases were copied into most of their voices'
  lines and were removed: the Badger's quoted "right then", and the Whale's sea phrases, one of which
  made a healer say it "kept watch over" a player, a sentinel's verb.

### Rolling out

<a id="decision-22"></a>

#### 22. No switch for the October day; a tag instead.

- *Instead of:* a config flag to choose between the old and new day.

- *Why:* the change was structural (new graph nodes, a new prompt block per round) and the comparison
  was one-off, so keeping both runnable in the main code was not worth it. The commit before the change
  is tagged `phase2-baseline`; if the new day had played worse, the game could go back to the tag.
  This follows the project's rule for structural variants (`CLAUDE.md`, "Versioning design variants").

---

## How it was checked

| What | How | Result | How far to trust it |
|---|---|---|---|
| The scheduler's rules: debts open and close, freshness, the pair cap and its reset, the sweeps, the drain, the closing's choice of accused | Unit tests on hand-written transcripts, no model (`tests/engine/test_scheduler.py`, `test_sweep.py`, `test_closing.py`, `test_day_rounds.py`) | Pass (2026-10-26) | Implementation evidence for the rules as written. The tests are largely AI-written and not yet audited |
| The tags | Smoke 1; tags against a judge on 183 messages (decision 8) | 27 of 27 tagged players grounded; 79% agreement with the judge | Limited: grounding and semantic agreement are different checks; the judge is unchecked against a person |
| The opening filter | 13 real openings and one planted line, offline (decision 16) | All correct | Limited: 14 lines |
| The echo gate | 65 blind-judged open-floor lines (decision 13) | 10 of 29 restatements held, 0 of 36 worthwhile lines | Limited: one judge per line |
| The whole day | Four games read in full on each version (October: nine-seat flash-lite; then ten-seat Haiku) | The mechanics behave as described | Limited: read games, not a measured comparison |
| Sequential against concurrent | The June acceptance study (decision 1) | Better on structure | Limited: 4 against 8 games, read by the person who built it |

## What is not established

- **There is no standing regression bar for the current discussion design.** The June acceptance
  study used a written rubric and lexical metrics; later changes used small studies and game
  readings. Those checks have not become a consistent set of thresholds for repetition, response
  opportunities, substantive answers or participation under the current design.

- **The tags are the weak joint.** The scheduler and the closing run on the speakers' own tags, which
  missed accusations on 24 of 183 evaluated messages in the nine-seat study. The fraction of
  actual accusations missed is not established by that denominator. A rebuttal that tags nobody
  opens no debt and
  draws no reply. Once, the gate held an accused player's own defence because the accusations against
  it were untagged, so the exemption for answering someone who named you never applied; that player
  never spoke that day and was voted out as a villager (October test game 1, day 3).

- **The gate holds about a third of restatements.** It is not called on the first line of an empty
  floor and never sees the morning report, so a first line restating the record always passes.

- **The opening produced no contest on the nine-seat game:** no evil player claimed in the four test
  games. Evil claims were taken up in the roles work afterwards
  ([reasoning_failures](../deduction/report.md) §4).

- **The closing's effect on voting is unmeasured.** All seven defended players were voted out in
  those games. That does not show whether individual votes changed or what would have happened
  without a closing defence.

- **The knobs were set by hand and never swept:** two cycles per pair, a reset after a table's worth
  of turns, two sweeps, three lines per player.

- **The rules describe the opening order wrongly.** The game rules every player reads say the opening
  is played "in an order drawn at random that day"; the code publishes the openings in seat order
  (`Agents/prompts/game_rules.py`; `Agents/nodes/day/flow.py::start_opening`). Fixing the sentence
  changes a prompt, so it starts a new prompt epoch.

- **No factual-error count has been run on voiced lines.**

---

## When to revisit the design

The limitations above are not all reasons to redesign immediately. The next comparison should
identify which assumption is under test and what evidence would change the decision. The criteria
below are proposed evaluation directions, not checks already run or acceptance thresholds already met.

| Choice | Assumption to test | Evidence that would justify revisiting it |
|---|---|---|
| Speaker-generated tags and engagement-based discharge (8–10) | Tag errors and superficial replies rarely prevent a useful response | Human-checked accusation and response labels show missed opportunities, repeated scheduling, or debts cleared without substantive engagement |
| Seat-order sweeps with reactive priority (2, 7) | Residual order effects are acceptable for the intended game experience | Seat-permuted comparisons show systematic differences in participation, influence or outcomes attributable to order |
| Default speech plus the echo gate (12–14) | Reduced repetition is worth the suppression risk and extra call latency | A fixed evaluation set shows useful lines held, defences lost, or little repetition reduction for the added latency |
| Restricted simultaneous openings (16–17) | Players can disclose useful results without making the first claimant an automatic target | Games with varied roles and evil counterclaims show useful disclosures suppressed or persistent claimant targeting |
| Closing defence (18) | A final response opportunity improves the experience or helps players assess the case | A comparison with no closing finds little useful response content or player value; voting outcomes alone do not settle that question |
| Pair limits, sweeps and the cap (11, 19–20) | The hand-set limits contain loops without cutting off useful exchanges | Parameter comparisons reveal avoidable loops, missed participation or unresolved exchanges at day end |
| Prompted voices (21) | Preferred wording does not materially impair factual accuracy or reasoning | A factual-error audit or larger paired study finds role confusion, meaning changes or degraded role-reading performance |

For a revision, record the baseline commit, prompt/config version, model and backend, sample,
metric definitions, and acceptable tradeoffs before comparing results. Separate **getting a turn**,
**publishing a line**, and **answering a question**: one can improve while another gets worse.
Track model calls and elapsed time separately, since sequential calls affect waiting time as well as cost.

The immediate documentation/code discrepancy is the opening-order sentence described above. Correcting
it should be recorded as a new prompt epoch; this report revision does not change that prompt.

## Code and data

| Part | Code |
|---|---|
| The day's graph and its routers | `Agents/graphs/day.py`; `Agents/nodes/day/flow.py` (`route_speaker`, `route_after_discussion`, `start_opening`, `start_closing`, `collect_round`) |
| Speaker selection | `Agents/turn/scheduler.py::select_next_speaker` (`build_reactive_queue`, `next_sweep_speaker`, the drain) |
| The opening filter | `Agents/turn/round_filter.py::filter_openings` |
| The echo gate | `Agents/turn/echo_gate.py::line_echo_of`, called from `Agents/turn/resolve.py` |
| Who gets a closing turn, and the moderator's line | `Agents/rules/closing.py::closing_speakers`, `closing_announcement` |
| A human's turn and tags | `Agents/turn/human_turn.py`; `Agents/turn/addressing_agent.py` |
| The night-1 lot | `Agents/prompts/prompt_inputs.py::night_one_lot` |
| The round prompts | `Agents/prompts/day_discuss.py` (`OPENING_ROUND_RULES`, `PROACTIVE_ROUND_RULES`, `CLOSING_ROUND_RULES`, `TOWN_VOTE_REASON_RULE`); the turn-order sentence in `Agents/prompts/game_rules.py` |
| The voices | `Agents/prompts/voices.py`; on for hosted games in `server/game/run_config.py` |
| The settings | `Agents/config/game.py::GameConfig` (`per_pair_reengagement_cap`, `reengagement_cooldown_multiplier`, `max_proactive_sweeps`, `discussion_utterance_multiplier`, `min_discussion_utterances`) |

| Record | Where |
|---|---|
| June build journey and smoke tests | [experiment_log.md](experiment_log.md) §2–8; per-case results in `data/`, scripts in `scripts/` (frozen) |
| June acceptance study | [quality_gate/experiment_log.md](quality_gate/experiment_log.md), `quality_gate/data/` |
| October rebuild, step by step | [discussion_evidence](../discussion_evidence.md) §2, §3 (P1), §7.1–7.5 |
| The October test games | `../data/phase2_step8_games/` |
| The echo gate's offline checks | `../data/line_echo_check/`, `round_echo_check/` |
| Voices | [Rewrite study](../data/voice_rewrite/README.md), [prompted-line study](../data/persona_line/README.md), [paired games](../data/persona_voice_games/README.md) |
| Silence calibration | [Study and results](../data/silence_calibration/README.md) |
| The night-1 target check | `../data/night1_target_bias/` |

The wolves' night chat runs on the same principle, one wolf at a time, each reading what was said
before its turn, for up to three rounds (`Agents/nodes/night/pack.py`); it is not covered here.

*Rewritten 2026-10-26 as the account of the current day and its decisions; the earlier report
(the design of 2026-06-05) is in git history. Editorial revision on the same date added navigation
and revision criteria, and corrected the interpretation of lexical
echoes, tag-error denominators, closing outcomes and voice comparisons. Historical measurements are
retained; the narrower conclusions above supersede stronger wording in the linked study summaries.
This editorial pass did not rerun the experiments or implementation tests.*
