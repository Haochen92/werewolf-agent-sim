# Evaluation — how we measure the memory pipeline, and how far to trust it

> **What this chapter is.** The agent plays Werewolf and keeps an episodic memory it writes to and retrieves
> from across games (chapter 3). This chapter is about how we *measured* whether that memory works, and — the
> harder question — how far to trust each measurement. It keeps two things apart: whether a component *works*
> (the design verdict, chapter 3), and whether the *instrument* that judged it is any good (here). The frozen
> cases the judges run on are captured separately ([`../tracing/report.md`](../tracing/report.md)).
>
> **Where things live.** This file is the hub. Each measurement instrument has its own write-up, linked below.
> The [`source_map.md`](source_map.md) ledger owns the reliability tags, the code pointers, and the dated
> code-vs-report verification results — read it when you want the receipts.

## The one distinction that organizes everything

Every evidence folder braids two threads. This chapter follows one of them.

| Level | Question | A better one means | Home |
|------|----------|--------------------|------|
| **L0 — the design** | does the dedup / extraction / retrieval design meet its goal? | a better *design* | **chapter 3** (the verdict) |
| **L1 — the apparatus** | how do we *measure* whether it meets its goal? | a better *measurement* | **here** |
| **L2 — trust** | is that measurement itself any good: anchored, calibrated, low-noise? | a *more trustworthy* measurement | **here** ([`source_map.md`](source_map.md) tags) |

So a topic write-up catalogues an **instrument** and rates **its** reliability; it does not re-argue what the
design found. Where a component's measurement is thin or uncalibrated, **that absence is itself a finding** —
it is why, for example, the wolf result is read as measurement-limited rather than as a true ceiling.

## What the apparatus is good for

The strongest thing to say about this eval system is not any single score. It is that **the apparatus
repeatedly caught its own errors**:

- It discarded a baseline after detecting an epoch shift between runs (Fisher p=0.0028), then made a
  same-epoch fresh baseline mandatory.
- It caught a config slip that had let two arms diverge, and turned the check into an automated invariant that
  now hard-fails the run.
- It retracted an inflated engagement metric once it found the model had been silently skipping a third of its
  inputs.
- It caught a denominator artifact that had put the investigator find-rate on the wrong sign.
- It flagged both of its own paid v7 runs as invalid before they could be reported.
- It even refuted its own design: a canary showed that pairing arms by board draw buys almost no variance
  reduction, so the same-epoch baseline was the load-bearing part all along.

Self-correction at this rate is the best evidence the harness is real rather than decorative.

The second thing: **the apparatus knows which of its instruments to trust.** The trustworthy numbers are the
deterministic and outcome-anchored ones — the de-lucked town-play proxies (validated against faction-win at
|r|≈0.6), the deduplication golden scorer, the LLM-free loop measure, and the paired A/B machinery. The
uncalibrated LLM judges are treated as cheap, directional smoke alarms, not as gauges. Knowing the difference
is the whole point of the L2 column.

The top-level question the whole apparatus serves is the memory-on-vs-off A/B. Its verdict — town play
improves convergently across arms, the wolf and serial-killer arms are null or inconclusive, and the raw
win-rate is underpowered — belongs to chapter 3; the A/B *machinery* and how far to trust it are written up in
[`end_to_end_ab/report.md`](end_to_end_ab/report.md).

## The modality ladder — three ways we judge, cheapest first

Every component's quality is checked on one or more of three rungs. They form a calibration chain: the
cheapest is the noisiest, and the most expensive is the one that could calibrate the others.

1. **LLM-as-judge** → [`llm_judge/report.md`](llm_judge/report.md). One model scores another against a rubric.
   Cheap, fast, and the workhorse of day-to-day iteration — but every *live* judge here is uncalibrated, so
   its output is directional, not a gauge. Six components are judged this way (situation-summary, retrieval,
   application, extraction, dedup quality, day-summary).
2. **Sampled human + pro-LLM review** → [`sampled_human_review/report.md`](sampled_human_review/report.md).
   Pull a handful of real cases and read them with a person and a stronger model. This was the actual workhorse
   of most v5→v7 qualitative calls, and it is the **weakest-built rung**: no principled case sampler, no
   durable record. The build is specified but not done ([`plan.md`](sampled_human_review/plan.md)).
3. **Golden-set labels** → [`labeling/report.md`](labeling/report.md). Human-labelled answer keys — the gold
   standard, and the source of the apparatus's most trustworthy judge-adjacent numbers: the dedup decision
   scorer, the situation-retrieval NDCG set, and the cross-encoder reranker labels.

Above all three sits the **A/B and instrument layer** that decides "did it work" and keeps the measurement
honest: the end-to-end A/B, the de-lucked outcome metrics, the A/B methodology and drift guards, and the v7
loop.

```
        ┌──────────────────────────────────────────────────────────┐
 above  │  END-TO-END A/B  —  "did memory help?"  (on vs off)        │
 all →  │  + de-lucked metrics · drift guards · the LLM-free loop    │
        └──────────────────────────────────────────────────────────┘
 what gets judged (components) ───────────────────────────────────────
   day-summary · agent-decision (situation → retrieval → application)
   extraction (obs/SP + v7 synthesis) · dedup (online + batch)
 × how it's judged (the modality ladder, a calibration chain) ─────────
   ① LLM-judge (cheap, noisy)  →  ② sampled human + LLM review (underbuilt)
   →  ③ golden-set labels (gold; calibrates ①)
```

## Status board

