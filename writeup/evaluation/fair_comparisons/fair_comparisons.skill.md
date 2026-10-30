# Designing fair comparisons

*Level 2 · [Evaluation](../evaluation.md) · Level 3: [What the paired baseline reanalysis changed](paired_baseline.md) · status: trial draft written with the write-portfolio-page skill on 2026-10-28; revised after the editorial and claims reviews, and on 2026-10-29 for the parent-context ruling and length; for the owner's review.*

<!-- Brief (frame, evidence selection, approved outline, open questions):
_authoring/fair_comparisons.skill.brief.md. Drafted 2026-10-28 from the sources listed at the end;
not independently verified. -->

## Page copy (draft)

Behind the controls in the chapter summary is a two-part test. A difference between two versions is
evidence for the change only when the two sides differ in nothing else, and the gap is larger than what
repeating one version would produce. Each part needs its own remedy. A difference between the sides
creates a false effect, so I matched what both sides start from and how they are scored, and, in the
memory experiments' multi-round runs, had code check that the run used the set-up it declared.
Randomness within each side can imitate or hide an effect, so I measured how far results move with
nothing changed, and, for one planned test, checked by simulation whether it was large enough before
paying for it. Both conditions bite here, because the comparisons are small, about 30 games a side or
a few dozen recorded turns, and the agents sample at temperature 1.0. Most of the evidence below comes
from the original nine-player game; the later ten-player game deals ten seats from twelve roles, so
its lineup varies from deal to deal.

### Giving both sides the same start and the same judge

A game's id determines its deal, the assignment of roles to seats, so running both versions on the
same list of ids gives them the same starting positions; a test checks that an id reproduces its
deal. The same deal is not the same game. At temperature 1.0 two games part ways at the first line
that differs, so a pair of games on one deal is two independent plays of the same start. Matching rules
out one side being dealt easier games, and nothing more.

One evaluator for both sides means one judge with one rubric, scoring both sides in one run after both
have finished. Scoring them in separate runs lets a change in measurement pass for a change in play.
When the rubric of the judge that labels discussion messages was revised to split one label into two,
the older games were re-read with it alongside the new ones, and on those same older messages the share
labelled as citing something a player had said moved from 74% to 63%. Where code can score the outcome, such as a vote
checked against the true roles, no judge is used.

### Checking that the run is the one declared

Matching assumes that each run actually used the set-up it was meant to. That takes three separate
jobs: recording the set-up, enforcing a rule about it, and checking that a setting does what its name
says. Code does the first two; the third is still mostly done by hand.

**Recording.** Every experiment game record carries a runtime fingerprint: the code version, a hash of
the main prompt files, and the model settings the game ran with. It states facts; it does not act on
them.

The memory experiments test whether players do better when they can look up lessons drawn from earlier
games. Their multi-round runs are learning loops: rounds of games with memory on and off on the same
deals, with the store of lessons updated after each round.

**Enforcing.** Two code checks guard those loop runs. The first stops the run if the fingerprint
changes between games. The second exists because one June loop run, meant to give memory to the town's
roles only, gave it to every role, wolves included, and its conclusion about town memory came out
plausible but wrong, without any error. Now a loop run must declare which
roles have memory, or explicitly waive the check, before any game starts; after each round it reads
back which roles actually had it, and stops on a mismatch. Outside the learning loop neither check
runs, and across separate runs a person compares the fingerprints.

| What the July learning-loop run recorded | Value | What happens to it |
|---|---|---|
| Code commit; uncommitted changes | `a010dc68…`; none | Recorded on every game. A change between games stops the run; across runs a person compares |
| Hash of the main prompt files | `fcb194406952618f` | As above |
| Player model | `gemini-3.1-flash-lite` | As above. The provider reported only this name, so a change behind it could not be recorded |
| Player thinking level | `minimal` | Recorded correctly on every game; a later probe showed this level gives this model no reasoning tokens (see below) |
| Roles declared to have lesson memory | town roles only | Declared before the first game |
| Roles whose lesson memory was on, read back each round | healer, investigator, vigilante, villager, in all four rounds | A mismatch would have stopped the run |

*Selected fields from the nine-player run that built the store of lessons for the final memory test
(the finished store against no memory, described below); four rounds of ten games a side, July 2026.
The first four rows are the fingerprint, which records; the last two are the memory check, which
enforces. The check covers the per-role lessons only. A short list of public behaviours that hint at a
hidden role was, by design, part of the memory side for every seat, wolves included, and the check
does not cover it.*

