# The day discussion: who speaks, when, and when the day ends

This page covers how a day's discussion runs in the game today: who gets the floor and in what order,
what keeps the talk from repeating itself, how a day ends, and how each part was tested. It ends with
three dated studies that shaped the design. The build journey of June 2026 is in
[the experiment log](experiment_log.md), and the June acceptance study in
[`quality_gate/`](quality_gate/experiment_log.md). The October 2026 rebuild is recorded in
[discussion_evidence](../game_play_enhancement/discussion_evidence.md) §7, and the voice and silence
studies of 2026-10-18 in the `data/` folders linked from those sections.

## The problem

In Werewolf the town must find the evil players by talking, then vote one out. Every AI player is a
model call. The models decide what each player says. The engine decides everything else about the
conversation: who speaks next, whether a line is published, and when the talking stops.

A good day needs four things:
- **A player who is asked or accused answers next**, not three turns later.
- **Every living player gets a chance to speak**, including a player sitting on a night result.
- **The table hears each point once.** Seven players repeating the same suspicion is noise, and it
  piles votes onto one name.
- **The vote stays fair.**

The design rests on one distinction: **fairness and naturalness matter at different moments.**
Speaking later in a discussion is an advantage, because the later speaker has heard more. That
advantage only counts at the vote. So the vote is blind and simultaneous: every player commits
against the same transcript, and all votes are revealed together. With the vote protected, the
discussion can be sequential, one speaker at a time, each reading everything said before it.

A second distinction decides where models are used. **Who speaks, and when the day ends, is
computed by code from the transcript.** A model is used only for the question code cannot answer:
whether a line adds anything.

## A day today

```
Day 1      opening round → day summary → night
Day 2 on   opening round → discussion → closing defence (if anyone has two accusers) → day summary → vote
                           │
                           ├─ reactive turns: whoever owes an answer speaks next
                           └─ sweeps: when nobody owes, the floor goes round the players who have not spoken
```

Day 1 has no discussion and no vote: there is almost nothing on the record to argue about yet. The
parts below are described in the order a day runs them.

### The opening round: everyone at once, restricted

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

**Why it exists.** In the June design a day ended after three passes in a row. On day 1 almost
everyone passed, so the day ended after three players: in 28 of 28 June games, and 8 of 9 games on
the website. On 8 of 96 June voting days a living player was never offered a turn. The opening round
asks every player at the start of every day, so a player with a result always gets to state it.

**Why at once, and why restricted.** A round of mostly passes played one seat at a time is close to
a minute of "player_x passes" before anything happens; at once, the wait is about one model call.
The June design played open statements at once, and they came out near-identical (the first
study below). The opening escapes that by allowing only private facts and claims, which differ
from seat to seat.

**What the first version got wrong.** In the first games on this day (2026-10-07, nine-seat,
`gemini-3.5-flash-lite`), every investigator who claimed in a day-2 opening was voted out that day:
three times out of three, 7 votes to 1 each time. Reading the games showed a chain. Night-1 targets
fell mostly on seat 1 (in all four test games the investigator checked player_1), because with
nothing to go on the model takes the lowest player number. So the investigator's first result was
about the player most likely to be dead by morning, and the opening rule told it to announce a
result the morning had already revealed. Everyone else passed, so the only name on the table was the
investigator's, and the open floor and the vote piled onto it. Two fixes shipped: on night 1 the
engine draws a default target by lot, which a player takes unless it has a reason not to, and the
opening rule now says a result the morning already made public is not news
([discussion_evidence](../game_play_enhancement/discussion_evidence.md) §7.4 step 8, §7.5).

### The discussion, part 1: reactive turns

Every spoken message carries **speech-act tags**: for each player it addresses, the form
(`question`, `response` or `mention`) and the stance (`accusation`, `defense`, `agreement` or
`neutral`). An AI player writes them as part of the same structured output as its message. A human
types free text, so a separate model call tags the human's message the same way afterwards.

The tags drive the scheduler. A question to a player, or an accusation of a player, **opens an
obligation**, or debt: that player owes the speaker an answer. Any later line by the player who owes
that engages the speaker it owes (a response, a mention or a counter-question) **discharges** it.
Whoever owes an answer speaks before anyone else, the most recently opened debt first. A player owed
by three accusers answers all three in one turn. A real exchange from one of the October games
(`phase2-step8-game1`, day 2):

