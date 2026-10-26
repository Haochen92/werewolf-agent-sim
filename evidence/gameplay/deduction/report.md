# Helping agents reason from the facts they already have

Factual errors damage a social-deduction game because other players act on them. An investigator
inventing a check can get an innocent player voted out; an agent ignoring a decisive result can leave
the town with nothing useful to discuss. Deliberate deception belongs in Werewolf. Accidental mistakes
about the game record undermine that experience.

The deduction engine grew out of that problem. After fixing missing inputs and trying prompt and
model changes, the AI seats (Claude Haiku 5.5 at a low thinking budget) still had the relevant
facts but failed to connect them. The design
was to **compute supported deductions in code and put them directly into each agent's prompt**.
The model still decides what to say, whom to trust and how to act.

The result is promising but limited: in one frozen failure, all 10 injected replays recorded a
previously missed conclusion, compared with none without it. All 10 still stayed silent. The engine
can supply a missing reasoning step; that does not establish better decisions or better whole-game
play. Its substantial rule and verification machinery is the cost of supplying that help reliably.

## 1. Why build this after trying prompts?

The [factual-error report](../../evaluation/factual_errors/report.md) establishes the wider problem.
In the July nine-seat census, about 3% of public messages contained a factual error. In an October
live game, an invented investigation result led to an innocent player's elimination and a serial
killer win. These observations motivated reliability work; they are not a baseline measurement for
this deduction engine.

That work exposed different causes with different remedies:

| Failure | Appropriate response |
|---|---|
| A fact is missing or distorted before it reaches the agent | Repair the input, record or summary |
| A fact is present but worded confusingly | Clarify the prompt and replay the failing turn |
| The facts are clear, but the agent misses or overstates their implications | Test more reasoning effort, a stronger model, or explicit deductions |
| The agent understands a fact but follows an outdated plan | Investigate how it carries forward and updates its strategy |

The engine addresses the third row. It cannot substitute for the other fixes.

**The earlier methods helped in some places, but did not resolve the remaining failures.** The July
prompt bundle reduced errors on selected error-prone turns from 48% to 30%. A later nine-seat replay on
gemini-3.5-flash-lite also found a substantial benefit from more thinking: bad samples fell from 82
to 27 of 267, at medium against minimal. So “prompt changes did not work” would be too
broad a claim.

The immediate ten-seat experiments that preceded this engine were less encouraging:

| Attempt | Result on the tested cases | Implication |
|---|---|---|
| Increase Haiku's thinking from low to medium | 98/160 correct votes versus 65/160, at about 2.7× the output tokens; discussion errors barely changed | Useful for votes, but no general reliability fix |
| Use a stronger day summariser | 18/30 summaries flawed in each arm | No improvement in this screen |
| Rewrite the private-note prompt to separate changes, reasoning and plans | 27 fact/rule errors versus 15 in 56 samples per arm | Not adopted; asking for more explicit reasoning did not make it more reliable |
| Take a majority of three low-effort votes | 39% correct versus 41% for one vote | Repeated samples often shared the same mistake |

These studies used different cases and measures; their percentages should not be compared across
rows. The setups are in the [experiment log](experiment_log.md).

The resulting design choice was to move rule-based inference into code. If the same game facts imply
the same conclusion, computing that conclusion once avoids asking the model to rediscover it on
every turn. This is a bounded intervention: it supplies logical consequences while leaving uncertain
social judgments and actions to the model.

## 2. One example explains both the benefit and the risk

A healer was roleblocked on night 1. In this game's cast, only the Chanteuse, a wolf role, could
perform that block, and blocking requires a visit. The trailseer (player_3) said it had followed
player_7 to the healer that night; player_7 admitted the visit and claimed no role.

The healer's notes repeated the premises over three turns without drawing the useful connection.
It passed all three turns. The engine now supplies the first step explicitly, beside the healer's
own night record:

> Night 1 (last night): You were roleblocked: your protection of player_5 did not happen. Only the
> Chanteuse could roleblock that night, and a block is a visit, so the Chanteuse, a wolf, came to you
> that night.

It also connects the reported visit, with the uncertainty preserved:

> player_3 says player_7 came to you on night 1, and player_7 agrees. If that is true, either
> player_7 is the Chanteuse, or player_7 and the Chanteuse both came to you.

Both lines are verbatim from the engine's acceptance test for this turn. Each carries its premises
in the sentence: the first says why only the Chanteuse fits. **It cannot say “player_7 is the
Chanteuse.”**
A second visitor could have performed the block. Nor does a correct report prove the reporter's
claimed role: a liar can report something that really happened.

