# Orchestrating the conversation

*Level 2 · [Game design and orchestration](../game_design_orchestration.md) · previous: [Designing evidence worth debating](../evidence_design/evidence_design.md) · next: [Executing a day and night](../day_and_night/day_and_night.md) · status: page copy drafted 2026-10-26 with the level prompts; for the owner's review.*

## Brief

Copied from [`../content_plan.md`](../content_plan.md), "Level 2 page briefs", section 2 (condensed); the
plan keeps its copy until the owner moves it.

**Reader question:** when every player is a model call, how does the engine decide who speaks, what gets
published and when the day ends, without the machinery itself becoming evidence the players argue
about?

**Promise:** openings, replies, speaking opportunities, publication filters and closing defences.
Silence is the featured investigation; the voices are a short final subsection.

**Featured story:** silence had three sources, and the largest was invisible (block 126): 367 of 517
passes came from a judge's hold; three passes in a row ended day 1 in 28 of 28 games; on 8 of 96 voting
days a player was never offered a turn. Separating "never offered", "held" and "chose to pass"
redirected the October rebuild, ending in the calibration that made speech the default and moved the
filter after the line (128).

**Subsections:** (1) what a good day needs, and what code decides, the day's flow, about 30 calls a
voting day (117); (2) talk in sequence, vote at once, the five openers, the acceptance study's scope
(118); (3) turn order is computed, not chosen: debts, freshness, the pair cap, sweeps, the stateless
scheduler, the tags, the player_7 / player_9 exchange, the tag numbers with their scopes (119, 120);
(4) silence had three sources (126); (5) the opening round and the investigator-lynch chain (122, 127);
(6) speak by default, filter after the line: the calibration, the volume-knob table, the shipped gate,
why a separate judge, what a held line leaves behind, the readers' scope, the possible Level 3 link
(128, 121, 123); (7) a last word for the most-accused, its effect on votes unmeasured (124); (8) how
players sound (125); (9) how it is checked, and what is not established (129, 130).

