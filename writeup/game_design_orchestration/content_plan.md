# Game design and orchestration: portfolio content plan

Editorial assessment, 2026-10-26. This maps the gameplay and orchestration evidence onto portfolio pages.
It is not page copy, and it does not claim that the pages exist. The model it follows is
[`../evaluation/content_plan.md`](../evaluation/content_plan.md). The starting arrangement is chapter 1 of
[`../structure_proposal.md`](../structure_proposal.md) (v2). The evidence is the map's blocks 102–139
([`../map.md`](../map.md)), checked against the reports they cite. This pass keeps the five Level 2
pages and the one Level 3 page, and moves four items between pages.

**Revised 2026-10-26 after an external review, with the owner's agreement.** The chapter now runs
game → requirements → design decisions → evidence. The chapter page opens with the game, then turns
on one question: what changes when the players are model calls? A table of the game's requirements
answers it, and each Level 2 page develops one or more rows. Each page opens from its gameplay
requirement before any framework detail. The three question subheadings and the compact who-decides
table on Level 1 are dropped; the who-decides table moves, in full, to page 4.

## Reading structure

**Level 1 is the chapter page: "Game design and orchestration: making ten agents play together".**
It opens with a short explanation of the game, before any graph. It then states what the game requires
of a system whose players are model calls, gives the chapter's one design rule and summarises each
Level 2 subject. The project case-study page sits above it.

**Level 2 holds complete explanations of substantial subjects.** Each page has its own opening,
subsections, featured story and exhibits. A visitor arriving directly should understand the question,
the design, what was learned and the limits without reading the chapter first.

**Level 3 is optional, curated depth.** It develops one investigation or mechanism that would
interrupt its Level 2 parent, and it adds a method, analysis or walkthrough. The parent keeps the
finding and its essential caveats.

Repository links are provenance. A reader can follow every selected explanation without leaving the
portfolio.

## Recommendation: five Level 2 pages, each developing the game's requirements

The proposal's five subjects survive the test against the blocks. Each holds several connected
decisions with their own evidence, and none could be folded into another without losing its reader
question. On the Level 1 page they appear as five summaries, in the order of the requirements table
(see "Level 1 presentation"). No question subheadings, grouping page or navigation item sit between
them.

| Level 2 page | The game-level question it opens with | Why it deserves a page | Blocks |
|---|---|---|---|
| **1. Designing evidence worth debating** | What must the roles give players, so that there is something to argue about and evil can contest it? | Diagnoses thin talk from one exact source that nobody contested. Then a cast design (partial observers; an engine that never reports a false result) and an evil contest through claims, with the chapter's strongest controlled result | 131–139 |
| **2. Orchestrating the conversation** | Ten players share one day: who speaks, what gets said aloud, and when does the talk stop? | Turn order computed by code from the speakers' own tags. Silence traced to three sources. A publication filter moved after the line on calibration evidence. Each decision has its own failure and fix | 117–130 |
| **3. Executing a day and night** | Conversation is in turn, but votes and night choices are made independently and must all be collected before anything resolves. How does the familiar cycle become execution? | The graph's shape (subgraph versus named node), parallel versus sequential steps, state fold-back, shared records and the step budget. These are the multi-agent orchestration decisions themselves | 102, 107–110, 112–114, 116 |
| **4. One agent turn, from input to action** | A role may act only on certain players, and only while uses remain. How does a model's answer become a move code can apply? | The output contract: one structured question rather than a tool loop, legal targets in the schema, required fields, enforcement against caching, and a legal fallback on every path. The full who-decides table | 103–104 (with 97, 100, 147 cross-referenced) |
| **5. Adding a human in the loop** | A human may take minutes to answer. How does the game wait, survive a restart and continue without changing what the AI players already did? | Interrupt and resume, the re-run of AI turns, the cache and its uncached twin, the three things kept (checkpoint, node cache, prompt cache), and the async server host | 105–106, 111, 114–116, 165 |

**Why the arrangement holds.**
- **Pages 3 and 4 stay apart.** They answer different questions: how ten calls become one game, and
  how a model's answer becomes something code can trust. Merging them would bury the structured-output
  decisions under graph topology.
- **Pages 2 and 3 meet at one decision**, parallel against sequential steps. Page 3 owns the execution
  pattern: `Send`, the barrier, and the round numbered at the collecting node. Page 2 owns the
  conversational evidence: near-identical lines from parallel talk.
- **Page 5 is its own subject.** The orchestration topic opens with the cache bug (block 115), and the
  topic-level hook "What does it take to seat a human at a table of AI agents?" belongs here.

