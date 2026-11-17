# Log: the Vigilante test that passes or fails without a code change

The investigation of why `test_a_human_vigilantes_shot_is_spent_once_across_the_pause_and_resume`
(in `tests/engine/test_ten_seat_game.py`) fails on some runs and passes on others, and its repair.
Entries are in date order. Later entries replace earlier ones where they disagree; earlier entries
are not rewritten. All of this work is exploratory (debugging), not a planned comparison.

The earlier diagnosis this log starts from is in `../improvements.md` (row 15 and the section
"Records for the write-up") and `../u13_seed_notes.md`; its replays are in
`../measurements/u2_diag_vig.py` and `../measurements/u2_diag_runs.txt`.

## 2026-11-17: the question, and what is taken from the earlier diagnosis

**The question.** Why does the test fail on some runs and pass on others with no code change, and
how can it be repaired so that it passes on every run and still fails if the rule it protects is
broken?

**What the test does.** It plays one whole ten-seat game on the real game graph, with every model
call answered by a scripted stand-in that picks a random legal answer. Seat `player_9` is a human
Vigilante. A Vigilante is a village role with two bullets; at night it may shoot a player or hold
fire, and `uses_left["vigilante"]` in the game state counts the bullets left. Each time the game
pauses for the human (a LangGraph interrupt), the test answers: at the Vigilante's night turn it
shoots the first listed player if no shot has gone ahead yet, and holds fire otherwise. After the
game it asserts that one shot went ahead (counted from the night records) and that one bullet is
left. The rule being protected: the night's turns run again when the game resumes after the pause,
and that re-run must not spend the bullet a second time.

**What the earlier diagnosis (2026-11-12) says, to be checked here, not assumed.**

1. The scripted players share one random generator, and the day and night turns run on several
   threads at once, so which thread draws which number depends on thread order. The game played
   therefore differs from run to run.
2. The test counts shots from the night records, and the engine does not keep a record for a seat
   that dies the same night. When the Vigilante shoots on night 1 and is killed that night, the
   count is 0 although the bullet was spent, and the assertion fails.
3. In every replay examined, the bullet was spent once.

The replays behind this were run on 2026-11-12, with and without a thread-pool setting that has
since changed (the per-phase pool is now one thread per seat). They gave 2 failures in 10 runs with
the setting and 4 in 10 without. Today's report of "roughly a third" is a separate, unrecorded
count.

**Plan for the work.** First reproduce the failure on today's code and count it, with the exact
command recorded. Then check each of the three points above directly on today's code. Only then
choose a repair. The repair must leave a test that still fails when the bullet is spent twice;
that is shown by breaking the rule on purpose in a scratch copy of the engine code and running the
repaired test against it. Engine code under `Agents/` is changed only for that demonstration and
restored afterwards; a real engine defect, if one is found, is reported, not fixed here.

Commit `a543c724`; `Agents/`, `tests/` and `server/` had no uncommitted changes when this started.

## 2026-11-17: the failure reproduced on today's code, less often than reported

**What was run.** The unchanged test, 30 times, each run in a fresh Python process (so nothing
carries over between runs), four processes at a time on a 4-CPU machine:

```
seq 1 30 | xargs -P 4 -I{} bash -c 'poetry run pytest -q -p no:cacheprovider \
  "tests/engine/test_ten_seat_game.py::test_a_human_vigilantes_shot_is_spent_once_across_the_pause_and_resume" \
  >/dev/null 2>&1 && echo pass || echo fail' | sort | uniq -c
```

**Result.** 1 of 30 runs failed; 29 passed. Total time 3 min 47 s.

**Interpretation.** The failure is reproduced: the same code and the same seed (5) give different
results in different runs. The rate in this sample (1 in 30) is lower than the 2 in 10 measured on
2026-11-12 and the "roughly a third" reported today. Those counts were made with a different
thread-pool size and, for today's report, under conditions that were not recorded, and the rate
probably depends on how busy the machine is, since that changes thread timing. With 1 failure in
30, this sample says nothing reliable about the rate; it shows only that the failure still occurs.
The pass/fail count alone cannot show the cause, so the next step looks inside each run.

