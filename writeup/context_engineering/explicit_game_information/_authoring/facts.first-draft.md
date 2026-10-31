# Making facts available and unambiguous

*Level 2 · [Context engineering](../context_engineering.md) · first draft 2026-10-31*

## Page copy (draft)

When a model player states something false about the game, the natural diagnosis is that the fact
was missing from its prompt. Often it was. But reading the games in October found a second case that
looks the same from the outside: the fact was in the prompt and still went wrong, because the player
had to reconstruct it from prose spread over several days, or the line was worded so that it could
mean something else, or the conclusion rested on a rule the prompt never stated. In the earlier
nine-player version, about 3% of public messages carried a factual error of some kind.

The two cases need different repairs. A missing fact is a wiring fault between the engine and the
prompt. A fact that is present but costly to use is a presentation fault, and its repair follows one
principle: code prints, as data, what a player would otherwise have to work out. The sections below
ask what the player was left to reconstruct, what never reached it, what a present line could be
taken to mean and which rules went unstated, and then whether printing the facts was enough on its own.

### What was the player expected to reconstruct?

The first version of the prompt gave each player the rules, the list of living players and the
transcript, in which the game master announces each death. Who had died, with which role, and which
roles were therefore still in play were all in there, spread across days of prose. One such
announcement, as the transcript of a recorded game shows it:

> game_master: Night of day 3: player_5 was killed by the wolves last night. They were a healer.

To know on day 4 how many wolves could still be alive, a player had to collect every line like it
since day 1, subtract the revealed roles from the public cast and hold the result while writing. The
July census, a count of factual errors over 50 games of the earlier nine-player version, found that
the commonest error was exactly this arithmetic: hunting "the remaining wolf" when no wolf was alive.

Every call now carries two board lines below the transcript, computed by code from the engine's own
record of deaths. From the same prompt:

> == Dead so far (public) ==
> player_2 (vigilante, night 1), player_1 (wolf, lynched day 2), player_4 (villager, night 2), player_5 (healer, night 3)
>
> == Roles still in play (fixed cast minus revealed deaths) ==
> 1 wolf, 1 serial killer, 1 investigator, 2 villager

The first line lists the dead with the role revealed at death and when they died; the second
subtracts those roles from the public cast. In the ten-player game a body's role can be hidden, and
the subtraction would then be one too high, so the line says so in words: "(one of these is dead: a
body whose role is hidden)". The announcement stays in the transcript; what changed is that the
player no longer derives the count from it. Whether a printed count stopped the counting error is the
last section's question, because the first replay of the board said it did not on its own.

### What never reached the prompt at all?

Some facts the engine knew were in the prompt in no form. In October a code review followed each
kind of fact from the engine's events, through the data handed to a player's turn, to the rendered
prompt, and found 12 places where a fact was lost or blurred on the way. The healer had no record of
its own past protections, so it could not say whom it had protected on night 2, and could not test
another player's story about that night. The vote turn, which asks the player to update its private
strategy note, was never shown the note it was replacing, so it overwrote it. And the engine's exact
announcements and a model's summary of the day were rendered under the same day headings, so a false
statement in a summary and the engine event that contradicted it looked equally authoritative.

The main repair is the **night record**: the engine writes each night actor its own account, one
line a night, as the player's own past act: "Night 2 (last night): you checked player_5. player_5
reads Not suspicious." A night with no action says why, so that a player never reads its own silence
as a result it is keeping back: "you chose not to act", "you had no checks left". The vote turn now
sees the note it is asked to revise, and earlier days arrive in three blocks labelled by their
author, which is the subject of [the next page](../day_summaries_and_claim_ledger/previous_days.md).