**Changes from the starting arrangement.**
1. **The game's requirements table becomes the chapter page's organising thread.** "Who decides what"
   (block 103's exhibit) stays whole on page 4, where the split between code and model is the subject.
   Level 1 states the rule in one sentence; a second, overlapping table there would repeat the
   requirements table.
2. **The async host (block 111) goes on page 5, not page 3.** The graph runs identically in batch and
   CLI play. The thread-pool choice exists because a served game streams to people, and the 64-thread
   sizing came from a human wolf's prompt arriving late.
3. **The shared records (block 107) go on page 3.** They are the agents' shared state. Chapter 3 owns
   the fixes to the records (summary, ledger, labels). Page 3 states only the mechanism: one error
   reaches all ten seats.
4. **The voices (block 125) go on page 2 as a short closing subsection**, for now. They are in the
   discussion report but are not listed in the proposal's chapter outline. Whether the voice-rewrite
   study becomes a Level 3 page is open (see "Open questions").

The structure proposal's open question 1 (where balance sits) is settled here: **on page 1, as its own
subsection**, beside the paired games whose three wolf wins it qualifies. The Level 1 summary repeats the
untested-on-Haiku limit in its scope sentence.

**No "what went wrong" section on Level 1.** Each challenge stays on the page whose design caused it, as
that page's case study. Each Level 1 summary already carries one revealing result or failure, so a
separate list would repeat the summaries and turn the chapter into an overview followed by a bug
catalogue.

## Level 1 presentation

**Order.**
1. The game and its central tension, in plain words.
2. The turn: what changes when the players are model calls.
3. The design rule, in one sentence.
4. The requirements table.
5. The five summaries, in the table's order.

No graph diagram appears before the game is explained.

**1. The game, first (200–250 words in all, plus a small day-and-night loop figure).** One section covers
the traditional game, the inspiration and this version together. No separate history of Town of Salem:
it would invite a comparison the chapter does not need. The reader needs four things:
- **Hidden roles, different objectives.** Players do not know each other's roles, and the sides want
  different things.
- **The central tension.** The town is the majority and must infer whom to trust from talk and votes. The
  wolves know each other, coordinate privately at night and conceal themselves in public.
- **The cycle.** Public discussion and a vote by day alternate with private actions by night.
- **This version.** Name Town of Salem as the stated inspiration (the role sheet records the renames away
  from its role names, for a 1920s setting). Most roles have a night ability, and a lone killer and a
  neutral bring objectives of their own. The result is partial evidence and competing explanations.

Give the broad composition only: ten seats, four sides (town, two wolves, a lone killer, a neutral),
eight seats dealt every game and two drawn, the lineup public. The twelve-role table waits for page 1.
State that the ten-seat game has run since 2026-10-09, after a nine-seat version: many numbers below are
nine-seat, and each says so.

Two wording rules for this section:
- **Victory.** Never "the game ends when only one side is left". Each side has its own win condition
  (role sheet, "Win logic"): the town wins when no wolf and no lone killer remain; the wolves when the
  lone killer is gone and they equal or outnumber the rest; the lone killer when at most one other player
  is left. The neutrals win alongside another side: the Speculator with the side it picked, alive or dead,
  and the Fortune Teller's bets are scored beside the winner without ending the game. A day-12 backstop
  ends a game that runs long. The opening may compress this to "each side has its own win condition, and
  the neutrals can win alongside another side".
- **Engine results and claims are different things.** The engine applies every mechanic truthfully and
  never reports a false result. What players *say* about their roles and results can be anything. Evil
  contests the town through claims, not through false engine output. Never write "evil lies with true
  facts".

Town of Salem is designed for cooperation between factions; this record never observed it here (the
neutral coordinating opening claims was not seen). Describe what the roles make possible, not what the
agents did. The origin of Werewolf as a variant of Mafia, and Town of Salem's design aims, are general
knowledge, not this record: keep them short and uncited.

**2. The turn: what changes when the players are model calls.** One short paragraph, the chapter's
transition. In the reviewer's words, roughly: *human players manage much of a Werewolf game's
conversation themselves. With AI players, the system must explicitly decide who receives information,
who gets a turn, which choices happen independently, and when those choices become game outcomes.*

**3. The design rule (one sentence).** Code applies the rules and changes state; models interpret
information and choose actions (block 102). The full who-decides table is on page 4.

**4. The requirements table.** One table, the chapter's organising thread:

| What the game requires | What the system must provide | Where |
|---|---|---|
| Hidden roles and private results | Separate information for each seat | Chapter 2 (page 3 states only that the hand-built payload is the boundary) |
| Evidence that players can weigh and evil can contest | Roles that give partial, truthful evidence; claims as the only place to lie | Page 1 |
| Discussion that responds to earlier speech | Turn scheduling and updated conversational context | Page 2 |
| Votes and night choices made independently | Independent decisions, then collection, then one resolution | Page 3 |
| Actions restricted by role and remaining uses | Validation and rule-based state updates | Page 4 |
| A human who may take time to answer | A pause, durable state and a controlled resume | Page 5 |

The private-information row establishes the requirement only; chapter 2 owns its implementation.
"Votes made independently" is the accurate wording, not "secret votes": votes are cast at the same time
and tallied, whether or not the ballots are shown afterwards. "Remaining uses" is literal: the Vigilante
has two bullets, the Fortune Teller two self-bets, the Speculator one pick.

**5. Summaries (90–130 words each, two short paragraphs).** Each runs: what the game needs → the
engineering choice → one revealing result or failure, with its scope in the same sentence → what remains
uncertain. A descriptive link closes each.
1. *Designing evidence worth debating.*
   - **Question:** why was the nine-seat talk thin? The one exact source was never contested.
   - **Decision:** three partial observers instead of one exact investigator, and an engine that never
     reports a false result, so evil contests through claims.
   - **Finding:** card text alone moved evil from denying to claiming. Claims went from 13 to 33 and
     denials from 21 to 3, on 41 frozen pressured turns, Claude Haiku 5.5, 82 samples per arm, one blind
     model judge per line.
   - **Scope:** balance was tuned on Gemini 3.5 Flash-Lite and held, never run on Haiku. Discussion
     quality was not measured against the nine-seat game.
2. *Orchestrating the conversation.*
   - **Decision:** turn order is computed from the speakers' own tags.
   - **Lead finding:** silence had three sources, and the largest was invisible. 367 of 517 passes were
     a judge holding a line, in 28 nine-seat games on Flash-Lite.
   - **Consequence:** speech by default with an echo gate after the line. As shipped, the gate held 10
     of 29 restatements and none of 36 worthwhile lines. That is 65 open-floor lines, one model reader
     each.
3. *Executing a day and night.*
   - **Need first:** choices made independently must all be collected before the night or the vote
     resolves; conversation must happen in turn.
   - **Decision:** the graph's shape follows flow, not role. Parallel steps are for a shared snapshot,
     sequential steps for conversation.
   - **Lead example:** a parallel open floor generated seven lines to keep two and was reverted
     (2026-10-07). Alternative: the note-wipe bug as a caught-and-fixed episode.
4. *One agent turn, from input to action.*
   - **Decision:** one structured question per turn, with legal targets in the schema and a legal move
     at the end of every path.
   - **Finding:** on Haiku the schema is written as text and checked in code. Unenforced replies failed
     1 time in 412 Haiku calls, and votes went from never reading the provider's cache to reading most
     of it.
   - **Why not a tool loop:** the owner's reasoning, not measured. The one measured part: a forced tool
     call turns Haiku's thinking off.
5. *Adding a human in the loop.*
   - **Decision:** an interrupt in the same pipeline, so a human's answer takes the model's validation
     path.
   - **Finding:** a resume re-ran the step's AI votes, so the AI turns were cached and the human turns
     were not. The verification game replayed 20 ballots from cache (one nine-seat game, 2026-08-19).
   - **End on the cache key that crossed games:** fixed and deployed 2026-10-26, and checked with a before-and-after
     control. Link to Level 3.

**Hooks.** The map's "Can an AI lie well, and can the other AIs catch it?" is reworded for page 1 (or its
summary) as "Can an AI lie convincingly when every fact the game reports is true?" The record answers
that with the replay. It answers "can the other AIs catch it" only anecdotally: the town sided with the
false claimant in two of the three wolf wins. "What does it take to seat a human at a table of AI
agents?" opens page 5. Its other answers (the stage's wait on Haiku, the drafting
helpers) belong to chapters 6 and 8 and are linked, not retold.