This is the central engineering difficulty. Supplying an inference is easy; checking all the ways it
could be false is harder. Injected text is taken up almost every time: all ten replays in §5 wrote
the line into their notes. So a wrong line would not be an occasional error. It would be a false
premise in every game where its conditions hold.

Every line therefore needs to communicate one of three things:

| Kind of statement | What it means |
|---|---|
| Certain | Holds in every legal situation compatible with this seat's information |
| Conditional | Holds if the explicitly named claims are true |
| Alternatives | Lists the possible branches without promoting one branch to a fact |

The healer's first line is certain; its second lists the alternatives under a named claim. A
conditional reads, for example: “If player_2's watch is true, player_8 is the Healer: no other role
still in play could have come to you on night 2.”

These are design requirements, not a claim that testing has proved the entire implementation correct.
The wording carries the qualification in the sentence itself so that an agent cannot miss it by
skipping a heading.

## 3. How it works

The path through the system is:

**Information this seat may see → facts and constraints → deductions → prompt text → model decision**

### Start with the seat's information

The engine reads a `SeatView`, built from the same payload already allowed to that player: public
events, its own role and night results, and pack information if it is a wolf. It does not receive the
omniscient game state. Public claims are available as claims, not automatically accepted as facts.

This boundary matters as much as the logic. Giving an agent the right answer from a hidden role table
would defeat the game. The intended help is what a careful player could infer from permitted
information. The existing [information boundary](../../agent_boundaries/report.md) remains responsible
for constructing that input correctly.

### Translate game mechanics into constraints

Some conclusions are direct: a roleblock tells the recipient that a blocking visit occurred. Others
restrict who could hold a role, who could have made an observed visit, or whether an ability still has
uses left.

Rules ask what a role *is* rather than naming it: night-immune, blockable, whether its visits show
under its own name, whether it reads Suspicious. One role-trait table answers those questions. A new
role is declared there, the trait tests show which rules its traits already cover, and only new
behaviour needs a new rule. The table is checked against the game engine, not just declared (§4).

Each deduction records its premises and supporting events. This allows a rendered line to be traced
back to the rule and evidence that produced it.

### Narrow candidate roles until nothing changes

The central solver is **constraint propagation**. It keeps a set of possible roles for each player,
including dead players whose roles were concealed. Known roles are fixed; unknown players start with
the roles that still have unaccounted-for copies in the dealt cast.

An illustrative example, assuming one copy of each role:

| Player | Before propagation | After propagation |
|---|---|---|
| A | Healer or Sentinel | Healer or Sentinel |
| B | Healer or Sentinel | Healer or Sentinel |
| C | Healer, Sentinel or Chanteuse | Chanteuse |

A and B must use up the Healer and Sentinel between them. C therefore cannot hold either. We do not
need to decide which role A holds to deduce C's role.

The implementation repeats four kinds of rule:

1. **Role counts:** if all copies of a role have known holders, remove it elsewhere; if only enough
   possible holders remain to fill its copies, those holders must have it.
2. **Closed groups:** if a group of players must use up a group of roles, remove those roles outside
   the group, as in the example.
3. **Observed actors:** if an event establishes that one of several players performed an action, and
   only one can still have the required role, narrow that player's roles accordingly.
4. **Game continuation:** exclude concealed-body assignments that would have made the game end at an
   earlier win check, since the game demonstrably continued.

Other constraints are applied before this loop: for example, a role known to have acted on a night
cannot belong to a concealed body that died before that night.

Every removal may unlock another rule, so the solver repeats until a full pass removes nothing.
It terminates because candidate sets are finite and only shrink. If the solver detects a contradiction,
its caller receives no candidate result instead of a forced answer.

**This is not a full search through every complete game state.** The main algorithm propagates
constraints, although the continuation rule does enumerate combinations for concealed bodies.
Closed-group checks also examine player subsets, so this is not a claim of cheap scaling to arbitrary
large games. The separate brute-force role-assignment oracle is used for testing.

The reason for propagation is traceability: each removal has a named rule and evidence. It can miss
relationships a fuller search would discover. Missing a deduction leaves the model with less help;
removing a genuinely possible role risks giving it a false conclusion.

### Keep assumptions separate, then render the result

For conditional deductions, the engine reruns propagation with a supported claim premise added for
that run. A conclusion from that run stays qualified: “If player_2's watch is true…” It does not
become a fact in the baseline candidate sets.

Additional rules compare claims with the record and with each other, connect private results to
reported visits, and enumerate explanations where the evidence leaves alternatives. Evil seats also
get facts about which cover roles and night stories fit the record. Their role cards provide the
strategic advice; the deduction lines describe consistency.

