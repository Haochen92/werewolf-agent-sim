# Keeping the facts straight chapter (draft)

*Level 1 page copy, first draft 2026-10-30, revised the same day after the editorial and claims reviews and restructured around the owner's opening (what a player needs for its turn), written from `_authoring/context_engineering.brief.md` (the
owner's spine: four kinds of failure, four remedies). Not yet reviewed by the owner. The chapter's card
tag is context engineering; the page is organised around the problem it solves.*

---

## Page copy (draft)

### Keeping the facts straight: helping agents reason from what they know

The game is a variant of Werewolf (chapter 1): hidden wolves try to outlast everyone else, who must find
them and vote them out, and a human can take a seat. Each AI player's turn is one model call, and the
model knows only what that call's prompt contains. Over the project the game moved between several
small, low-cost models; where a result comes from an earlier one, the page says so. At night, some roles visit another player (to
protect, watch, investigate or block them) and the engine tells each one privately what happened; by
day, players argue and vote.

#### What a player needs for its turn

To take part, a player needs to know what it is trying to do, what it can do, what has happened and what
it meant to do last time. The game's state holds everything; each turn receives a view assembled for
that player and the decision in front of it (chapter 2 sets what it may see). Some of that view is game
state, such as the living players and each night's results; some is fixed text, such as the rules and
role descriptions; and some is kept only to help the player play, such as summaries of earlier days and
the player's own notes.

| What the turn receives | Why the player needs it | In the first version? |
|---|---|---|
| Its role, objective and abilities | what it is trying to achieve and what it can do | yes |
| The rules and every role's abilities | to interpret events and weigh other players' claims | yes; gaps filled after failures (below) |
| Who has died and as what, and the roles still in play | the board as it stands, without working it out from the transcript | added after miscounts |
| Its own night results | to act on what only it knows | partly: results such as a check, yes; a record of every night action (such as the Healer's protections) added later |
| Today's discussion | to respond to what was said, challenged or asked | yes |
| An account of earlier days | to recover past claims and accusations without rereading every day | yes, as a model's retelling; restructured with checked claims |
| Its private strategy note from its last turn | to carry its assessment and plan from one call to the next, and revise them | yes |
| Conclusions computed by code | the steps players missed | added |

A turn answers in fixed fields: its message, vote or night action, its updated note and, when it claims
a role, the role it claims. Here is part of one real turn, the Healer's on day 2 (it protects one player
each night), shortened and with the deduction engine off, as the game showed it:

```text
You are player_8, the healer. … every decision balances your own survival against shielding the
players who matter most.
Dead so far (public): player_1 (role not revealed, night 1)
Your night actions: Night 1 (last night): You were roleblocked: your action was not carried out and
you learned nothing tonight.
Your strategy note: Night 1 I was roleblocked, so I have no results. … Stay quiet on day 2 unless
addressed, … and do not reveal my role without need.
Day 2 discussion: … player_3: I'm the trailseer … Night 1 I followed player_7 and they went to
player_8. … player_7: … yes, I went to player_8 last night. That's all I'll say about it, and I'm not
claiming a role.
```

The strategy note is the player's own written account of its assessment and plan, not a record of its
internal thinking, so it can carry a mistaken belief or an outdated plan forward as easily as a sound
one.

At first a turn held only the rows marked as in the first version. I assumed a model could work out the
rest from a context of this size. It often could not: players stated things the game's record
contradicted. Lying is part of Werewolf; these were mistakes, and in an earlier, nine-player version of
the game (July) about 3% of public messages held one (Evaluation explains how they were found and counted).
Even a printed fact did not always help: a correct list of the roles still in play did not stop a player
hunting for "the remaining wolf" when none was left.

