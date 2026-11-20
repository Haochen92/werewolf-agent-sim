# Measuring play quality beyond win rate

*Level 2 · [Evaluation](../evaluation.md) · trial draft written with the second version of the write-portfolio-page skill, 2026-10-29; revised after one editorial and one claims review; open questions in the brief; for the owner's comparison.*

## Page copy (draft)

Play metrics are scores that code computes from a saved game record to show how well the agents
played: whether a vote removed an evil player, whether a protection kept a townsperson alive. They
exist because the win is a weak measure of a version's play at the number of games this project could
run. On the original nine-player game, comparing two versions over 30 games each could reliably
detect only a difference of about 35 percentage points in win rate (one it would find four times in
five, at the usual 5% significance level).

A game holds many decisions, and each can be graded against the true roles, which are known once the
game ends. That raises two separate questions. Was a decision a good move by the game's rules? And do
players who make more such moves win more games? The first is answered by counting; the second needs
a check against real results. The healer, who protects one player each night, shows why both are
needed: when the game expanded to ten players, its saves were still counted by the same rule and still
good moves, but its save rate no longer went with winning.

### Why grade decisions instead of wins

A win is one result per game, and it carries luck that has little to do with how well a version
plays: which roles were dealt to whom, whom the other side happened to target, and close votes that
could have gone either way. A version that plays better wins more often only on average, and that
average needs many games to show.

Graded decisions carry less of that luck. A town vote on an evil player counts as a good vote even if
the town later loses for unrelated reasons. Counting such outcomes across a game gives each game a
number with less of that luck in it than its win or loss.

It is still one number per game. Decisions in the same game share its deal and its history: a vote on
day three depends on what happened on days one and two. Ten graded votes from one game are not ten
independent games, so the checks below treat the game, not the decision, as the unit.

### Grading a decision by the rules

The game's rules define a good move. A town vote that removes an evil player removes a threat. A save
keeps one more townsperson alive for the next day. A shot by the vigilante, a town role that can shoot
one player at night, is a hit when it lands on an evil player. For the expanded game I ruled a table
that grades every kind of turn as good, neutral or bad, and code applies it to each decision against
the true roles. The per-game scores that the next section checks are computed separately, from the
same kinds of outcomes counted across a game, not by averaging the table's grades. No model is called
in either, so a score costs nothing and comes out the same every time, for both versions in a
comparison. The original game had no such table: its scores were chosen by how well they tracked
winning, as the next section explains.

Where a score depends on how long a player stayed in the game, it is a rate: good outcomes divided by
the chances the player had. Without that, a healer who lived nine nights would outscore one killed on
the second night simply by surviving. The healer's save rate shows how each night is counted.

| What happened that night | Counts as a chance | Counts as a save |
|---|---|---|
| The healer protected a townsperson who was attacked and survived | Yes | Yes |
| The healer protected someone nobody attacked | Yes | No |
| A wolf-side role blocked the protection (possible on the expanded game) | No | No |
| The healer was already dead | No | No |

*The healer's save rate: saves of townspeople divided by protections that went ahead. A healer with
no protection that went ahead gets no score, not a zero.*

Grading decisions removes the luck around a decision, not the luck inside it. A villager who votes at
random and hits a wolf scores the same as one who reasoned their way there, and a healer's save
depends on whom the attackers chose. That luck averages out over many games; it never leaves a single
grade.

### Checking that good moves win games

Whether good moves win games needs a check against real results: across a batch of games, each
per-game score is correlated with whether its side won. A rule alone says only that a move is good,
and a comparison of versions needs scores that stand for winning. The correlation runs from −1 to +1,
with one score and one result per game.

A score passes when it moves with its side's wins in the direction its rule predicts, by more than
chance would explain, in each reading. Two readings guard against a false link. Some games were played
with the agents' memory of earlier games switched on, and memory can raise both a score and the win
rate, so each score is also read on the games played with memory off. Games were also run in batches,
each on one model and set-up, which can differ in both play and results. The check on the expanded
game therefore also read each score within batch: each batch's own average is subtracted from the
score and from the win before correlating.

