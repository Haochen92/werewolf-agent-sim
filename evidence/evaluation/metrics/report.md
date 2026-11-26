# Play-quality metrics: scoring how well the agents played

This page covers the scores that code works out from a saved game record to say how well the agents
played: the share of votes that hit a real threat, a grade for each decision, how right a player's guesses
about roles were, who won. No model is called, so a score costs nothing, gives the same answer every time,
and is computed the same way for both sides of a comparison.

The page leads with the approach: why code scores play, how a decision is graded, and how a score is
checked against winning. Two test runs, on the nine-seat game in June–July 2026 and on the ten-seat game in
October 2026, follow as the evidence, then what they taught and the scores in use today.

Not here: how a judge's or a person's labels are scored ([scoring](../scoring/report.md)); pass-or-fail
checks with no score ([deterministic_audits](../deterministic_audits/report.md)); the controls on a
comparison ([experimental_controls](../experimental_controls/report.md)). The full working text, with code
paths, line numbers, every dated correction and the ten-seat run's detail, is the
[experiment log](experiment_log.md). How the nine-seat scores were designed, with all 48 candidates and the
July audit logs, is in [`../../metrics/`](../../metrics/README.md). How it all fits together is in
[the hub](../report.md).

## In short

- **Code scores play, because the win alone carries too much luck** and the early model judges could not
  compare memory on with memory off.
- **The rules say what a good move is.** A save keeps a townsperson alive, a vote on a wolf removes a threat;
  each decision is graded against the true roles by that rule.
- **The check against winning is support, and a way to catch surprises.** It started as the gate a score had
  to pass (June 2026); on the ten-seat game the rules come first and the check confirms or questions them.
- **Both runs agree on the core.** The town's lynch scores, power roles lost at night and wolves blending in
  go with winning on both games. The healer's save rate did on nine seats and does not on ten, for a reason
  the records show. Most new roles' scores need more games than the 78 there are.

## Quick view

| Score | Trust | Main limit |
|---|---|---|
| Town lynch scores, power roles lost at night, lone killer lynched | ✅ both games | 78 ten-seat games, mixed models |
| Wolves voting with the lynch; serial killer's kills of power roles | ✅ both games | 17 wolf wins, 7 serial-killer wins on ten seats |
| Town vote accuracy | ✅ as a count; 🟡 on ten seats | Weak in two flash-lite batches |
| Healer save rate | ✅ nine seats · ❌ ten seats | Does not go with winning on ten seats (§4) |
| New roles' scores (Chanteuse, Sentinel, Trailseer, Sigilist, Illusionist) | 🟡 rule-graded | Too few games to test; Chanteuse real blocks pass |
| Investigator finds, vigilante shots | 🟡 rule-graded | Rare: 20 and 19 games |
| Ten-seat decision grades | ⚠️ | The owner's table, applied exactly; never tested against win as a whole |
| Read Brier score | 🟡 | Two confidence levels, most reads "unclear" |
| Counts used to judge prompt and rule changes | ✅ as counts · 🟡 as readings | 4–31 games each, one model |

✅ sound · 🟡 usable with caveats · ⚠️ weak · ❌ does not hold.

---

## 1. Why code scores play, not a judge

**The question:** how do you tell whether one version of the agents plays better than another?

**The win is too lucky to do it alone.** A game ends in one bit, which side won, and that bit carries the
luck of the role deal, of whom the wolves happened to target, and of every coin-flip vote. Seeing a
moderate effect through it takes hundreds of games. A game holds many decisions, though (every vote, every
night target, every protection), and each can be graded against the true roles. Many graded decisions per
game vary far less than one win bit, so an effect shows at a game count the project can afford.

**The early judges could not referee an A/B.** The first model judges described memory quality, but their
scores were subjective and they ran only in the memory-on games, so they could never compare memory on with
memory off.

