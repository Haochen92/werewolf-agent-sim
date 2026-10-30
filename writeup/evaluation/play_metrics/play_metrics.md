# Measuring play quality beyond win rate

*Level 2 · [Evaluation](../evaluation.md) · previous: [Finding and fixing factual errors](../factual_errors/factual_errors.md) · next: [Checking agent outputs with code](../code_checks/code_checks.md) · status: revised 2026-10-29; for the owner’s review.*

## Historical brief (2026-10-25)

**Reader question:** What can be measured when wins are too noisy to identify modest gains affordably?

Subsections: why decisions provide more observations than wins; rule-based grades and opportunity-adjusted
rates; checking association with winning; what transferred to the expanded game; rare actions and remaining
uncertainty. Explain that decisions within one game are related, not independent extra games.

**Exhibits:** one worked vote or protection score, then the contrasting healer and lynch metrics.
Explain why a save remains useful even when its rate no longer separates winning and losing games.

**Sources:** [metrics](../../../evidence/evaluation/metrics/report.md), with relevant material from
[scoring](../../../evidence/evaluation/scoring/report.md). Correlation supports a proxy; it is not a causal
effect or a validation of the combined decision grade.

**Level 3:** [Which play metrics transferred to the expanded game?](metric_transfer.md), linked beneath the subsection it deepens.

Exhibits for this page are listed in [`../exhibits/source_map.md`](../exhibits/source_map.md).

---

<!-- Editorial review 2026-10-25: phrasing and structure revised; no independent factual
verification. Earlier completion notes below describe the pre-edit draft and are retained as history.
Verifier handoff: The healer comparison now distinguishes exclusion of an old point estimate from a direct test of
a difference between populations. Verify whether the earlier estimate has an interval or a direct
comparison exists; otherwise retain the narrower conclusion. Detailed healer counts remain in Level 3.
Verified 2026-10-25 (main session): the record gives no interval or direct test for the nine-player healer estimate; it gives two independent nine-player estimates, +0.36 (50 games) and +0.40 (180 July games) (metrics/report.md §3). A standard Fisher-z comparison of independent correlations, computed for this check only: z = 2.2 (p ≈ 0.03) against +0.36/50, z = 3.3 (p ≈ 0.001) against +0.40/180, i.e. the drop is unlikely to be chance alone, but the comparison crosses game version and models, so it says nothing about why. Kept off the page (not in the record); the owner may add it on Level 3. The narrower page wording is correct as is.
-->

## Page copy (draft)

A game of Werewolf ends with one result: which side won. That result carries the luck of the role deal,
of whom the killers happened to target and of every close vote. Small batches can therefore provide
little evidence of a change in playing strength. Depending on the improvement being tested, a
comparison based on wins can require more games than the project could afford for each change.

A game contains many decisions, though: every vote, every night target, every protection. I used scores
that grade those decisions against the true roles, computed by code from the saved game record, as
candidate proxies for play quality. A proxy here is a measurable stand-in for what we actually care
about, which is playing well enough to win.

Two questions have to be kept apart. A scoring rule rewards a specified outcome, such as keeping a
townsperson alive. A separate check asks whether higher scores are associated with winning. When the
game expanded from nine to ten players, the healer's save remained a good outcome under the rules,
but its save rate no longer showed the earlier association with town wins. That distinction shapes
how these scores can be used.

### Why grade decisions instead of games?

One win per game is a noisy measure. A graded decision isolates a single choice: a town vote on a wolf
counts as right even if the town later loses on an unrelated coin flip. Averaging grades within a
game gives a more detailed measure than its single win or loss. This can make a comparison more
sensitive to changes in the decisions being scored, but the benefit depends on the metric and its
variation across games.

Those decisions are not independent extra games. Votes in the same game share its deal, its history
and its players; thirty graded votes from one game are not thirty games' worth of evidence. The checks
on this page therefore use the game as the unit: one score per game, compared with that game's result.

The score also had to be computable in the same way for both versions being compared. An early
proposal weighted votes by how certain the agent could have been, but its uncertainty signal existed
only in games with memory enabled. It could not fairly compare memory on with memory off. The chosen
approach instead scores recorded outcomes without asking agents to produce extra answers for the
evaluator.

