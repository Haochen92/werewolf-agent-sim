# Evaluation: the working record

*This keeps whole, as they stood on 2026-10-23 and 24, the two pages rewritten on 2026-10-24: the old hub
(Part 1), with its self-correction list, status board, cross-cutting findings and the dated memory
campaign section, and the old source map (Part 2), with a row per instrument, the July verify-in-code
results and the superseded July sections. The plain overview is [report.md](report.md); the slim source
map is [source_map.md](source_map.md). Since then several folders moved: `replay_screens/` and
`whole_game_evaluation/` into `evaluation_scopes/{turn,game}/`, `sampled_human_review/` into
`labeling/sampled_reads/` (links below were updated to the new paths). Items listed below as untracked
were committed on 2026-10-24. Part 3 keeps the 2026-10-25 hub (one block per method page, with its numbers
and the per-call code paths) as it stood before the hub was rewritten to explain the methods conceptually.*

---

# Part 1. The hub as of 2026-10-24

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
| **Memory** | do stored lessons improve play; are the model-written fields right; does credit mean anything | paired game A/B, decision-replay screen, the LLM-free loop measure and credit validators, memory-component judges, golden labels, field audits | [`memory_system/`](../memory_system/report.md), [`../memory_system/v7/execution_plan/report.md`](../memory_system/v7/execution_plan/report.md), [`credit/report.md`](../credit/report.md) |
| **Play quality** | do prompt, rule and card changes make the agents argue, vote and talk better | frozen-turn replays, blind packet reads, ten-seat metrics, read Brier score, vote-target counts, same-deal game pairs, balance batches | [`gameplay/discussion_evidence.md`](../gameplay/discussion_evidence.md), [`gameplay/discussion/`](../gameplay/discussion/report.md) |
| **Factual errors** | how often agents state something the game record contradicts, and does a change reduce it | the census (code screen plus model reader), the hallucination bench, pinned-case replays, the summary-claim replay | [`gameplay/turn_prompt/`](../gameplay/turn_prompt/validation_plan.md), `discussion_evidence.md` §6 and §8 |
| **The deduction engine** | is every line it injects true in every legal game; does it help the seat | soundness tests over random legal nights, a brute-force oracle, acceptance cases, solver and block censuses, injection and placement replays | [`gameplay/deduction/`](../gameplay/deduction/report.md) |
| **Models and cost** | can a candidate model play the game's turns; is it worse than the default; what does a game cost | admission probes, bench arms against the default, a thinking-budget replay, seat-model games, cost and cache accounting | [`caching/report.md`](../caching/report.md), [`model_selection/report.md`](model_admission/model_selection.md), `gameplay/deduction/experiment_log.md` |
| **The information boundary** | does any prompt carry another seat's private information | batch leak checks, payload leak tests, the served-game leak audit, information-fidelity pins | [`agent_boundaries/report.md`](../agent_boundaries/report.md) |

A seventh layer, **experimental controls** (the A/B testing method), serves all six: drift guards, the arm guard, the runtime fingerprint,
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
2. **Sampled or blind read** → [`labeling/sampled_reads/report.md`](labeling/sampled_reads/report.md). Cases
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
memory-field audits, the v7 loop and its credit, model admission, and experimental controls.

```
        ┌──────────────────────────────────────────────────────────────────┐
 above  │ DECIDING + INSTRUMENT LAYER                                       │
 rungs  │ paired games · frozen-turn replays · play metrics · the bench     │
        │ memory-field audits · v7 loop + credit · model admission          │
        │ experimental controls (drift, arm guard, seedability, power gate) │
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
| A structured field against the truth | the vote target, the night pick or the claimed role against the true roles; the legality of a move | [`metrics/`](metrics/report.md), [`evaluation_scopes/turn/`](evaluation_scopes/turn/report.md) |
| A forbidden term in text | a seat id written into a lesson, counted by script; another seat's private information in a prompt | [`deterministic_audits/`](deterministic_audits/report.md); `extraction/post_game/report.md` |
| A number the model wrote, recomputed from the board | players alive was exact in 97% of 6,099 cases; the Vigilante's shots left in 16% of 1,109 | [`deterministic_audits/`](deterministic_audits/report.md) (case 3) |
| A structured claim against the engine's record | claims in the ledger checked against announced deaths, saves and the cast | [`deterministic_audits/`](deterministic_audits/report.md) |
| Format and events | schema validity, length caps, retries, timeouts, the rescue model firing | [`model_admission/`](model_admission/report.md) |

Outside these, code loses. A keyword count of meaning said 32 summaries named a quiet player, and
reading the matches found 4 of 124 (below, failure modes). A regex agreed with the model's addressee
tags on 63% of 30 cases, so tagging went to the model
(`../../interview_prep/lessons/deterministic_where_reliable.md`). The prose leak pass is substring
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
| [**Sampled and blind reads**](labeling/sampled_reads/report.md) (rung ②) | play quality · memory | outcome-blind case sampler (9); the blind packet protocol, used by seven October screens (10); Phase 3 hand-read games; June discussion-quality gate; v8 retrieval and store reads; decision-tag read (10); credit attribution spot-check | 🟡 blind packet reads (no longer underbuilt; one Claude reader per item, no agreement or owner calibration) · 🟡 failure modes / ⚠️ counts for the hand reads · 🟡 v8 reads · ✅ decision-tag read (98 of 102, above a 90% bar set beforehand; model readers) · ⚠️ spot-check (n=15) · case sampler built, tested, never used (unrated) |
| [**Golden labels**](labeling/report.md) (rung ③); [dedup scorers](labeling/dedup.md) | memory · play quality · factual errors | every golden set in the project, gold or silver, by how it was labelled (a person, a model panel with review, models only, a written expectation); the multi-model labelling pipeline; dedup golden scorers | 🟡 pipeline (calibration half not built) · 🟡 dedup decision scorer (human keys; scores predate v6 and today's models) · 🟡 prefilter sets (65 human labels; the 232 are model labels) · ⚠️ tell-detector cases and readers' duplicate groups (model labels) |
| [**Scales and scores**](scoring/report.md) | all | the scale of one label (binary, categorical, graded, 1–5, pairwise, probability); how a judge is scored against a golden set (precision and recall, kappa, NDCG, Brier); the paired tests for comparing versions | 🟡 standard scores built and used · ⚠️ no score of a 1–5 judge against people |

### Testing a change

How a change is compared with what it replaces.

| Report | Subject | What it covers | Trust |
|---|---|---|---|
| [**Frozen-turn replays**](evaluation_scopes/turn/report.md) | memory · play quality · deduction engine | memory decision-replay screen (9); checkpoint replay (9); tell-book screen (9); stage-filter replay (10); night-1 target check (9); about ten October prompt, wording and deduction-line screens (10); per-day replay design | ✅ decision-replay screen (triage), night-1 target check · 🟡 October screens (direction, not size), checkpoint replay · ⚠️ tell-book, counter-claim and private-note screens · ⏸ per-day replay |
| [**Whole-game evaluation**](evaluation_scopes/game/report.md) | memory · play quality | arms paired by game id, paired McNemar and Wilcoxon tests; June memory A/B, v6 strategy-point A/B, pre-registered v7 endpoint (9); persona-voice and evil-cover pairs, 8 deals each (10) | 🟡 nine-seat memory harness (win underpowered, MDE about 36 points; pairing buys almost no variance; the endpoint's paired statistic has no committed code) · ⚠️ ten-seat same-deal pairs |

### Measures and fair comparison

What a score means, and the guards that keep a comparison fair.

| Report | Subject | What it covers | Trust |
|---|---|---|---|
| [**Play metrics**](metrics/report.md) | play quality · memory | decisions graded by the rules against the true roles; each score checked against its side's win, on the nine-seat game (June–July) and the ten-seat game (78 games, 2026-10-24); read Brier; vote-target accuracy; discussion, Phase 2 and balance counts | ✅ town lynch scores, power roles lost, wolf blending (both games) · ❌ healer save rate on ten seats · 🟡 new roles' scores (rule-graded, too few games) · ⚠️ ten-seat decision grades as a whole · 🟡 read Brier · ✅ counts / 🟡 readings (4–31 games, one model) |
| [**A/B testing (experimental controls)**](experimental_controls/report.md) | all subjects | which guards apply to a whole-game A/B and to a frozen-turn replay; drift guards, fingerprint, arm guard, paired stats, manifests; embedding canary (since 2026-07-02); power (MDE) gate; seedability test; prompt golden; run graduation; reasoning-token scope probe | 🟡 overall · ✅ arm guard, in-run fingerprint, power gate, seedability · 🟡 prompt golden (one turn type), reasoning-token probe · ⏸ run graduation (built, never used) · manual: the cross-epoch gate, the $3 canary, checking that a setting produced its behaviour |

### Pipelines

A fixed chain of the methods above, run for a recurring decision.

| Report | Subject | What it covers | Trust |
|---|---|---|---|
| [**Factual errors**](factual_errors/report.md) | factual errors · models | July census (code screen, two-model reader, owner hand check) (9); T1b, T2 and T1c replays (9); the bench, with frozen sets and paired arms; invented-check replay; ten-seat pinned cases; summary-claim replay (10) | ✅ census screen within its scope · ✅ invented-check replay, for its one turn · 🟡 reader, July replays, bench and ten-seat replays, as regression checks not rates · ⛔ no factual-error rate on the ten-seat game |
| [**Model admission and cost**](model_admission/report.md) | models and cost | three checks in order: test prompts (`eval-model-admission`), a replay of saved turns against the default model, real games; live schema gate; thinking level for votes; summariser comparison; memory-job model comparisons; July selection; cost and cache accounting | 🟡 usable as a gate, not a ranking (replay spread about 6 points at 70 samples) · 🟡 thinking-budget replay, cost accounting · ⚠️ summariser comparison, seat-model games, memory-job comparisons, live schema gate, July selection |

**Dated records, kept for provenance, not current:** [`loop/`](loop/report.md) (the measurement kit of the v7 learning loop, closed July 2026), [`hardening_pass/`](hardening_pass/report.md) (the July 2026 review of the memory methods). The discussion tagger, a judge retired from credit 2026-07-13 and out of the write-up, is kept as a note in the LLM-judge folder: [`llm_judge/discussion_tagger.md`](llm_judge/discussion_tagger.md). `dimension_extraction/` was dissolved on 2026-10-23: its code checks are in deterministic_audits and its blind read in labeling/sampled_reads.

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
- Untracked on 2026-10-23: the solver census runner and output, `gameplay/deduction/report.md`, the
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

**The cheapest upgrades.** All are on the owner's pending list (`writeup/_planning/map.md`, "Evaluation hardening
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
  with a win gain. ([`memory_system/report.md`](../memory_system/report.md),
  correction of 2026-10-22.)
- **v6 store (2026-06-17).** The town gain did not repeat (+6 points, p=0.77).
- **v7 (July).** The test was pre-registered (signed 2026-07-16). The build run finished on 2026-07-19
  with a 168-lesson store, at $25.74. On the endpoint (2026-07-20, 30 boards), the town's decision score
  was 0.147 lower with memory (p≈0.06), and lower on 19 of 30 boards. As committed in advance, this was
  reported as "no compounding detected", leaning toward harm
  ([`../memory_system/v7/execution_plan/report.md`](../memory_system/v7/execution_plan/report.md) §5).
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


---

# Part 2. The source map as of 2026-10-24

*Rewritten 2026-10-23 as the ledger for all evaluation, beside the hub (was: the memory pipeline's
inventory, written 2026-06-27, verified in code 2026-06-28, paths updated 2026-07-02).*

> **What this is.** The receipts behind [`report.md`](report.md). For every instrument it gives the code,
> the record, the game it ran on, its trust mark and what changed since July. The marks come from the
> spokes; this file sets none of its own. Where a spoke rates parts of one instrument differently, the
> row says so.
>
> **Where things live (settled).** `evaluation/` holds the code and `evidence/` holds the record. The data
> plane between them is `evaluation/{config,frozen_eval_sets,eval_results}/` and `batch_results/`
> (`CLAUDE.md`, "Eval Architecture"; `evaluation/README.md`, Data plane). The July note calling this
> folder provisional is withdrawn.
>
> **Paths.** Code paths are from the repo root. Record paths are from `evidence/`. Paths and statuses
> were checked against the working tree on 2026-10-23 (branch `feature-frontend-v1`, HEAD `1a5c0da1`,
> with uncommitted edits in `Agents/deduction/`). The July verify-in-code results are kept as a dated
> record at the end, each with its status today.

## Legend

**Trust marks (current, the hub's):** ✅ sound · 🟡 usable with caveats · ⚠️ smoke-test only · ⏸
design-only (or built and never used, where the row says so) · ⛔ underbuilt · "—" no mark in any spoke.

**July marks**, kept in the dated sections: ✅ VALIDATED · 🟡 PARTIAL · ⚠️ CLAIMED-UNVERIFIED · 🔴
WEAK/NULL · ⏸ DEFERRED · 🔍 NEEDS-CODE-READ. 🔴 has no current equivalent. July 🔴 rows now carry the
spoke's ⚠️ or 🟡, or are recorded as a result rather than an instrument mark.

**Since July:** **new** (not in the July map) · **moved** (code path changed) · **re-rated** (mark
changed) · **fixed** · **retired** · **same**.

**Game:** 9 = the nine-seat game (through July 2026); 10 = the ten-seat game (live since 2026-10-09).

**Tests** named below are cited for what they pin. The suite is largely AI-written and unaudited, so a
passing test is not evidence of quality.

## The spine

```
Data plane         frozen cases · batch records · captures · checkpoints → sampled sets
Rung 0             code checks, no model                        (deterministic_audits/)
Rung ①             LLM judges                                    (llm_judge/)
Rung ②             sampled and blind reads                       (labeling/sampled_reads/)
Rung ③             golden labels                                 (labeling/)
Instrument layer   factual errors · replays · paired games · metrics · memory-field
                   audits · v7 loop · methodology · model admission and cost
