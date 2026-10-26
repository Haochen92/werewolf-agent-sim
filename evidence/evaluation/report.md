# Evaluation: how the project checks its agents, and how far to trust each check

**The system being checked.** Werewolf, a hidden-role game, played by AI agents. Around the players the
project built a memory of lessons from past games, a deduction engine that writes certain conclusions into
each player's prompt, a catalogue of models the players can run on, and a public website.

**What this page is.** The overview of the project's evaluation: what is evaluated, the methods used, how
to choose between them, what the methods caught about themselves, and how far each can be trusted. It is
meant to be read on its own. Each method has its own page with the detail, linked below. Two questions are
kept apart throughout:
1. **Does a part work?** (does memory improve play, does a prompt fix help) That is answered in the design
   folders named in the first table.
2. **Is the check that judged it any good?** That is answered here and in the method pages.

The earlier version of this page, with the dated memory-campaign section and the full instrument ledger, is
kept whole in the [experiment log](experiment_log.md). Records that live outside git, and the data every
method reads, are in [the source map](source_map.md).

## In short

- **Seven methods, cheapest first.** Code checks with no model; LLM judges; labelling by readers (one-off
  sampled reads and reusable golden sets); tests of a change at three scopes (one frozen turn, one day,
  whole games); scores computed from the game record; and the controls that keep every comparison fair.
  Two pipelines are built from them: the factual-error checks and model admission.
- **The rule that runs through all of it:** use code wherever the answer can be computed from the game
  record or the rules, and a reader only for meaning, with readers anchored to a person.
- **The apparatus caught its own errors, repeatedly**: a drifted baseline, a misconfigured memory arm, leak
  checkers that checked nothing, a thinking level that produced no reasoning, a test that let a replayed
  vote see its own result.
- **What holds:** code checks, exact counts and scores against the true roles, and the nine-seat gold sets.
  **What is directional only:** model judges and model readers, none checked against a person on the
  ten-seat game.
- **The largest gaps:** no person's check on any ten-seat label set, no factual-error rate on the ten-seat
  game, no CI, and the nightly leak audit not installed.

## What is evaluated

Six subjects. Memory was the first, and since the memory research closed in July 2026 most evaluation work
has been on the other five.

| Subject | The question | Main methods | Design verdict lives in |
|---|---|---|---|
| **Memory** | do stored lessons improve play; are the model-written fields right; does credit mean anything | whole-game A/Bs, the decision replay, the loop's credit validators, memory-component judges, golden sets, field audits | [`memory_system/`](../memory_system/report.md), [`memory_system/v7/execution_plan/`](../memory_system/v7/execution_plan/report.md), [`credit/`](../credit/report.md) |
| **Play quality** | do prompt, rule and card changes make the agents argue, vote and talk better | turn replays, blind sampled reads, ten-seat metrics, the read Brier score, vote-target counts, same-deal games, balance batches | [`game_play_enhancement/`](../game_play_enhancement/report.md), [`sequential_discussion/`](../sequential_discussion/report.md) |
| **Factual errors** | how often agents state something the record contradicts, and does a change reduce it | the census (code screen plus model reader), the factual-error test sets, pinned-case replays | [`game_play_enhancement/`](../game_play_enhancement/report.md) (problem 1), [`generation_prompt/`](../generation_prompt/validation_plan.md) |
| **The deduction engine** | is every line it writes true in every legal game; does it help the seat | soundness tests over random legal nights, a brute-force oracle, acceptance cases, censuses, injection and placement replays | [`reasoning_failures/`](../reasoning_failures/report.md) |
| **Models and cost** | can a candidate model play the game's turns; is it worse than the current one; what does a game cost | test prompts, replays against the current model, real games, cost and cache accounting | [`caching/`](../caching/report.md), [`model_selection/`](model_admission/model_selection.md) |
| **The information boundary** | does any prompt carry another seat's private information | batch leak checks, payload leak tests, the served-game leak audit, fidelity pins | [`agent_boundaries/`](../agent_boundaries/report.md) |

