# Gameplay: what went wrong in how the AI players play, and what fixed it

This page is the entry point to the gameplay area: how the AI players are given information, take part
in the day's discussion and reach decisions, the roles and rules they play under, and how each was
investigated and improved. It takes five problems seen in real games in turn: what each looks like,
what it traced to, what was done, what the evidence shows, and what is still open. Each problem links
to the report that holds its detail.

**Version.** Written against the working tree of 2026-10-26 (last commit `ccaec2f6`). Statements about
how the game works today describe that snapshot; each component report below has its own version line
and names the code it was checked against. The results belong to the model, seat count and date given
with each, and most were measured on earlier prompts than today's. The nine-seat game ran until
2026-10-09 and the ten-seat game since. Claude Haiku 5.5 has been the default player model since
2026-10-15.

## The area

Every AI player is one model call per turn. The model decides what a player says and does. The engine
decides everything else: what each player is told, who speaks next, and what happens at night. The
component reports each answer one question:

| Report | It answers |
|---|---|
| [The day discussion](discussion/report.md) | Who speaks, when, and how a day ends; the voices, and the silence ruling of 2026-10-18 |
| [The turn prompt](turn_prompt/report.md) | What a seat reads on its turn, in what order, and what it must answer |
| [The deduction engine](deduction/report.md) | The conclusions code works out from what a seat knows and writes into its prompt |
| [The roles](roles/report.md) | The cast, how each side wins, the balance batches, and how evil contests the town |
| [The day summary](../extraction/day_summary/report.md) | How a past day reaches later prompts: the summary, and the claim ledger checked by code |
| [Agent boundaries](../agent_boundaries/report.md) | Who may know what, where that is enforced, and how it is tested |
| [discussion_evidence](discussion_evidence.md) | The journey log of the October 2026 work, kept whole; its section index says which report carries each part today |

How errors are found and counted is measurement, and stays in
[factual_errors](../evaluation/factual_errors/report.md); the judges are in
[llm_judge](../evaluation/llm_judge/report.md). This page keeps what was done about the errors.

**How the five problems relate.** Problems 1 and 3 share a cause, the reasoning slip, and a fix: the
facts and conclusions code writes into the prompt serve both. Problems 2 and 5 share a root cause: the
nine-seat game had one exact source of information, and evil never contested it. Problem 4's silences
cut across the others. Where one problem rests on another, it links rather than repeats.

---

## Problem 1. Factual errors: players stating what the record contradicts

**What it looks like.** A player claims a check it never made, hunts "the last wolf" when both wolves are
dead, misquotes who voted for whom, or repeats a claim the day summary invented. In July 2026 about 3% of
public messages carried one (nine-seat). On the ten-seat game (ten games read against a rubric, October
2026), inventing facts had become rare; the commonest errors were bad reasoning about what an ability can
see, and the summariser distorting plain claims.

**Why it matters.** One error can decide a game. On 2026-10-03 the investigator announced a check it never
made, the village voted out an innocent player on that claim, 4 to 1, and the serial killer won.

**What it traced to.** Five causes, diagnosed case by case: *making things up*, *a reasoning slip*,
*misreading* correct information, *losing track* of what has happened, and *missing or confusing input*.
They overlap: a player reasoning well from a corrupted summary makes no error of its own. The diagnosis and
the cause of each symptom are in [factual_errors](../evaluation/factual_errors/report.md), step 3.

**What we tried, and what worked.** One pattern held across the fixes. Telling the model to take more care
with facts it already had did not change what it wrote. What worked was changing what it was given, or
moving the check out of the model into code. More thinking time cut reasoning slips on
gemini-3.5-flash-lite; on Claude Haiku 5.5 it improved votes but not the facts in what the seats wrote
(the last two rows).

