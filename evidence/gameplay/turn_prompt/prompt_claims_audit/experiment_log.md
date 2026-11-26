# Prompt-claims audit — are the hand-authored PLAYSTYLE tactics actually true?

**Date:** 2026-06-17 · **Status:** audit complete; one falsified claim → investigator rewrite drafted
behind a default-off flag (`WW_INVESTIGATOR_PROMPT=transmit`), ready to A/B.

## Why this audit exists

The generated **threat-brief** (`Agents/prompts/roles.threat_brief`) was deliberately held to a
*facts-only* bar — true regardless of how anyone plays — precisely so the eval harness can't launder
the experimenter's strategy into the result. The hand-written **PLAYSTYLE prose** was **never held to
that bar.** It is full of *tactical claims* — assertions that behaviour X helps a faction — that we
assumed were good play. Those assumptions are testable against the metrics we already track. At least
one is false, and harmful.

Two axes, kept distinct:
- **Steering** — the clause is prescriptive (do X) rather than mechanical fact. Not inherently bad.
- **Not strictly true** — the steer asserts *effectiveness* our evidence contradicts (or can't
  support). That is the problem class.

## Clause audit (substantive clauses)

| Role | Clause | Type | Status |
|---|---|---|---|
| **Investigator** | "primary goal is survival — info worthless if you die before you can use it" | steer | **contradicted** — backwards: a read is worthless if *untransmitted*; surviving with an unspoken read changes no votes |
| | "Never reveal your role prematurely" | steer | **contradicted** (with the IM block → de-facto non-reveal) |
| | "Information Management: rather than publicly accusing the moment you have a result, steer with questions and let consensus build" | steer | **contradicted** — this *is* the observed failure mode (see below) |
| | "Each result names a player's exact role" | fact | ✓ |
| **Wolf** | "blend your vote with the village majority whenever possible" | steer | **validated / helpful** (see blend test) |
| | "a dissenting protest vote leaves a permanent suspicious record" | steer | consistent with the above |
| **Villager** | "be proactive… don't stall in 'we need more information' loops" | steer | untested; note it steers *opposite* to the investigator's concealment lean (prompts aren't internally consistent on town forthcomingness) |
| | "public voting record is the most durable hard evidence" | fact-ish | ✓ |
| **Healer** | "staying alive matters a great deal" | steer | grounded (dead healer = no protection) |
| **SK** | "participate so you neither dominate nor vanish" | steer | balanced; the harmful "blend by going quiet" passivity came from **memory**, not this prose |
| **Vigilante** | "whether to reveal is your own call" | neutral | ✓ (correctly defers to the agent) |

## The two testable claims, against tracked metrics

The audit **discriminates** — it does not produce a blanket "prompts launder strategy." Of the two
hand-authored tactics we can test, the wolf's holds and the investigator's fails.

### Investigator "conceal / let consensus build" — FALSIFIED (harmful)

From the v6 SP A/B reads (`evidence/memory_system/effectiveness/v6_sp_ab`): the investigator *votes*
the confirmed wolf ~100% but *asserts* the confirmed read only ~33–67%; the dominant failure is
**vague mention** — naming the wolf with no claim of having investigated it. Direct transcript
(`v6ab_baseline.jsonl`, game `cb298a71`): the investigator writes **five** day-3 messages prosecuting
the confirmed wolf entirely on "behaviour / voting record / manipulation" and **never says it
investigated them** — laundering the confirmed read as behavioural suspicion. The wolf is removed
after a confirmed read ~60–67% **regardless of arm** — the bottleneck caps the town's single
highest-value channel, and memory cannot lift it. This is **provenance-suppression, prompt-caused**:
the model is doing exactly what the IM block instructs. (`investigator_transmission.py`.)

### Wolf "blend with the majority" — VALIDATED (helpful)

`wolf_unconditioned_blending_rate` (the validated camouflage proxy, sign +) vs wolf-win:

```
POOLED (all v6ab arms)  n=122  r=+0.164 p=0.070   wolfwin| blend≥.8: 0.38 (n=50)  blend<.8: 0.25 (n=72)
baseline only           n= 22  r=-0.233 p=0.297   wolfwin| blend≥.8: 0.14 (n=7)   blend<.8: 0.27 (n=15)
```

Pooled trends positive (38% vs 25%, p=0.07), directionally consistent with the prior larger-N
validation on the `ab_*` set (**r=+0.20, p=0.003 at n=220**;
`paired_ab/diagnose_wolf_blending.py`). The baseline-only sign flips negative but is hopelessly
underpowered (22 games / 7 high-blend) — noise. Weight of evidence: **blending helps wolves; the
prompt tells the truth there.** (Pooling across arms is legitimate: every v6ab arm has memory-less
wolves — the deceiver arm is the SK — so the wolf channel is constant across all six.)

## What this reframes

The "garbage-in" root sits one layer **upstream** of where we'd been placing it. The chain is not
just *source-games → memory*; it is **prompt tactical claim → shapes the play → extraction mirrors the
play → memory amplifies it.** The investigator's mined lesson *"build a case gradually / don't open
with a hard accusation"* (v6 A/B mechanism #4) is the prompt's *"let consensus build"* instruction,
extracted and fed back. **Memory faithfully amplified a prompt-injected bad strategy.** So a memory
result can be flat/negative not because memory is useless but because it is a faithful mirror of play
that the prompt itself biased.

## The fix (targeted, not a wholesale purge)

Only the investigator block carries a *measurably harmful* steer, and it sits on the role holding the
game's highest-value information. The rewrite (drafted in `Agents/prompts/roles.py`, behind
`WW_INVESTIGATOR_PROMPT=transmit`) **corrects the false framing toward a neutral tradeoff — it does
NOT swap in the opposite tactic.** Baking in "reveal immediately" would launder our strategy the same
way concealment did. Instead it states the true mechanic the old prompt got wrong (a read only helps
once the village acts on it; an unshared read changes no votes) and presents reveal as a genuine
two-sided call (rally the village vs paint a night target) — the agent's to weigh. If a *neutral*
framing lifts transmission, that proves the old prompt was actively suppressing, not that we hand-fed
the answer.

**A/B design (when green-lit, same-epoch concurrent, fresh baseline):** two arms — control (default
prompt) vs `WW_INVESTIGATOR_PROMPT=transmit` — on held-out game_ids. Primary read = the transmission
metric (`claimed`/`transmitted` rate) and the investigator→lynch chain (`removed`); confirmatory =
town win-rate + the validated decision-quality basket. Memory off for the clean prompt-effect read.

## Caveats

Pooled blend p=0.07 is a *trend*, leaning on the prior n=220 for significance; both claims are
correlational (blending/transmission could co-move with game state). The robust part is the
**asymmetry** between the two claims. Clause typing is a judgement call; the table is the audit's
opinion, the two tested rows are the evidenced ones.

## Provenance

Reads over `batch_results/v6ab_*.jsonl` (epoch of the v6 SP A/B, store `memory_stores/v6_1`).
Blend test `blend_claim_test.py` (this folder); transmission metric
`evaluation/src/experiments/investigator_transmission.py`; prior blend validation
`evidence/memory_system/effectiveness/paired_ab/diagnose_wolf_blending.py`; rewrite + flag in
`Agents/prompts/roles.py`.