**Two other designs were tried and turned down** (June 2026):
- **A code-graded "vote decision quality", weighted by how sure the voter could be.** Almost no player
  knows a role for certain: only the investigator (its own checks), the vigilante (a shot that bounced off
  the serial killer) and the wolves (each other). The one signal of how uncertain a seat was, the situation
  summary, existed only in memory-on games, and a weight that exists on one side biases the comparison.
- **Making every agent write out a belief about each player.** Changing what agents must output changes how
  they play, which spoils the very comparison it was meant to measure. It is also circular: a model's vote
  already follows what it says it believes, and whether the belief was right still needs the true roles.

So the project scores outcomes of decisions, computed from the record.

## 2. The approach

### Grade each decision by the rules, against the true roles

**A good move is defined by the game's rules.** A save is one more townsperson alive the next day; a town
vote on a wolf removes a threat; a vigilante shot on an evil player is a hit; a Sentinel watch that names an
evil visitor is a find. On the ten-seat game every kind of turn has a row in a table the owner ruled (good,
neutral or bad), and code grades each decision by it.

**Grading the decision, not the game, takes out most of the luck.** A town vote on a wolf counts as right
even if the town later loses on an unrelated coin flip, so the luck of the deal, of everyone else's play and
of how the game snowballed falls away.

**A rate divides by the chances a player had.** This is fairness, not luck removal. A healer who lived nine
nights would outscore one killed on night 2 on "saves per game" for no reason but survival, so its rate
divides saves by the nights it actually protected someone. A role that never had a chance gets no score,
not a zero.

**What is left is the luck inside one decision.** A villager who votes blindly and hits a wolf scores like
one who reasoned it out, and a healer's save depends on whom evil chose to attack. Over many games that
averages out; it is never removed from a single decision. The project's name for these scores,
"de-lucked", means *less lucky than the win*, not luck-free.

**What goes in.** The trusted nine-seat scores read only facts the game engine recorded: votes, revealed
roles, deaths, night targets. One supporting score also reads the agents' own accusation tags, which the
playing model writes, so it sits a step lower. None reads a judge's output.

### Check the score against winning

**The question:** a rule says a move is good. Does making more of those moves win games?

Each score is correlated with its own side's win across a batch of games (a number from −1 to +1; the
town's best scores come out near +0.5 to +0.65). This catches a score whose meaning looked obvious and was
wrong, and it is the evidence an A/B headline needs: "memory made them win more" rests on scores that go
with winning, not only on moves the rules call good.

**Each check guards against one way of being fooled:**
- **Memory raising both the score and the win.** Every score is also read on the memory-off games alone.
- **Batches that differ.** A batch that both played differently and won more can make any score look linked
  to winning, so the ten-seat check also reads each score within batch.
- **A score diluted by games where it cannot matter.** On nine seats the wolves' night-kill score looked
  null over 180 games; in 77 of them the wolves could not win at all (when the town never lynched the
  serial killer, the serial killer won). Within the 103 games where it was lynched, the score went clearly
  with wolf wins.
- **Testing many scores and keeping the lucky ones.** With 30 or more scores, one or two pass by chance.
  The correction was applied by hand where it mattered, and scores that measure one thing count as one
  witness: four town vote scores moving together are one measure, not four.
- **A score that is close to the win itself.** A lone killer that survives longer wins more almost by
  definition, so a survival count says little about skill.

**A null on few games means "not yet tested", not "fails".** The check reports a range as well as a value.
A score at +0.12 over 78 games has a range of about −0.10 to +0.33, so a real link of +0.3 is still
possible. Seeing a link of 0.2 reliably takes about 190 games, and the evil sides, with fewer wins, need
more. A score is read as failing only when the range rules out the size it should have, as with the healer
(§4).

### How the approach changed

| When | Where trust in a score came from |
|---|---|
| **June 2026**, nine-seat | **The check was the gate.** Scores were candidates and the check against winning chose among them: 48 tried, 11 kept, 3 supporting, 5 marked do-not-use |
| **July 2026** | **First exceptions.** A score whose direction the rules fix (a vigilante shot on an evil player) may report on its own kind of decision even when the action is too rare to test, but may not decide a comparison's result. Memory's credit rules were written from game logic, not mined |
| **October 2026**, ten-seat | **The rules come first.** The owner's table defines a good move for every kind of turn before any data exists. The check confirms a score, or questions it when a result is surprising |

