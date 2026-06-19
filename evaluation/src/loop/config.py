"""Compounding-loop config — every lever toggleable (config-flag policy: variants coexist, compared).

One harness runs all arms; flip fields to A/B credit, synthesis, prune, decay, model, cadence, window.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class LoopConfig:
    # arm: what's in the loop. off = memory-off baseline (no seed/write); ob_loop = observations only;
    # ob_sp_loop = observations + strategy-point synthesis (the full loop).
    arm: str = "ob_sp_loop"

    model: str = "gemini-3.1-flash-lite"   # extract + synth model (validated ≈ pro); toggle → gemini-2.5-pro

    games_per_generation: int = 5          # batch size = the consolidation tick cadence
    generations: int = 6

    # (a) credit
    credit: bool = True
    window_generations: int = 0            # rolling de-luck window (0 = all generations so far)
    frozen_base_rates: bool = False        # reuse gen-1 baseline across generations (model-stability dep.)

    # (b) consolidation
    synthesize: bool = True                # credit-aware synthesis (CREDIT_SYNTH_PROMPT)
    incremental: bool = True               # re-synthesize only cells whose obs changed since last tick
    prune: bool = True                     # drop SPs with de-luck lift < tau & follow >= min_follow (b1)
    prune_tau: float = -0.15
    prune_min_follow: int = 8
    evict: bool = True                     # drop SPs surfaced >= min_retrieved but never followed (rejected)
    evict_min_retrieved: int = 8

    discussion_credit: bool = False        # (d) — off for loop v1 (free floor measured, tagger unbuilt)

    def env(self) -> dict:
        """Env overrides to pin the extraction+synthesis model for a run (both primary and backup)."""
        return {"GOOGLE_GENAI_PRO_MODEL": self.model, "GOOGLE_GENAI_PRO_BACKUP_MODEL": self.model}
