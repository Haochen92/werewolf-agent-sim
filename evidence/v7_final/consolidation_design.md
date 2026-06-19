# v7 Consolidation (b) — design + the credit→consolidation (a→b) link

**Date:** 2026-06-19 · **Status:** DESIGNED, not built. (a) credit is built+validated
(`evaluation/src/experiments/credit_backfill.py`); this is the design for (b), the layer that *acts* on
(a)'s grades. b1 is free/deterministic; b2 (synthesis) is an LLM step (paid to run). Nothing here is
committed or run. This doc is the reference for building (b).

This refines the plan's one-line layer-4 bullet ("retrieval reads the utility to rank; decay / promote /
evict / recency window"). Two deltas from that line: (i) **"retrieval reads utility to rank" is PARKED**
(retrieval is the closed chapter per §1a) → (b) is **store-side**, not retrieval-side; soft-rank stays an
optional default-off companion. (ii) **recency window = deferred** (the rolling window covers it).

---

## 1. Mental model — (a) is the thermometer, (b) is the thermostat

(a) **measures** each strategy point's quality; (b) **acts** on the measurement. The **store is the shared
state** — (a) writes per-SP credit onto it, (b) reads exactly that credit. No other channel connects them.

```
   play games
      │  agents retrieve SPs, follow some
      │  (Agents/turn/adoption.py, LIVE: bumps follow_count / retrieved_count)
      ▼
  (a) CREDIT  ── for each FOLLOWED SP, join to the decision's DE-LUCKED PROXY outcome
      │         (score_vote / score_night_target — NOT game win/loss, NOT net_verdict)
      │         → write positive / neutral / negative_count
      │         → utility = shrunk LIFT vs the frozen memory-off baseline (§3)
      ▼
  (b) CONSOLIDATION  (every 5 games)
      │   b1  deterministic DROP of clear losers           (free, no LLM)
      │   b2  synthesis over the rolling window per faction (LLM, paid):
      │        keep winners · revise mediocre · discard dups · drop weak · generate new
      ▼
  updated store ──► next games retrieve it ──► (loop closes; content compounds)
```

---

## 2. What (a) produces (the credit signal (b) consumes)

- **Per-SP utility**, SP-only (observations ride frequency × criticality, not credit — you don't "follow"
  an observation).
- **Reward = de-lucked per-decision PROXY**, never the halo. Three things the word "outcome" can mean;
  only one is allowed: game win/loss ❌ (halo), `net_verdict` ❌ (halo), **de-lucked proxy ✅** (scores the
  *choice* against true roles, independent of whether the lynch/kill landed).
- Fills the long-empty `positive_count` / `neutral_count` / `negative_count` on `StoredStrategyPoint`
  (the follow/override side is already written live by adoption.py). Conservation:
  `positive + neutral + negative == follow_count`.
- **Coverage grows in stages**, bounded by what's scoreable: per-turn deterministic now (votes, night
  targets) → +cheap joins (investigator find→lynch, healer save) → +discussion/reveal class once (d) the
  tagger exists. ⚠ The schema docstring says "game outcome was scored positive" — **misleading; fix to
  "de-lucked decision proxy" when building** so nobody re-introduces the halo via the field name.

---

## 3. The baseline — two cases (contemporaneous in the experiment; frozen-table in production)

A note isn't "good" because its decisions came out positive — even no-memory play hits threats at some
base rate. So utility = **LIFT** = the note's outcome minus the **memory-off base rate of the same cell**.
The question is where that base rate comes from, and it differs by context:

- **Experiment / the loop run (the path we actually build) — CONTEMPORANEOUS, drift-free.** We co-run a
  **memory-off arm at the consolidation cadence (every 5 games, same epoch)** — it's already one of the
  loop's arms (off / ob-loop / ob+sp-loop, same-epoch concurrent launch). So each consolidation cycle
  grades against a *same-epoch* baseline. **Epoch drift is a non-issue by construction** — no frozen
  table needed. This is the real deliverable.