Altogether the engine works at eight levels, one code folder each, in the order a seat would use them:

| Level | What it adds | Example line |
|---|---|---|
| Own results | What the seat's own night record proves, shown beside the record | the healer's roleblock line (§2) |
| Public events | What the morning, the dead roster and a read-out will prove to everyone | “player_3's will shows player_7, the Chanteuse, went to player_8 on night 1. The pack's kill that night was on player_1, so that visit was her block on player_8.” |
| Candidate roles | Which roles each player and hidden body could still hold | “The Serial Killer is alive and is one of player_2, player_4, player_6, player_8 and player_10.” |
| Joins | The seat's own results set against another player's claim | the healer's either/or line (§2) |
| Conditionals | Propagation rerun with a claim assumed true | “player_8 can be the Serial Killer only if player_2's watch is false.” |
| Comparisons | Today's claims against the record and each other | “player_2 claims the Sentinel. Its report that player_7 came to you on night 2 is true. That does not show that player_2 is the Sentinel.” |
| Explanations | Every branch of a claim the morning leaves open; abilities used up across nights | “player_5's self-bet has saved it twice, so it has none left.” |
| Evil seat facts | For a wolf, the Serial Killer or the Necromancer: which roles it could claim without contradiction, which night stories fit | “No living player holds the Sentinel, so if you claim it, no one can counter-claim you truthfully.” |

The renderer turns the items into two blocks. The public block is built from the public record alone,
so it is the same for every seat and sits in the cached prompt prefix. The seat block sits after the
cache boundary, before the agent's carried-forward strategy note. Placement screens found no reliable
behavioural difference between before and after the note (§5); before is the cache-friendlier order,
because the note changes every turn and so stays last. Direct consequences of a private result also
appear beside that result. Derivations are logged rather than printed.

Within a block, entries go in seat order, never by importance. These models favour the first-named
player in a list, so an entry placed first because it had the most to say would pull votes toward
that player.

This is the seat block an investigator received at a day-3 vote in one acceptance case. As played,
before the engine, it voted out the healer who had protected it:

```
- If the current role claims are true, the Serial Killer is player_6 or player_10.
- You were roleblocked on night 2, so the Chanteuse came to you, and player_7 was the
  Chanteuse. player_2's report that player_7 came to you that night is true. This does
  not show that player_2 is the Sentinel.
- player_8 can be the Serial Killer only if player_2's watch is false.
```

In a census of 278 saved Haiku turns, the median seat block was four lines, or 742 characters; the
median public block was one line. The engine adds roughly a paragraph to the prompt.

Modes allow deductions to be off, limited to private records, extended to facts without claim-based
inferences, or fully enabled, with faction overrides. Human seats receive none. Games using roles or
use limits outside the verified set receive none either: adding a second blocking role, for example,
would invalidate “only the Chanteuse can block.”

## 4. What makes the implementation credible—and what remains uncertain

The main risk is an unjustified conclusion presented as certain. Verification targets that risk in
several ways:

| Check | What it can catch |
|---|---|
| Examples and counterexamples resolved through the real game engine | A rule that misses an interaction such as a block, concealment or borrowed action |
| Exact rendered-text assertions and four frozen acceptance cases | Wording that loses a qualification, omits a required line or states a forbidden conclusion |
| Brute-force role assignments on test cases | A candidate removed even though a compatible assignment permits it |
| Random nights resolved through the real game engine | Deductions that conflict with the actual roles or resolved events |
| Hidden-state changes with the visible input held equivalent | Output that depends on information the seat should not know |
| Role-trait checks against resolved nights | A trait table that disagrees with actual game behaviour |

The suite includes 20,000 random nights in each of the own-results, public-events and candidate test
files. The trait check resolves real nights with every role attacked, blocked, watched, followed, checked
and sigilled; it caught all 168 tested single-trait flips. The deduction suite passed in full on
2026-10-26.

A separate census compared propagation with the brute-force oracle on 150 generated games: 3,408 seat
views and 525 public views. It found no extra candidate roles left by propagation relative to that
oracle. That is useful evidence of coverage on those inputs, **not a completeness proof**: both
systems can omit the same game fact, and conditional runs were not included in the census.

The tests were largely AI-written and have not had an independent audit. Examples, random sampling
and an oracle provide complementary evidence; they do not establish that every legal interaction has
been checked. The aspiration to supply everything a careful human could deduce exceeds what has
been demonstrated.

