# Sampled reads: labelling once, to decide between versions

This page covers the one-off use of labelling: a reader goes through a sample of cases one at a time and
labels each against a fixed list of questions (a rubric), to decide between two versions of a prompt or
feature: which lines deny, which rewrites change a fact, what decided a game. The labels are used for that
decision, not kept as a reference; reusable labels are golden sets, on [the labelling page](../report.md),
which also explains the techniques both share (drawing items, hiding the source, fixing the rubric,
measuring agreement, anchoring to a person). This page says when a read is the right tool, how the October
reads were run, where they were used, and how far to trust them.

**Who the readers are.** In the October 2026 reads the readers are Claude subagents (Sonnet or Opus) started
from the working session, not people. The owner sets the question and often the rubric, and rules from the
summaries; no record shows the owner reading a packet item by item. So this is "sampled review by a stronger
model, spot-checked by the session", not human review. The project's human-labelled sets (the dedup keys,
the census read, one game of tell-detector cases, all nine-seat, May–July 2026) are golden sets, on
[the labelling page](../report.md).

The full write-up, with the July record, the case sampler's build notes and every read's detail, is the
[experiment log](experiment_log.md); the sampler's original plan is [plan.md](plan.md). The replays whose
lines these reads judged are in [turn replays](../../evaluation_scopes/turn/report.md). How it all fits together is in
[the hub](../../report.md).

## In short

- **Reading is the fallback when nothing cheaper can judge.** A new prompt question rarely has a golden set,
  and the LLM judges are uncalibrated, so most qualitative design calls in this project were made by reading
  cases.
- **In July it left no record** (⛔): reads happened in a chat window, on cases picked by hand. **Since
  October it has a fixed method**: seeded draws, packets that hide which version wrote each line, a key file
  that maps them back, the readers' answers on disk, and code that scores them. It is now the main way play
  quality is judged.
- **It stays 🟡** because each item has one model reader, nobody has measured how often two readers agree,
  and no October rubric has been checked against the owner's own labels.
- **Labels tied to an act are stable, labels needing judgment drift.** Re-read by fresh readers, "did the
  seat claim a role" held exactly (13 and 33); "does the line explain the visit" moved from 29 to 19 of 73.

## Quick view

| Read | Trust | Main limit |
|---|---|---|
| Blind packet reads (October screens) | 🟡 | One model reader per item; agreement never measured |
| Decision-tag read | ✅ against a bar set beforehand | 98 of 102 agree; model readers; six games |
| Phase 3 game reads | 🟡 failure modes · ⚠️ counts | Counts from different readers, no agreement check |
| Discussion-quality gate (June) | 🟡 pattern · ⚠️ numbers | Read by its builder, who knew which design was which; 4 games each |
| Credit spot-check | ⚠️ | 15 claims; the true error rate could be as high as about 36% |
| Case sampler | not rated | Built and tested, never used for a real review |

✅ sound · 🟡 usable with caveats · ⚠️ weak.

---

## 1. When to read cases

**The question:** a judge is cheap but uncalibrated, a golden set is trusted but slow to build. When is
reading a sample the right tool?

The project judges free text in three ways, cheapest first: an LLM judge scoring against a rubric
([llm_judge](../../llm_judge/report.md)), a sampled read (this page), and a golden set
([labelling](../report.md)). A read is right when:
- **the question is new**, so no golden set exists for it (a reworded card, a new voice line);
- **the quality is subtle**: a fabrication, a line that changes what a listener would do, "does this read
  like a person";
- **a one-off decision** is at stake, where building a reusable golden set would cost more than the decision.

It is not a substitute for a golden set: a read gives "a real signal a reader saw", not a calibrated rate,
and its labels are not reused. The same draw can feed the next rung, though: a sample read here can be
promoted to a golden set.

## 2. The approach: a read built so it can be checked

**The blind packet read** (October 2026), used by every screen that needed a judgment on free text:
1. **Generate.** Replay frozen turns, or play games, under each version, and save every sample.
2. **Draw.** A seeded draw picks the items when there are too many to read.
3. **Packet.** Shuffle the samples with a fixed seed, give each an opaque id, and show what the speaking seat
   could see and its line, never the version, the speaker's role or its private record. A **key file** maps
   each id back to version, turn and sample.
4. **Read.** One reader subagent per packet, with a rubric of fixed labels; one JSON verdict per item, usually
   with a quote or reason.
5. **Unblind and score.** The runner joins the verdicts to the key and counts per version.

**Four features that make a read checkable** (each used by at least one screen):
- **A noise floor inside the read.** The persona-line read judged plain-against-plain pairs beside
  voiced-against-plain: two plain replies differed in stance in 3 of 10 pairs, voiced against plain in 9 of
  30. Without the baseline, "30% of voiced replies change stance" would have read as an effect.
- **Measures fixed before the run.** The placement screen wrote its measures into its README before
  generating anything.
- **A code check beside the reader.** The voice-rewrite read ran a fact gate beside the readers; the readers
  found 19 of 90 rewrites changed something a listener could act on, and the gate caught 1 of them.