**Cross-links:** page 3 (parallel and sequential steps as execution); chapter 2 (what each speaker may
see); chapter 3 (the vote-reason and reply briefs, block 145; the night-1 lot, block 146); Evaluation
(the readers' calibration, hardening task 1b).

**Level 3 (possible, owner to decide):** "Silence calibration: a volume knob, not a filter", beneath
subsection 6.

**Tags:** multi-agent orchestration, dialogue management, event-driven scheduling, output guardrails,
LLM-as-a-judge.

This page's exhibit rows are proposed in the drafting notes, for the owner to merge into
[`../exhibits/source_map.md`](../exhibits/source_map.md).

---

<!-- Drafted 2026-10-26 from the sources listed at the end. Not independently verified. -->

## Page copy (draft)

Orchestrating the conversation means running a day's discussion among ten players who are all model
calls. The players decide what they say. The engine decides everything else: who speaks next, whether
a line reaches the table, and when the talking stops.

The players cannot see the engine, so whatever it does looks like behaviour to them. If the engine
never offers a player a turn, the table sees a player who stayed quiet, and in a game about hidden
roles, quiet is suspicious. So the rules that run the day must give everyone a fair chance to speak and
to answer, keep repetition from burying useful lines, and still end the day, without leaving marks the
players will argue about. This page follows those rules through a day. Its featured story is silence:
in my June design, most of it was the engine's doing, and nobody at the table could tell.

### What a good day needs, and what code decides

A good day needs four things:

- a player who is asked or accused gets a prompt chance to answer;
- every living player gets a chance to speak, including one sitting on a night result;
- repetition does not crowd out useful lines: seven players repeating one suspicion is noise, and it
  piles votes onto one name;
- no voter can adapt to votes already revealed.

Two choices follow. Talk order and vote visibility are separate questions: talk runs in sequence, so
each player can answer what was just said, and votes are cast at once, so nobody watches a tally form.
And code decides the flow; a model is asked only what code cannot answer: what a line says, and
whether it adds anything.

```
Day 1      opening round → day summary → night
Day 2 on   opening round → discussion → closing defence → day summary → vote
```

A voting day with a full table costs about 30 model calls (four nine-seat test games on Gemini 3.5
Flash-Lite, October 2026).

### Talk in sequence, vote at once

My first design ran the discussion in concurrent rounds: every player spoke once per round, all
generated in parallel from the same snapshot of the conversation and revealed together. It was simple
and fast, and every player saw the same thing. But no player could see that another was about to make
the same point. On day 1 of one concurrent game, five of eight players opened like this:

```
player_2: "…Does anyone have any initial thoughts on how we should handle the first vote?"
player_5: "…Does anyone have any initial thoughts on who to look out for?"
player_6: "…Does anyone have any initial leads or thoughts?"
player_7: "…Does anyone have a theory on who we should look at first?"
player_8: "…Does anyone have any initial thoughts on who to look out for…?"
```

Sequential turns let each player read every line before its own. That makes avoiding a repeat
possible; it does not make the model do it, which is why a filter still sits after the line (below).
Votes stayed parallel: every living player votes on the same transcript, and the votes are revealed
together. How both patterns run as graph steps is on [Executing a day and
night](../day_and_night/day_and_night.md). The cost is a slower day, and a later speaker still speaks
better informed than an earlier one.

The switch rested on what the design makes possible, illustrated by a small acceptance study: four
sequential games against eight concurrent games already on disk (Gemini 3.1 Flash-Lite, June 2026),
read against a written rubric. The games were unpaired and the reader had built the design, so the
study describes the difference rather than measuring it; the concurrent design is kept under a version
tag and can still be run. The failure came back once: an open floor where all the quiet players spoke
at once, tried in October, generated seven lines to keep two in its first round (nine-seat,
Flash-Lite), and went back to one player at a time.

### Turn order is computed, not chosen

The scheduler is code that picks the next speaker from the day's transcript. My first sequential draft
gave every player a weighted score (pressure, novelty, a talk-time penalty, a boost for the quiet),
but then answering an accusation had to compete with every other term, and the weights had nothing to
be calibrated against. I replaced it with two hard paths to the floor: a player owes an answer, or it
is next on the open floor and nobody owes one.

**Debts come from the speaker's own tags.** Each line carries tags written in the same structured
answer, so they cost no extra call: for each player addressed, a form (question, response or mention)
and a stance (accusation, defence, agreement or neutral), since most lines here are a question and an
accusation at once. A question or accusation opens a debt. Whoever owes speaks first, the newest debt
first, and a player owing three accusers answers all three in one turn. Any later line by the debtor
that engages the speaker clears the debt, whatever its form tag says, because models mislabel the
form: in June, a reply tagged as a mention never cleared, and the same player was picked seven times
in a row.

A real exchange from an October test game (nine-seat, Flash-Lite, day 2), with the tags each speaker
wrote:

```
player_7 (open floor)            → player_9: question, accusation
  "Checking someone who died on night one is awfully convenient since it can't be cross-checked.
   Player_9, if you're the real investigator, who are you looking at tonight?"
player_9 (reply, owes player_7)  → player_7: response, defence
  "Player_7, I didn't plan for player_1 to get hit by both the wolves and the serial killer on
   night one. It's just bad luck that my first check died right away."
```

Player_9 spoke next because player_7's tags opened a debt, not because a model chose it, and its
prompt said so: "You were directly addressed by player_7. Respond to them this turn." The reply defends
the earlier check but never says whom player_9 will investigate. The scheduler can give a turn; it
cannot make the turn an answer. (The prompt's wording is chapter 3's, in [the turn
prompt](../../../evidence/gameplay/turn_prompt/report.md).)

**Two limits keep a feud from taking the day.** The draft's talk-time penalty could never silence a
player who had been addressed, so two players locked on each other could trade lines forever.
*Freshness* replaced it: while B still owes A, another question or accusation from A to B, however
reworded, opens nothing, and because it keys on who pressed whom, no model has to judge whether the wording is new. A
*cap per pair* stops the exchange after two rounds of A pressing and B answering, until the pair has
gone untouched for as many turns as there are living players.

**The open floor, and the end of the day.** When nobody owes, a sweep offers the floor to the players
who have not spoken today, in seat order, answering any new debts before the next player; a second
sweep runs only if the first produced a line. The day ends when nobody owes and the sweeps are done.
Behind that sits a cap of three real lines per living player, and at the cap the day drains rather
than stops: open debts are answered, each debtor at most once more. A hard stop had left accusations
hanging: on the June design, every day that ended with one unanswered had hit the cap.

**Recomputed every turn.** The scheduler keeps no counters; before each turn it works out who owes whom
from the transcript itself. Counters would be the obvious design, but one missed update and they
disagree with the transcript for the rest of the day. Recomputing cannot drift, and a test can write a
transcript by hand and check the pick. The cost: the transcript must hold everything the scheduler
needs, so a human's untagged free text gets a separate tagging call ([Adding a human in the
loop](../human_in_the_loop/human_in_the_loop.md)).

