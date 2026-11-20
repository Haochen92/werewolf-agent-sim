# Working out selected conclusions in code: the deduction engine

*Level 2 · [Context engineering](../context_engineering.md) · first draft 2026-10-31*

## Page copy (draft)

### What the engine is responsible for

Some failures in the replays were neither a missing fact nor an ambiguous one: the player had every
premise in front of it, often in its own notes, and did not take the first step from them. The healer
the chapter page describes is the case this page follows: blocked on night 1, told by two players that
player_7 had come to it, and never connecting the block to the one role that could have made it.

For that kind of failure I chose to work out a selected set of consequences in code and print them into
the prompt. The model keeps the judgement: whom to trust, whom to suspect and what to say.

The reason is cost, not necessity. The levers tried before it, repairing the inputs, rewording the
prompt and raising the thinking effort, each helped somewhere ([page 1](../explicit_game_information/facts.md) and
[page 3](../structured_assessments/turn_request.md) tell those results), and none removed this failure at the
setting the live game runs on: a small model at a low thinking setting. The same model at a high
thinking setting makes the healer's connection on its own, and so do two larger models, but at about
2.8 times the time a turn, or, for a larger model, seats costing roughly twenty times as much a game
(about $2.30 against $0.12). A conclusion computed once in code supplies the step at the live setting's
speed; the figures are in the results below.

### From visible facts to a conclusion

The healer's turn, followed through the engine, shows the whole path.

**The seat's view.** The engine starts from the same selected information the player's prompt is built
from: the public record (the announcements, the dead with the roles revealed at death, the votes and the
dealt cast), the seat's own role and night results, and, for a wolf, its pack and the pack's kills. It
never reads the hidden roles, and other players' statements arrive as claims, kept apart from facts
([chapter 2](../../information_boundaries/information_boundaries.md) explains how the selection is
enforced). The healer's view holds its night-1 record (it tried to protect player_5 and was
roleblocked), the public record of night 1, and two claims: the trailseer's report that it followed
player_7 to the healer, and player_7's admission of the visit.

**Mechanics as constraints.** The rules then say what each fact implies. Many conclusions depend on what
a role *is* rather than which role it is, so the rules ask about traits: can this role be blocked, is it
immune at night, does a check on it read Suspicious, do its visits show under its own name. One table of
role traits answers those questions, checked against the game engine's own behaviour rather than
written by hand. The healer's first step uses one trait: in this cast only the Chanteuse, a wolf, can
block, and a block is a visit, so the Chanteuse came to the healer on night 1.

**Narrowing the possible roles.** Most of the engine's lines come from a solver that keeps, for each
player and for each body whose role was hidden at death, the set of roles it could still hold. Known
roles are fixed; the rest start with every role that still has an unaccounted copy in the dealt cast.
**Constraint propagation**, repeatedly removing the roles the facts rule out until nothing more can be
removed, narrows those sets. The healer's lines do not need it, so an illustration (not a recorded game)
shows the step the healer's case does not. Assume one copy of each role:

| Player | Could be, before | Could be, after |
|---|---|---|
| A | Healer or Sentinel | Healer or Sentinel |
| B | Healer or Sentinel | Healer or Sentinel |
| C | Healer, Sentinel or Chanteuse | Chanteuse |

A and B must use up the Healer and the Sentinel between them, so C cannot hold either; nothing had to
be decided about A or B to settle C. The solver repeats four kinds of rule: role counts (every copy of a
role has a known holder, so it is removed elsewhere); closed groups, as in the table; observed actors
(one of several players must have acted, and only one can still hold the role the act required); and
game continuation (a hidden body cannot have held a role that would have ended the game earlier). Each
removal can enable another, so the solver repeats until a full pass removes nothing, and it stops
because the sets are finite and only shrink. Each removal records its rule and the events behind it, so
a printed line can be traced back to its premises.

**The printed line.** The first conclusion is printed where the healer reads its own night result:

> Night 1 (last night): You were roleblocked: your protection of player_5 did not happen. Only the
> Chanteuse could roleblock that night, and a block is a visit, so the Chanteuse, a wolf, came to you
> that night.

The second sits in a block of lines about the other players, under player_7's entry:

> player_3 says player_7 came to you on night 1, and player_7 agrees. If that is true, either player_7
> is the Chanteuse, or player_7 and the Chanteuse both came to you.

Both are the engine's lines for that turn, pinned as an **acceptance case**: a real failed turn, rebuilt
from the information the seat had, that the engine must answer with these sentences and with none of a
short list of forbidden ones. The engine works at eight levels in all, from a seat's own results to the
facts an evil seat gets; the [evidence report](../../../evidence/gameplay/deduction/report.md) lists
them with an example line each.

