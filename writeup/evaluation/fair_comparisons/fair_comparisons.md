# Designing fair comparisons

*Level 2 · [Evaluation](../evaluation.md) · previous: [Choosing between turn replays and whole games](../replays_and_games/replays_and_games.md) · next: [Evaluating models before switching](../model_admission/model_admission.md) · status: rewritten 2026-10-29; for the owner’s review.*

## Historical brief (2026-10-25)

**Reader question:** Does the apparent improvement come from the intended change?

Subsections: unintended differences versus sampling variation; current baselines and interleaving;
recording configurations versus enforcing them; verifying requested settings; paired analysis and
uncertainty. Explain provider pinning through the general guarantee and its limits, with dated details
only if relevant to a specific example. Deciding the analysis before the data (added 2026-10-25): the
memory endpoint test fixed its measure, its number of games and its reporting before any game, and
changed its plan once, in writing, before data. Show the method only; its result belongs to Memory, and
the missing script behind its final number stays off the page (whole games, case 2).

**Lead story:** the shifted baseline and the later paired reanalysis. Its uncertain cause motivates
comparable runs; it does not prove provider drift. Thinking-token and memory-arm incidents illustrate
checking the experiment that actually ran. Do not imply every runner enforces every safeguard.

**Exhibit:** an annotated experiment record showing matched inputs, intended change, configuration and
measurement. Explain that a fingerprint records facts; a separate guard enforces a rule about them.

**Sources:** [experimental controls](../../../evidence/evaluation/experimental_controls/report.md), relevant
paired-test material from scoring, and deterministic audits case 5.

**Level 3:** [What the paired baseline reanalysis changed](paired_baseline.md), linked beneath the subsection it deepens.

Exhibits for this page are listed in [`../exhibits/source_map.md`](../exhibits/source_map.md).

---

<!-- Editorial review 2026-10-25: phrasing and structure revised; no independent factual
verification. Earlier completion notes below describe the pre-edit draft and are retained as history.
Verifier handoff: The baseline summary now states that the paired analysis changes both sample and method. The
pairing-power claim is limited to the decision score studied. Keep the June 12 canary interpretation
correction in the evidence owner's queue; no historical record was edited in this prose pass.
Verified 2026-10-25 (main session): the 2026-06-12 canary now carries a dated correction note in paired_ab/experiment_log.md (suspected, not established; owner ruling 2026-10-25); the map's rule now reads 'drift may be named as suspected, never asserted without evidence'. The six-point rerun spread is attributed to the ten-player admission replay set (model_admission/report.md §1). No further change needed.
-->

## Page copy (draft)

A comparison needs more than matching prompts and a better score. The intended versions must
actually run, their conditions must be comparable, and the experiment must be sensitive enough to
distinguish an improvement from variation between games.

Those requirements became concrete through three problems: a historical baseline that stopped
looking comparable, a memory experiment that ran a different configuration from the one intended,
and a planned test that usually missed an improvement even when one was deliberately added. Each
led to a different safeguard.

### Why historical baselines became questionable

An early memory experiment reused results from an older memory-off baseline in the nine-player
game. With unchanged prompts and game code, the town had won 20 of 30 earlier games but won only
1 of 10 fresh baseline games. That raised a problem before memory's effect could be interpreted:
the old results might no longer describe the conditions under which the new experiment was running.

A change in the hosted model was suspected, but the records could not establish it. A later
analysis compared the 20 starting deals played in both periods. Town wins fell from 12 to 7 on
those deals, but the paired test did not distinguish the drop from chance. This analysis used a
different sample as well as a different statistical test; its weaker evidence cannot be credited
to pairing alone.

The practical response did not require settling the cause. The reused deals were played again so
that the memory-off control came from the same period as the memory games. Running compared
versions together became the rule for subsequent experiments. It reduced exposure to changes
between periods while leaving ordinary sampling variation to be handled in the analysis.

[What the paired baseline reanalysis changed](paired_baseline.md) explains the two samples, the
statistical tests and why neither establishes that the model service changed.

### Hold the inputs and measurement comparable

The comparison aims to isolate the intended change. A different role deal, model configuration or
scoring rubric introduces a **confounding factor**: another difference that could explain the
result. The controls address these at three points:

