# Namespace augmentation — probe log

**Date:** 2026-06-11
**Code (pointer):** `scripts/augment_namespaces.py` + `scripts/augment_incremental_merge.py`,
`Agents/memory/extraction/augment_agent.py` (commits 599f90d / 12f92da / fd2f980).
**Source games:** `evaluation/frozen_eval_sets/extraction/extraction_v5_0.jsonl` (20 v5_seed games).

## Goal

v5_0 (memory-off-built store) is thin on some `(role, action_phase)` namespaces
— `day_vote` / `night_action` cells hold 6–30 items vs 37–44 for `day_discussion`.
Test whether a targeted re-extraction pass can deepen a thin cell **without** the
circularity of the memory-on-built v5_1 store. The make-or-break question: does
re-mining add genuine **variety**, or just **number** that dedup collapses?

## Method

Focused pass: the per-role extraction prefix (rebuilt offline from each frozen
case) + a tail that pins BOTH role and a single phase, asking for an exhaustive
deep pass on that one cell. Probed cell: `investigator/day_vote`. Candidates routed
through the existing online dedup into a v5_0-seeded store, dumped to the throwaway
`memory_stores/v5_0_augmented/`. Then an incremental-merge inspection
(`new_keys` = augmented-minus-base keys; old v5_0 items frozen) measured how much
the online "kept" set would consolidate under a merge-capable pass.

## Results

20 games → 141 raw candidates. Online dedup (KEEP/DISCARD only):

| kind | candidates | kept | discarded | cell before→after |
|---|---|---|---|---|
| observations | 70 | 45 | 25 | 12 → 57 |
| strategy_points | 71 | 53 | 18 | 6 → 59 |

Incremental merge (dry run): observations 3 merged, strategy_points 0 merged.

## Finding (inconclusive on the variety question — a tooling result)

The "kept" counts overstate distinctness: the online dedup is KEEP/DISCARD-only, so
near-dups it can't merge are kept as separate entries. But the merge pass barely
fired (3 obs, 0 sp), which **contradicts** a by-eye read of the 59 kept SP situations
— there are clear near-duplicate clusters (investigator-under-suspicion,
endgame-find-last-threat, day1-abstain-stalemate, voting-record-used-against-you),
suggesting true distinct variety nearer ~15–25.

Root cause: the merge/dedup prompt was tuned on the OLD single-prompt, terser,
pre-per-role system. The per-role extraction is far more **verbose** and embeds the
dimensional context (information_landscape / game_phase / consensus_texture /
agent_exposure) as PROSE inside the `situation` field rather than the dedicated
fields. Since `situation` is the embedded field, verbose prose lowers surface
similarity → clusters don't form → the merge never fires.

So neither dedup pass reliably measures distinct variety on v5 content. The
augmentation mechanism works; the measurement is blocked on a stale merge prompt.

## Next (deferred — prompt-freeze)

1. Re-tune the merge/dedup prompt for verbose per-role items.
2. Tighten extraction field discipline (dimensions in their structured fields, not
   `situation` prose) — also helps retrieval.

Recommendation: park augmentation as built-and-validated; treat the merge re-tune as
a separate scoped phase.