The inputs give a player a basis for its turn; they do not make it use that basis correctly. The rest of
the chapter takes four kinds of failure, each with its own remedy, and each remedy refines rows of the
table. Most follow one principle: code works out what is certain, and the model keeps the judgement. Deciding what goes into a model's context, and in what form, is usually called context
engineering. Most results below come from replaying a turn that went wrong: the same frozen input sent to
the model ten times, before and after a change. A replay shows whether that failure was removed; it is
not an error rate across whole games, which was not measured after these changes.

#### Making the facts understandable

The first failure: players misread or invented facts that were in front of them.

A fact that is present but easy to misread fails like a missing one. The engine now prints what a player
would otherwise work out from prose, such as who has died and as what, and words each of the player's
night results as its own action on a named night. The board alone did not stop the "remaining wolf"
error; printed together with a one-line read of every player (described below), it cut errors on 100
replayed error-prone turns, one sample each, from 48% to 30%, two changes measured together. The rules
now also state in full what each ability shows, because players filled gaps with rules of their own.

The Sentinel watches a player at night and learns who visited them. In a run of games, a player argued
that the Sentinel should appear in its own list of visitors, and in three of four games the real Sentinel
conceded the false rule, which made its genuine report look false, and was voted out. The rules had
never said otherwise. With the missing rule
sentence added, the replayed Sentinel conceded 0 times in 10, against 10 in 10 before.

*Explore: Making facts available and unambiguous →*
<!-- Link specification: Level 2 page 1, not yet drafted. -->

#### Preserving earlier days faithfully

The second: earlier days reached players distorted.

Each day is condensed once it ends, and a mistake in that account is not one player's private error:
every player reads it the next morning. So each statement keeps its source, and a player now reads
earlier days as three blocks with different authors.

