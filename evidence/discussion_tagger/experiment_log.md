# Discussion Tagger — chronological overview

> **What this is.** The chronological record of the discussion-tagger workstream — a sequel to the
> credit system. By mid-June 2026 the compounding loop could already credit two of the three kinds of
> decision an agent makes (votes and night actions); day discussion was the third, and nothing could
> score it. This log records the two zero-cost deterministic attempts to score discussion, the measured
> failure of both, the post-mortem showing why that failure is structural for deceivers rather than
> fixable, the LLM tagger designed to cover exactly the residual, and the adversarial reviews that cut
> the tagger's validity claim down three times before a different, adjacent claim was allowed to stand.
> Sections are in time order, and corrections are shown in place rather than edited away: a
> deterministic metric that came back null (§1a), a first credit wiring that paid for what was already
> free (§4), and a headline number retracted as a **halo** — a score that secretly just tracks who won
> (defined properly at §2).
>
> **Companion docs.** The current shipped mechanism, stated destination-first, is
> [report.md](report.md); how far the instrument is *trusted* is owned by the apparatus report
> [../evaluation/discussion_tagger/report.md](../evaluation/discussion_tagger/report.md). The raw run
> records this log distils are frozen in [../v7_final/experiment_log.md](../v7_final/experiment_log.md)
> §11–12 and the metrics design files
> ([../metrics/design/discussion_scoring_plan.md](../metrics/design/discussion_scoring_plan.md),
> [../metrics/design/discussion_lead_vs_blend.py](../metrics/design/discussion_lead_vs_blend.py));
> this log points at them for the data, but tells the story itself.

---

## 0 · The starting point — a credit system with a missing channel (2026-06-18)

The v7 goal is a memory system that compounds. After each game, agents write memories — lessons like
"an early role-claim under pressure is usually fake" — and carry them into later games. A memory item
an agent explicitly chose to follow when making a live decision is called a **strategy point (SP)**.
For the store to get better rather than merely bigger, the loop has to decide which SPs earned their
keep: between generations it **credits** each followed SP by whether the decisions it influenced were
good, then keeps the winners and evicts the rest.

"Good" cannot mean "the game was won." Werewolf outcomes are heavily luck-confounded: a sound vote can
sit in a lost game, and a blunder can be bailed out by a teammate. So credit is **de-lucked**: a
decision is scored against the ground truth the game engine knows, not against the final result.
Mechanically, voting for a player who really is a wolf scores positive whether or not the game was
eventually won. One bound on the term is worth stating now, because §6 turns on it: de-lucking removes
*outcome* luck; it does not remove *opponent strength*. A correct decision against a stronger opposing
lineup still has fewer good options to be correct about.

Every credit channel that existed at this point had what might be called a **direct anchor** — a
concrete board action to hold against that ground truth. A day vote is anchored on the vote itself:
who you voted for, scored against that player's true role. A night action is anchored on the action
taken: the wolf's kill target, the healer's protection, the vigilante's shot, each attributable to one
decision and scored against the target's true role. The loop's two existing credit channels, votes and
night actions, were built on exactly those anchors.

Discussion has neither. In a social-deduction game, talk is most of the play: an effective accusation,
a convincing defense, a clever deflection, or a well-timed role claim can swing where the votes and
the night kills go. But a speech is not a board action — there is no single move it can be lined up
against and scored. The practical consequence for the loop: the entire day-discussion channel had no
verdict to credit SPs against. A wolf's memory could only ever be rewarded for its votes and kills,
never for the deception that is its actual craft; a villager's for its vote, never for the argument
that assembled the room behind that vote. Closing that gap is this workstream
([../metrics/design/discussion_scoring_plan.md](../metrics/design/discussion_scoring_plan.md),
2026-06-18).

## 1 · The free layer first — two deterministic attempts, built and measured (2026-06-18 → 06-19)

The scoring plan staged the work as a ladder with pre-registered gates: build the free deterministic
layer first, and spend on an LLM only if the free layer measurably failed. (Two labels from the frozen
design docs, kept because those docs use them: **d0** is the deterministic-only option, **d-full** the
full LLM tagger.) Both zero-cost attempts are kept here because their failure is what justified the
tagger.

