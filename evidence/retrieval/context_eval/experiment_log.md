# Context-Based Retrieval Evaluation

> **🛑 EXECUTION DEFERRED (2026-06-01) — DO NOT START LABELLING.** The methodology below is
> hardened and final, but **all human labelling is parked until after the foundation rebuild.** Five
> substrate changes are coming (parallel→sequential game, more roles, consolidated tracing, night-phase
> memory, **v5 DB replacing v4_deduped_v2**) — and every gold here is conditioned on that substrate
> (candidate pools are top-10 retrievals from v4_deduped_v2; cases are day-only / 4-role / parallel).
> Labelling now would be thrown away. **What survives wholesale: the methodology** (two-gold opposite
> blinding, acceptance gates, progressive staged labelling, balance analysis). **Resume = re-run the
> case-building + labelling on stable v5**, cheaply via the consolidated tracing pipeline. See
> [[project-ship-roadmap]] Phase A/B. Everything below is the design to execute *then*, not now.

> **⏩ READING GUIDE / CURRENT STATE (updated 2026-05-31). Start here if you're picking this up fresh.**
> This log is a long investigation with several deliberate course-corrections. Read this block,
> then jump to **"FORWARD PLAN (Part 1 + Part 2)" at the very bottom** — that's the actionable
> spec. Everything between is the chronological evidence trail.
>
> **One-paragraph journey.** Goal: build a retrieval eval that labels memory relevance against
> the *game context*, not the situation summary. A precondition diagnostic found (1) the cheap
> auto label panel (mistral/nim) is **unusable** as judges — they label almost everything
> "relevant" (mistral 7/1848 zeros, nim 0; nim also failed 21% of long prompts); (2) query-only
> labels **systematically over-credit topical matches** — 93% of their disagreements with the
> strong judges are over-crediting, and the reranker's *merged training labels* 99%, concentrated
> in the **majority-vote merge tier** (458/1383). (3) Relevance has a hard **~80% inter-judge
> ceiling** (ChatGPT vs Sonnet agree 80.5% binary / 64.5% exact) — no single labeler is "truth."
> (4) flash-lite **with context** is a near-ceiling cheap judge (77% vs the 80.5% ceiling); adding
> chain-of-thought doesn't raise accuracy but **halves its over-crediting bias** (92%→66%). (5) A
> cheap "does the bias actually hurt the reranker" gate: held v4's ranking fixed, re-scored vs
> strict strong-judge labels — observations drop ~0.06–0.09 NDCG@5 (significant only after folding
> val in, n=25; the n=13 first look was underpowered), strategy points flat → **reranker relabel
> is low-priority**.
>
> **The conceptual turn that drives the forward plan:** the reranker eval and the summary-recall
> eval need **two different gold sets with *opposite* blinding** (reranker = relevance to the
> *query*, context-blind; summary-recall = usefulness given the *context*, summary-blind). Our
> existing strong-judge labels saw **both** query and context → a mash-up that is the clean gold
> for *neither*. The forward plan builds the two golds properly, once, with a vendor-diverse LLM
> panel + a human anchor. **Status: design fully specified, no Part-1/Part-2 labeling run yet.**

## Motivation

The current retrieval eval labels memory relevance against the **situation summary query** — "is this memory relevant to the situation description?" This makes the ground truth query-dependent: if the situation summary misses a key tension, a memory that addresses that tension scores 0 even though it's exactly what the agent needs.

This creates a blind spot: we can measure reranker quality and retrieval NDCG, but we cannot evaluate the situation summary itself or whether the agent uses retrieved memories effectively. The only end-to-end signal is LLM-as-judge, which misses information gain (see `feedback-llm-judge-limitations.md`).

## Proposed approach

Label memory relevance against the **game context** instead of the situation summary. The situation summary is used only to fetch a candidate pool — the ground truth is "would this memory help the player in this game state?"

### Labeling process

1. For each eval case, use a good situation summary to retrieve top-N candidate memories (observations + strategy points)
2. Show the labeler the full game context (same as `format_game_state` renders) plus each candidate memory
3. Label: "Is this memory useful for a player in this game situation?" (0/1/2 graded scale)
4. The situation summary is NOT shown to the labeler — relevance is judged against the raw game state

### What this enables

The same label set serves two modular evaluations:

**1. Situation summary recall**

For a given situation summary, retrieve memories and measure what fraction of context-labeled golden memories appear in the top-K. Different summaries can be compared on the same fixed ground truth:

- Summary A (2.5-pro, v4b prompt) retrieves 9/10 golden memories → recall 0.90
- Summary B (flash-lite, old prompt) retrieves 6/10 → recall 0.60
- Summary C (new prompt iteration) retrieves 10/10 → recall 1.00

This directly evaluates whether the situation summary captures the right dynamics without needing to judge the agent's action.

**2. Strategy adoption**

Given the golden relevant memories (the "right inputs"), does the agent actually use them? This isolates the downstream question: retrieval delivered good content — did the agent apply it?

- Measures the gap between "had the right memory" and "acted on it"
- Can evaluate different action prompts or models with retrieval held constant

### Key difference from current labels

| | Current (query-based) | Proposed (context-based) |
|---|---|---|
| Ground truth tied to | Situation summary | Game state |
| Can evaluate situation summary | No (circular) | Yes (recall metric) |
| Can evaluate strategy adoption | No | Yes (given golden memories) |
| Reusable across prompt iterations | No (new query = new labels) | Yes (game state is fixed) |
| Reranker training data | Yes | Also yes (query, memory, label triples still valid) |

### Relationship to current work

The reranker cross-encoder training (see `evidence/fine_tuning/cross_encoder/experiment_log.md`) trains on (query, memory, relevance) pairs. This is unaffected — the reranker scores relevance to a query regardless of how the query was generated. The two efforts are complementary:

- **Reranker CE**: improves scoring given a fixed query
- **Context-based eval**: evaluates whether the query itself is good

## Status

Idea stage. Not yet implemented. Current labeling sprint (109 cases for reranker CE) uses query-based labels. A future iteration could re-label a subset against game context to bootstrap this eval.

---

# Precondition diagnostic: does full context actually move the labels? (2026-05-31)

Before building any new labeling pipeline, we need to know whether the context-based
eval can find signal *at all*. This section records the reasoning and the cheap
diagnostic we run to decide go / no-go.

## What we already have, and how it was built

The reranker labeling sprint produced, for 109 cases, a pool of candidate memories
(top-10 bi-encoder on `v4_deduped_v2`) labeled 0/1/2 for relevance. Crucially, the
pipeline already contains an *accidental* version of the experiment we care about:

| Source | What it saw when labeling | Stored at |
|---|---|---|
| flashlite / mistral / nim (auto) | **golden situation summary + memory only** (query-based) | `expanded_labels_{flashlite,mistral,nim}.json` |
| chatgpt / sonnet (manual) | **full game state + golden summary + memory** (context-seeing) | `manual_batches/`, merged into `expanded_merged_labels.json` |

Provenance worth pinning down (verified against the artifacts, not memory):

- The **golden situation summaries were generated by `gemini-2.5-pro`**
  (`expanded_golden_situations.json` → `model: gemini-2.5-pro`). They are the
  best-available summary and were used both as the retrieval query (to build the
  candidate pool) and as guidance shown to the manual labelers.
- **`opus-4.6` was the label *tiebreaker*** (`expanded_merged_labels.json` stats:
  `tie_tiebreaker: 148`), **not** the summary author.
