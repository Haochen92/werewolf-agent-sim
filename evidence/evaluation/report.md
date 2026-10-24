# Evaluation: what we measure, how, and how far to trust it

*Rewritten 2026-10-23 as the hub for all evaluation (was: the memory pipeline only, July 2026).*

**What this page is.** The hub for evaluation. It explains how every part of the project is checked,
and how far each of those measurements can be trusted.

**The system being checked.** Werewolf, a hidden-role game, played by AI agents. The project adds a
memory of lessons from past games, and a deduction engine that writes conclusions into each player's
prompt. It also has a catalogue of models the players can run on, and a public website.

**Two questions this page keeps apart.**

1. **Does a part work?** For example, does memory improve play? That is answered in the design
   folders, which the first table below names for each subject.
2. **Is the check that judged it any good?** That is answered here.

**Where things live.**

- Each family of checks has its own report. Every one is linked in the status board further down.
- [The ledger (`source_map.md`)](source_map.md) lists every check with its trust mark, where its code
  and its records are, what has changed since July 2026, and the dated results of checking each
  report against the code.
- The frozen cases are recorded separately, in [the tracing report](../tracing/report.md). These are
  saved game moments that the checks replay.

## What is evaluated, and with what

Six subjects are evaluated. Memory is one of them, and since the memory research closed in July 2026
most evaluation work has been on the other five.

| Subject | The question | Main instruments | Design verdict lives in |
|---|---|---|---|
| **Memory** | do stored lessons improve play; are the model-written fields right; does credit mean anything | paired game A/B, decision-replay screen, the LLM-free loop measure and credit validators, memory-component judges, golden labels, field audits | [`memory_system/`](../memory_system/store_progression.md), [`execution_plan/report.md`](../execution_plan/report.md), [`credit/report.md`](../credit/report.md) |
| **Play quality** | do prompt, rule and card changes make the agents argue, vote and talk better | frozen-turn replays, blind packet reads, ten-seat metrics, read Brier score, vote-target counts, same-deal game pairs, balance batches | [`game_play_enhancement/discussion_evidence.md`](../game_play_enhancement/discussion_evidence.md), [`sequential_discussion/`](../sequential_discussion/report.md) |
| **Factual errors** | how often agents state something the game record contradicts, and does a change reduce it | the census (code screen plus model reader), the hallucination bench, pinned-case replays, the summary-claim replay | [`generation_prompt/`](../generation_prompt/validation_plan.md), `discussion_evidence.md` §6 and §8 |
| **The deduction engine** | is every line it injects true in every legal game; does it help the seat | soundness tests over random legal nights, a brute-force oracle, acceptance cases, solver and block censuses, injection and placement replays | [`reasoning_failures/`](../reasoning_failures/report.md) |
| **Models and cost** | can a candidate model play the game's turns; is it worse than the default; what does a game cost | admission probes, bench arms against the default, a thinking-budget replay, seat-model games, cost and cache accounting | [`caching/report.md`](../caching/report.md), [`model_selection/report.md`](../model_selection/report.md), `reasoning_failures/experiment_log.md` |
| **The information boundary** | does any prompt carry another seat's private information | batch leak checks, payload leak tests, the served-game leak audit, information-fidelity pins | [`agent_boundaries/report.md`](../agent_boundaries/report.md) |

A seventh layer, **methodology**, serves all six: drift guards, the arm guard, the runtime fingerprint,
seedability, the power gate and the prompt golden.

**The game changed under the apparatus.** Through July 2026 the game had nine seats, was played by
Gemini flash-lite, and evaluation centred on memory. Since 2026-10-09 the live game has ten seats drawn
from a twelve-role cast. Seats default to Claude Haiku 5.5 (`DEFAULT_GAME_MODEL`,
`Agents/llm_factory/accessors.py`). Memory is off unless the player switches it on for a game
(`server/game/run_config.py`), and lessons come from a Postgres store
(`Agents/memory/persistence/postgres.py`). Most memory instruments describe the nine-seat game; most
play-quality, factual-error and deduction instruments describe the ten-seat game. The status board says
which.

## The one distinction that organizes everything

Every evidence folder braids two threads. This chapter follows one of them.

