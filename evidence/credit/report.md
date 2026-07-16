# The credit layer — how a decision becomes a learning signal

> **Scope:** the mechanism. How one recorded decision turns into per-memory utility: the two ledgers,
> the per-channel valence rules with the reasoning behind each, the baselines, the shrinkage, and the
> line between credited signals and diagnostics. This doc is also the wiring spec for the v1 build —
> every component is marked **as built** (running code) or **v1 — ruled, wiring pending**. All five
> judgment calls that were open in the 2026-07-11 draft have since been ruled by the owner
> (2026-07-11 → 2026-07-13) and are absorbed inline with dates. **The v1 wiring was BUILT 2026-07-13**
> (same day, after the rulings closed): every row below marked "as built (2026-07-13)" is running code
> with tests — `evaluation/src/loop/` (credit, read_ledger, first_link, tells/tell_credit/tell_fold)
> plus the live book channel `Agents/memory/tell_book.py`.
> **Companions:** the *why* of the redesign, with alternatives and rejections, is the design record
> ([`read_tactic_credit_redesign.md`](read_tactic_credit_redesign.md));
> the game-grain, win-validated A/B ruler is [`../metrics/report.md`](../metrics/report.md); how far
> to trust the surrounding loop machinery is the eval hub's job
> ([`../evaluation/loop/report.md`](../evaluation/loop/report.md)).
> **Status:** active record, rewritten 2026-07-13 (supersedes the 2026-07-11 draft in place).

> **Orientation — one pipeline, two ledgers.** Every credit signal is built along one path:
>
> **decision → facts → valence → attribution → baseline → shrinkage → ledger**
>
> *Facts* are what happened (who was voted, what the target's true role was). *Valence* is whether
> that was good **for the actor's own faction**. *Attribution* is which memory item the signal lands
> on. *Baseline* subtracts what happens anyway without memory. *Shrinkage* damps thin evidence.
> The pipeline feeds two ledgers with two mechanisms: **strategy points** (usage-gated — an SP must
> be followed to earn anything) and **tells** (off-policy — a tell scores on every player who
> exhibits it, shown to an agent or not). That asymmetry is why the two mechanisms cannot be one.

---

## 1. What credit is for — and what is never credited

Credit exists for the v7 compounding loop's curation steps: **consolidation** decides per strategy
point whether to keep, prune, or synthesize over it (`loop/consolidate.py`), and the **tell fold**
(`loop/tell_fold.py`) decides per tell whether it stays on the detector checklist and enters the
injected book. (The fold is the periodic curation tick that runs every ~10 games, *folding* newly
mined tells into the store — dedup against canon, probation, retirement. The name has nothing to do
with cross-validation folds.) Both need a per-item utility, and the two obvious sources fail:

- The game's **win** is too sparse and too noisy to grade a single lesson. Sparse: one bit per
  game, shared by every lesson every agent used that game. Noisy: a large share of outcome variance
  is role-assignment and night-target luck rather than skill (the metrics campaign's estimate:
  roughly a third), so a single lesson's true effect would need hundreds of games to show through.
- The agent's own **follow/override choice** is degenerate. Measured on the v6ab town arms (1,748
  memory-on decisions with verdicts): when an agent judged a shown SP applicable it followed 1,943
  times and overrode 26 — a **98.7% follow rate** (the G3a finding; the real filtering happens one
  step earlier, at the "not relevant" verdict, 3,155 times). A bit that is almost always "followed"
  cannot separate good SPs from bad ones — it is true of the best and the worst SP alike. The same
  measurement settles a related question: most decisions follow exactly one SP, but ~24% follow two
  or three at once (mean 1.11 per decision), which is why the attribution risk in §3 is *dilution
  across co-followed SPs*, not a single-SP mistake.

What remains is the middle grain — *when an agent used this memory and then acted, was that one
action good, judged against the true hidden roles?* — many small per-decision rewards, dense enough
that one mis-graded turn washes out.

