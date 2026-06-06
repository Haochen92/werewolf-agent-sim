# Feasibility analysis — caching + variance-reduction claims vs. current tracing

**Date:** 2026-06-06. **Status: ANALYSIS ONLY, no code changes.** Context: external advice proposed
five levers for the budget-constrained eval (Phase C win-rate A/B): (1) instrument implicit-cache
hit rate, (2) explicit caching for a guaranteed discount, (3) CUPED/regression adjustment,
(4) rich per-run telemetry, (5) bootstrap/Bayesian CIs instead of p-values. This note checks each
claim against the actual tracing/metrics stack on `feature-tracing`.

**Verification setup:** code reading (langchain-google-genai 4.2.2, langfuse 3.14.6 from the
lockfile venv) + one live Langfuse query over the **600 most recent generations** (all
`gemini-3.1-flash-lite`, Vertex backend).

---

## Claim 1 — "Instrument cache hits via usage metadata" → ALREADY DONE (zero work), and the data is damning

No implementation needed; the pipeline already records it end-to-end:

- `langchain-google-genai` maps the API's `cached_content_token_count` into
  `usage_metadata.input_token_details.cache_read` (site-packages `chat_models.py:1144-1159`).
- The Langfuse `CallbackHandler` (attached to every game via `Agents/tracing.py:76`) flattens that
  to `input_cache_read` in each generation's `usage_details` (`CallbackHandler.py:1211-1218`).

Live measurement (600 most recent generations):

| metric | value |
|---|---|
| generations with nonzero `input_cache_read` | **2 / 600** |
| input tokens served from cache | **7,956 / 1,895,364 (0.4%)** |
| avg input / call | 3,158 tok |
| output tokens (incl. reasoning) | 124,034 |

So the advice's framing ("your discount will wobble") is too generous for this workload: implicit
caching is effectively **not landing at all**. Plausible mechanism: the stable prefix is the
per-(role × node-type) system prompt at ~1.0–1.4k tokens (measured below), and calls from 9 agents
with different system prompts interleave, so no prefix stays hot. There is no hidden discount to
stabilize — current cost figures (~$0.3–0.4/game) are honest full-price numbers.

**Action implied: none.** If we ever want a per-game cache-hit metric, it's a Langfuse aggregation
query over data that already exists, not new instrumentation.

## Claim 2 — "Explicit caching for a reliable 90% discount" → NOT a fit for this prompt architecture

The plumbing side is real: `ChatGoogleGenerativeAI` natively supports `cached_content` (works on
Vertex via google-genai 1.75.0), and `llm_factory.create_chat_model` forwards kwargs, so wiring a
cache name through is a moderate, contained change.

The economics fail, though, on three measured facts:

1. **The shared prefix is too small.** The only block shared by *all* calls is `GAME_PREAMBLE`
   ≈ 630 tokens. The full stable prefix is per-(role × node-type): measured system prompts run
   ~960–1,400 tokens (e.g. `VILLAGER_DAY_DISCUSS` ≈ 1,306, `HEALER_DAY_VOTE` ≈ 964). The advice
   itself quotes a 2,048-token minimum — every candidate cache is **below the entry bar**.
2. **Cache fan-out.** Clearing the bar honestly would mean ~13+ separate caches (6 roles ×
   discuss/vote, 5 night prompts, wolf channel, summary, novelty judge), each paying storage
   per hour and needing TTL management across a batch.
3. **Savings ceiling is modest anyway.** Stable prefix ≈ 35–40% of the avg 3.2k input/call. Even at
   a granted 90% discount on all of it, that's roughly a quarter of LLM spend — ballpark **≤ $0.10
   of a ~$0.35 game**, before storage cost and before the min-token bar disqualifies most caches.

The one way to make it work — restructuring prompts so all roles share one large common prefix — is
**frozen**: main-pipeline prompts condition the Phase B gold labels
(`feedback-memory-pipeline-prompt-freeze`), and a request-structure change mid-series is a
generation-harness change (same comparability concern as the Vertex-vs-Google-AI backend finding).