**The raw material — what discussion already leaves on the record.** Discussion is not unscoreable
prose all the way down. Every speaking agent emits, as part of its structured output alongside the
message text, a list of **addressed-target tags**: for each player the message addresses, the form of
address (question / response / mention) and a **stance** — accusation, defense, agreement, or neutral.
These tags persist on the public day transcript (the `day_channel`) together with a monotonic **`seq`**
number that orders utterances within the day. One real entry, lifted from the batch the tests below
ran on (`batch_results/v6ab_townsp.jsonl`, day 4, `seq` 7, message trimmed):

```json
{ "player": "player_1",
  "message": "Player 8, I agree that we should be skeptical of those who were consistently
              hesitant early on [...] Player 3, you ask who is suspicious — I am looking at
              those who remained completely passive during the critical votes against the
              serial killer. [...]",
  "addressed_targets": [
    {"target": "player_8", "addressed_form": "response", "stance": "agreement"},
    {"target": "player_3", "addressed_form": "response", "stance": "accusation"} ] }
```

A deterministic script can therefore already answer questions like "who accused whom, in what order,
and how does that line up with the day's vote?" — a plain join of stance tags to the vote record and
to true roles, with no text parsing anywhere. Both attempts below are built on this material.

### (a) Lead-vs-blend — splitting the one wolf-discussion signal we had

*Derivation.* The only instrument that touched wolf day-play at the time was `wolf_steering_rate`: the
share of days on which the wolf majority's votes landed on the day's lynch. Its known flaw
([../metrics/design/deceiver_metric_refinement.md](../metrics/design/deceiver_metric_refinement.md)):
it is vote-level, so a wolf voting where the town was already headed looks identical to a wolf that
*drove* the town there. The discourse record above makes the two separable. Define a **mislynch day**
as a day the town lynches one of its own. On such days, a wolf **leads** if it publicly accused the
eventual mislynch target early in the accusation sequence — operationalized as
`lead_score = 1 − rank/(n_accusers − 1)`, where rank is the wolf's position among that target's
accusers ordered by `seq`. A wolf **blends** if its vote merely matched the day's lynch, whoever
started the pile.

*Test structure.* `discussion_lead_vs_blend.py` (2026-06-18), run over 180 existing games — no new
generation spend. Per day, order the accusation-stance tags by `seq`, find the mislynch days, compute
each wolf's lead and blend rates, and correlate each metric with whether the wolf faction won the game
(a point-biserial *r*).

*Catches: the plan's pre-registered **Gate A** — does active wolf day-offense carry any win signal the
vote metrics miss?* Reading the numbers: *r* is the correlation with winning (positive = wolves that do
this win more), *p* is the probability the correlation is just noise (below 0.05 is the conventional
bar for "real"), *n* is how many games showed the behavior at all:

```
wolf_steering_rate   r=+0.308 p=0.0008 n=116   vote-level: wolf majority voted the day's mislynch
wolf_blend_rate      r=+0.270 p=0.0004 n=165   vote-level: a wolf's vote matched the day's lynch
wolf_lead_score      r=-0.093 p=0.5075 n=53    discussion-level: accused the mislynch target early   NULL
wolf_lead_binary     r=-0.122 p=0.3840 n=53    discussion-level, binary form                         NULL
```

The infrastructure passed: lead-vs-blend is genuinely distinct from the vote metrics (|r| < 0.06
against both), so the joins and the stance tags work. But **active wolf offense carries no win signal,
and it barely happens**. In 127 of 180 games *no* wolf ever publicly accused the eventual mislynch
target, and 109 of 169 mislynch days had *no wolf among the accusers* at all — the town mostly
self-destructs without wolf help. Note also where the wolf win signal actually lives: steering and
blend are both **vote-level** blending, voting where the room goes, not anything done in the
discussion text. **Gate A fails, cleanly.** The free active-offense signal is not just weak; it is
mostly absent.

### (b) Advocacy-only credit — "an accusation is a vote in words"

