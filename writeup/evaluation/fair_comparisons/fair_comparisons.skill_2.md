# Designing fair comparisons

*Level 2 · Evaluation › Designing fair comparisons · trial draft written with the second version of the write-portfolio-page skill, 2026-10-29 · brief: [`_authoring/fair_comparisons.skill_2.brief.md`](_authoring/fair_comparisons.skill_2.brief.md) · revised 2026-10-29 after one editorial and one claims review; editorially revised, not factually verified; open questions in the brief.*

## Page copy (draft)

A fair comparison runs two versions of the system that differ only in the change being tested: memory
on against memory off, or one prompt against another. When the new version scores differently, two
kinds of problem can make that difference misleading.

The first is any other difference between the two sides: different starting positions, a setting
configured differently from what was declared, a model service that changed underneath, or outputs
scored in a different way. Each can fake an effect. I remove these by matching them, recording them
on every game, and letting code stop a run where it can check a rule.

The second is randomness within each side. The same situation produces different moves, so a small
batch of games can move a long way with nothing changed. Matching does little for this. It needs a
measured noise floor and a test whose size and main measure are decided before the games.

The two problems met in one baseline that shifted on unchanged prompts and code: chance and a change in
the hosted model could not be told apart. Since then, the rule has been that both sides of a comparison
run in the same time window.

### What has to match

A game starts from a deal: the assignment of roles to seats. The game's id determines the deal, so two
versions given the same list of ids start every game with the same roles in the same seats. That is
the same deal, not the same game. Players sample with randomness (temperature 1.0), so two games on
one deal part ways at the first line that differs. For a question about one decision, a turn replay
holds more fixed: it rebuilds a recorded turn from the game's saved state, so every version sees the
same board and history.

| What could differ | How it would show | Control |
|---|---|---|
| Inputs | One side gets easier deals, or a different history before the replayed turn | The same list of game ids; turns rebuilt from saved state |
| Set-up | A side runs a different model, prompt or memory setting from the one declared | The set-up stamped on every game, and checks that stop a run |
| Conditions underneath | The hosted model changes with no change in my code | Both sides in the same time window |
| Measurement | The two sides are scored by different judges, rubrics or runs | One judge, from the current code, scores both sides in one run |

Scoring can shift even with the same judge: one rubric change moved a label's rate from 74% to 63% on
unchanged messages. So old games are re-scored alongside the new ones, not compared with their
earlier scores.

The third row is the least obvious, because nothing in the code changes.

### A baseline that moved with nothing changed

In June, a memory experiment in the original nine-player game needed a memory-off baseline. (The
current game has ten players, dealt from a cast of twelve roles.) In the nine-player game the town
(villagers, plus a healer, an investigator and a vigilante) plays against the wolves and a serial
killer, a lone player who wins by outlasting everyone. An earlier baseline of 30 games had 20 town
wins. The plan reused 20 of those deals, whose winners were on record, and played 10 new ones.

The town won only one of the 10 new games. The prompts were identical byte for byte, and the code that
plays the game had not changed. Read as unrelated games, 1 win in 10 against 20 in 30 looked too large
a drop to be chance. The record's leading explanation was a change in the hosted player model, whose
name had no dated version that could be fixed; chance was recorded as the alternative.

Either way, the old games could no longer serve as the control, so the 20 reused deals were played
again in the new period. That gave each of them one result from each period: the only comparison that
held the starting roles fixed. A later reanalysis compared those 20 deals as pairs, counting only the
deals whose result changed. The town won 12 of them the first time and 7 the second: 7 deals turned
from a win to a loss and 2 the other way. A split at least that uneven would occur by chance about one
time in five (p = 0.18). The 10 new games remain the starkest sign of a drop, but they are few and were
dealt differently from the games they were compared with. The outcomes moved; neither the size of the
shift nor its cause was established.

