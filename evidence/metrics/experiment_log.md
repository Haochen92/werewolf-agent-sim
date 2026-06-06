# Evaluation Metrics — per-role play-performance scoring

**Status: DESIGN DISCUSSION (2026-06-06), no code yet.** Part of Phase A #3 (tracing consolidation;
see `evidence/tracing/`) — "design against the eval needs." The metrics ARE the eval need: they are
the key driver of how we measure the memory system's impact (Phase C win-rate A/B). This log tracks
the audit + the design discussion. Pre-Phase-B-labelling; freeze rules apply
(see `feedback-memory-pipeline-prompt-freeze` — no main-pipeline prompt changes).

## Goal / criteria

Beyond win rate, we want **per-role scores** that:
1. **Objective**, not vague/subjective.
2. Measure **decision quality given the circumstances** (process), not outcomes (which include luck).
3. Ideally **normalized by uncertainty** — judge a choice against the information available at decision
   time (info-starved spot → near-coinflip → low weight; info-rich spot → choosing against the
   evidence is a real, heavily-weighted error). Process-vs-outcome, à la decision theory/poker.

## Metric versioning (v0 → v1 → v2)

This work is **v2**, a refinement — not a from-scratch build. The history matters:

- **v0 — nothing logged.** Early games ran but emitted no structured metrics. Impact could only be
  eyeballed; there was no quantitative signal at all.
- **v1 — the CURRENT eval (the proxy + judge suite below).** Forming this was itself substantial
  progress: deciding *what* to count, building the per-game accumulators (`DayResolutionMetric` /
  `NightResolutionMetric`), the derived rates, and the LLM-judge rubrics. v1 took us from "measure
  nothing" to a working, repeatable proxy basket + memory-pipeline judges. The proxies it defined are
  the foundation we build on — the audit below is a critique *of a real artifact*, not of a blank slate.
- **v2 — this workstream: refine the DETERMINISTIC scores.** De-luck the v1 outcome proxies (condition
  on opportunity), make uncertainty-awareness explicit where feasible, and verify each proxy is
  monotonic in skill. v2 keeps v1's mechanical, fully-objective backbone and sharpens it; it does NOT
  discard v1 or chase a per-decision determinism the system can't honestly support (see discussion).

## How v1 came to be — provenance & rationale

No design log was ever written for v1; the rationale below is reconstructed from git history
(`1cd5ed7 "Add: runtime memory metrics for evaluation"`, `a299ee2 "Fix: measure wolf blending…"`,
`67e22c3 "Make metrics robust for 3 factions…"`; judge commits `eb23f72`, `50403f5`, `bf9490a`,
`c07dff7`…) and the code itself. Two design pillars:

### Pillar 1 — the LLM-as-judge pipeline (subjective by nature), aimed at "did memory help?"
The judge suite (`evaluation/judges/`) measures the thing win rate can't see directly: **was the
memory useful for *this decision*** — `retrieval_relevance` (were the pulled memories on-point),
`strategy_application` (did the agent actually use them), `action_quality`, `grounding`,
`summary_quality`. Aggregated across memory-on turns, this is the qualitative read of memory
effectiveness, complementing the win-rate A/B.

**Why it's subjective — concretely:** the judge is *itself an LLM* scoring free-text on a 1–5 rubric.
So a score depends on (a) the judge model + prompt phrasing + temperature, (b) the judge's own
interpretation with no ground-truth anchor, (c) the backend — Vertex vs Google AI give different
outputs at temp 0 ([[feedback-vertex-backend-affects-scores]]), and (d) known blind spots — our own
finding is that the judge **misses information gain** ([[feedback-llm-judge-limitations]]), plus the
usual verbosity/leniency/position biases. It's reproducible only approximately. That subjectivity is
exactly why v1 *also* shipped the deterministic metrics, and why v2 leans on them.

### Pillar 2 — the deterministic metrics: "score whatever we can extract mechanically"
`compute_metrics.py` was built bottom-up from what the game emits with **zero LLM**: votes, revealed
roles, deaths (`Day/NightResolutionMetric`). **Normalization is already present** — every
`DerivedGameMetric` is a *rate*, normalized by **opportunity** (the denominator), not a raw count:
e.g. `investigator_accuracy = wolves_found / investigations`, `healer_save_rate = saves /
nights_alive`, `wolf_steering_rate = steered / mislynch_days`. So v1 already de-noises by opportunity;
what it does *not* do is normalize by **information/difficulty** (uncertainty). That — not "no
normalization" — is the precise gap v2 targets.

## Accurate limitations (re-checked against `Agents/prompts/roles.py` + the gameplay changes)

