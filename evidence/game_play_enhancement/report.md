# Gameplay problems and what we tried

This page covers the main problems in how the AI players play: what went wrong in real games, what each
problem traced to, what was tried against it, and what worked. How the errors were found and measured is
not here but in the evaluation reports: [factual_errors](../evaluation/factual_errors/report.md) for
statements the record contradicts, [llm_judge](../evaluation/llm_judge/report.md) for the judges. The full
design record, with every ruling, game and replay, is [discussion_evidence.md](discussion_evidence.md).

*Started 2026-10-24 with the first problem; the others are listed at the end, to be written when this
folder is walked for the write-up.*

## Problem 1. Factual errors: players stating what the record contradicts

**What it looks like.** A player claims a check it never made, hunts "the last wolf" when both wolves are
dead, misquotes who voted for whom, or repeats a claim the day summary invented. In July 2026 about 3% of
public messages carried one (nine-seat). On the ten-seat game, inventing facts had become rare; the commonest
errors were bad reasoning about what an ability can see, and the summariser distorting plain claims.

**Why it matters.** One error can decide a game. On 2026-10-03 the investigator announced a check it never
made, the village voted out an innocent player on that claim, 4 to 1, and the serial killer won.

**What it traced to.** Five causes, diagnosed case by case: *making things up*, *a reasoning slip*,
*misreading* correct information, *losing track* of what has happened, and *missing or confusing input*.
They overlap: a player reasoning well from a corrupted summary makes no error of its own. The diagnosis and
the cause of each symptom are in [factual_errors](../evaluation/factual_errors/report.md), step 3.

**What we tried, and what worked.** One pattern held across the fixes. Telling the model to take more care
with facts it already had did not change what it wrote. What worked was changing what it was given, or
moving the check out of the model into code.

| Change | What it did | Result |
|---|---|---|
| **Telling the model** | | |
| Cite the record exactly (2026-10-04) | Every day turn: keep each past vote, death and save exactly as the record has them | Vote misquotes 24 before and 24 after (16 cases better, 18 worse, p = 0.86); reverted the same day |
| The vote history laid out per player (2026-10-04) | The same votes, rearranged by voter | 26% → 21% of messages bad, within noise (p = 0.69); reverted with the rule above |
| The summariser checks each accusation against the record (`record_check`, 2026-10-03) | Cite the record wherever it contradicts the accusation | All 27 written were wrong (October 16 replay); removed 2026-10-16 |
| A rewritten private-note prompt (October) | Asked for a more careful note | Worse: 27 fact errors against 15 in 56 samples; not adopted |
| **Giving it the fact, or moving the check to code** | | |
| Results reworded (October) | "Night 3 (last night): you investigated player_5, who is the healer" | The invented check: 20 of 20 samples → 0 of 20 |
| The July bundle | A printed line of the roles still alive, a board of the dead, and more | Error-prone turns 48% → 30% wrong (p = 0.003) |
| Each agent's own night record; engine facts labelled apart from summaries (2026-10-03) | The engine writes what each seat did and learned at night | Part of the October fixes: 97 → 82 of 267 bad, a direction (p = 0.14) |
| The claim ledger, kept by code (October) | The summariser only transcribes claims; code checks them against the engine's facts | The repeated invented claim: 5 of 5 samples → 0 of 5 |
| The deduction engine (deployed 2026-10-19) | Code works out the conclusions a seat can draw and hands them over | On the replayed turn, every note records the fact, against none as played ([reasoning_failures](../reasoning_failures/report.md) §4) |
| A higher thinking budget (October) | More reasoning before the answer | Bad samples 82 → 27 of 267, for reasoning slips |

The results are on frozen turns replayed many times, except the July bundle's, which was a test fixed before
its data existed; how those replays are run and judged is in
[factual_errors](../evaluation/factual_errors/report.md), step 4.

**Why telling did not work.** On the vote misquotes, the record was already in the prompt. The model wrote
the point it wanted to make and filled in the supporting vote from impression, and an instruction to copy the
record did not change that ([discussion_evidence](discussion_evidence.md) §6.6). A request to cite produces
prose that nothing checks. A citation helps when something checks it: making the cited fact a structured
field that code compares with the record is the first change in the factual_errors report's "What we would
do differently next time".

**Where it stands.** Every fix in the second half of the table is live except the higher thinking budget:
the seats run Claude Haiku 5.5 at low thinking, and medium for votes only is an open decision for the owner
([reasoning_failures/experiment_log.md](../reasoning_failures/experiment_log.md) §2). No factual-error rate has been
measured on the ten-seat game; the known failures are replayed after each fix, and new ones are still found
by playing.

## Other problems, to be written

- **Thin talk.** Accusations rested on votes, silence and speaking order rather than on weighing claims
  ([discussion_evidence](discussion_evidence.md) §1–2), which led to the discussion redesign (§3–7).
- **Reasoning failures.** Seats absorb facts but do not take the first inferential step; the deduction
  engine is the answer, written up in [reasoning_failures](../reasoning_failures/report.md).
- **Silence.** Whole days with no speech, and seats that pass while holding a result
  ([reasoning_failures/experiment_log.md](../reasoning_failures/experiment_log.md), R1 and R12).
- **Evil never contesting.** No evil player faked a role claim, so town's information was never contested;
  the deduction engine now gives evil seats facts for a cover ([reasoning_failures](../reasoning_failures/report.md)
  §4, "The evil side").
