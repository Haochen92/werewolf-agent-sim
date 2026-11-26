# Gameplay: how the agents play, what failed, and what changed

This report is the entry point to gameplay: how the game runs, what each player knows, how players
reason and speak, and whether the rules give them something worth debating. It explains the main
problems that drove the design and what the evidence supports. The linked component reports own the
implementation, experiments and detailed trade-offs.

The central problem is that a functioning game engine does not guarantee convincing players. Agents
invented checks, missed implications of their own results, stayed silent with useful evidence and
failed to offer plausible rival claims. Some failures needed clearer prompts; others led to changes
in the discussion flow, the cast or the division of work between code and models.

Three findings connect the work:

- **Correct information must be both available and usable.** Labelling an agent's own night actions
  fixed a known misreading. Explicit deductions helped an agent record an implication it had missed.
  Neither result establishes that supplying more information always improves decisions.
- **Good discussion needs evidence, competing explanations and a chance to speak.** The cast,
  evil-role guidance and speaking schedule address different parts of that problem. More claims or
  more speech are observable changes; better discussion remains a separate question.
- **Local improvements do not add up to a measured improvement in the whole game.** Most evidence
  comes from selected turn replays and small game batches. Today's factual-error rate, discussion
  quality and balance remain unmeasured.

**Version and scope.** This overview reflects the component reports as of 2026-10-26 (commit
`59bae5f5`); each report carries its own version line, and the orchestration report the cache fix of
that day. Results belong to the model, rules and sample named with each study. The nine-seat game ran
until 2026-10-09 and the ten-seat game since; Claude Haiku 5.5 has been the default player model
since 2026-10-15.

## The area

A player receives a prompt, returns a structured decision, and the engine applies the game's rules.
The next player's information depends on that result. Models also summarise discussion and judge
whether some lines should be published, so errors can enter through the surrounding system as well
as through a player's own reasoning.

| Report | What it explains | Read it when you want to understand… |
|---|---|---|
| [Orchestration](orchestration/report.md) | The parent graph, day and night phases, state updates, checkpoints and human turns | How the pieces execute together; why human resume needed caching and how a missing game id caused cross-game answer reuse |
| [Roles](roles/report.md) | The cast, abilities, victory conditions, balance studies and evil-role guidance | Why the game moved from one exact information source to several partial sources, and how evil can contest them |
| [Turn prompt](turn_prompt/report.md) | The information a seat reads, its ordering, and the required answer fields | How engine records become usable inputs and structured actions; which prompt changes helped |
| [Deduction engine](deduction/report.md) | Rule-based conclusions supplied from information a seat may already know | Why explicit reasoning support was added, how the solver works, and what its tests and agent replays establish |
| [Discussion](discussion/report.md) | Openings, replies, the open floor, closing defences and publication filters | Who gets to speak, what can suppress a line, and how the silence policy changed |
| [Day summary](../extraction/day_summary/report.md) | The record of earlier discussion and the claim ledger | How facts and claims survive into later days without treating a summary as ground truth |
| [Agent boundaries](../agent_boundaries/report.md) | Allowed information and the payload builders that enforce it | How private role information is kept out of other seats' inputs |

For the architecture, start with **orchestration**, then follow the component involved in the turn.
For the design journey, read the five problems below. Problems 1 and 3 concern information and
reasoning; Problems 2 and 5 concern evidence and competing claims; Problem 4 concerns whether useful
contributions reach the table.

The boundary with evaluation is deliberate: [evaluation/report.md](../evaluation/report.md) explains
how changes are measured and how far to trust the checks. Its
[factual-errors workflow](../evaluation/factual_errors/report.md) owns finding, counting and diagnosing
errors. This page owns the gameplay responses to those findings.
[discussion_evidence.md](discussion_evidence.md) preserves the October investigation in chronological
order; its section index points to the component reports that now own each topic.

## Problem 1. Factual errors: players stating what the record contradicts

**The failure.** Agents claimed checks they never made, hunted a remaining wolf after both wolves
were dead, misquoted votes and repeated invented claims from summaries. July's nine-seat census
found errors in about 3% of public messages. In the ten ten-seat games read against an October
rubric, incorrect inferences and distorted summaries were more prominent than invented facts. That
small audit does not establish a new error rate.

