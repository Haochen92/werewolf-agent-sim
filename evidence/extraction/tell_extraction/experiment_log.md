# The Tell Ledger — Build Journey

> **What this is.** The chronological record of building the **tell system** — the pipeline that mines
> recurring, publicly-observable behavior patterns ("tells") from finished games, organizes them into a
> bounded store, and counts how often each role actually exhibits them. It runs from the first mining
> prompt through the dedup experiments, a 30-game lifecycle simulation, the design amendment the simulation
> forced, the detector build and its goldens, to the pipeline's graduation into the loop (§17). Later entries supersede earlier ones; where the design changed, the
> change is shown *in its place* rather than edited away — the point is the journey, including the parts the
> data overruled.
>
> **Companion docs.** The final design, destination-first, is in [`report.md`](report.md). What a tell is
> *for* — the credit redesign that makes accuracy-counted facts the currency — is the design record at
> [`../../discussion_tagger/read_tactic_credit_redesign.md`](../../discussion_tagger/read_tactic_credit_redesign.md)
> §3, and the run this gates is planned in
> [`../../execution_plan/compounding_measurement_plan.md`](../../execution_plan/compounding_measurement_plan.md)
> §R. Guiding principle: **the miner surfaces candidates; the counting decides what they mean** — we build
> detectors here, never judges.

---

## 1. Motivation — facts you can count, and why the prompt is the risky part

A **tell** is a behavior visible at the table: "when accused, votes for their accuser." The ledger turns
such patterns into *facts with error bars*: count who exhibits each across many games, join exhibitors'
roles once the game reveals them, and ask whether the behavior lands on evil players more (or less) often
than a random cast-pick would. That comparison against the cast's base rate is the tell's **lift** — the
only thing that says what a behavior *means*. No model is asked "does this suggest a wolf?"; the count
answers it.

That concentrates the risk in mining. Everything downstream is arithmetic, which does not degrade quietly.
But if a mined description is role-inferential ("defends their packmate"), unfalsifiable ("plays
suspiciously"), or this game's plot in general words, the ledger counts noise with perfect precision. So
the probe iterates the mining prompt against real games until its failure modes are bounded, before any
store-facing run depends on it. Two constraints are fixed by the design record and not re-argued here:
**descriptions must be observable behavior, objectively described** (a role-blind detector and the live
player prompt both read them, and neither can check a claim requiring a hidden role); and **the miner emits
no direction** ("this suggests wolf" is banned — direction is decided later by lift, and a miner that
assigns meaning is a judge importing the outcome-halo bias this redesign removes).

---

## 2. Decisions before the first call

Each was settled by reasoning before any API call, with a "because" that mattered later:

- **One call per game-day, not per game** — the day is the coherent behavioral unit, and cheap-model
  attention degrades with input length (direct evidence in this repo). Prior days' public record rides
  along as context, so cross-day patterns stay reachable.
- **The miner sees the public record only — by construction, not instruction.** Night actions and private
  reasoning are absent from its input, so a table-invisible behavior *cannot* be mined; an instruction can
  be ignored, an absent input cannot. (A true-roles header is included — mining may be omniscient, counting
  is not.)
- **The model names the exhibitor's `player_id`, never their role** — the behavior→role join is a
  deterministic lookup; letting a model transcribe roles buys only error.
- **Every mined entry carries a verbatim evidence quote** — the anti-confabulation anchor every later human
  review verifies against.
- **Don't over-police generality.** A too-broad tell is self-punishing (its lift collapses to zero and the
  math discards it); the real enemy is the *over-specific* tell wrapped around this game's storyline, which
  bloats the store before support starvation can kill it. So the prompt asks only for "a pattern that could
  recur."
- **The in-sample halo, named before it bites.** An omniscient miner over-notices behaviors fitting the
  roles it sees, so lift on the mined games is biased upward. Remedy, pre-registered: mine on one slice,
  count on a held-out slice.