### How strongly can the conclusion be stated?

Look at the two lines again. The first says the Chanteuse came to the healer; the second does not say
that player_7 is the Chanteuse, even though player_7 admitted the visit. Two things stop it. Another
visiting role could also have come to the healer that night, so the block does not single out player_7.
And a true report does not establish the reporter's role: a wolf can report a visit that really
happened. So the first line is certain; the second lists the alternatives under a named claim.

Every line the engine prints carries one of three grades, and the grade is in the sentence itself:

| Grade | When it holds | Example |
|---|---|---|
| Certain | in every legal game that agrees with what the seat knows | "…so the Chanteuse, a wolf, came to you that night." |
| Conditional | in every such game in which the named claims are also true | "If player_2's watch is true, player_8 is the Healer: no other role still in play could have come to you on night 2." (another seat's turn) |
| Alternatives | a complete list of the branches the facts leave open, none promoted | "…either player_7 is the Chanteuse, or player_7 and the Chanteuse both came to you." |

A conditional line comes from running the solver again with the named claim assumed true; the
assumption stays in that run and never enters the baseline sets. A conclusion that holds on only some
branches is not printed at all; the one rule is never to state as absolute what some legal game makes
false. And when the facts contradict one another, the solver returns no candidate result rather than
a forced answer.

The grade is in the wording rather than a heading because an injected line is taken up almost every
time: in ten replays of the healer's turn, every note recorded the Chanteuse's visit once the line was
present, and none did without it. A wrong certainty would therefore not be an occasional error. It would
be a false premise in every game where the line's conditions hold, read by the player as its own result.

### What the engine may know, and what it leaves to the player

Two boundaries keep the engine in its place: what it may use, and what it may say.

**Information access.** Chapter 2 checks that no private field reaches the wrong prompt. The engine
raises a different question, because a line of advice could use hidden information without copying any
forbidden field: "player_7 is a wolf" reads the same whether it came from the rules or from the role
table. So the test asks whether the output depends on anything the seat cannot see: change the hidden
roles of the other players while holding everything this seat can see fixed, and require the deductions
to be identical. An illustration, not a recorded test state:

| | Test state A | Test state B |
|---|---|---|
| Actual hidden wolf | Alice | Bob |
| Information available to the Investigator | Identical | Identical |
| Expected deduction | Alice or Bob could be the wolf | Alice or Bob could be the wolf |

If the engine named Alice in one state and Bob in the other, its output would be responding to
information the Investigator should not have. A test of this kind is called a **metamorphic test**: it
fixes a relationship the outputs must satisfy, unchanged visible information means unchanged
deductions, rather than the correct answer for each state. It shows independence from hidden
information on the cases tested, not that a conclusion is right: a line can respect the boundary and
still be wrong. Correctness is checked separately, against the actual roles and against a search over
every role assignment the seat's information allows
([Testing whether deductions deserve certainty](../../evaluation/code_checks/code_checks.md)).

**Consequences, not advice.** The lines state what follows from the rules and the record, never whom
to suspect or what to say. The healer's lines do not add "suspect player_7"; whether a wolf would admit
such a visit, and whether to say any of this aloud, stays the player's call. The same rule holds on the
evil side, where the question is a **cover**: a false role claim an evil seat can hold up. The engine
gives a wolf or lone killer the facts a cover needs, which roles it could claim without contradicting
the public record and which night stories fit the visits others may have seen; the role card gives the
advice. Engine: "No living player holds the Sentinel, so if you claim it, no one can counter-claim you
truthfully." Card: "Plan your cover before you need it. Your worked-out lines list the roles you can
claim without contradicting the public record." One further line was tried and dropped: a summary of
what each rival claimant had said moved one case's votes toward the named player in a small screen, the
kind of steering the engine must not do.

### What changed in replayed decisions

Each screen replays a **frozen turn**, a recorded turn rebuilt from the saved game and answered again
several times, with the engine's lines and without them. The first row uses the game's live **output
mode**, in which the answer's schema is sent to the model as text rather than enforced by the provider
([chapter 6](../../cost_and_latency/cost_and_latency_codex.md) tells why that mode was adopted).

| Failure replayed | With the engine's lines, against without | What limits the reading |
|---|---|---|
| The healer's turn (live output mode) | Its **read** of player_7, the one-line assessment of another player each turn asks for, named the Chanteuse in 8 of 10 samples against 2 of 10; it spoke in 7 against 3 | "Without" restores the game's original night record, whose "you learned nothing tonight" works against the deduction, so this compares the engine against that record, not one line in isolation. One turn, 10 samples a setting. An earlier replay of the same turn in the enforced output mode found the line taken up every time and no sample speaking; the Level 3 tells it. |
| A Sentinel misreading its own watch | Report lines relying on a false rule fell from 6 of 40 to 2 of 40; replies to such reports stayed at 17 of 55 | 19 frozen turns, 5 samples each. The replies answer the recorded transcript, which already holds the Sentinel's wrong denial, so the replay cannot show what would follow a corrected report; the downstream effect is unresolved. |
| Evil seats pressed to explain a visit | Claims 44 against 36; denials 0 against 4 | 41 pressured turns, two samples each. The arms were labelled by different judges, so the counts are exploratory. |

In each case the lines changed what the first speaker did. Where that help is worth having is bounded
by the same healer turn run without the engine: the game's model at its live setting read player_7 as
the Chanteuse in 2 of 10 samples; at a high thinking setting it reached 9 of 10 on its own, with a turn
taking 17.4 seconds against 6.3; two larger models reached 9 and 10 of 10. The engine is a substitute for
that slower or costlier configuration on a step of this kind, not a general gain. The only whole-game
comparison bundled the engine's cover facts with revised evil cards: the wolves won 3 of 8
paired games against none before, and the two changes cannot be separated
([chapter 1](../../game_design_orchestration/evidence_design/evidence_design.md) tells those games).

*Explore: The roleblocked healer →*
<!-- Level 3, planned at deduction_engine/roleblocked_healer.md: the enforced-mode uptake result with its
date and mode; the carried-note 2×2 (9 of 20 against 3 of 20); the placement screens; the investigator's
vote case and the moderator closing line; the 2026-10-30 model and thinking comparison in full with its
subagent-harness caveat. Drafted after this page is reviewed. -->

### Scope and remaining questions

The engine covers the standard twelve roles and the use limits the rules state; a game outside that
set gets no lines at all, because a second blocking role, for instance, would make "only the Chanteuse
could roleblock" false. Its coverage of missed deductions rests on the four acceptance cases, and one
level, the explanations for a claim the morning leaves open, has never produced a line in 278 recorded
turns. No whole-game comparison with the engine on and off has been run for the town, and no error rate
after the engine has been measured. The engine, solver included, was written by an AI coding assistant;
my part was the requirement, the grading rule, the acceptance cases from real failures and the
experiments. How its conclusions are checked is on
[Evaluation's code-checks page](../../evaluation/code_checks/code_checks.md); what stopped the healer
acting on them is the Level 3 above.

<!-- Sources for the page copy (checked 2026-10-31). Numbers lifted as they stand; none re-derived.

§1. Failure class and the choice: deduction/report.md §1 (the cause table's third row; "bounded
intervention"). Cost, not necessity: report.md 2026-10-30 note and experiment_log.md §8 Result 2 (Haiku
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
blockable, visits under own name, reads Suspicious; the table checked against the engine, §4 trait
check). Solver, A/B/C illustration ("assuming one copy of each role"), the four kinds of rule,
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

§4. The question ("did the advice use hidden information?") and the Alice/Bob table: content_plan.md
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
roles/report.md decision 10). The dropped counter-claimant line: report.md §5 ("did not improve pooled
voting in a small screen and moved one target game's votes the wrong way"); map block 54 (12/16 →
12/17 pooled, 7/4 → 5/7 in its own case).

§5. Frozen turn / replay: glossed per the outline. Output mode: experiment_log.md §8 Setup
(json_mode = schema sent as text, live for Haiku since 2026-10-14; json_schema = enforced). Row 1:
experiment_log.md §8 Result 1 live row (8/10 read, 7/10 spoke) and Result 2 Haiku low (2/10, 3/10);
scope note in Result 2 (engine on against the original night record; not one line isolated); one turn,
10 samples a setting. The enforced-mode result (§4: 10/10 notes, 0/10 spoke; 2026-10-16) named with its
mode and sent to the Level 3. Row 2: gameplay/data/visit_wording_ab/README.md "Arm C" (mech report 6/40
→ 2/40; mech react 17/55 → 17/55; 19 cases, n=5; arm A re-judged with arm C's judges; "a replay of those
turns cannot show the downstream effect"). Row 3: roles/report.md decision 11 table ("Card, covers off"
36 claims / 4 denials against "Covers, fixed" 44 / 0; 41 turns, two samples each; the fixed arm judged
by a separate set of judges); report.md §5. Model/thinking limits: experiment_log.md §8 Result 2 (Haiku
low 2/10; Haiku high 9/10, 17.4 s against 6.3 s; Sonnet 9/10; Opus 10/10; all engine off, game path,
live mode). Bundled games: roles/report.md "The games: a bundle, eight pairs" (wolves 3 against 0 of 8;
cards, two engine changes and everything committed between the builds; "cannot say how much came from
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
