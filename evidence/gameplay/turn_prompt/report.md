# The turn prompt: what an AI seat reads, and what it must answer

The turn prompt is the interface between the game engine and an AI player: it supplies the player's
information and asks for a discussion message, vote or night action. The central problem is factual
reliability. An agent can invent a check, misread a vote or reason from the wrong surviving roles even
when the relevant information is somewhere in its prompt.

The design therefore makes engine facts explicit, separates them from player claims and summaries,
and asks for structured answers that code can validate. Some changes helped in the tests recorded
here. The strongest planned comparison was the July board-and-reads bundle: errors fell from **48%
to 30% across 100 selected, error-prone contexts** in the nine-seat game. That is a replay result,
not a whole-game error rate. Later changes mostly address individual failures; they do not establish
that today's full prompt plays better than an earlier version.

This report first explains [the current turn](#a-turn-today), then groups
[the decisions and evidence](#decision-index) by the problem they address. It closes with
[implementation checks](#how-it-is-checked), [limits](#what-is-not-established) and
[reasons to revisit the design](#when-to-revisit-the-design). The detailed history is in
[the experiment log](experiment_log.md), [the July validation plan](validation_plan.md) and
[the October investigation](../discussion_evidence.md) §6–8.

**Version and scope.** The code described here is at `588a3273` (2026-10-26). It was checked against
`ccaec2f6`; since then the seed model catalogue was brought in line with the live one, and comments
and docstrings were corrected. Results belong to the models, seat counts and prompt versions named
with each test; most predate this version. The nine-seat game ran until 2026-10-09 and the ten-seat
game since.

## The problem

Each AI player makes one model call per turn: a discussion line, a vote, or a night action. The model
decides what the player says and does. Everything the model knows about the game, it learns from that
one prompt, and everything the game learns from the model, it reads from the structured answer.

The design has four requirements:

- **The information the seat needs, stated clearly.** A fact that is present but easy to
  misread can cause the same errors as a missing fact. The October investigation found both
  (decisions 2 and 3).

- **Nothing the seat may not know.** Who may see what is defined and checked in
  [agent_boundaries](../../agent_boundaries/report.md#1-the-guarantee-current-contract); this page does
  not restate it.

- **An answer code can use.** The scheduler, the claim ledger and the vote count all read fields of
  the answer, so it must parse, and its checkable parts must be fields, not prose.

- **A reusable opening to reduce input cost.** Ten seats read the same rules and the same transcript
  many times a day. If every prompt opens with the same text, the provider can serve that part from its
  cache.

Two distinctions shape the design:

- **Rules, tactical guidance and learned lessons serve different purposes.** The prompt supplies
  rules, facts and role guidance; retrieved memory supplies lessons from earlier games. Decision 6
  removed prescribed suspicion cues such as evasiveness. It did not remove all tactical guidance:
  decision 7 describes advice that remained in the role cards.

- **Facts are computed by code; judgement is the model's.** The engine writes
  the death record, the roles not ruled out by revealed deaths, each seat's night history and the
  deduction engine's conclusions. The model
  supplies the reads, the argument and the choice.

---

## A turn today

A turn has three parts: a shared record of the game, information specific to the seat, and a
structured answer. Here, a **seat** means one player controlled by the model; a **read** is that
player's current assessment of another player.

### The order of the prompt

Every seat turn, of every kind, is built in the same layout (`Agents/prompts/layout.py`). A
discussion turn reads:

```
system   the rules of this game's cast, and how to keep facts, claims and guesses apart
user     == Previous days ==            the record of earlier days (the game master's record,
                                        the claim ledger, the accusations)
         the deduction engine's public lines, when it has any
         == Today's discussion ==       today's published lines, the same for every seat
         =========================      ← the cache boundary
         == Dead so far ==, == Roles still in play ==
         the role card: strategy, identity and framing, tone (and voice), the answer format
         the reads instruction; "Day 3 discussion."
         the seat's private facts: the living players, uses left, its own night record
         the round's rules, and the turn's brief
         the seat's own deduction lines, any lessons from memory, its private strategy note
         the standing speaking rules
```

Votes and night actions use the same parts below the boundary, in a slightly different order. A
wolf's prompt adds the pack's roster and its night chat. On night 1, eligible seats also receive a
randomly drawn default target (decision 5).

**Why this order.** Everything above the boundary is identical for every seat and every kind of call
at the same moment of the game. A vote, a night action or another seat's turn can therefore read from
cache what an earlier call wrote. Below the boundary sits everything that differs by seat or call, in
rough order of how often it changes. The dead roster sits below the boundary because it changes at the
vote, between a day's turns and the night after it. The cost evidence is in
[the caching report](../../caching/report.md) §3.2 and §4.3: in paired games the layout cut GPT-6
Luna's cost per call by 28%, and left Haiku's unchanged.

The layout has a price in what the seat reads first. The role card, with its strategy and cautions,
now comes after the transcript instead of before it (decision 14).

### The board facts

Every call, the wolves' night chat included, carries two public lines below the cache boundary
(`Agents/prompts/layout.py::BOARD`; `Agents/prompts/night.py::_night`):

- **The dead**, each with the role revealed at death and when they died: "player_8 (trailseer, night 1),
  player_9 (sigilist, lynched day 2)" (`Agents/prompts/prompt_formatters.py::format_dead_roster`).
- **The roles still in play**: the fixed public cast minus every revealed death
  (`format_alive_roles`). A body whose role was hidden subtracts nothing, so the line says so in words:
  "(one of these is dead: a body whose role is hidden)".

The seat's own facts come with its role card. **The uses it has left** appear under the name its card
uses: checks, watches, bullets, sigils, conceals
(`Agents/prompts/prompt_inputs.py::build_agent_prompt_input`).
**Its own night record** is written by the engine, one line per night, as a past action of the seat's:
"Night 2 (last night): you checked player_5. player_5 reads Not suspicious."
(`prompt_formatters.py::format_night_actions`). A night with no action says why, to distinguish a
skipped action from a result the seat has not disclosed: "you chose not to act", "you had no checks
left"
(`_quiet_nights`). A wolf also gets the living pack with each wolf's role, and the pack's night chat.

How results are worded is a tested choice. The old line read *"Day 3: player_5 was revealed as
healer"*, which looked like a public death reveal; replayed, the investigator invented a check on every
sample (decision 2). Every result now names the night, marks the previous night "(last night)", and
says "you checked".

### The record of past days

A seat never sees an earlier day's discussion again. It reads earlier days in three labelled blocks,
in order of how far to trust them (`prompt_formatters.py::format_day_summaries`):

1. **The game master's record**: the engine's exact announcements of each night and each vote.
2. **The claim ledger**: every role claim and claimed night action, per player and across days, built
   by code and checked against the record. A check reads "Record: player_9 was revealed as
   illusionist, as claimed".
3. **The accusations**: the day summary's account of who accused whom, each dead player tagged with
   the role revealed.

The labels tell the model which source to trust when the accounts conflict. How the
summary is written, how the ledger checks claims, and how both have been tested is in
[the day-summary report](../../extraction/day_summary/report.md).

### What the seat must answer

Each turn answers one schema, filled with the roles this game dealt
(`Agents/schemas/lineup_output.py`). Every seat turn opens with the same fields, in this order
(`TurnOutput`):

```
reads                  one per living player other than itself: player, why, suspected_role, confidence
strategy_verdicts      follow / override / not_relevant, one per numbered lesson shown  (only if shown)
memory_applicability   fully / partly / does_not_apply, one per numbered observation    (only if shown)
updated_strategy       the seat's private note, shown back to it on its next turn
… then the turn's own fields
```

A discussion turn then adds `pass_turn`, `message`, `claim`, `claimed_night_actions` and
`addressed_targets` (`DayDiscussOutput`). A vote adds `vote_target`, and each night role one target
field of its own, such as `investigator_target` with the value `no_check` for keeping a check.

- **Field order is intended to put assessment before action.** The schema places reads and the
  private note before the message, vote or target. Earlier tests found that changing output order
  could change actions. The model does not always follow the requested order, however, and today's
  order has not been tested for message quality (decision 10).
- **Every field the turn shows is required.** A seat that may decline gets a boolean (`pass_turn`) or a
  sentinel value (`abstain`, `no_check`, `hold_fire`), never an optional or empty field (decision 11).
  The two verdict lists are the exception: they default to empty and are removed from the schema of a
  turn shown no lessons (`Agents/turn/action_space.py::output_schema_for_memory_shown`).
- **The schema defines legal targets.** The target field of a vote or night action
  lists only the players that seat may target, and a reply naming anyone else fails validation
  (`action_space.py::output_schema_with_legal_targets`).
- **Claims are fields.** `claim` is the role the message claims, or `none`; `claimed_night_actions`
  lists each past action the message newly states, in fixed words (an action, a night, a target, a
  result such as `suspicious` or `no_visitors`). The claim ledger reads these fields before it reads
  the day summary (decision 13).
- **Speech-act tags.** `addressed_targets` records whom the message addresses, as a form (question,
  response, mention) and a stance (accusation, defence, agreement, neutral). The scheduler decides who
  speaks next from these tags; that is described in [the discussion report](../discussion/report.md),
  decisions 8–10.

### Example: an investigator's discussion turn

This is the user message of an investigator's day-3 discussion turn, as the code renders it. The
board is the fixed test board of the exact-prompt golden (`tests/fixtures/day_discuss_prompt_golden.json`),
rendered through the real turn node, not a played game. The rules in the system message, most of the
role card and the answer format are cut, marked "…":

```text
== Previous days ==
-- The game master's record (exact; it outranks anything a player or a summary says) --
Nothing announced yet.

-- Accusations in the day discussion (a summariser's account of what players argued; claims, not facts) --
[Day 2]
player_9 was lynched on a 4-3 vote.

== Today's discussion ==
game_master: Night of day 2: player_3 was attacked by the wolves but was saved by the healer!
player_4: player_2, why abstain?
=========================

== Dead so far (public) ==
player_8 (trailseer, night 1), player_9 (sigilist, lynched day 2)

== Roles still in play (fixed cast minus revealed deaths) ==
1 investigator, 1 sentinel, 1 vigilante, 1 healer, 1 chanteuse, 1 illusionist, 1 serial killer, 1 speculator

## INVESTIGATOR (Core Strategy)
…
You are player_3, the investigator.
…
Before your decision, record your current read — one entry each for: player_1, player_2, player_4, player_5, player_6, player_7, player_10 (best-guess role, or 'unclear').

Day 3 discussion.

Surviving players: player_1, player_2, player_3, player_4, player_5, player_6, player_7, player_10
Checks left: 0
Your night actions (private; recorded by the game master, and only you know them):
Night 1: you checked player_7. player_7 reads Suspicious. Only a wolf reads Suspicious in this game, so player_7 is a wolf.
Night 2 (last night): you checked player_5. player_5 reads Not suspicious. So player_5 is not a wolf, but player_5 could still be the Serial Killer or the Speculator.

You were directly addressed by player_4. Respond to them this turn — answer their question or defend against their accusation. Do not stay silent. …

== Worked out for you ==
…
- The Speculator is alive and is one of player_1, player_2, player_4, player_5, player_6 and player_10.

Adaptive Strategic thinking:
    You have a private strategy note from your previous turns (your own working notes: they can be
    out of date or wrong, and the game master's record and the transcript outrank them):
    player_3's note: watch player_2.
…
```

The example illustrates three design choices. The board lines are computed, not summarised. The night record
names each check as the seat's own action and by its night. And the sentences after each result ("Only
a wolf reads Suspicious in this game, so player_7 is a wolf") are the deduction engine's: what follows
from the seat's own results with certainty
([the deduction report](../deduction/report.md) explains how those lines are made and tested).

### Model settings, validation and retries

Each turn is one structured-output call to the game's model. The default has been Claude Haiku 5.5
since 2026-10-15; a game on the website runs on the model the player chose
(`Agents/llm_factory/accessors.py::DEFAULT_GAME_MODEL`, `_game_model`). Temperature is 1.0 unless set
otherwise (`get_llm`). Each model's settings live in the model catalogue, a database table edited
without a deploy (`scripts/model_catalog.py`); the code holds only its seed
(`Agents/llm_factory/catalog.py::SEED_MODELS`). As read from the live catalogue on 2026-10-26, Claude
Haiku 5.5 runs every seat turn at thinking `low`, with the schema written as text in the prompt and the
reply validated in code (`json_mode`, since 2026-10-14), and has no rescue model. The seed in code has
matched the live row since 2026-10-26 (`d424d0f9`).

**Why the schema is not enforced on Haiku.** An enforced schema counts as the start of the prompt for
caching, and a vote's or night action's schema lists that seat's legal targets, so no two seats could
share the cached transcript. Written as text after the cached part, the same schema still rejects an
illegal target in code. In the trial, unenforced replies failed 1 time in 412 Haiku calls, and in paired
games votes and night actions went from never reading the cache to reading most of it; on Haiku the cost
per call stayed level because it reasoned more ([caching log](../../caching/experiment_log.md) §12, §13, §15).

A reply that breaks the schema is asked again, with the schema enforced by the provider where the
first call left it unenforced. If that fails and the model has a rescue model, the rescue model gets
one try (Haiku has none). A discussion turn that still fails becomes a pass, and a vote or night action
becomes a random legal move (`Agents/turn/agent_player.py::run_agent`).


---

## The decisions behind it

The decisions follow four steps: supply clear facts, guide the turn, structure the answer, then tune
layout and thinking effort. Each records the reason for the choice, the evidence available and its
limits. Dates and model names matter: these are studies of different versions, not one cumulative
test of the current prompt.

### Decision index

| Question | Decisions | Evidence and remaining uncertainty |
|---|---|---|
| What facts is the seat given? | [1–5](#decision-1): the board, results worded as own actions, the own night record and labelled record, rules stated in full, the night-1 lot | One planned nine-seat comparison (July); single-turn and few-turn replays since |
| What is the seat told to do? | [6–9](#decision-6): suspicion cues removed, tactical guidance reviewed, short per-turn briefs, sentences tried and not kept | Small studies and replays; one rewrite never A/B tested |
| What must the seat answer? | [10–13](#decision-10): field order, required fields, numbered memory, claims as fields | May–July tests on flash-lite; today's order changed for Claude, its quality effect unmeasured |
| How is the prompt laid out? | [14](#decision-14): the shared-prefix layout | Cost measured in paired games; one unresolved lead on vote quality |
| How long does the seat think? | [15](#decision-15): thinking level per model | Large replay effects on two models; Haiku's setting is an open decision |

### What the seat is given

<a id="decision-1"></a>

#### 1. Show the board and ask for a read of every player (shipped 2026-07-09).

- *Instead of:* leaving agents to work out who had died, and as what, from the game master's prose in
  the transcript.

- *Why:* the July census of 50 nine-seat games found a role-fact error in about 3% of public messages,
  4% of private notes and 9.6% of night-action notes. The commonest error was survivor arithmetic,
  such as hunting "the remaining wolf" when no wolf was alive
  ([factual_errors](../../evaluation/factual_errors/report.md), step 1).

- *What the first test showed:* printing the facts alone did not stop the error. Replaying the four
  errors confirmed by an earlier hand count, three never recurred in any arm, including the arm with no
  change; the fourth recurred with a correct "roles still in play" line in the prompt (T1b, 72 calls,
  2026-07-07). The board was retained as an explicit reference, and the next test added reads: a forced
  one-line read of every living player, written before the action and shown back the next turn.

- *What the reads cost and gave* (T2 and T3, flash-lite, 2026-07-07: 60 frozen decisions, 40 day
  votes and 20 night actions, in the two arms without reads; the 40 votes alone in the two arms with
  reads; 200 calls in all): every output parsed; the verdicts on memory kept full coverage; the reads added about
  60% output tokens per call (375 to 599), the board added no output tokens. Wolves read their
  packmates as wolves 9
  times in 9. Reads covered 0.84–0.85 of the living players; listing the expected names in the
  instruction raised that to 0.93. A coverage monitor logs any turn below 0.85 and never retries
  (`Agents/turn/eval.py::_reads_coverage`).

- *The adoption test* (T1c, 2026-07-08, nine-seat, flash-lite): error-prone turns from the census were
  regenerated under the old prompt and the bundle, one sample each, and judged by the census reader.
  The first run pointed the right way and showed that the "clean" control turns were error-prone too,
  so the hypothesis was reworded around all error-prone contexts and written into the plan before the
  second run. On 100 fresh contexts: **48% bad on the old prompt, 30% on the bundle; 29 pairs better
  and 11 worse; one-sided sign test p = 0.003.** It cost about $3.

- *Cost accepted:* about 60% more output per call, and a read field the model fills even when it has
  nothing to say ("unclear", "unchanged").

- *How far it reaches:* the rates describe turns chosen because they went wrong, not whole games; no
  hand read of the verdicts is recorded; and vote turns were rebuilt with the vote's own result in
  view. That makes those prompts unlike a real vote and limits interpretation of both arms
  ([factual_errors log](../../evaluation/factual_errors/experiment_log.md) §2). The bundle shipped
  on day, vote and the four single-actor night turns; the wolves' night was left out because the test
  never covered it. Today the board appears in every call type, the pack's chat included.

<a id="decision-2"></a>

#### 2. A result is worded as the seat's own action on a named night (2026-10-03).

- *The failure:* in game `832404e9` (nine-seat, `gemini-3.5-flash-lite`), the investigator announced
  "I investigated player_9 last night, and they are the remaining wolf". It never checked player_9; the
  village voted player_9 out 4 to 1, a villager, and the serial killer won. Its prompt listed its real
  night-3 check as *"Day 3: player_5 was revealed as healer"*. Player_5 had also died that night with
  the healer role announced, so the line read as public news.

- *The test:* the exact turn was rebuilt from the game's saved state and sampled 20 times under each of
  four variants ([discussion_evidence](../discussion_evidence.md) §6.2):

  | Variant | Invented a check | Reported its real check |
  |---|---|---|
  | As played | 20 / 20 | 0 / 20 |
  | Results reworded | 0 / 20 | 20 / 20 |
  | Previous note removed | 20 / 20 | 0 / 20 |
  | Reworded and note removed | 0 / 20 | 20 / 20 |

  The rewording changed two things at once, the night dating and "you investigated", and the test
  cannot say which mattered. It is one turn from one game: it shows the old wording can make invention
  near-certain in that situation, not how often the situation arises.

- *The fix:* every result written as *"Night 3 (last night): you investigated player_5, who is the
  healer"*, in every game, not behind a switch, because the old wording was a correctness bug. The
  ten-seat investigator learns only "Suspicious" or "Not suspicious", so today's line reads "Night 2
  (last night): you checked player_5. player_5 reads Not suspicious." It keeps both properties the fix
  introduced.

<a id="decision-3"></a>

#### 3. Restore missing history and label each source (2026-10-03 and 04).

- *The failure:* in game `46355b89` (nine-seat, `gemini-3.5-flash-lite`), town won on a premise a wolf
  had leaked and town had rejected the day before. Agents cited private or missing information as
  public, and a vote *for* a player was read as support.

- *What was found:* a code review of the path from engine events to prompts found 12 places where a
  fact was lost or blurred on its way to a seat (2026-10-03). Among them: the healer had no record of
  its own protections, a vote overwrote a private note it never showed, and engine facts looked the
  same as a model's summary once rendered. A check the next day found 8 addressed and 4 only partly
  ([factual_errors log](../../evaluation/factual_errors/experiment_log.md) §8–9). The fixes included a
  private night record for every night actor, written by the engine; the three labelled blocks of the
  record; "voted to eliminate" in place of "voted for"; and the vote turn shown the note it replaces.

- *Evidence:* on the nine-seat replay set (89 cases, 3 samples each, memory off, `gemini-3.5-flash-lite`
  at its then-default thinking level, which produced no reasoning), bad samples went from 97 to 82 of
  267, with 24 cases better and 14 worse (p = 0.14): an improvement in this sample, with substantial
  uncertainty
  ([discussion_evidence](../discussion_evidence.md) §6.5).

- *Cost accepted:* none measured. "Addressed" in the check describes the wiring, not that the model
  now follows it.

<a id="decision-4"></a>

#### 4. State missing rules and rank them above player claims (October).

- *The failure:* in the ten-seat games read in full in October (on gemini-3.5-flash-lite,
  gemini-3.5-flash and GPT-6 Luna), invented facts had become rare. The commonest player error was a
  wrong inference about what an ability observes: a watch read as clearing the watched player, an
  empty watch read as an empty house. Games also turned on rules the engine applied and the prompts
  did not state. An illusionist that carries its own kill leaves no trace, and four players asserted
  the opposite and voted out the real trailseer, whose empty trail was right (game f02,
  gemini-3.5-flash). In all four GPT-6 Luna games a player argued the sentinel should appear in
  its own visitor list, and in three the real sentinel conceded and was voted out
  ([discussion_evidence](../discussion_evidence.md) §8.4). In the first Haiku game, "I visited nobody"
  was answered as "no one visited you" (§8.6, 2026-10-12).

- *The fix:* the missing rules written into the rules block or the role card, and a closing line that
  the rules are exact and a player's statement of a rule is a claim like any other. The visit rule now
  says which way a visit goes and what a watch and a follow cannot see.

- *Evidence, from replays of the failing turns:*
  - The visit rule, Haiku 5.5 at effort low, 18 frozen turns from game `403f4dbc`, 5 samples each:
    messages reading a visit the wrong way round fell from 16 of 35 to 5 (§8.6).
  - The sentinel sentence on GPT-6 Luna: the real sentinel conceded a false rule 10 times in 10
    before, 0 after (§8.4).
  - The illusionist sentence on the f02 turns: gemini-3.5-flash went from 10 of 10 to 7 of 10, and
    flash-lite stayed at 10 of 10. The line ranking the rules above a player's statement took
    gemini-3.5-flash to 4 of 10; flash-lite stayed at 10 of 10. The later speakers on those turns
    repeated a false rule already in the transcript, suggesting that correcting the rules alone may
    not stop a false account already repeated by players (§8.4).

- *Cost accepted:* a longer rules block, in the system message every call shares.

- *Interpretation recorded* (§8.5, item 7): stronger reasoning does not compensate for missing rules;
  it can still produce confident conclusions from an incomplete description. These cases do not
  establish how that risk changes with model strength.

<a id="decision-5"></a>

#### 5. When there is no reason to choose, the engine supplies the chance (2026-10-07).

- *The failure:* in the nine-seat games, night-1 choices fell on the lowest seat. Over 28 earlier
  games the investigator checked `player_1` on night 1 in 21, the serial killer hit it in 26, the
  healer protected it in 25; in the four test games of 2026-10-07 the investigator checked it in all
  four. The answer example in every prompt named `player_2`, and on day 2 across the 32 games
  `player_2` drew 40 accusation tags and 41 votes, against a median of about 8 and 12 for the other
  seats ([discussion_evidence](../discussion_evidence.md) §7.5).

- *The obvious fix, and why it failed:* shuffling every player list. On 32 recorded boards (192
  calls on `gemini-3.5-flash-lite`), the target was still the lowest-numbered other seat in 95 of 96
  shuffled calls, against 94 of 96 in seat order. In this replay, changing list order did not remove
  the preference for low seat numbers.

- *The fix:* on night 1 only, the engine draws a default by lot, seeded by the game, the night and the
  player, and the prompt offers it: "a lot has been drawn for you: player_N. Take it unless you have a
  reason to prefer someone else." (`Agents/prompts/prompt_inputs.py::night_one_lot`). The pack draws one
  lot; the vigilante draws none, to avoid encouraging a shot without evidence. The example read names no
  seat (`"player": "<exact player_id>"`).

- *Evidence,* on the same 32 boards (192 calls): without the lot, seat 1 took 78 of 96 night-1
  actions, and on 16 of 32 boards the check, the protection and the kill fell on one player. With it,
  the agents took the lot in 95 of 96 calls, the actions landed on all nine seats (6 to 16 each), and
  no board had all three on one player. No read copied the placeholder in 192 calls.

- *The rule it set for every prompt since:* an example must not name a legal answer, and a choice with
  no evidence behind it needs its randomness from the engine.

### What the seat is told to do

<a id="decision-6"></a>

#### 6. Remove prescribed suspicion cues (June 2026).

- *The failure:* the role prompts had told agents to treat evasiveness and deflection as tells. Agents
  policed each other's tone and silence instead of playing, and one recited the villager's block
  ("playing too passively is also a classic way f[or wolves to hide]"). The memory extractor, which
  learns lessons from games, risked writing that prescription into the lesson store.

- *The fix:* the prescribed suspicion cues were stripped from every role's strategy block, and a
  clause added for
  when nothing is concrete: do not manufacture suspicion from tone or volume, prefer a test or a
  contradiction ([prompt_boundary](prompt_boundary/experiment_log.md)). The same clause is in today's
  discussion prompt (`Agents/prompts/day_discuss.py::DISCUSSION_SILENCE_RULE`).

- *Evidence* (`gemini-3.1-flash-lite`, eight seats, memory off, 2 games per arm, unpaired): messages
  with tone-policing words fell from 24 of 119 (20.2%) to 8 of 79 (10.1%). Canned openers on day 1 fell
  from 10 of 19 to 2 of 14. The counts are substring matches, a lower bound, and the policing drop is
  confounded with an easier board in the second pair of games.

- *Why it was kept anyway:* the change was kept on principle, not on the counts. Prescribing which
  behaviours count as suspicious would build an answer into the prompt that the
  memory experiments were meant to investigate. This is a narrower boundary than removing all
  strategic advice from role cards.

<a id="decision-7"></a>

#### 7. Review tactical advice against observed play (2026-06-17).

- *The audit:* every tactical claim in the hand-written role prose was checked against metrics the
  games already tracked ([prompt_claims_audit](prompt_claims_audit/experiment_log.md); the nine-seat
  games of the v6 memory A/B).
  - *The investigator's "conceal your findings, let consensus build":* raised a concern about
    withholding useful evidence. In those games the
    investigator voted for the wolf it had confirmed, but asserted the confirmed read in only about a
    third to two thirds of cases, mostly naming the wolf without saying it had checked it. The block
    was rewritten as a two-sided trade-off: a result helps only once the town acts on it, and revealing
    makes the investigator a target. Today's card keeps that wording
    (`Agents/prompts/roles/investigator.py::DISCUSS_FRAMING`).
  - *The wolves' "blend your vote with the majority":* consistent with a positive association in the
    recorded games. Where the wolves voted with the
    majority at least 80% of the time, they won 38% of games (n = 50), against 25% elsewhere (n = 72);
    the correlation over the 122 games was r = +0.16, p = 0.07, consistent with an earlier r = +0.20,
    p = 0.003 over 220. Both are correlations.

- *Left unchanged on purpose* (2026-10-03): a later review proposed removing "the public voting record
  is the most durable hard evidence you have" and the blend line, to push talk away from votes. Both
  were kept on the grounds that voting records remain useful and majority-blending showed a positive
  association with winning. The effect of removing either line on play quality was not tested
  ([discussion_evidence](../discussion_evidence.md) §3, P4). Both lines are in today's
  role cards.

- *Not established:* the investigator rewrite was drafted for an A/B that is not recorded as run. In 28
  later nine-seat games (2026-09-17, `gemini-3.5-flash-lite`) the investigator claimed in 24, which is
  an outcome count with no comparison, on a different model.

<a id="decision-8"></a>

#### 8. Explain why the seat is being asked to speak.

- *The firing brief* (June): a seat picked to answer someone is told "You were directly addressed by
  player_4. Respond to them this turn" (`prompt_inputs.py::_firing_brief`). The brief was intended
  to keep the seat focused on the question or accusation that triggered its
  turn, instead of producing another generic line. Its role in the
  scheduler is in [the discussion report](../discussion/report.md), decision 10.

- *Two lines added after the first Haiku game* (2026-10-12, ten-seat, Haiku 5.5 at effort low; replay
  of 18 frozen turns, 5 samples each, §8.6):
  - The reply brief now asks the seat to answer what is new and point back to what it already said.
    Restated or re-asked replies went from 27 of 30 samples to 23. The framing changed ("As I said");
    the content mostly did not.
  - A town seat on a voting day's open floor is asked to decide its vote now and, if it has not said
    why, to say it (`day_discuss.py::TOWN_VOTE_REASON_RULE`). A first wording moved passes from 24 of 25
    to 23; the second, asking the seat to decide now, to 16 of 25.

- *Why after the transcript:* the brief changes every turn, so above the boundary it would break the
  cache for every seat.

<a id="decision-9"></a>

#### 9. Sentences tried and not kept.

Each of these was tested in a replay and removed. They show why a plausible instruction still needs
testing: some did little, and others improved
one case while worsening another.

- *Compare candidates in each read* (2026-10-16, Haiku 5.5, 11 frozen votes from game `403f4dbc`, 10
  samples each): on the ballot it was written for, the vigilante's vote for the real threat fell from
  7 of 10 to 0 of 10 (Fisher p = 0.003); it abstained in 6 and voted the real sentinel in 3. Where
  evidence was strong it helped: the
  day-4 reads cited the decisive vote in 11 of 30 samples against 2 (p = 0.01). Vote output grew from
  960 to 1,297 tokens. Not adopted ([discussion_evidence](../discussion_evidence.md) §8.7).
- *Tag each ballot with what its target turned out to be* (same study): per-case results moved both
  ways, more than any effect tested, and the reads cited the vote no more often. Removed.
- *Cite the record exactly, and the votes laid out per player* (2026-10-04, nine-seat): the citation
  rule left vote misquotes at 24 before and 24 after, and the per-player layout moved bad messages from
  26% to 21%, within noise. Both were reverted. The detail is in
  [the gameplay report](../report.md), problem 1, which draws the lesson: a request to cite produces
  prose that nothing checks.

### How the answer is structured

<a id="decision-10"></a>

#### 10. Put reads and notes before the action.

- *How it was found* (May–June 2026, flash-lite; [the log](experiment_log.md) §3 and §7):
  - Asking the model which retrieved strategy it adopted *after* its action produced labels that read
    as rationalisations. Moving the field first raised the judge's adoption-accuracy score from 4.00
    to 4.38 and its action-quality score from 3.97 to 4.47, both on 1–5 scales
    ([strategy adoption report](../../memory_system/strategy_adoption/report.md)). The action changed
    when the reporting field moved, suggesting that the field influenced the decision rather than
    merely describing it.
  - The vote came before the reasoning. Moving the reasoning ahead of the vote changed nothing on its
    own. Together with a required verdict on each retrieved memory, it raised the coherence between the
    stated reasoning and the vote cast from 75% to 92.5%. Delivering the verdict instruction in the
    prompt body, not the field description, raised verdict coverage from 0.27 to 0.97.

- *The reads joined in July:* in the ordering arm of T3, reads before the strategy note tripled how
  often a seat overrode a strategy suggestion (0.06 to 0.17), but the reads were judged less
  substantive when the
  seat had no earlier reads to update. Reads-first shipped provisionally.

- *Changed for Claude* (2026-10-13): with the schema sent as text instead of enforced, Haiku 5.5 kept
  the schema's order on only 15 of 24 real turns, and every mismatch put `reads` first. The recorded
  plausible cause is the prompt's reads line, which asks for the reads before the decision. Telling
  the model to keep the schema's order gave 13 of 23. The schemas were reordered to reads,
  verdicts, note, decision, and the same 24 turns then kept the order 24 of 24
  ([caching log](../../caching/experiment_log.md) §12). That order is today's.

- *Not established:* the July tests had the verdicts before the reads. Whether moving the verdicts
  after the reads changed message quality was not measured.

<a id="decision-11"></a>

#### 11. Every field is required; "no" is a value, not a missing field.

- *Why:* flash-lite silently dropped nullable fields, which made the absence of a field ambiguous:
  was the action intentionally declined, or was the
  output incomplete? Silence became a required `pass_turn` boolean, abstention the value `abstain`, and each
  optional ability its own keep value (`no_check`, `hold_fire`). The rule is recorded from the June
  schema work and repeated in the code (`lineup_output.py::NightActionClaim`); no failure rate for
  optional fields is recorded.

- *`pass_turn` comes before `message`.* The recorded reason is that a model that has already written a
  message will not then decline to send it. That reason was not tested.

- *The verdict exception* (2026-10-14): over 20 Haiku games (3,118 seat decisions), 426 turns that were
  shown no lessons still returned verdicts, typically "lesson 1: follow", copied from the answer
  example. A turn shown no lessons now gets neither the verdict fields nor their example
  ([caching log](../../caching/experiment_log.md) §16).

<a id="decision-12"></a>

#### 12. Memory items are numbered, and their instructions appear only with them.

- *Numbers, not keys* (May): strategies were first keyed by UUID, and flash-lite corrupted the
  36-character strings about 30% of the time. Items are now numbered from 1 in the prompt; an index
  out of range is logged and skipped, where a corrupted key would have credited the wrong lesson.
- *Only when shown* (2026-10-04): the memory instructions were about 1,200 characters on every turn,
  spent on an empty list when memory was off. They now appear only when lessons are shown
  ([discussion_evidence](../discussion_evidence.md) §6.6). In a served game memory is the player's
  switch, and it retrieves strategy points only (`server/game/run_config.py::game_run_config`).

<a id="decision-13"></a>

#### 13. A seat states its own claims in fields (2026-10-17).

- *Why:* a summariser error is read by every later seat. In game e06 (ten-seat, flash-lite) the day
  summary turned "I was roleblocked last night" into a chanteuse claim; two players repeated it, and
  the real investigator was voted out holding a true result (§8.4). This motivated collecting claims
  directly from the speaker in fields code can check, rather than
  relying entirely on a summariser to infer them.
- *The fix:* `claim` and `claimed_night_actions` on every discussion answer, in the summariser's fixed
  vocabulary, so the ledger reads the speaker's own fields first and the summary only for a player who
  filled none.
- *Cost accepted:* more output per discussion turn. A human seat types free text and has no fields,
  so a human's claims still come from the summary.

### How the prompt is laid out

<a id="decision-14"></a>

#### 14. The shared-prefix layout (live 2026-10-14).

- *Instead of:* the earlier layout, which put each seat's role card in the system message and some
  seat-specific lines before the transcript, so two seats' prompts diverged early.
- *Why:* to let every seat and call type reuse the day's transcript from cache. The cost evidence is
  the caching report's ([§4.3](../../caching/report.md)): two paired games per arm, 28% less per call on
  Luna, no change on Haiku, where extra reasoning used up the input saving. The earlier layout is kept
  at the tag `prompt-layout-baseline`.
- *Observed participation:* under the new layout, from day 2 on, Haiku spoke on free turns about 53–54% of
  the time against 20–35% before (4 games against 6). One plausible reading is that the role card's
  cautions ("revealing your role could mark you as a night target") weigh less once they no longer sit
  in the system message ([caching report](../../caching/report.md) §4.5). The extra participation
  was treated as a benefit; participation alone does not establish better
  discussion.
- *An unresolved lead:* in the vote replay of
  [discussion_evidence](../discussion_evidence.md) §8.7 (Haiku 5.5, game `403f4dbc`), day-4 control
  votes were right 25 of 30 times on the code
  before 2026-10-12, 20 at the layout tag, and 13 on the current code, with the decisive vote cited in
  19, 12 and 2 of 30 reads. One plausible reading was that the layout moved "the public voting record
  is the most durable hard evidence you have" from before the ballots to after them. A later replay on
  one layout found the same votes right 9 of 30 times at Haiku's `low` effort and 28 of 30 at `medium`
  ([deduction log](../deduction/experiment_log.md) §2), showing that thinking level also matters on
  these cases. The studies do not establish how much of
  the earlier decline came from layout, thinking level or other changes; each uses one game.

### How long the seat thinks

<a id="decision-15"></a>

#### 15. The thinking level is set per model.

The thinking level is a setting of the call, not prompt text, but it also affects whether the model
uses the supplied information correctly. Its replay effects
were large enough to consider alongside wording changes.

- *gemini-3.5-flash-lite* (nine-seat replay set, 2026-10-04): at the then-default level the model
  reasoned for 0 tokens. At `medium`, bad samples fell from 82 to 27 of 267 (36 cases better, 4
  worse), at about 2.4 times the cost and 3.3 times the time per turn
  ([discussion_evidence](../discussion_evidence.md) §6.7). The catalogue now runs it at `medium`.
- *Claude Haiku 5.5* (ten-seat, frozen cases from two games): at `medium` against `low`, votes were
  right 98 of 160 times against 65 (12 cases better, 1 worse, p = 0.003); discussion turns did not
  change (47 against 49 bad of 115). A game would cost about $0.23 instead of $0.12. Moving votes to
  `medium` remains an open decision; Haiku runs every seat turn at `low`, votes included (the live
  catalogue, 2026-10-26; [deduction log](../deduction/experiment_log.md) §2). The result's home, as
  a lever against factual errors, is [the gameplay report](../report.md).

---

## How it is checked

| What | How | Result | How far to trust it |
|---|---|---|---|
| The exact text a discussion turn sends | Golden: every role's discussion prompt on a fixed board, rendered through the real node and compared byte for byte (`tests/engine/test_draft_preview.py`, fixture `tests/fixtures/day_discuss_prompt_golden.json`) | Pins the text; a change shows as a diff | Catches accidental change only. Covers discussion turns, not votes or nights |
| The rules block | The composed rules for two casts that deal every role, compared with rendered files (`tests/engine/test_game_rules_render.py`, `Agents/prompts/goldens/`) | Pins the English the model reads | As above |
| The layout | Every template opens with the shared system message and public record; the prefix is the same for every seat and call type; a held line reaches no prompt, not even its author's (`tests/engine/test_shared_prefix_layout.py`) | Structural assertions | Says nothing about play |
| The board, reads and lot | `tests/engine/test_dead_roster.py`, `test_player_reads.py` (field order, read targets exclude the seat, the alive-roles line), `test_night_lot.py` (the lot is another living player, stable on retry, varies across games, night 1 only) | Structural assertions | Implementation evidence |
| Reads stay private | Leak check `check_reads_isolation` in `tests/leak_test.py`, also run after every batch game | See [agent_boundaries](../../agent_boundaries/report.md) §3 | As that report rates it |
| Read coverage | A monitor logs any turn whose reads cover under 0.85 of the living players (`Agents/turn/eval.py`) | Logging only | Nothing reads the log routinely |
| Errors on known failures | The hallucination bench (`eval-hallucination-bench`), graduated from the July ship test | Decisions 1–4, 15 | 🟡: replays of chosen failures, not a rate ([factual_errors](../../evaluation/factual_errors/report.md), step 4) |

The test files named here passed on 2026-10-26. The suite is largely AI-written and not yet audited,
so this page names tests and what they assert, never a count.

## What is not established

- **No error rate on the ten-seat game.** The census rate comes from July's nine-seat game on the
  old prompt; the bundle comparison uses selected error-prone contexts. The ten-seat error
  comparisons use selected failures. Full-game observations and cost studies
  answer other questions; they do not supply a representative factual-error rate.

- **No test of today's prompt as a whole against an earlier one.** The July bundle was tested on its
  own; later studies cover particular changes or bundles on different models and selected turns or small
  game batches. Their results cannot be added up into an estimate of today's overall quality.

- **Small wording changes move single cases a lot.** In §8.7, adding true facts to the ballot lines
  moved per-case vote counts by up to five of ten samples in both directions. That is more than most
  effects tested on those cases, so a one-game replay can identify a local effect without
  establishing that it generalises.

- **The rules text is long, and some of it gets quoted.** Seats have recited rule sentences as
  arguments ("a follow only shows where someone went"), an open item in the
  [deduction log](../deduction/experiment_log.md) (R11). The rules also still say openings are played
  "in an order drawn at random that day", while the code publishes them in seat order (see
  [the discussion report](../discussion/report.md), "What is not established").

- **Today's field order and the unenforced schema were not checked for message quality** (decision 10).

- **The investigator rewrite was never compared with the wording it replaced** (decision 7).

## When to revisit the design

The criteria below are directions for a future comparison, not checks already run.

| Choice | Assumption to test | Evidence that would justify revisiting it |
|---|---|---|
| The reads (1, 10) | A forced read of every player still ties messages and votes to beliefs on today's models | A bench arm without reads shows no difference in errors or votes, with a worthwhile reduction in output cost (about 60% added in the July test) |
| The board and the own night record (1–3) | Facts the engine knows are best printed, not left to the model | A seat misreads a printed line, as the old results line was misread |
| Rules stated in full (4) | A longer rules block costs little and prevents misreadings | Rule sentences recited as arguments, or errors traced to a rule still unstated |
| The shared-prefix layout (14) | The role card after the transcript does not weaken how seats use the record | A vote-case set from several games, at one thinking level, shows the earlier layout voting better |
| Reads first, verdicts after (10) | The verdicts' position does not matter once reads come first | A memory-on bench comparison of verdict positions finds a difference |
| The thinking level (15) | Additional reasoning is worth its cost for some turn types | A broader vote comparison confirms the replay gain at an acceptable cost; discussion needs a separate comparison |
| Instruction-only fixes (8, 9) | A clearer instruction can improve how the seat uses available facts | A wording change improves a known failure in replay and the improvement also appears in full games |

For a revision, record the baseline commit, model, thinking level, seat count and sample, and judge
both arms with one judge in one run. Separate a turn's facts from its reasoning: a fix to one can move
the same error count as a fix to the other.

## Code and data

| Part | Code |
|---|---|
| The layout and the board | `Agents/prompts/layout.py` (`SHARED_SYSTEM`, `PUBLIC_RECORD`, `BOARD`) |
| The templates | `Agents/prompts/day_discuss.py::day_discuss_template`, `day_vote.py::day_vote_template`, `night.py::night_template`, `wolf_chat_template`, `carrier_template` |
| The rules block | `Agents/prompts/compose.py::preamble`, from `Agents/prompts/game_rules.py` and the role cards in `Agents/prompts/roles/` |
| Payload to prompt variables | `Agents/prompts/prompt_inputs.py::build_agent_prompt_input` (`_firing_brief`, `_discussion_stage_rules`, `night_one_lot`) |
| Rendering game records | `Agents/prompts/prompt_formatters.py` (`format_dead_roster`, `format_alive_roles`, `format_night_actions`, `format_day_summaries`) |
| Memory blocks and the strategy note | `Agents/prompts/memory/context.py` |
| Output schemas | `Agents/schemas/lineup_output.py` (`TurnOutput`, `DayDiscussOutput`, `DayVoteOutput`, the night outputs); `Agents/schemas/game_events.py::AddressedTarget` |
| Schema per turn | `Agents/turn/action_space.py` (`output_schema_with_legal_targets`, `output_schema_for_memory_shown`) |
| The call, retries and rescue | `Agents/turn/agent_player.py::run_agent`; `Agents/turn/pipeline.py::run_memory_informed_action` |
| Model, temperature, thinking level | `Agents/llm_factory/accessors.py`, `Agents/llm_factory/catalog.py::SEED_MODELS` |

| Record | Where |
|---|---|
| The build journey to July | [experiment_log.md](experiment_log.md) |
| The July tests (T1–T5) | [validation_plan.md](validation_plan.md); results in `validation/` (scripts frozen) |
| No strategy in the prompt | [prompt_boundary/experiment_log.md](prompt_boundary/experiment_log.md) |
| The tactical-claims audit | [prompt_claims_audit/experiment_log.md](prompt_claims_audit/experiment_log.md) |
| The October investigation | [discussion_evidence](../discussion_evidence.md) §6.2, §6.4–6.7, §7.5, §8.4–8.7 |
| The night-1 lot check | `../data/night1_target_bias/` |
| The Haiku replays | `../data/haiku_turn_replay/`, `../data/haiku_vote_replay/` |
| The layout's cost and the field-order trial | [caching report](../../caching/report.md), [caching log](../../caching/experiment_log.md) §12–16 |

*Written 2026-10-26; it replaces the July account in the log's §0.*