| Level | Question | A better one means | Home |
|------|----------|--------------------|------|
| **L0 — the design** | does the memory, the deduction engine or a prompt change meet its goal? | a better *design* | the design folders (table above) |
| **L1 — the apparatus** | how do we *measure* whether it meets its goal? | a better *measurement* | **here** |
| **L2 — trust** | is that measurement itself any good: anchored, calibrated, low-noise? | a *more trustworthy* measurement | **here** ([`source_map.md`](source_map.md) marks) |

So a spoke catalogues an **instrument** and rates **its** reliability; it does not re-argue what the
design found. Where a measurement is thin or uncalibrated, **that absence is itself a finding.** It is
why the July wolf-memory null was read as measurement-limited rather than as a ceiling, and why no
ten-seat play score can yet be called validated.

## What the apparatus is good for

The strongest thing to say about this evaluation system is not any single score. It is that **the
apparatus repeatedly caught its own errors.**

In June and July 2026 (nine-seat, memory):
- It discarded a baseline after detecting an epoch shift between runs (Fisher p=0.0028), then made a
  same-epoch fresh baseline mandatory.
- It caught a config slip that had let the memory arm run every faction instead of the town only, and
  turned the check into an arm guard that now fails the run before spending.
- It retracted an inflated engagement metric (about 0.70 to 0.55) once it found the model had been
  silently skipping a third of its inputs.
- It re-ran an investigator proxy that had come out significantly wrong-sign (+0.38, p=0.039, n=30) at
  six times the sample, and found the sign was small-sample noise (+0.15, not significant, N=180).
- It flagged both of its own June paid loop runs as invalid before they could be reported.
- A $0 audit of model-filled memory fields fired its own pre-registered re-open condition: a field the
  retrieval gate keyed on was worse than a constant (0.606 against 0.827 for always-False).
- It refuted part of its own design: a canary showed that pairing arms by deal buys almost no variance
  reduction, so the same-epoch baseline was the load-bearing part all along.

In October 2026 (ten-seat, play, factual errors, models):
- Three leak checkers were found to have been no-ops on every live game, because the batch runner never
  passed them their inputs. That was found on 2026-10-14 and closed the same day.
- A probe found that every memory game had run at a thinking level that produced zero reasoning tokens.
  The runtime fingerprints of 680 records (398 June A/B, 222 loop, 60 endpoint) confirmed it. Both arms
  ran the same way, so the comparisons stand, but every memory verdict is about players that do not
  reason first.
- The bench's first build let a replayed vote turn see its own result. Reading the controls by hand
  caught it before v1, and showed the July ship test had the same leak.
- The admission run's short probes passed DeepSeek V4 Pro 27 of 27, but its real turns came back in
  prose 3 times in 6. The runner now counts real-turn failures in its recommendation.
- A replay screen read an 8-of-10 against 1-of-10 split on an identical prompt as noise, then got a
  stable rate (about one in three) only by shuffling every arm into one schedule at n=25.
- Re-embedding a 232-case calibration set showed that dedup thresholds re-derived for a new embedding
  model would auto-discard two labelled keeps.

Self-correction at this rate, across subjects, is the best evidence the harness is real rather than
decorative.