| Change | What it did | Result |
|---|---|---|
| **Telling the model** | | |
| Cite the record exactly (2026-10-04) | Every day turn: keep each past vote, death and save exactly as the record has them | Vote misquotes 24 before and 24 after (16 cases better, 18 worse, p = 0.86); reverted the same day |
| The vote history laid out per player (2026-10-04) | The same votes, rearranged by voter | 26% → 21% of messages bad, within noise (p = 0.69); reverted with the rule above |
| The summariser checks each accusation against the record (`record_check`, 2026-10-03) | Cite the record wherever it contradicts the accusation | All 27 written were wrong (October 16 replay); removed 2026-10-16 |
| A rewritten private-note prompt (October) | Asked for a more careful note | Worse: 27 fact errors against 15 in 56 samples; not adopted |
| **Giving it the fact, or moving the check to code** | | |
| Results reworded (2026-10-03) | "Night 3 (last night): you investigated player_5, who is the healer" (nine-seat); on the ten-seat game, from 2026-10-09, "Night 2 (last night): you checked player_5. player_5 reads Not suspicious." | The invented check: 20 of 20 samples → 0 of 20 (one nine-seat turn) |
| The July bundle | A printed line of the roles still alive, a board of the dead, and more | Error-prone turns 48% → 30% wrong (p = 0.003) |
| Each agent's own night record; engine facts labelled apart from summaries (2026-10-03) | The engine writes what each seat did and learned at night | Part of the October fixes: 97 → 82 of 267 bad, a direction (p = 0.14) |
| The claim ledger, kept by code (October) | The summariser only transcribes claims; code checks them against the engine's facts, and since 2026-10-17 reads each speaker's own claim fields first | The repeated invented claim: 5 of 5 samples → 0 of 5 |
| The deduction engine (deployed 2026-10-19) | Code works out the conclusions a seat can draw and hands them over | On the replayed turn, every note records the fact, against none as played ([the deduction report](deduction/report.md) §4) |
| **Letting it think longer** | | |
| gemini-3.5-flash-lite: thinking level minimal against medium (nine-seat, 2026-10-04) | At minimal the model reasoned for 0 tokens; at medium it reasons before answering | Bad samples 82 → 27 of 267 (36 cases better, 4 worse), for reasoning slips, at about 2.4 times the cost per turn |
| Claude Haiku 5.5: thinking level low against medium (ten-seat, October) | Haiku reasons at both levels; medium gives it longer | Votes right 65 → 98 of 160 (12 cases better, 1 worse, p = 0.003); fact errors within noise: in vote notes 50% → 46% of samples (p = 0.21), in discussion turns 49 → 47 of 115 |

The results are on frozen turns replayed many times, except the July bundle's, which was a test fixed before
its data existed; how those replays are run and judged is in
[factual_errors](../evaluation/factual_errors/report.md), step 4. The nine-seat rows ran on
`gemini-3.5-flash-lite`; the 97 → 82 replay ran at the level where it produced no reasoning. The detail
of each prompt change, with its N, is in [the turn prompt report](turn_prompt/report.md), decisions 1–5 and
15.

**Why telling did not work.** On the vote misquotes, the record was already in the prompt. The model wrote
the point it wanted to make and filled in the supporting vote from impression, and an instruction to copy the
record did not change that ([discussion_evidence](discussion_evidence.md) §6.6). A request to cite produces
prose that nothing checks. A citation helps when something checks it: making the cited fact a structured
field that code compares with the record is the first change in the factual_errors report's "What we would
do differently next time".

**Where it stands.** Every change in the "giving" group of the table is live; the deduction engine runs at
its fullest level unless a game sets otherwise (`Agents/config/run.py::DEFAULT_DEDUCTION_MODE`). The
thinking level is set per model in the live model catalogue (a database table; read 2026-10-26):
gemini-3.5-flash-lite runs at medium, and Claude Haiku 5.5 at low for every seat turn, votes included.
On Haiku, medium lands the vote more often without making the written reasoning cleaner, so it is a
lever on votes rather than on factual errors. Moving Haiku's votes to medium, at about $0.23 a game
instead of $0.12, is parked (2026-10-26; [the deduction log](deduction/experiment_log.md) §2, §6). No factual-error rate has
been measured on the ten-seat game; the known failures are replayed after each fix, and new ones are
still found by playing.

## Problem 2. Thin talk: accusations that weighed little

**What it looks like.** On the nine-seat game the talk felt thin. Most accusations rested on how people
had voted, who had stayed quiet and who had spoken first, rather than on weighing two claims against each
other. A census of 28 nine-seat games (`gemini-3.5-flash-lite`, memory off, played 2026-09-17) counted
what 194 accusations rested on, using labels the end-of-day summary writes: a behaviour pattern 47%, the
voting record 28%, a concrete claim 20%, communication style 5%. The labels come from the playing model,
not an independent judge, so the census points a direction rather than measures
([discussion_evidence](discussion_evidence.md) §2.1).

