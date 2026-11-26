# Working out selected conclusions in code: the deduction engine

*Level 2 · [Context engineering](../context_engineering.md) · separate revision for review, 2026-10-31*

## Page copy (draft)

### What the engine is responsible for

Some failures in the replays were neither a missing fact nor an ambiguous one: the player had every
premise in front of it, often in its own notes, and did not take the first step from them. The healer
the chapter page describes is the case this page follows: blocked on night 1, told by two players that
player_7 had come to it, and through all three of its turns that day not connecting the block to the one
role that could have made it (it got there only in a private note that night, and never said so).

For that kind of failure I chose to work out a selected set of consequences in code and print them into
the prompt. The model keeps the judgement: whom to trust, whom to suspect and what to say.

The engine was a way to support the small model used in live games after input and prompt repairs.
It was not the only way to obtain the inference: later tests found that a higher thinking setting
or a larger model could make the same connection without it. The comparisons below show where the
engine helped and the cost of those alternatives on this case.

### From visible facts to a conclusion

The healer's turn, followed through the engine, shows the path from a seat's facts to a printed line.
Lines come from two stages: rules applied directly to a seat's own results and to claims, where the
healer's lines come from, and a solver that narrows which roles each player could hold.

**The seat's view.** The engine reads what the player's own prompt is built from, and never the hidden
roles: the public record, the seat's own role and night results, and, for a wolf, its pack and the
pack's kills. The public record is the announcements, the dead with the role each revealed at death (a wolf's
conceal can hide one), the read-out wills and the cast, the roles dealt this game. Other players'
statements arrive as claims, kept apart from facts
([chapter 2](../../information_boundaries/information_boundaries.md) explains how the selection is
enforced). The healer's view holds its night-1 record (it tried to
protect player_5 and was roleblocked), the public record of night 1, and two claims: player_3, the
trailseer (a role that learns where one player went each night), said it followed player_7 to the healer,
and player_7 admitted the visit.

**Mechanics as constraints.** The rules then say what each fact implies. Many conclusions depend on what
a role *is* rather than which role it is, so the rules ask about traits: can this role be blocked, is it
immune at night, does a check on it read Suspicious, do its visits show under its own name. One explicit table of role traits answers those questions and is tested against the game
engine’s behaviour. The healer's first line is a direct rule on its own result and one trait: in this cast only
the Chanteuse, a wolf, can block, and a block is a visit, so the Chanteuse came to the healer on
night 1. Its second line joins that result with the two claims.

**Narrowing the possible roles.** At the engine's centre is a solver that keeps, for each
player and for each body whose role was hidden at death, the set of roles it could still hold. Known
roles are fixed; the rest start with every role that still has an unaccounted copy in the dealt cast.
**Constraint propagation**, repeatedly removing the roles the facts rule out until nothing more can be
removed, narrows those sets. The healer's lines do not pass through it, so an illustration (not a
recorded game) shows what it does. Assume one copy of each role:

| Player | Could be, before | Could be, after |
|---|---|---|
| A | Healer or Sentinel | Healer or Sentinel |
| B | Healer or Sentinel | Healer or Sentinel |
| C | Healer, Sentinel or Chanteuse | Chanteuse |

A and B must use up the Healer and the Sentinel between them, so C cannot hold either; nothing had to
be decided about A or B to settle C. The solver repeats rules of four kinds (role counts, closed groups like
the table's, observed actors, and the fact that the game went on, which rules out concealed bodies whose
roles would have ended it) until a full pass removes nothing; the sets are finite and only shrink, so it
stops. Each removal records its rule and the events behind it, so a printed line can be traced back to
its premises.

**The printed line.** The first conclusion is printed where the healer reads its own night result:

> Night 1 (last night): You were roleblocked: your protection of player_5 did not happen. Only the
> Chanteuse could roleblock that night, and a block is a visit, so the Chanteuse, a wolf, came to you
> that night.

The second sits in a block of lines about the other players, under player_7's entry:

> player_3 says player_7 came to you on night 1, and player_7 agrees. If that is true, either player_7
> is the Chanteuse, or player_7 and the Chanteuse both came to you.

Both are the engine's lines for that turn, pinned as an **acceptance case**: a real failed turn, rebuilt
from what the seat knew, that the engine must answer with these sentences and none of a short list of
forbidden ones. The engine prints eight kinds of line in all, from a seat's own results and the public events,
through the possible roles and the joins with claims, to the facts an evil seat gets; the
[evidence report](../../../evidence/gameplay/deduction/report.md) lists them with an example each.

### How strongly can the conclusion be stated?

Look at the two lines again. The first says the Chanteuse came to the healer; the second does not say
that player_7 is the Chanteuse, even though player_7 admitted the visit. The visit rests on two claims,
player_3's report and player_7's admission, so the line holds only under the premise that they are true.
And under that premise another visiting role could still have come to the healer that night, so the line
lists both branches. So the first line is certain; the second lists the alternatives under a named claim.

The wording answers two questions: does the conclusion depend on a claim, and does it identify one
possibility or leave several? A certain line must hold in every legal game compatible with the seat's
information. A conditional line must hold if its named claims are true. An alternatives line keeps
all remaining branches rather than promoting one. The Healer's second line combines the last two:
even if the visit claims are true, either player_7 blocked it or another visitor did.

A conditional line about possible roles comes from running the solver again with the named claim
assumed true; the assumption stays in that run and never enters the baseline sets. A join such as the
healer's second line sets the seat's own result against the claim directly. A single conclusion that holds on only some
branches is not printed at all; the one rule is never to state as absolute what some legal game makes
false. And when the facts contradict one another, the solver returns no candidate result rather than
a forced answer.

The condition belongs in the sentence itself so it remains visible if the player copies the line
into its note. Otherwise a tentative statement can return on the next turn as an unqualified fact.
An incorrect certain line would introduce a false premise whenever its conditions triggered.

### What the engine may know, and what it leaves to the player

Two boundaries keep the engine in its place: what it may use, and what it may say.

**Information access.** Chapter 2 checks that no private field reaches the wrong prompt. The engine
raises a different question, because a line of advice could use hidden information without copying any
forbidden field: "player_7 is a wolf" reads the same whether it came from the rules or from the role
table. So the test asks whether the output depends on anything the seat cannot see: change the hidden
roles of the other players while holding everything this seat can see fixed, and require the deductions
to be identical. An illustration, not a recorded test state, from the seat of an Investigator, the role
that checks one player a night:

| | Test state A | Test state B |
|---|---|---|
| Actual hidden wolf | Alice | Bob |
| Information available to the Investigator | Identical | Identical |
| Expected deduction | Alice or Bob could be the wolf | Alice or Bob could be the wolf |

If the engine named Alice in one state and Bob in the other, its output would be responding to
information the Investigator should not have. A test of this kind is called a **metamorphic test**: it
fixes a relationship the outputs must satisfy (unchanged visible information, unchanged deductions)
rather than the correct answer for each state. It shows independence from hidden information on the
cases tested, not that a conclusion is right: a line can respect the boundary and still be wrong.
Correctness is checked separately, against the actual roles and against a search over every role
assignment the seat's information allows
([Testing whether deductions deserve certainty](../../evaluation/code_checks/code_checks.md)).

**Consequences, not advice.** The lines state what follows from the rules and the record, never whom
to suspect or what to say. The healer's lines do not add "suspect player_7"; whether to say any of this
aloud stays the player's call. The same rule holds on the
evil side, where the question is a **cover**: a false role claim an evil seat can hold up. The engine
gives a wolf, or the solo evil seat, the facts a cover needs: which roles it could claim without
contradicting the public record, and which night stories fit the visits others may have seen. The role
card, the seat's role instructions, gives the advice. The engine's line: "No living player holds the Sentinel, so if you claim it, no
one can counter-claim you truthfully." The card's: "Plan your cover before you need it. Your worked-out
lines list the roles you can claim without contradicting the public record…" 

### What changed in replayed decisions

