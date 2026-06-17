# v6 SP A/B — episodic-memory effectiveness (town obs · deceiver obs/sp/both)

**Date:** 2026-06-17 · **Status:** ALL 6 arms complete at N=30 (baseline, town-obs, town-sp, sk-obs,
sk-sp, sk-both).

## Setup

- **Arms (paired, same 30 held-out fresh game_ids → identical role draws):** `baseline` (no memory),
  `town-obs`, `sk-obs`, `sk-sp`, `sk-both`. Deceiver arm = the **serial killer**, not the wolf:
  the registry threat-brief fix (commit `bbc7c5b`) changed wolf behaviour, so wolf memory mined under
  the old SK-blind prompt is stale; the SK was always self-aware, so its `v6_1` memory stays valid.
  (A `town-sp` arm was added mid-run; **no `town-both` arm** — synergy-rescue is untested for town.)
- **Store:** `memory_stores/v6_1` (UNDEDUPED), seeded read-only from the serialized cache, `--no-memory-dump`.
- **Retrieval pinned RAW** (rerank + MMR-filter OFF) — i.e. the precision mechanisms are disabled by
  design (comparability with the prior raw A/B; the precision knobs are a deliberate follow-up lever).
- **Same-epoch:** all arms launched concurrently → one model snapshot. **Epoch is SK-favoured:**
  overall SK 47% / villagers 35% / wolves 18% (avg 4.7 days); baseline SK 52% — high but not ceilinged.
- Game model `gemini-3.1-flash-lite`, temp 1.0, `game_thinking_level: minimal`.

## Headline results (paired McNemar / Wilcoxon vs baseline)

**Nothing reaches p<0.05.** N=30 with a binary/role-outcome DV is underpowered for the effect sizes
here. The value is in the *coherent directional pattern* + the mechanism below.

**Metric validity — report discipline.** Only a subset of what we emit is monotonic-in-skill, and
only those + win-rate are OUTCOME claims (per `evidence/metrics/proxy_win_monotonicity.md`):
- **Validated (skill-monotonic):** win-rate, and the TOWN decision-quality basket —
  `town_vote_accuracy`, `correct_elimination_rate`, `mislynches`/`town_mislynch_rate`,
  `serial_killer_lynched`.