Three things are deliberately **never** outcome-credited:

- **Observations** — descriptive records ("I did X in situation Y and Z happened"). You don't
  "follow" one, so there is nothing to credit; they are the substrate synthesis distills SPs from
  and ride frequency plus the deterministic extraction anchor.
- **The Brier ledger** — the agent's read accuracy against revealed roles. It is a meter on the
  *agent*, never on a memory item, and it must stay separate: mixing application quality into a
  fact's credit makes the fact's score depend on who applied it (design record §3, Layer 2).
- **Diagnostics** — instruments that watch the same games without paying credit (§5). The main
  two: the **discussion tagger**, an LLM judge that reads a full day's transcript with the true
  roles visible and issues one per-player verdict on how well that player worked the discussion —
  "holistic" because it judges the whole day at once rather than any single move — and the
  **first-link read-delta**, which asks whether an addressed player's next stated read moved the
  way a push intended. A diagnostic may explain a result; it never feeds prune, protect, or
  synthesis.

Two standing boundaries. First, **credit never referees an A/B.** Credit is the loop's *internal*
reward: its only job is deciding which memories to keep, prune, or synthesize. It has never itself
been validated against winning, so "average credit went up" is not evidence that memory helps — a
loop that graded its own effect with its own reward would be marking its own homework. Whether
memory helped is always answered outside the loop, by the win-validated proxy basket and the
end-point A/B (the metrics report). Second, **credit is v7-only**: v5/v6 recorded follows live but
nothing joined outcomes back until `credit_backfill.py` closed the join.

## 2. The facts/valence split

The layer is two modules on purpose:

- **Facts** — `evaluation/src/loop/decision_scoring.py` (**as built**): one frozen decision in,
  deterministic facts out. Votee's true role, threat-hit, mislynch, abstain, night target class,
  the original choice set, and board pivotalness (`query_criticality`). No LLM, no opinion about
  whether an outcome was *good*.
- **Valence** — `credit_backfill._vote_credit` / `_night_credit` (**as built**; reused live):
  interprets those facts per faction — "did this action advance the actor's own win condition?"

The split exists because the facts have ~15 importers (replay screens, audits, instrument
validation, credit) that must all agree on ground truth, while the *interpretation* legitimately
differs per consumer. Without the split every consumer re-derives "was this vote correct" and they
drift.

One ruling lives on the facts side: **criticality stays out of credit magnitude** (ruled
2026-07-11). *Criticality* (pivotalness) measures how close the board is to a decided game. It is
deterministic arithmetic over the game's three terminal clocks (`Agents/board_clocks.py`) — each
faction's countdown of eliminations until its win condition: the wolf clock (non-wolves left to
remove), the SK clock (everyone-but-one left to remove), the town clock (threats left to remove). A
**swing-board decision** is one taken when any clock is at ≤1 — the game can end within one
elimination, so a single mislynch or landed kill can decide it. The ruling says that decision still
earns the same ±1 as a sleepy day-1 vote. The reason: pivotalness is a property of the *board*, not
of the lesson — an SP followed at a pivotal moment is not thereby a better SP, and weighting credit
by board tension would concentrate credit noise into exactly the highest-variance moments.
Criticality is used in two other places instead: **lesson selection** — extraction mines new memory
candidates preferentially from pivotal decisions, since that is where a lesson is worth writing —
and **audit ground truth** — the periodic quality audit samples pivotal decisions, where a grading
error would matter most.

## 3. The strategy-point ledger

### Step 1 — attribution: the follow join (as built)