- **A free ground truth where one exists.** The evil-cover games counted claims from the seat's own
  structured claim field, so the headline needed no reader.

**Choosing what to read without bias.** A sample chosen by whether a side won measures the win, not the
property being read. The **case sampler** (built 2026-07-02, `eval-case-sample`) selects on outcome-blind
signals only (a code-scored decision grade and how much was at stake) and raises an error if a selection
signal names the winner. It was smoke-tested on nine-seat records and never used for a real review; the
October reads drew seeded samples inside each runner instead, mostly from pools of chosen failure cases.

## 3. Where reads were used

**Blind packet reads** (ten-seat, October 2026):

| Read | Readers | Items | What it decided |
|---|---|---|---|
| Deduction-block placement (10-17) | 1 subagent, measures fixed beforehand | 24 samples | Both placements fixed the original failures; neither difference large enough at n = 3 to rule on |
| Private-note rewrite (10-16/17) | 2 subagents, the owner's rubric | 56 samples per version | The rewrite added errors (15 → 27) |
| Silence calibration (10-18) | 4 Sonnet subagents | 156 lines | Held passes would have said something worth hearing 57% of the time, mostly new readings and questions, not new facts |
| Evil-cover screen, steps 1–5 (10-18) | 4–8 Sonnet subagents per step | 41 turns × 2 samples per version | Claims rose 13 → 33, denials fell 21 → 3 |
| Voice rewrite (10-18) | 4 Sonnet subagents | 90 rewrites | 19 of 90 changed a fact |
| Persona line (10-18) | 4 Sonnet subagents | 30 voiced + 10 plain pairs | More natural in 25 of 30, stance no more changed than noise |
| Visit wording (10-21) | 8 subagents, then 4 fresh ones | 95 lines per version per model | The wording was not the cause |

**The decision-tag read** (ten-seat, 2026-10-13). Every lesson extracted from 40 games was tagged after the
fact with the decision it describes (2,277 lessons, by Haiku, $0.08). Code checked the tags against the
record first: 2,100 match a recorded decision, 151 none (mostly limited-use roles declining a night action),
26 name a pattern over several; where the lesson states a day, tags agree 94.7–96.8%. Then one Sonnet reader
per game, for six random games, named each lesson's decision without seeing the tag: **98 of 102 random tags
agreed (96.1% ± 3.8%), against a 90% bar set before the read**; 24 of 25 flagged ones agreed too. Model
readers, not a human; six games.

**Hand-reads with the truth visible** (not blind by design):
- **Phase 3 game reads** (ten-seat, 2026-10-10): 25 games rendered as transcripts with true roles; five read
  for what decided them, ten audited on a five-way rubric (invented fact, summary error, invalid deduction,
  evil deception, night error), then six Flash and four Luna games, and eleven odd votes against each voter's
  reasoning. Quotes were checked against the transcripts before use; the record names three ways its counts
  mislead (errors built on a corrupted summary are not separated, hedged reads were sometimes counted as
  errors, most errors concern new roles). The rubric and readers' reports were not kept.
- **Discussion-quality gate** (eight-seat, 2026-06-05): four concurrent and four sequential discussion games
  read against a rubric, beside code counts. The reader built the design and knew which was which; the
  verdict rests on a pattern in all 8 games (repetition within a round in concurrent play), not a number.

**Reads of memory.** The v8 lesson-fit read and store reads became reference sets, so they are on the
labelling page ([Case 3](../report.md)). One read stays here:
- **Credit spot-check** (nine-seat, 2026-07-13): 15 "I followed this lesson" claims drawn with a fixed seed
  from 2,387; at 13 of 15 matching, the true mismatch rate could be as high as about 36%.

## 4. How far to trust the reads

**Checked:**
- **Re-reads by fresh readers moved judgment labels, not act labels.** Evil cover: claim counts held exactly
  (13 and 33), but "explains the accusation or visit" moved from 29 to 19 of 73 in one version and 42 to 35
  of 68 in the other. Visit wording: one version's mechanics errors moved from 19 to 23 of 95. Neither re-read
  was planned as an agreement test, so these are observations, not an agreement rate.
- **Failed blinding is disclosed.** In the note-rewrite read the new layout was visible and both readers
  noticed it.
