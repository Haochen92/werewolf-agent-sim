# Making facts available and unambiguous

*Level 2 · [Context engineering](../context_engineering.md) · separate revision for review, 2026-10-31*

## Page copy (draft)

A false statement can come from missing information, but it can also come from information the
player was left to reconstruct or interpret. A list of living players and a history of deaths may
contain enough to calculate the remaining roles without stating that count anywhere.

The prompt changes addressed both problems: carry facts that had been omitted, and make existing
facts explicit through computed counts, clearly attributed night results and fuller ability rules.
The tests then asked whether those changes helped agents use the information correctly.

### What was the player expected to reconstruct?

The first version of the prompt gave each player the rules, the list of living players and the
transcript, in which the game master announces each death. Who had died, with which role, and which
roles were therefore still in play were all in there, spread across days of prose. One such
announcement, as the transcript of a recorded game shows it:

> game_master: Night of day 3: player_5 was killed by the wolves last night. They were a healer.

To know on day 4 how many wolves could still be alive, a player had to collect every line like it
since day 1, subtract the revealed roles from the public cast and hold the result while writing. A census of factual errors over 50 games of the earlier nine-player version found survivor
arithmetic was the commonest error, including hunting "the remaining wolf" when no wolf was alive.
Code flagged candidate statements and a model reader judged them; the errors found affected about
3% of public messages, a lower bound rather than a complete count.

Every call now carries two board lines below the transcript, computed by code from the engine's own
record of deaths. From the same prompt:

> == Dead so far (public) ==
> player_2 (vigilante, night 1), player_1 (wolf, lynched day 2), player_4 (villager, night 2), player_5 (healer, night 3)
>
> == Roles still in play (fixed cast minus revealed deaths) ==
> 1 wolf, 1 serial killer, 1 investigator, 2 villager

In the ten-player game a body's role can be hidden, and the second line's subtraction would then be
one too high, so the line says so in words: "(one of these is dead: a
body whose role is hidden)". The announcement stays in the transcript; what changed is that the
player no longer derives the count from it. Whether a printed count stopped the counting error is the
last section's question: in the one error that recurred when the board was first tested, it did not.

### What never reached the prompt at all?

Some facts the engine knew reached the prompt in no form. In October a code review followed each
kind of fact from the engine's events, through the data handed to a player's turn, to the rendered
prompt, and found 12 places where a fact was lost or blurred on the way. The healer had no record of
its own past protections, so nothing the engine wrote could tell it whom it had protected on night 2,
or let it test another player's story about that night. A vote turn overwrote the player's private
strategy note without being shown it. And the engine's exact announcements and the day summary,
a model's condensed account of an earlier day's discussion, were rendered under the same day
headings, with nothing to say which outranked the other.

The main repair is the **night record**: the engine writes each night actor its own account, one
line a night, as the player's own past act: "Night 2 (last night): you checked player_5. player_5
reads Not suspicious." A night with no action says why, so that a player never reads its own silence
as a result it is keeping back: "you chose not to act", "you had no checks left". Earlier days now
arrive in three blocks labelled by their author, the subject of
[the next page](../day_summaries_and_claim_ledger/previous_days.md).