- **Probe on the production model** — `get_llm_pro()` (gemini-2.5-pro); a prompt validated on a cheaper
  model is one the real pass never runs. (The cheap model's shot comes later — §6–7.)
- **Deterministic screens check structure only** — regex verifies no role words, no player IDs,
  quote-in-record; objectivity, generality, and motive-freedom are semantic, judged by reading.

Scaffolding: [`scripts/tell_mining_probe.py`](scripts/tell_mining_probe.py), prompts frozen per iteration
in [`prompt_versions/`](prompt_versions/), outputs in `outputs/` as JSONL rows `{game_id, day, exhibitor,
behavior, evidence_quote, exhibitor_role, screen_flags, prompt_version}`.

---

## 3. v1 — first contact (5 games, 25 day-calls, 177 tells)

Prompt [`prompt_versions/v1.txt`](prompt_versions/v1.txt): an analyst persona in the house extraction style.

**What held immediately.** Zero role-word and zero player-ID violations across 177 descriptions — the
leak-critical rules cost nothing to enforce. The exhibitor spread is healthy (villagers largest, 28 of the
91 rows read), which the base-rate math needs: a miner surfacing only evil behaviors could never show a
behavior *fails* to discriminate. Several candidates are the discriminative move-types hoped for, lifted
verbatim from `outputs/mining_v1.jsonl`:

> "Casts a solitary vote for a player when all other players vote to abstain." (a wolf, day 2)
>
> "Votes for the player the room has already converged on without having voiced any suspicion of them
> during discussion." — the blend-vote pattern, surfaced unprompted.

**The first thing to debug was the instrument, not the model.** The run reported 54 of 177 quotes (30%) as
not-found. Re-screening after normalizing unicode punctuation and stripping edge ellipses dropped that to
11 of 177 (6%): most "failures" were the screen comparing smart quotes against straight quotes. *Catches: a
brand-new screen is an uncalibrated instrument — check its false-positive rate before believing its number.*

**Three real defects:**

1. **Spliced quotes (~6% after fair screening)** — the model stitches non-adjacent sentences or elides with
   "…". Fix: one contiguous verbatim span, never splice.
2. **Motive attribution (~2 per 91 rows read)** — "Announces being the target of a failed night attack **to
   establish credibility**"; the purpose clause is inference. The edge: *reported* motive is fine ("claims
   their vote was meant to break a deadlock"); only miner-authored purpose clauses are banned. A sweep found
   5 suspects of which 3 were legitimate reported speech — low but nonzero. Fix: a carve-out rule plus a BAD
   example from the failure.
3. **Episode re-descriptions (a handful per game)** — general phrasing wrapped around this game's plot,
   near-zero recurrence, pure bloat. Fix: a grain rule — describe the *move type*; if the description needs
   the storyline, generalize or skip.

**Decide:** all three fixes are prompt-side; the screen normalizer ships with the probe. → v2.

---

## 4. v2 — the three fixes land (same 5 games, 184 tells)

Prompt [`prompt_versions/v2.txt`](prompt_versions/v2.txt) adds the contiguous-quote rule, reported-speech
carve-out, and move-type grain rule, each anchored by a BAD example from v1.

**Verified with the same instruments.** Quote defects fell 6% → 1%, and the 26 quotes still containing "…"
all match verbatim (players' own ellipses) — splicing stopped rather than the screen loosening. The
motive-clause sweep found 6 hits, all inside reported speech: the carve-out working. Episode re-descriptions
gone. Leak rules still 0-for-184. Yield ~7 tells per day-call.

**One early positive for the counting path.** Unprompted, the model converges on *identical wording* for
recurring patterns — one phrasing appears verbatim for four exhibitors across games (22 of 184 rows in
exact-wording duplicate groups). Exact matching is free, so every merge it catches is one the paid semantic
judge never risks.

**Decide: v2 is the review candidate.** Signals that would reopen the prompt: the owner's review, the dedup
stage (if wordings prove unmergeable), the held-out detector pass (if behaviors prove undetectable
role-blind).

---

## 5. v3 — the owner points at the epistemic rule, and it exposes a double defect

The owner pointed at the standing `EPISTEMIC_STATUS_RULE` (`Agents/prompts/standards.py`) — the certainty
spectrum the strategy prompts already use: *own knowledge → system-confirmed → claimed-with-evidence →
claimed → unknown*. Reading v1/v2 against it showed the flat "no role words" rule was wrong in **both
directions at once**:

- **Under-blocked.** v1 produced "justifies a past vote against a now-confirmed **ally**" and v2 three
  counts of "a now-revealed **valuable player**" — hidden-relationship claims whose truth requires an
  *unrevealed* role, so a role-blind detector cannot verify them, yet the role-word regex never fired
  because "ally" and "valuable" aren't role words.
- **Over-blocked.** Death reveals and public role claims sit at certainty levels 2–4 (public, checkable),
  and reacting-to-a-reveal and role-claiming are classic tell families; the blanket ban silently suppressed
  the whole family — v1 and v2 contain not one claim- or reveal-conditioned tell.

*Catches: a flat lexical ban is the wrong shape for an epistemic constraint — what matters is the certainty
level the sentence asserts, not the word. The codebase already had the right rule; the prompt should have
inherited it.*

**v3** ([`prompt_versions/v3.txt`](prompt_versions/v3.txt)): role/faction words allowed *only* with an
explicit public-certainty marker ("revealed on death as…", "a player claiming to be…"); bare role
attribution stays banned; hidden-relationship words banned by name, the v1 "ally" failure as the BAD
example. Screens updated to match. **Verified (same 5 games, 181 tells):** zero bare-role and zero
hidden-relation flags, quote flags 1.6%, yield stable. The unlocked family materialized — seven
certainty-marked tells, all epistemically sound, including "publicly claims to be the investigator," the
game's most classic tell, invisible to v1 and v2.

**Decide: v3 supersedes v2 as the review candidate.**

---

## 6. Can a cheaper model carry the sweep? (the budget forcing function)

Mining a large corpus on 2.5-pro projects to ~$15–30, too large a share of the remaining budget. So a
screen: same v3 prompt, 5 games, screens; only the model changed (one backend throughout — the house rule
that scores are never compared across backends).

| | 2.5-pro (reference) | 3.5-flash | flash-lite 3.1 |
|---|---|---|---|
| tells | 181 (7.2/call) | 103 (4.1/call) | 116 (4.6/call) |
| leak-class flags | **0** | 4 | 3 |
| quote flags | 3 | 0 | 1 |
| exact-wording convergence (rows in duplicate groups) | **24** | 3 | **0** |

The yield drop and leak flags are arguable (several cheap flags read as borderline reported speech). The
disqualifying line is the last: **wording convergence collapsed to zero.** Pro reuses the same sentence for
a pattern unprompted; flash-lite never does. Convergence is what lets free exact-matching catch recurrence
before the paid semantic judge runs — a flash-lite corpus would be 100% judge-dependent, and every merge
pushed onto a judge is added wrong-merge exposure.

**Decide: mine on pro, ration by corpus size instead of model quality** — bootstrap ~60 games (~$8–10),
defer the rest. The cheap model's real shot is the *detector* (binary matching is far easier than
open-ended mining), where a golden set will measure whether it clears the bar. *(Superseded within a day.)*

---

## 7. v4 — the owner's channel split rescues flash-lite (and the budget)

The owner proposed attacking §6's failure *mechanism*, not paying around it. Flash-lite's missing discussion
tells looked like attention anchoring on the compact, structured vote block. So **split the day into two
focused flash-lite calls**, discussion-layer and vote-layer. Temporally principled: the discussion call
omits the focus day's vote block (nothing anachronistic to anchor on); the vote call keeps the full day
because the strongest vote tells are cross-channel ("votes for the room's target *without having voiced*
suspicion" is unreadable without the discussion). Free by-product: every tell now carries a `channel` tag, a
hard partition downstream.

**Verified (v4 split on flash-lite, same 5 games, 50 calls, 213 tells):**

| | pro single (ref) | flash-lite single | **flash-lite split (v4)** |
|---|---|---|---|
| tells | 181 | 116 | **213** |
| leak-class flags | 0 | 3 | 1 (0.5%) |
| quote flags | 3 | 1 | 4 (1.9%) |
| convergence rows | 24 | 0 | **19** |
| the §6 gap case (game-1 day-2 discussion tells) | 4 | **0** | **3**, mapping onto pro's finds |

The coverage gap closed, total yield now *exceeds* pro's single pass, and convergence recovered from zero to
19: focusing each call stabilizes the pattern vocabulary. Honest residuals: an occasional miner-authored
motive clause still slips (~1–2%), and the vote prompt's named example families may bias against novel vote
patterns — noise the dedup and read tiers absorb, not corpus poison.

**Decide: the mining design is v4-split on flash-lite** — a full sweep now costs ~$2–3 instead of $15–30,
and §6's pro-on-60-games plan is superseded, budget returned to the run reserve. *Catches: when a cheap
model fails a task, first ask whether the task can be reshaped to remove the failure mechanism. The model
was never the binding constraint — the input layout was.*

---

## 8. Dedup v0 — how the corpus collapses (run before paying for any sweep)

The owner redirected the sequencing: before mining more games, show how the *existing* corpus consolidates.
The store's history with observations and strategy points says volume-before-dedup-control is how stores
rot, and the dedup dynamics were the un-derisked part.

**Scope rules decide what "duplicate" means.** Tell dedup is **global within a channel, never partitioned by
role**: lift needs the same behavior's exhibitors counted across *all* roles, so a role partition would
split numerator from denominator and silence the refutation channel (the villager exhibitors that prove a
vague tell means nothing). Channel (vote vs discussion) *is* a hard partition — a vote tell references cast
votes by construction, so a cross-channel merge is a category error.

**v0, TF-IDF prefilter: near-zero collapse — and the prefilter, not the judge, was the bottleneck.** 202
distinct wordings produced only 10 candidate pairs and 3 merges, while the manual read already knew ~14
votes-own-accuser variants sat in the corpus. At tell length paraphrases share almost no tokens, so lexical
cosine sees nothing. *Catches: the house cosine-is-not-a-judge rule bites one level earlier than expected —
at this length, lexical cosine is not even a usable prefilter.*

**v0.1, production embeddings: real collapse, and a scale surprise.** The similarity scale is heavily
compressed — the *median* vote-channel pair sits at 0.84, the 99th percentile at 0.93 — so an absolute
threshold is meaningless (0.80 admitted 2,837 "candidate" pairs). With a cap of 400 judged pairs per channel
as the filter: 213 rows collapsed to 166 canonical tells, 44 merges, the clusters the right ones. A read of
all 44 found one questionable case (~2%), from an ambiguous pronoun, not judge over-eagerness. Under-merge —
true paraphrase pairs the cap never examined — is the real residual, and a running theme.

**Decide:** (1) the prefilter moves from absolute-threshold to **rank-based top-k neighbors** (on a
compressed scale only ranks carry information); (2) ambiguous voter/target wordings are a known
manual-repair class; (3) whether growth converges is unanswerable at 5 games — the next increment is more
games plus a re-dedup, and that curve, not fiat, sets the sweep size.

---

## 9. The distinctness audit — how much of 166 earns its existence

The owner's challenge: 166 canonical tells from *five games* smells like bloat. Method: one strong-model
reviewer per channel over every canonical (rubric: merge / episode / trivial / vague / keep), then an
independent verification pass over every vote merge, every drop verdict, and a sample of discussion merges.

**The reviewers were verified before their counts were trusted** — vote merges ~17/20 clean (including a
subtle mirror pair correctly kept apart: accuser-votes-target vs target-votes-accuser), discussion ~90%
agreement. **Two verdicts were overturned on principle.** The reviewer ruled accuse-then-vote TRIVIAL "because
it's baseline follow-through." Wrong here: **commonness is the base-rate math's job, not the ontology's.** A
universal behavior dies of lift collapse honestly on its own, and this one is demonstrably non-universal
(zero of its six exhibitors were evil — a town-leaning tell is as useful as an evil-leaning one). TRIVIAL is
reserved for literal non-choices that cannot be counted. *Catches: a delegated reviewer imports the "boring =
useless" rule; a counting architecture makes boring self-punishing, so the ontology should only drop what
cannot be counted.*

**The accounting:** 166 canonicals → **107 keepers**, 45 further merges (the capped judge's recall gap, now
closed by review), 14 drops. About a third was bloat — the owner's smell right in direction, though the
majority survives. Two-thirds of keepers are single-instance hypotheses, what five games *should* produce.
The head was already coherent (five games, in-sample, direction only): votes-own-accuser at n=18 with 9 evil
exhibitors against a 1-in-3 prior; accuse-then-vote and abstain-despite-arguing both town-leaning at 0 evil.

**Design consequences:** (1) the 45 recall-merges size the gap the top-k prefilter must close; (2) the
detector cannot be per-tell — at 107+ tells that explodes, so it scans a *checklist* per player-game, making
calls scale with games not corpus; (3) periodic strong-model distinctness audits ARE the batch pass of the
house dedup architecture, and this was the first.

---

## 10. The ledger simulation — 30 games through the spec (2026-07-12)

By now the design record had a full ledger spec: a three-tier store (bounded detector-scanned **checklist**,
unbounded **archive**, small injected **book**), drop-or-keep dedup at ingest, an admission queue with a
time-to-live, probation verdicts after K scanned games, and re-entry from archive on recurrence. Before
trusting any of it the whole lifecycle was simulated: 25 more games mined (v4-split flash-lite, quality flags
stable ~2.7%), then all 30 games' 1,109 mined instances replayed in order through the spec. Honesty label:
no detector exists yet, so "support" here means *mined recurrence*, standing in for detected counts — good
for the plumbing, meaningless for tell validity.

**Finding 1 — the vocabulary does not saturate.** Fresh tells arrived ~43/game early, then flat ~22/game
through games 21–30, 740 total canonicals at game 30, no downward trend. **There is no "mine it all"
endpoint, so the bulk mining sweep died as a concept.** Mining is a standing per-game pass, and the bounded
checklist is *the* mechanism that makes an open vocabulary affordable.

**Finding 2 — the head concentrates, but the online judge fragments it.** The top tell sat at n=18, with the
*same tell* in two other wordings at n=11 and n=10 the capped pairwise judge never united. Consolidated,
true head tells run n≈30–40 over 30 games, roughly **twice what any single wording shows** — so batch
consolidation directly determines whether head tells reach creditable support.

**Finding 3 — the funnel behaves.** The admission queue is a rolling ~150-entry window (TTL works, no
explosion); probation absorbs ~12% of inflow; everything else ages to the archive unscanned (recoverable,
and re-entry fired repeatedly). Tier occupancy at game 30: 40 incumbents / 30 probation / 168 queued / 502
archived.

**Finding 4 — cost, against the owner's constraint (everything standing must be flash-lite).** The dedup
judge ran 5,350 calls over 30 games ≈ 178/game; all-in standing cost estimated at $0.02–0.03 per game, 100%
flash-lite. *(Corrected 2026-07-13, §14: the per-call unit cost was ~6× low against actual billing. The
dedup-judge share stays small — two-sentence prompts — but the detector share re-prices to ~$0.20+/game.)*

---

## 11. Batch consolidation №1 — is the linear growth real? (2026-07-12, $0 API)

The owner challenged Finding 1: extrapolated, 22 fresh tells/game × 100 games is over 2,000 — *"I find it
hard to believe there are genuinely so many noticeably distinct tells."* Two rivals, opposite consequences:
(a) the vocabulary really is open-ended at this grain, or (b) online dedup recall degrades as the store grows
— a new wording is only compared against its top-5 embedding neighbors, and the one true match among 700
candidates is harder to find than among 100, so "fresh" increasingly means "missed merge." The store owed
itself a batch consolidation anyway, so the pass doubled as the experiment.

**Method.** Per-channel clustering by strong-model (Opus) subagents, run Claude-side off the API budget,
under the extensional-equivalence rule ("the same tell only if a reader scanning a transcript would count the
same moments as instances of both") plus §9's calibration. The re-measurement needed **no API calls**: tell
IDs encode creation order and the simulation records fresh-per-game, so each cluster's "would-have-been-fresh"
game reconstructs from its earliest member.

*Catches:*

1. **Part of the "under-merge" was a simulation bug.** 24 of the 740 canonicals were *literally identical
   strings* — same-wording rows in the same game batch each created a new tell, because the ingest loop never
   re-checked the exact-match index it had just updated. Fixed in `ledger_sim.py`; about a fifth of the vote
   channel's redundancy was this leak, not judge recall.
2. **The two channels are genuinely different, not differently judged.** Vote: 291 → 181 canonicals, 38%
   redundant, where the retaliation-vote family alone spanned 27 wordings whose consolidated support ≈69 makes
   it the store's №1 tell. Discussion: 449 → 414, only 8% redundant, 48 borderline pairs conservatively left
   split. My verification found one wrong inclusion (excised as a coded override) — the strong model's error
   rate stayed at the §9 level, one or two per ~60 verdicts.
3. **The verdict splits the difference, and the split is the finding.** After consolidation (740 → 596) the
   fresh rate is *still* flat ~16/game — so growth is not a dedup-recall artifact; the vocabulary really is
   open-ended. **But the share of newly-born tells that ever recur collapses by cohort: 37% for games 1–10,
   19% for 11–20, 11% for 21–25.** The *recurring* vocabulary converges (the head was essentially discovered
   in the first ~15 games); the flat inflow is a tail of one-offs. Both intuitions were right: the store grows
   forever, and there are *not* thousands of real tells.

**Decisions.** Finding 1 re-scoped, not retracted: "no saturation" is true of the tail, false of the core,
and the tiered design already handles that shape. `outputs/consolidated_store.json` (596 canonicals) becomes
the reference canon; the detector's checklist seeds from it, not the raw store.

---

## 12. The design amendment — online dedup retired, the ledger goes epoch-quantized (2026-07-12)

The owner drew the conclusion §10–11 set up: if the batch pass is both *required* (Finding 2) and *better*
(§11 repaired what online judging fragmented), why run an online LLM judge at all? Proposal: dedup only in
batch, every N games, folding new tells into the frozen old. Adopted, because the simulation's data made the
case on three axes — **cost** (the online judge was ~178 of the ~204 per-game calls, the single most
expensive standing component); **accuracy** (it was also the *least* accurate judgment — pairwise,
cheap-model, top-5 neighborhood — and under-merged the head 2× that the batch pass then repaired anyway, so
the system paid the most for its worst judgment); and **latency** (nothing time-critical consumes its output;
observations keep their online KEEP/DISCARD pass because they inject into the *next* prompt, but a tell's only
consumer is the checklist, and a ≤10-game entry delay is immaterial against a 12-game probation window and an
n≥20 evidence floor).

**The amended lifecycle:** per game, only mining, free exact-match accumulation, and the detector against a
**frozen checklist v_k**. Every **N=10 games, the fold** — the LLM dedup folds the epoch's new wordings into
the frozen canon (proven text is never rewritten, which keeps accumulated counts valid across versions),
tallies recompute, probation and admissions run, checklist v_k+1 publishes. Every **~30 games, the audit** —
the strong-model pass of §11. Frozen per-epoch checklists are a measurement win: stable denominators,
versioned artifacts, comparable games. Named trade-off: the fold moves onto the critical path — skip it and
the checklist goes stale and new vocabulary stops entering; accepted because the pass is cheap and
schedulable. Store-size control is three-layered — the checklist cap bounds attention and credit, the fold
and audit bound head fragmentation, and retiring long-unseen singletons from the *comparison index only*
(rows are never deleted) bounds dedup recall rot. The store itself is never capped.

---

## 13. The detector — role-blind counts, and a temporary golden to aim it (2026-07-12)

Mining produces discovery; the **detector** produces the only counts lift may use. It is the miner's mirror:
role-blind and exhaustive, so every non-detection is recorded and rates become computable. The golden's
status, plainly: the owner sanctioned a **temporary** golden for direction (strong-LLM adjudication plus my
transcript review), with the owner's own detector-blind adjudication remaining the run-gating check before
any credit ships.

**Build.** [`scripts/detector_probe.py`](scripts/detector_probe.py): one flash-lite call per (game, player,
channel), temperature 0, carrying the public record and the frozen channel checklist, **no true-roles
header** — role-blind by the same guarantee-by-absence as the miner. Checklist v0 = the top 48 per channel
from the consolidated canon. Every completed scan is a denominator row. First run: 5 games, 90 scans, 317
detections, quote-flag rate 4%.

**The temporary golden, independence preserved.** 40 stratified cells — 20 detector positives across
channels/tells/games, 20 zero-detection cells on head tells — adjudicated by five Opus agents (one per game),
each given the role-blind transcript and the cases *without* the detector's answers (anchoring a judge on the
system under test buys fake agreement). I read every disagreement: 10 of 40 disagreed, and I ratified all 10
adjudicator verdicts with zero overrides.

*Catches:*

1. **The first version's failure modes split cleanly.** Precision decent (discussion 10/11, vote 7/10); every
   vote false-positive was a relation-clause miss (voting the accused after questioning the accuser is not
   "votes the accuser"). Recall weak (54% vote / 67% discussion at day grain), clustered in multi-day exhibits
   and absence-defined tells (behaviors made of *not* speaking — silent-then-abstain).
2. **The second version fixed what it aimed at and broke what it wasn't looking at.** A day-by-day scan, a
   relation-clause rule, and an absence pass took vote precision 0.70 → 1.00 and recovered the silent-abstain
   miss — while discussion recall *fell*. The two versions agreed on only 39% of rows. The finding is not that
   either beat the other: **single-pass cheap-model detection is unstable, and prompt iteration reshuffles the
   instability instead of shrinking it.**
3. **A union of passes buys the recall back.** The two versions' union scored 77% / 73% day-recall at 0.77 /
   0.85 precision — the cheap ensemble fix, ~36 calls/game. *(Cost corrected 2026-07-13: ~$0.22/game at
   observed billing, not the "one or two cents" first quoted.)*
4. **The "noise" turned out deterministic — and the owner's channel-split instinct fixed the one systematic
   miss.** The detectors already split at the call level; what didn't split was the *view* — both read the
   identical full transcript. A third variant gave the discussion calls a vote-tally-stripped record (lynch
   outcomes and night announcements kept). (a) Its vote calls were byte-identical inputs to v2's and produced
   row-identical outputs — read at the time as **"temperature-0 flash-lite is fully deterministic."**
   *(Corrected 2026-07-13, caching log §⑤a: that 1.00 was real but lucky — repeated identical uncached runs
   self-agree at 0.90–1.00, occasionally exact, so the endpoint is NEAR-deterministic, and the earlier
   disagreement was still overwhelmingly prompt/view sensitivity with a small serving-side flicker floor
   underneath.)* (b) The stripped view recovered the one cell no full-view pass had found — a three-day
   records-over-reads exhibit the compact tally block had stolen attention from — and lifted single-pass
   discussion precision 0.75 → 0.90. Best union (full-view ∪ split-view): **discussion 0.93 precision / 87%
   day-recall with zero missed negative cells; vote 0.77 / 77%.**

**Decisions.** (1) Detection policy candidate for v1: **a union of two deterministic passes, one full-view,
one split-view** (~36 flash-lite calls/game, ~$0.22/game at observed billing, corrected 2026-07-13 from an
initial 1–2¢ quote; uncached and at thinking_level=low, both reducible); revisit the pass count after the
owner's golden. (2) The golden's honesty bounds, on record: 40 cells is direction-grade, and positives were
sampled *from the first version's own detections*, so it is flattered by construction. (3) The one cell no
pass finds, and borderline day-boundary cases, go to the owner's detector-blind adjudication round — the gate
that certifies, where this golden only aims.

---

## 14. The held-out pass — provisional lift, and the first per-role signatures (2026-07-12)

With the policy chosen, the owner called the held-out pass: run the k=2 union over games the tells were never
mined from, producing the first lift table — provisional until the golden certifies, but with held-out games
and complete denominators the previews lacked. The split fell out cleanly: the mined 30 games were exactly
the baseline arm of the v6ab batch, so the five memory arms (150 games) are all held-out — and the *right*
measurement population, since credit runs on memory-on games. Sampled 12 games per arm (60 games, 2,160
flash-lite calls).

**Cost correction (2026-07-13, owner-reported billing): this run cost $13, not the quoted $1.50–2.50.**
Measured input volume was as assumed (~8k tokens/call, ~17M total), so the miss was unit-cost, not
token-count: effective all-in ≈ **$0.006/call**, ~6× the estimate — plausibly thinking tokens (the probe runs
`thinking_level="low"`; thinking bills at output rates) and stale per-token prices. All standing-cost figures
written before this date inherit the under-estimate and are corrected where they appear; **$0.006/flash-lite-
call at this prompt size is the planning number until billing says otherwise.**

**Catch — the paired design almost corrupted the join.** The v6ab arms are a *paired* A/B: all five arm files
replay the same 12 boards with identical game_ids and identical role maps (verified). Keying by game_id alone
collapsed five behaviorally-distinct games into one — deflating denominators 5× and silently deduplicating
exhibitors across arms. Fixed by keying on (arm, game_id); the role join was never wrong (pairing pins the
cast), only the counting. *Catches: a paired generation design makes "game_id" ambiguous downstream. The
honesty cost that remains: 60 games = 12 boards × 5 arms, so exhibitor slots are not fully independent
samples; the effective n sits between 12 and 60.*

**Result — 5,151 unioned detections, and the in-sample story survives contact with held-out data, stronger.**
The evil-leaning head is a coherent *record-management-and-counter-accusation* family, now at real support:

- counter-accusing that the accuser's role claim is a distraction (27/30 evil, shrunk lift +0.49)
- discouraging reliance on voting records (41/48, +0.47 — record *suppression*, the mirror of town's record
  advocacy)
- accusations-are-a-diversion reframes (60/76, +0.43)
- off-consensus votes (52/70) and the defends-own-voting-history family (61/84)

The town-leaning head is genuine investigative work plus one surprise: **publicly claiming a role went
0-for-28 evil** — in this population/epoch, evil never fake-claims, so a claim is near-certain town. Per-role
signatures at real power: wolves own the counter-accusation/record-suppression family (×2.8–3.1 their share);
the SK's profile is lone-operator cover (joins the consensus vote after warning against bandwagons, explains
its silence as strategy) — the wolf≠SK split replicates held-out; investigators are loudly distinctive (×8.2
on asserts-confidence-while-refusing-to-disclose-source — 10 of its 11 exhibitors were investigators — and ×5
on role-claiming and call-vote-then-vote-it); the vigilante remains the role with no profile.

**Two implications flagged, not resolved here.** (1) The investigator signatures are role-*revealing*: a book
containing "refuses to disclose source ⇒ likely investigator" helps wolves aim night kills as much as it
helps town. Book composition needs a faction-exposure pass before injection (design record book stage, §4).
(2) The role-claim tell (0/28) is the most epoch-fragile head item: it reflects current-model timidity about
fake-claiming, and a prompt or model change could flip it — it must carry the cross-epoch caveat prominently.

**Decisions.** (1) `outputs/heldout/provisional_lift_table.json` is the first real lift artifact —
provenance-stamped PROVISIONAL, owner golden pending; nothing feeds credit from it. (2) Head support now
clears the n≥20 floor for a dozen tells on held-out data alone. (3) Multiple-comparisons and paired-boards
caveats ride with the table; magnitudes like 27/30 and 0/28 survive any reasonable correction directionally,
but magnitude estimates await the certified detector.

---

## 15. Status and what's next

**Where this stands (2026-07-12).** Mining, the ledger design, the 596-canonical store, and the detector are
all settled as above. Everything standing runs on flash-lite — but the 2026-07-13 cost correction (§14)
re-prices the standing path at roughly **$0.25–0.30/game uncached** (detection ~$0.22 + mining ~$0.05),
comparable to the ~$0.28 generation cost of a game rather than the cent-scale first quoted.

The levers, status end of 2026-07-13 (full probe record:
[`../../caching/experiment_log.md`](../../caching/experiment_log.md) §⑤–⑤a): explicit prefix caching is **built
and verified** (`--cache`, 94% cache_read) but **default OFF** — no temp-0 config is bit-deterministic
(uncached+low self-agrees 0.90–1.00) and caching degrades that further (0.56–0.83); **thinking→minimal is
REJECTED** — it collapsed detection recall to 0 golden true-positives (the saturated ~1k reasoning tokens do
the work); k=2→k=1 awaits the golden. Same-day resolution (caching log §⑤b): the owner called the
reproducibility question directly — none of detection's consumers need it (aggregates; role-blind noise can't
correlate with roles; goldens bind to stored artifacts; extraction took the identical trade at ship) — so the
one remaining gate was accuracy parity, checked on the 40 golden cells: **cached union scored equal-or-better
than uncached (0.83/77% vote, 0.93/87% discussion)**. **Standing config = cached + low** (default ON in the
probe); standing overhead lands at **~$0.17–0.20/game**, with k=1 the remaining lever toward ~$0.10–0.12. The
shipped design, destination-first, is in [`report.md`](report.md).