The second thing: **the apparatus knows which of its instruments to trust.** The trustworthy numbers are
the ones no model decides. These are the code checks (the leak checks, the deduction oracle, the arm
guard, seedability, the embedding canary), exact counts against the game record (vote targets, winners,
structural counts, the LLM-free loop measure), and judgments anchored to people (the dedup golden keys,
the census reader's hand check, hand-written expectations, the deduction acceptance cases). The
nine-seat town proxies, validated against faction win at |r|≈0.6, belong here too, for the nine-seat
game only. Uncalibrated LLM judges and Claude model readers are treated as directional smoke alarms,
not gauges. Knowing the difference is the whole point of the L2 column.

## The ladder: four ways we judge, cheapest first

A single output (a line, a vote, a summary, a stored lesson) is judged on one or more of four rungs.

0. **Code checks with no model** → [`deterministic_audits/report.md`](deterministic_audits/report.md).
   Pass/fail checks or exact counts over prompts, game records and the engine. They cost nothing and have
   no noise. Their limit is scope: a code check finds only a violation of a rule someone wrote down. The
   information boundary and the deduction engine's soundness rest entirely on this rung, because no judge
   can see across thousands of prompts or enumerate every legal deal. Two code checks are homed with
   their subject: the census screen (in the bench spoke) and the dedup golden scorers (in labeling).
1. **LLM judge** → [`llm_judge/report.md`](llm_judge/report.md). One model scores another against a
   rubric. Cheap and fast, and most judges here are uncalibrated. The exceptions are the factual-error
   judges. The census reader was hand-checked in July: all 90 public-message positives were read, and
   sampled precision on private notes was about 0.8. The bench reader had 10 of 12 checked verdicts
   upheld. The golden-expectation judge works from hand-written expectations whose verdicts were read by
   hand. Since 2026-10-12 every judge defaults to Claude Haiku 5.5, the same model the players use.
2. **Sampled or blind read** → [`sampled_human_review/report.md`](sampled_human_review/report.md). Cases
   are drawn and read against a rubric. In July this was the weakest-built rung: no case sampler, no
   durable record. A sampler was built on 2026-07-02 and has never been used for a real review. Since
   October the blind packet read (seeded packets, a hidden key, verdict files, code that unblinds) has
   been the main play-quality instrument. Its readers are Claude subagents, not people. Each item gets
   one reader, agreement between readers has never been measured, and no rubric has been checked against
   the owner's labels.
3. **Golden labels** → [`labeling/report.md`](labeling/report.md), which lists every golden set in the
   project and who labelled it. The gold sets (the dedup decision sets, the census reader's
   23-case set, the owner's census read) are all nine-seat, May to July 2026. Every ten-seat reference
   set is model-read or a hand-written expectation, with no person's check. The labelling pipeline
   produces labels but has no code that measures a panel against a human anchor.

Rungs ①–③ form a calibration chain: golden labels can calibrate the judges and readers below them. In
practice the links are mostly unconnected. The application judge's calibration was designed and never
run, and calibrating the bench judge and the blind readers against the owner is pending. Rung 0 sits
below the chain: it needs no calibration, because it only answers questions that can be written as
rules.

Above the rungs sits the **A/B and instrument layer** that decides "did it work" and keeps the
measurement honest: paired games, frozen-turn replays, play metrics, the hallucination bench, the
memory-field audits, the v7 loop and its credit, model admission, and methodology.

```
        ┌──────────────────────────────────────────────────────────────────┐
 above  │ DECIDING + INSTRUMENT LAYER                                       │
 rungs  │ paired games · frozen-turn replays · play metrics · the bench     │
        │ memory-field audits · v7 loop + credit · model admission          │
        │ methodology (drift guards, arm guard, seedability, power gate)    │
        └──────────────────────────────────────────────────────────────────┘
 subjects ─── memory · play quality · factual errors · deduction engine
              · models and cost · information boundary
 how one output is judged, cheapest first ─────────────────────────────────
   ⓪ code check (no model; exact; only what is encoded)
   → ① LLM judge (cheap; mostly uncalibrated)
   → ② sampled or blind read (Claude readers; one per item)
   → ③ golden labels (people; can calibrate ① and ②)
```

## Choosing the instrument: two rules the record supports

*Added 2026-10-23. Both rules are drawn from instruments described in the spokes; each example names
its source.*

**1. Code checks what has a ground truth it can compute; meaning needs a reader.** A code check (rung 0)
is reliable when the answer is computable from the game state or drawn from a closed vocabulary. Five
kinds recur here:

| Kind | Example | Source |
|---|---|---|
| A structured field against the truth | the vote target, the night pick or the claimed role against the true roles; the legality of a move | [`metrics/`](metrics/report.md), [`replay_screens/`](replay_screens/report.md) |
| A forbidden term in text | a seat id written into a lesson, counted by script; another seat's private information in a prompt | [`deterministic_audits/`](deterministic_audits/report.md); `extraction/post_game/report.md` |
| A number the model wrote, recomputed from the board | players alive was exact in 97% of 6,099 cases; the Vigilante's shots left in 16% of 1,109 | [`deterministic_audits/`](deterministic_audits/report.md) (case 3) |
| A structured claim against the engine's record | claims in the ledger checked against announced deaths, saves and the cast | [`deterministic_audits/`](deterministic_audits/report.md) |
| Format and events | schema validity, length caps, retries, timeouts, the rescue model firing | [`model_admission/`](model_admission/report.md) |

Outside these, code loses. A keyword count of meaning said 32 summaries named a quiet player, and
reading the matches found 4 of 124 (below, failure modes). A regex agreed with the model's addressee
tags on 63% of 30 cases, so tagging went to the model
(`../cross_project_synthesis/deterministic_where_reliable.md`). The prose leak pass is substring
matching, so a paraphrased leak passes ([`deterministic_audits/`](deterministic_audits/report.md)).

**2. When a model screens for a human, set it to catch too much.** A screener makes two errors: a false
alarm (it flags something fine) and a miss (it passes something wrong). When a person checks every
flag, a false alarm costs seconds and a miss is never seen, so the screen is set for recall over
precision. The factual-error census is the worked example
([`factual_errors/`](factual_errors/report.md)): code first flags every unit that names a
dead player, a dead role or a count, so nothing in that scope is skipped; a cheap model reads each flag
as the recall layer; a stronger model re-reads its positives as the precision layer; the owner checks
the result. A sample of the precision layer's rejections is read too, because those are the one place
misses hide: 2 to 3 of 15 were real errors, so the published counts are floors. The cascade's numbers are
only as good as its readers, which is why calibrating them against the owner's labels is on the
pending list.

## Status board

Marks: ✅ sound · 🟡 usable with caveats · ⚠️ smoke-test only · ⏸ design-only · ⛔ underbuilt. Each mark
is the report's own verdict. "9" and "10" mark the nine-seat and ten-seat games. Code and record paths
for every row are in [`source_map.md`](source_map.md).

### Judging one output

The ladder above, one report per rung.

| Report | Subject | What it covers | Trust |
|---|---|---|---|
| [**Deterministic audits**](deterministic_audits/report.md) (rung 0) | information boundary · deduction engine · memory · play quality | batch leak checks on every `run_batch` game; payload leak tests; served-game leak audit; fidelity pins; deduction soundness over 20,000 random legal nights per test and a brute-force oracle; 4 acceptance cases; solver and block censuses; scheduler and whiff record audits (9); pivotal-turn flags (9); embedding canary; model-written memory fields recomputed from the record: search filters (9), stored uses-left count and verdict halo (10) | ✅ leak checks, payload tests, fidelity pins (narrow), deduction soundness and oracle, solver census (one run), canary (batch runner only) · 🟡 served-game audit (built and tested; not running, cron found not installed 2026-10-23), acceptance cases (the only coverage test), block census, record audits · 🟡 stored uses-left count, verdict halo (against an unvalidated grade) · ✅ search-filter recompute, as a record · ⏸ category labels never validated · ⚠️ pivotal-turn flags |
| [**LLM judges**](llm_judge/report.md) (rung ①); notes: [agent decision](llm_judge/agent_decision.md), [extraction](llm_judge/extraction.md), [day summary](llm_judge/day_summary.md), [discussion tagger (retired)](llm_judge/discussion_tagger.md) | memory · play quality · factual errors | every judge in the project by kind: narrow judges against given facts (census reader, expectation judge), in-game judges (echo gate, opening filter, the speakers' accusation tags), labelling at scale (decision tagger, de-halo, point dedup), the memory-era 1–5 rubric judges; what each was checked against; the top-ups for today's game; [detailed record](llm_judge/experiment_log.md) | 🟡 factual-error judges (person-checked, nine-seat, Gemini era) · 🟡 echo gate (blind model readers) · ⚠️ opening filter and accusation tags · ⚠️ memory-era rubric judges (records; none checked against people) |
| [**Sampled and blind reads**](sampled_human_review/report.md) (rung ②) | play quality · memory | outcome-blind case sampler (9); the blind packet protocol, used by seven October screens (10); Phase 3 hand-read games; June discussion-quality gate; v8 retrieval and store reads; decision-tag read (10); credit attribution spot-check | 🟡 blind packet reads (no longer underbuilt; one Claude reader per item, no agreement or owner calibration) · 🟡 failure modes / ⚠️ counts for the hand reads · 🟡 v8 reads · ✅ decision-tag read (98 of 102, above a 90% bar set beforehand; model readers) · ⚠️ spot-check (n=15) · case sampler built, tested, never used (unrated) |
| [**Golden labels**](labeling/report.md) (rung ③); [dedup scorers](labeling/dedup.md) | memory · play quality · factual errors | every golden set in the project, gold or silver, by how it was labelled (a person, a model panel with review, models only, a written expectation); the multi-model labelling pipeline; dedup golden scorers | 🟡 pipeline (calibration half not built) · 🟡 dedup decision scorer (human keys; scores predate v6 and today's models) · 🟡 prefilter sets (65 human labels; the 232 are model labels) · ⚠️ tell-detector cases and readers' duplicate groups (model labels) |
| [**Scales and scores**](scoring/report.md) | all | the scale of one label (binary, categorical, graded, 1–5, pairwise, probability); how a judge is scored against a golden set (precision and recall, kappa, NDCG, Brier); the paired tests for comparing versions | 🟡 standard scores built and used · ⚠️ no score of a 1–5 judge against people |

### Testing a change

How a change is compared with what it replaces.

| Report | Subject | What it covers | Trust |
|---|---|---|---|
| [**Frozen-turn replays**](replay_screens/report.md) | memory · play quality · deduction engine | memory decision-replay screen (9); checkpoint replay (9); tell-book screen (9); stage-filter replay (10); night-1 target check (9); about ten October prompt, wording and deduction-line screens (10); per-day replay design | ✅ decision-replay screen (triage), night-1 target check · 🟡 October screens (direction, not size), checkpoint replay · ⚠️ tell-book, counter-claim and private-note screens · ⏸ per-day replay |
| [**Whole-game evaluation**](whole_game_evaluation/report.md) | memory · play quality | arms paired by game id, paired McNemar and Wilcoxon tests; June memory A/B, v6 strategy-point A/B, pre-registered v7 endpoint (9); persona-voice and evil-cover pairs, 8 deals each (10) | 🟡 nine-seat memory harness (win underpowered, MDE about 36 points; pairing buys almost no variance; the endpoint's paired statistic has no committed code) · ⚠️ ten-seat same-deal pairs |

### Measures and fair comparison

What a score means, and the guards that keep a comparison fair.

| Report | Subject | What it covers | Trust |
|---|---|---|---|
| [**Play metrics**](metrics/report.md) | play quality · memory | nine-seat de-lucked basket validated against win; trust tiering on the push; ten-seat metrics and decision grades; read Brier; vote-target accuracy; leverage anchor; discussion, Phase 2 and balance counts; two prompt-claim checks | ✅ nine-seat town basket (nine-seat only) · 🟡 investigator, town discussion · ⚠️ deceiver · ⚠️ ten-seat metrics and grades (exact, never validated against win) · 🟡 read Brier · ✅ vote-target accuracy as a count · ✅ counts / 🟡 readings (4–31 games, one model) |
| [**Fair comparisons (methodology)**](methodology/report.md) | all subjects | which guards apply to a whole-game A/B and to a frozen-turn replay; drift guards, fingerprint, arm guard, paired stats, manifests; embedding canary (since 2026-07-02); power (MDE) gate; seedability test; prompt golden; run graduation; reasoning-token scope probe | 🟡 overall · ✅ arm guard, in-run fingerprint, power gate, seedability · 🟡 prompt golden (one turn type), reasoning-token probe · ⏸ run graduation (built, never used) · manual: the cross-epoch gate, the $3 canary, checking that a setting produced its behaviour |

### Pipelines

A fixed chain of the methods above, run for a recurring decision.

| Report | Subject | What it covers | Trust |
|---|---|---|---|
| [**Factual errors**](factual_errors/report.md) | factual errors · models | July census (code screen, two-model reader, owner hand check) (9); T1b, T2 and T1c replays (9); the bench, with frozen sets and paired arms; invented-check replay; ten-seat pinned cases; summary-claim replay (10) | ✅ census screen within its scope · ✅ invented-check replay, for its one turn · 🟡 reader, July replays, bench and ten-seat replays, as regression checks not rates · ⛔ no factual-error rate on the ten-seat game |
| [**Model admission and cost**](model_admission/report.md) | models and cost | probe battery (`eval-model-admission`); live schema gate; bench arms against the default; thinking-budget replay; summariser comparison; seat-model games; memory-job model comparisons; July selection; cost and cache accounting | 🟡 usable as a gate, not a ranking (bench spread about 6 points at 70 samples) · 🟡 thinking-budget replay, cost accounting · ⚠️ summariser comparison, seat-model games, memory-job comparisons, live schema gate, July selection |

**Dated records, kept for provenance, not current:** [`loop/`](loop/report.md) (the measurement kit of the v7 learning loop, closed July 2026), [`hardening_pass/`](hardening_pass/report.md) (the July 2026 review of the memory methods). The discussion tagger, a judge retired from credit 2026-07-13 and out of the write-up, is kept as a note in the LLM-judge folder: [`llm_judge/discussion_tagger.md`](llm_judge/discussion_tagger.md). `dimension_extraction/` was dissolved on 2026-10-23: its code checks are in deterministic_audits and its blind read in sampled_human_review.

## Cross-cutting findings

Read across all the spokes, five findings recur, plus a short list of named failure modes.

**1. What can be trusted.** Three kinds of instrument hold up.
- **Code checks.** The batch leak checks have run on every batch game since 2026-06-06. Their one
  confirmed true positive was 109 violations from a refactor, and 0 after the fix. Every "certain" line
  of the deduction engine holds over 20,000 random legal nights per test and against every allowed deal.
  The arm guard and the in-run fingerprint fail a run rather than warn. The limit is what they encode:
  paraphrased leaks and rules nobody wrote down pass.
- **Outcome-anchored or exact scores.** The nine-seat town basket (|r|≈0.55–0.65 against win), exact
  vote-target and winner counts, the LLM-free loop measure, the decision tags against a bar set
  beforehand, and bench sign tests whose effect clears the bench's own noise. Re-judging moved bench
  totals by 1–2 samples of 267, and reruns moved an arm by about 6 points at 70.
- **Goldens.** The dedup decision keys, the census reader's July hand check, the hand-written
  expectations, and the four deduction acceptance cases.

**2. What cannot be trusted as a gauge.**
- The memory-component judges: none has been checked against people.
- The discussion-evidence judge and the summariser comparison judge: no human check.
- The blind model readers. Every October blind read is Claude subagents, one reader per item. When fresh
  readers re-judged the same lines, labels tied to an observable act held exactly (claims 13 and 33),
  while judgment labels moved by several items (29 to 19 of 73 in one evil-cover arm).
- Same-family judging. Every judge now defaults to the players' own model, and the admission runs had
  Gemini judges grading a Gemini reference arm. Neither bias was measured.

**3. Where the anchors are thin.**
- **No validation against win on the ten-seat game.** `VALIDATED_ON_TEN_SEAT_METRICS` is empty, so
  nothing pushes as "validated" (`Agents/compute_metrics.py`). The ten-seat grade table is an owner
  ruling that no one has tested, and the verdict-halo study uses it as truth. Balance was read on
  flash-lite; no balance batch has run on Haiku, the live model.
- **Factual errors.** The only population rate is July and nine-seat: about 3% of public messages (68 of
  2,292) and about 4% of private notes. The census has never run on a ten-seat game, and its screen
  knows only the nine-seat roles. The bench replays day turns only, though July found night notes the
  worst surface (9.6%). The reader's calibration is Gemini-era; the Haiku default has no recorded check.
- **The deduction engine's coverage** rests on four acceptance cases. Soundness is tested at scale;
  completeness is not.
- **Replays.** Ten samples of one case show the spread of answers to one prompt, not ten situations.
  Only a few screens measured their own noise floor.
- **Nine-seat role names in three scorers.** `score_vote`, `read_ledger.py` and the discussion-evidence
  judge's role join run on ten-seat records without error and score the new evil roles as town.
- **Every memory verdict** is about players with zero reasoning tokens.

**4. What is recorded outside version control.**
- `batch_results/` is gitignored. It holds the June A/B data, the v7 build run and endpoint (including
  `PREREG_AMENDMENT.md`), and the v6 games the credit validators read.
- `evaluation/eval_results/` is gitignored. It holds all 20 admission records and the admission bench
  summaries, the bench's screen run, the R1 samples, the note-screen generations and the Haiku vote
  outputs.
- Untracked on 2026-10-23: the solver census runner and output, `reasoning_failures/report.md`, the
  Haiku vote replay runners, config and data, and the two new spokes `deterministic_audits/` and
  `model_admission/` themselves.
- Code not found: the script behind the v7 endpoint's paired statistic, the reasoning-token probe, and a
  round-filter runner named in a README.
- The tool built to close this gap, `eval-graduate`, has graduated nothing.

**5. What is not running.**
- The nightly leak-audit cron is documented but was found not installed on 2026-10-23, so no served game
  is known to have been leak-checked.
- There is no CI. Tests run only when someone runs pytest. The embedding canary runs only inside
  `run_batch`; the server's retrieval never runs it.
- The tests in `tests/` are largely AI-written and unaudited. The spokes cite deliberate tests (the leak
  tests, the deduction oracle, seedability, the prompt golden) and never a test count.

**The failure modes worth naming once:**
- **Flat or saturated judge dimensions** carry no information. Village dynamics was pinned at 5.00, and
  extraction's original five dimensions clustered near the top.
- **Regenerating and judging in one harness** confounds generation with scoring.
- **Outcome halo.** A measure conditioned on whether the side won measures the win. It is now measured
  on the memory itself: the extraction model's verdict follows the side's win about twice as strongly as
  the decision's grade (+0.80 against +0.40 per observation).
- **A setting is not its behaviour.** The record shows what was configured, not what happened. The June
  loop ran every faction while town-only was believed. "Minimal" thinking produced zero reasoning
  tokens. Three leak checkers were configured and checked nothing. Short probes kept the schema's field
  order 17 of 17 times while Haiku's real turns kept it 15 of 24.
- **One case resampled, read as many situations** (the AC2 vote).
- **Keyword counts of meaning.** A keyword count said 32 summaries named a quiet player; reading the
  matches found 4 of 124.
- **A frozen transcript hides the trajectory.** The checkpoint replay could not reproduce the v7 store's
  abstain cascade: abstains ran 12–18% on frozen turns against 31% in live games.

**The cheapest upgrades.** All are on the owner's pending list (`writeup/map.md`, "Evaluation hardening
tasks"), and none is scheduled:
1. One owner labelling session on 50–100 bench verdicts. It calibrates the judge that every prompt and
   model change goes through. A double-read and an owner slice of the silence-calibration readers would
   follow, if their numbers stay in the write-up.
2. Audit the critical tests (rules engine, payload builders, deduction, credit grading, translator), then
   add a pytest CI workflow over the deterministic suite.
3. Install the leak-audit cron. This is an outward change to the host and needs the owner's yes.

The spokes add three small ones: record reasoning tokens per game, move the admission records into
`evidence/`, and give every replay screen a noise floor.

## The memory campaign, as of July 2026

*A dated section, corrected 2026-10-23. The July hub's bottom line is withdrawn: "town play improves
convergently" overstated the record, the discussion tagger no longer credits anything, and v6 is not the
live path.*

Everything below is the nine-seat game, played by `gemini-3.1-flash-lite` with zero reasoning tokens.

- **June memory on/off A/B (30 paired boards).** Memory improved the town's *decisions*. Healers saved
  the real target 37% → 60% (p=0.005), and town lynches hit an enemy 47% → 64% (p=0.028). The town win
  rate rose 27% → 43%, which was not significant (p=0.27). The figure "+17pp, p=0.013" is a fusion
  error: p=0.013 belongs to the reranked arm's +33 points, which carries a model-drift caveat. Wolves and
  the serial killer gained nothing. The decision-replay screen converges with the decision measures, not
  with a win gain. ([`memory_system/store_progression.md`](../memory_system/store_progression.md),
  correction of 2026-10-22.)
- **v6 store (2026-06-17).** The town gain did not repeat (+6 points, p=0.77).
- **v7 (July).** The test was pre-registered (signed 2026-07-16). The build run finished on 2026-07-19
  with a 168-lesson store, at $25.74. On the endpoint (2026-07-20, 30 boards), the town's decision score
  was 0.147 lower with memory (p≈0.06), and lower on 19 of 30 boards. As committed in advance, this was
  reported as "no compounding detected", leaning toward harm
  ([`execution_plan/report.md`](../execution_plan/report.md) §5).
- **The cause was traced to credit's abstain blind spot.** Cautious lessons drove the town's abstains,
  and credit graded every town abstain neutral, so the loop could not prune them. One abstain lesson had
  19 follows and a credit of exactly zero. A fix was built on 2026-07-21 and passed 9 of 12 checks on
  recorded games. A fresh run under the fixed credit was never authorised
  ([`loop/report.md`](loop/report.md)).
- **The owner closed the memory research on 2026-07-21.** No store was promoted. The wolf-direct arm
  never ran and will not.
- **The ten-seat memory (v8, October 2026) has not been tested at scale.** It serves lessons from a
  Postgres store when a player switches memory on. Its credit pass ran once, as a demonstration, on 20
  memory-on games. There is no verdict on it either way.

What the apparatus keeps from the campaign is its method: a pre-registered paired test whose guards
held, and limits it disclosed itself (win underpowered, pairing buying almost no variance, zero
reasoning tokens).

---

*Hub for all evaluation, distilled from the spokes linked above and checked against their records and
the working tree on 2026-10-23. The dated verification results and full code pointers live in
[`source_map.md`](source_map.md). Whether each component actually works, as opposed to how well we can
measure it, lives in the design folders named at the top.*