**The game changed under the methods.** Through July 2026 the game had nine seats, was played by Gemini
flash-lite, and evaluation centred on memory. Since 2026-10-09 the live game has ten seats drawn from a
twelve-role cast, seats default to Claude Haiku 5.5, and memory is a per-game choice served from a Postgres
store. Most memory results describe the nine-seat game; most play, factual-error and deduction results
describe the ten-seat game. The status board says which.

## The methods

### Judging one output, cheapest first

A single output (a line, a vote, a summary, a stored lesson) is judged by one or more of these.

0. **Code checks with no model** ([deterministic_audits](deterministic_audits/report.md)). Pass-or-fail
   checks and exact counts over prompts, game records and the engine: leak checks after every batch game,
   the deduction engine tested against a brute-force oracle over 20,000 random legal nights per test,
   model-written numbers recomputed from the board. Free and noiseless; they find only what a rule someone
   wrote can see. The information boundary and the deduction engine's soundness rest entirely on them.
1. **LLM judges** ([llm_judge](llm_judge/report.md)). One model scores another against a rubric: the
   factual-error readers, the in-game classifiers (the echo gate, the opening filter, the speakers'
   accusation tags), labelling at scale, the memory-era 1–5 rubric judges. The page explains how the judges
   were built: decide whether a model is the right tool, choose the kind of judging, design the rubric,
   validate it against a golden set, a stronger model or a real outcome. Only the factual-error judges were
   checked against a person, in the nine-seat Gemini era.
2. **Labelling by readers** ([labeling](labeling/report.md)). Readers label items against a rubric, for two
   uses: **golden sets**, kept as a reference a cheaper check is scored against, and **sampled reads**
   ([sampled_reads](labeling/sampled_reads/report.md)), made once to decide between two versions. Both use
   the same techniques: draw items blind to the outcome, hide the source behind a key file, fix the rubric
   and the bar first, measure agreement, anchor to a person. The gold sets (labelled or checked by a
   person) are nine-seat, May–July 2026; every ten-seat set is silver (model readers) or a hand-written
   expectation. The code to score model labels against a person's was built on 2026-10-23, and owner-check
   packets for three model sources wait on the owner's labels.
3. **Scales and scores** ([scoring](scoring/report.md)). How a label is recorded (binary, categorical,
   graded, pairwise, probability), how a judge is scored against a golden set (precision and recall, kappa,
   NDCG, Brier), and the paired tests that compare two versions.

The rungs form a calibration chain: a person's labels calibrate the judges and readers, which then label at
scale. In practice the links are mostly unconnected; the first owner checks are the step that connects them.
Code checks sit below the chain: they answer only questions written as rules, so they need no calibration.

### Testing a change

4. **Evaluation scopes** ([evaluation_scopes](evaluation_scopes/report.md)). The same controlled experiment
   at three scopes, like unit, integration and end-to-end tests:
   - **[One frozen turn](evaluation_scopes/turn/report.md)**: a recorded turn's whole input rebuilt exactly,
     each version answering it many times. Holding everything else fixed makes an effect visible from tens
     of samples, at under $0.01 to about $0.25 a screen. Fourteen screens, June–October 2026.
   - **One day**: replay one day live with the earlier days frozen. Designed in July 2026, not built.
   - **[Whole games](evaluation_scopes/game/report.md)**: the same deals played with and without the
     change. The only way to see outcomes and effects that cascade across days; noisy (30 games a side show
     only a win gap of about 35 points).
5. **Play metrics** ([metrics](metrics/report.md)). Scores code computes from a game record: decisions
   graded by the rules against the true roles, then checked against each side's win. On the nine-seat game
   the check chose the scores (48 tried, 11 kept); on the ten-seat game the rules define a good move and the
   check confirms or questions it (78 games, 2026-10-24).
6. **Experimental controls** ([experimental_controls](experimental_controls/report.md)). What keeps any A/B
   fair: both sides in one time window, one change per side, the same judge for both, a runtime fingerprint
   that stops a run if anything underneath changes, the arm guard for memory runs, a power check before a
   paid run.

