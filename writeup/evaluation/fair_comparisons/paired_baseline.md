# What the paired baseline reanalysis changed

*Level 3 · Evaluation › [Designing fair comparisons](fair_comparisons.md) · status: page copy drafted 2026-10-25 with the level prompts, reviewed in the main session; for the owner's review.*

## Brief

Show the shared-deal transition
table and why the independent and paired readings differ. Preserve the paired p = 0.18 and unresolved
cause. Do not promote the 67% → 10% headline as proof of drift. The parent keeps the corrected conclusion.

The parent page keeps the finding and its essential caveats; this page adds the method and analysis.
Exhibits for this page are listed in [`../exhibits/source_map.md`](../exhibits/source_map.md).

---

<!-- Editorial review 2026-10-25: phrasing and structure revised; no independent factual
verification. Earlier completion notes below describe the pre-edit draft and are retained as history.
Verifier handoff: The power finding is no longer extrapolated from decision scores to wins. Pinning is described
as a control on model identity, not proof of an unchanged service. The linked reanalysis script is
still untracked and needs inclusion in the published repository; this pass did not stage or commit it.
Verified 2026-10-25 (main session): the transition table and winners by side match the script's output (poetry run python -m evaluation.experiments.june_baseline_shift_check: shared 20, original {villagers 12, SK 7, wolves 1}, re-run {7, 6, 7}, 5/7/2/6, p = 0.180; fresh 10: {1, 6, 3}). The script is still untracked: commit it before publishing the link.
-->

## Page copy (draft)

In June 2026 a fresh baseline in the original nine-player game came back with the town winning far
less often than before, on identical prompts and unchanged game code. The first reading of it looked
decisive: 1 town win in 10 new games against 20 in the earlier 30, p = 0.0028. The question was
whether that showed the hosted model had changed.

A later reanalysis used the 20 deals that had been played in both periods and tested them as pairs.
The town still won less often, 12 times the first time and 7 the second, but at p = 0.18 the drop could
not be distinguished from chance. The outcomes moved; their size and cause were not established. This
page explains the two readings, why they differ, and what the reanalysis did and did not change.

### The two baselines

The town in this game is the ordinary villagers plus a healer, an investigator and a vigilante. They
play against the wolves and a serial killer, a lone player who wins by outlasting everyone. A memory
experiment needed a memory-off baseline as its control. An earlier baseline of 30 games already
existed, in which the town had won 20, and the winners of 20 of those deals were on record.

A game's id determines its deal, the assignment of roles to seats. Before the experiment, each of the
20 recorded ids was checked to reproduce its exact deal, and all 20 did. The code that plays the game
had not changed since the earlier baseline; only evaluation plumbing that does not affect play had. So
the plan reused those 20 deals with their recorded winners and played 10 new deals as fresh baseline
games.

A matched deal means the same starting roles, not the same game. Players sample at temperature 1.0,
so two games on one deal part ways at the first line that differs. A pair of results on one deal
therefore compares two independent plays of the same starting position.

### The first reading: games treated as independent

The 10 fresh games gave the town 1 win, the serial killer 6 and the wolves 3. In the earlier 30 the
town had won 67%, the serial killer 27% and the wolves 7%. Fisher's exact test compares the rates of
two separate groups; on 1 of 10 against 20 of 30 it gave p = 0.0028.

The record's leading explanation was a change in the hosted player model. That model's name had no
dated version that could be pinned, and each response reported only the name itself as its version,
so a change underneath could not have appeared in the records. Chance at this sample size was recorded
as the alternative.

Either way, the old games could no longer serve as the control. The 20 reused deals were played again
in the new period, so all 30 baseline games came from the same days as the memory games. A second
reading compared those 30 with the earlier 30: 27% town wins against 67%. That reading also treated
the games as independent, although 20 deals appeared on both sides.

### The reanalysis: the shared deals as pairs

Re-playing the 20 deals created matched pairs: each deal had one result from the earlier period and
one from the new period. The reanalysis read the recorded winners of both and made no model calls.

The test that fits this design is the exact McNemar test. A deal the town won both times, or lost both
times, says nothing about a change between periods. Only the deals whose result changed count. If
nothing had changed, each of them would be as likely to move in one direction as the other, like a coin
flip. The test asks how often a split at least as uneven as the one observed would occur by chance. No
decision threshold was fixed before the reanalysis. It was a correction to the analysis, not a new
experiment.

### Results

| | Town won in the new period | Town lost in the new period | Total |
|---|---|---|---|
| **Town won in the earlier period** | 5 | 7 | 12 |
| **Town lost in the earlier period** | 2 | 6 | 8 |
| **Total** | 7 | 13 | 20 |