**Public tags on the chapter card:** multi-agent orchestration, human-in-the-loop systems, structured
outputs and validation (`skills_inventory.md`). Supporting terms named on the pages where they are
explained: LangGraph, fan-out/fan-in, checkpointing, cache-key design, event-driven scheduling,
simulation environment design.

## Level 2 page briefs

Each brief moves to the top of its page file when the page is created. Every page opens from its
gameplay requirement (the game-level question in the recommendation table) before any framework detail.
Proposed files:

| # | Level 2 page · Level 3 pages |
|---|---|
| 1 | `evidence_design/evidence_design.md` |
| 2 | `conversation/conversation.md` |
| 3 | `day_and_night/day_and_night.md` |
| 4 | `agent_turn/agent_turn.md` |
| 5 | `human_in_the_loop/human_in_the_loop.md` · Level 3: `human_in_the_loop/cache_key.md` |

### 1. Designing evidence worth debating

**Reader question:** how do you design a hidden-role game so that model players have competing evidence
to weigh, and so that the evil side can actually contest it?

**Promise:** why these roles, what each reveals, how evil can contest claims, and what the balance checks
established on the model they were run on.

**Featured story:** the evil contest. Evil never claimed a role. The instructions went from permission
to a planned cover. On frozen turns the card text alone moved claims 13 → 33. In whole games the bundle
exposed the town's next problem: choosing between claimants.

**Subsections, in reading order:**
1. *Why the nine-seat talk was thin* (131). The one exact source went uncontested.
   - The Investigator claimed in 24 of 28 games.
   - Claim-based town accusations landed on evil 34 of 35 times.
   - No wolf or serial killer ever claimed.

   Scope: 28 games, Flash-Lite, memory off, labels from the playing model's own summaries. Present this
   as exploratory evidence and as the owner's reading.
2. *Three partial observers instead of one exact investigator* (132).
   - **Exhibit:** the role table (role, side, what it learns, uses). Optionally the owner's purpose table
     for the added roles, labelled as design intentions.
   - **Cost observed:** misreading what an ability observes became the commonest player error. Its fix
     (rules in the prompt) is chapter 3's (block 144); link it.
3. *The engine never reports a false result, so a lie has to be a claim* (133). Keep engine results
   and players' claims apart in every sentence: the mechanics are applied truthfully; a claim can be
   anything.
   - No framer and no decoy visit.
   - Engine-read records for dead town roles.
   - A fixed public lineup.
   - **Observed cost:** three of four contested claims in batch 4 went against the evil claimant.
4. *From permission to a planned cover* (134). Three steps, with the reason for writing facts rather
   than orders. **Exhibit:** the wolves' four-sentence instruction, quoted.
5. *Card text alone, on frozen turns* (137). The featured result.
   - **Exhibit:** the before-and-after table, plus the Illusionist's healer claim.
   - **What the judges could not see:** the claim that contradicts its sighting. Link chapter 3's
     covers line (block 54) without retelling it.
6. *In whole games: more claims, and a new problem* (138).
   - **Exhibit:** the four-row winners table.
   - **Scope, beside the table:** eight pairs; the bundle includes card and engine changes; the games
     diverge after the first different line. This is a direction, not a change in win probability.
   - Then the false-claimant case (the real Investigator voted out 6–2).
7. *Balance: what the checks established, on Flash-Lite* (135). The page promises what the checks
   established on that setup, never that the game is balanced.
   - **Exhibit:** the four-batch table.
   - **The tell:** the sigil was a one-step tell and was reworded.
   - **Scope:** 31 games on Flash-Lite; three evil wins show evil can win, not how often; never re-run
     on Haiku or on today's rules.
8. *How the rules are checked* (136). Describe what the tests check: the specified endings, a scripted
   game on the real graph, the seeded deal, three games read in full and two bugs found. Do not name who
   wrote the tests.
9. *What is not established* (139):
   - balance on the site's model;
   - balance per lineup;
   - the separate share of cards and engine;
   - discussion quality against the nine-seat game;
   - the cover-risk paragraph, checked by prompt tests only.

**Keep off this page:** batches 2 and 3 ran on uncommitted working trees. The stand-in model's turns in
batch 2 may stay as a limit.

**Cross-links:**
- covers line and claimable roles → chapter 3, deduction (blocks 54, 47);
- claim field and ledger → chapter 3 (blocks 69, 71);
- the opening round's original evil silence → page 2.

### 2. Orchestrating the conversation

**Reader question:** when every player is a model call, how does the engine decide who speaks, what gets
published and when the day ends, without the machinery itself becoming evidence the players argue
about?

**Promise:** openings, replies, speaking opportunities, publication filters and closing defences.
Silence is the featured investigation; the voices are a short final subsection.

**Featured story:** silence had three sources, and the largest was invisible (126).
- 367 of 517 passes came from a judge's hold.
- Three passes in a row ended day 1 in 28 of 28 games.
- On 8 of 96 voting days a player was never offered a turn.

Separating "never offered", "held" and "chose to pass" redirected the October rebuild. It ends in the
calibration that made speech the default and moved the filter after the line (128).

**Subsections:**
1. *What a good day needs, and what code decides* (117). The four needs. Discussion order and vote
   visibility are separate choices. **Exhibit:** the day's flow in two lines. Note that a voting day
   costs about 30 model calls (four nine-seat test games).