**Checking the effect.** Neither the record nor the checks can show whether a setting did anything.
In October a probe found that the "minimal" thinking level made that model produce no reasoning tokens
at all; it produced them only from "low" up. Every memory-experiment game until then had run at
"minimal", and the fingerprint had recorded it correctly each time. Both sides of every comparison ran
at the same level, so the comparisons stayed fair; what narrowed was their scope, to players that
produced no reasoning tokens before answering. Game records still store only the configured level.

### A baseline that shifted with nothing changed

Matching and checks hold fixed what the project controls. The hosted model service is not one of
those things.

In June, a memory experiment in the original nine-player game needed a memory-off baseline. An earlier
baseline of 30 games existed, in which the town had won 20. The new baseline was to reuse the 20 of
those games whose winners were on record, without replaying them, and add 10 newly played deals that
were not among the earlier 30. The 10 new deals gave the town 1 win, on byte-for-byte identical play
prompts and unchanged game code.
Read as two independent groups, 1 win in 10 against 20 in 30 looked decisive. The record's leading
suspect was a change in the hosted model. Its name had no dated version to pin, and each response
reported only the name, so a change behind it could not have appeared in any record. Chance at this
sample size was recorded as the alternative.

Either way, the old results could no longer serve as the control. The 20 earlier deals were played
again, so that all 30 baseline games came from the same period as the memory games, and the rule
followed: both sides of a comparison run in the same time window, and new results are never compared
with historical runs. Code enforces the rule only in some runners. The learning loop runs each
round's games for both sides as one block, in a shared pool and paired by deal, so both sides fall
within the same stretch of hours; the final memory test went further and started each deal's two games
together. A turn replay runs its versions in one session. The general batch tool does not alternate
configurations game by game, so a whole-game comparison outside the loop has to be interleaved by hand.

Replaying the 20 deals also gave a second comparison, which a later reanalysis tested deal by deal. The
two comparisons use different games:

| Comparison | Town wins | How often chance alone gives a gap this large |
|---|---|---|
| The 10 new deals, against all 30 earlier games | 1 of 10; 20 of 30 | About 3 in 1,000 |
| The 20 reused deals, earlier result against replayed result | 12 of 20; 7 of 20 | About 18 in 100 |

*The original nine-player game, memory off. The earlier 12 wins are part of the earlier 30 games' 20.
Of the 20 reused deals, 7 turned from a town win to a loss and 2 the other way; the other 11 kept their
result.*

The 10 new deals show the steepest drop and remain the strongest sign that something changed. But they
are only 10 games, on deals the earlier games never played, so they cannot say how large the change
was. On the 20 deals compared like for like, the town still won less often, yet a split as uneven as
7 to 2 occurs about 18% of the time by chance alone. How much pairing helps for wins was not measured;
the reanalysis's value is that it used the comparison the design actually contained, instead of
treating repeated deals as unrelated games.

The outcomes moved; how much, and why, were not established. Drift in the hosted model remains a
suspicion, and on the like-for-like deals chance remains possible. The reanalysis changed the claim, from a change in the model
service to a baseline that shifted for an unknown reason. It did not change the rule, which rests on
the records being unable to tell those two explanations apart.

**Link:** Explore why the two readings differ, deal by deal → [What the paired baseline reanalysis
changed](paired_baseline.md).

### Reading a difference against noise

The June reanalysis left chance open, and running both sides together does nothing for randomness
within each side. The tool here is a noise floor: how far a result moves when nothing has changed,
measured at the level the comparison works at.

- **The judge.** On the factual-error test set, recorded turns in which agents had stated false facts,
  re-judging the same 267 saved responses moved the count marked wrong by 1 or 2, so smaller
  differences there mean nothing.
- **One recorded turn.** The identical vote prompt, on the same model, chose the same player in 8 of
  10 samples in one experiment and 1 of 10 when rerun in a later one: ten samples of one turn measure
  the spread of answers to one prompt, not ten situations. Two habits answer this, so far used in only some replay experiments: running the
  unchanged version twice, and shuffling all versions into one schedule.

