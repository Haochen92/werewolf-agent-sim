# Consolidation walkthrough — experiment log

> Chronological record of the consolidation ownership review: the walkthrough of both compounding
> mechanisms (SP consolidation + tell fold), the probes it triggers, and the revisions it produces.
> Later entries supersede earlier ones. **Genre note:** this is a review-and-ruling log, not a
> build journey — every entry is an owner probe, the ruling it produced, the implementation, and a
> suite-count delta; it doubles as the changelog for [`report.md`](report.md). The steady-state
> mechanism lives in the report and its per-store docs (this log records only decisions and
> changes); the two mechanisms' *build* journeys predate this folder and stay in their original
> homes — the SP side across the execution plan's §0.4/§0.5 fixes
> (`../memory_system/v7/execution_plan/report.md`) and the loop run records
> (`../memory_system/v7/`), the tell side in `../extraction/tell_extraction/experiment_log.md` (version at `2382b34c`) §10–§16.
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

## 8. §6.8 wired — the loop stops injecting observations (2026-07-15)

Restructuring this folder surfaced a wiring gap and it became the eighth agenda item: the v7 design
retires observation injection (prompts carry tells + SPs; obs are synthesis substrate only), but a
code-read of the working tree showed the run path did not enforce it. `--retrieval-types` defaults
to `both` (`scripts/run_batch.py`), the loop driver launched games with only `--configs` plus the
tell-book env and never passed the flag, and the retrieval pipeline still rendered observations into
prompts — so a run launched as wired would silently have been an obs+SP+tells arm, a plausible wrong
arm with no error (the same failure shape as the v2 arm slip §6 keeps guarding against).

**Owner ruling (same day): the design stands, fix the wiring.** No re-litigation of whether obs
should be injected — they should not; the item is purely that the default arm must match the design.

**Built.** A new `LoopConfig.retrieval_types` knob (default `strategy_points_only`, so the loop
cannot inherit run_batch's `both` default); the driver appends `--retrieval-types <cfg>` to every
game launch (both arms — symmetric and harmless on the OFF arm, which retrieves nothing regardless);
and a per-generation fail-loud invariant, `assert_observations_retired`, that checks two existing
record surfaces — the recorded per-game `retrieval_types_config["observations"]` (what the engine
ran with) and every memory-enabled ON decision's `retrieved_observations` eval-case slot (what
actually reached the prompt) — no new capture plumbing needed. `"both"` reproduces the v5/v6 obs+SP injection for a
comparison arm. The `tell_book.py` module docstring was sharpened to say the retirement is enforced
by that config default, not by the retrieval layer (which still supports obs injection for the
comparison arms). Two notes stand: this is an epoch-bundle member (it changes generation behavior),
and the v5/v6 static-memory rungs that used obs injection are unaffected — a v7 arm-definition item,
not a retraction.

Suite 684 → 690 green (new: the SP-only default, the driver flag, and the assertion's config +
prompt-input trips). Report §6.8 flipped to RESOLVED (+ the two inline §6.8 mentions and the status
header), `observations.md` §1 and its §6 gap 1 updated. §6 agenda now open: §6.2's prefilter
limitation (tracked), §6.4's signing-time pin, §6.5's post-run readout.

---

## 9. The walkthrough agenda moves here from the report (2026-10-26)

The report was rewritten on 2026-10-26 as a reference for today's two passes. Its §6, the agenda of the
2026-07-14 ownership walkthrough, is log material and moves here whole, with its item numbers, because
code comments, the v7 plan and this log cite them as "report §6.N". Its status block and its three
example records move with it.

**The report's status as of 2026-07-16.** First written 2026-07-14 (as `evidence/consolidation/report.md`),
revised the same day across three review sessions (entries 4–7); restructured 2026-07-15 (folder renamed
to `store_curation/`, per-store detail split out). Suite 684 green at the 07-14 review, 690 after entry 8,
692 after item 9 below; uncommitted, `feature-dimension-schema`. Of the agenda, still open then: §6.2's
tracked prefilter limitation, §6.4's signing-time pin, §6.5's post-run readout. Its verification section
also recorded, then: no fold had yet run inside a live generation loop, and everything cited was offline
replay on the v6ab archive, one epoch old. (The July learning run later ran four folds; see the report's
v7 section.)

**The three example records the report quoted (2026-07-14).**