A decision's credit lands on every SP the agent reported following at that decision
(`strategy_verdicts` → `strategy_index_to_key`). Self-report is the accepted v1 attribution because
its failure mode is benign: at ~99% follow the risk is **dilution, not bias** — an SP that didn't
really shape the action gets the outcome smeared onto it, weakening contrast rather than tilting
it, because the valence itself is deterministic. The bound is now MEASURED (2026-07-13, n=15 seeded
sample, AI-adjudicated — `attribution_spot_check.json` beside this report). The check: draw 15
claimed follows and read each transcript asking *did the action actually enact what this SP
advises?* 13 of 15 did (**enacted**); 2 were **empty claims** — the agent reported following the SP
but the action shows no trace of it, so any credit would have landed on an SP that did nothing.
Fifteen samples is small, so the honest number is a confidence bound, not the raw 2/15: at 95%
confidence the true empty-claim rate is **at most 36%** (Clopper–Pearson, the standard exact bound
for small samples). Read plainly: even in the worst case consistent with this sample, roughly
two-thirds of credit lands on SPs that genuinely shaped the action — and the failure direction is
dilution (added noise), never a systematic tilt. Both observed misses had one shape — a follow
claimed on a turn the agent then PASSED (said nothing) — so the discussion ledger now credits
SPOKEN turns only (the pass-gate, `credit.py::_spoke`, applied to the OFF base too), which removes
the only observed failure mode structurally. The outcome-blind matcher that would replace
self-report stays deferred future work.

### Step 2 — valence: the per-channel rules

Each row states the rule, the validated proxy it mirrors, and its status. Every credited channel
traces to the win-validated proxy campaign ([`../metrics/candidate_ledger.md`](../metrics/candidate_ledger.md));
where a channel is deliberately weak or generous, the owner ruling that accepted it is dated inline.

| Channel | Roles | Rule | Validating evidence | Status |
|---|---|---|---|---|
| Day vote | town | **+** threat lynch (wolf *or* SK) · **−** townmate · abstain neutral | town vote basket (validated, \|r\|≈0.6 family) | as built |
| Day vote | wolf | **+** vote matches the day's final plurality, **−** off-plurality | G2 day-blend r=+0.22; blend-with-majority audit r=+0.20 | as built |
| Day vote | SK | **+** any non-self lynch | none — near information-free; **ruled 2026-07-13: keep for v1** (concealment floor now carries SK day-skill) | as built |
| Day discussion, day grain | all | every followed discussion SP gets one tick, signed by what the day's lynch was worth to the actor's faction | M1 vote endpoint, held-out Pearson +0.51 (n=51 SPs, v6ab) | as built (2026-07-13) |
| Day discussion, move grain | all | a followed SP that produced a stance-tagged push at a specific player: **did it work** (lynch landed where pushed) × **target's faction value** | reuses the validated vote-endpoint + roles lookup; deterministic | as built (2026-07-13) |
| Day discussion, concealment | wolf, SK | per-day suspicion-delta credited to a followed concealment-type SP, behind two guards (below) | guarded slice; luck-of-attention residual named and accepted | as built (2026-07-13; SPs are typed `sp_type=concealment` at synthesis, so legacy untyped stores earn nothing here) |
| Night | investigator | **+** threat found · miss **neutral**, never − | raw find-rate is a validated *null*; the validated construct is conversion (`investigator_find_to_lynch_rate`, basket member) — **ruled 2026-07-13: keep neutral-miss** | as built |
| Night | vigilante | **+** threat shot · **−** friendly fire · held bullet neutral | both sides: friendly fire −0.29 (N=180, validated error-companion); landed wolf-kills rate +0.16 (p=.035, validated secondary); threat-hit rate +0.18 (n.s., n=53 — directional, logically-anchored) | as built |
| Night | wolf / SK | **+** power-role-or-threat kill · plain-townie kill neutral | direct positives: `wolf_power_kill_rate` +0.31 (p=.002, `sk_lynched=1` stratum; pooled ~null) · `sk_power_roles_killed` +0.32; mirror ★ `power_roles_killed_by_evil` −0.40 from the town ledger | as built |
| Night | healer | **+** saved a town player who was actually attacked · **−** shielded a threat from an attack · heal on an unattacked player neutral | ★ `healer_town_save_rate` +0.36/+0.33 (v5), **+0.40 at N=180**; the friendly-fire split validates negative | as built (2026-07-13) |