### Grading a decision by the rules

The scoring rules define which outcomes to reward. A town vote on a wolf removes a threat; a
protection that stops an attack keeps a player alive; a vigilante's night shot on an evil player is
a hit. For the expanded game I defined a table that marks every kind of turn as good, neutral or
bad, and code grades each decision against it.

Some scores are rates, and a rate must divide by the chances a player actually had. A healer, who
protects one player each night, would collect more saves simply by surviving longer. Its score
therefore divides saves by the nights on which its protection went ahead. A role that never had the
chance to act gets no score rather than a zero.

How one healer protection is graded in the expanded game:

| What happened that night | What the game records | Effect on the healer's save rate |
|---|---|---|
| The protected townsperson was attacked and survived | A save | One save; the night counts |
| Nobody attacked the protected player | No save | The night counts, with no save |
| The protected player was evil and was attacked | A save of an enemy | Not a town save; counted against the healer in a separate rate |
| The Chanteuse, an evil role that blocks one player's night action, blocked the healer | The protection did not happen | The night is left out entirely |

*Rate = saves of townspeople ÷ nights the protection went ahead. Checked against the scoring code and
the game's night-resolution rules.*

Grading a decision separates it from the eventual win or loss, but does not remove luck inside the
decision. A villager who votes blindly and hits a wolf scores the same as one who reasoned it out,
and a healer's save depends on whom the killers chose to attack. More games can reduce the influence
of those chance events; scoring does not remove them from a single decision. The scores describe selected outcomes, not the quality of the reasoning that produced them.

### Checking whether a score goes with winning

A plausible scoring rule is not enough to establish a useful proxy. The check compares each
per-game score with that side's win or loss using a correlation from −1 to +1. A positive value
means higher scores tended to occur in games the side won; a value near zero indicates little
linear association in that sample.

The original game's Investigator illustrates why this check mattered. Finding an enemy seemed
useful, but the rate of finding wolves did not show the expected association with town wins.
A different measure—whether a confirmed wolf was later voted out—tracked winning more closely
(+0.40 over 180 games). The distinction was between acquiring information and acting on it.
This supported the follow-through measure as a candidate proxy; it did not establish that increasing
it would cause more wins.

A pooled correlation can also reflect differences between batches. For example, one configuration
might produce both higher scores and more wins. The checks therefore examined memory-off games
separately and, in the expanded game, associations within batches. These checks help assess whether
the relationship persists under narrower conditions. They do not turn an association into a causal
effect.

The role of validation changed as the game expanded. In the original game, the check helped select
scores from a set of candidates. The ten-player game introduced more roles, with too few examples
of each to choose every score that way. Memory also needed grades from the first game. I therefore
defined good, neutral and bad outcomes from the rules, then used the win-association check to assess
which per-game metrics could support claims about playing strength. That check did not validate the
combined decision-grading table used by memory.

### What transferred to the expanded game

The expanded game added information roles that learn about other players at night, new evil roles and
a second kind of lone killer, the necromancer. Correlations from the nine-player game
could not simply be assumed. Before any check, the scores had to be rewritten to read the new game's
night records and to take each player's side from the role list rather than from the original role
names. The check then ran on 78 ten-player games.

| Score, correlated with its side's win | Original nine-player game | Expanded ten-player game |
|---|---|---|
| Share of lynches that removed a threat (town) | +0.65 (50 games) | +0.49 (78 games; 95% interval +0.30 to +0.64) |
| Healer's saves of townspeople per protection night (town) | +0.36 (50 games) | −0.03 (75 games; 95% interval −0.26 to +0.20) |

*Associations, not causal effects. The nine-player figures come from June 2026 games on the Gemini
models of that time, with no interval reported; the ten-player games were played mostly on Claude Haiku
5.5 in October 2026. The nine-player lynch figure held on memory-off games; the ten-player one held
within batch (+0.55) and on memory-off games (+0.48).*

The share of lynches that removed a threat retained a positive association: higher values tended
to occur in town wins. The within-batch and memory-off checks supported that reading in the expanded
game. This made it a better-supported proxy in these games than the healer's save rate.