- An observation from the v2 smoke run's store, `observation_count: 2` (the same lesson arrived twice):
  *situation:* "Day 1, an information-starved opening where you established a baseline of being a
  helpful, cautious voice …" → *approach:* "You advocated for a measured pace on Day 1 to delay any
  momentum against you and discourage early investigation." → *outcome:* "Positive; successfully
  steered the village away from identifying an early target, preserving your anonymity."
- A strategy point from a smoke-run store, trimmed: *situation:* "Healer is operating during day
  discussion … Stakes: maintaining your status as an unexposed power role is more valuable than pushing
  a specific lynch early …" → *action:* (a directive the agent may follow), with counters
  `follow_count / positive_count / negative_count`.
- A tell from the v1 seed book, `tell_id: disc_530`: "A player who is being accused of holding a hostile
  role counter-accuses their accuser of using the role claim as a distraction to protect themselves." —
  evil 27/30, shrunk lift +0.49.

**The agenda, as it stood on 2026-07-16.** Ordered by criticality. Items 1–7 were the 2026-07-14 review
agenda; their numbering is frozen. New items append; existing items never renumber.

1. **RESOLVED 2026-07-14 — the fold publication tripwire is built** (ruled and built same day; entry 7).
   The fold is the critical path — a bad fold publishes a bad checklist that detection runs against for
   a whole epoch with no in-epoch correction. Two always-on deterministic invariants now gate persistence
   and publication: monotone detected support (a recount may never shrink — shrinkage means ledger rows
   were silently lost) and head continuity (a top incumbent leaves only via this fold's explicit
   null-lift verdict). Mechanism: `tells.md` §4. Residual, tracked: wrong keep/discard verdicts at the
   single-wording grain remain possible; the tripwire catches their *systematic* form, and the periodic
   audit stays the semantic backstop.
