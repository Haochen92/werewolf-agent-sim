# Memory effectiveness: what each version established

**Memory has not shown a reliable benefit across versions.** An early fixed store improved selected town
measures in one June test, with important statistical and baseline limitations. The next store showed no
clear benefit. The July learning loop's final memory also showed no benefit, with an estimate leaning
toward harm. Today's ten-seat system has not had a memory-on versus memory-off test.

This report is the reference for **effectiveness across the recorded versions and campaigns**: what was
compared, what happened and what can be concluded. The [memory hub](../report.md) explains the pipeline
and its evolution. [Detailed results](detailed_results.md) preserve the June statistics, replay tables,
baseline investigations and source index; the v7 and v8 reports own their respective investigations.
You do not need those details to follow the account below.

## The experiments at a glance

An **observation** describes a move and its effects in a past game. A **lesson**—called a *strategy point*
in code—recommends an action for a situation. A **paired board** starts both conditions with the same
role deal and seed; later play still differs through model sampling and the decisions made.

| Version or campaign | What was tested | Main result | What it establishes |
|---|---|---|---|
| Early `v3_deduped` and `v4` stores | Memory off, wolves only, or everyone; about 30 unpaired games per condition | Town wins rose 70% → 96.7% with everyone's memory in one batch; the next batch showed 74.2% → 73.3% | An unstable early result, not a repeatable benefit |
| `v5_1` pilot | A growing store, unpaired games and an older baseline | Town wins fell by 32 percentage points | Confounded; not evidence that memory alone caused the fall |
| **June `v5_0` static A/B** | Frozen observations; 30 paired boards per condition, with memory assigned to different factions and retrieval settings | Selected town decision measures improved; raw-town win change was inconclusive; no wolf or lone-killer benefit detected | A limited positive result for this store and configuration |
| **v6 A/B (`v6_1` store)** | Observations or lessons for town; observations, lessons or both for the lone killer; 30 paired boards per condition | No outcome comparison reached significance; lessons alone tended negative | No clear benefit; not a replication of v5 because prompts, store and run period changed |
| v7 June learning runs | Memory updated between generations | Two runs invalid for their intended questions: a distorted credit baseline, then the wrong factions receiving memory | Engineering lessons, not valid estimates of learning benefit |
| **v7 July endpoint** | Final learned memory against none, 30 paired boards after four learning generations | Town decision score lower with memory; neither paired test significant | No benefit detected from the finished memory; not a direct comparison between generations |
| **v8 ten-seat system** | Component checks and one credit-pass demonstration | No memory-on versus memory-off comparison | Effect on play remains unknown |

The early game, the rebuilt nine-seat game and the current ten-seat game differ. These rows are not a
leaderboard: changing rules, prompts, stores and models prevents direct ranking of versions by their
win rates. Version names also label stores or pipeline generations, not uniform experimental conditions.

## 1. Early stores: why a controlled test was needed

The strongest early result was town winning 29 of 30 games with memory for everyone, against 21 of 30
without it (`v3_deduped`, Fisher p = 0.012). But it was the best of six comparisons. On the next store
and role/phase organisation (`v4`), the apparent benefit disappeared. Both store content and its
organisation changed, so the batches do not explain why.

The `v5_1` pilot then suggested harm, but its store grew during testing and its memory-off baseline came
from an earlier run period. Neither comparison kept enough fixed to isolate memory. This motivated the
June test's frozen store, fresh baseline and paired starting boards.

