# Sampled review: the working record

*This is the full trust write-up as it stood on 2026-10-23, kept whole: every screen's or read's
mechanism, numbers, corrections and code paths. The plain summary is [report.md](report.md), written
2026-10-24 from this text.*

*Widened 2026-10-23 to every blind or sampled read: the July case sampler, the October blind packet
reads, hand-read games, rubric reads, and sampled reads of memory stores and credit. Written 2026-06-30
for the case sampler alone, with a build note of 2026-07-02; that text is kept below as the record,
with dated corrections.*

**What this page covers.** Checks where a reader goes through a sample of cases one by one and labels
them against a fixed list of questions (a rubric). This page covers how the cases are picked, how the
reads are recorded, and how far to trust them. In the October reads the readers are Claude subagents
started from the working session, not people. That means no per-call API charge; the reads are covered by the owner's
Claude subscription.

There are four groups:

1. **The case sampler** (nine-seat game, built July 2026). Can we pick cases to read by a fixed rule
   that cannot see who won, so the sample is not tilted toward cases that flatter a change?
2. **Blind packet reads** (ten-seat game, October 2026). When two versions of a prompt are compared,
   which version's lines does a reader label as better or worse, if the reader cannot tell which
   version wrote each line?
3. **Hand-reads with the true roles visible** (ten-seat Phase 3 games, 2026-10-10; eight-seat
   discussion games, 2026-06-05). Read whole games: what decided them, and which kinds of mistake do
   players make?
4. **Sampled reads of memory** (ten-seat v8 memory, October 2026; nine-seat credit, July 2026). Are
   the stored lessons and the lessons fetched for a turn correct and relevant? When a player says it
   followed a lesson, did it?

This page rates **how far each check can be trusted**. What each read found is in the design folder
named in its section. How all the evaluation reports fit together: [the hub](../../report.md). Where each
claim in these reports comes from: [the source map](../../source_map.md).

| Check | Trust | Main limit |
|---|---|---|
| Case sampler (Instrument 1) | — | Built and tested, but never used for a real review, so not rated |
| Blind packet reads (Instrument 2) | 🟡 | One model reader per item. Agreement between readers never measured |
| Phase 3 game reads (Instrument 3) | 🟡 for finding failure modes, ⚠️ for the counts | Counts come from different readers, with no agreement check |
| Discussion-quality gate (Instrument 3) | 🟡 for the pattern, ⚠️ for any number | Read by the person who built it, who knew which design was which; 4 games each |
| v8 memory reads (Instrument 4) | 🟡 | Before and after were read by different readers; no owner pass on record |
| Credit spot-check (Instrument 4) | ⚠️ | Only 15 claims; the true error rate could be as high as about 36% |
| Decision-tag read (Instrument 4) | ✅ against a bar set beforehand | 98 of 102 tags agreed; model readers, not a human; six games |