- The candidate **pool is therefore pro-anchored**: every labeled-useful memory is,
  by construction, something the pro summary already retrieved at top-10.

## The two distinct "ceilings" (don't conflate them)

1. **Label ceiling — the measuring stick.** The manual labels (chatgpt + sonnet,
   full context + pro summary, opus tiebreak) are the best-available judgment of
   *"is this memory genuinely useful for the player in this game state?"* This is the
   **ground truth** a recall eval scores against — it is the ruler, not a model to beat.

2. **Summary ceiling — a model to beat.** The pro summary's *retrieval* is the upper
   bound on achievable recall. But it is a ceiling **partly by construction**: because
   the candidate pool was retrieved *using* the pro summary, a weaker summary is graded
   only on "did you recover the useful subset of what pro already found." That is a real
   number, but pro-anchored, not absolute.

## Caveats that bound how far we can read the results (raised in review)

- **Pool-coverage bias → need a union pool for absolute numbers.** To measure a
  summarizer's *true* recall we must pool the **union** of candidates retrieved by
  *every* summary model under test and label that union. Otherwise a memory that a
  weaker model retrieves but the pro model missed is simply unlabeled — it silently
  counts as a miss (or falls outside the eval), unfairly inflating the pro ceiling.
- **The manual ceiling is a "two-step, somewhat arbitrary" ceiling.** The full-context
  labelers judged with the **pro-model summary as guidance**, not after writing their
  *own* summary from the raw state. So their labels conflate (a) the labeler model's
  own judgment with (b) the pro summary's framing. It is **not** a clean estimate of how
  that labeler would perform if it generated its own situation summary and then labeled.
  It is the best usefulness proxy we have, but it is summary-anchored.

## What this diagnostic actually measures (and why this design)

Two candidate comparisons:

- ❌ **Manual (context-seeing) vs auto (query-only).** Free — uses only stored labels —
  but **confounded**: chatgpt/sonnet are stronger labelers than flashlite/mistral/nim,
  so any divergence mixes "saw context" with "smarter model." Can't attribute the cause.
- ✅ **Same auto panel, context-visible vs its own query-only labels.** Hold the model
  constant; add full game state to the *existing* query-based prompt (keep the pro
  summary — replacing it would conflate "added context" with "removed summary"). The
  delta is then the **pure effect of seeing context**, with no capability confound. This
  mirrors the structure of the SP label-drift diagnostic
  (`evidence/fine_tuning/cross_encoder/reranker/scripts/sp_label_drift_diagnostic.py`):
  toggle exactly one thing, keep the rest byte-identical.

We run the ✅ design. Condition B (context) prompt = the production reranker prompt with
one added `## Full game state` block; everything else (intro, situation, memory, 0/1/2
scale, response instruction) is byte-identical to the stored query-only run, so the
label delta isolates context. Baseline (condition A) is read directly from the stored
`expanded_labels_{model}.json` — no re-run needed.

## Decision criteria — movement alone is NOT enough

The question isn't just "did labels change," it's "did they change in a *structured,
meaningful* direction." Three outcomes:

- **Barely moves (low flip rate, no directional bias).** The query-only labels already
  encode what context would add → the pro summary captures what matters → a separate
  context-based labeling process adds little, and **the whole eval may be unnecessary**
  (at least against good summaries).
- **Moves with a clear asymmetry** — context *promotes* memories the query-only panel
  scored 0 up to 1/2, and those items correspond to tensions the summary under-described
  → the summary is lossy, context labels are a genuinely different ground truth →
  **build the eval.**
- **Moves but symmetric / unstructured** (flips both directions, no bias). This is
  labeler *noise* from a harder task, **not** signal. More movement here would argue
  *against* trusting context-only labels, not for them. We must distinguish this case
  from the asymmetric one — hence we report signed Δ and the 0→{1,2} promotion rate
  separately, not just a raw flip rate.

## Run

Panel: `gemini-3.1-flash-lite` (thinking=low), `mistral/mistral-small-2506`,
`nim/meta/llama-3.1-8b-instruct` — identical to the production auto panel.
Script: `evidence/retrieval/context_eval/scripts/context_drift_diagnostic.py`.
Sampled run first (seed 42) for a fast read; `--sample 0` for the full 1,848 items.

## Results (full 1,848 items, 2026-05-31)

Artifacts: `labels/context_labels.json` (context condition), `labels/drift_report.json`.

### Per-model drift (context − query-only)

| Model | flip rate | mean signed Δ | 0→useful | useful→0 | context nulls |
|---|---|---|---|---|---|
| **flashlite** (gemini-3.1-flash-lite) | 27.3% (504/1848) | **−0.107** | 13.3% (41/308) | 14.4% (221/1540) | 0 |
| mistral (mistral-small-2506) | 13.0% (241/1848) | −0.022 | 28.6% (2/7) | 0.8% (14/1841) | 0 |
| nim (llama-3.1-8b) | 34.1% (500/1465) | −0.319 | 0/0 | 1.0% (15/1465) | **383** |
| consensus (rounded mean) | 21.3% (393/1848) | −0.131 | — | — | — |

### Label distributions — query-only → context

| Model | query-only (0 / 1 / 2) | context (0 / 1 / 2) |
|---|---|---|
| flashlite | 308 / 672 / 868 | **488** / 510 / 850 |
| mistral | **7** / 1012 / 829 | 19 / 1029 / 800 |
| nim | **0** / 1114 / 734 | 15 / 1310 / 140 (+383 null) |

### What this says

**1. The cheap auto panel cannot label context relevance — only flashlite is usable.**
mistral assigns "not relevant" to **7 of 1848** items query-only (and 19 with context);
nim assigns it to **0**. They are near-constant "relevant" stamps with no discriminating
power, so their drift numbers are noise on a degenerate baseline. nim additionally
**failed 383/1848 (21%)** of the longer context prompts — it destabilizes on long input.
A context-based golden set therefore **cannot** be built from this panel; it needs strong
labelers (which is exactly what the chatgpt/sonnet manual labelers were).

**2. For the one reliable labeler (flashlite, 0 nulls both conditions), context moves
labels meaningfully and in a *structured* direction — this is signal, not noise.**
27.3% of labels flip. The shift is specifically **1 → 0**: marginal "partially relevant"
labels get pruned (672 → 510), zeros nearly double (308 → 488), while strong matches are
preserved (2s: 868 → 850, basically flat, with even 4 items 0→2). A blanket
"longer-prompt-lowers-scores" artifact would depress 2s too; preserving strong matches
while pruning marginal ones is what genuine applicability-checking looks like.

**3. The original premise inverts.** We expected context to mainly *recover
summary-missed useful memories* (a recall gap → 0→useful). That direction is real but
**modest: 13.3% of zeros** (41 items). The **dominant** effect is the opposite —
context *prunes topically-plausible-but-situationally-useless* memories: **221 demotions
vs 41 promotions, ~2.3:1**, concentrated in the marginal "1" band. Query-only relevance
**over-credits surface/topical matches** (same role, same phase keywords echoed in the
summary); full context reveals many don't bear on the live decision.

### Verdict: qualified GO, with two reframes

- **Not redundant.** By our own criterion (if labels barely moved, skip the separate
  process) the reliable labeler moved 27% with a consistent directional bias → context
  captures something query-only labeling does not. The eval is worth building.
- **Reframe the metric from recall to precision/efficiency.** The bigger gap the summary
  creates is not "useful memories missed" but "useless memories surfaced because they look
  topically on-theme." This dovetails with the existing reranking findings, where
  efficiency/redundancy (not recall) were the metrics that moved. A context eval should
  foreground precision/efficiency of the retrieved set, not just recall@K.