It changed because the ten-seat game deals ten seats from twelve roles, which leaves too few games per role
to choose scores the June way, and because memory's credit needed a grade for every decision from the first
game. The check still decides one thing: whether a kind of move the rules call good actually wins games.

## 3. Evidence, run 1: the nine-seat check (June–July 2026)

**The question:** which of the nine-seat scores went with winning?

**The answer: the town's, clearly; the others only in part.** The June check ran on 50 games (30 memory
off, 20 on), the July audit on 180.

| Side | Verdict | What went with winning | What did not, or is not measured |
|---|---|---|---|
| **Town** | ✅ | Share of lynches that hit a threat (+0.65 in both readings); share of town votes on a threat (+0.62 over 50 games, +0.57 over the 30 memory-off); lynching the serial killer (+0.64, +0.85); the healer's saves per protection night (+0.36, +0.33). All held again on the 180 July games | — |
| **Investigator** | 🟡 | A confirmed wolf reaching a later lynch (+0.40, 180 games); how fast the town followed a find (+0.31, a supporting score) | How often it found wolves (−0.09, −0.14: do-not-use). An early alarm that later finds went with *more* town wins (+0.38 over 30 games) shrank to +0.15, not significant, at 180 games: small-sample noise |
| **Wolves and serial killer** | ⚠️ | Serial killer's kills per night survived (+0.26); its kills of town power roles (+0.32); wolves voting with the day's lynch, i.e. blending in (+0.27); wolf night kills on power roles, only in games where the serial killer was lynched (+0.31 over 103 games); for the town, power roles lost to night kills (−0.40) | Wolves leading a vote: a count cannot tell a wolf who drove a lynch from one who joined it. Wolves accusing townspeople was expected to help them and came out the opposite way (−0.33): wolves who attacked town lost more. The wolves' strongest single link with winning, the serial killer being lynched (+0.46), is something the town does, not the wolves |
| **Town discussion** | 🟡 | The share of town accusations aimed at real threats (+0.34) | It adds nothing beyond vote accuracy (+0.02 once vote accuracy is held fixed, 175 games): town discussion changes the result only by turning into votes. No wolf discussion score worked: "the wolf leads the accusation" was null (−0.09, 53 games), and in 127 of 180 games no wolf accused the player later wrongly lynched |

**One cheap explanation was ruled out:** that the speaking-order scheduler starved the investigator or the
wolves of chances to speak. Investigators with a find to share spoke before the vote 58 times out of 58,
and wolves held the floor before the pile-on on 76.5% of such days.

**How sure we are:**
- Each figure is from one batch, all nine-seat, on the Gemini models of the time. The vigilante's
  correct-shot score went from +0.43 to +0.18 between the two batches, partly because vigilantes fired in
  72% of the earlier games and 29% of the later; the town's vote scores (+0.65 on both) and the healer's
  (+0.36, then +0.40) held.
- The correlations show which scores track winning, not that a score causes a win.
- Three smaller nine-seat checks are kept in the log: whether a measure of how much a turn is at stake picks
  out decisive turns (B4), whether the wolves' "blend your vote" tactic goes with winning (B8, a trend at
  p = 0.07), and whether the investigator's find reached the village (B9, a keyword match).

## 4. Evidence, run 2: the ten-seat check (2026-10-24)

**The question:** on the ten-seat game, do the rule-graded scores go with winning?

**The data.** 78 ten-seat games from 2026-10-11 on, whose every night carries its full record: mostly
Claude Haiku 5.5, with flash-lite seeding games and a few GPT-6 Luna games. Memory was off in 49. Town won
46, the wolves 17, the lone killer 15 (serial killer 7, necromancer 8). The 41 phase-3 games of October 9
and 10 record each night's choices but not their outcome, so they cannot be rescored and are left out.