## 2026-11-17: the three points of the earlier diagnosis, checked on today's code

**Approach, and the alternative it had to rule out.** The earlier diagnosis blamed thread order.
A second explanation fits the same symptom: Python randomises the hashing of strings per process
(unless `PYTHONHASHSEED` is set), so any code that iterates over a set of player names can change
order between processes. To separate the two, a probe
(`../measurements/u13_vig_probe.py`) replays the test's exact game and answers, and prints, for
each run: what the test's assertions would give, the shots counted from the state's night records
(the test's count), the shots counted from the night metric, the bullets left, whether the
Vigilante died on a night it fired, and a short hash of every night's choices. Two runs with the
same hash played the same game. The night metric is the record that the night resolution writes
into the run's `Metrics` object for every actor, including one that died that night; the test
`test_the_night_metric_keeps_what_the_night_decided_and_every_actors_record` pins that it keeps
those. The probe was run in four settings, each run in a fresh process, four at a time:

```
PYTHONHASHSEED unset or 0;  threads=default (today's pools) or threads=serial (every pool one worker)
poetry run python evidence/_study/engineering_notes/measurements/u13_vig_probe.py threads=default|serial
```

**Results** (all 70 lines are in `../measurements/u13_vig_probe_runs.txt`):

| Setting | Runs | Distinct games | Test would fail | Bullets left = 1 | Shots in the metric = 1 |
|---|---|---|---|---|---|
| Today's pools, hash seed random | 20 | 20 | 1 | 20 | 20 |
| Today's pools, hash seed fixed at 0 | 20 | 20 | 1 | 20 | 20 |
| One worker per pool, hash seed random | 20 | 1 | 0 | 20 | 20 |
| One worker per pool, hash seed fixed at 0 | 10 | 1 | 0 | 10 | 10 |

In both failing runs the state's count was 0, the metric's count was 1, one bullet was left, and
the Vigilante died on the night it fired.

**What this establishes.**

1. *Thread order is the source of the variation (verified).* With the hash seed fixed, every one
   of 20 runs still played a different game; with one worker per pool, all 30 runs played the same
   game whatever the hash seed. The string-hashing explanation is ruled out for this test. The
   scripted model draws from one `random.Random(5)` shared by all seats, and the seats' turns run
   on parallel threads, so the order of the draws follows the thread schedule.
2. *The test fails when the Vigilante dies on the night it fires (verified in both failures).*
   The night resolution gives no record of that night to a seat that died in it
   (`tonight_records` in `Agents/nodes/night/resolution.py`). That is the intended rule ("a player
   who died tonight gets no record of tonight", pinned by
   `test_a_dead_player_gets_no_record_of_its_last_night`), not an engine defect. The test counts
   shots from those records, so it counts 0 while the metric shows the shot went ahead.
3. *The bullet was spent once in every run (verified in all 70).* So no engine defect was found:
   the failures are the test's, not the rule's.

**A further way the test can fail, from reading the code (possible, not observed).** If the
Chanteuse blocks the Vigilante on a night and the Vigilante is also killed that night, no shot
ever goes ahead and one bullet is not spent, so `uses_left` stays at 2 and the test fails for a
correct engine. None of the 70 runs did this.

## 2026-11-17: the repair chosen, and why

**Decision.** Fix the situation the test sets up: the scripted players never choose the Vigilante
as the target of anything (a kill, a block, a sigil, a vote). The Vigilante then cannot die or be
blocked, so its night-1 shot always goes ahead and its record is always kept, and the test's two
assertions (one shot went ahead, one bullet left) hold in every game a correct engine plays. The
games still differ from run to run by thread order; the test no longer depends on which one is
played.

**Alternatives considered.**

- *Count the shot from the night metric instead of the state's records, and assert that the
  bullets left equal two minus the shots.* This removes the first cause, but not the
  block-and-kill case above, and in a game where no shot goes ahead the test would pass while
  checking nothing about a double spend. To be sure of a shot, the situation has to be fixed
  anyway. Rejected.
- *Make the scripted model independent of thread order* (for example, a generator per seat).
  This makes each seed play one game, so the test would pass or fail on every run for seed 5
  without removing the cause; and the same scripted model serves the whole-game tests in the
  file, whose games would change. Rejected for this repair; still worth considering for the file
  as a whole.
- *Run the pools with one worker.* The test exists to check the pause and resume of the night's
  parallel turns, so serialising them changes what it tests. Rejected.

**What is changed.** Only `tests/engine/test_ten_seat_game.py`: the scripted model takes an
optional set of seats to spare (default empty, so the other tests are unchanged), and the
Vigilante test finds the human seat from the deal before the game starts (the deal is fixed by the
game id) and spares it. Stage: implemented, not yet tested.

## 2026-11-17: the repaired test still fails when the bullet is spent twice

**Question.** Sparing the Vigilante must not have made the test unable to fail. Does the repaired
test fail when the rule it protects is broken?

**Approach.** The plan in the first entry was to break the rule in a scratch copy of the engine.
Patching the engine functions inside the test process with pytest's `monkeypatch` does the same
without editing any file under `Agents/`, so that was used instead
(`../measurements/u13_vig_mutations.py`). Two breaks:

- *spent twice*: the night resolution's spending function (`_spent` in
  `Agents/nodes/night/resolution.py`) is applied twice to the shot.
