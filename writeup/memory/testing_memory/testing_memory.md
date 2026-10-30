# Testing whether memory helps (Level 2, draft)

Drafted 2026-10-27. Rewritten 2026-10-28 on the owner's structure: the verdict first, then what each test
led to (only what survives in today's design), then what the next test needs. The learning loop's
amendment and the method detail now live only in the Evaluation chapter. Claim scope is recorded in
[`../memory_presented_set.md`](../memory_presented_set.md) (the Effectiveness row, extended
2026-10-28).

---

## Testing whether memory helps

A memory pipeline can write plausible lessons, retrieve them and get players to follow them without making
their decisions any better. To test that benefit, I compare games played from the same starting deals with memory on and off.

**Memory has not been shown to improve play.** I ran three rounds of comparisons on the earlier nine-seat
game. A fixed store in June improved some town decisions without establishing a benefit, a rebuilt store
showed no clear gain, and the learning loop's finished memory leaned toward worse play. Today's ten-seat
memory has not been compared with memory off at all.

The tests were still worth running. None settled the question, but each result, read with the game logs
beside it, pointed at the next thing to fix: sometimes in how I ran the comparison, sometimes in the
pipeline itself.

### What each test led to

| Test | What it showed | What it led to | In today's design as |
|---|---|---|---|
| Early batches (about 30 unpaired games a side) | Results that did not repeat: the town won 29 of 30 with memory in one batch, then gained nothing on the next store; a pilot whose store kept growing during the test looked like harm | Play the same deals with and without memory, freeze the store, and play the memory-off games in the same time window | The comparison controls |
| June fixed store (30 deals played twice) | Promising but inconclusive: the healer saved the attacked player more often (37% → 60%) and town eliminations hit an enemy more often (47% → 64%), but none of the 24 comparisons stayed significant once corrected for how many there were, and memory-off reruns of the same deals the next day scored about as well as the town had with memory | Choose one main measure and a few supporting ones before looking at results | One main measure, chosen before the games |
| | No benefit detected for the wolves or the lone killer | A win can hide bad play and a loss good play, most of all for the deceivers, so judge advice by the decisions it shaped, not by who won | Credit grades decisions, not results |
| Rebuilt store (30 deals played twice) | No clear gain; with lessons, the town's decision measures trended worse, none significantly | Many lessons repeated the town's own weak play, and a store that never changes cannot repair them | The learning loop: credit and pruning |
| First learning runs | One run measured lessons against a distorted baseline; another gave memory to every faction instead of the town | Check that the arm which ran is the arm requested, and simulate how many games a test needs before paying for it | The arm check and the sample-size check |
| Learning-loop endpoint (30 deals played twice) | The finished memory leaned toward worse play | A lesson to sit out the vote had survived pruning because every town abstention was graded neutral | Today's credit rules |

The first rows taught me how to run the test; [Designing fair comparisons](../../evaluation/fair_comparisons/fair_comparisons.md)
tells that part in full, including the baseline that shifted between run periods. The last rows changed the
pipeline, and two of them carry the chapter's argument.

**Advice that copied weak play.** On the rebuilt store, town wins moved +6 points with observations
(p = 0.77) and −7 with lessons (p = 0.75), and with lessons the town's vote accuracy and correct
eliminations both trended down, though not significantly. The numbers could not say why, so I read the
lessons. Many of the town's lessons repeated its own weak play: keep your findings to yourself, vote with
the consensus. The store was built from the same mediocre games it was meant to improve on, and it had no
way to notice: a lesson, once written, stayed. That reading, not a measured effect, is why the next
version scored each lesson against what happened when players followed it and removed the ones that did
harm.

**A negative result, then a diagnosis.** The learning loop ran four generations and built a store of 168
lessons. Town players received the lessons, while all seats received behavioural hints called *tells*;
the treatment therefore tested lessons and tells together. On 30 deals played with and without memory,
the town's average decision score was 0.147 lower with memory and worse on 19 of the 30 deals
(paired t-test p = 0.065, Wilcoxon p = 0.105): no benefit detected, and an estimate leaning toward harm. That sent me looking at passive advice. A lesson telling
the Vigilante to sit out the vote when the evidence was speculative had survived every credit pass,
because the rules graded every town abstention as neutral, so following it could never count against it.
Today's rules grade an abstention on a day when nobody is voted out as bad, and under them the lesson is
pruned ([The lesson that pruning failed to remove](../curating_lessons/abstention_credit.md)). The
corrected loop was never played, so this is a fix to the scoring, not evidence that the fixed memory
plays better.

### Why effectiveness is hard to establish

Matching deals controls the starting roles, but sampled dialogue and decisions still make the games
diverge. This **sampling variation** can hide a useful effect or produce an apparent gain. A test needs
one main measure, an improvement worth detecting, and enough games to distinguish that improvement
from the variation. A non-significant result alone does not establish that memory has no useful effect.
[Designing fair comparisons](../../evaluation/fair_comparisons/fair_comparisons.md#how-much-a-comparison-can-see)
explains the power analysis used to plan that sample.

The whole-game comparison also cannot locate the cause. Advice may be poor, retrieved for the wrong
situation, ignored, or followed without improving the decision. Reading the traces and checking
individual components can expose those failures, but fixing one does not establish an overall benefit.
That is why the investigations above informed the design without settling whether memory helps.

Evaluation is possible for a bounded claim: whether a particular store and retrieval configuration
improves a chosen measure under a fixed player model. Whether the learning process reliably produces
better stores is a separate, larger question.

### What the next test needs

Two questions are still open, and they need separate experiments:

- **Does today's store help?** Freeze the current store and play matched games with memory on and off.
- **Does learning improve the store?** Preserve stores from different learning generations and evaluate
  them under the same conditions. That tests progress within one learning run. Establishing that the
  process reliably improves stores would also require independent learning runs, since each can produce
  different advice. This experiment also waits on credit, which decides what each generation keeps and
  is not yet tuned for ten seats.

The first step is a small ten-seat pilot to estimate both the variation in paired decision scores and
actual memory-on costs. Before the main comparison, choose a **minimum worthwhile improvement** and use
that estimate to plan the sample size. Smaller effects require more games; the nine-seat results can
inform planning, but cannot fix the sample needed for today's game.

For a rough cost reference, 16 ten-seat games on the player model at low thinking, with memory off,
cost $2.48 in total ($0.08–0.26 per game). At that observed range, 100 games would cost about $8–26
for gameplay alone. This is an illustration, not a proposed sample size or a complete experiment budget:
memory lookups, pilot games and failed or repeated runs add cost. Testing learning also requires
games for each learning generation, offline extraction and synthesis, and evaluation of the resulting stores.
Repeating the learning process adds those costs again.

Whichever size is chosen, four things are fixed and recorded before the first game: the exact store,
the retrieval settings, the player model and its thinking level, and the main measure with how a
difference will be read. The sample size and stopping rule are also set in that plan, kept in the repository.
Until that test runs, memory stays an opt-in feature that players can switch on, not a claimed
improvement.

<!-- Sources and verification, 2026-10-28:
Early batches and pilot: effectiveness/report.md §1 (v3_deduped 29/30 vs 21/30, Fisher p .012, best of
six; v4 74.2% -> 73.3%; v5_1 grew during testing, older baseline, -32pp); detailed_results.md "The v5_1
pilot".
June A/B: effectiveness/report.md §2; detailed_results.md "The June A/B on the v5_0 store" (37.0 -> 59.8
p .005; 47.0 -> 63.8 reported p .028; raw arms before the written pre-registration, 24 tests, none clears
0.002), "Side-findings that shaped later work" (wolf 33 -> 30% p 1.000, SK 40 -> 20% p .146; "a win can
hide bad play ... so v7's credit graded lessons by decision quality"), "The discarded historical
baseline" (Fisher p .0028; never pair against a baseline from another epoch). Low-baseline caveat not
repeated here: the page claims no June benefit; Evaluation's fair-comparisons page carries it.
Rebuilt store: v6_sp_ab/experiment_log.md (town obs +6 p .77; town lessons -7 p .75, town_vote_accuracy
-0.086 and correct_elimination_rate -0.103, p about .19-.25; mechanism 4: town lesson content, quoted
"do not reveal your findings", "vote with the consensus"; caveat: content analyses lexical/qualitative,
judge-confirmation pending). NOT used: mechanism 1's "77% vs 32% abstain" (withdrawn 2026-10-28,
credit/day_matched_baseline/README.md: day-2-heavy follows against an all-day rate) and mechanism 3's
"followed 63-66% vs 69%" (same follows-against-all-days comparison, not re-checked by day). v6's
retrieval-mismatch finding omitted: its fix (field-matching tilt) showed no benefit and is off
(retrieval/report.md).
First learning runs and power: v7/report.md (distorted credit baseline; driver defaulted to all
factions; simulation 11% at 24 games for +0.15).
Endpoint: v7/report.md; 168 lessons; -0.147, 19/30, t .065, Wilcoxon .105; treatment = lessons + tells.
Abstention fix: curating_lessons/abstention_credit.md (Vigilante day-vote lesson, 19 follows, 0.00 as
run; pruned under the no-lynch-day rule at -0.64 all days / -0.38 same days); credit/report.md §2, §6.
Earlier draft planning table (removed from public prose, retained here for provenance; not a ten-seat
sample-size recommendation): evidence/memory_system/v7/execution_plan/data/v7_endpoint_ab/paired_boards.json, per-board
gap mean -0.1464, SD 0.4181 (n 30); margin 1.96*SD/sqrt(n); 80% power n = ((1.96+0.8416)*SD/d)^2 -> 61 for
d 0.15, 138 for d 0.10. Normal approximation.
Cost: gameplay/data/persona_voice_games/README.md, 16 ten-seat games on Haiku 5.5 at low thinking,
memory off, $2.48 total, $0.08-0.26 a game; memory-on cost not measured separately. Public illustration:
100 games x $0.08 and $0.26 = $8-26; no detection power or complete budget is claimed for 100 games.
Editorial follow-up, 2026-10-28: added sampling variation, diagnostic versus causal scope, and fixed-store
versus repeatable learning claims. Removed precise prospective power/margin table from page copy;
its normal-approximation calculations remain above as historical planning notes. Restored lessons-plus-tells
treatment scope and changed no-benefit wording to no benefit detected. Cost reference checked against
gameplay/data/persona_voice_games/README.md; no new games or effectiveness analyses run.
Current state: v8/report.md; memory opt-in (memory_presented_set.md §4). Next tests are proposals. -->
