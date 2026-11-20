# Making assessments explicit and testing how they shape decisions

*Level 2 · [Context engineering](../context_engineering.md) · separate revision for review, 2026-10-31*

## Page copy (draft)

When an agent made a poor decision, its short private note often gave too little explanation to
locate the failure. I wanted a record of the evidence it noticed, the lessons it considered and the
approach it intended to take, so I could compare that assessment with its action.

The answer therefore asks for a structured, explicit chain of thought: written assessments before
the decision. These fields make the stated assessment inspectable; they do not reveal the model's
complete internal reasoning. Getting them filled required changes to both the answer structure and
the instructions. Whether a fuller assessment helped required separate tests of the decisions.

Those tests used **replays**: recorded turns rebuilt from saved state and answered again under each
prompt version. Repeated samples show behaviour on those situations, not the frequency of a problem
across games. [Evaluation](../../evaluation/replays_and_games/replays_and_games.md) explains the method.

### What the written assessment needs to reveal

The assessment has three parts: **reads**, each giving another living player's suspected role,
confidence and a reason; **verdicts** on retrieved lessons or observations, when any are shown;
and a **strategy note** carried into the player's next turn. The message, vote or night action follows.
One recorded situation illustrates what those fields let me inspect.

A healer, player_8, whose night action protects one player, had been roleblocked on night 1; its
night record told it so, adding that it had "learned nothing tonight". By the middle of day 2 the
trailseer, player_3, whose ability shows where a followed player went, had said it followed player_7 to
the healer that night, and player_7 had admitted the visit without claiming a role. In this cast only
the Chanteuse, a wolf, can block, and a block is a visit. The healer passed all three of its turns
that day. A replayed answer from the turn after the admission shows what was—and was not—stated.

| Field | What the healer wrote (one replay sample of the frozen turn, the prompt as played) | What it let me see |
|---|---|---|
| Reads | player_3: unclear (low): claims trailseer; follow result on player_7 to player_8 is unverified but plausible · player_7: unclear (low): admits visiting player_8 on night 1, no role claim | The written read retained the reported visit and who claimed it. |
| Verdicts | none asked for: no lesson was shown on this turn | No retrieved lesson was supplied on this turn. |
| Strategy note | "I was roleblocked night 1 and have no results. … Stay quiet unless addressed, watch for claims and the first vote … Do not reveal my role without need." | The approach it set: keep silent and keep the role hidden. |
| Action | passed | The action followed the note. |

*One of ten replay samples of this turn with the schema enforced; each read gives a suspected role,
a confidence and a reason. The recorded game shows the same pattern on all three turns.*

The read retained the visit claim, and the action agreed with the note's plan to stay silent. But
the written assessment never connected the block to the Chanteuse's visit. That identifies a gap to
investigate without proving what the model understood internally. The night record's “learned nothing”
wording and the private plan to stay silent were also possible influences. The
[deduction-engine page](../deduction_engine/deduction_engine.md) follows the intervention.

### Getting the requested assessment into the answer

Three changes made the answer better match the work requested.

**Give the assessment its own field, and ask for it in the prompt.** An instruction to assess each
retrieved lesson originally sat in the strategy-note field's description. The model kept writing its
usual terse note. A separate required verdict field gave the assessment a place in the answer.
With that field already present, moving the instruction into the prompt body raised the share of
answers giving one verdict per item from 0.27 to 0.97. The field and the instruction served different
purposes: one defined where to answer, the other elicited complete coverage.

**Make declining explicit.** Required action fields distinguish a deliberate refusal from an incomplete
answer: silence is `pass_turn: true`, abstention is `abstain`, and an unused check is `no_check`.
The current memory-verdict lists are an exception: they default to empty, so coverage still depends
on the prompt instruction.

**Show fields only when they apply.** When the answer schema was sent as text, turns with no lessons
still copied “lesson 1: follow” from the example: 426 of 3,118 decisions in twenty games. Memory
instructions, verdict fields and their examples now appear only when lessons are supplied.

The answer every seat turn opens with is now:

```
reads                  one per living player other than itself: player, why, suspected_role, confidence
strategy_verdicts      follow / override / not_relevant, one per numbered lesson shown   (only if shown)
memory_applicability   fully / partly / does_not_apply, one per numbered observation     (only if shown)
updated_strategy       the seat's private note, shown back to it on its next turn
… then the turn's own fields: message and pass_turn, vote_target, or the night target
```

How a reply is validated against this contract, retried and given a legal fallback is the subject of
[Structured agent execution](../../game_design_orchestration/agent_turn/agent_turn.md).

### Putting assessment before action

The chapter's vote study showed why order was worth testing: a note written before the vote agreed
with it more often, though votes against real threats became less frequent. Consistency alone was
not evidence of better decisions.

Reads were also tried before and after the strategy note. With reads first, players overrode a
retrieved suggestion about three times as often, but a model judge rated the reads less substantive
when there were no earlier reads to update. That placement was adopted provisionally.

A later change addressed disagreement between the prompt and the schema—the listed answer fields. The prompt's opening line asked
for the reads before the decision, while the schema listed the memory verdicts first. When the schema was sent as text rather than enforced by the provider, today's model kept the schema's field order on 15 of 24 real turns, and every mismatch put
the reads first; the recorded reading is that the prompt's opening line pulled the model. Adding a
sentence asking it to keep the schema's order gave 13 of 23. Reordering the schema to match the
prompt, reads, verdicts, note, decision, gave 24 of 24 on the same turns; agreement the other way
round was not tried, and which assessment field should come first was not itself tested. That order
is today's.

Keeping the order is compliance, not quality; the chapter page's figures separate the two, since on
that earlier model the note-first layout matched reasoning to vote more often and still voted against
a real threat less often. Today's order has not been tested for message quality.

### Testing whether a fuller assessment helps

The main test came from a vote I watched go wrong while playing. Four players were left on day 5: the
Vigilante and the Sentinel, both town, the Sentinel's claim true; the Speculator, a seat that chooses a
side and had chosen the town; and the Necromancer, a seat that wins alone and was the one hostile
player left. I was the Necromancer. The Vigilante voted the Sentinel out as "unverified", although the
day before it had written that the Sentinel's watch fitted the Investigator's check, and nothing since
had contradicted it; the two quiet seats got "no evidence either way". A consistent claim was held to a
standard that silence never had to meet, and nothing in the format prevents that: each read is written
on its own.

I tested one additional instruction: compare each player with the strongest plausible alternative,
and say when the evidence does not distinguish them. Eleven votes from that game, including the failing
ballots and controls it had got right, were replayed ten times per version with memory off.

The original bad vote was not the usual replay outcome. Without the instruction, the Vigilante voted
for the hostile Necromancer in 7 of 10 samples. With it, that fell to 0 of 10: it abstained in six
and voted for the Sentinel in three. Seven of the revised reads said nothing separated the two quiet
players. The fact that did distinguish them—the Necromancer alone had abstained on the previous day's
vote—was cited less often. This suggests the instruction's uncertainty clause encouraged abstention
in this case; it does not establish a general mechanism.

On three earlier votes from the same game, where the evidence was stronger, the instruction elicited
more useful detail. A wolf had voted out the Investigator alongside another wolf. Reads cited that
vote in 11 of 30 samples with the instruction, compared with 2 without. Votes against that wolf moved
from 13 to 17 of 30, a small change on these sampled turns. Vote output also grew from 960 to 1,297
tokens on average.

I removed the instruction. It elicited better-supported reads in one part of the game but broke the
decision it was written to help. Even the original condition's seven correct votes were not all
well grounded: three cited a misquoted vote. Both the assessment and the resulting action needed
inspection; neither more detail nor a correct target alone settled whether the prompt helped.

### When the prompt supplies the answer

An assessment can also be influenced by the prompt's incidental details. Two patterns prompted changes
to the information offered when there was little game evidence to distinguish candidates.

On night 1 nothing
distinguishes the seats, and over 28 earlier games the Investigator checked player_1 in 21 of them.
The obvious fix, shuffling every player list, was checked before any game on 96 night-1 calls, the
Investigator, the Healer and the lone killer on 32 recorded situations, and did nothing: the target
was still the lowest-numbered other seat in 95 of 96. The model was following the number, not the
order. So on night 1 the engine draws a seat by lot, seeded by the game, the night and the player, and
the prompt offers it: "a lot has been drawn for you: player_N. Take it unless you have a reason to
prefer someone else." On the same 96 calls, player_1 had been the target 78 times; with the lot, the
actions landed on all nine seats, 6 to 16 each. The Vigilante draws no lot, so as not to encourage a
shot without evidence.