The healer's save rate did not reproduce the earlier association. The new interval excluded the old
point estimate, but the old estimate also has uncertainty: this was not a direct test of the difference
between game versions. The practical finding is narrower—the new sample did not validate save rate
as a proxy for winning.

The healer averaged about one save in both town wins and losses, while surviving for more protection
nights in wins. A similar number of saves spread across more nights changes the rate. The detailed
records also show saves followed by later deaths or a kill elsewhere on the same night. The linked
transfer analysis examines those patterns.

My interpretation is that additional information roles and two killers may change the value of a
protection. The check did not test that mechanism. The comparison also crosses game versions and
models, so it cannot separate changes to the rules from changes in how the healer was played.

A save remains a useful action. By the rules it means one more townsperson the next day, so the
decision table still grades it as good. What the check removed was the healer's save rate as evidence
that a ten-player version wins more. Counting saves exactly and validating their rate as a proxy for
winning are different claims.

**Link:** Explore how the transfer was checked: within-batch and memory-off readings, rare roles and
intervals → [Which play metrics transferred to the expanded game?](metric_transfer.md)

### When there is not enough evidence to validate a proxy

Some actions were too rare for a useful conclusion in the 78-game sample. The Vigilante, who can
shoot a player at night, fired in only 19 games. Its correct-shot rate correlated +0.29 with town
wins, but the 95% interval ranged from −0.19 to +0.66. That range includes both no association and
a substantial positive one.

The scoring rule can still describe whether a shot hit an evil player. The sample does not establish
its rate as a reliable proxy for winning, or show that the proxy is useless. This is a different
result from having enough evidence to challenge a previously supported measure.

For a new game version, the next step is to specify each new metric's expected relationship with
winning before examining the results, check that the scorer handles the new roles correctly, and
report associations with their uncertainty. Examining many candidate metrics also increases the
risk of selecting chance findings. The new-role results from this check remain exploratory because
their expected directions were not recorded beforehand.

The practical boundary is to use a rule-based grade to describe the action it measures, and require
additional evidence before treating a higher score as better overall play. The combined decision
grades used by memory still need that separate validation.

**Evidence.**

- [Play-quality metrics: scoring how well the agents played](../../../evidence/evaluation/metrics/report.md) (the approach, both checks, the healer, the cautions).
- [The working record](../../../evidence/evaluation/metrics/experiment_log.md), Part A (the nine-player scores) and the 2026-10-24 entry (the ten-player check).
- [Ten-player win check: games and full results](../../../evidence/evaluation/metrics/data/ten_seat_win_check/README.md).
- [The nine-player check against winning](../../../evidence/metrics/proxy_win_monotonicity.md).


<!-- Selection pass 2026-10-29, direct edit under the agreed requirements, without skill workflow.
Kept: why proxies, comparable scoring, opportunity-adjusted rates, association checks, healer transfer,
and one rare-action example. Removed the extra candidate/design inventory, wolf-kill subset analysis,
correlated-metric/survival examples, additional transfer findings, sample-size estimate, early-investigator
history and separate scorer-bug anecdote. They remain in the prior copy below and evidence reports.
Qualified sample-size and sensitivity claims; grades measure recorded outcomes, not reasoning quality.
Sources checked: evidence/evaluation/metrics/report.md, sections 1–4 and 6. No new calculations,
experiments or implementation audit. This is an editorial pass, not fresh factual verification.
-->

<!-- Prior page copy, superseded by the selection pass of 2026-10-29.
A game of Werewolf ends with one result: which side won. That result carries the luck of the role deal,
of whom the killers happened to target and of every close vote. Detecting a moderate improvement
through wins alone takes hundreds of games, more than the project could run for each change it wanted
to compare.

A game contains many decisions, though: every vote, every night target, every protection. I used scores
that grade those decisions against the true roles, computed by code from the saved game record, as
candidate proxies for play quality. A proxy here is a measurable stand-in for what we actually care
about, which is playing well enough to win.

Two questions have to be kept apart. A rule-based score rewards a specified outcome, such as keeping a
townsperson alive. A separate check asks whether games with more of those moves are games that side
won more often. When the game expanded from nine to ten players, one score kept passing the first test
and stopped passing the second. This page explains how the scores were built, how they were checked,
and what that contrast means for using them.

