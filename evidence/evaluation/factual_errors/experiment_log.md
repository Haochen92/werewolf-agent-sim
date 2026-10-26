# Factual errors: the detailed record

*The folder was named `hallucination_bench/` until 2026-10-23; the bench's code keeps that name
(`eval-hallucination-bench`).*

This file holds the full detail behind [report.md](report.md). Read report.md first. Come here for how each method was built, how far it was checked, and every count, date and caveat.
Written 2026-10-23. The code audit of 2026-10-03 and its fix check of 2026-10-04 used to be two separate files. They are folded in here as §8 and §9.

---

## 0. How the methods fit together

Every method here freezes a moment of a recorded game and asks one narrow question about it. The methods differ in two ways: what is frozen, and who decides whether a statement is wrong.

| Method | Section | What it answers | Who decides "wrong" | Game | Trust |
|---|---|---|---|---|---|
| Census screen (July 2026) | §1 | Which statements touch a fact that can be checked | Code | Nine-seat | ✅ within its scope |
| Census reader (July 2026) | §1 | Does a flagged statement contradict the record | Two models, checked by hand | Nine-seat | 🟡 |
| T1b counterfactual replay (July 2026) | §2 | Do 4 known errors come back under the new prompt | A grader, then a hand read | Nine-seat | ⚠️ no statistical power per case |
| T2 regression replay (July 2026) | §2 | Do the added prompt fields break how agents apply strategy | Counts on the output | Nine-seat | 🟡 |
| T1c ship test (July 2026) | §2 | Does the new prompt reduce errors on turns prone to error | The census reader | Nine-seat | 🟡 |
| The bench (October 2026) | §3–4 | Error rate per arm (model × prompt), paired per case | The census reader, or a written expectation | Nine-seat cases | 🟡 |
| Invented-check replay (October 2026) | §5 | Which wording made one investigator invent a check | A hand read of every sample | Nine-seat | ✅ for that one turn |
| Ten-seat pinned cases (October 2026) | §6 | Do known ten-seat failures still happen | A written expectation, with verdicts read by hand | Ten-seat | 🟡 regression only |
| Summary-claim replay (October 2026) | §7 | Does the summariser still invent, drop or misfile claims | Code checks on its structured output | Ten-seat | 🟡 regression only |

Two words come up throughout.

- A **frozen turn** (also called a **case**) is one agent turn, stored as the game state the engine held when the agent spoke. Because the state is stored, the turn can be re-run under another prompt or model.
- An **arm** is one setup under test. Usually it is a model plus a prompt version. Sometimes it is an older version of the engine, checked out from git.

Many design verdicts below sit in [discussion_evidence](../../gameplay/discussion_evidence.md). This file cites it by section number.

---

## 1. The census (July 2026, nine-seat)

**What it is.** The census gives a population rate. It answers: what share of all agent text carries a role-fact error? A role-fact error is a statement that contradicts the game record about deaths, roles, counts of players left, or who claimed what. The census is a pipeline of four stages. It ran once, on 2026-07-08. It covered the 50 `v2_full` games in both paired arms, under the prompt epoch of 2026-06-22. (A prompt epoch is the set of prompts in force from a given date.)

Two kinds of agent text are counted:

- **Public messages**, which every player hears.
- **Private notes.** A private note is the strategy note an agent writes for itself, carried into its next turn. Notes written alongside a night action are called night-action notes.

**How it works.**

*Stages 1 and 2: the screen.* This is code; no model is called.

- It flags every text unit that does one of four things:
  - names a dead player;
  - uses a role word whose holders are all dead;
  - states a count that differs from the true number of players alive;
  - says a player made a claim that is absent from the logged claims.
- It then drops only what it can prove is fine. That is game-master text, and count claims that match the true count.
- Player ids and role words are closed sets. So any error that names one of them is caught by design.
- An error that names nothing is out of scope by design. Examples are "the guy we lynched" or an invented event.
- Of 7,846 units scanned, 2,461 were kept as candidates.

*Stage 3: the reader.* A model reads each candidate against a fact sheet.

- The **fact sheet** is built by code from the game record. It lists:
  - deaths, with role and attacker;
  - alive counts;
  - votes;
  - logged claims;
  - the speaker's own private knowledge.
- The reader never sees the transcript.
- Sometimes a public message contradicts what the speaker privately knows. That is labelled deception and kept out of the count.
- The reader is a cascade of two models:
  - The **recall layer** reads every candidate. Its job is to miss nothing. This was `gemini-3.1-flash-lite`.
  - The **precision layer** re-reads only the recall layer's positives. Its job is to throw out false alarms. This was `gemini-3.5-flash`.
- The cascade was chosen on a golden set of 23 cases, over four rounds. On that set, flash-lite missed no golden error, and 3.5-flash handled the fine distinctions.

*Stage 4: the hand check.* The owner read:

- all 90 positives among public messages;
- a sample of 25 of the 278 positives among private notes;
- a sample of 15 of the 273 units the precision layer rejected.

**What it can claim.** This holds for that one nine-seat epoch.

| Surface | Errors | Rate | How the count was reached |
|---|---|---|---|
| Public messages | 68 genuine of 2,292 | about 3.0% | All 90 positives read by hand |
| Private notes | about 222 of 5,554 | about 4.0% | From a sampled precision of about 0.8 |
| Night-action notes | 113 of 1,179 | 9.6% | Confirmed by the models; the worst surface |

**How far it was checked, and what it cannot see.**

- The public rate is well grounded. It rests on a full read of its 90 positives.
- The private rate rests on 25 sampled items. So it is a point estimate with real sampling error.
- The counts are floors. In the sample of 15 rejected units, 2 to 3 of the precision layer's rejections were real errors.
- The fact sheet lists deaths only. So a claim about a failed night attack cannot be checked.
- Claims made earlier on the same day are not yet in the claims log. That makes a claim credited to the wrong player the weakest class.
- **Nine-seat only.** The screen knows the six nine-seat roles (`ROLE_ALIASES`: wolf, serial killer, villager, healer, investigator, vigilante). It cannot pick up a ten-seat role word such as the necromancer or the sentinel.
- **Never re-run.** The plan pre-registered a second measurement on the first batch after the prompt change of 2026-07-09 ([`validation_plan.md`](../../gameplay/turn_prompt/validation_plan.md), "T1-improvement"). No record of it was found. On 2026-10-10, running the census on ten-seat games was listed as open, at an estimated $2 to $3 (discussion_evidence §8.5, last paragraph).

