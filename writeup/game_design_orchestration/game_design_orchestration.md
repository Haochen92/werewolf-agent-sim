# Game design and orchestration chapter (draft)

Level 1 page copy. The chapter's structure is in [`content_plan.md`](content_plan.md); each Level 2 page
has its own folder here, with its Level 3 pages beside it; exhibits and where they come from are in
[`exhibits/source_map.md`](exhibits/source_map.md). Only page 5 is drafted; the other four summaries
link to planned paths. Lines marked **Exhibit** and **Link** are specs for the page, not page copy.

---

## Level 1: the chapter page

### Game design and orchestration: making ten agents play together

Werewolf, a variant of the party game Mafia, is a game of hidden roles. Roles are dealt in secret, and
the sides want different things. The town is the majority but must infer whom to trust
from what people say and how they vote. The wolves know each other, coordinate privately at night and
pass as ordinary townspeople by day. Public discussion ending in a vote alternates with private
actions at night.

This version takes Town of Salem as its stated inspiration, with the roles renamed for a 1920s
setting. The ten seats belong to four sides: six town roles, two wolves, a lone killer and a neutral.
Eight seats are dealt every game and two are drawn from pairs of roles; the lineup is public,
but not who holds which role. Most roles act at night, and the town's three information roles each
learn a partial fact: whether a player reads as suspicious, who visited a player, or where a player
went. The lone killer and the neutral bring objectives of their own. Each side has its own win
condition, and the neutral can win alongside another side.

The engine applies every mechanic truthfully and never reports a false result. What players say about
their roles and results can be anything, so evil (the wolves and the lone killer) contests the town
through claims. The game is built
to produce partial evidence and competing explanations. The ten-seat game has run since 2026-10-09;
numbers from the earlier nine-seat game say so.

**Exhibit (diagram).** The day-and-night loop: day (discussion, then a vote that removes one player) →
night (private actions, resolved together) → morning report → next day, with "a side meets its win
condition" as the exit. No graph nodes. Spec in `exhibits/source_map.md`, L1-loop.

Human players manage much of a Werewolf game's conversation themselves. When every player is a model
call, the system must decide explicitly who receives which information, who gets a turn, which choices
are made independently, and when those choices become game outcomes. A human at the same table adds
one more requirement: the game must be able to wait.

I built the engine on one rule: code applies the rules and changes the game's state; models interpret
information and choose actions.

Each requirement below is developed on one page of this chapter, except private information, which
has a chapter of its own.

| What the game requires | What the system must provide | Where |
|---|---|---|
| Hidden roles and private results | Separate information for each seat | Information boundaries (chapter 2) |
| Evidence that players can weigh and evil can contest | Roles that give partial, truthful evidence; claims as the only place to lie | [Designing evidence worth debating](evidence_design/evidence_design.md) |
| Discussion that responds to earlier speech | Turn scheduling and updated conversational context | [Orchestrating the conversation](conversation/conversation.md) |
| Votes and night choices made independently | Independent decisions, then collection, then one resolution | [Executing a day and night](day_and_night/day_and_night.md) |
| Actions restricted by role and remaining uses | Validation and rule-based state updates | [Turning an answer into a legal action](legal_action/legal_action.md) |
| A human who may take time to answer | A pause, durable state and a controlled resume | [Pausing the game for a human](human_seat/human_seat.md) |

<!-- **Link (planned):** "Information boundaries (chapter 2)" → the chapter 2 page, once built. -->

#### Designing evidence worth debating

Players need evidence to weigh, and evil a way to contest it. In 28 nine-seat games on Gemini 3.5
Flash-Lite, the Investigator, the one role with exact results, claimed in 24, and no evil player ever
claimed a role. I replaced that one exact source with three roles that each see part of the truth, a
narrowed Investigator among them, and kept the engine truthful, so a lie has to be a claim.

Evil still denied rather than claimed. Replaying 41 recorded turns where an evil player was under
suspicion, on Claude Haiku 5.5, with only its role card (its instructions) changed, claims rose from
13 to 33 and denials fell from 21 to 3 (82 samples per version, one blind model judge
per line). Balance
was tuned on Flash-Lite, never on Haiku, and discussion quality was not measured against the
nine-seat game.

**Link:** Explore the cast, the evil contest and what the balance checks established →
[Level 2](evidence_design/evidence_design.md).

#### Orchestrating the conversation

Ten players share one day, so code decides who speaks next and when the talk stops. I compute the turn
order from tags each speaker puts on its own line, naming whom it questions or accuses: whoever owes an
answer speaks next, otherwise the floor goes round the unheard.

Silence had three sources (no turn offered, a filter holding the line, a choice to pass), and the
largest was invisible: in 28 nine-seat games on Flash-Lite, 367 of 517 passes were lines a model
judge had held back. Players now speak by default, and an echo gate after
the line holds repetition: on 65 lines of open discussion from ten-seat Haiku games it held 10 of 29
restatements and none of 36 worthwhile lines, one model reader per line, unchecked against a person.