On the original game, the town's lynch scores passed clearly. The share of the town's lynches that
removed an evil player correlated about +0.65 with town wins over 50 games, the same over the 30 of
them played with memory off, and held on a later batch of 180.

The check also caught a score whose meaning looked obvious. The investigator checks one player's
identity each night, so how often it found evil players seemed a natural measure of its play. That
rate did not go with town wins: −0.09 for finds of any evil player and −0.14 for wolves over 50 games,
and still near zero over 180. What did was the share of its finds that the town later voted out:
+0.40 over 180 games. A find helps only once the town acts on it.

On the original game, the check chose the scores: 48 candidates were tried and 11 kept. That could not
work on the expanded game, where many new scores rest on actions taken in only some games and the evil
sides win few games, leaving too few games per score to choose by correlation. There the rules come
first: the table defines a good move before any data exists, and the check confirms a score or
questions it.

### When the game expanded

When the game expanded to ten players, the lynch share still went with winning and the healer's save
rate did not. The expanded game deals ten seats from twelve roles: eight every game, including the
healer, new information roles and a wolf-side role that can block a night action, and two seats that
each draw one of two roles, the lone killer who wins alone (the serial killer, as before, or a new
necromancer) and a new neutral seat.

Before any check, the scoring code had to change. It read night fields a ten-player game never fills,
so several scores read zero on ten-player games even when the event happened. They were rewritten to
read each night's full record and to take every player's side from the role list. The check used only
games whose records hold each night's full outcome: 78 games, played mostly on different models from
the nine-player games, 49 of them with memory off. Each result below has a 95% interval: the range of
correlations consistent with this sample.

| Score | Original game | Expanded game |
|---|---|---|
| Share of town lynches that removed an evil player | +0.65 (50 games) | +0.49 (+0.30 to +0.64; 78 games) |
| Healer's saves of townspeople per protection | +0.36 (50 games) | −0.03 (−0.26 to +0.20; 75 games) |

*Correlation of each per-game score with town wins. The original game's check reported no intervals.
The healer's score covers the 75 games in which at least one of its protections went ahead.
Associations, not causal effects.*

The lynch share carried over. It held within batch (+0.55) and with memory off (+0.48), so in this pool
neither memory nor differences between batches explains the link.

The healer's rate did not. Its earlier estimate came from a score kept because it passed, which can
flatter a result, but it held at +0.40 on the later batch of 180 nine-player games. A direct comparison
of the two correlations, on the Level 3 page, makes chance alone an unlikely explanation for the drop.

The records show where the link went. The healer made about one save per game whether the town won
(1.07) or lost (1.03), so its saves did not separate won games from lost ones. What differed was how
long it lived: 3.25 protection nights in games the town won, 2.48 in games it lost, and its number of
protection nights correlated +0.29 with town wins. The rate divides saves by those nights, so the same
number of saves over more nights pulls the rate down in the games the town won. The rate did what it
was built to do and took survival out of the score; on the expanded game, survival was the part of the
healer's record that went with winning.

Why the number of saves did not separate won games from lost ones here is not settled. My reading is
that with more information roles worth protecting, whom to guard became a harder guess, and one save
decided the game less often. The check does not test that reading. The comparison also crosses models
as well as game versions, so a change in how the healer was played cannot be excluded.

A save remains a good move by the rules, and the table still grades it as one. Its rate is no longer
evidence that one version plays better than another on the expanded game. Counting a move by its rule
and confirming it as a proxy for winning are separate results; the healer kept the first and lost the
second.

**Link:** Explore how the ten-player check separated scores that carried over from those that did not
→ [Which play metrics transferred to the expanded game?](metric_transfer.md)

### When a result is too weak to read

Most scores for the new and rare roles gave no clear answer, and at 78 games that usually means
untested, not failed. One new role's score correlated +0.12, with an interval from −0.11 to
+0.33: both no link and a real link of +0.3 are consistent with it. Seeing a link of 0.2 reliably takes
about 190 games. The evil sides need more, because a side's scores can only be checked against that
side's wins: the wolves won 17 of the 78 games and the lone killer 15. Reading a score as failing needs
an interval that rules out a link of a size worth having.