2. *Talk in sequence, vote at once* (118).
   - **Exhibit:** the five "Does anyone have any initial thoughts…" openers.
   - **Scope of the acceptance study:** 4 against 8 games, unpaired, `gemini-3.1-flash-lite`, read by
     the builder. The design enables avoiding repetition; it does not guarantee it.
3. *Turn order is computed, not chosen* (119, 120).
   - **Mechanism:** debts from tags, freshness, the pair cap and sweeps. The stateless scheduler is
     recomputed from the transcript.
   - **Tags:** the speaker tags its own line, in two dimensions.
   - **Exhibit:** the player_7 / player_9 exchange with its tags and the prompt line, noting that the
     reply defends but does not answer.
   - **Tag numbers, with their scopes:** string matching lost all 11 of its disagreements with the
     model; agreement with an unchecked judge was 145 of 183 messages, and 24 messages had a missed
     accusation (a message-level rate).
4. *Silence had three sources* (126). The featured story, as three counted lines.
5. *The opening round, and what it first got wrong* (122, 127).
   - **Why the round is restricted, sent at once and filtered by kind.**
   - **What it got wrong first:** the investigator-lynch chain, three of three claimants voted out
     (nine-seat, Flash-Lite, first test games).
   - **Ownership:** the night-1 lot's evidence is chapter 3's (block 146), so this page keeps the chain
     and the "not news" fix.
6. *Speak by default, filter after the line* (128, 121, 123).
   - **Calibration:** a player's choice to pass did not separate value, and cutting one sentence was a
     volume knob.
   - **Exhibit:** the volume-knob table.
   - **The shipped gate:** 10 of 29 restatements held, 0 of 36 worthwhile.
   - **Why a separate judge** (lesson 15, generator-verifier separation).
   - **What a held line leaves behind:** nothing.
   - **Scope:** one model reader per line, readers not yet checked against a person. A forced line may
     differ from a chosen one.
   - The Level 3 link (possible) sits here.
7. *A last word for the most-accused* (124). Picked from public tags, not private reads, and announced
   in a line written by code. 7 of 7 defended players were voted out. **The closing's effect on votes is
   unmeasured; say so in that sentence.**
8. *How players sound* (125), if kept here.
   - Voice in the player's own prompt rather than a rewrite.
   - **Exhibit:** the drift pair beside one voice line.
   - **Scope:** the paired-games numbers stay a lean (eight pairs, about 19% more talk on the voiced
     side).
   - **Never imply the voices made games more fun.**
9. *How it is checked, and what is not established* (129, 130).
   - Rule tests on hand-written transcripts.
   - Separate getting a turn, publishing a line and answering a question.
   - The held-defence case.
   - No standing regression bar.
   - Order effects unmeasured.
   - The opening-order sentence is wrong (seat order, not random).

**Cross-links:** page 3 (parallel and sequential steps as execution); chapter 2 (what each speaker may
see); chapter 3 (the town's vote-reason
brief and reply brief, block 145); Evaluation (the readers' calibration, hardening task 1b).

**Length risk:** this page carries the most blocks. If it runs past about 2,000 words, move subsection 8
to chapter 3 before cutting any scope.

### 3. Executing a day and night

**Reader question:** how do ten model-driven seats become one consistent game? Who acts when, what each
receives, how their results combine, and what stops a loop from running away?

**Promise:** the familiar game cycle translated into graph execution: conversation in sequence,
independent choices, collection, resolution and state updates. LangGraph is introduced here as the
implementation of those needs.

**Open with the game, not the framework.** The page's first paragraphs say, in game terms, that night
choices and votes are made independently and must all be collected before the night or the vote resolves,
and that conversation must happen in turn because each line answers the last. Only then name `Send`, the
collecting barrier and subgraphs, as the way those needs were met.

**Featured story:** a subgraph's result comes back by hand, and one fold-back wiped every other seat's
private note each night (112).
- **Damage, from the test:** notes broken for every seat but the first night actor, nearly all seats
  blank from day 2, and a corrupted end-of-game map that memory extraction reads.
- **Fix:** notes merge by seat.
- **Cost kept:** each wrapper must know what it sent.

Tell it as fixed: what the faulty update did, the change made and the tests that pin it. How it was
noticed is not recorded (commit `d1cbd2f8`, 2026-07-23); do not infer it from same-day commits.

**Subsections:**
1. *The game as a graph* (102, 109).
   - **Exhibit:** the parent graph, START to END, as a drawn diagram generated from `build_parent_graph`
     so it cannot drift.
   - Explain node, edge and router in one sentence each.
2. *A subgraph where a phase has its own flow; a named node where a turn is one step* (109).
   - The two collapses: June's factories (12 day and 4 night functions with identical bodies; from
     `refactor/node_factory_pattern.md`) and October's named solo nodes sharing one body.
   - "Role-specific content is payload data, not topology."
   - **Scope:** why the first subgraphs were chosen is not recorded, and the October reason is inferred.
3. *The same snapshot in parallel, conversation in sequence* (108).
   - `Send` per seat with a collecting barrier. `COLLECT_ROUND` numbers the lines. `NIGHT_RESOLUTION`
     resolves every choice at once, so branch order cannot matter.
   - **Worked example:** the pack's night shows both patterns in one subgraph.
   - **Exhibit:** the day subgraph's diagram.
   - The conversational evidence is page 2's; link it.
4. *Why the subgraphs are invoked by hand* (110).
   - The hand-built payload is the privacy boundary, because a `Send` passes its payload verbatim.
   - The guarantee itself is chapter 2's (blocks 1–5); link it.
   - Name the consequence that page 5 develops: a resume re-runs the step.
5. *How a subgraph's result comes back* (112). The featured story.
6. *What the agents share* (107).
   - Four records, in trust order. **Exhibit:** a four-line list.
   - One error reaches all ten seats: the nine-seat census's clustered errors, and game `e06`'s
     summariser.
   - **Ownership:** the fixes are chapter 3's, and how the errors were counted is Evaluation's.
7. *The step budget* (113). Computed from the rules that end the day. The parent still uses the default
   100.