The second cue was the answer example. Every prompt's sample read named `player_2`, and on day 2
across 32 games `player_2` drew 40 accusation tags and 41 votes against medians of about 8 and 12 for
the other seats. That points to the example as the cue; it now names no seat, and its effect on day 2
was not re-measured. The rule these set for every prompt since: an example never names a legal answer,
and a choice with no evidence behind it gets its randomness from the engine, not from the model.

### Giving the model more thinking effort

Requiring a written assessment and increasing **thinking effort**, the model call's reasoning setting,
are different interventions. Higher effort helped on some replay measures without changing the
requested answer fields. Votes and discussion needed separate checks.

| Model and cases | Measure | Lower effort | Higher effort |
|---|---|---|---|
| Earlier model: 89 turns, 3 samples each, provider-enforced schema | Samples with a factual error | 82 of 267 | 27 of 267 |
| Current model: 16 votes from two games, 10 samples requested per turn, schema sent as text | Votes against an actual threat | 97 of 157 returned votes | 122 of 158 returned votes |
| Current model: 23 discussion turns, 5 samples each, provider-enforced schema | Samples with an error | 49 of 115 | 47 of 115 |

The earlier model's higher setting cost about 2.4 times as much and took 3.3 times as long per turn;
that setting was adopted wherever the model is still used. In the current model's live text mode,
votes improved while average output rose from about 1,440 to 2,120 tokens per vote. Discussion errors
changed little in the separate enforced-schema test, while time rose from 6.7 to 11.2 seconds per turn.
These are different tasks and, for the current model, different output modes; the vote finding does
not establish a discussion benefit. Moving live votes to higher effort remains an open cost decision.

Today's field order has not been tested for message quality, and these selected replay results do not
measure the combined prompt's effect across whole games. The useful distinction remains between
getting an assessment written, making the action agree with it, and improving the decision itself.
The cost of output mode and thinking settings is developed in
[Cost and latency](../../cost_and_latency/cost_and_latency_codex.md).