Pairing whole games by deal turned out to buy little precision for town votes. In two back-to-back
memory-off runs of the nine-player game that shared 8 deals, the share of town votes cast against a
wolf or the serial killer varied about as much between games on the same deal as between games on
different deals: a standard deviation of 0.25 within a deal, against 0.21–0.26 across deals. Nearly
all the variation came from how a game played out. Matching deals remains the default, because
it costs nothing and rules out one side getting easier deals, but in June it was the shared time window
that made the comparison fair. Pairing has not been re-measured on the ten-player game.

Noise also limits what whole games can show. With 30 games a side, only large gaps would be detected
four times in five: about 36 points of town win rate, or 0.18 in that share of town votes. A gap of
0.10 in the vote share would need about 100 games a side. A decision-level measure such as the vote
share varies less from game to game than a win does (a standard deviation of about 0.25, against 0.5),
so the comparisons lean on decision scores, though small effects stay out of reach at these sizes. The
main one, the town's decision score, grades every decision a town player makes after day 1 against the roles
revealed at the end, +1 if it helped the town, 0 if neutral and −1 if it hurt, and averages them per
game, so it runs from −1 to +1.

### Deciding the test before the games

Knowing the noise makes it possible to ask, before paying for games, whether a planned test can see the
effect it is looking for. The learning loop's first planned test asked whether the town's decision
scores rose across rounds. A simulation built from real memory-off games, with no model calls, showed
that at the size of an earlier paid loop run in June (four games in each of six rounds) it would
notice a rise of 0.15 across the run, the size the plan expected, only about 1 time in 9. That trend
test was dropped, and the next paid run used a different design.

The replacement, the final memory test, let the loop learn for four rounds and then played the finished
store against no memory on the same 30 deals, in the nine-player game. Its reading was fixed
in writing before the run began. Among many possible measures, from each side's wins to each role's
decisions, one usually looks significant by luck if it is chosen afterwards, so one main measure was
named in advance: the town's decision score, compared deal by deal, with the others labelled
secondary. The number of games was fixed, so the test could not be stopped early when the numbers
looked good, and the wording for a null or negative result was set in advance.

The plan changed once, in writing, after the games that built the store but before any game of the
test itself. The signed plan had three versions on 20 deals each: the finished store, the store after
the first round, and no memory. It became two versions on 30 deals, the finished store against no
memory, because the first-round store held no lessons yet and the freed games made the comparison more
precise. Every comparison against the first-round store went with it; the main measure and the reading
of a null stayed as signed. The simulation was not repeated for this paired design, so whether 30 deals
could detect a realistic effect is not known. The test's result belongs to the memory chapter, in
[Testing whether memory helps](../../memory/testing_memory/testing_memory.md).

### What the controls establish, and what still depends on a person

The controls are strongest where code enforces them. An id reproduces its deal, a replay rebuilds its
turn from saved state, and in learning-loop runs a fingerprint change stops the run and the roles with
lesson memory are declared before the run and read back during it. They are weaker where a person has to
remember a step: interleaving a whole-game comparison outside the loop, comparing fingerprints across
runs, and checking that a setting did what it names. The cause of the June shift remains unknown; the
rule it produced stands because drift and chance could not be told apart.

The next steps follow from those gaps: alternate the versions game by game in every batch tool, not
only in the loop; record reasoning tokens for each game beside the configured level; simulate each test
design before a paid run; and, in the ten-player game, where lineups differ between deals, account for
the dealt lineup, which is known before play and so can reduce noise without biasing the comparison.

**Evidence.**

- [A/B testing: the controls that keep a comparison fair](../../../evidence/evaluation/experimental_controls/report.md):
  "Why controls", "When does a comparison need a fresh baseline?", §1–§4, "What we would do differently
  next time".