8. *Checked without a model* (114, wiring part).
   - A scripted-model game on the real parent graph through the server's translator.
   - The note-merge test and the checkpoint allowlist.
   - **Scope:** implementation evidence, nothing about play.
9. *Limits* (116, graph part). No alternative orchestration design was compared. The first subgraphs'
   reason is not recorded. The root recursion limit is not derived from game length.

**Tags:** multi-agent orchestration, LangGraph, fan-out/fan-in, shared-state architecture.

### 4. One agent turn, from input to action

**Widened 2026-10-26 (owner):** the page follows one whole turn: the player's input, the model's
response, validation, retries and fallback, and the hand-off to the game (speech published; a vote
or night choice collected for the resolution, which is page 3's). What goes into the input is
chapter 2's; how it is worded is chapter 3's. The optional-field and Haiku-cache findings stay on
this page, not on Level 1. Diagram: input → response → validation / retry / fallback → accepted
speech or choice → (for choices) collect → resolve, as on the chapter page.

**Reader question:** how do you make a model's turn something code can trust? One answer of a known
shape, always legal, and always resolvable, even when the model or the provider fails.

**Promise:** the output contract, validation, retries and fallback. The title separates it from page 3
at a glance: page 3 is how ten turns become a game; this page is how one answer becomes a move.

**Open with the game:** a role may act only on certain players, and only while its uses remain (the
Vigilante's two bullets, the Speculator's one pick). The engine must be able to apply whatever comes
back.

**Featured story:** legal targets live in the schema, and on Claude Haiku 5.5 that collided with caching
(104).
- An enforced schema counts as the start of the prompt. A vote's schema lists that seat's targets, so no
  two seats could share the cached transcript.
- The schema is now written as text after the cached part and checked in code, and it is enforced only
  on a retry.
- **Result:** 1 failure in 412 Haiku calls. In paired games, votes and night actions went from never
  reading the cache to reading most of it.

The cost side is chapter 6's; this page owns the validation side.

**Subsections:**
1. *Code asks; the model answers one structured question* (103). The full "who decides what" table,
   eight rows: the concrete form of the design rule the chapter page states in one sentence. Its
   deduction row ("what follows with certainty") is labelled "→ chapter 3"; the table says who decides,
   not who built it. A seat has no tools.
2. *Why not a tool loop* (103).
   - **The owner's reasoning (2026-10-26):** the action space is fixed and small, so a tool would be
     called every turn. That means an extra round-trip, more output tokens and a less stable cached
     prefix, and the result would still need structured validation.
   - **Say plainly:** reasoned, not measured.
   - **The one measured part** (block 100): on Haiku a forced tool call turns its thinking off, and the
     probes chose the JSON-schema method, 51 of 51 against 45 of 51 (unit to confirm).
   - **Cost accepted:** the model can do only what a field allows.
3. *The output contract* (104; turn prompt "What the seat must answer", decisions 11 and 13).
   - Every field the turn shows is required, and "no" is a value (`pass_turn`, `abstain`, `no_check`,
     `hold_fire`), because Flash-Lite silently dropped nullable fields.
   - A target field lists only legal targets.
   - Fields that code reads downstream: the speech-act tags (page 2), `claim` and `claimed_night_actions`
     (the ledger, chapter 3).
   - **Field order is chapter 3's** (block 147): one sentence and a link.
4. *Enforced by the provider, or checked in code* (104). The featured story.
5. *When a reply fails* (104).
   - Ask again with the schema enforced. Then a rescue model, if the game has one; Haiku has none today.
   - Then a legal fallback: a pass for discussion; a random legal move or the role's word for declining
     for votes and night actions.
   - The stall budget and the rescue's design are chapter 7's (block 97).
   - Note that a fallback pass is a valid answer, which is how one was later cached and replayed in
     another game (page 5, Level 3).
6. *Semantic guardrails sit on page 2.* One paragraph only:
   - the opening filter and the echo gate are model judgements after the line;
   - both fail open;
   - a valid but wrong classification passes.

**Limits:**
- No failure rate for optional fields is recorded; the rule came from June schema work.
- No alternative orchestration was compared.
- Haiku has no rescue model.
- Today's field order and unenforced schema have not been checked for message quality (chapter 3).

**Length:** this is the shortest page, about 1,000–1,400 words. Do not pad it. If the owner prefers, it
can absorb page 5's "a human's answer takes the same path" paragraph rather than repeat it.

**Tags:** structured outputs and validation, output guardrails, graceful degradation.

### 5. Adding a human in the loop

**Reader question:** what does it take to seat a human at a table of AI agents, when the game must stop
for the human, wait, survive a restart and continue without changing what the AI players already did?

**Promise:** interrupts, checkpoints, repeated execution, caching and the server host. The cross-game
cache incident remains optional deeper reading (Level 3).

**Open with the game:** a person at the table may think for minutes, close the tab or come back after a
server restart, while nine AI players have already acted. Then the framework.

**Featured story:** the resume that re-ran the AI votes. Each step below is a cause and a fix, told as
caught and fixed:
1. **The tally.** The server's tally disagreed with the engine's, and its own cross-check refused to
   broadcast a wrong lynch. The first fix, keeping the first ballot, crashed the other way; the tally now
   keeps the latest ballot.
2. **The cause.** A subgraph invoked from inside a node is a black box, so a resume re-runs the whole
   step, and each human vote re-billed about 8 AI vote calls (nine-seat).
3. **The cache.** AI turns are cached, with an uncached twin for humans.
4. **The key.** The default pickled key never hit after a checkpoint round-trip, so the key became the
   payload's canonical JSON. Result: 20 ballots replayed from cache.

**Subsections:**
1. *A human's turn is an interrupt in the same pipeline* (105, orchestration decision 11).
   - The checkpoint is saved under the game's id (PostgreSQL, so a paused game survives a restart).
   - The answer is shaped like a model's reply, so it takes the same validation.
   - An absent human's turn is delegated to the seat's agent.
   - **Cost:** a human's free text has no tags, so a separate call tags it (page 2).
   - **Security:** a human's line enters other prompts unlabelled; that gap is chapter 2's (block 98).
     Link only.
2. *What LangGraph did at the pause* (105).
   - **Exhibit:** the incident table (problem, cause, fix):
     - an interrupt per nesting level;
     - the re-run votes;
     - an interrupt reaching the server only when its parallel step ends.
   - **Scope:** LangGraph 1.1.10, still pinned.
3. *Why the AI turns are cached and the human's never* (106, 114).
   - The featured story's steps 2–4.
   - **Exhibit:** the toy graph's two lines. With the parallel nodes in the parent, the AI sibling ran
     once across a pause and resume; inside a subgraph invoked from a wrapper, it ran twice.
   - **The declined alternative:** framework-managed subgraphs, which would mean redesigning the privacy
     boundary.
   - **Evidence scope:** one verification game (2026-08-19, nine-seat pack vote since replaced). The
     twin was still needed on LangGraph 1.2.14 (probe, 2026-10-07).
4. *Three things kept, three scopes* (106).
   - **Exhibit:** the game checkpoint, the AI node cache and the provider prompt cache, each with what
     it keeps and its scope.
   - This is the table chapter 6 points back to.
   - A surviving checkpoint does not guarantee a surviving cache entry.
5. *A cache key must name its scope* (115).
   - One paragraph:
     - the opening round adopted the cached pattern;
     - its payload held nothing particular to its game;
     - one served game replayed another's failed opening across models;
     - the game id is now in every cached payload.
   - Deployed 2026-10-26: say what the fix does and how it was verified (the regression tests and the
     before-and-after control), and make no statement about served games since, either way.
   - The Level 3 link sits here.
6. *Running the engine inside the web server* (111).
   - Three options. **Exhibit:** three lines, each with why it was kept or rejected.
   - The toy parity check before migrating.
   - The executor sizing from a human wolf's late prompt: 8 threads, then 64.
   - **Cost accepted:** the blocking/async boundary sits inside LangGraph.
7. *Checks and limits* (114, 116).
   - **Checks:**
     - the resume toy, with its stated blind spot (the config helper is pinned by its own unit test);
     - the cache-key round-trip and isolation tests.
   - **Limits:**
     - a resume still re-runs the step, and a miss after expiry or a restart re-bills the AI turns and
       may change their answers;
     - the cache assumes nothing outside the payload changes an answer mid-game;
     - the event log can lead the checkpoint by one step (accepted, and it needs a hard crash);
     - how many served games crossed before the fix is unknown.

**Limited uses across a pause (block 165, filed 2026-10-26).** A use is deducted only in the night
resolution, the barrier after every night turn, and the counts are computed from the night's starting
state. A human's pause happens inside a turn, so it always comes before the resolution, and a resume
cannot spend a use twice. Both halves are tested: the resolution run twice gives the same counts, and a
scripted game with a human Vigilante, paused at its night turn and resumed with a shot, ends with one
bullet left (the test fails if a shot is spent twice). One or two sentences in subsection 3, as an
idempotence point. Scope: the scripted model, one lineup, one seed; it shows the count is right, not
exactly-once execution of the step.

**Tags:** human-in-the-loop systems, checkpointing, cache-key design, asynchronous programming. Name
reliability (execution mechanics) without claiming exactly-once execution.

## Level 3 candidates (assessed 2026-10-26)

Every plausible Level 3 candidate from blocks 102–139 has been assessed against the six criteria and two
tests in [`../portfolio-level-3-writing-rubric.md`](../portfolio-level-3-writing-rubric.md), "Selecting a
Level 3 page". Each candidate is anchored in a Level 2 subsection that covers the same finding.

| Level 3 page | Anchoring subsection |
|---|---|
| The cache key that crossed games | Page 5, "A cache key must name its scope" |
| Silence calibration (possible) | Page 2, "Speak by default, filter after the line" |
| The voice rewrite (possible) | Page 2, "How players sound" (or chapter 3, if the voices move) |
| Hosting a sync graph in an async server (possible) | Page 5, "Running the engine inside the web server" |

### Selected

| Page | Reader question | Added value ("Readers will learn how…") | Why separate | What stays on Level 2 | Verification needed |
|---|---|---|---|---|---|
| **The cache key that crossed games** (page 5) | How did a cache built to make a human's resume free end up serving one game's failed turn to another game, on another model? | …five choices, each reasonable alone, composed into a cross-game key: privacy-first wiring, cached re-runs, a value-based key, one process-wide cache, and an opening payload with nothing game-specific in it. Also how a collision count, a recorded incident and a before-and-after control bounded what is known | The chain, the 7-of-66 collision analysis, the two games side by side and the 5 → 0 control need sustained attention. The parent's argument is how the game pauses for a human | The bug in one paragraph: payload with no game id, the incident, the fix, deployed 2026-10-26, one recorded case, extent unknown. Plus the lesson: a cache key must name its scope | (1) How the `51226f24` replay was attributed: its `player_9` turn has no captured prompt, so state the evidence (a `generation_failed` pass on a game where every other call succeeded, at the one seat whose role matched). (2) The control's setup: the scripted model on pre-fix code against the fixed code, the two Haiku games, the six shared seats' roles. (3) Restart times for the 19 other candidate pairs, if they can be checked |

All six criteria hold.
- **Distinct question:** how the chain composed. Page 5 asks how the game pauses for a human.
- **Substantial value:** a mechanism walkthrough plus a bounded-uncertainty analysis.
- **Reason to separate:** the parent would stall on it.
- **Optional for the parent:** page 5 keeps the finding and its limits.
- **Bounded scope:** from the August key to the October fix and its control.
- **Defensible:** the owner ruled the fix and the deploy, and the record states the uncertainty.

**Remove-the-link test:** passes; page 5's paragraph stands alone. **One-sentence test:** passes (the
added-value cell).