The fixes were checked with **replays**: rebuild a recorded turn from the saved game and ask the
model to answer again. On 89 turns of the nine-player game, three samples per turn, answers judged
by a model reader to contain a factual error fell from 97 to 82 of 267. Twenty-four turns improved
and fourteen worsened. This tested the fixes together, including re-summarised earlier days, so it
does not isolate the night record's effect. The improvement in this sample had substantial uncertainty.
[Evaluation's replays page](../../evaluation/replays_and_games/replays_and_games.md) explains what
these tests can establish.

### What could the wording mean?

A fact that reached the prompt could still be read as a different fact. The investigator in the
recorded game above had checked player_5 on night 3, the night player_5 died with the healer role
announced. Its private result was written:

| | The investigator's night-3 result, as shown to it |
|---|---|
| As played | "Day 3: player_5 was revealed as healer" |
| Reworded | "Night 3 (last night): you investigated player_5, who is the healer" |

"Revealed" is also used for a role shown at death. Dated by day and without an actor, the private
line could read as a repeat of the public announcement. On day 4 the Investigator announced a check
it had never made on another player, whom the village then voted out.

That suggested a presentation problem; it did not establish why the model invented the check.
Rebuilding the turn and sampling it 20 times under each wording produced an invented check in all
20 answers with the old line and none with the new one. All 20 reworded answers reported the real
check. The change named both the actor and the night, so the test cannot separate their effects.
It is one turn, not an estimate of how often this error occurs.

Results now describe the player's own action on a named night, with the previous night marked
“last night.” In the ten-player game the Investigator learns only Suspicious or Not suspicious;
the night-record example above shows that version. [Evaluation's factual-errors
page](../../evaluation/factual_errors/factual_errors.md) covers the discovery and other replay variants.

### What mechanics needed spelling out?

In the ten-player games read in full in October, wrong inferences about abilities were more common
than invented facts. A watch shows who came to a player; a follow shows where a player went.
Agents reversed those directions or treated an empty watch as evidence that the watched player
had done nothing. The chapter page's Sentinel cases show how these misunderstandings entered discussion.

The **rules block**, the shared statement of the game's rules that opens every prompt, defined a
visit in one direction and left the inverse unstated; the **role cards**, each role's own
instructions, said what a watch or a follow learns and never what it cannot. The missing rules went
in, stated both ways:

> A visit goes one way, from the visitor to the player visited. A watch on a player shows who came to
> them, never where they went or whether they acted; a follow on a player shows whom they went to,
> never who came to them. "I visited no one" and "no one visited me" are different claims, and a watch
> that saw no one does not mean the watched player stayed home. When you speak of a visit, say which
> way it went: "I went to X", "X came to me".

The rules also state that a player's account of a rule is a claim: where it conflicts with the
written rules, the rules take precedence.

The visit wording was tested alongside two other prompt lines on 18 recorded turns, five samples
each. Among 35 public-message samples checked for reversing a visit, errors fell from 16 to 5.
That supports the combined prompt change on those cases, not the visit sentence alone.

A different rule exposed a limit. An Illusionist can hide the victim of a wolf attack; when it
carries out that attack itself, the visit leaves no trace. Players asserted the opposite and
rejected a correct empty trail reported by the Trailseer, the role that follows another player's
visits. Adding the missing exception did not reliably undo the false account already in the
discussion. For two later speakers on the original model, errors fell from 10 of 10 samples to 7
with the exception and 4 with the rule-priority sentence added. A smaller model repeated the error
in all 10 samples under each version. A correct rule in the prompt can still lose to a false rule
repeated by other players; these single-game replays do not establish how often that happens.

### Did making the facts explicit suffice?

Not reliably, and the board's first test, before it shipped, is where that shows. That test and the
comparison after it belong to July and the nine-player version: they tested the first section's board
lines together with the reads, not the October repairs, which have only the replays told above.

Four errors confirmed by a hand count were replayed six times each under three arms: no board, the
list of the dead with their roles, and that list with the roles still in play. Three of the four
never recurred in any arm, including the arm with no change. These samples could not establish
whether a repair helped those three cases. The fourth
recurred with a correct roles-still-in-play line in the prompt. With six samples an arm that is one
case, not a measured shortfall, but it meant the board could not be relied on alone. I kept it as a
reference and added a second change meant to make the player use it: a **read**, a one-line
assessment of every other living player, required before the action and shown back to the player on
its next turn. The idea, recorded before the test: a player that has just written a read for every
living player, with no wolf among them, must contradict its own answer to go hunting a remaining wolf.

The board lines and reads were then tested together on error-prone turns from the census. After an
initial run, the question was fixed before a second run on 100 fresh turns. Each turn was answered
once under the old prompt and once with the pair of changes, then judged by the census's model reader.

Answers containing an error fell from 48% to 30%; 29 paired turns improved and 11 worsened. The
reads cost about 60% more output per call. This supports the combined change, not the board or reads
individually. The turns were selected for errors, so these percentages do not describe ordinary games.
Vote prompts also included the vote's own result, unlike a live vote, which limits both conditions.

The board supplied a reference; the reads asked the agent to assess each player before acting.
Why that assessment comes before the action, and whether it improves decisions, is the subject of
[the page on how the turn is asked](../structured_assessments/turn_request.md).

### What is not established

There is no factual-error rate for the ten-player game: the census counted the earlier nine-player
version on the old prompt, and every ten-player measurement since is a replay of selected failures
or a reading of a few games. Today's prompt has not been tested as a whole against an earlier one:
the July bundle was tested on its own, and each October repair on its own failing turns, on different
models, so their results cannot be added up. And the longer rules text has a cost of its own: players
have been seen reciting rule sentences as arguments ("a follow only shows where someone went"), an
open item.

<!-- Sources for the page copy (checked 2026-10-31; revised after the claims review the same day).
Numbers lifted as they stand; none re-derived.
Opening: turn_prompt/report.md "The problem" (a fact present but easy to misread causes the same
errors as a missing one; the October investigation found both; facts computed by code, judgement the
model's); map block 140. The reconstruct-from-prose case was found and fixed in July (decision 1),
hence "in July and again in October". Census: factual_errors/report.md step 1 (50 nine-seat games,
July 2026; code screen, model reader cascade, the owner checked the flagged public messages; 68 of
2,292 public messages, 3.0%, role-fact errors only: deaths, roles, counts, claims; a floor since 2–3
of 15 sampled rejects were real). The 0.14% rate is never cited (handle-with-care). Versions: report
"Version and scope" (nine-seat until 2026-10-09, ten-seat since); decisions 1–3 are nine-seat,
decision 4 ten-seat.
§1: the "before" line is the game master's announcement in the investigator's as-played day-4 prompt
of game 832404e9 (evidence/gameplay/data/investigator_replay/prompt_A.txt, transcript line "Night of
day 3: player_5 was killed by the wolves last night. They were a healer. ..."; the second sentence
of that line, a healer save on player_7, is cut). The two board lines are from the same prompt
(lines "== Dead so far (public) ==" and "== Roles still in play ..."). In that 2026-10-03 prompt the
board sat above the transcript (the earlier layout); "below the transcript" describes today's layout
(report "The order of the prompt", "The board facts"). The outline named the golden fixture's test
board ("player_8 (trailseer, night 1), player_9 (sigilist, lynched day 2)"); the same-game pair was
used instead so that §3's result line comes from the same prompt (brief, open question 1). Format and
the hidden-body clause: Agents/prompts/prompt_formatters.py format_dead_roster, format_alive_roles.
First version left agents to work out deaths from the game master's prose: decision 1 "Instead of".
Census commonest error = survivor arithmetic, "the remaining wolf": decision 1 "Why";
factual_errors/report.md step 1 table (221 of 368). "In the one error that recurred ... it did not":
T1b (decision 1; validation/t1b_results.md: case 2 recurred 2 of 6 with the dead list, 1 of 6 with the
full board, 0 of 6 without; "at N=6/arm no directional claim between arms is supportable").
§2: the code review, 12 places, 2026-10-03: factual_errors/experiment_log.md §8 (findings 1, 3, 5:
the healer "cannot reliably answer 'whom did you protect on night 2?' from engine facts in its
prompt", a strategy note may hold it; the vote renders no previous note and then overwrites it;
engine announcements and model summaries under identical day headings); report decision 3. The
triggering game 46355b89 stays off the page. Day summary gloss: report "The record of past days";
day_summary/report.md (page 2's subject). Night record wording: report "The board facts" (the
investigator line; "you chose not to act", "you had no checks left"; prompt_formatters.py
_quiet_nights: "you chose not to act.", "you did not act: you had no checks left."). Vote turn shown
the note; three labelled blocks: decision 3 "The fixes included". 8 addressed / 4 partly, "addressed"
describes the wiring: log §9; decision 3 "Cost accepted". Replay: discussion_evidence.md §6.5 (three
arms: before 97/267; after with the games' own summaries 86/267, 18 better / 11 worse, p = 0.26;
after with earlier days re-summarised 82/267, 24 better / 14 worse, p = 0.14, "the arm a live game
would match"; one flash-lite judge for all, which §6.5 says "needs work"); report decision 3 quotes
the 82 arm and the page follows the report. Model and thinking setting stay here.
§3: discussion_evidence.md §6.2; report decision 2. The quote pair as in the report; the night-3
check on player_5, who died that night with the healer role announced; "revealed" = the word for
roles shown at death; dated by day; no "you investigated". "Could read as public news" and the
promise-then-invention reading are §6.2's "readings of the prompt's structure, not measurements",
labelled so on the page. Day 4 announcement; player_9 voted out 4 to 1, a villager; the serial
killer won (kept to "whom the village then voted out"). 20 samples per variant, as played 20/20
invented, reworded 0/20 with the real check 20/20; the note-removed arms and the four-variant table
are Evaluation's. Shipped in every game, not behind the v2 switch, "a correctness bug rather than a
design variant": §6.2 "The fix". Today's "you checked" line: decision 2 "The fix". Handle-with-care:
never "the wording, not the reasoning"; two changes at once; one turn of one game.
§4: report decision 4; discussion_evidence.md §8.4 (ten audited games: invented facts 2, invalid
deductions 28; f02), §8.5 item 7, §8.6 (the visit rule text and its reasoning; "the cards say what a
watch or a follow learns, never what it cannot"; the shared rules defined a visit in the passive).
Trailseer and Illusionist glosses: roles/role_sheet.md via chapter 1's observer table; the carried
kill: Agents/prompts/game_rules.py ("Roles that watch or follow see visits, except the pack's kill on
a victim an illusionist concealed, which leaves no trace"; "An illusionist that carries the kill
itself and conceals that victim is not seen there at all"), roles/illusionist.py. Rule text verbatim
from game_rules.py (the visit bullet; the closing "These rules are exact ..." lines). The rulings
were the owner's (§8.4: "The owner ruled the same day ... and the rules now say so"); who drafted the
text is not recorded, so the page says "went in" (brief, open question 2). Visits:
data/haiku_turn_replay/README.md: arms before / after v1 (three fixes: the visit rule, the reply
brief, the vote-reason line) / after v2; 18 frozen turns from game 403f4dbc, 5 samples, Haiku 5.5 at
effort low; wrong-way readings 16 of 35 → 5 (origin 5 → 2 of 15, cascade 11 → 3 of 20); §8.6.
Carried-kill replay: data/phase3_turn_replay/README.md ("The f02 rule", "A rule claim is a claim"):
four day-4 turns, 5 samples, both models; player_1 (origin) flash 1/5 → 0/5, flash-lite 1/5 → 1/5;
cascade turns flash 10/10 → 7/10 → 4/10 with the ranking line, flash-lite 10/10 under all three
prompts; "the origin and control changes are within noise"; §8.4 "The stated rule". §8.6 "Cascades":
"A stated rule did more against a spreading misreading than the f02 replay found". Model names stay
here, per the no-model-names rule. Sentinel: one sentence, the number stays on the parent.
§5: decision 1. T1b arms: baseline (no board), board (dead roster), full_board (+ alive-roles line);
4 errors × 6 replays × 3 arms = 72 calls, 2026-07-07; three never recurred in any arm incl. no-change;
the fourth recurred with a correct roles line (factual_errors/experiment_log.md §2;
t1b_results.md). The reads hypothesis, recorded in t1b_results.md ("the agent that has just written 5
reads with no wolf among them must contradict its own committed output to assert a remaining wolf")
and validation_plan.md T1c ("the reads commitment is the live hypothesis"). Reads: forced one-line
read of every living player, before the action, shown back next turn (decision 1; map 142). T1c:
error-prone turns from the census, old prompt vs bundle, one sample each, census reader; run 1
pointed the right way and showed the clean controls were error-prone; hypothesis reworded and written
into the plan before run 2; 100 fresh contexts, 48% vs 30%, 29 better / 11 worse, one-sided sign test
p = 0.003, about $3 (decision 1; log §2). "Most firmly planned": report "strongest planned
comparison"; T1b and T2 also had expectations in the plan (log §2); "pre-registered" is kept off the
page per the owner. Cost: reads about 60% more output tokens per call (375 → 599), the board added
none (T2/T3, decision 1). Limits: decision 1 "How far it reaches"; log §2 "How far to trust T1c".
Never separated: map 142; content_plan §7. July, nine-seat, before the October repairs: report
"Version and scope", decision dates.
§6: report "What is not established" (first, second and fourth bullets); R11 in the deduction log.
The opening-order sentence mismatch stays off (chapter 1). Test authorship and the audit status of
the suite stay off (handle-with-care).
Kept in notes, off the page: T2/T3 details (60 frozen decisions, 200 calls, wolves read packmates as
wolves 9 of 9, read coverage 0.84–0.85 → 0.93, the coverage monitor); the wolves' night left out of
the July ship and added later; the bench's later flaw-finding on the vote rebuild; the triggering
game of the code review (46355b89); the healer's core-strategy wording still inconsistent at e53cb1e;
the visit replay's reply-brief and vote-reason results (chapter 1 / page 3).
-->

<!-- Supporting material relocated during the 2026-10-31 revision.
The following superseded passages are retained as authoring history, not current claims.

When a model player states something false about the game, the natural diagnosis is that the fact
was missing from its prompt. Often it was. But reading the games, in July and again in October, found
a second case that looks the same from the outside: the fact was in the prompt and still went wrong,
because the player had to reconstruct it from prose spread over several days, or the line was worded
so that it could mean something else, or the facts were there but the rule needed to read them was
not. The July census, a count over 50 games of the earlier nine-player version in which code flagged
candidate statements and a model reader judged them, found an error about deaths, roles or who was
left in about 3% of public messages, as a floor.

The two cases need different repairs. A missing fact is a wiring fault between the engine and the
prompt. A fact that is present but costly to use is a presentation fault, and its repair takes three
forms, each of them code doing what the player was being left to do: it prints, as data, what a
player would otherwise work out; it writes each private result as the player's own act on a named
night; and it states the rules in full, above any player's account of them. The game ran as a
nine-player version until early October and as a ten-player cast since; the board lines, the code
review and the rewording below belong to the first, the rules work to the second. The last question
is whether printing the facts was enough.



A check the next day found 8 of the 12 findings addressed and 4 only partly; "addressed" means the
fact now reaches the prompt, not that the model uses it. The behavioural check was a **replay**: a
recorded turn is rebuilt from the saved game and the model answers it again, several times. (When a
replay is the right test and when only a whole game will do is
[Evaluation's replays page](../../evaluation/replays_and_games/replays_and_games.md).) On 89
recorded turns of the nine-player game, three samples each, judged by a model reader, with the prompt
before and after the review's fixes and earlier days re-summarised as a live game would have them, the
samples with a factual error went from 97 to 82 of 267, and 24 of the 89 turns were better against 14
worse: an improvement in this sample, with substantial uncertainty.



"Revealed" is the word the game uses for a role shown at death, the line was dated by day rather than
by night, and it did not say who had done the revealing. Next to the public announcement quoted in the
first section it could read as a repeat of public news. The record's reading, not a measurement: having
promised the day before to share its result, the investigator found no night-3 result it recognised as
its own, and on day 4 announced a check it had never made, on another player, whom the village then
voted out. Rebuilding that turn and sampling it 20 times, the as-played line produced an invented check
in all 20; the reworded line produced none, and each of its 20 answers reported the real check. How
the failure was found in play, and the other variants tested, are on [Evaluation's factual-errors
page](../../evaluation/factual_errors/factual_errors.md).

Every result is now written as the player's own act on a named night, with the previous night marked
"(last night)", in every game rather than as an optional variant, because the old line was a
correctness fault, not a design choice; today's ten-player line is the one the night record above
shows. The result is one turn of one game: it shows the old wording could make the
invention near-certain in that situation, not how often the situation arises. And because the
rewording changed the verb and the dating together, it does not say which of the two mattered.



By October, in the ten-player game, invented facts had become rare in the games read in full, and the
commonest player error was a wrong inference about what an ability observes. That cast gives several
town roles a partial view of the night, the design [chapter 1
explains](../../game_design_orchestration/evidence_design/evidence_design.md): a watch shows who came
to the watched player, a follow shows where the followed player went. Players reversed those
directions, read an empty watch as an empty house, and asserted rules the engine does not apply, and
games turned on it. In one, the Trailseer, the role that follows a player at night and learns whom
they visited, reported an empty trail on the Illusionist, an evil role that can hide a victim's role.
Four players asserted that an Illusionist's hiding visit is always seen, and voted the Trailseer out.
Its empty trail was right: an Illusionist that carries the pack's kill itself and hides that victim
leaves no visit to see. The Sentinel concession on the chapter page is the same kind of fault.



The carried kill got its own sentence in the rules and on the Illusionist's card ("Roles that watch
or follow see visits, except the pack's kill on a victim an illusionist concealed, which leaves no
trace"), and the block now closes by ranking itself above any player's account of a rule: "These
rules are exact. A player's statement of how a rule works is a claim like any other, and where it
disagrees with these rules, these rules are right."

Each fix was replayed on the turns that had shown the error, on the model that had made it. The visit
rule was tested together with two other prompt lines added the same day. On 18 frozen turns from the
game with the reversed visits, five samples each, the public messages that read a visit the wrong way
round fell from 16 of 35 to 5 of 35, including on the turns where other players had already made the
misreading (11 of 20 to 3).

The carried-kill case shows a limit. Four of that game's day-4 turns were replayed before and after
the sentence. The first player to assert the false rule seldom made the error in either arm (1 of 5,
then 0 of 5: too few to measure the rule on). The two later speakers, whose transcript already held
the false rule asserted several times, kept repeating it: on the model that had played the game,
10 of 10 before the sentence, 7 of 10 after, and 4 of 10 once the ranking line was added; on a smaller
model, 10 of 10 under all three prompts. So in that game a stated
rule did little against a false rule the players had already repeated to each other, while in the
visit replay the repeated misreading did fall. How far a correct rule reaches a false one already in
the transcript is open, and both are single-game replays.



The pair was then tested together, as **the bundle**, in the most firmly planned comparison behind
this page: its measure was written into the plan before the second run's data existed. Error-prone
turns from the census were rebuilt and answered once each under the old prompt and under the bundle,
and the census's model reader judged each answer. A first run pointed the same way and showed that the
turns picked as clean controls were error-prone too, so the question was reworded to cover all
error-prone turns before a second run. On 100 fresh turns, 48% of answers under the old prompt carried
an error against 30% under the bundle; in 29 pairs the bundle did better and in 11 worse. The reads
cost about 60% more output per call; the board lines added no output.

How far that reaches: the turns were selected because they had gone wrong, so the rates describe
error-prone turns, not whole games; each turn was answered once per arm and judged by a model reader,
with no hand read of the verdicts on record; vote turns were rebuilt with the vote's own result in
view, which makes both arms unlike a real vote; and the board and the reads were never tested apart,
so the comparison supports the pair, not either alone. Why the reads sit before the action rather
than after it is [the question of the page on how the turn is asked](../structured_assessments/turn_request.md).


-->