Three screens rebuilt recorded turns and sampled answers with and without added deductions. They
tested different interventions, so their results should not be combined into an overall effect.

**The Healer's missed connection.** This compared the whole engine against the original prompt,
whose night record ended “you learned nothing tonight.” Enabling the engine replaced that record
and added the other deduction lines. The answer schema was sent as text, the game's live output
mode. The relevant outcomes were whether the Healer's read named player_7 as the Chanteuse and
whether it spoke. Speaking could bring the block into discussion; the deduction itself did not
prove player_7 was the blocker.

**Misreported visits.** A Sentinel learns who visited the player it watched; a Trailseer learns where
its target went. The failing Sentinel denied a visit made by its own watch. This screen added two
lines to an engine already running: its watch was itself a visit, and an explanation of whether
a watch and a follow fitted together. It also included an unrelated input fix.

**Evil covers.** On turns where an evil player had been challenged about a visit, a further line
supplied facts for a consistent cover. The role card and other engine lines stayed the same.

| Screen | Without → with the added deductions | Scope |
|---|---|---|
| Healer | Named the visitor as Chanteuse: 2 → 8 of 10; spoke: 3 → 7 of 10 | One turn, 10 samples per version; engine and replacement night record together |
| Visit reports | Report errors: 6 → 2 of 40; reply errors: 17 → 17 of 55 | Eight report turns and eleven replies, five samples each; all the reduction was on Sentinel reports |
| Evil covers | Role claims: 36 → 44 of 82; denials: 4 → 0 of 82 | 41 turns, two samples each; different model judges assessed the arms |

The unchanged visit replies do not measure what would follow a corrected report: their frozen
transcripts still contained the original denial. The cover comparison is exploratory because the
judge changed between arms. Claims that a careful town could show false also rose from zero to three;
more claims did not mean every cover was sound.

These screens mainly examine lines generated by direct rules. None isolates the constraint solver's
contribution to play; its correctness checks are the code tests described above. The Healer result
also concerns one model setting. Without the engine, the same model at higher effort named player_7
as the Chanteuse in 9 of 10 samples, taking 17.4 seconds per turn against 6.3. Two larger models did
so in 9 and 10 of 10. Running the cheaper of those larger models in every seat cost about $2.30 per
game against $0.12 for the live model. The engine helped on this turn; its value on other missed
inferences needs separate evidence.

The only whole-game comparison bundled revised evil-role cards with engine and other changes.
Wolves won three of eight paired games against none, but the engine's share cannot be isolated
([chapter 1](../../game_design_orchestration/evidence_design/evidence_design.md)).

*Explore: The roleblocked healer →*
<!-- Level 3, planned at deduction_engine/roleblocked_healer.md: the enforced-mode uptake result with its
date and mode; the carried-note 2×2 (9 of 20 against 3 of 20); the placement screens; the investigator's
vote case and the moderator closing line; the 2026-10-30 model and thinking comparison in full with its
subagent-harness caveat. Drafted after this page is reviewed. -->

### Scope and remaining questions

