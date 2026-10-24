# Fair comparisons: the guards that keep an A/B honest

This page covers the safeguards that keep a comparison between two versions fair: what each one guards
against, which comparisons it applies to, and how far it can be trusted. A comparison here is usually
small (about 30 games a side, or a few dozen frozen turns) and runs at temperature 1.0, so one silent
change underneath it can fake a result. Most of these safeguards are code that stops a run or fails a
test; a few are steps a person has to remember. The tests used to compare two versions (McNemar,
Wilcoxon, Fisher) are in [scoring](../scoring/report.md); how a whole-game comparison and a frozen-turn
replay are set up is in [whole_game_evaluation](../whole_game_evaluation/report.md) and
[replay_screens](../replay_screens/report.md); the dated audit of three statistical levers is in
[variance_reduction_levers.md](variance_reduction_levers.md). How it all fits together is in
[the hub](../report.md).

## Why guards

A comparison is only fair if the two sides differ in the one thing being tested. Many things can change
without anyone touching the code: the model service, the embedding model behind an alias, a prompt edited
for another reason, an arm configured differently from what was declared.

**The case that set the rules.** On 2026-06-11, ten fresh memory-off games came back with the villagers
winning 10%, against 67% in the original batch (Fisher p = 0.0028), with byte-identical prompts and no code
change. Something underneath had moved. From then on both arms run in the same time window, and results
are never compared with historical runs.

## Which guards apply to which comparison

| Guard | Whole-game A/B | Replay of frozen turns (a test set) |
|---|---|---|
| Both arms in the same time window | ✅ built into the loop driver; not in `run_batch.py` | ✅ arms run in one session |
| The arm guard (each arm runs the memory setup it declares) | ✅ loop driver | — |
| Fingerprint on every record, checked within a run | ✅ | ✅ |
| Embedding check at batch start | ✅ | — (no new embeddings) |
| Same deal from the same game id | ✅ | — (the turn is rebuilt from saved state) |
| Same inputs: the turn rebuilt from the game's saved state | — | ✅ |
| Old versions run from a git worktree on a tag | ✅ for structural changes | ✅ |
| One judge, from main, scores both arms | ✅ where a judge is used | ✅ |
| A noise floor (the same outputs re-judged) | — | ✅ on the factual-error test set |
| A power check before a paid run | ✅ (the trend test only) | — |
| Prompt golden (a prompt cannot change by accident) | ✅ day discussion only | ✅ day discussion only |

## Quick view

| Check | Trust | Main limit |
|---|---|---|
| The arm guard: two hard stops | ✅ | Tested in one real run since (July 19); in the loop driver only |
| Fingerprint check during a run | ✅ | Covers one run; across runs a person must compare |
| Paired statistics | ✅ | The maths is checked, but pairing added almost no power |
| Power gate | ✅ | Nine-seat trend test only; the paired design that replaced it was never simulated |
| Seedability test | ✅ | Same deal, not the same game |
| Embedding check at batch start | ✅ (rated in [deterministic_audits](../deterministic_audits/report.md), case 5) | Cannot pin the model; no record of it ever firing |
| The cross-epoch rule and the $3 memory-off check | 🟡 | Manual |
| Does a setting do what it names? | 🟡 | Manual; game records store the setting, not the reasoning tokens |
| Prompt golden | 🟡 | Pins one prompt, the day discussion |
| Run graduation | 🟡 | Built July 2026; first used 2026-10-23 |
| Provenance manifests | not rated | Shows that an input changed; cannot rebuild a run byte for byte |

✅ sound · 🟡 usable with caveats.

---

## 1. Stop the run before it costs money

**The arm guard.** Two hard stops in the loop driver (`evaluation/src/loop/invariants.py`). Before any
game, the run must declare which roles have memory on, or it does not start. During the run, each
generation's actual memory settings are read back and compared with the declaration; a mismatch stops
the run. It was built after a June run in which the memory-on arm turned out to be running a different
setup from the one believed. In the one run since (2026-07-19, declared town-only), every generation
recorded the four town roles. ✅

**The fingerprint check within a run.** Every game record carries a runtime fingerprint
(`Agents/run_fingerprint.py`): the backend, region, model ids, embedding model, temperature, thinking
levels, a hash of the prompt files, and the git commit. Within a loop run, any change in it between games
stops the run. Across runs nothing stops automatically: a person compares the fingerprints. ✅ within a run.