- **NOT validated → DESCRIPTIVE only:** `investigator_wolf_find_rate` (found_wolf_day was backwards),
  the vigilante/healer **activity counts**, and the **SK/deceiver basket** (never validated — "needs
  the A/B's larger N"). These describe HOW behaviour changed, not whether skill/outcome improved, and
  are kept out of the headline below.

### SK branch (N=30, final)
| arm | SK win | Δ vs base | discord (arm+/base+) | p |
|---|---|---|---|---|
| sk-obs | 47% | 0 | 7/7 | 1.00 |
| sk-sp | 30% | −17pp | 6/11 | 0.33 |
| sk-both | 53% | +7pp | 6/4 | 0.75 |

The cleanest test is the **direct synergy contrast sk-both vs sk-sp** (no baseline in the way):
SK lynched **47% vs 70%** (p=0.071), +23pp win (p=0.118), +0.40 nights, +0.40 kills. So:
**SP-alone trends harmful to the deceiver** (the stale "blend by going quiet" passivity SP, followed
past the early game → caught — predicted a priori), and **obs+SP-with-synergy rescues it** (obs
cross-check overrides the bad SP — exactly the synergy mode's design intent). Coherent across
win-rate AND the SK proxy basket (exploratory/unvalidated).

### Town branch (N=30, final) — validated metrics only
- **town-obs: flat/null.** villager win +6pp (p=0.77); validated decision-quality basket all Δ≈0,
  p>0.8. **Does NOT replicate v5's town-memory benefit.**
- **town-sp: trends negative on decision quality.** villager win −7pp (p=0.75, NS — the −14pp at
  n=21 regressed); but the validated basket trends consistently worse: `town_vote_accuracy` −0.086,
  `correct_elimination_rate` −0.103, `town_mislynch_rate` +0.103 (all p≈0.19–0.25, NS). So SP memory
  trends to *degrade* town decision quality — directionally consistent with sk-sp and the
  counterproductive-content finding, below significance.

**Behavioural (DESCRIPTIVE — non-monotonic, not an outcome claim):** the *only* p<0.05 movements in
the batch are **vigilante activation** — town-obs `shots_taken` +0.53 (p=0.001), `bullets_unused`
−0.53 (p=0.001), `evil_shots` +0.33 (p=0.008), `friendly_fire` +0.20 (p=0.034); town-sp `shots_taken`
+0.27 (p=0.021). Memory makes the vigilante fire ~3–4× more — but it's double-edged (more evils AND
more friendlies; pooled precision 80%→67%), so it is **behavioural potency, not a skill gain**, and it
washes on outcomes. (obs also nudges `healer_save_rate` +0.13, p=0.11; SP does not.) These are causal
evidence that memory moves behaviour — see mechanism #1 — not town improvements.

### Cross-cutting
**SP-form memory (the v6 strategy-points channel) trends harmful for BOTH factions; observations are
neutral; the synergy arm is the only one that helps.** No `town-both` arm, so synergy-rescue is
confirmed only for SK.

## Mechanism (why) — the substance

1. **Verdicts are causally upstream of actions, not rationalization.** Output schema emits
   `strategy_verdicts` first and the action (`vote_target`) LAST, so with autoregressive +
   minimal-thinking generation the action is conditioned on the committed verdict. Behaviourally:
   following an abstain-SP → **77% abstain vs 32% baseline** (+45pp); judging it not_relevant →
   **30% ≈ baseline** (true ablation, no residual leakage). The instrument is faithful — "ignore"
   really ignores; "follow" really enacts.

2. **Retrieval precision is mediocre and the agents' rejections are VALID.** obs applies-rate ~60%
   (only ~9% "fully"); SP not-relevant ~50% (town **63%**). Sampled `not_relevant` verdicts are
   correct — the SPs are conditional (IF precondition THEN action) but retrieval matches on situation
   *text* embedding, surfacing precondition-MISMATCHED SPs (an "as a confirmed Investigator…" lesson
   for a still-hidden investigator). The agent does retrieval's precision job for it. **Systemic
   (both factions), town worst.**

3. **Following memory does NOT improve town decision quality.** Day-vote correctness among decisive
   votes: followed 63–66% vs baseline 69% (flat/slightly worse); investigator night find-enemy:
   followed 45–59% vs 61% (small n). Memory's potent behavioural lever channels into **caution
   (more abstention)**, not sharper enemy-ID → washes out.

4. **Town SP content is a mirror of bottleneck-capped play — and self-defeating.** NOT caution-skewed
   (40% active vs 16% passive, like SK) — but the *active* lessons are counterproductive in substance:
   several explicitly encode the transmission bottleneck — *"do not reveal your findings, build a
   case gradually"*, *"don't open with a hard accusation"*, *"establish bona fides before
   prosecuting"*, plus herd-follow (*"vote with the consensus"*) and weak-signal pressure. Extraction
   faithfully mined the town's own sub-optimal play and now feeds it back, reinforcing the failure.

5. **Investigator-transmission bottleneck caps town, unmoved by memory.** The wolf is removed after a
   confirmed read ~60–67% **regardless of arm** — memory doesn't lift the investigator→lynch chain.
   And it's **self-reinforcing**: the investigator stays hidden → the high-value "confirmed
   investigator" SPs are correctly dismissed as inapplicable → memory literally can't help it
   transmit. (Transmission is also genuinely incomplete: investigator *votes* the wolf ~100% but
   verbally *asserts* the confirmed read only ~33–67%; "vague mention" failure mode is real.)

## Interpretation (headline)

**Episodic memory mined from a system's own capped play reinforces its existing failure modes rather
than improving on them** — sharpest for the SP channel. The memory is faithfully retrieved and
faithfully followed (mechanism #1), so the flatness is not an instrument artifact; it's **content**:
the lessons mirror mediocre play (#4) and don't carry decision-improving signal (#3), while an
upstream communication bottleneck caps the outcome anyway (#5). Retrieval precision is a real but
secondary problem (#2). The one bright spot is the **synergy mode** (obs correcting SP), which
flips the deceiver result from harmful to neutral/positive.

## Leads / next steps (all read-side-screenable first; any live re-run needs a fresh same-epoch baseline)

- **Replay screen for precision** (town is replay-screenable): re-retrieve frozen eval-case snapshots
  with rerank+filter and/or **dimension-aware gating** (we have the v6 structured dims) → does the
  not-relevant rate drop? Screen before committing a live arm.
- **Content lever is upstream of retrieval**: source-game quality (mine from stronger town play — but
  this epoch's town is bottleneck-capped) vs normative extraction (distil what town *should* do — risks
  laundering experimenter strategy into the store; same line we drew for prompts).
- **LLM-judge passes** (post-batch, avoid API contention): (a) transmission = did the investigator
  *assert* the confirmed read (vs the heuristic bracket); (b) categorize SP content
  concealment/herd vs decisive enemy-ID at scale.
- **Add a `town-both` arm** to test whether synergy rescues town-sp's negative trend (as it did for SK).
- **More N** for the SK synergy contrast (lynch-rate p=0.071 would likely tighten at ~2×N).

## Caveats

Nothing significant (all p>0.07); N=30 underpowered; SK proxy basket unvalidated; content/transmission
analyses are lexical/qualitative (judge-confirmation pending); town-sp incomplete (21/30); raw
retrieval (precision off by design). Epoch is SK-favoured — absolute rates won't transfer across runs;
within-arm paired deltas are the unit.

## Provenance

Store `memory_stores/v6_1` · code at commit `620fb3c` (threat-brief fix `bbc7c5b`, dedup reconcile
`3117656`, tracking changes `d4b5f47`/`8554984`) · seed set `game_ids.json` (30 fresh held-out) ·
runner `launch_arms.sh` · transmission metric `evaluation/src/experiments/investigator_transmission.py`.
Per-arm records `batch_results/v6ab_<arm>.jsonl` + eval-case sidecars.