**What is explicitly NOT done, in gate order** *(status as written 2026-07-12; superseded in
place by later entries — §16 amended gate 1 and discharged the order, §14 provisionally
discharged gate 2, §17 discharged gates 3–4):*

1. **The owner's detector-blind golden adjudication** — the certifying pass. Everything in §13 is aimed by a
   temporary golden the owner has not adjudicated; no lift number is trusted before this gate.
2. **The held-out lift pass.** No tell has a validity number yet. Mined-recurrence support is a plumbing
   proxy; real support and lift require the detector on games the tells were not mined from.
3. **The v1 credit wiring** — connecting detected counts to the read/tactic credit design, per the design
   record and [`../../credit/report.md`](../../credit/report.md).
4. **Production implementation of the epoch lifecycle** — the probe scripts simulate it; the fold/audit
   machinery is not production code, and the match-index retirement rule (§12) is designed but not built.

---

## 16. The owner golden begins — and granularity gets an operational definition (2026-07-13)

The certifying pass (§15 gate 1) started as designed and immediately reshaped itself on contact with the
owner's actual time and energy. Built: a two-layer blind bundle (`owner_golden_build.py`) — 6 fresh held-out
games on distinct boards (arms cycled, so the paired-board hazard can't enter), 24 cells (2 focus players × 2
channels × 6 games), a fresh **cached** k=2 detector run as the stored artifact under certification (~$0.80),
and a sealed phase-2 pool: cached union + pre-existing uncached held-out rows + 146 Opus prelabel rows from
six agents ($0 API), 181 candidates total, shuffled and source-blind. Recall is bounded by pooling; the
owner's blind read exists only as the pool's error bar.