## 2. Detect drift underneath

- **Both arms in one time window,** so drift hits both alike. Built into the loop driver
  (`_run_arms_parallel`, pairing games by id). `scripts/run_batch.py` takes several configs but does not
  alternate them game by game, so a batch run has to be set up by hand to interleave.
- **Never compare with historical runs** ([model_drift](../../model_drift/drift_surfaces_and_guards.md)).
  Two backends for the same model (Google AI and Vertex) give different scores even at temperature 0, so
  the backend is part of what must match.
- **The embedding check at batch start** (`evaluation/src/audits/embedding_canary.py`). The embedding
  service exposes only an alias, so a change of model behind it cannot be seen in the record. Twelve fixed
  pairs of game texts are re-embedded at the start of every batch; if any pair's similarity moves by more
  than 0.02 from its pinned value, the batch stops before spending anything. It runs by default; a missing
  pin file only warns. There is no record of it firing.
- **Manual steps.** Results from different *epochs* (stretches of fixed prompts) are never compared, and
  before a cross-day reading, ten memory-off games are played on the baseline seeds as a check (about $3).
  Both depend on a person remembering. 🟡

## 3. Same inputs on both sides

- **Same deal from the same game id** (`Agents/nodes/orchestrator.py`, `initialize_game`). The game id is
  the one seed: the deal of roles to seats is drawn from it. `tests/engine/test_seedability.py` checks that
  an id reproduces its deal, that different ids differ, and, on the ten-seat game, that the drawn seats vary
  with the seed. It guarantees the same deal, not the same game: at temperature 1.0 two copies diverge from
  their first different move. ✅
- **The same turn, rebuilt.** A frozen-turn replay rebuilds the turn from the game's saved state with the
  engine's own builder, so every version under test gets the same board, history and private results.
- **Old versions run as they were.** A structural change is compared against the old code run from a git
  worktree on an annotated tag, not by keeping dead code in main (the variant rule in `CLAUDE.md`).
- **One judge for both arms.** Where a judge scores the comparison, the same judge from main scores both
  sides after the fact, with everything but the design pinned.
- **The prompt golden.** `tests/engine/test_draft_preview.py` renders every role's day-discussion turn on a
  fixed ten-seat board and fails if the text differs from the stored golden by one byte. It catches a change
  from any source (template, builder, deduction block), which the fingerprint's prompt hash can miss. It covers
  only the day discussion, and it was deliberately regenerated in 34 commits between 2026-09-29 and
  2026-10-21, each marking a new epoch. 🟡

## 4. Can the test see the effect?

- **The power gate** (`evaluation/src/instrument_validation/power/mde_simulation.py`, built 2026-07-05). A
  free simulation run before any paid run: it resamples scores from games already played, plants an effect
  of known size, and counts how often the planned test finds it. At the previous paid run's size (24 games
  over six generations) it found a planted +0.15 about one time in nine, which retired that test before any
  money was spent on it. With nothing planted it raised a false alarm 2–3% of the time, as a 5% test should.
  It was not run for the paired design that replaced the trend test. ✅ for what it sizes.
- **What pairing bought.** Splitting the June variance showed the deal itself explains almost none of it
  (spread within one deal 0.25, across deals 0.21–0.26), so pairing by game id adds almost no power; running
  both arms in the same window was what mattered. With 30 games a side, only large effects can be seen
  (about 0.18 in vote accuracy, or 36 points in win rate); effects near 0.10 need about 100 games a side.
- **A noise floor for replays.** Re-judging the same outputs shows how far totals move with no change at
  all: 1 to 2 of 267 on the nine-seat factual-error test set, so smaller differences mean nothing.

## 5. The record

- **Provenance manifests** (`evaluation/src/core/manifest.py`). A result records the git commit, its config
  and a hash of it, and each input file by path and SHA-256, so an input silently regenerated under the same
  name can be detected. It cannot rebuild a run byte for byte.
- **Run graduation** (`eval-graduate`, `evaluation/src/cli_runner/graduate_run.py`). Copies a finished result
  from the untracked results folder into `evidence/`, with a manifest of its inputs. Built in July 2026 and
  first used on 2026-10-23, for the results the evaluation pages cite.