### Why grade decisions instead of games?

One win per game is a noisy measure. A graded decision isolates a single choice: a town vote on a wolf
counts as right even if the town later loses on an unrelated coin flip. Averaged over the many
decisions in a game, such grades vary far less than the result, so a difference between two versions
of the agents can show up in fewer games.

Those decisions are not independent extra games. Votes in the same game share its deal, its history
and its players; thirty graded votes from one game are not thirty games' worth of evidence. The checks
on this page therefore use the game as the unit: one score per game, compared with that game's result.

Two other designs were considered and turned down, and the reasons shaped what a usable score had to
be. A vote score weighted by how certain the voter could have been needed a measure of uncertainty that
existed only in games with memory switched on, so it could not be computed the same way for both sides
of a memory comparison. Asking every agent to write out a belief about each player would have changed
the behaviour being measured. Early model judges had a similar problem: they described memory quality
and ran only in memory-on games. The scores that remained read only what the game engine recorded:
votes, deaths, revealed roles and night actions.

### Grading a decision by the rules

The scoring rules define which outcomes to reward. A town vote on a wolf removes a threat; a
protection that stops an attack keeps a player alive; a vigilante's night shot on an evil player is
a hit. For the expanded game I defined a table that marks every kind of turn as good, neutral or
bad, and code grades each decision against it.

Some scores are rates, and a rate must divide by the chances a player actually had. A healer, who
protects one player each night, would collect more saves simply by surviving longer. Its score
therefore divides saves by the nights on which its protection went ahead. A role that never had the
chance to act gets no score rather than a zero.

How one healer protection is graded in the expanded game:

| What happened that night | What the game records | Effect on the healer's save rate |
|---|---|---|
| The protected townsperson was attacked and survived | A save | One save; the night counts |
| Nobody attacked the protected player | No save | The night counts, with no save |
| The protected player was evil and was attacked | A save of an enemy | Not a town save; counted against the healer in a separate rate |
| The Chanteuse, an evil role that blocks one player's night action, blocked the healer | The protection did not happen | The night is left out entirely |

*Rate = saves of townspeople ÷ nights the protection went ahead. Checked against the scoring code and
the game's night-resolution rules.*

Grading the decision removes much of the luck in the final result, but not the luck inside the
decision. A villager who votes blindly and hits a wolf scores the same as one who reasoned it out,
and a healer's save depends on whom the killers chose to attack. More games can reduce the influence
of those chance events; scoring does not remove them from a single decision. The scores are less
dependent on luck than the win, not free of it.

### Checking whether a score goes with winning

A rule can make a move look obviously good when it does not help a side win. The check compares each
score with its own side's win across a batch of games, as a correlation from −1 to +1. On the original
nine-player game, the town's best scores came out between about +0.5 and +0.65.

That check found scores whose meaning had looked obvious and was wrong. The investigator, who checks
one player's identity each night, was expected to help the town by finding wolves often. Its find
rate did not go with town wins (−0.09 and −0.14 in the first check). What did was a confirmed wolf
being voted out later (+0.40 over 180 games): the follow-through score tracked winning more closely
than the find rate alone. Wolves accusing townspeople was expected to help the wolves, and came out
the other way (−0.33).

The check guards against several ways of being misled. Memory could raise both a score and the win, so
each score was also read on the memory-off games alone. Some scores matter only in some games: the
wolves' night-kill score looked unrelated to winning over 180 games, but in 77 of them the wolves could
no longer win. Within the 103 games where they could, it went with their wins (+0.31). Testing about
thirty scores means one or two can pass by chance, and four town vote scores that move together count
as one measure, not four. A count close to the result itself says little about skill: the serial killer,
a lone killer who forms a third side and wins alone, has to survive to win, so its nights survived
track its wins almost by definition.

A positive correlation shows that a score tracks winning in those games. It does not show that raising
the score causes wins.

The check's role also changed. In June 2026 it acted as a gate: 48 candidate scores were tested and 11
kept. The expanded game deals ten seats from twelve roles, which leaves too few games per role to
choose scores that way, and memory needed a grade for every decision from the first game. So on the
expanded game the rules came first, and the check confirms a score or questions it. It tested the
per-game scores, not the decision table as a whole.