<!-- Sources for the page copy (checked 2026-10-31):
Opening: the three failures and the written-assessment scope follow the Level 1 section and the
owner's 2026-10-30 ruling (skills_inventory, "Chain-of-thought prompting"). Replay method and the
swing-of-five: turn_prompt/report.md "What is not established" (adding true facts to the ballot lines
moved per-case vote counts by up to five of ten); discussion_evidence.md §8.7 limits.
§1 exhibit: deduction/experiment_log.md §4 (the failure, the three passed turns, the notes side by
side); deduction/report.md §2. The sample is case 9b3219e5dc1eb831 ("right after player_7 admitted
visiting player_8 and refused to claim"), slice as_played, Haiku 5.5 at low, sample 0 of
data/deduction_injection/runs/deduction_injection/eval_results/judged_haiku_low.jsonl (2026-10-16,
enforced schema); the carried note is state.agent_strategies.player_8 in cases.jsonl, and the original
action is "(passed)". The case holds no lessons (memory empty), so the verdict fields were removed by
output_schema_for_memory_shown. The six other reads in the sample are "unclear (low): unchanged".
The night record the seat read then ("… and you learned nothing tonight") is page 4's and page 1's.
§2: decision 10 and experiment_log.md §7; the 0.27 → 0.97 is row_reliability in
memory_system/strategy_adoption/forced_schema_screen/experiment_log.md ("Prompt-limit vs output-limit",
2026-06-16, n = 60): the share of answers giving one verdict per numbered observation, with the forced
field already in the base arm; the verdict lists default to empty today (Agents/schemas/lineup_output.py
TurnOutput) and the report names them the exception; decision 11 (flash-lite dropped nullable fields; pass_turn,
abstain, no_check, hold_fire; the verdict exception, 426 of 3,118 over 20 Haiku games) and
caching/experiment_log.md §16; decision 12 (about 1,200 characters, only when shown); decision 8 and
discussion_evidence.md §8.6 (firing brief wording; the vote-reason line's second wording, passes 24 of
25 → 16 of 25 on the five open-floor turns of the 18-turn replay, 5 samples each; the first wording 23;
the after arm also carried the visit rule and the reply brief; six of the nine speaking samples named a
vote with its reason; Haiku 5.5 at low).
Kept in notes: the reply brief's result (restated replies 27 of 30 → 23; the framing changed, "As I
said", the content mostly not); the first vote-reason wording (24 → 23). Skeleton: report "What the
seat must answer" (TurnOutput).
§3: decision 10 and experiment_log.md §11.1 (reads before the note: override rate 0.06 → 0.17, "triples";
reads "lazier" with no prior history; reads-first shipped provisionally); the May adoption-field
result stated as the Level 1 states it, no 1–5 scores; caching/experiment_log.md §12 (Haiku unenforced
15/24, every mismatch reads first; instructed 13/23; reordered 24/24; "one plausible cause" the prompt's
opening line). Agreement figures and 40% → 26% recalled in a clause only: decision_replay log
(coherence 75% → 92.5%; reorder 2×2 step 2, memory-off 0.40 → 0.26, where the measure is votes against
a real threat, lower is worse for the town). "Not tested for message quality": decision 10, "What is
not established".
§4: discussion_evidence.md §8.7 and data/haiku_vote_replay/README.md (game 403f4dbc, day 5: the
vigilante, the speculator (picked Town), the sentinel player_9 and the Necromancer player_3, the owner's
seat; the vigilante's original ballot reproduced 1 of 10 on the current code (3 and 6 of 10 on two
earlier commits); day-6 ballots: the vigilante voted out the speculator and the speculator voted the
vigilante after player_3's first-ever sigilist claim; day-4 controls: vigilante, healer, sentinel, right
answer player_1 the chanteuse; the sentence's text; 11 frozen votes, 10 samples
each, Haiku 5.5 at low, memory off; vigilante 7/10 → 0/10, abstain 6, sentinel 3; "nothing separates
player_3 from player_10" 7 of 10; the day-4 abstention fact cited 3/10 vs 8/10; day-4 reads citing the
decisive vote 11 vs 2 of 30; votes for player_1 13 → 17 of 30; output 960 → 1,297 (+35%); reads 517 →
802 characters; not adopted); decision 9. p-values omitted on purpose (Fisher 0.003; 0.01). Ballot tag:
§8.7 (day 4 right 12 vs 13 of 30; per case sentinel 4 → 9, vigilante 6 → 2, healer 3 → 1, day-5 sentinel
7 → 3). Cite the record exactly: decision 9 and gameplay/report.md problem 1 (nine-seat, 2026-10-04,
gemini-3.5-flash-lite at a setting with 0 reasoning tokens, §6.7; misquotes 24 before and after, no
denominator in the source; the per-player vote layout 26% → 21% within noise, not on the page). The
other ballots: data/haiku_vote_replay/README.md (speculator 0 of 10 with 10 and 9 abstaining; day 6 1 →
2 of 20; day 3 30 → 28 of 30; the day-5 sentinel 7 → 6). "Three of the seven rested on a misquoted vote":
§8.7 ("three of its reads say player_3 voted out the investigator on day 3, which player_1 did").
Suspicion cues: decision 6 (tone-policing 24 of 119 → 8 of 79 on substring matches, 2 unpaired games
per arm, an easier board in the second pair; kept on principle). Decision 7's audit in one sentence
(owner 2026-10-31 ruling): wolves voting with the majority at least 80% of the time won 38% of games
(n = 50) against 25% (n = 72), r = +0.16; the investigator rewrite's A/B is not recorded as run.
§5: decision 5 and discussion_evidence.md §7.5 (investigator checked player_1 in 21 of 28 games; 32
boards, 192 calls on gemini-3.5-flash-lite: shuffled 95 of 96 lowest-numbered, 94 of 96 unshuffled;
without the lot seat 1 took 78 of 96 night-1 actions and 16 of 32 boards put check, protection and
kill on one player; with the lot taken 95 of 96, all nine seats 6 to 16 each; the vigilante draws none;
player_2 40 accusation tags and 41 votes on day 2 against medians about 8 and 12; the example reads
"<exact player_id>"; no read copied the placeholder in 192 calls).
§5 (retitled in review from "accidental cue" to "supplies the answer" so the suspicion-cue paragraph
sits with the cues rather than in §4; the 96 calls are 32 boards × investigator, healer, serial killer).
§6: decision 15; 267 = 89 cases × 3 samples (map block 143); flash-lite is no longer the default seat
model but runs at medium where used (catalogue); "all replayed at the lower level of the model in use":
compare-candidates, the brief and the reorder trial at Haiku low, the July reads and the cite rule at
flash-lite's then-default (0 reasoning tokens), the lot on flash-lite 2026-10-07 (level not restated in
§7.5); the framing line ("moved more than any wording did") rests on §6.7 ("larger than
everything in §6.4–6.6 put together") and deduction/experiment_log.md §2 ("the strongest single lever
measured"); discussion_evidence.md §6.7 (gemini-3.5-flash-lite at minimal: 0 reasoning tokens;
medium: 82 → 27 of 267, 36 better / 4 worse, about 2.4× cost and 3.3× time; runs at medium now);
deduction/experiment_log.md §2 (Haiku 5.5 low vs medium, enforced schema: votes 65/160 vs 98/160, 12
better / 1 worse; discussion 49/115 vs 47/115, 6 better / 5 worse; 11.2 s vs 6.7 s; about $0.23 vs
$0.12 a game; the discussion cases are 18 from 403f4dbc and 5 from 2f19d908) and §9 (live mode
json_mode: 97/157 vs 122/158; output about 1,440 vs 2,120 tokens a vote). "Reported no reasoning
tokens", never "did no reasoning". Day-4 vote lead: decision 14 and §8.7 (25, 20, 13 of 30 across code
versions; 9 of 30 at low vs 28 of 30 at medium on one layout). Dedup judge pointer:
memory/store_upkeep/dedup_judge.md ("Order beat rules", the "when unsure" lean); the judges pointer
(narrow questions) was cut with the closing pointer per the outline's cut list.
Kept off the page (handle with care): model family names (Haiku 5.5, gemini-3.5-flash-lite,
gemini-3.1-flash-lite, Sonnet judge) and their versions; 1–5 judge scores (4.00 → 4.38, 3.97 → 4.47);
p-values; the participation figures and the layout's cost (chapter 6); the output-mode story (chapter
6's cache-layout account); the uptake results and the silence 2×2 (page 4 and the Level 3); the
tactical-advice audit (decision 7; the wolves' blend correlation and the untested investigator rewrite
stay in evidence); the reply brief's "As I said" result.
-->

