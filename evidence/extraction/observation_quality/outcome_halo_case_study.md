# Case Study: the Outcome Halo in Observation Extraction, with Ground Truth

**Scope:** two observations extracted from one human-seat game, graded by the extraction judge, where
the graded player is the project owner and can attest what each action was trying to do. The only
case in this archive where intent is known rather than inferred.
**Date:** 2026-07-26 · **Branch:** `feature-dimension-schema` (working tree ahead of `7b891fe`).
**Run:** game `447cbe95-9173-4a1e-a76b-9a3e9201141a`; seats on `gemini-3.1-flash-lite`, extraction on
`gemini-2.5-pro` with the per-cell v6 dimension schema, memory retrieval off, the human seat the
serial killer.
**Artifact:** `outcome_halo_human_game.json` (FROZEN RECORD): all 12 observations the game
produced. They were deleted from the live store the same day, because human games are never mined;
this copy exists only as evidence.
**What happened since:** the halo was measured at scale and ruled on in October 2026; see the note at
the end.

> **What is being graded.** After a game, an extraction model reads the whole transcript, every role
> and the outcome, and writes 4 to 8 observations per role: what the player did and what it led to.
> Each observation carries a judgement, `net_verdict` (positive, negative or mixed), with a rationale,
> `impact_on_final_game_outcome`, written from the end of the game. That verdict never reaches a seat
> or the credit system. It reaches two places: dedup, where two observations with different verdicts
> are never merged (the contrast is the lesson), and strategy synthesis, which weights a cluster of
> observations by the spread of their verdicts. So a verdict that grades the wrong thing changes which
> lessons survive and which way they point.

## The specimen

Both entries are lifted verbatim from the artifact, serial killer, night-action cell. The serial
killer wins by being the last killer standing, so killing a wolf is its best possible night.

**Entry 1. Night 1, nine alive, no information yet.** The kill happened to hit the vigilante.

> **approach:** "Made a speculative, information-less kill on the first night, which happened to
> eliminate the Vigilante."
> **impact_on_final_game_outcome:** "Negative. By removing the Vigilante, you eliminated a chaotic
> village-sided role that could have caused mis-lynches, **benefiting your solo win condition**.
> Simultaneously, **the wolves killed the Investigator**, meaning the two strongest village power
> roles were removed at once, accelerating the wolves' path to parity…" (emphasis added)

The rationale's first clause says the kill helped. The verdict is then reached by adding in the
wolves' own night kill, an event this player neither caused nor could see. The judge graded the
night's joint outcome, and charged it to one player's ledger.

**Entry 2. Night 2, seven alive, the player publicly under suspicion.** The kill removed a wolf,
identified from how that player had talked by day.

> **approach:** "Targeted and killed a player **correctly identified as a wolf** based on their
> aggressive, information-forcing behavior during the day's discussion."
> **impact_on_final_game_outcome:** "Negative. Although eliminating a rival wolf is beneficial in a
> vacuum, doing so while you were the primary lynch suspect was a fatal error. This action **removed
> a viable alternative target** for the village, allowing them to consolidate votes on you the next
> day…" (emphasis added)

The entry concedes the read was correct and the kill was the role's win condition, then calls it a
fatal error on a counterfactual: that the village would have lynched the wolf instead. The day record
does not support it. That player was only revealed as a wolf by the death announcement, and the votes
against the human seat had already formed the day before. The player was lynched the next day and
lost, and the verdict works backward from the loss. From the seat: the kill was a deliberate, correct
priority call.

## What the two entries show

Two distinct ways a verdict written from the end of the game grades the result instead of the
decision:

- **Attribution across factions.** Entry 1 bills another faction's simultaneous action to this player.
- **Back-propagation from the loss.** Entry 2 starts from "this player lost" and constructs a causal
  story in which the best move was the mistake.

Neither needs a human player to happen. Both are properties of grading with the outcome in hand, and
both fit what the earlier calibration study found on 932 agent-game observations: the verdict tracks
whether the faction won far more than whether the move mattered
([`experiment_log.md`](experiment_log.md), this folder). What this case adds is that
the grading is wrong against known intent, not merely correlated with the outcome.

For context, not as a result: all 12 observations from this game were graded negative except one
mixed, across the two roles that both died.

## What this case does not show

- One game, two entries. A mechanism exhibit, not a rate. How often the judge disagrees with a
  deterministic grade on agent-only games was not measured here (it was, later; see below).
- Human play is out of distribution for an extraction prompt written for agent transcripts. The two
  mechanisms do not depend on who played, but an error on this game is not an error rate on agent
  games.
- Nothing here touches the memory A/B results of the time. The verdict never fed credit, so the v7
  measurement stands on its own instrumentation.

## The call at the time

No pipeline change: memory research was closed and the live game shipped memory off. The case was
recorded as the sharpest illustration of why the credit redesign had moved every grade to
deterministic anchors (day credit from vote endpoints, reads credited by accuracy) and demoted model
judgement to a diagnostic. The direction it argues for store-building: grade a night kill by its
mechanical consequences (the target's true faction, the votes that follow), not by a model's
post-hoc story. What would weaken it: a golden-set audit showing the judge agreeing with deterministic
grades at a high rate on agent-only games.

## What happened since (note added 2026-10-14, corrected 2026-10-26)

The test this case asked for was run in October 2026 on the ten-seat game, once a deterministic
grader existed for every decision: on 1,472 observations from 40 games, a move the grader marks good
was called positive 83% of the time on the winning side and 23% on the losing side, and a
second-model pass, de-halo, which rewrites the verdict word with the outcome text still in view,
halved the praise for winners' bad moves (18% to 9%) but left that gap at 75% against 21%. The
measurement is in [the observation-quality report](report.md) §4, "How strong the halo is, and what
de-halo does". (Until 2026-10-26 this note joined two fits: the 1,472-observation weights with the
482-observation result that de-halo worked "only on the losing side". On all 1,472 observations it
also cut the winning side's praise for bad moves.) The rulings (`evidence/memory_system/v8/decisions.md`
§13):
every observation now names the decision it describes, so it can be graded; each stores both the
verdict and the deterministic grade; which one synthesis should read is a config flag, with the
verdict variant shipping and the comparison designed but not yet run. Credit was never a consumer and
remains deterministic.
