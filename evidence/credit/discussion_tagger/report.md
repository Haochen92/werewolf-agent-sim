# The discussion tagger: an LLM judge for discussion credit, retired

> **Write-up: not used. No detailed read needed.** Owner ruling 2026-10-22: the tagger stays out of the
> write-up; at most one plain sentence in the credit topic ([map](../../../writeup/_planning/map.md), folder walk).

A decision record from the v7 memory loop of June and July 2026 (the nine-seat game). The loop's
**credit** step scored each lesson a player had chosen to follow by whether the decisions it led to were
good. Votes and night actions could be scored by rules; day discussion could not. The tagger was a
language-model judge built to fill that gap. It was used for credit from 2026-06-20 and retired on
2026-07-13. The full path, with every number, is in the [experiment log](experiment_log.md); how far the
tagger can be trusted is in the [LLM-judge note](../../evaluation/llm_judge/discussion_tagger.md).

## In short

- **Question:** could a model judge give memory credit for day discussion, where rule-based checks could
  not?
- **Test:** the tagger was built on 2026-06-19. It was checked on 8 games for whether it only copied the
  free vote-based signal, and on 24 games for whether its verdict predicts the deceivers' win beyond the
  vote record, with the outcome hidden from it.
- **Answer:** it measures something real about how wolves and the serial killer talk. That was never shown
  to make memory better: no test ran with wolf memory on against off. A town gain once read off its credit
  was retracted.
- **What followed:** on 2026-07-13 the owner retired it from credit in favour of rules. It survives as a
  diagnostic that can be run on stored games. It feeds no credit and runs in no game.

## Why it was built

**Credit had no signal for talk.** Credit is *de-lucked*: a decision is scored against the true roles
the engine knows, not against who won, because a sound vote can sit in a lost game. A vote can be scored
this way: it lands on a real wolf or it does not. A night action can too. A speech has no single board
action to hold against the truth, so a wolf's lessons could be rewarded for its votes and kills but never
for its deception.

**Two free attempts failed first (2026-06-18 to 06-19).** Both used the stance tags (accusation, defence,
agreement) that every message already carries.

- *Did wolves lead the town onto the wrong player?* Over 180 existing games, a wolf's "lead score" (how
  early it accused the town player who was then voted out) did not track wolf wins (r = −0.09, p = 0.51,
  53 games). It also barely happened: in 127 of 180 games no wolf ever accused that player.
- *Score an accusation as a vote.* After requiring at least 3 accusing turns per lesson, only 41 lessons
  could be scored, too few to test, and what they measured repeated the vote score.

The best free signal was cruder: credit every speech by whether that day's vote went the speaker's side's
way. It covered 100 lessons and predicted held-out game outcomes almost as well as the board measures
(Pearson +0.51 with n = 51, against +0.54). It became the free floor the tagger had to beat. It
is blind to one thing deceivers do: they often kill a power role at night without having drawn any
suspicion onto it in the day (the record gives 71% for wolves, 62% for the serial killer).

**Why no rule could do the deceivers' half.** Most town talk pays off in votes, which rules score. A
deceiver's skill is concealment and being believed. The obvious concealment score, how many votes a
serial killer drew, just restates whether it was caught: a score that secretly tracks who won (the log
calls this a *halo*). Whether a story was believed leaves no trace on the board at all.

## What it was

At the end of each game day, one call to a cheap model (`gemini-3.1-flash-lite`, temperature 1.0) read the day's talk with
every player's true role, that day's vote and the night's deaths. For each player it returned:

- a **discussion verdict** (positive, neutral or negative): did this player's talk help their own side,
  judged apart from how the vote or game went;
- a **night verdict**: was their night action a read the day's talk justified, or a blind or lucky pick;
- **detail tags** (framing, believability, role claims), the evidence the discussion verdict weighs.

Only the two verdicts were credited, and never the win: a positive verdict counted as positive even in a
lost game. Each player's private reasoning was shown to the tagger only to work out what a decision was
based on, never to grade it; the prompt enforced this, not code. The design record is
[`discussion_credit_design.md`](../../memory_system/v7/discussion_credit_design.md).