2. **Threshold provenance is mixed — top-ranked knob now checked, rest pinned.** Evidence-anchored: the
   SP cap (bloat record), the credit window (density calculation). Design-anchored, never swept:
   `prune_tau = −0.15`, the three follow/retrieve floors (8/8/2), `K_PROBATION = 12`, the null-lift cut
   (0.03 at n≥20), the prefilter (0.80/top-3), the checklist caps (25/15/48). The review ranked
   `prune_tau` as the only knob that could plausibly flip a run conclusion: every generation the loop
   *deletes* SPs whose lift falls below τ, and the compounding story assumes those deletions remove
   genuinely bad directives — if lift at that threshold were mostly noise, pruning would be deleting
   near-randomly, good SPs included. The held-out check ran 2026-07-14 (`heldout_credit_reproduction`,
   zero spend; method and full numbers: `strategy_points.md` §6): Pearson(lift_A, lift_B) = +0.54 at
   n = 31, A-flagged losers stayed negative on the held-out half 8/9 against a 61% base rate, and the one
   flip sat below the prune rule's ≥8-follow floor. Direction-credible at small n: the prune rule cuts
   reproducible signal, not noise. Tracked limitation: the tell-side prefilter (0.80/top-3) remains
   uncalibrated — the data to calibrate it exists (the 30-game sim's resolved rows), but a replay harness
   is a new instrument and the closing rule is no new complications pre-run. The remaining knobs are
   pinned as design-anchored in the pre-reg, with a post-run sensitivity readout. *(2026-07-15: the
   complete per-knob inventory — value, provenance class, validation status, and the pinning policy's
   rationale — is now [`knobs.md`](knobs.md).)*
3. **RESOLVED 2026-07-14 — the fuzzy match index is bounded** (owner ruling: a simple hard cap over the
   ledger design's unseen-based retirement, "easy to build, easy to explain"; built and suite-verified
   same day, entry 7). Wording resolution now consults ~65 candidates per channel, flat as the singleton
   tail grows; retirement from *matching* is not deletion. Mechanism and the three-cap disambiguation:
   `tells.md` §3/§5. Tracked limitations: the 30/10 window sizes are design-anchored (unswept); the
   fold-time recompute-from-rows scan is linear in total history (trivial at run scale; snapshotting is
   the fix if it ever matters).
4. **SP dedup only runs when synthesis added SPs** (`cfg.sp_dedup and syn.get("added")`). A seeded store's
   pre-existing near-duplicates are never collapsed in-loop — the run's seed store must arrive already
   deduped. *Resolution path (2026-07-14):* the pre-reg is silent on the SP store's starting state and
   must pin it at signing. Cold start (as both v2 smokes) closes this by construction; a seeded store gets
   one report-only batch-dedup pass first.
5. **Probation pressure under open vocabulary.** The sim's funnel was healthy at 30 games, but the flat
   singleton inflow means the 15-slot probation lane is permanently contested; beyond 30 games the
   rotation/starvation behaviour is unmeasured. Post-run readout, not a blocker.
6. **RESOLVED 2026-07-14 — the role-revealing exclusion is removed** (owner ruling, pre-reg §5 records
   it): the book is a role-identification manual for every unrevealed role, selection re-based on
   subject-role concentration, launch seed rebuilt (`tell_book_v2_seed.json`, 34 entries, all six roles).
   Mechanism: `tells.md` §6. Residual for the walkthrough: the injection-channel screen (27.5% changed,
   direction positive) was measured on the v1 wolf+SK-only book — the v2 book is unscreened, and its
   weakest tail entries (vigilante/healer at lift +0.03–0.06) are near-prior; whether the book needs a
   minimum-strength floor is a fair probe.
7. **RESOLVED 2026-07-14 — SP cells adopt the two tell-style lane pieces that transfer** (owner ruling,
   same day it was raised; entry 5): the synthesis cap re-scoped to the contested lane, and a guaranteed
   exploration slot at the retrieval cap. Rejected, reasons standing: archive-with-rotation (an archived
   SP would need paid retrieval slots to re-earn; the obs store already serves as the SP's archive, since
   deletion plus re-synthesis is the SP-native re-audit path) and a probation deadline (a
   generation-based clock would kill rare-situation SPs). Mechanism and residuals: `strategy_points.md` §5.
8. **RESOLVED 2026-07-15 — the v7 obs-injection retirement is now wired into the run path** (found while
   restructuring this folder, ruled and built the same day; entry 8). The design stands (prompts carry
   tells + SPs; observations are synthesis substrate only) and the wiring now enforces it: a new
   `LoopConfig.retrieval_types` knob defaults to `strategy_points_only`, the loop driver passes
   `--retrieval-types` to every game (both arms), and a per-generation invariant
   (`assert_observations_retired`) fails loud on two record surfaces — the recorded per-game
   `retrieval_types_config["observations"]` and every memory-enabled ON decision's recorded
   `retrieved_observations` slot — so an obs+SP arm can never launch silently under the SP-only default.
   `"both"` reproduces the v5/v6 obs+SP injection for a comparison arm. Mechanism: `observations.md` §1.
   Two notes, unchanged: pulling observations out of prompts changes generation behaviour, so it stays in
   the same epoch bundle as the other prompt-affecting changes; and the static-memory claim rungs that
   used obs injection (v5/v6 arms) are unaffected — this was a v7 arm-definition item, not a retraction.
9. **NEW 2026-07-16 — the book collapses same-behaviour fragments at injection** (`tell_book_dedup`,
   default on; found while cold-reading `tells.md`, ruled, built and suite-verified the same day). The
   book seats only ~3 tells per (subject role, channel), and the unwired merge/split audit's
   fragmentation (`tells.md` §8 gap 5) reaches the prompt with a sharp geometry: selection ranks by
   `subject_lift`, so the fragments of a *popular* discriminating behaviour are precisely the high-lift,
   high-support rows the book preferentially pulls in — two or three of a role's three slots can repeat
   one behaviour, collapsing the manual to a single signal where it intended several. `build_book` now
   runs the fold's own embedding+judge cascade (§3 step 1) over each candidate pool before the cut,
   keeping the highest-lift member of each same-behaviour class so freed slots backfill with distinct
   behaviours. Guardrail is structural: candidates are lift-sorted, so only lift-equivalent rows are ever
   dropped — diversity never costs lift. Mechanism: `tells.md` §6; suite 692 (+2). Deliberately scoped as
   a **symptom fix, not the cure**: it is view-layer (canon, ledger, and credit untouched — a collapsed
   fragment keeps its identity, stays scanned, keeps paying credit), and it does *not* pool the
   fragments' evidence, so the credit side stays fragmented across partial-support lifts. Pooling into
   one accurate lift and one identity is the audit's canon merge (still unwired), which remains the real
   fix; this only stops the injection budget being spent twice on one behaviour.

**What became of the agenda.** The July v7 run started from an empty lesson store, which closed item 4
for that run. Item 2's tracked prefilter limitation and item 5 were never read out: the memory research
closed on 2026-07-21, and the tell side did not graduate. Item 4's rule is still in today's learning
tick; the published ten-seat store had its duplicate groups removed by review before publishing.
