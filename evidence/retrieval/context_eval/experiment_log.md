# Context-Based Retrieval Evaluation

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

**Judges — 3 LLM + human (the measurement instrument):**

| judge | lineage | role |
|---|---|---|
| ChatGPT | OpenAI | strong judge |
| Claude Sonnet | Anthropic | strong judge |
| `deepseek-ai/deepseek-v4-pro` | DeepSeek | 3rd diverse judge (NOT a writer; different model from the open writers) |
| **Human (~150 items)** | — | calibrator/anchor — measures & corrects each judge's skew |

3 judges → majority + "all agree" high-confidence + disagreement-routing. Judge cost is
negligible (~$1–2 total at this volume); the human anchor is the only bounded human cost.

## 3. Infra & speed

- **Use OpenRouter for the open models** (sidesteps NIM's free-tier rate limits; it aggregates
  multiple providers per model, OpenAI-compatible). Add an `openrouter/` wrapper to
  `Agents/llm_factory.py` — same ~10-line pattern as the existing `nim/` wrapper (base_url
  `https://openrouter.ai/api/v1`, `OPENROUTER_API_KEY`). NIM stays available; OpenRouter is the
  reliable paid fallback. Qwen3-Next has a **$0 free tier** on OpenRouter for the experiment.
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

Outputs: the pure-C gold (also feeds **strategy adoption** later), a ranking of summarizers, and
the open-vs-flash-lite production signal (quality from recall, cost from §2, latency from §3).

## 5. Part 2 — Reranker pure-Q gold (OPTIONAL / lower priority)

The gate (Step 1a–c) showed the reranker is ~adequate (obs ~0.06–0.09 NDCG gap, SP flat), so this
is **low-priority** — do it only if that obs gap matters downstream.

- Reuse Part 1's summaries as queries, sampled as a **realistic MIXTURE of qualities** (production
  won't use the most expensive summarizer for a 100+/game call), not just the pro summary.
- **Label pure-Q:** judges see **query + candidate, context-blind**; SP = situation-only, OBS =
  situation+content (match the reranker's input). Easier/cheaper — no transcript to read.
- Then re-derive reranker train/test on pure-Q labels, retrain (Modal), compare old-vs-new **on the
  clean pure-Q test labels**. Note: existing strong labels are context-contaminated for this and
  can't be reused as-is.

## 6. The labeling protocol (applies to each gold)

0. **Rubric first** (highest ROI): 0/1/2 definitions, the input each type is judged on, **6–8
   worked edge cases** (phase mismatch, topical-but-useless, partial). Identical rubric for humans
   and all LLM judges.
1. **Stratified human anchor (~150)**, split **calibration / validation** (fit any bias correction
   on one half, test on the other). Stratify by memory-type × agreement-pattern × role,
   oversampling the **confident-agreement** zone (where correlated over-crediting hides). If a 2nd
   human is available, dual-label ~30 for inter-annotator agreement (κ).
2. **Vendor-diverse panel at scale**, CoT, same rubric.
3. **Calibrate panel→human + pre-registered acceptance test**, e.g.: accept panel as gold if
   panel-vs-human binary agreement ≥ 80%, 95% CI lower bound ≥ 75%, and no significant directional
   bias (sign test). This is the "reasonable confidence level."
4. **Route only hard cases to humans** (panel disagreement / low confidence); cap it (~≤100).
5. **Final gold** = calibrated panel where confident (soft when the panel splits) + human label on
   routed items. Report coverage, panel-vs-human agreement + CI, κ, per-judge skew, % human-routed.

Human cost ≈ one focused day (1–2h rubric + ~2–3h for the 150 anchor, grouped by game state so each
scene is read once + ~1–2h routed adjudication). **Integrity:** actually run the anchor, or mark it
honestly as designed/piloted — never claim a validation that wasn't done.

## 7. Status: decided vs open

- **Decided:** the two-gold decomposition; the roster (§2); OpenRouter infra; Part 1 = priority,
  Part 2 = optional; extraction scoped out; soft labels; human-anchor design; speed not pre-gated.
- **Reranker net decision (from the gate):** keep v4; the relabel is a small-upside, downstream-
  gated, low-priority option — not blocking.
- **Open / pin at the start of next session:** exact case count (40–50?), confirm the Qwen variant,
  **add the `openrouter/` wrapper + run two smoke tests** (an open writer on a full-context summary;
  DeepSeek on one judge prompt) to verify the roster responds, then generate Part 1 summaries.

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
