# The Tell Ledger — How It Works

**Scope:** the tell system end-to-end — how behavior patterns ("tells") are mined from finished
games, deduplicated and stored, promoted onto a bounded checklist, counted by a role-blind
detector, and prepared for accuracy-based credit. Covers the **final v1 design** (decided
2026-07-12) and the probe evidence behind each decision. What tells are *for* — the credit
currency and its valence rules — lives in the design record
([`../../discussion_tagger/read_tactic_credit_redesign.md`](../../discussion_tagger/read_tactic_credit_redesign.md)
§3) and the credit mechanism doc ([`../../credit/report.md`](../../credit/report.md)); this
document is the storage-and-measurement half. **Companion:** the chronological build journey,
including everything the data overruled, is [`experiment_log.md`](experiment_log.md).

**Distilled** 2026-07-12 from the probe workstream (2026-07-11 – 07-12). **Build status, stated
up front:** the design is final and every mechanism below was exercised on real data by probe
scripts in this folder — including a held-out lift pass (60 games, provisional table in
`outputs/heldout/`) — but the production implementation (the epoch fold/audit machinery as
pipeline code) is not yet built, and no lift number is certified yet. The gate still ahead of
any trusted number is in §5.

**Orientation — the two clocks the system runs on:**

```
EVERY GAME (standing, all flash-lite; ~$0.17–0.20 at observed billing, cached detection — see §1):
  mine the day record (2 calls/day, channel-split)     → new candidate wordings + instances
  exact-match accumulate (free)                        → repeat wordings land on their canonical
  detector scans each player × channel                 → detected (tell, player, day) rows
       against the FROZEN checklist v_k                  + a denominator row per scan

EVERY 10 GAMES — "the fold" (publishes checklist v_k+1):
  LLM dedup folds new wordings into the frozen canon (drop-or-keep, freeze-old)
  recompute all tallies from instance rows · probation verdicts · admissions · re-entries

EVERY ~30 GAMES — "the audit" (strong model, run Claude-side, $0 API):
  re-cluster within the canon · split-check suspicious nulls · repair wording by judgment
```

A **tell** is one sentence of observable behavior at move-type grain — a real one, the store's
current №1 by support: *"A player casts a vote for someone who publicly questioned them during
the discussion phase"* (the retaliation vote; consolidated support ≈69 across 30 games). The
system's whole point is that no model ever says what that behavior *means*; counting does.

---

## Motivation — counts, not judges

The credit redesign replaced LLM-judged discussion quality with **accuracy-credited facts**: a
tell earns standing by its **lift** — how much more (or less) often its exhibitors turn out to
be evil than the cast's base rate predicts. (In a 9-player cast with 3 evil, a random behavior
lands on evil ~1/3 of the time; a tell whose exhibitors are evil 6 times in 9 carries real
information, one at 3-in-9 carries none.) Lift is arithmetic on counts, so the design problem is
entirely about producing counts that can be trusted:

- The **miner** may be omniscient (it sees true roles — that's what makes discovery efficient),
  but precisely because it is omniscient its output is salience-biased and has no denominator —
  it reports what it found notable, not how often anyone had the chance to do the thing. So
  **mined counts may never feed lift.** They are discovery and recurrence evidence only.
- The **detector** is the opposite by construction: role-blind (it cannot favor wolves it cannot
  see) and exhaustive (it scans every player against every checklist tell, so every
  non-detection is a recorded denominator entry). **Detected counts are the only lift source.**

Everything else in the design — the tiers, the caps, the epochs — exists to make that
measurement affordable and stable while the store underneath it grows without limit.

---

## 1. The guarantee (the contract this design holds)

- **Leak-safety by construction, not by instruction.** The miner's context contains only the
  public record (plus the roles header), so undetectable-at-the-table behaviors cannot be mined;
  the detector's context contains no roles, so its counts cannot be role-contaminated. Role
  words appear in a tell only with a public-certainty marker ("revealed on death as…",
  "claiming to be…"); hidden-relationship phrasings ("ally", "packmate") are banned outright.
- **No model assigns meaning.** The miner emits no direction; the detector emits yes/no/day; the
  dedup judge decides only extensional identity ("would a reader count the same moments?").
  Direction comes from lift, computed on games the tell was not mined from (the in-sample halo
  split).
- **Bounded cost against an unbounded store.** The store is never capped, but the agent-facing
  and detector-facing surface is: a hard checklist cap per channel (25 incumbents + 15 probation
  + 8 rotation = 48). Standing per-game cost is mining + detection only, all flash-lite —
  **~$0.25–0.30/game uncached at observed billing** (corrected 2026-07-13: the held-out run
  billed $13 for 2,160 calls ≈ $0.006/call, ~6× the initial estimate; detection at k=2 is ~36
  calls/game ≈ $0.22, mining ~$0.05). That is comparable to a game's own generation cost
  (~$0.28), not the cent-scale first quoted. Three reduction levers, status as of 2026-07-13:
  **explicit prefix caching is the STANDING CONFIG** (adopted 2026-07-13 after a golden
  accuracy-parity check — cached union scored 0.83/77% vote, 0.93/87% discussion, equal-or-
  better than uncached; 94% cache_read on the ~5.5–8k-token per-(game, channel) prefix,
  extraction-v5 mechanism, default ON in `scripts/detector_probe.py`): detection ≈ $0.12–0.14/game,
  tell system ≈ **$0.17–0.20/game all-in**. **thinking `low` → `minimal` is REJECTED** — it
  collapsed golden recall to zero; the ~1k reasoning tokens/call are doing the detection.
  **k=2 → k=1** awaits the owner golden (would land near $0.10–0.12 all-in).
- **Counts are recomputable, never accumulated.** Every mined or detected instance is a row
  (`tell_id · game_id · exhibitor · revealed_role · source: MINED|DETECTED · day · quote`);
  every tally is recomputed from rows, so counts are windowable and survive re-clustering. The
  freeze-old dedup rule (canonical text is never rewritten; new wordings either die into an
  existing canonical or become a new one) is what keeps rows valid across checklist versions.
- **Credit can only touch what was measured.** Credit-eligible tiers are the incumbent lane and
  the injected book; probation and rotation slots accrue counts but never charge an agent's
  read. An archived tell has no denominator, hence no lift, hence no credit — it is outside the
  credit system, not merely down-weighted.
- **Detection is near-deterministic; reproducibility lives in the stored artifacts.**
  (Corrected 2026-07-13 — an earlier "deterministic, Jaccard 1.00" claim overgeneralized from
  one run pair.) Identical uncached temp-0 runs self-agree at row Jaccard **0.90–1.00**,
  occasionally exact; no configuration reproduces exactly, and the explicit prefix cache
  (now the default) degrades stability further (0.56–0.83 — the full 2×2 with thinking levels
  is in [`../../caching/report.md`](../../caching/report.md) gap 0; the cheap-thinking escape
  was rejected on accuracy: 0 golden true-positives at `minimal`). The standing configuration
  is **cached + low thinking** — adopted because a golden parity check showed the flicker
  scores as noise (equal tp/fp to uncached), lift's consumers are aggregates, and the
  role-blind detector's noise cannot correlate with hidden roles by construction. Detected
  rows are durable JSONL artifacts, goldens certify a *stored run*, and a re-run is a new
  sample — exact re-runs are not promised in any configuration.

What the design deliberately does **not** do: it does not try to stop the store growing (the
30-game simulation showed the vocabulary's singleton tail is open-ended, ~16 genuinely new
tells/game with no downward trend — but the *recurring* core converges, and only the recurring
core ever costs anything); and it does not let dedup be the store-size control (that was the
failure mode of the earlier observation-store design — non-convergent past ~17%; here the cap
bounds the working set and dedup only has to keep the *head* honest).

---

## 2. The model — three tiers, two counts, one epoch clock

**The tiers, defined by what membership licenses:**

| Tier | Bound | What membership licenses |
|---|---|---|
| **Book** | ~3 per unrevealed role | injected into live player prompts; the only tier agents ever read |
| **Checklist** (incumbents + probation + rotation) | 48/channel hard cap | scanned by the detector — the only place counts accumulate |
| **Archive** | unbounded | full record, instances retained; zero scan cost; recoverable |

Movement between tiers is mechanical. A newly mined tell enters the **queue**; if no new
evidence arrives within 5 games it ages to archive. Queue → **probation** admission is by
recurrence priority when slots open; a probationer is scanned for 12 games and promotes to
**incumbent** on support ≥2, else archives. Incumbents are ranked by support (detected, once the
detector runs) under the cap. Demotion: an incumbent with fat support and null lift (n≥20,
|lift| below threshold) is first **split-checked** — a null blend can hide two directional
sub-tells — then archived as measured-and-uninformative. Re-entry from archive: mined recurrence
in 2+ distinct games re-queues a tell, and 8 rotation slots per channel cycle
least-recently-scanned archive entries back through the detector at zero marginal cost. One
rule is never applied: ranking by lift at thin support — that selects on noise and locks in
early luck (the probe's cleanest town-leaning tell began as a lift≈0 singleton).

**The two counts, kept apart everywhere:** MINED instances drive attention (queue priority,
probation promotion, re-entry) because they prove a pattern recurs and is discoverable. DETECTED
instances drive validity (lift, incumbent rank, demotion, credit) because only they have
complete denominators and no role halo. The simulation ran on mined-recurrence as a labeled
stand-in; nothing validity-shaped is claimed from it.

**The epoch clock** (why dedup is not online): the per-game path runs no LLM dedup at all — only
free exact matching, which pro-grade mining makes productive because the miner converges on
identical wording for recurring patterns. Semantic dedup happens at the 10-game **fold**, where
the judge sees whole families at once instead of isolated pairs, and at the ~30-game **audit**
(a strong model re-clustering the canon). The simulation showed the online judge was
simultaneously the most expensive standing component (~178 of ~204 calls/game) and the least
accurate (it fragmented head-tell support 2×, which the batch pass then repaired) — so it was
removed, and the ≤10-game entry latency it saves is immaterial against the 12-game probation
window. Named trade-off: the fold is critical-path — skipped, the checklist goes stale and new
vocabulary stops entering.

**Mining** (settled at v4): two flash-lite calls per game-day — a discussion-layer call whose
record omits the focus day's vote block (temporally principled, and it removes the compact
structured block cheap models anchor on), and a vote-layer call with the full day (vote tells
are cross-channel by nature). Channels are hard partitions for dedup and storage; within a
channel, dedup is global — never partitioned by exhibitor role, or lift's numerator and
denominator would live in files that are never compared.

**Detection** (settled at det_v1 ∪ det_v3): per (game, player, channel), the detector reads the
public record plus the frozen checklist and reports every (tell, day) the focus player
exhibited, with a verbatim quote. Two deterministic passes union their rows: one full-view, one
whose discussion calls read a vote-tally-stripped record (the mining split applied to detection
— it recovered the one systematic miss). Direction-grade accuracy on the temporary golden:
discussion 0.93 precision / 87% day-recall, vote 0.77 / 77%.

**Where it lives:** probe scripts + frozen prompts in this folder (`scripts/tell_mining_probe.py`,
`scripts/detector_probe.py`, `prompt_versions/`); the reference canon in
`outputs/consolidated_store.json` (596 canonicals over 30 games); the ledger spec in the design
record §3; constants above are v1 values, hand-set and revisitable on detector-era data.

---

## 3. How we verify it

Layered to match where each risk lives — structure checked by regex, semantics by reading,
mechanism dynamics by simulation, accuracy by adjudicated golden:

| Layer | What's checked | How |
|---|---|---|
| **Structural screens** | role words without certainty markers, hidden-relation words, player IDs, quote-not-in-record | regex per mined/detected row; flags are triage, never verdicts (defect rates bounded ~1–2% at v4) |
| **Semantic quality** | objectivity, motive-freedom, grain | sample reads per prompt iteration; two defect classes fixed with BAD examples built from real failures |
| **Dedup correctness** | wrong-merge rate, under-merge (recall) | read of all 44 v0.1 merges (~2% wrong); distinctness audit (166→107, reviewer verified before counts trusted); consolidation №1 head clusters read and ratified individually |
| **Lifecycle dynamics** | growth, queue depth, tier occupancy, cost | 30-game replay simulation (`scripts/ledger_sim.py`) — mined-support proxy, labeled as such |
| **Detector accuracy** | precision/recall at (tell, day) grain | temporary golden: 40 stratified cells, 5 independent Opus adjudicators (never shown detector output), every disagreement re-read against transcripts (10/10 ratified) |

The strongest verification is structural: the leak boundaries (public-record-only miner,
role-blind detector) are properties of what the prompts *contain*, so they cannot regress
without a code change — the screens exist only to catch drift in the model's output, not to
enforce the boundary.

---

## 4. Case study — the store that wouldn't stop growing

**Verdict (skim this, skip the rest):** The original plan assumed a finite tell vocabulary — mine
a large batch of games once, dedup, keep the good ones. A 30-game simulation falsified the
premise: genuinely new tells arrive at a flat ~16/game with no endpoint. A batch consolidation
then showed the deeper structure — the *recurring* core converges fast (~140 tells; discovery of
tells-that-repeat fell 37% → 19% → 11% by cohort) while the inflow is an endless tail of
one-offs. The design's answer was to stop fighting store growth entirely: cap the *measured*
surface, let the archive grow, and move all semantic dedup to batch epochs — which also
retired the online LLM judge that was both the costliest and the least accurate component. *The
data overruled the plan twice, and the second time it also cut the largest standing cost.*

*Forensics, by subhead:*

**The plan the data killed.** The bootstrap plan was a one-time mining sweep (~60–180 games)
into a deduplicated corpus — implicitly assuming the vocabulary saturates. The simulation's
fresh-tell curve stayed flat through game 30 (740 canonicals and climbing linearly), so "mine it
all" has no endpoint and the sweep died as a concept. Mining became a standing per-game pass.

**The owner's challenge, and the split verdict.** Extrapolating the flat curve gave >2,000 tells
by game 100 — implausible as a count of *real* distinct behaviors. A strong-model batch
consolidation (740 → 596) settled it: the flat growth is real (not a dedup-recall artifact) but
it is almost all singleton tail; the tells that ever recur were mostly discovered in the first
~15 games. Both intuitions were right at once — unbounded store, small real core.

**The amendment the numbers forced.** The same simulation measured the online dedup judge at
~178 of ~204 per-game LLM calls *and* found it had fragmented the top tell's support across
three wordings (18+11+10) that the batch pass had to reunite. Paying the most for the worst
judgment, with no consumer needing its output same-game, is a removal argument, not a tuning
argument — hence the epoch-quantized lifecycle (§2), proposed by the owner and adopted on the
simulation's evidence. Removing the judge cut ~178 of ~204 standing calls per game (the
absolute dollar figures first attached to this were ~6× low — corrected 2026-07-13, §1), and the
checklist became a versioned, frozen artifact per epoch — cleaner denominators as a by-product.