### What transferred to the expanded game

The expanded game added information roles that learn about other players at night, new evil roles and
a second kind of lone killer, the necromancer. Correlations from the nine-player game
could not simply be assumed. Before any check, the scores had to be rewritten to read the new game's
night records and to take each player's side from the role list rather than from the original role
names. The check then ran on 78 ten-player games.

| Score, correlated with its side's win | Original nine-player game | Expanded ten-player game |
|---|---|---|
| Share of lynches that removed a threat (town) | +0.65 (50 games) | +0.49 (78 games; 95% interval +0.30 to +0.64) |
| Healer's saves of townspeople per protection night (town) | +0.36 (50 games) | −0.03 (75 games; 95% interval −0.26 to +0.20) |

*Associations, not causal effects. The nine-player figures come from June 2026 games on the Gemini
models of that time, with no interval reported; the ten-player games were played mostly on Claude Haiku
5.5 in October 2026. The nine-player lynch figure held on memory-off games; the ten-player one held
within batch (+0.55) and on memory-off games (+0.48).*

The lynch score carried over: games in which the town voted out evil players were games the town won.
Others kept their nine-player direction too, including town roles with night abilities lost to night kills
(against town wins), the town voting out the lone killer, and the wolves voting with the day's majority.

The healer's save rate did not reproduce the earlier association. The new interval excluded the old
point estimate, but the old estimate also has uncertainty: this was not a direct test of the difference
between game versions. The practical finding is narrower—the new sample did not validate save rate
as a proxy for winning.

The healer averaged about one save in both town wins and losses, while surviving for more protection
nights in wins. A similar number of saves spread across more nights changes the rate. The detailed
records also show saves followed by later deaths or a kill elsewhere on the same night. The linked
transfer analysis examines those patterns.

My interpretation is that additional information roles and two killers may change the value of a
protection. The check did not test that mechanism. The comparison also crosses game versions and
models, so it cannot separate changes to the rules from changes in how the healer was played.

A save remains a useful action. By the rules it means one more townsperson the next day, so the
decision table still grades it as good. What the check removed was the healer's save rate as evidence
that a ten-player version wins more. Counting saves exactly and validating their rate as a proxy for
winning are different claims.

**Link:** Explore how the transfer was checked: within-batch and memory-off readings, rare roles and
intervals → [Which play metrics transferred to the expanded game?](metric_transfer.md)

### Rare actions and remaining uncertainty

Many actions are too rare to test in 78 games. The vigilante, who can shoot a player at night, fired in
19 games; it hit evil players with 16 of 22 shots. Its correct-shot rate correlated +0.29 with town
wins, with a 95% interval from −0.19 to +0.66. That interval includes no link and a strong one, so the
score is graded by its rule but untested as a proxy. Investigator finds turned into lynches, present in
20 games, are in the same position.

An inconclusive result on few games means the proxy remains unvalidated; it does not establish that
the proxy fails. Seeing a link of 0.2 reliably would
take about 190 games, and the evil sides, which won less often, need more. Small samples also mislead in
the other direction: on the nine-player game, an early investigator find appeared to go with more town
wins (+0.38 over 30 games), then shrank to +0.15, not significant, over 180.

The expanded game's new roles add another limit. Their expected directions were not written down before
the check, so their results are exploratory rather than tests. With 32 scores examined, one or two may
pass by chance.

Scores written against role names also need care when the cast changes. Three scorers outside this
check had counted the new evil roles as town; they were switched to the role list on 2026-10-24.

The next step for a new game version is to record each new score's expected direction before the
first batch, then run the same check with intervals before a comparison relies on it. The decision
table itself still needs its own test against winning.

**Evidence.**

- [Play-quality metrics: scoring how well the agents played](../../../evidence/evaluation/metrics/report.md) (the approach, both checks, the healer, the cautions).
- [The working record](../../../evidence/evaluation/metrics/experiment_log.md), Part A (the nine-player scores) and the 2026-10-24 entry (the ten-player check).
- [Ten-player win check: games and full results](../../../evidence/evaluation/metrics/data/ten_seat_win_check/README.md).
- [The nine-player check against winning](../../../evidence/metrics/proxy_win_monotonicity.md).
-->

