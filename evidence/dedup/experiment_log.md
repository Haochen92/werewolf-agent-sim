# Deduplication — chronological overview

**What this is.** The spine of the whole dedup workstream: why each sub-experiment happened, in time
order, with a pointer into each one's own log. Memory entries (observations + strategy points)
accumulate near-duplicates as games are played; duplicates crowd the retrieval slate and teach nothing
new. Dedup is how the store stays lean. This doc is the *map*; the destination — how dedup works in the
code **today** — is the companion [report.md](report.md).

**The shape of the problem (so the chronology has somewhere to hang).** Dedup splits into two
families, and the LLM family into three passes:

- **LLM dedup** — a model judges whether two entries teach the same thing.
  - **Per-extraction (online):** each new entry, as a game ends, against existing neighbours. KEEP/DISCARD.
  - **Batch (offline, system-wide):** the whole store swept in similarity clusters. KEEP/DISCARD/**MERGE**.
  - **Incremental batch:** the batch pass restricted to clusters touching new entries, with old entries
    frozen so re-runs converge.
- **Embedding auto-filter** — a deterministic similarity pre-filter that disposes of the obvious cases
  (clearly-novel → keep, clearly-duplicate → discard) with **no LLM call**, leaving only the ambiguous
  middle band for the model.

**Reading contract.** Sections are in time order; each is a one-paragraph orientation that points to
the sub-log holding the detail. The arc has a real correction in it (an n=5 result overturned by n=39)
and a real architectural shift at the end (the v6 gate) — both are called out where they happen, not
smoothed over. For the current shipped state and the places these older logs lag the code, jump to
[report.md](report.md).

---

## 1 · May 23 — Store dedup discovers the retrieval win  →  [store_retrieval_impact/](store_retrieval_impact/experiment_log.md)

The workstream started as a retrieval problem, not a dedup one. After building retrieval filtering (a
dedup gate, MMR, per-situation caps), evaluation showed the bottleneck wasn't retrieval sophistication
— it was a **dirty store** full of near-duplicate observations. The first measurement asked: does
cleaning the store at the source beat filtering at retrieval time? On n=5 frozen cases it did, clearly
(observation efficiency 3.00→4.00, redundancy halved). A latent bug surfaced too — the cluster builder
capped clusters at 8 and naively chunked larger ones, letting duplicates across chunk boundaries
survive (fixed 8→25). **This is what motivated everything below.**

## 2 · May 26 — Per-extraction golden labels + prompt tuning  →  [per_extraction/](per_extraction/experiment_log.md)

With store-cleanup proven worthwhile, attention turned to the **online** decision-maker — the per-game
pass that judges each new entry KEEP / DISCARD / MERGE. We had no ground truth for its accuracy (the
old eval scored one LLM with another). So we hand-labelled 50→65 golden cases and tuned the prompt
across v1→v11b. The journey is the lesson: directional **calibration cascades create ratchets** (push
"prefer D" and you kill KEEP recall; push "prefer M" and you flood false merges); **action-before-
situation field ordering** fixed strategy-point errors better than any instruction; and two rounds of
**golden-label revision** were needed when *every* model failed the same cases (uniform cross-model
failure was label error, not prompt error). The convergence point: **MERGE was eventually removed from
online dedup entirely** (v11) — rare, hard to call, and its rewrites corrupted entries.

## 3 · May 26-27 — Batch prompt tuning + the idempotency alarm  →  [batch_prompt_tuning/](batch_prompt_tuning/experiment_log.md)

The **offline** whole-store pass is harder than online (clusters of 2–25 entries, multiple operations
per cluster, MERGE retained because the model sees a whole cluster). We ported the per-extraction
criteria into the cluster prompts (v0→v3 + a "lite" anti-over-merge variant) on an 111-key golden set,
and landed a **two-pass pipeline** — flash-lite triages cheaply, 2.5-pro verifies and writes the merges
where it matters (89.2%, the best of all approaches). Critically, an **idempotency test** showed a
second run on an already-deduped store removed *another* ~10% — the pass is **not idempotent**. That
alarm is what motivated incremental dedup (§6). The mechanics of this pass are reference material in
[batch_architecture.md](batch_architecture.md).

## 4 · May 26 — Retrieval impact, phase 2: the correction  →  [store_retrieval_impact/ §Phase 2](store_retrieval_impact/experiment_log.md#phase-2-v3-prompt-calibration-and-larger-sample-n39)

The n=5 result from §1 was **optimistic**. Replicating on n=39 with the tuned prompts overturned it:
the original aggressive dedup (v0, 39% store reduction) actually *lost* observation relevance — it had
crossed from removing redundancy into removing distinct lessons. The conservative v3 store (17%
reduction) was the real winner: best efficiency and unique-lesson counts while holding relevance.
**Dedup is a Goldilocks problem** — the break-even is prompt-sensitive, not a fixed similarity
threshold — and this is why the shipped batch default is the conservative `bounded` clustering mode.
(A second finding foreshadowed later work: strategy-point redundancy never responded to dedup at all —
a content-coverage gap, not a dedup gap.)

## 5 · May 26 — Embedding pre-filter: the automatic layer and its ceiling  →  [embedding_prefilter/](embedding_prefilter/experiment_log.md)

Per-role extraction produces 2–3× more entries, overwhelming the LLM dedup pipeline. The fix: a
**deterministic embedding pre-filter** that auto-decides the obvious cases (very-high similarity →
discard, very-low → keep) and only pays for an LLM call on the ambiguous middle. We calibrated
zero-error thresholds on the golden set, validated on a 232-case cross-game set, then tried to push the
coverage higher — 3072 dimensions, `SEMANTIC_SIMILARITY` task type, multi-dimensional boundaries — and
**every improvement came back negative**. The takeaway is a property, not a tuning failure: embeddings
capture *topic, not stance* ("investigate the loud players" and "avoid the loud players" embed ~95%
alike), so ~15-30% auto-decision coverage is a hard ceiling — the LLM is irreducible for the middle.

## 6 · Jun 9 — Incremental dedup: diagnosing non-convergence  →  [incremental_convergence.md](incremental_convergence.md)

The idempotency alarm from §3 became a diagnosis. Running batch dedup incrementally (only clusters
touching new entries) is cheap, but the LLM is shown the *whole* cluster including old, settled
entries — so every new neighbour is a fresh chance to re-litigate and erode old data. There is no
stable fixed point: the store drifts past the optimal dedup degree. The fix has two parts — preserve
`created_at` through merges so old/new classification stays honest (Fix 1), and **forbid old-vs-old
operations** in the apply layer so old lessons are only ever absorbed *into*, never away (Fix 2). At the
time of writing, both were **proposed, not yet built**. *(Status has since changed — see that doc's
banner and [report.md](report.md).)*

## 7 · June (v6, current) — the deterministic gate + freeze-old  →  [report.md](report.md)

The current era is barely represented in the logs above because it postdates them. Three shifts define
the live system: (a) a **deterministic gate** (`Agents/memory/dedup_gate.py`) now partitions candidates
by a structured `gate_key` + hard pair-checks *before* any embedding or LLM step, shared by both the
online and batch paths — so the model only ever compares already-homogeneous entries; (b) Fix 2 from §6
(**freeze-old apply guard**) is **built and live**; (c) online dedup is **KEEP/DISCARD only** (MERGE
confined to the offline batch pass). The full current state — and every place the older logs lag the
code — is in [report.md](report.md).

---

## Sub-logs (the detail behind each beat)

| Beat | Log | Type |
|---|---|---|
| §1, §4 | [store_retrieval_impact/experiment_log.md](store_retrieval_impact/experiment_log.md) | does dedup help retrieval? (n=5 → n=39 correction) |
| §2 | [per_extraction/experiment_log.md](per_extraction/experiment_log.md) | online dedup prompt tuning v1→v11b |
| §3 | [batch_prompt_tuning/experiment_log.md](batch_prompt_tuning/experiment_log.md) | offline dedup prompt + two-pass tuning |
| §5 | [embedding_prefilter/experiment_log.md](embedding_prefilter/experiment_log.md) | automatic pre-filter calibration |
| §6 | [incremental_convergence.md](incremental_convergence.md) | incremental non-convergence diagnosis + fix |
| reference | [batch_architecture.md](batch_architecture.md) | batch-pass mechanics (how-it-works) |
| destination | [report.md](report.md) | current live state of everything + gap tracking |