- [The paired memory experiment's log](../../../evidence/memory_system/effectiveness/paired_ab/experiment_log.md):
  the baseline shift, "Can we pin or detect the drift?" and "Seed set".
- [Deterministic evaluation](../../../evidence/evaluation/deterministic_audits/report.md), case 5 (the
  guards).
- [Whole-game evaluation](../../../evidence/evaluation/evaluation_scopes/game/report.md): "How a
  whole-game comparison is set up" and case 2.
- [Testing the test before paying for it](../../../evidence/memory_system/v7/report.md) (the simulation).
- [The July run's files](../../../evidence/memory_system/v7/execution_plan/data/README.md) (the record
  in the exhibit).

<!-- Supporting notes moved out of the page copy in the revision pass of 2026-10-29 (owner ruling: a
Level 2 page does not re-introduce the game; length guard). Never deleted; restore with their sources
(listed in the sources comments below) if needed.
- Game introduction, removed from the opening (the reader arrives from the chapter page): "Here the
  system is a set of AI agents playing a Mafia-style hidden-role game. A town majority, which does not
  know who holds which role, plays against a hidden evil minority: wolves, who know one another, and a
  serial killer who plays alone. By day the players discuss and vote someone out; by night some roles
  act in secret. The original game had nine players; the expanded game deals ten seats from a cast of
  twelve roles."
- "Many things can also change without anyone editing the code: the hosted model behind a name, a
  setting configured differently from what was intended, or the judge that scores the outputs."
- Town composition in the June game: "In that game the town is ordinary villagers plus a healer, an
  investigator and a vigilante." (paired_ab log "Design").
- Frozen-turn replays (answers the replays page's question): "A frozen-turn replay holds more fixed: the
  turn is rebuilt from the game's saved state, so every version sees the same board, history and
  private results ([Choosing between turn replays and whole games](../replays_and_games/replays_and_games.md))."
- Pinning (answers "would pinning have prevented it?", not the page's question): "Pinning a model
  version, where a provider offers one, helps but does not replace the rule. It removes one source of
  drift, a different model served under the same name, but not changes around the model: Anthropic, for
  example, documents that a model ID's weights and configuration stay fixed while the serving
  infrastructure around them can change." Open question 9 (naming the provider) applies if restored.
- Backend at temperature 0: "The cloud service is also part of what must match. In this project, one
  judge model's accuracy on the same labelling task moved from 76.9% to 73.8% when it was served
  through a different cloud service, at temperature 0."
- Model rerun noise (the model-admission page's question): "Two runs of the same model on the same 70
  recorded turns differed by about 6 percentage points in their share of bad responses, so a quality
  check can find a large deficit but cannot rank close candidates ([Evaluating models before
  switching](../model_admission/model_admission.md))."
- Link to play metrics: "[Measuring play quality beyond win rate](../play_metrics/play_metrics.md)
  explains how such scores were chosen and checked."
- Exhibit row: "Temperature | `1.0` | As above" (temperature is stated in the opening).
- Simulation detail, marked for a possible Level 3 page ("Testing the test before paying for it", a
  "possible" candidate in the content plan): the planned test fitted a line through each round's scores;
  pretend runs resampled 15 real memory-off games and added a known rise; with nothing added it raised a
  false alarm 2–3% of the time, as a 5% test should.
- Endpoint run checks: "During the test, each deal's two games were started together, and a deal
  counted only when both had finished." (the first half is kept in "Keeping both sides in one time
  window").
- Moved in round 2 (2026-10-29): "One turn-replay runner now records reasoning tokens for each sample"
  (the factual-error test set's runner, 3e05e8a7); the closing's next step covers the gap for games.
-->

<!-- Round-2 review fixes (2026-10-29). Sources for the changed passages:
Opening scope: controls "Quick view" (the power gate covers the nine-seat trend test only; the paired
design was never simulated). Game versions clause: variance_reduction_levers.md correction 2026-10-23.
Judge order of events: discussion_evidence.md §6.1 lines 451–465 (both sides re-judged with the new
rubric; the 74% → 63% move seen in that re-judging).
June loop-run slip: invariants.py assert_arm_factions docstring ("a town-only conclusion was drawn from an
all-memory-on arms-race board").
Thinking row: blindspot_fix log §⑦ (the probe was on the test set; game records hold the level only).
Tells caption: v7 report "The pre-registration"; config.json "tells": true.
Baseline groups: paired_ab log "Seed set" (20 recovered ids with recorded winners: 12 villagers / 7 SK
/ 1 wolves; 10 fresh uuid4s, not among the original 30). Why only 20: the records say only that these
20 had recorded winners; the page says no more than that. "Only 10 games, on deals the earlier games
never played, so they cannot say how large the change was": paired_baseline.md ("The fresh games remain
the strongest evidence of a drop, but they are 10 games against a different set of deals"; "no reliable
estimate of the shift's size").
Pairing and wins: paired_baseline.md ("did not establish how much pairing improves precision for win
outcomes"). Pairing sample: drift_surfaces_and_guards.md "Variance constants" (two back-to-back all-off
runs, canary1 N=10 and canary2, 8 common seeds; measured 2026-06-12; the runs are not named on the page).
Vote share = town_vote_accuracy (votes on a wolf or the serial killer).
Detection criterion: drift_surfaces_and_guards.md line 136 (two-arm N=30, 80% power at p < 0.05: ~0.18
vote accuracy, ~36pp win rate; ~100 games/arm for 0.10). Per-game sd ~0.25 vote accuracy vs 0.5 binary
win: same section, line 135. "Small effects stay out of reach": the simulation in the next section.
AC2 rerun: gameplay/deduction/data/deduction_placement_n10/results.md ("the identical before_note prompt
was rerun in ../deduction_ac2_ablation/ (V0) and voted player_8 in 1 of 10, against 8 of 10 here";
player_8 was the original failure, so "the right player" in the controls report is wrong; the page says
"chose the same player").
Plan change: PREREG_AMENDMENT.md (signed: 20 boards × 3 conditions, final store / gen-1 store / memory-off;
amended to 30 × 2, final vs off; "Primary readout unchanged: final-store ON vs OFF") and v7/report.md
lines 195–203 (signed main comparison "between the final memory and the memory after the first
generation"; "It changes the question"). The two records disagree on whether the main comparison
changed; the page says "every comparison against the first-round store went with it", true on either
reading; flagged in the brief.
-->

<!-- Revised 2026-10-28 after the editorial and claims reviews (resolution table in the brief). Sources
for the changed passages:
Game context in the opening: role sheet / chapter context (town majority vs wolves and a lone serial
killer; nine-player original; ten seats from twelve roles: variance_reduction_levers.md correction).
Judge passage: discussion_evidence.md lines 461–465 (the baseline's "something a player said" share
74% → 63% after a rubric revision; same rubric, same run).
Recording/enforcing scope: fingerprinting report §1–§2 (experiment game records only; served games
unstamped; the prompt hash covers the main prompt modules, not nested packages such as the role cards).
Both code checks run only in the learning-loop driver (controls "Quick view"; driver.py run_loop).
Tells: v7/report.md "The pre-registration" (a short list of tells shown to every seat in the memory
games, wolves included); config.json "tells": true; driver.py sets WW_TELL_BOOK for the ON arm only.
The arm check reads the per-role memory_config only.
Thinking scope: credit/blindspot_fix/experiment_log.md §⑦ (the table covers the June static A/B, the v7
loop runs and the v7 endpoint: every memory-experiment game at minimal). Token recording: the
factual-error test set's runner (3e05e8a7), named on the page only as "one turn-replay runner".
June: "reused the recorded results of 20 of those games" — paired_ab log "Seed set" (20 recovered ids
with recorded baseline winners). Different games in the two comparisons; the 10 fresh deals remain the
strongest evidence; pairing did not add precision: paired_baseline.md "Why the readings differ".
Same window: driver.py _run_arms_parallel submits on_tasks + off_tasks to one ThreadPoolExecutor
(game_concurrency 3 in the July run), so within a round the ON games mostly start first; both sides
fall in the same round's block. Endpoint: v7_endpoint_ab.log "[start] off g0[start] on g0" (each deal's
two games started together).
Backend at temperature 0: dedup/report.md ("the backend alone moved one run from 76.9% to 73.8% at
temperature 0"; Google AI Studio → Vertex, flash-lite, dedup judge prompt v10; labeling/dedup.md).
Pinning statement: controls §1 (Anthropic, "Model IDs and versioning", checked 2026-10-25).
Noise: 267 = judged samples on the nine-seat factual-error test set (factual_errors/report.md step 4);
"so far used in only some replay screens": turn report "What we would do differently" row 1 (done in the
persona line and AC2 2×2; most screens ran each arm once); 70 turns, 10% vs 16% bad-sample rate:
model_admission/report.md (§1 and "How far to trust the quality checks").
Pairing spread: paired_ab log line 128 (town_vote_accuracy per-game sd 0.249 within seed vs 0.211–0.262
across). Detectable gaps: controls §3 (detection criterion not stated there; "show reliably" follows the
game report's "would reliably show"); 0.10 read as vote accuracy (open question in the brief).
Decision score definition: v7/report.md "The score".
Trend test: v7/report.md lines 92–156 ("The June runs had been read this way"; "the size of the previous
paid run", 4 games × 6 generations; +0.15 across the run; "dropped on 2026-07-05, before any paid run
used it" — the two statements disagree; the page says "the next paid run used a different design",
true on either reading; flagged in the brief).
Endpoint: signed 2026-07-16 before any game of the run (v7 report "The pre-registration"); amendment
2026-07-20 "after the learning games but before any test game", with its two recorded reasons (v7 report;
PREREG_AMENDMENT.md). The game report case 2's "before any game was played" is imprecise. Dropped from
the page: the exclusion of games whose decisions fell back to defaults (game report case 2), because the
signed plan names only halts and quarantined partials, so it is unclear whether it was fixed in advance.
-->

<!-- Sources for the page copy (drafted 2026-10-28):
Opening: experimental_controls/report.md "Why controls" (about 30 games a side or a few dozen frozen
turns; temperature 1.0; things that change without code). Two conditions and two remedies: same report,
"When does a comparison need a fresh baseline?" paragraph "Two kinds of variability".
Same deal from game id; test checks it; same deal not the same game: controls §1 "Same deal from the same
game id"; tests/engine/test_seedability.py. Pair = two independent plays of one start: game report "How a
whole-game comparison is set up" ("Not controlled: the model's sampling").
Rebuilt turn: controls §1 "The same turn, rebuilt".
One judge, one run; 74% → 63% after a rubric split; old games re-read: controls §2 "One judge for both
sides". Code where it can score: controls §2.
Record / enforce / check: fingerprint fields Agents/run_fingerprint.py runtime_fingerprint (git_commit,
git_dirty, prompt_bundle_hash, llm_backend, game_model, temperature, thinking levels, pro models,
embedding model + dims, vertex_location). Within-run stop: evaluation/src/loop/invariants.py
assert_fingerprint_consistent, called in driver.py; across runs a person compares: controls §1,
fingerprinting report §7 "Two runs compared by a person".
Arm guard incident: invariants.py assert_arm_factions docstring (ON arm ran all_enabled when town_only
intended; "a town-only conclusion was drawn from an all-memory-on arms-race board — a plausible WRONG
number, no error"); deterministic_audits case 5. Declare-or-waive: assert_arm_declared. Read-back each
generation: driver.py ("ARM GUARD") and controls §1. "Round" = the loop's "generation".
Exhibit: evidence/memory_system/v7/execution_plan/data/v7_compound_town5/ (the four-generation build
run, 2026-07-17 to 19, ten games per generation, off baseline on): run_meta.json runtime_fingerprint
(git_commit a010dc688cb6…, git_dirty false, prompt_bundle_hash fcb194406952618f, game_model
gemini-3.1-flash-lite, temperature 1.0, game_thinking_level minimal; other fields omitted);
config.json overview.expect_factions "town_only", loop_config.unchecked_arm false; loop_history.json
arm_factions = [healer, investigator, vigilante, villager] for generations 1–4. This is the run the
controls report calls "the one run since" the guard (it dates it 2026-07-19, the run's last day). Chosen
over the fingerprint report's capture stamp (phase3_games/game1), which records git_dirty true.
"Ten games a side": summary.json, 10 completed games per side in each of generations 1–4 (checked
2026-10-28).
Thinking level: controls §4 (2026-10-04 probe; "minimal" gave no reasoning, reasons from "low"; every
game until then at minimal; both sides same level; scope narrows; test-set runner records reasoning
tokens per sample since 3e05e8a7; game records carry only the configured level). Wording follows the
map: "produced no reasoning tokens", not "did not reason".
June case: controls "The case that set the rules"; paired_ab/experiment_log.md lines 5–22 (byte-identical
play prompts; no game-rule/scheduler code change since baseline commit b9756960; "most likely cause"
alias drift "or small-N variance"; re-run the 20 recovered ids so all 30 baselines are same-epoch) and
lines 61–67 (seed set: 20 recovered with recorded winners, 10 fresh). Town composition: paired_ab log
"Design". Not pinnable; served model_version echoes the alias: paired_ab log lines 24–38. Original 30:
town 20 (controls report).
Two-readings table: Fisher p = 0.0028 (independent; "about 3 in 1,000"); exact McNemar p = 0.18 on 9
changed deals, 7 W→L / 2 L→W, 12 → 7 (controls report; evaluation/experiments/june_baseline_shift_check.py,
re-run 2026-10-25 per paired_baseline.md's verification note: 5/7/2/6, p = 0.180). Test names kept off
Level 2 (owner default 2026-10-28); they are on the Level 3 page. "Changed the claim, not the rule":
controls revision note 2026-10-25; paired_baseline.md "What the reanalysis changed".
Same-window enforcement: controls §1 "Both sides in one time window" and the control table (loop driver
yes, run_batch.py no; replays in one session). driver.py _run_arms_parallel runs ON and OFF tasks in one
capped pool, pairing by game_id. Replay runs in one session: controls report, not re-checked against the
replay tool's code (brief, open question).
Fresh-baseline cases: controls "When does a comparison need a fresh baseline?" table (fixed bar → no;
same day → not necessarily, interleave and read against noise floor; replay baseline "costs cents, re-run
by default" → softened to "cheap enough to re-run alongside"; different days → yes).
Pinning: controls §1 "Pin the model where the provider allows it" (Anthropic: weights and configuration
of an ID fixed, serving infrastructure can change; flash-lite had no numbered version). Provider not
named on the page (owner voice rule). Backends differ at temperature 0: controls §1 "Never compare with
historical runs". Ten baseline games on fixed seeds before a cross-day reading; clean result proves
nothing: controls §1 "Manual steps" (cost left off).
Noise floors: 1–2 of 267 (scoring layer 3; controls §3); 8 of 10 vs 1 of 10 and the two habits (turn
report §2 item 1); ~6 points at 70 samples, gate not ranking (controls §3; model_admission report).
Pairing bought little: controls §3 "What pairing bought" (0.25 within, 0.21–0.26 across); game report
"What pairing turned out to buy" (0.249; nine-seat only; free, rules out easier deals; same window was
what mattered). Detectable sizes ~0.18 vote accuracy / 36 points win rate / ~100 games a side for 0.10:
controls §3. Vote accuracy = Agents/compute_metrics.py town_votes_on_threat / town_votes_total.
Simulation: controls §3 "The power gate"; v7 report "Testing the test before paying for it" (trend test
= slope through generation averages; 15 memory-off scores resampled; +0.15 planted, the planning
assumption from the largest earlier effect ~+0.2; 24 games over six generations ≈ 1 in 9 (11%); false
alarm 2–3%; no model calls). Score range −1 to +1: execution_plan report per the baseline packet. "Not run
for the paired design that replaced it": controls quick view and "next time" row 3.
Endpoint method: game report case 2 "What and why" and "How it works" (measure, secondary measures,
fixed number of games, reporting promised: "no compounding detected", the amendment three arms on 20
deals → two arms on 30 before any game, the run's self-checks). Result left to Memory (content plan;
the memory page says the method lives here). "Whether 30 deals were enough was not checked": game report
case 2 "How far to trust it". Off the page per Handle with care: the missing final-number script and the
git-ignored per-game data.
Closing: controls "Bottom line" and "What we would do differently next time" rows 1–4; ten-seat lineup as
a pre-treatment covariate: variance_reduction_levers.md correction 2026-10-23.
Supporting notes (moved out of the page copy at drafting, 2026-10-28, for length; restore if the
editorial review finds section 4 thin):
- When a fresh baseline is needed: "Not every check needs a fresh baseline. A check against a bar fixed
  in advance, such as a recorded failure that must not return, has no second side to drift. Two versions
  run on the same day, with nothing else changed, depend more on interleaving and a measured noise floor
  than on a fresh baseline; a turn-replay baseline is cheap enough to re-run alongside anyway. Two
  versions run on different days always need both sides run together."
- Cross-day check: "When a reading across days cannot be avoided, ten baseline games on fixed deals are
  played first as a check. That can show that something moved; a clean result does not prove that
  nothing did."
- Fingerprint fields in full: the code commit and whether the code had uncommitted changes, a hash of
  the prompt files, the model names, the temperature, the thinking levels and the embedding model.
Left off deliberately: the 2026-06-12 canary; the second independent reading (27% vs 67%, on the Level 3
page); winners by side (Level 3); the three meanings of "pairwise" as a list; prompt golden, provenance
manifests, run graduation, worktree-on-tag; the embedding check (optional; cut for length); a judge from
neither side (LLM judges page); costs; per-provider pinning details; fingerprint gaps (role cards outside
the prompt hash, served games unstamped: the fingerprint's own page in chapter 7). -->
