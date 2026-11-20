# Context engineering

*Alternative Level 1 draft, 2026-10-30. Organised around the failures that motivated the work. The
four Level 2 pages are planned; their titles below are navigation placeholders.*

## Page copy (draft)

### Context engineering: helping agents use what they know

Each agent takes its turn through a new model call. To play, it needs to know its objective, what it
can do, what has happened and what decision is required now. The graph holds the changing game state;
code selects the fields for that seat and combines them with rules and role instructions to build its
prompt. **Context engineering** is the work of making that information useful to the agent.

#### What an agent needs for its turn

Consider a wolf preparing to speak during the day. It needs to conceal its identity, protect its
allies and influence the vote. It also needs to understand the other roles: an Investigator can
identify a wolf, while a Healer can prevent a night kill. Their abilities affect which public claims
are plausible and what the wolf might say in response.

The first version used an eight-player cast. Its wolf discussion prompt supplied the following:

| What the prompt supplied | Why the wolf needed it |
|---|---|
| **Identity, objective and role guidance** | Know which player it controls, how the wolves win, and that it should conceal its identity and defend allies. |
| **Game rules and each role's abilities** | Understand the day/night cycle, voting, the pack's night attack, protection and investigation. |
| **Living allies and opponents** | Know who remains in play and distinguish packmates from possible targets. |
| **The current day and discussion round** | Place the decision in the game. |
| **Discussion history** | Follow claims and accusations, identify pressure on an ally, and decide what to contribute. |
| **The immediate task and answer format** | Produce a discussion message the application can use. Votes and night actions have different tasks. |

The same principle applies to other seats: an Investigator also needs its private check results,
while a Healer needs the information relevant to choosing a protection target. The engine keeps
state to resolve the game; the prompt exposes the part the player needs to make its next decision.
Static rules come from templates, rather than being reconstructed from graph state.

The initial expectation was that, with these records and instructions, the model could work out the
relevant facts and choose a sensible action. The context was short relative to the advertised window,
so retaining the information did not appear to be the main obstacle. But fitting information into a
prompt was different from getting the model to interpret and use it reliably.

There was also no private strategy note in that first version. A later change carried a model-written
assessment and plan into the next turn, allowing the agent to continue or revise its approach instead
of rebuilding it each time. That created continuity, but could also carry a mistaken belief forward.
The subsequent refinements addressed five problems: misreading facts, distorting earlier information,
failing to use evidence in an action, missing implications of facts already recognised, and reading
the prompt's own example as an answer.

#### Make implicit facts and ambiguous records explicit

The initial prompts expected the agent to reconstruct some facts from the information supplied:
who had died from the starting cast and living-player list, and which roles remained from the
revealed deaths. That reconstruction was not reliable enough, so the prompt gained an explicit
death roster and remaining-role counts.

Other failures came from how agents interpreted the wording. The Sentinel watches a player and
learns who visited them. In one game, the Illusionist said, “I visited nobody on night 2.” The
Investigator and Sentinel treated this as contradicting the Sentinel's watch result, which showed
two visitors to the Illusionist. They had reversed the direction of the claim: receiving visitors
does not contradict visiting nobody. The rules were expanded to state that a watch reveals who
came to the watched player, not where that player went or whether they acted. They also asked
players to make the direction explicit when speaking: “I went to X” or “X came to me.”

In a separate case, other players argued that the Sentinel should appear in its own visitor list,
and the real Sentinel accepted that
false rule. Adding the missing rule sentence stopped the concession in ten replays of the failing
turn, compared with ten concessions before the change.

This was a targeted repair, not a general solution to factual errors. Printing a correct board had
also failed to stop a survivor-count error in an earlier replay. Making a fact available gives the
agent a reference; it does not ensure the agent reads or applies it correctly.

*Explore: Making facts available and unambiguous →*

#### Preserve earlier information without changing its meaning

Each turn starts a new model call, so an agent's earlier assessment and plans must be supplied again
if it is to continue them. Its private strategy note carries that thinking forward; the public
transcript contains only what players chose to say aloud.