**What it traced to.** Two explanations were on the table, and neither held as the main cause.
- *The investigator hides its results.* It did not: it claimed publicly in 24 of 28 games (§2.2).
- *The engine's silences and speaking order read as behaviour.* Real, but small. Quietness drove
  something like one accusation in eight, and a keyword search found speaking order cited as evidence on
  only 5 of 95 days (§2.4; Problem 4).

The cause was elsewhere. Town accusations resting on a claim landed on a wolf or the serial killer 34
times of 35; those resting on behaviour, 25 of 42, and on the voting record, 15 of 28, where a random
accusation lands on evil about a third of the time. And across the 28 games no wolf and no serial killer
ever claimed a role. Their only answer to a real investigator was to call its result invented, as in
this summary entry about a wolf:

> *Player_2 fabricated an investigator claim and a wolf check on player_4 as a convenient defense when
> cornered about surviving double attacks.*

So the game had one exact source of information and nobody contested it. When the investigator spoke, the
day was settled; when it did not, there was nothing better than votes and behaviour (§2.5). Making the
investigator braver would not help. The game needed several imperfect sources, and a real way for evil to
contest them.

**What was done.** Three steps, cheapest first.
- *Prompt changes* (2026-10-03): players told how turn-taking works, the summary no longer asking who was
  quiet, shorter messages, and permission for evil to claim. Two games were judged against three before;
  at that size any difference is a direction to look into, not a measured effect (§6, §6.1).
- *The day redesign* (2026-10-07): an opening round in which every player may claim, counterclaim or
  report a night result; reactive turns for whoever is asked or accused; a closing defence for the
  most-accused ([the discussion report](discussion/report.md)).
- *The ten-seat cast* (ruled 2026-10-07, wired 2026-10-09): three partial observers in place of one exact
  investigator. The Sentinel sees who came to a player, the Trailseer where a player went, and the
  Investigator learns only "Suspicious" or "Not suspicious". Evil muddies them with true mechanics, a block
  and a conceal, never a false result ([the roles report](roles/report.md)). The second need, evil
  contesting, is Problem 5.

**What the evidence shows.** The new mechanisms run as designed, in read games. On the nine-seat game the
opening produced no contest: in four test games 5 of 106 opening turns were spoken, all by the
investigator or the vigilante, and no evil player claimed. On the ten-seat cast, across balance batches 2
to 4 (18 games, flash-lite), 13 of 30 evil lynches had a night observation of the seat behind them and 17
had none: after the caps on checks and watches, the day decided most games. Six games on the stronger
`gemini-3.5-flash` showed real claim contests and covers broken by cross-examination (§8.4). These are
counts of mechanisms and readings of games, not a measure of discussion quality.

**What is still open.** Whether contested claims make better discussion, the aim the cast was built for,
has been read in games, not measured: discussion quality on ten seats has not been compared with the
nine-seat game. Homes: [discussion_evidence](discussion_evidence.md) §1–2 (the census),
[the discussion report](discussion/report.md), [the roles report](roles/report.md).

## Problem 3. Reasoning failures: the facts absorbed, the first step missed

**What it looks like.** In a ten-seat game of 2026-10-14 (`2f19d908`, Claude Haiku 5.5 at low thinking in
every seat), the healer was roleblocked on night 1. On day 2 the trailseer reported seeing player_7 go to
the healer, and player_7 admitted the visit. Only the Chanteuse, a wolf, can roleblock. The healer wrote
every premise into its notes three times, never named player_7, and passed all three turns (case R1 in
[the deduction log](deduction/experiment_log.md)). In a served game two days later (`645228e7`, Haiku
5.5), three town seats read a serial-killer attack that the healer saved as making its target "likely
town". From there they read the investigator's Suspicious check on that target as a frame, and the town
voted out the real investigator 6–1 (R9). In the ten ten-seat games read against a rubric, a conclusion
that does not follow from correct facts was the commonest kind of error, with 28 cases
([factual_errors](../evaluation/factual_errors/report.md), step 1).