Rare actions are the extreme case. The vigilante fired in only 19 games, and 16 of its 22 shots hit
evil players: accurate when it acts, but its correlation with winning (+0.29, interval −0.19 to +0.66)
settles nothing. A score like the
vigilante's, whose direction the rules fix, can still report on its own kind of decision. It is not
used to decide whether one version beats another.

### What the checks do not establish

These are correlations. They show which scores went with winning in these games, not that raising a
score causes wins. The check on the expanded game examined 32 scores, so one or two could pass by
chance. The carried-over town scores are well past that and match their earlier direction. The new
roles' scores had no expected direction written down before the run, so their results are exploratory.

The check also tested per-game scores, not the table that grades every decision. Code applies that
table the same way every time, but whether the decisions it grades good, across every kind of turn,
go with winning has not been tested; the per-game scores cover only some of those turns.

The next step is to run the check on the first batch of each new version of the game, reporting
intervals and writing down each new score's expected direction before the run. A comparison of
versions can then rely on the scores that still track winning, and treat the others, like the
healer's, as records of good moves only.

**Evidence.**

- [Play-quality metrics](../../../evidence/evaluation/metrics/report.md), §1–§2 (why decisions are
  graded and how a score is checked), §3 (the nine-player check), §4 (the ten-player check).
- [The working record](../../../evidence/evaluation/metrics/experiment_log.md), Part A and the entry
  for 2026-10-24.
- [Ten-player win check: the games and all 32 scores](../../../evidence/evaluation/metrics/data/ten_seat_win_check/README.md).