Rationale for the rows that aren't self-evident:

- **Abstain is neutral, not negative** (town): inaction is its own failure mode, but collapsing it
  into − would make "did nothing" indistinguishable from "spent town's one removal tool on a
  townmate," which is strictly worse.
- **Wolf day skill is blending, and plurality-matching is bussing-aware by construction.** The rule
  is a lookup against the day's final `vote_counts` plurality (abstain-majority counts; not
  conditioned on whether the lynch landed). When the room is already lynching your packmate,
  blending *means* voting the packmate — the correct cover play. A naive "voted an ally = negative"
  rule would punish exactly the sophisticated move.
- **Blend and steering never net** (ruled 2026-07-13). A deliberate off-plurality frame scores
  blend-negative *and* may score move-grain positive; both fire, because they measure different
  skills (concealment vs steering) and the real wolf skill is choosing *when* to do which — a
  late-game off-plurality gamble that protects parity must surface as (blend −, steer +), not be
  averaged to zero.
- **The move-grain rule has a failed ancestor, and the difference is load-bearing.** A
  deterministic per-turn advocacy credit — "score every accusation exactly as a vote at its target"
  — was built and measured in June (tagger log §1b) and failed its pre-registered gate. Not because
  the arithmetic was wrong, but because it could not stand *alone*: only accusatory turns are
  scorable at all, just 41 SPs survived the ≥3-turn support filter (too thin for any held-out
  check), and what signal remained duplicated the vote channel. v1 does not re-run that bet. The
  credited floor is the day-grain endpoint (validated held-out +0.51), and move-grain reuses the
  advocacy primitive only as a *refinement on top* — sharpening attribution where a stance-tagged
  push exists, falling back to the endpoint everywhere else, never asked to rank SPs by itself.
  What was *not* revived from June is influence scoring (did the push move the room?); that is
  first-link's job, and it stays a diagnostic (§5).
- **The endpoint carries a self-lynch guard** (wiring catch, 2026-07-13): the reused vote rule is
  blind to the actor being the day's lynch — a lynched SK's followed discussion SPs would have read
  "positive" under "any non-self lynch." The endpoint scores the actor's own lynch as negative first,
  before any other rule.
- **SK day generosity is a known hole, accepted.** Any non-self lynch scores +, so a healer
  mislynch and a wolf lynch look identical. Ruled acceptable for v1 because the channel is
  sign-safe and SK day-skill now has a better home (the concealment floor); revisit after the
  first compounding run.
- **The investigator's real value is conversion, not finding** — the validated proxies say so (raw
  find-rate null; find→lynch validated). Night credit therefore stays generous (miss neutral), and
  whether an investigator's *push* moved the room is a transmission question handled in §5.
- **Night-confirmation → day-lynch conversion is credited piecewise, never as a linked bonus.**
  Three night actions privately confirm a threat without removing it: the investigator's find, and
  the vigilante's or (since this epoch's whiff disclosure) the wolf's attack on the night-immune
  SK — the target survives, which is itself the confirmation. Each step of cashing that knowledge
  in already has its own channel: the night action earns **+** for picking a threat
  (`_night_credit` grades the choice, not the kill), a day push at the confirmed player earns
  through move-grain if the lynch lands, and the vote earns through the vote channel. What is
  deliberately NOT paid is a bonus for the chain *as a chain* ("you knew, then it died"): the join
  "confirmed player was later lynched" cannot tell cause from coincidence, which is exactly the
  influence claim reserved for the ablation-replay gate (§5). The chain is instead measured at
  game grain, in the metrics layer: investigator find→lynch ★ +0.40 (validated, N=180); the
  vigilante `skconfirm` mirror r=+0.48 but n=9 (far too thin); the wolf mirror added 2026-07-14,
  untestable on the archive (wolves only learned of the whiff this epoch). The pattern behind all
  of this is one rule: a night action that **changes the board** carries win signal alone (landed
  wolf-kill +0.16 validated); one that only **produces knowledge** is ~null alone (raw SK-shots
  r≈+0.04) and pays its faction only through conversion. Night credit's + for the SK-shot is
  therefore knowingly generous — it rewards a correct choice whose win-value hangs on a
  conversion credit does not track, the same generosity as the investigator's find.
