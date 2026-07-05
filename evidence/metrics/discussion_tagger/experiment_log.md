# Discussion Tagger — chronological overview

**What this is.** The spine of the discussion-tagger workstream, in the order it happened: why discussion was
the one part of play nothing could score, why two deterministic attempts to score it failed, how the LLM
tagger was designed to fill exactly the gap they left, and how its validity claim was cut down three times
under adversarial review before the replacement claim was allowed to stand. It ends where
[report.md](report.md) begins — that companion doc is the current shipped mechanism; how far the instrument is
*trusted* is owned by the apparatus report
[../../evaluation/discussion_tagger/report.md](../../evaluation/discussion_tagger/report.md).

**Reading contract.** Sections are in time order and each states what it tested and what it found. The arc
keeps its real corrections in place rather than smoothing them: a deterministic metric that came back null
(§2), a first credit wiring that paid for what was already free (§4), and a headline number that had to be
**retracted as a halo** before a *different*, adjacent number was validated as skill (§6). `(§N)` markers are
navigation, not chronology-of-record. The raw run records this arc distils from are frozen in
[../../v7_final/experiment_log.md](../../v7_final/experiment_log.md) §12 and the sibling metrics files
([../discussion_scoring_plan.md](../discussion_scoring_plan.md),
[../discussion_lead_vs_blend.py](../discussion_lead_vs_blend.py)); this log points at them, it does not copy
them.

---

## 0 · Origin — why discussion was invisible

Every metric the project had scored the **board**: votes, kills, lynches, protections. Nothing scored the
**discussion** that drives the board. As the discussion-scoring plan put it (2026-06-18): *"A wolf can talk
its way out of a corner and the scorecard only sees whether it was eventually lynched; a villager can lead the
room to the right read and we only see the vote. Discussion is the highest-leverage, lowest-observability part
of the game and is currently invisible."* For the v7 compounding loop this was not cosmetic: the loop credits
strategy points by de-lucked decision outcomes, and the entire day-discussion channel had no verdict to credit
against. A wolf's memory could only ever be rewarded for its votes and kills, never for the deception that is
its actual craft.

## 1 · Why a deterministic proxy structurally can't judge discussion

The deterministic proxy system was the right default and deserves credit before its failure mode: it is free,
it is de-lucked by construction (it scores decisions against true roles, not against who won), and it cleanly
covers the *outcomes* of six of the seven discussion primitives — accuse, lead, defend, blend, deflect, claim
all leave a trace in votes or roles. The problem is the seventh, and it is the one that matters most for
deceivers.

- **Wolf day-offense is unmeasurable from the board.** A deterministic `wolf_steering_rate` cannot distinguish
  *leading* a bandwagon from *joining* one — voting where the town was already headed looks identical to
  driving it ([../deceiver_metric_refinement.md](../deceiver_metric_refinement.md)). The honest reframe was
  "night-offense null, day-offense **unmeasured**."
- **Concealment credit is tautological.** For the night-immune serial killer, "votes drawn at me" is the
  precursor to its only removal, so `suspicion_drawn` ≈ "lost," and it is literally `town_vote_accuracy` read
  from the other seat — "town voted well" and "the SK concealed poorly" are one event. Any deterministic
  concealment score collapses into the outcome it was supposed to be independent of (the halo).
- **Framing is the primitive determinism can't even *detect*.** Town value is roughly transmission + correct
  offense, both verifiable against roles and votes — tractable and cheap. Deceiver value is *concealment*, and
  framing/credibility/deception-quality leave no deterministic trace. This is the root cause the rest of the
  workstream aims at: **the deterministic proxies are sufficient for town and for night outcomes, and
  structurally blind to deceiver day-discussion merit.**

## 2 · The deterministic predecessors, in place (d0)

Before spending on an LLM, two zero-cost deterministic attempts were built and measured. Both are kept here
because their failure is what justified the tagger.

