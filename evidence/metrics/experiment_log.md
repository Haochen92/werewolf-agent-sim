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

## Audit of existing metrics (2026-06-06)

Two **fully separate** families. (Full catalog with file:line in the session record; condensed here.)

### Family 1 — deterministic game/role metrics (`Agents/compute_metrics.py`, `schemas/metrics.py`)
**100% mechanical (votes, revealed roles, deaths) — zero LLM, fully objective. BUT entirely
outcome-based, zero uncertainty-normalization.** They measure *what happened* (luck included):
- `BaseGameMetrics`: winner, game_length, mislynches, wolf_eliminations, healer_save_count,
  healer/investigator_nights_alive + exit_method, investigator_wolves_found, power_roles_killed,
  wolf_power_role_target_nights, mislynch/wolf-elim day breakdowns (steered/blended/dissented).
- `DerivedGameMetrics` (rates): `correct_elimination_rate` (wolf lynches / lynches),
  `healer_save_rate` (saves / nights — **pure luck**: did wolves happen to target the protected
  player), `investigator_accuracy` (wolves_found / investigations — a forced late 1-of-2 guess scores
  = an early skillful read), `wolf_steering/blending/dissent_rate`, `wolf_power_role_targeting_rate`.

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
