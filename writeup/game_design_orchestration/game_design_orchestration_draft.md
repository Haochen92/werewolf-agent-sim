# Game design and orchestration chapter: diagram-led draft (for comparison)

Level 1 page copy, drafted beside [the current chapter page](game_design_orchestration.md) so the two
can be compared. Here, diagrams take over part of the explanation. The diagrams are in
[`exhibits/`](exhibits/); the current page's diagrams are unchanged.

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
role-specific abilities. Ten players belong to four sides: six town roles, two wolves, a lone killer
and a neutral.

Investigative roles receive private evidence they may choose to reveal. Protective and attacking roles
must make decisions based on uncertain information. The wolves need to conceal their identities and
coordinate their actions, while the lone killer and neutral pursue separate objectives.

These rules create the conditions for deception, deduction and cooperation. They also introduce the
central engineering challenge: **how do you make ten independently responding language models
participate in the same game, each with different information, while keeping their decisions
consistent with the rules?**

![Ten players on four sides, what is public and what is private, and one day and night](exhibits/game_at_a_glance.svg)

*Players share the same game but not the same information. Public claims, private evidence and hidden
actions shape later decisions.*

*Explore: [Designing evidence worth debating](evidence_design/evidence_design.md) →*

---

#### Keeping each player's information separate

For social deduction to work, players must operate under different information constraints. A town
investigator knows their own results but not the wolves' identities. The wolves know one another and
can coordinate privately. Everyone observes public events, but the claims made during discussion may
be true or false.

In a human game, the moderator controls this separation. Players receive individual role cards, night
results are delivered privately, and public announcements reach the whole table. Online games such as
Town of Salem implement the same boundary through their interfaces.

With agents, that separation must be enforced programmatically. The game system holds everyone's
roles, actions and results to resolve the rules, but **a model call knows only what its input
contains**.

Providing an agent with the complete game state and instructing it to ignore privileged information
would undermine the game. Even one private result included in the wrong prompt could give a player
knowledge they could never legitimately obtain.

I therefore build a restricted view for every turn, selecting only the information that player is
entitled to receive:

- The public game record, including announcements and discussion.
- The player's own role, abilities and private results.
- Any information shared within their faction, where applicable.

Wolves, for example, receive their faction's private conversation. Town players do not.

The boundary is enforced **when selecting the input, before the prompt is formatted**. I also check
assembled model inputs for private information reaching the wrong player.

This design keeps information isolation separate from the agent's willingness to obey instructions.
The model can lie about what it knows, but the system should not supply information it was never
entitled to possess.