Because a model change and chance could not be told apart, I turned the safe response into a rule:
both sides of a comparison run in the same time window, and new results are never compared with
historical runs. A change underneath then affects both sides alike. The memory-experiment driver
enforces this in code by running both sides together; a turn replay runs all its versions in one
session. The general batch tool does not alternate versions game by game, so a
whole-game comparison run outside the memory driver has to be interleaved by hand.

Pinning a model version, where a provider offers it, fixes which model sits behind a name, but less
than the word suggests: one provider states that the serving system around a fixed model can still
change behaviour. The June model had no dated version to pin, and its responses reported only its
name, so a change underneath could not have shown in the records.

**Link:** Explore the two readings of the shifted baseline and the paired re-test →
[What the paired baseline reanalysis changed](paired_baseline.md).

### Recording the set-up, and enforcing it

The same-window rule assumes that each side ran with the set-up it was meant to have. Every game
record therefore carries a fingerprint of its set-up: the code commit and whether it had uncommitted
edits, a hash of the main prompt files, the player model, temperature, thinking levels and the
embedding model.

A fingerprint records facts; it does not act on them. The guard is separate. Within one run of the
memory-experiment driver, every game's fingerprint on both sides is compared with the first, and any
difference stops the run, so a run resumed on another model or commit, or after an edit to the hashed
prompt files, cannot mix incomparable games into one result. Across separate runs nothing stops
automatically: a person compares the fingerprints.

| Part of the game record | Role in the comparison | What code does with it |
|---|---|---|
| Game id | Matched input: fixes the deal | Both sides play the same list of ids; a test checks that an id reproduces its deal |
| Memory setting for each role | The intended change | Declared before the run; read back after each batch of games, and a mismatch stops the run (next section) |
| Fingerprint: commit, prompt hash, model, temperature, thinking levels, embedding model | Set-up that must match | Recorded on every game; within a run, any change stops it |
| Decision scores, computed from the record (for example, whether a town vote removed an enemy) | Measurement | The same code scores both sides |

*What each part of a memory-experiment game record does in a comparison. The last column separates
what code only records from the rules it enforces.*

<!-- **Exhibit (content):** FC-record. Optionally render as an annotated record excerpt, the same four
labels attached to the fields; keep the record/enforce distinction in the labels. (Moved into a comment
after the editorial review: the spec line read as page copy.) -->

### Checking the experiment that actually ran

A matching fingerprint can still hide the wrong experiment: it records only part of the set-up, and
only as configured. Two faults showed what that leaves out.

The first was a memory run meant to give memory only to the town. It gave memory to every faction,
the wolves and the serial killer included, and nothing raised an error: the run produced a plausible
result for an experiment that had not been run. Now a run must declare which roles have memory before
any game, or explicitly waive the check. During the run, the memory settings each batch of games
actually recorded are read back and compared with the declaration, and a mismatch stops the run. In the
one run since, every batch recorded the four town roles, as declared.

The second was a setting that did not do what its name said. A probe found that the lowest thinking
level, used for the player model in every game until then, produced no reasoning tokens. Both sides of every memory comparison had used the same
level, so those comparisons stayed fair. What narrowed was their scope: those results describe players
that produced no reasoning tokens before answering. Replays of the factual-error test set, a fixed set
of saved turns used to check whether agents state things the game record contradicts, now record the
reasoning tokens of each response. Game records still store only the requested level, so checking what
it produced in a game remains a manual step.

With the set-up matched and checked, one source of difference remains: two identical sides still
produce different results.

### Reading a difference against noise

The way to see how much results vary by chance is to repeat something with nothing changed. What is
repeated decides which variation is measured.

Re-judging the same saved outputs measures the judge's own variation. On the factual-error test set,
judging the same 267 responses again changed the number judged to contain an error by one or two
([LLM judges](../llm_judges/llm_judges.md) covers judge checks). Re-running the same version measures
generation variation, which can be far larger for a single case. In one example, an unchanged saved
vote turn went to the right player in 8 of 10 samples on one run and 1 of 10 on the next. Each figure
comes from a single check, so it gives a scale rather than a fixed threshold: a difference within that
range is not evidence of a change.

