# Consolidation walkthrough — experiment log

> Chronological record of the consolidation ownership review: the walkthrough of both compounding
> mechanisms (SP consolidation + tell fold), the probes it triggers, and the revisions it produces.
> Later entries supersede earlier ones. **Genre note:** this is a review-and-ruling log, not a
> build journey — every entry is an owner probe, the ruling it produced, the implementation, and a
> suite-count delta; it doubles as the changelog for [`report.md`](report.md). The steady-state
> mechanism lives in the report and its per-store docs (this log records only decisions and
> changes); the two mechanisms' *build* journeys predate this folder and stay in their original
> homes — the SP side across the execution plan's §0.4/§0.5 fixes
> (`../execution_plan/compounding_measurement_plan.md`) and the loop run records
> (`../v7_final/`), the tell side in `../extraction/tell_extraction/experiment_log.md` §10–§16.
> **Section-map note (2026-07-15):** the folder was renamed from `evidence/consolidation/` and the
> report restructured into a framework doc plus per-store docs
> (`observations.md` / `strategy_points.md` / `tells.md`). Report references in the entries below
> are to the report *as of 2026-07-14*: its old §2 (SP tick, incl. §2.1 obs decay) is now
> `strategy_points.md` + `observations.md`, its old §3 (tell tick) is now `tells.md`; §6 item
> numbers are unchanged and remain valid.

## 1. Motivation — one review for two mechanisms (2026-07-14)

The pre-run program (`compounding_measurement_plan.md` §R) gates the paid run on the owner
personally owning the two load-bearing pipeline stages that were agent-built: credit (closed — the
decision_scoring walkthrough, recorded in `../credit/report.md`) and **consolidation**. Two
rulings shaped the consolidation half before it started:

- **Format = walkthrough, not blind derivation** (owner, 2026-07-14). The plan's original wording
  called for a blind re-derivation (write the design without reading the code, then confront). The
  decision_scoring gate had already replaced that format with the faster teach-back — the agent
  presents the current pipeline, the owner probes and revises — and the owner ruled the
  consolidation gate follows the same format. The plan is stamped accordingly.
- **Scope = both compounding mechanisms** (owner, 2026-07-14). "Consolidation" in the codebase names
  only the SP tick (`loop/consolidate.py`); the tell ledger's compounding step is the epoch fold
  (`loop/tell_fold.py`), specced and simulated in the tell-extraction campaign but with no unified
  mechanism record. Since the run's thesis — stores that improve with play — rests on both ticks
  equally, the review covers both, and this folder is the single record for the pair.

## 2. Review basis authored (2026-07-14)

[`report.md`](report.md) written as the presentation document: both ticks step-by-step with the
reason for each step, the structural asymmetries that force two mechanisms (§4), verification
status (§5), and the open review points as the walkthrough agenda (§6). Two §6 items were *found
while writing* it, by reading the working tree rather than the design docs — the ledger design's
match-index retirement is not present in `fold()` (§6.3), and SP dedup is gated on synthesis
having added SPs, so a seed store must arrive pre-deduped (§6.4). Suite state at authoring: 655
green, uncommitted, `feature-dimension-schema`.

Next: the walkthrough itself (owner probes the report against the code); its catches, revisions,
and the SP-synthesis golden anchor points it is expected to produce land here as dated entries.

## 3. First ruling lands early — the book goes role-grain (2026-07-14)

Reviewing the report's §6.6, the owner ruled the role-revealing exclusion **out** (behavior→role
inference is the mechanism's point; the shared book is symmetric — wolves hunt, healers protect,
investigators learn to conceal) and extended the book to a role-identification manual for **every**
unrevealed role. Implementing it surfaced that the exclusion was doubly enforced: the book reused
credit's positive-evil-lift eligibility, which alone excluded town-power-role tells. Fix: book
selection re-based on subject-role concentration (`tell_credit.subject_lift`), credit's §6.5 rule
untouched, seed book rebuilt role-grain (`tell_book_v2_seed.json`, 34 entries, six roles). Suite
655 green. Full build detail: tell-extraction log §18; report §3.3/§6.6 updated in place; pre-reg
§5 rewritten as RULED (4 signature boxes remain).

## 4. Store-bounding review — three rulings, implemented (2026-07-14)