<!-- Revision after review (2026-10-29, step 6): see the brief's Review resolution table. Changes to
sources: the deal is from Agents/schemas/roles.py (FIXED_SEATS: eight seats every game, healer
included; LONE_KILLER_ROLES serial killer / necromancer; NEUTRAL_ROLES speculator / fortune teller), so
the old "not dealt" table row and "each role absent from some games" were wrong and are gone. Healer
+0.40 on the 180 July games: report §3 "How sure we are". Healer protection nights +0.29 with town
wins: log 2026-10-24. The denominator sentence ("same saves over more nights gives a lower rate") is my
arithmetic reading of 1.07/1.03 saves over 3.25/2.48 nights, not a statement in the record; flagged
for the owner. The owner's recorded reason "two killers a night" was dropped: the nine-player game
also had two killing sides (wolves, serial killer), so it cannot explain the change. "Passes" is
defined from report §2 and log Part A (expected sign, significant, in each reading). Investigator find
rates −0.09/−0.14 are the 50-game June figures; "near zero over 180": log Part A L2 ("N=180 confirms
the dead floor"). Sentinel interval −0.11 (summary.json −0.106), not report §2's −0.10. Per-game scores
and decision grades are separate scorers (Agents/ten_seat_metrics.py vs grading.py): report §6. The
scorer-port zeros: "every one of the 28 ten-seat balance games" (report §6); the count is left off
because the source does not place those games among the 78. Removed from the page, kept here: the
rejected certainty weighting (report §1), the information-role pattern (60% of 134; +0.19, p = 0.12,
66 games; +0.09), 220 = 79 + 141, 56 of 79, 23 saves with another death that night.
-->

<!-- Sources for the page copy (checked 2026-10-29, skill trial 2):
Opening: definition, report header and "In short". Win-rate detectable difference: about 35 points at 30
games per arm, 80% power, nine-seat harness (evaluation_scopes/game/experiment_log.md MDE table, "about
35 points (the doc said about 36)"; experimental_controls/drift_surfaces_and_guards.md). The proxies'
own detectable effect is in other units (vote accuracy 0.18-0.21) and is deliberately not compared.
Two questions, rule vs check: report §2, §5 item 2. Healer preview: report §4; parent L1.
Why decisions: luck sources and "many decisions per game": report §1. One number per game: the check
correlates one per-game score with one win (evaluation/experiments/ten_seat_win_check.py, check_score).
Rules define a good move; vigilante hit; owner's table good/neutral/bad for every kind of turn: report §2;
log B1 (owner's ruling, memory_system/v8/plan.md §9.6). No model call, same answer: report header.
Healer table: Agents/ten_seat_metrics.py healer_town_save_rate = town saves / protections that went ahead
(went_ahead = not roleblocked; _safe_div returns None on zero); save verdict Agents/rules/night.py
(attacked, protected, not immune -> "saved"); blocked protection counts neither way: log 2026-10-24.
A protected evil player who was attacked counts as a chance, not a town save (friendly-fire rate kept
separately); omitted from the table for simplicity, covered by the caption's "saves of townspeople".
Residual luck and "less lucky than the win": report §2. Rejected uncertainty weighting (situation
summary only in memory-on games): report §1. Who rejected it is not recorded; written impersonally.
Check: point-biserial vs own side's win: report §2; memory-off reading (nine- and ten-seat) and
within-batch reading (ten-seat only): report §2 guards; data README. Lynch share +0.65 (50; both
readings), held on 180: report §3 table. Investigator −0.09 (threat_find_rate), −0.14 (wolf_find_rate),
find-to-lynch +0.40 (180): report §3; log Part A L2 and 2026-07-02 update.
June gate 48 tried / 11 kept; rules first on ten seats; ten seats from twelve roles: report §2 "How the
approach changed". The July exception (rule-fixed direction may report, not decide): same table.
Expanded game roles: Chanteuse blocks; lone killer = serial killer or necromancer: role sheet; schemas.
Scorer port: zeros in every one of 28 ten-seat balance games; rewritten 2026-10-11 to night records and
sides from the role registry: report §6; log B1. 78 games, 49 memory off, models (Haiku 56, flash-lite
17, GPT-6 Luna 5; nine-seat on the Gemini models of June-July): data README; report §3 "How sure we are".
Table: +0.65 (50) report §3; +0.49 (+0.30 to +0.64), within +0.55, memory-off +0.48: report §4, log,
summary.json; healer +0.36 (50) report §3 / proxy_win_monotonicity.md; −0.03 (−0.26 to +0.20, 75): report
§4, data README. Nine-seat check reported no intervals: metric_transfer.md sources note.
Direct comparison of the healer correlations: computed for metric_transfer.md (Fisher z, p ≈ 0.03 vs the
50-game estimate), not in the evidence record; owner approved it there; stated in words here (brief,
open question 1, default accepted 2026-10-29).
Healer records 220 = 79 + 141; 56 of 79 nobody died; 1.07/1.03; 3.25/2.48; 36 saved died later (omitted);
23 someone else died that night to the other killer: log 2026-10-24. Owner's reading: log "Owner's
reading" (2026-10-24); "two killers a night" rephrased as wolves and lone killer both attacking, since the
nine-player game also had two killing sides (metric_transfer.md completion note). Cross-model caveat:
report §3 vs §4.
Weak results: +0.12 (−0.10 to +0.33) is the Sentinel row (report §2, summary.json); about 190 games for
0.2; evil sides need more; failing only when the range rules out the expected size: report §2. Wolves 17,
lone killer 15: report §4. Vigilante 19 games, 16 of 22, +0.29 (−0.19 to +0.66): log "The vigilante".
Information roles: 134 named, 81 (60%) lynched; +0.09; +0.19, p = 0.12, 66 games: log; report §4.
Rare rule-fixed scores report, do not decide: report §2 table (July 2026).
Limits: 32 scores, one or two by chance, carried-over rows well past that: report §4 "How sure we are";
new-role directions not written in advance (owner's call): log 2026-10-24; grades untested as a whole:
report §6. Next step: report "What we would do differently" items 3-4.
Left off (Handle with care / selection): runner uncommitted at the time; grade-table tests; 119-game first
count; three scorers switched to the role registry on the check's morning (outside this check's code
path); VALIDATED_ON_TEN_SEAT_METRICS and the dashboard; memory results; vote-accuracy batch split,
Chanteuse and other carried-over rows (Level 3); wolf night-kill dilution, survival tautology, wolves'
accusations (−0.33), early-alarm +0.38 -> +0.15 (evidence). -->
