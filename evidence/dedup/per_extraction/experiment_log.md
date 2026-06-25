# Per-extraction dedup — golden labels & prompt tuning (experiment log)

**What this is.** The detailed chapter behind beats **§3, §6, §7** of the
[dedup overview](../experiment_log.md): the **per-extraction** (online) dedup decision-maker — the LLM
that judges each newly extracted entry against its neighbours as a game ends — tuned against
human-anchored golden labels across prompt versions **v1→v11b**. The overview gives the highlights;
this gives all the load-bearing detail. The destination (how online dedup runs today) is
[../report.md](../report.md).

**Terms used throughout (anchored once).**
- **observation** vs **strategy point** — an observation is a *situation → approach → outcome*
  lesson-by-example; a strategy point is a reusable *situation → action* rule. They dedup differently,
  and observations carry an extra action (MERGE) that strategy points never do.
- **decision schemes** — the dataset was first recorded in a legacy `A/B/C/D`
  (DISCARD / REPLACE / DIFFERENTIATE / KEEP) scheme; this work uses **D / M / K**
  (DISCARD / MERGE / KEEP), and the endgame collapses it to **D / K**.
- **accuracy** — unless stated otherwise, *strict* accuracy = exact match against the human golden
  label. *Lenient* additionally accepts the `also_acceptable` second label on the few genuinely
  borderline cases.
- **prompt versions** v1→v11b are **per-extraction prompt** versions (not store versions, not the
  batch prompt). Replays run a frozen case set through a given (model × prompt-version).
- **the model roster** (it recurs in every table): **baseline** = `gemini-2.5-flash` (the model from
  the original 30-game batch); **production** = **flash-lite** = `gemini-3.1-flash-lite`; **strong
  comparison** = **3.5-flash** = `gemini-3.5-flash`; **rewrite judge** = `gemini-3.1-pro-preview`.

**Reading contract.** Roughly chronological. Prompt versions are shown **as they were tried** —
including the several that *regressed* — because the back-and-forth is the lesson, and twice the
"failures" turned out to be **mislabelled golden data**, not bad prompts. The arc converges on removing
MERGE; the synthesis (lessons, the still-open discard-vs-keep question, live state) is at the **end**,
after the full chronology.

**The shape of the journey (so the v-by-v detail has a map).** Prompt tuning went through four phases
plus an endgame, and the headline is that *directional* calibration never worked:

1. **Phase 1 (v2–v5): structural decision-gates** — forcing the model through two-stage D/M/K gates
   consistently *hurt*. (And round 1 of golden-label revision happened here.)
2. **Phase 2 (v6): a directional calibration cascade** — "prefer D over M over K" lifted DISCARD
   recall to 93% but crushed KEEP recall to 41%. (Round 2 of golden-label revision happened here.)
3. **Phase 3 (v7–v8): from cascade to targeted** — removing the cascade flipped it to over-merge;
   *targeted, failure-mode-specific* notes finally worked (3.5-flash hit 80%).
4. **Phase 4 (v9–v9d): presentation over instruction** — reordering fields (action before situation)
   beat any amount of added instruction text.
5. **Endgame (v10→v11→v11b): drop MERGE** — rare, hard, and destructive on weak models; per-extraction
   became KEEP/DISCARD only.

---

## ① Why golden labels at all

The per-extraction pipeline runs after every game to decide whether each newly extracted observation
and strategy point is novel (**KEEP**), redundant (**DISCARD**), or — for observations — a variant
worth folding in (**MERGE**). We had no way to measure how *accurately* the LLM made those calls: the
existing `dedup_eval.py` scored decisions with an *LLM judge*, i.e. one model grading another with no
ground-truth anchor. To find systematic biases in the dedup prompt we needed **human-annotated golden
labels** and a deterministic scorer.

## ② The eval anchor: golden labels + baseline

### Building the golden set

We sampled **50 cases** (later expanded to 65 — §below) from 390 dedup spans across 30 games
(`v4_action_phase_v2`, seed=42), balanced 25 observations / 25 strategy points. Each case carries the
new entry, its top-k candidates with similarity scores, and the LLM's original decision. Labelling was
interactive human review across two sessions; we surfaced full original text whenever a summary felt
ambiguous (~15 of 50, mostly observations).

Three design decisions shaped the set, each earning its keep later:
- **Strategy points are D/K only** — `StrategyDedupDecisionOutput` is `StrategyDiscard | StrategyKeep`;
  merging two prescriptive rules is semantically harder than merging two anecdotes. (A
  discard-*with-rewrite* option let a discard still steal better phrasing — revisited and removed at v10.)