**What it traced to.** The facts were in the prompt and correctly stated; the seat did not take the first
inferential step from them. This is Problem 1's reasoning slip, seen in decisions as well as statements.

**What was done.** Four levers were tried against the same failures before any code was written:
- *A higher thinking budget* (Haiku at medium against low) moved votes: 98 of 160 right against 65 on 16
  frozen vote cases. The notes and discussion turns stayed within noise (Problem 1, the last row).
- *A stronger summariser* (Sonnet 5.5 for the day summary) was not better: 18 of 30 summaries flawed in
  each arm.
- *A rewritten private-note prompt* was worse: 27 fact errors against 15 in 56 samples per arm.
- *A majority of three low-effort votes* was right as often as one (39% against 41% of cases). The
  errors repeat across samples, because the model holds the same wrong belief each time it reads the same
  context.

Letting a seat call code for facts on request was weighed and rejected: the facts are deterministic and
already in the prompt, so a tool adds a round trip per turn and no information.

The majority-vote result is the case for code. The missing step is deterministic, so it can be written
down once rather than sampled for. The **deduction engine** (deployed 2026-10-19) works out, from what a
seat already knows, every conclusion a careful human would draw, and writes it into that seat's prompt.
Each line is graded in its own wording: certain, true if named claims are true, or a complete list of
possible explanations. It reads only what the seat may already see, so it opens no second leak path, and
no line may state as certain what some legal game would make false. For R1's healer it now writes: "You
were roleblocked: your protection of player_5 did not happen. Only the Chanteuse could roleblock that
night, and a block is a visit, so the Chanteuse, a wolf, came to you that night."

**What the evidence shows.** The engine removes the step it targets, and does not by itself change what a
seat does.
- On the R1 turn, all ten low-effort replays with the line injected wrote the conclusion into their notes,
  where none did as played. The seat still spoke in 0 of 10, held back by its own note (Problem 4).
- On a second known failure, an investigator's day-3 vote against the healer who had protected it, 5 of
  25 votes still went to the healer with the engine and today's closing line in place.
- The tests establish soundness, not coverage. Random games and an exhaustive search over every legal deal
  check that no stated conclusion is false (`tests/engine/deduction/`); four acceptance cases, rebuilt from
  real failures, are the only test of what the engine misses.

**What is still open.** No town-side effect on outcomes is claimed: a paired whole-game comparison of the
town with and without the engine has not been run. Whether the engine's lines outrank a contrary note was
measured only on the four acceptance cases. Seats also recite rule sentences as all-purpose reasons to
discount evidence ("a follow only shows where someone went"; R11, open), and the engine's lines carry the
same risk. Home: [the deduction report](deduction/report.md); the case register R1–R14 is in
[its log](deduction/experiment_log.md).

## Problem 4. Silence: turns not taken, and results not shared

**What it looks like.** Three kinds of silence, with different causes.
- *Silence made by the engine.* In the 28 nine-seat games of 2026-09-17, which ran on the scheduler
  designed in June, players passed 517 times; 367 of those passes were a novelty judge holding the line,
  and nobody at the table could tell ([discussion_evidence](discussion_evidence.md) §2.4). A day ended
  after three passes in a row, so day 1 ended after three players in 28 of 28 of those games (and in 8 of
  9 games on the website), and on 8 of 96 voting days a living player was never offered a turn.
- *Seats passing while holding a result.* R1's healer (Problem 3) passed three turns holding the fact that
  would expose the Chanteuse. In the served game `645228e7` (2026-10-16, Haiku 5.5), days 1, 2 and 4 had
  no speech at all. On day 4 all four survivors passed, including the vigilante whose shot had killed the
  illusionist; it never claimed and was voted out (R12).
- *Worthwhile lines held back on the open floor,* found by the silence calibration below.

**What it traced to.**
- *The engine's:* a novelty judge on volunteered turns, and a day that ended after three passes.
- *R1's:* the seat's own carried-forward note, "Stay quiet on day 2 unless addressed". With that note the
  healer spoke in 3 of 30 samples; with a neutral note carrying the same facts, 9 of 20 (Fisher p =
  0.007). Removing a survival sentence from the healer's card changed nothing (6 of 20 either way).
- *R12's:* the opening round's rule that passing is the normal answer, together with notes that said "stay
  hidden" ([the deduction log](deduction/experiment_log.md) §7).
