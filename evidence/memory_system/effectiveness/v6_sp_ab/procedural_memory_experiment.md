# Procedural memory (`strategy_points`) — the untested deceiver channel + self-evaluating rules

**Status:** DESIGN (2026-06-15), no code. A PARALLEL workstream to the dimension build — flagged
"unrelated but important." It reframes the wolf/SK null and is the cheap experiment that decides
whether dimension work is justified for deceivers at all.

## The reframe — the system is TWO-TIER, and only one tier was ever measured

- **Episodic memory = `observations`** — specific past events + outcomes → *inference* ("what's really
  going on here") → the **villager** channel.
- **Procedural memory = `strategy_points`** — distilled situation→action rules weighted by
  positive/neutral/negative counts → *execution* ("what's the move in this spot") → the **deceiver**
  channel. This is textbook procedural memory (weighted production rules); it is NOT episodic.
  (Naming: "procedural memory" / "playbook" > "strategy_points"; "episodic + procedural" is a stronger
  portfolio story than one episodic store.)

**Every effectiveness measurement to date used `observations` only** — the paired A/B, the
decision-replay screen, the wolf/SK two-edged-sword diagnosis. The procedural channel deceivers lean on
was never evaluated. So the **wolf/SK null is plausibly a CHANNEL MISMATCH, not a structural ceiling.**

### Verification result (2026-06-15, code recon)
The procedural channel is **fully WIRED, just not firing**: `retrieve_strategy_points_for_agent`
(`Agents/memory/retrieval/accessors.py:49`), namespace `("strategy_points", role, action_phase)`,
gated by `_retrieval_type_enabled(config, "strategy_points")` (`gating.py:115-120`, defaults `True` if
unset), formatted (`format_strategy_points`), injected (DAY/NIGHT memory context), adoption tracked
(`adopted_strategy_keys` → `StrategyAdoption`). `StoredStrategyPoint` already carries `retrieved_count`,
`used_count`, `positive/neutral/negative_count`. The SK strategy_points show `retrieved_count`/
`used_count` = 0 → not firing in the measured games. **STEP 1 of the experiment = confirm whether the
A/B config explicitly set `retrieval_types_config={"strategy_points": False}` vs ran-but-never-matched.**

### STEP 1 RESULT (2026-06-15) — EXPLICITLY DISABLED, confirmed
Every paired-A/B arm batch record carries
`retrieval_types_config = {"observations": true, "strategy_points": false}`. Cross-checked against the
eval-case sidecars: across **545 serial_killer cases in `ab_arms_sk`, 0 retrieved strategy_points**
(486 retrieved observations). So the procedural channel was **config-disabled**, not unmatched — the
wolf/SK null (and every effectiveness number to date) is an OBSERVATIONS-ONLY result. The
channel-mismatch premise is therefore live, and the `strategy_points-only` / `both` arms are genuinely
untested. Proceed to the decision-replay experiment (wolf×day_vote, arms {off · obs-only · sp-only ·
both}, retrieval→adoption→proxy).

## Why the structural theory predicts this (not contradicts it)
Memory's value ∝ how *situational* a role's optimal policy is. Villager policy is situational (depends
on the exact evidence config) → episodic. Deceiver *routine* (blend, vote with majority, leave no
record) is near-invariant → little for memory there — BUT deceiver *skill* is situational and lives in
the prescriptive register: "accused by a credible role → feign cooperation, invite a check"; "healer
saved your target → treat them confirmed, pivot"; "final-three vs villager+wolf → argue the wolf caused
the losses." Those are situational deception tactics, and they live in `strategy_points` — the
unexercised channel. **The thesis worth owning either way: "episodic memory's value is proportional to
how situational a role's optimal policy is — large for inference-heavy village roles, small for
near-invariant deceiver routine, but procedural memory is the deceiver's register."** Sharper and more
defensible than "memory helps everyone."

Dovetail with our OWN data: observations memory *raised* deceiver **day-detectability** (the two-edged
sword — `wolf_elim_rate` 0.227→0.292/0.340; SK lynched 63%→78%). The procedural playbook is exactly the
channel that might *help* day-social deception where the episodic channel *hurt* it. Clean, testable.

## The experiment (CHEAP / now — gates everything downstream)
Reuse the decision-replay harness (off-policy, paired, **village held fixed by construction**; day
actions wired incl. wolf day-vote).

- **Cell:** `wolf×day_vote` first (deceiver-first, not -only; deceiver proxies are immediately
  observable, villager "right read" only resolves post-hoc).
- **Arms:** {memory off · observations-only (what we measured) · **strategy_points-only** (the untested
  channel) · both}.
- **Score:** per-decision proxies we already have — net_verdict-aligned vote quality, exposure /
  detectability incidents, survival duration. **NOT win-rate** (village quality dominates deceiver
  win-rate → low-sensitivity instrument; luck is real even in human play).
- **Measure three things, not one:** retrieval-fires → **adoption** (we found observations 59% IGNORED;
  enabling retrieval ≠ behavior change) → proxy-effect.
- **Decision:** strategy_points move the deceiver proxies → channel mismatch, dimensions justified for
  deceivers (better match amplifies a real effect). They don't → structural ceiling, reframe the
  asymmetry AS the headline finding. Either way: one eval.

## Self-evaluating production rules (the "learns with time" loop)
The valenced-subset reward (see dimension spec §10a) makes `strategy_points` self-weighting:

- **reward(P) = role-signed difference-in-deltas** on the **valenced** dims (heat↓, forward_exposure↓,
  standing↑, parity-progress toward my faction, enemy-target-removed) between adopters and non-adopters
  of P in matched situations. Descriptive dims (situation, info_landscape, public_private *content*) are
  context, NO valence. Quasi-causal (the matched diff isolates P from game noise); no game-outcome
  attribution needed.
- **Cheap subset is the deterministic one:** target-removed / survival / parity-progress give a FREE
  "after" delta (game-state-derived); the LLM-read valenced dims (heat, standing) cost an extra
  situation-read → medium tier. The free subset is exactly the deceiver's clean proxies.

### Tiers (build only the cheap one now)
- **CHEAP / now:** the matched adopt-vs-not EVALUATION above (reuses logged `adopted_strategy_keys` +
  existing count fields + proxies). IS the deceiver-first experiment. Validates the valenced-delta reward.
- **MEDIUM / follow-up:** feed the utilities back into retrieval ranking (down-rank low-utility rules,
  promote high) — the count fields exist; wiring update-from-local-proxy + use-in-rank is bounded. This
  is what makes "plays better with time" literally true.
- **PARK / complex:** exploration to avoid rich-get-richer (trial low-count rules / counterfactual judge
  on non-adopted candidates) + live weight-convergence across a batch.

## Ordering
Villager·day dimension build proceeds in parallel (justified regardless of this). The deceiver half is
gated on this cheap procedural experiment — run it before pouring dimension work at the deceiver gap.

## Pointers
- Dimension spec: `evidence/extraction/situation_dimensions/dimension_schema_build_spec.md` (§10a links the reward).
- Wolf/SK diagnosis + proxies: `project-episodic-memory-remaining-work` memory.
- Harness: `evaluation/src/experiments/decision_replay.py`; proxies `decision_scoring.py`.