### Possible (pass the criteria; owner to decide)

| Candidate | Reader question | Added value ("Readers will learn how…") | Open point |
|---|---|---|---|
| **Silence calibration: a volume knob, not a filter** (page 2) | Can a model player's own choice to pass be tuned into a filter for useful speech? | …replaying each voluntary pass with "do not pass", blind classification of the forced lines, and a one-sentence ablation showed that the choice to pass did not separate value. Also how the shipped gate was then measured on the same lines | **Draft now as a complete study** (owner, 2026-10-26); update it when the owner's labels arrive (Evaluation hardening task 1b). Present it as an engineering decision informed by model judgements: one Sonnet reader per line, never checked against a person, and 23–46 turns per cell, stated where the results are, not as a closing caveat. The parent keeps the result and the gate's 10 of 29 / 0 of 36 |
| **Why the voice is in the prompt, not a rewrite** (page 2 or chapter 3; draft the page 2 subsection first, and create the deeper page only if the method adds something substantial) | Can a second model call add a persona's voice without changing what a line claims? | …blind naturalness and fidelity judging, a deterministic fact gate (names, nights, role words) that caught 1 of the 19 meaning changes, and a line study with a plain-against-plain noise baseline | **The home is open** (page 2 or chapter 3). Judges were Sonnet subagents. The paired games are a lean. Its general lesson (a rewrite can change meaning a name-and-night check cannot see) is strong for an LLM-engineering reader |
| **Hosting a synchronous agent graph in an async server** (page 5) | When the engine is synchronous and the server is async, where should the blocking live? | …three options compared by what each moves (threads, ownership, a viral rewrite), a toy parity check run before the migration, and executor sizing from an observed delay | **May belong to a server chapter.** The record is the server's design notes, not `evidence/`. The 64-thread fix rests on one observed late prompt (in a code comment, 2026-10-17). Page 5 keeps the decision in a paragraph |

