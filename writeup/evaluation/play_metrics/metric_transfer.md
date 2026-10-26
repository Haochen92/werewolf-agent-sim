# Which play metrics transferred to the expanded game?

*Level 3 · Evaluation › [Measuring play quality beyond win rate](play_metrics.md) · status: page copy drafted 2026-10-25 with the level prompts, reviewed in the main session; for the owner's review.*

## Brief

Develop the within-batch
and memory-off checks, rare-role samples, confidence intervals and healer records. The Level 2 page
retains the two contrasting findings and their implications; the deep dive explains how they were checked.

The parent page keeps the finding and its essential caveats; this page adds the method and analysis.
Exhibits for this page are listed in [`../exhibits/source_map.md`](../exhibits/source_map.md).

---

<!-- Editorial review 2026-10-25: phrasing and structure revised; no independent factual
verification. Earlier completion notes below describe the pre-edit draft and are retained as history.
Verifier handoff: Check whether an interval for the nine-player healer estimate or a direct between-version test
exists. The new text does not claim a proven population difference. Confirm the treatment of multiple
comparisons before strengthening any validation claim. Chanteuse is now separate from transferred
metrics because it is new; no correlation or interval was recalculated.
Verified 2026-10-25 (main session): as on the parent: no recorded interval or direct test; two nine-player estimates (+0.36/50, +0.40/180); the computed Fisher-z comparison (z = 2.2 and 3.3) supports a real difference in the association, not its cause. Multiple comparisons: the record states 32 scores and 'one or two may pass by chance' with no correction applied; the page's wording matches. Chanteuse correctly separated as new. Owner approved 2026-10-25 adding the direct comparison to the healer subsection (Fisher z for independent correlations; the computation is in this note, not in the evidence record).
-->

## Page copy (draft)

The project's play scores grade individual decisions against the true roles: whether a lynch removed
an evil player, whether a protection saved a townsperson. On the original nine-player game, a check had
shown which of those scores went with their side winning. The live game then expanded to ten players,
and every comparison of agent versions on it would lean on scores whose link to winning had only been
established on the old game.

A check on 78 ten-player games showed why the scores needed reviewing. The town's lynch scores and
several others carried over, holding within batches and in games without memory. The healer's save
rate showed no clear association in the new sample. Most scores for the new roles remain
inconclusive because the relevant actions occurred in too few games. This page explains how those
readings were made and where they stop.

### Why the earlier check could not be assumed

The expanded game deals ten seats from twelve roles. It adds information roles such as the Sentinel,
who watches one player and learns everyone who visited them, and the Trailseer, who follows one player
and learns whom they visited. The wolves' side includes the Chanteuse, who blocks one player's night
action. The lone killer, a third side that wins alone, can be the serial killer or a necromancer. Because
ten seats are dealt from twelve roles, a given role is absent from some games. A score that tracked
winning on the old game might not track it on this one.

Before any correlation could be computed, the scores had to compute at all. The original scoring code
read night fields that a ten-player game never fills, so those scores read zero in every one of the
first 28 ten-player balance games, even when the event happened. They were rewritten on 2026-10-11 to
read each night's full record and to take every player's side from the role list. The scores this check
used therefore classify the new evil roles correctly. Three other scorers, outside this check, had
counted those roles as town; they were switched to the role list on the morning of the check.

### The games

The check used every ten-player game whose nights carry their full outcome: 78 games from 2026-10-11
onwards. Another 41 games from the two days before record each night's choices but not what came of
them, so their scores cannot be rebuilt, and they were left out.

The pool is mixed. Most games were played on Claude Haiku 5.5, with a set of seeding games on Gemini
flash-lite and a few on GPT-6 Luna. Memory was off in 49 games. The town won 46, the wolves 17 and the
lone killer 15. Those evil-side win counts limit what any wolf or lone-killer score can show.

### Three readings of each score

Each game produced one value per score, correlated with whether that score's side won the game (a
point-biserial correlation, from −1 to +1). The game is the unit: decisions inside a game share its
deal and history, so they are not treated as separate observations.

Each score was read three ways, because a mixed pool offers two easy ways to be fooled.

1. **All games.** The plain correlation over the pool.
2. **Within batch.** Each batch's own average was subtracted from both the score and the win before
   correlating. A batch that both played differently and won more often can otherwise make any score
   look linked to winning.
3. **Memory off.** Memory can raise a score and the win together, so each score was also read on the
   49 memory-off games alone.