![The full game state, the step that builds each player's input, and what an Investigator and a wolf each receive](exhibits/context_isolation.svg)

*Model calls receive player-specific views, not the complete game state. Information isolation is
enforced before prompt construction.*

*Explore: [Agent information boundaries](../../evidence/agent_boundaries/report.md) →*

---

#### Giving players opportunities to discuss and respond

Once players have their information, they need opportunities to share evidence, challenge accusations
and respond to one another. But discussion cannot continue indefinitely, and a few outspoken agents
should not prevent others from contributing.

In a human game, people listen continuously. They can recognise when a response is expected, interrupt
an accusation or decide when to reveal information. Online Mafia games rely on the same behaviour:
players type during a shared countdown and manage their own participation.

LLM agents do not behave this way. **An agent only participates while its model is being called.** It
reads a fixed conversation snapshot, generates a response and then stops until called again.

That difference changes how conversation must be orchestrated.

| Conversation behaviour | Human players | LLM agents |
|---|---|---|
| Awareness | Continuously follow discussion | See a snapshot when called |
| Responding | Can answer an accusation immediately | Must be scheduled for another turn |
| Participation | Choose when to speak | Depend on explicit turn opportunities |
| Timing | Can respond while others remain engaged | Each response has model latency |
| Conversation closure | Timer or moderator can end discussion | Code must decide when sufficient exchange has occurred |

The obvious scheduling approaches each introduce a different problem.

##### Why simpler schedulers were insufficient

| Approach | Benefit | Limitation |
|---|---|---|
| **Simultaneous rounds** | Simple and allows parallel calls | Players answer the same snapshot and talk past one another |
| **Poll everyone after every speech** | Lets agents indicate whether they want to speak | Nine additional model calls for each spoken line |
| **Real-time countdown** | Resembles an online human game | Faster models get more speaking opportunities |
| **Fixed speaking order** | Predictable participation | An accusation may go unanswered while unrelated speeches continue |

My initial implementation used simultaneous rounds. In one recorded day, five of eight players
independently opened with essentially the same question: "Does anyone have any initial thoughts…?"
Because everyone received the same discussion snapshot, their responses were disconnected. An accused
player could respond only in a later round, addressing everyone at once.

This showed why distributing turns fairly was not enough. The scheduler also needed to preserve
**conversational causality**: when one player addresses another, the answer should arrive before the
conversation moves too far ahead.

##### A reply-driven scheduler

I built a scheduler around conversational obligations rather than fixed rounds.

Each agent labels its speech with the intended recipient and its conversational purpose: questioning,
accusing, defending or agreeing.

When a player asks another a question or makes an accusation, the scheduler records that the addressed
player owes a reply. That obligation takes priority over ordinary speaking opportunities.

An exchange can therefore unfold as:

**A accuses B → B responds → subsequent players react to both statements.**

If several players accuse the same person, the accused player can answer them together rather than
receiving a separate turn for every accusation.

When there are no pending replies, the scheduler gives opportunities to players who have not spoken.
This ensures that an agent holding private evidence has a chance to contribute rather than being
excluded by repeated exchanges between more active players.

The scheduler also needs stopping rules. Repeated accusations do not create unlimited speaking
opportunities, and exchanges between the same pair are capped to prevent one argument from dominating
the day.

Discussion ends once owed replies have been answered and everyone has had an opportunity to speak,
subject to an overall cap of three lines per living player. If the cap is reached first, outstanding
questions receive one final answer. Players accused by at least two others then receive a closing
defence before voting.

The resulting division of responsibility is deliberate: **code decides who speaks and when; the model
decides what to say**.

This preserves room for unscripted conversation without making turn allocation dependent on model
latency or uncontrolled self-selection.

*Explore: [Orchestrating the conversation](conversation/conversation.md) →*

---

#### Running the game: coordinating phases and player decisions

A complete game requires more than a conversation scheduler. It needs to track surviving players,
select the next phase, gather decisions, resolve their effects and determine whether a faction has won.

The result of one phase changes what is possible in the next. A daytime vote may remove a player who
would otherwise act at night. Night actions can eliminate players, protect targets or produce private
information that influences the following morning's discussion.

I organise this progression using **LangGraph**, which connects execution steps through shared game
state. The graph determines what runs next, while the state records the game's progress and the
results of completed steps.

However, different activities require different execution patterns.

##### Sequential discussion, parallel decisions

The open discussion must run sequentially. Each speaker needs to observe the conversation produced by
earlier speakers, particularly when answering accusations or revealing evidence.

<!-- Corrected from "Discussion must run sequentially": the openings and the closing defences run in
parallel (orchestration report, "The day subgraph"); only the scheduled discussion between them is
one speaker at a time. The diagram shows all three. -->

Votes and night actions have different requirements. Players should make their decisions
independently, without seeing choices submitted by others in the same round. Their model calls can
therefore run in parallel, using separate permitted views of the same game state.

The wolves are an intentional exception: they coordinate their night kill through private
communication before submitting their agreed action.

Parallel execution reduces the time spent waiting for individual agents. But it introduces an important
distinction between **collecting decisions and applying their effects**.

For example, a protective ability may prevent an attack, while a blocking ability may prevent another
player's action from taking effect. Applying these actions immediately as model responses arrive could
make outcomes depend on which request finishes first.

Instead, a dedicated resolution step collects the choices and applies the game's rules together. The
resulting state is then used to produce private results and the public morning report.

This makes game resolution independent of model response timing.

![A day and a night, showing which steps run one at a time, which run all at once, and where the rules take over](exhibits/phase_execution.svg)

*The graph coordinates execution, while the rules determine outcomes independently of model completion
order.*

*Explore: [Executing a day and night](day_and_night/day_and_night.md) →*

---

#### One agent turn, from input to action

Within that orchestration, each agent needs a consistent interface for receiving information and
returning decisions.

A discussion turn produces speech. A vote identifies a player, while a night action may select a
target, use an ability or decline to act.

Despite those differences, the execution path is shared: prepare the player's permitted input, request
a model response, validate it and return the accepted result to the game.

The input includes the current game situation, only the information the player is entitled to receive,
and the legal choices available for that turn.

##### Why structured responses instead of tool calls?

These decisions operate within a predefined set of legal actions. A Vigilante, for example, must choose
an eligible target or decline to shoot. The agent does not need to discover which tools exist or decide
how to invoke them.

I therefore use structured responses. The model selects among available actions and may explain its
decision, but the action must be expressed in a predictable format that the game can interpret.

Validation is necessary because a generated response may be malformed, identify an ineligible target
or otherwise fail to provide a legal decision.

Invalid responses can trigger another attempt. If the agent still cannot produce a valid answer, the
system supplies a defined fallback, such as passing in discussion or declining an action.

This prevents a single invalid model response from leaving the game without a permitted outcome.

Finally, an accepted vote or night choice is not immediately applied to game state. It is collected
and passed to the phase resolver, preserving the separation between agent decisions and game rules.

![One turn: the player's input, the model's reply, the check, a retry with the format enforced or a legal fallback, then the hand-off to the game](exhibits/agent_turn.svg)

*Model output is validated before it affects the game. Votes and night actions take effect only when
their phase resolves.*

*Explore: [One agent turn, from input to action](agent_turn/agent_turn.md) →*

---

#### Letting a human join the game

The same game can also support human-controlled seats. A human needs the same information boundaries,
speaking opportunities and legal choices as an AI player. Ideally, introducing a person should not
require separate versions of the game's rules.

The main difference is how a decision arrives.

An AI turn requests a model response and normally completes within the execution workflow. A human
interacts through a browser, may take minutes to decide, disconnect unexpectedly or return later.

The game therefore needs to represent a pending human decision explicitly without losing its progress.

##### Pausing and resuming execution

I use LangGraph interrupts to pause execution at a human decision and persistent checkpoints to save
game progress.

When the player submits an answer, execution resumes and the response passes through the same
validation used for AI decisions. If the human does not return, an AI agent can take the turn.

This allows humans and agents to share the same decision pipeline.

However, pausing a step introduced a less obvious problem: **what happens to work already completed
when execution resumes?**

A human vote may still be pending even though other agents have submitted theirs. In my first test with
two human players, resuming the interrupted step caused completed AI votes to run again. Some agents
generated different choices, effectively changing votes they had already submitted.

The interrupted step was being repeated, not merely continued from the pending human response.

To address this, I cache completed AI decisions. If resumption repeats a step, its previously completed
model calls can reuse their recorded answers rather than generating new decisions.

This preserves already-completed choices while allowing the human's pending turn to be submitted.

##### Checkpoints and cached decisions serve different purposes

The solution has an important limitation.

Persistent checkpoints survive server restarts, but the AI-response cache is temporary. Cached entries
can expire or disappear when the server restarts.

The game can still resume from its checkpoint if the cache is missing, but affected agents may need to
generate their decisions again.

This distinction matters: **preserving the state of the game is not the same as preserving every
result of an interrupted execution step**.

The checkpoint handles durable progress, while the cache reduces unwanted re-execution of completed AI
decisions.

![A vote with one human player: the pause, the repeated step with and without the cache, and the two kinds of saved work](exhibits/human_resume.svg)

*Checkpointing makes the game resumable; caching completed AI turns reduces changes caused by
re-executing an interrupted step.*

*Explore: [Adding a human in the loop](human_in_the_loop/human_in_the_loop.md) →*

<!-- Diagram sources (2026-10-27). game_at_a_glance.svg: roles/role_sheet.md "The lineup" and "Win
logic"; discussion/report.md "A day today" (day 1: openings only); orchestration/report.md "The parent
graph" (win check after the vote and after the night). context_isolation.svg: agent_boundaries/report.md
§§1–3 (the checks run over the logged inputs after batch games and in unit tests, not as a live gate).
phase_execution.svg: orchestration/report.md "The day subgraph" (openings and closing defences in
parallel, discussion one turn at a time), "The nights" (the pack chats one at a time, in parallel with
each solo role's node), NIGHT_RESOLUTION after every branch. agent_turn.svg: agent_turn.md "Retry,
then supply a legal fallback" (the retry enforces the schema; the rescue model is left to Level 2).
human_resume.svg: human_in_the_loop.md "What survives a pause or a restart?" and the first two-human
test; no framework terms, no dates. -->