These errors matter because other players act on them. In one nine-seat game, an investigator
invented a check, the town eliminated an innocent player 4–1 on that claim, and the Serial Killer won.
The diagnosis had to distinguish missing information, ambiguous wording, lost history and faulty
reasoning: each calls for a different fix.

**The response.** The prompt now makes the board and each seat's night history explicit, labels
engine records separately from summaries, and collects claims in structured fields for the ledger.
These changes reduce reliance on a model reconstructing facts from scattered prose.

| Representative change | Evidence | Limit |
|---|---|---|
| Reword a result as “Night 3: you investigated…” rather than a public-looking reveal | Invented checks fell from 20/20 to 0/20 samples | One nine-seat turn |
| Print the board and require a read of each living player | Errors fell from 48% to 30% across 100 selected contexts in the July bundle comparison | Error-prone contexts, not a whole-game rate; the bundle does not isolate each addition |
| Ask the model to cite the record exactly | Vote misquotes remained at 24 before and after | This instruction did not help on the replay set; it does not show that all prompt changes fail |
| Give Haiku more thinking time | Correct votes rose from 65/160 to 98/160; discussion errors changed little | Selected ten-seat cases; better votes did not imply cleaner written reasoning |

**What this supports.** Clearer wording helped when the input was misleading. Supplying explicit
records and checking claims in code addressed other failures. A general instruction to be more
careful did not substitute for those changes. Thinking effort was another useful lever, but its
benefit depended on the model and task.

**What remains open.** No factual-error rate has been measured on the ten-seat game. Known failures
are replayed after changes, while new failures still emerge during play. The reports record
flash-lite at medium thinking and Haiku at low; moving Haiku votes to medium remained an open
cost-quality decision.

**Read next:** [turn prompt](turn_prompt/report.md), decisions 1–5 and 15, for input and thinking
changes; [day summary](../extraction/day_summary/report.md) for the ledger; Problem 3 for explicit
deductions. The [factual-errors report](../evaluation/factual_errors/report.md) explains the samples
and diagnosis behind these comparisons.

## Problem 2. Thin talk: accusations that weighed little

**The failure.** Nine-seat discussion leaned on voting patterns, silence and speaking order rather
than weighing competing accounts. In 28 games on `gemini-3.5-flash-lite`, the playing model's summary
labels attributed 47% of 194 accusations to behaviour patterns, 28% to votes and 20% to concrete
claims. Those labels are exploratory evidence, not an independently validated measure of quality.

The investigator was not simply refusing to reveal: it claimed in 24 of those games. The larger
problem was that its exact information faced little competition. No wolf or Serial Killer claimed
a role in the sample, and town accusations based on claims targeted evil in 34 of 35 cases. That
supported a design diagnosis: there was little room to debate a genuine result, and little reliable
evidence to discuss when no result was shared.

**The response.** The redesign addressed both opportunity and substance. The day gained opening
claims, reactive replies and closing defences. The ten-seat cast replaced one exact investigator
with three partial observers: the Investigator gets Suspicious or Not suspicious, the Sentinel sees
visitors, and the Trailseer sees where a player went. Blocking and concealment complicate those
observations through game mechanics. Evil also needed guidance to offer a competing account
(Problem 5).

**What the evidence supports.** Read games showed claim contests and covers broken by
cross-examination. The mechanics supplied more kinds of evidence. They did not establish that
discussion improved overall: the studies counted actions and examined examples, rather than
comparing nine-seat and ten-seat discussion against a validated quality measure. Similarly, an
elimination without a direct night observation does not by itself show that discussion caused it.

**Read next:** [roles](roles/report.md) for the cast and its trade-offs;
[discussion](discussion/report.md) for the day structure. The original census and competing
explanations are in [discussion_evidence](discussion_evidence.md) §1–2.

## Problem 3. Reasoning failures: the facts absorbed, the first step missed

**The failure.** In a ten-seat Haiku game, the healer recorded that it had been blocked and read a
Trailseer claim identifying a visitor. Only the Chanteuse could block that night. The healer repeated
the premises in its notes but did not connect them or speak. Other games showed agents misreading a
saved attack as evidence of the target's faction. These were reasoning failures despite relevant
facts being present.