Vote accuracy, the share of town votes that landed on a threat, shows why the second and third readings
matter. Over all games it correlated +0.37 with town wins; with memory off it fell to +0.24 (p = 0.10).
Split by batch, it was +0.54 in the 29 memory-on games, +0.37 in memory-off Haiku games and +0.08 and
+0.16 in two 12-game batches on other setups. Average vote accuracy was the same with memory on and off
(0.57 and 0.59). The memory-on games were nearly all on Haiku, so in this pool memory and model cannot
be told apart. The weaker memory-off figure cannot isolate the effect of memory from those batch differences.

### Directions, intervals and when a null counts

Scores the June check had tested kept June's expected direction: a town lynch on a threat should go
with town wins. For scores belonging to the new roles, I chose to run the check first and read the
results afterwards, so no direction was written down in advance. Those results are exploratory
rather than tests of predictions made in advance.

Each correlation over all games carries a 95% interval, computed with Fisher's transformation. The
interval decides how a weak result is read. At 78 games, a correlation of +0.12 has an interval of
about −0.10 to +0.33, so a real link of +0.3 remains possible. Such a result leaves the score
unvalidated as a proxy. Excluding a meaningful effect size would support a stronger conclusion, but
that size must be justified. An earlier sample's estimate is itself uncertain and should not be
treated as the known population value.

### Results

| Group | Score | All games (95% interval) | Within batch | Memory off |
|---|---|---|---|---|
| Carried over | Share of lynches that removed a threat | +0.49 (+0.30 to +0.64) | +0.55 | +0.48 |
| | Town power roles lost to night kills | −0.55 (−0.69 to −0.38) | −0.55 | −0.43 |
| | Town voted out the lone killer | +0.38 (+0.17 to +0.55) | +0.40 | +0.43 |
| | Serial killer's kills of town power roles (45 games) | +0.48 (+0.21 to +0.68) | +0.58 | +0.47 |
| | Wolves voting with the day's lynch (70 games) | +0.29 (+0.06 to +0.49) | +0.36 | +0.22 |
| New, exploratory | Chanteuse blocks that stopped a real town action | +0.31 (+0.09 to +0.50) | +0.28 | +0.45 |
| Inconclusive | Sentinel watches that named an evil visitor | +0.12 (−0.11 to +0.33) | | |
| | Investigator finds turned into lynches (20 games) | +0.29 (−0.18 to +0.65) | | |
| | Vigilante correct shots (19 games) | +0.29 (−0.19 to +0.66) | | |
| Earlier association not reproduced | Healer's saves of townspeople per protection night (75 games) | −0.03 (−0.26 to +0.20) | −0.07 | −0.12 |

*Correlation of each per-game score with its side's win, 78 games unless stated. Power roles are town
roles with night abilities. Selected rows from 32 scores examined. Associations, not causal effects.*

The carried-over scores retained their earlier direction under all three readings, although not
every association was statistically significant: the wolves voting with the lynch fell to +0.22, not
significant, on the memory-off games. The inconclusive rows have intervals that include both no link
and a strong one. The vigilante, who can shoot a player at night, fired in only 19 games, though 16
of its 22 shots hit evil players.

### The healer

The healer protects one player each night. On nine players, its save rate correlated +0.36 with town
wins over 50 games. On ten players it was −0.03, with a 95% interval from −0.26 to +0.20. That
interval excludes the earlier point estimate, but the earlier estimate also has uncertainty. The interval alone is not a direct test that the two populations differ; it shows that the new
sample did not reproduce the earlier positive association.

A direct comparison of the two correlations, run for this page, makes chance an unlikely explanation
for the drop: p ≈ 0.03 against the 50-game estimate, and p ≈ 0.001 against the +0.40 the healer's
score held on a later batch of 180 nine-player games. It cannot say why the association changed,
because the comparison crosses both the game version and the models.

The rate counts a save when the healer protected a player who was attacked and lived, and divides by the
nights its protection went ahead; a night on which the Chanteuse blocked it counts for nothing. Of 220
protections that went ahead, 79 were saves and 141 guarded someone nobody attacked. The saves were real:
in 56 of the 79, nobody died that night. But 36 of the saved players died later, and in 23 saves someone
else died the same night to the other killer.

The healer made about one save per game whether the town won (1.07) or lost (1.03). What differed was
its survival: 3.25 protection nights in games the town won, 2.48 in games it lost, and the healer's
number of protection nights itself correlated +0.29 with town wins.