- *The open floor's:* a calibration on 2026-10-18 drew 162 turns from 16 ten-seat Haiku games and replayed
  each sampled pass once with "do not pass this time"; blind judges classed each line. Lines the players
  had held back were worth hearing 57% of the time (23 of 40), and lines they posted 52% (13 of 25), so
  speaking or passing did not separate value. Cutting one sentence, "a pass costs nothing here", doubled
  open-floor speech (20 of 64 turns to 41 of 64), but restatements rose with the worthwhile lines.

**What was done.**
- *The day redesign* (2026-10-07): every player is asked at the start of every day; the open floor goes
  round each player who has not spoken; the day ends when those rounds run out, not after three passes.
  The novelty judge survives only as the echo gate on open-floor lines. A held line reaches no prompt,
  opens no debt and counts for nothing in the closing.
- *The silence ruling* (2026-10-18): players speak by default on the open floor, and the echo gate sorts,
  holding restatements and filler. The opening stays as it was.
- *Votes with a reason* (2026-10-12): a town seat on a voting day's open floor is asked to decide its vote
  and, if it has not said why, to say it. On 25 frozen turns, passes fell from 24 to 16.

**What the evidence shows.** On the 65 judged open-floor lines, the gate as shipped holds 10 of 29
restatements and none of 36 worthwhile lines. In four ten-seat Haiku games on the deals of four earlier
ones, the share of open-floor turns spoken rose from 41 of 100 to 54 of 93, and all 7 held lines restated
a line spoken shortly before. One judge read each line, each cell had 23 to 46 turns, and a forced line may
differ from what a player would say by choice.

**What is still open.**
- *The opening still treats passing as normal.* What opening passes held back in the calibration was mostly
  a role claim or a night result the seat chose to keep (10 of 15 worthwhile forced lines). Whether seats
  should claim earlier is a separate question, and R12 stays open in the register.
- *The note behind R1's silence* is a cross-role issue in how notes are carried forward. No fix has been
  adopted; the rewritten note prompt was screened and was worse (Problem 3).
- *One missing tag can silence an accused player.* Once, accusations against a player carried no tags, so
  its defence met the echo gate without the exemption for answering an accuser, was held, and the player
  was voted out as a villager without having spoken (seen once, 2026-10-07).

Homes: [the discussion report](discussion/report.md), decisions 12–14, 16 and 20, which is the home of the
silence ruling; the [silence calibration](data/silence_calibration/README.md); R1 and R12 in
[the deduction log](deduction/experiment_log.md).

## Problem 5. Evil never contesting: denial, never a rival claim

**What it looks like.** Across the 28 nine-seat games, no wolf and no serial killer ever claimed a role
(Problem 2). Denial was the only defence, and a denial gives the town no rival story to weigh. The habit
outlived the cast change. In the served game `645228e7` (2026-10-16), an illusionist said "I'm not the
investigator" in three of its four messages, denying a claim nobody had put to it (R10). In four Haiku
games of the silence calibration, 2 of 12 evil seats claimed, and the seats that denied a sighting were
voted out.

**What it traced to.** The role cards. The nine-seat wolf instructions never mentioned bluffing, though the
shared rules allowed any claim, and the ten-seat cards of 2026-10-09 said that staying unclaimed was a
fine cover. With nothing contesting the town's information, half of Problem 2's root cause stood.

**What was done.** Three changes to the evil role cards, then facts from the engine:
1. *Permission* (2026-10-03): a paragraph saying an evil player may claim a town role, with the risks,
   written as facts rather than an order. No evil claim in either of the first two games with it: at two
   games, no change seen, not a measured null.
2. *A cover story* (2026-10-09, ten-seat, flash-lite): never explain a visit with what you really did, and
   keep a cover in your strategy note. Evil claims went from 4, 8 and 4 in the three earlier balance
   batches to 19 in batch 4.
3. *Claim, never deny* (ruled 2026-10-18, Haiku 5.5): a denied sighting reads as a lie and gets you voted
   out, so claim a role whose night action explains the visit, and plan that cover before it is needed.
   Under the new card, an Illusionist a Sentinel had seen answered: "I'm the healer. Last night I protected
   player_5, which is why they were saved, so that's the visit your watch saw."