*The 20 deals played in both periods, nine-player game, memory off. Exact McNemar p = 0.18 on the 9
deals whose result changed.*

Eleven deals kept their result. Of the nine that changed, seven went from a town win to a loss and two
the other way. The direction agrees with the first reading. But a split at least that uneven, in either
direction, would occur about 18% of the time if the two periods were alike. The shared deals are
consistent with a real drop and with chance.

The winners by side show that the readings do not describe the same shift either.

| Games | Town | Wolves | Serial killer |
|---|---|---|---|
| The 20 shared deals, earlier period | 12 | 1 | 7 |
| The same 20 deals, new period | 7 | 7 | 6 |
| The 10 fresh deals, new period | 1 | 3 | 6 |

*Counts of games won. The earlier 30 as a whole: town 67%, serial killer 27%, wolves 7%.*

The serial killer won most of the fresh games; on the shared deals the serial
killer's wins barely changed and the wolves gained. These groups are too small to identify a pattern.
They do show that the two readings are not two measurements of one well-defined change.

### Why the readings differ

The paired reading differs from the first in two ways at once. It uses different games, the 20 shared
deals rather than the 10 fresh ones, and it tests them as pairs. The reanalysis does not separate the
two effects. The fresh games remain the strongest evidence of a drop, but they are 10 games against a
different set of deals. The shared deals are the comparison that holds starting roles fixed, and analysed as the
pairs they are, they leave chance open.

A separate analysis found that a decision score varied about as much within one deal as across
different deals, so matching deals added little precision for that measure. It did not establish
how much pairing improves precision for win outcomes.
Its value here is that it uses the comparison the design actually contains, instead of treating 20
shared deals as unrelated games, as the 30-against-30 reading did.

### What the reanalysis changed

It changed the claim, not the experiment. What had been read as a change in the model service is now
described as a baseline that shifted, with the cause not established. Drift in the hosted model and
chance both remain open.

It did not change the memory experiment's control, which already came from the same period as its
memory games. Nor did it weaken the rule that the case produced: both sides of a comparison run in the
same time window, and new results are not compared with historical runs. That rule rests on the fact
that the two explanations could not be told apart, and the reanalysis confirmed that they still cannot.

### What it does not show

The reanalysis does not show that the hosted model stayed the same. A p-value of 0.18 on nine changed
deals means the data cannot rule chance out, not that chance explains the drop. It also gives no
reliable estimate of the shift's size: the readings range from the town winning 12 of 20 shared deals
and then 7, to 1 of 10 fresh deals against 20 of 30 earlier games.

The evidence covers one memory-off configuration of the original nine-player game, one player model,
and two periods. The records could not have identified the cause: they hold the model's name, and
the service reported nothing finer. Pinning a model version would reduce uncertainty about model
identity, without holding every aspect of the serving system fixed. More paired games could improve
precision, but neither step alone would identify the cause of a change.

**Link:** Return to the same-window rule and the other controls → [Designing fair
comparisons](fair_comparisons.md).

**Evidence.**

- [A/B testing: the controls that keep a comparison fair](../../../evidence/evaluation/experimental_controls/report.md),
  "The case that set the rules".