| Block | Written by | Example |
|---|---|---|
| The game master's record | the game engine | night outcomes, every ballot, each revealed role |
| Claims | the fields in which each AI speaker states the role it claims (the summary's transcription for a player who filled none, such as a human), checked by code against the record | "player_3: claimed trailseer (day 2). Record: revealed as trailseer when they died on night 2, as claimed." |
| Accusations | a summarising model | who argued what against whom, labelled as claims, not facts |

A record check confirms only what the public record can settle: where the record fits more than one
reading it says nothing, and a claim it cannot contradict stays a claim. The summarising model records
who said what and never judges whether it is true; checking against the record is left to code.

One game showed why the summary still needs a guard in code. The Investigator said "I was roleblocked
last night", something done to it, without filling in its claim fields, so its claims came from the
summary. The summary recorded it as having blocked itself, which only the Chanteuse, a wolf, can do, and
so as claiming to be the Chanteuse. The next day the real Investigator accepted that it had made that
claim and was voted out 7 to 1. The summariser is now told that something done to a player is not that
player's claim, and code drops any claimed action that could only have been done to the speaker, such as
blocking itself, with the role claim resting on it. The error was too rare to recur in replay, so the
code rule, pinned by a test, is the guard.

*Explore: Carrying earlier days forward →*
<!-- Link specification: Level 2 page 2, not yet drafted. -->

#### Connecting the assessment to the action

The third: decisions did not follow the player's own assessment of the facts.

Having the facts in the prompt did not mean the decision rested on them. When a player was asked which
lesson from memory (lessons carried over from earlier games, chapter 4) it had followed only after
acting, its answers read as rationalisations. So the answer is structured so the model writes its
assessment before it acts: a one-line read of every other player with a reason, a verdict on each lesson
if any are shown, its private note, and only then the message, vote or night action. This is a structured form of chain of
thought.

The order ties the decision to the written reasoning, and that cuts both ways. On 40 replayed votes from
an earlier model, a separate model reading only the reasoning could name the player voted for 92.5% of
the time with the reasoning first, against 75%. But in a larger replay on the same model (three runs of
100 votes), votes landed on a real threat less often when the player's note came before the vote: 26%
against 40%. The vote follows the reasoning, including when the reasoning is wrong. Better decisions
need better material to reason from, which is what the last section supplies.

How the structure is imposed matters too. A model's thinking setting controls how much hidden
reasoning it does before answering, counted in reasoning tokens. On the Healer's turn, when the provider
enforced the answer's format (structured output), the game's current model reported no reasoning tokens
in 4 samples of 10 and read the situation correctly 2 times in 10; with the format given in the prompt as
text, as the game now sends it, every sample used reasoning tokens and the read was right 8 times in 10,
both with the deduction engine on. The evidence is from this model; other low-cost models have also
reported no reasoning tokens with an enforced format at their low settings, though none was a
like-for-like comparison.

*Explore: Testing how each turn is asked →*
<!-- Link specification: Level 2 page 3, not yet drafted. -->

#### Computing selected conclusions in code

The last failure was the hardest to see: every premise was in the prompt, and the player still did not
draw the conclusion. Take the Healer's turn above. In this game only the Chanteuse, a wolf, can
roleblock, and a block is a visit; player_3 reported following player_7 to the Healer, and player_7
admitted it, the only visit to the Healer anyone reported. Replayed on the game's current model at its
everyday thinking setting, the Healer read player_7 as the Chanteuse 2 times in 10. Its night record, as
the game first showed it, also said it had "learned nothing tonight", which worked against the
deduction.

Some conclusions follow from the rules and what the player has seen, so code can work them out. A
deduction engine, added after the earlier fixes, narrows which roles each player could still hold from
what that player is allowed to know (chapter 2), and writes its conclusions into the prompt, each worded
with its certainty: certain, true if a named claim is true, or the list of possibilities. For the Healer,
it replaced "learned nothing" with one certain line, the Chanteuse came to you that night, beside a few
general lines. Naming player_7 was left to the model: it is a strong suspicion, not a certainty, since
another player could also have visited. With the engine on, the read rose to 8 in 10. The engine came first; a later replay of the same turn showed the other ways to close the gap. Larger
models made the link with the engine off (9 and 10 in 10), and so did the game's own model at a higher
thinking setting (9 in 10). But a larger model costs about twenty times as much a game, and the higher
setting made a turn nearly three times as long on this case, where the engine works out the certain step
once, in code.

To keep the engine from using hidden roles, a test swaps roles a player cannot see and requires the
engine's lines to stay the same. The engine's code was written by an AI coding assistant; I set its
requirements, the rule for how certain each line must be, and the cases it had to pass.

*Explore: Working out selected conclusions in code →*
<!-- Link specification: Level 2 page 4, not yet drafted; its Level 3, "The roleblocked healer". -->

Chapter 4 turns to the other way I tried to improve play: lessons carried from earlier games.

<!-- Sources.
Opening table, "In the first version?": role card, rules and role descriptions, today's discussion, night
results and the strategy note were in the first prompts (strategy note and day summary in the code from
2026-05-09, git log -S; the project began 2026-05-01). The day summary began as a model's retelling and
was restructured after a narrated false premise and failed record checks (day_summary/report.md §4); the
claim ledger 2026-10 (§3, decision 13). The board of the dead and roles still in play: turn_prompt/report.md
decision 1 (2026-07-09, after survivor-count errors) and the information-fidelity pass (2026-10). Night
results reworded as the seat's own action on a named night: decision 2 (2026-10-03). Reads: decision 1
(2026-07-09). Deduction engine: deduction/report.md (2026-10). "I assumed a model could work out the rest
from a context of this size": the owner's account of the first design (2026-10-30), not a measured claim.
Healer excerpt: evidence/gameplay/deduction/data/healer_model_compare/turn_engine_off.md (game 2f19d908,
day 2, player_8; today's rendering with the deduction mode off, whose night line is the one the game showed),
shortened.
Reorder cost: memory_system/effectiveness/decision_replay/experiment_log.md "Adoption confound + reorder test"
step 2 (2026-06-13, judge-free 2x2, 3 x N=100, the strategy note before the vote: memory off 0.40 vote-first
against 0.26 reason-first; the coherence 92.5% vs 75% is section D, N=40, judged). Output mode with effect:
deduction/experiment_log.md §8 Result 1 (engine on, Haiku low: json_schema 2/10, json_mode 8/10).
Night-record row: turn_prompt/report.md decision 3 (the Healer had no record of its protections until 2026-10).
Intro: ~3% of public messages, the July nine-seat census (evidence/evaluation/factual_errors/report.md
step 1; turn_prompt/report.md decision 1). "The small, low-cost model the game runs on": Claude Haiku 5.5,
the house default seat model (catalogue). The obvious design not being enough: turn_prompt/report.md
decision 1 ("printing the facts alone did not stop the error").
Figure: turn_prompt/report.md "A turn today"; day_summary/report.md §3. Simplified grouping by author.
Facts misread or invented: turn_prompt/report.md decision 1 (T1b: the fourth recurring error came back
with a correct "roles still in play" line; survivor arithmetic the commonest July error), decisions 2–4.
Sentinel: decision 4 and discussion_evidence.md §8.4 (all four GPT-6 Luna games; three concessions; the
replayed sentinel 10/10 → 0/10, GPT-6 Luna).
Earlier days: evidence/extraction/day_summary/report.md §3 (the three blocks; the ledger says nothing where
the record fits more than one reading; quoted claims line), §4 (the summariser records, never judges),
§7 (game e06: "I was roleblocked" recorded as a Chanteuse claim; voted out 7 to 1; the fix, commit
6248fc58: the ledger drops an action that can only have been done to the speaker). The invention did not
recur in replay; the code rule is the guard (§7 Limits) — on Level 2.
Decisions and assessment: turn_prompt/report.md decision 10 (judge: a separate model reading the reasoning, decision_replay section D); decision 1 (board plus reads, 48% → 30% on 100 error-prone contexts, nine-seat, flash-lite); the format sent as text since 2026-10-14 for caching (catalogue note), not for reasoning; (after-action strategy labels read as rationalisations;
reasoning before the vote plus a required verdict per memory: coherence 75% → 92.5%; May–June,
gemini-3.5-flash-lite; the order not always kept by Haiku until the schema was reordered, 2026-10-13).
"Structured form of chain of thought": skills_inventory.md (revised 2026-10-30). Output mode:
deduction/experiment_log.md §8 Result 1 (Haiku, engine on, enforced json_schema: 0 reasoning tokens in 4
of 10; json_mode: every sample); same direction in other low-cost models: Gemini 3.5 Flash-Lite 0
reasoning with structured output at minimal and low (catalogue; discussion_evidence §6.7), forced tool
call turning thinking off (model_admission/report.md).
Not connected: deduction/experiment_log.md §8 Result 2 (game path, json_mode, engine off: Haiku low
2/10, high 9/10 at median 17.4 s against 6.3 s; Sonnet 5.5 low 9/10; Opus 5.5 low 10/10) and Result 1
(engine on, json_mode, Haiku low 8/10); deduction/report.md §1 (built after input and prompt fixes and
more thinking), §2–§4 (constraint propagation; three grades of statement; the seat view; hidden-role
tests). Authorship: the engine, solver included, AI-written; the owner's part the requirement, grading
rule, acceptance cases, experiments (project memory, code authorship split). "Nearly three times the
wait": 17.4 s against 6.3 s median per turn on this case.
Cost criterion: Sonnet seats about $2.30 a game against Haiku's $0.12 (deduction/experiment_log.md §2), about 19 times. Human seat: chapter 1. Claims example: day_summary/report.md §3 (player_3's trailseer line). e06: the investigator filled no claim field, so the ledger fell back on the summary (§7 "Why it got through").
Close: no whole-game error rate after the changes (content plan, care list). Memory: chapter 4.
Chapter card tags (not page copy): Context engineering, Structured outputs and validation; Symbolic
reasoning when the owner is ready to explain the algorithm and its test limits. -->