- *spent per run of the turn*: the Vigilante's night turn counts each time it starts, and the
  resolution spends that many bullets for its shot. A human's turn starts once before the pause and
  again on resume, so this is the double spend the test is meant to catch: work done before the
  pause and repeated after it. In one all-AI game (no pause) run under this break, the Vigilante
  fired once and had one bullet left, as with the unbroken engine, so the break shows only across
  a pause.

Each case asserts that the repaired test raises an `AssertionError` on the line
`assert final["uses_left"]["vigilante"] == 1`, so a failure elsewhere does not count. A control case
runs the repaired test on the unbroken engine. Each case runs in its own process, because a second
game under the test's fixed game id in one process resumes from the first game's checkpoint.

```
F=evidence/_study/engineering_notes/measurements/u13_vig_mutations.py
for k in control spent_twice spent_per_run; do poetry run pytest -q -p no:cacheprovider $F -k $k; done
```

**Result.** All three cases passed: the repaired test passed on the unbroken engine and failed on
the bullet count under both breaks (0 bullets left where 1 is expected), each run once.

**Interpretation.** The repaired test can still fail when the bullet is spent twice, including the
case where the second spend comes from re-running the turn after the pause. Because the Vigilante's
shot now always goes ahead, this holds in every game the scripted players can produce, not only in
the game of one run; the breaks were each run once, though, so that wider statement rests on the
argument, not on repeated runs.

## 2026-11-17: the repaired test across repeated runs

**What was run.** The repaired test 100 times, each in a fresh process, four at a time, with the
same command as the baseline entry (`seq 1 100` in place of `seq 1 30`); then the probe 40 times in
the repaired setting (`u13_vig_probe.py threads=default spare`, hash seed random).

**Result.** 100 of 100 test runs passed (7 min 44 s). In the 40 probe runs, all 40 played different
games, the Vigilante was never named as a target, it never died on the night it fired, one shot
went ahead and one bullet was left in every run (the 40 lines are appended to
`../measurements/u13_vig_probe_runs.txt`, marked `spare`). A separate run of each break printed
the bullets left: 0 under both, which confirms the figure given in the previous entry, written
before it was printed.

**Interpretation.** Before the repair the test failed in 1 of 30 test runs and 2 of 40 probe runs
today. At a rate of that order, 100 passes in a row would be unlikely if the cause were still
there, but the run count alone is not the main evidence. The main evidence is that the probe shows
why each run passes: the games still vary by thread order as before, and the event that caused
every observed failure (the Vigilante dying on the night it fired) cannot happen, because no
scripted player chooses it. The whole `tests/engine` folder was run once after the change as well
(`poetry run pytest -q -p no:cacheprovider tests/engine`): 1436 passed.

**Status.** The test change is implemented and tested; it is not committed. No engine code was
changed, and no engine defect was found.