<!-- Supporting material relocated during the 2026-10-31 revision.
The following superseded passages are retained as authoring history, not current claims.

When an agent made a poor decision, I wanted to tell three failures apart: it missed a fact; it went
wrong between the facts and the conclusion, which includes how it used a lesson it had been given; or
it decided against its own assessment. A short private note could not show which. So the answer every
turn returns is an explicit, structured chain of thought, written as fields the answer must fill before
the decision. The record is the agent's written assessment; the model's hidden reasoning tokens are a
separate chain, which this record neither shows nor claims to improve. Getting the fields filled and
placed before the action depended on where the request sat, in the answer's fields and the prompt
body, as much as on what it said; whether a fuller assessment helped had to be tested on the decisions
it produced. The changes below were replayed where they could move a decision, some measured on
whether the field appeared, some on the decision itself.

The test in each case was a replay of a frozen turn: a recorded turn rebuilt from the saved game,
with the transcript, notes and night results as the agent saw them, answered again several times
under each version of the prompt. Ten samples of one turn measure what a change does to that decision,
not how often the problem occurs in play, and small wording changes moved single cases by as much as
five of ten samples either way (measured below, when true facts were added to one game's ballot
lines), so a result on one game is a local effect until another game repeats it. Two output modes
appear below: the schema enforced by the provider, or sent as text and checked in code, the game's
mode now. [Choosing between turn replays and whole
games](../../evaluation/replays_and_games/replays_and_games.md) explains the method.



