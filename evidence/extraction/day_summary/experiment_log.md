# Day Summary — chronological overview

**What this is.** The spine of the day-summary quality workstream, in the order it happened: why the summary
needed evaluating, what each prompt version tested, what the judge could and couldn't tell us, and how the
two shipped decisions (structured output, and the generation model) were actually made. It ends where
[report.md](report.md) begins — that companion doc is the destination, the current truth of how day-summary
works in the code. The measurement apparatus itself is written up in
[../../evaluation/llm_judge/day_summary.md](../../evaluation/llm_judge/day_summary.md).

The raw dated lab notebook this narrative was distilled from is preserved verbatim in **Appendix A**, so the
curated arc and the original record can be read side by side.

**What day-summary is.** At the end of each day's discussion, before the vote, one LLM call condenses the
day's public talk into a structured summary. It is the *only* representation of a past day an agent ever sees
again, because raw transcripts are never re-shown, so an omission here is an omission for the rest of the
game. That single fact is why the workstream exists.

**The two channels.** Hard game-state facts (the vote tally, the elimination, the death-revealed role) do
*not* depend on this LLM: they are written deterministically by the game master at vote resolution and
appended to the same `day_summaries` stream. The LLM summary owns the *argumentative* content: accusations
and their reasoning, role claims, alliances, and village dynamics. Keeping that division in mind explains why
several apparent "completeness" failures below turn out not to matter.

**What "quality" means here.** From v2 on, quality was scored by an LLM judge on five 1-5 dimensions:
`completeness`, `accuracy`, `evidence_type_clarity`, `village_dynamics`, `epistemic_correctness`. Two of those
turned out to be presence checks on forced structure; three could actually move (§2, §7).

**Naming.** The **prompt** iterated v1→v4b. A separate **model bake-off** (§7) compared generation models
under the fixed v4b prompt. The **judge** model was gemini-2.5-pro throughout.

**Reading contract.** Sections are in time order, and each states what it tested and what it found. The arc
contains real corrections shown in place, not smoothed over: a word-limit hypothesis that was falsified (§3),
and a judge that proved unable to rank the versions it was built to rank (§5). For the current shipped state,
jump to [report.md](report.md).

---

## 0 · Origin — why the day summary exists, and why its quality mattered

The day summary exists for two reasons. First, it **bounds the context**: agents act over many days, and
re-feeding every earlier day's full transcript on every later prompt would make the context swell as the game
runs on, so each past day is compressed once into a fixed-size digest and only the current day is shown raw.
Second, it **turns dialogue into signal**: a raw discussion is mostly repetition, hedging, and social texture,
so a structured extract of the load-bearing facts is cheaper and cleaner for a downstream model to reason over
than the transcript.

That design has a consequence. The summary becomes the sole carrier of a prior day into every later decision:
agent prompts, the situation-summary query, and post-game extraction all read it, and none of them ever see
the raw transcript again. So its quality is a bottleneck for multi-day reasoning, yet it had never been
evaluated. Three things were unknown: did it capture all the strategically important content (completeness),
were its attributions correct (accuracy), and did its omissions propagate downstream (impact)? The
four-section v1 template had been written once and never revisited. Everything below is judged against one
bar: preserve what a later day needs, without inventing what didn't happen.

## 1 · v1 baseline — four fixed categories

v1 captured four fixed buckets: accusations, defenses, role reveals, and alliances. That was a defensible
first cut, but it asked for none of the *situation* signals the downstream consumers actually needed — how
much the village knew, how aligned it was, who was driving. Those signals are exactly what the
situation-summary query and post-game extraction were built to consume, so their absence was the root gap v2
set out to close.

## 2 · v2 — compose the situation standard, and build the judge

**Change.** v2 composed the shared `SITUATION_STANDARDS` document into the prompt and added a "Village
dynamics" section. This is the same standard the situation-summary and extraction prompts already used. A
hand comparison on 8 pairs confirmed it added real signal: every summary now stated whether the village was
information-rich or information-starved, described the consensus texture, and named who was driving versus
deflecting.

**The judge.** To score this at scale, a five-dimension LLM judge (gemini-2.5-pro) was built. Its first
result was already the shape of everything that followed:

| Dimension | Avg | Min |
|---|---|---|
| completeness | 4.56 | 3 |
| accuracy | 4.83 | 4 |
| evidence_type_clarity | 4.89 | 3 |
| village_dynamics | 5.00 | 5 |
| epistemic_correctness | 4.89 | 3 |

`village_dynamics` was pinned at a perfect 5.00, and `completeness` was the weak spot: the judge flagged
dropped vote actions and secondary accusers in 5 of 18 pairs (e.g. `0313eab5_day3`, `6a8635b0_day2`). The
reading at the time was that the word limit forced the model to triage, and it triaged away votes and minor
accusers.

## 3 · The word-limit hypothesis, falsified

If the model was triaging to fit a budget, raising the budget should help. It didn't. Bumped from 400 to 500
words, the model kept writing 130-230 words either way, and completeness didn't move (4.44 → 4.39). One
outlier even got worse. The limit was reverted. The lesson corrected the §2 diagnosis: the gaps are not a
budget problem, they are the model's **summarization priorities**. It chooses what to include, and a higher
ceiling doesn't change those choices.

## 4 · v3 — completeness fixes, and the noise floor

v3 targeted the two named causes. It clarified that past votes cited *as evidence* should be kept (the "no
vote tally" rule had been over-applied), and it told the model to list *all* accusers in a pile-on. It fixed
the two worst v2 cases (`6a8635b0_day2` 3→5, `0313eab5_day3` 3→4) but regressed others, and the averages
drifted slightly down within noise. The real finding was methodological: individual pairs swing ±1 between
runs from generation non-determinism, so at n=18 with a single run per pair, the deltas being chased (−0.11,
−0.22) were smaller than the noise.

## 5 · v4 — structured output, and the decision the judge couldn't make

**Change.** Free-text generation let the model choose what to include, and even "list ALL accusers" didn't
hold. v4 replaced the free-text field with structured extraction — separate `Accusation`, `RoleClaim`,
`Alliance`, and `VillageDynamics` entries — plus a deterministic serializer that rebuilds the text block
downstream expects. Forcing one entry per accusation makes pile-on participants hard to drop. Completeness
nudged up (4.44 → 4.50); one game regressed on epistemic (a confirmed-dead role labeled "unverified"), which
v4b then fixed.

**The decision.** Across v2, v3, and v4 the judge could not statistically distinguish any version. So the
call to keep structured output was made on **architectural** grounds, not judge deltas: a deterministic
format, forced enumeration, and fields that later code can parse. Falling back to a non-eval reason when the
instrument can't resolve a difference is the honest move, and it is the pattern that repeats in §7.

## 6 · v4b — targeted epistemic and vote-declaration fixes

v4b added a "confirmed by death reveal" epistemic tier and extended the vote rule to cover in-discussion vote
*declarations*, not just past references. The targeted fix landed cleanly (`04aabab0` day3 and day4 both
jumped epistemic 1→5). New low scores appeared on *different* pairs (a fabricated game-master announcement on
`8e437de2_day3`), which confirmed rather than contradicted the §4 finding: the residual movement is
generation non-determinism, not a remaining prompt gap.

## 7 · Model bake-off — thinking budget over model size

With the prompt settled, the last lever was the generation model. Four configs were scored under v4b
(judge = gemini-2.5-pro):

| Model | comp | acc | epis | latency (18 pairs) |
|---|---|---|---|---|
| flash-lite (minimal) | 4.50 | 4.61 | 4.72 | ~10 min |
| flash-lite (medium) | 4.44 | 4.89 | 5.00 | ~10 min |
| 3.5-flash | 4.78 | 4.78 | 5.00 | ~80 min |
| **2.5-pro** | **4.83** | **4.94** | 5.00 | ~120 min |

2.5-pro scored highest, but latency ruled it out. The decisive read was not the aggregate but a manual
inspection of failure cases: **medium thinking** on flash-lite removed the two most damaging modes of minimal
thinking — a fabricated game-master announcement (`8e437de2_day3`) and a dropped primary accuser
(`6a8635b0_day2`) — at no latency cost over minimal. So the choice was flash-lite with medium thinking: the
thinking budget bought the quality that mattered without paying the model-size latency tax.

---

## Recurring threads

- **Saturation is mechanistic, not uniform** (§2, §7) — the two dimensions that never move
  (`village_dynamics`, `evidence_type_clarity`) are presence checks on structure the prompt forces; the three
  that move are content checks against the transcript.
- **Noise ≥ signal at n=18** (§3, §4) — single-run-per-pair scoring swings ±1, so sub-0.2 deltas were never
  real.
- **Generation non-determinism, not prompt gaps** (§4, §6) — after v4, different pairs regress each run and no
  systematic gap remained.
- **Architecture and latency over judge deltas** (§5, §7) — both shipped decisions were made on grounds the
  judge couldn't provide, because it couldn't rank near-equal options.
- **Two channels** (throughout) — the LLM owns argumentative content and the game master owns the hard facts,
  which is why dropped-vote "completeness" failures are largely harmless.

## Artifacts

| Beat | Artifact | What it holds |
|---|---|---|
| §2 | `regen_comparison.json` | v1-vs-v2 hand comparison (the Village-dynamics signal) |
| §2-§7 | `eval_summary.txt`, `eval_results.jsonl` | per-dimension score tables + per-pair judge output |
| §7 | `eval_summary_31-flash-lite_medium.txt`, `eval_summary_35-flash.txt`, `eval_summary_25-pro.txt` (+ matching `eval_results_*.jsonl`) | the model bake-off, per config |
| all | `prompt_versions/` | checkpointed prompts v1 → v4b |
| destination | [report.md](report.md) | current shipped state + freshness/gap tracking |
| apparatus | [../../evaluation/llm_judge/day_summary.md](../../evaluation/llm_judge/day_summary.md) | the L1/L2 measurement write-up |

---

## Appendix A — Raw lab notebook (2026-05-27, verbatim)

> Preserved unedited as the original dated record, superseded by the curated narrative above. File paths and
> identifiers here are period-accurate (pre-refactor) and may not resolve against current code; the current
> pointers live in [report.md](report.md).

# Day Summary — Experiment Log

## Context

The day summary component condenses each day's public discussion into a
structured summary covering key accusations, defenses, role reveals, and
alliances. It runs once at the end of each day's discussion rounds, before
voting.

### Pipeline position

Day summaries are consumed by every downstream agent prompt as historical
context for decision-making:

```
Day discussion messages → Day summary (LLM extraction) → Agent prompts (all roles)
                                                        → Situation summary (query generation)
                                                        → Post-game extraction (episodic memory)
```

The summary is the only representation of prior days that agents see — they
never receive raw discussion transcripts from previous days. This makes
day summary quality a bottleneck for multi-day reasoning.

### Implementation

- **Prompt:** `Agents/prompts/extraction.py` — `DAY_SUMMARY_PROMPT`
- **Schema:** `Agents/schemas/output.py` — `DaySummaryOutput` (single `summary: str` field)
- **Node:** `Agents/nodes.py` — `summarize_day_discussion()`
- **Formatter:** `Agents/formatters.py` — `format_day_summaries()`

### What's missing

Day summary quality has never been evaluated. We don't know:
1. **Completeness** — does the summary capture all strategically important
   information from the discussion?
2. **Accuracy** — are attributions (who said/accused/claimed what) correct?
3. **Downstream impact** — do summary omissions or errors propagate into
   agent decisions or retrieval queries?

The current four-section template was designed once and never iterated on.
It may miss information categories that matter (e.g., tone shifts, implicit
suspicion, information asymmetry signals).

---

## Experiment: Day Summary Quality Evaluation

### Objective

Evaluate the quality of the current day summary prompt, identify systematic
gaps, and iterate on the prompt to improve downstream usefulness.

### Method

1. Update the day summary prompt to compose `SITUATION_STANDARDS` and add a
   "Village dynamics" section covering the dimensional framework.
2. Re-generate summaries on raw transcripts from `eval_sets/v4_filtering_eval.jsonl`
   (4 games, 8 day-discussion transcripts).
3. Qualitative comparison: old (v1) vs new (v2) summaries on the same transcripts.
4. Evaluate whether the new summaries preserve SITUATION_STANDARDS signals
   for downstream consumers.

### Dataset

Sources:
- `eval_sets/v4_filtering_eval.jsonl` — 40 cases across 4 game traces
- `eval_sets/v2_memory_wolfs_only_all_enabled_all_enabled.jsonl` — 40 cases across 4 game traces

18 transcript/summary pairs extracted (days with ≥5 raw discussion messages
that can be matched to their generated summaries via cross-day cases across
8 unique games).

---

## Log

### 2026-05-27 — Experiment initialized

- Created experiment folder at `evidence/extraction/day_summary/`
- Documented pipeline position and current implementation
- Built labeling tool: `evaluation/experiments/labeling/day_summary_labeler.py`
- Built re-generation tool: `evaluation/experiments/labeling/day_summary_regen.py`

### 2026-05-27 — v2 prompt: compose SITUATION_STANDARDS

**Problem:** The v1 prompt captured 4 fixed categories (accusations, defenses,
role reveals, alliances) but never asked for SITUATION_STANDARDS dimensions.
Downstream consumers (situation summary, agent decisions, post-game extraction)
need signals about information landscape, consensus texture, and agent exposure —
none of which v1 provided.

**Change:** Composed `SITUATION_STANDARDS` into `DAY_SUMMARY_PROMPT` via
`{situation_standards}` format variable (same pattern as post-game extraction
and situation summary prompts). Added "Village dynamics" section. Merged
accusations + defenses into one section. Bumped word limit 300 → 400.

- Original prompt checkpointed: `prompt_versions/v1_original.txt`
- Files modified: `Agents/prompts/extraction.py`, `Agents/nodes.py`

**Re-generation results** (8 pairs, old vs new on same transcripts):

The new "Village dynamics" section consistently adds three types of signal
that were absent from v1:

1. **Information landscape characterization** — every summary now explicitly
   states whether the village is information-rich or information-starved and
   what type of evidence is driving suspicion (e.g., "suspicion driven entirely
   by communication style", "concrete voting record evidence").

2. **Consensus texture** — summaries now describe village alignment (e.g.,
   "split into two distinct camps", "highly unified push against player_6",
   "fragmented, no unified consensus").

3. **Who is driving vs passive** — summaries now identify who is steering
   the discussion and who is deflecting or quiet (e.g., "player_1 is
   aggressively driving for specific targets", "player_8 is on the defensive").

Evidence type annotations on accusations (e.g., "(evidence type: voting record)")
make the information landscape explicit at the individual-accusation level too.

- Full comparison: `regen_comparison.json`

Also added lighter epistemic status rule to the prompt: role claims must
distinguish "claimed with public evidence" vs "claimed without evidence."
Full `EPISTEMIC_STATUS_RULE` doesn't apply (day summaries use player IDs,
not role descriptors).

### 2026-05-27 — v2 LLM judge eval (18 pairs)

Built day summary quality judge reusing existing eval infrastructure:
- Judge prompt: `evaluation/judges/prompts.py` — `DAY_SUMMARY_JUDGE_*`
- Judge runner: `evaluation/judges/day_summary.py`
- Experiment runner: `evaluation/experiments/day_summary_eval.py`
- Score schema: `evaluation/core/schemas.py` — `DaySummaryScores`

Five evaluation dimensions: completeness, accuracy, evidence_type_clarity,
village_dynamics, epistemic_correctness (each 1-5).

**Results (18 pairs, judge=gemini-2.5-pro):**

| Dimension              |  Avg | Min | Max |
|------------------------|------|-----|-----|
| completeness           | 4.56 |   3 |   5 |
| accuracy               | 4.83 |   4 |   5 |
| evidence_type_clarity  | 4.89 |   3 |   5 |
| village_dynamics       | 5.00 |   5 |   5 |
| epistemic_correctness  | 4.89 |   3 |   5 |

**Observations:**

1. Village dynamics scores **perfect 5.00** across all 18 pairs — the new
   section and SITUATION_STANDARDS composition work as intended.
2. Evidence type clarity and epistemic correctness near-perfect (4.89).
3. **Completeness is the weakest dimension** (4.56, min=3). The judge flagged
   specific omissions in 5 of 18 pairs:
   - `0313eab5_day3` (score=3): omitted that player_5 also voted for the
     Investigator — the primary rebuttal others used against player_5.
   - `6a8635b0_day2` (score=3): omitted that player_5 also accused players 7
     and 8 (secondary accusations simplified away).
   - `6a8635b0_day3` (score=4): omitted player_2 from the list of accusers.
   - `cdcd2c6e_day2` (score=4): framed a vote as an "accusation" — lost the
     strategic significance of an explicit vote action.
   - `cdcd2c6e_day3` (score=4): omitted final votes cast by players 6, 2, 8.
4. The completeness gaps share a pattern: **vote actions and secondary
   accusations are dropped when the model prioritizes fitting within the
   word limit.** The 400-word limit forces triage, and the model consistently
   deprioritizes votes and minor accusers.

- Full results: `eval_results.jsonl`
- Summary table: `eval_summary.txt`

### 2026-05-27 — v3 prompt: completeness fixes

**Problem:** Completeness gaps in v2 had two root causes:
1. "Do not include vote results" was over-applied — the model dropped
   references to past votes cited during discussion as evidence.
2. No instruction to be exhaustive about accusation participants — when 5
   players pile on, the model lists 3 and drops 2.

**Changes:**
- Clarified vote rule: "Do not include the formal vote tally... However, DO
  include when players reference past votes during discussion as evidence."
- Added to accusations section: "List ALL players who participated in each
  accusation — who joined a pile-on matters strategically."
- Checkpointed v2: `prompt_versions/v2_situation_standards.txt`

**Results (v3 vs v2, 18 pairs):**

| Dimension              | v2 avg | v3 avg | Delta  |
|------------------------|--------|--------|--------|
| completeness           |   4.56 |   4.44 |  -0.11 |
| accuracy               |   4.83 |   4.67 |  -0.17 |
| evidence_type_clarity  |   4.89 |   5.00 |  +0.11 |
| village_dynamics       |   5.00 |   5.00 |   0.00 |
| epistemic_correctness  |   4.89 |   4.67 |  -0.22 |

**Observations:**

1. The v3 changes **fixed the two worst v2 cases** — `6a8635b0_day2`
   completeness jumped 3→5, `0313eab5_day3` improved 3→4.
2. But **regressions appeared elsewhere** — `cdcd2c6e_day4` dropped 5→3
   (omitted a key logical statement), and two cases got epistemic=2
   (`6a8635b0_day3`, `8e437de2_day3` — stated roles as confirmed when
   they were only claimed).
3. **Evidence type clarity hit perfect 5.00** — the vote-reference rule
   clarification may have helped the model distinguish evidence types more
   precisely.
4. **Overall averages slightly worse** — but individual pair scores shift
   ±1 between runs due to generation non-determinism. The signal is noisy
   at n=18 with single-run per pair.

**Diagnosis:** The remaining issues are:
- **Epistemic errors** are the most concerning — the model occasionally
  treats healer-save confirmations or role claims as fully confirmed facts.
  The lighter epistemic rule may need strengthening, or specific examples
  for the healer-save case.
- **Completeness gaps** appear random rather than systematic — different
  details are omitted each run, suggesting the 400-word limit forces
  triage and the model's prioritization varies.
### 2026-05-27 — Word limit bump: 400 → 500 (no improvement, reverted)

**Hypothesis:** Completeness gaps might be caused by 400-word limit forcing
the model to drop details.

**Finding:** The model writes 130-230 words regardless of limit — well under
both 400 and 500. Bumping to 500 had no effect on completeness (4.44 → 4.39).
The `8e437de2_day3` outlier actually got worse (accuracy 4→1, misattributed
a healer claim to the wrong player).

**Conclusion:** Completeness gaps are not about word budget. They reflect the
model's **summarization priorities** — it chooses which details to include,
and a higher ceiling doesn't change those choices. Reverted to 400 words.

| Dimension              | v3@400 | v3@500 |
|------------------------|--------|--------|
| completeness           |   4.44 |   4.39 |
| accuracy               |   4.67 |   4.56 |
| evidence_type_clarity  |   5.00 |   4.94 |
| village_dynamics       |   5.00 |   4.83 |
| epistemic_correctness  |   4.67 |   4.78 |

### 2026-05-27 — v4: structured output extraction

**Problem:** Free-text generation lets the model choose what to include. Even
with explicit instructions ("list ALL accusers"), completeness averaged ~4.4
because the model's summarization priorities vary across runs.

**Change:** Replaced free-text `summary: str` with structured extraction via
`with_structured_output(DaySummaryOutput)`. New nested Pydantic models:
`Accusation`, `RoleClaim`, `Alliance`, `VillageDynamics`. Added deterministic
`_serialize_day_summary()` that converts structured output back to the same
string format downstream consumers expect.

Files modified:
- `Agents/schemas/output.py` — new nested models, redesigned `DaySummaryOutput`
- `Agents/prompts/extraction.py` — simplified prompt for structured extraction
- `Agents/nodes.py` — added `_serialize_day_summary()`, updated `summarize_day_discussion()`
- Checkpointed v3: `prompt_versions/v3_pre_structured.txt`

**Results (v4 structured vs v3 free-text, 18 pairs):**

| Dimension              | v3 avg | v4 avg | Delta  |
|------------------------|--------|--------|--------|
| completeness           |   4.44 |   4.50 |  +0.06 |
| accuracy               |   4.67 |   4.72 |  +0.05 |
| evidence_type_clarity  |   5.00 |   5.00 |   0.00 |
| village_dynamics       |   5.00 |   5.00 |   0.00 |
| epistemic_correctness  |   4.67 |   4.56 |  -0.11 |

**Observations:**

1. **evidence_type_clarity and village_dynamics remain perfect** (5.00) — the
   structured fields preserve the gains from SITUATION_STANDARDS composition.

2. **Completeness improved slightly** (4.44 → 4.50). The structured format
   forces separate `Accusation` entries, so pile-on participants are less
   likely to be dropped. But two `cdcd2c6e` pairs still score 3 — the model
   drops in-discussion vote *declarations* (distinct from vote references).

3. **Epistemic regression on `04aabab0` game** — day3 and day4 both score
   **1/5**. The model labels a *confirmed dead* Investigator's role as
   "unverified." Root cause: the prompt distinguishes "claimed with public
   corroboration" vs "unverified" but doesn't explicitly tell the model that
   **eliminated players' roles are revealed on death** and should be treated
   as confirmed facts, not claims. The Game Context section says this, but
   the role_claims extraction rules don't connect the dots.

4. **`8e437de2_day3` fixed itself** — the historically hardest case scored
   5/5 across all dimensions. The structured format may help with complex
   role-claim chains by forcing each claim into a separate structured entry.

5. **Completeness gaps on `cdcd2c6e`** — the model omits explicit vote
   declarations made during discussion (e.g., "I'm voting for player_3").
   The vote rule says to include past vote *references*, but doesn't cover
   new vote declarations within the current discussion.

### 2026-05-27 — v4b: epistemic + vote declaration fixes

**Changes:**
1. Added "Confirmed by death reveal" as the top epistemic tier — eliminated
   players' roles are confirmed facts, not claims. Instructed model not to
   list death-revealed roles as `role_claims`.
2. Extended vote rule to cover current vote *declarations* in discussion
   (not just past vote references).

**Results (v4b vs v4a, 18 pairs):**

| Dimension              | v4a avg | v4b avg | Delta  |
|------------------------|---------|---------|--------|
| completeness           |   4.50  |   4.50  |   0.00 |
| accuracy               |   4.72  |   4.61  |  -0.11 |
| evidence_type_clarity  |   5.00  |   4.89  |  -0.11 |
| village_dynamics       |   5.00  |   5.00  |   0.00 |
| epistemic_correctness  |   4.56  |   4.72  |  +0.16 |

**Targeted fix landed:** `04aabab0_day3` and `04aabab0_day4` both jumped
epistemic 1→5 — the death-reveal clarification resolved the systematic error.

**New noise emerged elsewhere:** `8e437de2_day3` fabricated a "Game Master
announcement" (accuracy=2, epistemic=2), and `6a8635b0_day3` mislabeled an
evidence type (3). These are different pairs from v4a's issues, confirming
this is generation non-determinism rather than a prompt problem.

Prompt checkpointed: `prompt_versions/v4_structured.txt`

### Current state (v4b structured output)

**Stable strengths (across all runs):**
- village_dynamics: 5.00 (perfect in every run since v2)
- evidence_type_clarity: 4.89-5.00

**Converged dimensions:**
- completeness: ~4.50 (up from v1 baseline, stable across v3/v4)
- accuracy: ~4.6-4.7
- epistemic: ~4.6-4.7

**Remaining variance is generation non-determinism at n=18 with single runs.**
Different pairs regress each run — no systematic prompt gap remains. Further
improvement likely requires model-level changes (fine-tuning, multi-pass
extraction) rather than prompt iteration.

**What the structured output accomplished:**
- Forces exhaustive enumeration of accusations (separate entries per accusation)
- Fixed the historically hardest case (`8e437de2_day3`) by decomposing complex
  role-claim chains into individual structured entries
- Deterministic serialization ensures consistent downstream format
- Schema field descriptions serve as implicit prompt instructions

**Decision:** Keep structured output (v4b). Judge scores across v2/v3/v4 are
within noise at n=18 with single runs — no version is statistically
distinguishable. Structured output is preferred for architectural reasons:
deterministic format, forced enumeration, and easier to extend for downstream
consumers that may parse specific fields. Epistemic correctness is deprioritized
because actual Game Master announcements are appended to the day dialogue
separately — the summary doesn't need to infer epistemic status.

### 2026-05-27 — Model comparison experiment

Added `--gen-model` and `--thinking` flags to the eval runner to test
different generation models with the same structured output prompt (v4b).

**Configurations tested:**
1. gemini-3.1-flash-lite, thinking=minimal (current default)
2. gemini-3.1-flash-lite, thinking=medium
3. gemini-3.5-flash (no thinking)
4. gemini-2.5-pro (no thinking)

**Results (18 pairs, judge=gemini-2.5-pro):**

| Model                   | comp  |  acc  | evid  |  dyn  | epis  |
|-------------------------|-------|-------|-------|-------|-------|
| flash-lite (minimal)    |  4.50 |  4.61 |  4.89 |  5.00 |  4.72 |
| flash-lite (medium)     |  4.44 |  4.89 |  4.94 |  5.00 |  5.00 |
| 3.5-flash               |  4.78 |  4.78 |  5.00 |  5.00 |  5.00 |
| **2.5-pro**             |**4.83**|**4.94**|**5.00**|  5.00 |  5.00 |

**Observations:**

1. **2.5-pro scores highest** — completeness (4.83) and accuracy (4.94).
   Three dimensions at perfect 5.00. But ~120 min for 18 pairs.

2. **3.5-flash is close** — completeness 4.78, accuracy 4.78, three
   dimensions perfect. But ~80 min for 18 pairs — a large latency increase
   over flash-lite for a marginal score gain.

3. **flash-lite (medium thinking) matches 3.5-flash quality at flash-lite
   latency** (~10 min for 18 pairs). Accuracy jumps 4.61→4.89 and epistemic
   hits perfect 5.00 vs minimal thinking. Completeness slightly regresses
   (4.50→4.44) but within noise.

4. **All models achieve perfect 5.00 on dynamics** — the structured output
   with SITUATION_STANDARDS is robust across model capabilities.

**Manual inspection of failure cases:**

Compared actual summaries on pairs where flash-lite (minimal) had issues:

- `6a8635b0_day2` (comp 3): minimal dropped player_1 from accusers list
  (the primary instigator). Medium thinking and 3.5-flash both include
  player_1 correctly.
- `8e437de2_day3` (acc 2): minimal **fabricated a Game Master announcement**
  about a healer save that didn't happen. Medium thinking produces no
  hallucination — correctly lists no role claims. 3.5-flash also correct.
- `cdcd2c6e_day2` (comp 3): all models miss the explicit vote declaration;
  medium thinking and 3.5-flash both score 4 (partial improvement).

The key distinction between flash-lite minimal and medium thinking: medium
thinking avoids hallucinations (fabricated facts) and accuser omissions.
These are the most damaging failure modes for downstream agent decisions
since day summary is the only representation of prior days agents see.

3.5-flash occasionally over-extracts (spurious "villager" role claims from
players just saying "I'm not a wolf"), while flash-lite medium thinking
produces cleaner output. 3.5-flash also adds ~70 min latency per eval run
for no meaningful quality gain over flash-lite medium.

**Per-pair files:**
- `eval_results_31-flash-lite_medium.jsonl` / `eval_summary_31-flash-lite_medium.txt`
- `eval_results_35-flash.jsonl` / `eval_summary_35-flash.txt`
- `eval_results_25-pro.jsonl` / `eval_summary_25-pro.txt`

**Decision:** Use flash-lite with medium thinking for day summaries. It
matches 3.5-flash quality on the dimensions that matter (completeness,
accuracy) at flash-lite latency. The thinking budget eliminates the two
worst failure modes of minimal thinking (hallucinated facts, dropped
accusers) without the latency cost of upgrading the model.

### Experiment complete