**The response.** Several alternatives were tried before adding the deduction engine: more thinking,
a stronger summariser, a rewritten private-note prompt and majority voting over repeated samples.
More thinking helped votes; the other screens did not resolve the failures. Repeated answers could
share the same mistake, so sampling more was not enough on those cases.

The deduction engine moves selected rule-based inferences into code. It starts with the seat's
allowed information, narrows possible roles using game constraints, and supplies conclusions in the
prompt. Certain conclusions, conclusions conditional on named claims, and possible explanations are
kept distinct. It is intended to help weaker agents connect the logic while leaving interpretation
and action choices to them.

**What the evidence supports.** On the healer's frozen turn, the injected line changed recognition
of the Chanteuse's visit from 0/10 to 10/10 notes. Only 2/10 identified the particular player as
probably the Chanteuse, and speech remained at 0/10. This is promising evidence of uptake, with a
clear limit: recording an implication does not guarantee completing the reasoning or acting on it.

The implementation also adds considerable complexity. Tests compare deductions with game mechanics
and legal assignments on tested inputs. They support confidence in emitted conclusions; they are
not a proof of soundness for every state or completeness for every useful inference. The solver and
much of its testing were AI-written and have not been independently audited.

**What remains open.** There is no paired town-side whole-game comparison establishing an outcome
benefit. A stale private note can still override useful evidence, and rule sentences can become
generic excuses for discounting claims. These are reasons to assess what an agent does with the
extra information, not just whether the information appears in its prompt.

**Read next:** [deduction](deduction/report.md) for the algorithm, a worked example, validation and
complexity trade-offs. Its [experiment log](deduction/experiment_log.md) holds the failure cases and
alternative interventions.

## Problem 4. Silence: turns not taken, and results not shared

**The failure.** Silence came from three sources: the scheduler never offered a turn, a publication
filter held a proposed line, or the agent chose to pass. Treating them as one behaviour obscured the
cause. In the 28-game nine-seat sample, 367 of 517 passes were lines held by the novelty judge.
Ending a day after three passes also meant some players never got a turn.

Even when offered a turn, agents sometimes kept useful results private. The healer in Problem 3
carried a note saying to stay quiet unless addressed. In another Haiku game, all four survivors
passed on day 4, including a Vigilante whose shot had killed an evil player; it never claimed and
was eliminated.

**The response.** The redesigned day offers every survivor an opening, routes replies to addressed
or accused players, and gives the open floor a fuller sweep before ending. The 2026-10-18 silence
ruling asks players to speak by default on the open floor, with an echo gate to hold repetition and
filler. Openings retain a different policy: passing is still normal there. A voting-day instruction
also asks town players to decide their vote and explain it if they have not already done so.

**What the evidence supports.** Calibration found worthwhile lines among forced replies to turns
where agents had passed. Removing “a pass costs nothing here” increased speech, but also repetition.
On 65 judged open-floor lines, the shipped gate held 10 of 29 restatements and none of 36 worthwhile
lines. In four games on deals used by four earlier games, spoken open-floor turns rose from 41/100
to 54/93. These are small studies with model-generated judgements, not proof that more speech made
better games.

**What remains open.** Openings may still suppress useful claims. Private notes can preserve an
outdated plan to stay hidden. Missing speech-act tags can also prevent an accused player from
receiving the intended reply treatment. The schedule, publication gate and agent's choice therefore
need separate checks.

**Read next:** [discussion](discussion/report.md), especially the silence policy and its calibration.
The note-related failures remain in the [deduction case log](deduction/experiment_log.md), R1 and R12.

## Problem 5. Evil never contesting: denial, never a rival claim

**The failure.** Evil agents often denied accusations without offering a role or night story the
town could weigh against a real claimant. This continued after the cast changed. The cards permitted
bluffing but also treated remaining unclaimed as acceptable; permission alone had not produced the
intended behaviour in the early games.

**The response.** Guidance progressed from permission to bluff, to planning a cover in the private
note, to a stronger instruction to claim a role that explains a reported visit. The deduction engine
then supplied cover options and night stories consistent with the seat's information. The cards
provided tactical advice; code supplied constraints on which stories would fit. A later warning
addressed situations where a cover was unsafe.