Records            hardening pass (July) · discussion tagger (retired) · archive
```

---

## Data plane (the input substrate)

Mostly the capture side's output; listed because every instrument reads it. Marks here are July's and
no spoke re-rates them.

| Piece | Code | Game | Mark | Since July / notes |
|---|---|---|---|---|
| Frozen-set builders | `evaluation/src/data/builders/{agent_decision,extraction,dedup,hallucination_bench}.py` (`eval-build-dataset` at `pyproject.toml:39`, `eval-build-{extraction,dedup}-dataset`, `eval-build-hallucination-bench`) → `evaluation/frozen_eval_sets/<id>.jsonl` + manifest | both | July ✅ | **moved** (was `experiments/dataset_builder.py`). Tests `tests/evaluation/test_{eval_case_sink,local_case_source,langfuse_fetch}.py` |
| Stratified sampling | `evaluation/src/data/sampling.py` (`sample_cases`); test `tests/evaluation/test_sampling.py` | 9 | July ✅ | same. Default day-only. Also the cohort step of the case sampler |
| Converters and sources | `evaluation/src/data/{converters,sources}/`, `frozen_sets.py`, `batch_layout.py`; `sources/replay_api.py` (served games through the public replay endpoint) | both | July ✅/🟡 | **new**: `replay_api.py`, `batch_records.py`. Old formats in `evaluation/src/archive/legacy_cases.py` |
| Live-game checkpoints | `evaluation/experiments/haiku_game_turn_cases.py` (`day_states`; reads the server's Postgres without writing) | 10 | — | **new**. Case source for most October replays |
| Captures | `*.capture.json.gz` from the capture runners in `evaluation/experiments/`; served games' `prompt_captures` (`server/storage/prompt_captures.py`) | 10 | — | **new**. Source for the evil-cover and counter-claim screens and the block census |
| Provenance manifest | `evaluation/src/core/manifest.py`; test `tests/evaluation/test_manifest.py` | both | July ✅ | same. Methodology spoke: "drift-evident provenance, not byte-for-byte reproducibility" (`tracing/fingerprinting/report.md` §1, §5) |
| Cost estimates | `evaluation/src/core/costs.py` | both | 🟡 (model admission §9) | **changed**: prices now come from the model catalogue (`costs.py:13-14`). The 4-characters-per-token estimate remains (`costs.py:16`) |

---

## Rung 0 — code checks with no model (new)

Spoke: [`deterministic_audits/report.md`](deterministic_audits/report.md). The July map had no rung 0. The
embedding canary was built on 2026-07-02, superseding the July line that alias drift was undetectable.

| Instrument | Code | Record | Game | Mark | Since July / notes |
|---|---|---|---|---|---|
| Batch leak checks | `tests/leak_test.py` (`run_leak_tests`, `leak_inputs`); wired in `scripts/run_batch.py` and the capture runners | `agent_boundaries/report.md` §3–5, `experiment_log.md`, `leakwire_smoke.log`, `leakfix_smoke.log` | both | ✅ | **new**. Nine checks per game. One true positive (109 → 0, 2026-06-06). Three checkers were no-ops on live games until 2026-10-14 |
| Payload leak tests | `tests/engine/test_{round,night}_payload_leaks.py`, `test_wolf_channel_day_visibility.py`, `test_night_whiff_disclosure.py` | `agent_boundaries/report.md` §3, §5 | 10 | ✅ | **new**. Each plants a leak and asserts the check catches it |
| Served-game leak audit | `server/housekeeping/leak_audit.py`, `server/storage/prompt_captures.py`; `tests/server/test_leak_audit.py` | `agent_boundaries/report.md` §3, §5; `server/README.md`; cron status `writeup/_planning/map.md` | 10 | 🟡 | **new**. Built and tested. The cron was found not installed on 2026-10-23 (no crontab entry, no log); no served game is known to have been audited |
| Information-fidelity pins | `tests/engine/test_information_fidelity.py` | `gameplay/discussion_evidence.md` §6.4–6.5; `evaluation/factual_errors/experiment_log.md` §8 | 10 | ✅ (narrow) | **new**. Module docstring on held drafts is stale; the test asserts the current rule |
| Deduction soundness, random nights | `tests/engine/deduction/test_{own_results,public_events,candidates,conditionals}.py`; `tests/factories/{random_nights,random_claims}.py` | `gameplay/deduction/report.md` §2, §4; `gameplay/deduction/deduction_catalogue.md` "Build verification", "Build status" | 10 | ✅ | **new**. 20,000 nights per test at fixed seeds. Mutation checks at build were one-time |
| Brute-force oracle and metamorphic leak test | `tests/factories/role_assignments.py`; `test_candidates.py`, `test_own_results.py`, `test_role_traits.py` | same | 10 | ✅ | **new**. Oracle and engine share the written rules, so a fact neither encodes is invisible to both |
| Acceptance cases AC1–AC4 | `tests/engine/deduction/test_acceptance.py` | catalogue "Acceptance cases" | 10 | 🟡 | **new**. The only test of coverage; four hand-written goldens |
| Solver census | `evaluation/experiments/deduction_solver_census.py` (untracked) | `gameplay/deduction/data/solver_census/census.json` (untracked); `gameplay/deduction/report.md` §4 (untracked) | 10 | ✅ (one run) | **new**. 150 games, 3,408 seat views, 0 misses. Commit `e765a18e`, dirty |
| Block census | `evaluation/experiments/deduction_block_census.py` | `gameplay/deduction/data/deduction_block_census/`; catalogue slice 8 | 10 | 🟡 | **new**. 278 turns over 4 games, 2026-10-18; not re-run since slice 17 |
| Scheduler access audit | `evaluation/src/audits/scheduler_access_audit.py`; `tests/evaluation/test_scheduler_access_audit.py` | `metrics/metrics_audit/scheduler_bias_log.md` §3 A–C | 9 | 🟡 | **new** to this map. Hard-codes nine-seat roles and fields |
| Whiff conversion audit | `evaluation/src/audits/whiff_conversion_audit.py`; `tests/evaluation/test_whiff_conversion_audit.py` | `scheduler_bias_log.md` ③.E | 9 | 🟡 | **new** to this map. Its premise no longer holds since the failed kill is disclosed |
| Pivotal-turn flags | `evaluation/src/audits/recall_flags.py` | `memory_system/v7/extraction_coverage_ab_spec.md`; `memory_system/v7/experiment_log.md` | 9 | ⚠️ | **re-rated** (July: diagnosis-funnel step 1, unrated). Never validated as a definition; no tests |
| Embedding canary | `evaluation/src/audits/embedding_canary.py`, `embedding_canary_pins.json`; call site `scripts/run_batch.py` | `evaluation/hardening_pass/experiment_log.md` §4.9 | both | ✅ (batch only) | **new**. Pins re-made 2026-07-16 and 2026-10-12 (`qwen/qwen3-embedding-8b`). The server never runs it. No record of it firing |

Code checks homed elsewhere: the census screen (factual errors), the dedup golden scorers (rung ③), the
arm guard, fingerprint, seedability and prompt golden (methodology), and the summary-claim replay's
field checks (factual errors).

---

## Rung ① — LLM judges

Spoke: [`llm_judge/report.md`](llm_judge/report.md). The shared default is
`DEFAULT_JUDGE_MODEL = "anthropic/claude-haiku-5-5"` (`evaluation/src/judges/config.py:15`, owner
2026-10-12, commit `e70f1627`). Players and the in-game gates default to the same model. Every recorded
memory-judge score came from Gemini judges and cannot be compared with a re-run on Haiku. The spoke rates
the memory-component judges ⚠️ as a group; its per-judge table keeps the July tags, given in brackets.

| Judge | Code | Record | Game | Mark | Since July / notes |
|---|---|---|---|---|---|
| Situation-summary (pairwise + rubric) | `evaluation/src/judges/situation_summary{,_pairwise}.py`; `evaluation/src/cli_runner/regen_replay/both/situation_summary_{pairwise,rubric}.py` (`eval-summary`, `eval-summary-rubric`); `evaluation/src/replay/situation_summary.py` | `extraction/situation_summary/`; `evaluation/llm_judge/agent_decision.md` | 9 | ⚠️ (July 🟡) | **moved**, **re-rated**. A golden retrieval key exists, not wired to the judge |
| Retrieval | `judges/retrieval.py`; `cli_runner/regen_replay/both/retrieval.py` (`eval-retrieval`); `replay/retrieval.py` | `retrieval/`; `agent_decision.md` | 9 | ⚠️ (July 🔴 in the spoke's table, 🟡 here) | **moved**, **fixed**: fallback rows carry `is_fallback` (`judges/retrieval.py:30`) and are excluded from every average (`both/retrieval.py:97-110`; `tests/evaluation/test_retrieval_judge_fallback.py`) |
| Application and adherence | `judges/turn_action.py`; `cli_runner/regen_replay/both/turn_eval.py` (`eval-application`); `replay/turn_action.py`; `evaluation/src/loop/memory_adherence.py` | `memory_system/strategy_adoption/{report,judge_validation_protocol}.md` | 9 | ⏸ calibration never run | **moved**. Still uncalibrated; no longer gates anything |
| Extraction | `judges/extraction.py`; `cli_runner/regen_replay/judge/extraction_judge.py` (`eval-extraction`, `pyproject.toml:49`); `evaluation/src/archive/per_role_extraction.py` | `extraction/post_game/`; `evaluation/llm_judge/extraction.md` | 9 | ⚠️ (July 🟡, de-bugged not calibrated) | **moved**. v7 synthesis unjudged |
| Dedup quality (online, batch) | `judges/{dedup,batch_dedup}.py`; `cli_runner/regen_replay/judge/dedup_judge.py` (`eval-dedup`), `both/batch_dedup_judge.py` (`eval-batch-dedup`) | `evaluation/labeling/dedup.md`; `dedup/` | 9 | ⚠️ | **moved**. `batch_dedup.py` swallow-all fix of 2026-06-28 (not re-checked) |
| Day-summary | `judges/day_summary.py`; `cli_runner/regen_replay/both/day_summary_judge.py` (`eval-day-summary`) | `extraction/day_summary/experiment_log.md`; `evaluation/llm_judge/day_summary.md` | 9 | ⚠️ smoke test | **moved** |
| Turn-pipeline | `judges/turn_pipeline.py` (`eval-turn`, `eval-e2e`) | — | 9 | ⚠️ (group) | **new** to this map |
| Census and bench reader | `judges/role_fact_read.py` (`eval-role-hallucination-read`) | `gameplay/turn_prompt/validation/hallucination_baseline.md`; `discussion_evidence.md` §6.6 | 9 cases | 🟡 | **new**. Owner hand check 2026-07-08 on the Gemini cascade; 10 of 12 bench verdicts upheld; no record of the 23-case gate on Haiku |
| Golden-expectation | `judges/golden_expectation.py` | `discussion_evidence.md` §8.4–8.7 | both | 🟡 | **new**. Expectations hand-written; verdicts read by hand; no agreement rate |
| Discussion-evidence | `evaluation/experiments/discussion_evidence.py` (`judge`) | `discussion_evidence.md` §4–6, §7.1, §9; `gameplay/data/{baseline_smoke,live_baseline,live_v2,live_v2_game2}/`, `data/phase2_step8_games/judge/` | 9 | ⚠️ | **new**. Every "check:" line in the review sheets blank. Role join is nine-seat only |
| Echo gate and offline checks | `Agents/turn/echo_gate.py`; `evaluation/experiments/line_echo_gate_check.py`, `silence_calibration.py` (`gate_check`) | `gameplay/data/{line_echo_check,round_echo_check,silence_calibration}/`; `discussion_evidence.md` §7.4 | 9 → 10 | 🟡 | **new**. As shipped: held 10 of 29 restatements, 0 of 36 worthwhile lines, against four blind Sonnet readers. Its June predecessor, the standalone novelty label, separated constructed pure-restatement from genuinely new probes 20 of 20 both ways (`gameplay/discussion/experiment_log.md`, Smoke 2, 2026-06-01): labelled by construction, an upper bound. `round_echo_filter_check.py`, named in a README, is not in the repo |
| Opening filter | `Agents/turn/round_filter.py` | `gameplay/data/silence_calibration/README.md` | 10 | ⚠️ | **new** |
| Decision tagger | `scripts/tag_observation_decisions.py` | `memory_system/v8/data/decision_tags/` | 10 | ✅ in labeling/sampled_reads (beat a pre-set bar) · 🟡 in llm_judge §7 (model readers only) | **new**. The two spokes differ; see rung ③ note below |
| De-halo pass | `Agents/memory/extraction/dehalo.py` | `memory_system/v8/decisions.md` §13; `memory_system/v8/data/dehalo_compare/` | 10 | ⚠️ | **new**. Checked against the deterministic grade, not people |
| Point-dedup judge (v8 synthesis) | via `evaluation/experiments/v8_sp_dedup_dry_run.py` | `memory_system/v8/experiment_log.md` | 10 | ⚠️ | **new** |
| Summariser comparison judge | `evaluation/experiments/haiku_summary_compare.py` (Sonnet 5.5) | `gameplay/deduction/experiment_log.md` §3 | 10 | ⚠️ | **new**. First judging invalid (judge saw the moderator's line); rerun |

The criticality and forced-schema screens use no judge; they are replays (below).

---

## Rung ② — sampled and blind reads

Spoke: [`labeling/sampled_reads/report.md`](labeling/sampled_reads/report.md). Readers are Claude subagents
(Sonnet or Opus) unless a row says otherwise. July rated this rung ⛔ underbuilt; the spoke now rates it
🟡.

| Instrument | Code | Record | Game | Mark | Since July / notes |
|---|---|---|---|---|---|
| Case sampler | `evaluation/src/diagnosis/sampler.py`; `evaluation/src/cli_runner/diagnosis/case_sampler.py` (`eval-case-sample`); `tests/evaluation/test_diagnosis_sampler.py` | `evaluation/labeling/sampled_reads/{plan.md,sampler_smoke/}`; `writeup/_planning/triage.md` row 68 | 9 | unrated (built, tested, never used) | **new**: the July "planned build" (below), built 2026-07-02. `assert_outcome_blind` raises on outcome-named signals |
| Blind packet reads | runners in `evaluation/experiments/`: `silence_calibration`, `evil_cover_screen`, `voice_rewrite_screen`, `persona_line_screen`, `visit_wording_cases`, `note_prompt_cases`, `deduction_placement_screen` | their `gameplay/data/` and `gameplay/deduction/data/` folders (packets, keys, verdicts) | 10 | 🟡 | **new**. One reader per item; agreement never measured; no owner calibration |
| Phase 3 hand-read games | `evaluation/experiments/phase3_render_transcript.py` | `gameplay/data/phase3_reads/README.md` | 10 | 🟡 failure modes · ⚠️ counts | **new**. Not blind; rubric and reader reports not kept |
| Discussion-quality gate | `evidence/gameplay/discussion/quality_gate/scripts/metrics.py` (study code in the record) | `gameplay/discussion/quality_gate/{experiment_log,rubric}.md` | eight-seat | 🟡 structural claim · ⚠️ deltas | **new**. Read by the implementer, arm known |
| v8 retrieval and store reads | `evaluation/experiments/{v8_gate_lookups,v8_reextract_reads}.py` | `memory_system/v8/experiment_log.md`; `memory_system/v8/data/{gate,reextract}/` | 10 | 🟡 | **new**. The planned owner pass after the subagents was not found |
| Credit attribution spot-check | — (sampling recorded in the file) | `credit/attribution_spot_check.json`; `credit/report.md` §5 | 9 | ⚠️ | **new**. 13 of 15; true mismatch could be up to about 36% |

---

## Rung ③ — golden labels

Spoke: [`labeling/report.md`](labeling/report.md); dedup scorers in [`labeling/dedup.md`](labeling/dedup.md).

| Instrument | Code | Record | Game | Mark | Since July / notes |
|---|---|---|---|---|---|
| Labelling pipeline | `evaluation/src/labeling/{engine,voter,exporter,base,config,pipeline}.py`, `adapters/`, `dedup_golden_builder.py`, `manual_labelers/`; `tests/evaluation/test_labeling_pipeline.py`, `test_dedup_golden_builder.py` | `evaluation/labeling/{report,plan,experiment_log}.md` | 9 | 🟡 | **moved** (test path). No `calibration.py`; none of the seven gaps closed. `dedup_golden_builder` default moved to Haiku 5.5 on 2026-10-12; no golden minted with it |
| NDCG and reranker scorers | `evaluation/src/labeling/label_scorer/` (`situation_retrieval_ndcg`, `reranker_comparison`, …) | `llm_judge/golden_set_method.md`; `fine_tuning/cross_encoder/reranker/` | 9 | part of the pipeline row | **moved** into the labelling package. Situation golden: about 20 human cases, the rest machine-added; not wired to the judge |
| Dedup golden scorers | `evaluation/src/audits/{dedup_score,batch_dedup_score}.py` (`eval-dedup-score`) | `evaluation/labeling/dedup.md`; `evaluation/frozen_eval_sets/dedup_v2_golden_labels.json` | 9 | 🟡 | same. 65 online / 111 batch human keys. Scores predate v6, the Vertex shift and the Haiku default. `dedup.md` still cites old `evaluation/src/experiments/` paths |
| Prefilter calibration sets | `evaluation/src/studies/{eval_auto_dedup,auto_dedup_dataset_builder,batch_dedup_merge_eval}.py`; `scripts/sweep_2d_thresholds.py`; `evaluation/experiments/prefilter_similarity_exhibit.py` | `dedup/embedding_prefilter/experiment_log.md`; `memory_system/v8/data/embedder_migration/` | 9 content | 🟡 | **new** to this map. 65 human labels; the 232-case set is model-labelled. Qwen thresholds fail on the 232 |
| Tell-detector cases | `evaluation/src/loop/tells.py`; probes frozen in `extraction/tell_extraction/scripts/` | `extraction/tell_extraction/report.md` §4, `experiment_log.md` ⑧ ⑩ ⑪; `outputs/owner_golden/` | 9 | ⚠️ | **new**. 40 cases by five Opus adjudicators; one game owner-checked (7 of 8) |
| Readers' duplicate groups | `evaluation/experiments/v8_sp_dedup_dry_run.py` | `memory_system/v8/data/reextract/{points,dedup_dry_run}/` | 10 | ⚠️ | **new**. One pass by model readers; applied as labels without a check |

---

## Instrument layer

### Factual errors

Spoke: [`factual_errors/report.md`](factual_errors/report.md). All **new** to this map. The run
templates under `evaluation/config/template/hallucination_bench_*.json` were edited on 2026-10-12 to
Haiku judges, so they no longer reproduce their recorded runs.

| Instrument | Code | Record | Game | Mark |
|---|---|---|---|---|
| Census screen | `evaluation/src/audits/role_hallucination_screen.py` (`eval-role-hallucination`) | `gameplay/turn_prompt/validation/hallucination_baseline.md` | 9 | ✅ within its scope (`ROLE_ALIASES` holds the six nine-seat roles only) |
| Census reader | see rung ① | same | 9 | 🟡 |
| T1b counterfactual replay | `gameplay/turn_prompt/validation/t1b_replay.py` (frozen study code) | `gameplay/turn_prompt/validation/t1b_results.md` | 9 | ⚠️ no power per case |
| T2 regression replay | `gameplay/turn_prompt/validation/regression_replay.py` (frozen) | `gameplay/turn_prompt/validation/t2_results.md` | 9 | 🟡 |
| T1c ship test | `gameplay/turn_prompt/validation/t1c_ab_replay.py` (frozen) | `gameplay/turn_prompt/experiment_log.md` §12; `validation/t1c{,2}_outputs.jsonl` | 9 | 🟡 (vote turns saw their result) |
| The bench | `evaluation/src/cli_runner/regen_replay/both/hallucination_bench.py` (`eval-hallucination-bench`); `evaluation/src/data/builders/hallucination_bench.py`; `evaluation/src/replay/hallucination_bench.py`; `evaluation/frozen_eval_sets/hallucination_bench_v{1,2}.jsonl` (125, 129 cases) | this spoke; its `experiment_log.md` §8–9 (the code audit and fix check, folded in 2026-10-23); `discussion_evidence.md` §6.5–6.7; screen run `evaluation/eval_results/hallucination_bench/screen_v1/` (gitignored) | 9 cases | 🟡 (day turns only) |
| Invented-check replay | `evaluation/experiments/investigator_claim_replay.py` | `gameplay/data/investigator_replay/` (no README); `discussion_evidence.md` §6.2 | 9 | ✅ for that one turn |
| Ten-seat pinned cases | `evaluation/experiments/{phase3_turn_cases,haiku_game_turn_cases}.py`; configs `evaluation/config/hallucination_bench_phase3_*.json`, `hallucination_bench_haiku_game{,_vote_v2}.json` | `gameplay/data/{phase3_turn_replay,haiku_turn_replay}/`; `discussion_evidence.md` §8.4, §8.6 | 10 | 🟡 regression only |
| Summary-claim replay | `evaluation/experiments/summary_claim_replay.py` | `gameplay/data/phase3_summary_replay/` | 10 | 🟡 regression only |
| Ten-seat population rate | — | — | 10 | ⛔ none exists |

### Frozen-turn replays

Spoke: [`evaluation_scopes/turn/report.md`](evaluation_scopes/turn/report.md). Shared engine for the October screens:
`evaluation/src/replay/hallucination_bench.py` (`turn_payload`, `turn_template`, `hydrate_state`).

| Instrument | Code | Record | Game | Mark | Since July / notes |
|---|---|---|---|---|---|
| Decision-replay screen | `evaluation/src/studies/decision_replay.py`; engine `evaluation/src/replay/decision_screen/`; lenses `Agents/memory/consolidation/decision_scoring.py` (shim `evaluation/src/loop/decision_scoring.py`) | `memory_system/effectiveness/decision_replay/` | 9 | ✅ triage | **moved** (was `experiments/studies/`). Converges with June's decision measures, not a win gain. Reruns need a `phase2-baseline` checkout |
| Checkpoint replay | `evaluation/src/replay/decision_screen/checkpoint_replay.py` (`eval-checkpoint-replay`) | `credit/blindspot_fix/experiment_log.md` ④–④d | 9 | 🟡 | **new**. Never run on generation snapshots; model not in the manifest |
| Tell-book screen | `evaluation/src/replay/decision_screen/tell_book_screen.py` | `extraction/tell_extraction/experiment_log.md` ⑫ | 9 | ⚠️ | **new** |
| Stage-filter replay | `evaluation/experiments/v8_stage_filter_replay.py` | `memory_system/v8/experiment_log.md`; `data/gate/stage_filter{,_40games}/` | 10 | 🟡 | **new** |
| Criticality screen | `evaluation/src/studies/criticality_screen.py` | `extraction/situation_dimensions/criticality_screen/` | 9 | — (July 🔴: the result, within ±0.03 noise) | **moved**. No judge; scored by `hit_threat` |
| Forced-schema screen | `evaluation/src/studies/forced_schema_screen.py`; `evaluation/src/instrument_validation/dimensions/dimension_gating_screen.py` | `memory_system/strategy_adoption/forced_schema_screen/experiment_log.md` | 9 | — (July 🟡 directional) | **moved** |
| Night-1 target check | `evaluation/experiments/night1_target_bias_check.py` | `gameplay/data/night1_target_bias/`; `discussion_evidence.md` §7.5 | 9 | ✅ | **new** |
| Evil cover screen | `evaluation/experiments/evil_cover_screen.py` | `gameplay/data/evil_cover_screen/` | 10 | 🟡 | **new** |
| Private-note screen | `evaluation/experiments/note_prompt_cases.py` | `gameplay/deduction/experiment_log.md` §6; `gameplay/deduction/data/note_prompt/`; generations in `eval_results/note_prompt_screen/` (gitignored) | 10 | ⚠️ | **new** |
| Haiku vote replay | `evaluation/experiments/haiku_vote_{cases,score}.py` (untracked); `evaluation/config/hallucination_bench_haiku_vote_compare.json` (untracked) | `discussion_evidence.md` §8.7; `data/haiku_vote_replay/`, `data/haiku_sentinel_vote/` (untracked) | 10 | 🟡 | **new** |
| Visit-wording A/B | `evaluation/experiments/visit_wording_cases.py` | `gameplay/data/visit_wording_ab/` | 10 | 🟡 | **new** |
| Persona line screen | `evaluation/experiments/persona_line_screen.py` | `gameplay/data/persona_line/` | 10 | 🟡 | **new**. The one screen with a designed noise baseline |
| Voice rewrite screen | `evaluation/experiments/voice_rewrite_screen.py` | `gameplay/data/voice_rewrite/` | 10 | 🟡 | **new** |
| Deduction injection (R1) | `evaluation/experiments/deduction_injection_{cases,score}.py` | `gameplay/deduction/experiment_log.md` §4–5; `gameplay/deduction/data/deduction_injection/`; samples in `eval_results/hallucination_bench/{deduction_injection,healer_silence}/` (gitignored) | 10 | 🟡 | **new** |
| Placement and AC2 series | `evaluation/experiments/deduction_placement_screen.py`, `deduction_ac2_{ablation,2x2,closing_fixed}.py` | `gameplay/deduction/data/deduction_placement{,_n10}/`, `deduction_ac2_*/` | 10 | 🟡 | **new**. Uncommitted trees, diff hashed |
| Counter-claim vote screen | `evaluation/experiments/counter_claim_vote_screen.py` | `gameplay/data/counter_claim_votes/` | 10 | ⚠️ | **new**. The engine change was never committed; cannot rerun at HEAD |
| Per-day replay | none | `memory_system/effectiveness/day_replay/design.md` | 9 | ⏸ | same (still not built) |

### Paired game A/B

Spoke: [`evaluation_scopes/game/report.md`](evaluation_scopes/game/report.md).

| Instrument | Code | Record | Game | Mark | Since July / notes |
|---|---|---|---|---|---|
| June memory on/off A/B | `scripts/run_batch.py`, `scripts/make_ab_seed_set.py`; `evidence/memory_system/effectiveness/paired_ab/analyze_ab.py`, `evidence/memory_system/effectiveness/regenerate_stats.py`; `evaluation/src/core/stats.py` | `memory_system/effectiveness/paired_ab/{report,experiment_log}.md`; `memory_system/report.md` (correction 2026-10-22); data `batch_results/ab_*.jsonl` (gitignored) | 9 | 🟡 | **re-rated** (July ✅ VALIDATED). The headline is corrected: decisions improved (healer saves p=0.005, correct eliminations p=0.028, Wilcoxon), wins did not significantly (p=0.27). Never pair "+17pp" with p=0.013 |
| Older does-memory-help batches | `run_batch` arms | `memory_system/effectiveness/report.md` | 9 | July ⚠️ | same; not re-examined. Batch A 70 → 97% not replicated in Batch B; the 23-point swing was a store and namespace confound |
| v6 strategy-point A/B | `evidence/memory_system/effectiveness/v6_sp_ab/launch_arms.sh`; `scripts/run_batch.py` | `memory_system/effectiveness/v6_sp_ab/experiment_log.md` | 9 | 🟡 | **new** row (July verify #10). Town and serial killer only; the wolf was excluded |
| v7 endpoint A/B | `evaluation/src/loop/measure.py` (`game_score`); the run driver and the paired-statistic script: not found | `memory_system/v7/execution_plan/report.md` §4–5, `experiment_log.md`; `batch_results/v7_endpoint_ab/` (gitignored: `PREREG_AMENDMENT.md`, `config.json`, `endpoint_result.json` with pooled per-decision scores only) | 9 | 🟡 | **new** |
| Persona-voice games | `evaluation/experiments/persona_voice_games.py`, `persona_voice_games_score.py` | `gameplay/data/persona_voice_games/` | 10 | ⚠️ | **new**. 8 pairs, one-flag difference on one commit |
| Evil-cover games | `evaluation/experiments/evil_cover_screen.py` (`games`) | `gameplay/data/evil_cover_games/` | 10 | ⚠️ | **new**. Three changes bundled; dirty trees |

### Play metrics

Spoke: [`metrics/report.md`](metrics/report.md).

| Instrument | Code | Record | Game | Mark | Since July / notes |
|---|---|---|---|---|---|
| Nine-seat de-lucked basket | `Agents/compute_metrics.py`; `Agents/schemas/metrics.py:254` (84 fields, was 63); `evaluation/src/instrument_validation/proxies/`; `evaluation/src/core/stats.py` (`point_biserial`) | `metrics/{proxy_win_monotonicity,experiment_log}.md`; `metrics/design/`; `metrics/metrics_audit/` | 9 | ✅ town · 🟡 investigator · ⚠️ deceiver · 🟡 town discussion | **re-rated**: discussion July 🔴 → 🟡 (town diagnostic proxy found 2026-07-02); harness **moved** to `instrument_validation/proxies/proxy_win_monotonicity.py`. Validated on nine seats only |
| Trust tiering and push | `Agents/compute_metrics.py:688-776` (`VALIDATED_ON_TEN_SEAT_METRICS` at :728, empty; `_metric_tier` :731; push :741) | `memory_system/v8/plan.md` §8.4 | 10 | — | **changed**: the July "indiscriminate push" became tiered on 2026-07-02; since the ten-seat port nothing pushes as "validated" |
| Ten-seat metrics and decision grades | `Agents/ten_seat_metrics.py`; `Agents/memory/consolidation/grading.py`; `scripts/grade_observations.py`; `tests/memory/test_ten_seat_grading.py` | `memory_system/v8/{plan.md §8.1–8.4 and §9.6, decisions.md §8 and §12–13, experiment_log.md}` | 10 | ⚠️ | **new** |
| Read Brier | `evaluation/src/loop/read_ledger.py` (nine-seat); `evaluation/experiments/persona_voice_games_score.py` (ten-seat) | `credit/report.md` §1, §4; `gameplay/data/persona_voice_games/` | both | 🟡 | **new** |
| Vote-target accuracy | `Agents/compute_metrics.py:536`; `decision_scoring.py` (`score_vote`, nine-seat threat set); `evaluation/experiments/haiku_vote_score.py` | Part A of the spoke; `discussion_evidence.md` §8.7 | both | ✅ as a count | **new** |
| Leverage anchor | `evaluation/src/instrument_validation/proxies/leverage_anchor_separation.py` | `memory_system/v7/plan.md`; `memory_system/v7/experiment_log.md` | 9 | 🟡 | **new** |
| Discussion census | `evaluation/experiments/discussion_evidence.py` (`census`) | `discussion_evidence.md` §2 | 9 | ✅ counts · 🟡 labels | **new** |
| Phase 2 step 8 counts | `evaluation/experiments/phase2_step8_{capture,counts}.py` | `gameplay/data/phase2_step8_games/` | 9 | ✅ counts · 🟡 reading | **new** |
| Balance batches | `evaluation/experiments/phase3_capture.py` | `gameplay/data/phase3_{games,balance,balance_2,balance_3,balance_4}/`; `discussion_evidence.md` §8.3 | 10 | ✅ counts · 🟡 reading | **new**. 31 games on flash-lite; none on Haiku |
| Blend-tactic check | `evidence/gameplay/turn_prompt/prompt_claims_audit/blend_claim_test.py` (study code in the record) | same folder, `experiment_log.md` | 9 | 🟡 | **new** |
| Investigator transmission | `evaluation/src/studies/investigator_transmission.py` | `memory_system/effectiveness/v6_sp_ab/experiment_log.md` | 9 | ⚠️ | **new**. Records cite the old `experiments/` path |
| Batch summary | `scripts/analyze_batch.py` | none | both | no trust of its own | **new** |

### Memory-field audits

Was the spoke `dimension_extraction/`, dissolved 2026-10-23: the code checks are now in
[`deterministic_audits/`](deterministic_audits/report.md) (case 3; detail in its `experiment_log.md` §5), and
the decision-tag read in [`labeling/sampled_reads/`](labeling/sampled_reads/report.md) (the decision-tag read).

| Instrument | Code | Record | Game | Mark | Since July / notes |
|---|---|---|---|---|---|
| Query-side dimension audit | `evaluation/src/instrument_validation/dimensions/dimension_audit.py`; computed fills in `Agents/memory/retrieval/situation_agent.py` (`_override_deterministic_dims`, `_known_board_facts`) | `extraction/situation_dimensions/dimension_accuracy_audit/` | 9 | ✅ as a record | **re-rated** (July hub ⚠️). Every query-side numeric now computed by code; parity and swing joined 2026-07-11 |
| Stored uses-left check | no standalone runner found | `memory_system/v8/experiment_log.md`, 2026-10-12 | 10 | 🟡 | **new** |
| Verdict halo | `evaluation/experiments/v8_verdict_halo.py` | `memory_system/v8/data/halo/`; `memory_system/v8/decisions.md` §13 | 10 | 🟡 | **new**. Least squares, no intervals |
| Decision tags | `scripts/tag_observation_decisions.py`; `evaluation/experiments/v8_decision_tag_check.py` | `memory_system/v8/data/decision_tags/` | 10 | ✅ (llm_judge §7: 🟡) | **new** |
| Category labels on stored lessons | — | — | 9 | ⏸ never validated | same (the kappa clause never ran) |

### v7 loop and credit

Spoke: [`loop/report.md`](loop/report.md). All nine-seat.

| Instrument | Code | Record | Mark | Since July / notes |
|---|---|---|---|---|
| Measure | `evaluation/src/loop/measure.py`; `tests/evaluation/test_loop_measure.py` | `memory_system/v7/execution_plan/report.md` | ✅ (LLM-free) | same. `game_score` is the endpoint's primary, pinned to the legacy abstain rule |
| Credit engine | `evaluation/src/loop/{credit_backfill,credit,conversion_credit}.py`; `tests/evaluation/test_credit_blend.py` | `credit/report.md` | spoke: sound, with stated limits | **changed**: `discussion_mode` is gone; tagger credit deleted 2026-07-13; `abstain_credit` (default `neutral`) and the conversion channel added 2026-07-21, off by default |
| Invariants | `evaluation/src/loop/invariants.py` (`assert_arm_factions`, `assert_arm_declared`, `assert_fingerprint_consistent`, `assert_observations_retired`) | — | ✅ | **moved** line refs → function names. `assert_observations_retired` **new** (2026-07-15) |
| Driver and config | `evaluation/src/loop/driver.py` (`run_loop`, `_run_arms_parallel`), `config.py` | — | July 🟡 | same. Dead toggles `arm` (label only) and `frozen_base_rates` (declared, unwired) were still unwired on 2026-10-23 |
| Consolidate and merge | `evaluation/src/loop/{consolidate,merge}.py` | — | ✅ mechanics | evict rule can now fire (`credit.py::_adoption_counts`); evicted nothing in the July run |
| July 19 build run | `run_loop` | `memory_system/v7/execution_plan/report.md` §5, `experiment_log.md`; `batch_results/v7_compound_town5/` (gitignored) | part of ✅ mechanics | **new** |
| Credit validators | `evaluation/src/instrument_validation/credit/{g2_separability,g3a_verdict_validity,heldout_credit_reproduction,windowed_credit}.py` | `memory_system/v7/experiment_log.md` §1–2, §6 | 🟡 | **new** (promoted 2026-07-04). `memory_system/v7/review_map.md` mislabels G3a as "tagger verdict validity" |
| Blind-spot fix validation | `evaluation/experiments/credit_blindspot_validation.py`; `tests/evaluation/test_credit_blindspot_fix.py` | `credit/blindspot_fix/step1_validation.{md,json}`, `experiment_log.md` | 🟡 | **new** |
| Tell lift and fold | `evaluation/src/loop/{tell_credit,tell_fold}.py` | `extraction/tell_extraction/report.md` §2–4; `store_curation/tells.md` | 🟡 | **new** |
| First link | `evaluation/src/loop/first_link.py`; `tests/evaluation/test_read_ledger_first_link.py` | `credit/read_tactic_credit_redesign.md` §3 | ⏸ (never run on record) | **new** |
| Synthesis A/B and offline prune | `evaluation/src/studies/{synth_deluck_ab,consolidation_prune}.py` | `memory_system/v7/runs/synth_deluck_ab{,_flite}/` | ⚠️ | **moved**; July: named in the diagnosis funnel, unrated |

### Methodology

Spoke: [`experimental_controls/report.md`](experimental_controls/report.md).

| Instrument | Code | Record | Game | Mark | Since July / notes |
|---|---|---|---|---|---|
| Fingerprint and drift guards | `Agents/run_fingerprint.py` (`runtime_fingerprint`); `evaluation/src/loop/invariants.py` | `evaluation/experimental_controls/drift_surfaces_and_guards.md`; `tracing/fingerprinting/report.md` | both | ✅ in-run · manual cross-epoch | same. The prompt-bundle hash misses nested prompt packages |
| Interleaved arms | `evaluation/src/loop/driver.py` (`_run_arms_parallel`); not in `scripts/run_batch.py` | — | 9 | — | same; per-game alternation in `run_batch` still unbuilt |
| Paired statistics | `evaluation/src/core/stats.py` (`mcnemar_exact`, `wilcoxon_paired`, `binomial_ci`, `point_biserial`) | — | both | July ✅ | same (verify #1) |
| Power (MDE) gate | `evaluation/src/instrument_validation/power/mde_simulation.py` | `memory_system/v7/execution_plan/report.md` §2 (full table at `24dfd3a7`) | 9 | ✅ | **new**. Not run for the paired endpoint design |
| Seedability | `Agents/nodes/orchestrator.py` (`initialize_game`); `tests/engine/test_seedability.py` | `memory_system/effectiveness/paired_ab/experiment_log.md` (20 of 20 by hand, 2026-06-11) | both | ✅ | **new** |
| Prompt golden | `tests/fixtures/day_discuss_prompt_golden.{py,json}`; `tests/engine/test_draft_preview.py` | — | 10 | 🟡 | **new**. Day-discussion turn only; regenerated in 34 commits 2026-09-29 to 10-21 |
| Run graduation | `evaluation/src/cli_runner/graduate_run.py` (`eval-graduate`); `tests/evaluation/test_graduate.py` | `tracing/fingerprinting/report.md` | — | ⏸ built, never used | **new** |
| Reasoning-token scope probe | no committed script found; bench token recording since `3e05e8a7` | `credit/blindspot_fix/experiment_log.md` §⑦; `discussion_evidence.md` §6.7 | 9 | 🟡 | **new**. Game records still carry only the configured level |
| Variance-levers audit | — | `evaluation/experimental_controls/variance_reduction_levers.md` | 9 | — | **moved** 2026-07-07 |

### Model admission and cost

Spoke: [`model_admission/report.md`](model_admission/report.md) (untracked on 2026-10-23). All **new**.

| Instrument | Code | Record | Game | Mark |
|---|---|---|---|---|
| Admission run | `evaluation/src/cli_runner/model_admission.py` (`eval-model-admission`); `evaluation/src/model_admission/{probes,seat_schemas}.py`; configs `evaluation/config/model_admission/*.json`; `tests/evaluation/test_model_admission.py` | 20 records in `evaluation/eval_results/model_admission/` (gitignored); the spoke is the first written record | both | 🟡 |
| Live schema gate | `tests/live/test_model_structured_output.py` | docstring note of 2026-09-10 only | 10 | ⚠️ (no `anthropic/` credential branch) |
| Bench arms for admission | `eval-hallucination-bench`; configs `evaluation/config/hallucination_bench_phase3_*.json`, `model_admission/bench_*.json`, `hallucination_bench_shared_prefix_luna.json` | summaries in `evaluation/eval_results/hallucination_bench/` (gitignored) | both | 🟡 |
| Thinking-budget replay | `evaluation/experiments/haiku_effort_{cases,score}.py` | `gameplay/deduction/experiment_log.md` §2; `gameplay/deduction/data/haiku_effort_replay/` | 10 | 🟡 |
| Summariser comparison | `evaluation/experiments/haiku_summary_compare.py` | `gameplay/deduction/experiment_log.md` §3; `gameplay/deduction/data/haiku_summary_compare/` | 10 | ⚠️ |
| Seat-model games | `evaluation/experiments/phase3_capture.py` | `gameplay/data/phase3_{flash,luna}_games/` | 10 | ⚠️ |
| Memory-job model comparisons | `evaluation/experiments/{claude_extraction_compare,dehalo_compare}.py`; v5 `evaluation/src/studies/extraction_model_comparison.py` | `memory_system/v8/data/{extraction_model_comparison,dehalo_compare}/`; `memory_system/v7/extraction_screens/` | 10 / 9 | ⚠️ |
| July seat-model selection | none | `model_selection/report.md` | 9 | ⚠️ (historical) |
| Cost and cache accounting | `Agents/llm_factory/{pricing,catalog}.py`; `server/game/usage.py`; `evaluation/src/core/costs.py`; `evaluation/src/loop/cost.py`; `evaluation/experiments/game_cache_share.py`; `scripts/model_catalog.py`; `tests/engine/test_{pricing,langfuse_prices,shared_prefix_layout}.py` | `caching/report.md` §4–5; `caching/experiment_log.md` §11 | both | 🟡 |

---

## Records: retired, frozen and archived

| Record | Code | Record | Status |
|---|---|---|---|
| Discussion tagger | `evaluation/src/loop/discussion_tagger.py`; `evaluation/src/cli_runner/discussion_tagger_eval.py` (`eval-tagger`); `evaluation/src/instrument_validation/tagger/{tagger_validation,tagger_effectiveness}.py` | `evaluation/llm_judge/discussion_tagger.md` (moved 2026-10-23); `memory_system/v7/experiment_log.md` §12g | **retired**. 🟡 as recorded in July. Credit mode deleted 2026-07-13 (`evaluation/src/loop/driver.py:373`, "since the tagger mode's retirement"); runs in no game; out of the write-up (owner, 2026-10-22, `writeup/_planning/map.md`). Its report's consumer table is stale and is left as a record |
| Hardening pass | — | `evaluation/hardening_pass/{report,experiment_log}.md` | dated record (2026-07-02, interim). Its fixes are rated where they now live |
| Archive | `evaluation/src/archive/{legacy_cases,legacy_retrieval_judge,eval_retrieval_v1,situation_summary_model_comparison,dedup_model_comparison,per_role_extraction,pairwise_extraction,pairwise_extraction_prompts}.py` | — | superseded; do not import live |
| Labelling and training structure (2026-06-29) | `training/` at the repo root; `evaluation/src/labeling/` | `evaluation/labeling/report.md` §1 | dated note: `training/` left `evaluation/` because it trains models rather than judging cases. `auto_dedup_labeler` was folded into the engine and adapter path (byte-identical prompts over 232 cases). `merger.merge` was retired after the staged pipeline showed it had never composed. Parked |

---

## Records outside version control (as of 2026-10-23)

| What | Where | Cited by |
|---|---|---|
| June A/B game data | `batch_results/ab_*.jsonl` (gitignored) | evaluation_scopes/game, labeling/sampled_reads (sampler smoke) |
| v7 build run and endpoint, including the pre-registration amendment | `batch_results/v7_compound_town5/`, `batch_results/v7_endpoint_ab/` (gitignored) | loop, evaluation_scopes/game |
| v6 games read by the credit validators and proxy validations | `batch_results/v6ab_*.jsonl` (gitignored) | loop, metrics |
| Admission records and admission bench summaries | `evaluation/eval_results/model_admission/`, `evaluation/eval_results/hallucination_bench/*/summary.json` (gitignored) | model_admission, `caching/report.md` |
| Bench screen run, R1 samples, note-screen generations, Haiku vote outputs | `evaluation/eval_results/{hallucination_bench,note_prompt_screen}/` (gitignored) | factual_errors, evaluation_scopes/turn |
| Solver census runner and output; `gameplay/deduction/report.md` | untracked files | deterministic_audits |
| Haiku vote replay runners, config and data | committed `516318c9` (2026-10-24) | evaluation_scopes/turn, metrics |
| The spokes `deterministic_audits/` and `model_admission/` | untracked folders | this hub |
| Code not found | the v7 endpoint's paired-statistic script; the reasoning-token probe; `evaluation/experiments/round_echo_filter_check.py`; the runner of the stored uses-left check | evaluation_scopes/game, methodology, llm_judge, deterministic_audits |

---

## Superseded July sections (dated)

**The v7-run trust scorecard (2026-06-28).** It was written to gate a v7 run that has since happened. Its
five points, and what became of each:

| July point | Status on 2026-10-23 |
|---|---|
| "Town memory helps": paired A/B (N=30) and the replay screen converge | Corrected. June improved the town's decisions, not significantly its wins (p=0.27). v6 did not repeat it (+6 points, p=0.77). The v7 endpoint was 0.147 lower with memory (p≈0.06, 19 of 30 boards). Research closed 2026-07-21 |
| The wolf-memory null is power plus invalid runs; the tagger is a validated deceiver metric | Moot. The wolf-direct arm never ran and will not. The tagger was retired from credit on 2026-07-13 |
| Config sensitivity: lock `expect_factions` with matching `configs`, `base_store`, `model`/`dedup_model`, and `off_baseline=True` before a v7 run | The locks held in the July 19 run (`expect_factions: town_only`, verified per generation). No loop run is planned |
| Retrieval levers (criticality, core dilemma) are within noise | Stands, as a nine-seat result |
| The application judge is human-uncalibrated | Still true; gates nothing |

**The planned build (2026-06-27): the case-pull sampler.** Built on 2026-07-02 as
`evaluation/src/diagnosis/sampler.py` with `eval-case-sample`. Never used for a real review.

**The eval-report skeleton (2026-06-27/28).** It organized the hub by memory case type × modality. The
hub now organizes by subject × rung, with the A/B and instrument layer on top.

**The diagnosis funnel (memory, nine-seat), paths updated.** How a memory null was drilled into:
(1) did retrieval fire → EvalCase fields + `evaluation/src/audits/recall_flags.py`; (2) was it
relevant → `evaluation/src/judges/retrieval.py` + the situation NDCG golden; (3) was it used →
`judges/turn_action.py` + `evaluation/src/loop/memory_adherence.py`; (4) did the decision change →
`evaluation/src/replay/turn_action.py`; (5) did the outcome change → metrics, the paired A/B and the
decision-replay screen (`evaluation/src/studies/synth_deluck_ab.py` is a synthesis study, not an outcome
test).

---

## Verify-in-code pass — results (2026-06-28), with status on 2026-10-23

The July pass read the code behind the 🔍 flags and folded corrections into the July tables. Each item
gives the July verdict in brief, then its status today.

1. **`core/stats.py`: confirmed as the primary home.** Clopper–Pearson CIs (analytic, not bootstrap),
   Fisher exact, exact McNemar and Wilcoxon signed-rank, point-biserial; two-sided; no built-in
   multiple-comparison correction. The paired-A/B figures are Wilcoxon; the metric validations are
   point-biserial. *Status:* unchanged. `diagnose_wolf_sk_proxies.py` now lives in
   `evaluation/src/instrument_validation/proxies/`; `town_echo_read.py` is still in
   `memory_system/effectiveness/paired_ab/`; bootstrap CIs are still only in `training/evaluator.py`.
2. **Retrieval fallback: bias confirmed.** Fewer than two items gave relevance 1 but efficiency 5, pooled
   with no counter. *Status:* **fixed** (`is_fallback`, excluded at
   `cli_runner/regen_replay/both/retrieval.py:101,109`).
3. **`Agents/compute_metrics.py`: confirmed, one rename** (`town_mislynch_rate`; `suspicion_drawn` split
   by faction); the push was indiscriminate. *Status:* the push has been tiered since 2026-07-02, and
   since the ten-seat port nothing pushes as validated. 84 fields.
4. **Arm guard: confirmed, location corrected** (the loop, not `run_batch.py`). *Status:* held in the
   July 19 run. The July line refs (`driver.py:331`, `invariants.py:185-210`, `config.py:19`) have moved;
   `config.py:19` is now `retrieval_types`. The functions are `assert_arm_factions` and
   `assert_arm_declared` in `invariants.py`.
5. **Loop toggle matrix: confirmed and mapped** (32 config fields; both arms share generation and
   boards). *Status:* the field count was not re-checked. The dead toggles `arm` and
   `frozen_base_rates` are still unwired.
6. **Dedup and day-summary judges: resolved** (dedup 🟡; day-summary ⚠️; the `batch_dedup.py` silent
   failure fixed 2026-06-28). *Status:* both now in the spoke's ⚠️ memory-judge group; the fix was not
   re-checked.
7. **`eval-extraction` is a real entry.** *Status:* now `pyproject.toml:49`, pointing at
   `cli_runner/regen_replay/judge/extraction_judge.py`.
8. **Backend consistency: nuanced.** Env-driven, recorded in `runtime_fingerprint.llm_backend`,
   hard-asserted constant within a loop run; across runs a human must check. *Status:* unchanged in
   mechanism. The judge default is now Claude Haiku 5.5, so July Gemini scores and today's re-runs differ
   by vendor as well as backend.
9. **Tagger-validity tension: resolved, no contradiction** (the +0.56/+0.60 wolf/SK figures and the
   retracted +0.556 town figure are different quantities). *Status:* moot; the tagger is retired and out
   of the write-up.
10. **`v6_sp_ab`: wolf scope overstated.** The deceiver arm was the serial killer; the wolf was excluded.
    *Status:* holds. The direct wolf A/B will not run.

**Residuals from the July pass:**
- 🔧 retrieval fallback pooling → **fixed**.
- ✅ `batch_dedup.py` swallow-all-exceptions → fixed 2026-06-28.
- 🔧 dead toggles `arm` and `frozen_base_rates` → still unwired.
- ⏳ uncalibrated: application judge (⏸), day-summary judge, dedup quality scores → still uncalibrated;
  none gates anything now.
- ⏳ direct wolf strategy-point/observation A/B never run → will not run.

*Ledger rewritten 2026-10-23 from the spokes, their records and the working tree of that date. The
spokes own the marks; the design folders own the verdicts.*


---

# Part 3. The hub as of 2026-10-25 (one block per method page)

*Kept whole as it stood on 2026-10-25, before the hub was rewritten to explain the methods conceptually; this version carries the numbers, the per-call code paths and the per-block case lists. Its headings are one level down here.*


> **What this page is.** The overview of the project's evaluation, meant to be read on its own: what is
> evaluated and why, a block for every method page saying what it answers, what is inside it and how far it
> can be trusted, then the rules for choosing a method, what the methods caught about themselves, and what
> holds across them. The detail lives in the method pages; this page tells you what you will find there.
> **Companion records:** the [experiment log](experiment_log.md) keeps the previous hub and source map whole;
> the [source map](source_map.md) lists the data every method reads and the records outside git.
> **The guiding rule:** use code wherever the answer can be computed from the game record or the rules, a
> reader only for meaning, and anchor every reader to a person.

**The system being checked.** Werewolf, a hidden-role game, played by AI agents. Model calls do four jobs
in it:
- **Playing:** each seat's turns: what it says, how it votes, its night action, and the private note and
  role guesses it keeps.
- **Running the game around the players:** the summariser that writes up each day; the echo gate and the
  opening filter, which decide which lines are said aloud; and, for human seats, a classifier that tags whom
  a message addresses and helpers that draft a line.
- **Building and serving memory:** a call that turns the situation into a memory search, extraction of
  lessons after each game, and passes that clean the lessons (removing an outcome bias, tagging decisions,
  merging duplicates, distilling strategy).
- **Measuring:** LLM judges and model readers that label the other calls' outputs.

Some of what is evaluated is plain code: the deduction engine that writes certain conclusions into each
prompt, the code that builds each prompt (and so decides what each seat may see), and the scores computed
from game records. A model catalogue sets which model does each job.

**Two versions of the game.** Through July 2026 the game had nine seats, was played by Gemini flash-lite,
and evaluation centred on memory. Since 2026-10-09 the live game has ten seats drawn from a twelve-role
cast, seats default to Claude Haiku 5.5, and memory is a per-game choice served from a Postgres store. This
page calls them the **nine-seat** and the **ten-seat** game. Most memory results describe the nine-seat
game; most play, factual-error and deduction results describe the ten-seat game. Each block below says
which.

### In short

- **The evaluation answers three questions, not one.** Does each part do its job well enough to trust? Can
  the checks themselves be trusted? Does a change make things better? The third is the first, measured on
  two versions, so it rests on the other two.
- **Most of it evaluates model behaviour**: what the players say and decide, and the summariser, the
  in-game classifiers, the memory jobs and the judges. Some of it checks the code around the models (the
  deduction engine, the code that builds each prompt) and the measuring harness itself.
- **Ten method pages, in three groups.** Judging one output: code checks, LLM judges, labelling (golden
  sets and sampled reads), and the scales and scores they share. Testing a change: one frozen turn, one day
  or whole games, play metrics, and the controls that keep a comparison fair. Two worked workflows that
  combine them: the factual-error checks and model admission.
- **The apparatus caught its own errors, repeatedly**: a baseline that shifted on identical prompts, a
  misconfigured memory arm, leak checkers that checked nothing, a thinking level that produced no reasoning,
  a test that let a replayed vote see its own result.
- **What holds:** code checks, exact counts and scores against the true roles, and the nine-seat gold sets.
  **What is directional only:** model judges and model readers, none checked against a person on the
  ten-seat game.
- **The largest gaps:** no person's check on any ten-seat label set, no factual-error rate on the ten-seat
  game, no CI, and the nightly leak audit not installed.

---

### What the evaluation is for

**1. Does each part do its job well enough to trust?** Every model call has a job, and each is checked
against it. The players should state only true facts and vote for real threats; the summariser should
record claims as they were made; the echo gate should hold back only lines that repeat; the extractor's
verdict on a play should follow the play, not who won; the deduction engine should never write a false
conclusion; no prompt should carry another seat's secrets. Most of the method pages answer this question
for one part or another.

**2. Can the checks themselves be trusted?** A judge, a label or a code check can be wrong too, and a wrong
check produces confident wrong numbers. So each check is itself checked: a model judge against a person's
labels, a code check by planting a fault it must catch, a score against whether it goes with winning.

**3. Does a change make it better?** A prompt fix, a model switch or a memory feature is judged by
measuring question 1 on both versions, under controls that keep everything else the same.

**Every model call, by job.** The calls found in the code on 2026-10-25, and where each is checked. Code
paths are from the repo root.

| Job | Model call | What it does | Code | Where it is checked |
|---|---|---|---|---|
| **Playing** | A seat's turn | Its line, vote or night action, with the private note and role guesses it keeps; the wolves' night chat is a turn too | `Agents/turn/agent_player.py` (`run_agent`, called by the day and night nodes) | [factual_errors](factual_errors/report.md), [metrics](metrics/report.md), [turn replays](evaluation_scopes/turn/report.md), [sampled reads](labeling/sampled_reads/report.md), [model_admission](model_admission/report.md) |
| **Running the game** | Day summariser | Writes up each day; since October it only transcribes accusations and role claims, and code keeps the claim ledger | `Agents/nodes/day/summary_agent.py` | [factual_errors](factual_errors/report.md) (the summary-claim replay); [llm_judge](llm_judge/report.md), case 7 |
| | Echo gate | Holds back an open-floor line that adds nothing | `Agents/turn/echo_gate.py` | [llm_judge](llm_judge/report.md), case 2 |
| | Opening filter | Keeps the opening lines that are claims, results or challenges | `Agents/turn/round_filter.py` | [llm_judge](llm_judge/report.md), case 2 |
| | Addressing classifier (human seats) | Tags whom a human's message addresses, which sets who must reply | `Agents/turn/addressing_agent.py` | [llm_judge](llm_judge/report.md), case 3 (not yet checked) |
| | Drafting helpers (human seats) | Draft a line for the player to send, or turn a wolf's rough notes into one line | `Agents/turn/drafting_agent.py` | Not evaluated: the player reads and sends the line |
| **Memory** | Memory search query | Turns the seat's situation into the query and fields memory is searched by | `Agents/memory/retrieval/situation_agent.py` | [llm_judge](llm_judge/report.md), case 6; [deterministic_audits](deterministic_audits/report.md), case 3 |
| | Extraction | Writes lessons from a finished game, offline in batches | `Agents/memory/extraction/extraction_agent.py`, `offline.py` | [llm_judge](llm_judge/report.md), case 5 (nine-seat); [deterministic_audits](deterministic_audits/report.md) (uses-left count, verdict halo) |
| | De-halo pass | Rewrites verdicts in lessons that the game record does not support | `Agents/memory/extraction/dehalo.py` | [llm_judge](llm_judge/report.md), case 4 |
| | Decision tagger | Says which decision an older lesson describes | `Agents/memory/extraction/decision_tags.py` | [llm_judge](llm_judge/report.md), case 4; [sampled reads](labeling/sampled_reads/report.md) (the decision-tag read) |
| | Dedup decision | Keeps, discards or merges a new lesson | `Agents/memory/deduplication/dedup_agent.py` | [labeling](labeling/report.md), cases 1–2 |
| | Point dedup | Finds duplicate strategy points in the store | `Agents/memory/batch_deduplication/cluster_agent.py` | [llm_judge](llm_judge/report.md), case 4; [labeling](labeling/report.md) (the ten-seat duplicate groups) |
| | Strategy synthesis | Distils strategy points from groups of lessons, in the memory's periodic consolidation | `Agents/memory/strategy_synthesis.py` | Outside this folder: the rule screen in [`memory_system/v8/`](../memory_system/v8/experiment_log.md) |
| | Reranker (off by default) | Reorders retrieved lessons by relevance | `Agents/memory/retrieval/rerank_agent.py` | [labeling](labeling/report.md), case 2 |
| | Namespace augmentation (built, parked) | Re-mines one role and phase of a finished game more deeply | `Agents/memory/extraction/augment_agent.py` | Not evaluated |
| **Measuring** | LLM judges | Label or score another call's output against a rubric | `evaluation/src/judges/`, `evaluation/src/loop/`, `evaluation/experiments/` | [llm_judge](llm_judge/report.md) |
| | Labelling panel | Several models label items for a golden set before a person reviews them | `evaluation/src/labeling/engine.py` | [labeling](labeling/report.md), case 2 |
| | Blind model readers | Claude subagents reading blind packets | Started from a working session, not in the code | [sampled reads](labeling/sampled_reads/report.md); [labeling](labeling/report.md), case 3 |

**What is evaluated, by subject.** Seven subjects. Memory was the first, and since the memory research
closed in July 2026 most evaluation work has been on the other six.

| Subject | The question | Main methods | Design verdict lives in |
|---|---|---|---|
| **Memory** | do stored lessons improve play; are the model-written fields right; does credit mean anything | whole-game A/Bs, the decision replay, the loop's credit validators, memory-component judges, golden sets, field audits | [`memory_system/`](../memory_system/report.md), [`memory_system/v7/execution_plan/`](../memory_system/v7/execution_plan/report.md), [`credit/`](../credit/report.md) |
| **Play quality** | do prompt, rule and card changes make the agents argue, vote and talk better | turn replays, blind sampled reads, ten-seat metrics, the read Brier score, vote-target counts, same-deal games, balance batches | [`gameplay/`](../gameplay/report.md), [`gameplay/discussion/`](../gameplay/discussion/report.md) |
| **Model calls that run the game** | does the summariser keep claims straight; do the echo gate, the opening filter and the accusation tags label lines as intended | LLM judges, model readers, the summary-claim replay, code checks on the claim ledger | [`gameplay/`](../gameplay/report.md), [`gameplay/discussion/`](../gameplay/discussion/report.md) |
| **Factual errors** | how often agents state something the record contradicts, and does a change reduce it | the census (code screen plus model reader), the factual-error test sets, pinned-case replays | [`gameplay/`](../gameplay/report.md) (problem 1), [`gameplay/turn_prompt/`](../gameplay/turn_prompt/validation_plan.md) |
| **The deduction engine** | is every line it writes true in every legal game; does it help the seat | soundness tests over random legal nights, a brute-force oracle, acceptance cases, censuses, injection and placement replays | [`gameplay/deduction/`](../gameplay/deduction/report.md) |
| **Models and cost** | can a candidate model play the game's turns; is it worse than the current one; what does a game cost | test prompts, replays against the current model, real games, cost and cache accounting | [`caching/`](../caching/report.md), [`model_selection/`](model_admission/model_selection.md) |
| **The information boundary** | does any prompt carry another seat's private information | batch leak checks, payload leak tests, the served-game leak audit, tests of what each player is told | [`agent_boundaries/`](../agent_boundaries/report.md) |

The design folders in the last column say whether a part works. The method pages below say how it was
checked and how far that check can be trusted.

---

### The method pages

```
 judging one output, cheapest first
   code check (no model; exact; only what a rule encodes)
   → LLM judge (cheap; mostly checked against other models)
   → labelling: sampled reads (one-off) · golden sets (reusable; a person anchors them)
   all scored on the scales and scores page
 testing a change
   one frozen turn → one day (designed, not built) → whole games      scored by play metrics
   kept fair by experimental controls
 two worked workflows: factual errors · model admission