- **Use strong labelers.** Don't auto-label context relevance with the cheap panel. The
  next step is the *free* comparison we set aside: do the strong context-seeing manual
  labelers (chatgpt/sonnet) show the same prune-dominant correction vs query-only? If yes,
  we already hold a usable context ground truth and have corroboration from a second model
  class.

### Connected finding (reranker training data)

The reranker's merged training labels blended these auto labelers (3) with the 2 manual.
Because mistral/nim almost never emit "0", the **auto majority is biased toward
"relevant"** — a plausible source of topical over-ranking in the trained reranker. Worth a
follow-up check; not pursued here.

### Caveats on this diagnostic

- Only the candidate **pool** is held fixed (pro-summary-retrieved); this varies the
  *labeling* input, so it measures **label** divergence, not the production summary's
  retrieval recall. The recall question still needs the varying-summary eval (and a union
  pool — see caveats above).
- Anchored on flashlite because it is the only stable, discriminating labeler here; the
  mistral/nim signals are largely uninformative for the reasons above.

## Follow-up: who do we trust — weak labeler or strong judges? (2026-05-31)

The drift write-up called flashlite's context-pruning "genuine applicability-checking,"
which assumes flashlite is *right*. It might instead be a weak judge discarding nuance the
strong judges caught. We have both strong context-seeing judges (chatgpt, sonnet) per item
in `expanded_merged_labels.json` (`labeling.scores`), so we can test it directly. Both the
strong judges and our context-flashlite saw the **same** information (pro summary + full
context); the only difference is model strength.

### Aggregate: context moves flashlite TOWARD the strong judges

- Binary "useful vs not" agreement with strong judges: query-only **68.1%** → context **74.0%**.
- When context changed a flashlite label, it moved **toward** the strong judges 2:1
  (13.4% toward, 7.5% away, 79.2% unchanged distance).

So the **input** (judge against full context) is validated — it pulls the weak model toward
the strong ceiling. The weak *model*, however, is a different question.

### Spot-check of the starkest disagreements (read by hand)

**Prune direction** (context-flashlite=0, both strong=2; 6 such items):
- *wolf, day 3* — memory = "wolves stay quiet during village infighting over a mis-lynch,
  then join the emerging vote to stay hidden." Situation = exactly that. Textbook-applicable.
  Query-only flashlite correctly said **2**; context flipped it to **0**. **flashlite wrong,
  strong right.**
- *healer, day 3* — healer-concealment cross-examination tactic, clearly applicable to a
  healer navigating post-mistake recriminations. flashlite=0 too harsh; **strong better.**
- *healer, day 2* — endgame/info-rich memory vs a day-2/info-starved situation; genuine
  phase mismatch. Transferable bit ("healer votes with majority to hide") makes it ~partially
  useful. **Truth ≈ 1; flashlite=0 too harsh, strong=2 too generous.**

**Over-keep direction** (context-flashlite=2, both strong=0; 37 such items):
- *wolf endgame* — memory = wolves *amplify* a consensus to kill an innocent; but here the
  wolf's own ally is the cornered target and must *break* consensus. Opposite move. flashlite
  over-credits a surface match; **strong right.**
- *villager, day 2* — memory's lesson hinges on "previous day's voting record," which doesn't
  exist yet on day 2. Phase/info mismatch; context even pushed flashlite 1→2 (more wrong).
  **strong right.**

Read: in the residual disagreements flashlite errs in **both** directions; the strong
judges' calls are consistently the more defensible. The aggregate convergence means context
is the right setup, not that flashlite-as-judge is trustworthy.

### Decisive asymmetry, measured against the strong judges (not flashlite's drift)

| Comparison vs strong judges (binary useful cut) | agree | over-credit | under-credit | % of disagreements over-crediting |
|---|---|---|---|---|
| query-only flashlite | 1258 | 546 | 44 | **93%** |
| **official merged consensus** (reranker training labels) | 1329 | 514 | 5 | **99%** |

Query-only labeling, and the merged consensus built largely from the cheap panel,
**systematically over-credit relevance** — they call ~510–550 memories "useful" that the
strong context-aware judges reject. Under-crediting is negligible. This is the clean,
trusted-reference version of the drift finding: the gap the summary+query-only labeling
creates is **false-positive topical matches**, not missed memories.

### Conclusions

1. **Trust the strong judges (chatgpt/sonnet), not the cheap panel.** Confirmed two ways:
   degenerate label distributions, and erring in hand-checked disagreements.
2. **Judge against full context — but with a strong model.** Context is the right input
   (moves even the weak model toward the ceiling); the weak model is the weak link.
3. **Build the context eval on the strong context-seeing labels we already have.** No new
   cheap-panel labeling. The eval's metric should foreground **precision/efficiency**
   (rejecting topical false positives), corroborated here against the trusted judges.
4. **Reranker-training concern is now quantified, not hypothetical:** the merged training
   labels over-credit vs the strong judges on 514/1848 items (99% of their disagreements).
   The reranker likely inherited a topical-over-ranking bias. Worth a dedicated follow-up:
   re-derive reranker labels weighting the strong judges, and re-check NDCG.
5. **Caveat on the ceiling:** the strong judges saw the pro summary as guidance and were
   occasionally a touch generous themselves (the day-2 endgame case). They are the best
   proxy we have, not infallible — spot-audit, don't deify.

## Follow-up 2: can flash-lite reason its way to the strong judges? (2026-05-31)

Question: is flash-lite a bad *judge*, or just bad at judging without doing the reasoning
itself? Condition C gives flash-lite the full game state with **no pro summary** and makes
it write its own situation analysis first, then rate (chain-of-thought).
Script: `scripts/flashlite_self_summary_judge.py`; 400-item sample, seed 42.

**First, the realistic ceiling.** Relevance is intrinsically fuzzy: the two strong judges
agree with **each other** only **80.5%** (binary useful cut) / 64.5% (exact 0/1/2) on the
same 400 items. No labeler is "ground truth"; ~20% binary disagreement is the noise floor.

### Agreement with strong judges (same 400 items, 95% CI ≈ ±4.9%)

| Condition | agreement | vs ceiling 80.5% |
|---|---|---|
| A. query-only (no context) | 73.5% | below |
| B. context + pro summary, direct rate | **77.0%** | ~at ceiling |
| C. context + self-analysis (CoT), no pro summary | 75.2% | ~at ceiling |
| *ceiling: chatgpt vs sonnet* | *80.5%* | — |

All three flash-lite conditions are within one CI of each other and of the ceiling. **On
raw accuracy, CoT does not beat simply handing flash-lite the context+pro-summary** (75.2 vs
77.0, tied; head-to-head when they differ, B is closer to strong 55 vs 39). So self-reasoning
doesn't make flash-lite a *more accurate* judge.

### But CoT substantially reduces the over-crediting BIAS

Direction of the disagreements (over = flash-lite says useful, strong say not):

| Condition | over | under | % of disagreements over-crediting |
|---|---|---|---|
| A. query-only | 98 | 8 | **92%** |
| B. context + pro summary | 401 | 79 | 84% (full 1848) |
| C. context + self-CoT | 65 | 34 | **66%** |

