# Making assessments explicit and testing how they shape decisions

*Level 2 · [Context engineering](../context_engineering.md) · first draft 2026-10-31*

## Page copy (draft)

When an agent made a poor decision, I wanted to tell three failures apart: it missed a clue, it
misapplied a lesson it had been given, or it decided against its own assessment. A short private
note could not show which. So the answer every turn returns is an explicit, structured chain of
thought, written as fields the answer must fill before the decision. The record is the agent's
written assessment; the model's hidden reasoning tokens are a separate chain, which this record
neither shows nor claims to improve. Getting the fields filled, putting them before the action, and
finding out whether more of them helped took several changes, and each was tested against the
decisions it produced.

The test in each case was a replay: a recorded turn rebuilt from the saved game, with the transcript,
notes and night results as the agent saw them, answered again several times under each version of the
prompt. Ten samples of one turn measure what a change does to that decision, not how often the problem
occurs in play, and small wording changes moved single cases by as much as five of ten samples either
way, so a result on one game is a local effect until another game repeats it. [Choosing between turn
replays and whole games](../../evaluation/replays_and_games/replays_and_games.md) explains the method.

### What the written assessment needs to reveal

Four fields open every turn's answer: a **read** of each other living player (a suspected role, a
confidence and a one-line reason), a **verdict** on each lesson retrieved from memory (follow,
override or not relevant), the **strategy note** the seat writes for itself and reads back on its
next turn, and only then the decision: the message, the vote or the night target. One recorded turn
shows what they let an investigator see.

A healer had been roleblocked on night 1. By the middle of day 2 the trailseer, whose ability shows
where a followed player went, had said it followed player_7 to the healer that night, and player_7 had
admitted the visit without claiming a role. In this cast only the Chanteuse, a wolf, can block, and a
block is a visit. The healer passed all three of its turns that day. Its answer on the turn after the
admission shows which kind of failure that was.

| Field | What the healer wrote (one replay sample of the frozen turn, the prompt as played) | What it let me see |
|---|---|---|
| Reads | player_3: unclear (low): claims trailseer; follow result on player_7 to player_8 is unverified but plausible · player_7: unclear (low): admits visiting player_8 on night 1, no role claim | It recognised the clue: it knew it had been visited, and by whom. |
| Verdicts | none asked for: no lesson was shown on this turn | No retrieved lesson was in play, so none was misapplied. |
| Strategy note | "I was roleblocked night 1 and have no results. … Stay quiet unless addressed, watch for claims and the first vote … Do not reveal my role without need." | The approach it set: keep silent and keep the role hidden. |
| Action | passed | The action followed the note. |

*One of ten regenerations of the turn on the unchanged prompt; the note it was shown is the one the
game recorded, and the game's own notes set the same premises side by side on all three turns.*

The facts were recognised and the decision agreed with the written approach. What is missing is the
step between them: nothing connects "I was blocked" to "the blocker visited me", and so to player_7.
That narrows the failure to a missed inference, the case the [deduction
engine](../deduction_engine/deduction_engine.md) on the next page was built around; why a seat holding
the fact stays silent is examined there too.

### Getting the requested assessment into the answer

Asking for an assessment did not reliably produce one. Three things went missing, and each needed a
change to the answer's shape rather than another sentence of instruction.

**An instruction in a field's description was skipped.** The first request to assess each retrieved
lesson sat in the description of the note field, and the model wrote its usual terse note. The
assessment became a **required field**, a field without which the answer is invalid, one verdict per
lesson. The instruction to write them also moved from the field description into the prompt body,
which took the share of lessons that received a verdict from 0.27 to 0.97.

**An absent field was ambiguous.** An earlier model silently dropped optional fields, so an empty
answer could mean a declined action or an incomplete one. Every field the turn shows is therefore
required, and "no" is a value: silence is `pass_turn: true`, an abstention is the vote `abstain`, and
a kept check is `no_check`.

