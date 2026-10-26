# Game design and orchestration chapter (draft)

Level 1 page copy. The chapter's structure is in [`content_plan.md`](content_plan.md); each Level 2 page
has its own folder here, with its Level 3 pages beside it; exhibits and where they come from are in
[`exhibits/source_map.md`](exhibits/source_map.md). Only page 5 is drafted; the other four summaries
link to planned paths. Lines marked **Exhibit** and **Link** are specs for the page, not page copy.

---

## Level 1: the chapter page

### Game design and orchestration: making ten agents play together

The Ninth Express is a variant of the Mafia-Style game played with AI agents. It is a social deduction game where players have secret roles and competing objectives. In a typical game of Mafia, there is usually two factions. A majority faction e.g. town that has the numbers but does not know the true role of other players. A minority faction whom members knows one another and try to pass as townspeople. A faction win by eliminating the other, usually through 2 basic mechanisms. A Day phase where players from majority faction tries to reason and deduce who is from the other faction and vote them out. And a night phase where the minority faction gets to remove someone from the majority faction. 

My version takes inspiration from an advanced variant known as Town of Salem which includes additional features beyond the basic mafia game, such as giving unique skills to each players and adding more factions.

The game has Ten players from 4 different factions: six town roles, two wolves, a lone killer and a neutral. The lineup is public; who holds each
role is secret. Each side has its own win condition to fulfil, either being the only faction remaining or satisfy their unique win conditions in the case of neutrals.
Three town roles gather different pieces of evidence to facilitate deductions and discussion for voting out a evil in the day.

The engine reports truthful results. Players can lie about what those results were, or which role
they hold. That distinction creates the central design problem: give players enough evidence to reason
with while leaving room for competing explanations.

![The day-and-night cycle: discussion and a vote, private night choices, resolution, then the morning report](exhibits/day_night_loop.svg)

*Day 1 has openings only. Later days include a vote, which may eliminate a player. Night actions produce
private results and a public morning report.*

Human players organise much of a Werewolf conversation themselves. With ten agents, I had to make
those arrangements explicit: who speaks next, what each seat knows, which choices are independent,
and when an action changes the game. Adding a human also means being able to pause and resume.

The design rule is simple: **code applies the rules and updates game state; models interpret the
information and choose actions.** The pages below explain how I turned the game's requirements into
that division of work. The current game has ten seats; evidence from the earlier nine-seat version is
labelled where it appears.


| What the game requires                        | What the system provides                             | Where                                                                   |
| --------------------------------------------- | ---------------------------------------------------- | ----------------------------------------------------------------------- |
| Hidden roles and private results              | Separate information for each seat                   | Information boundaries (chapter 2)                                      |
| Evidence players can weigh and contest        | Partial, truthful results; room to make false claims | [Designing evidence worth debating](evidence_design/evidence_design.md) |
| Discussion that responds to earlier speech    | Turn scheduling and updated context                  | [Orchestrating the conversation](conversation/conversation.md)          |
| Independent votes and night choices           | Collect decisions before resolving their effects     | [Executing a day and night](day_and_night/day_and_night.md)             |
| Actions restricted by role and remaining uses | Validation and rule-based updates                    | [Turning an answer into a legal action](legal_action/legal_action.md)   |
| A human who may take time to answer           | Checkpointed progress and controlled resume          | [Adding a human in the loop](human_in_the_loop/human_in_the_loop.md)    |

<!-- **Link (planned):** "Information boundaries (chapter 2)" → the chapter 2 page, once built. -->

#### Designing evidence worth debating

An exact result can settle an accusation before there is much to discuss. I replaced the earlier
game's single exact information role with three roles that each reveal part of the truth. Evil players
also needed instructions that helped them contest accusations through claims, rather than simply deny
them.

When I replayed 41 recorded turns where an evil player was under suspicion on Claude Haiku 5.5,
changing only its role card, claims rose from 13 to 33 among 82 samples per version. One blind model
judge assessed each response. This supports the card change on those recorded situations; discussion
quality was not measured against the nine-seat game, and balance was tuned separately on Flash-Lite.

**Link:** Explore the cast, the role cards and the limits of the balance checks →
[Designing evidence worth debating](evidence_design/evidence_design.md).

#### Orchestrating the conversation

A useful discussion needs replies as well as speeches. I use tags in each speaker's output to identify
questions and accusations, then offer turns to players who owe an answer before moving through those
who have not spoken.

Silence also needed diagnosis. In 28 nine-seat Flash-Lite games, 367 of 517 passes came from a model
filter suppressing generated lines. I changed the design so players speak by default, with a later
check for repetition. On 65 lines from ten-seat Haiku games, that check withheld 10 of 29 restatements
and none of 36 lines judged worthwhile. Those labels came from one model reader per line and have not
been checked against human labels.

**Link:** Explore turn order, the sources of silence and the repetition check →
[Orchestrating the conversation](conversation/conversation.md).

#### Executing a day and night

Votes and night choices can be collected independently from the same game state. Conversation needs
sequential turns so speakers can respond to what was just said. I expressed that distinction in
LangGraph: parallel decision steps followed by resolution, and sequential steps for discussion.

When I tried parallel open discussion in one nine-seat test game on 2026-10-07, speakers made
overlapping points: seven lines were generated to keep two. I reverted to one speaker at a time.
That experience informed the graph's structure; it was not a comparison of orchestration frameworks.

**Link:** Explore how the game cycle becomes graph execution →
[Executing a day and night](day_and_night/day_and_night.md).

#### Turning an answer into a legal action

A model chooses within rules enforced by code. Each turn asks for a structured answer with legal
targets, then validates the reply and handles failures. I chose this over a tool loop because the
available actions are few and fixed; that was a design judgement, not a measured performance advantage.

The output contract also affected cost. On Claude Haiku 5.5, varying provider-enforced schemas prevented
seats from sharing the same cached prompt prefix. I moved the schema into text after the shared input
and validated replies in code. In a trial on 2026-10-13, one of 412 Haiku replies failed the format;
paired-game checks showed substantially more prompt-cache reuse. The trade-off was taking
responsibility for validation in exchange for better cache sharing.

**Link:** Explore the output contract, validation and fallbacks →
[Turning an answer into a legal action](legal_action/legal_action.md).

#### Adding a human in the loop

A human answer passes through the same validation as an AI answer, but it may arrive minutes later.
I use checkpoints to save the game while it waits. Resuming initially re-ran AI votes, allowing players
to change their minds; caching completed AI turns preserved those answers while the entries remained
available. In one nine-seat verification game on 2026-08-19, 20 ballots replayed from cache.

The checkpoint survives a restart; the answer cache does not. Its key also needed to distinguish games:
a later incident was attributed to one game reusing another's failed opening. My fix added the game id,
with regression tests and a scripted before-and-after control checking isolation between games.

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
