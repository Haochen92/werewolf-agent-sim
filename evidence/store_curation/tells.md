# The tell store — ledger, canon, checklist, and the injected book

> **Scope:** the per-store mechanism doc for tells, under the framework in [`report.md`](report.md)
> (its cross-cutting principles are cited by number). A tell is a falsifiable behavior→role fact —
> "a player who is accused counter-accuses their accuser of using the role claim as a distraction"
> (evil 27/30, shrunk lift +0.49) — credited **off-policy**: every exhibitor in every game counts,
> whether or not anyone read the book. The curation tick is the **epoch fold**
> (`evaluation/src/loop/tell_fold.py`); pricing is `tell_credit.py`; mining/detection is
> `tells.py`. The design record with its rejected alternatives is
> [`../credit/read_tactic_credit_redesign.md`](../credit/read_tactic_credit_redesign.md) §3; the
> mining/detection instrument's build journey is
> [`../extraction/tell_extraction/experiment_log.md`](../extraction/tell_extraction/experiment_log.md).
> **Status:** split out of the parent report 2026-07-15; mechanism as of the 2026-07-14
> fold-ownership review (log §7; suite 684 green, uncommitted, `feature-dimension-schema`).

**Role and consumers.** Tells are the read layer's knowledge base: behavior→role statistics that
let any agent turn observed behavior into role inference. Written by per-game **mining** (an
omniscient pass over the public record that discovers candidate wordings) and **detection** (a
role-blind pass that scans each game against the frozen checklist — the only rows that feed
credit, because a miner that has read the whole game is halo-exposed). Read by every agent via the
injected **book** (§6). Because a tell's evidence is counted over *stored games*, tells need no
retrieval exploration machinery — candidates mature uninjected (report §4).

## 0. The tell lifecycle, end to end (the generation graph)

A tell's life runs on two clocks. Something happens in *every game*, and curation happens once per
*fold* — one fold per generation at the run's shape (this batching is what "epoch-quantized" in §2
means). Reading top to bottom is one full turn:

> **mine + detect** *(inside every game, against the frozen checklist v_k)* → **fold** *(after the
> generation's games: resolve wordings, append rows, rule verdicts, publish checklist v(k+1))* →
> **build the book** *(for the next generation)* → **mine + detect** *(next generation)*

Concretely, per generation the driver's tell tick runs (`driver.py::_tell_tick`):

1. **Mine + detect** (`tells.py`) — during each game, an omniscient **mining** pass discovers
   candidate wordings and a role-blind **detection** pass scans the game against the frozen
   checklist v_k. Only detected rows feed credit; mining has read the whole game, so it is
   halo-exposed.
2. **Fold** (`tell_fold.fold`) — after the generation's games, the single curation step: resolve the
   epoch's new wordings against the canon, append instance rows to the ledger, advance the probation
   clock, rule verdicts, and publish the next checklist v(k+1). Its five sub-steps are §3.
3. **Build the book** (`tell_credit.build_book_file`) — assemble the role-identification manual from
   the ledger, ready to inject into the next generation's games (§6).

That is the whole per-generation tick: mine + detect, fold, rebuild book. A fourth step is
*designed but not wired* — a periodic strong-model **audit** that would re-examine existing
canonicals for merges and splits (§3). The fold only *flags* candidates for it (the split-check
verdict, §3 step 4); the audit itself is never called from the loop and exists today only as a
one-shot offline screen (`granularity_screen.py`). So in-run, splits are flagged and deferred, never
applied.

So detection runs continuously but always against a *frozen* card, while every curation decision is
batched into the fold. §1 introduces the three data artifacts the fold moves data between; §3 is the
fold in detail; §6 is the book that closes the loop.

## 1. Three artifacts, one per job

The fold's main confusion point at the ownership review, so it leads here. All three are plain JSON
the fold reads and writes directly — there is **no ORM or Pydantic model** for them (the Pydantic
schemas in the pipeline are only the LLM I/O shapes: the mining and detection outputs, and the dedup
judge's verdict).

The **ledger** (`instances.jsonl`) is the append-only event log, one JSON row per instance, never
edited. It holds **two kinds of row**, tagged by `source_kind`: **MINED** rows (from the omniscient
discovery pass — used only to grow the canon, never to price) and **DETECTED** rows (from the
role-blind detector — the *only* rows lift is computed from). Every tally is recomputed from these
rows each fold; nothing is accumulated.

The **canon** (`canon.json`) is the identity registry: every canonical tell ever admitted, each a
row of `{tell_id, channel, text, status, born_fold, games_scanned, last_scanned_fold, split_check}`,
status one of incumbent / probation / archive. It stores *identity and status, not counts* — n and
lift live nowhere on disk; they are re-derived from the ledger each fold. A canon entry is born
**only** when a mined wording fails to resolve to any existing entry (§3 step 1); detected rows never
mint identities (they can only reference tells already on the checklist).

The **checklist** (`checklist_v{k}.json`) is the bounded published subset of the canon (≤48 per
channel) that detection actively scans games for. **Do not confuse it with the *match index* of §3
step 1** — that is a *different* bounded slice of the canon (~65 per channel, different composition)
used for a different job (comparing a new wording against known ones). §5 tabulates both.

So the canon gives instances somewhere to be filed, the ledger gives canon entries their evidence,
and the checklist is the active-duty roster drawn from the canon at each fold.

## 2. The two principles the fold is built on

**Curatorial, never generative.** A tell's meaning lives in its *extension* — which transcript
moments count as instances — so canonical text is **never rewritten**. A newly mined wording either
*dies into* an existing canonical (its instances credit the survivor; the wording is dropped at the
door) or becomes a new canonical on probation. Rewriting text would break denominator continuity
for every already-detected count; wording repair belongs to the periodic strong-model audit, not
the fold. This is the mirror image of SP dedup's "never merge" rule, for the mirror-image reason
(report §2.3, principle 2): an SP's meaning is its directive text, a tell's meaning is its
instance set.

**Epoch-quantized.** Detection always runs against a **frozen checklist v_k**; curation happens
only at the fold (one per generation — at the run shape of 10 games/generation, the ledger design's
N=10 cadence), and a strong-model audit is meant to run every ~3 epochs (designed, not yet wired —
§0). An online per-game dedup pass existed
and was retired (2026-07-12): it was the pipeline's most expensive component (178 LLM calls/game)
AND its least accurate — incremental one-at-a-time judging fragmented the head 2× (one bandwagon
tell split 18+11+10 across three canonicals). Tells have no same-game consumer (unlike memory that
must reach the next prompt), so a ≤10-game consolidation delay costs nothing.

## 3. What one fold does

1. **Resolve the epoch's new wordings** against the same-channel canon, cheapest test first
   (principle 3): normalized exact-match (free, global over the whole canon) → embedding prefilter
   (top-3 candidates at cosine ≥ 0.80 — the embedding only *nominates*, never judges) → a strict
   extensional LLM judge ("same tell iff a transcript reader would count the SAME moments as
   instances of both; a sub-type with a distinct mechanism is NOT the same"). Unresolved wordings
   become new canonicals on probation.

   The fuzzy stages consult a **bounded match index** — a slice of the canon distinct from the
   published checklist (a different slice for a different job; §1), not the whole canon. The index is
   three slices per channel: all incumbents (already bounded by the verdict cycle), the 30 most
   recent probation entries, and the 10 most recently scanned archive entries — roughly 65 candidates
   in total, and flat as the singleton tail grows. *(This is the §6.3 ruling of 2026-07-14: a hard cap,
   chosen over the ledger design's unseen-based retirement because it is easy to build and easy to
   explain.)*

   Retirement from the *match index* is not deletion. Exact-match still runs globally, so an
   identical wording can never mint a duplicate identity; the canon and ledger keep everything; and a
   wording whose true match has fallen out of the index re-enters as a new probation canonical, which
   the audit could later reunite (once wired — §0). Because tallies recompute from rows, nothing is
   permanently lost.
   (Snapshotting the candidate list also removed a latent crash: the old live-reference list could
   grow mid-loop past the precomputed embedding array.)
2. **Append instance rows** to the ledger. All tallies **recompute from rows** on every fold (set,
   not accumulate — principle 5), so a curation mistake never bakes into a counter. MINED rows are
   discovery only; **lift is computed from DETECTED rows exclusively** — mined rows come from a
   halo-exposed pass, detector rows from the role-blind instrument.
3. **Advance the probation clock** in *scanned games* — games whose detection ran with this tell on
   the checklist. Scanning is what gives a tell any chance to be detected, so the window counts
   *opportunities* (scans), not *hits*: a tell that was rarely scanned hasn't failed, it just wasn't
   tried — the clock measures opportunity, not outcome.
4. **Rule verdicts.** A probation tell still a singleton (≤ 1 detected instance) after
   `K_PROBATION = 12` scanned games → archive (an evidence-*volume* cut, direction-neutral). An incumbent with fat support (n ≥ 20)
   and null lift (|shrunk lift| < 0.03) → archive **with `split_check` set true**. The fold does no
   splitting itself — it only writes the boolean. A null blend can hide two directional sub-tells,
   and *determining* the split (re-partitioning the tell's instance rows and recomputing each
   sub-tell's lift from the ledger) is the audit's job; since the audit is not yet wired into the
   loop (§0), `split_check` is at present a durable to-do marker, not an applied operation. The one
   forbidden move: never *retain-rank* by lift at thin support — that selects on noise (the probe's
   cleanest town tell began as a lift≈0 singleton).
5. **Publish checklist v_{k+1}**: per channel, up to 25 incumbents ranked by |shrunk lift| under a
   **direction-balanced quota** (evil-leaning and town-leaning both surface — every role's book
   needs candidates), all live probation (newest first, capped at 15), and spare slots up to the
   48-cap rotated to the **least-recently-scanned archive entries** — a zero-marginal-cost
   re-trial (just another scan, *not* the strong-model audit), so every archived tell eventually
   re-earns or re-fails on fresh counts.

**Granularity is settled operationally**, outside the fold's per-epoch loop: two same-channel tells
are THE SAME iff same instances AND same lift — semantics propose a merge, pooled-lift arithmetic
ratifies it (a bad merge shows as visible lift dilution). Merging or splitting *existing*
canonicals is never a fold operation; it belongs to the periodic strong-model audit, on that
evidence — an audit not yet part of the running loop (it exists as the one-shot offline
`granularity_screen.py` that produced these findings; wiring it, or its cadence, is open — §8). The
one forbidden fold direction: never merge a discriminating child into a ~0-lift
generic parent (the granularity screen found seven such hierarchy pairs, e.g. a ~0-lift generic
vote tell containing a +0.21 child).

## 4. The publication tripwire

*(§6.1 ruling, built 2026-07-14 — always-on, no LLM, no knob.)* The fold is the critical path: a
bad fold publishes a bad checklist and detection runs against it for a whole epoch with no
in-epoch correction. Two deterministic invariants gate persistence and publication.

**Monotone detected support.** The fold keeps no running counters: every fold it *recounts* every
tell's support from scratch by re-reading the whole instance ledger (deliberate — principle 5).
That recount has one dependency: each row says "player X, game 41," and tallying it requires
looking up game 41's roles in the `roles_by_game` map the fold is handed. If that map is ever
missing an older game (a driver bug, a truncated file), every row from that game silently drops
out of the recount — no error, the tally just shrinks, and the checklist would publish from wrong
numbers. The invariant exploits the one thing that cannot legitimately happen: the ledger is
append-only, so a tell's count can only rise between folds. Each fold saves its counts in
`state.json`, and the next fold asserts new ≥ saved for every tell; any decrease means rows were
lost, and the fold crashes loudly instead of publishing quietly-wrong numbers. (Receipt-box
intuition: every receipt is kept forever and totals are recounted monthly from the box — if this
month's recount of January is *lower* than last month's recount of January, you didn't spend less,
you lost receipts.)

**Head continuity.** The handful of tells doing the most detection work must not silently
disappear from the card: a top-support incumbent may leave only via this fold's *explicit*
null-lift verdict; any other exit means curation diverged from the fold's own rulings.

On violation the fold raises before any *curation* persists (canon status, the recomputed counts,
the published checklist). The appended instance rows are written first, in step 2, so they stay on
disk — the ledger records what happened, and only curation is gated; a halted fold loses no evidence
and re-runs after the fix. One accepted implementation
deviation: the saved counts are scoped to incumbents at persist time and the head derives from
state rather than being re-filtered against fold-time canon status — this makes the head
tamper-immune (an external canon edit cannot hide from it) and stops legitimately-archived tells
from re-tripping later folds. Residual, tracked at report §6.1: wrong keep/discard verdicts at the
single-wording grain remain possible; the tripwire catches their *systematic* form, and the
(still-unwired) audit is the intended semantic backstop.

## 5. Bounding — three caps, three surfaces

The tell side carries two of the system's three population caps; the disambiguation (each bounds a
different surface):

| Cap | Side | What it bounds |
|---|---|---|
| `synth_cell_unproven_cap = 12` | SP (`strategy_points.md` §2) | how many *unproven* SPs a cell may hold before synthesis stops adding |
| Checklist cap (48/channel, §3 step 5) | Tell | how many tells the *detector scans games for* each epoch |
| Match-index cap (~65/channel, §3 step 1) | Tell | how many known tells a *new wording is compared against* at the fold |

Why the checklist cap is THE tell-side cost control: mining keeps discovering ~16 genuinely new
singleton wordings per game with no saturation in sight (open vocabulary at move grain — report
§5), so anything that scales with the *corpus* eventually drowns. In complexity terms, detection is
O(players × channels × views) model calls per game — 2 channels × 2 views (the k=2 union) — with the
≤48-entry checklist carried in context (prefix-cached); wording resolution is one batched embedding
plus ≤3 judge calls per new wording (the top-3 prefilter) against the ≤65-entry match index. Both
are flat as the canon grows; the store itself is never capped (rows and identities are
cheap and recomputable). The epoch quantization (§2) bounds the
third surface — curation frequency. The append-only ledger still grows by design: inert during
play, but the fold-time recompute-from-rows scan is linear in total history (trivial at run scale;
snapshotting is the fix if it ever matters).

## 6. The injected book

The book is built from the ledger at fold time (`tell_credit.build_book`), not retrieved per turn.
It is a **role-identification manual for every unrevealed role** (owner ruling 2026-07-14, which
removed the draft role-revealing exclusion: behavior→role inference is the mechanism's point, and
the shared book is symmetric — the same information lets wolves hunt an investigator, the healer
protect one, and the investigator learn to conceal). Selection is per (subject role, channel): the
top ~3 tells by **subject-role concentration** (`subject_lift` — the subject's shrunk share of
exhibitors over its cast prior) above a support floor of 8.

**The same-behavior collapse** (`make_book_collapse`, `tell_book_dedup` default on, built 2026-07-16).
The 3-slot budget has a sharp exposure: the unwired audit's fragmentation (§8) lets one behavior
persist as several canonicals, and because selection ranks by `subject_lift`, the fragments of a
*popular* discriminating behavior are exactly the high-lift, high-support rows the book pulls in — so
two or three of a role's three slots can end up saying the same thing. To catch this at the point of
injection, `build_book` runs the fold's **own** cascade (embedding prefilter → the extensional-
equivalence judge, §3 step 1) over each (subject role, channel) candidate pool *before* the cut,
collapses same-behavior fragments into one entry, and lets the freed slots backfill with distinct
behaviors. The guardrail is structural, not a knob: candidates are lift-sorted, so the survivor of a
class is always its highest-lift member — the only rows ever dropped are lift-equivalent to a kept
one, so diversity can never cost lift.

This is a **symptom fix, not the cure, and deliberately scoped as one.** It is *view-layer*: it runs
on the book candidates only, touches neither canon nor ledger, and — because credit is computed from
the ledger independently of book membership (see the divergence below) — a collapsed fragment keeps
its identity, stays scanned, and **keeps paying credit**. What it does *not* do is pool the fragments'
evidence: each still carries its own partial-support lift, so the credit side stays fragmented. Pooling
into one accurate lift (and one identity) is the audit's canon merge (§0), still the real cure; this
only stops the injection budget being spent twice on one behavior. *(Rationale record: report §6; the
fragmentation risk it addresses is §8 gap 5.)*

Note the deliberate divergence from credit: credit pays **positive evil-lift** tells only (a
town-marker read backwards double-counts, and "look town" credit is farmable — credit report §6.5),
but a town-power-role tell with *negative* evil-lift still belongs in the book. What pays and what
informs are different questions — an investigator tell injects, and never pays.

At render time (`Agents/memory/tell_book.py`) the only logic is a roles-alive filter — a
wolf-marker is dead weight once both wolves are revealed dead. Arm gating is by environment
(`WW_TELL_BOOK` = path to the book; absent ⇒ empty block, which IS the baseline behavior). The
book is public information — behavior statistics from past games' *revealed* roles — so it needs
no role gating or leak check; every seat may read it. The launch seed is `tell_book_v2_seed.json`
(34 entries, all six roles; built by the preserved
`../extraction/tell_extraction/scripts/build_seed_book.py`).

In v7 the book is also what *supersedes* observation injection: the prompt's learned-knowledge
channels are the book (facts) and retrieved SPs (directives); observations stay behind the scenes
as synthesis substrate (report §6.8 tracks the wiring gap on this).

## 7. Verification specific to this store

The simulation-before-code record is summarized at report §5 (the 30-game ledger sim, batch
consolidation №1, the granularity screen); the instrument-side verification — detector golden
(k=2 union: disc 0.93 precision / 87% day-recall, vote 0.77/77%, N=40, direction-grade), the
held-out lift table (12 paired boards × 5 arms), and the owner-golden g1 round — lives in the
tell-extraction log (§13–§16), because it verifies the *instrument*, not the fold. What no test
has yet exercised: a fold inside a live generation loop (the `--tells` smoke is the queued next
step), and the v2 role-grain book is unscreened (report §6.6 residual).

## 8. Gaps and open points (2026-07-15)

Criticality-ordered; agenda items live at report §6 and are not repeated.

1. **No live fold yet** — everything above is offline replay on the v6ab archive, one epoch old;
   the `--tells` smoke must show the fold's counters and the tripwire passing inside a real
   generation.
2. **v2 book unscreened; minimum-strength floor undecided** (report §6.6): the injection-channel
   screen was run on the v1 wolf+SK book; the v2 tail entries (vigilante/healer at +0.03–0.06
   lift) are near-prior.
3. **Prefilter 0.80/top-3 uncalibrated** (report §6.2 tracked limitation) and the 30/10
   match-index windows unswept (report §6.3) — both design-anchored, pinned in the pre-reg.
4. **Probation-lane pressure beyond 30 games unmeasured** (report §6.5): the 15-slot lane is
   permanently contested under open vocabulary; rotation/starvation behavior is a post-run
   readout.
5. **The merge/split audit is unwired.** The fold flags null-lift incumbents (`split_check`) and
   never rewrites text, both on the premise that a periodic strong-model audit will later apply the
   merges and splits — but that audit is not called from the loop; it exists only as the one-shot
   offline `granularity_screen.py`. Until it is wired (or run between generations by hand), splits
   are flagged and deferred and `split_check` accumulates on archived tells unread.

   The failure mode over a ≤10-generation run is **fragmentation, not corruption.** The never-destroy
   invariants (freeze-text, recompute-from-rows, archive-not-delete) and the §4 tripwire hold with or
   without the audit, so no published count is ever wrong — but the fold can only *add* identities and
   coarsely *archive* them, never *re-grain*, so grain drifts monotonically toward over-fragmentation
   with no counter-force. Concretely: (a) near-dup probation singletons the fold's judge missed crowd
   the newest-first 15-slot lane, pushing older honest probation tells off the checklist, where they
   stop being scanned and stall below K=12 for as long as the lane stays oversubscribed (compounds
   gap 4 below); (b) a `split_check` archival that is really two directional sub-tells stays merged and
   semi-retired — a real discriminator becomes a standing measurement blind spot (a false-negative on
   signal, the one cost worse than clutter). Nothing published is wrong; the store is just messier and
   some real tells never mature.

   **Partly mitigated at the injection point** (`tell_book_dedup`, 2026-07-16 — §6): the book now
   collapses same-behavior fragments before the 3-slot cut, so failure mode (a)'s worst consequence —
   a role's manual repeating one behavior across its slots — no longer reaches the prompt. This is a
   *symptom fix only*: it is view-layer, does not pool the fragments' evidence, and leaves the
   credit-side fragmentation and the lane starvation untouched. The audit is still the cure. *(Raised
   2026-07-16.)*
6. **Lifecycle verdicts barely fire within the run horizon.** The tell lifecycle is slow relative to
   a ≤10-generation run: probation→archive needs `K_PROBATION = 12` scanned games (§3 step 4), so
   across ~10 folds most probation tells never resolve. The tell store is better off than the other
   two on *size* — the checklist's 48/channel cap is a hard bound that binds regardless of
   generation count (§5) — but the canon and probation lane still grow near-monotonically in-run, and
   whether the lifecycle reaches a steady state at this fold cadence is unestimated. Post-run
   readout. *(Raised 2026-07-15.)*