**Build catches (both against my own scaffolding).** (1) The focus-player sampler drew from the roster, not
day-active players — g5's draw was a night-1 death with zero transcript footprint; an Opus prelabeler caught
it. (2) The "deterministic" rng draw did not reproduce across script edits, so the focus map is now PINNED as
literals: a published sample is a frozen contract, not a seed. *Catches: reproducibility that depends on
replaying an rng sequence through evolving code is not reproducibility.*

**g1 adjudicated end-to-end** (`outputs/owner_golden/owner_verdicts.json`): detector precision 7/8 upheld; one
`n_wording` rejection ("at the last moment" implies a change of heart, not silence-then-join); and the
structural verdict — four ids (vote_221/51/238/673) describing ONE silent-bandwagon event, vote_673 canonical.
The owner's blind read found 0 of the 5 ratified behaviors, which is the pooling design working, not failing.
Cross-checked against §14 lift, the owner's instincts were exact: the silence-conditioned family he dismissed
carries ~no lift (vote_2: n=163, +0.02); the two he called real tells are the discriminators (vote_14 +0.20;
vote_380 +0.38, 74% evil at n=70 — in g1 cast on the SK by the wolf, who was night-killed for it).

**Protocol pivot, owner-decided.** Blind reads are too expensive for a tired human and add only the error-bar
layer, so g2–g6 go **judge-only** (pool verdicts, per-game incremental unsealing, anchoring caveat on record),
and — the larger call — **the provisional labels are GO for credit wiring**: the owner accepted
temp-golden-grade certification for the v1 build, remaining owner verdicts an upgrade path, not a blocker.
§15's gate order is amended by this entry; the log does not pretend the original order survived.