A check the next day found 8 of the 12 findings addressed and 4 only partly; "addressed" means the
fact now reaches the prompt, not that the model uses it. The behavioural check was a **replay**: a
recorded turn is rebuilt from the saved game and the model answers it again, several times. (When
a replay is the right test, and when only a whole game will do, is the subject of
[Evaluation's replays page](../../evaluation/replays_and_games/replays_and_games.md).) On 89
recorded turns of the nine-player game, three samples each, the samples with a factual error went
from 97 to 82 of 267, with 24 turns better and 14 worse: an improvement in this sample, with
substantial uncertainty.

### What could the wording mean?

A fact that reached the prompt could still be read as a different fact. The investigator in the
recorded game above had checked player_5 on night 3, the night player_5 died with the healer role
announced. Its private result was written:

| | The investigator's night-3 result, as shown to it |
|---|---|
| As played | "Day 3: player_5 was revealed as healer" |
| Reworded | "Night 3 (last night): you investigated player_5, who is the healer" |

"Revealed" is the word the game uses for a role shown at death, the line was dated by day rather than
by night, and it did not say who had done the revealing. Next to the public announcement quoted in the
first section it read as a repeat of public news, and on day 4 the investigator announced a check it
had never made, on another player, whom the village then voted out. Rebuilding that turn and
sampling it 20 times, the as-played line produced an invented check in all 20 and the reworded line in
none, with the real check reported in all 20. How the failure was found in play, and the other
variants tested, are on [Evaluation's factual-errors
page](../../evaluation/factual_errors/factual_errors.md).

Every result is now written as the player's own act on a named night, with the previous night marked
"(last night)", in every game rather than behind a setting, because the old line was a correctness
fault, not a design choice. The result is one turn of one game: it shows the old wording could make
the invention near-certain in that situation, not how often the situation arises. And because the
rewording changed the verb and the dating together, it does not say which of the two mattered.

### What mechanics needed spelling out?

By October, in the ten-player game, invented facts had become rare in the games read in full, and the
commonest player error was a wrong inference about what an ability observes. That cast gives several
town roles a partial view of the night, the design [chapter 1
explains](../../game_design_orchestration/evidence_design/evidence_design.md): a watch shows who came
to the watched player, a follow shows where the followed player went. Players reversed those
directions, read an empty watch as an empty house, and asserted rules the engine does not apply.
Games turned on it. In one, four players asserted that an Illusionist's concealing visit is always
seen and voted out the real Trailseer, whose empty trail was right, because an Illusionist that
carries its own kill leaves no trace. The Sentinel concession on the chapter page, where the real
Sentinel accepted that it should appear in its own visitor list, is the same kind of fault.

The **rules block**, the shared statement of the game's rules that opens every prompt, defined a
visit in one direction and left the inverse unstated; the **role cards**, each role's own
instructions, said what a watch or a follow learns and never what it cannot. I wrote the missing
rules in, stated both ways:

> A visit goes one way, from the visitor to the player visited. A watch on a player shows who came to
> them, never where they went or whether they acted; a follow on a player shows whom they went to,
> never who came to them. "I visited no one" and "no one visited me" are different claims, and a watch
> that saw no one does not mean the watched player stayed home. When you speak of a visit, say which
> way it went: "I went to X", "X came to me".

The block now closes by ranking itself above any player's account of a rule: "These rules are exact.
A player's statement of how a rule works is a claim like any other, and where it disagrees with these
rules, these rules are right."

Each sentence was measured by replaying the turns that had shown the error, on the model that showed
it. On 18 frozen turns from the game with the reversed visits, five samples each, public messages
reading a visit the wrong way round fell from 16 of 35 to 5. The Illusionist case shows the limit. On
that game's turns replayed before and after the sentence, the first speaker seldom made the error at
all; the later speakers, whose transcript already held the false rule asserted by their peers, kept
repeating it: on one model 10 of 10 before the sentence, 7 of 10 after, and 4 of 10 once the ranking
line was added; on a smaller model 10 of 10 throughout. A stated rule guards the origin of a
misreading. It does not undo one the players have already repeated to each other, and these are
single-game replays, not a measure of how often either happens.

### Did making the facts explicit suffice?

Not on its own, and the first test of the board lines said so before they shipped. In July, before
the October repairs above and on the nine-player version, four errors confirmed by a hand count were
replayed six times each under three arms, with and without the board. Three of the four never
recurred in any arm, including the arm with no change: they had been one-off slips. The fourth
recurred with a correct roles-still-in-play line in the prompt. I kept the board as a reference and
added a second change meant to make the player use it: a **read**, a one-line assessment of every
other living player, required before the action and shown back to the player on its next turn.

The pair was then tested together, as **the bundle**, in the one comparison in this chapter whose
measure was written down before its data existed. Error-prone turns from the census were rebuilt and
answered once each under the old prompt and under the bundle, and the census's model reader judged
each answer. A first run pointed the right way and showed that the turns chosen as clean controls
were error-prone too, so the question was reworded around all error-prone turns and written into the
plan before the second run. On 100 fresh turns, 48% of answers under the old prompt carried an error
against 30% under the bundle; in 29 pairs the bundle did better and in 11 worse. The reads cost about
60% more output per call; the board lines added no output.

How far that reaches: the turns were selected because they had gone wrong, so the rates describe
error-prone turns, not whole games; each turn was answered once per arm and judged by a model reader,
with no hand read of the verdicts on record; vote turns were rebuilt with the vote's own result in
view, which makes both arms unlike a real vote; and the board and the reads were never tested apart,
so the comparison supports the pair, not either alone. It is also a test of the first section's lines
with the reads, not of the October repairs, which have only the replays told in their own sections.
Why the reads sit before the action rather than after it is [the question of the page on how the
turn is asked](../structured_assessments/turn_request.md).

### What is not established

There is no factual-error rate for the ten-player game: the census counted the earlier nine-player
version on the old prompt, and every ten-player measurement since is a replay of selected failures
or a reading of a few games. Today's prompt has not been tested as a whole against an earlier one:
the July bundle was tested on its own, and each October repair on its own failing turns, on different
models, so their results cannot be added up. And the longer rules text has a cost of its own: players
have been seen reciting rule sentences as arguments ("a follow only shows where someone went"), an
open item.

<!-- Sources for the page copy (checked 2026-10-31). Numbers lifted as they stand; none re-derived.
Opening: turn_prompt/report.md "The problem" (a fact present but easy to misread causes the same
errors as a missing one; the October investigation found both; facts computed by code, judgement the
model's); map block 140. ~3%: factual_errors/report.md step 1 (68 of 2,292 public messages, 50
nine-seat games, July 2026; a floor). The 0.14% rate is never cited (handle-with-care).
§1: the "before" line is the game master's announcement in the investigator's as-played day-4 prompt
of game 832404e9 (evidence/gameplay/data/investigator_replay/prompt_A.txt, transcript line "Night of
day 3: player_5 was killed by the wolves last night. They were a healer. ..."; the second sentence
of that line, a healer save on player_7, is cut). The two board lines are from the same prompt
(lines "== Dead so far (public) ==" and "== Roles still in play ..."). The outline named the golden
fixture's test board ("player_8 (trailseer, night 1), player_9 (sigilist, lynched day 2)"); the
same-game pair was used instead so that §3's result line comes from the same prompt (brief, open
question 1). Format and the hidden-body clause: report "The board facts";
Agents/prompts/prompt_formatters.py format_dead_roster, format_alive_roles ("(one of these is dead:
a body whose role is hidden)"). First version left agents to work out deaths from the game master's
prose: report decision 1 "Instead of". Census commonest error = survivor arithmetic, "the remaining
wolf": decision 1 "Why"; factual_errors/report.md step 1 table (221 of 368). "First replay said not
on its own": decision 1, T1b.
§2: the code review, 12 places, 2026-10-03: factual_errors/experiment_log.md §8 (findings 1, 3, 5
quoted in substance: healer protections, "whom did you protect on night 2?"; vote overwrites a note
it never rendered; engine facts and summaries under identical day headings); report decision 3.
Triggering game 46355b89 kept off the page (page 2 / Evaluation). Night record wording: report
"The board facts" (the investigator line; "you chose not to act", "you had no checks left";
prompt_formatters.py _quiet_nights: "you chose not to act.", "you did not act: you had no checks
left."). Vote turn shown the note; three labelled blocks: decision 3 "The fixes included". 8
addressed / 4 partly, "addressed" describes the wiring: log §9; decision 3 "Cost accepted". Replay
97 → 82 of 267, 89 cases × 3, 24 better / 14 worse, p = 0.14, "an improvement in this sample, with
substantial uncertainty": decision 3 "Evidence"; log §9 table (97 / 86 / 82; the page quotes the
after_resum arm as the report does). The setting that produced no reasoning tokens is left to the
sources: a replay result's model and setting do not change this page's reading of it.
§3: discussion_evidence.md §6.2; report decision 2. The quote pair as in the report; the night-3
check on player_5, who died that night with the healer role announced; "revealed" = the word for
roles shown at death; dated by day; no "you investigated". Day 4 announcement; player_9 voted out 4
to 1, a villager; the serial killer won (kept to "whom the village then voted out"). 20 samples per
variant, as played 20/20 invented, reworded 0/20 with the real check 20/20; the note-removed arms
and the four-variant table are Evaluation's. Shipped in every game, not behind the v2 switch, "a
correctness bug rather than a design variant": §6.2 "The fix". Handle-with-care: never "the
wording, not the reasoning" (the record's own heading says it; the page does not); two changes at
once; one turn of one game.
§4: report decision 4; discussion_evidence.md §8.4 (ten audited games: invented facts 2, invalid
deductions 28; f02: four players asserted the conceal visit is always visible and voted out the real
trailseer; the owner ruled the carried kill leaves no trace; the Luna sentinel chain), §8.5 item 7,
§8.6 (the visit rule text and its reasoning; "the cards say what a watch or a follow learns, never
what it cannot"; the shared rules defined a visit in the passive). Rule text verbatim from
Agents/prompts/game_rules.py (the visit bullet; the closing "These rules are exact ..." lines).
Visits: 18 frozen turns from game 403f4dbc, 5 samples, Haiku 5.5 at effort low, wrong-way readings
16 of 35 → 5 (§8.6; decision 4). Illusionist: f02 day-4 turns, first speaker seldom made the error;
later speakers repeated it from the transcript; gemini-3.5-flash 10 of 10 → 7 of 10, 4 of 10 with
the ranking line; flash-lite 10 of 10 throughout (§8.4 "The stated rule"; decision 4). Model names
stay here, per the no-model-names rule. "Single-game replays": map block 144. Sentinel: one
sentence, the number stays on the parent. "I wrote the missing rules in": the owner's rulings in
§8.4 ("The owner ruled the same day ... the rules now say so") and the fix in §8.6.
§5: decision 1. T1b: four errors from the earlier hand count, 6 replays × 3 arms = 72 calls,
2026-07-07; three never recurred in any arm incl. no-change; the fourth recurred with a correct
roles line (factual_errors/experiment_log.md §2). Reads: forced one-line read of every living
player, before the action, shown back next turn (decision 1; map 142). T1c: error-prone turns from
the census, old prompt vs bundle, one sample each, census reader; run 1 pointed the right way and
showed the clean controls were error-prone; hypothesis reworded and written into the plan before run
2; 100 fresh contexts, 48% vs 30%, 29 better / 11 worse, one-sided sign test p = 0.003, about $3
(decision 1; log §2). "The one comparison ... written down before its data existed": report
"strongest planned comparison"; log §2 "pre-registered" (research term kept off the page per the
owner). Cost: reads about 60% more output tokens per call (375 → 599), the board added none (T2/T3,
decision 1). Limits: decision 1 "How far it reaches"; log §2 "How far to trust T1c" (no hand read of
verdicts; vote turns rebuilt with the vote's own result in view; both arms read the same rebuilt
turns). Never separated: map 142; content_plan §7. July, nine-seat, before the October repairs:
report "Version and scope", decision dates.
§6: report "What is not established" (first, second and fourth bullets); R11 in the deduction log.
The opening-order sentence mismatch stays off (chapter 1). Test authorship and the audit status of
the suite stay off (handle-with-care).
Kept in notes, off the page: T2/T3 details (60 frozen decisions, 200 calls, wolves read packmates as
wolves 9 of 9, read coverage 0.84–0.85 → 0.93, the coverage monitor); the wolves' night left out of
the July ship and added later; the bench's later flaw-finding on the vote rebuild; the triggering
game of the code review (46355b89); the healer's core-strategy wording still inconsistent at e53cb1e.
-->