4. *The engine's evil-seat lines* (deployed 2026-10-19): which roles the seat could claim without a public
   contradiction, and night stories that fit its real nights. Facts only; the advice stays in the cards.

**What the evidence shows.**
- *The card text, on frozen turns.* On 41 pressured evil turns from earlier Haiku games, replayed twice per
  arm on Haiku 5.5 at low thinking, claims rose from 13 to 33 and denials fell from 21 to 3.
- *The engine's share, on the same turns.* With the new card in every arm, the cover lines moved claims
  from 36 to 44, and claims contradicting a reported sighting from 4 to 1.
- *In whole games.* In eight paired Haiku games on fixed deals, the evil seats that claimed rose from 3 of
  24 to 11 of 24, and the wolves won 3 games against none.

How far these reach: one blind judge per line, and the steps had different judges, so counts compare
within a step, not across (under the pooled labels the "before" arm has 19 denials, not 21). The paired
games bundle the cards, two engine changes and everything else committed between the two builds. They
show a direction, and only the frozen-turn screen separates the cards from the engine.

**What is still open.** Reading the three wolf wins showed what the town now lacks: judgement between two
claimants, not facts. A follow-up engine line that spelled out each counter-claimant's results was screened
on 10 town vote turns and changed nothing (12 votes for the fake claimant without it, 12 with it), and was
dropped. No balance batch has run on Haiku 5.5 or on today's rules, so whether evil now wins too often or
too rarely is unknown. A paragraph on cover risk, added after a served game of 2026-10-19, has been checked
by prompt tests only. Homes: [the roles report](roles/report.md), "The evil contest"; the engine's share in
[the deduction report](deduction/report.md) §4.

---

## What is unresolved across the area

Each component report lists its own gaps. These are the ones that cut across the area.

| Gap | What it leaves unknown | Home |
|---|---|---|
| No factual-error rate on the ten-seat game | How often errors happen today. The only rate is July's, nine-seat, on an older prompt; every ten-seat number is a replay of known failures or a hand audit | [factual_errors](../evaluation/factual_errors/report.md), "What is not measured" |
| No measured bar for discussion quality | Whether the redesigned day and the new cast made the talk better, and whether a later change makes it worse. Checks so far are small studies and read games | [discussion](discussion/report.md), "What is not established"; [roles](roles/report.md), same section |
| No balance batch on Haiku 5.5 | Whether each side still wins sometimes on the model the site plays and today's rules. The four batches (31 games) ran on flash-lite before the evil-card ruling, the engine and later rule changes | [roles](roles/report.md), "Balance" |
| The speech-act tags | The scheduler and the closing defence run on tags each speaker writes about its own message. Against a judge they missed accusations on 24 of 183 nine-seat messages, and no standing test checks them | [discussion](discussion/report.md), "What is not established"; [discussion_evidence](discussion_evidence.md) §9, items 8–9 |
| No whole-game effects of the interventions | Whether the engine helps the town win, whether the closing defence changes votes, and how the evil gains split between cards and engine in games. The evidence is frozen turns at small N, and one bundled set of eight paired games | [deduction](deduction/report.md) §5; [roles](roles/report.md) |
| Single-game replays move a lot | In one vote replay, adding true facts to the ballot lines moved per-case vote counts by up to five of ten samples in both directions, more than most effects tested on those cases. A one-game replay shows a direction at best, and today's prompt as a whole has never been compared with an earlier one | [turn_prompt](turn_prompt/report.md), "What is not established" |
| The judges | The Claude Haiku 5.5 judges, default since 2026-10-12, have no recorded check against people; several screens were labelled by chat subagents, with agreement between judges not measured | [factual_errors](../evaluation/factual_errors/report.md), step 4; [deduction](deduction/report.md) §5 |
| The rules text | Seats recite rule sentences as arguments (R11, open), and the rules still say openings are played in an order drawn at random while the code publishes them in seat order | [turn_prompt](turn_prompt/report.md), [discussion](discussion/report.md) |

*Started 2026-10-24 with Problem 1. Rewritten 2026-10-26 as the area overview: the map, the version line
and problems 2–5 were added from the component reports, Problem 1's thinking-budget rows name their model,
and its results row carries the ten-seat wording. No experiment was run for this page.*