### Deferred to another chapter's pages

- **The covers line and the evil seat's claimable roles** (block 54; claims 36 → 44, contradicted sightings
  4 → 1): chapter 3, deduction. Page 1 links to it.
- **The invented check and its rewording** (block 141): Evaluation page 1 owns how it was found; chapter 3
  owns what changed.
- **The summariser's framing in `e06`, and the claim ledger** (blocks 69, 71): chapter 3. Page 3 cites the
  case in one clause.
- **The night-1 lot and seat bias** (block 146): chapter 3. Page 2 keeps only the investigator-lynch chain.
- **The cache bug's diagnosis from captures** (block 163): chapter 7. **The provider prompt cache** (block
  8): chapter 6, which points back to page 5's three-row table.
- **The 301-second hang, stall budget and rescue model** (block 97): chapter 7. Page 4 links to it.
- **The leak checks' first run, 109 leaks** (block 4): chapter 2. Page 3 links to it.

### Kept on Level 2 (fails a criterion)

| Example | Criterion it fails |
|---|---|
| The card-only replay (137) | Reason to separate: it is page 1's featured story, and the parent needs the same table and quote. The method fits in two paragraphs |
| The eight paired games (138) | Substantial additional value: one bundled result that fits in a paragraph and a table |
| The four balance batches and the hold (135) | Defensible content as a standalone page: win counts from 6–13 games a batch, one model, never re-run. The sigil-tell reasoning fits in a paragraph |
| The nine-seat accusation census (131) | Defensible content as a standalone page: labels from the playing model's own summaries, exploratory |
| Sequential against concurrent: the June acceptance study (118) | Defensible content: unpaired, 4 against 8 games, read by the builder. The parent keeps the decision and the five-openers exhibit |
| The note-wipe fold-back bug (112) | Substantial additional value: page 3's featured story, complete in a paragraph and the test's damage list |
| The node-factory collapse (109; `refactor/node_factory_pattern.md`) | Substantial additional value: the June code has since been replaced by the October collapse. Its byte-identical fingerprint gate is chapter 7's provenance point (block 162) |
| The interrupt, tally and late-announcement incidents (105) | Reason to separate: they are page 5's argument |
| The investigator-lynch chain (127) | Substantial additional value: three links in a paragraph. The lot's evidence is chapter 3's |
| Tags against a judge (120) | Substantial additional value: one agreement figure with an unchecked judge |

## Disposition of every report

Paths are relative to `evidence/` unless marked. Every source the task names is accounted for.

