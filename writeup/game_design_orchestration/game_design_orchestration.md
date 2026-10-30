# Game design and orchestration chapter (draft)

Level 1 page copy. The chapter's structure is in [`content_plan.md`](content_plan.md); each Level 2 page
has its own folder here, with its Level 3 pages beside it; exhibits and where they come from are in
[`exhibits/source_map.md`](exhibits/source_map.md). All five Level 2 pages and two Level 3 investigations are drafted; their editorial revision is recorded in [editorial_notes.md](editorial_notes.md).
This revision integrates the Level 2 links into the chapter narrative; the content plan records
this structure (updated 2026-10-26).

---

## Level 1: the chapter page

### Game design and orchestration: making ten agents play together

The Ninth Express is a variant of Mafia played with AI agents. It is a social deduction game where
players have secret roles, competing objectives and incomplete information.

In a typical Mafia game, the majority faction (town) must identify and eliminate a hidden minority
faction (wolves). The wolves know one another's identities and try to pass as townspeople. Players
discuss their suspicions, make claims about what they know and vote to eliminate someone. At night,
players with special abilities act privately.

My version takes inspiration from Town of Salem, extending this format with additional factions and
role-specific abilities: ten players on four sides, shown below with what each side wants and who
knows what. Some roles learn things at night and choose whether to reveal them; others must decide whom
to protect or shoot on uncertain information.

![Ten players on four sides, what is public and what is private, and one day and night](exhibits/game_at_a_glance.svg)

*Players share the same game but not the same information. Public claims, private evidence and hidden
actions shape later decisions.*

#### Giving players evidence worth debating

A social deduction game is only as good as its arguments. The town needs evidence strong enough to
challenge a story, and evil needs room to tell one. My first, nine-seat version had neither. One
Investigator could identify a player's exact role, and the wolves and the serial killer never claimed a
role at all: their only answer to a real result was to call it fabricated. That gave the town no rival
story to weigh, and the rest of the talk turned to tone and timing.

So I redesigned both sides. Three town roles now each see a different part of the night, true but
incomplete: whether a player reads as suspicious, who visited a player, and where a player went. The
game never reports a false result, so a lie has to be spoken: evil players now plan a cover role with
a story for each night, and claim it rather than deny.

*Explore: [Designing evidence worth debating](evidence_design/evidence_design.md) →*

Those rules set the engineering problem for the rest of this chapter: ten separately called language
models must play one game, each with different information, and every decision must stay within the
rules.

#### Keeping each player's information separate

For social deduction to work, players must hold different information: their own role and results,
anything their faction shares, and public claims that may be true or false.

In a human game, the moderator controls this separation: role cards are dealt privately, night results
are given privately, and announcements reach the whole table. Online games such as Town of Salem do
the same through each player's screen.

With agents, there is no table and no moderator. One program holds everyone's roles, actions and
results, because it needs them to apply the rules. Each agent, by contrast, knows only what is in the
input of its model call, so that input is the only place where the separation can hold or fail. The
shortcut would be to send every agent the whole game and tell it to ignore what its role should not
know. A model cannot unsee its input, though: anything in the prompt can shape its reply, so one private
result in the wrong prompt gives that player knowledge it could never have obtained in play.

So I use **context isolation**: controlling which information enters each agent's context. For every
turn I build that player's input from the full state, selecting only what it is entitled to, before the
prompt is written. A model can still lie about what it knows, but it is never given
what it should not have. After test games, I also check every input that was sent for a private record
that reached the wrong player.

