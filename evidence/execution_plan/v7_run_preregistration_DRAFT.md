# v7 compounding run — pre-registration (DRAFT, awaiting owner signature)

> **Status: SIGNED 2026-07-16** (owner, in-session; boxes ticked with §8 adopted as drafted — no modifications noted). Originally authored 2026-07-13.
> Everything unmarked restates the plan of record (`compounding_measurement_plan.md` §R and the
> read/tactic design record). Every `☑ [SIGNED 2026-07-16]` box is an owner decision — the draft proposes a
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

☑ [SIGNED 2026-07-16] **Arms as stated** (any additional arm = new money; the design intends exactly these two).

## 3. Primary endpoint (ONE, fixed now)

**End-point A/B**: after the final generation, generate a fresh paired batch — final loop store vs
baseline — on identical boards/seeds, and compare the **town decision basket** (the validated
proxy basket; |r|≈0.6 vote-basket family). Direction + magnitude reported with N; no other
endpoint may be promoted to primary after data exists.

☑ [SIGNED 2026-07-16] **Primary = town decision basket on the end-point A/B.**

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

☑ [SIGNED 2026-07-16] **N = 4×10 + 2×10 and the no-peeking stopping rule.** (Shrink to 3 generations if you
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

## 8. 2026-07-16 pre-launch revision (agent-drafted; supersedes conflicting lines above at signing)

**Owner decisions taken 2026-07-16 (recorded, not proposed):** town arm ONLY this run — the wolf/SK
arm is deferred to a later self-contained run (own OFF baseline, own epoch; nothing here compares
across runs). Budget reserve raised to $150; flash-lite-only unchanged.

**Two items the signature must resolve (from §3/§4 as drafted):**

- **End-point control.** §3 above says final store vs *baseline*; the plan of record's adopted design
  (plan §R / ladder note) is final store vs the *gen-1 store* — the contrast that isolates
  compounding from the static effect. Draft default for signing: **three conditions on shared
  boards — final vs gen-1 (PRIMARY) vs memory-OFF (secondary: "does the tells+SP channel help at
  all", a claim the obs-injection retirement makes new)** — at **20 boards per condition** (60
  endpoint games). Note the old static-memory result rode observation injection and does not carry.
- **Size.** Build 4 × 10 + 10 OFF (80 games ≈ $44–56 at the smoke-measured ~$0.50–0.56/ON-game) +
  endpoint 60 ≈ **$77–98 total**, well inside $150.

**Frozen-at-launch (re-stamp; the §6 2026-07-13 pin is superseded):**

- **Embedding model: `gemini-embedding-2` @1536 dims, Vertex, ADC** (quota-forced 2026-07-16: the
  new project caps `-001` at an unmodifiable 5 req/min; `-2`'s embedContent bucket is granted
  50/min). Alias canary **re-pinned** on `-2` same day (the documented legitimate re-pin: intentional
  model change; cold-start run owes no store rebuild). Absolute cosine knobs **percentile-remapped**
  to `-2`'s scale (check: 80 obs + 96 tell texts, per-text embeds, pair counts verified): retrieval
  `dedup_gate` 0.92→**0.87** (p96 preserved) · tell `PREFILTER_THRESHOLD` 0.80→**0.68** (p41
  preserved; top-3 cap unchanged) · synthesis clustering 0.70→**0.65** (never-binds preserved).
  Client workaround: a batch-collapse guard re-embeds per text when the installed langchain client
  returns one vector per batch under `-2` (logged when it fires); the offline batch-dedup default
  (legacy `-001` stores) is deliberately NOT remapped.
- **Two latent wiring fixes from the smoke campaign** (each with a regression test): the tell fold's
  default embedder now passes the shared store embedding model (first-ever live fold caught the
  missing argument), and `measure.game_score` drops `read_excluded` verdicts from sum AND count
  (mirroring credit_backfill — the two instruments stay on one de-luck semantics).
- **Smoke gate: PASSED 2026-07-16** — smoke #8 (`batch_results/v7_tells_smoke8/`, cold start, 1 gen
  × 2 games/arm, tells on, seed checklist 48/channel + v2 book): full tick end-to-end — games (arm
  guard + leak tests green) → merge 33 obs → credit (cold zeros) → mine 43 / detect 131 → **fold 1
  published checklist v1 (40 disc / 37 vote)** → book rebuilt (4 entries — the ledger-built book is
  thin at 2 games; ramps with support at run shape) → consolidate → generation score printed →
  loop_history written. Realized cost $1.01. Invariants all fail-loud and none fired.
- Suite **694**; runs launch as **systemd user units** (session-tethered processes die with the
  session — measured twice). **Git SHA at signing: `6ae7865`** (measure fix `38bb568` + embedding
  bundle `6ae7865` on `feature-dimension-schema`).

☑ [SIGNED 2026-07-16] **§8 as drafted** (endpoint = 3 conditions × 20 boards, final-vs-gen-1 primary; note any
modification inline).

---

**Owner signature**: SIGNED (owner, in-session)  **Date**: 2026-07-16
(Sign by replacing this line with "SIGNED <date>" and ticking every ☐ above; note any modification
inline next to its box.)