**Link:** Explore turn order, silence and the echo gate → [Level 2](conversation/conversation.md).

#### Executing a day and night

Votes and night choices are made independently, and every one must be in before the vote or the
night resolves; conversation must happen in turn, because each line answers the last. I run the game
on LangGraph, a framework that executes a program as a graph of steps with shared state. The graph's
shape follows that flow, not the roles: parallel steps where every seat answers the same snapshot,
then one step that collects and resolves them; sequential steps where seats converse.

Open discussion run in parallel, tried in a nine-seat test game (2026-10-07), produced overlapping
points: seven lines generated to keep two. It was reverted to one speaker at a time. No alternative
orchestration design was compared; the evidence is tests and incidents found and fixed.

**Link:** Explore how the day-and-night cycle becomes graph execution →
[Level 2](day_and_night/day_and_night.md).

#### Turning an answer into a legal action

A role may act only on certain players, and only while uses remain: the Vigilante has two bullets.
Each turn, code asks the model one question with a fixed answer format (a schema) listing only legal
targets, and every path ends in a legal move. I chose this over a tool loop because the actions are
few and fixed (reasoned, not measured).

On Claude Haiku 5.5, a provider-enforced schema counts as the start of the input, so seats with
different targets could not share the provider's prompt cache, which reuses an identical start. The
schema is now text after the shared part, checked in code: in a 2026-10-13 trial, unenforced replies
failed once in 412 Haiku calls, and in paired games votes and night actions went from never reading
the cache to reading most of it.

**Link:** Explore the output contract, validation and fallbacks → [Level 2](legal_action/legal_action.md).

#### Pausing the game for a human

A person may take minutes to answer, close the tab or come back after a server restart. A human's turn
is a pause in the same pipeline as a model's: the game saves its state and stops, and the answer
resumes it, validated like a model's reply.

Resuming re-ran the step's AI votes, and some voters changed their minds. I cached the AI turns, with
an uncached path for humans; in one nine-seat verification game (2026-08-19), 20 ballots replayed from
cache. The key later proved too wide: it lacked the game id, and one game on the public site replayed
another's failed turn. The fix, deployed 2026-10-26, adds the game id; regression tests check it, and a
before-and-after control on two deals went from five turns served across games to none.

**Link:** Explore the pause, the cache and how the engine runs inside the web server →
[Level 2](human_seat/human_seat.md).

<!-- Authoring sources for the Level 1 copy (drafted 2026-10-26):
The game: evidence/gameplay/roles/role_sheet.md, "Renames" (1920s setting, away from Town of Salem),
"The lineup" (10 seats, 12 roles, 6 town / 2 wolves / 1 lone killer / 1 neutral, 8 fixed, 2 drawn),
"Win logic" (compressed per the plan's victory rule); roles/report.md "The cast today" (lineup public,
the three information roles' results) and "How each side wins". Werewolf/Mafia and the Town of Salem
inspiration: general knowledge, uncited (content plan). Ten-seat since 2026-10-09: gameplay/report.md
"Version and scope". Engine truthful / claims anything: roles/report.md decisions 3 and 5; map 133.
Transition: content plan "Level 1 presentation" item 2 (the reviewer's wording, lightly adapted).
Design rule: map block 102; orchestration/report.md "The problem".
Summary 1: map 131 (24 of 28; no evil claim; gemini-3.5-flash-lite, 2026-09-17; memory off), 132-133,
137 (41 pressured turns; Haiku 5.5; 82 samples per arm; claims 13 → 33, denials 21 → 3; four blind
Sonnet subagents, one per line), 135 and 139 (balance on Flash-Lite, held, never on Haiku); hub
problem 2 (discussion quality not measured against nine seats).
Summary 2: map 119-120 (tags, debts, sweeps), 126 (367 of 517; 28 nine-seat games; the three sources),
128 (65 lines; 10 of 29, 0 of 36; 16 ten-seat Haiku games; one reader per line; hardening task 1b).
Model for the 28 games: roles/report.md "The problem" names gemini-3.5-flash-lite for this census.
Summary 3: map 108-109; discussion/report.md decision 7 (seven lines to keep two, first game,
2026-10-07, overlapping points); the October test games were nine-seat (map 127); map 116 / orchestration
report "Version and evidence" (no alternative design compared).
Summary 4: map 103-104; turn_prompt/report.md "Why the schema is not enforced on Haiku"; caching
experiment_log.md §12 (2026-10-13: 1 in 412 Haiku calls) and §13/§15 (paired games, cache reads). Tool
loop: orchestration/report.md decision 1 (owner's reasoning, not measured).
Summary 5: map 105-106, 115; orchestration/report.md decisions 11-12 and "What is not established"
(control: same two deals, scripted model, pre-fix 5 of the second game's openings from the first's
cache, fixed code none); deploy_log.md 2026-10-26 (`2ecec0cc`). No statement about served games since.
Chapter card tags (not page copy): multi-agent orchestration, human-in-the-loop systems, structured
outputs and validation. -->