**The scheduler is only as good as the tags.** String matching, tried on 30 frozen cases in June
(Flash-Lite), lost all 11 of its disagreements with the model's tags. Against an LLM judge's reading of
183 messages (nine-seat games, 2026-10-03), the tags named the same accused player, or none, on 145, and
missed an accusation on 24 messages: a rate per message, not the share of accusations missed, against
a judge not yet checked against a person.

### Silence had three sources

On the June design, the first sequential one, a day ended after three passes in a row, and a
volunteer's line went to a novelty judge, a separate model call that could hold it back. The records of
28 nine-seat games on that design (Gemini 3.5 Flash-Lite, played 2026-09-17) show three kinds of
silence:

- **Held.** 367 of 517 passes were the judge holding a line. The table saw only a player who said
  nothing.
- **Never offered.** The three-passes rule ended day 1 after three players in 28 of 28 games (and 8 of
  9 games on the website). On 8 of 96 voting days, a living player was never offered a turn.
- **Chose to pass.** The other 150 passes were players choosing not to speak.

So 71% of the passes were the engine's doing. Players read silence as behaviour less often than
expected: a read of sampled accusations put quietness behind something like one accusation in eight,
and a keyword search found speaking order cited as evidence on 5 of 95 days, never checked by a judge. The
game rules now tell every player that the order of speech is the moderator's doing and says nothing
about a role. Silence was also not why the talk was thin; that came from one exact source of
information that nobody contested, which [Designing evidence worth
debating](../evidence_design/evidence_design.md) takes up.

Separating the three sources gave the October rebuild its targets. "Never offered" got the opening
round and the sweeps: every player is asked at the start of every day, and the day ends when the
sweeps run out, not after three passes. "Held" and "chose to pass" both bear on one question, whether
a line is worth hearing, and the calibration below settled where that is decided: once, after the line
is written.

### The opening round, and what it first got wrong

Every day begins with an opening round, sent to every living player at the same time. An opening may
contain only a role claim or counterclaim, the speaker's own night result if the morning did not
already publish it, or a challenge to an earlier claim with a reason; passing is the normal answer.
It is a round because the three-passes rule left players unasked, and asking everyone gives the holder
of a night result its chance without singling out that role, which would itself be a tell. It runs at
once because a round of mostly passes, seat by seat, is close to a minute of "player_x passes". And it
is restricted because open statements made at once come out near-identical, as the five openers
showed, while claims and private results differ from seat to seat.

One cheap model call then labels each opening's kind and holds anything else. I chose an allow-list
over the open floor's filter because "is this one of three kinds?" is a steadier question for a cheap
model than "is this new?", and a repeated claim is exactly the contest the opening exists for. The call
judges kind, never truth, so a false claim is published; an error keeps the line; a human's opening is
never held. Offline, on 13 real openings and one planted padding line, it kept all 13 and held the
padding.

In its first games (nine-seat, Gemini 3.5 Flash-Lite, 2026-10-07), every investigator who claimed in a
day-2 opening was voted out that day: three of three, 7 votes to 1 each time. Reading the games showed
a chain:

1. Night-1 targets fell on seat 1: with nothing to go on, the model takes the lowest player number. In
   all four test games the investigator checked player_1.
2. So the investigator's first result was about the player most likely to be dead by morning, and the
   opening rule told it to announce that result even when the morning had already revealed it.
