# Separating behavioral knowledge from tactical advice

> **Decision record:** the July 10–14, 2026 read/tactic redesign for the nine-seat game.
> **Editorial review:** October 13, 2026. The proposal led to an implemented experimental tell
> pipeline and prompt channel; it did not establish a gameplay benefit. This record explains the
> design choice. The [credit reference](report.md) explains scoring, and the
> [tell report](../extraction/tell_extraction/report.md) covers construction and evidence.

## 0. The decision in brief

Separate two questions an agent answers before acting: **what to believe about other players**, and
**what to do given those beliefs**. Store behavioral associations as individual *tells*, and tactical
advice as *strategy points*. Evaluate tells against revealed roles across players exhibiting the
behavior. Evaluate strategies against recorded decisions when an agent reports following them.
Measure the agent's read accuracy separately.

This replaced an approach that asked one omniscient language-model judge to assess both reading and
tactical execution. The new design makes each scoring rule inspectable, although behavior detection,
strategy attribution, and the choice of reward remain sources of error.

## 1. The tension

Werewolf agents act on uncertain beliefs about hidden roles. A poor result can follow either a wrong
belief or a poor decision made with the right information. A single end-of-day judgment cannot reliably
say which memory should change.

The previous discussion judge was a reasonable starting point: it could assess tone, persuasion and
concealment that simple action checks missed. Its discussion verdict correlated with faction wins in
a 24-game, single-epoch study. That supported its use as a diagnostic, but did not establish that
using its verdict to curate memory would improve agents. Its night read-quality override also lacked
an independent accuracy check. The [discussion-tagger report](discussion_tagger/report.md)
records that evidence.

The redesign therefore separated the objects being evaluated. A behavioral association should not
lose credibility merely because an agent misapplied it. A strategy should not automatically inherit
every error in the belief on which it acted. Neither separation, however, makes a strategy's causal
contribution directly observable.

## 2. Two kinds of memory, three measurements

Each measurement has a different consumer.

| Object | Example or meaning | Measurement and use |
|---|---|---|
| Tell | A recurring public behavior associated with a role | Detected exhibitors' revealed roles, compared with the role's frequency in the cast; used to select behavioral knowledge |
| Strategy point | A situation-specific instruction for acting | Outcomes associated with reported follows, compared with memory-off outcomes; used in strategy curation |
| Agent read | The agent's belief about a particular player | Accuracy against revealed roles; used to assess the agent, not to credit an individual tell |

**Example from the actual tell book (`vote_41`):**

> A player casts a vote for someone they directly accused in the discussion.

In plain words: **they accuse someone, then vote for that same person**. The saved counts were
43 investigators among 240 players who exhibited this behavior across the sampled games. The
[34-entry seed book](../../evaluation/frozen_eval_sets/tell_book_v2_seed.json) preserves the exact
wording and counts. The steps below use this example to explain how a behavior becomes a role clue.

An illustrative strategy is “shoot the player you most strongly believe is a threat.” If it is followed
against a town player, the scoring problem is whether to penalize the belief, the strategy, or both.
That example motivates the separation; it does not prove the proposed attribution is correct.

## 3. The credit method

### Tells: propose a pattern, then check whether it predicts a role

Both mining and detection run **after games finish**, using saved transcripts. Neither is an extra
step during a live player turn. In the research loop, a batch of games finishes, the detector checks
those games against the existing behavior list, and the list and book are then updated for later
batches. Newly mined candidates are considered for a later checklist; they are not automatically
validated by the game that suggested them. Agents do not need to use a proposed tell while it is
being tested.

Using the **real accuse-then-vote example above**, the process has four steps:

1. **Propose the behavior to look for.** A model reads a finished game, including who held each role,
   and extracts descriptions of public behavior. This is the *mining* step. Accusing someone and
   then voting for them is a candidate worth checking, not yet advice that the player is probably
   an investigator.

2. **Match players to behaviors.** A second model receives another finished game's public transcript
   and a list of candidate behaviors. It identifies **which player IDs exhibited which behaviors**,
   with quotes from the transcript to support each match. For this example, it checks who accused
   someone and then voted for that same person. It is not given the players' true roles or told
   which role the candidate originally came from. Its output says who did what, not who is a wolf
   or investigator.

3. **Look up the matched players' true roles and count them.** Code takes those player IDs and
   looks up their roles in that game's saved record. Across the historical sample, this behavior
   matched 240 player/game pairs, of which 43 were investigators. Repeating the behavior within
   one game still counts once for that player. Investigators made up about 18% of the matches,
   compared with about 11% of all seats in these nine-seat games. This was a modest association
   with investigators, not a behavior unique to them.