The shared discussion needs a different kind of continuity. By later days, passing every earlier
transcript would mean repeating hundreds of lines in every player's calls. Day summaries condense
those discussions while today's messages remain available in full. Structured claim fields also
let code assemble each player's claimed role and night actions into a **claim ledger**, then check
them against public game facts. Plain transcripts could still be supplied to the players, but code
would need those claims extracted into fields to perform the same checks. This design reduces the
discussion carried forward and supports those checks; it has not been shown to produce better play
than full transcripts.

Anything carried forward can carry an error forward too. A summary that misreads one line, or a note
that records a wrong belief, is read again on every later day, and a statement that was contested when
spoken can return as fact the next morning. One such line cost a game: a summary turned an
Investigator's "I was roleblocked" into a role claim, and the town voted the Investigator out on it.

The guard is to keep recording apart from judging. The summariser writes what was said, attributed to
its speaker, and never decides whether it is true. Each speaker states its own claims in fields, and
code checks those against what the game has announced, saying only what the record settles. What it
cannot settle stays a claim for the agent to weigh.

*Explore: Carrying earlier days forward: the day summary and claim ledger →*

#### Make the reasoning explicit: a structured chain of thought

When an agent made a puzzling decision, its short strategy note often gave too little explanation to identify what had gone wrong. I wanted it to state which evidence it considered, how it assessed the other players, and whether a retrieved lesson applied. That would make it easier to distinguish a missed fact, an unsupported inference and a decision that did not follow its own assessment.

Asking for that assessment in the prompt was not always enough. An instruction to assess each retrieved lesson, placed in a field’s description, was skipped in favour of the usual terse note. Giving each lesson its own required verdict field made the assessment an explicit part of the answer.

The order also mattered. When the vote came first, the note followed a choice already written: in a replay study, a quarter of those notes never committed to the player voted for.

The current turn therefore asks for the assessment before the decision:

1. **Reads:** assess every other player and give a reason.
2. **Memory verdicts, when lessons are supplied:** evaluate each lesson’s relevance to this turn.
3. **Strategy note:** record the assessment and intended approach.
4. **Decision:** produce the speech, vote or night action.

This gives each assessment a place in the answer and leaves a record for investigation. The reads can show whether the agent recognised a clue; the verdicts show how it treated a lesson; the note states the approach against which its action can be compared. These are the agent’s written assessments, not a complete account of its internal reasoning.

Closer agreement is not the same as a better decision. On 40 replayed votes, a separate model reading only the reasoning could identify the player voted for 75% of the time with the vote first, 87.5% with the reasoning first, and 92.5% with a required verdict on each lesson as well. The order makes the written reasoning the thing the action follows; it does not make the reasoning right. These studies informed the design; whether today’s order improves decisions has not been tested.

*Explore: Making the reasoning explicit: a structured chain of thought →*

#### Compute selected implications

Some agents recorded the relevant facts but still missed what followed from them. A Healer noted that it had been roleblocked, yet failed to connect that result to the blocking role: only the Chanteuse could block, and blocking required a visit. After input repairs and experiments with prompts and thinking effort, I chose to supply selected inferences through a **deduction engine**.

The engine starts from the information available to that player and uses the game’s rules to narrow the possibilities. Through **constraint propagation**, it repeatedly eliminates possibilities incompatible with those facts and rules, then writes the resulting conclusions into the prompt.

Its conclusions must respect two boundaries. First, they may use only information the player is allowed to know. One test changes hidden roles while holding the player’s visible information fixed and checks that the deductions stay the same. Second, the engine states what follows from the evidence; the agent still decides whom to suspect, what to say and how to act.

The wording must also preserve uncertainty. “The Chanteuse visited you” follows from the Healer’s own block result. But a report that Alice visited does not establish that Alice is the Chanteuse: another visitor could have performed the block. Each conclusion is therefore stated as certain, conditional on a named claim, or a set of remaining alternatives.

On replays of the Healer’s turn using the game’s live output mode, the agent identified the visitor as the Chanteuse in 8 of 10 attempts with the deductions, compared with 2 of 10 without them. It also spoke in 7 of 10, compared with 3. In another replay screen, deductions reduced a Sentinel’s errors when reporting its own watch from 6 of 40 to 2 of 40. Replies to that report did not improve: those turns already contained the dispute in their recorded discussion.