3. Everyone else passed, so the investigator's was the only name on the table, and the open floor and
   the vote piled onto it.

Two fixes followed. The opening rule now says a result the morning already made public is not news.
And on night 1 the engine draws a default target by lot; its evidence is chapter 3's, in [the turn
prompt](../../../evidence/gameplay/turn_prompt/report.md). The record lists the fixes, not a later
lynch rate for claimants. The four test games also showed what the opening could not supply: 5 of 106
opening turns were spoken, all by the investigator or the vigilante, and no evil player claimed a role.
Giving evil a way to contest claims became the roles work in [Designing evidence worth
debating](../evidence_design/evidence_design.md).

### Speak by default, filter after the line

On the open floor, a player now speaks by default, and the **echo gate** decides whether the line is
published: one cheap model call, at a low thinking level, that reads the new line against the day's
spoken lines. It holds restatement, agreement with no new reason, a request already made and filler;
it keeps a new fact, the speaker's own reading with its reason, and a question nobody has asked. Code,
not the judge, exempts a line answering a player who named the speaker, and a human's line. If the
call fails, the line is kept.

The gate is a separate call because, in June, a novelty label folded into the player's own call failed
both ways: one wording made the player call almost everything a repeat, another almost everything new.
Run separately on a finished line, the label sorted 20 of 20 restatements and 20 of 20 new points
correctly (Flash-Lite, June, on the gate's predecessor). Those tests also changed the task and its
prompting, so they show that the separate call worked, not why. The design keeps the result: the call
that writes a line never judges it, so generator and verifier stay separate.

**The calibration.** The obvious fix for a quiet open floor was to tune the rule that tells a player
when to pass. To test whether any wording could separate useful lines from restatements, 162 turns
were drawn from 16 ten-seat Claude Haiku 5.5 games (2026-10-18), and each sampled pass was replayed
once with "do not pass this time" added; 6 of the 80 replays failed, leaving 156 judged lines in all. Four blind Claude Sonnet readers, one
per line, sorted each line as a new fact, reading or question, or as restatement or filler, without
knowing whether it had been posted, held back or forced. On the open floor, lines players had held back
were worth hearing 23 times in 40 (57%), and lines they posted 13 in 25 (52%): the choice to speak did
not separate value. Rewriting the pass rule around those kinds moved no decision. Cutting one sentence,
"a pass costs nothing here", moved everything:

| Open-floor turns where the player spoke | With the sentence | Sentence cut |
|---|---|---|
| Turns judged worth hearing (35) | 13 (37%) | 23 (66%) |
| Turns judged a restatement or filler (29) | 7 (24%) | 18 (62%) |
| All turns (64) | 20 | 41 |

*Each turn's value is one blind reader's verdict on its line; one sample per turn and arm; Haiku 5.5,
2026-10-18.*

The sentence was a volume knob, not a filter: more of the useful lines got said, and restatement
nearly tripled. No wording tried made a player better at judging its own line, so the sorting moved
after the line: players speak by default, and the gate holds.

**The shipped gate.** On the 65 judged open-floor lines, the gate as shipped holds 10 of 29
restatements and none of the 36 worthwhile lines; the previous bar ("the same point as an earlier
line") held none of either. In four ten-seat Haiku games on the deals of four earlier games, the share
of open-floor turns spoken rose from 41 of 100 to 54 of 93, and all 7 held lines restated a line spoken
shortly before. The calibration's verdicts come from one reader per line, with 23 to 46 turns in each
cell it compares, and the readers have not yet been checked against a person; how that check is being
built is on [Designing and validating LLM judges](../../evaluation/llm_judges/llm_judges.md). A forced
line may also differ from what a player would have said by choice.

The cost is one more model call per open-floor turn, and more restatement than a perfect filter would
allow: the gate holds about a third. Keeping the line when the call fails does not cover a wrong
verdict; a mistaken hold still silences a line, as the limits below show.

**A held line leaves nothing behind.** Nobody sees it, its author included, and the private note
written with it is dropped, so the author does not go on believing the table heard it. It opens no
debt, counts for nothing in the closing, and its author is not asked again that day. The last two
rules came from test games: held lines' tags once counted toward the closing, so the moderator named
four accusers of six whose lines nobody had heard; and a second sweep re-asked two held players, who
both repeated themselves.

**Explore the method:** how passes were replayed and judged, the four prompt changes and the gate's
bars → [Silence calibration: a volume knob, not a filter](silence_calibration.md).

### A last word for the most-accused

When the discussion ends, the one or two players accused today by at least two different players each
get a closing defence: one last turn, sent at the same time, with no new accusations and no replies. It
is the accused player's last word before the vote, as in Town of Salem, without a second vote.

The trigger I first wanted was an accusation still unanswered, but the scheduler lets an accused
player reply before the day can end, so those existed only on capped days. Being most-accused works
better: in the 28 nine-seat games on the June design, the lynched player was among the day's
most-accused on 61 of 67 voting days. The count uses the public tags, never the players' private reads,
because who gets a closing turn is public and would leak what players secretly think (what each seat
may see is chapter 2's, in [Agent information boundaries](../../../evidence/agent_boundaries/report.md)).

A moderator line written by code announces the closing. A model's summary of the case is the obvious
alternative, but players take the moderator's lines as fact, so a mistake in it would become a "fact"
the game seemed to endorse. The code-written line first named the accusers too; a tag can be wrong,
and a count in the moderator's voice was read as fact, so the line now names only who is called. A turn
for each accused player's top accuser was considered and dropped: two more calls, and one more
prominent turn for a wolf pushing a lynch.

In four test games (nine-seat, Flash-Lite, October 2026), the closing ran on 7 of 12 voting days, and
the defended player was voted out all 7 times; whether a closing defence ever changes a vote is
unmeasured.

### How players sound

On the website, each AI player speaks in its puppet's voice, set by one line in its own prompt, e.g.
"Brisk and polite, like a porter on a busy shift: short and practical." A voice is tone only: it may not
lean on suspicion, firmness or a side, or hint at a role. Batch games run without voices, and a human
player is never given one.

The obvious way to add a voice is a second call that rewrites each line. In a rewrite study (30 real
lines in three voices each, rewritten by Haiku 5.5, judged by blind Claude Sonnet readers), the
rewrites read better in 74 of 90 cases, but 19 of the 90 changed something a listener could act on:
"your watch showing me at their door" became "your watch has you at their door". A check on names and
nights caught 1 of the 19. So the voice goes in the player's own prompt, where the model that reasons
is also the one that speaks, and there is no second text to drift.

On frozen Haiku turns, a voiced and a plain line differed in what they argued in 9 of 30 pairs, and
two plain samples of the same turn in 3 of 10: the same rate, on too few pairs to show that the voice
changes nothing. In eight pairs of ten-seat Haiku games on the same deals, the players' guesses about
each other's roles scored better with voices in 7 of 8 pairs, but the voiced side also talked about
19% more, so that is a lean, not a result. No count of factual errors has been run on voiced lines.

### How it is checked, and what is not established

The scheduler's rules are tested apart from their effect: unit tests on hand-written transcripts, with
no model, pin debts opening and closing, freshness, the pair cap and its reset, the sweeps, the drain
and the choice of who gets a closing turn. They show the rules work as written, not that they make a
good day. The tags, the opening filter and the gate have the small behavioural checks above, and the
whole day was read in full on four games for each version. Any revision has to keep three things
apart, **getting a turn**, **publishing a line** and **answering a question**, since one can improve
while another gets worse: the player_9 exchange got a turn and was published, and still did not answer.

What is not established:

- **No standing regression bar.** There are no fixed thresholds for repetition, response
  opportunities, substantive answers or participation under the current design, and today's discussion
  has not been measured against the nine-seat design's.
- **The tags are the weak joint.** A rebuttal that tags nobody opens no debt. In one October test game
  (nine-seat, Flash-Lite, day 3), the accusations against player_7 carried no tags, so every route to
  speak failed together: no reply was queued; its open-floor line, a defence, reached the gate without
  the exemption for answering an accuser and was held as a repeat; a held player is not asked again;
  and no closing ran. Player_7 was voted out as a villager without having spoken that day.
- **Order effects are unmeasured.** A later speaker's advantage and the framing set by early speakers
  have not been quantified; a comparison with seats permuted is the proposed test.
- **The numbers were set by hand and never swept:** two rounds per pair, the reset after a table's
  worth of turns, two sweeps, three lines per player. One shipped wrong: the reset sat at three tables'
  worth instead of one, and was corrected about 20 days later, found on a reading of the code.
- **The rules describe the opening order wrongly.** The rules every player reads say the openings run
  in an order drawn at random; the code publishes them in seat order. Fixing the sentence changes a
  prompt, so it waits for the next prompt version.

**Evidence.**

- [The day discussion: who speaks, when, and when the day ends](../../../evidence/gameplay/discussion/report.md),
  "The problem", "A day today", decisions 1–4, 7–21, "How it was checked" and "What is not
  established".
- [Discussion evidence](../../../evidence/gameplay/discussion_evidence.md), §2.4 (the three sources of
  silence), §7.1 (what the game records say), §7.4 step 8 and §7.5 (the October test games and the
  investigator chain).
- [Silence calibration](../../../evidence/gameplay/data/silence_calibration/README.md), steps 1–5.
- [Voice rewrite study](../../../evidence/gameplay/data/voice_rewrite/README.md),
  [prompted-voice line study](../../../evidence/gameplay/data/persona_line/README.md) and
  [paired voice games](../../../evidence/gameplay/data/persona_voice_games/README.md).
- [June acceptance study](../../../evidence/gameplay/discussion/quality_gate/experiment_log.md).

<!-- Sources for the page copy (drafted 2026-10-26):
Opening: map 117; discussion/report.md "The problem" (the engine decides the rest), decision 15
("they may read the machinery as behaviour"); content plan brief 2 reader question.
Needs and two choices: report "The problem" (four needs; two distinctions); day flow: "A day today"
(closing only if anyone has two accusers: stated in the closing subsection); ~30 calls: "Who decides
what" footnote and discussion_evidence §7.4 step 8 (four games, flash-lite, memory off, "about 30 calls
a voting day"); model gemini-3.5-flash-lite per §7.4 step 8 and §7.3.
Sequence vs concurrent: decision 1 (sound first choice; five openers verbatim; enables, does not
guarantee; cost; acceptance study: 4 vs 8, gemini-3.1-flash-lite, written rubric, unpaired, reader had
built the design, descriptive; tag concurrent-baseline). Lexical echo metric (0.00 vs 0.05–0.06) left
out: the 0.60 threshold misses paraphrase, so it needs a caveat longer than its value here. Parallel
open floor: decision 7 (2026-10-07, seven lines to keep two, tag phase2-parallel-proactive); nine-seat
flash-lite from §7.4 (the step 6 capture predates the step 8 games, same model).
Scheduler: decisions 3 (weighted score, two hard paths), 8–10 (tags, two dimensions, any engagement
discharges; seven times in a row, June), 11 (freshness, pair cap, talk-time penalty replaced, reset),
4 (stateless; human tags), 19–20 (drain; cap 3/player, floor 6; 10 capped June days with an open
accusation debt per §7.1; the cap never reached in four October games, closest day 11 of 12, cut for
length); "Reactive turns" exchange and prompt line verbatim (phase2-step8-game1, day 2); "The sweeps".
Tag numbers: decision 8 evidence (Smoke 1, June, gemini-3.1-flash-lite, 30 frozen cases, 11
disagreements favoured the model; 145/183, 24 missed, message-level, judge unchecked; the 1 added
accusation cut for length). Quietness "one in eight": §2.4 extrapolates from 25 sampled accusations in
the "behaviour pattern" bucket (about a fifth about silence), hence "a read of sampled accusations". Vote-reason / reply briefs: block 145, chapter 3 (linked to the
turn-prompt report until the chapter 3 page exists).
Three sources: discussion_evidence §2.4 (517 passes, 367 novelty gate, 150 chose, 71%; 25 sampled
accusations, ~1 in 8; 5 of 95 days, keyword search, unjudged) and §7.1 (28 of 28, 8 of 9 website, 8 of
96 voting days); model and date: discussion_evidence closing sources line (gemini-3.5-flash-lite on
Vertex) and report decision 12 (played 2026-09-17); §2.5 (thin talk = one uncontested source; engine
silence not the main cause). Rule sentence: decision 15 ("less than expected"). Mapping to the rebuild:
map 126 ("redirected the October rebuild (the opening round, the sweeps, default speech)"); decisions
16, 20, 13.
Opening: "The opening round"; decision 16 (why a round, at once, restricted, allow-list; 13 + 1
offline; 5 of 106); decision 6 (no guaranteed slot for the investigator: priority would single it out).
Chain: decision 17 (2026-10-07, nine-seat, gemini-3.5-flash-lite, three of three, 7-1; three links;
two fixes); §7.4 step 8 (5 of 106, no evil claim). Night-1 lot evidence: block 146, chapter 3.
Gate: "The sweeps" (holds/keeps/exemptions/fails open); low thinking: Agents/turn/echo_gate.py
get_llm_judge("low"), checked 2026-10-26. Separate judge: decision 12 (Smokes 2-4, 20/20 and 20/20,
temperature 0 and 1.0; does not isolate the cause); discussion/experiment_log.md Smokes 2-4
(flash-lite, June).
Calibration: decision 13; silence_calibration/README.md step 1 (162 turns, 16 games = the persona voice
games, Haiku 5.5; 156 lines; four blind Sonnet subagents, one per line, blind to spoken/held/forced;
open-floor pass 40 at 57% = 23; posted open floor 25 at 52% = 13), step 2 (rewrite moved no decision),
step 3 table (pass sentence cut: worth hearing 13/35 → 23/35; D 7/29 → 18/29; total 20/64 → 41/64;
37/24 → 66/62), step 4 (v3 as ported 10/29, 0/36; current bar 0/29, 0/36), step 5 (4 games on the
deals of voices-01..04; 41 of 100 → 54 of 93; 7 held, all restating a line spoken shortly before).
Readers unchecked: map 128, hardening task 1b. "Holds about a third": report "What is not
established". Failed call vs wrong verdict: portfolio-writing-prompt evidence discipline; content plan
page 4 subsection 6. Held line: decision 14 (note dropped; no debt; closing; not re-asked; four
accusers of six; four calls nothing kept); the 2026-10-14 layout change left out (dated history, not
needed to explain the rule).
Closing: "The closing defence"; decision 18 (design intent, Town of Salem; trigger; 61 of 67 (28 June
games); public tags not private reads; code-written line; names dropped 2026-10-16; top-accuser turn
dropped; 7 of 12 voting days, 7 of 7 voted out, effect open); §7.1 (unanswered accusations only on
capped days).
Voices: "The voices"; decision 21; voice_rewrite/README.md (30 lines, three voices, Haiku 5.5
rewriter, blind Sonnet subagents; 74/90; 19/90; gate 1 of 19; drift pair verbatim); persona_line/
README.md (15 frozen Haiku turns judged as 30 voiced-vs-plain pairs, 10 per voice, plus 10
plain-vs-plain pairs; stance 9/30 vs 3/10; the 25-of-30 naturalness preference left out for length);
persona_voice_games/README.md (8 pairs, Haiku 5.5, Brier better 7 of 8; p ≈ 0.07 and the town-wins
figures left out, the plan asks for a lean; 206 vs 246 lines ≈ 19% more). Voices on in hosted games:
server/game/run_config.py persona_voices=True (checked 2026-10-26).
Checks and limits: "How it was checked" (tests/engine/test_scheduler.py, test_sweep.py,
test_closing.py, test_day_rounds.py; four games read in full per version); "When to revisit the
design" (getting a turn / publishing / answering); "What is not established" (no regression bar; tags
weak joint; held-defence case = discussion_evidence §9 item 9, phase2-step8-game1, day 3; order
effects, seat-permuted test; knobs; opening-order sentence, Agents/prompts/game_rules.py line 43
"in an order drawn at random that day", checked 2026-10-26); decision 11 (reset shipped wrong ~20
days, found 2026-06-24). Discussion quality vs nine-seat: gameplay hub problem 2; content plan
"No overclaims". -->
