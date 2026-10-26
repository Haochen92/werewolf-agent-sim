# Game design and orchestration chapter (draft)

Level 1 page copy. The chapter's structure is in [`content_plan.md`](content_plan.md); each Level 2 page
has its own folder here, with its Level 3 pages beside it; exhibits and where they come from are in
[`exhibits/source_map.md`](exhibits/source_map.md). Only page 5 is drafted; the other four summaries
link to planned paths. Lines marked **Exhibit** and **Link** are specs for the page, not page copy.

---

## Level 1: the chapter page

### Game design and orchestration: making ten agents play together

The Ninth Express is a variant of the Mafia-style game, played with AI agents. It is a social deduction game where players have secret roles and competing objectives. A typical game of Mafia has two factions. A majority faction, e.g. the town, has the numbers but does not know the true roles of the other players. A minority faction, e.g. the wolves, whose members know one another, tries to pass as townspeople. A faction wins by eliminating the other, usually through two basic mechanisms: a day phase, where players from the majority faction try to reason out who is from the other faction and vote them out, and a night phase, where the minority faction gets to remove someone from the majority faction.

My version takes inspiration from an advanced variant known as Town of Salem, which adds features beyond the basic Mafia game, such as giving each player a unique skill and adding more factions.

The game has ten players from four different factions: six town roles, two wolves, a lone killer and a neutral. The lineup is public; who holds each
role is secret. Each side has its own win condition to fulfil: the town wins by removing every evil player, the wolves once they equal or outnumber everyone else, the lone killer once at most one other player is left, and the neutral alongside another side.
Three town roles gather different pieces of evidence to feed the deductions and discussion behind voting out an evil player in the day.

The engine never lies: every result it reports is true. Players can lie, about their results or about
which role they hold. So the design problem is to give players enough true evidence to reason with,
while leaving room for competing stories.

![The day-and-night cycle: discussion and a vote, private night choices, resolution, then the morning report](exhibits/day_night_loop.svg)

*Day 1 has openings only. Later days include a vote, which may remove a player. Night actions produce
private results and a public morning report.*

Human players run much of a Werewolf conversation themselves: they take turns, answer each other and
sense when to stop. With ten AI agents, I had to make each of those arrangements explicit: who speaks
next, what each seat knows, which choices are made independently, and when an action changes the game.
A human at the table adds one more: the game must be able to pause and resume.

I split the work with one rule: **code applies the rules and updates the game's state; models
interpret what they see and choose actions.** The table lists what the game needs, what the system
provides for it, and where each is explained. The game today has ten seats; numbers from the earlier
nine-seat version say so.

| What the game requires | What the system provides | Where |
|---|---|---|
| Hidden roles and private results | Separate information for each seat | Information boundaries (chapter 2) |
| Evidence players can weigh and contest | Partial, truthful results; room to make false claims | [Designing evidence worth debating](evidence_design/evidence_design.md) |
| Discussion that responds to earlier speech | Turn scheduling and updated context | [Orchestrating the conversation](conversation/conversation.md) |
| Independent votes and night choices | Collect every decision before resolving its effects | [Executing a day and night](day_and_night/day_and_night.md) |
| Actions restricted by role and remaining uses | Validation and rule-based updates | [Turning an answer into a legal action](legal_action/legal_action.md) |
| A human who may take time to answer | Checkpointed progress and a controlled resume | [Adding a human in the loop](human_in_the_loop/human_in_the_loop.md) |

<!-- **Link (planned):** "Information boundaries (chapter 2)" → the chapter 2 page, once built. -->

#### Designing evidence worth debating

An exact result can settle an accusation before there is much to discuss. The earlier nine-seat game
had one role with exact results. I replaced it with three roles that each see part of the truth, a
narrowed Investigator among them. Evil players needed help too: their instructions now push them to
answer an accusation with a claim of their own, instead of a flat denial.

When I replayed 41 recorded turns where an evil player was under suspicion, on Claude Haiku 5.5,
changing only its role card, claims rose from 13 to 33 (82 samples per version, one blind model judge
per response). That shows the card change works in those recorded situations. I did not measure
whether discussion got better than in the nine-seat game, and I tuned the balance between the sides
separately, on Flash-Lite.

**Link:** Explore the cast, the role cards and the limits of the balance checks →
[Designing evidence worth debating](evidence_design/evidence_design.md).

#### Orchestrating the conversation

A good discussion needs replies, not just speeches. Each AI player tags its own line with whom it
questions or accuses. I use those tags to pick the next speaker: anyone who owes an answer goes first,
then the floor goes round the players who have not spoken.

Silence needed a diagnosis too. In 28 nine-seat Flash-Lite games, 367 of 517 passes were lines a model
filter had held back, not players choosing to stay quiet. So I made speaking the default, with a later
check that only holds back repetition. On 65 lines from ten-seat Haiku games, it held back 10 of 29
restatements and none of 36 lines judged worthwhile. One model judged each line, and no person has
checked those labels yet.

**Link:** Explore turn order, the sources of silence and the repetition check →
[Orchestrating the conversation](conversation/conversation.md).

#### Executing a day and night

Some choices happen at the same time, e.g. votes and night actions: every player decides from the same
state, and nothing takes effect until all the choices are in. Conversation is the opposite: each
speaker needs to hear the last line before answering. I built the game in LangGraph around that
difference: parallel steps for decisions, followed by one step that resolves them, and sequential
steps for discussion.

When I tried open discussion in parallel, in one nine-seat test game on 2026-10-07, the speakers made
overlapping points: seven lines were generated to keep two. I went back to one speaker at a time. That
game shaped the design; I did not compare other orchestration frameworks.

**Link:** Explore how the game cycle becomes graph execution →
[Executing a day and night](day_and_night/day_and_night.md).

#### Turning an answer into a legal action

Models choose; code enforces the rules. Each turn asks the model one question with a fixed answer
format that lists only the legal targets, then checks the reply and falls back to a legal move if it
fails. I chose this over letting the model call tools because the possible actions are few and fixed;
that was my judgement, not something I measured.

The answer format also affected cost. On Claude Haiku 5.5, a format enforced by the provider counts as
the start of the input, so seats with different legal targets could not share the provider's prompt
cache. I moved the format into plain text after the shared part and check replies in my own code. In
a trial on 2026-10-13, one of 412 Haiku replies broke the format, and in paired games votes and night
actions went from never reading the cache to reading most of it. The price is that checking the
format is now my code's job.

**Link:** Explore the output contract, validation and fallbacks →
[Turning an answer into a legal action](legal_action/legal_action.md).

#### Adding a human in the loop

A human's answer goes through the same checks as an AI's, but it may arrive minutes later. While the
game waits, a checkpoint saves it. At first, resuming re-ran the AI players' votes and some changed
their minds; caching their finished turns kept the original answers, as long as the cache entries were
still there. In one nine-seat verification game on 2026-08-19, 20 ballots replayed from cache.

The checkpoint survives a restart; the cache does not. The cache key also had to tell games apart: in
one recorded case, a game reused another game's failed opening. My fix added the game id, checked by
regression tests and a scripted before-and-after control.

**Link:** Explore pausing, resuming and hosting a human's game →
[Adding a human in the loop](human_in_the_loop/human_in_the_loop.md).

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