The game changed since v1's metrics were written: **voting is now optional** (abstain / plurality, no
forced lynch) and there is a **third faction** (night-immune serial killer + town vigilante). Checking
each metric against the *actual* current roles, some limitations are **real and concrete**, and one of
my earlier critiques was **exaggerated**:

**Real & concrete (gameplay-change-induced staleness — verified in code, not yet fixed):**
- **`mislynches` / `correct_elimination_rate` don't credit lynching the SK.** `mislynches` counts any
  `voted_player_role != "wolf"` ([compute_metrics.py:50](Agents/compute_metrics.py#L50)) and
  `correct_elimination_rate = wolf_eliminations / total` only counts `role == "wolf"`. But the SK
  **can only be removed by a day vote** (roles.py:56) — lynching it is the village's single most
  important day-objective against that faction, yet it scores as a *mislynch*. "Correct" should be
  `role in {wolf, serial_killer}` from the town's perspective.
- **`investigator_accuracy` ignores SK discovery and mismodels the role's objective.** It counts only
  `investigator_target_role == "wolf"` ([compute_metrics.py:74](Agents/compute_metrics.py#L74)), but
  the investigator's stated job (roles.py:21) *also* values **clearing a townie** (narrows the pool)
  and, post-3-faction, **finding the SK** — neither is credited, so a deliberate, skillful
  town-clear or SK-find reads as a "miss."
- **`_exit_method` mislabels SK/vigilante night kills as `"killed_by_wolves"`**
  ([compute_metrics.py:171-174](Agents/compute_metrics.py#L171)) — acknowledged in an in-code comment;
  per-killer attribution deferred to the dense per-role pass.

**Exaggerated in my first pass (correcting for accuracy):**
- **`healer_save_rate` is NOT "pure luck."** It's luck-laden but **monotonic in skill**: a healer that
  reads threats well (roles.py:8) protects likely targets and saves more over many games. It's a
  *valid* proxy — exactly the kind v2 keeps and verifies via proxy-vs-win, not one to discard.
  (Three factions make it noisier — two night killers now — but not invalid.)

**New gaps from optional voting (not bugs, but incompleteness):**
- A **strategic abstain** (good play under uncertainty) is invisible: it just shrinks
  `total_eliminations`, neither rewarded nor penalized. Vote-quality is now an incomplete picture, and
  the lynch-rate denominators are smaller → noisier at low N.

**Net:** the headline v1 weakness for our purposes is **not** the outcome-vs-decision-quality
philosophy — it's that the 3-faction + optional-voting changes left several metrics **semantically
stale** (SK-lynch and SK-discovery uncredited, killer attribution wrong). Those are concrete and
fixable in v2 and matter more than the luck critique.

## Audit of existing metrics (2026-06-06) — this is v1

Two **fully separate** families. (Full catalog with file:line in the session record; condensed here.)

### Family 1 — deterministic game/role metrics (`Agents/compute_metrics.py`, `schemas/metrics.py`)
**100% mechanical (votes, revealed roles, deaths) — zero LLM, fully objective. Already normalized by
OPPORTUNITY (rates, not raw counts), but NOT by information/difficulty (uncertainty), and
outcome-based.** They measure *what happened* (luck included, but mostly monotonic in skill — see
"Accurate limitations" above for which are stale vs valid):
- `BaseGameMetrics`: winner, game_length, mislynches, wolf_eliminations, healer_save_count,
  healer/investigator_nights_alive + exit_method, investigator_wolves_found, power_roles_killed,
  wolf_power_role_target_nights, mislynch/wolf-elim day breakdowns (steered/blended/dissented).
- `DerivedGameMetrics` (rates): `correct_elimination_rate` (wolf lynches / lynches),
  `healer_save_rate` (saves / nights — luck-laden but monotonic-in-skill, a *valid* proxy),
  `investigator_accuracy` (wolves_found / investigations — stale: ignores town-clears and SK-finds),
  `wolf_steering/blending/dissent_rate`, `wolf_power_role_targeting_rate`. See "Accurate limitations"
  for which are stale (SK-related) vs valid-but-luck-laden.

### Family 2 — LLM judges (`evaluation/judges/`, `evaluation/core/schemas.py`)
**Decision-quality-oriented and partially uncertainty-aware, BUT subjective (LLM), scoped to the
MEMORY system (not holistic role play), per-action (not aggregated per-role/game).** Judges:
pipeline (summary_quality, retrieval_relevance, strategy_application, grounding), summary
(faithfulness, specificity, retrieval_usefulness, non_redundancy, role_perspective), retrieval
(relevance, unique_lessons, efficiency), application (action_quality, strategy_application, grounding,
adoption_accuracy), day_summary (completeness, accuracy, evidence_type_clarity, village_dynamics,
epistemic_correctness), extraction/per_role_extraction (specificity, epistemic_compliance, grounding,
coverage, diversity, perspective_compliance, strategy_depth, novelty), dedup/batch_dedup.
Uncertainty handling is ad-hoc (e.g. "if relevance ≤2 score neutral"). Frameworks:
`EPISTEMIC_STATUS_RULE` + `SITUATION_STANDARDS` (`Agents/prompts/standards.py`).

### Verdict against the criteria
**The target metric — per-role, decision-quality, uncertainty-normalized, objective — does NOT exist.**
Family 1 is objective but outcome/luck-based. Family 2 is decision-quality-ish but subjective +
memory-scoped + per-action. This is the gap, and it's the dense signal the roadmap always wanted for
the Phase C A/B (win rate alone is too noisy).

## Design discussion — why pure deterministic decision-quality is not feasible now

Attempted a deterministic-first "Vote Decision Quality" (vote vs known roles, uncertainty-weighted).
It collapsed under scrutiny:
- **Mechanical role-knowledge is nearly empty.** The only agents who *mechanically know* another live
  player's role: the **investigator** (own results), the **vigilante** (an immune target = confirmed
  SK, via `vigilante_results`), and **wolves** (allies). No villager ever mechanically knows a role.
  So a deterministic "voted a known wolf / known townie" check fires for ~1–2 agents on a few turns —
  a sanity anchor, not a metric.
- **No A/B-symmetric uncertainty signal.** The situation summary (with `information_landscape`) is
  **memory-arm-only** — it doesn't run in memory-off games (confirmed: memory-off game had 0
  situation_summary / 0 memory_retrieval spans, but 4 day-summaries). A normalizer that exists in
  only one arm biases the comparison. The `day_summary` runs in **both** arms but is **end-of-day,
  village-level, and static** — it can't see intra-day suspicion shifts and isn't per-agent.
- **No captured per-agent, per-player, evolving certainty.** That structured belief signal — which a
  true decision-quality + uncertainty metric needs — is simply not emitted.

### What the existing system DOES capture (both arms, categorical/deterministic-usable)
- The **vote** (per agent/day, validated player_id).
- **Mechanical private knowledge**: investigator_results, vigilante_results, wolf allies.
- **Dynamic behavioral-categorical signals**: `addressed_targets`, `day_summary` `Accusation{target,
  evidence_type}` / `RoleClaim`, full voting records.
- Free-text/dynamic but NOT deterministic: `updated_strategy`, messages, situations (memory-arm only).
- **Not captured**: structured per-agent per-player evolving role-belief/certainty.

### Output-path redesign (force agents to emit a per-player belief vector) — REJECTED
1. It's a **main-memory-pipeline prompt change** → invalidates Phase B labels (freeze rule).
2. It **confounds the A/B** — changing required output changes how agents play, contaminating the
   win-rate/skill signal we are measuring.
3. It's **subjective + circular** — a competent LLM's vote already aligns with its self-reported
   beliefs (belief-vs-vote consistency adds ~no independent signal), and belief-correctness still
   needs ground truth → back to outcome.

## DECISION — proxy-basket approach (statistically honest, freeze-safe)

Keep outcome **proxies**, **de-luck** where cheap, rely on **N (games × days)** to average luck, and
require only that each proxy is **monotonic in skill**. Win rate stays the headline; the proxy basket
is the variance-reducer.

1. **Curate a per-role proxy basket** from data we already emit (investigator targeting, healer
   protect-given-threat, vote-vs-strongest-public-accusation, wolf blend/steer, SK/vig survival+kills).
2. **De-luck each** by conditioning on *opportunity*, not raw outcome (e.g. healer rate only over
   nights a kill occurred and a defensible target existed; investigator accuracy normalized by
   live-wolf density).
3. **Verify monotonicity objectively** — correlate each proxy with its faction's **win** across games.
   Win is the independent ground-truth skill anchor (non-circular). Drop proxies that don't move with
   winning.
4. **Confirm both-arm symmetry + raw-data coverage** for each kept proxy.

Explicitly accept the basket is luck-laden-but-monotonic rather than feigning a per-decision
determinism the system can't honestly support. A richer decision-quality layer, if ever wanted, is a
**post-hoc eval-side judge done AFTER labelling** — never an output-path change.

## Next step

Inventory the existing proxies; classify each by (de-luckable? both-arm-symmetric? plausibly
monotonic?); run the **proxy-vs-win correlation** on available games to decide which to keep and
whether the basket is strong enough. All post-hoc query — no frozen-pipeline changes.