The [early-batch tables](detailed_results.md#before-the-rebuild-two-unstable-batches) and
[pilot account](detailed_results.md#the-v5_1-pilot) preserve the figures and qualifications.

## 2. v5: selected town measures improved, with limits

The June 11 test used `v5_0`: observations extracted from 20 memory-off games, then frozen. Each
condition played the same 30 boards. The raw town condition used plain retrieval and ran interleaved
with its memory-off baseline.

Two kinds of measure matter. **Win rate** measures the whole-game outcome but is noisy at this sample
size. **Decision measures** score particular choices against the hidden roles, such as whether an
elimination hit an enemy. They provide more observations but remain proxies: scoring a decision does
not remove every effect of luck or prove that the move was strategically best.

| Raw town condition | Memory off → on | Reading |
|---|---|---|
| Healer protected the actual target | 37.0% → 59.8% | Positive result, p = 0.005 |
| Town eliminations hit an enemy | 47.0% → 63.8% | Positive result, reported p = 0.028 |
| Town votes targeted an enemy | 56.0% → 71.0% | Favourable estimate, p = 0.053 |
| Town won the game | 27% → 43% | Inconclusive, p = 0.267 |

These are **selected favourable results**, not an established general memory benefit:

- The raw arms ran before the written pre-registration. None of their results clears a correction
  across all 24 raw-arm tests. Healer saves do clear the narrower three-measure correction.
- The baseline may have drawn low. Town also improved when only an opposing faction received memory;
  next-day memory-off runs scored near the memory-on town. Opponent effects, sampling and possible
  provider drift are not separated by these observations.
- The measures overlap. Correct elimination and mislynch count the same events in opposite ways;
  they are not two independent confirmations.

No benefit was detected for wolves or the lone killer. A reranked town arm had a larger win increase
(27% → 60%, p = 0.013), but ran after the baseline, leaving a timing confound. Its vote accuracy did
not show an advantage over plain retrieval. That made reranking a lower priority, without ruling out
smaller benefits.

The [June detail](detailed_results.md#the-june-ab-on-the-v5_0-store) includes all town tables,
[pre-registration timing](detailed_results.md#which-measures-were-fixed-in-advance), and the
[baseline investigation](detailed_results.md#was-the-baseline-a-low-draw). The reference also records the rounding-sensitive elimination p-values and their recheck.

## 3. v6: no clear benefit from observations or lessons

The June 17 campaign used the undeduplicated `v6_1` store, rebuilt around structured situation fields,
with plain retrieval and a fresh baseline. It tested five memory conditions plus that baseline, each
on 30 paired boards. The lone killer was the only deceiver tested; there was no wolf-memory arm.

| Who received memory | Memory supplied | Outcome against memory off |
|---|---|---|
| Town | Observations | Win difference +6 percentage points, p = 0.77; no clear decision-quality gain |
| Town | Lessons | Win difference −7 points, p = 0.75; decision measures also tended negative |
| Lone killer | Observations | Win rate unchanged at 47%, p = 1.00 |
| Lone killer | Lessons | Win rate 47% → 30%, p = 0.33 |
| Lone killer | Both | Win rate 47% → 53%, p = 0.75 |

None established an outcome improvement. The combined lone-killer condition looked better than lessons
alone, but that direct contrast was also inconclusive (p = 0.118). It does not establish that combining
memory types repairs harmful advice. Town never received a combined condition.

This was **not a replication of v5**: the store and play prompts changed, and the tests ran in different
periods. The later no-memory town already scored near the earlier memory-on town. A replay comparing
both stores in one sitting also found similar scores. Those observations make a stronger baseline a
plausible explanation, but do not identify why the earlier benefit failed to recur.

The [v6 experiment log](v6_sp_ab/experiment_log.md) owns all six arms, behaviour changes and their
limitations. Its directional interpretations are hypotheses; the outcome comparisons remain
inconclusive. The [cross-version detail](detailed_results.md#why-the-v6-ab-found-no-town-effect)
explains the baseline and prompt changes.

## 4. v7: the finished learning memory did not show a benefit

v7 tried to improve the store automatically: play games, grade decisions associated with followed
lessons, write new lessons and remove poor ones. Two June runs were invalid for their intended
questions, prompting stronger baseline and configuration checks.

The July experiment completed four learning generations, then played 30 boards with the finished
memory and without it. The town's average decision score was lower by the reported 0.147, and worse
on 19 of the 30 boards. The paired t-test gave p = 0.065; Wilcoxon gave p = 0.105. Neither established
harm at the stated significance threshold, and the experiment did not establish a benefit.

The recorded verdict was **“no compounding detected.”** Its precise meaning matters: the amended
endpoint compared final memory with none, not final memory with an earlier generation. The treatment
also included behavioural hints called *tells*, so their effect was not separated from the lessons'.

Investigation found a credit blind spot that let cautious abstention advice survive pruning. Revised
scoring removed the example lesson when applied to recorded games, but the corrected loop was never
played. That is evidence of a scoring fix, not evidence that the fixed memory improves play.

The owner closed this research campaign on July 21. The [v7 report](../v7/report.md) owns its design,
amendment, power analysis and result; this report retains its place in the effectiveness record.

## 5. v8: component checks, no effectiveness result yet

v8 changed the game to ten seats and rebuilt much of the memory pipeline. Its checks cover retrieval
fit, incorrect rule claims, outcome-verdict bias, decision tags and execution of a credit pass. These
help assess individual stages; none compares play with memory against play without it.

The [v8 report](../v8/report.md) therefore supplies **no whole-game effectiveness verdict**. Earlier
nine-seat results cannot be transferred to it. Its proposed experiment size is a planning estimate
from earlier data, not a completed validation on ten seats.

## Supporting studies: what they answer

These studies help explain or choose a design. Keep them separate from whole-game effectiveness.

| Study | Finding and limit | Detailed home |
|---|---|---|
| May memory-type ablation | Observations, lessons and both scored similarly on 120 replayed turns from three games; largest judge-score gap 0.17/5. No significance test or no-memory condition; not proof of equivalence or benefit | [Ablation](../ablation/report.md) |
| June decision replays | Tested reasoning order, forced applicability verdicts and outcome framing. No tested prompt change gave a clear general improvement; results varied by situation | [Replay screens](#screening-layer-per-decision-replays) |
| Retrieval and capacity studies | Assess relevance, repetition and how many memories to show. Better retrieval scores do not themselves establish better play | [Retrieval](../../retrieval/report.md) |
| Adoption checks | Assess whether agents' reports of using lessons match their actions. Reported use is not evidence that the advice helped | [Strategy adoption](../strategy_adoption/report.md) |

### Screening layer: per-decision replays

The June screens froze recorded decisions and changed the memory input or how the agent used it. Their
store was a re-extracted `v5_0` variant, not the June A/B store itself. Writing reasoning first improved
agreement between reasoning and votes without clearly increasing memory use. Forced applicability
judgements worsened votes in a small screen. Outcome framing gave different results in different game
situations.

These screens helped prioritise more conditional lesson content. They did not establish that content
was the only remaining problem or that prompt changes generally cannot help. The
[replay detail](detailed_results.md#screening-layer-per-decision-replays) preserves the tables,
sample sizes and costs; the [log](decision_replay/experiment_log.md) records the investigation.

## What you need to be able to explain

The defensible account has four parts:

1. **Why the tests became controlled:** early results moved with the store and baseline, so later
   comparisons froze the treatment and paired the starting boards.
2. **What the positive result actually was:** selected town decision measures on one v5 store, with
   multiple-comparison and baseline caveats—not a repeatable win-rate improvement.
3. **What later versions showed:** no clear benefit in v6 or the v7 endpoint; the corrected v7 loop
   was not tested, and v8 has no whole-game comparison.
4. **Why the engineering work still matters:** the experiments exposed problems in experimental
   controls, advice quality and credit. Fixing those mechanisms is distinct from demonstrating that
   memory improves the agents.

The June v5, v6 and v7 comparisons used the player model at its minimal thinking setting. A later probe
reported zero reasoning tokens for that configuration; it does not establish an absence of internal
reasoning. The conclusions do not establish results at higher thinking settings or on today's game.
Exact arm tables, test choices and artifacts are reference material in
[detailed results](detailed_results.md), rather than facts you need to memorise.

*Scope: editorial consolidation of the existing reports and the v6 experiment log, 2026-10-26. No code,
deployment state or raw experimental data was independently checked, and no statistics were rerun.*