**What survived unchanged.** The three-tier shape, drop-or-keep dedup, the probation funnel, and
recurrence re-entry all behaved as designed in the same simulation (queue stable at ~150 with
the TTL working; probation absorbing ~12% of inflow with the right admissions). The amendment
moved *when* judgment runs, not *what* the store is.

---

## 5. Known gaps

Criticality = likelihood × impact × detectability. Freshness: all entries checked against this
folder's artifacts **2026-07-12**; all open unless noted.

- **[high — the gate] No owner-adjudicated golden; all lift is provisional.** Every detector
  accuracy number rests on the temporary golden (40 cells, Opus-adjudicated + my review,
  positives sampled from the detector's own first-version output — flattered by construction).
  A held-out lift pass HAS run (60 games = 12 paired boards × 5 memory arms;
  `outputs/heldout/provisional_lift_table.json`, log §14) and its head is coherent and strong
  (record-management/counter-accusation family 71–90% evil at n=27–84; role-claiming 0/28
  evil) — but the instrument is uncertified, the 12-boards×5-arms sample is not 60 independent
  games, and ~96 tells were scanned (some strong cells arise by chance). The owner's
  detector-blind adjudication is the certifying pass; until it, nothing feeds credit.
- **[medium] Vote-channel detection is the weak half: 0.77 precision / 77% recall.** The
  residual FPs are relation-clause misses (voting the accused after questioning the accuser ≠
  "votes the accuser"), and one cell (interrogate-then-switch-vote) is missed by every pass —
  a systematic blind spot that more unioning cannot fix. Both go to the owner-golden round.
- **[medium] The production lifecycle is unimplemented.** The fold and audit exist as probe
  scripts and a one-off Claude-side pass, not as pipeline code; the match-index retirement rule
  (singletons unseen ~40–50 games leave the comparison index) is designed but not built. Until
  the fold is scheduled machinery, the "critical-path" trade-off in §2 is a manual obligation.
- **[medium] Consolidated support values are upper bounds.** Merged clusters sum member
  supports; a (game, exhibitor) pair that hit two fragments is double-counted until
  instance-level dedup runs at the next audit. Affects ranking near the cap boundary, not the
  head.
- **[low–medium] Ledger constants are hand-set and unswept.** Cap 48/channel, probation K=12,
  queue TTL 5, fold N=10, audit ~30, re-entry threshold 2 — all reasoned defaults exercised
  once in simulation under a mined-support proxy. They should be revisited on detector-era
  data; the sequential-discussion workstream's unswept-tunables slip is the standing argument
  for actually doing it.
- **[low] Miner residuals at v4:** ~1–2% miner-authored motive clauses slip through, and the
  vote prompt's enumerated pattern families may bias against novel vote patterns. Both are
  absorbed by dedup and the read tier; neither poisons counts.
- **[low] Cross-epoch validity of tells is untested.** Tells were mined from one prompt-epoch's
  games; a future prompt change shifts the behavior distribution, and nothing yet measures how
  much of the canon transfers. (The index-retirement rule aligns with prompt epochs partly for
  this reason.)

**Deferred by design (not gaps):** book composition and injection at generation time (design
record §4); the credit wiring itself (the four open valence calls in
[`../../credit/report.md`](../../credit/report.md) §6); mining the remaining backlog of games
(only if head support demands it before go-live).