**Bottom line.** In July this kind of review was underbuilt (⛔). That no longer holds: since October
2026 the blind packet read has a fixed method and a full record on disk (seeded samples, a key file
that hides which version wrote each line, the readers' answers, and code that matches them back). It
is now the main way play quality is judged. It stays 🟡 for three reasons: each item is read by one
model reader, nobody has measured how often two readers agree, and no read has been checked against
the owner's own labels.

## Where this sits

The eval system judges quality on a three-rung ladder, cheapest first: ① an LLM judge scoring against
a rubric ([`../../llm_judge/report.md`](../../llm_judge/report.md)), ② sampled review by a person or a
stronger model (this folder), ③ golden labels ([`../report.md`](../report.md)). In
July, rung ② had no system behind it, and that gap was this report's headline. In October it became
the rung most play-quality decisions rest on.

**What "human" means here (2026-10-23).** In the October reads the readers are Claude subagents (Sonnet
or Opus) launched from the working session, not people. The owner sets the question and often the
rubric, and rules from the summaries. No record was found of the owner reading a packet item by item.
The human-labelled keys in the project (the dedup keys, the census read, one game of the tell-detector
cases) are all nine-seat, May to July 2026, and are catalogued in [`../report.md`](../report.md)
(*corrected 2026-10-23*: this sentence said the tell-detector golden was the only owner-labelled read). Reading this rung as "sampled review by a stronger
model, spot-checked by the session" is accurate; reading it as human review is not.

## The July 2026 record (nine-seat): why rung ② needed building

### What it is

Pull a handful of real decision cases, put each in front of a **human** *and* an **advanced model** (a
stronger LLM than the one being judged), and read them — "does this situation summary actually read like the
right retrieval query? did this extraction invent anything? is this merge faithful?" It is the modality that
answers the questions an automated judge can't: **information gain, subtle fabrication, and "does this read
right to a person."**

### Why it matters — it was the actual workhorse of v5→v7

Most of the *qualitative* design calls in the memory pipeline were made this way, not by a judge or a golden
set: extraction-selection phrasing, situation-summary wording, the dedup "tricky cases", the day-summary
saturation diagnosis. When you change a prompt or add a dimension you rarely have a golden set for the new
question, and the LLM-judge is itself uncalibrated (→ `../../llm_judge/`), so the honest fallback is to **read
the cases**. That is rung ② doing the real work.

### The gap — why it's the weakest rung despite carrying the most weight

It was **used** as a methodology but never **systematised**, and that costs it on two axes:

1. **No principled sampler.** *Which* cases got reviewed was ad-hoc — whatever was on hand, or eyeballed
   outliers. With no disciplined selection there's selection bias: you tend to read the cases that confirm the
   change, and an unrepresentative handful can't generalise. **This is the missing piece the build targets.**
2. **No durability, no record.** The review happened in a terminal / a chat and left **no artifact** — so its
   findings aren't reproducible or citable as evidence, only as judgment.

And it is **not cheap**: needing a human *and* a pro-LLM per case, it costs about what golden-labelling costs —
**without** golden-labelling's reusability. So in practice it was a **compromise**: reached for when a full
golden set wasn't worth building, but inheriting the cost without the rigor. That trade is defensible for
one-off diagnosis; it is *not* a substitute for a golden set, and the reports that lean on it say so.

> **Correction (2026-10-23).** Both gaps describe the v5–v7 memory reads, and they stay true of those.
> Gap 2 no longer holds for the October reads, which keep packets, keys and verdicts on disk. Gap 1 is
> half closed: October draws are seeded, but the pools they draw from are usually chosen failure cases
> (see "How far to trust the reads"). The cost point also changed: subagent reads launched from the
> session make no API call, under the owner's budget rule ("no API judge").

### How much to trust it (July)

As a *lens* it is the strongest of the three — a human catches what a machine judge structurally cannot. As a
*measurement* it is the weakest: unsampled, unrecorded, unreproducible. The correct reading of any rung-②
finding is **"a real signal a person saw," not "a metric."** Hardening it (below) is what would let it produce
evidence, not just judgment — and the same sampler is the front door that *feeds* rung ③ (you sample a cohort,
then either eyeball it here or promote it to a golden set).

## Instrument 1: the case sampler (built 2026-07-02, nine-seat)

The build — a deterministic case **sampler** (select → cohort → replay → surface) plus a recorded review
loop — is specified in [`plan.md`](plan.md).

**BUILD — 2026-07-02: the sampler exists (status flip: "not built" → "built, smoke-tested").** The two
gaps this report named — **no principled sampler** and **no durable record** — both close:

- **Code (the reusable logic):** [`../../../../evaluation/src/diagnosis/sampler.py`](../../../../evaluation/src/diagnosis/sampler.py)
  — the four steps as importable functions. **SELECT** on two combinable, outcome-blind signals:
  a deterministic per-case decision score (`decision_scoring.score_vote`/`score_night_target`, the
  DEFAULT) plus a **computed** leverage anchor (`is_swing`/`distance_to_parity` via
  `query_criticality`, never the LLM situation-dimension fill — Phase 1 showed the wolf-side `is_swing`
  fill scores 0.606, worse than the always-False constant). The application-judge score is an **opt-in**
  outlier source, flagged `(uncalibrated)` in every output because that judge's calibration is a later
  phase. `assert_outcome_blind` makes the halo rule executable — selecting on `winner`/`won`/… raises.
  **COHORT** via `data.sampling.sample_cases` (stratified, seed-deterministic). **REPLAY**
  (`replay_case_stage`) is wired to the live `replay/` harness but **guarded default-OFF** (refuses
  unless `enabled=True` after spend sign-off — the `dimension_audit --regen` discipline; building is $0).
  **RECORD** = `ReviewVerdict` + `append_verdict` to a durable local JSONL.
- **CLI:** `eval-case-sample` (thin: args → pipeline → files).
- **Smoke ($0, real local sidecar data — `batch_results/ab_nh_town.jsonl`, read-only):**
  [`sampler_smoke/`](sampler_smoke/) — `review_packets.md` (9 human-readable packets), `cohort_strata.json`,
  and `verdicts.jsonl` (one demo verdict exercising the record path). The 9-case cohort drew from all three
  channels — **by reason:** 3 `outlier:decision_score` · 3 `leverage:is_swing` · 4 `cohort:stratified`;
  **by role:** vigilante 3 · healer 3 · investigator 2 · villager 1; **by phase:** day_vote 4 · night_action 3
  · day_discussion 2; **by game-phase:** late 5 · early 4.

> **Corrections (2026-10-23).**
> - **Paths moved.** The CLI is `evaluation/src/cli_runner/diagnosis/case_sampler.py`, registered as
>   `eval-case-sample` (`pyproject.toml`); the July link to `evaluation/src/experiments/case_sampler.py`
>   is dead. The tests are at `tests/evaluation/test_diagnosis_sampler.py`. The July regenerate command
>   names the old path; run it as
>   `poetry run eval-case-sample --batch batch_results/ab_nh_town.jsonl --out evidence/evaluation/labeling/sampled_reads/sampler_smoke --n-outliers 3 --n-leverage 3 --cohort-max 4 --seed 0 --emit-demo-verdict`
>   (the flags are the July ones; not re-run for this widening).
> - **The reason counts add to 10 for 9 cases**, so at least one case carries two reasons.
> - **Never used for a real review.** The smoke run, with one placeholder verdict, is the only record of
>   the sampler running. The "upcoming v5/v6/v7 + eval concurrent review" it was built for did not use
>   it (`writeup/_planning/triage.md`, row 68). It reads nine-seat batch records only. The October reads below
>   drew their own seeded samples inside each runner instead.

**What it can claim.** Selection that cannot see the outcome, by construction: `assert_outcome_blind`
raises if a selection signal names the winner. That turns the outcome-halo rule (a sample chosen by
whether the side won measures the win, not the property) into code.

**Trust: built, tested, unused.** It has earned no rating, because no review has run on it.

## Instrument 2: blind packet reads (ten-seat, October 2026)

### How it works

Every October screen that needed a judgment on free text used the same five steps. The runner code
is in `evaluation/experiments/`; the records are in the `data/` folders named below.

1. **Generate.** Replay frozen turns (or play games) under each arm and save every sample to a JSONL.
2. **Draw.** A seeded draw picks the items when there are too many to read (silence calibration: 40
   passes per round, every held line, 25 posted lines per round).
3. **Packet.** Shuffle the samples with a fixed seed, give each an opaque id, and write packets that show
   what the speaking seat could see (the public record, earlier summaries, today's discussion) and the
   line. The arm, the speaker's role and its private record are left out. A *blind key* file maps each
   opaque id back to arm, turn and sample.
4. **Read.** Each packet goes to one reader subagent with a rubric of fixed labels. Readers write one
   JSON verdict per item, usually with a short quote or reason.
5. **Unblind and score.** The runner's `score` command joins verdicts to the key and counts per arm.

A *blind read* in this file means steps 3–5: the reader does not know which arm produced the line.

### Where it was used

| Read (2026-10) | Readers | Items | Record |
|---|---|---|---|
| Deduction-block placement (10-17) | 1 subagent, measures fixed in the README before the run | 24 samples | [`gameplay/deduction/data/deduction_placement/`](../../../gameplay/deduction/data/deduction_placement/results.md) |
| Private-note rewrite (10-16/17) | 2 Claude subagents, the owner's rubric | 56 samples per arm | `gameplay/deduction/data/note_prompt/judging/`; [`gameplay/deduction/experiment_log.md`](../../../gameplay/deduction/experiment_log.md) §6 |
| Silence calibration, step 1 (10-18) | 4 Sonnet subagents, kinds A–D plus "worth hearing" | 156 lines | [`silence_calibration/README.md`](../../../gameplay/data/silence_calibration/README.md) |
| Evil-cover screen, steps 1–5 (10-18) | 4, 8, 4 and 4 Sonnet subagents | 41 turns × 2 samples per arm | [`evil_cover_screen/README.md`](../../../gameplay/data/evil_cover_screen/README.md) |
| Voice rewrite (10-18) | 4 Sonnet subagents (2 naturalness, 2 fidelity) | 90 rewrites | [`voice_rewrite/README.md`](../../../gameplay/data/voice_rewrite/README.md) |
| Persona line (10-18) | 4 Sonnet subagents | 30 voiced pairs + 10 plain pairs | [`persona_line/README.md`](../../../gameplay/data/persona_line/README.md) |
| Visit wording, arms A/B and A/C (10-21) | 8 subagents, then 4 fresh ones | 95 lines per arm per model | [`visit_wording_ab/README.md`](../../../gameplay/data/visit_wording_ab/README.md) |

These screens are catalogued as replays in [`../../evaluation_scopes/turn/report.md`](../../evaluation_scopes/turn/report.md);
this section rates only their read. The decision-tag check (one Sonnet reader per game naming each
decision without seeing the tag, against a 90% bar set beforehand) uses the same pattern; it is
under Instrument 4 below.

### What it can claim

Counts of labelled kinds per arm, with the arm hidden from the reader, and a verbatim line behind every
count. A screen can say that one arm's lines were judged to deny less, restate more or change a fact
more often, at the stated n. It cannot give a calibrated rate: the labels are one model's reading of a
rubric, and nothing has measured how often a second reader would agree.

### Design features that make a read checkable

- **A noise floor inside the read.** The persona-line screen judged plain-against-plain pairs alongside
  voiced-against-plain. Two plain replies differed in stance in 3 of 10 pairs; voiced against plain, 9
  of 30. Without the baseline, "30% of voiced replies change stance" would have read as a content effect.
- **Measures fixed before the run.** The placement screen wrote its measures into the README before
  generating anything.
- **A deterministic check beside the read.** The voice-rewrite screen ran a code gate (same players,
  nights and role words) next to the fidelity readers. The readers found 19 of 90 rewrites changed
  something a listener could act on; the gate caught 1 of those 19. The read exposed the gate's blind
  spot, which a gate-only check would have missed.
- **A free ground truth where one exists.** The evil-cover games counted claims from the seat's own
  structured claim field, so the headline count needed no reader.

## Instrument 3: hand-reads with the truth visible

Two reads were not blind, by design: the reader needed the true roles or knew the arm.

**Phase 3 game reads (ten-seat, 2026-10-10).** Twenty-five games rendered as readable transcripts by
`evaluation/experiments/phase3_render_transcript.py`, showing true roles, claims, notes and night actions.
Five games were read for what decided them (Claude read one; four Opus agents read four). Ten more were
audited by five Opus agents, two games each, on a five-way rubric: invented fact, summary error, invalid
deduction, evil deception (deliberate or self-misunderstood), night error. Six Flash and four Luna games
followed on the same rubric, and eleven odd votes were read against each voter's own reasoning.
Record: [`phase3_reads/README.md`](../../../gameplay/data/phase3_reads/README.md).
- **Checked:** the main session checked the readers' decisive and spot quotes against the transcripts
  before use. The README's review note (2026-10-10) names three ways the counts mislead: invalid
  deductions made on top of a corrupted summary are not separated from reasoning errors; defeasible
  reads ("I trust them more") were sometimes counted as errors, so that count is probably high; and
  most errors concern new roles, which the counts cannot separate from general over-inference.
- **Not kept:** the rubric as a file and the readers' own reports. Only the README's tallies and the
  transcripts are stored.
- **Trust: 🟡 for finding failure modes, ⚠️ for the counts.** A quoted, checked example establishes
  that a failure happens. The per-game counts come from different readers with no agreement check.

**Discussion-quality gate (eight-seat, 2026-06-05).** A hand-judged comparison of four concurrent and
four sequential discussion games against [`rubric.md`](../../../gameplay/discussion/quality_gate/rubric.md)
(redundancy, responsiveness, dogpiling, turn fairness), with deterministic counts from
`quality_gate/scripts/metrics.py` (lexical echo rate, top speaker's share, longest same-speaker run).
Record: [`quality_gate/experiment_log.md`](../../../gameplay/discussion/quality_gate/experiment_log.md).
- **Limits it states:** the reader was the implementer, who had a stake in the outcome, and knew the
  arm; N=4 per arm, unpaired; the concurrent games' backend and temperature were not recorded.
- **Checks it states:** the scored claims are deterministic counts; every qualitative call quotes a
  verbatim excerpt a reader can re-check; the strongest case for the losing design is argued on the record.
- **Trust: 🟡 for the structural claim, ⚠️ for any quantitative delta.** The verdict rests on a pattern
  present in all 8 games (blind same-round repetition in concurrent play), not on a number.

## Instrument 4: sampled reads of memory (nine- and ten-seat)

These reads ask whether stored or retrieved memory is right, so the reader sees the rules and, where
needed, the true roles. They are sampled reads, not blind comparisons.

- **v8 retrieval relevance (ten-seat, 2026-10-12).** `evaluation/experiments/v8_gate_lookups.py` drew
  96 of 352 lookups, stratified by model, role and phase. Four Sonnet subagents read them against the
  rules with the games' true roles, labelling each lesson's fit, the situation's errors and any leak.
  The runner names a second reader, the owner, after the subagents; no record of that owner pass was
  found. Record: [`memory_system/v8/experiment_log.md`](../../../memory_system/v8/experiment_log.md) (the
  gate), `memory_system/v8/data/gate/read/`.
- **v8 store reads (ten-seat, 2026-10-13).** `evaluation/experiments/v8_reextract_reads.py`: four Sonnet
  subagents, each a quarter of the store's cells, read the 40-game store's 605 points for wrong rules and
  duplicates, and re-read the 96 lookups' fit against the larger store. The log states two limits:
  the fit re-read used different readers, so the before-and-after comparison is approximate; and the
  quarters flagged 4 and 13 rule errors, a spread that mixes reader and cell differences. The readers'
  65 duplicate groups were later used as a reference set for the point dedup (catalogued in
  [`../report.md`](../report.md)). Record: same log; `memory_system/v8/data/reextract/`.
- **Credit attribution spot-check (nine-seat, 2026-07-13).** Fifteen "I followed this lesson" claims
  drawn with a fixed seed (20260713) from 2,387 eligible ones; a model compared each lesson with the
  decision taken. Record: [`credit/attribution_spot_check.json`](../../../credit/attribution_spot_check.json),
  [`credit/report.md`](../../../credit/report.md) §5, which states the bound: at 13 of 15 the true mismatch
  rate could be as high as about 36%.

**Trust: 🟡 for the v8 reads** (stratified, recorded per part, limits stated in the log); **⚠️ for
the spot-check** (n=15, as its own report says).

### The decision-tag read (2026-10-13, ten-seat)

*Moved here on 2026-10-23 from the dissolved `dimension_extraction/` (its §5).*


**What it is.** After the halo ruling, each observation must name the decision it describes. Future
extraction picks it from the seat's own recorded decisions. The 2,277 observations of the 40 games
already extracted were tagged after the fact by Claude Haiku 5.5, one batched request per game with its
saved input (`scripts/tag_observation_decisions.py`; $0.08). The tags feed the verdict-halo measure and the
planned computed `uses_left` count ([`../../deterministic_audits/experiment_log.md`](../../deterministic_audits/experiment_log.md) §5c–d).

**How it works.** Two checks.
- **Free checks against the record**, by code: 2,100 tags match a decision the saved input records, 151
  match none (mostly limited-use roles declining a night action, which leaves no line), 26 name a pattern
  over several. Where the observation's own text states one day, the tag agrees 94.7% on nights (476
  cases), 96.3% on votes (430) and 96.8% on discussion (469).
- **A blind read** (`evaluation/experiments/v8_decision_tag_check.py`): six games at random, 17 random
  observations each, plus up to ten flagged ones per game (unmatched, or disagreeing with the stated day).
  The runner writes one reader file per game with the tags removed; one Claude Sonnet reader per game
  names each observation's decision from the record; the runner scores the answers against the tags.
  Data: `memory_system/v8/data/decision_tags/`.

**What it showed.** 98 of 102 random tags agree (96.1% ± 3.8%), and the day alone 101 of 102, against a
bar of 90% set before the read. Three of the four disagreements are a wolf's night tagged "several" where
the reader chose one skill; one is a healer protection put a night early. The flagged set agrees 24 of
25: the unmatched tags were mostly real declines, and the text check's disagreements were mostly its own
misreading of a day mentioned as background. Record: the v8 log, "Reopened" entry of 2026-10-13.

**Limits.** The readers are models, not a human; no human read of the tags is recorded. Six games is a
small draw, and the interval is the sampling interval only. The tags cover 40 games extracted on two
models (Gemini 3.8 Flash and Claude Sonnet 5.5).

## How far to trust the reads

**What has been checked.**
- **Re-reads by a different reader set moved some labels and not others.** Two screens re-judged the
  same lines with fresh readers. In the evil-cover screen, claim counts held exactly (13 and 33), but
  "explains the accusation or visit" moved from 29 to 19 of 73 lines in one arm and from 42 to 35 of 68
  in the other. In the visit-wording screen, the Haiku arm A's mechanics errors moved from 19 to 23 of
  95. Labels tied to an observable act (did the seat claim a role) are stable; labels needing judgment
  (does the line explain the visit) drift by several items between reader sets. Neither re-read was
  planned as an agreement test, so these are observations, not a measured agreement rate.
- **Partial blinding is disclosed when it fails.** In the note-rewrite read, the new notes' layout was
  visible and both readers noticed it; the log records that a reader who can see the layout may lean
  either way.
- **Quotes are checked.** Reader reports were spot-checked against transcripts in the phase 3 reads,
  and the voice rewrite's 19 changed lines were read against the originals.

**What has not been checked.**
- **Agreement.** Every read gives each item to one reader. No item set was read twice on purpose, so
  inter-reader agreement is not known for any rubric.
- **Calibration against a person.** No October rubric was compared with owner labels on the same items.
- **Selection.** Draws are seeded, but the pools are mostly chosen failure cases (the turns where a seat
  was pressured, the games that went wrong). A read says what an arm does on those turns, not across
  play. The July sampler's outcome-blind selection was not used for them.
- **Small n.** Most reads have 20–100 items per arm, and differences of a few items are inside the
  re-read drift above.

## Verdict + cheapest upgrade

**🟡.** The July verdict (⛔ underbuilt) no longer holds. The blind packet read has a fixed protocol and
leaves a complete record, and several reads carry their own controls: a plain-against-plain noise floor,
measures fixed in advance, a code gate run beside the reader. It stays at 🟡 because every number is
one model reader's label per item, with no measured agreement and no human anchor.

**Cheapest upgrades**, each small:
1. **Double-read a slice.** Give 30–40 items of one past screen (the silence calibration's 156 lines,
   say) to a second reader set and report agreement per label. The packets and keys are on disk, so this
   needs no new generation.
2. **Owner-label the same slice.** One sitting on those items would anchor the rubric to a person, the
   step rung ③ exists for.
3. **Keep the rubric and the readers' reports as files** in hand-read folders, as the packet reads
   already do.

## Sources

| What | Code | Record |
|---|---|---|
| Case sampler | `evaluation/src/diagnosis/sampler.py`, `evaluation/src/cli_runner/diagnosis/case_sampler.py` (`eval-case-sample`), `tests/evaluation/test_diagnosis_sampler.py` | [`plan.md`](plan.md), [`sampler_smoke/`](sampler_smoke/), `writeup/_planning/triage.md` (row 68) |
| Placement screen read | `evaluation/experiments/deduction_placement_screen.py` | `gameplay/deduction/data/deduction_placement{,_n10}/` |
| Note-rewrite read | `evaluation/experiments/note_prompt_cases.py` | `gameplay/deduction/data/note_prompt/judging/`; [`gameplay/deduction/experiment_log.md`](../../../gameplay/deduction/experiment_log.md) §6 |
| Silence calibration | `evaluation/experiments/silence_calibration.py` | [`silence_calibration/README.md`](../../../gameplay/data/silence_calibration/README.md), `packet_*.md`, `blind_key.json`, `verdicts_*.jsonl` |
| Evil-cover screen read | `evaluation/experiments/evil_cover_screen.py` (`packets`, `score`) | [`evil_cover_screen/README.md`](../../../gameplay/data/evil_cover_screen/README.md) |
| Voice rewrite read | `evaluation/experiments/voice_rewrite_screen.py` | [`voice_rewrite/README.md`](../../../gameplay/data/voice_rewrite/README.md) |
| Persona line read | `evaluation/experiments/persona_line_screen.py` | [`persona_line/README.md`](../../../gameplay/data/persona_line/README.md) |
| Visit-wording read | `evaluation/experiments/visit_wording_cases.py` (`blind`, `score`) | [`visit_wording_ab/README.md`](../../../gameplay/data/visit_wording_ab/README.md), `judge_rubric.md`, `key.jsonl` |
| Phase 3 game reads | `evaluation/experiments/phase3_render_transcript.py` | [`phase3_reads/README.md`](../../../gameplay/data/phase3_reads/README.md), `transcripts/`, `votes/dossiers.md` |
| Discussion-quality gate | `evidence/gameplay/discussion/quality_gate/scripts/metrics.py` (study code in the record) | [`quality_gate/experiment_log.md`](../../../gameplay/discussion/quality_gate/experiment_log.md), [`rubric.md`](../../../gameplay/discussion/quality_gate/rubric.md) |
| v8 relevance and store reads | `evaluation/experiments/v8_gate_lookups.py`, `v8_reextract_reads.py` | [`memory_system/v8/experiment_log.md`](../../../memory_system/v8/experiment_log.md), `memory_system/v8/data/{gate,reextract}/` |
| Credit attribution spot-check | — (sampling recorded in the file) | [`credit/attribution_spot_check.json`](../../../credit/attribution_spot_check.json), [`credit/report.md`](../../../credit/report.md) §5 |