**(a) Lead-vs-blend — the discourse infra works, the signal is null.** `discussion_lead_vs_blend.py`
(2026-06-18, 180 games) split wolf day-offense into *lead* (accusing the eventual mislynch target early in the
sequence) vs *blend* (joining a forming pile), reconstructed from `addressed_targets`.

*Catches: does active wolf day-offense carry any win signal the votes miss?* Result:

```
wolf_steering_rate   r=+0.308 p=0.0008 n=116
wolf_blend_rate      r=+0.270 p=0.0004 n=165
wolf_lead_score      r=-0.093 p=0.5075 n=53   NULL
wolf_lead_binary     r=-0.122 p=0.3840 n=53   NULL
```

The infrastructure passed — lead-vs-blend is genuinely distinct from the vote metrics (|r| < 0.06 from both) —
but **active wolf offense carries no win signal, and it barely happens**: in 127 of 180 games *no* wolf
publicly accused the eventual town-mislynch target, and 109 of 169 mislynch days had *no wolf among the
accusers* at all. The town mostly self-destructs. So the free active-offense signal is not just weak, it is
mostly absent. **Gate A fails, cleanly.**

**(b) Advocacy-only credit — computable but thin.** `discussion_credit_deterministic.py` (2026-06-19) credited
day-discussion strategy points on the one cleanly per-SP-computable deterministic signal — *advocacy
correctness*, scoring each accusation faction-relative against the accused's true role ("an accusation is a
vote in words," reusing `credit_backfill._vote_credit`).

*Catches: is there enough deterministic per-SP discussion signal to skip the LLM entirely?* No — only
accusatory turns are creditable, yielding just **41** discussion SPs with ≥3 advocacy-follows; the held-out
reproduction was underpowered and the signal was redundant with votes (target-correctness, not
discussion-specific). Transmission credit was blocked outright (it needs persisted role claims), and heat
credit was per-day and tautological (§1).

**The d0 decision, and the free floor it settled.** The free deterministic advocacy signal was thin and
redundant; the free lead-vs-blend signal was null → the workstream **committed to building the LLM tagger**
("d-full"). But first it pinned a *broader* free baseline the paid tagger would have to beat:
`discussion_coverage_check.py` credited **every** followed discussion SP by the day's faction-relative lynch
outcome — the **day-vote endpoint**, team-aware, covering all turns rather than only accusatory ones. This
floor credited **100 discussion SPs (2.4× the advocacy-only 41), held-out Pearson +0.51** ≈ the board's +0.54,
and a companion check found deceivers night-kill power roles without visible day-heat (wolves→power 71%,
SK→power 62%) — a vote-blind "hidden read" worth wiring. **This day-vote floor became the validated default
("floor" mode); the tagger had to earn its cost against it.**

## 3 · Designing the LLM tagger

The design (`discussion_credit_design.md`, 2026-06-19,
[../../v7_final/discussion_credit_design.md](../../v7_final/discussion_credit_design.md)) is stated here by
construction; whether the construction *worked* is §4's job.

- **Granularity ladder — "tag fine, credit coarse."** Seven primitives (accuse / frame / lead / defend /
  blend / deflect / claim) collapse into three axes (offense / defense / transmission) and finally into **one
  holistic verdict** per turn. The fine tags are the *detection vocabulary*; credit stays coarse (one value
  per turn) to avoid the per-dimension density trap that spreads a weak signal into noise.
- **Structure-not-valence, and omniscient.** The pass runs post-game with true roles revealed, so it can *emit
  structure* (framing, credibility, role-reveal) reliably; **valence stays on observable behavior + true
  roles**, never on a player's own account, because LLMs confabulate self-serving rationales.
- **All-required schema.** Flash-lite silently drops optional/nullable fields, so every field is mandatory —
  a constraint that shaped the schema, not an afterthought.
- **De-luck by construction.** The reward is `verdict − base_rate`, base 0 — never the game's win/loss. A good
  play in a lost game is still positive; the halo the deterministic concealment metrics collapsed into (§1) is
  designed out at the reward level.