**Granularity, settled operationally.** The owner asked at what granularity two verbally-similar tells are
"really different," without opening a research problem. Adopted: *two same-channel tells are the same iff they
fire on the same instances at the same lift* — semantics propose, measurement disposes. `granularity_screen.py`
(instance grain = arm/game/player/day, n≥10, held-out union): **0 automatic merges, 7 hierarchy flags** —
generic parents at ~0 lift containing specific children that carry the signal (vote_41 ~0 ⊃ vote_56 +0.21;
vote_426 ~0 with town-leaning children at −0.10..−0.17). One honest limit, verified: near-duplicate checklist
entries COMPETE for instances (the g1 fragment family co-fires at J=0.04–0.14 because the detector books each
event under one or two ids), so vote-splitting duplicates are invisible to co-firing — the fold's semantic
pass still proposes those, and the merge verdict is checked by pooled-lift arithmetic (a wrong merge shows up
as lift dilution). The one forbidden merge direction: never fold a discriminating child into its zero-lift
parent. *Catches: the elegant fix wasn't a new similarity measure — it was refusing to let similarity decide
anything lift can decide.*

---

## 17. The pipeline graduates — v1 credit wiring, the live book channel, and the two pre-run screens (2026-07-13)

**Motivation.** With all five §6 valence rulings closed (credit report), the last build item before the v7 run
was the wiring: the credit rules as running code, the tell pipeline as maintained loop modules, and the
injection channel carrying the book into live prompts.