4. **Select the better-supported clues for the prompt.** The system reduces the score of patterns
   seen only a few times, so a couple of lucky matches do not receive full weight. This adjustment
   is called *shrinkage*. It selects a small book of supported tells; this example was included in
   the saved book. Its prompt line gives the behavior and the observed count, 43 investigators in
   240 cases, so the agent receives the strength of the clue rather than a categorical role label.

The first model proposes what to check. The second identifies who did it. **Code then connects each
match to the player's actual role and calculates the association.** The detector's checklist contains
only behavior descriptions and IDs, not the original discovery roles, games or quotes. That keeps the
candidate's origin from suggesting which players it should match. Public claims and revelations in
the transcript remain visible.

Only a limited list of behaviors is checked in each game, to keep detection affordable. Periodically,
the system adds new candidates to that list and sets others aside. Candidates can therefore accumulate
counts before any agent is shown them. The store keeps their original discovery examples separate
from the detections used for scoring, and preserves each behavior's wording so its counts continue to
refer to the same claim.

The historical counts establish an association in the sampled games. Whether the detector recognizes
the behavior reliably, and whether the clue still helps under a different model or game, require their
own checks. Those tests and the storage design are described in the
[tell report](../extraction/tell_extraction/report.md).

**What kind of approach is this?** It is statistical pattern discovery assisted by language models:
propose a pattern, detect examples, and estimate which roles occur disproportionately among them.
It resembles *association-rule learning*, which measures how often one condition accompanies another.
Here the models turn conversational behavior into countable observations; the arithmetic assesses the
behavior–role association. This is a useful classification of the method, not a documented claim that
the project was derived from a particular algorithm or paper.