Matching deals reduced this noise very little. In the nine-player game, eight deals each played twice
varied about as much within a deal as across deals, measured on one decision score, the town's vote
accuracy. The variation came mainly from how a game played out, not from who was dealt what. This was
not re-measured on the ten-player game. Pairing by deal is still the default, because it costs nothing,
rules out one side getting easier deals and lets matched games be compared side by side. Shared deals
do not protect against a change underneath; running both sides in the same window does.

### Planning the test before the games

Noise this large decides how many games a comparison needs, and that has to be known before paying for
them. With 30 games a side, a difference in the town's win rate would need to be about 36 percentage
points to show reliably. Vote accuracy, the share of town votes cast against an enemy, needs a
difference of about 0.18; effects near 0.10 on that scale need about 100 games a side. That is why the
final memory test rested its verdict on a decision score, checked against winning before use
([play metrics](../play_metrics/play_metrics.md)), and why many questions go to turn replays first.

Before one planned paid run, a simulation without model calls checked whether its test could see a
realistic improvement at all. It built pretend runs from the scores of games already played, added an
improvement of known size, and counted how often the test found it: at the previous paid run's size,
about one time in nine. The test was dropped before any money was spent on it.

The paired test that replaced it, the memory experiment's final test, fixed its analysis before any
game. It named one main measure, the town's decision score on each deal, because with many measures
one usually looks significant by luck. It fixed the number of games, so it could not stop early when
the numbers looked good, and promised to report a null or negative result as such. Its one change of
plan was made in writing, before any game. Its result belongs to the Memory chapter.

### What still depends on a person

The controls are strongest where code enforces them: the deal drawn from the game id, the turn rebuilt
from saved state, the fingerprint check within a run and the declared memory arm.
They are weaker where a person has to remember a step: interleaving a whole-game comparison run outside
the memory driver, comparing fingerprints across separate runs, and checking what a setting produced
in games.

The next steps follow from those gaps: alternate versions game by game in every batch tool; record
reasoning tokens on every game record beside the requested level; and simulate the exact test design
before each paid run, since the final memory test was not checked this way. On the ten-player game,
the dealt lineup is known before play, so a comparison could adjust for it without bias, which may
reduce noise. No comparison has done so yet.

**Evidence.**

- [A/B testing: the controls that keep a comparison fair](../../../evidence/evaluation/experimental_controls/report.md):
  every control, what it guards against and where it is enforced.
- [Checks done by code](../../../evidence/evaluation/deterministic_audits/report.md), case 5: the arm
  guard, the fingerprint check and the embedding check.
- [Whole-game evaluation](../../../evidence/evaluation/evaluation_scopes/game/report.md): how a
  whole-game comparison is set up, what pairing turned out to buy, and the final memory test's plan.
- [Turn replays](../../../evidence/evaluation/evaluation_scopes/turn/report.md): single-case noise.
- [Testing the test before paying for it](../../../evidence/memory_system/v7/report.md): the simulation.

<!-- **Link (planned):** "Its result belongs to the Memory chapter" → the Memory chapter's page on the
final memory test, once it exists. Do not publish a dead link. -->