**The answer: the core carries over; the healer does not; most new roles' scores need more games.**

| Group | Score | All games | Within batch | Memory off |
|---|---|---|---|---|
| **Carries over** | Share of lynches that hit a threat | +0.49 | +0.55 | +0.48 |
| | Share of lynches on townspeople | −0.45 | −0.49 | −0.48 |
| | Town power roles lost to night kills | −0.55 | −0.55 | −0.43 |
| | Town lynches the lone killer | +0.38 | +0.40 | +0.43 |
| | Serial killer's kills of power roles (45 games) | +0.48 | +0.58 | +0.47 |
| | Wolves voting with the lynch (70 games) | +0.29 | +0.36 | +0.22 |
| | New: Chanteuse blocks of a real town action | +0.31 | +0.28 | +0.45 |
| **Rule-graded, too few games** | Sentinel watches naming evil | +0.12 (−0.11 to +0.33) | | |
| | Sigilist hits | +0.20 (−0.03 to +0.40) | | |
| | Trailseer follows naming evil | +0.03 (−0.20 to +0.25) | | |
| | Investigator finds turned into lynches (20 games) | +0.29 (−0.18 to +0.65) | | |
| | Vigilante correct shots (19 games) | +0.29 (−0.19 to +0.66) | | |
| **Does not carry over** | Healer saves per protection night (75 games) | −0.03 (−0.26 to +0.20) | | |

Ranges in brackets are 95%. The full table of 32 scores is in
[`data/ten_seat_win_check/`](data/ten_seat_win_check/README.md).

**The healer: a good move that decides fewer games.** A save is a night the healer protected a player who
was attacked and lived; by the rules it is one more townsperson for the next day. On ten seats the healer
made about one save a game whether the town won (1.07) or lost (1.03); what differed was how long the
healer lived (3.25 protection nights in games the town won, 2.48 in games it lost). Of 220 protections,
79 were saves and 141 guarded someone nobody attacked; 36 of the saved died later, and in 23 saves someone
else died that night to the other killer. With more information roles to guard and two killers a night,
whom to save is a harder guess and one save changes the result less often. The range rules out the
nine-seat size (+0.36), so this is a real difference between the games, not a small sample.

**The information roles: finding is not what wins, again.** Sentinel watches named an evil player 40 times,
Trailseer follows 58 times, investigator finds 22 times. Of the 134 evil players the three named, 81 (60%)
were later lynched. How many evil players they named per game shows no link with the town winning (+0.09);
the share later lynched leans the right way (+0.19, p = 0.12, 66 games). That is the nine-seat pattern
(turning a find into a lynch mattered, the find rate did not), too weak to confirm at this size.

**Vote accuracy: a batch difference, not a memory one.** +0.37 over all games, but +0.24 (p = 0.10) with
memory off. By batch it is +0.54 in the 29 memory-on games, +0.37 in the memory-off Haiku persona games, and
+0.08 and +0.16 in the flash-lite seeding and evil-cover batches (12 games each). Average vote accuracy was
the same with memory on and off (0.57, 0.59). The memory-on games are nearly all Haiku, so memory and model
cannot be told apart here.

**How sure we are:**
- 78 games from one pool of versions and models, with 17 wolf wins and 15 lone-killer wins; 32 scores
  tested, so one or two may pass by chance. The "carries over" rows are well past that, and each matches its
  nine-seat direction.
- The new roles' directions were not written down before the run; those rows are exploratory.
- Rare events stay rare: the vigilante fired in 19 games (16 of 22 shots on evil players), and critical
  Chanteuse blocks happened 35 times in 26 games (+0.10).
- The necromancer's nights survived (+0.51) goes with its win almost by definition, as the serial killer's
  nights survived did on nine seats (+0.555).
- No score has been named "validated" in the code yet (`VALIDATED_ON_TEN_SEAT_METRICS`); that changes the
  labels the live game sends and is the owner's decision.

## 5. What the two runs taught