A third screen suggested that supplying facts consistent with a wolf’s cover encouraged claims rather than denials, though different judges assessed the two versions. These tests show effects on selected failures, not a general improvement in games. The Healer’s connection was also made without the engine by stronger models, and by the same model at a higher thinking setting.

*Explore: Working out selected conclusions in code: the deduction engine →*

#### When an example is read as a target

A sample answer in a prompt is meant to show the format. When the player has no evidence of its own, the
model treats it as the answer. The sample read in every prompt named player_2, and on the first voting day
player_2 drew about four times the accusations and votes of any other seat. The same happened wherever a
field had nothing real to hold: the model filled it with the example. The fix is a rule, not a better
example. An example never names a legal answer, and a field with nothing to hold is left out of the prompt
along with its example.

<!-- Sources and navigation notes (not page copy).
Initial turn table: git show db288e6:Agents/prompts.py, GAME_PREAMBLE and WOLF_DAY_DISCUSS,
verified directly. Historical eight-player cast, not the present ten-seat roles. Living rosters
were already supplied; later death/role summaries must not be presented as the first player lists.
Initial Investigator input: INVESTIGATOR_DAY_DISCUSS in the same snapshot. No claim that all roles
received the same private fields or that the initial wolf had later specialist abilities.
Strategy note added later: evidence/gameplay/turn_prompt/experiment_log.md §1–§2, origin and
adaptive-strategy commits. Context-window expectation is the owner's stated initial rationale in
this conversation, not a measured prompt-length or recall result. Summary history: evidence/extraction/
day_summary/experiment_log.md §1–§2; no claim that summaries were introduced only after the July
board work. Sections group problems, not a strict chronology of implementation.
Framing: evidence/gameplay/deduction/report.md §1, different failures and remedies; no claim that
these are controlled diagnoses of all agent errors or an obligatory four-stage progression.
Facts: evidence/gameplay/turn_prompt/report.md decisions 1, 3 and 4. Sentinel 10/10 -> 0/10 is one
failing turn replay, not a frequency estimate. Correct-board recurrence from decision 1, T1b.
Summary: evidence/extraction/day_summary/report.md §3 and §7. Structured speaker claims take
priority; summary fallback remains. Public-record comparisons do not validate all claims. Self-block
rule guards the incident; the invented claim did not recur in replays, so no prevention-rate claim.
Answer structure: evidence/gameplay/turn_prompt/report.md decision 10. Reasoning-first alone had no
effect; reasoning-first + memory verdicts changed coherence 75% -> 92.5%. Current reads/verdicts/note/
decision order is later and not established by that experiment. (Compare-candidates, decision 9,
is off the Level 1 and off page 3 by the owner's rulings of 2026-10-31.) No claim about internal chain of thought or universal benefit from explicit assessments.
Deduction: evidence/gameplay/deduction/report.md §1–§5. Healer example and certainty distinction §2;
propagation §3; current healer results: report 2026-10-30 note and experiment_log.md §8.
Sentinel screen: evidence/gameplay/data/visit_wording_ab/README.md, arm C. Covers: report §5;
different judges per arm. Earlier enforced-mode uptake/silence result superseded here by live-mode
replays. Authorship moved off L1 at the owner’s request; retained in the planned L2 close.
Example cue (section added 2026-10-31, owner's ruling: a short L1 section, no L2): turn_prompt/report.md
decision 5 (day 2 across 32 nine-seat games: player_2 drew 40 accusation tags and 41 votes against medians
of about 8 and 12; "about four times" rounds 40/8 and 41/12; the example read now names no seat; the day-2
effect was not re-measured). "Field with nothing to hold": caching/experiment_log.md §16 (426 of 3,118
turns shown no lessons returned the example's "lesson 1: follow"; field and example now dropped when no
lesson is shown). The night-1 seat bias and the lot are told on chapter 1's day-and-night page, not here.
The planned L2 titles are navigation placeholders, not broken links to nonexistent files. Page 4
owns the hidden-role-change metamorphic test explanation; Evaluation's code_checks.md covers the
broader verification strategy. The roleblocked healer is the planned focused L3 investigation.
-->