**Left open.** The other tests in the file share the same scripted model, so their games also
vary by thread order. They passed here, but whether any of them can fail by chance was not
examined. A scripted model that does not depend on thread order (for example, a random generator
per seat) would make every game in the file repeatable; that is a separate change.

## 2026-11-17, later: one correction, the scope of the repaired test, and the commit

**Correction to the entry "the three points of the earlier diagnosis".** That entry says "Two runs
with the same hash played the same game." The hash covers the choices made on every night
(`night_resolutions[*].choices` in the replay script) and nothing from the day. So what the table
establishes is narrower than its column "Distinct games" says: 40 runs with today's thread pools
made 40 different sets of night choices, and 30 runs with one worker per pool made one set. Runs
with different night choices did play different games. Runs with the same night choices were not
shown to have had the same day discussion and votes. The conclusion drawn from the table does not
depend on that: with one worker per pool the order of the random draws is fixed, and the night
choices stopped varying, which is what identifies thread order as the cause. An outside reviewer
pointed this out after reading the log.

**The scope the repair gives up.** Because no scripted player may target the Vigilante, this test
no longer plays games in which the Vigilante is killed, or is stopped from acting by another role,
on a night it fires. That is deliberate: the test's question is whether one successful shot costs
one bullet across a pause and resume, and it now always gets a successful shot. It is a limit on
what the test covers, not only a rejected alternative. Whether another test checks the bullet
count when the Vigilante is killed or blocked on the night it fires was not checked; a search of
the test names in `tests/engine` found none that says so.

**Committed.** The test change is commit `33e67bd4`, and this log with its scripts is commit
`4f93ecd8`. The status "not committed" in the previous entry was correct when it was written.
Stage: implemented, tested and committed; not pushed.

## 2026-11-17, later still: three more corrections, from a second reader

A writer who was given only this log, to write a report from it, listed statements the log does
not support. Three are corrected here.

1. **"All 40 played different games"** (entry "the repaired test across repeated runs"). This is
   the same error as the one corrected above. The 40 replays of the repaired test made 40 different
   sets of night choices; the day was not compared.
2. **"100 passes in a row would be unlikely if the cause were still there"** was stated without a
   calculation. The calculation: if the failure rate before the repair is taken as 3 in 70 (the 1
   failure in 30 test runs and the 2 in 40 replays), the chance of 100 passes in a row with the
   cause still present is 0.957 to the power 100, about 1.2%. If it is taken as 1 in 30, it is
   about 3.4%. Both rates come from very few failures, so these figures are rough. The entry
   already says that the count is not the main evidence, and that remains the case.
3. **The tree the repaired runs used** was not stated. The 100 runs and the 40 replays used commit
   `a543c724` plus the uncommitted change to `tests/engine/test_ten_seat_game.py`, which was later
   committed unchanged as `33e67bd4`.

One assumption is also made explicit. The statement that the repaired test's assertions hold "in
every game a correct engine plays" assumes that a seat which no scripted player ever targets cannot
die, be blocked or lose its shot in some other way. The 40 replays agree with that; the engine's
rules were not searched for an exception.

## 2026-11-17, evening: why the Vigilante is also spared from votes

A reader of this log asked why the repair spares the Vigilante from votes, when every observed
failure was a death at night. The log had not said. What reading the test and the rules shows:

- The repair works by filtering every choice a scripted player makes from a fixed list of seats
  (`_fill` in the test file removes spared seats from any such list). Votes are choices of that
  kind, so they are spared along with kills and blocks. This follows from how the filter was
  written. It was not a separate decision with its own reason.
- The game's rules text says day 1 has no vote, so no vote can remove the Vigilante before its
  first night turn, which is when the test fires the shot. I read this in the rules text given to
  the players (`Agents/prompts/game_rules.py`); I did not trace it through the graph code.

So sparing the Vigilante from votes is probably not needed for the test's two assertions, and it
narrows the test a little more than the cause required: the test also no longer plays a game in
which the Vigilante is voted out on a later day. Whether the assertions would still hold in such a
game (the count of shots read from the night records of a seat that was later voted out) was not
checked. Stage: a question recorded, nothing changed.