**Built (all tested; suite 653 green).** The probes graduated to `evaluation/src/loop/`: `tells.py` (mining +
the k=2 cached detector, prompts verbatim in `tell_prompts/`), `tell_credit.py` (lift arithmetic pinned to
§14's convention; the §6.5 positive-only eligibility; the role-revealing book filter), `tell_fold.py` (the
epoch fold: freeze-old wording dedup, probation clock K=12, fat-null archive with split-check, publishes
checklist v_k+1). The live half is `Agents/memory/tell_book.py` + a `{tell_book}` slot above the reads
instruction in every day/night template, env-gated per arm (`WW_TELL_BOOK`); the loop driver runs
mine→detect→fold→rebuild-book per generation (`--tells`). Credit side: healer night credit (the ★construct
verbatim; the "needs the attack-join" blocker had been stale since the wolf-blend join made game records
available to the pass), the read-partition, the endpoint self-lynch guard, move-grain targeted-push credit,
the concealment floor (both guards, `sp_type=concealment` synthesis tag), and the tagger credit mode retired.
The probes here stay frozen records; this folder's code is superseded scaffolding from here on.

**Attribution spot-check (n=15, seeded, AI-adjudicated — `evidence/credit/attribution_spot_check.json`).**
13/15 enacted, 2/15 not-enacted (95% one-sided upper bound ~36% dilution). Both misses were follow-claims on
turns the agent then PASSED — closed structurally: the discussion ledger now credits spoken turns only
(`credit.py::_spoke`), applied to the OFF base too. *Catches:* the check isolated exactly the dilution shape
it was designed for, and the finding became a gate instead of a bound.

