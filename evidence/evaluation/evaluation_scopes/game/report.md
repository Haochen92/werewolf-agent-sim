# Whole-game evaluation: outcomes and cascading effects

This page covers the project's whole-game tests: play the same deals twice, once with a change and once
without, and compare how the games went. It covers why the project uses them, how they are set up,
where they were used, and how far each result can be trusted. How this fits with the other ways the
project evaluates is in [the hub](../../report.md). The full detail of each test (every command,
correction and count) is in [the detailed record](experiment_log.md). What each test found about the
design itself is in the design folders linked from each case.

## Why whole games

**Whole games are the only way to measure outcomes and cascading effects.** Some questions only exist
across a whole game: who wins, and whether the sides stay balanced. And many changes cascade. A lesson
changes a vote on day 1, a different player is dead by day 3, and every later decision differs. A
replay cannot show that, because it freezes everything after the changed turn.

**The price is noise, from those same cascades.** The cascade, plus the model's randomness, makes two
games on the same deal drift apart. One game tells you little, so an answer needs many. The noise
comes from exactly the thing being measured.

**One more thing only whole games give:** a test of the system as it really runs. Replies in prose
instead of moves, stalls, the real cost per game, and a leak check misfiring on a new feature all
surfaced only in whole games. That is an end-to-end smoke test rather than a measurement, but it is
real.

## How a whole-game comparison is set up

The two arms are set up the same in every way except the one thing under test.