- **Production (later / optional) — FROZEN CALIBRATION TABLE, viability ∝ model stability.** You can't run
  a memory-off twin per production game (doubles cost), so you'd measure the per-cell base rate once, freeze
  it, and grade against it. ⚠ **This is only as reliable as the model is stable.** Epoch drift here is
  frequent — **for flash-lite it's ~daily**, so a frozen table goes stale almost immediately and would need
  recalibration at the drift cadence (≈daily) to stay meaningful; for a **more stable model** it holds far
  longer and the frozen-table approach is genuinely viable. So the frozen table is a *production fallback*
  whose usefulness scales with model choice — not the primary mechanism.

**Takeaway:** the loop experiment sidesteps the whole baseline-staleness problem via the same-epoch off-arm;
the frozen table only matters if/when consolidation is deployed in production, and there it's a
model-stability bet (fine for a stable model, fragile for flash-lite).

---

## 4. SP operations: keep / discard / drop / revise — **NO MERGE**

Merge is an **observation-only** operation, and here's why it doesn't transfer to strategy points:

- **Observation = evidence for a fact.** Two obs of the same fact under approach-variation → same lesson →
  **merge pools the evidence** (count++); the fact is unchanged, only confidence grows. Coherent.
- **Strategy = a directive.** "Merging" two directives is incoherent: same action → it's a **duplicate**
  (discard the worse-credited, keep one); different actions → averaging e.g. "lie" and "tell the truth"
  is nonsense. There is no evidence-pooling operation for an instruction.

So the SP op set is **{ keep, discard (exact dup — credit picks the survivor), drop (bad credit),
revise (single-SP refine) }**. The "two similar SPs" case = **discard-the-worse**, never fusion.

**Revise ≠ merge.** Revise regenerates ONE directive from (its old self + fresh window observations) — it
is synthesis *from evidence*, not combining two directives. "Is a revised strategy still the same
strategy?" → **identity = yes** (same key, `revised_at` stamp, old credit kept as a decaying prior, for
lineage/bookkeeping); **trust = re-earned** (the consolidation-driving score = lift over *post-revision*
follows). Identity preserved, quality reset.

---

## 5. The decision rule (simplified — one trigger, not four)

Driven entirely by (a)'s credit (utility = shrunk lift) + evidence (follow count):

| Band | Condition | Action |
|---|---|---|
| Winner | mature + high lift | **keep** (optionally promote) |
| Salvageable | mature + mediocre/mixed lift | **revise** (T1 — the one real trigger) |
| Loser | mature + clearly negative lift + high evidence | **drop** |
| Immature | too few follows | **wait** (accumulate; never act on thin evidence) |
| Un-creditable | discussion SP, pre-(d) | **abstain** (passthrough; never grade what you can't score) |
| Exact dup | same situation+action as a better-credited SP | **discard** the worse |

**⚠ §10 consistency pin (density guard).** §10a contains two things with opposite density needs — keep them
straight or §10 quietly re-adds what's cut here:
- **Aggregate weight-fit = ON** — regress a role's de-luck composite across ALL its decisions (hundreds of
  points) → per-role offense/defense weights. Pools the big pile → reliable. These weights **set the
  drop/revise thresholds below**.
- **Per-SP dimensional credit = OFF** — grading one SP on its offense-vs-defense (or any dimension)
  sub-reason slices ~3 follows into ~1 → noise. This is the **same subdivision as the cut T2**; §10a's
  "per-point credit grain = the `exposed→safe` transition" is that trap (also doubly blocked: discussion
  axis → needs (d) + many loop cycles).
- **One-line rule:** set general weights from the big pile (fine); score each SP as ONE number via those
  weights (fine); never grade a single SP on sub-reasons until it's been used enough to earn it (not soon).