### Pipelines built from these

7. **Factual errors** ([factual_errors](factual_errors/report.md)). Find errors in played games, freeze them
   as test cases, measure a rate with the census (a code screen, then a cheap reader, then a stronger
   re-read of its positives, then the owner), and check every fix on the test set. About 3% of public
   messages had an error in July (nine-seat); the problem side, what was tried and what worked, is in
   [the gameplay report](../game_play_enhancement/report.md).
8. **Model admission** ([model_admission](model_admission/report.md)). Five questions of a model migration:
   quality (replays against the current model), integration (can the code use it), cost and speed,
   reliability (rate limits, the rescue model, drift), rollout and records. Since 2026-10-24 one command
   runs the checks for a candidate with pass criteria fixed beforehand; it has not yet been run on one.

```
 how one output is judged, cheapest first
   ⓪ code check (no model; exact; only what a rule encodes)
   → ① LLM judge (cheap; mostly uncalibrated)
   → ② labelling: sampled reads (one-off) · golden sets (reusable; a person anchors them)
 how a change is tested
   one frozen turn → one day (not built) → whole games      scored by play metrics
   kept fair by experimental controls
 pipelines: factual errors · model admission
```

## Choosing the method: two rules

**1. Code checks what has a ground truth it can compute; meaning needs a reader.** Five kinds of code check
recur:

| Kind | Example | Where |
|---|---|---|
| A structured field against the truth | the vote target, the night pick or the claimed role against the true roles | [metrics](metrics/report.md), [turn replays](evaluation_scopes/turn/report.md) |
| A forbidden term in text | a seat id written into a lesson; another seat's private information in a prompt | [deterministic_audits](deterministic_audits/report.md) |
| A number the model wrote, recomputed from the board | players alive exact in 97% of 6,099 cases; the Vigilante's shots left in 16% of 1,109 | [deterministic_audits](deterministic_audits/report.md), case 3 |
| A structured claim against the engine's record | claims in the ledger checked against announced deaths, saves and the cast | [deterministic_audits](deterministic_audits/report.md) |
| Format and events | schema validity, retries, timeouts, the rescue model firing | [model_admission](model_admission/report.md) |

Outside these, code loses. A keyword count of meaning said 32 summaries named a quiet player, and reading
the matches found 4 of 124. A regex agreed with the model's addressee tags on 63% of 30 cases, so tagging
went to the model. The prose leak pass is substring matching, so a paraphrased leak passes.

**2. When a model screens for a person, set it to catch too much.** When a person checks every flag, a false
alarm costs seconds and a miss is never seen. The factual-error census is the worked example: code flags
every unit that names a dead player, a dead role or a count; a cheap model reads each flag; a stronger model
re-reads its positives; the owner checks the result. A sample of the rejections is read too, because misses
hide there: 2 to 3 of 15 were real errors, so the published counts are floors.

## What the methods caught about themselves

The strongest evidence that the evaluation is real is that it repeatedly found its own faults.

**June and July 2026 (nine-seat, memory):**
- A fresh no-memory baseline came back with the villagers winning 10% of games against 67% before, on
  identical prompts (Fisher p = 0.0028): the model service had drifted. Old baselines were dropped, and both
  sides of a comparison now run in one time window.
- A configuration slip let the memory side run memory for every faction instead of the town only. The check
  became the arm guard, which stops the run before spending.
- An engagement score was retracted (about 0.70 to 0.55) once the model was found to have silently skipped a
  third of its inputs.
- An investigator score that came out significantly backwards (+0.38, p = 0.039, 30 games) was re-run at six
  times the sample and the sign was noise (+0.15, not significant, 180 games).
- Both of the June paid loop runs were flagged invalid by the loop's own checks before they were reported.
- A free audit of model-filled memory fields fired its own pre-registered re-open condition: a field the
  retrieval gate keyed on was worse than a constant (0.606 against 0.827 for always-False).