- [The paired memory experiment's log](../../../evidence/memory_system/effectiveness/paired_ab/experiment_log.md),
  "Epoch-shift finding", the re-test as pairs, "Can we pin or detect the drift?" and "Seed set".
- [The reanalysis script](../../../evaluation/experiments/june_baseline_shift_check.py) (reads recorded
  winners; no model calls).
- [Whole-game evaluation](../../../evidence/evaluation/evaluation_scopes/game/report.md), "What pairing
  turned out to buy".

<!-- Sources for the page copy (drafted 2026-10-25):
Opening and conclusion: experimental_controls/report.md "The case that set the rules" (1 of 10 vs 20 of
30, Fisher p = 0.0028; 12 → 7 on 20 shared deals, exact McNemar p = 0.18; "neither the size nor the cause
is established").
Town composition: paired_ab/experiment_log.md "Design" (town_only = villager, healer, investigator,
vigilante). Serial killer as lone player: whole-game report ("the lone killer").
The two baselines: paired_ab log "Seed set" (20 recovered ids with recorded baseline winners, 10 fresh;
crc32(game_id) reproduces the role draw, 20/20; play-path code unchanged since baseline commit b9756960,
only behaviour-neutral eval plumbing changed); "Epoch-shift finding" (byte-identical play prompts).
Same deal, not the same game: controls report §1.
First reading: paired_ab log lines 7–11 (fresh 10: villagers 10% / SK 60% / wolves 30%; original 30:
67% / 27% / 7%; Fisher p = 0.0028; "most likely cause" drift on the alias "or small-N variance"). Script
output confirms fresh 10 = villagers 1, serial_killer 6, wolves 3. Not pinnable, model_version echoes
the alias: paired_ab log "Can we pin or detect the drift?". Re-run of the 20 for a same-epoch baseline:
paired_ab log lines 12–16. Second reading 27% vs 67%: controls report.
Reanalysis method: evaluation/experiments/june_baseline_shift_check.py (original winners from
seed_set.json "recovered"; re-run winners from the recovered batch file; exact McNemar as
binomtest(won_original_only, changed, 0.5), two-sided; no model call).
Transition table and winners table: script output, re-run 2026-10-25: shared deals 20; original winners
villagers 12 / serial_killer 7 / wolves 1; re-run winners villagers 7 / wolves 7 / serial_killer 6; town
won both 5, original only 7, re-run only 2, neither 6; p = 0.180. Row and column totals are the script's
winner counts (12 and 8; 7 and 13). Matches the exhibit spec FC-transition in exhibits/source_map.md.
"About 18% of the time": the meaning of the two-sided exact p = 0.18 (binomial, 9 changed, p = 0.5).
Pairing adds little power: controls report §3 "What pairing bought"; whole-game report "What pairing
turned out to buy" (nine-seat).
What changed: controls report's revision note (2026-10-25: "the June case re-tested as pairs (the
earlier text called it a model-service change)"); paired_ab log re-test note. Rule stands because the
two could not be told apart: controls report. The memory experiment's control was same-epoch: paired_ab
log "Raw results" ("Same-epoch baseline").
What it does not show: controls report ("chance at this size is not ruled out"); paired_ab log (alias
not pinnable or detectable). -->

<!-- Completion note
Structure: opening question and conclusion → the two baselines (setup) → the first reading → the
reanalysis method → results with the transition table → winners by side → why the readings differ →
what changed → what it does not show. No rule was fixed in advance for the reanalysis, and the page
says so rather than presenting one.

Additions beyond the brief, flagged for the verifier:
- The winners-by-side table (fresh deals: the serial killer gained; shared deals: the wolves gained).
  It comes straight from the script's printed counts and shows that the two readings do not describe
  one well-defined change. It is small-sample and is labelled as such on the page. Drop it if the owner
  finds it distracting.
- "Why the readings differ" says the paired reading changes two things at once (which games, and
  pairing) and that the reanalysis does not separate them. This is my reading of the design, not a
  statement in the records; it follows the map's general rule against claiming to isolate one of two
  bundled changes. Using the variance finding (deal explains little) to say pairing adds little power
  here applies a nine-seat result measured on decision scores, not wins; the verifier should check
  whether that transfer is acceptable or should be softened further.
- The closing sentence (a pinned version removes one candidate; more paired games narrow chance) is a
  reasoned next step, not a recorded plan. Cut it if the owner prefers only recorded material.

Verification needed (per the content plan's five-field record): the deal pairing in the reanalysis
script and its inputs. Checked: the script pairs by game id between seed_set.json "recovered" winners
and the recovered batch file, and its output matches the controls report. Not checked: that the
recorded "recovered" winners match the original games' own records (they were taken from an
extraction batch file when the seed set was built in June).

Left off deliberately: "model drift" as a fact (the page says drift and chance both remain open); the
2026-06-12 memory-off canary and its "real model shift" conclusion (a separate, untested cross-day
comparison; see the Level 2 note); memory A/B results; the deal-reproduction check's method (crc32) as
a code identifier; where the batch files are stored (the recovered-games data sits outside the
committed record); costs. The reanalysis script was untracked in git when this draft was written: the
evidence link resolves only once it is committed. No first person: the record does not say who ran
the reanalysis.

Rubric self-scores (Level 3): added depth 2 (the transition table, the McNemar logic and the
two-changes-at-once analysis are not on the parent); method inspectability 2 (inputs, pairing, test,
absence of a predeclared threshold); counting units 2 (deals vs changed deals vs games; pairs are two
plays of one deal, not one game); decision-rule precision 2 (no rule existed; stated); analytical
assumptions 1 (the variance-transfer sentence is an applied assumption, flagged above); scope
alignment 2 (one memory-off configuration, nine-player game, one model, two periods); bounded
consequence 2 (claim changed; experiment and rule unchanged; cause open).
Length: about 1,350 words of page copy including tables. -->