The engine covers the standard twelve roles and the use limits the rules state; a game outside that
set gets no lines at all, because a second blocking role, for instance, would make "only the Chanteuse
could roleblock" false. Its coverage of missed deductions rests on four acceptance cases from real failures, and one kind of
line, the list of every explanation the morning's announcement leaves open for a claim, has never fired
in 278 recorded turns. No whole-game comparison with the engine on and off has been run for the town, and no error rate
after the engine has been measured. The engine, solver included, was written by an AI coding assistant;
my part was the requirement, the grading rule, the acceptance cases from real failures and the
experiments. How its conclusions are checked is on
[Evaluation's code-checks page](../../evaluation/code_checks/code_checks.md); the remaining investigation of the Healer’s response is planned for *The roleblocked healer*.

<!-- Sources for the page copy (checked 2026-10-31). Numbers lifted as they stand; none re-derived.

§1. Failure class and the choice: deduction/report.md §1 (the cause table's third row; "bounded
intervention"). At the time of the build (catalogue header: 2026-10-16 to 10-19): experiment_log.md §2
Question (a larger model ruled out for player turns on cost, about $2.30 a game against $0.12) and §4
table (medium thinking, as played, read 3/10; enforced output mode, 2026-10-16); the prompt rewrite (§6)
came after the engine and input repair alone was never tried on this turn (§8 scope note), so the page
says "each helped elsewhere" and names only the thinking step for this turn (claims review round 2).
Cost, not necessity, dated as a later check (§8, 2026-10-30): report.md 2026-10-30 note and experiment_log.md §8 Result 2 (Haiku
low engine off 2/10; Haiku high 9/10, median 17.4 s against 6.3 s a turn = "about 2.8 times";
Sonnet 9/10, Opus 10/10; Sonnet seats about $2.30 a game against Haiku's $0.12, §2's question restated
in §8; "roughly twenty times" is the owner's phrasing in the outline, the dollar figures stand beside it)
and §8 "What it shows" ("the engine buys most of the gap at the live setting's speed"). "Each helped
somewhere": report.md §1 (July bundle 48% → 30%; thinking on another model 82 → 27 of 267), told on
pages 1 and 3, not here.

The four ten-seat attempts before the engine (notes, not page copy; report.md §1 table; experiment_log.md
§2, §3, §6; the levers list): thinking low → medium, votes right 98/160 against 65/160 at about 2.7× the
output tokens, discussion 47/115 against 49/115 bad (§2; enforced output mode; §9's live-mode re-run:
97/157 against 122/158); a stronger day summariser, 18/30 flawed in each arm (§3; the judge was one of
the two models compared); the private-note rewrite, 27 fact/rule errors against 15 in 56 samples per arm,
not adopted (§6); a majority of three low-effort votes, 39% against 41% (the levers list). Different
cases and measures; not comparable across rows.

§2. The seat's view: report.md §3 "Start with the seat's information" (SeatView from the seat's
payload: public events, own role and night results, pack information for a wolf; claims as claims, not
facts); catalogue §0 "What the seat knows" (announcements, dead roster, votes, dealt cast; wolves' pack
and kill record). Traits: report.md §3 "Translate game mechanics into constraints" (night-immune,
blockable, visits under own name, reads Suspicious; a new role "is declared there"; the table checked
against the engine by the §4 trait check, so "declared by hand and tested", not derived). The healer's
lines are the "Own results" and "Joins" kinds (report.md §3 level table; catalogue A6, F2), not solver
output; "At the engine's centre is a solver" replaces "most lines" (no record counts lines by kind).
Uptake scoped to the one turn (claims review). Model/thinking comparisons all engine off with the
original record (§8 Result 2), so like for like with the 2/10 arm. Solver, A/B/C illustration ("assuming one copy of each role"), the four kinds of rule,
termination, traceability: report.md §3 "Narrow candidate roles until nothing changes". The healer's
path: experiment_log.md §4 "The failure" and "The design"; catalogue AC1. The two printed lines
verbatim: report.md §2 and catalogue AC1 "As built" (line 1 in the night record; line 2 the seat block,
player_7's entry). Acceptance case: catalogue "Acceptance cases" (four; must-say and must-not-say).
Eight levels: report.md §3 level table (one sentence here, linked). Kept off: runtime figures, the
census block sizes (median 4 lines / 742 characters over 278 turns), the cache-boundary placement
(chapter 6), the seat-order rule.

The acceptance-case seat block (AC2, notes only; report.md §3): the investigator's day-3 vote block:
"- If the current role claims are true, the Serial Killer is player_6 or player_10. / - You were
roleblocked on night 2, so the Chanteuse came to you, and player_7 was the Chanteuse. player_2's report
that player_7 came to you that night is true. This does not show that player_2 is the Sentinel. /
- player_8 can be the Serial Killer only if player_2's watch is false." As played, before the engine,
that seat voted out the healer who had protected it.

§3. Why player_7 cannot be named: experiment_log.md §4 "The design" (another player could also have
visited; the block does not prove the trailseer honest; correction 2026-10-16); catalogue AC1 "Must not
say". The three grades: catalogue §0 (certain; follows if named claims are true; possible explanations,
a complete list; "a conclusion that holds only on some branches is not stated at all"; "never state as
absolute what is not"); report.md §2 table. Conditional by rerunning propagation with the claim
assumed: report.md §3 "Keep assumptions separate". The conditional example line: report.md §2.
Contradiction → no candidate result: report.md §3 "Narrow candidate roles". Uptake: experiment_log.md
§4 (all ten low-effort notes on the injected turn recorded the Chanteuse's visit; none without it;
enforced mode, 2026-10-16); report.md §2 ("taken up almost every time").

§4. The seat's view has no votes field (Agents/schemas/deduction.py, SeatView/PublicRecord: cast counts,
dead roster, announcements, read-out wills, living players, claims); the page lists wills, not votes
(claims review 2026-10-31). The question ("did the advice use hidden information?") and the Alice/Bob table: content_plan.md
§2 section 4 (owner's wording, 2026-10-30; "not the state of a specific test"); the test:
tests/engine/deduction/test_candidates.py::test_hidden_roles_the_seat_cannot_see_do_not_change_its_items
(name only; test authorship unmentioned per the handle-with-care list); report.md §4 row "Hidden-state
changes with the visible input held equivalent". "Metamorphic test" named after the words (outline).
Independence on tested cases, not correctness: content_plan.md §2 section 4 scope note; the correctness
checks (random nights through the real engine; the role-assignment oracle) are Evaluation's
code_checks.md "Testing whether deductions deserve certainty", linked, not retold. Consequences not
advice: report.md §1 ("leaving uncertain social judgments and actions to the model"), §3 ("Their role
cards provide the strategic advice; the deduction lines describe consistency"); roles/report.md
decision 11. The cover line: report.md §3 level table, "Evil seat facts" row. The card sentence:
Agents/prompts/roles/pack.py (the wolves' shared discussion instruction, live since 2026-10-19 per
roles/report.md decision 10). The dropped counter-claimant line is in notes only (moved off the page after review, 2026-10-31: it
answers a different question and its record does not call it advice): gameplay/data/counter_claim_votes/
README.md: a true line naming what each of two rival claimants had said, screened on 10 town vote turns,
3 samples each; votes fake/real 12/16 without → 12/17 with, and in its own case 7/4 → 5/7 (the wrong
way); likely cause name salience (the real claimant named first); dropped by the owner 2026-10-18.

§5. Frozen turn / replay: glossed per the outline. Output mode: experiment_log.md §8 Setup
(json_mode = schema sent as text, live for Haiku since 2026-10-14; json_schema = enforced). Row 1:
experiment_log.md §8 Result 1 live row (8/10 read, 7/10 spoke) and Result 2 Haiku low (2/10, 3/10);
scope note in Result 2 (engine on against the original night record; not one line isolated); one turn,
10 samples a setting. The enforced-mode result (§4: 10/10 notes, 0/10 spoke; 2026-10-16; one injected line) named with its
mode and date and sent to the Level 3; §8 Result 1's enforced re-run with the whole engine on spoke 5/10,
so the mode alone does not explain the silence (Level 3). Row 2: gameplay/data/visit_wording_ab/README.md "Arm C" (mech report 6/40
→ 2/40; mech react 17/55 → 17/55; 19 cases = 8 report turns, including a Trailseer's, and 11 replies,
n=5; the gain on the Sentinel's own turns b77857 4→2 and cb1f34 2→0; arm C = rows A56 and E19 plus a fix
in joins/reports.py that let a follow naming the follower reach the engine; arm A re-judged with arm C's
judges; "a replay of those turns cannot show the downstream effect"). Row 3: roles/report.md decision 11 table ("Card, covers off"
36 claims / 4 denials against "Covers, fixed" 44 / 0; claims a careful town could show false 0 of 36 →
3 of 44, "seats departing from the line"; contradicting a sighting 4 → 1; 41 turns, two samples each;
all arms with R11's card and the deduction blocks re-rendered, so the covers line is what differs; the
fixed arm judged by a separate set of judges); report.md §5. Row 2's arms (visit_wording_ab arm A at
tag 1371b5e5, 2026-10-21, against arm C) both ran the engine deployed 2026-10-19; what differs is rows
A56 and E19 plus the joins/reports.py fix. The 2026-10-16 replay's injected text was an earlier wording
("…so the Chanteuse, a wolf, visited you that night"), replacing the record's line (log §4 "The design"). Model/thinking limits: experiment_log.md §8 Result 2 (Haiku
low 2/10; Haiku high 9/10, 17.4 s against 6.3 s; Sonnet 9/10; Opus 10/10; all engine off, game path,
live mode); "$2.30 a game against $0.12" is §2's and §8's "Sonnet seats cost about $2.30 a game against
Haiku's $0.12" (all ten seats on that model). The 2026-10-16 enforced-mode replay (§4) and the 2026-10-30
live-mode run (§8) differ in output mode and in the lines present (one injected line against the whole
engine), so the page attributes the speaking difference to neither. Which stage produced the targeted
lines: healer A6 (own results) and F2 (joins); Sentinel A56 (own record) and E19 (claim comparison);
no replay isolates candidate-role (solver) lines (the "with" arm renders the whole block). Bundled games: roles/report.md "The games: a bundle, eight pairs" (wolves 3 against 0 of 8;
the arms differ by the card text, two engine changes (implied role claims, the covers line) and
everything committed between the builds; "cannot say how much came from
the cards and how much from the engine"). Kept off: the carried-note 2×2, placement screens, the vote
case and the moderator line (Level 3); p-values; the subagent harness.

§6. Scope (standard twelve roles and limits; outside it every seat gets nothing; the second-blocker
example): report.md §3 "Modes" paragraph. Coverage on four acceptance cases; the level that never fired
on 278 turns: report.md §5 last paragraph, §4. No town-side whole-game A/B or post-engine error rate:
report.md §5. Authorship: content_plan.md §2 section 4 ("the engine, solver included, was written by an
AI coding assistant; my part was the requirement, the grading rule, the acceptance cases from real
failures and the experiments"); the outline keeps it on this page only; owner confirmation pending
(brief, open question 1). Test authorship and audit status unmentioned (handle-with-care).

Model names (Claude Haiku 5.5 at low; Claude Sonnet 5.5 and Opus 5.5 as the two larger models) stay in
this note; the page says "a small model at a low thinking setting" and "two larger models". -->

<!-- Supporting material relocated during the 2026-10-31 revision.
The following superseded passages are retained as authoring history, not current claims.

The reason is cost, not necessity. The levers tried before it, repairing the inputs, rewording the
prompt and raising the thinking effort, each helped elsewhere ([page 1](../explicit_game_information/facts.md) and
[page 3](../structured_assessments/turn_request.md) tell those results). On this turn, at the time, one step more
thinking left the connection made in 3 of 10 samples, and a larger model was ruled out on cost; the live
game runs a small model at a low thinking setting. A later check on the same turn found that the same
model at a high thinking setting makes the connection on its own, at about 2.8 times the time a turn,
and so do two larger models, the cheaper of them at roughly twenty times the cost a game. So the engine
is the cheaper route to this step, not the only one; the figures are with the results below.



Every line the engine prints carries its grade in the sentence itself. Two things set the grade:
whether the line rests on the seat's certain information or on a named claim, and whether it reaches one
conclusion or a complete list of alternatives. A complete list is itself true in every legal game, which
is why it may be printed when no single branch may, and it can sit under a named claim, as the healer's
second line does:

| Grade | When it holds | Example |
|---|---|---|
| Certain | in every legal game that agrees with what the seat knows | "…so the Chanteuse, a wolf, came to you that night." |
| Conditional | in every such game in which the named claims are also true | "If player_2's watch is true, player_8 is the Healer: no other role still in play could have come to you on night 2." (another seat's turn) |
| Alternatives | a complete list of the branches the facts leave open, none promoted | "…either player_7 is the Chanteuse, or player_7 and the Chanteuse both came to you." |



The grade is in the wording rather than a heading because a printed line is read as the seat's own
result and copied into its notes (the results below show that on the healer's turn), so the grade has
to survive the copying. A wrong certain line would be copied the same way: not an occasional error but a
false premise wherever its conditions hold.



Each screen **replays** frozen turns, recorded turns rebuilt from the saved game and answered again
several times, with and without the lines in question, and counts what the seat that received them did;
what other seats reply is a separate question. Only the first row turns the whole engine off; the other
two add a line to an engine already running. That row is the healer's turn in the game's live **output
mode**, the answer's schema sent as text rather than enforced
([chapter 6](../../cost_and_latency/cost_and_latency_codex.md) tells why). "Without" is the turn as
played: engine off, the original night record in place with its "you learned nothing tonight". "With"
replaces that record with the line above and adds the engine's other lines. Speaking is the wanted
outcome here: as played, the healer passed all day holding the one fact that would have exposed player_7.

| Failure replayed, and what was added | With the lines, against without | What limits the reading |
|---|---|---|
| The healer's turn; the whole engine against engine off | Its **read** of player_7 (the one-line assessment of another player each turn asks for) named the Chanteuse in 8 of 10 samples against 2 of 10; it spoke in 7 against 3 | The engine against the original record, not one line isolated. One turn, 10 samples a setting. A 2026-10-16 replay of the same turn, schema enforced, with only an earlier wording of the first line in place of the record, found every note copying the line (none without it) and no sample speaking; the runs differ in output mode and in the other lines, so the speaking gain belongs to neither for certain. *The roleblocked healer*, linked below, takes this up. |
| Seats reporting their own watch or follow (a Sentinel learns who came to the player it watched, a Trailseer where the player it followed went); the failing Sentinel had denied a visit its own watch had made. Added: a line on the seat's own record ("your watch was itself your visit") and one on whether a watch and a follow fit | Of 40 report samples, those stating a false rule about these results fell from 6 to 2, all of the fall on the Sentinel's turns; of 55 samples replying to such reports, 17 stated one, with the lines and without | 8 report turns and 11 replies, 5 samples each; an unrelated input fix shipped with the lines. The replies answer the recorded transcript, which already holds the Sentinel's denial, so the replay cannot show what would follow a corrected report: the downstream effect is unresolved. |
| Evil seats asked to explain a visit someone saw. Added: the covers line; the card and the other lines the same in both arms | Of 82 samples in each arm, those claiming a role rose from 36 to 44 and those denying the sighting fell from 4 to 0 (a denial reads as a lie and gets the seat voted out, so a cover is the wanted outcome) | 41 pressured turns, two samples each. Claims a careful town could show false rose from 0 to 3, seats departing from the line. The two arms were classified by different model readers, so a shift can reflect the reader as much as the behaviour: exploratory. |

In each row the counts named moved in the intended direction, within those limits; the cover row is a
direction only. The lines these screens target come from the direct rules (the
healer's own result and its join with the claims; the Sentinel's own record); no replay isolates the
solver's lines, whose checks are the code tests linked above. Where the help is worth having is bounded
by the same healer turn run with the engine off and the original record in place, for every model: the
game's model at its live setting read player_7 as the Chanteuse in 2 of 10 samples; at a high thinking
setting it reached 9 of 10 on its own, a turn taking 17.4 seconds against 6.3; two larger models reached
9 and 10 of 10, and a game with the cheaper of them in every seat costs about $2.30 against $0.12. On
this turn the engine closed most of the gap to those configurations; whether it does so for other
missed steps is untested. The only whole-game comparison bundled revised evil cards with two engine changes and everything else committed between
the two builds: the wolves won 3 of 8 paired games against none before, and the engine's share cannot be
separated
([chapter 1](../../game_design_orchestration/evidence_design/evidence_design.md) tells those games).


-->