```

**The calibration chain.** A person's labels check the judges and the model readers, which then label at
scale. In practice the links are mostly unconnected: no person has yet checked a ten-seat judge, and the
first owner checks are the step that connects them. Code checks sit outside the chain: they answer only
questions written as rules, so they need no calibration, only a test that they fire.

**Trust marks**, used in every block and taken from the method page's own verdict: ✅ sound · 🟡 usable with
caveats · ⚠️ a smoke test only · ❌ does not hold · ⏸ designed, not built · ⛔ underbuilt.

#### Judging one output

##### Code checks with no model ([deterministic_audits](deterministic_audits/report.md))

**What it answers.** Where the right answer can be computed from the game record, the rules or a fixed list
of allowed values, is the output right? Free, instant, the same answer every run, and run on every item.

**What is inside.**
- Why code wins where it applies: a table of code against an LLM judge against a person, by cost, coverage,
  repeatability and how each fails.
- An inventory of every code-only check in the project, about two dozen, each with its result and trust.
- Five cases, one per approach:
  1. **Check every output against a rule: the leak checks.** That no prompt carries another seat's secrets,
     run after every batch game, in unit tests on the code that builds prompts, and over games played on the
     website (the served-game audit). The first run (June 2026) caught 109 leaks from a code change; 0 since.
  2. **Compare with independent test code: the deduction engine.** Every conclusion the engine writes (for
     example "player_7 must be the Chanteuse") tested against the true roles over 20,000 random legal nights
     per test, against a brute-force oracle over every deal of roles the player's knowledge allows, and on
     four real failures as acceptance cases. Two counts of its output too: impossible roles kept (0 in 150
     random games) and how much text it adds to a prompt.
  3. **Score a model's structured output against the truth: the memory-search fields.** A model filled
     fields that memory search filtered on; code recomputed each from the game state. Players alive was
     exact in 97% of 6,099 cases, the Vigilante's shots left in 16% of 1,109, and the wolves' swing-vote
     flag was worse than always answering no. A rule fixed before the run reopened an earlier result.
  4. **Code narrows, a reader judges: the factual-error pre-screen** (the census below).
  5. **Guard the experiment's own setup:** the arm guard, the embedding-model check and the prompt snapshot
     (all explained under experimental controls).
- Audits of saved nine-seat games (did the speaking order starve any role; did attackers act on a failed
  attack) and the tests of what each player is told about its own night actions.

**How far to trust it.** ✅ the leak checks, the payload tests, the deduction engine's soundness tests and
oracle, the embedding check (in the batch runner only). 🟡 the served-game audit (built and tested; its
nightly job was never installed), the four acceptance cases (the only test of what the engine misses), the
prompt-length count, the saved-game audits. ⚠️ the do-or-die turn flags. The limit of every code check: it
finds only what its rule encodes, and a check fed no input passes silently, so each needs a planted fault
it must catch.

**Read it when** you want to know what is checked exhaustively and for free, or how a code check was itself
tested.

##### LLM judges ([llm_judge](llm_judge/report.md))

**What it answers.** Where a question needs reading (is this line new, does this summary mislead), how was
each model judge built, and how far can its labels be trusted? An *LLM judge* is a model that reads another
model's output and labels it against a rubric, a written statement of what to look for. The page also
covers the *model classifiers in the product*, which label the same way but whose label changes the game or
the memory (the echo gate holds a line; the dedup decision drops a lesson), so they are things to be
measured, not measurements.

**What is inside.**
- The five-step workflow every judge went through: decide that a model is the right tool; choose the kind
  of judging; design the rubric; validate it against a golden set, a stronger model or a real outcome; fix
  the configuration, model and scoring.
- Eight cases, one per use case:
  1. Finding factual errors: the census reader and the expectation judge.
  2. What the table hears in the live game: the echo gate (holds back a line that only repeats what was
     said) and the opening filter.
  3. Who must answer in the live game: the speakers' accusation tags and the addressing classifier.
  4. Labelling the ten-seat memory at scale: the decision tagger, the de-halo pass (a second model re-reads
     each verdict the extractor wrote while knowing who won) and dedup.
  5. Scoring memory quality on a 1–5 rubric: the extraction and day-summary judges.
  6. Comparing two memory queries side by side: the pairwise situation-summary judge.
  7. Answering one study's question: the discussion-evidence judge and the summariser comparison.
  8. Memory research: the tell detector and the same-tell, memory-adherence and coherence judges.
- The full inventory of every judge and classifier in the code with its check, and the top-ups each would
  need for today's game.
- Supporting files: [agent_decision.md](llm_judge/agent_decision.md), [day_summary.md](llm_judge/day_summary.md)
  and [extraction.md](llm_judge/extraction.md) are dated nine-seat accounts of the memory-era judges, each
  with a status note on what changed; [golden_set_method.md](llm_judge/golden_set_method.md) is the plan for
  golden sets of reference points (not built).

**How far to trust it.** The judges built on a narrow question against facts handed to them held up; the
1–5 quality rubrics did not. 🟡 the factual-error judges (checked against a person, nine-seat, Gemini era).
🟡 the echo gate (checked against model readers). ⚠️ the opening filter and the accusation tags. ⚠️ the
memory-era rubric judges. Every judge and classifier now runs on the same model as the players, and that
bias was not measured.

**Read it when** you need to know how a model judge was built, what it was checked against, or whether a
judge's number can carry a decision.

##### Labelling: golden sets ([labeling](labeling/report.md))

**What it answers.** What reference labels exist to score a cheaper check against, who made them, and how
far can they be trusted? A *golden set* is a set of items with trusted labels. **Gold** labels are made or
checked by a person; **silver** labels are made by models and not checked by a person, so they are a
reference, not ground truth.

**What is inside.**
- The five techniques that golden sets and sampled reads share: draw the items without seeing the outcome
  (a sample chosen by who won measures the win); hide which version produced each item behind a key file;
  fix the rubric and the pass bar before reading; measure agreement between readers; anchor to a person.
- A table of every golden set in the project (22), by who labelled it, its size, game and date, and
  whether it is still current.
- Five cases, one per way of labelling:
  1. A person labels everything: the online dedup set (65 pairs).
  2. A model panel, then a person on the disagreements: 863 dedup cases labelled by three models, where a
     person's review showed a "discard" majority was wrong 37% of the time.
  3. Models only: the ten-seat readers.
  4. A written expectation per case: the factual-error pinned cases.
  5. A small gold set checked by a large silver one: the embedding prefilter.
- The labelling pipeline and its calibration step (built 2026-10-23): it scores model labels against a
  person's, with agreement, Cohen's kappa, per-label precision and recall, and a pass or fail.
- Supporting files: [owner_checks/](labeling/owner_checks/) holds blind packets for three model sources (the
  accusation tags, the echo gate, the factual-error judge), waiting on the owner's labels;
  [dedup.md](labeling/dedup.md) is the memory-era account of the dedup scorers; [plan.md](labeling/plan.md)
  is the build plan for the calibration step.

**How far to trust it.** 🟡 the gold sets, all nine-seat, May to July 2026. ⚠️ the ten-seat silver sets: no
person has checked any of them, and several back live features (the accusation tags, which pick who gets a
closing defence before the vote; the echo gate; the published memory store). 🟡 the calibration step, built and not yet used.

**Read it when** you need the reference a check was scored against, or want to know how a label set was
made.

##### Labelling: sampled reads ([sampled_reads](labeling/sampled_reads/report.md))

**What it answers.** When two versions of a prompt or feature need judging and no golden set exists, which
is better? A *sampled read* labels a sample of cases once, for that decision, and is not kept as a
reference.

**What is inside.**
- When a read is the right tool: a new question rarely has a golden set, and the judges are uncalibrated, so
  most qualitative design calls in the project were made by reading cases.
- The October 2026 method: seeded draws, packets that hide which version wrote each line, a key file that
  maps them back, the readers' answers saved, and code that scores them.
- Where reads were used: the October screens' blind packets, the decision-tag read, the phase 3 game reads
  (25 ten-seat games read as transcripts with the true roles, for failure modes), the June
  discussion-quality gate, the credit spot-check, and a case sampler built for later reviews.
- Who the readers are: Claude subagents (Sonnet or Opus), not people. The owner sets the question and
  rules from the summaries.

**How far to trust it.** 🟡 the blind packet reads: one model reader per item, and how often two readers
agree was never measured. Re-read by fresh readers, labels tied to an act held exactly ("did the seat claim
a role": 13 and 33) and labels needing judgment moved ("does the line explain the visit": 29 to 19 of 73).
✅ the decision-tag read, 98 of 102 against a bar set beforehand. ⚠️ the credit spot-check (15 claims). In
July 2026 reads left no record; since October they do.

**Read it when** a design call was made by reading cases and you want to know how the read was run.

##### Scales and scores ([scoring](scoring/report.md))

**What it answers.** How is one label recorded, how is a judge scored against a golden set, and how are two
versions compared beyond chance? The page keeps the three apart, because mixing them is the commonest
mistake.

**What is inside.**
- **The scale of one label:** binary, categorical, graded, pairwise preference, coverage of reference
  points, each with the project's example and who gives it.
- **Scoring a judge against a golden set:** accuracy, precision and recall, kappa, NDCG (for rankings) and
  the Brier score (for probabilities).
- **Comparing two versions:** McNemar, Wilcoxon and Fisher tests, with intervals.
- Where the project stands: what is built and used, what was built on 2026-10-23 and not yet used, and what
  is not built.

**How far to trust it.** 🟡 the standard scores are built and used. ⚠️ no 1–5 rubric judge has been scored
against people, so those numbers show direction only.

**Read it when** a report quotes a score or a test and you want to know what it measures.

#### Testing a change

**Every change is tested at two levels.** First the changed call itself: its own input frozen (a player's
turn, one day's summary, one finished game's record, one candidate lesson) and the call run again under the
change, scored against its job by the methods above. Then its effect on play, through the scopes below. For
a change to a player's prompt the two are the same test; for the summariser, the memory jobs and the
classifiers they are separate, and some components have only the first.

| Component | Its own unit, replayed or scored on frozen inputs | Its effect on play |
|---|---|---|
| **Day summariser** | One day: the summary call rebuilt with exactly the input production gave it, run 5 times, scored by code against fixed failure patterns; it caught one regression before it shipped ([factual_errors](factual_errors/report.md), step 4) | The player turn that read the summary, replayed: the repeated invented claim went from 5 of 5 samples to 0 |
| **Dedup decision** | One candidate lesson against its neighbours, scored on golden sets of 65 and 111 human labels; the best setup matched 99 of 111 ([labeling](labeling/report.md)) | Through retrieval and whole-game memory A/Bs: the store-retrieval check found the aggressive store had lost relevance at 39 cases ([`dedup/store_retrieval_impact/`](../dedup/store_retrieval_impact/experiment_log.md)) |
| **Extraction** | One finished game's record, re-extracted offline and scored: the post-game judge on 48 nine-seat games, the uses-left count against the engine, the outcome-halo measure ([llm_judge](llm_judge/report.md), [deterministic_audits](deterministic_audits/report.md)) | Frozen memory lookups searched again against the rebuilt store and read for fit ([`memory_system/v8/`](../memory_system/v8/experiment_log.md)); the October rebuild also changed the store's size and filter, so extraction alone was not isolated. Whole-game memory A/Bs in the nine-seat era |
| **Echo gate, opening filter** | One candidate line, read blind: the gate held 10 of 29 restatements and 0 of 36 worthwhile lines ([llm_judge](llm_judge/report.md), case 2) | Not separately measured |

##### Evaluation scopes: one turn, one day, whole games ([evaluation_scopes](evaluation_scopes/report.md))

**What it answers.** How much of the game should a test hold fixed? The same controlled experiment (hold
everything fixed but the change, run both versions side by side, compare) runs at three scopes, like unit,
integration and end-to-end tests. Unlike software tests they are statistical: the same input is sampled many
times and versions are compared by rate. The overview page compares the three by what each holds fixed, what
it can see, its cost and the samples it needs, and says when to move up a scope.

- **[One frozen turn](evaluation_scopes/turn/report.md)** (the unit test). A recorded turn's whole input
  (the board, the transcript so far, the seat's private record, its memory) is rebuilt exactly, and each
  version answers it many times. Inside: how a replay is built; what any replay can and cannot show; the
  design of the per-day replay; and the fourteen screens of June to October 2026, each a short test of one
  change:
  - on the nine-seat game: the **decision replay** (one vote or night action regenerated with memory on and
    off), the **checkpoint replay** (a fixed exam of town decisions re-answered against each memory store),
    the **tell-book screen** (votes with and without a block of tells, the signs that give a role away) and
    the **night-1 target check** (where unguided first-night choices land);
  - on the ten-seat game: the **stage-filter replay** (96 memory lookups searched again, dropping lessons
    from a different stage of the game) and nine October screens of prompt, card and deduction-engine
    changes (an evil seat's cover claim, a voting sentence, visit wording, persona voices, the private note,
    a rival-claim line, where the deduction block sits).

  A screen cost under $0.01 to about $0.25. **Trust:** ✅ the decision replay (as a way to find direction)
  and the night-1 check; 🟡 the October screens (direction, not size) and the checkpoint replay; ⚠️ the
  tell-book, counter-claim and private-note screens. Its biggest limit is single-case noise: the same vote
  prompt went to the right player in 8 of 10 samples on one run and 1 of 10 on the next.
- **One day** (the integration test). Replay one day live with the earlier days frozen, to see effects that
  build within a day. ⏸ designed in July 2026, not built.
- **[Whole games](evaluation_scopes/game/report.md)** (the end-to-end test). The same deals played with and
  without the change. Inside: why whole games, how one is set up, and three cases: the June memory A/B (the
  standard harness), the pre-registered v7 endpoint (the final test of the July memory loop, decided in
  advance), and small ten-seat runs (persona voices and evil covers, 8 deals each). It is the only way to see
  outcomes and effects that cascade across days, and it is noisy: 30 games a side show only a win gap of
  about 35 points. **Trust:** 🟡 the nine-seat memory harness (wins underpowered; pairing by deal buys
  little; the endpoint's statistic has no committed script); ⚠️ the ten-seat same-deal pairs.

**Read it when** you want to know which scope a question needs, or what a replay or a whole-game A/B can
claim.

##### Play metrics ([metrics](metrics/report.md))

**What it answers.** How well did the agents play, beyond who won? Code works out scores from the saved
game record (the share of votes on a real threat, a grade for each decision, how right a player's role
guesses were), so a score costs nothing and is the same for both sides of a comparison.

**What is inside.**
- Why code scores play: the win alone carries too much luck, and the early model judges could not tell
  memory on from memory off.
- The approach: each decision graded by the rules against the true roles, then each score checked against
  its side's win.
- Run 1, the nine-seat check (June to July 2026, 50 games then 180): the check chose the scores, 48 tried
  and 11 kept.
- Run 2, the ten-seat check (78 games, 2026-10-24): the rules define a good move and the check confirms or
  questions it.
- The scores in use today, including the read Brier score (how close a player's stated role guesses came to
  the truth), and the cautions that apply to every score.

**How far to trust it.** ✅ the town's lynch scores, power roles lost at night and wolves blending in: they
go with winning on both games. ❌ the healer's save rate on the ten-seat game, trusted on nine seats. 🟡 the
new roles' scores, too few games to test. 🟡 the read Brier score. ⚠️ the ten-seat decision grades: the
owner's table, applied exactly, never tested against winning as a whole. Counts are ✅, readings of them 🟡.

**Read it when** a report says agents played better or worse, and you want to know what was scored.

##### Experimental controls ([experimental_controls](experimental_controls/report.md))

**What it answers.** When two versions are compared, do they differ only in the change? The comparisons
here are small (about 30 games a side, or a few dozen frozen turns) and run at temperature 1.0, so one silent
change underneath can fake a result.

**What is inside.**
- The case that set the rules: on 2026-06-11 a fresh no-memory baseline came back with the villagers
  winning far less often than the original, on byte-identical prompts with no code change. Ten fresh deals
  gave 1 villager win in 10 against 20 in the original 30 (Fisher p = 0.0028); on the 20 deals played in
  both baselines, tested as pairs, the town's wins fell from 12 to 7 (exact McNemar p = 0.18). The outcomes
  moved; neither the size nor the cause (model drift on an alias that could not be pinned, or chance) is
  established, and because the two could not be told apart, the same-window rule followed.
- The comparisons the project runs (whole games, frozen-turn replays, model admission) and a table of which
  control applies to which.
- **When a comparison needs a fresh baseline**, the old version run again beside the new one. A check
  against a bar fixed in advance needs none; a comparison of two versions on the same day needs one only if
  something else changed, but still needs a measured noise floor; a comparison across days needs one. The
  page separates the two kinds of variability that spoil a comparison: a difference between the sides,
  which fakes an effect and is what the controls remove, and randomness within each side, which hides an
  effect and only sample size and a noise floor deal with.
- What pinning a model covers, per provider: Claude IDs are pinned snapshots (fixed weights, though the
  serving infrastructure can change); the Gemini flash-lite models and DeepSeek have nothing to pin to;
  Luna's page does not say.
- The controls, in five groups:
  1. The two sides differ only in the change: both in one time window, one change per side, the **arm
     guard** (two hard stops if a memory run's side is not set up as declared), the same deal from the same
     game id.
  2. Both sides are measured the same way: one judge scores both.
  3. The test can see the effect: the power gate (simulate a test before paying for it), paired statistics,
     a noise floor.
  4. A setting does what it names.
  5. The record: the **runtime fingerprint** (a stamp of model, backend, prompt version and commit on every
     record, checked during a run), provenance manifests (each result records its commit, config and a hash
     of every input file) and run graduation (a finished result copied into this record with its manifest).
- [variance_reduction_levers.md](experimental_controls/variance_reduction_levers.md): a dated audit of three
  statistical levers, kept for completeness.

**How far to trust it.** ✅ the arm guard, the in-run fingerprint, the power gate, same-deal seeding, and the
paired statistics' maths (pairing added almost no power). 🟡 the prompt snapshot (one prompt, the day
discussion) and run graduation (first used 2026-10-23). By hand: never comparing across prompt epochs
(stretches of fixed prompts), interleaving
a hand-run batch, and checking that a setting did what it names. One time window is built into the memory
experiment driver, and a frozen-turn replay runs both versions in one sitting; the general batch tool does
not alternate its sides, so other whole-game comparisons are interleaved by hand.

**Read it when** you want to know why a comparison can be believed, or which control a given A/B had.

#### Two worked workflows

A *workflow* here is a fixed sequence of the methods above, run again and again for one recurring question.
Most subjects have one: the leak checks for the information boundary live in
[`agent_boundaries/`](../agent_boundaries/report.md), the deduction engine's soundness tests in
[`gameplay/deduction/`](../gameplay/deduction/report.md), the memory A/B and its credit validators under
memory, and the labelling pipeline on its own page above. These two have their own pages because they answer
questions for the whole project and show the methods working together.

##### Factual errors ([factual_errors](factual_errors/report.md))

**What it answers.** How often do agents state something the game record contradicts, and does a fix reduce
it? A *factual error* is a statement the record shows is false, or reasoning that only makes sense if
something false were true ("we must find the last wolf" when both wolves are dead).

**What is inside.**
- What counts and what does not: guesses about hidden roles, talk about the past and deliberate lies are not
  errors.
- The four-step workflow, one section each:
  1. **Find** errors, by counting them on a sample of games (the July census: code flags every candidate
     statement, a cheap model reads each flag, a stronger model re-reads its positives, the owner checks) or
     by playing and reading games.
  2. **Freeze** failing turns as test cases: the nine-seat test set (129 cases) and the ten-seat pinned
     cases, each with a written expectation.
  3. **Diagnose** the cause: read whether the fact was in the agent's input; the October code audit found 12
     places where facts were lost on the way into a prompt (8 fixed in a day, 4 partly); replay the turn
     with one thing changed (the invented-check replay: 20 of 20 samples invented a check, 0 of 20 with the
     results reworded).
  4. **Check** a fix on the test set: the July ship test (48% of error-prone turns wrong before, 30% after,
     p = 0.003); the October versions, where a higher thinking budget cut bad samples from 82 to 27 of 267.
- What the labels can and cannot say, and what is not measured.

**How far to trust it.** ✅ the census screen within its scope. 🟡 the model reader and the test-set runs,
which are regression checks, not rates. ⛔ no factual-error rate on the ten-seat game. The only rate is from
July, nine-seat: about 3% of public messages (68 of 2,292) and about 4% of private notes. What was tried
against the errors and what worked is in [the gameplay report](../gameplay/report.md).

**Read it when** you want to know how a hallucination was found, counted, diagnosed or shown fixed.

##### Model admission ([model_admission](model_admission/report.md))

**What it answers.** May a model do one of the game's jobs (play a seat, vote, write the day summary,
extract memory, judge), and with which settings? In industry this is model migration, asked as five
questions.

**What is inside.**
- One section per question: **quality** (replays of saved turns against the current model, vote replays
  scored by code, real games, the thinking-level search for votes); **integration** (can the code use it:
  test prompts per calling mode, on short prompts and real turns); **cost and speed** (prices with cache and
  batch rates, cost per game, seconds per call, the stage's waits from served games' traces);
  **reliability** (rate limits, the rescue model, the backup key, drift guards); **rollout and records**
  (the model catalogue as a switch, dated notes per model).
- The one-command check per candidate (built 2026-10-24), with pass criteria fixed in its config before the
  run.
- The summariser and memory-job model choices, and what was not done against common practice.
- [data/](model_admission/data/README.md): the raw output of every admission run.

**How far to trust it.** 🟡 as a gate, not a ranking: it can reject a clearly worse model but not rank close
ones, because two runs of one model on the same 70 turns differed by about 6 points. ✅ the rescue path,
deployed. ⚠️ the summariser and memory-job comparisons, the seat-model games and the live schema check. ⏸ the
one-command check, built and never run on a candidate. While the project is experimental, a model is dropped
only for cost, latency or integration; quality is measured and recorded.

**Read it when** you want to know why a model is on the menu, or what a switch would need.

#### Other records in this folder

- [experiment_log.md](experiment_log.md): the previous hub and source map, kept whole as they stood on
  2026-10-23 and 24.
- [source_map.md](source_map.md): the data every method reads, the retired and archived records, and the
  records outside version control.
- Dated records, kept for provenance and not part of the current methods: [`loop/`](loop/report.md) (the
  checks on the July 2026 learning loop; part of the memory chapter), [`hardening_pass/`](hardening_pass/report.md)
  (the July review of the memory methods), and the retired discussion tagger
  ([llm_judge/discussion_tagger.md](llm_judge/discussion_tagger.md)).

---

### Choosing the method: two rules

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

### What the methods caught about themselves

The strongest evidence that the evaluation is real is that it repeatedly found its own faults.

**June and July 2026 (nine-seat, memory):**
- A fresh no-memory baseline came back with the villagers winning far less often than before, on
  byte-identical prompts with no code change: 1 of 10 fresh deals against 20 of the original 30 (Fisher
  p = 0.0028). On the 20 deals played in both, tested as pairs, the town's wins fell from 12 to 7 (exact
  McNemar p = 0.18), so the shift's size and cause were never established: drift on the model alias, which
  could not be pinned, or chance. Old baselines were dropped, and comparisons since run both sides in one
  time window (enforced in code by the memory-experiment driver and the replay tools, by hand elsewhere).
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

### Cross-cutting findings

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
- **One case resampled, read as many situations** (a vote from the deduction engine's second acceptance
  case).
- **Keyword counts of meaning** (32 against 4 of 124).
- **A frozen transcript hides what follows:** abstains ran 12–18% on frozen turns against 31% in live games.

### What we would do differently next time

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

*Rewritten 2026-10-24 as a standalone overview; restructured 2026-10-25 into one block per method page, with
the three questions the evaluation answers. The previous hub (2026-10-23), including the dated
memory-campaign section, is kept whole in the [experiment log](experiment_log.md), Part 1. The memory
campaign's verdicts live in [`memory_system/report.md`](../memory_system/report.md) and
[`../memory_system/v7/execution_plan/report.md`](../memory_system/v7/execution_plan/report.md): in short, June's memory improved the town's
decisions but not significantly its wins, the v6 store did not repeat it, and the pre-registered v7 endpoint
found no compounding, leaning toward harm; the ten-seat memory has not been tested at scale.*
