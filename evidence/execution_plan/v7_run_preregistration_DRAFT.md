# v7 compounding run — pre-registration (DRAFT, awaiting owner signature)

> **Status: DRAFT** — authored by the agent 2026-07-13 while the owner recovers; unsigned.
> Everything unmarked restates the plan of record (`compounding_measurement_plan.md` §R and the
> read/tactic design record). Every `☐ [SIGN]` box is an owner decision — the draft proposes a
> default with its reason, and signing means adopting it. Nothing launches before every box is
> ticked and this header says SIGNED with a date.

## 1. Thesis under test

Does the consolidation loop make memory **compound** across generations — a store that improves
with play — versus the validated static-memory effect (a fixed store helping town)? Both prior
paid runs are INVALID (run-1 unpaired; run-2 arms-race confound); this run is the third and, at
current budget, final attempt.

## 2. Arms

- **Loop arm**: full pipeline — extraction → credit (v1 wiring: vote-endpoint day credit,
  read-partitioned night credit, concealment floor, §6 valence rulings, first-link DIAGNOSTIC) →
  consolidation each generation (prune / evict / credit-aware synth) → tell epoch fold every 10
  games (frozen checklist v_k, cached k=2 detection). **Injected into prompts: strategy points +
  tell book. Observations are substrate-only (never injected).**
- **Baseline arm**: same harness, memory OFF (the ambient base-rate arm credit already consumes).
- Arm guard `--expect-factions` ON for every batch (the run-2 confound tripwire).

☐ [SIGN] **Arms as stated** (any additional arm = new money; the design intends exactly these two).

## 3. Primary endpoint (ONE, fixed now)

**End-point A/B**: after the final generation, generate a fresh paired batch — final loop store vs
baseline — on identical boards/seeds, and compare the **town decision basket** (the validated
proxy basket; |r|≈0.6 vote-basket family). Direction + magnitude reported with N; no other
endpoint may be promoted to primary after data exists.

☐ [SIGN] **Primary = town decision basket on the end-point A/B.**

Secondary (reported, never promoted): per-role basket splits; store-quality trajectory (SP-lineage
lift, prune/evict census, lift-weighted composition — the $0 "does the store improve" battery);
tell-book lift stability across epochs; wolf/SK concealment floor movement. Synthesis-quality
judging vs human anchors is **provisional** until the owner authors golden anchor points (D2) —
reported with that caveat.

## 4. Size, budget, stopping rule

- Proposed shape: **4 generations × 10 games** (epoch fold at each boundary) **+ 2 × 10 paired
  end-point games** ≈ 60 games ≈ **$36–43** at observed per-game cost (~$0.30–0.40 generation +
  ~$0.25–0.30 memory/extraction/tell overhead), inside the ~$45 reserve.
- **Stopping rule**: fixed N, no result-based stopping. The run halts early ONLY on invariant
  tripwires (arm-guard failure, leak-check failure, epoch-fold failure) — a halted run reports as
  halted, never as a result.

☐ [SIGN] **N = 4×10 + 2×10 and the no-peeking stopping rule.** (Shrink to 3 generations if you
want more reserve; say so at signing.)

## 5. Injection policy — RULED (owner, 2026-07-14; no signature box)

**No role-revealing exclusion.** The injected book is a **role-identification manual for every
unrevealed role**, including power-role-identifying families (the held-out investigator
source-withheld family, ×8.2). Rationale: inferring a specific role from public behavior is the
tell mechanism's entire point, and the shared book is symmetric by design — the same information
lets wolves hunt an investigator, the healer protect one, and the investigator learn to conceal
the pattern. The 2026-07-13 draft's exclusion default (and its 2026-07-14 counterpoint annotation)
is superseded by this ruling.

Implemented same day: the exclusion is removed from the code; book selection now ranks by
**subject-role concentration** (`tell_credit.subject_lift`) rather than credit's evil-lift — §6.5
(what *pays*: positive evil-lift only) is unchanged; the two deliberately disagree on town-subject
tells. Launch seed book = `evaluation/frozen_eval_sets/tell_book_v2_seed.json` (34 entries, all six
roles; built by the frozen-record script `evidence/extraction/tell_extraction/scripts/build_seed_book.py`).
Caveat carried into interpretation: the recorded injection-channel screen (27.5% changed, direction
positive) ran on the v1 wolf+SK-only book; the v2 book is bigger and role-grain, and has not been
re-screened.

## 6. Frozen at launch (provenance)

Runtime fingerprint (git SHA, prompt hash, model IDs, backend) stamped on every batch; checklist
v_k artifacts versioned per epoch; detector = cached k=2 union at thinking=low (golden-parity
config, 2026-07-13); credit = the v1 wiring with all five §6 rulings as stamped in
`evidence/credit/report.md`; no prompt edits mid-run (a mid-run prompt change = new epoch of a NEW
experiment, i.e., the run ends).

## 7. Interpretation commitments (signed before data)

- Null/negative on the primary = "no detected compounding at this power," reported as such — not
  retried with a new endpoint, not narrated away.
- Cross-arm comparisons only within this run's epoch; no comparison to any pre-epoch batch.
- Any number from a halted or guard-tripped batch is quarantined, never pooled.

---

**Owner signature**: ____________  **Date**: ____________
(Sign by replacing this line with "SIGNED <date>" and ticking every ☐ above; note any modification
inline next to its box.)
