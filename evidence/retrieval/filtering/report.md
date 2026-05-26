# Retrieval Pipeline: From Raw Similarity Search to Useful Memory

## The Problem

The agent's memory system stores two types of knowledge extracted from past games: **observations** (specific game moments with outcomes) and **strategy points** (generalised if-then rules for recurring situations). At decision time, the agent generates a situation summary and retrieves the most semantically similar items from each store.

The naive approach — fetch the top-k items by embedding similarity — broke down quickly. In one case, the retrieval layer returned 12 observations for a single investigator scenario. Many of them taught the same strategic lesson ("acting on weak reads causes mislynches") through different anecdotes. Feeding all of them into the prompt didn't make the agent smarter; it consumed context, diluted the genuinely distinct guidance, and made it harder for the agent to identify what actually mattered.

The core issue wasn't relevance — most items were topically related. It was **redundancy**. The embedding space clusters similar game situations tightly together, so a similarity-ranked list naturally surfaces variations on the same theme rather than a diverse set of strategic perspectives.

## The Solution

The pipeline needed to do three things: remove near-duplicates, promote diversity, and control total volume. I implemented each as a separate layer, choosing different mechanisms for observations and strategy points based on what each content type actually needed.

```
Retrieve (wide, 10/situation) -> Dedup Gate -> MMR -> [Rerank] -> Cap -> Prompt
```

**Observations get cosine dedup.** These are case studies — narrative accounts of what happened and what it meant. The redundancy pattern is "same lesson, different game." Two observations where a healer stayed quiet and survived teach the same thing regardless of the specific players involved. For these, I compute pairwise cosine similarities between the candidate embeddings and greedily remove any item that exceeds a threshold against an already-selected item.

**Strategy points get Maximal Marginal Relevance (MMR).** These are prescriptive rules, and the failure mode is different. Strategy points rarely duplicate each other verbatim, but they can cluster around the same game phase or decision type. MMR balances relevance to the query against diversity from already-selected items:

$$\text{MMR} = \arg\max_{d_i \in R \setminus S} \left[ \lambda \cdot \text{Sim}(d_i, q) - (1 - \lambda) \cdot \max_{d_j \in S} \text{Sim}(d_i, d_j) \right]$$

where λ controls the tradeoff. A higher λ prioritises relevance; a lower λ prioritises diversity. Strategy points benefit from active diversity optimisation because the agent needs coverage across different contingencies (what to do if targeted, what to do if the consensus is wrong, what to do if information is scarce), not just the most similar advice.

**A hard cap (3 per situation) provides a deterministic bound.** After dedup or MMR selection, I truncate to at most 3 items per situation summary. With typically 2 situations per turn, this means 6 items maximum reach the prompt — enough for diverse guidance without context bloat. This cap runs unconditionally as the final step before prompt injection, regardless of which earlier pipeline stages are enabled.

**Reranking is available but parked.** The pipeline includes an LLM reranker that can re-score items by relevance to the situation. It's built, tested, and toggled off by default via a per-role config. I chose not to activate it because the bi-encoder ordering proved sufficient at this volume (5-6 items) — the top items by embedding score were consistently the right ones. It remains available as a toggle if specific roles later show poor bi-encoder ranking.

## The Iteration

### Threshold tuning

The dedup threshold was the first parameter to tune, and the initial value was badly wrong.

At **0.85**, the threshold was too aggressive. Observations that taught *opposing* lessons — one where a healer stayed quiet and survived, another where a healer engaged actively and was killed — were being treated as duplicates because they shared vocabulary (healer, save, discussion, wolves, targeted). Average observations retrieved dropped from 4.9 (baseline) to 1.6. The agent was left with a single data point where it needed a contrastive pair.

At **0.92**, the threshold retained these valuable opposing examples while still catching true duplicates — items that differed only in player numbers or minor phrasing. This recovered volume without reintroducing redundancy.

### MMR lambda

For strategy points, I tested λ = 0.8 (relevance-heavy) against lower values. At 0.8, the retrieval maintained high relevance (mean 3.0–4.0) while keeping redundancy low (efficiency scores of 2–3). Lower lambda values pushed too hard on diversity and surfaced strategies for irrelevant game phases. The 0.8 setting reflected the reality that for prescriptive advice, being *about the right situation* matters more than covering every possible contingency.

### Building the evaluation

Evaluating retrieval quality required its own design iteration. The evaluation used frozen EvalCase records from captured game traces, replayed against an exported memory snapshot (522 items from v4 observations and strategy points). The same 5 cases were held constant across all 4 runs — retrieval is deterministic (same store, same queries, same top_k), so any score differences between runs reflect only the changed pipeline parameter or judge model.

I built an LLM judge that scored retrieved sets on relevance, redundancy, and unique idea count — and immediately hit a problem.

The first judge model (**Gemini Flash-Lite**) failed to discriminate. Scores clustered around 3–4 regardless of retrieval quality, and roughly 30% of evaluations produced malformed output — the model returned 3-item `redundant_pairs` where the schema allowed a maximum of 2, causing validation failures. Switching to **Gemini 2.5 Flash** eliminated the formatting failures entirely (0% failure rate across all subsequent runs) and produced scores that tracked meaningfully with retrieval changes. The cost difference between the two models is negligible for evaluation workloads.