**Injection-channel replay screen (design record §8 gate 3; `outputs/book_screen.json`).** 40 frozen v6ab
day-vote decisions replayed ± the seed book through the REAL injection path (bare memory block, so the
contrast isolates the book). Result: **channel ALIVE** — 7/40 decisions (17.5%) changed under the book;
correctness direction null at this N (2 wrong→right vs 3 right→wrong, discordant n=7). *Catches:* the first
book was composition-skewed — the per-role cap filled entirely with the higher-lift discussion family, so vote
decisions were screened against a book with zero vote tells. Fix: the cap is now per (subject role, channel);
the balanced 12-entry book (`evaluation/frozen_eval_sets/tell_book_v1_seed.json`) re-screened on the SAME 40
decisions (`outputs/book_screen_v2_balanced.json`): 11/40 changed (27.5%), correctness 20 → 24, discordant
pairs 5 wrong→right vs 1 right→wrong — DIRECTION positive, magnitude/significance not established (n=6
discordant, one-sided exact p≈0.11; old-epoch decisions). The gate question (channel-liveness) passed on both
books; the balanced book is the launch default, decision-quality belongs to the run, and cross-epoch transfer
of the seed book stays a first-generation readout (owner-accepted 2026-07-13).

## 18. The book goes role-grain — the role-revealing exclusion is removed (2026-07-14)