1. **Finding is not what wins; turning a find into a lynch is.** On nine seats the investigator's find rate
   failed and its find-to-lynch rate passed. On ten seats the number of evil players the three information
   roles named shows nothing, and the share later lynched leans positive.
2. **A move can be good by the rules and still not decide games.** The healer's save is always good for the
   town; on ten seats it no longer separates won games from lost ones. The rule grade and the check answer
   different questions, and both are needed.
3. **Read a score within the games where it can matter.** The wolves' night kills showed only in games where
   the serial killer was lynched; the ten-seat scores are read within batch so batch differences cannot fake
   a link.
4. **Survival counts sit close to the win.** Both runs had a lone killer whose nights survived went with its
   win almost by definition; a rate per night survived is the skill-bearing form.
5. **Scorers written against role names break when the cast changes.** Three scorers scored the new evil
   roles as town until they were switched to the role registry on 2026-10-24; three places still name the
   nine-seat roles (§7). Writing against sides from the registry, as the ten-seat metrics do, carries over.

## 6. The scores in use on the ten-seat game

### Per-game metrics and per-decision grades ⚠️

**What they are.** Two scorers, both code.
- **Per-game metrics** (`Agents/ten_seat_metrics.py`). They recompute the 21 nine-seat metrics that a
  ten-seat game cannot fill, from each night's full record, and add scores for the new roles: the
  Chanteuse's blocks (real, critical, wasted), the Illusionist's conceals, the Necromancer's nights
  survived, the Speculator's pick and whether its side won, the Fortune Teller's points, Sentinel and
  Trailseer results that named an evil visitor, and the Sigilist's hits. Before this port (2026-10-11),
  the nine-seat code read fields a ten-seat game never fills, and those metrics read 0 in every one of the
  28 ten-seat balance games even when the event happened.
- **Per-decision grades** (`Agents/memory/consolidation/grading.py`, 2026-10-13). Each decision is graded
  good, neutral or bad, or left unscored, by the owner's table. Memory's credit uses the grades.

**What they can claim.** What the engine recorded, exactly: a block cancelled a town action, a bet scored, a
decision matched the table's "good" row.

**What they cannot claim.** That the table as a whole rewards winning play: the check in §4 tested the
per-game scores, not the grades.

**How far checked.**
- The metrics were checked by hand against one pilot game, and against winning in §4.
- The grade table's rows are pinned by tests, which are AI-written and unaudited: they show the code
  follows the table, not that the table is right.
- On the 12 memory-off seeding games the average grades looked as the rules predict: the Fortune Teller at
  −0.60 because most bets miss, the Sigilist at −0.35, the pack's kill at +0.42.
- Grades reached 1,711 of the 2,277 observations extracted from 40 games. The rest name no single decision,
  name an unscored one, or come from a served game whose result could not be rebuilt.

### Read Brier score 🟡

