"""Production consolidation config — OPERATIONAL levers only, no credit-rule switches.

The credit system itself is not configurable here by design (owner ruling 2026-07-21): production
ships exactly one grading rule — the ten-seat table of plan §9.6 item 10 — and it is hard-coded in
``grading``/``credit_rules``/``credit`` (the conversion channel was dropped with the port: it credited
town day lookups, which no longer happen). The knobbed legacy-capable variants
survive only in ``evaluation/src/loop/`` so the frozen research runs stay reproducible. What IS
configurable is the machinery around the rule: prune/evict thresholds, synthesis cadence, decay
windows, models — the held-out-validated production params that migrated from the loop harness. One
exception to the grading being fixed: which memory-off base a follow is compared with
(``baseline_by_day``, 2026-10-28), kept as a flag so the all-days base still runs for comparison.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TickConfig:
    model: str = "claude-sonnet-5-5"            # synthesis model (Sonnet 5.5, owner 2026-10-12; Claude since the
                                                # Gemini credits ran out, 2026-10-15); a claude-* model is called
                                                # through the Anthropic SDK
    dedup_model: str = "anthropic/claude-haiku-5-5"  # KEEP/DISCARD dedup passes (merge-free => a cheap model is safe)
    obs_fold_dedup: bool = True                 # freeze-old obs dedup after the fold (off only in LLM-free tests)
    publish: bool = True                        # after a pass, mirror the records into the served game's
                                                # index (persistence/postgres.py); off = records only

    # prune / evict (the credit pass's, every pass; decisions §14)
    prune: bool = True
    prune_tau: float = -0.15
    prune_min_follow: int = 8
    protect_min_follow: int = 2                 # proven-SP exemption: positive lift + this many follows => never dropped
    evict: bool = True
    evict_min_retrieved: int = 8
    evict_require_override: bool = True         # scope-aware: spare not_relevant-dominant non-follows
    baseline_by_day: bool = True
    """Compare each followed decision with memory-off play on the same game day (days 1-3, then
    "4+"): lessons fire at particular stages, and an all-days base mixes easy late days with hard
    early ones. False = the all-days base of before 2026-10-28."""
    baseline_min_n: int = 20
    """Memory-off decisions a day needs before it is used as a base; a thinner day falls back to the
    channel's all-days base."""

    # observation decay (count-scaled allowance clocked from last reinforcement)
    evict_observations: bool = True
    obs_evict_min_age: int = 4

    # synthesis (slow-synth: the one paid op, every k ticks)
    synthesize: bool = True
    batch: bool = False                         # a Claude synthesis model runs as one Message Batch (half
                                                # price, back within the hour as a rule): offline runs only
    incremental: bool = True
    synth_min_new_obs: int = 4
    synth_replenish_floor: int = 3
    synth_cell_unproven_cap: int = 12
    synth_track_min_follow: int = 5
    synth_every_k_gens: int = 2
    synth_outcome: str = "verdict"              # which outcome each observation shows synthesis: the extraction
                                                # judge's "verdict" or its decision's deterministic "grade"
                                                # (decisions §13; both kept until measured)
    sp_dedup: bool = False
    """The lesson dedup after synthesis. Off until tuned (owner, 2026-10-26): its dry run on the 605
    points of the 40-game store caught 9 of the readers' 65 duplicate groups and dropped points across game
    stages (evidence/memory_system/v8/experiment_log.md, 2026-10-13), and on the 111-entry labelled set
    the Haiku 5.5 judge deleted 7 distinct points (evidence/dedup/batch_dedup/experiment_log.md,
    2026-10-26). The planned retune: partition by honesty and the stage facts, and a stronger judge."""

    def env(self) -> dict:
        """Env overrides pinning every paid model in a tick to the cheap tier — the pro-2.5 cost
        guard, carried over verbatim from the loop harness (extraction/synthesis/dedup fallbacks
        all resolve through these variables). A Claude synthesis model is called directly, so the
        factory's pro model is pinned to the dedup model instead."""
        pro = self.dedup_model if self.model.startswith("claude") else self.model
        return {"GOOGLE_GENAI_PRO_MODEL": pro, "GOOGLE_GENAI_PRO_BACKUP_MODEL": pro,
                "MEMORY_BATCH_DEDUP_MODEL": self.dedup_model}