**Cut as over-built (the data can't support them — median follows/SP = 3):** dimension-split revision
(needs dim-level credit; no power at 3 follows), "fresh-evidence" as a distinct trigger (that's just what
synthesis-from-window *does*), conflict-merge (that's dedup's job). **Deferred guards** (add only if the
loop shows churn): cap-revisions-per-cycle, drop-after-K-revisions. **Principle:** we can't validate any
trigger until the loop runs (paid) — build the simplest thing that closes the loop, let its real behavior
tell us what complexity to add.

**Gate-then-LLM (same pattern as dedup):** a cheap deterministic gate *selects* candidates
(maturity + lift band); the LLM synthesis only *acts* on those — it doesn't re-read the whole store.

---

## 6. b1 (free) vs b2 (paid)

- **b1 — deterministic pre-prune.** Drop SPs with `shrunk_lift < τ AND follow ≥ N`. Pure read of (a)'s
  ledger, no LLM, reuses dedup `delete()` + the created_at freeze-old guard. Builds + validates offline
  NOW. Becomes the first stage of the recurring consolidation pass.
- **b2 — credit-informed synthesis (the missing script, LLM/paid).** Every 5 games, rolling window per
  faction: keep/revise/discard/drop the survivors + generate new SPs from the window's observations.
  - **Synthesis source (open fork):** deduped **observations** (cheap, structured — lean) vs raw
    **transcript** (richer, many tokens). Observations-first, transcript as optional upgrade.
  - **Revise = revise-in-place** (preserve lineage + credit-as-prior; re-earn trust), per §4.

### 6a. b1 thresholds — what N and τ mean, and how they're derived

Two numbers gate the drop rule `shrunk_lift < τ AND follow ≥ N`:

- **N (follow floor) = how many times a note was used before its verdict is trusted** — a "don't convict
  on one witness" gate. Below N the lift is mostly noise. **Derived from the noise floor:** median follows
  per SP = 3, each follow scores ±1, so a 3-follow average is dominated by variance. The shrinkage
  (`lift × follow/(follow+5)`) already discounts thin notes; N is the hard floor where the estimate has
  settled. **N = 8** is the conservative choice (verdict is no longer noise) — read off the distribution,
  not a magic constant.
- **τ (lift threshold) = how much WORSE than no-memory a note must be before deletion**, in **lift units.**
  Each decision is scored +1 (good) / 0 (neutral) / −1 (bad); a note's **lift = (its mean score) −
  (the memory-off baseline for that cell)**. τ = −0.15 → "drop only notes that come out ≥0.15 worse than
  playing with no note at all." **Derived from "harmful beyond the noise band":** τ = 0 ("drop anything
  below baseline") is too aggressive — ~half of notes sit slightly below baseline from wash/noise and are
  *harmless* (b2 revises those); τ ≈ −0.15 is clearly outside the noise band for a mature note.
- ⚠ **These are PRAGMATIC, not statistical** (honest caveat). The rigorous version drops a note only if its
  lift's **confidence interval excludes 0** (we're actually confident it's harmful). Our sample sizes are
  too small for tight CIs, so a conservative fixed threshold — chosen where the sensitivity grid's drop set
  is small, stable, and only robust negatives — is the practical stand-in.
- **Chosen default (2026-06-19): N ≥ 8, τ ≤ −0.15** → 8 SPs (~1% of the 790-SP store), 298 follows
  prevented; catches the 79-follow net-loser; the highest mature-SP lift (+0.43) is far above the cut, so
  winners can't be caught. The borderline band (−0.15 … −0.05) is left for b2 to *revise*, not delete.

### 6b. Validating that pruning removes GENUINELY-bad content (not noise)

Deleting "the notes the metric disliked," measured on the same games, is circular. The free,
non-circular test is **held-out reproduction:** split the games, find losers on half A, and check they're
*still* negative on held-out half B (which never saw them flagged) + correlate lift_A vs lift_B. Positive
correlation / losers-stay-negative ⇒ the signal is real and stable ⇒ deletion justified. Flat ⇒ the
threshold is catching noise ⇒ back off before deleting. (`heldout_credit_reproduction.py`; baseline uses
the FULL memory-off data per the frozen-calibration design, only the follows are split.) The
*plays-better* proof remains paid/loop-time.

⭐ **HELD-OUT RESULT (2026-06-19, `heldout_credit_reproduction.py`, zero spend) — PASSES.** Split v6ab
games by game_id, lift computed per half (full-data baseline). **Pearson(lift_A, lift_B) = +0.54 (n=31,
p≈0.002)** → the credit signal reproduces across independent game sets (real, not noise). **A-flagged
losers (lift_A < −0.15) stay negative on held-out B: 8/9 = 89%** vs a 61% base negativity rate → the
loser flag adds discrimination. **The lone flip (−0.50→+0.04) had only 3 follows → vindicates the N≥8
floor** (well-evidenced losers at 12/28/29 follows all stayed firmly negative). Caveats: n=31 modest
(split thins sparse follows), r=+0.54 moderate-not-overwhelming (real-but-noisy on capped content), the
doubly-mature subset skews negative (hence the 61% base). Conclusion: **b1 at N≥8, τ≤−0.15 removes
stably-bad content, not noise → pruning justified.** plays-better still paid/loop.

---

## 7. End-to-end examples (real SPs from the (a) backfill)

| SP (the note) | (a) produces | (b) does |
|---|---|---|
| **Loser** — *"When a player puts mild suspicion on you in an info-starved spot…"* | 79 follows; raw +0.39, cell memory-off base ~+0.69 → **lift −0.30**; mature + clearly bad | **b1: DROP** (free). The store's *most-followed* note was below just-winging-it — killed without an LLM. |
| **Winner** — *"If you have credibility from a previous correct call…"* | 24 follows, almost all positive → **lift +0.31** | **b2: KEEP / promote.** Untouched — don't fix what works. |
| **Salvageable** — a mid SP, mature, **lift ≈ +0.04** | ~12 follows, mixed | **b2: REVISE (T1)** from the window; `revised_at` stamped, fresh maturation window, old credit = decaying prior. Re-earns credit; still weak after K → drop. |
| **Immature** — freshly-extracted, 2 follows | lift too noisy | **WAIT** — below maturity gate; re-enters later. |
| **Discussion SP** — *"Offer a counter-suspicion rather than just denying."* | followed in discussion, **no board outcome → (a) can't credit**; counters stay empty | **ABSTAIN** — untouched until **(d)** gives it a grade. |

Those six actions — keep / revise / drop / wait / abstain / discard — are the entire decision space.

---

## 8. The (d) dependency — "(b) complete" = (b) + (d)

The abstain row is the (d) gap made concrete: **every discussion SP sits ungoverned until the tagger
lands.** (b) converges the store for board-decision SPs, but discussion SPs accumulate unchecked. So
treat (d) as part of "(b) done," or reorder (d) before (b). (b) alone is also **whack-a-mole without (c)**
the extraction anchor — evicting a *common* bad lesson just lets it re-enter at the next extraction; (c)
stops re-entry at the source. (b) still helps (removes accumulated junk; re-entry is slower than
accumulation), but its value is partial until (c)+(d).

---

## 9. Validation (zero-spend where possible)

- **b1 mechanism + safety:** evicts exactly the flagged losers, keeps winners, never touches a high-lift /
  thin-evidence / frozen-old note (inspection + guard tests).
- **b1 free impact estimate:** Σ follows on evicted SPs = "bad-ish follows prevented" (the 79-loser = 79).
- **b2 face validity (cheap):** run one synthesis window — does it revise weak notes toward the window's
  evidence and drop the credit-losers, leaving winners alone?
- **Deferred (loop-time / paid):** "does the consolidated store *play* better" — the real proof; same
  ceiling as (a). Offline we validate the *policy* is sound + safe, not the outcome.

---

## 10. Open / deferred

- **Open forks:** synthesis source (observations vs transcript); recalibration cadence for the baseline
  table; exact τ / N thresholds (set on the ledger distribution).
- **Deferred:** recency/age-decay; dimension-split revision (T2); anti-churn guards; soft retrieval-rank
  companion (parked with retrieval).
- **Dependencies:** (c) extraction anchor (stops bad-lesson re-entry); (d) discussion tagger (unlocks
  discussion-SP credit → un-blocks the abstain set).