The game is a hidden-role deduction game: a town of named roles against hidden wolves and solo
seats, with day votes and night actions, and I sometimes take a seat on the live site. Every turn's
answer opens with its assessment and ends with its decision. The assessment is a **read** of each other
living player (a suspected role, a confidence and a one-line reason); a **verdict** on each item shown
from memory, a lesson distilled from earlier games or an observation recorded from one, in two short
lists present only when memory supplied something; and the **strategy note** the seat writes for
itself and reads back on its next turn. Then comes the decision: the message, the vote or the night
target. One recorded turn shows what the assessment lets an investigator see.



The record rules out a misread clue and a misapplied lesson, and the decision agreed with the written
approach. It points to the middle of the list: nothing connects "I was blocked" to "the blocker visited
me", and so to player_7, under a night record whose last clause worked against that step and a
self-set stance of silence. That missing step is the case the [deduction
engine](../deduction_engine/deduction_engine.md) on the next page was built around; the night
record's wording and the silence are tested there too.



Asking for an assessment did not reliably produce one. The answer failed to match the request in three
ways, and each needed the request moved, into the answer's shape or into the prompt body, rather than
another sentence in the same place.

**An instruction in a field's description was skipped.** The first request to assess each retrieved
lesson sat in the description of the note field, and the model wrote its usual terse note. The
assessment became a **required field**, a field without which the answer is invalid, one verdict per
memory item, which gave each verdict a slot. Coverage rose only when the instruction to fill them also
moved out of the field description into the prompt body: the share of answers giving one verdict per
item shown went from 0.27 to 0.97, with the field itself unchanged. Today the two verdict lists are
the one exception to the rule below; they default to empty, and coverage rests on that prompt-body
instruction.

**An absent field was ambiguous.** An earlier model silently dropped optional fields, so an empty
answer could mean a declined action or an incomplete one. Every field the turn shows is therefore
required, and "no" is a value: silence is `pass_turn: true`, an abstention is the vote `abstain`, and
a kept check is `no_check`.