**Verdict: skip.** Revisit post-v5-rebuild/labelling, and only if Phase C batch budgeting actually
hurts. Also note: the advice's numbers (90%, 2,048 min, 2.5-era pricing) are for **Gemini 2.5**; we
run `gemini-3.1-flash-lite` (`Agents/agents.py:97`) — minimums/discounts/storage rates would need
re-verification against current Vertex docs before any build decision.

## Claim 3 — "CUPED / regression adjustment" → trivially codeable, but the covariate doesn't exist

The claim is conditional — "if you have any per-scenario covariate that predicts the outcome" — and
the condition fails here:

- Every game is **structurally identical**: same 9-player cast, same role line-up, same config
  within an arm. There is no scenario difficulty, no varying agent count — nothing pre-treatment
  that differs between games.
- All between-game variance comes from temp=1.0 **sampling**, which is exactly the noise CUPED
  cannot touch (it's not predictable from anything observable before the game).
- Candidate covariates we *do* record (game length, vote counts, role exits) are **post-treatment**
  — adjusting on them would bias the memory-on/off comparison, not sharpen it.

Related correction to the advice's premise ("you've got pairing covered"): **true paired design
isn't actually available either.** The only seed in the system is `game_id` → scheduler
`cycle_seed` (`Agents/scheduler.py:9-15`), which pins speaking-order tie-breaks only — LLM sampling
is unseeded, so paired games diverge at the first sampled token. And even that pairing isn't
plumbed: `build_game_config` accepts `game_id` (`Agents/tracing.py:63`) but `run_game` doesn't
expose it (`Agents/main.py:32-40`), `run_batch` never passes it, and it isn't written to the batch
JSONL record (it lives only in Langfuse trace metadata). Threading it through is a ~5-line change,
worth doing for **replay/debugging provenance**, not for variance reduction.

**Verdict: not applicable in the current design.** Becomes relevant only if Phase C introduces real
scenario heterogeneity (e.g. varied castings or seeded memory-store variants) — then the scenario ID
is the covariate and CUPED is a few lines on top of the existing JSONL.

## Claim 4 — "Extract more signal per expensive run" → ALREADY IMPLEMENTED (this is v1)

This is a correct principle and is precisely what the existing stack does:

- Per-game accumulators: `DayResolutionMetric` / `NightResolutionMetric` capture every vote, tie,
  night target, save, investigation, and attributed death (`Agents/schemas/metrics.py`).
- ~20 base + derived per-game metrics computed in one pass (`Agents/compute_metrics.py`) and pushed
  as Langfuse scores at both trace and session level (`push_scores_to_langfuse`).
- Per-decision `EvalCase`s for night actions (the current `feature-tracing` work) add
  decision-level rows on top of game-level rows.

The v2 metrics design (`experiment_log.md` § "Why dense, de-lucked proxies — the variance
argument") already makes the same argument this advice makes: many measurements per $0.35 game →
tighter estimates per dollar. Remaining known gaps are tracked (pre-rerank pools, store snapshots,
run_batch night-decision dump). **Action implied: none beyond the existing plan.**

## Claim 5 — "Bootstrap/Bayesian CIs instead of p-values" → easy, analysis-side only, worth adopting

- `scipy 1.17` / `numpy` / `pandas` are already in the lockfile.
- `scripts/analyze_batch.py` currently computes **no inferential statistics at all**, so this is an
  add, not a replacement — no methodological debt to unwind.
- Inputs are ready: per-game metric rows in the batch JSONL (`computed_metrics` per record). A
  percentile bootstrap over any per-game metric is ~20 lines; a beta-binomial posterior for win
  rate is less.

**Verdict: adopt at Phase C analysis time.** It composes directly with the v2 proxy-basket plan
(de-lucked proxies + monotonicity check) and costs zero extra runs.

## Follow-up 1 — is the ~0% hit rate a prompt-design issue or inherent dynamism?

**Mostly layout, not dynamism.** Measured block sizes (day-discuss prompts):

| block | size | role-agnostic? |
|---|---|---|
| GAME_PREAMBLE | ~630 tok | yes |
| ROLE_CORE_STRATEGY + identity (`You are {player_id}`) | ~210–310 tok | **no — sits at position ~630** |
| TONE_INSTRUCTION + RESPONSE_FORMAT | ~330 tok | yes |
| DISCUSSION_SILENCE_RULE | ~226 tok | yes, but placed at the *bottom of the human message* |

~80% of the system prompt (~1.2k tok) is identical across all 9 agents, but the role-specific block
is sandwiched at token ~630, so the cross-agent common prefix dies **just below the ~1k implicit-cache
minimum**. Likewise `{firing_brief}` (per-turn) is the first line of the human message, ahead of
within-day-stable content (surviving players, day summaries) and the append-only day channel — killing
same-agent within-day prefix continuation. Both divergence points are placement choices.

An information-preserving reorder (role block to the end of the system prompt; firing_brief below the
channel; silence rule hoisted to system) would make ~1.2k tok of contiguous common prefix —
**~40% of the avg 3.2k input/call becomes cache-eligible**, with good temporal locality already in
place (sequential discussion fires same-node-type calls back-to-back). A deeper context-first /
identity-last restructure could push eligibility to ~75%, but that is a real behavioral change.

The unavoidable residue: per-call retrieved memory, the firing brief, and per-call channel-snapshot
length — ~50–60% of input is genuine dynamism. And implicit grants remain opportunistic even with a
perfect layout.

**Why not now:** a reorder is not provably output-neutral (LLMs are order-sensitive; proving
neutrality costs an A/B worth more than the ~$0.05–0.08/game it protects), and the prompt freeze
applies regardless — these prompts condition Phase B gold labels. **Disposition: quantified design
debt; fold the cache-friendly reorder into the v5 rebuild moment, when prompts are touched and
re-frozen anyway.**

## Follow-up 2 — caches are model-specific (confirmed; no workaround exists)

What's cached is the **KV state** — per-layer attention key/value tensors computed by running the
prefix through the model. Those tensors are outputs of the specific model's weights, so they are
meaningless to any other weights: same prompt + different model (even a different version of the
same family) = zero hit, recomputed from scratch. This is why the explicit-cache API binds a model
name at creation — it's the nature of the artifact, not a relaxable policy (Anthropic's prompt
caching is model-specific for the same reason). It's stricter still: serving-stack changes to the
*same* model (re-quantization, infra updates) can invalidate cached state — part of why implicit
hits are best-effort even with a perfect prefix layout. Scoping: explicit caches live in the
project (+ region on Vertex); implicit caching matches only against your own recent requests —
no cross-tenant sharing (a cross-customer hit would leak that someone else sent that prefix).

**Eval implication — neutral-to-positive for us:**
- "Each model warms its own cache" only matters if you *count on* cache savings across
  model-comparison arms. We don't (implicit ≈ 0%, explicit rejected above).
- Model-specificity actually *protects* comparison fairness: caching can never create a cost or
  latency asymmetry between model arms (judge swaps, NIM/Mistral arms) — every arm pays full
  price uniformly, matching the honest full-price accounting we're already in.
- Becomes a real planning input only post-v5-rebuild **if** the cache-friendly layout lands **and**
  we run multi-model comparisons: per-arm cost then differs by per-model hit rate, not just
  pricing — carry the per-generation `input_cache_read` field into any cross-model cost report.

## Summary table

| # | Claim | Verdict | Work |
|---|---|---|---|
| 1 | Instrument implicit-cache hits | **Already done**; measured hit rate ≈ 0 (2/600, 0.4% of input) | none |
| 2 | Explicit caching, 90% off | **Doesn't clear break-even**: prefixes 0.6–1.4k tok < 2,048 min; ~13 caches; ceiling ≲ $0.10/game; prompt restructure frozen | skip |
| 3 | CUPED adjustment | **No valid covariate exists** (identical scenarios, sampling-only variance); pairing itself is weaker than assumed (seed pins scheduler only, and isn't plumbed) | n/a (revisit if Phase C varies scenarios) |
| 4 | Rich per-run telemetry | **Already implemented** (v1 metrics + EvalCases + Langfuse scores) | none beyond tracked gaps |
| 5 | Bootstrap/Bayesian CIs | **Easy and worthwhile**; deps present, analysis-side, zero extra runs | ~20 lines at Phase C analysis |

Net: of the five levers, four are either already built or inapplicable to this design; the one
genuine adoption is the cheapest (CIs). The most useful *new fact* produced by checking the claims
is empirical: **implicit caching contributes ~0% today**, so all cost planning should assume
full-price input tokens.