Four critique-round amendments (A1–A4, same day) shaped it: **A1** — framing/credibility need only an
end-of-day pass, not per-message; **A2** — *determinism ⊥ halo*: the fact that "concealed = heat-low +
survived" is deterministically *computable* makes it cheap, **not** safe to credit (the passive-SK tautology),
so concealment keeps the de-halo brackets regardless; **A3** — add the night-action *exposure* endpoint
(reveal-risk / confirm-out / hidden read the day-vote can't see); **A4** — feed each agent's own
`updated_strategy` reasoning in for **attribution only** (de-confound a night target, surface an unvoiced
read, trace influence), with valence still deterministic. The tagger was fully built the same day
(`discussion_tagger.py`, commit `c038bd5`), wired into the loop's per-SP credit engine alongside the vote and
night channels; the wolf vote channel was scored **blend-aware** (a wolf voting the room's plurality is
positive — the validated signal — not scored by target).

## 4 · Verify → decide: does the tagger earn its keep?

The risk after §3 was the obvious one: *the tagger might just re-derive the free floor at a price.*
`tagger_effectiveness.py` (2026-06-19, 8 games,
[../../v7_final/tagger_effectiveness.py](../../v7_final/tagger_effectiveness.py)) tested exactly that, with two
de-luck probes — halo (does the verdict just track who won) and **redundancy** (does it just track the free
day-vote floor).

*Catches: is the paid signal anything the free floor doesn't already give?* The first wiring failed the test:

- **Merit-only discussion verdict** — halo **+0.21**, redundancy with the free floor **+0.55**. Poor ROI:
  paying flash-lite to reproduce a free signal.
- **Enriched verdict** (the holistic verdict *weighing* framing/credibility/role-reveal) — halo **+0.11**,
  redundancy **+0.34** (down from +0.55). Now it adds the concealment axes the floor structurally can't see.
- **Night read-quality** — halo +0.12, and it **reassigns ~31% of night actions**: 30 skilled misses
  *credited* and 12 lucky hits *demoted* vs the outcome-only deterministic night credit. No free signal exists
  for read quality, so this is where the paid tagger is irreplaceable.

**Decision:** the tagger earns its keep on its *unique* axes — framing-weighted discussion + night
read-quality — not the merit-only day-credit first wired. The holistic (enriched) verdict became the credited
field, and the `discussion_mode` default flipped **floor → tagger** (2026-06-20, commit `d7eaa45`). This is
also why `report.md` insists only the holistic `verdict` feeds credit: the sub-tags are what *make* it
enriched, but crediting them separately was the poor-ROI path already rejected here.

## 5 · Correctness pass — are the tags actually right?

With the tagger credited, the next risk was silent per-field error. `tagger_accuracy.py` (2026-06-20, 8 games,
[../../v7_final/tagger_accuracy.py](../../v7_final/tagger_accuracy.py)) cross-checked the structure tags — not
their effectiveness, their *correctness*.

*Catches: does the tagger hallucinate framing/role-claims, or read them from the actual game?*
`framing=manipulative` skewed exactly as it should against true roles — **town 7% / wolf 85% / SK 88%** — and
credibility was non-degenerate. But `role_reveal` was **regex-soft**: cross-tabbed against a first-person
self-claim regex on raw chat, it missed implicit claims and risked hallucinating them. The fix was *at the
source*, not in the tagger prompt: persist the in-game structured `DaySummary.role_claims` (gameplay-neutral,
2026-06-20) and **anchor** `role_reveal`/credibility on it — a claim whose declared role ≠ true role is a
deception tell. This is why the shipped contract (`report.md`) states role-reveal is anchored on structured
extraction with only a raw-message *fallback* for pre-anchor records.

## 6 · The v2 run — a retraction, then a validation

The v2 loop run (2026-06-22–23, `all_enabled` vs `all_disabled`) is where the tagger's headline was both
*broken* and *rebuilt*, and the distinction is the most important thing in this log.

**The retraction (§12f).** A "+0.556 discussion gain" had been read off the credited store for the town
`villager/day_discussion` cell. It was **retracted as a halo.** It was an *undifferenced credit level* — raw
`(positive − negative)/follow` with the tagger base pinned at 0 — never differenced against the no-memory arm.
Positive tagger verdicts occur *with or without* memory (the exact halo the design warned of, §1/A2), and it
was compounded by a `game_id`/tag-cache collision (the ON and OFF arms shared a `game_id`, so the cache served
ON-arm tags to the OFF arm — one of the two bugs that invalidated the town question of that run). When
differenced properly via the free day-vote floor (valid in *both* arms), villager/day_discussion on−off was
pure noise (mean ≈ −0.12).

**The validation (§12g).** A separate, adversarial investigation asked whether the tagger's *discussion
verdict* carries real skill. It was held to a far higher bar than the retracted number ever was —
`tagger_skill_retest.py` ([../../v7_final/v2_full/tagger_skill_retest.py](../../v7_final/v2_full/tagger_skill_retest.py)),
N=24 ON games:

*Catches: is the wolf/SK discussion signal outcome-leak, wordiness, or real skill?*

| faction | (A) outcome-in \| de-luck | (B) **blinded** \| de-luck | (C) **blinded + verbosity-controlled** |
|---|---|---|---|
| **wolf** | +0.60 | +0.58 | **+0.56** |
| **serial_killer** | +0.55 | +0.55 | **+0.60** |
| **town** | +0.07 | +0.06 | **+0.02** |

The wolf/SK discussion signal **survives blinding the tagger to the outcome and partialling out message
verbosity** → it is real deceiver skill the vote proxy cannot see, not leak and not wordiness. Town adds ~0 —
its skill *is* the vote proxy, the negative control.

And the leak the retraction implied was measured directly, not assumed: `tagger_deleak_ablation.py`
([../../v7_final/v2_full/tagger_deleak_ablation.py](../../v7_final/v2_full/tagger_deleak_ablation.py)) ran a
**2×2** (outcome shown/withheld × all/speakers-only, N=6). *Catches: how much of the day-local coupling is the
tagger simply seeing who won?* Withholding the vote and deaths moved the coupling **+0.07 town / −0.02 wolf /
~0 SK** — negligible — and the mechanical silent-player effect was ~0 (the tagger barely tags non-speakers,
2/86). The 2×2 was necessary because a one-armed re-tag confounds the outcome axis with the silent-player
axis. **Decision:** keep `show_outcome=True` (blinding bought within-noise gain at the cost of the night
verdict's legitimate lynch context); bump the tag cache `v1 → v2`.

**+0.556 vs +0.56 — the two numbers are not the same claim.** They are numerically adjacent and this is exactly
why they get confused; they measure different things, on different factions, with opposite status:

| | +0.556 (retracted) | +0.56 (validated) |
|---|---|---|
| quantity | undifferenced **credit level** `(pos−neg)/follow` | **partial *r*** of verdict with faction-**win** |
| faction | **town** villager/day_discussion | **wolf** (SK = +0.60) |
| controls | none (never differenced vs no-memory) | blinded to outcome + verbosity partialled out |
| status | **halo → retracted** | **real skill → validated** |

The corroboration is internal: the *skill* column for **town** is +0.02 — the tagger adds nothing for the very
faction whose "+0.556" halo was retracted. There is no contradiction between the two, only a naming trap.

## 7 · Hardening and graduation (2026-07-02)

A code+evidence review flagged the tagger as load-bearing (the paid credit signal rides it) yet failing
silently, and closed three paths ([../../evaluation/hardening_pass/experiment_log.md](../../evaluation/hardening_pass/experiment_log.md)
§4.2–4.4):

- **Per-day LLM failure was swallowed** → now collected and surfaced as an end-of-game `logger.error` counting
  degraded days, with a `strict` mode that re-raises.
- **Missing eval-cases sidecar silently emptied `role_claims`/`private_reads`** → now warns loudly once per
  game.
- **The tag cache could serve one arm's tags to the other** (the §6 collision) → a session/trace provenance
  slug is folded into the cache key *and* asserted on read, re-tagging fresh on mismatch.

The load-bearing validation numbers had also lived only as stdout; the retest/ablation scripts now *also*
write `*_results.json` (statistics untouched, not re-run — so the JSON is not yet on disk; the durable record
remains v7_final §12g). Finally the three validation scripts (accuracy / skill / deleak) were **graduated**
into one config-driven runner, `eval-tagger`
([../../../evaluation/src/cli_runner/discussion_tagger_eval.py](../../../evaluation/src/cli_runner/discussion_tagger_eval.py),
modes `accuracy | skill | deleak`); the frozen v2_full scripts stay in place as dated evidence.
`tagger_effectiveness.py` (§4) was not graduated and remains a frozen script.

## 8 · Limitations and future work (freshness: 2026-07-04)

Ordered by criticality (likelihood × impact × detectability); minor gaps are kept, not deleted.

1. **Metric, not a memory verdict (Med-High).** The tagger is a *validated instrument*, not evidence that
   wolf/SK memory compounds. The v2 run that produced its numbers was mis-configured to all-factions-on,
   confounding the town question and never isolating a wolf memory-on/off contrast. Converting the tentative
   wolf signal into a memory *verdict* needs a **direct wolf SP/obs A/B** — never run — with the tagger as its
   discussion-merit ruler.
2. **Uncalibrated per-field (Med).** No human golden behind `framing`/`credibility`/`role_reveal`; they are
   distributionally sane and face-valid, never label-validated. The credited holistic `verdict` is validated
   correlationally; the sub-tags are not. The cheapest independent upgrade is a small golden.
3. **Single-epoch, N=24 (Med).** The +0.56/+0.60 rests on one epoch; it would piggyback on a held town-only
   rerun for power and a fresh epoch — closing with gap 1.
4. **Night-verdict residual leak untested (Low).** The night verdict still sees its own kill's death (the
   night analogue of the day leak §6 cleared for discussion). A two-prompt split fixes it only if a clean
   deceiver *night* metric is ever needed; night already has a deterministic de-luck proxy underneath.
5. **Not promoted to the standing scorecard basket (Low).** The tagger lives in the loop credit ledger + its
   own apparatus, not as a standing de-lucked proxy in the metrics basket (the "Phase-2 LLM tagger" the
   discussion-scoring plan deferred). Deliberate, documented.
6. **"flash-lite" is caller-pinned (Low).** `get_llm_pro()`'s bare default is `gemini-2.5-pro`; flash-lite
   holds only under the loop's env pin. Not a live hole (the driver always pins), but a footgun for a
   standalone caller.

**Meta-lesson.** The tagger's validity claim shrank three times under adversarial review — *haloed →
winner-blind → leak negligible* — and only then was the *replacement* claim ("real deceiver skill,
+0.56/+0.60") asserted, held to the same standard (blinded + verbosity-controlled) that broke the numbers
before it. The discipline that makes this workstream trustworthy is not that the first number was right; it is
that the first number was retracted in place, and the number that replaced it had to survive the same knives.

---

*Companion reference (current mechanism): [report.md](report.md) · Trust/reliability apparatus:
[../../evaluation/discussion_tagger/report.md](../../evaluation/discussion_tagger/report.md) · Frozen design +
run records: [../../v7_final/discussion_credit_design.md](../../v7_final/discussion_credit_design.md),
[../../v7_final/experiment_log.md](../../v7_final/experiment_log.md) §12, and the v2_full/ tagger scripts ·
Deterministic prehistory: [../discussion_scoring_plan.md](../discussion_scoring_plan.md),
[../discussion_lead_vs_blend.py](../discussion_lead_vs_blend.py),
[../deceiver_metric_refinement.md](../deceiver_metric_refinement.md). Live code:
[../../../evaluation/src/loop/discussion_tagger.py](../../../evaluation/src/loop/discussion_tagger.py). Written
2026-07-04.*
