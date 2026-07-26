# RL × Memory System — selection-scorer ("contextual bandit") exploration

**Status: PARKED — paper design only (2026-06-12), post-ship / learning-project tier.** Nothing here
is on the critical path (Phase B → freeze gate → frontend, per `evidence/execution_plan/phase_b_plan_review.md`).
Logged so the design survives until/if we come back to it.

## Thesis fit (why this hybrid and not "add RL")

Project thesis: episodic memory = cheap, rule-change-robust learning from experience, vs classic RL
which retrains on every rule change / model swap. The only hybrid that *preserves* the thesis keeps
the knowledge in the store and learns a small policy at the seams — when the game changes, the store
is re-extracted (cheap, done twice already: 9-role expansion, net-horizon rewrite) and only a tiny
model retrains.

## REJECTED: Xu et al.-style decision-layer self-play RL (frozen LLM proposes, policy picks)

- **Generation wall.** Policy training is cheap; the *simulator* is the cost. Self-play needs
  thousands of episodes × ~160 LLM calls/game — API: $0.3–0.4/game → thousands of dollars; local
  9–20B: weeks of wall-clock. RL learns from experience it generates, not from a dataset.
- **Transfer.** The policy learns "which of THIS LLM's proposals to pick against THESE opponents
  under THESE rules" — couples to proposal distribution (train-local → deploy-flash-lite doesn't
  transfer), opponent distribution, and rule set. Every rule change re-triggers the campaign —
  exactly what the thesis predicts.
- **Ceiling.** Selection-only: can't pick an action the LLM never proposes. And rerank ≈ raw
  (paired A/B) suggests selection-among-reasonable-options isn't the current lever anyway.

Verdict: great education, wrong project. If ever pursued for learning, do it on a toy game with free
episodes.

## ADOPTED DESIGN (if ever built): outcome-trained memory-selection scorer

Key framing: **"bandit" names a training loop, not a pipeline component.** The pipeline stays
`retrieve (embedding top-N) → score → inject top-5`; the only contested slot is the scorer.

- **vs the CE reranker:** same slot, same architecture, different objective. Relevance labels =
  "is this memory ABOUT this situation"; outcome labels = "does injecting it lead to BETTER
  decisions." Relevant ≠ helpful — the myopic-framing SK entries were highly relevant AND poisonous;
  a relevance-trained CE ranks them up (correctly, by its objective), an outcome-trained scorer can
  learn to rank them down. This is the *learned* version of the track-1 quality-flag rider's insight.
- **Arrangement: ONE scorer, two training stages** (not two stacked selectors): stage 1 = relevance
  gold pretrain (dense, clean — the existing pure-Q CE plan); stage 2 = continue training the same
  model on outcome data as a correction. Outcome signal is too noisy to learn topicality from
  scratch; it's the only signal that catches "on-topic but harmful."
- **Counterfactual data:** logged sidecars only contain outcomes for memories actually injected
  (off-policy / logging bias — candidates the heuristic never picks have no outcome data). The
  Phase B **replay harness is the offline explorer**: replay a logged turn with candidate #k swapped
  in, score the regenerated decision with the de-lucked proxies, pennies per call. No live
  exploration, no degraded games.

## ⭐ v1 BEFORE v2 — tabular first (user-derived 2026-06-12)

v1: attribute each decision to the memory actually applied → score with de-lucked per-decision
proxies → accumulate a per-memory usefulness rate. **This IS a bandit — the tabular kind**
(memory = arm, empirical mean reward). And **Phase B already half-builds it**: the batch-merge
metadata aggregation ("appears in N games, role won M",
`evidence/execution_plan/phase_b_plan_review.md` track 2) IS the value
table; the missing half is merely *using* it at retrieval time as a ranking feature/filter.

Phase B de-noises every term of the credit-assignment problem:
- **3a/3b application labels** collapse "5 memories injected" → "the one actually applied" (biggest
  variance cut). ⚠ `adopted_strategy_keys` self-report = pre-fill, not truth — verify via the 3a
  mechanical echo-read.
- **3c** gives per-decision reward instead of per-game; **de-lucked proxies** strip luck variance.
- ⚠ **Do NOT change the generation schema to "select exactly 1 memory or null"** to clean up
  attribution: generation-side change → prompt-freeze violation (needs its own arm) AND distorts
  genuine blending of 2–3 memories. Post-hoc attribution (3a/3b) gets the de-noising for free
  without touching the game.

v2 (the learned contextual scorer above) is justified ONLY if v1 shows signal and the table's limits
bite, which are precisely:
1. **Cold start** — ~431 entries, most rarely injected; new entries (every rewrite/batch) start at
   zero data. Features generalize; table rows don't.
2. **Context-averaging** — one scalar per memory averages over situations; the net-horizon contrast
   pairs (same approach, different verdict by context) are in-house proof this loses real signal.
3. **Churn** — dedup merges/rewrites reset table rows; feature-based scores survive.

## Related: generator-side selection (logged in `../agent_dialogue/experiment_log.md`)

The generator already does inference-time selection (memory is advisory; `adopted_strategy_keys` +
override behavior — track 3b exists because overrides can be right). Training that skill into
weights = the SFT plan's existing "memory integration coverage" requirement; the cheap step-up is
DPO on track-3b-derived preference pairs. See the 2026-06-12 update in the agent_dialogue log.

## Interview framing (user decision 2026-06-12)

Don't present material not genuinely owned — the defensible headline stays: *"episodic memory is the
cheap, rule-change-robust alternative to RL, and I have the paired A/B evidence."* The v1 tabular
design is self-derived and fully explainable if asked ("score memories by attributed de-lucked
outcomes, stored as metadata, used at retrieval"); the v2 one-liner, only if confident: "the learned
version of my metadata score, for memories the table hasn't seen." Expected effect size is modest
(rerank ≈ raw says ranking isn't the bottleneck) — pitch as methodology (counterfactual eval via
replay), never as a win-rate promise.
