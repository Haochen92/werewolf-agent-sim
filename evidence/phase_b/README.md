# Phase B — the v6 dimension-schema build era

**"Phase B" is a roadmap-era codename.** It names the era that built the **v6 situation-dimension
schema**: giving every stored memory record (and every live retrieval query) structured *situation
dimensions* — state-describing fields like `players_alive` / `is_swing` / `exposure_class` — so
retrieval can match on the *situation*, not just prose. Phase C (a standalone big-N win-rate A/B) was
deleted; Phase B was reframed to component-measured optimization + the labelling/training methodology
capstone (see `plan_review.md`).

## Artifacts in this folder

- **`dimension_schema_build_spec.md`** — the design spec: the per-cell situation standard, mixin DAG →
  11 cells, and the two generating rules (gate-vs-soft / embed-vs-extract; situation = state, never
  prescription). Design finalized 2026-06-15, pre-code.
- **`plan_review.md`** — the 2026-06-12 plan record that reframed Phase B (Phase C deleted).
- **`criticality_screen/`** — does conditioning retrieval on the v6 criticality regime move villager
  day-votes? Result: initially GO, then DOWNGRADED to HOLD after a same-game-leakage bug (aligning the
  query to v6 dims *did* help; conditioning on the regime did not).
- **`forced_schema_screen/`** — the store × schema 2×2: does forcing a per-memory applies/partly/no
  verdict engage the dims? Forcing hurt v5, was neutral on v6; v6 migrated to production.
- **`dimension_accuracy_audit/`** — the $0 deterministic audit of whether the v6 query-side dimension
  fills are actually correct. Fired the RE-OPEN on the gating null (some fills anti-informative).
- Other planning docs: `dedup_clustering_and_sp_extraction_plan.md`, `procedural_memory_experiment.md`,
  `v6_full_store.md`, `v6_wide_migration_roadmap.md` (the store build + migration record).

## Where the live apparatus + current truth live now

- **Standing apparatus** (re-runnable rulers) has graduated to
  `../../evaluation/src/instrument_validation/dimensions/`: `dimension_audit.py` (the $0 fill-accuracy
  audit) and `dimension_gating_screen.py` (the soft-gating screen, RE-OPENED by the audit).
- **Current-truth docs — twin axis:** `../extraction/situation_dimensions/report.md` is the *mechanism*
  doc (how the dimensions work today), and `../evaluation/dimension_extraction/report.md` is the
  *instrument-trust* report (were the fills the screens gated on even correct?).