![The full game state, the step that builds each player's input, and what an Investigator and a wolf each receive](exhibits/context_isolation.svg)

*Each model call receives a view built for its player, not the full game state.*

*Explore: [Agent information boundaries](../../evidence/agent_boundaries/report.md) →*

#### Giving players opportunities to discuss and respond

Once players have their information, they need chances to share evidence, challenge accusations and
respond to one another, without a few outspoken agents crowding out the rest or the discussion running
on indefinitely.

In a human game, the day runs on a timer and anyone can speak whenever they like; online games such as
Town of Salem do the same in a shared chat. That works because people listen all the time: they notice
when a response is expected and jump in when they are accused.

A model can do none of that. It exists only while it is being called: it reads one fixed snapshot of
the conversation, takes a few seconds to answer, then stops until it is called again. So "speak
whenever you want" has to be imitated, and each obvious way of doing it fails:

| Approach | Why it is tempting | Why it fails |
|---|---|---|
| **Simultaneous rounds** | Simple, and the calls run in parallel | Players answer the same snapshot and talk past one another |
| **Ask everyone after every line** | Each agent says whether it wants to speak | Nine extra model calls for every line spoken |
| **A real-time countdown** | Like an online human game | Faster models get more chances to speak |
| **A fixed speaking order** | Everyone gets a turn | An accusation can sit unanswered while unrelated speeches continue |

My first design used simultaneous rounds, and on one day five of eight players opened with the same
question: "Does anyone have any initial thoughts…?" An accused player could answer only in the next
round, to everyone at once. Fair turns were not enough: when one player addresses another, the answer
has to come before the conversation moves on.

So I built a scheduler around replies. Each agent tags its line with whom it addresses and whether it
is questioning, accusing, defending or agreeing. A question or accusation leaves the named player
owing a reply, which goes ahead of every other turn: A accuses B, B answers, and later speakers hear
both. A player accused by several others answers them together. When nobody owes a reply, the floor
goes to players who have not yet spoken, so someone holding private evidence gets a chance to share it.

Stopping rules keep one argument from taking over the day. Repeated pressure on a player who has not
yet answered adds no extra turns, and exchanges between the same pair are capped. Discussion ends once
owed replies are answered and everyone has had a turn, under a cap of three lines per living player; if
the cap comes first, open questions get one last answer. Players accused by at least two others then
get a closing defence before the vote. **Code decides who speaks and when; the model decides what to
say.**

*Explore: [Orchestrating the conversation](conversation/conversation.md) →*

#### Running the game: coordinating phases and player decisions

A complete game has to track who is alive, which phase comes next and whether a side has won, and each
phase feeds the next: a vote may remove a player who would have acted that night, and the night decides
what players know the next morning. I organise this progression with **LangGraph**, a framework that
connects steps through shared state: the graph decides which step runs next, and the state records the
game's progress and each step's results.

The steps need two different execution patterns. A speaker has to see what was just said, so the
open discussion runs one turn at a time. Votes and night choices must be blind, so each player decides from
its own view of the same state, and those model calls run in parallel, which also cuts the waiting.

Running choices in parallel raises a second problem: night actions interact. A block can stop another
player's action, and a protection can stop an attack. If each choice took effect as soon as its model
replied, the outcome would depend on which call finished first. So the night waits for every choice,
and one resolution step applies the rules to all of them together.

![A day and a night, showing which steps run one at a time, which run all at once, and where the rules take over](exhibits/phase_execution.svg)

*The graph decides what runs and when; the rules decide what happens, whatever order the replies
arrive in.*

*Explore: [Multi-Agent Game Orchestration](day_and_night/day_and_night.md) →*

#### Structured Agent Execution

Every turn, whether a line of speech, a vote or a night action, follows the same path, shown below.
Two parts of it are design choices.

**A structured response, not tool calls.** The legal choices are known before the turn starts: a
Vigilante, for example, must pick an eligible target or decline to shoot. The agent has nothing to
discover, so instead of giving it tools to call, I ask for an answer in a fixed format that code can
read: the choice, with the agent's reasoning beside it.

**A check, and a way out.** A generated reply can still be malformed or name an ineligible target, so
every reply is checked before it reaches the game. A failed reply is asked for again with the format
enforced; if that fails too, a legal fallback, such as passing or declining, takes its place. One bad
reply never leaves the game without a legal move.

![One turn: the player's input, the model's reply, the check, a retry with the format enforced or a legal fallback, then the hand-off to the game](exhibits/agent_turn.svg)

*A reply is checked before it affects the game. Votes and night choices take effect only when their
phase resolves.*

*Explore: [Structured Agent Execution](agent_turn/agent_turn.md) →*

#### Letting a human join the game

The same game can also let a person take one of the seats. They need the same information boundaries,
speaking opportunities and legal choices as an AI player, so the game should not need a second set of
rules for them.

What differs is how a decision arrives. A model replies within seconds; a human reads the game in a
browser, may take minutes to decide, disconnect or come back later. So the game has to wait for them
without losing its progress. I pause the game at the human's decision and save its progress in a
checkpoint. When the answer arrives, the game resumes and the answer goes through the same checks as a
model's reply, so humans and agents share one turn pipeline. If the human never comes back, the seat's
AI agent takes the turn.

Resuming had a catch. Because of how the game's steps are wired to keep each player's information
separate, the game resumes by repeating the whole paused step, not only the human's part. In my first
test with two humans, the AI voters were asked again and some changed votes they had already cast. Now
each finished AI turn is cached, and a repeated step reuses it. The cache is temporary: after a server
restart the game still resumes from its checkpoint, but those AI players decide again.

![A vote with one human player: the pause, the repeated step with and without the cache, and the two kinds of saved work](exhibits/human_resume.svg)

*The checkpoint makes the game resumable; the cache keeps a repeated step from changing finished AI
turns.*

*Explore: [Adding a human in the loop](human_in_the_loop/human_in_the_loop.md) →*

<!-- Authoring sources retained from the fuller draft (2026-10-26). Historical findings and
experiment figures are no longer part of Level 1; the references below remain for deeper-page drafting.
Sources:
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

<!-- Diagram-led revision (2026-10-27, adopted from a draft written beside the previous version). Cut in the reduction, and what now carries each:
Opening: the per-side objectives paragraph → game_at_a_glance (each side's goal; the role kinds). The
bold engineering question → one plain statement (no rhetorical question).
Section 1: the bullet list of what a player receives, and "wolves receive their faction's chat" →
context_isolation (GETS / NEVER GETS per seat). Kept in prose: the human-table contrast, why the full
state cannot be sent, where the boundary sits.
Section 2: the human-vs-agent table → its content is in the two paragraphs before it (the owner's "A
model can do none of that" wording restored). "Conversational causality" → the plain requirement. No
diagram here, so the scheduler's reasoning stays in prose, merged from nine paragraphs into two.
Section 3: the wolves' exception → phase_execution ("the exception: they agree first"); "a dedicated
resolution step… morning report" → the diagram's resolution and morning boxes. Kept in prose: why
discussion is sequential, why decisions are parallel, why the night waits.
Section 4: the turn's steps (input contents, retry, fallback, hand-off) → agent_turn. Kept in prose:
why a structured response rather than tools; why a check and a fallback.
Section 5: "LangGraph interrupts" → plain "pause", per the ruling that framework terms stay on Level 2;
the "Checkpoints and cached decisions" subsection → human_resume's lower half, with its one consequence
kept beside the cache sentence. Kept in prose: why the step repeats, the two-human test.

Diagram sources (2026-10-27). game_at_a_glance.svg: roles/role_sheet.md "The lineup" and "Win
logic"; discussion/report.md "A day today" (day 1: openings only); orchestration/report.md "The parent
graph" (win check after the vote and after the night). context_isolation.svg: agent_boundaries/report.md
§§1–3 (the checks run over the logged inputs after batch games and in unit tests, not as a live gate).
phase_execution.svg: orchestration/report.md "The day subgraph" (openings and closing defences in
parallel, discussion one turn at a time), "The nights" (the pack chats one at a time, in parallel with
each solo role's node), NIGHT_RESOLUTION after every branch. agent_turn.svg: agent_turn.md "Retry,
then supply a legal fallback" (the retry enforces the schema; the rescue model is left to Level 2).
human_resume.svg: human_in_the_loop.md "What survives a pause or a restart?" and the first two-human
test; no framework terms, no dates. -->