<!-- Sources for the page copy (checked 2026-10-25):
Opening: win too lucky, hundreds of games for a moderate effect, many decisions per game vary less:
metrics/report.md §1. "Candidate proxies": Level 1 page wording; report "In short".
Rules vs check as separate questions: report §5 item 2; §2 "Check the score against winning".
Decisions not independent / game as the unit: the brief's instruction; the check correlates one per-game
score with one per-game win (evaluation/experiments/ten_seat_win_check.py, check_score).
Rejected designs (uncertainty-weighted vote quality; forced belief output; early judges memory-on only):
report §1. "Read only what the engine recorded": report §2 "What goes in" (one nine-seat supporting
score reads accusation tags; omitted as a detail).
Rule examples, the table the owner ruled (good/neutral/bad per turn kind): report §2; log B1.
Opportunity-adjusted healer rate; no chance → no score: report §2. Worked table: Agents/ten_seat_metrics.py
lines 86-96 (protects that went ahead = not roleblocked; healer_town_save_rate = town saves / protects;
friendly-fire rate for evil targets); Agents/rules/night.py verdict step (attacked + protected + not immune
→ "saved"). Chanteuse block counts neither way: log 2026-10-24 "The healer".
Luck inside one decision, "de-lucked" = less lucky than the win: report §2.
Correlation with own side's win; town best +0.5 to +0.65: report §2.
Investigator find rate −0.09/−0.14; find-to-lynch +0.40 (180 games); wolves accusing town −0.33: report §3
table; log Part A and 2026-07-02 update (pre-registered +, came out −0.33).
Guards: memory-off; wolf night kills 77 of 180 / 103 games +0.31; multiple comparisons, four vote scores
= one witness; survival close to win: report §2.
June gate 48 tried / 11 kept; why it changed; check tested per-game scores, not grades: report §2 "How
the approach changed"; §6 "What they cannot claim".
Transfer: rewrite to night records and role-list sides: report §6 (port 2026-10-11), §5 item 5; code
ten_seat_metrics.py takes sides from ROLE_SPECS. 78 games: report §4.
Table: +0.65 (50) nine-seat lynch share: report §3; +0.49 (+0.30 to +0.64): log 2026-10-24 and
summary.json; healer +0.36 (50): report §3, proxy_win_monotonicity.md row healer_town_save_rate;
−0.03 (−0.26 to +0.20, 75 games): report §4, summary.json. Nine-seat: Gemini models, one batch; no
interval in proxy_win_monotonicity.md. Ten-seat models: report §4 "The data". Within-batch +0.55,
memory-off +0.48: report §4 table.
Other carried-over scores: report §4 table ("Carries over").
Healer records (1.07/1.03; 3.25/2.48; 220 = 79 + 141; 36 died later; 23 someone else died): report §4;
log 2026-10-24. Owner's reading: log 2026-10-24 "Owner's reading". Cross-model caveat: report §3 "Gemini
models of the time" vs §4 "mostly Claude Haiku 5.5" (my addition; see completion note).
Vigilante 19 games, 16 of 22, +0.29 (−0.19 to +0.66): log 2026-10-24 "The vigilante"; report §4.
Find-to-lynch 20 games: report §4.
"Not yet tested"; ~190 games for 0.2; evil sides need more: report §2. Early alarm +0.38 (30) → +0.15
(180): report §3.
Directions not written before; 32 scores: report §4 "How sure we are".
Three scorers switched 2026-10-24: report §5 item 5, §7.
Next step: report "What we would do differently" items 3-4; grades untested: §6. -->

<!-- Completion note (2026-10-25)
Structure. Follows the brief's five subsections in its order. The featured story is "What transferred
to the expanded game" (the healer/lynch contrast), which also anchors the Level 3 page; the Level 3
link sits beneath it (plain "Link", as the Level 1 page does for pages whose files exist as briefs;
switch to "Link (planned)" if the Level 3 page is not published with this one). The worked
exhibit is a protection graded by the rules (a four-row table) rather than one recorded protection:
the record has no single worked protection to quote, and inventing one would be a fabricated example.
The table states the rule; it does not claim a specific game.