**A field that did not apply was filled anyway.** With the schema sent as text, a turn shown no lessons
still returned verdicts, typically "lesson 1: follow", copied from the answer example: 426 turns of
3,118 seat decisions in twenty games. The verdict fields, their example and the memory instructions,
about 1,200 characters, now appear only when lessons are shown. The same rule gives each turn a
one-line brief saying why the seat is being asked ("You were directly addressed by player_4. Respond
to them this turn") and, on a voting day, asks a town seat to decide its vote now and say why; on 18
frozen turns from one game that line brought open-floor passes from 24 of 25 samples to 16 of 25.

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

The order of the fields was found to matter twice before the current layout, as the chapter page
tells: a field reporting which lesson the seat had followed changed the action when it moved before
it, and with the vote first a quarter of the notes never committed to the player voted for. Two later
decisions set today's order.

The reads joined in July, placed before the note: in that replay a seat overrode a retrieved lesson's
suggestion about three times as often when it had written its reads first, though the reads were
judged thinner when there were no earlier reads to update, so reads first shipped provisionally.

The second decision came from the prompt and the schema disagreeing. The prompt's opening line asked
for the reads before the decision, while the schema listed the memory verdicts first. In the game's
live output mode, where the schema is sent as text and the reply is checked in code rather than
enforced by the provider, today's model kept the schema's order on 15 of 24 real turns, and every
mismatch put the reads first. Adding a sentence asking it to keep the schema's order gave 13 of 23.
Reordering the schema to match the prompt, reads, verdicts, note, decision, gave 24 of 24 on the same
turns. That order is today's.

Keeping the order is compliance, not quality. The chapter page's figures already separate the two:
the written reasoning matched the vote more often with the reasoning first, and in a larger replay on
the same model the note-first layout voted against a real threat less often. Today's order, with the
verdicts after the reads, has not been tested for message quality.

### Testing whether a fuller assessment helps

The main test came from a vote I watched go wrong while playing. On day 5 of a game with four
players left, the Vigilante voted out the real Sentinel because its claim was "unverified", although
the day before it had written that the Sentinel's watch fitted the Investigator's check and nothing
since had contradicted it. The two quiet seats got "no evidence either way". A consistent claim was
held to a standard that silence never had to meet, and nothing in the format prevents that: each read
is written on its own.

The smallest change that could test the idea was one sentence in the rules block every seat reads,
asking each read to compare the living players rather than assess each in isolation: explain what
makes this player a stronger or weaker candidate for the suspected role than the strongest plausible
alternative, and say so if the evidence does not distinguish them. Eleven votes were frozen from the
game: the two wrong day-5 ballots, the two a bluff won on day 6, and seven controls that had voted
right. Each was answered ten times with and without the sentence, memory off.

On the ballot it was written for, the sentence made things worse. The Vigilante's vote for the real
threat fell from 7 of 10 to 0 of 10: it abstained in 6 and voted the Sentinel in 3. Its reads show
why. Seven of ten said that nothing separated the real threat from the other quiet seat, and the one
fact that did, that player alone abstaining on the day-4 vote, was cited in 3 of 10 reads against 8 of
10 before. The sentence's escape clause absorbed the lean, and the ballot's abstain option absorbed the
uncertainty.

Where the evidence was strong, it helped. On day 4 the decisive fact was in the vote record: the
suspect had voted the Investigator out beside a wolf. The reads of that player cited the vote in 11
of 30 samples with the sentence against 2 without, and votes for the player rose from 13 to 17 of 30.
The cost was output: a vote grew from 960 to 1,297 output tokens.

I did not keep it. It traded the ballot it was written for against a gain on a control day, at a third
more output on every vote, and its effect depended on how strong the evidence was, which no fixed
wording can know in advance. A fuller assessment changed the assessment; the decision still had to be
checked.

Two more sentences went the same way. Tagging each ballot in the record with what its target turned
out to be, which added only true facts, moved single cases both ways (one voter 4 → 9 of 10, another
6 → 2) without moving the day's total, which is where the swing-of-five limit above comes from. And
"cite the record exactly" left vote misquotes at 24 before and 24 after: a request to cite produces
prose that nothing checks.

One kind of sentence was removed on principle rather than on a count. The early role cards told seats
to treat evasiveness and deflection as tells, and seats policed each other's tone instead of playing.
Those cues were stripped in favour of a clause for when nothing is concrete: prefer a test or a
contradiction. The comparison that followed was confounded with an easier board, so the change stands
on the principle that the prompt should not build in an answer the experiments were meant to
investigate; the tactical advice that remained was checked against the games' own records and kept
or rewritten on that reading.

### When the prompt supplies an accidental cue

A different failure class showed up across games rather than within one: the choice followed the
seat number or the example, not the evidence.

On night 1 nothing distinguishes the seats, and over 28 earlier games the Investigator checked
player_1 in 21 of them. The obvious fix, shuffling every player list, was checked on 32 recorded boards
before any game and did nothing: the target was still the lowest-numbered other seat in 95 of 96 calls.
The model was following the number, not the order. So on night 1 the engine draws a seat by lot, seeded
by the game, the night and the player, and the prompt offers it: "a lot has been drawn for you:
player_N. Take it unless you have a reason to prefer someone else." On the same boards, seat 1 had
taken 78 of 96 night-1 actions; with the lot, the actions landed on all nine seats, 6 to 16 each. The
Vigilante draws no lot, so as not to encourage a shot without evidence.

The second cue was the answer example. Every prompt's sample read named `player_2`, and on day 2
across 32 games `player_2` drew 40 accusation tags and 41 votes against medians of about 8 and 12 for
the other seats. The example now names no seat. The rule these set for every prompt since: an example
never names a legal answer, and a choice with no evidence behind it gets its randomness from the
engine, not from the model.

### Giving the model more thinking effort

**Thinking effort** is a setting of the call, counted in reasoning tokens, not a line in the prompt.
It is a separate lever from the written assessment, and it changed whether a seat used the
information it already had.

| Model and cases | Measure | Lower level | Higher level | Cost |
|---|---|---|---|---|
| One earlier player model, 267 replayed turns of the nine-seat game | samples with a factual error | 82 | 27 | about 2.4 times per turn |
| Today's player model, 16 frozen votes from two games, 10 samples each | votes on an actual threat | 65 of 160 | 98 of 160 | about $0.23 a game against $0.12 |
| The same model, 23 frozen discussion turns, 5 samples each | samples with an error | 49 of 115 | 47 of 115 | turns 11.2 s against 6.7 s |

The earlier model, at its then-default level, reported no reasoning tokens at all; at the higher
level 36 cases improved and 4 worsened, and it runs at the higher level now. Today's model improved on
12 of the 16 vote cases and worsened on 1, while its discussion turns did not change, so the two kinds
of turn need separate decisions. Those vote counts come from a run with the schema enforced; repeated
in the live output mode, both levels voted better and the higher still led, 122 of 158 against 97 of
157. Every seat turn still runs at the lower level; moving votes up is an open decision whose cost side
is in [Cost and latency](../../cost_and_latency/cost_and_latency_codex.md).

What the current combination leaves untested is specific. Today's field order and the live output
mode have not been checked for message quality, and a fall in one game's day-4 votes across three code
versions is entangled with the prompt layout and the thinking level, which were not separated. The
same pattern, that the shape of the answer moves the result as much as the instructions do, appears
in the project's other model calls, among them the deduplication judge's field order and its "when
unsure" lean in [How the deduplication judge was built](../../memory/store_upkeep/dedup_judge.md).

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
§2: decision 10 (verdict instruction moved to the prompt body, coverage 0.27 → 0.97; the required
verdict field) and experiment_log.md §7; decision 11 (flash-lite dropped nullable fields; pass_turn,
abstain, no_check, hold_fire; the verdict exception, 426 of 3,118 over 20 Haiku games) and
caching/experiment_log.md §16; decision 12 (about 1,200 characters, only when shown); decision 8 and
discussion_evidence.md §8.6 (firing brief wording; the vote-reason line's second wording, passes 24 of
25 → 16 of 25, six of nine named a vote with its reason; Haiku 5.5 at low, 18 frozen turns, 5 samples).
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
§4: discussion_evidence.md §8.7 (game 403f4dbc, day 5; the sentence's text; 11 frozen votes, 10 samples
each, Haiku 5.5 at low, memory off; vigilante 7/10 → 0/10, abstain 6, sentinel 3; "nothing separates
player_3 from player_10" 7 of 10; the day-4 abstention fact cited 3/10 vs 8/10; day-4 reads citing the
decisive vote 11 vs 2 of 30; votes for player_1 13 → 17 of 30; output 960 → 1,297 (+35%); reads 517 →
802 characters; not adopted); decision 9. p-values omitted on purpose (Fisher 0.003; 0.01). Ballot tag:
§8.7 (day 4 right 12 vs 13 of 30; per case sentinel 4 → 9, vigilante 6 → 2, healer 3 → 1, day-5 sentinel
7 → 3). Cite the record exactly: decision 9 and gameplay/report.md problem 1 (nine-seat, 2026-10-04,
misquotes 24 before and after; the per-player vote layout 26% → 21% within noise, not on the page).
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
§6: decision 15; discussion_evidence.md §6.7 (gemini-3.5-flash-lite at minimal: 0 reasoning tokens;
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