```
player_7 (open floor)  → player_9: question, accusation
  "Checking someone who died on night one is awfully convenient since it can't be cross-checked.
   Player_9, if you're the real investigator, who are you looking at tonight?"
player_9 (reactive, owes player_7) → player_7: response, defense
  "Player_7, I didn't plan for player_1 to get hit by both the wolves and the serial killer on
   night one. It's just bad luck that my first check died right away."
```

Player_9 spoke next because player_7's tags opened a debt, not because a model chose it. The
speaker's prompt for a reactive turn names whom it owes ("You were directly addressed by player_7.
Respond to them this turn"). Without that line, a player re-derives what to say from scratch and
tends to land on the same generic accusation; with it, an accused player defends.

**Two limits keep a feud from taking over the day.** They are often confused, so separately:
- **Freshness.** While player B still owes player A an answer, another question or accusation from
  A to B, however reworded, opens nothing new. The check ignores wording, so no model is needed to
  judge whether a re-accusation is a new angle.
- **A cap per pair.** After two completed cycles of A pressing B and B answering, further questions
  or accusations from A to B open no debt. Once the pair has gone untouched for as many turns as
  there are living players, the count resets, so a topic that comes back later can be taken up
  again. The cap bounds back-and-forth in a row; it does not ban a topic for the day.

A turn whose model call fails closes the debts that called it, so a provider outage cannot bring the
same player back forever.

### The discussion, part 2: the sweeps (the open floor)

When nobody owes an answer, the **sweep** gives the floor to the living players who have not spoken
today, one at a time in seat order. After each line, any debts it opened are answered before the next
player is asked. A second sweep goes round the players who have been silent since the first began,
but only if the first sweep produced a new line. There are at most two sweeps a day.

On the open floor a player **speaks by default**. Whether a line is worth hearing is decided after it
is written, by the **echo gate**: one cheap model call, at a low thinking level, that reads the new
line against the day's spoken lines. It holds:
- a restatement, of an earlier line or of the record;
- an agreement with no new reason;
- a request someone already made;
- filler.

It keeps a new fact, a reading of the player's own with its reason (even against the table), and a
question or test nobody has asked. Two cases are decided by code, not trusted to the judge: a line
answering a player who named the speaker is never gated, and neither is a human's line. The gate
fails open.

A held line is not published. It becomes a pass marker that keeps the text for its author, whose
next prompt shows that the line was never said, so the player does not go on believing the table
heard it. A held line opens no debt, and it counts for nothing in the closing. A player whose sweep
line was held is not asked again that day: in the game that showed it, the second sweep asked two
held players again and both repeated themselves.

One rule sits on top, for the town only. On a voting day, a town player who would vote for someone
and has not said why today is told to say it instead of passing (added 2026-10-12, after half the
votes in the first Haiku 5.5 game came from players who had not spoken). Evil players are not told
this: for them silence can be the better play.

**Why one at a time, and not a round.** On 2026-10-07 the open floor was briefly a parallel round:
every silent player at once, with a filter afterwards that kept the first of each group of
near-identical points. It generated seven lines to keep two in a day's first round, because seven
players reading the same board at once reach the same conclusion. The filter existed only because
parallel turns cannot see each other. One at a time, each player reads the lines before it, so the
gate has less to hold
([discussion_evidence](../game_play_enhancement/discussion_evidence.md) §7.4 steps 4b and 4c).

**Why the gate, and not a rule telling players when to pass.** A player cannot tell reliably whether
its own line adds anything. That was found twice: in June, when the judgement was folded into the
player's own call (the second study below), and in October, when no wording of the silence rule
moved the decision (the third study). The judgement works only after the line exists, made by a
call that did not write it.

### Ending the day

The discussion ends when nobody owes an answer and the sweeps are done. A hard cap sits behind
that: three real lines per living player (30 with ten alive), and never fewer than six. The cap does
not cut an exchange off mid-way. Once the cap-th line is in, the day **drains**: only debts opened
before that point are answered, each player who owes answers at most once more, and debts opened
during the drain are left for the closing. In the four October test games the cap was never reached (the
closest day had 11 lines of 12); days ended because the sweeps ran out.