- A check showed that pairing the two sides by deal buys almost no noise reduction, so running both sides in
  one window was what made comparisons fair.

**October 2026 (ten-seat, play, factual errors, models):**
- Three leak checkers had checked nothing on every live game, because the batch runner never passed them
  their inputs; found and fixed on 2026-10-14.
- Every memory game had run at a thinking level that produced zero reasoning tokens, confirmed in 680
  records. Both sides ran alike, so the comparisons stand, but every memory verdict is about players that do
  not reason first.
- The factual-error test set's first build let a replayed vote turn see its own result; reading the controls
  by hand caught it, and showed the July ship test had the same leak.
- DeepSeek V4 Pro passed 27 of 27 test prompts and answered 3 of 6 real turns in prose; real turns now count
  in admission.
- A replay read an 8-of-10 against 1-of-10 split on an identical prompt as noise, and got a stable rate
  (about one in three) only by shuffling every arm into one schedule at 25 samples.
- Re-embedding a 232-pair calibration set showed that dedup thresholds re-derived for a new embedding model
  would discard two labelled keeps.
- The ten-seat check of play scores against win (2026-10-24) showed the healer's save rate, trusted on nine
  seats, no longer goes with winning.

## Status board

Marks: ✅ sound · 🟡 usable with caveats · ⚠️ smoke test only · ❌ does not hold · ⏸ designed, not built ·
⛔ underbuilt. Each mark is the method page's own verdict. "9" and "10" mark the nine-seat and ten-seat games.

### Judging one output