Runtime was small in the recorded sample: candidate construction and solving took a median 0.45 ms
across 3,408 views; building both blocks for one acceptance-case vote took a median 10.5 ms over 30
builds. These measurements are from one aarch64 host. The significant cost is maintaining the rules
and their tests, rather than the measured execution time.

## 5. What improved in the agents?

**The strongest result is uptake of a supplied conclusion, not improved gameplay overall.** The
roleblocked-healer failure above was replayed with and without the injected consequence. On the turn
after player_7's admission:

| Outcome at low thinking effort | Without injection | With injection |
|---|---|---|
| Notes record that the Chanteuse visited the healer | 0/10 | 10/10 |
| Notes identify player_7 as probably the Chanteuse | 0/10 | 2/10 |
| Agent speaks | 0/10 | 0/10 |

The later suspicion is not a guaranteed deduction. This experiment tested the initial roleblock line,
not the causal effect of every component in the completed engine.

A follow-up changed the carried-forward strategy note while retaining the injection. With a neutral
note, the agent spoke in 9/20 samples versus 3/20 with its existing “stay quiet” stance. This small
screen suggests a separate behavioural obstacle: new knowledge can be absorbed without dislodging an
old plan. It does not establish a general fix for that obstacle.

Other screens reinforce the same boundary:

- **Vote mistakes persisted.** In an investigator's vote case, the healer still received 33/100 votes
  across four injection/placement variants. Correcting a misleading moderator closing line reduced
  healer votes from 9/25 to 5/25 in a follow-up comparison. At that size the difference is suggestive;
  it is not an isolated estimate of the engine's benefit.
- **Placement had no clear winner.** Screens on the four acceptance cases (3 and 10 samples per case
  per arm), then a 2×2 on the investigator's vote case alone (25 per arm), did not establish a
  reliable before-note versus after-note effect. The implementation uses before-note; it should not
  be described as a demonstrated behavioural solution.
- **Evil cover lines looked useful.** With revised role-card advice held constant, one screen of 41
  pressured evil turns, two samples each (82 per arm), recorded 44 role claims and no denials with a
  cover line, versus 36 claims and four denials without it. Different judges labelled the arms, so
  the counts are exploratory.
- **A true extra line was dropped.** Summarising what competing role claimants had reported did not
  improve pooled voting in a small screen and moved one target game's votes the wrong way. More
  information is not automatically more useful to the model.

The only whole-game comparison bundled revised evil role cards with deduction lines: wolves won
3/8 paired games versus none before. The [roles report](../roles/report.md) describes it. The engine's
contribution cannot be separated from the cards in that comparison. **No paired town-side whole-game
A/B or post-engine factual-error rate has been measured.**

Two further limits apply to all of the above. The screens were labelled blind by Claude subagents in
chat sessions (the thinking-budget and summary screens by Sonnet 5.5 in a batch), and agreement
between judges was not measured. And one level has never fired: the explanation branches for a
claim the morning leaves open produced no line on any of the 278 census turns. Their conditions are
real but rare; they are tested like every other rule and cost nothing when silent.

## Sources and implementation pointers

**Version.** This revision describes the implementation at `588a3273` (2026-10-26; since `ccaec2f6`,
the previous pin, the deduction code is unchanged and one test comment was corrected). Historical experiments keep their original models,
prompts and configurations; they are not all measurements of this snapshot.

- [Factual-error report](../../evaluation/factual_errors/report.md): motivation, definitions, earlier
  prompt results and diagnosis workflow.
- [Experiment log](experiment_log.md): observed failures and the thinking, summary, injection and
  private-note experiments.
- [Deduction catalogue](deduction_catalogue.md): detailed rules, owner decisions and build record.
- [Seat view](../../../Agents/deduction/seat_view.py),
  [solver](../../../Agents/deduction/candidates/solver.py),
  [continuation rule](../../../Agents/deduction/candidates/continuation.py),
  [conditional deductions](../../../Agents/deduction/conditionals/__init__.py), and
  [block assembly](../../../Agents/deduction/blocks.py): implementation entry points.
- [Deduction tests](../../../tests/engine/deduction/),
  [role-assignment oracle](../../../tests/factories/role_assignments.py), and
  [random-night generator](../../../tests/factories/random_nights.py): verification machinery.
- Recorded studies: `data/deduction_injection/`, `data/deduction_block_census/`,
  `data/deduction_placement/`, `data/deduction_placement_n10/`, `data/deduction_ac2_2x2/`,
  `data/deduction_ac2_closing_fixed/`, `data/solver_census/`, and the sibling gameplay datasets
  `../data/evil_cover_screen/`, `../data/evil_cover_games/`, `../data/counter_claim_votes/`.