### The closing defence

When the discussion ends, the one or two players accused today by at least two different players
each get one last turn, sent at the same time. They may not make new accusations, and nobody
replies. If nobody has two accusers, the day goes straight to the summary.

The accused are picked from the speech-act tags alone, counting spoken lines only. Two alternatives
were considered and rejected:
- **The players' private suspicion reads** would pick the accused more accurately, but who gets a
  closing turn is public, so it would leak what the players secretly think.
- **A model-written summary of the case** in the moderator's voice: players and humans take the
  moderator's lines as fact, so any mistake in it would become a "fact".

The moderator's line is written by code and names only who speaks. It once named the accusers as
well. A tag can be wrong (a question tagged as an accusation) or out of date (an accuser who later
said the story checks out), and a count of accusers in the moderator's voice was read as fact, so
the names were dropped (owner, 2026-10-16).

### The vote

The vote is blind and simultaneous: every living player votes against the same transcript, and the
votes are revealed together. This is where fairness is kept, so the discussion before it is free to
be sequential.

### The voices

In games on the website, each AI player speaks in its puppet's voice: one line in the player's own
prompt describes how it sounds ("Brisk and polite, like a porter on a busy shift: short and
practical"). It may not lean on suspicion, firmness or a side, or hint at a role. Voices have been
on in hosted games since 2026-10-19. In batch games and experiments they are off by default. A human
player is never given one.

Two ways of adding a voice were tested on 2026-10-18:
- **A second model call rewriting each line in a voice** read better (74 of 90 rewrites preferred by
  blind judges), but 19 of the 90 changed something a listener could act on: "your watch showing me
  at their door" became "your watch has you at their door", and "I'd vote you" became "I'm voting
  you". A check on names and nights caught 1 of the 19. Rejected.
- **One voice line in the player's own prompt**, the version shipped. Blind judges preferred it to
  plain text 25 times in 30. Judged on what the line argued, a voiced line and a plain one differed
  in 9 of 30 pairs, and two plain samples of the same turn in 3 of 10. Within that small baseline, the
  voice changed how a player sounds and not what it argues.

Then eight pairs of ten-seat games on Haiku 5.5, voices off in one game of each pair and on in the
other, on the same deal. Every measure leaned toward voices on: the players' guesses about each
other's roles scored better in 7 of 8 pairs (a sign test gives p ≈ 0.07), and town won 7 games of 8
with voices on against 4 of 8 with them off. That is a lean, not a result: eight pairs, games that
diverge after the first different line, and a voiced side that talked about 19% more, which gives the
other players more to go on. What it supports is that the voices did not make the AI players read
each other worse. Two voices' stock phrases were copied into the players' lines and were removed: the Badger's quoted
"right then", which opened most of its lines, and the Whale's sea phrases, one of which made a healer
say it "kept watch over" a player, a sentinel's verb.

## Who decides what

| Decision | Made by | Cost per day |
|---|---|---|
| Who speaks next; when the discussion ends; who gets a closing turn | Code, from the transcript and its tags | None |
| Whom a message addresses or accuses (the tags) | The speaker, in its own structured output; for a human, a tagging call afterwards | None extra for AI players |
| Whether an opening line is of an allowed kind | One cheap call over all the openings | One call |
| Whether a sweep line adds anything | The echo gate, one cheap call per sweep line | One call per sweep turn |
| The moderator's closing line | Code | None |
| What each player says, and its vote | The player's model | One call per turn |

A voting day with a full table costs about 30 model calls (the four October test games).

The scheduler is **stateless**: before every turn it recomputes the open debts and the sweep's
position from the day's transcript alone, with no counters kept on the side. So a resumed game
cannot fall out of step with its own record, and a test can write a transcript by hand and check the
pick.

## How it was checked

| What | How | Result | How far to trust it |
|---|---|---|---|
| The scheduler's rules: debts open and close, freshness, the pair cap and its reset, the sweeps, the drain, the closing's choice of accused | Unit tests on hand-written transcripts, no model (`tests/engine/test_scheduler.py`, `test_sweep.py`, `test_closing.py`, `test_day_rounds.py`) | Pass (2026-10-26) | ✅ for the rules as written. The tests are largely AI-written and not yet audited |
| Can a cheap model write the tags? | Smoke 1 (June, `gemini-3.1-flash-lite`, 30 frozen cases) | 30 of 30 valid outputs; 27 of 27 tagged players named in the message itself, none invented | 🟡: 30 cases, an older model |
| Do the tags match what a reader sees? | 183 agent messages, tags against an LLM judge's reading (nine-seat games, read 2026-10-03) | Same accused player (or none) on 145 (79%); the tags missed an accusation on 24 (13%), added one on 1 | 🟡: the judge is unchecked against a person. Counts of accusers run low more often than high |
| Does the opening filter keep the right lines? | Offline, on two test games' 13 real openings plus one planted padding line | All 13 kept, the padding held | 🟡: 14 lines |
| Does the echo gate hold repeats and keep worthwhile lines? | 65 open-floor lines judged blind by four Sonnet readers, then run through the gate (the third study) | As shipped: 10 of 29 restatements held, 0 of 36 worthwhile lines held | 🟡: one judge per line, 65 lines |
| Does the whole day work? | Four games read in full on each version (October: nine-seat flash-lite; then ten-seat Haiku) | The mechanics behave as described; see the limits below | 🟡: read games, not a measured comparison |
| Does sequential read better than concurrent? | The June acceptance study (the first study) | Yes, on structure | 🟡: 4 against 8 games, read by the person who built it |

## What is not established

- **Discussion quality has never been measured against a fixed bar.** Each version was judged by
  reading a few games. There is no rate of repeated lines, unanswered accusations or silent players
  that a change must not make worse.
- **The tags are the weak joint.** The scheduler and the closing run on the speakers' own tags, and
  the tags miss about one accusation in eight (nine-seat games). A rebuttal that tags nobody opens no
  debt and draws no reply. Once, the gate held an accused player's own defence because the accusations
  against it were untagged, so the "answering someone who named me" exemption never applied; that
  player never spoke that day and was voted out as a villager (October test game 1, day 3).
- **The gate misses most restatements.** As shipped it holds about a third of them. It is not called
  on the first line of an empty floor and never sees the morning report, so a first line restating
  the record always passes.
- **The opening produced no contest on the nine-seat game.** In the four October test games, 5 of
  106 opening turns were spoken, all by the investigator or the vigilante; no evil player claimed. Evil
  role claims were taken up in the roles work afterwards
  ([reasoning_failures](../reasoning_failures/report.md) §4).
- **The closing changed no vote** in those games: the defended player was voted out 7 times of 7.
- **The knobs were set by hand and never swept:** two cycles per pair, a reset after one table's
  worth of lines, two sweeps, three lines per player. One was found mis-set in June (the reset at
  three tables' worth against an intended one) because nothing swept it.
- **No factual-error count has been run on voiced lines.**

---

## Study 1. Concurrent or sequential discussion (June 2026)

*Superseded in part: the sequential design adopted here ran with a different open floor and a
different way of ending the day until October 2026 (the second study, and the sections above).*

**The question.** Should a day's discussion be played as rounds, with every player speaking at
once, or one speaker at a time?

**The design it replaced.** Discussion began concurrent: every player spoke once per round,
generated in parallel against the same snapshot of the transcript, all revealed together. It was a
sound first choice. It was the simplest to build (no scheduler, no state between turns), the fastest
(all calls at once) and fair by construction (no one speaks after anyone else).

**What went wrong.** The property that bought the fairness, everyone answering the same snapshot,
also made repetition invisible: no player could see that another was about to make the same point.
On day 1 of one concurrent game, five of eight players opened with near-identical lines:

```
player_2: "…Does anyone have any initial thoughts on how we should handle the first vote?"
player_5: "…Does anyone have any initial thoughts on who to look out for?"
player_6: "…Does anyone have any initial leads or thoughts?"
player_7: "…Does anyone have a theory on who we should look at first?"
player_8: "…Does anyone have any initial thoughts on who to look out for…?"
```

In a later round, four players asked one player the same question at once ("why did you vote for a
villager?"), and the accused could answer only after the round, to all four together.

**The test.** Four sequential games (`gemini-3.1-flash-lite`, two with memory off and two on) against
eight concurrent games already on disk from the same model family, read by hand against a written
rubric, with three counts from code: how often a line closely matched an earlier one that day, the
top speaker's share of a day, and the longest run by one speaker.

**The result.** Sequential had no near-duplicate lines (0.00 of lines against 0.05–0.06 for
concurrent), and an accused player answered each accuser in turn. Turn shares were comparable.
Concurrent still reached the right lynch when the evidence was strong; it read as parallel
monologues, not as a broken game.

**Its limits.** The comparison was unpaired, the concurrent games' backend and temperature were not
recorded, and the reader had built the sequential design. The counts are descriptive at this N. The
similarity count matches wording, so it shows that blind-round repetition is gone, which follows from
the design, but not that reworded repetition is. The decision rested on what the design guarantees
and the transcripts show in every game, not on a measured difference. It was reversible: the
concurrent design is kept at the tag `concurrent-baseline`.

**What changed.** Sequential discussion was adopted on 2026-06-05, with the blind vote unchanged.

## Study 2. A novelty judge: inside the player's call, or outside it (June 2026)

*Superseded: the June open floor (one quiet player at a time, a lenient novelty judge, the day ending
on three passes) was replaced in October 2026 by the sweeps and the echo gate above.*

**The question.** When nobody owes an answer, how should the engine decide whether a volunteer has
anything new to say?

**The first idea, and why it failed.** The plan cost no extra call: add a novelty label (already said /
borderline / new) as the last fields of each player's own call. Run as a separate judge on a fixed
line it had not written, the label worked: 20 of 20 restatements and 20 of 20 new points labelled
correctly, with the same answers at temperature 0 and 1.0 (Smokes 2 and 3). Folded into the player's
own call (Smoke 4), it failed both ways:
- asked whether the situation had moved on, the player called almost everything a repeat, since a
  mid-game recap is by definition a continuation, which would have silenced everyone;
- asked whether its own point was new, the player called almost everything new, even with a
  paraphrase already in the transcript, which would have silenced no one.

The standalone test had worked because the judge was disinterested and the line was fixed. Folding
the judgement into the player's own generation removed both. So the label was dropped, and silence
became structural: a player who was not given the floor stayed silent.

**What brought the judge back.** The first live games showed what the dropped label had been doing.
On quiet days, players given the floor with nothing owed piled agreement onto the same point; the
players said so themselves ("stuck in a cycle of agreeing… which itself is a trap"). A judge was
added again in the form that had passed: a separate call, after the line was written, on volunteer
turns only, never on an answer. An echo-heavy day's second round fell from 24 turns to 9.

**What it cost, found later.** Reading the June records in October showed the judge was the main
source of silence: of 517 passes in 28 games, 367 were the judge holding a line, and nobody at the
table could tell (discussion_evidence §2.4). That, with the day-1 problem above, led to the October
rebuild.

**What changed.** The lesson carried into today's design: a line's novelty is judged after it is
written, by a call that did not write it, on volunteer turns only.

## Study 3. Calibrating silence on the open floor (2026-10-18)

**The question.** Players seemed to stay silent when they had something worth saying. Was the
silence rule too strict, and could it be tuned to be strict in the opening and looser later?

**The method.** From 16 recorded ten-seat Haiku games, a seeded draw of 162 turns: passes and posted
lines from the opening, the open floor and reactive turns. Each pass was replayed once with "do not
pass this time; write the message you would say". Four blind Sonnet readers sorted every line into
four kinds, without knowing whether it had been spoken, held or forced:
- (A) a new fact: a claim, or the speaker's own night result;
- (B) a new inference, or a different reading of known facts;
- (C) a pointed question or test not yet asked;
- (D) a restatement, a repeated request, or filler.

**What it showed.**
- **The opening was clean.** All 25 posted opening lines were new facts. What opening passes held
  back was mostly a claim the player chose to keep, which is a strategic choice, not a misjudged
  rule.
- **On the open floor, speaking or passing did not separate value.** Forced lines from passes would
  have been worth hearing 57% of the time (23 of 40); posted lines 52% (13 of 25). What passes held
  back was mostly new readings and questions, the case that prompted the study, while about half of
  what was posted restated.
- **No wording fixed it.** Rewriting the silence rule around the four kinds moved no open-floor
  decision. One sentence did all the work: cutting "a pass costs nothing here" doubled open-floor
  speech (20 of 64 turns to 41 of 64), but restatements rose with the worthwhile lines (the player
  spoke on 66% of worthwhile turns and 62% of restating ones, against 37% and 24% before). It was a
  volume knob, not a filter.

**The ruling (owner).** Players speak by default on the open floor; the echo gate does the sorting,
with a bar that holds restatements and filler; the opening stays as it is. The new bar was checked on
the 65 judged open-floor lines: as shipped, at a low thinking level, it holds 10 of 29 restatements
and none of 36 worthwhile lines. The previous bar ("the same point as an earlier line") held none of
either.

**In whole games.** Four ten-seat Haiku games on the deals of four earlier ones: the share of
open-floor turns spoken rose from 41 of 100 to 54 of 93, and the gate held 7 lines, each a
restatement of a line spoken shortly before. Read in full, the open floor carried the games: three of
the four found a killer through it.

**Its limits.** A forced line is what a player writes when told not to pass, which may differ from
what it would have said by choice. Each cell has 23 to 46 turns and one reader per line. The "before"
and "after" games share only their deals.

**What changed.** The open-floor prompt lost the sentence, and the gate gained its bar and a higher
thinking level (`Agents/turn/echo_gate.py`), shipped on 2026-10-19.

---

## Code and data

| Part | Code |
|---|---|
| The day's graph and its routers | `Agents/graphs/day.py`; `Agents/nodes/day/flow.py` (`route_speaker`, `route_after_discussion`, `start_opening`, `start_closing`, `collect_round`) |
| Speaker selection | `Agents/turn/scheduler.py::select_next_speaker` (`build_reactive_queue`, `next_sweep_speaker`, the drain) |
| The opening filter | `Agents/turn/round_filter.py::filter_openings` |
| The echo gate | `Agents/turn/echo_gate.py::line_echo_of`, called from `Agents/turn/resolve.py` |
| Who gets a closing turn, and the moderator's line | `Agents/rules/closing.py::closing_speakers`, `closing_announcement` |
| A human's tags | `Agents/turn/addressing_agent.py` |
| The round prompts | `Agents/prompts/day_discuss.py` (`OPENING_ROUND_RULES`, `PROACTIVE_ROUND_RULES`, `CLOSING_ROUND_RULES`, `TOWN_VOTE_REASON_RULE`) |
| The voices | `Agents/prompts/voices.py`; on for hosted games in `server/game/run_config.py` |
| The settings | `Agents/config/game.py::GameConfig` (`per_pair_reengagement_cap`, `reengagement_cooldown_multiplier`, `max_proactive_sweeps`, `discussion_utterance_multiplier`, `min_discussion_utterances`) |

| Record | Where |
|---|---|
| June build journey and smoke tests | [experiment_log.md](experiment_log.md) §5–8; per-case results in `data/`, scripts in `scripts/` (frozen) |
| June acceptance study | [quality_gate/experiment_log.md](quality_gate/experiment_log.md), `quality_gate/data/` |
| October rebuild, step by step | [discussion_evidence](../game_play_enhancement/discussion_evidence.md) §7.1–7.5 |
| The October test games | `../game_play_enhancement/data/phase2_step8_games/` |
| The echo gate's offline checks | `../game_play_enhancement/data/line_echo_check/`, `round_echo_check/` |
| Voices | `../game_play_enhancement/data/voice_rewrite/`, `persona_line/`, `persona_voice_games/` |
| Silence calibration | `../game_play_enhancement/data/silence_calibration/` |

The wolves' night chat runs on the same principle, one wolf at a time, each reading what was said
before its turn, for up to three rounds (`Agents/nodes/night/pack.py`); it is not covered here.

*Rewritten 2026-10-26 as the account of the day as it runs today, checked against the working tree
of that date; the earlier report (June to October, the design of 2026-06-05) is in git history. The
three studies keep the mechanism as it ran then.*
