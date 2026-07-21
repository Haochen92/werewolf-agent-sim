"""Production consolidation config — OPERATIONAL levers only, no credit-rule switches.

The credit system itself is not configurable here by design (owner ruling 2026-07-21): production
ships exactly one grading rule — deadlock-negative town abstains + the conversion channel — and it
is hard-coded in ``credit_rules``/``credit``/``conversion``. The knobbed legacy-capable variants
survive only in ``evaluation/src/loop/`` so the frozen research runs stay reproducible. What IS
configurable is the machinery around the rule: prune/evict thresholds, synthesis cadence, decay
windows, models — the held-out-validated production params that migrated from the loop harness.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TickConfig:
    model: str = "gemini-3.1-flash-lite"        # synthesis model (validated ≈ pro on this task)
    dedup_model: str = "gemini-3.1-flash-lite"  # KEEP/DISCARD dedup passes (merge-free => flash-lite safe)
    obs_fold_dedup: bool = True                 # freeze-old obs dedup after the fold (off only in LLM-free tests)

    # conversion channel (always applied; these bound WHEN it can prune, not WHETHER it runs)
    conversion_window_days: int = 2             # a night-d find must convert by day d+1..d+window
    conversion_min_n: int = 5                   # min tallies before the conversion term can prune

    # prune / evict (fast-cull: every tick)
    prune: bool = True
    prune_tau: float = -0.15
    prune_min_follow: int = 8
    protect_min_follow: int = 2                 # proven-SP exemption: positive lift + this many follows => never dropped
    evict: bool = True
    evict_min_retrieved: int = 8
    evict_require_override: bool = True         # scope-aware: spare not_relevant-dominant non-follows

    # observation decay (count-scaled allowance clocked from last reinforcement)
    evict_observations: bool = True
    obs_evict_min_age: int = 4

    # synthesis (slow-synth: the one paid op, every k ticks)
    synthesize: bool = True
    incremental: bool = True
    synth_min_new_obs: int = 4
    synth_replenish_floor: int = 3
    synth_cell_unproven_cap: int = 12
    synth_track_min_follow: int = 5
    synth_every_k_gens: int = 2
    sp_dedup: bool = True

    def env(self) -> dict:
        """Env overrides pinning every paid model in a tick to the cheap tier — the pro-2.5 cost
        guard, carried over verbatim from the loop harness (extraction/synthesis/dedup fallbacks
        all resolve through these variables)."""
        return {"GOOGLE_GENAI_PRO_MODEL": self.model, "GOOGLE_GENAI_PRO_BACKUP_MODEL": self.model,
                "MEMORY_BATCH_DEDUP_MODEL": self.dedup_model}