Apparatus-yield varies. The apparatus-**first** topics (`end_to_end_ab`, `metrics`, `methodology`) are the
eval spine; the design-first folders (`day_summary`, `dedup`, `extraction`) carry a thinner, extractable
apparatus thread. Full code/evidence pointers per topic live in [`source_map.md`](source_map.md).

| Topic | The apparatus (L1) | Trust (L2) | Spoke |
|-------|--------------------|-----------|-------|
| **End-to-end A/B** | `run_batch.py` paired-by-game_id → `analyze_ab.py` → `core/stats.py` + de-luck proxies + decision-replay screen | 🟡 sound + self-aware (epoch-drift catch, convergent screen); win underpowered (MDE ~36pp); pairing buys ~0 variance (same-epoch is the real control) | [`end_to_end_ab/report.md`](end_to_end_ab/report.md) |
| **Day-summary** | 5-dim LLM-judge + regen-and-score harness (18 pairs) | ⚠️ smoke-test (uncalibrated · saturated · regen+judge confound · proxy≠objective) | [`llm_judge/day_summary.md`](llm_judge/day_summary.md) |
| **Agent-decision** (situation→retrieval→application) | pairwise-summary + retrieval + application judges + golden-NDCG + replay | 🟡 weakest at the live edge: every live judge uncalibrated; situation-NDCG golden machine-augmented + not wired into retrieval; ⏸ application calibration unrun; live v6 path thinnest-measured | [`llm_judge/agent_decision.md`](llm_judge/agent_decision.md) |
| **Extraction** (obs/SP + v7 synth) | per-role extraction judge (8 dims) | 🟡 **de-bugged, not calibrated** (2 real bug-fixes; machine-only/no golden; original 5 dims ceiling-saturated; v7 synth unjudged) | [`llm_judge/extraction.md`](llm_judge/extraction.md) |
| **Dedup** (online + batch) | deterministic golden scorer (strong) + 2 LLM quality judges (weak) | 🟡 decision-maker ✅ golden-anchored (65 online / 111 batch keys); quality judges uncalibrated; numbers stale (pre-v6 + backend shift); ✅ silent-fail bug fixed | [`labeling/dedup.md`](labeling/dedup.md) |
| **Metrics** (instruments) | de-lucked outcome proxies + monotonicity validation | ✅ town basket (\|r\|≈0.6) · 🟡 investigator (find-rate wrong-sign; only conversion validated) · ⚠️ deceiver (SK ok; wolf day-offense unmeasured) · 🔴 discussion; GameScore tiering unbuilt | [`metrics/report.md`](metrics/report.md) |
| **A/B methodology** | drift guards + arm-guard (hard-fail ×2) + pairing/stats | 🟡 strong where enforced; cross-epoch gate + embedding-alias drift are MANUAL/undetected; pairing BUILT but ≈0 power; CUPED N/A | [`methodology/report.md`](methodology/report.md) |
| **Sampled human review** (rung ②) | case sampler → human + pro-LLM eyeball | ⛔ UNDERBUILT — documented; the build *is* the sampler | [`sampled_human_review/report.md`](sampled_human_review/report.md) |
| **v7 loop** | LLM-free `measure.py` + paid omniscient tagger + invariants | ✅ mechanics (best-tested; caught its own invalid runs) · 🟡 science open (tagger = validated metric not memory verdict; both v2 runs invalid) | [`loop/report.md`](loop/report.md) |

## Cross-cutting findings

Read across all the topics, four limits and three named failure modes recur.

**The limits:**

1. **Every *live* LLM-judge is uncalibrated**, machine scoring machine, with no human or golden anchor behind
   the numbers. The trustworthy instruments are the *non-LLM* ones: the dedup decision-scorer (human golden),
   the metrics proxies (validated against win), the LLM-free loop measure, and the situation-NDCG and
   reranker goldens.
2. **The real anchors exist but aren't wired into the live judges.** The situation-NDCG golden isn't consumed
   by the live retrieval eval; the reranker golden isn't live (reranking is off); the application calibration
   is designed but not run. The calibration *capacity* exists, disconnected from the live measurement path.
3. **Staleness is uniform.** Nearly every anchor is on v4 stores, 2026-05 prompts, and the pre-Vertex backend,
   so most headline numbers describe superseded code.
4. **The live v6 path is the least-measured.** v6 ships baseline retrieval with reranking and filtering off;
   the heavily-studied designs are dormant or default-off. Diagnostic confidence is highest where the code
   isn't running.

**The failure modes worth naming once:**

- **Flat / ceiling-saturated judge dimensions** are zero-information gauges (village-dynamics pinned at 5.00;
  extraction's original five dimensions clustered near the top).
- **Regen-and-judge in one harness** confounds generation with scoring: a change in the score can't be
  separated from a change in what was generated.
- **Outcome-halo selection** smuggles in the answer: a metric conditioned on whether the side won measures the
  win, not the property it claims to.

**The recurring cheapest upgrade is one move:** calibrate one judge, or wire in an anchor that already exists.
Highest-leverage is the application calibration (about half a day, no new code).

## Bottom line for v7

Trust the deterministic and outcome instruments — the town proxies, the dedup scorer, the loop measure, the
paired-A/B machinery — and the validated tagger-as-metric; do not lean on the uncalibrated LLM-judge layer.
The gating need is a valid paired run plus a wolf-direct arm, not more judges.

---

*Hub for chapter 4, distilled from the per-instrument write-ups linked above. The dated code-vs-report
verification results and full code pointers live in [`source_map.md`](source_map.md). Whether each memory
component actually works, as opposed to how well we can measure it, is chapter 3.*