**A field that did not apply was filled anyway.** With the schema sent as text, a turn shown no lessons
still returned verdicts, typically "lesson 1: follow", copied from the answer example: 426 turns of
3,118 seat decisions in twenty games. The memory instructions, about 1,200 characters, and later the
verdict fields and their example, now appear only when lessons are shown. The same rule, a line only
when it applies, also adds to the request: a brief saying why the seat is being asked ("You were
directly addressed by player_4. Respond to them this turn"), and on a voting day a line asking a town
seat to decide its vote now and say why, added after four seats voted a player out, correctly, without
one giving a reason the town could weigh; on five open-floor turns from that game, five samples each,
passes went from 24 of 25 to 16 of 25.



The order of the fields was found to matter twice before the current layout, as the chapter page
tells: a judge rated actions higher once the field reporting which lesson the seat followed moved
before them, and with the vote first a quarter of the notes never committed to the player voted for.
Two later decisions set today's order.

The reads were placed before the note rather than after it: in the replay that compared the two
placements, a seat that wrote its reads first overrode a retrieved lesson's suggestion about three
times as often, the check against its own beliefs that memory was meant to get, though a model judge
rated those reads thinner when there were no earlier reads to update (each turn's reads are shown
back to it on the next). Reads first shipped provisionally.



The smallest change that could test the idea was one sentence in the rules block every seat reads,
asking each read to compare the living players rather than assess each in isolation: explain what
makes this player a stronger or weaker candidate for the suspected role than the strongest plausible
alternative, and say so if the evidence does not distinguish them. Eleven votes were frozen from the
game: the two day-5 ballots that went to the Sentinel, the Vigilante's and the Speculator's; the two
day-6 ballots cast after the Necromancer's unchallenged claim to a dead player's role; and seven
controls the game had got right, three town voters on each of days 3 and 4 and the Sentinel's own
day-5 vote. Each was answered ten times with and without the sentence, memory off.

The recorded ballot turned out to be a minority draw: on the current prompt the Vigilante voted the
Necromancer in 7 of 10 samples and the Sentinel in 1 (three of the seven rested on a misquoted vote).
With the sentence it never voted the Necromancer, 0 of 10: it abstained in 6 and voted the Sentinel
in 3. Its reads show why. Seven of ten said that nothing separated the Necromancer from the other
quiet seat, and the one fact that did, that the Necromancer alone had abstained on the day-4 vote, was
cited in 3 of 10 reads against 8 of 10 before. The sentence's escape clause absorbed the lean, and the
ballot's abstain option absorbed the uncertainty.

Where the evidence was strong, it changed the assessment. The three day-4 controls, 30 samples, had
to find player_1, a wolf, and the decisive fact was in the vote record: on day 3 player_1 had voted the
Investigator out beside the other wolf. The reads of player_1 cited that vote in 11 of 30 samples with
the sentence against 2 without; the votes for player_1 moved from 13 to 17 of 30, within the swing
single cases show on these same ballots. The remaining ballots barely moved: the Speculator abstained
in nearly every sample either way, no version resisted the day-6 bluff, and the day-3 controls stayed
right in 30 and 28 of 30. The cost was output: a vote grew from 960 to 1,297 output tokens.

I did not keep it. It broke the ballot it was written for and bought a better-grounded read elsewhere,
at a third more output on every vote; on this game it helped where the evidence was strong and hurt
where it was thin, so its effect looked dependent on evidence a fixed wording cannot see in advance.
A fuller assessment changed the assessment; the decision still had to be checked.

Two more sentences went the same way. Tagging each ballot in the record with what its target turned
out to be, which added only true facts, moved single cases both ways (one day-4 voter 4 → 9 of 10,
another 6 → 2), more than any effect tested, which is where the swing-of-five limit comes from. And
in an earlier study on an earlier model, at a setting where it reported no reasoning tokens, "cite the
record exactly" left vote misquotes unchanged at 24 before and after on that replay set: a request to
cite produced prose that nothing checked.



A written assessment can only justify the choice it is asked about, and when nothing in the evidence
decides, the prompt itself can decide, by design or by accident. The early role cards did it by
design, telling seats to treat evasiveness as a tell, and seats policed each other's tone instead of
playing; those cues gave way to "prefer a test or a contradiction", kept on principle rather than on a
comparison that was confounded, since the prompt should not build in an answer the experiments were
meant to investigate, and the tactical advice that remained was checked against the games' own records.



The written assessment is one lever on whether a seat uses what it has; **thinking effort**, a setting
of the call counted in reasoning tokens, is the other. The wording results above were all replayed at
the lower level of the model in use, and they have to be read against it: on the same replay measures
it moved more than any wording did.

| Model and cases | Measure | Lower level | Higher level | Cost or time |
|---|---|---|---|---|
| One earlier player model, 89 replayed turns of the nine-seat game, 3 samples each, schema enforced | samples with a factual error | 82 of 267 | 27 of 267 | about 2.4 times the cost and 3.3 times the time a turn |
| Today's player model, 16 frozen votes from two games, 10 samples each, schema enforced | votes on an actual threat | 65 of 160 | 98 of 160 | about $0.23 a game against $0.12 |
| The same votes, schema sent as text (the mode the game uses) | votes on an actual threat | 97 of 157 | 122 of 158 | about 1,440 against 2,120 output tokens a vote |
| The same model, 23 frozen discussion turns, 5 samples each, schema enforced | samples with an error | 49 of 115 | 47 of 115 | 6.7 s against 11.2 s a turn |

The earlier model, at its then-default level, reported no reasoning tokens at all; at the higher level
36 of its 89 cases improved and 4 worsened, and it runs at the higher level wherever it is still used.
Today's model improved on 12 of the 16 vote cases and worsened on 1, the higher level still led in the
text mode, and its discussion turns did not change, so votes and discussion need separate decisions. Every seat turn still runs at the lower level; moving votes up is an open
decision whose cost side is in [Cost and latency](../../cost_and_latency/cost_and_latency_codex.md).



What the current combination leaves untested is specific. Today's field order and the text output
mode have not been checked for message quality. The day-4 control votes also fell across three
versions of the code in the same game, a change entangled with the prompt layout and the thinking
level, which were not separated. A related pattern, that where a request or a fact sits changes the
result, appears in the project's other model calls, among them the deduplication judge's input order
and its "when unsure" lean in [How the deduplication judge was
built](../../memory/store_upkeep/dedup_judge.md).


-->