## 6. Does a setting do what it names?

On 2026-10-04 a probe found that the "minimal" thinking level gave `gemini-3.1-flash-lite` no reasoning at
all (it reasons only from "low"), and every memory game had run at "minimal". The fingerprint had recorded
the setting on every record, but nothing recorded whether it produced any reasoning. Both arms always ran at
the same level, so every comparison stays fair; what narrows is the scope of each memory result, which is
about players that did not reason first. The factual-error test set's runner has recorded reasoning tokens per sample since
`3e05e8a7`; game records still carry only the configured level. 🟡

## What we would do differently next time

| Stage | Change | What was done | What it would buy |
|---|---|---|---|
| Set-up | **1. Interleave arms in every batch tool**, not only the loop driver | `run_batch.py` runs configs without game-by-game alternation | The same-window rule enforced by code everywhere, not by habit |
| Set-up | **2. Record what a setting produced next to the setting** (reasoning tokens per game) | Records hold the configured level only | A setting that does nothing is caught at the first game, not months later |
| Planning | **3. Simulate power for the exact design before each paid run** | Done for the trend test; the paired endpoint that replaced it was never simulated | No paid run whose test could not see the effect it looked for |
| Analysis | **4. On the ten-seat game, record the dealt lineup and stratify by it** | Nine-seat games all had the same cast, so there was nothing to adjust for | The lineup is known before play, so adjusting for it is safe and removes real variance (see [the levers audit](variance_reduction_levers.md)) |

**Bottom line.** The safeguards are strong where code enforces them: the arm guard, the fingerprint check,
the embedding check, seedability and the power gate. They are weaker where a person has to remember a step:
comparing across epochs, interleaving a hand-run batch, and checking that a setting did what it names.

## Sources

| What | Where |
|---|---|
| Runtime fingerprint | `Agents/run_fingerprint.py` (`runtime_fingerprint`); contract [`../../tracing/fingerprinting/report.md`](../../tracing/fingerprinting/report.md) |
| Arm guard, fingerprint guard, interleaved arms | `evaluation/src/loop/invariants.py`, `driver.py` (`_run_arms_parallel`, `run_loop`) |
| Paired statistics | `evaluation/src/core/stats.py` (`mcnemar_exact`, `wilcoxon_paired`); [scoring](../scoring/report.md), layer 3 |
| Provenance manifests | `evaluation/src/core/manifest.py` |
| Embedding check | `evaluation/src/audits/embedding_canary.py`, `embedding_canary_pins.json`; call site `scripts/run_batch.py`; build record [`../hardening_pass/experiment_log.md`](../hardening_pass/experiment_log.md) §4.9 |
| June drift catch, seed effect, detectable effect sizes | `../../memory_system/effectiveness/paired_ab/experiment_log.md`; `../../model_drift/drift_surfaces_and_guards.md` |
| Power gate | `evaluation/src/instrument_validation/power/mde_simulation.py`; readout [`../../execution_plan/report.md`](../../execution_plan/report.md) §2 (full table at `24dfd3a7`) |
| Seedability | `Agents/nodes/orchestrator.py` (`initialize_game`); `tests/engine/test_seedability.py` |
| Prompt golden | `tests/fixtures/day_discuss_prompt_golden.{py,json}`; `tests/engine/test_draft_preview.py` |
| Run graduation | `eval-graduate` → `evaluation/src/cli_runner/graduate_run.py`; `tests/evaluation/test_graduate.py`; `evaluation/README.md` (Data plane) |
| Reasoning-token scope | [`../../credit/blindspot_fix/experiment_log.md`](../../credit/blindspot_fix/experiment_log.md) §⑦; [`../../game_play_enhancement/discussion_evidence.md`](../../game_play_enhancement/discussion_evidence.md) §6.7; test-set token recording `3e05e8a7` |
| Noise floor | [factual_errors](../factual_errors/report.md), step 4 |

*Rewritten 2026-10-23 and checked against the code of that date; the June text it replaces is in git
history. The tests named here are cited for what they pin; the test suite is largely AI-written and
unaudited, so no test count is offered as evidence.*