The owner probed whether the SP tick's cost stays bounded as the store grows: does synthesis
activity compound with observation count, and what bounds the two stores? Checking the report's §2
claims against the code surfaced that the §2.2 gates throttled only the paid LLM step, not the
clustering in front of it, plus two structural gaps:

- **Clustering ran before the gates.** Every synth tick fully clustered all 17 cells (one embedding
  search per obs) and only then evaluated admission — so a capped or quiet cell paid its whole
  clustering bill anyway, and the per-tick clustering cost scaled with total store size.
- **The reinforced core was immortal.** The age × frequency decay rule never dropped an obs with
  count ≥ 2, leaving the store's size — and with it the clustering cost — with no bound at all.
- **Discarded work by construction.** Every all-old cluster the new-clusters-only gate rejects was
  still being built before being thrown away.

Three rulings, all implemented and verified same day:

- **Count-scaled decay replaces age × frequency** — drop an obs once it goes
  `obs_evict_min_age × observation_count` generations without reinforcement; a count-1 obs behaves
  exactly as before, a reinforced one earns proportional grace but is no longer immortal. The named
  trade-off (an evicted reinforced obs re-enters as a count-1 singleton — store size traded for
  re-litigation) and the ruled fallback (per-cell size-restricted LRU, if a live run shows the
  scaled rule failing to bound the store) are recorded in report §2.1. The driver sidecar now
  tracks last-reinforced generation alongside first-seen (a reinforcement = a rise in
  `observation_count`); `obs_evict_max_count` is deleted as subsumed.
- **Gates run before clustering** — admission needs only keys, the sidecar, and the SP count, so a
  skipped cell pays zero embedding cost.
- **Clusters seed from new arrivals only** — old obs still join as neighbors; a depleted cell keeps
  full seeding for its replenish path. With this, per-tick clustering cost tracks the generation's
  inflow rather than the store.

Suite 655 → 666 green (new: count-scaled decay, sidecar stamping, gate-ordering, and
seeded-clustering tests; uncommitted, `feature-dimension-schema`). Report §2.1/§2.2 revised in
place. A fourth question from the same review — whether SP cells should adopt tell-style
proven/probation/new segments — was analyzed but not ruled; it enters the walkthrough agenda as
report §6.7.

## 5. §6.7 ruled same day — the two transferable lanes adopted (2026-07-14)

The owner ruled on §6.7 within hours of it entering the agenda: adopt the two pieces of the tell
lane structure that transfer to SPs, reject the two that don't (the rejection reasons in §6.7
stand unchanged). Both adopted pieces were implemented and verified the same day:

- **The synthesis cap gates the contested lane.** The per-cell ceiling stops counting proven SPs
  (same predicate as the prune exemption, now a shared helper so the two sites can't drift); knob
  renamed `synth_cell_sp_cap` → `synth_cell_unproven_cap`, value kept at 12 since the bloat record
  it anchors on was overwhelmingly unproven duplicates. This fixes both flat-cap failure modes at
  once: a cell full of proven SPs no longer stops exploring, and a full contested lane still blocks
  — more untested candidates would only dilute exploration, and the lane now has a drain (below).
- **A guaranteed exploration slot at retrieval.** At the per-situation cap (the one choke point
  every retrieval path passes), if all kept SPs are proven and the pool holds an unproven one, the
  best unproven candidate takes the lowest slot (`sp_exploration_slot`, default-on, plumbed and
  recorded like `sp_proven_tiering`). Injection stays ≤3 per situation. SP credit is usage-gated,
  so this is what lets a contested-lane candidate earn its way out — prove, sour, or evict.

Two notes for the record. The game-side proven predicate (follow ≥ 5 ∧ positives > negatives)
deliberately differs from the loop-side lift-based one — the read path has no base rates; both
sites now carry a comment saying so. And the exploration slot changes live-game retrieval
behavior, so it is an epoch-bundle member exactly like proven tiering (plan §0.4 stamped
accordingly).

Suite 666 → 676 green (new: contested-lane cap and exploration-slot tests). Report §2.2/§4/§6.7
updated in place; the §0.4 build stamp in the execution plan carries a dated addendum for the knob
rename.

## 6. The negative-record ledger consolidated into report §5 (2026-07-14)

Owner observation closing the store-bounding review: the v7 runs failed to prove the compounding
thesis, but they surfaced most of what is now known about store curation — and those findings had
no single home (bloat in config comments, the stall in the execution plan, dedup non-convergence
in `../dedup/`, this week's three in this log). Since this folder is the declared single record
for the compounding pair (§1), the inventory now lives in report §5 as an 11-row pathology →
surfaced-by → standing-guard table, replacing the prose list of four. The "surfaced by" column is
deliberate claim calibration: it separates what the *runs* demonstrated (bloat, ~6× re-synthesis,
the gen-6 stall, the harmful tail) from what design reviews and this week's store-bounding review
caught by reading the mechanism the runs motivated.

## 7. Fold-ownership review — §6.1 and §6.3 resolved, §6.2 checked (2026-07-14)

The owner probed the tell tick's semantics directly, and the session doubled as walkthrough
coverage of §3. Three clarifications worth recording, then the rulings.

**Clarifications folded into the report.** (a) The three-artifact distinction — ledger (append-only
event rows) vs canon (identity registry) vs checklist (the bounded published card) — was the
review's main confusion point and is now the §3 orientation. (b) Probing "why can't the fold be
keep/discard only, like SP dedup?", the owner independently re-derived the shipped design: the
fold's per-wording op set IS {keep, discard}, and merge/split of existing canonicals belongs to the
evidence-ratified audit. Recorded as ownership evidence for the D2 gate. (c) The §6.1 failure modes
are not exotic operations but the two ways a binary verdict goes wrong (wrong DISCARD = stats
blend; wrong KEEP = fragmentation) — which sharpened the tripwire from a fuzzy continuity idea into
two deterministic invariants.

**§6.1 ruled and built — the publication tripwire.** Always-on, no LLM, no knob: (1) monotone
detected support against the state-carried `last_n` of the previous publication (catches a
`roles_by_game` join silently dropping older games' rows); (2) head continuity — a top incumbent
leaves only via this fold's explicit null-lift verdict. Trips raise before anything persists;
appended instance rows remain (the ledger records what happened, the tripwire gates curation). One
implementation deviation, accepted: `last_n` is scoped to incumbents at persist time and the head
derives from state rather than being re-filtered against fold-time canon status — this makes the
head tamper-immune (an external canon edit cannot hide from it) and stops legitimately-archived
tells from re-tripping later folds.

**§6.2 checked at zero spend.** The review ranked `prune_tau` as the only threshold that could
plausibly flip a run conclusion; its held-out reproduction ran same day
(`heldout_credit_reproduction`, v6ab archive): Pearson(lift_A, lift_B) = +0.54 (n = 31), A-flagged
losers stayed negative on the held-out half 8/9 vs a 61% base rate, the one flip at 3 follows —
below the run's ≥8 floor (all 4 flagged SPs at ≥8 follows stayed negative). Direction-credible at
small n: pruning cuts reproducible signal. The prefilter (0.80/top-3) stays uncalibrated as a
tracked limitation — the sim data to calibrate it exists, but a replay harness is a new instrument
and the owner's closing rule is no new complications pre-run.

**§6.3 ruled and built — the bounded match index.** Owner chose a hard cap over the ledger design's
unseen-based retirement ("easy to build, easy to explain"): the fuzzy stage consults incumbents +
30 newest probation + 10 most-recently-scanned archive entries per channel (~65 candidates, flat as
the singleton tail grows); exact-match stays global; retirement from matching is never deletion —
recurrence re-enters as probation and the audit reunites, with tallies recomputed from rows. The
snapshot candidate list also removes a latent crash (the old live-reference list could grow mid-loop
past the precomputed embedding array). Window sizes 30/10 are design-anchored, tracked in §6.3.

**§6.4 resolution path.** The pre-reg is silent on the SP store's starting state; it must pin it at
signing — cold start (as both v2 smokes) closes the item by construction; a seeded store gets one
report-only batch-dedup pass first.

Suite 676 → 684 green (new: tripwire and bounded-index tests). Report §3/§5/§6.1/§6.2/§6.3/§6.4 and
the status header updated in place. §6 agenda now open: §6.2's prefilter limitation (tracked),
§6.4's signing-time pin, §6.5's post-run readout.