- **Held fixed (the controlled variables):** the deal (the game id seeds the role draw, so both arms
  get the same roles in the same seats), the model and its thinking level, the code and prompts (one
  commit), anything that could change during a run (a memory store is read-only for the test), and the
  time window (both arms run together, so a provider's overnight model change hits both).
- **Changed (the independent variable):** the one design under test, such as memory on against off.
  The arm without the change is the *control arm*; the arm with it is the *treatment arm*.
  The changed variable can also be the model itself, as in the seat-model games of
  [model_admission](../../model_admission/report.md). Two cautions apply there: a new model often brings
  its own call mode or prompt tweaks, so the arms differ by a model *and its setup*; and model choice
  is mostly a gate (can it play, is it clearly worse than the default), so it is compared first on
  saved turns with every input fixed, and in whole games last. A model change nobody chose (a
  provider update, or a switch forced by quota) is not a variable at all: it starts a new baseline,
  and earlier results are never compared against it.
- **Measured (the dependent variables):** decision scores computed from the game record, and wins.
- **Not controlled: the model's sampling.** Players run at temperature 1.0, so the two games part ways
  at the first line that differs. Only the start is identical; everything after it is played fresh.

That last point is what separates this from a frozen-turn replay
([turn replays](../turn/report.md)), where the whole history up to one turn is fixed and
only that turn is rerun.

Three practices follow:

- **Run both arms at the same time.** A hosted model can change with no code change. In June a fresh
  no-memory baseline, on identical prompts, came back with the villagers winning 1 of 10 deals against
  20 of the original 30 (p=0.0028, games treated as independent); on the 20 deals played in both, tested
  as pairs, the town's wins fell from 12 to 7 (exact McNemar p=0.18). Drift and chance could not be told
  apart, so both arms now run in the same window and an old baseline is never reused
  ([experimental controls](../../experimental_controls/report.md)).
- **Score decisions, not only wins.** With 30 games a side, only a win gap of about 35 points would
  reliably show. So the verdict rests on decision scores computed from the game record (did the town
  vote out an evil player, did the healer save the real target), which were checked against winning
  before use ([metrics](../../metrics/report.md)).
- **Use paired tests.** Each deal's two games are compared with each other: exact McNemar for wins,
  Wilcoxon for decision scores.

The deal is pinned by the game id; a test (`tests/engine/test_seedability.py`) holds this for the
ten-seat game, and in June it was checked by hand on 20 of 20 ids. The arms differ by a config flag on
one commit where possible; a structural change runs the old version from a git worktree on a tagged
commit instead.

**What pairing turned out to buy: almost no noise reduction.** In June, the same deal was played
several times with nothing changed. Games on the same deal spread as widely (0.249) as games on
different deals (0.21–0.26). If the deal mattered, same-deal games would land much closer together.
At temperature 1.0, almost all the variation comes from how a game plays out, not from who was dealt
what, so fixing the seed barely reduced the noise the tests have to see through. It is still the
default, because it is free, it rules out "one arm got easier deals", it lets matched games be read
side by side, and it makes a run repeatable. What actually made the June comparison fair was running
both arms in the same window. This was measured on the nine-seat game and not re-measured on ten
seats.

## Choosing between a whole game and a replay

A change can be judged three ways, and each sees something the others miss:

| | Whole-game A/B | Frozen-turn replay | Reading lines (blind read) |
|---|---|---|---|
| **What it sees** | Wins and decisions over whole games, including effects that build up over days | One decision, rerun with one input changed | Whether lines read better or worse |
| **What it misses** | Why something changed | Anything that plays out later in the game | Whether better lines change outcomes |
| **Cost** | One ten-seat game on Haiku 5.5: about $0.08–0.26 (16 games in October). One 30-game memory arm in June: about $15–30 | Under $0.01 to about $0.25 per screen, all samples included (October) | No per-call API charge: Claude subagents, covered by the owner's subscription |
| **Noise** | High: games diverge after the first move | Lower: one moment, sampled many times | Reader to reader |
| **Sample needed** | 30 games a side detects only a win gap of about 35 points | Tens of samples per case | Tens of lines per arm |

**When to use which.** Replay first: for a question about one decision, a replay isolates the cause,
holds everything else fixed and finishes in minutes. Escalate to whole games only when:

1. **the question is an outcome over a game**, such as who wins or whether the sides stay balanced;
2. **the effect builds across turns**: a lesson used on day 1 changes who is alive on day 3, or a
   change makes players talk more and so gives everyone more to read;
3. **a new feature has to be shown running in the real game loop**: no crashes, the leak check
   passing, the real cost per game.

A whole game does produce about 150 decisions, but they are not independent: they share one game's
history and move together. That is why the unit of analysis is the deal, not the decision.

**What drives the cost is how many model calls an answer needs.** A call costs about the same either
way (about $0.001–0.0015 on Haiku 5.5). A replayed turn is one call, so a screen costs whatever
number of samples it runs: turns × samples × arms. The October screens ran 75 to 164 calls, under
$0.01 to about $0.25 each. A ten-seat game is about 150 player calls ($0.08–0.26 on Haiku), and an
answer needs many games: 16 for an 8-deal direction check, 60 for a 30-deal test, which is thousands
of calls, each game taking several minutes. The reason is noise. A replay sample measures the changed
decision directly, so a few dozen samples show an effect; in a game the change touches a few of its
calls, the rest is noise around it, and the games diverge, so many are needed. On pricier models the
gap grows (one game cost $0.72 on flash-lite and $2.72 on flash).

**The missing middle step: a per-day replay.** Between one turn and a whole game sits replaying one
whole day: rebuild a recorded game up to day *k*, then let that day play out live under the change,
with every turn, the real speaking order and the votes. It would show effects that build within a day
without the noise of whole games, at about $0.10–0.15 per day. It was designed in July 2026 and never
built ([turn replays](../turn/report.md), the per-day replay section). Looking back, the
October voices question fit it better than either a turn replay or whole games.

## Where the project used it

| Test | Question | Games | Result | Trust | Detail |
|---|---|---|---|---|---|
| June memory A/B (nine-seat, June 2026) | Do players with memory of past games play better than players without? | 30 deals per arm | The town's decisions improved (healer saved the real target 37% → 60%, p=0.005; town votes removed an enemy 47% → 64%, p=0.028). Town wins rose 27% → 43%, not significant (p=0.27). Wolves and the lone killer gained nothing | 🟡 | Case 1; log §1 |
| Strategy-point A/B (nine-seat, 2026-06-17) | Do lessons distilled from past games help more than plain memories of what happened? | 30 deals, six arms | Nothing significant; the June town gain did not repeat (+6 points, p=0.77) | 🟡 | log §2 |
| v7 endpoint (nine-seat, 2026-07-20) | Does a memory store built over four rounds of games beat no memory, under a test fixed in advance? | 30 deals, 60 games | Town decision score 0.147 lower with memory (p≈0.06), lower on 19 of 30 deals; closed as "no compounding detected", leaning toward harm | 🟡 | Case 2; log §3 |
| Persona voices (ten-seat, 2026-10-18) | Do players still read each other as well when every seat talks in a character's voice? | 8 deals | Reads were better with voices on 7 of 8 deals (p≈0.07), but the voiced games had 19% more talk to read | ⚠️ | Case 3; log §4 |
| Evil covers (ten-seat, 2026-10-18) | After the changes to the evil seats' cards and prompts, do evil seats fake a role claim, and what does it do to balance? | 8 deals | Evil seats claimed a role 11 of 24 times against 3 of 24; wolves won 3 of 8 against none | ⚠️ | Case 3; log §5 |

The silence calibration (four games before and after a silence-rule change) uses the same pattern; its
reads are rated in [sampled reads](../../labeling/sampled_reads/report.md).

✅ sound · 🟡 usable with caveats · ⚠️ smoke test only.

---

## Case 1. The standard harness: the June memory A/B

**What and why.** The first real test of memory: on 30 deals, do players who can look up lessons from
past games play better than players who cannot? Wins were the obvious measure, but at 30 games a side
only a huge gap would show.

**How it works.** `scripts/run_batch.py` plays each arm on the same frozen list of game ids, with the
memory store read-only so it cannot grow during the test. An analysis script pairs the two arms' games
by id and runs the paired tests on wins and on the validated decision scores. A cheaper frozen-turn
screen ran alongside as a cross-check.

**Result.** Memory improved the town's decisions: the healer saved the real target 37% → 60% of the
time (p=0.005), and town votes removed an enemy 47% → 64% (p=0.028), over 30 boards. Town wins rose
27% → 43%, which was not significant (p=0.27). Wolves and the lone killer gained nothing. The
frozen-turn screen pointed the same way on decisions.

The harness also corrected itself. Its first baseline was thrown out when a fresh one came back
different (above: 1 of 10 deals against 20 of 30; tested as pairs, p=0.18, cause not established),
which led to the same-window rule. And its own check showed that
pairing by deal adds almost no power, which changed what the design was understood to buy.

**How far to trust it.** 🟡. The method is sound and the limits are its own findings: wins are too
noisy at this size, and pairing buys little. Never cite "+17 points, p=0.013": that p-value belongs to
a different arm (+33 points with reranking, which carries a model-drift caveat). All memory games ran
with zero reasoning tokens (found 2026-10-04); both arms matched, so the comparison stands, but it is
about players that do not reason first.

**Code and data.** `scripts/run_batch.py`, `scripts/make_ab_seed_set.py`,
`evidence/memory_system/effectiveness/paired_ab/analyze_ab.py`, `evaluation/src/core/stats.py`;
[paired_ab](../../../memory_system/effectiveness/paired_ab/report.md),
[store_progression](../../../memory_system/report.md) (correction of 2026-10-22).

## Case 2. Decided in advance: the v7 endpoint test

**What and why.** The v7 learning loop was meant to make memory better with each round of games. The
final test asked one question: does the finished memory (168 lessons, built over four rounds) beat
no memory?

A memory test can be scored many ways: town wins, wolf wins, each role's decisions, per game or per
decision. With that many measures, one will usually look "significant" by luck alone. Check them all
afterwards and report the best one, and you fool yourself without meaning to. So for this test, the
rules were written down before any game was played (a *pre-registration*).

**How it works.**
- **The measure was chosen in advance:** the town's decision score on each deal, computed from the game
  record with no model involved. Other measures were labelled as secondary.
- **The number of games was fixed in advance,** so the test could not be stopped early when the numbers
  looked good.
- **The reporting was promised in advance:** a null or negative result would be reported as "no
  compounding detected".
- **The plan changed once, in writing, before any game was played** (three arms on 20 deals became two
  arms on 30). Changing the plan before data is allowed; changing it after seeing data is not.
- **The run checked itself.** Each deal's two games ran together, a deal counted only when both
  finished, a game whose decisions fell back to defaults was thrown out, and at the end the run
  confirmed it had used the same code and model setup as the loop.

**Result.** With memory, the town's decision score was 0.147 lower (p≈0.06), and lower on 19 of 30
deals. As promised, it was reported as "no compounding detected", leaning toward harm. Because the rules
were fixed first, the negative result is believable: nobody can say the measure was picked to make it
fail. The cause was traced to the scoring rules that drove the loop, which graded every town abstain
as neutral and so could not remove lessons that made the town abstain
([credit blind-spot log](../../../credit/blindspot_fix/experiment_log.md)).

**How far to trust it.** 🟡. The strongest design on this page, with three gaps. The script that
computed the final number was not found, so the result is recorded in the reports but cannot be
re-run from committed code. The per-game data sits in a folder git ignores. And whether 30 deals were
enough to detect a real effect was not checked for the final design.

**Code and data.** `evaluation/src/loop/measure.py`; the pre-registration, amendment, config and run
log in [execution_plan/data](../../../memory_system/v7/execution_plan/data/README.md);
[the v7 report](../../../memory_system/v7/report.md), "The pre-registration" and "What the signed run found".

## Case 3. Small whole-game runs: smoke tests with a direction (persona voices, evil covers)

**What and why.** In October, two changes to the live game needed a quick look at whole games: would
character voices make players read each other worse, and would the evil-seat changes make evil players
fake-claim and win more? Neither needed a full 30-deal test; a direction was enough to decide.

**How it works.**
- **8 deals each, on Claude Haiku 5.5, memory off.** Each game saves its prompts, reads, final state,
  and a manifest with the commit, run config, cost and winner.
- **One change, or a bundle.** The voices test differs by one config flag on one commit. The evil-cover
  test compares two versions of the code (the old one run from a git worktree), because card text is
  not a flag, and it bundles three changes.
- **Scored by code, no model.** Reads are scored against the true roles (Brier score: the squared gap
  between stated confidence and whether the read was right). Evil claims come from each line's own
  structured claim field, not from a judge.

**Result.** With voices, reads were better on 7 of 8 deals (Brier 0.129 against 0.155, sign test
p≈0.07), but the voiced games had 19% more talk, which by itself gives readers more to read. After the
evil-seat changes, evil seats claimed a role 11 of 24 times against 3 of 24, and the wolves won 3 of 8
games against none. The leak check flagged 5 voice games; every flag was a sentence the receiving seat
also held in its own record, so the check was narrowed and all 16 games passed.

**Looking back.** The voices question, whether players still read each other well, was a question
about reading, and the replay screens of the same day (a voiced line, a voice rewrite) answered it
more cleanly: they hold the transcript fixed, which the games could not, since the voiced games had
19% more talk. A per-day replay would have covered the part a turn replay misses (more talk across a
day). What the voice games did add was the end-to-end run of a new live feature: no crashes, the real
cost, and a false alarm in the leak check found and fixed. The evil-cover games had a better reason to
exist: balance (who wins) only exists across whole games, though 8 deals cannot settle it.

**How far to trust it.** ⚠️ smoke test only. Eight deals give a direction, not an estimate, and no
measure was fixed before either run. The evil-cover arms bundle three changes, so they cannot say which
one did the work (a replay screen isolated the card text), and 12 of its 16 runs came from uncommitted
code.

**Code and data.** `evaluation/experiments/persona_voice_games.py`, `persona_voice_games_score.py`,
`evil_cover_screen.py`;
[persona_voice_games](../../../gameplay/data/persona_voice_games/README.md),
[evil_cover_games](../../../gameplay/data/evil_cover_games/README.md).

---

## What would make it stronger

The memory tests are closed: the memory research ended on 2026-07-21, and the ten-seat memory (v8) has
not been tested at scale. For future same-deal tests the upgrades are procedural:

- **Fix the measure before the run**, as the June called shots and the v7 pre-registration did.
- **Run both arms from one committed tree behind a config flag** where the change allows it.
- **Commit the script that computes a reported statistic**, which the v7 endpoint lacks.
- **Build the per-day replay** before the next question about effects within a day; it would sit
  between the turn replay and whole games.
- **Buy more deals, not more pairing.** Pairing adds little power here. On the nine-seat game no measure
  taken before a game predicted its result, so variance-reduction tricks such as CUPED did not apply; on the
  ten-seat game the dealt lineup is known before play and can be stratified or adjusted for
  ([the levers audit](../../experimental_controls/variance_reduction_levers.md), corrected 2026-10-23).

**Bottom line.** The harness is sound, and it found and stated its own limits: wins need far more games
than were played, and pairing by deal buys almost no noise reduction. Every memory verdict therefore
rests on decision scores. The October ten-seat runs give a direction only, and looking back, part of
what they asked was better answered by a replay.

*Written 2026-10-23 and checked against the records named above. Which commit and tree each run used
is in the full evaluation ledger ([experiment log](../../experiment_log.md), Part 2); which files are not in git, in
[the source map](../../source_map.md).*