My reading is that, with more information roles worth guarding, whom to protect is a harder guess, and
with two killers acting at night, one save decides the game less often. The records fit that reading; the
check does not test it. The comparison also crosses models, from the Gemini models of June to mostly
Haiku in October, so a change in how the healer was played cannot be excluded.

### Finding versus acting on a find

The information roles repeated a nine-player pattern. Sentinel watches named an evil player 40 times,
Trailseer follows 58 times and finds by the investigator, who checks one player's identity each
night, 22 times. Of the 134 evil players they named, 81 (60%)
were later voted out. The number named per game showed no link with town wins (+0.09); the share later
voted out leaned the right way (+0.19, p = 0.12, 66 games). On nine players the investigator's find rate
failed and its find-to-lynch rate passed. Here the pattern is too weak to confirm.

### What the check changed

The check supported using the core town scores in this ten-player sample and left the healer's save
rate unvalidated as a proxy for winning. A save
remains good by the rules, since it keeps one more townsperson alive for the next day, and the decision
table still grades it that way. Its rate is no longer evidence that one version wins more than another.

It also left most new roles' scores graded by rules but unvalidated as proxies. Promoting any score
to "validated" in the live game's labels remains my decision, and none has been promoted. For the
next game version, the record names three changes: write scorers against sides rather than role
names, record each night's full outcome from the first game, and write down each new score's
expected direction before the first check.

### What it does not show

These are correlations in one pool of 78 games from one period. They show which scores tracked
winning there, not that raising a score causes wins. Examining 32 scores creates opportunities for
chance findings. Matching an earlier direction and checking within batches adds context, but does
not by itself correct for multiple comparisons. The new Chanteuse result is exploratory, even though
it appears alongside the carried-over metrics.

The check tested the per-game scores, not the decision table that grades every turn. Whether that table
as a whole rewards winning play remains untested. A count close to the result itself also says little:
the necromancer's nights survived correlated +0.51 with its wins, because it has to survive to win.

**Evidence.**

- [Play-quality metrics](../../../evidence/evaluation/metrics/report.md), §2 (the method) and §4 (the ten-player check).
- [The working record](../../../evidence/evaluation/metrics/experiment_log.md), entry for 2026-10-24.
- [Ten-player win check: the games and all 32 scores](../../../evidence/evaluation/metrics/data/ten_seat_win_check/README.md).

<!-- Sources for the page copy (checked 2026-10-25):
Opening, three groups: metrics/report.md §4 "The answer"; §7. Ten seats from twelve roles: §2 "How the
approach changed". Role descriptions: evidence/gameplay/roles/role_sheet.md (Sentinel l.117,
Trailseer l.118, Chanteuse blocks l.73); wolves = Chanteuse + Illusionist, lone killer = serial killer or
necromancer: Agents/schemas/roles.py.
Port: zeros "in every one of the 28 ten-seat balance games" and port 2026-10-11, night records, sides from
the registry: report §6; log B1. Three scorers switched "that morning": log 2026-10-24 correction;
report §5 item 5, §7.
Games: 78 from 2026-10-11, 41 excluded (choices, no outcome); models; 49 memory off; town 46 / wolves
17 / lone killer 15: report §4; data README table. Evil wins limit: report §4 "How sure we are".
Method: point-biserial per game vs own side's win; within batch = batch mean subtracted from score and
win; memory-off: ten_seat_win_check.py (check_score, within_batch_correlation). Batches with one game are
dropped from the within-batch reading (code); omitted as a detail.
Vote accuracy batch split: report §4; log 2026-10-24. "Two 12-game batches on other setups" = flash-lite
seeding and Haiku evil-cover batches (data README); simplified because one is Haiku.
Directions: log 2026-10-24 "owner's call, run first, then read". Interval: Fisher z (code,
correlation_range); +0.12 → −0.10 to +0.33 example: report §2 (Sentinel row, summary.json −0.106 to
+0.333). Failing only when range rules out expected size: report §2.
Results table: summary.json pooled_r, pooled_range_95, within_batch_r, memory_off_r, rounded to two
places; report §4 table. Vigilante 19 games, 16 of 22: log "The vigilante".
Healer: +0.36 (50) proxy_win_monotonicity.md / report §3; −0.03 (−0.26 to +0.20) report §4; save
definition Agents/rules/night.py verdict; rate and Chanteuse exclusion Agents/ten_seat_metrics.py 86-96
and log "The healer"; 220 = 79 + 141; 56 of 79; 36; 23; 1.07/1.03; 3.25/2.48; +0.29: log 2026-10-24.
Owner's reading: log. Cross-model caveat: report §3 (Gemini) vs §4 (mostly Haiku).
Information roles: report §4; log.
What changed: report §5 items 1-2, "What we would do differently" 1, 2, 4; VALIDATED_ON_TEN_SEAT_METRICS
empty and the owner's decision: report §4 "How sure we are"; log "Not done".
Limits: 32 scores, one or two by chance, carried-over rows beyond that: report §4; grades untested:
report §6; necromancer +0.51: report §4. -->