<!-- Sources for the page copy (drafted 2026-10-29, trial 2 of the write-portfolio-page skill):
Opening: experimental_controls/report.md "Why controls" (about 30 games a side, temperature 1.0; things
that change without code) and "When does a comparison need a fresh baseline?" ¶2 (two kinds of
variability need different tools: controls remove differences between the sides; only sample size and a
measured noise floor deal with randomness within each side).
What has to match: controls §1 "Same deal from the same game id" (deal drawn from the id; same deal, not
the same game; diverge from the first different move); "The same turn, rebuilt"; §2 "One judge for both sides"
(rubric split moved another label 74% → 63% on the same messages; the redesign's old games re-read with
the new rubric). Table condensed from the controls report's control table. Omitted: prompt golden,
provenance manifests, run graduation, "a judge from neither side" (llm_judge case 7).
June case: controls "The case that set the rules"; paired_ab/experiment_log.md lines 5–22 (byte-identical
play prompts; no game-rule/scheduler change since the baseline commit; most likely cause model drift "or
small-N variance"; re-run the 20 recovered ids), 24–38 (not pinnable: no dated snapshot; served
model_version echoes the alias), 61–67 (20 recovered ids with recorded winners, 10 fresh). Town
composition: paired_ab "Design" (town_only = villager, healer, investigator, vigilante). First reading
1 of 10 vs 20 of 30 (Fisher p = 0.0028, kept off this page by the approved default; on Level 3). Paired
re-test 12 → 7, 7 W→L, 2 L→W, exact McNemar p = 0.18 (controls report; script output verified on the L3
page 2026-10-25). "About one time in five" = the two-sided exact p = 0.18. "Neither the size nor the cause
is established": controls report. Reanalysis worded neutrally (who ran it is not recorded).
Same-window rule and enforcement: controls report (rule follows because the two could not be told apart);
control table (loop driver yes; the general batch tool no; replays in one session); §1 "Both sides in one
time window"; evaluation/src/loop/driver.py `_run_arms_parallel` (both arms in one pool, paired by
game_id).
Pinning: controls §1 "Pin the model where the provider allows it" (providers' pages checked 2026-10-25:
one provider fixes the weights and configuration of an ID, but the serving infrastructure can change and
occasionally changes observable behaviour; the June flash-lite alias had no numbered version). Provider
and model names kept off the page (owner rule: no model families in prose).
Supporting notes moved out of the page copy at the length trim (2026-10-29):
- Embedding check (cut first, per the brief's length plan): where a name cannot be pinned, a behaviour
  check can watch it. Before every memory batch, twelve fixed pairs of texts are embedded again, and the
  batch stops before spending if any pair's similarity moves more than 0.02 from its stored value
  (controls §1; memory runs; runs by default; no record of it firing; a missing pin file only warns).
- Old versions: a structural redesign runs the old side from a checkout of the old code on an annotated
  tag, rather than keeping a copy alive beside the new one (controls §1; CLAUDE.md variant rule).
"Could not have appeared in the records": paired_ab log "Can we pin or detect the drift?" (served
model_version echoes the alias; the fingerprint's game_model records the alias, all the service exposes).
Fingerprint: Agents/run_fingerprint.py `runtime_fingerprint` (git_commit + git_dirty, prompt_bundle_hash,
llm_backend, vertex_location, game_model, temperature, game/summary/judge thinking levels, pro models,
embedding model + dims). Within-run stop: driver.py `assert_fingerprint_consistent` on both arms
(invariants.py docstring: "a backend / model / prompt / commit flip mid-run"). Across runs a person
compares: controls §1. Fingerprint coverage gap (prompt subfolders not hashed) left off the page.
Exhibit table: fields as above; game id ↔ tests/engine/test_seedability.py; memory setting ↔
invariants.py `assert_arm_declared` / `assert_arm_factions`; decision scores ↔ Agents/compute_metrics.py
(town_votes_on_threat / town_votes_total). Matches exhibit spec FC-record in exhibits/source_map.md.
Arm guard: deterministic_audits/report.md case 5 ("gave memory to every side while it was believed to be
town-only"); invariants.py docstrings ("a plausible WRONG number, no error"; declare via --expect-factions
or waive via --unchecked-arm; read-back each generation); controls §1 (one run since, 2026-07-19,
declared town-only, every generation recorded the four town roles). "Round of games" = the loop's
"generation".
Thinking level: controls §4 (probe 2026-10-04: "minimal" gave the player model no reasoning; it reasons
only from "low"; every game until then ran at "minimal"; both sides same level, so comparisons stay fair
and the scope narrows; the factual-error test set's runner records reasoning tokens per sample since
3e05e8a7; game records carry only the configured level). Map wording: "produced no reasoning tokens".
Noise: scoring/report.md and controls §3 (re-judging moved totals 1–2 of 267, nine-seat factual-error
test set); evaluation_scopes/turn/report.md §2 item 1 and "biggest limit" (8 of 10 → 1 of 10). Moved out
at the length trim: only with 25 samples per arm, all arms shuffled into one schedule, did that turn
settle, at about one in three in every arm. Model admission's ~6 points at 70 samples
left to that page.
Pairing: controls §3 "What pairing bought"; game report "What pairing turned out to buy" (spread within
one deal 0.249 vs across deals 0.21–0.26; still the default because free, rules out easier deals, lets
matched games be read side by side, repeatable; same window was what mattered; nine-seat only).
Sample size: controls §3 (30 a side: about 0.18 in vote accuracy or 36 points in win rate; effects near
0.10 need about 100 games a side). Vote accuracy = town votes on an evil player / town votes
(compute_metrics). Decision scores checked against winning before use: game report "Score decisions, not
only wins"; metrics/report.md.
Simulation: v7 report "Testing the test before paying for it"; controls §3 (built 2026-07-05; 24 games over
six generations; planted +0.15 found about 1 in 9; false alarm 2–3% with nothing planted; retired the
trend test before spend). Research labels ("power", "MDE") kept off the page per the applied-rigour ruling.
Final memory test: game report case 2 "What and why" and "How it works" (method only: main measure,
secondary measures, fixed number of games, reporting promised, one written plan change before data).
Result, the missing script and the git-ignored data stay off the page (Handle with care; Memory chapter).
What still depends on a person: controls "Bottom line"; "What we would do differently" rows 1–4 (the
paired endpoint was never simulated); variance_reduction_levers.md Lever 2 correction 2026-10-23 (ten-seat
deals ten seats from twelve roles; lineup is a pre-treatment covariate; not yet done for any comparison).
Revisions after the editorial and claims reviews (2026-10-29; resolution table in the brief):
- Fingerprint list: "the model service and region" dropped. The backend field still resolves only Google
  vs Vertex and is wrong for every non-Google model, the default since 2026-10-15
  (tracing/fingerprinting/report.md §4.3); the model name carries the provider. "A hash of the main
  prompt files": the hash is non-recursive and skips role cards, extraction/memory prompts and other
  subfolders (same report, "Current coverage gap"), so the stop covers "an edit to the hashed prompt
  files", not any prompt edit.
- Pairing: one score (town vote accuracy), canary pair of 2026-06-12, 8 common seeds; within-seed sd
  0.249 vs across-seed 0.211–0.262 (drift_surfaces_and_guards.md "Variance constants"). The old line
  "what made the June comparison fair was the shared time window" was replaced by the general statement
  about what protects against a change underneath, because one June arm (reranked town) ran after its
  baseline (memory_system/effectiveness/report.md §2, "timing confound").
- Rule wording: "the rule has been", not "the two sides run", per the Handle-with-care line (enforced in
  the memory driver and turn replays only).
- Thinking level: "every memory comparison" (the factual-error set itself compared thinking levels,
  82 → 27 of 267; model-admission comparisons differ by model).
- Arm fault: "every faction, the wolves and the serial killer included" follows invariants.py
  `assert_arm_factions` (ON arm ran all_enabled instead of town_only). deterministic_audits case 5 words
  it as "its 'control' was really a treatment"; the page wording holds under either reading. Flagged in
  the brief.
- Final memory test as the decision-score test: earlier memory tests reported wins beside decision
  scores (effectiveness report §2–§3).
- Ten-seat lineup: the levers audit shows it can be adjusted for without bias; it does not show it
  predicts outcomes, hence "may reduce noise".
Left off deliberately: the 2026-06-12 overnight canary; costs (the ten-game baseline check, per-game cost);
code and folder names; model and provider names; "drift" as fact; the untracked reanalysis script. -->