- **The healer rule mirrors its validated construct exactly.** A save is observable only when the
  heal target was attacked that night (by any attacker — wolf, SK, or the vigilante's mistake) and
  survived; the validated split is *who* was saved: a town save is the good-play half (★ basket
  member), shielding a threat is the validated error half. An unattacked heal is a prediction miss,
  neutral like the held bullet. This channel sat uncredited behind a stale blocker: the rule needs
  the attack-join from `night_resolutions`, and the credit pass historically read only eval dumps —
  but the wolf-blend rule already made it load each game record, so the join is now a free lookup
  (`night_resolutions` carries `healer_target`, both attacker targets, `vigilante_target`,
  `deaths`). Ruled into v1 on 2026-07-13.
- **`sp_type` is a new schema field, added for the concealment channel** (2026-07-13,
  `Agents/schemas/memory.py`): every synthesized SP is now stamped `general`, `concealment`, or
  `risk_policy`, and the concealment floor pays only `concealment`-typed SPs — one SP family, one
  instrument, so a generic wolf SP can never farm the suspicion-delta. Legacy stores predate the
  stamp, default to `general`, and earn nothing here until re-synthesized.
- **The concealment floor's two guards** exist because the naive score ("low suspicion + survived")
  collapses into "won," most completely for the SK. Guard 1: normalize by the day's total
  accusation volume, so a day when the room was busy elsewhere credits nobody's concealment.
  Guard 2: the agent must have spoken that day, so silence cannot farm the credit. The residual —
  believed-because-plausible vs believed-because-unscrutinized — is named, accepted, and assigned
  to the diagnostic tagger, never to credit.

### The read-partition (as built 2026-07-13)

One uniform rule sits on top of the night and targeted-day rows: **if the actor's own stated read
on the target turns out wrong, the outcome is excluded from the SP ledger and the read ledger
(Brier) takes the penalty instead.** A tactic is a procedure over a belief; when the belief was
wrong, the outcome says nothing about the procedure. The worked case: a vigilante follows "shoot
your highest-confidence threat," shoots a player it read as the SK, and the player is town.
Without the partition, the SP eats a −1 for a failure that belongs to the read; with it, the SP
gets nothing and the wrong read is penalized where reads are measured.

Three boundaries keep the rule honest:

- **It fires only on a stated-and-wrong read** (the per-target read list makes this a lookup). No
  stated read, or only a low-confidence one, means the outcome credits normally — exclusion
  requires evidence of a wrong belief, not the absence of one.
- **It applies uniformly but visibly matters in two places**: the vigilante shot and town's
  targeted day moves. The other night channels have no negative outcome to rescue (miss and filler
  kill are already neutral), so there the partition is nearly a no-op — implemented anyway, as one
  code path that cannot drift.
- **It never applies to deceivers or to risk policies.** Deception decouples belief from move (a
  wolf can correctly read a villager and frame them anyway), so deceiver moves are scored by the
  two move-grain questions alone. And an SP whose whole point is acting under uncertainty ("at
  parity, shoot even when unsure") prices its misses in — excluding its read-wrong instances would
  delete exactly the cases the policy exists to manage, so such SPs score as an aggregate over
  every firing.

### Step 3 — baseline: subtract what happens anyway (as built)

A raw followed-outcome rate is a **level**, and a level can be free. The standing example: the
last-standing SK's night kill lands almost every night no matter how well it played, so any SP it
followed would look brilliant on raw outcomes. Every channel is therefore differenced against the
**same cell's memory-OFF base rate** (`baselined_sum += value − base_rate`) — credit measures what
following the SP added *over the ambient rate of that role and phase without memory*.

The invariant that guards this: `invariants.py::assert_baseline_coherence` — every credited channel
must be differenced against a base produced by the **same grading instrument** on the OFF arm. A
level graded by one instrument minus a floor graded by another masquerades as lift; this error
class was caught three times before the invariant made it structural. The tell ledger's cast-prior
baseline (§4) registers as a second baseline *family* under the same invariant.

### Step 4 — shrinkage and windowing (as built)

Thin evidence flatters. An SP followed twice with two lucky positives must not outrank one followed
twenty times at a modest rate, so the ranked quantity is the lift pulled toward zero in proportion
to support: `shrunk = lift × follow/(follow + K)`, `SHRINK_K = 5` — empirical-Bayes damping. The
construction reproduces out of sample (held-out reproduction r=+0.54, n=31 SPs). Counts are
**recomputed over a rolling window each tick** (set, not accumulated), so stale credit ages out as
the meta shifts; out-of-window and never-followed SPs are zeroed by the same pass.

## 4. The tell ledger (as built 2026-07-13)

A **tell** is a falsifiable `behavior → role` claim, stored as an atomic list item — e.g. *"voted a
player who had drawn no discussion" → evil*. Its credit is its **empirical accuracy**: of all
players who exhibited the behavior, what fraction were evil, minus the cast prior (3 evil of 9), so
a behavior everyone exhibits prices itself to zero. The same shrinkage as SPs (K=5) damps thin
support. Sign is direction: positive lift marks evil, negative lift marks town.

What makes this ledger structurally different from the SP ledger is that it is **off-policy**: the
detector counts every exhibitor in every game, so a tell earns or loses credit whether or not it
was ever shown to an agent. That is why the injected book needs no exploration slot — candidates
mature in the background for free — and why tell credit needed no follow join.

The counting instrument is the **role-blind behavior detector**: per game, per player, per channel,
it marks which checklist behaviors are present in the transcript, blind to roles (otherwise the
hit-rate is circular — "the wolf did wolf-things"). As built and certified: temp-0 flash-lite,
cached k=2 union (a full-view pass plus a vote-tally-stripped split-view pass), measured against
the temp golden at 0.93 precision / 87% recall on discussion and 0.83/77% on vote cells, and
against the owner's detector-blind adjudication of game 1 at 7/8 precision. Provisional
(AI-adjudicated) labels were **ruled sufficient to wire credit on** (2026-07-13); the remaining
owner golden games are an upgrade path, not a gate. Detection overhead ≈ $0.17–0.20/game.

One valence ruling governs what the ledger pays out (**ruled 2026-07-13**): **positive-lift tells
only; town-markers stay diagnostic.** A tell's negative evil-lift *is* its positive town-signal
read from the other side — faction shares are complementary — so crediting both directions counts
one piece of information twice. And paying agents for "looking town" is farmable by a compounding
loop: it optimizes appearance rather than outcomes.

Tell lifecycle (mining, dedup-at-fold, probation, the frozen checklist epochs) is the fold's
mechanism, specified in the design record's ledger spec; this doc owns only the credit arithmetic.

## 5. What stays diagnostic — and the one promotion gate

Two instruments run alongside credit without touching it, plus the retired one:

- **The tagger** (as built): the omniscient per-day LLM verdict keeps running as a watch metric —
  its validated readout (discussion-verdict partial r +0.56 wolf / +0.60 SK with faction win,
  N=24, single epoch) covers exactly the residual credit cannot see: credibility, tone, diffuse
  concealment beyond the floor. Its **night read-quality override is retired** — night credit is
  the deterministic scorer above, refined by the read-partition — so the loop carries one night
  mechanism instead of two.
- **First-link read-delta** (as built 2026-07-13 — computed, uncredited): did an addressed player's next stated read
  move the way the push intended? It carries a momentum adjustment (subtract the target's
  pre-utterance trend, so joining a pile-on scores ~0) and two named caveats: ~40% of "unchanged"
  read entries are cold filler (undercounts deltas), and the delta lattice is coarse. Its job is to
  show whether move-level attribution discriminates driver from rider better than the day-grain
  smear.
- **Within-day trajectory shift** (owner-directed 2026-07-13): the room's stance toward a target
  before vs after the first informed push — observational, confounded, diagnostic-grade.

The line between these and the credited move-grain channel is *causality*. The credited channel
scores facts (the lynch landed on the pushed target; the target was worth pushing). The
diagnostics try to measure *influence* — whether the push moved the room. Influence claims get
credited only through the pre-registered promotion gate: **ablation replay** — checkpoint just
before a push, replay the day's remainder with the push present vs removed on paired seeds, compare
P(target lynched). The same gate serves the wolf steering channel. It is not funded until the
diagnostics show pushes that look load-bearing.

## 6. Known gaps and open work

Ordered by criticality; all freshness-dated 2026-07-13.

1. **Injection-channel replay screen — RUN 2026-07-13, channel ALIVE.** 40 frozen v6ab day-vote
   decisions replayed ± the book through the real injection path: 27.5% of decisions changed under
   the (channel-balanced) book, discordant pairs 5 wrong→right vs 1 right→wrong — direction positive,
   magnitude not established (n=6 discordant; old-epoch decisions). The hedge behind dropping
   observation injection is discharged: a flat compounding result cannot be blamed on a dead
   delivery channel. Record: tell_extraction log §17 + `outputs/book_screen*.json`.
2. **Cross-epoch seed book — open, near-free.** The v1 book seeds from tells mined on the v6ab
   archive, but the run executes in the 2026-07-09 prompt epoch, and one family (role-claim,
   0/28 evil held-out) is already known epoch-fragile. Spot-check head tells on current-epoch games
   (piggybacks on gap 1's games) or curate the seed conservatively.
3. **Self-report attribution spot-check — DONE 2026-07-13** (§3 Step 1): 13/15 enacted; the
   pass-while-claiming-follow failure it surfaced is now structurally closed by the pass-gate.
   Caveat: AI-adjudicated (owner spot-adjudication is the upgrade path, same as the tell goldens).
4. **Post-run / conditional:** the ablation replay (funded only if §5 diagnostics warrant), the
   outcome-blind tactic matcher and its golden set, the conditioned tell split (if
   stage-conditional hit-rates diverge), detector k=2→k=1 (cost, once stability data accumulates),
   owner golden g2–g6 (label upgrade path).

## Sources

- Code (maintained): `evaluation/src/loop/decision_scoring.py` · `credit_backfill.py` · `credit.py`
  · `invariants.py` · `consolidate.py` · `read_ledger.py` · `first_link.py` · `tells.py` ·
  `tell_credit.py` · `tell_fold.py` · `Agents/memory/tell_book.py` — module table in
  [`evaluation/src/loop/README.md`](../../evaluation/src/loop/README.md). Healer construct
  reference: `Agents/compute_metrics.py` (healer save split).
- Validation cited: G2/G3a (`evaluation/src/instrument_validation/credit/`), held-out credit
  reproduction (same package), the proxy campaigns
  ([`../metrics/candidate_ledger.md`](../metrics/candidate_ledger.md)), detector goldens
  (`../extraction/tell_extraction/`, log §13–16).
- Design lineage: [`read_tactic_credit_redesign.md`](read_tactic_credit_redesign.md)
  (the 2026-07-11 decision record this doc implements) · owner rulings 2026-07-11→13 recorded
  inline above.