| What needs to match | How the comparison controls it | What that buys |
|---|---|---|
| Starting situation | Both versions play the same deals, or receive the same saved turn in a replay | Neither version receives a different set of starting cases |
| Execution conditions | Run both versions in the same time window, with other model and application settings held fixed | Reduces unintended differences between the versions |
| Measurement | Apply the same scoring code or judge rubric to both versions | Keeps a change in measurement from looking like a change in play |

Matching deals creates a **paired design**: each starting assignment of roles is played under both
versions, and the analysis compares their outcomes deal by deal. It guarantees the same starting
roles, not the same game. Once an agent produces a different response, later agents receive a
different history and play can diverge.

Measurement needs the same care as generation. When a discussion judge's rubric split one label
into two, the share assigned to another label moved from 74% to 63% on the same messages. Comparing
old games under the old rubric with new games under the new one would have mixed changes in play
with changes in labelling. The old games were therefore scored again alongside the new ones using
the revised rubric. Consistent judging makes the comparison more interpretable; judge accuracy
still needs its own [validation](../llm_judges/llm_judges.md).

Scheduling is partly automated. The memory-experiment driver runs both versions concurrently,
matched by game id, and turn-replay comparisons run their versions in one session. The general
batch tool does not alternate configurations game by game, so comparisons outside those paths
still depend on manual scheduling. Same-window execution is a requirement with uneven enforcement,
not a guarantee supplied by every runner.

### Verify the experiment that actually ran

Even well-matched runs can answer the wrong question if their configuration differs from the
intended experiment. A June memory run was believed to give memory only to town agents, but gave
it to every faction. It produced plausible results without an error: nothing checked whether the
memory recipients matched the experiment's declaration.

The memory driver now requires that declaration before starting, unless the check is explicitly
waived. During the run, it reads back the actual memory settings after each round of games and
stops on a mismatch. In the recorded follow-up run, declared town-only, every round recorded the
four town roles and no others. That checks who received memory; it does not establish whether the
memory helped them.

Other conditions are recorded in a **runtime fingerprint**: model names, API backend, temperature,
requested thinking levels, prompt hashes and code version. Recording these makes differences
inspectable. A separate guard in the memory driver stops a run if the fingerprint changes between
games. Across separate runs, comparing fingerprints remains a manual step.

A fingerprint also has a boundary: it records requested settings, which may not have the expected
effect. A later probe found that the player model returned no reasoning tokens at its configured
“minimal” thinking level; it returned them at “low”. The experiments had recorded the request
without measuring its effect.

Both sides used the same level, so this finding did not introduce a configuration difference
between them. It narrowed what their results covered: the tested setting produced no reported
reasoning tokens. That is not proof that the model performed no reasoning. The factual-error
replay runner now records reasoning tokens per sample; game records still hold only the requested
level.

### Check what the experiment can detect

Controls reduce unintended differences, but they do not remove variation in sampled responses.
A fair comparison can still be too small to answer its question. **Statistical power** describes
how often a test would detect an effect of a specified size if that effect were present.

Before another paid run of the memory learning loop, a simulation checked the proposed test for
improvement over successive rounds. The measure was the town's decision score: code grades its
votes and night actions against the true roles, then averages the grades into one score per game,
from −1 to +1. This measures selected decisions rather than who won.

The simulation resampled scores from 15 existing memory-off games and added a known improvement
that grew across six rounds, ending 0.15 points above where it started. It then applied the planned
trend test. Across 2,000 simulated runs of 24 games each, the test detected that improvement only
about one time in nine. Even under the simulation's assumption of independent games, it usually
missed the effect it was intended to find.