The judge **prompt** needed its own fix. The initial version asked for separate redundancy and unique idea counts, but these were defined against different standards. Redundancy used a behavioural test ("would the player act differently?"), while unique ideas counted distinct anecdotes. This produced contradictory scores — one case scored redundancy=5 (maximum duplication) and unique_ideas=5 (maximum novelty) simultaneously.

I restructured the prompt around an explicit **clustering step**: before scoring, the judge groups items by the strategic lesson they teach, then derives all metrics from those clusters. This made the outputs internally consistent and more diagnostic — I could now see exactly which lessons were over-represented and which were missing.

I also flipped the redundancy scale to **efficiency** (higher = better), so all metrics pointed the same direction. A small change, but it eliminated the mental gymnastics of reading a dashboard where "high" meant "good" for relevance but "bad" for redundancy.

## Results

Final configuration: cosine dedup at 0.92 for observations, MMR with λ=0.8 for strategy points, 3-per-situation cap, evaluated with Gemini 2.5 Flash using the cluster-based judge prompt.

### Observations (n=5 scenarios)

| Metric | Mean | Median | Range |
|---|---|---|---|
| Avg items retrieved | 5.0 | 5 | 3–6 |
| Relevance | 4.20 | 4 | 3–5 |
| Efficiency | 3.40 | 3 | 2–5 |
| Unique Lessons | 2.80 | 3 | 1–5 |

### Strategy Points (n=5 scenarios)

| Metric | Mean | Median | Range |
|---|---|---|---|
| Avg items retrieved | 4.0 | 5 | 2–5 |
| Relevance | 3.00 | 4 | 1–4 |
| Efficiency | 2.00 | 2 | 1–3 |
| Unique Lessons | 1.20 | 1 | 0–3 |

The strongest case was the investigator/day_vote scenario, where 5 observations scored relevance=5, efficiency=5, and unique_lessons=5 — every item taught a distinct, actionable lesson for the agent's specific situation. The weakest was healer/day_vote, where the retrieval surfaced endgame consensus strategies for an early-game information-starved situation, scoring relevance=1 and unique_lessons=0.

## What I Learned

**The biggest insight was where the real bottleneck sits.** After four rounds of pipeline tuning, the limiting factor wasn't retrieval sophistication — it was memory content coverage. The strategy point store simply didn't contain entries for certain common situations (a revealed healer managing wolf targeting, an early-game vote with no evidence). The judge's unique_lessons=0 scores pointed directly at these gaps. No amount of dedup or MMR tuning can surface knowledge that doesn't exist.

**Evaluation design is engineering, not overhead.** The judge prompt went through as many iterations as the pipeline itself. The shift from flat scoring to cluster-based evaluation didn't just produce better numbers — it changed what I could *see*. Per-cluster annotations showed me which lessons were over-retrieved and which situations had no coverage, turning an opaque quality score into a diagnostic tool.

**Different content types need different diversity mechanisms.** Observations and strategy points look similar from the outside (both are text, both are retrieved by embedding similarity), but their redundancy patterns differ. Observations cluster by narrative similarity and need duplicate removal. Strategy points cluster by situation type and need diversity optimisation. Using the same mechanism for both would have over-filtered one or under-filtered the other.

**Start conservative with thresholds.** 0.85 cosine similarity seemed reasonable in theory but was far too aggressive in practice. Items that look similar in embedding space can teach very different strategic lessons. The vocabulary overlap between "healer stayed quiet and survived" and "healer engaged actively and was killed" is high, but the lessons are opposite. 0.92 was the right default — tight enough to catch true duplicates, loose enough to preserve contrastive pairs.

## Artifacts

| File | Description |
|---|---|
| [01_baseline_threshold085_pro.md](01_baseline_threshold085_pro.md) | Run 1: 10 samples, 0.85 threshold, gemini-2.5-pro judge |
| [02_threshold092_flashlite.md](02_threshold092_flashlite.md) | Run 2: 5 samples, 0.92 threshold, flash-lite judge (30% validation failures) |
| [03_lambda08_flash_nocap.md](03_lambda08_flash_nocap.md) | Run 3: 5 samples, lambda 0.8, 2.5-flash judge, no cap (12-item outlier) |
| [04_final_cap3_cluster_prompt.md](04_final_cap3_cluster_prompt.md) | Run 4: 5 samples, final pipeline with cap and cluster-based judge |

## Code References

- `Agents/retrieval_filters.py` — dedup_gate, mmr_filter, cap_per_situation
- `Agents/memory.py:RETRIEVAL_KEEP_PER_SITUATION` — hard cap constant
- `Agents/agents.py:_enrich_payload_with_memory` — pipeline integration
- `evaluation/judges/prompts.py:RETRIEVAL_USER_PROMPT` — cluster-based judge prompt
- `evaluation/experiments/retrieval.py` — experiment runner
- `evaluation/core/report.py` — deterministic markdown report generator