| Page | Subject | What it covers | Trust |
|---|---|---|---|
| [**Code checks**](deterministic_audits/report.md) | information boundary · deduction engine · memory · play | batch leak checks; payload leak tests; served-game leak audit; fidelity pins; deduction soundness over 20,000 random legal nights per test and a brute-force oracle; 4 acceptance cases; solver and block censuses; record audits (9); embedding check; model-written memory fields recomputed (9, 10) | ✅ leak checks, payload tests, deduction soundness and oracle, embedding check (batch runner only) · 🟡 served-game audit (built; nightly job not installed), acceptance cases (the only coverage test), block census, record audits · ⚠️ pivotal-turn flags |
| [**LLM judges**](llm_judge/report.md) | memory · play · factual errors | every judge and in-game classifier: how each was built, what it was checked against, top-ups for today's game | 🟡 factual-error judges (person-checked, nine-seat, Gemini era) · 🟡 echo gate (model readers) · ⚠️ opening filter, accusation tags · ⚠️ memory-era rubric judges |
| [**Labelling**](labeling/report.md): golden sets, [sampled reads](labeling/sampled_reads/report.md) | memory · play · factual errors | the shared techniques; every golden set by who labelled it; the labelling pipeline and its calibration step; the October blind reads, the decision-tag read, hand-read games | 🟡 gold sets (nine-seat) · ⚠️ ten-seat silver sets (no person's check) · 🟡 blind reads (one model reader per item) · ✅ decision-tag read (98 of 102, above a bar set beforehand) · 🟡 calibration step (built 2026-10-23, not yet used) |
| [**Scales and scores**](scoring/report.md) | all | label scales; scores against a golden set; paired tests | 🟡 standard scores built and used · ⚠️ no 1–5 judge scored against people |

### Testing a change

| Page | Subject | What it covers | Trust |
|---|---|---|---|
| [**Evaluation scopes**](evaluation_scopes/report.md): [turn](evaluation_scopes/turn/report.md) | memory · play · deduction engine | the decision replay (9); checkpoint and tell-book replays (9); stage-filter replay (10); night-1 target check (9); nine October prompt, wording and deduction screens (10) | ✅ decision replay (as a direction-finder), night-1 check · 🟡 October screens (direction, not size), checkpoint replay · ⚠️ tell-book, counter-claim, private-note screens |
| [**Evaluation scopes**](evaluation_scopes/report.md): day | — | the per-day replay | ⏸ designed July 2026 |
| [**Evaluation scopes**](evaluation_scopes/report.md): [game](evaluation_scopes/game/report.md) | memory · play | June memory A/B, strategy-point A/B, pre-registered v7 endpoint (9); persona-voice and evil-cover pairs, 8 deals each (10) | 🟡 nine-seat memory harness (wins underpowered; pairing buys little; the endpoint's statistic has no committed script) · ⚠️ ten-seat same-deal pairs |
| [**Play metrics**](metrics/report.md) | play · memory | decisions graded by the rules; each score checked against its side's win (9: June–July; 10: 78 games); read Brier; vote-target accuracy; prompt and rule counts | ✅ town lynch scores, power roles lost, wolf blending (both games) · ❌ healer save rate on ten seats · 🟡 new roles' scores (too few games) · 🟡 read Brier · ✅ counts / 🟡 readings |
| [**Experimental controls**](experimental_controls/report.md) | all | same window, fingerprint, arm guard, embedding check, seedability, power gate, prompt golden, run graduation | ✅ arm guard, in-run fingerprint, power gate, seedability · 🟡 prompt golden (one turn type), run graduation (first used 2026-10-23) · manual: cross-epoch comparisons, interleaving a hand-run batch, checking a setting did what it names |

### Pipelines

| Page | Subject | What it covers | Trust |
|---|---|---|---|
| [**Factual errors**](factual_errors/report.md) | factual errors · models | the July census (9); the nine-seat test set and ten-seat test turns; pinned cases; the summary-claim replay (10) | ✅ census screen within its scope · 🟡 reader, test-set runs (regression checks, not rates) · ⛔ no factual-error rate on the ten-seat game |
| [**Model admission**](model_admission/report.md) | models and cost | the five migration questions; test prompts, replays against the current model, real games; thinking level for votes; summariser and memory-job models; rate limits and rescue; cost accounting; the one-command pipeline | 🟡 as a gate, not a ranking (replay spread about 6 points at 70 samples) · ✅ rescue path (deployed) · ⚠️ summariser and memory-job comparisons, seat-model games, live schema check · ⏸ the pipeline (built, never run on a candidate) |

**Dated records, kept for provenance:** [`loop/`](loop/report.md) (the v7 learning loop's checks, closed July
2026; part of the memory chapter), [`hardening_pass/`](hardening_pass/report.md) (the July review of the
memory methods), and the retired discussion tagger ([llm_judge/discussion_tagger.md](llm_judge/discussion_tagger.md)).

## Cross-cutting findings

**1. What can be trusted.**
- **Code checks.** The batch leak checks have run on every batch game since 2026-06-06; their one confirmed
  catch was 109 violations from a refactor, 0 after the fix. Every "certain" line of the deduction engine
  holds over 20,000 random legal nights per test and against every allowed deal. The arm guard and the
  in-run fingerprint stop a run rather than warn. Their limit is what they encode: a paraphrased leak or a
  rule nobody wrote down passes.
- **Exact and outcome-anchored scores.** Vote targets and winners counted by code; the town's lynch scores,
  which go with winning on both games (about +0.5 to +0.65); the decision tags against a bar set beforehand;
  test-set sign tests whose effect clears the set's own noise (re-judging moved totals by 1–2 of 267; reruns
  moved an arm by about 6 points at 70).
- **Gold sets.** The dedup decision keys, the census reader's July hand check, the hand-written expectations,
  the four deduction acceptance cases.

**2. What is directional only.**
- The memory-component judges, the discussion-evidence judge and the summariser-comparison judge: none
  checked against a person.
- The model readers. Every October blind read is Claude subagents, one per item. Re-read by fresh readers,
  labels tied to an act held exactly (claims 13 and 33) and judgment labels moved by several items (29 to 19
  of 73).
- Same-family judging. Every judge defaults to the players' own model, and the admission replays had Gemini
  judges grading a Gemini reference. Neither bias was measured.

**3. Where the anchors are thin.**
- **The ten-seat game's labels and scores.** No ten-seat label set has a person's check. The first ten-seat
  check of play scores against win (78 games) confirmed the core and left most new roles' scores untested;
  the grade table is an owner ruling never tested as a whole. Balance was read on flash-lite only.
- **Factual errors.** The only rate is July and nine-seat: about 3% of public messages (68 of 2,292) and
  about 4% of private notes. The census has never run on a ten-seat game. The test sets replay day turns
  only, though July found night notes the worst surface (9.6%).
- **The deduction engine's coverage** rests on four acceptance cases: soundness is tested at scale,
  completeness is not.
- **Replays.** Ten samples of one case are the spread of one prompt, not ten situations; few screens
  measured their own noise.
- **Scorers tied to role names.** Three scored the new evil roles as town until they were switched to the
  role registry on 2026-10-24; three places still name the nine-seat roles (two return nothing on ten seats,
  one research helper miscounts).
- **Every memory verdict** is about players with zero reasoning tokens.

**4. What is not running.**
- The nightly leak audit is documented but was found not installed on 2026-10-23, so no served game is known
  to have been leak-checked.
- There is no CI; tests run only when someone runs pytest. The tests in `tests/` are largely AI-written and
  unaudited, so the method pages cite deliberate tests for what they pin, never a test count.

**Failure modes worth naming once:**
- **Flat judge scores** carry no information (village dynamics pinned at 5.00).
- **Outcome halo:** a measure that can see who won measures the win. The extraction model's verdict on a
  play follows the side's win about twice as strongly as the decision's grade.
- **A setting is not its behaviour:** town-only memory believed while every faction ran it; "minimal"
  thinking with zero reasoning; leak checkers configured and checking nothing; field order kept 17 of 17
  times on test prompts and 15 of 24 on real turns.
- **One case resampled, read as many situations** (the AC2 vote).
- **Keyword counts of meaning** (32 against 4 of 124).
- **A frozen transcript hides what follows:** abstains ran 12–18% on frozen turns against 31% in live games.

## What we would do differently next time

| Stage | Change | What was done | What it would buy |
|---|---|---|---|
| Design | **1. Anchor every judge and reader to a person when it is built**, with a 30–50 item owner sample | Person checks only in the nine-seat era; ten-seat labels all model-made | Every number that rests on a model label carries an error rate |
| Design | **2. Write scorers against sides and the role registry, never role names** | Six places tied to the nine-seat roles; three fixed on 2026-10-24 | A new cast scores correctly the day it ships |
| Testing | **3. Fix each test's measure, pass bar and noise floor before running it** | Done for the v7 endpoint, the decision-tag read and a few screens | Every comparison a test, not a description |
| Records | **4. Commit every cited run's outputs, and the script behind every reported statistic, at the time** | Outputs graduated into `evidence/` only on 2026-10-23; one endpoint statistic has no script | Every number re-runnable from the record |
| Operations | **5. Run the deterministic tests in CI, and install the leak audit with the server** | No CI; the nightly audit never installed | Regressions and leaks caught without someone remembering |

**Bottom line.** The project's evaluation is strongest where code can decide (leaks, the deduction engine,
votes and winners against the true roles) and where it tests one change at a time on frozen turns with the
noise measured. It is honest about its weak rung: model judges and readers carry most ten-seat judgments of
meaning, and none has yet been checked against a person. The tooling to close that gap exists, and the owner
checks are its first use.

*Rewritten 2026-10-24 as a standalone overview, from the method pages linked above. The previous hub
(2026-10-23), including the dated memory-campaign section, is kept whole in the
[experiment log](experiment_log.md), Part 1. The memory campaign's verdicts live in
[`memory_system/report.md`](../memory_system/report.md) and
[`memory_system/v7/execution_plan/report.md`](../memory_system/v7/execution_plan/report.md): in short, June's memory improved the town's
decisions but not significantly its wins, the v6 store did not repeat it, and the pre-registered v7 endpoint
found no compounding, leaning toward harm; the ten-seat memory has not been tested at scale.*