- **`also_acceptable` for genuine borderlines** — some cases sit honestly between D and M; rather than
  force one label and penalise a defensible call, we record both and report strict *and* lenient
  accuracy.
- **Tricky cases as a separate artifact** — the 7 hardest cases live in
  [tricky_cases.md](tricky_cases.md) with full text, the tension, and the prompt implication: a
  machine-readable golden file for scoring, a human-readable file for debugging.

### The legacy-mapping gotcha (a scoring fix, not a behaviour change)

The dataset's legacy `A/B/C/D` codes had to be translated to D/M/K. The naïve uniform map gave **66%**
and a suspicious mismatch list — nearly all strategy errors showed predicted=M, impossible since
strategy points have no merge. The fix: legacy **B (REPLACE)** maps to **M for observations** but **D
for strategy points** (which can't merge). Splitting the map by item type jumped accuracy to **78%** —
purely a scoring correction. *Lesson in miniature:* a label-set mapping is mediated by schema
constraints, not a lookup table.

### Baseline accuracy and the dominant failure

The baseline model — **gemini-2.5-flash** (the model used during the original 30-game batch) — scored
**78% strict / 80% lenient**.

| Metric | Overall | Observations | Strategy points |
|---|---|---|---|
| Strict | 39/50 (78%) | 18/25 (72%) | 21/25 (84%) |

Observations are the hard half (comparing nuanced anecdotes for "same lesson"); strategy points are
more concrete. The per-label breakdown names the enemy:

| Label | Precision | Recall | Support |
|---|---|---|---|
| D | 0.82 | 0.74 | 19 |
| **M** | **0.56** | **0.83** | 6 |
| K | 0.83 | 0.80 | 25 |

**MERGE has high recall but low precision — the model over-merges.** It calls MERGE on cases that
should be D or K. That single tendency drives most of the tuning that follows.

### Three systematic biases (from the 7 tricky cases)

1. **Over-merge when the response is similar but the *opposing tactic* differs** (cases 16, 21). Same
   villager response ("press with evidence") but a different wolf signal being countered → a different
   lesson the agent must learn separately.
2. **Merge-bias over discard when any surface detail differs** (cases 22, 24). The model treats a
   player-count or game-phase difference as enough to merge, even when the existing entry already
   generalises the pattern.
3. **Over-differentiate on game phase alone** (case 40). The "too obvious" defence fails identically
   mid-game and endgame; the phase change doesn't make it a new lesson.

These three became the test cases for every subsequent prompt.

## ③ The tuning loop — four phases + endgame

### Phase 1 (v2–v5): structural decision-gates consistently hurt

**v2** rebuilt the observation prompt as a **two-stage decision test** (Stage 1: lesson identity →
D vs not-D; Stage 2: signal novelty → M vs K) with a **calibration cascade** (doubt → D over M, M over
K) and *obs_count gravity* — a high-reinforcement existing entry raises the bar to merge into it.
(Three independent drafts converged on the structure; the merged draft that
shipped is in [drafts/](drafts/observation_prompt_draft_v2_merged.md).)

Replayed across five models, v2 **regressed**: the production model (flash-lite) fell **78% → 60%**.
The decision distribution showed why — flash-lite v2 predicted **38 discards** (golden has 19) and
MERGE recall collapsed to **0%** on three of four models. The cascade had ratcheted everything toward D.

**But half the "regression" was mislabelled data.** Every model — cheapest to most expensive —
independently refused to merge the same 4–5 cases. Uniform cross-model failure is stronger evidence of
*label* error than prompt error, so we re-examined all 6 MERGE labels:

| Case | Old → New | Reason |
|---|---|---|
| 1 | M → **D** | "2 saves" vs "3 saves" — degree, not kind |
| 17, 18 | M → **K** | structurally distinct triggering events |
| 23 | M → **D** | existing entry already generalises it (obs=3) |
| 19, 20 | M → M | the only true merges — a real tactic variant enriching a pattern |

Four of six MERGE labels were wrong. Re-scored against corrected labels, **3.5-flash v2 rose 74% → 80%**
(its "failures" were correct) while the baseline *dropped* 78% → 72%. MERGE is now rare — **2 of the 50
(4%)** *at this point* (round 2 revises it back up — see Phase 2).

**v3–v5** kept iterating on structure and all came back *worse* than v2: v3 (softened calibration) 62%
flash-lite; v4 (Stage 1 gates KEEP instead of D) cratered to **40%** with 25 false merges; v5 (drop M
calibration, add "MERGE is rarest" framing) 56.9% flash-lite / 40% 3.5-flash. The structural lesson:
**forcing explicit MERGE consideration through a decision gate *increases* MERGE false positives** —
in v2 the model could skip straight to DISCARD; in v5 every non-KEEP case passes through a D/M choice,
handing the model more chances to wrongly merge.

*(Mid-phase the eval set expanded 50 → 65 cases; the 15 new cases were cleaner — 10 D, 5 K, 0 M.
Distribution going into Phase 2: **D=31, M=2, K=32**.)*

### Phase 2 (v6): a directional calibration cascade

Abandoning the two-stage structure, **v6** went back to a *flat* prompt (closer to baseline) but kept
the v2 content — a dimensional situation comparison (information landscape, consensus texture, agent
exposure, game phase) plus the cascade **"when uncertain: prefer D over M, and M over K."**

It worked exactly as designed — too well:

| Model | Accuracy | D recall | K recall |
|---|---|---|---|
| flash-lite v6 | 67.7% | **93%** | **41%** |
| 3.5-flash v6 | 75.4% | **90%** | **66%** |

D recall soared, but the cascade **crushed K recall** — flash-lite discarded more than half of
genuinely-novel entries. Many K cases live in the "uncertain between D and K" band, and the cascade
consumed them.

**A second golden-label revision** ran here, triggered the same way (32 cross-model disagreements
reviewed): **10 labels changed**, mostly D→K, applying the **retrieval test** as the decisive criterion
— *would a search query matching situation A also retrieve situation B?* If not, they must coexist.
That review crystallised six labelling principles (retrieval test, confidence posture, agent exposure,
conflicting strategies → KEEP, success-vs-failure → KEEP, one-off-vs-persistent → MERGE) that fed the
next prompts. By the end of this round the working set was **D=30, M=5, K=29, M/K=1** — MERGE back up
to ~8% from its round-1 low of 2, still rare.

*Tracing the MERGE count (a diligent reader will): 6 → 2 (round 1 fixes 4 mislabels) → 2 (expansion
adds none) → 5 (round 2 reclassifies a few D/K cases as genuine tactic-variant merges) → 0 (v11
relabels all to K). Anchor on the frozen label file
`evaluation/frozen_eval_sets/dedup_v2_golden_labels.json` — today **D=30 / K=34 / M-K=1**, which the v11
"5 M→K" relabel forces back to the D=30 / M=5 / K=29 / M-K=1 above. The round-2 per-case working table
under-records the move back into MERGE, so the **file counts are authoritative, not the table.***

### Phase 3 (v7–v8): from cascade to targeted

**v7** removed the calibration cascade entirely. K recall recovered (flash-lite 41% → 55%, 3.5-flash
66% → 93%) — but the pendulum swung to **over-merge** (flash-lite predicted M 16× vs 5 golden). This is
the crux finding: **the calibration cascade is a lever with no neutral position — present = over-discard,
absent = over-merge.**

**v8** stopped pushing a *direction* and added **targeted, failure-mode-specific** notes instead:
"MERGE requires a clearly distinct tactic *category*, not different wording — if unsure, DISCARD," and
for strategy "focus on what the agent would DO, not how it's worded." This recovered D recall without a
ratchet:

| Model | v7 → v8 accuracy | D recall v7→v8 | K recall v7→v8 |
|---|---|---|---|
| flash-lite | 69.2% → 69.2% | 77% → **83%** | 55% → 52% |
| **3.5-flash** | 75.4% → **80.0%** | 60% → **77%** | 93% → 90% |

**3.5-flash v8 = 80%** is the best **three-label (D/M/K)** configuration — the best while MERGE still
existed. The lesson: **targeted corrections beat
directional cascades** — a criterion ("this difference isn't enough for M") doesn't ratchet the way a
bias ("prefer D") does.

### Phase 4 (v9–v9d): presentation beats instruction

v8's biggest remaining error on flash-lite was **strategy K→D** — the model saw situation similarity
first and rationalised conflicting actions as "variations of the same strategy." We tried adding
explicit instruction (a DISCARD verification check; a parallel ACTION COMPARISON section; an ACTION
CHECK output field) — *none* helped, and the output-field variant **regressed** (structured output
interfered with flash-lite's reasoning).

What worked was **v9d: reorder the fields so Action comes before Situation.** Same information, just
presented so the model meets the *conflicting action* before the *similar situation* anchors it
together:

| flash-lite | v8 → v9d |
|---|---|
| overall | 69.2% → **73.8%** |
| strategy | 72.0% → **84.0%** (+12pp) |
| K recall | 52% → 59% |

**Presentation order matters more than instruction volume** for weak models — a content-neutral reorder
out-performed every added paragraph. (3.5-flash was unmoved — already at 88% strategy.) v9d is the
production prompt going into the endgame.

### Endgame (v10 → v11 → v11b): dropping MERGE

> **Backend caveat (load-bearing for reading v10+).** Between v9d and v10 we switched the API backend
> from Google AI Studio to Vertex AI, which shifts outputs *even at temperature 0* (flash-lite v10:
> 76.9% on Google AI vs 73.8% on Vertex). v10+ numbers are comparable within themselves but **not**
> directly to v9d and earlier. This is why store-version and backend are stamped in run provenance.

- **v10 — remove discard-with-rewrite from strategy.** Models rewrote both fields 60–97% of the time
  even when value was in one detail, and the "good" rewrites were mostly mislabelled discards. Removing
  it forced cleaner D/K boundaries; flash-lite strategy **84% → 96%** on Vertex — though **overall held at
73.8%** (observations fell to 60% on the backend switch), and 3.5-flash landed at the same 73.8% overall:
the shared pre-v11 baseline below.
- **v11 — remove MERGE from observation dedup (the climax).** MERGE was rare (5/65), both models
  over-fired it (flash-lite predicted 15, 3.5-flash 8), and false merges produced the worst
  rewrite-quality scores and corrupted live entries. Dropping to **D/K only** (5 M labels relabelled K,
  golden D=30/K=34) lifted both models from their coincident **73.8% Vertex-v10 baseline** — flash-lite →
  **80.0%** (obs 60% → 70%), 3.5-flash → **83.1%** (obs 70% → 82.5%). The two models then show opposite residual errors: flash-lite
  **over-discards** (9 K→D), 3.5-flash **under-discards** (all errors D→K, 100% K precision).
- **v11b — strengthen the three-field match.** "DISCARD requires all three fields (situation,
  approach, outcome) to agree; a different tactic *category* or a different outcome → KEEP." This
  targeted flash-lite's over-discard: **80.0% → 83.1%**, K→D errors 9 → 4.

### Supporting analyses (folded in, not the spine)

- **Cost / latency — why flash-lite is the production model.** flash-lite vs 3.5-flash is ~6× cheaper
  per token but ~**3×** per *case* (flash-lite's thinking tokens narrow the gap); ~7× faster. Accuracy
  trails (flash-lite 69.2% vs 3.5-flash 80%, the v8 D/M/K figures; the decisive gap is **K recall 52% vs 90%**, i.e.
  over-discard). We kept **flash-lite** anyway: the cost/latency matter at scale, flash-lite improved
  with the v9d/v11b work, and the offline **batch dedup is a safety net** for both over-discard (rare,
  impactful) and over-keep (common, recoverable).
- **Rewrite quality (while MERGE still existed).** Judged by gemini-3.1-pro-preview on 4 dimensions:
  flash-lite v9d merges scored mq 4.21 / ip 4.05, 3.5-flash 4.55 / 4.45, **0% fabrication** on both.
  3.5-flash's edge was **fewer merges, not better ones** — it avoided the false merges that produced
  flash-lite's destructive rewrites. The destructive cases all traced to a *wrong decision*, not a bad
  rewrite — which is part of why v11 removed MERGE rather than tuning its rewrite further.

## ④ Synthesis

### Lessons (the transferable part)

- **When every model "fails" the same cases, check the labels first.** Five models across three
  generations produced 0% MERGE recall on the same 4 cases — that uniformity was *label* error.
  Prompt deficiencies produce *model-specific* failure patterns; cross-model agreement against the
  golden label is a label smell. (Two revision rounds changed 14 labels total, each strengthening
  ground truth — golden-label iteration is *part of* the eval, not a failure of it.)
- **Directional calibration is a ratchet with no neutral position.** "Doubt → D" kills KEEP; "doubt →
  M" floods false merges; removing all calibration over-merges. *Targeted* notes ("this specific
  difference isn't enough for X") fix a failure mode without biasing the whole distribution.
- **Forcing explicit consideration of a rare option increases its false-positive rate.** Routing every
  case through a D/M gate raised MERGE predictions 10× despite "MERGE is rarest" framing. For rare
  decisions, implicit availability beats an explicit gate.
- **Presentation order beats instruction volume for weak models.** A content-neutral field reorder
  (action before situation) added more than any paragraph of rules, and an extra output field *hurt*.
- **The retrieval test grounds an otherwise-subjective call.** "Are these the same situation?" is
  fuzzy; "would a query for A retrieve B?" is operational and resolved most labelling disputes.
- **Stronger models amplify both good and bad prompts.** 3.5-flash ranged 82% → 40% → 80% across
  versions; flash-lite stayed in a narrow 60–69% band. The stronger model extracts more from a good
  prompt and suffers more from a bad one.

### The open question: lean discard or lean keep

This is the recurring tension of the whole chapter, and it is **deliberately unresolved** (it threads
through the dedup overview's [§6](../experiment_log.md)). The *tactic* is settled — targeted
corrections, not directional cascades. The *strategic lean* is not:
- **Lean discard** keeps the store lean, and an over-discarded entry from a *common* situation will be
  re-extracted from a future game.
- **Lean keep** protects *rare*-situation lessons — over-discard those and they're permanently lost.

We never picked, on purpose: the right bias "depends on downstream retrieval quality and agent strategy
application, not on the prompt," and that downstream evaluation is part of the frozen memory work. The
live prompt sits near-neutral with targeted anti-over-discard notes (v11b).

## Current live state (2026-06-25)

This pipeline is **live and on by default** during store-build / seeding (`dump_enabled=True`,
`Agents/memory/persistence/config.py:89`), running after each game on every newly extracted entry.
Three things differ from where the tuning journey above left off — they are its *outcome*, not
contradictions of it:

1. **MERGE is gone — online dedup is KEEP/DISCARD only.** The v11 decision is the shipped state: the
   model is only ever offered DISCARD/KEEP (`Agents/memory/deduplication/schemas.py:84-91`). MERGE
   (rewriting) now lives **only** in the offline batch pass. The live prompts are a stabilized "v6.1"
   generation in `Agents/prompts/dedup.py` (carrying the v9d action-before-situation ordering) — not
   literally any single v-number above.
2. **A deterministic gate runs before the LLM.** Candidates are first narrowed by a structured gate
   (`Agents/memory/dedup_gate.py`) — same role/phase, same `gate_key` bucket, compatible hard
   pair-checks — so the LLM only ever compares already-homogeneous entries, and the gated dimensions are
   hidden from it via `situation_for_dedup`. This is v6 work that **postdates** this log.
3. **The embedding pre-filter auto-decides the easy cases.** The thresholds calibrated in the sibling
   [embedding_prefilter](../embedding_prefilter/experiment_log.md) log are live in
   `Agents/memory/deduplication/config.py` (SP 0.93/0.81, OBS 0.96/0.935); the LLM sees only the
   ambiguous middle band.

Full current-vs-documented gaps: [../report.md](../report.md) § *Current-vs-documented gaps*.

## Artifacts

| File | Description |
|---|---|
| `evaluation/frozen_eval_sets/dedup_v2_golden_labels.json` | 65 golden labels (D=30, K=34, M/K=1) — M relabelled to K at v11 |
| `evaluation/frozen_eval_sets/dedup_v2_sampled.jsonl` | the 65 sampled dedup cases (source dataset) |
| `evaluation/frozen_eval_sets/dedup_v2.manifest.json` | dataset manifest (390 cases, seed=42) |
| `evaluation/src/experiments/dedup_score.py` | deterministic golden-label scorer (strict + lenient) |
| `evaluation/src/experiments/dedup_replay.py` | re-runs frozen cases through a chosen model/prompt |
| `data/dedup_score_original_v2.json` | original baseline scoring (78% strict, pre-revision labels) |
| [tricky_cases.md](tricky_cases.md) | 7 mislabelled cases with full text + prompt implication |
| [drafts/](drafts/) | the v2 observation-prompt drafts (Draft 1 + the merged version that shipped) |
| `prompt_history/{dedup_prompt_baseline,standards_baseline,dedup_v5,dedup_v6}.py` | frozen prompt snapshots |
| `evaluation/frozen_eval_sets/dedup_v2_replay_*.jsonl` | one replay JSONL per (model × prompt-version), v2→v11 (older ones in `legacy/`) |
| `evaluation/eval_results/dedup_judge_*_v9d.jsonl` | rewrite-quality judge results (flash-lite + 3.5-flash) |

*Provenance: dataset `v4_action_phase_v2`, seed=42; per-extraction prompt versions v1→v11b; backend
Google AI Studio through v9d, Vertex AI from v10 (stamped per run).*