**The only error count on the ten-seat game** is a hand audit of ten games, about 345 heard lines. Model readers did the reading against a rubric (discussion_evidence §8.4). It is a sampled read, not a census. It is catalogued in [`../labeling/sampled_reads/`](../labeling/sampled_reads/report.md).

**Code and record.**

- Screen: `eval-role-hallucination`, in `evaluation/src/audits/role_hallucination_screen.py`.
- Reader: `eval-role-hallucination-read`, in `evaluation/src/judges/role_fact_read.py`.
- Record: [`gameplay/turn_prompt/validation/hallucination_baseline.md`](../../gameplay/turn_prompt/validation/hallucination_baseline.md). Next to it are `hallucination_candidates.jsonl` and `hallucination_verdicts{,_stage2}.jsonl`.

---

## 2. The July replays: T1b, T2 and T1c (nine-seat)

A **replay** re-runs a saved agent turn under a new prompt or model. These three replays tested the July prompt bundle before it shipped on 2026-07-09. The bundle had three parts:

- a board listing the dead;
- a line giving the roles still alive;
- a list of per-player reads.

All three replays were pre-registered in [`validation_plan.md`](../../gameplay/turn_prompt/validation_plan.md). Their scripts are study code. They are kept inside the evidence folder as frozen records: `gameplay/turn_prompt/validation/{t1b_replay,regression_replay,t1c_ab_replay}.py`.

### T1b, the counterfactual case replay (2026-07-07)

- **What it is.** A replay of the 4 errors confirmed by the earlier manual count.
- **How it works.** Each error was replayed 6 times under three arms, 72 calls in all.
- **What it showed.** Three of the four never came back in any arm. That includes the arm with no change. They were one-off slips at temperature 1.0. The fourth came back even with a correct board in the prompt.
- **What it showed about the method.** A replay of errors that rarely come back has no power to show a fix working. That lesson set how the bench picks its cases (§3).
- **Record.** [`t1b_results.md`](../../gameplay/turn_prompt/validation/t1b_results.md).

### T2, the regression replay (2026-07-07)

- **What it is.** A check that the added fields did not break schema validity or the memory verdicts.
- **How it works.** 60 frozen decisions, each with its original retrieved memories, were replayed under four arms, 200 calls in all.
- **What it showed.** Comparing a replayed action with the action first recorded is mostly noise. About half the actions flipped even in the arm with no change. The record recommends measuring that floor first, with pairs of resamples from the same arm. Only then read flips between arms.
- **Record.** [`t2_results.md`](../../gameplay/turn_prompt/validation/t2_results.md).

### T1c, the ship test (2026-07-08)

- **What it is.** A paired comparison of the old prompt and the new bundle on turns prone to error.
- **How it works.** Error-prone frozen turns from the census were regenerated under both prompts, one sample each. The census reader cascade judged them. The results were compared in pairs, one pair per turn.
- **Run 1.** It pointed in a direction, at p≈0.08 on its positives. It also showed that its "clean" control turns were prone to error too. So the context predicts the error.
- **Run 2.** The hypothesis was reworded, written into the plan, and tested on 100 fresh contexts with no overlap.
  - The old prompt was bad on 48%. The new bundle was bad on 30%.
  - 29 pairs were better and 11 worse.
  - A one-sided sign test gave p=0.003. A **sign test** counts the pairs where the new prompt did better and the pairs where it did worse, ignoring ties. It then asks how likely a split that uneven would be by chance.
- **Record.** [`gameplay/turn_prompt/experiment_log.md`](../../gameplay/turn_prompt/experiment_log.md) §12. Outputs: `validation/t1c_outputs.jsonl` and `t1c2_outputs.jsonl`.

**How far to trust T1c.** Its strength is that the main metric was fixed before its data existed. Three limits apply:

- The verdicts are the machine cascade's. No hand read of T1c's verdicts is recorded.
- The cases were chosen because they went wrong. So the rates describe contexts prone to error, not whole games.
- Building the bench later found a flaw in this replay (§3, last list). It rebuilt vote turns with the vote's own result in view. For that reason its error rates on vote turns run high. Both arms read the same rebuilt turns. So the leak bears on the rates more than on the paired comparison. No rerun has checked that.

On 2026-10-03 the ship test's method graduated into the bench (§3).

---

## 3. The bench (built 2026-10-03)

The text of this section is the 2026-10-03 record of how the bench was built. Later corrections and additions carry their dates inline.

**What it is.** A standing benchmark for factual errors in what the agents say. A factual error is a statement that contradicts the game record. The bench replays frozen turns under any prompt version or model. Then a judge counts the errors. It was built on 2026-10-03.

### Why

Two findings made a standing measurement necessary.

- **Errors are common, and one can decide a game.** The July census found role-fact errors in about 3% of public messages and 4% of private notes (§1). In a live game on 2026-10-03, the investigator announced a check it never made. The village voted out an innocent player on that claim. The serial killer won.
- **Replaying one turn finds the cause, but not how often it happens.** Replaying that investigator turn showed that the wording of its results caused the invented check. It invented the check in 20 of 20 samples on the old wording, and 0 of 20 on the new one (§5). Choosing a model needs many such turns, measured the same way every time. So does checking that a prompt change does not bring old errors back.

The July ship test (T1c) did this once, as study code. The bench makes it a maintained tool.

### How it works

**Cases.** A case is one agent turn, frozen as the game state the engine held when the agent spoke. The state holds:

- the transcript so far;
- earlier summaries;
- deaths and revealed roles;
- the agent's private results;
- its previous note.

Replay rebuilds the turn's inputs with the engine's own builders. Then it renders today's template. So the same case can run under any prompt version or model. The prompt itself is never stored, only the state.

**Arms.** An arm is a model plus a prompt version.