**Owner ruling (supersedes §17's role-revealing filter and the pre-reg §5 draft default):** no
exclusion — inferring a specific role from public behavior is the tell mechanism's entire point, and
the shared book is symmetric by design (the same information lets wolves hunt an investigator, the
healer protect one, and the investigator learn to conceal the pattern). The ruling exposed a second,
quieter gap: the book had been selecting via `credit_eligible` (positive **evil**-lift), so
town-power-role families — the held-out investigator source-withheld tell, ×8.2 — were excluded by
the credit rule's reuse even before the explicit filter. What pays and what informs are different
questions, and the book now asks its own.

**Built (suite 655 green):** `is_role_revealing` deleted; book selection re-based on a new
`tell_credit.subject_lift` — the subject role's shrunk exhibitor share over its cast prior (the same
K=5 construction as the evil-lift, role-grain; `lift_table` entries now carry `role_priors`).
Selection = per (subject role, channel), top 3 by subject lift over the n≥8 floor, every unrevealed
role. Book entries and the rendered line are subject-grain ("the exhibitor was a wolf 21/30 times
observed"). §6.5 credit eligibility is untouched — the investigator tell injects and never pays.
Launch seed rebuilt: **`tell_book_v2_seed.json`** (34 entries, all six subject roles; investigator
source-withheld tops the book at +0.55) via the frozen-record script
[`scripts/build_seed_book.py`](scripts/build_seed_book.py) — the v1 build had no preserved script,
this one does. v1 (12 entries, wolf+SK only) stays in place: §17's book-screen results ran on it.
*Caveats, on record:* the injection screen has not been re-run on the bigger v2 book, and the v2
tail (vigilante/healer entries at lift +0.03–0.06) is near-prior — a minimum-strength floor is an
open question for the walkthrough (consolidation report §6).

*Sources — this log absorbs the probe's working notes in place; the frozen prompts are in
[`prompt_versions/`](prompt_versions/), per-run outputs and store snapshots in `outputs/`, and the probe
scripts under [`scripts/`](scripts/) (`tell_mining_probe.py`, `dedup_v0.py`, `ledger_sim.py`,
`consolidation_prep.py` / `consolidation_apply.py`, `detector_probe.py`, `golden_sampler.py` /
`golden_score.py`, `heldout_lift.py`, `owner_golden_build.py`, `granularity_screen.py`) alongside. The pipeline
graduated to `evaluation/src/loop/` (§17); the scripts here stay as frozen records of how each
result was produced.*
