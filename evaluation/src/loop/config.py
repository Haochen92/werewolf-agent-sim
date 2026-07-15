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

    retrieval_types: str = "strategy_points_only"  # what the ON arm INJECTS into prompts. ⭐v7 design
    #   (owner ruling 2026-07-15; report §6.8 of evidence/store_curation): observations are SYNTHESIS
    #   SUBSTRATE — distilled into strategy points offline, NEVER injected into a live prompt. Default =
    #   SP-only so the loop cannot silently reproduce the v5/v6-style obs+SP injection: run_batch's own
    #   --retrieval-types default is "both", which the driver would otherwise inherit. "both" reproduces
    #   that v5/v6 obs+SP injection for a comparison arm; "observations_only" is the obs-only arm. The
    #   value is validated by run_batch's --retrieval-types choices= (names in RETRIEVAL_TYPES_CONFIGS —
    #   an unknown value crashes the first game subprocess before any real spend).
    expect_factions: str | None = None     # ⭐DECLARED experiment intent: which factions SHOULD have memory
    #   in the ON arm ("town_only", "all", or a comma list of roles). The driver reads the ON arm's ACTUAL
    #   memory_config and CRASHES on gen 1 if it doesn't match — the guard for the v2 trap (silently ran
    #   all_enabled vs the intended town_only, then drew a town conclusion off an all-memory-on arms-race
    #   board). None = no assertion, but the actual enabled-faction set is still logged + recorded.
    unchecked_arm: bool = False            # explicit opt-OUT of the arm-declaration gate (assert_arm_declared).
    #   The gate is fail-CLOSED: run_loop refuses to start unless expect_factions is set OR this is True — so
    #   the v2 trap can't recur by simply FORGETTING --expect-factions (the opt-in default let it). Set this
    #   (--unchecked-arm) only for a throwaway smoke where the arm isn't the thing under test.

    games_per_generation: int = 5          # batch size = the consolidation tick cadence (the LEARNING
    #   cadence — parallel games seed a frozen snapshot, so consolidation can ONLY happen at the
    #   generation boundary; small N = more frequent boundaries = faster/finer learning + more trend points)
    generations: int = 10                  # 10 consolidation steps = 10 slope points to eyeball the trend
    off_baseline: bool = True              # also run a memory-OFF arm (all_disabled, no seed/dump) as the
    #                                        flat comparison the slope is measured against
    game_concurrency: int = 5              # games within a generation run in PARALLEL (snapshot-seed →
    #   per-game dump → freeze-old merge; never a shared-store write race). Cap for API rate limits; 1 =
    #   sequential. Games are the wall-clock bottleneck, not consolidation.

    # (a) credit
    credit: bool = True
    window_generations: int = 6            # rolling de-luck window (generations). At N=5 the binding
    #   concern is credit DENSITY not recency: W=6 pools ~30 games/tick so SPs clear the follow>=8 prune
    #   threshold (W=4 -> ~20 games -> median ~3 follows -> prune barely fires -> a flat result is
    #   ambiguous). Recency cost is small in a pinned-model run (an SP's followed-value is stable; the
    #   non-stationarity is the store growing = which SPs exist, not a given SP's value). 0 = all-time.
    frozen_base_rates: bool = False        # reuse gen-1 baseline across generations (model-stability dep.)

    # (b) consolidation
    synthesize: bool = True                # credit-aware synthesis (CREDIT_SYNTH_PROMPT)
    incremental: bool = True               # re-synthesize a cell only when it has enough NEW evidence OR
    #   is depleted (below) — not "any new obs" (which re-synths nearly every cell every tick).
    synth_min_new_obs: int = 4             # re-synth a cell once it gains >= this many new obs since last
    synth_replenish_floor: int = 3         # ...OR its SP count fell below this (prune/evict depleted it)
    synth_cell_unproven_cap: int = 12      # HARD per-cell CONTESTED-lane ceiling: don't re-synthesize a
    #   cell already holding >= this many UNPROVEN SPs (cost guard + bloat ceiling on top of the new-obs
    #   gate). PROVEN SPs (positive de-luck lift & follow >= protect_min_follow) occupy EARNED slots OUTSIDE
    #   the quota, so a cell full of proven SPs still admits synthesis (exploration continues); a cell whose
    #   CONTESTED lane is full stays blocked — more untested candidates would only dilute exploration, and
    #   the lane drains via credit (a contested SP proves out, sours, or is evicted), not by refusing synth
    #   forever. Anchored on the §12 bloat record: healthy cells ran ~5 SPs, bloated ones ~34/cell (run-1
    #   grew 0→227 total) and that record was overwhelmingly UNPROVEN duplicates, so the same 12 protects
    #   against the same runaway — ~2.4x the healthy ~5 (headroom for legitimate deepening), well under the
    #   ~34 runaway. A DEPLETED cell (below synth_replenish_floor) is exempt so the replenish path still
    #   refills it. The cap gates GROWTH of the contested lane, not size: it holds until prune/evict shrink
    #   the lane (culls run every gen, synth only every k), so an over-cap cell resumes synth once its dead
    #   weight is culled below the cap.
    synth_track_min_follow: int = 5        # min follows before an SP's realized lift enters the synthesis
    #   TRACK RECORD (the credit-aware signal). Default 5 = the noise floor; a cheap smoke lowers it so the
    #   credit-aware path FIRES at tiny N (validates wiring, not calibration — the real run keeps the default).
    synth_every_k_gens: int = 2            # FAST-CULL / SLOW-SYNTH split: prune/evict/decay/credit run
    #   EVERY generation (cheap, deterministic), but the one paid op (LLM synthesis) runs only every k
    #   generations (cheaper + meatier — sees more accumulated obs per pass + less SP churn). 1 = every gen.
    #   At k=2, gen 1 is an obs bootstrap (no SPs yet); first synth at gen 2.
    sp_dedup: bool = True                  # after synthesis, KEEP/DISCARD-dedup the new SPs (freeze-old):
    #   collapse near-duplicate synthesized SPs, keeping the credited OLDER survivor (absorbs the dup's
    #   counts). SPs never MERGE (combining directives is incoherent). Without this, re-synthesizing active
    #   cells each generation piles up near-dup SPs and SMEARS the credit signal across them.
    dedup_model: str = "gemini-3.1-flash-lite"  # model for the loop's dedup passes (pro-2.5 was the cost
    #   driver, ~$9/run on the bloated store). SP dedup is KEEP/DISCARD only (schema forbids MERGE) so
    #   flash-lite is safe + cheap here. Obs dedup runs TRIAGE-ONLY (no merge, below) so flash-lite is safe
    #   there too. Toggle → "gemini-2.5-pro" for a quality comparison.
    obs_dedup_merge: bool = False          # obs dedup mode. False (default) = TRIAGE-ONLY (pass 1):
    #   KEEP/DISCARD collapse exact dups + count-bump, near-dups kept SEPARATE, no merge text, no pro-2.5
    #   — the cheap, nuance-safe version for the experiment. True = full dedup that can write merged text.
    prune: bool = True                     # drop SPs with de-luck lift < tau & follow >= min_follow (b1)
    prune_tau: float = -0.15
    prune_min_follow: int = 8
    protect_min_follow: int = 2            # PROVEN-SP EXEMPTION: an SP with POSITIVE de-luck lift and
    #   >= this many follows is NEVER dropped (prune/evict/any future age rule). A rare-but-proven lesson
    #   survives on thin evidence — positive signal, however sparse, beats deletion. Kept LOW (1-2) on
    #   purpose. Corollary (the non-stationarity case): SP degradation stays CREDIT-only — a note leaves
    #   only via NEGATIVE lift over the rolling window (souring) or as never-followed dead weight, never
    #   because it merely got old.
    evict: bool = True                     # drop SPs surfaced >= min_retrieved but never followed (rejected)
    evict_min_retrieved: int = 8
    evict_require_override: bool = True     # scope-aware (§10b): only evict a retrieved-but-unfollowed SP
    #   when its non-follow is OVERRIDE-dominant (agent applied it and beat it = bad content). SPARE
    #   not_relevant-dominant SPs — the situation didn't hold, a retrieval/scoping miss, NOT the lesson's
    #   fault; deleting it would blame content for a retrieval artifact. False = legacy blunt evict.

    # OBSERVATION decay (the obs analog of prune/evict). Obs carry no credit (you don't "follow" one), so
    # they decay by a COUNT-SCALED survival allowance clocked from the LAST reinforcement: drop an obs once
    # current_gen - last_reinforced_gen >= obs_evict_min_age * observation_count. Nothing is immortal — a
    # count-N obs buys N windows, but a reinforcement RESTARTS the clock, so a still-recurring lesson keeps
    # surviving while a distilled-and-abandoned one decays. The clock is the LAST reinforcement, not the
    # first-seen age, because an obs reinforced recently must NOT die on its original age. Recency is
    # enforced by SELECTION (what reaches synthesis), never by asking the synthesizer to weigh a number.
    # Trade-off: evicting a reinforced obs resets its identity — the next rewording re-enters as a count-1
    # singleton and may re-trigger synthesis of an already-distilled lesson; store size is traded for
    # re-litigation. Fallback if this fails to bound the store in a live run: per-cell size-restricted LRU
    # (evict oldest-touched).
    evict_observations: bool = True
    obs_evict_min_age: int = 4             # per-count grace window (generations since last reinforcement)
    #   before an obs is evictable; the allowance is min_age * observation_count. For a count-1 obs this is
    #   the old rule exactly. Most obs are singletons (game situations are diverse → count==1), so a small
    #   window (2) decimated the base (~250 dropped/gen) and starved synthesis; 4 lets a singleton persist
    #   through most of a 10-gen run while reinforced obs live proportionally longer.

    # (d) discussion credit on: day_discussion SPs earn the day-vote endpoint tick + the move-grain
    # refinement, and concealment-typed deceiver SPs earn the guarded concealment floor (free,
    # deterministic — evidence/credit/report.md §3). The omniscient-tagger credit MODE was RETIRED
    # 2026-07-13 (owner ruling): its night read-quality override is gone and its per-day verdict is a
    # standalone diagnostic (discussion_tagger.py, post-hoc), never a credit source.
    discussion_credit: bool = True

    # The tell pipeline (v1, 2026-07-13): per generation, mine + role-blind k=2 detect over the ON
    # arm's games against the frozen checklist, fold (dedup new wordings into canon, verdicts, publish
    # checklist v_{k+1}), rebuild the injected book. OFF by default — the v7 run turns it on. The seed
    # checklist/book are frozen artifacts from the held-out program (tell_extraction, log §13-16).
    tells: bool = False
    tell_seed_checklist: str = ""   # {channel: [{tell_id, text}]} — required when tells=True (cold store)
    tell_seed_book: str = ""        # optional gen-1 book (built from the held-out lift table)

    def env(self) -> dict:
        """Env overrides pinning EVERY paid model in a run to the cheap tier — the pro-2.5 cost guard.
        GOOGLE_GENAI_PRO_MODEL/_BACKUP pin extraction + in-process synthesis + the tagger (all resolve via
        get_llm_pro → these vars, whose default is gemini-2.5-pro). MEMORY_BATCH_DEDUP_MODEL pins any dedup
        that falls back to its module default (also gemini-2.5-pro) — the loop's own dedup calls already
        pass model=dedup_model, this covers subprocess/per-game paths. Applied to game subprocesses AND the
        driver's own process (run_loop), so nothing hits pro-2.5 regardless of the launch shell."""
        return {"GOOGLE_GENAI_PRO_MODEL": self.model, "GOOGLE_GENAI_PRO_BACKUP_MODEL": self.model,
                "MEMORY_BATCH_DEDUP_MODEL": self.dedup_model}