CoT roughly halves the topical over-crediting skew. Crucially, its **accuracy did not drop**
while doing so (75.2% ≈ B's 77%) — the extra "not useful" calls land mostly on items the
strong judges *also* reject, so this is genuine bias-correction, not blind conservatism.

### What this means

- **Relevance labeling has a hard ~80% ceiling.** Stop treating any single labeler as truth;
  every eval here is bounded by this.
- **flash-lite + context is a near-ceiling *accurate* cheap judge** — much better than the raw
  "68% vs strong" number (Follow-up 1) implied, because that was query-only *and* measured
  against a noisy reference. With context, flash-lite is about as accurate as the task allows.
  (mistral/nim remain degenerate — this is flash-lite specifically.)
- **CoT's value is bias, not accuracy.** If we want a cheap labeler that does NOT inject the
  topical-over-ranking bias, flash-lite-CoT is the best cheap option: near-ceiling accuracy
  *and* roughly balanced errors.
- This **reopens cheap scaling.** Strong judges give gold labels on only 109 cases; a
  flash-lite-CoT pass is near-ceiling-accurate and low-bias, so it can label far more cases
  cheaply — likely a bigger lever for the reranker than re-deriving labels on the same 109.

## Cross-reference: this confirms a KNOWN bias in the reranker labels, and locates it

The reranker experiment log (`evidence/fine_tuning/cross_encoder/reranker/experiment_log.md`,
"Systematic auto-model bias in new labels") already flagged exactly this: *"the 3 auto models
systematically inflate relevance compared to ChatGPT (full context)... matched surface-level
themes without checking whether the memory's preconditions actually applied."* Our work adds
two things:

1. **Scale + survival through the merge.** The bias isn't diluted away by the 5-model vote:
   the official merged labels over-credit vs the strong judges on **514/1848** items.
2. **Exactly where it survives** — the **majority tier**:

   | merge confidence tier | items | over-credit vs strong judges |
   |---|---|---|
   | unanimous (5/5) | 281 | 0% — clean |
   | **majority (3+ agree)** | 1383 | **33% (458) — 89% of all the leak** |
   | tie_tiebreaker (Sonnet) | 144 | 20% |
   | opus_tiebreak | 40 | 68% (n=40; "when in doubt → 1") |

   The 3-of-5 majority rule lets the correlated generous auto-trio (Mistral+NIM agree 73%,
   rarely emit "0") outvote the two careful strong judges. Unanimous and Sonnet-tiebreak
   tiers are fine.

**Debiasing needs no relabeling** — re-merge trusting ChatGPT+Sonnet on the majority-tier
disagreements (flip ~458 labels useful→not). See recommendation in
[[project-context-based-retrieval-eval]] / below.

### Recommended sequence for the reranker (disciplined, cheap-first)

1. **Re-derive the TEST split only** with a strong-judge-weighted merge (ChatGPT+Sonnet
   agree → their label; split → opus/keep), and **re-score the existing v4 reranker on it.**
   Zero training. Answers: does the bias actually manifest in v4's rankings, or wash out?
2. **Only if v4 degrades on clean labels:** re-derive the train split too, retrain (Modal),
   compare old vs new model *on the clean test labels* (not the old biased ones).
3. **Caveats:** (a) the reranker input is situation/summary-only (per v5 ablations), so only
   the over-crediting that's visible in the situation text — phase/precondition mismatch — is
   learnable; context-only-visible relevance is not. Expect partial gains. (b) There is a
   standing decision to not over-optimize reranking until downstream game-outcome
   measurement exists ([[reranking-pipeline-decisions]]); this re-eval respects it by
   *measuring* before optimizing. (c) For the stated ~2,800-pair volume bottleneck,
   flash-lite-CoT is the cheap low-bias way to scale, rather than more 3-auto-majority labels.

## Premise lock-in before the (costly, irreversible) human pass (2026-05-31)

**The strong-judge / human labels serve BOTH goals** (confirmed):
- (a) **Context eval ground truth** — validating situation-summary recall + strategy adoption (the original proposal).
- (b) **Reranker re-baseline** — replacing the over-crediting merged labels.

**Memory-type input-match rule** (governs which existing labels are reusable — the label
target must match what the reranker actually scores):
- **Observations:** reranker input = `situation | approach | outcome`; labelers saw the same
  → existing ChatGPT/Sonnet OBS labels are **valid, reusable, soft-averaged**. ✓
- **Strategy points:** reranker input = **situation-only**; labelers saw `situation | Action`
  → **mismatch**. The existing SP labels are "situation+action usefulness", not "situation
  relevance". This is the **untested residual** from the reranker log (the auto panel showed a
  0–4.6% action effect, but ChatGPT/Sonnet were never retested situation-only). For a clean SP
  reranker target, SP must be re-judged **situation-only** — a cheap LLM pass, not human — and
  situation-only is the correct objective on first principles (the agent judges the action
  downstream = adoption, not retrieval).

**Cost-ordered sequence (cheap-first):**
1. **Re-eval v4 on OBSERVATION strong-judge labels** (the clean, matched subset) — no humans.
   Does the over-crediting actually manifest in v4's observation ranking, or wash out? **Gate
   the rest on this.**
2. If it manifests: SP situation-only LLM re-pass + OBS soft labels → retrain → compare on
   clean labels.
3. **Human anchor (~150 stratified, blind)** validates the LLM ground truth **once**, serving
   both goals — not a per-consumer redo. **Status: DESIGNED, not yet executed** (stratification
   60 both-useful / 45 both-not / 45 disagree; sample size from a proportion-CI calc, p≈0.8,
   ±8% at 95%; soft strong-judge targets so no tiebreaker bias).

**Caveat bounding step 2:** the reranker input can't see full game context, so only the
over-crediting visible in the *situation text* (phase/precondition mismatch) is learnable;
context-only relevance is noise to it. Expect partial gains — measure, don't assume.

### Step 1 result: v4 observation ranking under clean labels (2026-05-31)

Held v4's ranking fixed, scored it on its 13 round-2 held-out test cases (observations only —
the input-matched subset; 4 round-1 test cases skipped, no strong labels).
Script: `scripts/reeval_v4_clean_obs.py`.

| v4 observation ranking, NDCG@5 scored against… | value |
|---|---|
| BIASED merged labels (what v4 was tuned toward) | 0.905 |
| CLEAN soft strong-judge labels | 0.845 |
| *bi-encoder reference vs clean* | *0.737* |

Paired drop biased→clean: **+0.059, 95% CI [+0.001, +0.118]** (n=13), driven by 2–3 cases
(per-case drops: most ≈0, two at 0.23/0.30).

**Read — observations don't justify a relabel.** The drop is *small and borderline*
(CI barely clears 0, n=13, fragile). And under the strict labels v4 still beats the bi-encoder
by **+0.108** — most of its ranking value survives the stricter grading. So the over-crediting
bias did **not** meaningfully corrupt v4's *observation* ranking. Spending a relabel + human
pass to fix observations is not warranted on this evidence.

**The open question is strategy points, not observations.** This step deliberately excluded SP
(input mismatch). SP is exactly where (a) the labels saw the action the reranker can't, and
(b) v4 was weakest (SP NDCG@5 0.841 overall, investigator×SP 0.629). So the gate is *half*
closed: observations are fine; the only potentially-justified relabel is the **SP
situation-only** pass — which is also the one with the cleanest first-principles rationale.
Next: a SP situation-only LLM re-pass, then the same re-eval on SP before any retrain/human pass.

### Step 1b result: v4 strategy-point ranking under clean labels — gate now closed (2026-05-31)