The small-sample adjustment pulls estimated role frequencies toward the ordinary cast frequencies.
One terminology difference matters when comparing methods: conventional association-rule *lift* is
a ratio, whereas this project's “shrunk lift” is an adjusted role share **minus** its cast frequency.
See the [association-rule definitions](https://dmg.org/pmml/v4-4-1/AssociationRules.html) and the
[credit reference](report.md) for the respective formulas.

### Strategies: attribute a decision, then score it

The accepted first implementation used the agent's existing follow verdict to identify which strategy
was applied. Deterministic rules then graded the recorded action using revealed roles and game events.
Subtracting the corresponding memory-off rate prevents a naturally successful action from making every
associated strategy look useful.

This is an association, not an isolated treatment effect. Several strategies may be followed together,
and agents select which advice to follow. A deterministic grader avoids an additional merit judge; it
does not remove attribution bias or guarantee that the reward captures every strategic consequence.

### Read errors: a proposed attribution boundary

The design proposed excluding outcomes attributable to a wrong read from ordinary tactic credit,
while retaining them in the agent's read evaluation. Strategies about acting under uncertainty were an
explicit exception: excluding their misses would flatter reckless policies.

For example, a policy that says “take a risky shot at parity” must be evaluated across hits and misses.
A tactic conditional on a correct identification asks a different question. This distinction is useful,
but assumes the stored strategy and stated belief allow that classification.

The implemented July partition was narrower than the general proposal: negative night outcomes could
be excluded when the actor reported a high-confidence threat read on a town target. Targeted town
discussion used the accusation and landed lynch to identify its exclusion case. The current legacy
scorer does not implement a per-strategy `risk_policy` exception. These implementation boundaries are
spelled out in the [credit reference](report.md); the design should not be read as a completed causal
decomposition.

### Discussion: use an observable endpoint, retain influence as a diagnostic

Discussion has no immediate success flag comparable to a shot or vote. The chosen starting signal was
the day's lynch, interpreted for the speaker's faction, with a refinement when a recorded accusation
landed on that target. This allows broad coverage, but shares the day's outcome among strategies that
may have contributed very differently.

A finer diagnostic asks whether the addressed player's next read moved in the intended direction.
The proposal subtracts the target's preceding read trend to reduce credit for joining an existing
pile-on. It cannot fully separate persuasion from anticipating the room. The design therefore kept
this *first-link read delta* outside memory curation. Its proposed promotion test was a paired replay
with and without the utterance, after identifying cases worth that expense.

For concealment advice, a separate signal compared accusations received with the day's accusation
volume and required participation. These guards reduce free rewards for silence or an inactive room.
They cannot distinguish effective concealment from the room simply attending to somebody else.

## 4. The tell book at generation time

The proposal delivered two memory blocks: a compact tell book and retrieved strategy points.
Observations remained stored examples from which strategies could be synthesized, rather than a third
injected block in this experiment.

The two delivery methods fit different content. Tactical advice can depend on the current situation,
so only a relevant subset is retrieved. A small tell book can be selected before the turn and inserted
before the agent forms its reads. During play, tells about fully revealed dead roles are removed.
There is no semantic search for tells on each turn.

The July 14 revision selected tells for every unrevealed subject role, including town power roles,
with separate slots for discussion and voting behaviors. Everyone receives the same public-study
knowledge. This helps wolves identify an investigator as well as helping town identify a wolf; the
symmetry was accepted rather than presenting the book as a town-only advantage.

Dropping observations from this experimental prompt was a scope decision, not evidence that they were
useless. Historical static-memory benefits belonged to their own observation-based configuration and
could not validate this replacement. The tell book needed its own evaluation.

## 5. Alternatives considered and rejected

The alternatives clarify what the separation does and does not buy.

| Alternative | Reason for the decision |
|---|---|
| Keep one holistic merit verdict | Useful for diagnostic coverage, but insufficiently specific for assigning errors to beliefs or procedures |
| Score tells by the agent's read errors they would fix | Makes a behavioral association's score depend on the strength and habits of the agent applying it |
| Score only tells an agent says it used | Restricts evidence to a selected sample and adds unreliable self-reported attribution |
| Store role heuristics as a prose paragraph | Fuses several claims, preventing per-behavior counts and retirement |
| Credit strategies by changes in listeners' reads | Public conversation and prior momentum confound influence; retained as a diagnostic |
| Use non-addressed listeners as an untreated control | They hear the same public utterance, so they are exposed too |
| Reserve an exploration slot in the injected tell book | Active candidates can be measured without being served; injection is unnecessary for collecting their evidence |
| Synthesize several tells into a broader sentence | The new claim needs new measurements; it cannot inherit all its parents' counts |
| Retrieve tells, form a read, then retrieve tactics | Adds a generation stage; the initial design instead supplied both kinds of memory before one decision |
| Segment tell selection by game stage immediately | Fragments support before stage-specific differences are established; conditioned variants remained an option |

An outcome-blind matcher for strategy use was also deferred. It could replace self-reported follows,
but would introduce another detector requiring its own evaluation. The initial choice favored using an
existing signal with visible limitations.

## 6. The decision and its tradeoffs

Adopt separate behavioral and procedural memories, separate their scoring, and retain broad merit and
influence measurements as diagnostics. This makes the reason for each memory update inspectable.
It does not demonstrate that the resulting updates improve play.

Three costs mattered. Read-based exclusions reduce the tactic sample and may introduce selection effects.
Discussion endpoints share outcomes across contributors. Behavioral associations may become stale when
the game, prompts, or model change. These are limits on interpreting scores, not reasons to collapse
the measurements back into one opaque verdict.

## 7. Consequence: the judge's role and where retrieval fits

The discussion judge no longer supplies the redesigned credit signal. It remains useful for inspecting
qualities such as tone and credibility that the deterministic rules miss. A diagnostic can explain a
result without deciding which memory is pruned.

Retrieval remains useful for a large set of situation-specific tactics. The tell channel instead uses
a bounded book selected from measured associations. The choice follows the shape and use of each kind
of knowledge, rather than assuming every memory needs the same retrieval pipeline.

## 8. What was built and what the evidence establishes

The [July build log](../extraction/tell_extraction/experiment_log.md) records mining, detection,
curation and prompt injection implemented in the research loop by July 13, followed by the role-based
book revision on July 14. The earlier “v1 not yet built” status no longer describes that outcome.

The detector was evaluated against a small, provisionally labelled set; one game also received direct
human adjudication. The decision to proceed with those labels did not turn them into a large independent
benchmark. A 40-decision replay with the balanced 12-entry book changed 11 decisions, with correctness
20/40 without the book and 24/40 with it. This demonstrated a responsive prompt channel, not a reliable
improvement. The later 34-entry book did not receive that same replay check.

The current prompt hook remains in `Agents/memory/tell_book.py`, controlled by `WW_TELL_BOOK`, separately
from ordinary memory retrieval. The [ten-seat deployment plan](../memory_system/v8/plan.md) leaves tells
outside its scope. Current strategy-credit work is a separate port under `Agents/memory/consolidation/`.
Neither the historical tell measurements nor the existence of the hook establishes ten-seat validity.

## 9. Lessons

The useful separation is between **a claim about the world**, **an instruction for acting**, and
**the agent applying them**. They can fail independently and need different evidence. Explicit scoring
makes those assumptions easier to challenge; it does not eliminate them.

This also changes the exploration problem. A strategy needs use before its followed outcomes can be
observed. An active tell can be measured against public behavior before it is placed in an agent's
prompt. Keeping that distinction avoided importing an unnecessary injection-based exploration policy.

**Evidence and implementation:** [credit reference](report.md),
[tell reference](../extraction/tell_extraction/report.md),
[chronological experiments](../extraction/tell_extraction/experiment_log.md), and
[research-loop module map](../../evaluation/src/loop/README.md).

Implementation pointers were checked against repository revision `d206680d` and the October 13, 2026
working tree. Historical measurements retain their linked run artifacts; this is an editorial review,
not a new experimental run.