*Derivation.* For a discussion turn there is exactly one deterministic per-turn credit signal: if the
turn accuses player X, score it exactly as a vote for X would be scored — against X's true role. This
reuses the vote channel's scoring function directly (`discussion_credit_deterministic.py`, 2026-06-19,
reusing `credit_backfill._vote_credit`).

*Test structure.* Run that scoring over the followed discussion turns in the credit records,
requiring at least 3 followed accusatory turns per SP (fewer is noise), and check whether the
resulting SP ranking predicts outcomes on held-out games — games the credit was not computed from,
the standard check that a ranking generalizes instead of memorizing.

*Catches: is there enough deterministic per-SP discussion signal to skip the LLM entirely?* No, three
ways. Only accusatory turns can be scored at all, and after the ≥3-turn filter just **41** discussion
SPs remained — too few for the held-out check to have any power. What signal existed duplicated the
vote channel: target-correctness again, nothing discussion-specific. And the other two deterministic
candidates were dead on arrival. *Transmission* credit (a role claim converting into the right lynch —
the investigator's core value) had nothing to join on, because the structured `role_claims` the
day-summary model computes were being flattened to prose before being saved; the structure was
restored and persisted later (§5). *Heat* credit (scoring concealment by how much suspicion a player
drew) was rejected on the tautology §2 lays out — a suspicion score largely restates who won.

### The decision, and the free floor it settled

Both free options had now failed: advocacy credit thin and redundant (b), lead-vs-blend null (a). So
the workstream **committed to the LLM tagger** (d-full). But first it pinned the strongest free
baseline the paid tagger would have to beat. `discussion_coverage_check.py` credited **every** followed
discussion turn, not just accusatory ones, by one blunt endpoint: did that day's lynch go the
speaker's faction's way? This is the **day-vote endpoint** — the day's one collective outcome, used as
the verdict for every speech that fed it. The floor covered **100 discussion SPs** (2.4× the
advocacy-only 41), and its credit predicted held-out game outcomes nearly as well as the board metrics
themselves (Pearson **+0.51** vs the board's +0.54). That is a genuinely strong free baseline.

A companion check also previewed why no vote-anchored floor can ever be *sufficient*: deceivers often
night-kill power roles they never once challenged in daytime discussion (wolves→power 71%, SK→power
62%). That is a read formed *during* discussion whose only observable consequence is a night action —
invisible to any credit anchored on the day vote. **This day-vote floor became the validated free
default; the tagger had to earn its cost against it (§4).**

## 2 · Post-mortem — why no deterministic proxy can judge deceiver discussion (2026-06-18 → 06-19)

The free layer was the right default and deserves the credit before the diagnosis: it is free, and it
is de-lucked by construction, since everything it scores is scored against true roles rather than
against who won. For most of discussion it genuinely covers the *outcomes*. An accusation lands as a
stance tag and can be scored like a vote (§1b). A role claim, once persisted, resolves against true
roles. Leading and blending show up in the vote and accusation order (§1a). Town's discussion value
mostly cashes out in exactly those places — a villager talks in order to shape votes, and the votes
are scored.

So why commit to a paid instrument instead of iterating on the free one? Because §1's failures are not
measurement gaps that a better formula fixes. Sorted by what the board can see, every discussion
behavior lands in one of three statuses:

1. **Outcome covered.** Acts whose consequences land on the board — accusations, claims, vote
   steering. Deterministic scoring works here, and it is cheap. This is most of *town's* value.
2. **Computable but tautological: concealment.** Take the serial killer, the cleanest case. The SK is
   immune to night kills, so the day vote is the *only* way it ever dies. Try to score its concealment
   with the obvious deterministic metric, `suspicion_drawn` — how many votes it attracted. A high
   score means the town was closing in, which for a player only the vote can kill is just "it lost"
   restated. Worse, those same votes are what the town's accuracy is scored on: "the town voted well
   at the SK" and "the SK concealed poorly" are one event counted from two seats, never two
   independent pieces of evidence. Any deterministic concealment score therefore collapses into the
   outcome it was supposed to be independent of. This log calls that failure mode a **halo** — a score
   that looks like it measures skill but secretly just tracks who won — and it recurs at every turn of
   the story (§4, §6).
3. **No trace at all: the qualities of deceiver play.** Whether a wolf's story was *believed*; whether
   its defense was a plausible cover or an obvious flail; whether an accusation stuck because of the
   narrative built around it. Nothing on the board records any of this. Determinism cannot even
   *detect* these qualities, let alone credit them.

Deceiver value is concealment and credibility — statuses 2 and 3. Town value is mostly status 1. That
asymmetry is the root cause the rest of the workstream aims at: **the deterministic proxies are
sufficient for town and for night outcomes, and structurally blind to deceiver day-discussion merit.**
(The offense half of the question was already answered empirically, not structurally: §1a *measured*
active wolf day-offense and found it null and rare — so what remained genuinely open was exactly the
concealment side.)

## 3 · Designing the LLM tagger (2026-06-19)

§1 and §2 fixed the design's requirements before a line of it was drafted: the paid instrument must
cover exactly what the free layer cannot (concealment quality, credibility, the vote-invisible night
consequences), must not re-derive what the floor already gives for free, and must never let its
verdict collapse into the outcome. The design (`discussion_credit_design.md`, 2026-06-19,
[../v7_final/discussion_credit_design.md](../v7_final/discussion_credit_design.md)) is stated here as
it was proposed; whether the construction *worked* is §4's job.

**First, a vocabulary — the seven primitives.** The design work started by asking, role by role, what
each role is even *trying to do* in discussion. A villager wants to surface threats and build a
correct lynch consensus. An investigator wants to transmit a confirmed read without getting
night-killed for revealing it. A healer wants to stay invisible. A wolf wants to conceal, misdirect,
protect its ally, and scout power roles to kill at night; the SK wants above all to survive the day
vote. Factoring the common moves out of those role goals gives seven recurring act types, the
**primitives** — **accuse, frame, lead, defend, blend, deflect, claim** — grouped under three axes:
*offense* (steer the room), *defense* (manage your own heat), *transmission* (turn private truth into
public action). To be clear about their status: the primitives are design vocabulary, not code. They
were never implemented as detectors or credit buckets; they are the checklist that tells the tagger
prompt what kinds of act to look for. **Frame** — building the story that makes an accusation stick —
is the §2-status-3 primitive that matters most for deceivers, and no deterministic trace of it exists.

**Tag fine, credit coarse — the granularity ladder.** The next question is grain: at what resolution
does the tagger see, and at what resolution does it pay? The obvious answer — credit each of the seven
primitives as its own per-dimension signal — dies on density. An SP's credit rests on a handful of
followed turns; splitting those few turns across seven scores spreads an already-weak signal into
noise. So the ladder: seven primitives collapse into the three axes and finally into **one holistic
verdict** per turn. The fine tags are the *detection vocabulary* — what lets the model see a frame or
a deflection at all; credit stays coarse, one value per turn.

**Omniscient, but valence never trusts the player.** The pass runs post-game with true roles revealed,
so it can *emit structure* (framing, credibility, role-reveal) reliably. The judgment of good or bad —
the **valence** — stays anchored on observable behavior plus true roles, never on a player's own
account of itself, because LLMs confabulate self-serving rationales: a self-report can explain what a
decision was, it cannot be allowed to grade it. (This rule returns as A4's boundary below.)

**All-required schema.** Flash-lite silently drops optional/nullable fields, so every field is
mandatory — a constraint that shaped the schema, not an afterthought.

**De-luck at the reward level.** The reward is `verdict − base_rate` with base 0 — never the game's
win/loss. A good play in a lost game is still positive; the halo the deterministic concealment metrics
collapsed into (§2) is designed out where credit is computed, not patched afterward.

Four critique-round amendments (A1–A4, same day) then shaped the design, each a problem → amendment:

- **A1 — per-message tagging was over-specified.** Framing and credibility only need an end-of-day
  pass: credibility ("was the story believed?") is only observable in the day's reactions and its vote
  anyway, so tagging per message would pay more for labels with less to ground them.
- **A2 — "it's deterministic now" must not relax the halo guard.** The temptation: "concealed =
  heat-low + survived" is deterministically computable, hence free, hence creditable. The amendment:
  computable is not safe — that is §2's passive-SK tautology restated (determinism ⊥ halo). So all
  concealment credit keeps its **de-halo brackets**, the three guard conditions that stop concealment
  from collapsing back into "survived ≈ won": concealment scores only when *paired with offense*
  (pure silence can't earn); it is *role-conditioned* on whether the heat shed was deserved (a wolf
  shedding deserved suspicion is the deception working, credited as deception skill); and it is
  *leverage-weighted* toward concealment that held against the room's momentum, not heat that was low
  because the game was already won.
- **A3 — the day-vote endpoint can't see night.** Discussion consequences that land at night — an
  investigator whose reveal gets it night-killed, a hidden read that surfaces only as a vigilante shot
  or an SK target — are invisible to any vote-anchored credit (the same blind spot §1b's companion
  check measured at 62–71%). Amendment: add the night-action **exposure** endpoint (reveal-risk,
  confirm-out, the hidden read).
- **A4 — the agent's own reasoning enters as attribution, never valence.** Each agent's
  `updated_strategy` reasoning is fed to the tagger so it can *attribute* — de-confound a night
  target, surface an unvoiced read, trace influence. Per the confabulation rule above, valence stays
  deterministic: a self-serving rationale can route credit to the right decision, it can never
  generate the credit.

### Built and wired the same day (2026-06-19, commit `c038bd5`)

The tagger was built the same day (`discussion_tagger.py`) and wired into the loop's per-SP credit
engine as the third credit channel beside votes and night actions. Three wiring facts matter later:

- **A mode switch, floor as default.** Discussion credit is selectable per run via the loop config's
  `discussion_mode`: `floor` (§1's free day-vote endpoint) or `tagger`. The floor stayed the default
  until the tagger earned the flip (§4).
- **A per-game tag cache.** Credit recomputes over a rolling window, so without a cache the tagger
  would re-pay flash-lite for the same games every tick. Tags are therefore cached per `game_id`; a
  re-score reads the cached tags. (This cache key returns, badly, in §6.)
- **The wolf vote channel went blend-aware.** The one signal §1a validated — wolves win by voting
  where the room goes — was wired in directly: a wolf voting the day's plurality scores positive,
  rather than being scored on target-correctness like town.

## 4 · Verify → decide: does the tagger earn its keep? (2026-06-19 → 06-20)

The risk after §3 was the obvious one: the tagger might just re-derive the free floor at a price.
`tagger_effectiveness.py` (2026-06-19, 8 games,
[../../evaluation/src/instrument_validation/tagger/tagger_effectiveness.py](../../evaluation/src/instrument_validation/tagger/tagger_effectiveness.py))
tested exactly that with two probes, each a correlation the verdict should *not* have. The **halo**
probe correlates the tagger's verdict with who won the game: high correlation means the verdict is
leaking outcome (§2's failure mode) rather than judging play. The **redundancy** probe correlates it
with the free day-vote floor: high correlation means the paid signal is a copy of the free one.

*Catches: is the paid signal anything the free floor doesn't already give?* The first wiring failed
the test:

- **Merit-only discussion verdict** (the tagger judging discussion merit alone) — halo **+0.21**,
  redundancy with the free floor **+0.55**. Poor ROI: paying flash-lite to reproduce a free signal.
- **Enriched verdict** (the holistic verdict *weighing* framing/credibility/role-reveal) — halo
  **+0.11**, redundancy **+0.34** (down from +0.55). Now it adds the concealment axes the floor
  structurally can't see.
- **Night read-quality** — halo +0.12, and it **reassigns ~31% of night actions**: 30 skilled misses
  *credited* and 12 lucky hits *demoted* vs the outcome-only deterministic night credit. A skilled
  miss is a night target the day's discussion genuinely justified that happened not to pay off; a
  lucky hit is the reverse. No free signal exists for read quality, so this is where the paid tagger
  is irreplaceable.

**Decision:** the tagger earns its keep on its *unique* axes — framing-weighted discussion plus night
read-quality — not the merit-only day-credit first wired. The holistic (enriched) verdict became the
credited field, and the `discussion_mode` default flipped **floor → tagger** (2026-06-20, commit
`d7eaa45`). This is also why `report.md` insists only the holistic `verdict` feeds credit: the
sub-tags are what *make* it enriched, but crediting them separately was the poor-ROI path already
rejected here.

## 5 · Correctness pass — are the tags actually right? (2026-06-20)

With the tagger credited, the next risk was silent per-field error. `tagger_accuracy.py` (2026-06-20,
8 games, [../v7_final/discussion_credit/tagger_accuracy.py](../v7_final/discussion_credit/tagger_accuracy.py))
cross-checked the structure tags — not their effectiveness, their *correctness*.

*Catches: does the tagger hallucinate framing/role-claims, or read them from the actual game?* The
`framing=manipulative` tag skewed exactly as it should against true roles — **town 7% / wolf 85% / SK
88%** — and credibility was non-degenerate (it spread across its levels instead of collapsing to one
value). But `role_reveal` was on softer ground: the only cross-check available was a regex for
first-person self-claims on the raw chat, and against it the tagger missed implicit claims and risked
hallucinating explicit ones. The fix was *at the source*, not in the tagger prompt: persist the
in-game structured `DaySummary.role_claims` — the reliable extraction the game already computes and
was throwing away (§1b) — and **anchor** `role_reveal`/credibility on it. A claim whose declared role
differs from the true role is then a mechanical deception tell. This is why the shipped contract
(`report.md`) states role-reveal is anchored on structured extraction with only a raw-message
*fallback* for records that predate the persist.

## 6 · The v2 run — a retraction, then a validation (2026-06-22 → 06-23)

**The run itself.** v2 was the compounding loop's second paid run, and the first designed to be
readable: a cold-started memory store, memory-ON and memory-OFF arms paired on the same board setups
(matched `game_id`s), 4 games per generation per arm, stopped at generation 6 by a pre-registered
stopping rule (~$15; full run record
[../v7_final/experiment_log.md](../v7_final/experiment_log.md) §12). Its *intended* design was
town-only: memory ON for town roles alone, against an all-OFF baseline. Two defects, both found the
next day by re-auditing the raw records instead of trusting the run's own narrative, broke that
design:

1. **The ON arm actually ran `all_enabled`** — every faction had memory; the intended `town_only`
   config existed but was never passed, so the driver fell back to its default. For the town question
   this is an arms-race confound: town was not playing against the fixed baseline wolves the design
   assumed, but against wolves that were improving too. And the vote proxy scores a town vote positive
   only if the votee is a real threat, so stronger wolves mechanically depress town's score regardless
   of town skill — de-lucking removes outcome luck, not opponent strength (§0). The clean town-only
   test was therefore never run.
2. **The tag cache collided across arms.** ON and OFF games shared `game_id`s, and tags cache per
   `game_id` (§3) — so the OFF arm was scored with the ON arm's cached tags.

The run was invalidated for its town question and repositioned as an all-memory-on A/B
(v7_final §12f). What follows is what that collapse did to the tagger's two headline numbers — one
retracted, one validated — and the distinction between them is the most important thing in this log.

**The retraction (v7_final §12f).** A "+0.556 discussion gain" had been read off the credited store
for the town `villager/day_discussion` cell. It was **retracted as a halo.** The number was an
*undifferenced credit level*: raw `(positive − negative)/follow` with the tagger base pinned at 0,
never differenced against the no-memory arm. That subtraction is not optional. Positive tagger
verdicts occur *with or without* memory, so a raw positive level says nothing about what memory
*added* — the exact halo the design warned of (§2/A2) — and the cache collision compounded it. When
differenced properly via the free day-vote floor, which is valid in *both* arms precisely because it
needs no tags, villager/day_discussion on−off was pure noise (mean ≈ −0.12).

**The validation (v7_final §12g).** A separate, adversarial investigation asked whether the tagger's
*discussion verdict* carries real skill. It was held to a far higher bar than the retracted number
ever was — `tagger_skill_retest.py`
([../v7_final/runs/v2_full/tagger_skill_retest.py](../v7_final/runs/v2_full/tagger_skill_retest.py)),
N=24 ON games:

*Catches: is the wolf/SK discussion signal outcome-leak, wordiness, or real skill?* Each column
removes one more mundane explanation: in (A) the tagger sees the game as-is; in (B) it is
**blinded** — votes and deaths withheld, so it cannot peek at who won; in (C) the correlation is
additionally recomputed with the part explained by sheer message volume mathematically removed (a
"partial *r*"), so talking a lot cannot masquerade as skill:


| faction           | (A) outcome-in\| de-luck | (B)**blinded** \| de-luck | (C)**blinded + verbosity-controlled** |
| ----------------- | ------------------------ | ------------------------- | ------------------------------------- |
| **wolf**          | +0.60                    | +0.58                     | **+0.56**                             |
| **serial_killer** | +0.55                    | +0.55                     | **+0.60**                             |
| **town**          | +0.07                    | +0.06                     | **+0.02**                             |

The wolf/SK discussion signal **survives blinding the tagger to the outcome and partialling out
message verbosity** → it is real deceiver skill the vote proxy cannot see, not leak and not wordiness.
Town adds ~0 — its skill *is* the vote proxy, the negative control.

And the leak the retraction implied was measured directly, not assumed: `tagger_deleak_ablation.py`
([../v7_final/runs/v2_full/tagger_deleak_ablation.py](../v7_final/runs/v2_full/tagger_deleak_ablation.py))
ran a **2×2** (outcome shown/withheld × all/speakers-only, N=6). *Catches: how much of the day-local
coupling is the tagger simply seeing who won?* Withholding the vote and deaths moved the coupling
**+0.07 town / −0.02 wolf / +0.05 SK** — negligible — and the mechanical silent-player effect was ~0
(the tagger barely tags non-speakers, 2/86). The 2×2 was necessary because a one-armed re-tag
confounds the outcome axis with the silent-player axis. **Decision:** keep `show_outcome=True`
(blinding bought within-noise gain at the cost of the night verdict's legitimate lynch context); bump
the tag cache `v1 → v2`.

**+0.556 vs +0.56 — the two numbers are not the same claim.** They are numerically adjacent and this
is exactly why they get confused; they measure different things, on different factions, with opposite
status:


|          | +0.556 (retracted)                                | +0.56 (validated)                               |
| -------- | ------------------------------------------------- | ----------------------------------------------- |
| quantity | undifferenced**credit level** `(pos−neg)/follow` | **partial *r*** of verdict with faction-**win** |
| faction  | **town** villager/day_discussion                  | **wolf** (SK = +0.60)                           |
| controls | none (never differenced vs no-memory)             | blinded to outcome + verbosity partialled out   |
| status   | **halo → retracted**                             | **real skill → validated**                     |

The corroboration is internal: the *skill* column for **town** is +0.02 — the tagger adds nothing for
the very faction whose "+0.556" halo was retracted. There is no contradiction between the two, only a
naming trap.

## 7 · Hardening and graduation (2026-07-02)

A code+evidence review flagged the tagger as load-bearing (the paid credit signal rides it) yet
failing silently, and closed three silent-failure paths
([../evaluation/hardening_pass/experiment_log.md](../evaluation/hardening_pass/experiment_log.md)
§4.2–4.4):

- **Per-day LLM failure was swallowed** → now collected and surfaced as an end-of-game `logger.error`
  counting degraded days, with a `strict` mode that re-raises.
- **Missing eval-cases sidecar silently emptied `role_claims`/`private_reads`** → now warns loudly
  once per game.
- **The tag cache could serve one arm's tags to the other** (the §6 collision) → a session/trace
  provenance slug is folded into the cache key *and* asserted on read, re-tagging fresh on mismatch.

The load-bearing validation numbers had also lived only as stdout; the retest/ablation scripts now
*also* write `*_results.json` (statistics untouched, not re-run — so the JSON is not yet on disk; the
durable record remains v7_final §12g). Finally the three validation scripts (accuracy / skill /
deleak) were **graduated** into one config-driven runner, `eval-tagger`
([../../evaluation/src/cli_runner/discussion_tagger_eval.py](../../evaluation/src/cli_runner/discussion_tagger_eval.py),
modes `accuracy | skill | deleak`); the frozen v2_full scripts stay in place as dated evidence.
`tagger_effectiveness.py` (§4) was not graduated and remains a frozen script.

## 8 · Limitations and future work (freshness: 2026-07-04)

Ordered by criticality (likelihood × impact × detectability); minor gaps are kept, not deleted.

1. **Metric, not a memory verdict (Med-High).** The tagger is a *validated instrument*, not evidence
   that wolf/SK memory compounds. The v2 run that produced its numbers was mis-configured to
   all-factions-on, confounding the town question and never isolating a wolf memory-on/off contrast.
   Converting the tentative wolf signal into a memory *verdict* needs a **direct wolf SP/obs A/B** —
   never run — with the tagger as its discussion-merit ruler.
2. **Uncalibrated per-field (Med).** No human golden behind `framing`/`credibility`/`role_reveal`;
   they are distributionally sane and face-valid, never label-validated. The credited holistic
   `verdict` is validated correlationally; the sub-tags are not. The cheapest independent upgrade is a
   small golden.
3. **Single-epoch, N=24 (Med).** The +0.56/+0.60 rests on one epoch; it would piggyback on a held
   town-only rerun for power and a fresh epoch — closing with gap 1.
4. **Night-verdict residual leak untested (Low).** The night verdict still sees its own kill's death
   (the night analogue of the day leak §6 cleared for discussion). A two-prompt split fixes it only if
   a clean deceiver *night* metric is ever needed; night already has a deterministic de-luck proxy
   underneath.
5. **Not promoted to the standing scorecard basket (Low).** The tagger lives in the loop credit
   ledger + its own apparatus, not as a standing de-lucked proxy in the metrics basket (the "Phase-2
   LLM tagger" the discussion-scoring plan deferred). Deliberate, documented.
6. **"flash-lite" is caller-pinned (Low).** `get_llm_pro()`'s bare default is `gemini-2.5-pro`;
   flash-lite holds only under the loop's env pin. Not a live hole (the driver always pins), but a
   footgun for a standalone caller.

**Meta-lesson.** The tagger's validity claim shrank three times under adversarial review — *haloed →
winner-blind → leak negligible* — and only then was the *replacement* claim ("real deceiver skill,
+0.56/+0.60") asserted, held to the same standard (blinded + verbosity-controlled) that broke the
numbers before it. The discipline that makes this workstream trustworthy is not that the first number
was right; it is that the first number was retracted in place, and the number that replaced it had to
survive the same knives.

---

*Companion reference (current mechanism): [report.md](report.md) · Trust/reliability apparatus:
[../evaluation/discussion_tagger/report.md](../evaluation/discussion_tagger/report.md) · Frozen design +
run records: [../v7_final/discussion_credit_design.md](../v7_final/discussion_credit_design.md),
[../v7_final/experiment_log.md](../v7_final/experiment_log.md) §12, and the v2_full/ tagger scripts ·
Deterministic prehistory: [../metrics/design/discussion_scoring_plan.md](../metrics/design/discussion_scoring_plan.md),
[../metrics/design/discussion_lead_vs_blend.py](../metrics/design/discussion_lead_vs_blend.py),
[../metrics/design/deceiver_metric_refinement.md](../metrics/design/deceiver_metric_refinement.md). Live code:
[../../evaluation/src/loop/discussion_tagger.py](../../evaluation/src/loop/discussion_tagger.py). Written
2026-07-04; restructured 2026-07-08 (per owner review: lead with the existing credit system and the
deterministic attempts before the structural argument; de-compress for a reader new to the pipeline).*