- Each arm runs in its own process. That is because prompt versions are switches read when the code loads.
- Supported models on 2026-10-03: Gemini, DeepSeek, models hosted by NVIDIA, OpenAI and Grok.
- *Added 2026-10-23:* Claude models are supported too. They use an `anthropic/…` model name, as the Haiku arms in §6 do.
- *Added 2026-10-23:* two arm options arrived after v1.
  - `"checkout"` generates from a git worktree on an older commit. So a before-and-after pair runs two engines and one judge.
  - `"resummarize"` first rewrites every earlier day's summary with the checked-out summariser. So the arm tests the summariser as well.

**Two judges, each told only what it needs.**

- Most cases use the July census reader (§1). A cheap model reads every statement that touches a fact that can be checked. A stronger model re-reads its positives.
- Hand-picked cases carry a written expectation instead. An **expectation** states the facts a turn must not break. For the investigator, it is the only checks it made. A narrow judge decides whether a statement breaks the expectation (`evaluation/src/judges/golden_expectation.py`).

> *Correction 2026-10-23.*
> - On 2026-10-12, every judge default moved to Claude Haiku 5.5 (commit `e70f1627`). That covers the reader's recall and precision layers, and the expectation judge.
> - The same commit edited the run templates under `evaluation/config/template/hallucination_bench_*.json`. So they no longer reproduce the judges their recorded runs used.
> - The runs of October 3 and 4 in §4 were judged by `gemini-3.1-flash-lite` (recall and expectations) and `gemini-3.5-flash` (precision).
> - The Phase 3 cases in §6 were judged by `gemini-3.5-flash`. The Haiku game cases in §6 were judged by Claude Sonnet 5.5.
> - No record was found of the 23-case reader gate being run on Haiku 5.5.
> - A Claude expectation judge runs as one Message Batch per run.

**Cases are chosen by what still fails.**

- The pool was the 227 census turns confirmed wrong in July, plus 40 turns judged correct, as controls.
- Most July errors were one-off slips. A July replay found that three of four confirmed cases never came back (§2, T1b).
- So each candidate was replayed three times under today's prompts. It was kept only if it went wrong at least twice.

### v1

The screen ran on `gemini-3.5-flash-lite` with the current (v2) prompts, memory off, 3 samples per case.

| | Bad samples |
|---|---|
| Census turns confirmed wrong in July | 153 / 684 (22%) |
| Controls | 4 / 120 (3%) |

- The commonest error was miscounting who is left. For example, an agent hunts "the remaining wolf" while the dead roster in its own prompt shows both wolves gone.
- By role, vigilante turns went wrong most often (37% of samples). Investigator turns went wrong least (0%).

The frozen set is `evaluation/frozen_eval_sets/hallucination_bench_v1.jsonl`. It holds 125 cases in four slices. A **slice** is a group of cases reported apart from the others. A **pinned case** is a failure that was fixed, kept so the bench can check it stays fixed.