Claims I was unsure of:
- The cross-model caveat on the healer ("the comparison crosses both the game version and the
  models") is my own reading of the record: nine-seat figures are from Gemini models of the time, ten-seat
  mostly Haiku. The report says the healer difference is "a real difference between the games, not a
  small sample". I kept "not only a small sample" and added that the check cannot separate game from
  model. The verifier should confirm the owner accepts this softening; I believe it is required by the
  false-alternatives check.
- "On 23 of the save nights someone else died to the other killer": the record says "in 23 saves someone
  else died that night to the other killer". Same claim, reworded.
- "Hundreds of games ... more than the project could run for each change": the report says "an effect
  shows at a game count the project can afford", not a specific budget. No figure given.
- Nine-seat lynch +0.65: the report says "+0.65 in both readings"; proxy_win_monotonicity.md shows +0.65
  pooled (50) and +0.64 memory-off (30). I cite only +0.65 over 50 games.
- The investigator's find rates (−0.09, −0.14) are two find-rate scores in the first check (threat and
  wolf find rates), not two batches. Worded as "in the first check".
- "So did the town's power roles lost at night ... and the wolves voting with the day's majority": wolves
  voting with the lynch was +0.22 and not significant with memory off (log); kept at summary level here,
  with the detail on Level 3.

Mechanism claims checked in code (today's code; the ten-seat check ran on 2026-10-24, so current code
should match it, but the verifier may confirm nothing in the save rate changed since):
- Healer rate and save definition: Agents/ten_seat_metrics.py lines 86-96; Agents/rules/night.py verdict
  (attacked, protected, not night-immune → saved; a night-immune target is "immune", not a save — left
  out of the table as a detail).
- Sides from the role list: Agents/ten_seat_metrics.py (ROLE_SPECS), Agents/compute_metrics.py.
- Game as the unit, three readings: evaluation/experiments/ten_seat_win_check.py.

Content-plan check (requested): the 2026-10-24 ten-seat check was not affected by the three mis-scoring
scorers. (1) Record: experiment_log.md 2026-10-24, "Correction, same day: the three scorers ... were
switched to the role registry that morning (f13c43ea), so they no longer mis-score ten-seat records."
(2) Code: the check's only scoring path is compute_game_metrics → ten_seat_metrics, which import sides
from Agents.schemas.roles.ROLE_SPECS and import none of the three scorers (score_vote in
decision_scoring.py, read_ledger.py, the discussion-evidence judge's role join). So the check would not
have used those scorers even before the switch. I could not run git to confirm commit order (git
commands needed approval in this session); the record's "that morning" plus the code path is the basis.
On the page I say only that the three scorers were outside the check.

Left off deliberately (Handle with care / bookkeeping): the check ran from an uncommitted runner on a
working tree (data README); the grade table's tests being AI-written and unaudited; the batch summary
script never cited; the live-push "validated" label being empty (state, not damaging, but not needed on
Level 2; mentioned on Level 3 as the owner's pending decision). The Brier read score, discussion census,
phase 2 counts and balance batches are omitted as outside this page's question (counts for prompt changes
belong elsewhere or are too detailed). No scoring-report statistic was needed: the page uses correlation
with an interval, which the scoring report does not cover; the scoring report is therefore not cited.

First person: "I used scores" (Level 1 uses it), "I ruled a table" (record: the owner's table), "My
reading" (record: owner's reading). Running the check is written neutrally.

Rubric self-scores (Level 2): Reader orientation 2; Added depth 2; Conceptual coverage 2 (rules vs
correlation, rates vs counts, independence, rare actions, chance passes, game vs model); Paragraph clarity 2;
Narrative economy 2 (healer mechanism told once; Level 3 carries method detail); Experimental separation 2
(nine-player 50/180-game checks and the ten-player 78-game check named separately; models stated);
Interpretation 2 (correlation ≠ cause; owner's reading labelled; game/model not separable); Evidence and
ownership 2; Technical accessibility 2 (proxy, correlation, interval in context); Exhibits and links 2.
Length: about 2,000 words of page copy including tables and captions (estimated; a word-count command
needed approval in this session), at the top of the guide. If it must shrink, the rejected-designs
paragraph is the first candidate to compress. -->