**What it is.** Before each decision a seat writes a *read* of every other player: a suspected role with
"high" or "low" confidence, or "unclear". The Brier score measures how well the committed reads matched the
roles revealed at the end; lower is better. "Unclear" reads claim nothing and are counted apart. A read the
seat already *knows* (a wolf's read on its packmate) is left out, so the score measures inference, not
private knowledge.

**What it can claim.** Whether committed reads matched the true roles, by role, phase and side, on the same
deals. Its one use as a headline: in 16 persona-voice games, reads were better with voices on (0.129)
than off (0.155), in 7 of 8 pairs (sign test p ≈ 0.07).

**What it cannot claim.**
- A calibration curve: two confidence levels give only a two-point check.
- Much about most reads: 86.8% (voices off) and 87.3% (voices on) were "unclear", so the score rests on the
  1,105 and 973 committed reads.
- That a lower score means better play: it has not been tested against win or against a person's reading.

There are two versions: the ledger (`read_ledger.py`) and a ten-seat re-implementation in
`persona_voice_games_score.py`, which takes sides from the role sheet. Until 2026-10-24 the ledger counted only
wolves and the serial killer as threats, so on a ten-seat record it mis-scored sides without warning; it now
reads the role registry (`f13c43ea`), and nine-seat records score as before.

### Vote-target accuracy ✅ as a count

**What it is.** A vote is right when it names a real threat. Three forms are in use: the share of town votes
on a threat in the per-game metrics (ten-seat-ready, since it takes sides from the role registry); one vote
scored against the true roles, used by the replayed-vote screens; and, for one replayed game, the exact
right target per day written into the scorer.

**What it can claim.** Whether the vote hit a threat. That is the outcome itself, so the count is exact.

**What it cannot claim.** Whether the vote was well reasoned on what the seat knew: a lucky vote counts as
right, a sound vote on a well-hidden threat as wrong. Until 2026-10-24 the single-vote scorer named only
wolves and the serial killer as threats, so a vote on the Chanteuse scored as a miss; it now reads the role
registry (`f13c43ea`).

### Counts used to judge prompt and rule changes ✅ as counts · 🟡 as readings

Since October most play work has been prompt and rule changes judged on a few games, which need scores that
are cheap and exact even when there are too few games to test them against win.

| Counts | What they showed | Data | What they cannot show |
|---|---|---|---|
| **Discussion census**, before the redesign | 1,166 messages, 517 passes (367 forced by the novelty gate); of 194 accusations, 47% rested on behaviour and 20% on a concrete claim | 28 nine-seat games, 2026-09-17, flash-lite, memory off | Independent labels: the evidence labels come from the model that plays. The real measure went to a separate judge |
| **Phase 2 per-day counts**, comparing scheduler designs | 5 of 106 opening turns spoken; closings on 7 of 12 voting days, the defended player voted out all 7 times | 4 nine-seat games, 2026-10-07, flash-lite | Rates: four games, and in one, 36 of 115 calls went to the rescue model |
| **Balance batches**, to set the role rules | Town won the first 13 games, then 3–3, 6–0 and 5–1 under later rules; the pack aimed 34 of its 56 kills at information roles | 31 ten-seat games, 2026-10-09 and 10, flash-lite | That a rule caused a lynch; anything stable from batches of six; balance on Haiku, which the live game now uses (no Haiku balance batch exists) |

**A lesson from the census:** a first keyword count said 32 day summaries named a quiet player. Reading the
matches found 4 of 124; most hits were day-1 lines such as "no players are staying quiet yet". Counts of
structure never needed that check; both counts of meaning on record (this one and the investigator's
"claimed" find) did.

### Batch summary

`scripts/analyze_batch.py` gives win rates and the mean, spread and range of each metric per batch. It reads
the metrics stored in each record at game time and does not recompute, so a ten-seat record from before the
2026-10-11 port still carries the old zeros. It does no paired comparison and gives no interval. No record
cites a run of it.

## 7. Cautions that apply to every score

- **Ten-seat evidence is one run of 78 games**, mostly on Haiku and flash-lite. It confirms the core and
  leaves most new roles' scores untested.
- **Exact counts, small samples, one model.** The October prompt and rule counts come from 4 to 31 games,
  mostly on flash-lite, so they show direction and mechanism, not size.
- **Three places still use nine-seat role names.** Two return nothing on ten seats: how fast the town
  followed an investigator's find, and the lynch-day wolf blending rate. One research helper,
  `query_criticality` (how much a board is at stake, used by the nine-seat case sampler), counts the literal
  wolf and serial-killer roles. Three others (the single-vote scorer, the read ledger, the discussion-evidence
  judge's role join) scored the new evil roles as town until they were switched to the role registry on
  2026-10-24 (`f13c43ea`).
- **Counts of meaning need a read.** Wherever a count stood for something semantic (a quiet player named, a
  find "claimed"), keyword counts were wrong until someone read the matches.

## What we would do differently next time

| Stage | Change | What was done | What it would buy |
|---|---|---|---|
| Design | **1. Write every scorer against sides, never role names** | Six places hard-coded the nine-seat roles; three fixed on 2026-10-24 | A new role set scores correctly the day it ships |
| Data | **2. Record each night's full outcome from the first game of a new version** | Added on 2026-10-11, after the 41 phase-3 games | Every game of a version can be rescored, not only the later ones |
| Validation | **3. Run the check against winning on the first batch of each new version, and report ranges** | Nine-seat twice; ten-seat once, on 2026-10-24 | A version's scores are confirmed, or questioned like the healer's, before a comparison leans on them |
| Validation | **4. Write down each new score's expected direction before the run** | Ten-seat new-role scores were read after the run | A new score's result counts as a test, not exploration |
| Data | **5. Read a sample of matches before reporting any keyword count** | The census's first keyword count was read afterwards and was 8 times too high | Counts of meaning that can be quoted |

**Bottom line.** The rules define what a good move is, code grades every decision by them, and a check
against winning confirms that those moves win games. On both games the town's lynch scores and power roles
lost at night pass that check, and wolves blending in does too. The healer's save stays a good move but no
longer decides ten-seat games the way it did on nine seats. Most new roles' scores are graded and waiting on
more games.

## Sources

| What | Code | Record |
|---|---|---|
| Nine-seat scores and their check against win | `Agents/compute_metrics.py`, `Agents/schemas/metrics.py`, `evaluation/src/instrument_validation/proxies/`, `evaluation/src/core/stats.py` | [`../../metrics/`](../../metrics/README.md) (`proxy_win_monotonicity.md`, `candidate_ledger.md`, `experiment_log.md`, `design/`, `metrics_audit/`); [log](experiment_log.md), Part A |
| Ten-seat check against win | `evaluation/experiments/ten_seat_win_check.py` | [`data/ten_seat_win_check/`](data/ten_seat_win_check/README.md); [log](experiment_log.md), 2026-10-24 |
| Trust labels sent with each score | `Agents/compute_metrics.py` (`_metric_tier`, `VALIDATED_ON_TEN_SEAT_METRICS`) | `memory_system/v8/plan.md` §8.4 |
| Ten-seat metrics | `Agents/ten_seat_metrics.py`; `compute_game_metrics` | `memory_system/v8/{plan.md §8.1–8.4, decisions.md §8}`; log B1 |
| Ten-seat decision grades | `Agents/memory/consolidation/grading.py`, `scripts/grade_observations.py` | `memory_system/v8/{plan.md §9.6, decisions.md §12–13, experiment_log.md 2026-10-13}`; log B1 |
| The save verdict | `Agents/rules/night.py` (the verdict step) | log, 2026-10-24 |
| Read Brier | `evaluation/src/loop/read_ledger.py`, `evaluation/experiments/persona_voice_games_score.py` | `credit/report.md` §1, §4; `gameplay/data/persona_voice_games/`; log B2 |
| Vote-target accuracy | `Agents/compute_metrics.py`, `Agents/memory/consolidation/decision_scoring.py`, `evaluation/experiments/haiku_vote_score.py` | log B3; [turn replays](../evaluation_scopes/turn/report.md) |
| Discussion census | `evaluation/experiments/discussion_evidence.py` (`census`) | `gameplay/discussion_evidence.md` §2; log B5 |
| Phase 2 per-day counts | `evaluation/experiments/phase2_step8_{capture,counts}.py` | `gameplay/data/phase2_step8_games/`; log B6 |
| Balance batches | `evaluation/experiments/phase3_capture.py` | `gameplay/data/phase3_{games,balance*}/`; `discussion_evidence.md` §8.3, §8.5; log B7 |
| Batch summary | `scripts/analyze_batch.py` | log B10 |

*Rewritten 2026-10-24 as a plain summary of the 2026-10-23 trust write-up, which is kept whole as the
[experiment log](experiment_log.md) (Part A and B1–B10 there), and reorganised the same day around the
approach, with the ten-seat check added as the second run. The tests named here are cited for what they
pin; the test suite is largely AI-written and unaudited, so no test count is offered as evidence.*