## What was learned

**1. The first version copied the free signal (2026-06-19, 8 games).** Judging discussion merit alone, its
verdict correlated +0.55 with the free floor and +0.21 with who won. Making the verdict weigh the detail
tags cut those to +0.34 and +0.11. The night verdict re-scored about 31% of night actions against the
outcome-only rule: 30 justified misses credited, 12 lucky hits demoted. With that, discussion credit
switched from the floor to the tagger on 2026-06-20.

**2. A town gain was retracted (2026-06-23).** A "+0.556 discussion gain" for the villager's discussion
lessons was read off the credited store after the loop's second run. It was a raw credit level, never
compared with the games played without memory. The tagger gives positive verdicts with or without memory,
so the level says nothing about what memory added. A cache bug made it worse: games with and without
memory shared game ids, so the no-memory games were scored with the memory games' tags. Compared properly
through the free floor, the villager's discussion difference was noise (mean about −0.12 over six
generations).

**3. The verdict does measure deceiver talk.** On the 24 memory-on games of that run, with the outcome
hidden from the tagger and message length removed, its discussion verdict predicted the win beyond the
vote record for wolves (+0.56) and the serial killer (+0.60), not for town (+0.02), as a partial
correlation. The leak test and the limits are in the
[LLM-judge note](../../evaluation/llm_judge/discussion_tagger.md). The +0.56 is a different quantity from
the retracted +0.556: a correlation with winning for wolves, against a credit level for town.

**4. Three silent failures were closed (2026-07-02).** A failed day now logs an error (or raises in strict
mode); a missing input file warns; and the tag cache key now carries the run's identity, so one set of
games can no longer be scored with another's tags.

**How sure we are.**
- Every result comes from the nine-seat game played by `gemini-3.1-flash-lite` at zero reasoning tokens,
  with one tagger prompt version.
- The correlations rest on one run of 24 games and show a measure, not a memory effect. The run itself gave
  every faction memory by mistake, so it could not answer whether town memory helps.
- The detail tags were never checked against people's labels and no per-tag accuracy number was saved;
  the night verdict's own read-quality tag had no check of any kind. The night verdict still sees the
  death its own kill caused; that leak was never tested.
- The 24-game and leak results were printed, never saved to a file; the durable record is the v7 log,
  section "12g. TAGGER LEAK/VALIDITY INVESTIGATION" ([log](../../memory_system/v7/experiment_log.md)).

## The retirement (2026-07-13)

The [credit redesign](../read_tactic_credit_redesign.md) of 2026-07-11 proposed it and the owner ruled on
2026-07-13. Its reasons: a verdict that correlates with winning in one 24-game study supports a diagnostic,
not using that verdict to decide which lessons survive; the night override had no independent accuracy
check; and one end-of-day judgement cannot say whether a player's belief or their action was wrong.

Discussion credit became rules: the day-vote floor, refined when a player's own accusation is where the
vote landed, plus a guarded concealment score for deceivers' concealment lessons. Night credit went back
to the rule-based scorer. The redesign's section "Discussion: use an observable endpoint, retain influence
as a diagnostic" gives the details. The code change landed on 2026-07-15 (commit `05fcad20`), removing the
tagger's credit ledger and the switch between floor and tagger. The owner signed the July v7 run's rules
on 2026-07-16, before any of its games, so no v7 result rests on tagger credit.

## Where it stands today

- **Code:** `evaluation/src/loop/discussion_tagger.py::tag_game` (with `tag_game_cached`), run through the
  validation runner `evaluation/src/cli_runner/discussion_tagger_eval.py` (`eval-tagger`). Nothing in the
  game, the server or today's ten-seat credit (`Agents/memory/consolidation/`) calls it.
- **Model:** the runner pins `gemini-3.1-flash-lite` by default. Called directly with nothing pinned, the
  tagger would now run Claude Sonnet 5.5, the default of `Agents/llm_factory/accessors.py::get_llm_pro`.
- **Never done:** a test with wolf memory on against off, which is what turning the measure into a memory
  result would need.