- **Quotes are checked** against transcripts (Phase 3) and originals (the voice rewrite's 19 lines).

**Not checked:**
- **Agreement:** every read gives each item to one reader, so agreement is unknown for every rubric.
- **Calibration against a person:** no October rubric was compared with owner labels on the same items.
- **Selection:** draws are seeded, but pools are mostly chosen failure cases, so a read describes those turns,
  not play in general.
- **Small n:** 20–100 items per version, and differences of a few items are inside the re-read drift above.

## 5. What the reads taught

1. **Hide the version, keep the key.** Packets with opaque ids and a key file turned chat-window reading into
   a record that can be re-scored.
2. **Build the noise floor into the read.** Without the plain-against-plain pairs, a normal amount of stance
   change would have been reported as an effect.
3. **Count acts by code, read judgments.** Labels a field can answer (a claim) were stable; labels needing
   judgment drifted by several items between reader sets.
4. **A reader beside a code check finds the check's blind spot**, as the voice rewrite's gate showed.
5. **Set the bar before the read.** The decision-tag read is the one ✅ here because its 90% bar was fixed
   first.

## What we would do differently next time

| Stage | Change | What was done | What it would buy |
|---|---|---|---|
| Selection | **1. Draw from all play, not only failure cases, with the outcome-blind sampler** | Pools of chosen failures; the sampler unused | Reads that describe a version's play, not only its worst turns |
| Reading | **2. Double-read a slice of every rubric** (30–40 items by a second reader set) | One reader per item; two accidental re-reads | An agreement rate per label |
| Anchoring | **3. Owner-label the same slice once** | No October rubric checked against the owner | Each rubric tied to a person, the step golden sets exist for |
| Design | **4. Fix the measures and the bar before generating** | Done in the placement screen and the decision-tag read | Every read a test, not a description |
| Record | **5. Keep the rubric and the readers' reports as files** for hand-reads too | Packet reads keep everything; the Phase 3 reads kept only tallies | Every count re-checkable |

The tooling for items 2 and 3 now exists: the labelling pipeline's calibration step (`pipeline calibrate`)
compares a model source's labels with a person's, and owner-check packets for three model sources are
waiting in [`../owner_checks/`](../owner_checks/). A double-read of a past screen needs no
new generation, since its packets and keys are on disk.

**Bottom line.** Sampled reading went from the project's least recorded check to its main way of judging play
quality: blind, seeded, keyed and on disk. Its findings hold where the label is an act or the effect is large;
where a label needs judgment, the next step is a second reader and an owner-labelled slice.

## Sources

| What | Code | Record |
|---|---|---|
| Case sampler | `evaluation/src/diagnosis/sampler.py`, `evaluation/src/cli_runner/diagnosis/case_sampler.py` (`eval-case-sample`), `tests/evaluation/test_diagnosis_sampler.py` | [`plan.md`](plan.md), [`sampler_smoke/`](sampler_smoke/), `writeup/_planning/triage.md` (row 68); [log](experiment_log.md), Instrument 1 |
| Placement screen read | `evaluation/experiments/deduction_placement_screen.py` | `gameplay/deduction/data/deduction_placement{,_n10}/` |
| Note-rewrite read | `evaluation/experiments/note_prompt_cases.py` | `gameplay/deduction/data/note_prompt/judging/`; `gameplay/deduction/experiment_log.md` §6 |
| Silence calibration | `evaluation/experiments/silence_calibration.py` | [`silence_calibration/README.md`](../../../gameplay/data/silence_calibration/README.md) |
| Evil-cover screen read | `evaluation/experiments/evil_cover_screen.py` (`packets`, `score`) | [`evil_cover_screen/README.md`](../../../gameplay/data/evil_cover_screen/README.md) |
| Voice rewrite read | `evaluation/experiments/voice_rewrite_screen.py` | [`voice_rewrite/README.md`](../../../gameplay/data/voice_rewrite/README.md) |
| Persona line read | `evaluation/experiments/persona_line_screen.py` | [`persona_line/README.md`](../../../gameplay/data/persona_line/README.md) |
| Visit-wording read | `evaluation/experiments/visit_wording_cases.py` (`blind`, `score`) | [`visit_wording_ab/README.md`](../../../gameplay/data/visit_wording_ab/README.md) |
| Decision-tag read | `scripts/tag_observation_decisions.py`, `evaluation/experiments/v8_decision_tag_check.py` | `memory_system/v8/experiment_log.md` ("Reopened", 2026-10-13); `memory_system/v8/data/decision_tags/`; log, Instrument 4 |
| Phase 3 game reads | `evaluation/experiments/phase3_render_transcript.py` | [`phase3_reads/README.md`](../../../gameplay/data/phase3_reads/README.md) |
| Discussion-quality gate | `evidence/gameplay/discussion/quality_gate/scripts/metrics.py` (study code in the record) | [`quality_gate/experiment_log.md`](../../../gameplay/discussion/quality_gate/experiment_log.md), [`rubric.md`](../../../gameplay/discussion/quality_gate/rubric.md) |
| Credit spot-check | — (sampling recorded in the file) | [`credit/attribution_spot_check.json`](../../../credit/attribution_spot_check.json), [`credit/report.md`](../../../credit/report.md) §5 |
| Owner-check packets | `evaluation/src/labeling/{anchor,calibration}.py`, `pipeline calibrate` | [`../owner_checks/`](../owner_checks/) |

*Moved on 2026-10-24 from `evaluation/sampled_human_review/` into the labelling folder, its v8 memory reads to
the labelling page's Case 3. Rewritten 2026-10-24 as a plain summary of the 2026-10-23 write-up, which is kept whole as the
[experiment log](experiment_log.md).*