That finding led to dropping the proposed trend test before paying for another run using it.
The replacement compared finished memory against no memory on matched deals. Its power was not
simulated, so the earlier check cannot establish that the replacement had adequate sensitivity.
The [memory experiment report](../../../evidence/memory_system/v7/report.md#testing-the-test-before-paying-for-it)
contains the simulation and design change.

Pairing itself also needed checking. In the original nine-player game, decision scores varied
about as much between repeated plays of one deal as between different deals. Matching deals
therefore added little precision for that score in that setting. It remained useful for balancing
starting roles, but it could not substitute for enough games. The same conclusion need not hold
for other measures or the expanded game, where the dealt cast can also vary.

For turn replays, repeated runs help distinguish variation in the model's responses from variation
in the judge's labels. Those are separate measurements: re-judging fixed outputs cannot tell us
how much another generation run would vary. [Choosing between turn replays and whole games](../replays_and_games/replays_and_games.md)
explains what each scope can establish.

### Commit to the analysis before seeing results

An experiment offers many possible readings: wins, vote quality, night decisions, individual roles
or an overall score. Selecting whichever looks best after seeing the results increases the risk
of presenting a chance finding as an improvement. A **pre-specified analysis** makes the main
question and reporting rules explicit before the evaluation data arrive.

For the memory loop's final evaluation, the written plan specified the town's decision score as
the primary measure, with other measures secondary. It fixed the number of games and committed to
reporting a null or negative result as “no compounding detected”, rather than searching for a more
favourable measure.

The plan was amended after the learning games but before any final evaluation game. Three
conditions on 20 deals became two on 30, comparing finished memory with no memory. This also
changed the question: whether the finished store helped, rather than whether it improved over an
earlier store. The amendment was recorded before collecting the endpoint results, so that change
remained visible in interpreting the experiment.

Pre-specifying the analysis limits selective reporting; it does not make a small experiment more
sensitive or validate its metric. The remaining engineering work follows those separate needs:
automate alternating versions in the general batch tool, record observed reasoning-token usage
alongside requested settings, and check power for the exact design before each paid evaluation.
These would extend safeguards that currently cover only particular runners or experiments.

**Evidence.**

- [Experimental controls](../../../evidence/evaluation/experimental_controls/report.md): baseline
  comparisons, matched inputs, measurement consistency, configuration checks and their coverage.
- [Deterministic evaluation](../../../evidence/evaluation/deterministic_audits/report.md), case 5:
  the memory configuration guard.
- [Measuring whether memory compounds](../../../evidence/memory_system/v7/report.md), “Testing the
  test before paying for it”, “The redesign” and “The pre-registration”: power simulation and
  the endpoint plan, including the timing and meaning of its amendment.

<!-- Revision 2026-10-29, direct rewrite at owner request; skill workflow discontinued.
Approved progression: historical baseline -> comparable inputs/measurement -> actual execution ->
statistical sensitivity -> pre-specified interpretation. Full prior copy and source mappings follow.
Detailed baseline statistics remain in paired_baseline.md. Provider-version inventory, full fingerprint
fields, detectable-effect estimates and repeat-run counts remain in evidence, not new L3 pages.
Source correction: v7/report.md (updated 2026-10-26) establishes that the amendment followed learning
but preceded endpoint games, and changed the comparator as well as the deal count. The older brief
and historical copy below are superseded on that point. Zero reported tokens is not no reasoning.
Sources read for consequential claims; no fresh code audit or experiment rerun.
-->

<!-- Prior page copy, retained as editorial history; superseded 2026-10-29.
When a new prompt, memory setting or model scores better than the old one, the result helps only if
the intended change caused it. Two other things can produce a difference. Something else may differ
between the sides: a model updated behind the same name, a side configured differently from what was
declared, a judge whose rubric changed between scoring runs. Or the difference may come from
sampling: the players' answers are sampled, so a game on the same deal can be won or lost with
nothing changed. Most comparisons here are small, about 30 games a side or a few dozen recorded
turns, so either can produce an apparent effect.

The two problems need different tools. Controls address unintended differences between the sides.
Repeated runs, suitable experimental design and enough independent cases help quantify sampling
variation and distinguish it from an effect. This page explains both, starting with the case that
set the project's rule on baselines.

### Unintended differences and sampling variation

A comparison is fair when its sides differ only in the change being tested. Four kinds of unintended
difference can break that, and each needs its own control.

| What can differ | Example | Control |
|---|---|---|
| The inputs | One side is dealt easier roles | Both sides play the same deals: a game's id determines which role each seat receives |
| The set-up | A side runs a different configuration from the one declared | The declared set-up is checked against the one that ran (memory experiments) |
| The conditions underneath | The hosted model changes with no code change | Both sides run in the same time window |
| The measurement | A judge's rubric changes between scoring runs | One judge scores both sides in one run |

Measurement is the easiest to overlook. When the rubric of the judge that labels discussion messages
split one label in two, another label's share moved from 74% to 63% on the same messages. Scoring old
games with the old rubric and new games with the new one would have looked like a change in play, so
the redesigned discussion's old games were re-read with the new rubric alongside the new ones.

Sampling variation remains when all four are held fixed. Two games on the same deal part ways at the
first line that differs, so a matched deal guarantees the same starting roles, not the same game.
No control removes this variation; it can hide a real effect or produce one by chance.

### A baseline that shifted

A June 2026 memory experiment initially reused an earlier memory-off baseline from the original
nine-player game. On byte-identical prompts and unchanged game code, the town then won only 1 of 10
fresh baseline games, compared with 20 of 30 earlier games. An independent-group comparison gave
Fisher's exact p = 0.0028. The record considered a change in the hosted model as well as chance, but
could not identify the cause.

The immediate response was to replay the reused deals so that the experiment's control came from the
same period as its memory games. This also produced 20 deals played in both periods. On those shared
deals, town wins fell from 12 to 7; an exact McNemar test of the paired outcomes gave p = 0.18.
That comparison did not distinguish the drop from chance. It used different games as well as a
different analysis, so the change in p-value cannot be attributed to pairing alone.

The practical rule did not depend on settling the cause: run both sides in the same time window.
The observed shift made the historical baseline questionable; it did not prove that the hosted
model had changed. The linked reanalysis explains the two comparisons and why their conclusions differ.

**Link:** Explore how testing the shared deals as pairs changed the reading of the shift →
[What the paired baseline reanalysis changed](paired_baseline.md).

### When a comparison needs a fresh baseline

"Pairwise" can mean three things. A *fresh baseline* is the old version run again in the same time
window as the new one. A *paired design* runs both versions on the same deals or recorded turns. A
*paired test*, such as McNemar's, compares the results pair by pair. Only the first is a question of
when to run.

| The question | Fresh baseline? | What still has to hold |
|---|---|---|
| Does it pass a bar fixed in advance, such as a regression case that must not recur? | No: there is no second side to drift | The bar is fixed before the run, and the sample can clear it beyond noise. "As good as the current version" is a comparison, not a fixed bar |
| Is A better than B, run the same day? | Not necessarily, if nothing else changed | Interleave the sides where possible; a short gap reduces drift, not sampling variation |
| Is A better than B, run on different days? | Yes: run both together, or interleave them | A pinned model version makes this safer, not safe |

The same-window rule is enforced in code by some runners, not all. The memory-experiment driver plays
both sides' games concurrently, matched by game id, and the turn-replay screens run all versions in one
sitting; a replayed baseline costs cents, so it is re-run by default. The general batch tool runs
several configurations without alternating them game by game, so a whole-game comparison run with it
has to be scheduled side by side by hand. Before a reading across days, ten baseline games on fixed
deals can show that something moved; a clean result does not show that nothing did.

Pinning a model version, where the provider allows it, removes one source of drift: a different model
served under the same name. It does not fix the outputs, which still vary by sampling, and it fixes the
model rather than everything around it: one provider states that changes to its serving infrastructure
occasionally alter observable behaviour. Some names cannot be pinned at all. The June player model had
no dated version, and each response reported only that name as its version, so the records could not
have shown a change underneath. The serving route matters too: the same model reached through two
different APIs gave different scores even at temperature 0, so the backend is part of what must match.

### Recording a configuration versus enforcing it

Every game record carries a *fingerprint*, a stamp of the conditions it ran under. A fingerprint
records facts; by itself it stops nothing. A separate guard turns a recorded fact into a rule. The
table reads a game record from the memory experiments that way.

| Part of the record | What it holds | Recorded, or enforced? |
|---|---|---|
| Matched input | The game id, which determines the deal | A test checks that an id reproduces its deal |
| Intended change | Which roles have memory on | Enforced: declared before any game, then read back each round of games |
| Configuration | Model names, API backend and region, temperature, requested thinking levels, embedding model | Recorded on every game; a change between games stops a memory-experiment run. Across runs, a person compares |
| Prompts and code | A hash of the prompt files; the code commit | As above. The day-discussion prompt is also compared byte for byte with a stored copy by a test |
| Embeddings | Only the embedding service's alias | Memory runs re-embed 12 fixed text pairs first, and stop before spending if any similarity moves by more than 0.02 |
| Not recorded | Whether a requested thinking level produced any reasoning | See the next section |

*Which facts a guard enforces depends on the runner: the fingerprint and memory-side checks stop the
memory-experiment driver, not every batch.*

The memory-side guard exists because of a June run believed to give memory to the town only. Every
side had it. The run produced plausible numbers and no error, because nothing compared the declared
set-up with the one that ran. The driver now refuses to start unless the memory side is declared or
the check is explicitly waived, and stops if any round's actual memory settings differ from the
declaration. In the one real run since, declared town-only, every round recorded the four town roles
and no others.

### Checking that a setting did what it names

A recorded setting shows what was requested, not what happened. In October 2026 a probe found that
the "minimal" thinking level produced no reasoning tokens from the player model then in use; it
produced them only from "low". Every game on that model until then had run at "minimal", and the
fingerprint had recorded the request without anything recording its effect.

Both sides of every comparison had run at the same level, so the comparisons stayed fair to each other.
What narrowed was their scope: the results describe players that produced no reasoning tokens before
answering, not players given a reasoning budget. The factual-error test set's runner now records
reasoning tokens per sample; game records still store only the requested level.

### How much a comparison can see

A fair comparison can still be too small to detect what it looks for. Before a paid run of the
memory learning loop, a simulation tested the planned trend test: it resampled scores from games
already played, added an improvement of known size, and counted how often the test found it. At the
previous paid run's size (24 games over six rounds), it found a planted +0.15 on the town's decision
score, which runs from −1 to +1, about one time in nine. That test was dropped before money was
spent on it. With nothing planted it raised a false alarm 2–3% of the time, below the nominal 5%
level in that simulation. The simulation was not repeated for the paired design that replaced it.

Pairing by deal bought less than expected. In the original game, games replayed on one deal varied
about as much as games on different deals: the variation came from how a game played out, not from
which roles were dealt, so pairing offered little additional precision for the decision score
examined. It stays the default because it is free and rules out one side receiving easier deals;
running both sides in the same window mattered more. With 30 games a side, only large effects show:
about 0.18 in town vote accuracy (the share of town votes cast against an evil player) or about 36
percentage points in win rate. Effects near 0.10 in vote accuracy would need about 100 games a side,
and wins far more. Decision scores and replayed turns can make some comparisons more sensitive, but
their findings remain limited to the behaviour and situations they measure.

Replays need a noise floor, and its source matters. Re-judging the same outputs measures the
evaluator: on the earlier game's factual-error test set, totals moved by 1 or 2 of 267. Re-running
generation is noisier: on the expanded game's model-admission replay set, two runs of one model
differed by about six percentage points at 70 samples, and one recorded vote went to the right
player in 8 of 10 samples on one run and 1 of 10 on the next.

**Link:** Explore repeated responses and case coverage in turn replays →
[Choosing between turn replays and whole games](../replays_and_games/replays_and_games.md).

### Deciding the analysis before the data

A memory test can be scored many ways: town wins, wolf wins, each role's decisions, per game or per
decision. With that many measures one will usually look significant by chance, and choosing it after
seeing the data turns chance into a finding. The final test of the memory learning loop, whether a
store built over four rounds of games beat no memory, therefore had its rules written before any game
was played:

- **The measure:** the town's decision score on each deal, computed by code; others were secondary.
- **The number of games,** so the test could not be stopped when the numbers looked good.
- **The reporting:** a null or negative result would be reported as "no compounding detected".
- **One change to the plan, in writing, before any game:** three arms on 20 deals became two on 30.
- **Checks during the run:** a deal counted only when both of its games, run together, finished; a game
  whose decisions fell back to defaults was discarded; and the run confirmed at the end that it had
  used the loop's code and model set-up.

Writing the measure down in advance makes it possible to check whether the analysis followed the
plan. It does not make a small experiment more informative, and departures still need reporting.



### What remains open

The controls are strongest where code enforces them: matched deals, rebuilt turns and the checks
within a memory-experiment run. They are weaker where a person
has to remember a step: comparing fingerprints across runs, interleaving a whole-game comparison
outside the memory driver, and checking that a setting produced what it names. The cause of the June
shift remains unresolved. The next steps follow from those gaps: alternate sides game by game in every
batch tool, record reasoning tokens per game, and simulate power for each design before a paid run. In
the expanded ten-player game, ten roles are dealt from a cast of twelve, so the lineup is known before
play and could be adjusted for.

**Evidence.**

- [A/B testing: the controls that keep a comparison fair](../../../evidence/evaluation/experimental_controls/report.md)
  (the June case re-tested as pairs; when a comparison needs a fresh baseline; what pinning covers).
- [Scales and scores](../../../evidence/evaluation/scoring/report.md), layer 3 (McNemar, Wilcoxon, Fisher
  and the noise floor).
- [Whole-game evaluation](../../../evidence/evaluation/evaluation_scopes/game/report.md), "How a
  whole-game comparison is set up" and case 2 (the pre-registered endpoint test).
- [Deterministic evaluation](../../../evidence/evaluation/deterministic_audits/report.md), case 5 (the
  guards on the experiment itself).
- [The power simulation](../../../evidence/memory_system/v7/execution_plan/report.md), §1–2.
-->

<!-- **Link (planned):** The endpoint test's result and what it meant for the learning loop → the Memory
chapter. -->

<!-- Sources for the page copy (drafted 2026-10-25):
Opening: experimental_controls/report.md "Why controls" (about 30 games a side or a few dozen turns,
temperature 1.0; things that change without code). "Two kinds of variability ... need different tools":
"When does a comparison need a fresh baseline?" paragraph 2.
Four-differences table: controls report §1 (same deal from game id; arm guard; same window) and §2 (one
judge). Rubric split 74% → 63%, old games re-read with the new rubric: §2 "One judge for both sides".
Same deal, not the same game: §1 "Same deal from the same game id".
June case: controls report "The case that set the rules"; paired_ab/experiment_log.md lines 5–22 (byte-
identical play prompts, no game-rule/scheduler code change since the baseline commit; re-run the 20
recovered ids so all 30 baselines are same-epoch) and lines 61–67 (seed set: 20 recovered with recorded
winners, 10 fresh). Original baseline: "20 in the original 30" (controls report). Fisher p = 0.0028.
Not pinnable; served model_version echoes the alias: paired_ab log lines 24–38. Paired re-test 12 → 7,
7 W→L, 2 L→W, exact McNemar p = 0.18: controls report; re-running
evaluation/experiments/june_baseline_shift_check.py on 2026-10-25 printed the same (5/7/2/6, p = 0.180).
"Neither the size nor the cause is established"; the rule followed because the two could not be told
apart: controls report. Town composition: paired_ab log "Design" (town_only = villager, healer,
investigator, vigilante).
Three meanings of pairwise; the three-row table (condensed; its 8-of-10 example moved to the noise
floor): controls report "When does a comparison need a fresh baseline?".
Same-window enforcement: controls report §1 "Both sides in one time window" and the control table (loop
driver yes, run_batch.py no; replay versions in one session). Code: evaluation/src/loop/driver.py
_run_arms_parallel runs ON and OFF tasks in one ThreadPoolExecutor pool, pairing by game_id. Replay
baseline "costs cents, re-run by default": fresh-baseline table. Ten baseline games on fixed seeds, a
clean result proves nothing: §1 "Manual steps" (cost left off).
Pinning: controls §1 "Pin the model where the provider allows it" (Anthropic's infrastructure statement;
flash-lite no numbered version). Backends differ at temperature 0: §1 "Never compare with historical
runs".
Record exhibit: fields checked in Agents/run_fingerprint.py runtime_fingerprint (git commit + dirty flag,
prompt_bundle_hash, llm_backend, vertex_location, game_model, temperature, thinking levels, pro models,
embedding model + dims). Within-run stop: driver.py (assert_fingerprint_consistent on both arms).
Seedability test, prompt golden, embedding check (12 pairs, 0.02, stops before spending): controls §1;
deterministic_audits case 5. Arm guard declare-or-waive and per-generation read-back:
evaluation/src/loop/invariants.py assert_arm_declared / assert_arm_factions; controls §1.
Arm-guard incident: deterministic_audits case 5 ("gave memory to every side while it was believed to be
town-only"); invariants.py docstring ("a plausible WRONG number, no error"); one run since, 2026-07-19,
four town roles: controls §1. "Round of games" = the loop's "generation".
Thinking setting: controls §4 (2026-10-04 probe; minimal → none, reasons from "low"; both sides same
level; scope narrows; test-set runner records reasoning tokens since 3e05e8a7; game records carry only
the configured level). Wording follows the map: "produced no reasoning tokens".
Power gate: controls §3; execution_plan/report.md §1–2 (score −1 to +1; 24 games over six generations;
+0.15 found about 1 in 9; false alarm 2–3%). Not run for the paired design: controls §3 and quick view.
Pairing bought little: controls §3 "What pairing bought"; game report "What pairing turned out to buy"
(nine-seat only). Detectable sizes 0.18 / 36 points / ~100 games for 0.10: controls §3. Vote accuracy:
Agents/compute_metrics.py town_votes_on_threat / town_votes_total.
Noise floors: 1–2 of 267 (scoring layer 3; controls §3); ~6 points at 70 samples (controls §3); 8 of 10
vs 1 of 10 (controls fresh-baseline table; turn report §2 item 1).
Pre-registration: game report case 2 "What and why" and "How it works" (method only).
What remains open: controls "Bottom line" and "What we would do differently next time" rows 1–4; the
ten-seat lineup: variance_reduction_levers.md correction 2026-10-23. -->

<!-- Completion note
Structure. The brief's subsections, in this order: unintended differences vs sampling variation; the
lead story (shifted baseline + paired reanalysis, with the Level 3 link beneath it, stating the finding
and its caveat); fresh baselines, interleaving and provider pinning (merged: pinning is the "conditions
underneath" control); recording vs enforcing (annotated-record exhibit + the memory-arm incident);
verifying requested settings (thinking tokens); how much a comparison can see (power, pairing, noise
floors; this carries "paired analysis and uncertainty" beyond the lead story, and the controls report's
§3); deciding the analysis before the data (method only); what remains open. The paired test is
explained once, in the lead story. Dropped in the length pass: judge-from-neither-side, the provenance
manifest paragraph, and DeepSeek's repointed name (all in the controls report).

Claims I was unsure of:
- The exhibit describes a game record's contents rather than quoting a real record; no values are
  shown. If the owner wants a real record, take one line from a loop run and relabel its fields.
- Detectable win-rate gap: the controls report says about 36 points, the whole-game report about 35;
  I used 36 (controls report, the primary home).
- The pairing spread figures (0.25 within a deal vs 0.21–0.26 across) were left qualitative: neither
  report states their unit beside them.
- "One provider states ..." is Anthropic (controls §1), unnamed to keep vendors off the page.
- Town composition is from the June A/B design; the counts of ordinary villagers and wolves are not
  stated in the sources read.
- "Each round of games" stands for the loop's generations; the arm read-back is per generation.

Mechanism claims checked in today's code (the June runs predate some guards; the arm guard's
fail-closed declaration is later than the incident): Agents/run_fingerprint.py (fields),
evaluation/src/loop/driver.py (_run_arms_parallel concurrency; fingerprint stop),
evaluation/src/loop/invariants.py (declare or waive; actual factions read back),
Agents/compute_metrics.py (vote accuracy). The turn-replay "one sitting" claim rests on the turn report
and the controls table, not a code read: replay arms are separate processes run in the same session.

Left off deliberately (Handle with care / evidence discipline): "model drift" as a fact (always a
shifted baseline, cause unresolved); never "every comparison runs side by side" (enforcement named per
runner); the endpoint test's missing script and git-ignored data; the endpoint result and all memory
A/B results (Memory chapter); "+17pp, p = 0.013"; test authorship and counts; the fingerprint's dirty
flag; costs. Also left off: the 2026-06-12 memory-off canary in paired_ab/experiment_log.md ("Drift +
noise-floor exhibit": town win 27% → 51% overnight, which that log calls "real model shift"). It is a
separate cross-day comparison, never re-tested; quoting its conclusion would contradict the map's
ruling. The owner may want to decide whether it appears anywhere.

Rubric self-scores (Level 2): reader orientation 2; added depth 2; conceptual coverage 2 (four kinds of
unintended difference, sampling variation, power, setting verification, pre-registration); paragraph
clarity 2; narrative economy 2; experimental separation 2 (the Fisher reading, the paired re-test, the
memory-arm incident, the thinking probe, the power simulation and the endpoint test each carry their
own sample); interpretation 2 (cause unresolved; "safer, not safe"; a clean check does not show nothing
moved); evidence and ownership 2 (no first person: no record names who ran the reanalysis or the
probe); technical accessibility 2 (Fisher, McNemar, fingerprint, pre-registration, noise floor explained
on first use); exhibits and links 1 (the record exhibit is descriptive, not a real record).
Length: about 2,250–2,400 words of page copy including tables (wc counts table pipes), over the 2,000
guide mainly because of the three tables; further cut candidates are the pinning paragraph's serving-route sentence and the
fresh-baseline table's first row. -->