<!-- Completion note (2026-10-25)
Structure: opening (question, why it mattered, conclusion) → why the old check could not be assumed
(including the port) → the games → method (three readings, with vote accuracy as the worked reason) →
directions and intervals (the decision rule for a null) → results table → the healer → the information
roles → what changed → what it does not show. Follows the Level 3 layout. The parent keeps the lynch/
healer contrast, the healer mechanism in brief, the cross-model caveat and the rare-action limit.

Content-plan verification item: the 2026-10-24 check ran on scorers already reading the role registry.
Basis: (1) experiment_log.md 2026-10-24 "Correction, same day ... switched to the role registry that
morning (f13c43ea)"; (2) code path: ten_seat_win_check.py scores only through compute_game_metrics →
Agents/ten_seat_metrics.py, whose sides come from Agents.schemas.roles.ROLE_SPECS; none of the three
switched scorers (score_vote / hit_threat in decision_scoring.py, read_ledger.py, the discussion-evidence
judge's role join) is imported on that path. So the check's scores were registry-based regardless of
the switch's timing. I could not run git in this session to confirm f13c43ea precedes the run's base
commit (commands needed approval); the verifier may confirm with
`git merge-base --is-ancestor f13c43ea 74dc0bd0`. The page says "on the morning of the check" from the
record and that the three scorers were "outside this check" from the code.

Intervals: the ten-player 95% intervals come from summary.json (Fisher z in the runner), rounded to
two places; the new ones not printed in the report are −0.69 to −0.38 (power roles lost), +0.17 to +0.55
(lone killer voted out), +0.21 to +0.68 (serial killer's power-role kills), +0.06 to +0.49 (wolves voting
with the lynch), +0.09 to +0.50 (Chanteuse real blocks). These are read from the saved output, not
re-derived. The nine-player check reported no intervals, so none is given for +0.36 or +0.65.

Claims I was unsure of:
- Cross-model caveat on the healer: my addition (nine-seat Gemini vs ten-seat mostly Haiku); the report
  calls it "a real difference between the games". I kept "not a small sample" and added that a change in
  play cannot be excluded. Owner/verifier to accept.
- "Two killers acting at night": from the owner's reading. The nine-player game also had two killing
  sides (wolves and a serial killer), so I avoided presenting the number of killers as a difference
  between the games; the clause only explains why one save matters less (cf. the 23 saves where someone
  else died to the other killer). An earlier draft sentence saying the games differ in the number of
  night killers was removed for that reason.
- "Promoting any score ... remains my decision, and none has been promoted": record says it is the
  owner's decision and the list is empty. First person used because it is the owner's decision.
- The interval method name ("Fisher's transformation") is from the runner's code, not the report.

Left off (Handle with care / bookkeeping): the runner was uncommitted on the working tree at the time;
the first count of 119 games (an intermediate count, not needed); tests pinning the grade table; the
two scores that return nothing on ten seats (named in the report; not needed for this question); the
live-dashboard name. The phrase "validated in the live game's labels" stays, as the owner's pending
decision, not a fault.

First person: "I chose to run the check first" (owner's call, 2026-10-24); "My reading" (owner's reading);
"my decision" (owner's decision). Running the check is neutral.

Level 3 rubric self-scores: Added depth 2 (three readings, interval rule, healer records, batch
confound); Method inspectability 2 (inputs, exclusions, readings, directions, interval); Counting units
2 (games as the unit; protections, saves and named players labelled as such; 75/70/45/20/19-game
denominators shown); Decision-rule precision 2 (carried over / too few games / did not carry over, with
the null rule); Analytical assumptions 2 (owner's reading labelled; exploratory rows labelled); Scope
alignment 2 (cross-model and pool limits beside the healer and the conclusion); Bounded consequence 2.
Length: about 1,500 words of page copy (estimated), at the top of the guide; the results table and healer section
carry most of it. -->
