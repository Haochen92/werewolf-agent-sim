# Deduplication — chronological overview

**What this is.** The spine of the whole dedup workstream, in the order it actually happened: *why*
dedup had to exist, what we reached for first, what broke, and what replaced it — with a pointer into
each sub-experiment's own log for the detail. The story ends in a **deliberate freeze** — tuning is
paused pending an upstream question (*does the memory even help?*), detailed in
[report.md](report.md) — so the open threads below are a parked decision, not a loose end. That
companion [report.md](report.md) is also the destination: how dedup works in the code **today**.

**The two things being deduplicated.** Post-game extraction writes two kinds of memory. An
**observation** records what happened in one situation — situation → approach → outcome, a
lesson-by-example. A **strategy point** is a reusable *situation → action* rule. They hit the same
duplication problem but behave differently under it, which turns out to be the crux of §5.

**What counts as a duplicate — the trigger, then the per-type rule.** Everything rests on one field:
**`situation`** is the only text embedded for retrieval ([store.py:29](../../Agents/memory/store.py#L29):
`fields=["situation"]`), so it is the **trigger** — two memories with the *same* situation retrieve
together, and the operative test in every dedup prompt is literally *"would a search query matching A
also retrieve B?"* The *intent* is that different situations don't collide; in practice a bi-encoder is
fuzzy (it captures topic, not stance — §2), so different situations **do** surface as candidates. The
deterministic **gate** (§9) is what makes "different *structured* situation ⇒ never compared" actually
hold; the free-text remainder stays a judgment call where some false positives slip through. On that
trigger the two types diverge:

- **Observations** (situation → approach → outcome): a duplicate needs **all three** to match — same
  situation, same *tactic category* (not wording or degree), same *success/failure* outcome. A different
  **outcome** is a **contrasting** lesson (keep both); same situation+outcome with a different *tactic
  variant* is the merge case (combined offline; online keeps-rather-than-discards, since online has no
  MERGE — §7).
- **Strategy points** (situation → action): same situation ⇒ the **action must differ** (target, timing,
  direction, risk) to keep.

These rules were not declared up front — they were **pinned down through mislabelling** (§6) and later
hardened into the deterministic **gate** (§9). Per-field detail + the full history:
[per_extraction/](per_extraction/experiment_log.md).

**The shape of the problem.** Played over many games, the store **compounds with near-duplicates**, and
duplicates crowd the retrieval slate while teaching nothing new. Everything below searches for a
mechanism that removes the redundancy *without* removing a distinct lesson. It splits into two
families, the LLM one into three passes — and these are the **only** terms this log uses for them:

- **Embedding auto-filter** — a deterministic similarity check; cheap, no LLM, but blunt.
- **LLM dedup** — a model judges whether two entries teach the same thing.
  - **per-extraction** (the *online* pass): each new entry, as a game ends. KEEP/DISCARD.
  - **batch** (the *offline* pass): the whole store swept in clusters. KEEP/DISCARD/MERGE.
  - **incremental batch**: the batch pass restricted to clusters touching new entries, old ones frozen.

**Naming — three independent version counters (the log always says which).** *Store* versions (v4, v5,
v6 …) track the memory store; *per-extraction prompt* versions (v1→v11b) and *batch prompt* versions
(v0→v3) track the two dedup prompts; the **v6 gate** is an architecture milestone, not a prompt. Where a
bare number would be ambiguous, the scheme is written out.

**Reading contract.** Sections are in time order; each is a one-paragraph orientation that points to
the sub-log holding the detail. The arc contains real corrections — an approach that looked sufficient
and wasn't, an n=5 result overturned by n=39, a tension we *still haven't settled* (§6) — and they're
called out where they happen, not smoothed over. For the current shipped state and the places these
older logs lag the code, jump to [report.md](report.md).

---

## 0 · Origin — why dedup exists

Observations and strategy points are extracted after every game and accumulated in a persistent store.
That accumulation is the whole point (memory compounds), but it has a failure mode: the same lesson
gets re-learned and re-written across games, so the store fills with near-duplicates that spend
retrieval slots on copies. Dedup is the mechanism that keeps the store lean. Every design below is
judged against one bar — *remove the redundancy without removing a distinct lesson.*

## 1 · First solution — cosine-similarity dedup

The first cut was purely deterministic: embed each new entry's situation, search the store, and decide
by the top cosine score. Below a low floor (`DEDUP_SIMILARITY_THRESHOLD = 0.55`,
[deduplication/config.py:7](../../Agents/memory/deduplication/config.py#L7)) nothing similar exists →
store as new; above a high threshold (~0.9 at the time) → treat as a near-duplicate and discard. Cheap,
simple, no model in the loop.

## 2 · Why cosine alone is too weak — the bi-encoder ceiling

It didn't hold up — not because cosine is useless, but because it fails *exactly in the zone that
matters*. Near-duplicates and genuinely-different lessons sit in almost the same embedding neighbourhood:
the gap between "same lesson" and "different lesson" is extremely narrow, because embeddings encode
**topic, not stance**. Two strategy points about the same situation that recommend *opposite* actions
embed ~95% alike. So a *single* similarity cutoff can't be set without either merging distinct lessons or
keeping duplicates. Where the two *don't* overlap — near-identical text, or plainly different topics —
cosine **is** reliable, and §5's pre-filter later harvests exactly those extremes (~15-30% of cases);
it's the broad ambiguous **middle** that's irreducible. The conclusion: cosine is a good first sieve and
can auto-decide the clear extremes, but it can't be the **sole decider** — the middle needs the LLM.

## 3 · LLM per-extraction dedup — and the vocabulary collapse to D/K

So each new entry, as a game ends, goes to an **LLM** that judges it against its nearest neighbours.
Early on (store versions up to ~v3) the prompt was **not tuned** — we accepted the default and used
**gemini-2.5-flash** (the model from the original 30-game batch). What changed most over time was the
**decision vocabulary**, and it collapsed for one reason: **every action that asks the model to *rewrite*
an entry is unreliable on a weak online model**, so each was pushed out in turn.

- The original scheme (strategy dedup, 2026-05-14) had **four** actions, `DISCARD / REPLACE /
  DIFFERENTIATE / KEEP` (the legacy `A/B/C/D` still referenced by the eval mappers — see the enum
  docstring in [deduplication/schemas.py](../../Agents/memory/deduplication/schemas.py)). Both *rewriting*
  actions were retired early, never reliably driven: **REPLACE** = "the new entry is better — replace the
  old, keeping the best of both"; **DIFFERENTIATE** = "similar situation, different action — rewrite
  *both* situations to make the distinguishing variable explicit."
- That left **MERGE** (rewrite two entries into one). MERGE was **born in the online pass** — observation
  dedup gained `DISCARD / MERGE / KEEP` on 2026-05-23 — and was **removed from online at v11**
  (2026-05-26): rare (≈5/65 golden cases), over-fired by both models, and **lossy on
  gemini-3.1-flash-lite**, which silently drops the `merged_approach`/`merged_outcome` fields and corrupts
  the entry (§7).

End state online: **KEEP/DISCARD only** — no rewriting. Rewriting (MERGE) survives **only** in the
offline batch pass, where a pro model runs it. Detail: [per_extraction/](per_extraction/experiment_log.md).

## 4 · Per-extraction dedup wasn't enough → batch as a second layer

Per-extraction dedup *does* search the whole store across all games (the namespace is
`(kind, role, phase)`, not game-scoped), so the gap isn't game boundaries. It is that online dedup is a
**greedy, insertion-time** check: each new entry is compared only against its **top-N** neighbours (top
5) at the moment it lands, and once two near-duplicates are both kept the pass **never re-examines that
pair**. So near-duplicates that fell outside each other's top-N window, or were both kept before they sat
together, accumulate — and online can't MERGE variants even when it sees them. (Cross-game blindness
only arises under *parallel* generation with separate per-game stores; the sequential baseline doesn't
hit it.) The second layer is **batch** dedup: an offline pass that re-clusters the *whole* store and
re-examines every near-duplicate together, with MERGE available. Mechanics:
[batch_architecture.md](batch_architecture.md); tuning: [batch_dedup/](batch_dedup/experiment_log.md).

## 5 · Does cleaning the store actually help retrieval? (and the embedding ceiling, measured)

Two threads landed here, both on the v4 store:

- **Retrieval impact** ([store_retrieval_impact/](store_retrieval_impact/experiment_log.md)). Measured
  on a frozen set of retrieval cases, each scored by a **gemini-2.5-flash judge on 1–5 rubrics**
  (relevance, efficiency, unique-lessons). Cleaning the store improved retrieval — but the win was
  lopsided, and the first read was optimistic. **Observations improved dramatically** (efficiency
  3.0→4.0, redundancy 52%→25%, n=5); **strategy points barely moved** (redundancy stayed ~59–77%). That
  non-response is itself a headline finding: strategy-point redundancy is a **content-coverage gap, not
  a dedup gap** — the store lacks entries for some situations, and no amount of dedup creates them. And
  the optimistic n=5 read was **overturned at n=39**: aggressive merging (39% store reduction) *lost*
  observation relevance, while conservative dedup (17%) won on efficiency and unique-lessons. Dedup is a
  Goldilocks problem.
- **The embedding pre-filter, calibrated** ([embedding_prefilter/](embedding_prefilter/experiment_log.md)).
  To stop paying for an LLM call on the obvious cases, we calibrated deterministic auto-keep/auto-discard
  thresholds — and in the process *measured* the §2 intuition. Auto-decision coverage plateaus at
  **~15–30% and that's a ceiling, not a tuning shortfall**: 3072-dim and `SEMANTIC_SIMILARITY` ablations
  both came back negative. The embedding space genuinely can't separate the middle band — only the LLM can.

## 6 · Golden labels, prompt tuning — and the discard-vs-keep tension we never settled

At v4 we built **golden labels** to evaluate prompts against ground truth instead of LLM-judging-LLM:
a human-led core set (sampled from `v4_action_phase_v2`) plus LLM-labelled cross-game sets, with
explicit rules for "same lesson vs different." Those rules were not given up front — the two
label-revision rounds *were* the act of pinning down where the boundaries sit (game-phase alone ≠ a new
trigger; opposite outcome, success vs failure, is always a keep; a different opponent-tactic is a
different lesson even when the response matches). On that anchor we tuned the per-extraction prompt
**v1→v11b** and the batch prompt **v0→v3**. The throughline — and the **single most-revisited open
question** — is whether to **lean discard or lean keep**:

- *Lean discard* keeps the store lean, and an over-discarded entry from a *common* situation will simply
  be re-extracted from a future game.
- *Lean keep* protects **rare-situation** lessons — over-discard those and they're **permanently lost**,
  because the situation may never recur.

The tuning settled the *tactic*. Directional calibration ("when in doubt DISCARD", or "prefer D over M
over K") turned out to be **a lever with no neutral position**: push it and you ratchet one category to
death. The per-extraction prompt's v6 cascade hit 93% D-recall but crushed K-recall to 41%; removing it
entirely just flipped the failure to over-merge. The lesson: **targeted, failure-mode-specific
corrections beat directional cascades.** But the *strategic* lean — should the store as a whole err
toward discard or keep? — was left **undecided on purpose**. It "depends on downstream retrieval quality
and agent strategy application, not on the prompt," and that downstream eval is part of what's frozen
(§8). **Still open.** Detail: [per_extraction/](per_extraction/experiment_log.md),
[batch_dedup/](batch_dedup/experiment_log.md).

## 7 · MERGE removed from online dedup

The golden-label work showed MERGE was rare (≈5/65 cases), hard for models to call, and — on
flash-lite — **destructive when wrong** (lossy rewrites that corrupt entries). So per-extraction dropped
to **KEEP/DISCARD only**; MERGE/rewrite survives only in the offline batch pass on a pro model. This is
the second of the two prunings in §3.

## 8 · Idempotency check → non-convergence → freeze

Running batch dedup twice on an already-clean store removed **another ~10%** of the store. The first
read called this "not idempotent"; the diagnosis sharpened it: a re-run with no new entries is a no-op,
so the pass is narrowly idempotent, but it does not **converge** (it re-litigates settled old entries
whenever a new neighbour lands).
Diagnosed in [incremental_convergence.md](incremental_convergence.md), with a two-part fix (preserve
`created_at`; forbid old-vs-old merges). Around here the **prompt and golden-label tuning was frozen**
(before store v5), pending two upstream decisions: whether the memory is even *helping* (an
effectiveness question) and a final memory **format**, both still being settled. The tuning hasn't moved
since — but structural work continued (§9).

## 9 · The deterministic gate (v6 architecture, post-freeze)

One architectural change did land after the tuning freeze, and it isn't in the logs above because it
postdates them: a **deterministic gate** (`Agents/memory/dedup_gate.py`) that partitions candidates by
a structured `gate_key` + hard pair-checks *before* any embedding or LLM step, shared by the online and
batch paths — so the model only ever compares already-homogeneous entries. It's the §2 lesson taken to
its conclusion: gate hard where the structured fields are reliable, reserve the LLM for the free-text
residual. The gate is really the **structured encoding of the decision-basis rules above**: the partition
key (`is_swing` + alive-bucket + `consensus_direction`) and the hard pair-checks (`net_verdict` /
`info_landscape_class` / `exposure_class`; strategy points: `direction` / `honesty`) are exactly the
situation differences a bi-encoder can't see, made deterministic. It only became possible because **v6
grew `situation` from one prose blob into many structured dimensions**
([dimension build spec](../extraction/situation_dimensions/dimension_schema_build_spec.md)) — that granularity is much of why
current dedup looks different from the v4-era prompt work above. The freeze-old fix from §8 also shipped
here. Current state: [report.md](report.md).

---

## Recurring threads (so a chapter's detail has a home in the arc)

- **The embedding ceiling** (§2, measured §5) — topic-not-stance is *why* an LLM is irreducible.
- **Weak models can't rewrite** (§3, §7) — the one reason REPLACE, DIFFERENTIATE, *and* MERGE were all
  pushed out of the online path; rewriting (MERGE) survives only on the pro-model batch pass.
- **Situation granularity** (§9) — `situation` grew from one prose blob into many dimensions (decomposed
  early for distinguishability; dimensionalized at v6 to mark critical moments); the structured dims are
  what made the deterministic gate possible. Schema history:
  [dimension build spec](../extraction/situation_dimensions/dimension_schema_build_spec.md).
- **Discard vs keep** (§6) — the open lever; tactic settled (targeted > directional), strategy deferred.
- **Conservative beats aggressive** (§5) — the reason `bounded` clustering is the batch default.

## Sub-logs (the detail behind each beat)

| Beat | Log | What it covers |
|---|---|---|
| §1–§2, §5 | [store_retrieval_impact/experiment_log.md](store_retrieval_impact/experiment_log.md) | does dedup help retrieval? (n=5 → n=39 correction) |
| §3, §6, §7 | [per_extraction/experiment_log.md](per_extraction/experiment_log.md) | online dedup prompt tuning v1→v11b; MERGE removal |
| §4, §6 | [batch_dedup/experiment_log.md](batch_dedup/experiment_log.md) | offline dedup prompt + two-pass tuning |
| §5 | [embedding_prefilter/experiment_log.md](embedding_prefilter/experiment_log.md) | automatic pre-filter calibration + the measured ceiling |
| §8 | [incremental_convergence.md](incremental_convergence.md) | incremental non-convergence diagnosis + fix |
| reference | [batch_architecture.md](batch_architecture.md) | batch-pass mechanics (how-it-works) |
| §9 / destination | [report.md](report.md) | current live state of everything + gap tracking |

---

## 10 · Addendum (2026-10-14): the ten-seat state

The arc above ends at the June freeze. The v8 port (October 2026, `memory_system/v8/`) changed the
shipped shape without reopening the tuning; each point is recorded in the sub-log it belongs to:

- **No rewriting anywhere now.** The observation fold runs the batch pass triage-only (KEEP/DISCARD on
  Flash-Lite) and the strategy-point dedup was cut to KEEP/DISCARD on 2026-10-13, with the judge unable
  to rewrite the point it keeps. The two-pass merge path is built, validated and off
  ([batch_dedup](batch_dedup/experiment_log.md), addendum).
- **The embedder changed and the thresholds with it.** `qwen/qwen3-embedding-8b` since 2026-10-12, every
  cosine threshold read per model; the prefilter's lines re-derived on the 65 golden cases only, and the
  232-case check shows the new strategy-point discard line would drop the log's own "topic, not stance"
  exemplar ([embedding_prefilter](embedding_prefilter/experiment_log.md), addendum). The Gemini-era
  prefilter lines had drifted unremapped since July.
- **Where the online pass runs.** As the store-write step of offline extraction, then the fold's triage
  over the new keys ([per_extraction](per_extraction/experiment_log.md), addendum).
- **The store is larger, the question older.** About 2,000 observations and 500 strategy points; the
  demo retrieves strategy points only; whether they are still a coverage rather than a duplication
  problem is unmeasured ([store_retrieval_impact](store_retrieval_impact/experiment_log.md), addendum).
- **Open from §8:** the `created_at` carry-through (Fix 1) is still not built; no non-Gemini judge has been
  run on either golden set.

---

## 11 · The June gap audit and its October rows (moved from the report, 2026-10-26)

Until 2026-10-26 the folder report carried this table of where the code had moved past the June
documents (rows 1–8, 2026-06-25) and past the June report itself (rows 9–12, 2026-10-14). The report is
now one present-tense account; the table is kept here as written, with its severity column (how
misleading the stale document was to a reader at the time).

| # | Gap | What the doc says | What the code does | Severity |
|---|---|---|---|---|
| 1 | **Merge fabrication guard** | contract implies merges are safe (counts summed, fails-safe survivor) | **No content check** — `operations.py` writes the rewritten text as-is; 2.5-pro fabricates ~1/3 of merges; the `fabrication_detected` judge exists only in `evaluation/`, unwired from apply | High — a reader *under*-trusts the risk; the item to close before the offline pass is turned on |
| 2 | **Freeze-old guard** | [incremental_convergence.md](incremental_convergence.md): Fix 2 "not yet built" | **Built & live** (commit `6704202`, 2026-06-16; `operations.py:137-150`, tests) | High — doc reads as an open risk that is actually closed; corrected via that doc's banner |
| 3 | **`created_at` on merge (Fix 1)** | proposed alongside Fix 2 | **Still NOT built** — `created_at` lives only on the envelope and resets on re-put (`operations.py:99-105`, `incremental.py:42`) | Medium — Fix 1 underpins Fix 2's old/new partition across runs; genuinely open |
| 4 | **The deterministic gate** | absent from every evidence doc | **Live** online + batch (`dedup_gate.py`, `gate_enabled=True`) | Medium — the most important current mechanism, undocumented before this report |
| 5 | **Namespace scoping** | [batch_architecture.md](batch_architecture.md): "dedup within a namespace" | namespace **+ gate bucket** (`clustering.partition_key_for`) | Low — additive; banner added to that doc |
| 6 | **Online MERGE** | per_extraction journeys MERGE v1→v11 | **removed** — KEEP/DISCARD only (`schemas.py:84-91`) | Low — the log's own endpoint; stated as live in its close |
| 7 | **Prompt version** | logs cite v9d / v11b | live = stabilized "v6.1" in `Agents/prompts/dedup.py` (same v9d ordering) | Low — naming only |
| 8 | **Run defaults** | scattered across logs | online on (`dump_enabled`); incremental off; bounded; gate on | Low — consolidated in the config table above |
| 9 | **Merge path dormant** (2026-10-14) | two-pass config "recommended", `two_pass=True` | the v8 fold runs triage-only (`skip_verify=True`); strategy-point dedup is KEEP/DISCARD with no rewrite (`2036f83a`); the 2.5-pro verify model is configured and never called | Medium — the fabrication risk in gap #1 is dormant, not open; the merge results describe a built, validated, switched-off path |
| 10 | **Prefilter thresholds** (2026-10-14) | the constants table above (May values on `gemini-embedding-001`) | per-model table in `Agents/llm_factory/embeddings.py`; on `qwen/qwen3-embedding-8b`: observations keep < 0.72 / discard ≥ 0.94, strategy points 0.61 / 0.88, derived on the 65 golden cases only; on the 232 cross-game cases the strategy-point line auto-discards two labelled keeps (one is case 155) and the observation lines decide 1.7% | High — "zero-error on golden + cross-game" no longer holds for the live model; the strategy-point path is dormant, the observation path nearly idle |
| 11 | **Threshold drift after the July embedder swap** (found 2026-10-12) | thresholds "calibrated" | the four prefilter lines were never remapped from `-001` to `-2`; the Gemini-era prefilter auto-kept some labelled duplicates for three months | Low now (model retired) — but the rule stands: a threshold is meaningful only for the model it was set on |
| 12 | **Fix 1, `created_at` on merge** (re-checked 2026-10-14) | gap #3 | still not built (`operations.py` carries no `created_at`); moot while no merge runs | Low while the merge path is off |

**Open work (not just stale docs), as written in June:** two genuine not-yet-built items remain, both
gating the offline pass. **(a) Merge fabrication guard** (gap #1) — the `fabrication_detected` judge
from the batch_dedup eval is the natural pre-apply check but isn't wired into `operations.py`, so a
fabricated merge would land; it's the top risk to close before the offline pass is turned on by
default. **(b) `created_at` preservation** (gap #3) — without it, the old/new partition the freeze-old
guard relies on is only trustworthy within a single run, so unbounded repeated incremental runs could
still drift; a prompt-neutral apply-layer change tracked in
[incremental_convergence.md](incremental_convergence.md).

**The October paragraph, as written (2026-10-14):** The sections above are the June truth; gaps #9 to
#12 record where the ten-seat game moved. In one paragraph: the gate, the bounded clustering, the online
KEEP/DISCARD pass (now the store-write step of offline extraction) and the freeze-old guard are live and
unchanged; nothing rewrites an entry anywhere, since the fold runs triage-only and the strategy-point
dedup is KEEP/DISCARD; the embedder is Qwen with its own threshold table, and the prefilter's lines on it
rest on the 65 golden cases alone. The sub-logs' dated addenda carry the detail and the owner's rulings
(`memory_system/v8/decisions.md` §14 for the strategy-point rules and the credit of a merged duplicate).

**Status on 2026-10-26.** Rows 1, 3, 9–12 stand. Row 2: the guard is built; the learning tick ran its
fold without it (its working folder carries no last-dedup marker), found in the code and fixed the
same day: both tick steps now name their new entries (the report's "Built and off"). Row 7: the name "v6.1" is not in the
code. Row 8: `dump_enabled` no longer gates any dedup; the online pass runs in
`write_extracted_store`. Since 2026-10-15 the keep-or-discard judges default to Claude Haiku 5.5
(`DEFAULT_DEDUP_MODEL`, `TickConfig.dedup_model`), unscored on either golden set.