| Slice | Cases | What it answers |
|---|---|---|
| curated | 44 | Did a prompt change fix errors that today's prompts still make? |
| random | 40 | Which model makes fewer errors? (Drawn without regard to the screen.) |
| control | 40 | Is the judge raising false alarms? |
| pinned | 1 | Does a fixed failure stay fixed? (The investigator's invented check.) |

### v2 (2026-10-03)

- v2 adds four pinned cases from live game `46355b89`, for 129 cases in all.
- Its first use was the information-fidelity pass, in discussion_evidence §6.5. The code audit behind that pass is §8 of this file.
- Both frozen sets are nine-seat. Their cases come from June boards, and from website games played before the ten-seat wiring landed on 2026-10-09.

### What to trust, and what not to

- **The judge was right on 10 of 12 verdicts checked by hand.** Both misses came from the fact sheet naming only one attacker for a player killed by two. That was fixed before the final judging.
- **An old case is today's turn on a June board.** Its state fits today's code. But the history it carries was written under June prompts: summaries, messages and earlier notes. Results are split by source, so cases from live games can be read apart. Those match today's games. They should replace the June ones over time.
- **The curated slice leans toward the screen model's own mistakes**, because flash-lite chose it. Compare models on the random slice. Rerun flash-lite as an arm every time: even flash-lite scores better on a rerun than in the screen.
- **A replayed vote turn must not see the vote's result.**
  - The game record files a day's vote result, and the following night's deaths, under that day.
  - The first build read them back into vote turns. So the agent saw its own outcome.
  - That was a replay error, not a game error. In a live game the result is posted after the votes.
  - It was caught by reading the controls by hand. It was fixed before v1.
  - The July ship test rebuilt vote turns the same way. So its error rates on vote turns run high.
- **Day turns only.** Night turns go through different builders and are not covered yet. *Still true on 2026-10-23* (`PHASES` in `evaluation/src/replay/hallucination_bench.py`).

### Code and record

- Commands: `eval-hallucination-bench` and `eval-build-hallucination-bench`. See `evaluation/README.md`, section *Hallucination bench*.
- Provenance commits: `a14de67`..`ab48570`.
- The screen run: [`data/screen_v1/`](data/screen_v1/eval_results/summary.json), graduated here on 2026-10-23.

---

## 4. What the October arms showed about the bench (nine-seat cases)

**What ran.** Six comparisons ran on `hallucination_bench_v2` on 2026-10-03 and 2026-10-04.

- Seats: `gemini-3.5-flash-lite`, memory off, 3 samples per case.
- Slices: curated, pinned and control. That is 89 cases and 267 samples.

Their design verdicts are in discussion_evidence:

| Section | Comparison |
|---|---|
| §6.5 | The information-fidelity pass |
| §6.6 | Day summary v4; a vote history per player; a rule to cite the record exactly |
| §6.7 | The thinking budget |

They established three things about the bench itself.

**1. Its noise floor.**

- Judging identical generations a second time moved the totals by 1 to 2 bad samples of 267. The v3 arm went from 82 to 83. The v4 arm went from 85 to 87.
- The notes of one arm went from 67 to 65 of 151.
- Controls drew 1 to 6 false alarms of 120, across arms.
- Four of the layout and wording changes stayed inside that floor. Examples: 24 cases better and 14 worse (p=0.14); 11 and 11 (p=1.0); 16 and 18 (p=0.86).

**2. It can see a real effect.** Raising the seats' thinking budget from "minimal" to "medium" took bad samples from 82 to 27 of 267. 36 cases were better and 4 worse (p<0.0001). That was the first change the bench resolved beyond its noise.

**3. The expectation judge was not reliable on flash-lite.** In the fidelity pass, the pinned cases were read by hand. They showed the judge reading a presupposition as an assertion, and at least one outright error. The record says to do one of two things before trusting those numbers: re-judge the pinned slice with a stronger model, or tighten the expectations.

**Two wording limits** come from the fix check (§9):

- The "checkable statements" in the message and note rows are whole output units, not single assertions.
- A bad control after regeneration is not always a judge false alarm. A newly generated answer can make a real error.

**Code and record.**

- The run outputs (summaries and judged samples) were copied on 2026-10-23 into [`gameplay/data/october_bench_arms/`](../../gameplay/data/october_bench_arms/README.md).
- discussion_evidence carries the counts.
- Templates: `evaluation/config/template/hallucination_bench_{fidelity_pass,summary_v4,vote_history,record_citation,thinking}.json`. Their judges were edited after the runs (§3, correction of 2026-10-23).
- Bench arms run to admit a new seat model are catalogued in [`../model_admission/`](../model_admission/report.md).
- Some later replays reuse this harness to measure votes or deductions, not factual errors. They are the deduction injection, the healer's silence and the Haiku vote replay. They are catalogued in [`../evaluation_scopes/turn/`](../evaluation_scopes/turn/report.md).

---

## 5. The invented-check replay (2026-10-03, nine-seat)

**What it is.** A replay of one investigator turn that invented a check: its exact day-4 turn from game `832404e9`.

**How it works.**

- The turn was rebuilt from the game's LangGraph checkpoint. The checkpoint was read without writing.
- It was sampled 20 times under each of four variants:
  - as played;
  - results reworded;
  - previous note removed;
  - both changes together.

**What it can claim.** On that one turn, the old wording of the results caused the invented check.

- As played: 20 of 20 samples invented the check.
- Reworded: 0 of 20.
- Removing the note changed nothing.

It cannot say how often this situation comes up across games. And the rewording changed two things at once.

**How far it was checked.**

- Every sampled message was read by hand.
- A keyword screen ran alongside. It missed one invention in each of two variants. That is why the counts come from the hand read.
- The case became the bench's first pinned case.

**Code and record.**

- Runner: `evaluation/experiments/investigator_claim_replay.py`.
- Every prompt and sample: [`gameplay/data/investigator_replay/`](../../gameplay/data/investigator_replay/) (no README).
- Record: discussion_evidence §6.2.

---

## 6. Pinned-case sets on the ten-seat game (2026-10-10 and 2026-10-12)

**What they are.** The same bench harness, run on new frozen sets built from ten-seat games.

**How they work.**

- Each case carries a hand-written expectation. So all judging goes through the expectation judge, not the census reader.
- Five samples per case and arm, memory off.
- The bench rebuilds discussion turns only. So a round turn is replayed as a sweep turn.

There are two sets.

| | Phase 3 turn cases | First Haiku game cases |
|---|---|---|
| Source | Ten discussion turns from the balance games that were read by hand | Eighteen turns from the owner's live game `403f4dbc` |
| Cases | Eight that went wrong, and two controls where a player reasoned correctly on the same evidence. Later sets added the f02 rule turns (four) and the sentinel turns from the Luna games (four). | Three slices: a visit read the wrong way round; a repeated reply; a vote cast without a stated reason |
| How built | | Read-only, from the game's checkpoints in the server's database |
| Arms | The committed code from a worktree against the fixed working tree, on flash-lite and on `gemini-3.5-flash` | Claude Haiku 5.5 seats at effort low |
| Judge | `gemini-3.5-flash` (§3, correction of 2026-10-23) | Claude Sonnet 5.5, one batch per arm |
| Record | discussion_evidence §8.4 | discussion_evidence §8.6 |

In the Haiku set, each turn is also labelled by where the misreading came from:

- *origin*: the misreading is not yet in the speaker's transcript;
- *cascade*: other players have already made it.

**What they can claim.**

- Whether a known failure still happens under a change.
- Whether a stronger model makes it on identical prompts.

They are not rates. The records say so: "0 of 10" means the failure stopped happening in the replay, not that it is gone. The full flash games tempered one replay result. The replay found 1 error in 50 frozen turns. Play found one invalid deduction in about 15 heard lines. The reason: frozen turns are known failures, and full games find new ones (discussion_evidence §8.5, item 3).

**How far they were checked.**

- Every verdict was read by hand before the counts were used.
- In the first Phase 3 pass, that reading caught a wrong expectation. It said "never claimed any role" on a day the speaker had truly claimed investigator. The expectation was corrected and the samples judged again.
- In the Haiku set, every visit sample was read by hand before the verdicts came back. The hand read found about 19 bad before and 6 after. The judge found 16 and 5.
- One wrong judge verdict was found in the vote slice.
- So the judge's errors come from the expectations as well as from the model. The hand read is part of the method.
- The Haiku set has three origin turns. That is too few to measure a rule on the origin turns alone.

**Code and record.**

| | Phase 3 turn cases | First Haiku game cases |
|---|---|---|
| Runner | `evaluation/experiments/phase3_turn_cases.py` | `evaluation/experiments/haiku_game_turn_cases.py` |
| Configs | `evaluation/config/hallucination_bench_phase3_{turns,f02_rule,f02_hierarchy,f02_wording,sentinel_before,sentinel_after}.json` | `evaluation/config/hallucination_bench_haiku_game.json`, `hallucination_bench_haiku_game_vote_v2.json` |
| Record and per-case tables | [`data/phase3_turn_replay/README.md`](../../gameplay/data/phase3_turn_replay/README.md) | [`data/haiku_turn_replay/README.md`](../../gameplay/data/haiku_turn_replay/README.md) |

---

## 7. The summary-claim replay (2026-10-10, ten-seat)

**What it is.** A replay of the day summaries that went wrong in the Phase 3 games, without playing new games.

- Each case is one day of one captured game.
- The summariser is handed exactly what production handed it, and run 5 times.

**How it works.** No model judges. Code scores each sample's structured output twice:

- on the summary's own fields;
- on the claim ledger that the current code builds from the summary.

The **claim ledger** is the record, per player, of role claims and claimed night actions. Agents read it to learn about earlier days.

The checks are fixed patterns:

- a role credited to a player who claimed none;
- an action on oneself that can only have been done to the speaker;
- a record check that denies an announced attack;
- a denial that must be kept;
- controls: true claims the summary must keep.

Later sets added two more: roleblocks filed as denials, and empty results the record could not hold.

The arm is the checkout. So each arm runs its own prompt, schema and ledger.

**What it can claim.** Whether the summariser and ledger still produce those specific failures, per model. The scoring itself has no judge error.

**How far it was checked.**

- The cases were found by reading by hand and by a pattern scan of 31 games. So the replay checks only the kinds of failure someone coded.
- Five samples per case cannot show a rare error being prevented. The invented chanteuse claim never came back in any arm. So a ledger rule and a test guard it instead.
- The record found one regression this way, before it shipped. The first ledger rule dropped a true vigilante claim.

**Code and record.**

- Runner: `evaluation/experiments/summary_claim_replay.py`.
- Record: [`data/phase3_summary_replay/README.md`](../../gameplay/data/phase3_summary_replay/README.md); discussion_evidence §8.4.

---

## 8. The information-fidelity code audit (2026-10-03)

**What it is.** A read-only review of the agent code at commit `76ce221`. It made no gameplay or prompt changes, and no paid model calls. It asked where facts get lost or blurred on their way to a player.

**Scope.** It followed facts along this path:

*engine events → graph payloads → prompt rendering → summaries and private notes → extraction*

- A **payload** is the data the graph hands one player's turn.
- **Extraction** is the step after a game in which a model draws lessons from it for memory.

**What "confirmed" means.** A finding marked confirmed means a code path or a missing piece of information was verified in the code. It does not mean its effect on how often errors happen was measured. Any claim about behaviour needs a replay or a check in live games. This audit was a new record. It did not revise any earlier experimental result.

**The twelve findings at a glance.** Findings 1 to 5 were the highest priority.

| # | Finding | Status in the audit |
|---|---|---|
| 1 | The healer has no lasting, exact record of its own protections | Confirmed omission; high risk to behaviour |
| 2 | Speech that was held back can survive as a private belief that it was spoken | Confirmed path; effect on behaviour not measured |
| 3 | Voting drops the private note, then can replace it | Confirmed omission |
| 4 | The summary is asked to judge corroboration without the record to judge it by | Confirmed input limit |
| 5 | Engine facts and model summaries look the same once rendered | Confirmed gap in how they are shown |
| 6 | A healer save is still described as revealing a role | Confirmed inconsistency |
| 7 | The wolves' "villagers" list includes the serial killer | Confirmed inconsistency |
| 8 | Wolf night lacks the dead roster and the count of roles alive | Confirmed omission |
| 9 | Vigilante day prompts do not show bullets left | Confirmed omission |
| 10 | The healer's stated protection rules are incomplete | Confirmed inconsistency |
| 11 | Claim revisions and who said what have no lasting structured slots | Confirmed omission |
| 12 | Extraction after the game is not given a full record of private actions | Confirmed omission |

### Highest-priority findings

#### 1. The healer has no lasting, exact record of its own protections

*Confirmed omission; high risk to behaviour.*

Where the information is missing:

- `Agents/graphs/parent.py:151` builds the healer's night payload without its past targets.
- `Agents/nodes/day/flow.py:132` and `:209` give no healer action history either.
- `Agents/state/orchestrator.py` holds only the current `healer_target`. `Agents/nodes/orchestrator.py:289` resets it.
- The private strategy prose is the only general memory across turns.
- Public announcements reveal successful saves. They do not reveal protection choices on players nobody attacked.

What follows:

- A truthful healer cannot reliably answer "whom did you protect on night 2?" from engine facts in its prompt.
- A strategy note may hold this. But the note is neither complete nor authoritative.
- This matters directly when checking another player's protection story.

Other roles:

- The vigilante's history is incomplete too. `Agents/nodes/night/resolution.py:123` adds private results only for immune targets. Ordinary shots, held fire and shots blocked by the healer do not enter a complete private record of actions.
- The serial killer's past choices also rely on prose and public outcomes.

*Proposed fix.* An action history, written by the engine and private to the actor. It holds the night, the chosen target, and only the outcome the actor is allowed to know. It must not disclose unrelated attackers or hidden roles. Test two cases: a healer target nobody attacked, and a target attacked by several factions.

#### 2. Speech that was held back can survive as a private belief that it was spoken

*Confirmed path; the effect on behaviour was not measured.*

The **novelty check** is a model that holds back a message when it adds nothing new.

- In `Agents/turn/resolve.py:124`, a novelty rejection hides the message. But it returns the original `TurnEffects`.
- `Agents/nodes/day/actors.py:101` still saves the turn's strategy note.
- `Agents/prompts/prompt_formatters.py:52` hides the rejected message.
- The next turn gets no notice that this draft was withheld.

*Offline reproduction.*

- The novelty judge was stubbed to reject a draft whose strategy said "I have now publicly revealed my finding."
- The resolved action was gated. Its public rendering was "No messages yet."
- Its kept strategy was exactly that claim of disclosure.

This shows that a wrong note can survive the hold-back. It does not measure how often models actually write such notes.

*Proposed fix.*

- Record private delivery status apart from the proposed speech.
- Label the previous strategy as fallible planning.
- Make the messages actually delivered authoritative.
- Keep new private reasoning, without treating an unspoken draft as public history.

#### 3. Voting drops the private note, then can replace it

*Confirmed omission.*

- `build_agent_prompt_input` provides `previous_strategy`, and the vote payload carries it.
- But `DAY_VOTE_MEMORY_CONTEXT` in `Agents/prompts/memory/context.py:80` does not render it.
- The vote output still asks for `updated_strategy`. The actor then overwrites that player's earlier note, in `Agents/nodes/day/actors.py:160`.

*Offline check.* A marker note planted for the test was present in a rendered healer discussion prompt. It was absent from that healer's vote prompt.

So information held only in the note can vanish at the step from discussion to vote to night. Investigator results and wolf chat come in through separate inputs. They are not lost this way.

*Proposed fix.*

- Supply the previous note when asking for its update.
- Separate exact private facts from the strategy prose, which can be revised.
- Adding the note alone can also carry existing errors forward. So give it clearly lower authority than engine records.

#### 4. The summary is asked to judge corroboration without the record to judge it by

*Confirmed input limit.*

- `Agents/nodes/day/flow.py:285` gives the summariser only today's messages that are not from the moderator.
- `Agents/nodes/day/summary_agent.py:34` gives it neither earlier summaries, nor the dead roster, nor public night records.
- Yet `Agents/prompts/extraction/day_summary.py:19` asks it to tell apart roles confirmed by death and claims backed up in public.

So it cannot reliably check a speaker's account of yesterday's save, death or vote. The risk is that a second-hand story becomes apparent corroboration. Statements like "we already established this yesterday" are the main danger.

*Proposed fix.* Either summarise assertions strictly as assertions, or supply the relevant public evidence written by the engine. Do not give the summary the hidden mapping of roles.

#### 5. Engine facts and model summaries look the same once rendered

*Confirmed gap in how they are shown.*

- Engine vote and night announcements are stored as `DaySummary`. So are the discussion summaries a model writes.
- `Agents/prompts/prompt_formatters.py:63` renders each one as `[Day N]` plus prose. There is no label for the source or type.
- Players do not use the structured fields.

The engine announcements are not deleted. They are kept alongside the summaries. But a false statement in a summary and an engine event that contradicts it have no explicit order of authority in the rendered section. An offline rendering confirmed that both get identical day headings.

*Proposed fix.* Tell engine public events apart from summaries of what players said. Exact events outrank paraphrases. A repeated accusation does not become an engine fact.

### Other confirmed inconsistencies and omissions

#### 6. A healer save is still described as revealing a role

- `Agents/prompts/standards.py:64` lists "healer save announcement" under "role revealed by game mechanics".
- A save confirms an event: an attack and a protection. It does not confirm the saved player's role.
- The day-summary prompt has the newer, explicit correction.
- But this shared block is still used by the situation-query and extraction prompts (`Agents/prompts/memory/situation_summary.py`).

*Fix.* Separate event confirmation from role confirmation the same way in every prompt. Replay a saved wolf. Check that retrieval and extraction do not turn it into confirmed town.

#### 7. The wolves' "villagers" list includes the serial killer

- `Agents/nodes/orchestrator.py:310` documents `surviving_villagers` as the bucket of everyone who is not a wolf. That includes the serial killer.
- Yet `Agents/prompts/day_discuss.py:240` and both wolf night templates label it "Surviving villagers".
- This is an ambiguous faction label. It is not a leak of a private role.

*Fix.* Label the rendered list "living non-wolf players (town or serial killer)", without revealing which player is the serial killer. Renaming the whole internal state field is not needed for the prompt fix.

#### 8. Wolf night lacks the dead roster and the count of roles alive

- `Agents/graphs/parent.py:121` and `Agents/nodes/night/wolf.py:94` leave out the dead roster and the cast counts.
- `WOLF_NIGHT_DISCUSS` and `WOLF_NIGHT_VOTE` leave out the rendered blocks.
- The other night roles get them.
- Inspecting the template variables confirmed that both wolf templates lack `dead_roster` and `alive_roles`.

Wolves can still work out the deaths from public history. But they lose the fixed aid that was added precisely so they would not have to.

*Fix.* Give wolf night the same public count. Never substitute the hidden identities of the roles alive.

#### 9. Vigilante day prompts do not show bullets left

- Day payloads carry `vigilante_bullets`.
- But `Agents/prompts/day_discuss.py:266` and `Agents/prompts/day_vote.py:157` render only the prose about private shot results.
- So a vigilante with zero bullets may not see that during a discussion about taking a shot tonight.
- The night prompt does include the counter. Night routing skips the vigilante when it has none.

*Fix.* Render the bullets left in day discussion and voting too. Offline template inspection confirmed the omission. Test a vigilante with zero bullets claiming it will shoot.

#### 10. The healer's stated protection rules are incomplete

- `Agents/prompts/night.py` and the healer playstyle say protection works against wolves or the serial killer.
- In fact, `Agents/rules/resolution.py:38` saves a protected target that is not immune from any attack collected that night. That includes the vigilante's shot, and several attacks on the same night.
- Offline check of the rules core: a vigilante-only attack plus a matching healer target gave `saved`.

*Fix.* State plainly that protection covers all night attacks on the chosen player, subject to the actual order-of-resolution rules. This finding is not evidence that players currently get every such inference wrong.

#### 11. Claim revisions and who said what have no lasting structured slots

- `Agents/schemas/output.py:174` models an accusation as accusers, target, reasoning and defence. It models a role claim as player, role and evidence.
- There is no required slot for a result's target or night, the source message, a retraction, or the status of an assertion.
- `summary_agent.py:59` turns these into prose.
- Revisions can survive in prose. But the schema does not require it, and does not support reliable matching of contradictions.

*Fix.* Add narrow fields for source and revision when building the claim ledger. Do not assume that all existing summaries lose revisions. That would need a fidelity census against the source messages.

#### 12. Extraction after the game is not given a full record of private actions

- `Agents/memory/extraction/inputs.py:70` builds its evidence from the public transcript, wolf chat, investigator results and the final strategy notes.
- It leaves out the exact action histories of the healer, the serial killer and the vigilante. It also leaves out the vigilante's private result records.
- These may exist in runtime metrics or eval artifacts. This builder does not provide them.
- The extraction prompts are framed as if the extractor knows everything. That overstates how complete the input really is.
- So the extractor can infer a plausible night tactic without seeing the actor's exact choice. It may also treat a final strategy note as an accurate account of earlier play.

*Fix.*

- Feed in clearly labelled records of actions and outcomes after the game. Include held actions and results never delivered.
- This is allowed after the game. Do not reuse that all-knowing input during play.
- Keep the rebuilding of facts separate from the hindsight and credit problem, which was already diagnosed.

### Lower-confidence risks: worth a focused replay, not an automatic rewrite

- **A second witness could be held back.** The novelty judge says that agreeing without a new angle is not new (`Agents/turn/novelty_agent.py:30`). It has no explicit exception for independent corroboration. Test the pair "I agree" against "I independently observed the same visit." Scheduler plan S3 already expects this.
- **Example names may leak into reads.** The JSON examples repeatedly name `player_2` as a suspected wolf, with a concrete invented reason. They are meant as format examples. But they could leak into live reads. Test equal templates with neutral examples, rather than claim this is an established cause.
- **Reads are not carried forward.** `PlayerRead.why` allows "unchanged". But reads are only logged. They are not carried as a structured state of a player's beliefs (`Agents/turn/eval.py:39`). No full map of earlier reads is supplied on the next turn. The private note can keep some beliefs. It cannot reliably keep every read and the evidence behind it.
- **Notes can keep a disproven premise.** Free-form private notes are rewritten each turn in 3 to 5 sentences. They carry no source references, and nothing requires disproven beliefs to be dropped. So a note can keep a premise after it was publicly corrected. Carrying notes into voting should go together with the authority split in finding 3.

### Earlier issues, and checks against false alarms

- "Voted for" is still in `Agents/nodes/orchestrator.py:214`. The clearer wording that was requested is not yet applied at this commit.
- The main rules do not explicitly describe silent attacks on immune players. But wolf daytime prompts already mark the wolf channel as private and forbid mentioning it in public. So the problem is not a total lack of a warning about the private channel.
- The investigator result wording already names the actual night and the actor's own investigation. Do not report the old "revealed as" wording as a current bug.
- Leaving today's summaries out of the day summary does not keep night agents from today's vote. Day resolution also appends the vote announcement to today's `day_channel`, and night prompts read that.
- In the day payload builders reviewed, private investigator results and wolf chat are gated by role. This audit found problems of meaning and of source. It found no proof of an open leak of hidden roles.
- Hidden and gated messages are left out of the formatters players see, on purpose. The concern in finding 2 is the kept private note. It is not raw rejected speech leaking into everyone else's prompt.

### Recommended order and verification

1. **First:** exact private action histories; feedback on whether a gated message was delivered; keeping the note through the vote; telling public events apart from claims by source. These deal directly with evidence that is missing or contradictory.
2. **Then:** shared healer meanings, wolf roster labels and the count on wolf night, and showing bullets left in the day.
3. **Only after these limited corrections:** consider broader experiments with prompts that show only the board.

**Offline checks performed.**

- Rendered whether the marker note appears in discussion and in vote prompts.
- Inspected the actual template variables of the wolf and vigilante templates.
- Rendered model and engine summaries with the same labels.
- Ran healer resolution against a vigilante attack.
- Forced a novelty hold-back and checked the kept strategy.

These checks make no claim about generated games or about error rates.

**Existing focused regression suite.** 31 passed, with:

`poetry run pytest -q tests/engine/test_night_whiff_disclosure.py tests/engine/test_night_resolution_investigator.py tests/engine/test_discussion_prompt_flag.py tests/engine/test_wolf_night_sequential.py`

These passing tests cover existing behaviour. They do not cancel out the omissions above, which they do not cover.

---

## 9. The fix check (2026-10-04, at e53cb1e)

**What it is.** A comparison of the code at `e53cb1e` with the audit at `76ce221` (§8). It was read-only, with no gameplay changes and no paid calls.

**What it qualifies.** discussion_evidence §6.4 says the fixes were "all built". This check qualifies that. The main changes are in place. But four of the original findings still have gaps.

| Original finding | State of the code at `e53cb1e` |
|---|---|
| 1. Missing own-night history | Addressed for new games. The engine writes records filtered to each actor, including healer choices and vigilante holds. |
| 2. Held-back speech kept in the private note | Partly mitigated. The author sees delivery feedback that day. It disappears on later days. |
| 3. Vote overwrites a note it never saw | Addressed. The note is rendered and labelled fallible. |
| 4. Summary lacks the record | Addressed. Public announcements and earlier role claims are supplied. |
| 5. Engine facts look the same as the summary | Addressed. Source labels and separate rendered sections. |
| 6. Healer save framed as role confirmation | Addressed in the shared reasoning standards. |
| 7. Wolf roster mislabelled villagers | Addressed in the templates players see. |
| 8. Wolf night lacks the count | Addressed in the payload and the templates. |
| 9. Daytime vigilante lacks bullet count | Addressed. |
| 10. Incomplete healer protection rules | Partial. The common rules and the night instruction were fixed. The core strategy still says wolves or serial killer. |
| 11. Claim sources and revisions | Partial. Status and results were added. There are no message ids and no exact revision links. The compact context of earlier claims drops the evidence labels. |
| 12. Extraction lacks complete private actions | Partial. The other night actors were added. Investigator checks that were never delivered are still missing. |

"Addressed" describes the wiring. It is not proof that the model now reliably follows it.

### Remaining details

**1. The healer's core strategy.** `Agents/prompts/roles.py:26` still says "Your protection blocks a night kill from either the wolves or the serial killer." The new common rules and the healer night instruction include vigilante attacks. Update the core strategy too, so the account is consistent.

**2. Delivery feedback lasts one day.**

- `Agents/prompts/prompt_formatters.py:69` keeps delivery feedback to the current day only.
- An offline check used a gated draft on day 2. The feedback was in its author's day-2 input. It was gone on day 3.
- `resolve_decision` still keeps the original strategy note.
- So a same-day correction is now possible. But a wrong note can outlive its delivery warning.
- This is a remaining risk. It is not measured evidence that the error happens again.
- A lasting delivery status, or reconciling the note, would close it.

**3. The compact claim history drops the evidence.**

- `format_claims_on_record`, at `prompt_formatters.py:105`, drops `evidence`. It keeps the claim and the results.
- `summary_context` passes that compact history to the next summariser, instead of the old discussion summaries.
- In a test, a claim labelled "contradicted: claimed self-protection" became just "claimed healer — results claimed: night 1: p protected self."
- Playing agents can still see the evidence in the full summaries. The loss is only in the compact ledger and in what the next summariser gets.
- Keep the verdict and the source there.
- V3 also lacks the ids of source messages, and links that say which earlier result a retraction replaces.

**4. Undelivered investigator checks are missing from extraction.**

- `Agents/rules/night_record.py:34` has no investigator action.
- In night resolution, investigator results are still delivered only if the investigator survives.
- Offline reproduction: an investigator checked `w0` and died that night. The metric kept the target. But `format_extraction_inputs` showed "No investigations yet", and the action record held only the wolf kill.
- Keeping the result from a dead actor is intended. But leaving it out of the all-knowing extraction after the game leaves audit finding 12 open.

**The lower-confidence risks from the audit were not all changed.**

- The novelty check still has no explicit exception for independent corroboration.
- Example reads still use `player_2` as a wolf.
- Structured earlier reads are still not carried into the next turn.
- Notes are now labelled fallible, and vote updates are told to drop disproven content. That is mitigation. It does not guarantee factual consistency.

### Verification, and how to read the bench run

**Tests.** 53 focused tests passed, with:

`poetry run pytest -q tests/engine/test_information_fidelity.py tests/engine/test_night_whiff_disclosure.py tests/engine/test_night_resolution_investigator.py tests/engine/test_discussion_prompt_flag.py tests/engine/test_wolf_night_sequential.py tests/evaluation/test_hallucination_bench.py`

**Bench outputs, counted again independently.**

| Arm | Bad samples |
|---|---|
| before | 97 / 267 |
| after | 86 / 267 |
| after_resum (the after arm with `resummarize`, §3) | 82 / 267 |

- The stored summary reports 24 cases better and 14 worse, sign test p=0.1433.
- The run's report rightly treats this as an early direction, not a shown improvement.

**Two points on how to read it.**

- Rewriting the summaries brings the inputs closer to a fresh game. But it is still a replay of frozen turns. The earlier dialogue and private notes were generated by the old system. No new course of play was produced.
- The "checkable statements" reported for messages and notes are really whole output units, each classed as an error or consistent. For example, notes were 77/(77+78) against 67/(67+84). They are not separate counts of single factual assertions. The wording should say "checkable messages" and "checkable notes". This does not change the totals over all samples.

**Limits of the sample.**

- The sample is selected (curated, pinned and controls). It is not a population error rate.
- A control that fails after regeneration is not always a judge false alarm. A newly generated answer can make a real error.
- The reported confusions of the pinned-case judge should be settled by hand before those numbers are used to certify single fixes to behaviour.

---

## 10. What is not measured

- **No factual-error rate on the ten-seat game.** The census screen knows only the nine-seat roles. Every ten-seat measurement above is either a replay of known failures or a hand audit.
- **No night turns on the bench.** The July census found night notes the worst surface (9.6%). The bench cannot replay them.
- **The reader's calibration dates from the Gemini models.** The 23-case gate, the 10-of-12 hand check and the July hand read all describe the Gemini cascade. The current Haiku default has no recorded check.
- **The bench's frozen sets are nine-seat.** The ten-seat cases are separate sets, one per study. They are not a maintained frozen set with slices.

---

## Sources

| What | Where |
|---|---|
| Census screen | `eval-role-hallucination`; `evaluation/src/audits/role_hallucination_screen.py` |
| Census reader | `eval-role-hallucination-read`; `evaluation/src/judges/role_fact_read.py` |
| Census record (2026-07-08) | [`gameplay/turn_prompt/validation/hallucination_baseline.md`](../../gameplay/turn_prompt/validation/hallucination_baseline.md); `hallucination_candidates.jsonl`, `hallucination_verdicts{,_stage2}.jsonl` beside it |
| Pre-registration for T1, T1b, T1c, T2 | [`gameplay/turn_prompt/validation_plan.md`](../../gameplay/turn_prompt/validation_plan.md) |
| T1b and T2 (2026-07-07) | `gameplay/turn_prompt/validation/{t1b_replay,regression_replay}.py` (frozen); [`t1b_results.md`](../../gameplay/turn_prompt/validation/t1b_results.md), [`t2_results.md`](../../gameplay/turn_prompt/validation/t2_results.md) |
| T1c (2026-07-08) | `gameplay/turn_prompt/validation/t1c_ab_replay.py` (frozen); [`gameplay/turn_prompt/experiment_log.md`](../../gameplay/turn_prompt/experiment_log.md) §12; `validation/t1c{,2}_outputs.jsonl` |
| The bench | `eval-hallucination-bench` (`evaluation/src/cli_runner/regen_replay/both/hallucination_bench.py`), `eval-build-hallucination-bench` (`evaluation/src/data/builders/hallucination_bench.py`), replay `evaluation/src/replay/hallucination_bench.py`, judges `role_fact_read.py` and `golden_expectation.py`; `evaluation/README.md`, *Hallucination bench* |
| Frozen sets | `evaluation/frozen_eval_sets/hallucination_bench_v1.jsonl` (125), `_v2.jsonl` (129) |
| Bench build and audits (2026-10-03, 04) | §3 of this file; the code audit and the fix check, §8 and §9 of this file; provenance commits `a14de67`..`ab48570`; screen run [`data/screen_v1/`](data/screen_v1/eval_results/summary.json) (graduated 2026-10-23) |
| October arms (nine-seat) | discussion_evidence §6.5–6.7; run outputs [`gameplay/data/october_bench_arms/`](../../gameplay/data/october_bench_arms/README.md); templates `evaluation/config/template/hallucination_bench_{fidelity_pass,summary_v4,vote_history,record_citation,thinking}.json` (judges edited after the runs, see §3) |
| Invented-check replay | `evaluation/experiments/investigator_claim_replay.py`; `gameplay/data/investigator_replay/`; discussion_evidence §6.2 |
| Phase 3 turn cases | `evaluation/experiments/phase3_turn_cases.py`; `evaluation/config/hallucination_bench_phase3_*.json`; `gameplay/data/phase3_turn_replay/` |
| Haiku game cases | `evaluation/experiments/haiku_game_turn_cases.py`; `evaluation/config/hallucination_bench_haiku_game{,_vote_v2}.json`; `gameplay/data/haiku_turn_replay/` |
| Summary-claim replay | `evaluation/experiments/summary_claim_replay.py`; `gameplay/data/phase3_summary_replay/` |
| Ten-seat hand audit (a sampled read, not here) | discussion_evidence §8.4; `gameplay/data/phase3_reads/`; [`../labeling/sampled_reads/`](../labeling/sampled_reads/report.md) |

*The bench sections were written 2026-10-03. The record was widened on 2026-10-23 against the code and records above, and the code audit and fix check were folded in that day. This file rates how far each method can be trusted. Whether each fix worked is for the design records to say.*