Before paying for a manual ChatGPT/Sonnet situation-only SP re-pass, we ran the SP gate with
the **existing** (action-visible) strong-judge SP labels — cheap-first. Script:
`scripts/reeval_v4_clean_sp.py`. SP doc = situation-only (matches reranker input).

| v4 SP ranking, NDCG@5 scored against… | value |
|---|---|
| BIASED merged labels | 0.851 |
| CLEAN soft strong-judge labels | 0.810 |

Paired drop biased→clean: **+0.041, 95% CI [−0.031, +0.113] — includes zero, not significant**
(n=13). Per-case mixed: a couple drop, but the investigator cases (v4's weak cell) actually
*improve* under clean labels.

**Conclusion — the reranker relabel is NOT warranted.** Across **both** memory types, v4's
ranking holds up against the strict strong-judge labels: observations drop +0.059 (barely
significant, 2–3 cases), strategy points +0.041 (not significant), and v4 still beats the
bi-encoder under clean labels. The over-crediting bias is real in the **labels** but did not
translate into materially worse reranker **rankings**. Likely mechanism: the over-crediting
lives in the marginal "1 vs 0" band, which sits at lower ranks; NDCG@5 is driven by the top
"2"s where the judges agree and v4 already ranks well. Because the SP ranking holds even under
action-visible labels, the **action-visibility residual is moot for ranking** — no situation-only
re-pass needed.

### Step 1c: power re-check — the n=13 gate was underpowered (2026-05-31)

n=13 detects only a ~0.10 NDCG drop reliably (per-case SD ≈ 0.12 → ~40–45 cases needed for a
0.05 effect). Folding in the held-out **val** cases roughly doubles n (script: `scripts/
reeval_v4_power.py`):

| memory type | split | n | drop biased→clean | 95% CI |
|---|---|---|---|---|
| observation | test | 13 | +0.059 | [+0.000, +0.118] |
| observation | **test+val** | **25** | **+0.087** | **[+0.022, +0.151]** ← significant |
| strategy_point | test | 13 | +0.041 | [−0.031, +0.113] |
| strategy_point | **test+val** | **24** | **+0.030** | [−0.017, +0.077] |

**Revised conclusion (supersedes the "not warranted" call above):**
- **Observations DO degrade under clean labels** — a real ~0.06–0.09 NDCG@5 gap, significant at
  n=25. The n=13 "not significant" was a power artifact. (Caveat: val was used for model
  selection, so part of its larger drop may be selection optimism; the true effect is likely
  the lower end, ~0.06. test-only alone is borderline-significant.)
- **Strategy points do NOT degrade** — flat and non-significant even at n=24.

**Net decision (revised):**
- **Observations:** a relabel+retrain has a **small but real** expected upside (~0.06–0.09
  NDCG@5) **and is cheap** — the existing ChatGPT/Sonnet OBS labels are input-matched, so it's
  just soft-averaging them and retraining, **no new labeling.** Worth doing as a low-cost
  experiment; whether ~0.07 NDCG matters is ultimately a downstream-game-outcome question
  ([[reranking-pipeline-decisions]]).
- **Strategy points:** keep as-is. No significant degradation, and the situation-only re-pass
  (expensive, manual) is not justified.
- **Human anchor:** justification is **purely the context eval** now, not the reranker.
- The over-crediting finding stands as a **labeling-process** lesson (cheap-panel majority vote
  inflates relevance; use strong judges or flash-lite-CoT + a human anchor).

**Methodological note:** the n=13→n=25 revision is itself the lesson — a cheap directional gate
flagged "maybe fine," but it was underpowered; expanding the held-out set before concluding
changed the answer for observations. Report the gate as *directional*, not definitive.

---

# ═══════════ FORWARD PLAN (Part 1 + Part 2) — the actual next steps (2026-05-31) ═══════════

This is the consolidated, actionable spec. Everything above is the evidence that led here.

## ⭐ LATEST SCOPE DECISION (2026-05-31, end of session) — read this before §1–8

The full validated two-gold program below is **deliberately descoped** to fit the actual deliverable:

- **Part 1 (context / summary recall): SMALL directional smoke test, NOT the full gold.** The only
  live reason to run it is deciding whether to **swap flash-lite for another writer** — a switch
  decision needs a *direction* ("promising / not / clearly worse"), not a statistically-validated
  gold. Run a small stratified sample (~10–20 cases, exact n TBD), judge with a strong model, report
  as **directional, expand only if promising.** Generate the candidate-model summaries anyway — they
  double as Part 2 queries (the realistic-quality mixture §5 wants).
- **Part 2 (reranker pure-Q gold): DO IT — it's the concrete deliverable.** Labelling is easier/
  cheaper (situation-only, no transcript), and the payoff is tangible: a **small local cross-encoder
  that reliably replaces an LLM reranker** (cost/latency win) *plus* a showcase of a **principled,
  statistically-supported labelling process** (pre-registered acceptance, staged human anchor, bias
  gate). **Honest framing:** the value is the *deployable artifact + methodology*, NOT a big reranker
  accuracy gain — the gate already showed v4 is ~adequate. Don't oversell the quality delta.
  **UPDATE (2026-06-01):** the LEVEL-gated commit is dropped — go **straight to the full ~130-case
  pure-Q gold + retrain** (see §5). A diagnostic gate can only say "don't bother," which can't change
  a decision driven by the artifact; the "does a CE train & beat baseline" risk is already retired by
  v4. Headroom is answered *empirically* by scoring old-v4 vs new model on a clean ~40-case test —
  which needs **~22 newly generated cases** (clean held-out v4 never saw) on top of relabelling the
  108 existing. flash-lite triage is kept only as an optional labelling *speed-up*, not a gate.
- **Summary-quality claim (scoped):** the situation summary is **functional** — conforms to prompt,
  passes LLM-judge + a manual spot-check of ~5–10 summaries. **Optimality / summarizer-comparison is
  future work** (the full Part 1 gold). Never let a single LLM judge carry a comparative claim.
- **Costs:** 3rd judge (DeepSeek) ≈ **$3–5 total** out of pocket; GPT/Claude via API ≈ tens of $;
  the binding cost is **human anchor time**, staged (pilot ~50, expand only if it doesn't clear).
  *(Chat subscriptions ≠ API — automate the panel via API; reserve manual time for the anchor.)*
- **Meta:** retrieval/labelling depth is **capped here.** Next effort rebalances to the agentic core +
  a **downstream game-outcome metric** ([[project-episodic-memory-remaining-work]]) — the signal that
  would actually tell us whether any of this retrieval quality moves agent performance.

## 0. The conceptual key — two ground truths, OPPOSITE blinding (do not mash them up again)

The reranker and the summary-recall eval ask different questions with different anchors:

| | **Reranker eval** | **Summary-recall eval** |
|---|---|---|
| Question | given the situation query (good or bad), can it retrieve the memories relevant **to that written query**? | does the summary surface the memories useful **for the context**? |
| Anchor | the **query Q** | the **context C** |
| Label = | relevance(M \| Q) — **pure-Q** | usefulness(M \| C) — **pure-C** |
| Labeler sees | Q + M, **context-blind** | C + M, **summary-blind** |
| Why blind | the reranker only ever sees Q (no context); rewarding memories Q can't point to is an unreachable target | you're *evaluating* Q, so Q in the label = circular |

The blindings are **mutually exclusive**, so one labeling pass cannot serve both. What we have:
`auto-panel query-only` = pure-Q but weak/over-crediting; `ChatGPT+Sonnet manual` = Q **+** C
(strong but a mash-up). **Neither clean gold exists yet** — that's what Part 1/2 build.

## 1. Scope decisions

- **Memory-extraction quality (the 3rd connected component) is scoped OUT** — judging whether an
  extraction is good needs reading whole game scripts (not feasible). Trust the existing per-role
  extraction pipeline.
- **The gold is conditional on the current `v4_deduped_v2` DB** (which has mixed memory quality
  from single-pass extraction + weak-model dedup rewrites). This is fine and needs **no cleanup
  first**: junk memories self-exclude (judged 0), near-duplicates surface in the precision/
  efficiency metric, and only *missing* useful memories are invisible — that's the scoped-out
  extraction axis. Document the conditionality.

## 2. Model roster (decided)

**Bias principle:** diversity *a priori* (different vendor/lineage = decorrelated bias) +
correction *post-hoc* (the human anchor measures each judge's skew; you can't pick "opposite-
biased" models up front). Never let a summary-writer also judge (it would favor memories its own
summary retrieved). Keep Gemini on the writer side only.

**Writers — 4 (the conditions under test in Part 1):**

| writer | role | input $/M | output $/M | speed | notes |
|---|---|---|---|---|---|
| `gemini-3.1-flash-lite` | production baseline (bar) | 0.25 | 1.50 | ~381 tok/s | what we run now |
| Gemini 2.5/3 Pro | quality ceiling (reference) | high | high | — | not a prod candidate |
| `meta/llama-4-maverick-17b-128e-instruct` | open candidate | 0.15 | 0.60 | MoE ~17B active | cheaper than 3.1 FL on both |
| `qwen/qwen3-next-80b-a3b-instruct` | open candidate | 0.09 | 1.10 | MoE ~3B active | cheapest input; free tier on OpenRouter |

Dropped mistral-small / nim-8b as writers (too small for full-context summarization — distinct
from their failure as *judges*). Against **3.1** flash-lite both open models **undercut on cost**;
speed is the open production question (see §3).

**Open ceiling gap (raised this session — flagged OPEN).** The two open writers above are both
*lightweight* (chosen as cheap flash-lite-3.1 *replacements*), so neither is a quality ceiling.
The roster's ceiling is **Gemini Pro — which is not open.** Whether we *also* need a **heavyweight
open** writer (NIM-hosted: Llama-3.1-405B / Nemotron-class / Qwen2.5-72B — **not** DeepSeek, it is a
judge) depends on the production goal: *cheapest-good-enough, any vendor* → no open ceiling needed
(Gemini Pro as reference bar + 2 cheap open candidates vs flash-lite suffices); *open-only stack* →
add one heavyweight open writer, else we never test whether open reaches Pro-tier summary quality.
A 405B-class open writer would also decorrelate the union pool (see §4). **Goal not yet pinned.**

**Judges — 3 LLM + human (the measurement instrument):**

| judge | lineage | role |
|---|---|---|
| ChatGPT | OpenAI | strong judge |
| Claude Sonnet | Anthropic | strong judge |
| `deepseek-ai/deepseek-v4-pro` | DeepSeek | 3rd diverse judge (NOT a writer). **Viability caveat:** via NIM it may hit free-tier limits; DeepSeek's own API is out-of-pocket but cheap (~$1–3 at this volume). **Optional** — see the GPT+Claude-only fallback in §5. |
| **Human (~150 items)** | — | calibrator/anchor — measures & corrects each judge's skew |

3 judges → majority + "all agree" high-confidence + disagreement-routing — but with **soft labels**
an even **2-judge panel (GPT + Claude) is fine** (no tiebreak needed, you average). **LLM judge cost
(corrected):** with premium judges + CoT it is **low tens of dollars per gold**, not $1–2 (that
figure assumed cheap judges); DeepSeek direct adds ~$1–3; a flash-lite-CoT pass is near-free. Still
negligible beside the human anchor, which is the only bounded human cost.

## 3. Infra & speed

- **Open writers run via NVIDIA NIM** (existing `nim/` wrapper — no new infra). The only pre-step is
  a **responsiveness smoke test** for the chosen NIM model(s) — *not* a production gate, just a "does
  it respond at full-context length" check. **OpenRouter is dropped** for now: it was production
  plumbing, and the cost-feasibility question it was meant to answer is **already settled by the §2
  price table** (both open candidates undercut flash-lite 3.1). Revisit only at the production-
  replacement step.
- **Speed is NOT a pre-gate.** For the experiment it's batch (parallelize). For production it's a
  third axis (quality × cost × speed) and is **provider-dependent** (low-active-param MoE on
  Groq/Cerebras can match/beat flash-lite; on commodity GPU it won't). For summarization (short
  output, big input) latency is dominated by prefill/TTFT. **Measure per-summary latency during
  Part 1** (free) and apply the speed gate only at the production-decision step — weighted by
  whether the game loop is batch sim (latency secondary) or live (per-turn latency the player
  feels).

## 4. Part 1 — Context validation + summary recall (PRIORITY; the original goal)

Builds the **pure-C usefulness gold** and answers "which summarizer best surfaces the
context-useful memories" + "can an open model replace flash-lite."

1. Each of the 4 writers generates situation summaries for each case.
2. Retrieve **top-10** per writer; **UNION** the retrievals → the candidate pool (union fixes the
   pool-coverage bias: a single-model pool makes that model the ceiling by construction).
3. **Label pure-C:** the 3-judge panel sees **context + candidate, summary hidden**, CoT,
   rubric-driven, **soft labels** (mean of judges; no tiebreaker — the Opus tiebreak itself leaned
   generous, 68% over-credit). Validate against the human anchor (§6).
4. **Metrics per writer:** recall@5 and recall@10 of the gold useful-set (decouple pool depth from
   metric K), **plus precision/efficiency** of the retrieved set (the metric the drift finding said
   matters — topical false positives, not just misses).
5. **Scale:** start 40–50 stratified cases (role × phase); expand if signal is promising.

**Pool-coverage bound (decided — NO separate completeness-critic).** A memory that exists in the DB
but *no* writer surfaces is invisible to the eval and silently counts as missing. We do **not** add a
"what memories *should* be useful" critic: it can't help when the memory may not be in the DB at all
(that's the scoped-out extraction axis), and the grounded version of it — a decorrelated retrieval
against the real DB — is just "broaden the pool," which we already get from vendor-diverse writers.
So instead: **maximize pool coverage via vendor-diverse writers** (Gemini + open; a heavyweight open
writer per §2 decorrelates further) and **document the residual bound honestly** — recall numbers are
*relative to the union pool*, and anything no candidate retrieved is out of scope (= the retrieval/
extraction ceiling). Relative writer comparison is unaffected: the blind spot is symmetric across writers.

Outputs: the pure-C gold (also feeds **strategy adoption** later), a ranking of summarizers, and
the open-vs-flash-lite production signal (quality from recall, cost from §2, latency from §3).

## 5. Part 2 — Reranker pure-Q gold (DECIDED 2026-06-01: full gold + retrain, NO diagnostic gates)

**Decision (supersedes the earlier optional / LEVEL-gated framing).** Build the full pure-Q gold and
**retrain from scratch** — skip the Level-1/Level-2 *gates*. Rationale: the deliverable is the
**artifact** (a deployable local cross-encoder trained on clean labels + a showcase of a principled,
statistically-supported labelling process), **not** a go/no-go on whether to optimize. A diagnostic
gate can only ever return *"don't bother — v4 is near the ceiling"* — which **cannot change** a
decision driven by the artifact's portfolio value. And the one genuinely risky question ("does a
cross-encoder even train and beat the bi-encoder on this data?") is **already retired by v4**
(NDCG@5 0.882). So the gates would spend effort — on numbers we've already learned not to fully trust
(the n=13→n=25 flip) — to answer a question we are no longer asking.

**Headroom is answered empirically, as a byproduct — not pre-measured.** After retraining, score
**both old v4 and the new model on the same clean held-out test.** *That* is the "is v4 leaving points
on the table" answer, obtained by running the real experiment instead of a proxy: new ≈ old ⇒ v4 was
already at the label-noise ceiling (a complete, shippable result); new > old ⇒ real recoverable
points. Strictly more trustworthy than any pre-gate, because it is the actual thing, not a stand-in.

**Steps:**
1. Build the pure-Q gold on **~130 cases** (inventory below), labelled per the §6 protocol (LLM panel
   at scale + bounded human anchor).
2. Re-split (train/val/test), retrain the CE on Modal with v4's recipe.
3. Score **old v4 and new model on the clean held-out test** → headroom answer + the deployable artifact.
4. **Honest framing:** the expected result may be *"≈ no gain."* That is still a strong portfolio
   piece — a deployable local reranker + a statistically-supported labelling method. **Do not oversell
   a delta** the gate already suggested is small.

**Case inventory — do we need to generate new cases? Partly (~22), for one specific reason:**

| bucket | count | generate? | label? |
|---|---|---|---|
| existing cases (query + top-10 pool on `v4_deduped_v2`) | 108 | **No — reuse the pools** | **Yes — all need fresh pure-Q labels** (existing labels are the context-contaminated mash-up, unusable) |
| new cases (fresh game states v4 never saw) | ~22 | **Yes — run through the existing summary→retrieve pipeline** | Yes — fresh pure-Q labels |
| **total** | **~130** | ~22 new | all 130 relabelled |

The **only** reason to generate the ~22 is a **clean held-out test of ~40 that v4 never saw.** v4's
pristine held-out is just **17** (val was used for model selection), and 17 cases cannot reliably
detect a 0.05 NDCG difference (per-case SD ≈ 0.12 → ~40 needed) — scoring old-vs-new on 17 would just
repeat the underpower trap the gate already taught us. `~17 pristine + ~23 new ≈ 40` clean test = a
trustworthy headroom number. Generation is **pipeline work** (run ~23 game states through
summary→retrieve to emit query+candidate pools), cheap, **no human time until labelling**. The other
~108 just need relabelling — their candidate pools already exist.

**Who labels what (the scale worry, resolved).** The **LLM panel** labels all ~130 cases (~1,300
pairs) — cheap, automated, API. **Human** effort is bounded and does **NOT** scale with the corpus:
~150 anchor *judgments* (validate the panel, §6) + ≤100 routed hard cases ≈ **~250 human
pair-judgments total**, not 1,300. Pure-Q pairs are short (query + one candidate, context-blind).

**Labelling details:**
- Reuse Part 1's summaries as queries, sampled as a **realistic MIXTURE of qualities** (production
  won't call the priciest summarizer 100+×/game), not just the pro summary.
- **Pure-Q:** judges see **query + candidate, context-blind**; SP = situation-only, OBS =
  situation+content (match the reranker's input). Easier/cheaper than Part 1 — no transcript to read.
- Existing strong labels are context-contaminated for this and **can't be reused as-is.**
- **Judges:** **GPT + Claude alone is a defensible 2-judge panel for Part 2** (cross-vendor
  decorrelation — the same pair that set the 80.5% ceiling; soft labels → no tiebreak needed).
  DeepSeek is an optional 3rd vendor (~$1–3 if its NIM free tier is unreliable and you pay direct).
- **flash-lite triage (optional, SPEED only — NOT a gate):** pre-label all pairs; auto-accept where
  flash-lite + both strong judges agree; route only the splits to a human. Cuts human effort to the
  contested minority. Not trusted as a verdict — every routed pair is human-verified, so the
  "can't trust flash-lite" concern doesn't bite (it only ever skips the unanimous-obvious pairs).

## 6. The labeling protocol (applies to each gold)

0. **Rubric first** (highest ROI): 0/1/2 definitions, the input each type is judged on, **6–8
   worked edge cases** (phase mismatch, topical-but-useless, partial). Identical rubric for humans
   and all LLM judges.
1. **Stratified human anchor (~150 *judgments*, NOT 150 cases)** — each judgment = one human label on
   one candidate memory; a single case supplies ~17–25 candidates, so ~150 judgments come from only
   ~20–40 cases. **You already have 108 cases → no case generation is needed for the anchor.** Split
   **calibration / validation** (fit any bias correction on one half, test on the other). Stratify by
   memory-type × agreement-pattern × role, oversampling the **confident-agreement** zone (where
   correlated over-crediting hides). **Spread, don't cluster:** judgments within one case are
   correlated, so draw a few candidates from many cases rather than exhausting a handful — sourcing
   all ~150 from ~5 cases collapses the *effective* sample (design effect) and your real CI ends up
   far wider than ±8%. (Reading-efficiency — read each scene once — pulls the other way; the
   compromise is a handful of candidates per case across ~20–40 cases.) If a 2nd human is available,
   dual-label ~30 for inter-annotator agreement (κ).
2. **Vendor-diverse panel at scale**, CoT, same rubric.
3. **Calibrate panel→human + pre-registered acceptance test**, e.g.: accept panel as gold if
   panel-vs-human binary agreement ≥ 80%, 95% CI lower bound ≥ 75%, and no significant directional
   bias (sign test). This is the "reasonable confidence level." **Why 80%, and how firm it is:** 80%
   is the *measured* reproducibility ceiling of the task — but from **one strong-model pair**
   (ChatGPT vs Sonnet, 400 items, **binary** cut; exact 0/1/2 agreement is only 64.5%), both anchored
   on the same pro summary (may inflate it), with ±~4% sampling error. It is a **provisional
   strong-model proxy — NOT a measured human-human ceiling or a hard law.** The dual-human κ (item 1)
   is what upgrades it: if human κ comes back higher, raise the bar; if lower, 80% is already
   generous. Don't deify it. (We can't demand >80% because that asks the panel to agree with one
   human more than two strong judges agree with each other; the ≥75% lower-bound floor is the 5-pt
   buffer that keeps the test achievable at the ceiling.)
4. **Route only hard cases to humans** (panel disagreement / low confidence); cap it (~≤100).
5. **Final gold** = calibrated panel where confident (soft when the panel splits) + human label on
   routed items. Report coverage, panel-vs-human agreement + CI, κ, per-judge skew, % human-routed.

**How many human judgments for what confidence (the real commit-vs-defer decision).** The anchor
validates *panel-vs-human agreement* — a single proportion at p≈0.8. **Unit = one human judgment on
one candidate memory, NOT a case.** Like a political poll, the sample size is set by the *precision
you want*, not by the population: a ±3% national poll uses ~1,000 people whether the electorate is
10M or 300M. Same here — this cost is **FIXED; it does NOT scale with the number of cases or LLM
labels in the corpus:**

| target 95% CI half-width | human judgments (validate raw panel) | if split 50/50 for bias-correction |
|---|---|---|
| ±10% | ~62 | ~124 |
| ±8% (the §6 default) | ~96 | ~190 |
| ±5% | ~246 | ~490 |

**~100 human judgments** buys the defensible claim "panel agrees with human 80±8%, no significant
bias" → panel accepted as gold. That ~100 is the threshold between *validated gold* and *designed/
future-work*; below ~60 it's a pilot. Routed hard-case adjudication (~≤100) is separate and cappable.
**Don't conflate two sample sizes:** this **~96 is *judgments*** validating the labeling instrument;
the **~40 in §5 is *cases*** giving NDCG-power for the reranker verdict. Different units, different
questions.

(*"Validate raw panel" vs "bias-correction split":* the left column **only measures** the panel's
agreement and ships the panel labels as-is — all N humans go into one agreement estimate. The right
column additionally **fits a correction** to the panel's skew, so it must split the humans into a
calibration half (fit the correction) and a held-out validation half (test it honestly) — hence ~2×
the labels. Use raw-validate if the panel passes the acceptance test clean; only fit a correction if
the panel shows a measurable, consistent skew worth removing.)

### Deciding whether to correct, and when to trust model agreement (staged, pre-registered)

**Don't pre-commit to 96/190 humans. Stage it and let a principled test stop you early.**

1. **Pre-register δ** — the smallest directional skew you'd bother correcting (e.g. ±5 percentage
   points of items). This is what makes "no correction needed" an honest claim rather than a
   p-hacked null.
2. **Pilot ~40–50 stratified human labels**, oversampling the **all-models-agree zone** (see the
   unanimity logic below).
3. **Test for skew on the pilot — two tests, not one:**
   - **McNemar / sign test** on the discordant (panel≠human) pairs → tests *presence* of directional
     bias. Significant + lopsided → you need correction, found out for ~50 labels.
   - **Equivalence test (TOST) against ±δ** → tests *absence*. Failing to reject McNemar is **not**
     proof of no bias (that's the n=13 underpowered trap again); only a CI for the skew sitting
     **entirely inside [−δ, +δ]** licenses "negligible skew, raw-validate, no correction."
   - Stop early if the result is clearly negligible *or* clearly large; expand toward ~96 **only** in
     the ambiguous zone (small point estimate, CI still wider than δ). Honest sample sizes: certify
     negligibility within ±10pp ≈ 80 labels, within ±5pp ≈ a few hundred — but staging usually pays
     far less than the worst case.
4. **The same pilot also tests the accuracy threshold** (not just bias) — check whether the 95% lower
   bound on agreement already clears the 75% floor. **Optional-stopping discipline:** pre-register the
   looks (e.g. n≈50 then n≈100) and **stop early only in the unambiguous directions** (clearly clears
   / clearly fails); naive peek-and-continue inflates the error rate. Expected outcome: flash-lite-CoT
   *alone* already hit ~75–77% vs the strong judges, so a 2–3 vendor strong panel should land
   mid-to-high 80s → a ~50-label pilot may clear outright. Whether you save labels depends on the
   realized margin (unknown until you look): high accuracy → big early saving; borderline → expand to
   ~100–250 (no saving, no waste); failing → stop at ~50. **One pilot serves both gates.**

**Unanimity is suspect *a priori*, trusted only *after* the audit — not by assumption.**
The prior "unanimous tier = 0% leak" finding held because that unanimous set **included the two
careful strong judges** (the leak was the *majority* tier, where the generous auto-trio outvoted
them). That is "agreement that contains a careful judge," not "agreement is safe." For a panel whose
members may share a *correlated* bias (any all-frontier-LLM panel risks this), unanimous agreement is
exactly where a shared bias produces confident-but-wrong labels — agreement looks like reliability
but is shared blindness, and no intra-panel statistic reveals it; only the human can. So the sequence:
   1. **A priori the unanimous-agree tier is the SUSPECT zone** → oversample it in the pilot.
   2. **Run the skew/TOST test on that tier specifically** (powered to detect a δ-sized *tier* skew —
      a stratified, adequately-sized audit, **not** a token sample).
   3. **If skew ≤ δ → unanimity is now an *earned* reliable signal** → trust the agree-tier on the
      rest of the data and route remaining humans to disagreements only (the label saving).
   4. **If skew detected → unanimity is NOT safe for this panel** → correct, or keep human coverage on
      the agree-tier too.

**Where a 3rd model (DeepSeek > Grok on cost) helps — and where it does NOT.** It lowers ensemble
variance, decorrelates bias (more likely to land in the no-correction regime), and makes a *3-vendor
unanimous* a stronger agree-signal for routing. It does **NOT** lower the human floor for establishing
validity: the human is an *external, different-class* instrument and the LLM judges share correlated
bias (the 5-model vote did **not** dilute the over-crediting — only strong/human judges caught it).
More correlated-LLM votes cannot substitute for the anchor. The 3rd model's real "fewer humans" win is
*concentration* via routing, not a lower validity floor.

Human cost ≈ one focused day (1–2h rubric + ~2–3h for the 150 anchor, grouped by game state so each
scene is read once + ~1–2h routed adjudication). **Integrity:** actually run the anchor, or mark it
honestly as designed/piloted — never claim a validation that wasn't done.

## 7. Status: decided vs open (updated 2026-05-31, this session)

- **Decided:** the two-gold decomposition; Part 1 = priority, Part 2 = optional/leveled; extraction
  scoped out; soft labels; speed not pre-gated; **open writers via NIM (OpenRouter dropped)**; **no
  completeness-critic — pool-coverage bound documented instead** (§4); **GPT+Claude is an acceptable
  2-judge panel, DeepSeek optional** (§2/§5); the human-anchor confidence table + **staged
  pre-registered-δ correction gate (McNemar + TOST) and the certify-then-trust unanimity rule** (§6);
  the Part 2 level ladder with the n=40 / ~130-case math (§5).
- **Reranker net decision (from the gate):** keep v4; relabel is small-upside, downstream-gated,
  low-priority — not blocking. **Recommended path: Level 1 (cheap pure-Q confirm) → decide.**
- **Open / pin next:** (1) **production goal — open-only stack vs cheapest-good-enough** — decides
  whether a heavyweight open writer joins the roster (§2); (2) exact Part 1 case count (40–50?) and
  Qwen variant; (3) NIM responsiveness smoke test for the chosen open writer(s); then generate Part 1
  summaries.

## 8. Artifacts map (where everything is)

- **Diagnostic scripts:** `scripts/context_drift_diagnostic.py`, `flashlite_self_summary_judge.py`,
  `reeval_v4_clean_obs.py`, `reeval_v4_clean_sp.py`, `reeval_v4_power.py`.
- **Adapter:** `evaluation/labeling/adapters/context_relevance.py` (ContextRerankerAdapter —
  injects game state into the reranker prompt; `render_game_state`).
- **This session's label outputs:** `labels/context_labels.json`, `drift_report.json`,
  `cot_labels.json`, `cot_report.json`, `reeval_v4_clean_{obs,sp}.json`.
- **Source labels (per-judge scores in `labeling.scores`):**
  `evidence/fine_tuning/cross_encoder/reranker/labels/round2_expanded/expanded_merged_labels.json`;
  candidates `expanded_candidates_for_labeling.json`; pro summaries `expanded_golden_situations.json`.
- **Eval dataset:** `eval_sets/v4_reranker_expanded.jsonl` (109 cases; case_index aligns 1:1).
- **Reranker split/data:** `evidence/fine_tuning/cross_encoder/reranker/training_data/`
  (`reranker_split.json`, `reranker_{train,val,test}.jsonl`); model `models/cross_encoder/reranker_v4`.
- **Reranker log (cross-referenced):** `evidence/fine_tuning/cross_encoder/reranker/experiment_log.md`.