**What the evidence supports.** In a card-only replay of 41 pressured Haiku turns, sampled twice per
arm, claims rose from 13 to 33 and denials fell from 21 to 3. A separate comparison with the new cards
in every arm found additional gains from engine cover lines. Those screens used different judges,
so their counts should be compared within each study, not added together.

Eight paired whole games tested a bundle of card and engine changes. Evil seats claiming rose from
3/24 to 11/24, and wolves won three games after the changes against none before. This shows the
bundle running in games, but does not isolate the engine's contribution or establish a reliable
change in win probability. The later cover-risk warning was not part of those paired games.

**What remains open.** More plausible lies create a new challenge for town: choosing between
competing claimants. Read games showed truthful claimants losing those contests, but do not establish
that town's only remaining problem is judgement. Balance on today's cards, rules and default model
has not been measured.

**Read next:** [roles](roles/report.md#the-evil-contest) for the progression from permission to
planned covers and the paired games; [deduction](deduction/report.md) for how cover information is
derived and checked.

## What holds across the area

**The strongest evidence is specific.** Some controlled replays show large changes on known failures:
clearer result wording prevented an invented check, a deduction line improved uptake, and revised
evil cards increased claims. Implementation tests support the rules and data flow they exercise.
Neither kind of evidence establishes the quality of today's complete game.

**The recurring design choice is where responsibility belongs.** Code owns legal actions, engine
records and rule-based deductions. Models supply choices, arguments and language interpretation.
When a failure is deterministic and checkable, moving that work into code can help. When the problem
is ambiguous input, a prompt correction may be sufficient. When it is competing claims or a decision
to speak, supplying another fact may leave the underlying behaviour unchanged.

**Execution reliability is part of gameplay too.** The
[orchestration report](orchestration/report.md) records a cache bug fixed on 2026-10-26: two games
could reuse an opening answer because the node-cache key omitted game identity. The recorded incident
copied a failed turn into a later game as a pass. Adding game identity separated those entries; the fix
was deployed the same day, and two Claude Haiku 5.5 games played back to back in one process on deals
sharing six seats' roles each made all ten day-1 opening calls, where a control on the pre-fix code
served five of them from the first game's cache.
This is distinct from a player choosing silence or a prompt failing to elicit a response, and from
the provider prompt cache used to reduce input cost. The orchestration report owns the incident,
regression checks and remaining uncertainty about its historical extent.

## What is unresolved across the area

| Gap | What remains unknown | Home |
|---|---|---|
| No ten-seat factual-error rate | How often errors occur in ordinary play after the changes | [Factual errors](../evaluation/factual_errors/report.md) |
| No validated comparison of discussion quality | Whether more speech and contested claims made discussion better | [Discussion](discussion/report.md), [roles](roles/report.md) |
| No balance study on today's configuration | How the sides perform after the card, deduction and rule changes; the four historical batches used flash-lite | [Roles](roles/report.md) |
| Limited separation of whole-game effects | Whether deductions help town outcomes, and how much of evil's gains come from cards versus engine support | [Deduction](deduction/report.md), [roles](roles/report.md) |
| Uncalibrated ten-seat model judgements | How often readers and judges mislabel errors or useful speech; repeated samples do not expand situation coverage | [Evaluation](../evaluation/report.md) |
| Fragile tags, notes and rule wording | Whether missing reply tags, stale private plans or misleading rule text continue to suppress useful play | [Discussion](discussion/report.md), [turn prompt](turn_prompt/report.md) |
| Incomplete operational verification | The historical extent of cross-game cache reuse and served-game verification after the fix | [Orchestration](orchestration/report.md) |

The next comparison should match the claim being made. A prompt correction needs a controlled replay
of the relevant failure. A claim about better discussion needs a defined, reviewed quality measure.
A claim about balance or outcomes needs games that let the consequences unfold. The
[evaluation hub](../evaluation/report.md) explains how to choose and interpret those checks.

*Started 2026-10-24; rewritten as the area's hub on 2026-10-26, with the detailed experiments left in
their component reports.*