| Source | Portfolio treatment | Reason |
|---|---|---|
| `gameplay/orchestration/report.md` | Pages 3, 4 (with the who-decides table) and 5; selected Level 3 | The graph-level decisions, the turn pipeline, human seats and the cache incident |
| `gameplay/discussion/report.md` | Page 2. Decision 5 (one node per turn) is cited on page 3 | The day today and its 22 decisions |
| `gameplay/roles/report.md` | Page 1 | The cast, balance and the evil contest |
| `gameplay/report.md` (hub) | Level 1 source. Problem 2 → page 1's opening; problem 4 → page 2's featured story; problem 5 → page 1's evil contest; the "execution reliability" paragraph → page 5 | Problems 1 and 3 belong to chapter 3 and Evaluation. Its unresolved table feeds the pages' limits |
| `gameplay/turn_prompt/report.md` | Page 4 only for "What the seat must answer" (the contract, not the order), "Model settings, validation and retries", decision 11, and decision 13 in one line | Everything else (wording, records, rules, briefs, field order, layout, thinking) is chapter 3's |
| `gameplay/discussion_evidence.md` | Not mined directly. It is the October journey record, linked as provenance. Facts used reach the pages through the reports. §2 → pages 1 and 2; §3 P3 → page 1, step 1; §7.4–7.5 → page 2; §8.2–8.3 → pages 1 and 3. §6, §8.4–8.7 → chapter 3 and Evaluation | Kept whole as the dated journey. Its section index already routes each part |
| `gameplay/roles/role_sheet.md` | Source of page 1's role table and the exact strings players see; linked as the ruling | The owner's design document |
| `gameplay/roles/phase3_wiring_census.md` | Page 3 (the October collapse's context); page 5's candidate idempotence sentence | Historical plan, dated note in place |
| `gameplay/roles/role_set/` (experiment log, smoke runs) | One sentence on page 1: the nine-seat cast was chosen for the memory experiment. Smoke runs unused | Superseded June design |
| `refactor/node_factory_pattern.md` | One paragraph on page 3 (the June collapse). Its fingerprint gate → chapter 7 | Placement table: node factories → chapter 1 |
| `frontend/docs/server_encountered_challenges.md` | §1–6 → page 5 (incident table, featured story); §8 → page 5's limits; §7 (the cookie path) is not chapter 1's | The human-seat incidents |
| `frontend/docs/server_design_notes.md` | §5 → page 5, "Running the engine inside the web server" (and the possible Level 3) | The concurrency decision |
| `frontend/docs/deploy_log.md` | The 2026-10-26 entry → Level 3 (deploy, pre-flight, served-game status) | Deploy state of the fix |
| `gameplay/data/` study folders | Exhibit sources: `evil_cover_screen/`, `evil_cover_games/`, `phase3_balance*/`, `phase3_games/`, `silence_calibration/`, `voice_rewrite/`, `persona_line/`, `persona_voice_games/`, `phase2_step8_games/` | Each exhibit is lifted from these records |
| `gameplay/deduction/` | Chapter 3. Page 1 links to the covers line; the Level 1 table's deduction row points there | Placement: the engine is chapter 3's |

## Boundaries and drafting checks

**One home per item** (the placement table):
- the evil contest: page 1, with chapter 3 linking;
- the node-cache bug: page 5 and Level 3, with chapter 7 holding the diagnosis and chapter 6 telling the
  caches apart;
- output guardrails: page 4, with the echo gate and opening filter on page 2;
- context isolation: chapter 2;
- field order: chapter 3.

Cross-link instead of retelling.

**No overclaims:**
- Discussion quality was not measured against the nine-seat game.
- "Fun" was never measured. Do not use "fun" or "engaging" as findings, including for the voices.
- Balance was tuned on Flash-Lite and held. It was never run on Haiku 5.5 or on today's rules.
- The eight paired games bundle card and engine changes.
- The closing defence's effect on votes is unmeasured.
- No alternative orchestration design was compared.
- The tool-loop reason is reasoned, not measured, except the Haiku forced-tool-call probe.
- The cache fix: state what it does and how it was verified (regression tests, the before-and-after
  control). Make no statement about served games since the deploy, either way (owner, 2026-10-26).

**Every number keeps its scope in the same sentence:** model, seat count (nine or ten), N, date, and the
unit (turns, samples, messages, games, voting days). Two traps:
- nine-seat numbers (the census, the June design's silence, "about 8 AI vote calls", 61 of 67 voting
  days, the four October test games) next to ten-seat ones;
- samples per frozen turn read as independent situations (82 samples come from 41 turns).

**Authorship:**
- The pages always say "I", never "we": the owner is the project's solo developer (owner,
  2026-10-26). That covers decisions, experiments and the server.
- The orchestration code may be presented as the owner's build.
- The deduction engine may not: it is AI-written, so keep its row in the who-decides table attributed to
  its chapter.
- Test authorship is never mentioned, either way. Verification subsections describe what each test
  checks.
- "Read by hand" and "read in full" do not become "I read" unless the record names the reader.

**Keep off the page:**
- the reports' "largely AI-written and not yet audited" lines on tests;
- batches 2 and 3 run from uncommitted working trees;
- missing CI;
- the uninstalled leak-audit job.

A limit that changes how to read a result always stays (the map's "Handle with care").

**Caught and fixed, not dramatised:** the vote tally, the never-hitting key, the note wipe, the
investigator lynch, the cross-game key. State each as found, the change made and its scope.

**Voice** (the owner's own pass on the chapter page's opening, 2026-10-26; imitate it on every page):
- Name the thing first, in one plain sentence.
- Build from the familiar outward, one layer at a time: the game need before the framework term.
- Define a design by the tension it resolves: who knows what, who wants what.
- Give the frame, then the parts ("two mechanisms: …").
- No dates, scope clauses or caveats inside an explanation; each caveat goes once, beside the claim it
  limits.
- On the chapter page, a result appears only where it pushed the design (e.g. the five identical
  openers that ended concurrent rounds), never for its own sake (owner, 2026-10-26).
- Avoid abstract nominalisations ("that distinction creates the central design problem"), defensive
  negations ("it was not a comparison of …") and trade-off jargon.

**Game wording** (from the 2026-10-26 review; details in "Level 1 presentation"):
- Never "the last side standing wins": each side has its own win condition, and the neutrals can win
  alongside another side.
- Engine results are always true; players' claims can be anything. Never "evil lies with true facts".
- "Votes made independently", not "secret votes".
- Cooperation between factions is what Town of Salem is designed for, not something observed here.

**Terms:**
- "Cache-key design", not "multi-tenant isolation".
- "Event-driven scheduling" or "shared-state architecture", not "event sourcing".
- "Simulation environment design" for the cast, not adversarial or red-teaming terms.
- The echo gate is a model judgement that fails open, not a deterministic guarantee.
- Checkpointing is demonstrated; exactly-once execution is not claimed.

**Time-sensitive statements to recheck at drafting:**
- Haiku 5.5 as the default player model;
- `json_mode` and no rescue model on Haiku;
- LangGraph 1.1.10 pinned;
- the deploy state of `2ecec0cc`;
- voices on in hosted games.

**Group B's framing stays in Group B.** Page 1's card text is game design that gives evil a way to
contest. It is not presented as "improving how agents play", which chapter 3 owns, and it makes no
claim about better play.

**Drafting order:** draft the Level 1 summaries and page 5 first. Page 5 has the strongest engineering
story and the selected Level 3. Then draft pages 1, 2, 3 and 4, and only the Level 3 pages the owner
selects.

## Open questions (owner)

Settled on 2026-10-26: the game → requirements → decisions → evidence arc; the requirements table in
place of the question subheadings and the Level 1 who-decides table (which moves whole to page 4, its
deduction row labelled "→ chapter 3"); the five page titles; no "what went wrong" section; the async
host on page 5, the shared records on page 3, the voices closing page 2; the page 1 hook reworded.

Still open:
1. **Possible Level 3 pages: direction set 2026-10-26, decided after drafting.**
   - *The voice rewrite:* kept as a candidate. Its question (can a rewrite change style without changing
     meaning?) could justify depth. Draft page 2's subsection first, then decide.
   - *The silence calibration:* draft now as a complete study; update it when the owner's labels arrive.
